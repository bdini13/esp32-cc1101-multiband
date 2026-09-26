#pragma once
#include <stdint.h>

// A3 PE42442 wiring ONLY. Never use this reset policy on A2 BGS13SN8.
namespace RfBoot {
constexpr uint8_t disable=4, inputV1=32, inputV2=33, outputV1=16, outputV2=17;
template<class Hal> void isolate(Hal& hal) {
  hal.high(disable); // V3 first; 111 is isolated, 000 is NOT isolated.
  hal.high(inputV1); hal.high(inputV2);
  hal.high(outputV1); hal.high(outputV2);
}
template<class Hal> void begin(Hal& hal) {
  isolate(hal); // preload all latches before enabling any output driver
  hal.output(disable); hal.output(inputV1); hal.output(inputV2);
  hal.output(outputV1); hal.output(outputV2);
}
}
