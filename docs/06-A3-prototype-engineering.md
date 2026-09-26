# A3 prototype engineering decisions

Updated 2026-09-26. This is an engineering prototype, not a proven four-band
product. No board has been assembled or measured. Do not order historical A2
files, mix A2 firmware with A3, or treat a clean DRC as RF qualification.

## Power and USB startup

U6 is now **AP63203WU-7**, a fixed 3.3 V switching regulator, with a 4.7 uH
Coilcraft XAL4030-472MEC and two 22 uF output capacitors. The linear regulator's
approximately 0.94 W dissipation at 550 mA/5 V becomes about 0.32 W converter
loss **if** efficiency is 85%. This is a screening calculation, not a measured
thermal rating. The IC's 2 A rating is not the board or USB power allowance.
[Diodes datasheet](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf).

C1/C2/C13 use 25 V, 1206 parts after inspecting Yageo's DC-bias curves. The
original proposed 10 V/0805 parts lost too much effective capacitance. See the
[exact 1206 part](https://www.yageogroup.com/component-documentation/download/specsheet/CC1206MKX5R8BB226).
Typical curves are not minimum guaranteed capacitance; aging and load-step
behavior still need review and measurement.

F1 is MF-NSMF075/13X-2: the old MF-NSMF050 is marked NRND and its hold current
falls to 0.40 A at 50 C. The replacement has 0.61 A hold at 50 C and 0.35 ohm
maximum post-reflow resistance at 23 C. **A PTC is not a 500 mA current limiter.**
[Bourns datasheet](https://www.bourns.com/docs/product-datasheets/mf-nsmf.pdf).

The CP2102N runs from protected VBUS and supplies its own VDD/VIO rail,
`+3V3_USB`. Its SUSPENDb signal controls TPS22918, which ramps power to the
main regulator only after USB configuration. A 10 nF/50 V CT capacitor gives
approximately 27.65 ms typical 10–90% rise at 5 V. The load switch is not
overcurrent protection or a USB-PD controller.
[CP2102N datasheet](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf),
[TPS22918 datasheet](https://www.ti.com/lit/ds/symlink/tps22918.pdf).

U8 SN74LVC2G125DCTR buffers both UART directions on the main rail. Its Ioff
feature addresses back-powering through UART while the ESP32 is off. Auto-reset
transistor behavior, leakage and power sequencing still need bench checks.
[TI buffer datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc2g125.pdf).

### J4: one-time power setup, not an RF switch

Ship the shunt **loose/unfitted**. First connect USB with only the CP2102N powered.
Using Silicon Labs' configuration utility, configure and read back the USB
descriptor for **bus-powered 500 mA**, retain the intended SUSPENDb behavior,
then unplug and fit J4 pins **1–2 (AUTO)**. Verify the host grants configuration
before the ESP32 rail rises. Suspend will turn the main rail off.

Pins **2–3 (EXT)** force power on and are only for a separately verified,
adequately rated regulated **5 V** source. They do not negotiate extra USB
current. Never use 9/12/20 V PD-trigger cables. U7 is a low-voltage part even
though the buck alone accepts higher voltages. Never connect external power
to J3 while USB is attached; there is no source-ORing circuit.

Initial testing is indoor, with Wi-Fi off, diagnostic-only firmware and a
current-limited supply. The full ESP32/radio load may exceed a 500 mA USB
budget at low cable-end voltage. Do not promise arbitrary-port operation or
unrestricted simultaneous Wi-Fi/radio transmission. Validate before adding
those modes. [Reproducible calculations](../reports/engineering-budget-A3.json).

## RF switches and software mapping

U3/U4 are **PE42442A-Z SP4T** switches specified for 30 MHz–6 GHz. Three ports
carry the filters; the fourth is externally terminated with 49.9 ohm. The
selection fixes the previous switch's low-band specification gap, but not the
matching network's unmeasured performance. Expect roughly two switch losses
in series; do not quote the IC's insertion loss as whole-board loss.
[pSemi datasheet](https://psemi.com/pdf/datasheets/pe42442ds.pdf).

The output switch's outer branches are reversed for planar routing, so it has
independent controls. The table is written **V1, V2**, not binary-number order.

| Mode | RF_DISABLE / V3 | U3 V1,V2 / GPIO32,33 | U4 V1,V2 / GPIO16,17 |
|---|---:|---|---|
| Safe boot | 1 | 1,1 | 1,1 |
| 315 MHz | 0 | 1,0 | 1,1 |
| 433 MHz | 0 | 0,1 | 0,1 |
| 868 or 915 MHz | 0 | 1,1 | 1,0 |

GPIO4 drives V3 on both switches. Five external **10 kohm pullups** establish
111 before firmware. They are stronger than the initially considered 100 kohm
parts, allowing more margin against internal pulls/leakage. Verify startup on
a scope. **000 selects RF4; it is not the all-off state.** GPIO16/17 on J3 are
now RF debug taps, not spare GPIOs. A3 diagnostics never select an active path.

Future selection must require stable CC1101 IDLE, drive V3 high, wait, update
both selectors, wait, lower V3, then configure/calibrate the radio. Respect the
switch's 25 kHz normal-mode maximum switching rate; use at least 50 us between
selection events. No RX/TX command interface is implemented yet.

## Routing, stackup and matching

The proposed stackup is JLC04161H-7628: 0.2104 mm top dielectric, Dk 4.4,
35 um outer copper. L2/In1 is the unbroken ground reference, with no signal
traces. Long RF runs use a **0.35 mm starting width**, short QFN necks are
0.20 mm. The main USB paired section uses 0.30 mm width / 0.20 mm gap; the
connector crossover and uncoupled transitions differ.
[Fabricator stackup](https://jlcpcb.com/impedance).

These geometries are first-order proposals, not impedance certificates. Get
fabricator confirmation including solder mask, etched trace shape and nearby
copper. Inspect return paths and the USB connector crossover. No blind/microvias
are used; small escape vias are 0.50/0.20 mm pad/drill, ordinary vias 0.60/0.30.

Native candidate DRC is **0 violations / 0 unconnected items** and fresh
schematic-to-PCB pin/value/footprint-name parity passes. The placement seed
is intentionally unrouted. C60 is shifted 0.4 mm north in the finishing step.
Two via centers lie inside SMD pads: C21.1 at (46.5,18.9) and U5 exposed
ground pad at (16,19.4), in mm. Require **resin fill and copper capping** at
these positions and supplier review of every pad-adjacent via. These are not
permission to use open via-in-pad or to assume ordinary low-cost processing.
The stackup's loss tangent 0.02 and solder-mask thickness 0.01 mm are modeling
assumptions, not verified supplier values; they are not impedance certification.

Power switching, RF and crystal routes are generated explicitly before the
remaining digital routing. RF ground lands connect to the switch exposed
paddles and nearby ground vias. R40's redundant zero-ohm series jumper was
removed to eliminate a detour; L41 now feeds the input switch directly.

The crystal was rotated to make room for digital pin escape without routing
clock signals through vias. One oscillator connection is consequently longer
than the old 3.5 mm straight-line screening goal. This is **not** an approved
waiver of startup/frequency testing. Record actual routed lengths, load trim,
cold-start behavior and probe loading during review; do not probe it casually
with a high-capacitance scope probe.

The balun and filter values remain reference-derived starting values, not a
four-band match. Board parasitics and the new switch packages alter the circuit.
VNA tuning, conducted RX tests and spectral tests are necessary. A single SMA
does not make an antenna broadband. No guaranteed range or sensitivity is claimed.

## Five-board acceptance plan

1. Independent schematic/layout review and supplier DFM/impedance confirmation
   on the exact file hashes; approve stock, footprints, paste and substitutions.
2. Assemble five only after a separately authorized quote. Inspect the first
   board for shorts and polarity before powering all five.
3. Configure/read back CP2102N with J4 open. Check USB enumeration, then AUTO
   power-up, suspend/resume, UART flashing and manual/automatic BOOT/RESET.
4. Measure 3.3 V during startup and 0–500 mA load steps; check input current,
   fuse drop, regulator/inductor temperature and RF rail noise. Reject rail
   dips below the ESP32 module's 3.0 V minimum.
5. Run diagnostics repeatedly on all five. Confirm crystal startup and actual
   frequency. A passing ID read is not an RF test.
6. Tune and measure each RF path into 50 ohm equipment, using a suitable
   attenuator and authorized test conditions. Record per-band insertion loss,
   return loss, receive performance and any rework. Transmit remains disabled
   until spectral and applicable operating-limit checks are complete.

An RF engineer can review/tune the exact prototype remotely or in a lab; these
measurements cannot be supplied by code alone. Keep at least one board in its
original population as a comparison while tuning another.
