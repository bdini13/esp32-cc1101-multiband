# Bring-up firmware

**A3 hardware only. Do not flash this switch mapping onto A2.** Before fitting
J4, configure/read back the CP2102N's 500 mA bus-powered descriptor with the
shunt removed. Follow the [power setup](../../docs/06-A3-prototype-engineering.md).

This PlatformIO/Arduino program verifies the initial digital hardware without
transmitting RF. It:

1. Configures both RF switches in their all-paths-isolated safe state.
2. Initializes the SPI bus at 1 MHz.
3. Resets the CC1101.
4. Reads PARTNUM and VERSION three times and rejects inconsistent responses.
5. Requires PARTNUM=0x00 and the reviewed VERSION=0x14.
6. Requires two consecutive MARCSTATE=0x01 (IDLE) reads.
7. Lights the status LED only after all these digital checks pass.

It intentionally does not load a modem profile or issue a transmit command.
Full register profiles will be added only after the PCB and regional operating
requirements are verified.

## Diagnostic behavior

Readiness waits have a 5 ms timeout; the IDLE polling window is 20 ms (a final
read may take up to another 5 ms). SPI chip select is released and transactions
are closed on every success/failure path. The manual reset preamble detaches
SPI, sets SCLK high/SI low, pulses CSn, holds it high for 50 us, and restores
SPI mode 0 before SRES. See TI's [CC1101 datasheet](https://www.ti.com/lit/ds/symlink/cc1101.pdf),
sections 19.1.2 and 29.3. Check actual timing on a logic analyzer during bring-up.

Serial output at 115200 baud includes `RESULT`, `PARTNUM`, `VERSION`, and
`MARCSTATE`. Failure strings distinguish readiness timeouts, unstable identity,
unexpected part, unreviewed version and an IDLE timeout. A value of `0xFF` may
mean that a field was never read; use `RESULT`, not the raw fields alone.
Other versions, including older 0x04 parts, require review; rejection does not
prove a counterfeit. The old all-zero-bus false-positive has been removed.

The unused, unguarded path-selection helper was removed. There is no command
interface that can select an RF branch, enter RX/TX, or write a modem profile.
Five external 10 kohm pullups remain necessary during reset and before code runs.
GPIO4 is the shared RF disable; GPIO32/33 select U3 and GPIO16/17 select U4.
The startup helper preloads all five outputs HIGH before enabling their output
drivers. PE42442 state 111 is isolated; 000 is not. Additional host tests check
the exact A3 pin map, output preload ordering and re-isolation ordering.
Passing diagnostics does not establish sensitivity, crystal accuracy, RF
isolation, emissions compliance or hardware reliability.

## Reproduce software checks

```sh
python3 tools/test_firmware.py
pio run -d firmware/bringup
```

Run from the repository root. The host tests require Python 3 and a C++11
compiler (`CXX` may override `c++`); they compile the same diagnostic header used
by the ESP32. Seventeen scenarios cover normal/repeated operation, stuck buses,
identity mismatch, reset/read timeouts, unstable/non-IDLE states and timer wrap.
They check SPI command boundaries and transaction cleanup, not actual electrical
timing or the Arduino peripheral driver. No board is flashed by these commands.

The tested PlatformIO platform is pinned to `espressif32@7.1.3`; resolved
framework/tool versions are recorded in the [checkpoint report](../../reports/overnight-checkpoint-2026-09-23.md).
This is not a complete dependency lockfile.
