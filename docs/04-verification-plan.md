# Rev A Verification Plan

No manufacturing order should be placed until all pre-order gates are checked.

## A3 current checkpoint — 2026-09-26

The routed A3 candidate has zero native DRC violations and zero unconnected
items. See [A3 engineering decisions and bench acceptance](06-A3-prototype-engineering.md)
and [fresh preflight](../reports/preflight-A3.json). The refined crystal layout
now passes the unchanged placement target; all 180 artifact checks and six
route screens pass. See the [refinement evidence](../reports/autonomous-refinement-A3-2026-09-26.md).
Six independent/supplier review categories remain pending. No physical tests
have occurred and no order is authorized by these reports.

## A2 historical checkpoint — 2026-09-22

- [x] Replace the incompatible crystal placeholder with an exact four-pad
  26 MHz part, manufacturer land pattern and documented initial load calculation.
- [x] Resolve the four USB hole-clearance errors by selecting HRO TYPE-C-31-M-12.
- [x] Fresh main-design ERC: 0 violations; placement DRC: 0 violations,
  217 unconnected items; targeted audit: 115/115 pass.
- [x] Produce a separate partial-routing candidate and run native DRC:
  0 violations, 23 unconnected items. It is NOT the approved main layout.
- [x] Add proposed exact parts for 63 of 81 populated BOM positions.
- [ ] Finish and review routing, including 35 candidate power segments narrower
  than the 0.40 mm target, USB coupling, RF geometry and return paths.
- [ ] Select the remaining 18 populated parts and verify sourcing for all parts.
- [ ] Close thermal, USB-power and low-band RF-switch acceptance gates.

See `05-A2-routing-and-validation.md` for the stackup target and tests.

## A1 historical correction checkpoint — 2026-09-22

- [x] Correct DGUARD, balun top-view pad mapping, LED polarity and D2 package.
- [x] Correct CP2102N supply/sense circuit and add local bypass capacitors.
- [x] Correct USB connector orientation and actual ESP32 antenna overhang.
- [x] Replace regulator package and add initial thermal/ground copper.
- [x] Run fresh ERC (0 violations) and targeted artifact audit (107/107 pass).
- [x] Generate a BOM inventory covering all 103 schematic footprints.
- [ ] Resolve J1's four 0.1944 mm hole-clearance errors against the chosen fab.
- [ ] Complete power/signal routing (215 unconnected items remain).
- [ ] Approve every exact BOM part; verify load profile, thermal behavior,
      USB current availability and low-band switch performance.

The checked corrections do not close the independent pre-order gates below.

## Pre-order schematic gates

- [ ] Confirm every ESP32-WROOM-32E pin against the current datasheet.
- [ ] Confirm EN and GPIO0 timing against the Espressif reference circuit.
- [ ] Confirm CP2102N power configuration and DTR/RTS polarity.
- [ ] Confirm independent 5.1 kohm USB-C CC resistors.
- [ ] Confirm USB ESD device orientation and pinout.
- [ ] Confirm regulator stability, capacitor ESR requirements, and worst-case
      thermal dissipation.
- [ ] Confirm all CC1101 supply pins and exposed pad connections.
- [ ] Confirm CC1101 crystal load calculation using the selected crystal.
- [ ] Confirm broadband balun footprint and orientation against manufacturer
      land pattern.
- [ ] Confirm both SP3T switch pinouts, logic thresholds, truth table, and
      power-up state.
- [ ] Independently trace all three RF branches from CC1101 to SMA.
- [ ] Confirm SMA gender and center-pin footprint with the exact ordered part.
- [ ] Run KiCad ERC with zero unexplained errors.

## Pre-order PCB gates

- [ ] Obtain the board house's actual four-layer stackup.
- [ ] Calculate 50-ohm grounded coplanar-waveguide geometry for that stackup.
- [ ] Confirm ESP32 antenna keepout on all layers.
- [ ] Confirm no digital trace crosses the CC1101/RF region.
- [ ] Review return-current paths for USB, SPI, crystal, and RF controls.
- [ ] Confirm thermal copper for the 3.3 V regulator.
- [ ] Confirm CC1101 exposed-pad paste aperture and ground vias.
- [ ] Check RF component orientation visually against the reference design.
- [ ] Run DRC with zero unexplained errors.
- [ ] Render front/back/3D views and perform a mechanical review.
- [ ] Print the board at 1:1 scale and physically compare USB and SMA parts.
- [ ] Verify all BOM parts are orderable and not end-of-life.
- [ ] Verify all assembly-side orientations in the pick-and-place file.

## First power-up

- [ ] Power from a current-limited 5 V bench supply before connecting USB data.
- [ ] Confirm no short between 5 V, 3.3 V, and GND.
- [ ] Confirm 3.3 V regulation and idle current.
- [ ] Confirm EN rises cleanly and the ESP32 produces UART boot output.
- [ ] Flash `firmware/bringup` and verify LEDs and switch truth table.
- [ ] Read plausible CC1101 PARTNUM and VERSION status registers.
- [ ] Verify SPI waveform and chip-ready timing with a logic analyzer.
- [ ] Confirm the CC1101 remains idle during RF path changes.

## RF validation

- [ ] Use a 50-ohm termination whenever an antenna is not installed.
- [ ] Measure each branch with a VNA or arrange measurement through an RF lab.
- [ ] Tune DNP matching footprints as required on the assembled PCB.
- [ ] Measure conducted output power and harmonics into a suitable attenuator.
- [ ] Test receive sensitivity with a known signal source where possible.
- [ ] Perform over-the-air range tests using the correct antenna for each band.
- [ ] Confirm firmware power settings remain inside the applicable regional
      rules before any non-shielded transmit testing.

## Rev A disposition

- [ ] Record every rework and measurement.
- [ ] Promote unchanged design to Rev B only if all critical checks pass.
- [ ] Otherwise update schematic, layout, BOM, and test plan before reordering.
