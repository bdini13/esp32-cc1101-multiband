#include "radio_diagnostics.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>

struct FakeHal {
  uint32_t clock = 0;
  bool active = false, selected = false;
  bool resetPins = false;
  uint32_t resetHighStart = 0;
  int isolationCalls = 0, starts = 0, ends = 0;
  int blockedTransaction = -1;
  bool blockAfterReset = false;
  std::vector<uint8_t> parts{0x00}, versions{0x14}, states{0x01};
  size_t partIndex = 0, versionIndex = 0, stateIndex = 0;
  std::vector<std::vector<uint8_t>> transactions;

  void isolateRf() { ++isolationCalls; }
  void beginResetPins() {
    assert(!active && !selected && isolationCalls > 0);
    resetPins = true;
  }
  void endResetPins() {
    assert(resetPins && !selected && clock - resetHighStart >= 40);
    resetPins = false;
  }
  void beginTransaction() {
    assert(!active && !selected && !resetPins && isolationCalls > 0);
    active = true;
    ++starts;
    transactions.emplace_back();
  }
  void endTransaction() {
    assert(active && !selected);
    active = false;
    ++ends;
  }
  void chipSelect(bool value) {
    assert(active || resetPins);
    if (resetPins && selected && !value) resetHighStart = clock;
    selected = value;
  }
  bool ready() {
    assert(active && selected);
    return starts != blockedTransaction &&
        !(blockAfterReset && starts == 1 && !transactions.back().empty());
  }
  uint32_t nowUs() { return clock++; }
  void delayUs(uint32_t value) { clock += value; }
  static uint8_t next(const std::vector<uint8_t>& values, size_t& index) {
    return values[index < values.size() ? index++ : values.size() - 1];
  }
  uint8_t transfer(uint8_t value) {
    assert(active && selected && ready());
    auto& bytes = transactions.back();
    bytes.push_back(value);
    if (bytes.size() == 1) return 0;
    assert(bytes.size() == 2 && value == 0);
    switch (bytes.front()) {
      case 0xF0: return next(parts, partIndex);
      case 0xF1: return next(versions, versionIndex);
      case 0xF5: return next(states, stateIndex);
      default: assert(false); return 0xFF;
    }
  }
  void verifySafeExit() const {
    assert(!selected && !active && !resetPins && starts == ends && isolationCalls > 0);
    for (const auto& bytes : transactions) {
      // Check command position, not arbitrary data bytes; no RX/TX/writes.
      if (bytes.empty()) continue;
      if (bytes.front() == 0x30) { assert(bytes.size() == 1); continue; }
      assert(bytes.front() == 0xF0 || bytes.front() == 0xF1 || bytes.front() == 0xF5);
      assert(bytes.size() == 2 && bytes.back() == 0);
    }
  }
};

int count = 0;
void check(const char* name, FakeHal& hal, Diagnostics::Error expected) {
  const uint32_t started = hal.clock;
  Diagnostics::Radio<FakeHal> radio(hal);
  const auto result = radio.run();
  assert(result.error == expected);
  assert(result.ok() == (expected == Diagnostics::Error::kNone));
  assert(static_cast<uint32_t>(hal.clock - started) < 30000);
  hal.verifySafeExit();
  std::cout << "PASS " << ++count << ": " << name << '\n';
}

int main() {
  using E = Diagnostics::Error;
  FakeHal good;
  check("documented ID and stable IDLE", good, E::kNone);
  assert(good.transactions.size() == 9);
  assert(good.partIndex == 1 && good.versionIndex == 1 && good.stateIndex == 1);
  check("repeat run safely re-isolates", good, E::kNone);
  assert(good.isolationCalls == 2);
  FakeHal low; low.parts = {0}; low.versions = {0};
  check("stuck-low bus rejected", low, E::kUnreviewedVersion);
  FakeHal high; high.parts = {0xFF}; high.versions = {0xFF};
  check("all-ones response rejected", high, E::kUnexpectedPart);
  FakeHal wrong; wrong.parts = {0x01};
  check("wrong part rejected", wrong, E::kUnexpectedPart);
  FakeHal old; old.versions = {0x04};
  check("older version held for review", old, E::kUnreviewedVersion);
  FakeHal unstable; unstable.versions = {0x14, 0x15};
  check("inconsistent version rejected", unstable, E::kUnstableIdentity);
  FakeHal unstablePart; unstablePart.parts = {0, 0, 1};
  check("third identity read mismatch rejected", unstablePart, E::kUnstableIdentity);
  FakeHal resetTimeout; resetTimeout.blockedTransaction = 1;
  check("SO stuck high before SRES", resetTimeout, E::kResetTimeout);
  assert(resetTimeout.transactions.front().empty());
  FakeHal afterReset; afterReset.blockAfterReset = true;
  check("SO stuck high after SRES", afterReset, E::kResetTimeout);
  FakeHal readTimeout; readTimeout.blockedTransaction = 3;
  check("status read readiness timeout", readTimeout, E::kReadTimeout);
  FakeHal stateTimeout; stateTimeout.blockedTransaction = 8;
  check("state read readiness timeout", stateTimeout, E::kReadTimeout);
  FakeHal notIdle; notIdle.states = {0x13};
  check("non-IDLE state times out", notIdle, E::kIdleTimeout);
  FakeHal reserved; reserved.states = {0xE1};
  check("reserved state bits rejected", reserved, E::kIdleTimeout);
  FakeHal transition; transition.states = {1, 0, 1, 1};
  check("requires two consecutive IDLE reads", transition, E::kNone);
  assert(transition.stateIndex == 4);
  FakeHal wrap; wrap.clock = UINT32_MAX - 100; wrap.blockedTransaction = 2;
  check("readiness deadline across micros wrap", wrap, E::kReadTimeout);
  FakeHal idleWrap; idleWrap.clock = UINT32_MAX - 200; idleWrap.states = {0};
  check("IDLE deadline across micros wrap", idleWrap, E::kIdleTimeout);
  std::cout << count << " fault-injection scenarios passed; no hardware exercised.\n";
}
