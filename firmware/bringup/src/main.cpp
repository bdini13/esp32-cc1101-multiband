#include <Arduino.h>
#include <SPI.h>
#include "radio_diagnostics.h"

namespace Pins {
constexpr uint8_t kSclk = 18, kMiso = 19, kMosi = 23, kChipSelect = 21;
constexpr uint8_t kGdo0 = 26, kGdo2 = 27;
constexpr uint8_t kRfSwitch0 = 32, kRfSwitch1 = 33, kStatusLed = 25;
}

SPIClass radioSpi(VSPI);
struct RadioHal {
  void beginResetPins() {
    radioSpi.end();
    digitalWrite(Pins::kSclk, HIGH);
    digitalWrite(Pins::kMosi, LOW);
    pinMode(Pins::kSclk, OUTPUT);
    pinMode(Pins::kMosi, OUTPUT);
  }
  void endResetPins() {
    radioSpi.begin(Pins::kSclk, Pins::kMiso, Pins::kMosi, Pins::kChipSelect);
  }
  void beginTransaction() {
    radioSpi.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
  }
  void endTransaction() { radioSpi.endTransaction(); }
  void chipSelect(bool selected) {
    digitalWrite(Pins::kChipSelect, selected ? LOW : HIGH);
  }
  uint8_t transfer(uint8_t value) { return radioSpi.transfer(value); }
  bool ready() { return digitalRead(Pins::kMiso) == LOW; }
  uint32_t nowUs() { return micros(); }
  void delayUs(uint32_t value) { delayMicroseconds(value); }
  void isolateRf() {
    digitalWrite(Pins::kRfSwitch0, LOW);
    digitalWrite(Pins::kRfSwitch1, LOW);
    delayMicroseconds(10);
  }
};

void setup() {
  // Preload latches before enabling outputs. External pulldowns still protect
  // RF selection during reset/boot, before firmware has executed.
  digitalWrite(Pins::kChipSelect, HIGH);
  pinMode(Pins::kChipSelect, OUTPUT);
  digitalWrite(Pins::kRfSwitch0, LOW);
  digitalWrite(Pins::kRfSwitch1, LOW);
  digitalWrite(Pins::kStatusLed, LOW);
  pinMode(Pins::kRfSwitch0, OUTPUT);
  pinMode(Pins::kRfSwitch1, OUTPUT);
  pinMode(Pins::kStatusLed, OUTPUT);
  pinMode(Pins::kGdo0, INPUT);
  pinMode(Pins::kGdo2, INPUT);
  digitalWrite(Pins::kSclk, LOW);
  digitalWrite(Pins::kMosi, LOW);
  pinMode(Pins::kSclk, OUTPUT);
  pinMode(Pins::kMosi, OUTPUT);

  Serial.begin(115200);
  delay(300);
  Serial.println("ESP32 + CC1101 A2 digital diagnostics v2");
  radioSpi.begin(Pins::kSclk, Pins::kMiso, Pins::kMosi, Pins::kChipSelect);
  RadioHal hal;
  Diagnostics::Radio<RadioHal> radio(hal);
  const auto result = radio.run();
  Serial.printf("RESULT=%s PARTNUM=0x%02X VERSION=0x%02X MARCSTATE=0x%02X\n",
                Diagnostics::errorName(result.error), result.part,
                result.version, result.state);
  digitalWrite(Pins::kStatusLed, result.ok() ? HIGH : LOW);
  Serial.println("RF paths remain isolated. No RX/TX profile or command issued.");
  Serial.println("Digital check only; this is not RF or board qualification.");
}

void loop() { delay(1000); }
