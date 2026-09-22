# Rev A1 correction record — 2026-09-22

Disposition: **review corrections implemented; still NOT FOR MANUFACTURE.**

The schematic, generated netlists, PCB, custom library, BOM inventory and renders
have been updated together. The previous review is retained unchanged as the
historical defect record. No Gerbers, purchase order or assembly release was made.

## Review findings and changes

| Finding | Implemented correction | Remaining qualification |
|---|---|---|
| CC1101 DGUARD grounded | U2.18 now +3V3_RF; dedicated C26 bypass | Power/ground routing and first-power measurements |
| Mirrored balun footprint | Top-view rows now 3–2–1 / 4–5–6; upper-right pin-1 mark | Physical part/tape orientation check before assembly |
| USB faces inward | J1 at (3.675,18) mm, −90°; recommended board-edge reference at x=0 | Connector-specific hole clearance and mechanical fit |
| CP2102N VBUS/power | 22.1k/47.5k sense divider; VIO/VDD/VREGIN on common external 3.3 V; 1k reset pull-up; local bypass pairs | Route and verify startup, USB enumeration and auto-reset |
| Reversed LEDs | D3/D4 pin 1 cathode to GND; pin 2 anode to resistor node | Assembly polarity and actual LED part selection |
| D2 package mismatch | PESD5V0S1UL now SOD-882, with explicit cathode/anode symbol | Confirm protection clamping and exact assembly package |
| Remote/missing decoupling | Repositioned C21–C25, crystal and bias resistor; added C26, C60/C61 and ESP32 C11/C12 | Short routed loops and ground stitching still required |
| ESP32 antenna over PCB | Module moved to y=6.30 mm; antenna tip y=−6.45 mm | Enclosure, nearby metal and RF testing |
| Small regulator thermal risk | AP7361C-33E-13 in SOT-223; grounded tab; preliminary heat spreading and eight vias | Load profile and measured thermal validation remain open |

Functional CC1101, BGS13SN8 and balun symbols replace generic connector symbols.
Pin types now provide more useful ERC, but ERC alone cannot identify every wrong
net assignment. The new `hardware/audit_design.py` checks generated artifacts for
the specific review regressions, rather than assuming the generator is correct.

Pin/source basis: [TI CC1101](https://www.ti.com/lit/ds/symlink/cc1101.pdf),
[Silicon Labs CP2102N](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf),
[TTM balun](https://cdn.ttm.com/repository/products/wireless-xinger/balun-transformers/B0310J50100AHF/B0310J50100AHF.pdf),
[Nexperia D2](https://assets.nexperia.com/documents/data-sheet/PESD5V0S1UL.pdf).

## Placement and copper

- Base board remains 90 × 36 mm, four copper layers, nominal thickness 1.6 mm.
- Vertical SMA footprint remains at the end opposite USB-C. Exact SMA part
  approval is still pending. The installed matching 3D model is missing, so
  the renders show its lands, not the connector body. Custom RF package models
  are also absent; these renders are not a complete clearance certification.
- ESP32 overhang adds 6.45 mm to the base-board width before enclosure clearance.
  Its feed lies approximately 0.26 mm outside the board edge; keep the external
  antenna region clear of enclosure metal and wiring.
- U2 supply-pad to assigned bypass-pad distances are now 1.33–2.56 mm.
  Switch bypass distances are 1.68/1.26 mm. Crystal connections measure
  2.13/2.22 mm between pad centers. These are straight-line placement distances,
  **not** achieved routed lengths or evidence of RF performance.
- Initial In1.Cu/B.Cu GND zones and a front-side regulator heat-spreading zone
  are filled. Eight 0.60 mm diameter / 0.30 mm drill ground vias connect the
  regulator region. Final ground stitching, RF return paths, power routing,
  impedance geometry and layer-stackup definition are unfinished.

## Regulator screening — not a certified current limit

AP7361C-33E-13 uses IN/GND/OUT pins 1/2/3 and a grounded tab; the ER variant
has a different pinout. Its SOT-223 datasheet thermal figure is 110 °C/W on the
specified minimum-land test board. Our actual board resistance is unknown.
[Diodes AP7361C datasheet, pin descriptions and thermal information](https://www.diodes.com/datasheet/download/AP7361C.pdf).

Illustrative conservative screening assumes 5.25 V input, 3.267 V output
(−1%), and 40 °C ambient. Ignoring small quiescent losses:

| Continuous load | LDO dissipation | Estimated junction using 110 °C/W |
|---:|---:|---:|
| 300 mA | 0.595 W | 105 °C |
| 500 mA | 0.992 W | 149 °C |

These are calculations, not measurements. They show why even the larger
package does not justify claiming 500 mA continuous or 1 A board capacity.
Use 300 mA only as a provisional design-screening point, not an approved
operating rating. Validate Wi-Fi peaks, radio load, USB source capability,
fuse temperature derating, startup/inrush, capacitor effective capacitance and
worst-case ambient. A DC/DC redesign remains possible if measured load or
thermal margin requires it. No numerical thermal improvement is assumed from
the newly added copper without simulation or measurement.

## Fresh verification

- KiCad 10.0.6 schematic ERC: **0 violations**, `erc-corrected.json`.
- Targeted artifact audit: **107/107 pass**, `design-audit.json`.
- PCB DRC: **4 hole-clearance errors**, all internal to J1, 0.1944 mm actual
  versus configured 0.2500 mm minimum. No clearance rules were relaxed or
  violations excluded to obtain these results.
- **215 unconnected items**, zero routed signal/power tracks, eight standalone
  thermal vias and three board-level filled ground zones. Exposed-pad thermal
  holes embedded in footprints are additional and not counted as those vias.
- No reported pad shorts, ordinary copper-clearance violations, courtyard
  overlaps, edge-clearance violations or silkscreen collisions.
- BOM now covers all **103 schematic footprints**, including ordinary
  resistors/capacitors previously omitted. Four mounting-hole footprints are
  PCB-only mechanical features. DNPs/test pads are explicitly excluded from
  purchasing quantities; five-board counts do not include assembly attrition.
- Bring-up firmware: PlatformIO build succeeded (21,576 bytes RAM;
  274,913 bytes program usage reported). Firmware was not changed or flashed;
  this does not verify physical hardware or radio performance.
- Top/3D placement and schematic SVG exports refreshed and visually inspected.
  Schematic uses net labels; final routed review must trace complete net paths.

## Still required before five-board order

1. Select the fabricator's actual dielectric stackup and approved capabilities;
   resolve the connector clearance errors by supported geometry/rules or a
   verified connector change, then set controlled-impedance routing constraints.
2. Complete all power/signal/RF routing, decoupling ground loops and via fencing;
   rerun full DRC and independently review pin maps and RF topology.
3. Approve exact SMA, crystal, passive/RF series, fuse, ferrite, LEDs and other
   BOM options. The complete inventory is still **not** a procurement-ready BOM.
4. Complete the thermal/current design budget and protection review, and plan
   measured validation on the prototypes.
5. Review the unsupported low-band performance risk and arrange RF test access.
   The [BGS13SN8 datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-bgs13sn8-datasheet-en.pdf)
   does not supply the same tabulated RF guarantees at 315/433 MHz as at
   698 MHz and above. Matching values remain reference starting values.
6. Review fabrication/assembly outputs and physical connector orientation
   before authorizing the initial five assembled prototypes.

After prototypes exist, measure actual thermal/current behavior, characterize
315/433 MHz switch behavior and tune/test all RF branches before claiming
four-band performance. That validation is distinct from authorizing a
controlled prototype fabrication; it cannot be replaced by ERC or this audit.
