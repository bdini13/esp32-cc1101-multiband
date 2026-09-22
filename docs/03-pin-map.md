# ESP32 Pin Map

## Assigned pins

| ESP32 GPIO | Direction | Function | Boot-sensitive? |
|---:|---|---|---|
| 0 | Input | BOOT button / auto-program | Yes; required |
| 1 | Output | UART0 TX to CP2102N | No |
| 3 | Input | UART0 RX from CP2102N | No |
| 18 | Output | CC1101 SPI SCLK | No |
| 19 | Input | CC1101 SPI MISO/SO | No |
| 21 | Output | CC1101 CSn | No |
| 23 | Output | CC1101 SPI MOSI/SI | No |
| 25 | Output | Status LED, active high | No |
| 26 | Input | CC1101 GDO0 interrupt | No |
| 27 | Input | CC1101 GDO2 interrupt | No |
| 32 | Output | RF_SW0, pulldown | No |
| 33 | Output | RF_SW1, pulldown | No |

## Expansion header candidates

| ESP32 GPIO | Capability/constraint |
|---:|---|
| 13 | General purpose; avoid forcing during boot until reviewed |
| 14 | General purpose; JTAG clock default function |
| 16 | General purpose |
| 17 | General purpose |
| 22 | General purpose / convenient I2C SCL |
| 34 | Input only; no internal pull resistor |
| 35 | Input only; no internal pull resistor |

GPIO2, GPIO4, GPIO5, GPIO12, and GPIO15 remain unused on Rev A because they are
strapping pins and provide little benefit here. GPIO6 through GPIO11 are used
internally by the WROOM module flash and are unavailable.

## RF selection sequence

```text
CC1101 SIDLE
wait for MARCSTATE == IDLE
RF_SW0/RF_SW1 = target truth-table value
wait >= 10 us
write target-band register profile
CC1101 SCAL
wait for calibration completion
enter RX only when requested
```

