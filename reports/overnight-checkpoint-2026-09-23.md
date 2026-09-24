# A2 overnight checkpoint — 2026-09-23

Status: saved engineering progress, **not ready for an order**. No PCB topology,
placement or routing was changed in this checkpoint. A2 images remain current.

## Completed

- Replaced the firmware's permissive identity check, which accepted an all-zero
  SPI response, with repeated exact identity checks and stable IDLE detection.
- Added bounded waits, distinct failure reporting, transaction cleanup, the TI
  manual-reset preamble, and a restricted API with no RX/TX/path-selection entry.
- Added 17 host fault-injection scenarios and six pre-order-check unit tests.
  All pass. Host tests do not validate GPIO waveforms or physical hardware.
- Successfully built the ESP32 firmware: 21,576 bytes RAM, 275,569 bytes flash.
- Re-ran the design audit: 115/115 pass. Fresh native KiCad checks: ERC zero
  violations; candidate DRC zero violations and **23 unconnected items**.
- Added a fresh-check preflight command, explicit pending review records and
  input SHA-256 fingerprints. It reports **BLOCKED**, as intended.
- Corrected the pin-map claim that GPIO4 was a boot-strapping GPIO.

Build environment: PlatformIO espressif32 7.1.3, Arduino framework
4.20017.260907+sha.dcc1105b, Xtensa toolchain 8.4.0+2021r2-patch5,
esptool package 2.41100.260830. Platform version pinned; no device flashed.

## Power replacement screening

AP63203WU-7 is a candidate, **not substituted into A2**. It is a fixed-3.3 V
buck with a 3.8–32 V input range. The manufacturer's starting circuit uses a
3.9 uH inductor, 10 uF input capacitance, two 22 uF output capacitors and a
100 nF bootstrap capacitor. TSOT26 pins are FB1, EN2, VIN3, GND4, SW5, BST6.
Its switching behavior requires a new hot-loop layout, shielded-inductor
selection, capacitor derating, noise review and transient testing. It does not
solve USB input-current permission. The PDF skill guided visual inspection of
manufacturer pin/ordering drawings before deciding against an unverified swap.
[Diodes datasheet](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf).

## RF replacement screening

PE42430 is another candidate, **not a drop-in replacement**. Its specified RF
range extends down to 100 MHz, but it has three control inputs and derives
power from them; control-high minimum is 3.0 V. That is not a verified direct
ESP32 GPIO interface. Its pinout, ground paddle, startup isolation, logic drive
margin and routing would all need redesign/review. Retaining the existing
switch in the saved draft does not resolve its low-band performance risk.
Visual inspection of the manufacturer's pinout and operating-range table
prevented treating it as an interchangeable eight-pin part.
[pSemi datasheet](https://psemi.com/pdf/datasheets/pe42430ds.pdf).

## Reproduce the order-blocker check

```sh
python3 tools/test_preflight.py
python3 tools/preflight.py --kicad-cli kicad-cli --output reports/preflight-A2.json
```

The last command intentionally exits **2** when blocked; 1 indicates execution
failure. It runs new ERC and candidate DRC, then checks BOM selection and six
review records. Even with all gates closed, it only reports that separate owner
order approval is needed. It cannot place orders or export fabrication files.
The candidate has a separate basename, so schematic parity is not automatically
checked by this command; independent connectivity review remains mandatory.
Review records are declarations, not authenticated engineering sign-offs.

## Remaining before the five-board prototype order

1. Choose/review power and low-band RF solutions; then revise the circuit/layout.
2. Finish critical routing and the 23 connections; review 35 narrow power
   segments, USB pair geometry, RF impedance and return paths.
3. Select the remaining 18 populated BOM positions and approve sourcing/assembly.
4. Complete mechanical and independent electrical/RF review, then obtain a quote
   and separate purchase approval. Bench/RF validation follows the prototype build.

See the [machine-readable fresh-check snapshot](preflight-A2.json) and
[roadmap](../ROADMAP.md). There are still no physical measurements or built boards.
