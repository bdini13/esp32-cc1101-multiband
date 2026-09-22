# A2 design updates — 2026-09-22

Disposition: **NOT ORDERABLE.** This pass fixes placement/part issues and adds
a separate, partially routed candidate. It does not complete the PCB or validate
four-band RF performance. No purchase, upload to a fabricator or TX test occurred.

## Implemented

- J1 changed from GCT USB4105 to HRO TYPE-C-31-M-12, with the matching KiCad
  footprint at (3.65, 18) mm, -90 degrees. The USB opening stays at the left
  edge; vertical standard SMA remains at the opposite end. Reviewed the base
  M-12 manufacturer drawing, not the alternate A/B/C variants. Original four
  hole-clearance errors are gone with the original 0.25 mm rule retained.
- D1 placement adjusted to clear the programming IC and connector escape area.
- Y1's old TXC 9HT11 footprint was inappropriate for the proposed 26 MHz
  crystal. Replaced it with exact Abracon ABM8-26.000MHZ-10-1-U-T and a custom
  four-pad footprint from the manufacturer's drawing. Updated symbol, ground
  pads, placement and BOM together. C31/C32 now 15 pF C0G, calculated from
  CL=10 pF and TI's typical 2.5 pF parasitics; actual trim remains unverified.
- Added POWER/RF_LOCAL/ANALOG_LOCAL/USB net classes and a 0.15 mm minimum trace
  width for fine-pitch escapes. No error exclusions or hole-clearance waivers.
- Added constrained local DSN export/import and routing audits. RF, analog and
  USB tracks remain top-only; In1.Cu is reserved for ground. Candidate carries
  its own copy of project rules so its native DRC is comparable.
- Proposed exact part numbers now cover 63 populated positions, including
  crystal, USB/SMA, fuse, bead, RF inductors and many resistors/bypass capacitors.
- Added a documented fabricator stackup target, power screening and bench/RF
  acceptance procedures in `docs/05-A2-routing-and-validation.md`.
- Refreshed top/3D placement images and schematic SVG. Missing connector/RF 3D
  bodies mean renders cannot establish connector clearance or antenna fit.

The PDF inspection workflow informed the USB and crystal land-pattern changes.
It did not constitute an independent engineering sign-off. Manufacturer sources
and calculations are linked in the validation document.

## Verification evidence

| Artifact/check | Result |
|---|---|
| `erc-A2.json` | 0 schematic ERC violations |
| `drc-A2-placement.json` | 0 violations; 217 unconnected items |
| `design-audit.json` | 115/115 checks pass; 107 footprints |
| Main placement board | 0 signal/power track segments; 8 thermal vias |
| `drc-A2-routing-candidate.json` | 0 violations; 23 unconnected items |
| `routing-audit-A2.json` | 735 track segments, 123 vias; 0 checked layer violations |
| Candidate power-width review | 35 segments below 0.40 mm target; unapproved |
| BOM | 103 footprint rows; 81 populated; 18 populated positions still unselected |

The two unconnected counts describe different files. The main board remains a
reproducible checked placement, while `hardware/A2-routing-candidate.kicad_pcb`
contains exploratory routing. It has not been promoted. Router completion,
router-specific DRC counts and native KiCad results are not interchangeable.
Use the native reports above; the local routing run stopped at its time limit.

Candidate unresolved connections include switch power/ground/control pads,
several RF paths, crystal Q2, CC1101 CSn, USB D+ and a ground-zone island.
Do not infer functional connectivity from the 0-violation clearance result.

## Remaining order blockers

1. Complete routing and manually review RF, crystal, USB, power and return paths.
   Calculate final impedance geometry against the confirmed manufacturing stackup.
   Remove inappropriate power neck-downs and any digital intrusion into RF/clock
   areas. Refill ground, resolve all airwires and repeat DRC/visual review.
2. Select C1, C2, C5, C10, C11, C20, C31, C32, C40, C41, C42, C44, C45, C47,
   C49, D3, D4 and R6. Verify DC-bias/tolerance, lifecycle, stock and assembly
   sourcing for every populated item. Existing proposed parts are not procurement
   approvals and five-unit quantities do not include spares.
3. Resolve supply capacity and USB current behavior. At the screening assumptions,
   a sustained 500 mA load gives approximately 149 C LDO junction temperature;
   there is inadequate margin. The actual PCB thermal performance is unmeasured.
4. Obtain an independent RF/layout review before ordering prototypes. The
   low-band switch performance and shared 868/915 matching need measurement on
   prototypes; budget for tuning/rework. No claim of equivalent performance to
   the Amazon module has been established.
5. Complete exact SMA drawing/physical-fit and assembly-orientation checks.

Before A2 edits, A1 hardware/docs/README were archived at
`reports/checkpoints/A1-hardware-before-routing.tar.gz`. Historical A1 reports
and images were retained. Current editable design sources are the generators;
regenerating placement overwrites manual routing, so preserve routing separately.
