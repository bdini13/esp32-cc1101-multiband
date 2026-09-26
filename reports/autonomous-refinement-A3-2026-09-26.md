# A3 autonomous layout refinement — 2026-09-26

The remaining crystal placement failure was resolved in the routed candidate,
without weakening its 3.5 mm limit. No part, pin assignment, RF filter value,
firmware operating mode or licensing term changed. No board was ordered.

## What changed

Y1 moved to (50.2,23.23) mm and -37.5 degrees. C31/C32 moved outward;
clock, ground, power and nearby digital traces were rebuilt. Both clocks
remain top-side and via-free. The earlier board is preserved in
`hardware/routing/A3-before-crystal-refinement.kicad_pcb`, with a source-hash
guard in the refinement script. The main placement/critical-route files remain
upstream seeds; the final routed candidate is the current layout authority.

| Metric | Before | Refined candidate |
|---|---:|---:|
| U2.8 to Y1.1 straight-line distance | 2.195 mm | 3.468 mm |
| U2.10 to Y1.3 straight-line distance | 4.478 mm | 3.479 mm |
| Q1 routed pin-center to crystal-center length | 2.538 mm | 4.299 mm |
| Q2 routed pin-center to crystal-center length | 6.887 mm | 3.994 mm |
| Longest clock route | 6.887 mm | 4.299 mm |
| Artifact checks | 179/180 | 180/180 |
| Added route screens | 4/6 (retrospective) | 6/6 |

This tradeoff lengthens Q1 while reducing Q2 and the total clock-route length.
The near-diagonal crystal is deliberate, not an assembly rotation error; the
assembler must honor its actual angle. Existing courtyard and clearance rules
were retained. Crystal load values remain starting values, not a measured tune.

## New checks beyond native DRC

TI advises keeping sharp-edged digital routing away from the oscillator input
and from beneath the Q1 crystal pad. The new screen projects digital traces
and vias from **every copper layer** onto the full Q1 rectangular pad envelope;
it conservatively ignores rounded corners and does not waive the screen
because a ground plane lies between layers.
[CC1101 datasheet](https://www.ti.com/lit/ds/symlink/cc1101.pdf).

The first trial caught CSn/GDO2 under this envelope. They and a nearby RF
selector route were moved. Minimum projected clearance is now **0.2079 mm**,
against a project screen of 0.20 mm. New tests deliberately inject a bottom
trace under the pad and verify detection. This is a geometry screen, not a
coupling/noise simulation. Other oscillator/RF review and bench tests remain.

The route model also follows actual trace/via connectivity to estimate DC
resistance. It assumes copper at 80 C, 80% of target layer copper thickness,
and 20 um via plating; each layer transition is charged a full 1.6 mm barrel.
These are explicit modeling assumptions, not supplier guarantees.

| Copper path | Independent screening load | Modeled drop |
|---|---:|---:|
| Buck output L1.2 → ESP32 supply | 0.5 A | 7.423 mV |
| USB A4 → fuse | 0.5 A | 14.331 mV |
| USB A9 → fuse | 0.5 A | 20.464 mV |
| Fuse → main load switch | 0.5 A | 4.667 mV |
| Load switch → buck input | 0.5 A | 2.506 mV |
| RF bead output → output RF switch | 0.1 A | 13.316 mV |

The model omits components, contacts/pad spreading, cable and ground-return
resistance. It follows the least-resistance single path, ignoring parallel
paths. It is not a thermal, ampacity, transient, USB-compliance or RF-noise
analysis. Loads in different rows must not be added and presented as an
approved simultaneous operating mode. See all 14 paths and six project screens
in [the current model](route-margins-A3.json) and the
[retrospective baseline](route-margins-A3-before-crystal-refinement.json).

## Verification and remaining boundary

- Native candidate DRC: **0 violations / 0 unconnected items**.
- Fresh schematic/PCB parity: passes; schematic connectivity is unchanged.
- Artifact audit: **180/180**, now checks the final routed geometry; only the
  two initial-stitching checks explicitly use the placement seed.
- Route screens: **6/6**. Seven new geometry/resistance/fault-injection tests pass.
- Eight preflight tests pass. Fresh preflight reruns route metrics and hashes
  generator/check code plus firmware sources, as well as hardware artifacts.
- Existing 17 diagnostic cases, RF-boot tests and connectivity fault tests
  are rerun; firmware has not been flashed or tested on hardware.

Preflight still requires six unsigned independent/supplier review categories.
Filled/capped C21 and U5 vias remain necessary. Matching, oscillator startup,
frequency accuracy, USB sequencing, thermal behavior and RF performance are
unmeasured. No human review was marked approved by the agent, and no
fabrication package or purchase order was created.
