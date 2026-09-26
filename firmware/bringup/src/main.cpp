#include <Arduino.h>
#include <SPI.h>
#include "radio_diagnostics.h"
#include "rf_boot.h"

namespace Pins {
constexpr uint8_t kSclk = 18, kMiso = 19, kMosi = 23, kChipSelect = 21;
constexpr uint8_t kGdo0 = 26, kGdo2 = 27;
constexpr uint8_t kStatusLed = 25;
}

struct RfPins {
  void high(uint8_t pin) { digitalWrite(pin,HIGH); }
  void output(uint8_t pin) { pinMode(pin,OUTPUT); }
};

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
    RfPins pins;
    RfBoot::isolate(pins);
    delayMicroseconds(10);
  }
};

void setup() {
  // A3 ONLY: PE42442 V3/V2/V1=111 is all-off. External pullups protect
  // RF selection during reset/boot, before firmware has executed.
  digitalWrite(Pins::kChipSelect, HIGH);
  pinMode(Pins::kChipSelect, OUTPUT);
  RfPins rfPins;
  RfBoot::begin(rfPins);
  digitalWrite(Pins::kStatusLed, LOW);
  pinMode(Pins::kStatusLed, OUTPUT);
  pinMode(Pins::kGdo0, INPUT);
  pinMode(Pins::kGdo2, INPUT);
  digitalWrite(Pins::kSclk, LOW);
  digitalWrite(Pins::kMosi, LOW);
  pinMode(Pins::kSclk, OUTPUT);
  pinMode(Pins::kMosi, OUTPUT);

  Serial.begin(115200);
  delay(300);
  Serial.println("ESP32 + CC1101 A3 digital diagnostics v3 (PE42442)");
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
