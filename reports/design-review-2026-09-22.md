# PCB design review — 2026-09-22

Disposition: **requires schematic and placement corrections before routing or manufacture.**

Reviewed the saved KiCad schematic, XML netlist, PCB pad assignments, generator
sources, BOM, custom RF footprints, and existing placement renders. Reran ERC
and DRC against the saved files without regenerating or modifying the design.
Manufacturer PDF drawings were checked visually where available, including the
balun outline and the previously captured M5Stack reference schematic.

## Confirmed electrical and mechanical defects

### 1. P1 — CC1101 DGUARD is connected to ground

`hardware/generate_schematic.py:287` assigns U2 pin 18 to GND. The saved netlist
and PCB both contain that connection. Pin 18 is DGUARD, a supply input, not a
ground pin. TI's pin table identifies it as a power-supply connection; the
M5Stack reference used for this project connects it to 3.3 V with the other
CC1101 supply pins. Correct to the appropriate RF supply and review all supply
connections and bypass capacitors. Functional radio operation cannot be assumed
with this pin grounded.

Source: [TI CC1101 datasheet, Table 19 and application circuits](https://www.ti.com/lit/ds/symlink/cc1101.pdf).

### 2. P1 — Balun footprint pad numbering is mirrored

`hardware/lib/esp32_cc1101.pretty/TTM_B0310J50100AHF.kicad_mod:24` places
1-2-3 across the upper row and 6-5-4 across the lower row. This copies the
manufacturer's explicitly labeled BOTTOM VIEW into a front-side PCB footprint.
With the same vertical orientation, the top view must have 3-2-1 across the
upper row and 4-5-6 across the lower row. The physical orientation marker must
also agree with the top view. Rotation alone does not correct a reflection.

Rebuild the footprint from a top-view projection and recheck the assembly
orientation. As drawn, the grounded pad 2 and unconnected pad 5 prevent a simple
180-degree rotation of the real part from restoring the intended connections.

Source: [TTM B0310J50100AHF Rev F, page 1 outline and pin table](https://cdn.ttm.com/repository/products/wireless-xinger/balun-transformers/B0310J50100AHF/B0310J50100AHF.pdf).

### 3. P1 — USB-C receptacle faces into the board

`hardware/generate_pcb.py:62` places J1 at (4.8, 18.0), rotation +90 degrees.
The installed KiCad USB4105 footprint marks its intended PCB edge at local
y=+3.675 mm. On the saved board that line is at x=8.475 mm, while the board's
left edge is x=0. The solder tails lie near x=1.12 mm. Thus the mating opening
faces the electronics instead of the outside edge. Rotate and reposition the
connector with its annotated mating edge aligned to the left board edge, then
redo USB protection placement and mechanical clearance.

Evidence: saved PCB geometry and the installed
`Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`
footprint's `PCB Edge` annotation. The previous render approval missed this.

### 4. P1 — CP2102N VBUS sensing bypasses the required divider

`hardware/generate_schematic.py:157` connects U5 pin 8 directly to the protected
5 V rail. Silicon Labs requires a resistor divider or equivalent for this
sense input in both bus-powered and self-powered configurations, including
when VIO is not yet powered. Its reference circuit uses 22.1 kohm above the
sense node and 47.5 kohm to ground. Pin 7 VREGIN is a separate power input;
do not apply the divider to the power input.

The power arrangement also needs a complete bypass and sequencing review:
VIO uses the external 3.3 V supply while VDD uses the internal regulator. C3 is
the only capacitor on VDD, and C4's VIO pad is 7.33 mm from the IC pad. Check
the manufacturer's per-power-pin capacitor requirements and VIO <= VDD limit.

Source: [Silicon Labs CP2102N datasheet, sections 2.1, 2.3 and Table 3.1](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf).

### 5. P2 — Both indicator LEDs are reversed

`hardware/generate_schematic.py:247` and `:255` connect LED pin 1 to the
positive resistor node and pin 2 to ground. The embedded KiCad Device:LED
symbol defines pin 1 as K (cathode) and pin 2 as A (anode). Both LEDs are
therefore reverse-biased in their intended operating state and will not light
normally. Swap the electrical assignments and preserve a consistent assembly
polarity mark.

### 6. P1 — D2's proposed part does not fit its footprint

`hardware/bom-draft.csv:26` selects PESD5V0S1UL, but
`hardware/generate_schematic.py:122` assigns SOD-323. Nexperia specifies
DFN1006-2 / SOD882 for that exact part. Select a matching part/footprint pair.
Also use a symbol that communicates its unidirectional polarity; the current
generic D_TVS symbol has anonymous A1/A2 terminals.

Source: [Nexperia PESD5V0S1UL datasheet, pinning and ordering information](https://assets.nexperia.com/documents/data-sheet/PESD5V0S1UL.pdf).

## Placement and performance risks requiring revision

### 7. P1 — Radio bypass capacitors are remote; switch bypass capacitors are absent

The C21-C25 row in `hardware/generate_pcb.py:102` is arranged above U2 rather
than around its supply pins. For U2 pins 4/9/11/14/15, the nearest capacitor
supply-pad center is respectively 5.53/6.89/6.09/4.62/4.13 mm away. These are
straight-line distances before routing. Y1's pads are about 5.1 mm from the
oscillator pins, and the RBIAS resistor pad is 6.21 mm from its pin.

Neither U3 nor U4 has its own local bypass capacitor. Even C25 is 12.15 mm
from U3 VDD and 21.86 mm from U4 VDD. The captured M5Stack reference includes
one 100 nF capacitor at each switch. Add local switch bypassing and rebuild the
CC1101 placement around short supply, oscillator and ground-return paths.

The differential RF paths also need coordinated orientation: C40/BAL_N is
above C41/BAL_P, while the current balun puts BAL_N below BAL_P. Correcting the
mirrored footprint and arranging these parts together should precede routing.
The RF switches' common/branch pad locations must likewise drive placement.

Source: [TI CC1101 datasheet, sections 7.6 and 7.8](https://www.ti.com/lit/ds/symlink/cc1101.pdf).

### 8. P2 — ESP32 antenna placement does not match the earlier description

`hardware/generate_pcb.py:65` places the module at y=15.5 mm. Its antenna
section lies approximately between y=2.75 and y=8.94 mm, entirely over the
rectangular base PCB. It does not overhang the edge. The footprint keepout
being empty is helpful but does not establish RF performance or satisfy the
stated overhang arrangement. Move the module or design a suitable board cutout.

Source: [Espressif module placement guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html#general-principles-of-pcb-layout-for-modules-positioning-a-module-on-a-base-board).

### 9. P2 — Regulator thermal capability is unproven

U6 is the conventional DBV SOT-23-5 TLV75733P, not the exposed-pad package.
At an illustrative continuous 300 mA load, a 5 V to 3.3 V LDO dissipates
approximately 0.51 W. TI lists 231.1 C/W for DBV on its JEDEC board and
100.8 C/W in the EVM comparison, showing strong layout dependence. These are
screening figures, not predicted temperatures for this unrouted PCB.
Calculate the actual Wi-Fi/radio load profile and thermal margin before
accepting this package. Its 1 A current rating alone does not establish that
the board can dissipate the heat.

Source: [TI TLV757P datasheet, thermal information and power dissipation](https://www.ti.com/lit/ds/symlink/tlv757p.pdf).

## Verification results and limits

- Fresh ERC: 0 violations. U2 and the RF switches use generic connector
  symbols with passive pins, so ERC cannot meaningfully validate their power
  pin functions. Replace them with verified functional symbols.
- Fresh DRC: 4 hole-clearance **errors**, each 0.1944 mm actual versus
  the configured 0.2500 mm minimum, internal to J1. The earlier description
  called these warnings; the current project classifies them as errors.
- 206 unconnected items; 0 routed tracks/vias; 0 board-level copper zones.
  Exposed-pad holes exist inside footprints, but no ground plane connects them.
- No reported current pad shorts, general clearance violations or courtyard
  overlaps. This does not establish electrical correctness or RF suitability.
- Four copper layers and 1.6 mm overall thickness are specified, but no actual
  fabricator dielectric stackup or routed impedance-controlled geometry exists.
- J2 uses a vertical SMA footprint on the opposite end from J1, consistent with
  the intended connector arrangement. The orderable SMA part remains TBD.
- The documented GPIO truth table agrees with Infineon's table when SW0=V2
  and SW1=V1. This verifies logic, not the complete RF design or assembly.
- The BOM omits many ordinary resistors and capacitors and is not an assembly
  BOM. Exact RF part series, crystal and other unspecified items remain open.
- BGS13SN8's tabulated RF performance starts at 698 MHz; the listed broader
  frequency range alone is not a guarantee of 315/433 MHz performance. Verify
  those lower bands experimentally or obtain supporting characterization.

Source: [Infineon BGS13SN8 datasheet, Tables 4 and 9](https://www.infineon.com/assets/row/public/documents/24/49/infineon-bgs13sn8-datasheet-en.pdf).

## Recommended correction sequence

1. Correct DGUARD, balun footprint, LED polarity, CP2102N sensing/power circuit,
   and the D2 part/footprint mismatch; adopt functional IC symbols.
2. Reorient USB-C; resolve module antenna geometry; rebuild radio placement
   with local bypassing and short RF/oscillator paths.
3. Complete the exact BOM and thermal design, choose the fabrication stackup,
   and route power, ground, USB and RF with appropriate constraints.
4. Repeat netlist/pin audits, ERC, routed DRC and mechanical review before
   generating the five-board fabrication/assembly package.

Review only: schematic, PCB, generators and BOM were not changed by this review.
