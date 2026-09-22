#include <Arduino.h>
#include <SPI.h>

namespace Pins {
constexpr uint8_t kSclk = 18;
constexpr uint8_t kMiso = 19;
constexpr uint8_t kMosi = 23;
constexpr uint8_t kChipSelect = 21;
constexpr uint8_t kGdo0 = 26;
constexpr uint8_t kGdo2 = 27;
constexpr uint8_t kRfSwitch0 = 32;
constexpr uint8_t kRfSwitch1 = 33;
constexpr uint8_t kStatusLed = 25;
}  // namespace Pins

namespace Cc1101 {
constexpr uint8_t kStrobeReset = 0x30;
constexpr uint8_t kStatusPartNumber = 0x30;
constexpr uint8_t kStatusVersion = 0x31;
constexpr uint8_t kStatusReadBurst = 0xC0;
}  // namespace Cc1101

enum class Band : uint8_t {
  k315,
  k433,
  k868,
  k915,
};

SPIClass radioSpi(VSPI);

bool waitForChipReady(uint32_t timeoutUs = 5000) {
  const uint32_t started = micros();
  while (digitalRead(Pins::kMiso) != LOW) {
    if (micros() - started > timeoutUs) return false;
  }
  return true;
}

uint8_t readStatusRegister(uint8_t address) {
  digitalWrite(Pins::kChipSelect, LOW);
  if (!waitForChipReady()) {
    digitalWrite(Pins::kChipSelect, HIGH);
    return 0xFF;
  }
  radioSpi.transfer(address | Cc1101::kStatusReadBurst);
  const uint8_t value = radioSpi.transfer(0x00);
  digitalWrite(Pins::kChipSelect, HIGH);
  return value;
}

bool resetRadio() {
  digitalWrite(Pins::kChipSelect, HIGH);
  delayMicroseconds(5);
  digitalWrite(Pins::kChipSelect, LOW);
  delayMicroseconds(10);
  digitalWrite(Pins::kChipSelect, HIGH);
  delayMicroseconds(50);
  digitalWrite(Pins::kChipSelect, LOW);
  if (!waitForChipReady()) {
    digitalWrite(Pins::kChipSelect, HIGH);
    return false;
  }
  radioSpi.transfer(Cc1101::kStrobeReset);
  const bool ready = waitForChipReady();
  digitalWrite(Pins::kChipSelect, HIGH);
  return ready;
}

void selectRfPath(Band band) {
  // The radio must remain idle during this operation. Full firmware will issue
  // SIDLE and verify MARCSTATE before calling this function.
  bool sw0 = false;
  bool sw1 = false;
  switch (band) {
    case Band::k315:
      // PCB wiring: SW0 -> BGS13SN8 V2, SW1 -> V1. V1/V2=10 selects RF1.
      sw0 = false;
      sw1 = true;
      break;
    case Band::k433:
      // V1/V2=01 selects RF2.
      sw0 = true;
      sw1 = false;
      break;
    case Band::k868:
    case Band::k915:
      sw0 = true;
      sw1 = true;
      break;
  }
  digitalWrite(Pins::kRfSwitch0, sw0 ? HIGH : LOW);
  digitalWrite(Pins::kRfSwitch1, sw1 ? HIGH : LOW);
  delayMicroseconds(10);
}

void isolateRfPath() {
  // SW0/SW1=00 means BGS13SN8 V2/V1=00: all paths disconnected.
  digitalWrite(Pins::kRfSwitch0, LOW);
  digitalWrite(Pins::kRfSwitch1, LOW);
  delayMicroseconds(10);
}

void setup() {
  pinMode(Pins::kChipSelect, OUTPUT);
  digitalWrite(Pins::kChipSelect, HIGH);
  pinMode(Pins::kRfSwitch0, OUTPUT);
  pinMode(Pins::kRfSwitch1, OUTPUT);
  pinMode(Pins::kStatusLed, OUTPUT);
  pinMode(Pins::kGdo0, INPUT);
  pinMode(Pins::kGdo2, INPUT);

  // Safe default: all RF paths isolated and CC1101 not placed into TX.
  isolateRfPath();

  Serial.begin(115200);
  delay(300);
  Serial.println("ESP32 + CC1101 Rev A bring-up");

  radioSpi.begin(Pins::kSclk, Pins::kMiso, Pins::kMosi,
                 Pins::kChipSelect);
  radioSpi.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));

  const bool resetOk = resetRadio();
  const uint8_t partNumber = readStatusRegister(Cc1101::kStatusPartNumber);
  const uint8_t version = readStatusRegister(Cc1101::kStatusVersion);

  Serial.printf("CC1101 reset: %s\n", resetOk ? "OK" : "FAILED");
  Serial.printf("PARTNUM: 0x%02X, VERSION: 0x%02X\n", partNumber, version);

  const bool plausible = resetOk && partNumber != 0xFF && version != 0xFF;
  digitalWrite(Pins::kStatusLed, plausible ? HIGH : LOW);
  Serial.println("Transmit remains disabled in bring-up firmware.");
}

void loop() {
  delay(1000);
}
