# Roadmap

An engineering plan, not a shipping schedule. An AI check or clean DRC alone
does not close a phase; all acceptance gates require human review.

## 1. Capture and document — substantially complete

- [x] ESP32-WROOM-32E-N8 + CC1101 architecture and GPIO map.
- [x] Software-selected three-path RF network for four target bands.
- [x] Schematic, placement, local footprints and draft BOM.
- [x] Safe-default bring-up firmware, renders and machine-readable checks.
- [x] Public documentation and AI disclosure prepared.

## 2. Pre-order engineering — in progress

- [x] Finish candidate connectivity: A3 native DRC has zero violations/unconnected items.
- [ ] Manually review RF, oscillator, USB pair, power and ground returns.
- [x] Replace the thermally constrained LDO with a buck and explicitly route main power.
- [ ] Approve branch-current/voltage-drop and buck load-step/thermal testing.
- [ ] Confirm USB current availability and startup behavior.
- [ ] Confirm fabricator stackup and 50-ohm RF / 90-ohm USB geometry.
- [x] Propose exact parts for all populated BOM positions.
- [ ] Verify current stock, authorized sourcing and assembler substitutions.
- [ ] Review the longer crystal connection; measure startup and frequency on prototypes.
- [ ] Confirm filled/capped via processing at C21 and the USB bridge exposed pad.
- [ ] Review connectors, solder/paste, RF pin mapping and assembly orientation.
- [ ] Obtain independent electrical/RF review; repeat ERC/DRC/audits.

Exit: a routed, reviewed prototype order candidate with zero unexplained errors,
all connections complete, documented residual risks and a validation plan.
This is not the same as production-ready hardware.

## 3. Five engineering prototypes — not ordered

- [ ] Produce reviewed Gerbers, drills, BOM and pick-and-place outputs.
- [ ] Check supplier DFM feedback, placement preview and substitutions.
- [ ] Approve a quote/order separately; this roadmap does not authorize purchase.
- [ ] Receive, inspect, photograph and record revision IDs for five units.

## 4. Bench and RF qualification — not started

- [ ] Current-limited first power, rails, boot/reset and USB checks.
- [ ] SPI identity verification, thermal and transient-load measurements.
- [ ] Crystal startup/frequency accuracy over intended operating conditions.
- [ ] VNA measurements and tuning at 315, 433, 868 and 915 MHz.
- [ ] Characterize low-band switch loss/isolation and shared upper-band matching.
- [ ] Conducted sensitivity, output spectrum and harmonics with proper equipment.
- [ ] Record failures/rework; make Rev B if acceptance limits are not met.

Exit: measured results and an honest operating envelope, not assumed range
claims or equivalence to another module.

## 5. Firmware and usability — planned

- [x] Repeated ID validation, timeouts and 17 host fault-injection tests.
- [ ] Bench-validate diagnostics and develop repeatable factory tests.
- [ ] Receive-first frequency/modem profiles and a documented control interface.
- [ ] Verified IDLE/isolate/select/reconfigure sequence for band changes.
- [ ] Deliberately selected region/power profiles before transmit features.
- [ ] Evaluate optional Wi-Fi/Bluetooth control and logging, subject to testing.

## 6. Possible sale — undecided

- [ ] Choose markets, use cases and supported antenna combinations.
- [ ] Obtain commercial licensing/provenance review of third-party inputs.
- [ ] Determine applicable RF/EMC/safety requirements with qualified help.
- [ ] Resolve enclosure, labeling, test fixtures and production QA.
- [ ] Confirm sourcing, costs, support/warranty and manufacturing yield.
- [ ] Decide whether to sell and under what business/licensing model.

Publication does not constitute a sales, compliance or production decision.
