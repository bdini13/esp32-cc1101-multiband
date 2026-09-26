#include "rf_boot.h"
#include <cassert>
#include <cstdio>
#include <utility>
#include <vector>
struct FakePins {
  std::vector<std::pair<char,uint8_t>> calls;
  void high(uint8_t p) {calls.emplace_back('H',p);}
  void output(uint8_t p) {calls.emplace_back('O',p);}
};
int main() {
  FakePins hal;
  RfBoot::begin(hal);
  const uint8_t expected[]={4,32,33,16,17};
  assert(hal.calls.size()==10);
  for(unsigned i=0;i<5;++i) {
    assert(hal.calls[i].first=='H' && hal.calls[i].second==expected[i]);
    assert(hal.calls[i+5].first=='O' && hal.calls[i+5].second==expected[i]);
  }
  hal.calls.clear();RfBoot::isolate(hal);
  assert(hal.calls.size()==5);
  for(unsigned i=0;i<5;++i)
    assert(hal.calls[i].first=='H' && hal.calls[i].second==expected[i]);
  std::puts("PASS: A3 RF boot pin map, preload-before-output, disable-first and re-isolation.");
}
