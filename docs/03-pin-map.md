# A3 ESP32 pin map

| GPIO | Function |
|---:|---|
| 0 | BOOT / automatic programming; strapping pin |
| 1 / 3 | UART TX / RX through powered-off-protected buffer |
| 4 | RF_DISABLE, V3 of both switches; HIGH disables |
| 16 / 17 | RF_OUT0 / RF_OUT1, U4 V1 / V2 |
| 18 / 19 / 23 | CC1101 SCLK / MISO / MOSI |
| 21 | CC1101 CSn |
| 25 | Active-high status LED |
| 26 / 27 | CC1101 GDO0 / GDO2 |
| 32 / 33 | RF_SW0 / RF_SW1, U3 V1 / V2 |

GPIO16/17 exposed at optional J3 are RF debug taps, **not spare outputs**.
GPIO13/14/22 and input-only GPIO34/35 are expansion candidates; do not
drive the radio-control taps externally. GPIO6–11 belong to internal flash.
GPIO2/5/12/15 remain unused strapping pins; GPIO4 is not a strapping pin.

## Switch states

| Mode | GPIO4 | GPIO32,33 | GPIO16,17 |
|---|---:|---|---|
| Isolated boot | 1 | 1,1 | 1,1 |
| 315 MHz | 0 | 1,0 | 1,1 |
| 433 MHz | 0 | 0,1 | 0,1 |
| 868/915 MHz | 0 | 1,1 | 1,0 |

Five 10 kohm pullups establish HIGH before firmware. The startup helper
preloads all outputs HIGH before enabling their drivers. **000 selects RF4;
it does not isolate.** Never use A2's old switch helper on this board.

Future selection: require stable CC1101 IDLE, raise GPIO4, wait at least
50 us, set both independent selector pairs, wait at least 50 us, lower
GPIO4, configure/calibrate the radio and verify completion. Respect the
switch's maximum switching rate. Receive/transmit and this selection sequence
are not implemented in the current diagnostic-only firmware.
