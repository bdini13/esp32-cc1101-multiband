#pragma once
#include <stdint.h>

// Restricted diagnostic API: no arbitrary writes, RX, TX or path selection.
// The same logic runs on the ESP32 and in host-side fault-injection tests.
namespace Diagnostics {
enum class Error : uint8_t {
  kNone, kResetTimeout, kReadTimeout, kUnstableIdentity,
  kUnexpectedPart, kUnreviewedVersion, kIdleTimeout
};
struct Result {
  Error error = Error::kNone;
  uint8_t part = 0xFF, version = 0xFF, state = 0xFF;
  bool ok() const { return error == Error::kNone; }
};
inline const char* errorName(Error error) {
  switch (error) {
    case Error::kNone: return "DIGITAL_CHECK_PASS";
    case Error::kResetTimeout: return "RESET_READY_TIMEOUT";
    case Error::kReadTimeout: return "SPI_READY_TIMEOUT";
    case Error::kUnstableIdentity: return "UNSTABLE_IDENTITY";
    case Error::kUnexpectedPart: return "UNEXPECTED_PARTNUM";
    case Error::kUnreviewedVersion: return "UNREVIEWED_VERSION";
    case Error::kIdleTimeout: return "IDLE_TIMEOUT";
  }
  return "INTERNAL_ERROR";
}
template <typename Hal> class Radio {
 public:
  explicit Radio(Hal& hal) : hal_(hal) {}
  Result run() {
    hal_.isolateRf();  // Enforced on every run, including after a fault.
    Result result;
    if (!reset()) {
      result.error = Error::kResetTimeout;
      return result;
    }
    for (uint8_t sample = 0; sample < 3; ++sample) {
      uint8_t part = 0xFF, version = 0xFF;
      if (!readStatus(0x30, part) || !readStatus(0x31, version)) {
        result.error = Error::kReadTimeout;
        return result;
      }
      if (sample && (part != result.part || version != result.version)) {
        result.error = Error::kUnstableIdentity;
        return result;
      }
      result.part = part;
      result.version = version;
    }
    // SWRS061I section 29.3. Other versions need review; rejection is not a
    // counterfeit verdict. In particular, a stuck-low bus must never pass.
    if (result.part != 0x00) {
      result.error = Error::kUnexpectedPart;
      return result;
    }
    if (result.version != 0x14) {
      result.error = Error::kUnreviewedVersion;
      return result;
    }
    const uint32_t started = hal_.nowUs();
    uint8_t consecutiveIdle = 0;
    while (static_cast<uint32_t>(hal_.nowUs() - started) < 20000) {
      if (!readStatus(0x35, result.state)) {
        result.error = Error::kReadTimeout;
        return result;
      }
      // Full byte check: bits 7:5 are documented read-zero.
      consecutiveIdle = result.state == 0x01 ? consecutiveIdle + 1 : 0;
      if (consecutiveIdle >= 2) return result;
      hal_.delayUs(50);
    }
    result.error = Error::kIdleTimeout;
    return result;
  }
 private:
  Hal& hal_;
  bool waitReady() {
    const uint32_t started = hal_.nowUs();
    while (!hal_.ready()) {
      if (static_cast<uint32_t>(hal_.nowUs() - started) >= 5000) return false;
      hal_.delayUs(1);
    }
    return true;
  }
  bool reset() {
    hal_.beginResetPins();  // GPIO: SCLK high, SI low per TI section 19.1.2.
    hal_.chipSelect(false);
    hal_.delayUs(5);
    hal_.chipSelect(true);
    hal_.delayUs(10);
    hal_.chipSelect(false);
    hal_.delayUs(50);  // At least 40 us high before SRES.
    hal_.endResetPins();  // Reattach SPI while CSn remains high.
    hal_.beginTransaction();
    hal_.chipSelect(true);
    bool ready = waitReady();
    if (ready) {
      hal_.transfer(0x30);  // SRES only; not a general-purpose strobe API.
      ready = waitReady();
    }
    hal_.chipSelect(false);
    hal_.endTransaction();
    return ready;
  }
  bool readStatus(uint8_t address, uint8_t& value) {
    hal_.beginTransaction();
    hal_.chipSelect(true);
    const bool ready = waitReady();
    if (ready) {
      // Read + burst bits distinguish status registers from strobes.
      hal_.transfer(address | 0xC0);
      value = hal_.transfer(0x00);
    }
    hal_.chipSelect(false);
    hal_.endTransaction();
    return ready;
  }
};
}  // namespace Diagnostics
