# Rev A Architecture

## System block diagram

```text
USB-C
  |-- ESD/protection -- 5V -- 3.3V regulator --+-- ESP32-WROOM-32E
  |                                            +-- CC1101/RF switches
  +-- D+/D- -- ESD -- CP2102N -- UART/auto-reset

ESP32 SPI ------------------------------- CC1101
ESP32 RF_SW[1:0] -------------------------+----------------------+
                                                                |
CC1101 RF_P/RF_N -- broadband balun -- SP3T -- matching paths -- SP3T -- SMA
                                             | 315 MHz |
                                             | 433 MHz |
                                             | 868/915 |
```

## Power

USB VBUS passes through resettable over-current protection and input transient
suppression. A1 uses the AP7361C-33E-13 3.3 V LDO in SOT-223: pin 1 IN,
pin 2/tab GND, pin 3 OUT. Do not substitute the different-pinout ER variant.
Initial front-side ground heat spreading, internal/bottom ground zones and
eight 0.30 mm-drill thermal vias are present. Power traces are not yet routed.
The IC's 1 A rating is not the allowable continuous board load. Worst-case
load/temperature and USB source-current behavior remain release gates; a
500 mA PTC does not negotiate USB current or guarantee compliance at startup.
See the A1 update report for thermal screening assumptions.
The current A2 screening and load-test procedure are in
`05-A2-routing-and-validation.md`; 500 mA sustained operation is not approved.

The RF section receives 3.3 V through a ferrite bead with local bulk and high
frequency decoupling. U2 pin 18 DGUARD is on +3V3_RF, not GND. C21–C26
provide local supply bypassing and C60/C61 bypass the individual switches.
The final routes must preserve short supply/ground loops. ESP32 C11/C12 are
local bulk and high-frequency bypass capacitors, separate from regulator C2.

## USB and programming

The ESP32-WROOM-32E has no native USB interface. A CP2102N connects USB D+/D-
to UART0. DTR and RTS drive the standard two-transistor ESP32 automatic-reset
circuit. RESET and BOOT buttons remain available if automatic programming fails.

U5 uses the external-regulator configuration: VIO, VDD and VREGIN all connect
to +3V3, with local 4.7 uF / 100 nF bypass pairs. Pin 8 senses USB power
through R5=22.1 kohm (upper) and R6=47.5 kohm (lower), not directly from 5 V.
R3 pulls reset up to that same 3.3 V rail. D2 is PESD5V0S1UL in SOD-882,
cathode to protected VBUS. Protection clamping/overshoot still needs validation.
In A2, J1 is HRO TYPE-C-31-M-12; its mouth remains on the left short edge.

## CC1101 frequency reference

A2 uses Abracon ABM8-26.000MHZ-10-1-U-T in a custom four-pad land pattern.
Pins 1/3 connect to the oscillator; pins 2/4 connect to ground. Initial 15 pF
load capacitors assume TI's typical 2.5 pF total parasitic capacitance, giving
10 pF effective load. Frequency trim and startup testing remain mandatory.
The selected crystal's component rating is -10 to +60 C, not industrial range.

## ESP32 placement

The module origin is (35.0, 6.30) mm. Its antenna tip is at y=-6.45 mm and
antenna feed at approximately y=-0.26 mm, outside the base-board edge y=0.
No copper, planes, traces, components, or mounting
hardware may enter the antenna keepout unless permitted by Espressif's module
layout guide.

## CC1101 digital interface

The ESP32 uses an SPI controller at a conservative bring-up speed of 1 MHz.
After electrical validation, firmware may increase the clock while remaining
within the CC1101 timing specification. GDO0 and GDO2 are routed to interrupt-
capable ESP32 inputs and test pads.

## Multiband RF path

The design basis is a single CC1101 followed by:

1. A broadband 50-ohm balun (B0310J50100AHF design family).
2. Two bidirectional SP3T RF switches (BGS13SN8 design family).
3. Three separately populated matching/filter branches:
   - 315 MHz
   - 433 MHz
   - shared 868/915 MHz
4. One 50-ohm controlled-impedance feed to the SMA connector.

This topology follows the same overall strategy as the published M5Stack Cap
CC1101 design. The captured values follow its Rev 0.3 schematic and remain
starting values, not an assertion that this different PCB is already tuned.
PCB dielectric, stackup, pad geometry, enclosure, and antenna all influence
the final match.

BGS13SN8's tabulated RF specifications start at 698 MHz. Its broader frequency
range does not establish guaranteed performance at 315/433 MHz. Those bands
require characterization or a verified alternative switch before acceptance.

### Switch truth table

| RF_SW0 | RF_SW1 | Path |
|---:|---:|---|
| 0 | 0 | All paths isolated (safe boot state) |
| 0 | 1 | 315 MHz |
| 1 | 0 | 433 MHz |
| 1 | 1 | 868/915 MHz |

The two switch ICs receive the same select lines so both ends select the same
branch. Pulldowns establish the isolated `00` state while the ESP32 boots.
Firmware must command CC1101 IDLE before changing the select lines.

The Infineon BGS13SN8 datasheet is authoritative at the IC pins: V1/V2 `00`
is isolation, `10` selects RF1, `01` selects RF2, and `11` selects RF3. The
board nets follow the reference naming, where RF_SW0 drives V2 and RF_SW1
drives V1. Consequently the table above is written in SW0/SW1 order. Unlike
the reference product, both controls are independent ESP32 GPIOs on this board,
so `00` remains available as a deterministic safe state.

## Antennas

The connector is shared; the antenna is not assumed to be universal. Rev A is
tested with three removable antennas. The 868 MHz antenna may be acceptable at
915 MHz only if its manufacturer specifies both bands or measurement confirms
an acceptable match.

## Layout constraints

- Four layers: signal/components, solid GND, power/slow signals, signal/GND fill.
- Obtain the actual fabricator stackup before setting 50-ohm trace geometry.
- Copy the RF reference placement topology closely; RF part spacing and ground
  via placement are circuit elements.
- Do not route digital signals under or through the RF network.
- Via-fence the RF region and antenna feed without violating the calculated
  coplanar-waveguide geometry.
- Keep USB and UART circuitry near the USB connector.
- Add optional DNP shunt/series tuning footprints at the antenna feed.
- J1 opening faces left; the footprint's recommended board-edge line is x=0.
- J2 is the vertical SMA footprint at (85.7, 18) mm, opposite USB-C.

## References used for the design basis

- TI CC1101 datasheet, Rev. I.
- Espressif ESP32-WROOM-32E/32UE datasheet and hardware design guidelines.
- Infineon BGS13SN8 datasheet.
- Anaren B0310J50100AHF datasheet.
- M5Stack Cap CC1101 public schematic, revision 0.3 dated 2026-05-28.
