# A2 routing and validation constraints

**Historical A2 analysis, superseded for the current board.** See
[A3 engineering decisions](06-A3-prototype-engineering.md). Do not apply A2
power or switch decisions to A3.

Status: engineering draft, not fabrication approval. No order has been placed.

## Stackup target

Use JLCPCB **JLC04161H-7628**, nominal 1.6 mm four-layer, as the current
design target, not a purchase commitment. Confirm the exact stackup with the
fabricator before release. The published sequence is:

| Layer | Material / nominal thickness | Function |
|---|---|---|
| F.Cu | 0.035 mm copper | Components, RF, USB, local bypass loops |
| Dielectric 1 | 7628 prepreg, 0.2104 mm | RF reference-plane spacing |
| In1.Cu | 0.0152 mm copper | Continuous GND; no signal routing |
| Core | 1.065 mm | FR-4 |
| In2.Cu | 0.0152 mm copper | Power and slow digital signals |
| Dielectric 2 | 7628 prepreg, 0.2104 mm | Bottom reference spacing |
| B.Cu | 0.035 mm copper | Digital signals and GND |

These are nominal laminate values, not a thickness-tolerance guarantee. The
main board currently carries a nominal 1.6 mm thickness; it does **not** yet
contain a approved controlled-impedance stackup or manufacturing coupon.
[Fabricator stackups](https://jlcpcb.com/impedance).

## Routing rules and limitations

The project defines Default, POWER, USB, RF_LOCAL and ANALOG_LOCAL classes.
Default trace width is 0.20 mm; power target width is 0.40 mm. The 0.15 mm
minimum allows local fine-pitch escapes; it is not an acceptable long power
trunk. Existing 0.25 mm hole-clearance rules remain, with no DRC exclusions.
These dimensions fit within the published prototype capabilities, but assembly
and impedance approval are separate. [Fabrication capabilities](https://jlcpcb.com/capabilities/Capab).

The local routing experiment constrains RF, crystal/bias/decoupling and USB
nets to F.Cu and leaves In1.Cu unavailable for traces. Its 0.20 mm RF/USB
widths are placeholders, **not calculated 50-ohm / 90-ohm geometry**.
Autorouting does not establish differential-pair coupling, filter behavior,
short bypass loops or an adequate power distribution network.

Before promoting any candidate:

1. Manually route the RF path and its ground returns. Solve the final 50-ohm
   SMA/feed geometry with actual dielectric data, mask, copper thickness and
   coplanar gap; obtain fabricator confirmation. Keep matching-network segments
   compact and include their parasitics in tuning.
2. Route USB D+/D- as a consistent 90-ohm differential pair, with short symmetric
   connector joins and ESD connections. Check skew, stubs and continuous ground.
3. Keep clock traces short; no fast digital routes beneath the crystal or RF
   network. Add appropriately placed ground stitching and return vias.
4. Review every sub-0.40 mm power segment. Permit only documented short escapes;
   calculate voltage drop using final copper, length and peak load.
5. Run native KiCad DRC and connectivity with the candidate's matching project
   settings. Zero shorts/clearance errors alone does not mean routing is complete.

## Crystal

Y1 is Abracon **ABM8-26.000MHZ-10-1-U-T**: 26 MHz, CL 10 pF,
ESR 50 ohms, four pads. Pins 1/3 are the oscillator terminals; 2/4 are ground.
Its -10 to +60 C rating limits the currently selected component set; this is
not an industrial-temperature-qualified board. [Exact part](https://abracon.com/parametric/crystals/ABM8-26.000MHZ-10-1-U-T),
[package drawing](https://abracon.com/Resonators/abm8.pdf).

C31=C32=15 pF C0G is the starting load: CL = 15/2 + 2.5 = 10 pF,
using TI's typical total parasitic capacitance. Actual PCB/pin parasitics are
not yet measured. Verify startup over supply/temperature, aging/tolerance budget
and carrier frequency with a calibrated instrument, then trim capacitors if
needed. Do not directly probe the crystal with a high-capacitance probe.
[CC1101 datasheet, sections 4.4 and 7.3](https://www.ti.com/lit/ds/symlink/cc1101.pdf).

## Power and temperature: unresolved acceptance gate

The AP7361C's 1 A headline rating does not establish board load capacity.
Screening at 5.25 V input, 3.267 V output and 40 C ambient, using the
datasheet's typical 110 C/W SOT-223 thermal resistance, gives approximately:

| Continuous load | LDO dissipation | Estimated junction temperature |
|---|---:|---:|
| 0.10 A | 0.198 W | 62 C |
| 0.30 A | 0.595 W | 105 C |
| 0.50 A | 0.992 W | 149 C |

This simplified calculation excludes small quiescent losses and is **not** a
prediction validated for this copper layout. The 500 mA case has inadequate
margin. Prototype testing must establish an allowed sustained load; neither
300 mA nor 500 mA is currently an approved board rating. If the intended Wi-Fi
and radio workload cannot meet the thermal target, redesign the supply as a
buck regulator before release. [Regulator datasheet](https://www.diodes.com/datasheet/download/AP7361C.pdf).

Test procedure after a reviewed board exists:

- Start on a current-limited bench supply with ESP32 held reset; check rail
  voltage and unexpected current before releasing reset.
- Test 4.75/5.0/5.25 V input, idle, boot, Wi-Fi burst and combined radio load.
  Capture 3.3 V at the ESP32 and CC1101 with an oscilloscope. Include cable,
  fuse, bead and trace voltage drops; check brownout and oscillator startup.
- Log input current, ambient, regulator/tab temperature and warm-up until
  steady state. Estimate junction temperature with an appropriate board model,
  not case temperature alone. Use a provisional design target <=110 C junction.
- Check capacitor effective values at DC bias, not nominal markings only.
- Verify USB source-current availability/enumeration behavior. CC resistors and
  a 500 mA PTC are not current negotiation or a startup power controller.

## RF acceptance gates

315/433/868/915 MHz remain supported **design targets**, not measured claims.
The selected switch's tabulated RF performance does not guarantee the lower
two bands. Measure insertion loss, return loss and isolation of each path with
a calibrated VNA. Measure the shared upper branch at both 868 and 915 MHz.
Then verify conducted sensitivity, output spectrum/harmonics and frequency
accuracy with appropriate equipment. Use RF terminations/attenuation and a
shielded setup; no unrestricted over-the-air transmit tests.

If 315/433 MHz performance fails, select a switch explicitly characterized for
those bands and re-evaluate its footprint, logic and matching. Firmware cannot
repair an unsuitable analog RF path. Keep the default 00 isolation state and
CC1101 IDLE during all switch changes. Current bring-up firmware does not TX.

## Purchasing status

The BOM remains a draft. Proposed exact parts have been added for the USB/SMA
connectors, crystal, fuse, bead, RF inductors and many passives. Unselected items
remain explicitly marked SELECT_EXACT_PART. All populated rows still need a
stock/lifecycle check, approved assembly sourcing and suitable spares. Five-unit
quantities exclude spares. Do not substitute M-12A/B/C for HRO's base M-12
connector without reviewing that variant's drawing.

Primary part references:

- [HRO connector](https://en.krhro.com/Product-Details/726.html), base M-12
  drawing sheet 4 (local reviewed copy: `tmp/pdfs/hro-official.pdf`).
- [Amphenol 132134](https://www.amphenolrf.com/en-us/part/132134/662/), standard
  SMA female, straight through-hole; final drawing/physical-fit check pending.
- [Coilcraft 0402HP](https://www.coilcraft.com/getmedia/54459dcc-b821-4a9d-b91e-0416ea86a9b2/0402hp.pdf),
  selected 5% RF inductors; values are starting values pending PCB tuning.
- [Bourns MF-NSMF](https://www.bourns.com/docs/product-datasheets/mf-nsmf.pdf),
  MF-NSMF050-2, 1206, 0.5 A hold at 23 C, 13.2 V; apply temperature derating.
- [Murata bead](https://www.murata.com/en-us/api/pdfdownloadapi?cate=cgsubChipFerriBead&partno=BLM18AG601SN1%23),
  [100 nF bypass](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM155R71C104KA88-01.pdf).
- Yageo exact spec sheets use `https://www.yageogroup.com/component-documentation/download/specsheet/`
  followed by the BOM part number; for example [10 kohm 0603](https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0710KL).
