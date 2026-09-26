# A3 prototype-review checkpoint — 2026-09-26

**Fully connected review candidate, not an approved order or proven radio.**
The owner's five-board prototype goal is unchanged. No hardware, quote, order,
human signature or measurement is represented by this checkpoint.

## Problems addressed

- Replaced the heat-constrained LDO with AP63203, a rated 4.7 uH inductor and
  higher-voltage/larger MLCCs selected after inspecting DC-bias curves.
- Added USB-side independent power, enumeration-controlled TPS22918 startup,
  J4 commissioning control and powered-off-protected UART buffers. Documented
  the USB current limitation instead of implying a buck negotiates power.
- Replaced the previous low-band-limited RF switches with PE42442 SP4Ts;
  checked manufacturer pin/land drawings, terminated unused RF4 ports and
  gave U4 independent selectors to avoid RF crossings.
- Corrected safe boot to five HIGH controls with 10 kohm pullups. Added
  preload/disable-order tests; transmit and receive commands remain absent.
- Explicitly routed RF, oscillator, USB, converter and main power before
  digital routing. Finished the remaining nets without suppressing DRC errors.
- Proposed exact parts for all 94 populated positions, plus a separate loose
  power-arm shunt accessory. There are 117 schematic footprints / 121 PCB
  footprints including four mounting holes; DNP parts and bare pads are not
  populated BOM purchases.
- Added fresh schematic/PCB comparison and fault-injected tests that reject
  wrong net, value, footprint name and missing component. A clean stale
  netlist is not accepted as the only connectivity evidence.

## Evidence

| Check | Result |
|---|---|
| Fresh schematic ERC | 0 violations |
| Routed A3 native DRC | 0 violations / 0 unconnected items |
| Fresh schematic to candidate comparison | PASS |
| Placement-seed native DRC | 0 violations / 283 unconnected items, intentionally unrouted |
| Artifact audit | 179/180; one crystal placement screening failure retained |
| Routing-layer constraints | 0 violations; no In1 signal tracks |
| Digital diagnostic tests | 17 fault-injection scenarios pass |
| RF boot tests | Pin map, preload order, disable-first and re-isolation pass |
| Preflight tests | 7 pass |
| Connectivity fault-injection tests | 4 malformed temporary boards rejected |
| ESP32 firmware build | PASS; 275645 bytes flash / 21576 bytes RAM |
| Physical boards tested | None |

The build used espressif32 7.1.3, Arduino framework
4.20017.260907+sha.dcc1105b, esptool 2.41100.260830 and Xtensa toolchain
8.4.0+2021r2-patch5. Project settings explicitly select 8 MB flash and
default_8MB partitions; the generic platform banner still says 4 MB.

KiCad top-copper, ground-plane, schematic and 3D exports were visually
inspected. The ground plane has no routed signals and appears continuous
beneath the circuitry; that is not an EMC/impedance certification. Missing
USB/SMA/custom-IC 3D bodies are disclosed in the README.

## Open items, with concrete closure criteria

1. **Crystal:** U2.10 to Y1.3 is 4.478 mm straight-line versus the retained
   3.5 mm screening target. The route is approximately 6.888 mm, plus its
   load-cap branch (whole net 8.142 mm). Q1 whole-net copper is 4.545 mm.
   The 3.5 mm limit is a project screening target, not a quoted TI maximum.
   An RF reviewer must assess relocation/clock loading before release; measure
   cold starts, frequency and supply/temperature sensitivity on the prototype.
   The check has deliberately NOT been weakened or silently waived.
2. **Power:** main paths are explicitly routed, but 62 branch/neck segments
   below 0.40 mm remain listed for current/voltage-drop review. Confirm USB
   configuration and J4 procedure, suspend/resume, back-power leakage, load
   steps, fuse drop and converter temperature. The full combined Wi-Fi/radio
   load can exceed 500 mA input at low cable-end voltage; it is not approved.
3. **RF:** approve matching/layout for prototype tuning, then measure each
   selected path with a VNA and conducted receive/spectral equipment. The
   switches' specified frequency coverage does not validate the whole board.
   Current firmware tests digital access only, not usable multiband RX/TX.
4. **Fabrication/assembly:** confirm exact stackup, RF/USB impedance, all
   small vias and pad-adjacent drills. C21.1 (46.5,18.9 mm) and U5 exposed
   ground pad (16,19.4 mm) require resin-filled/copper-capped vias. Confirm
   paste coverage, footprints, USB/SMA fit and real part availability.
5. **Independent review:** a qualified electrical/RF reviewer must approve
   the exact candidate hashes and documented prototype risks. No AI-generated
   result substitutes for their review or the subsequent bench tests.

See [fresh preflight](preflight-A3.json), [routing audit](routing-audit-A3.json),
[engineering calculations](engineering-budget-A3.json), and the
[detailed commissioning/acceptance plan](../docs/06-A3-prototype-engineering.md).
Preflight remains BLOCKED. No fabrication package was generated and no order
was placed. A1/A2 artifacts are historical; do not mix their firmware or parts
with A3. The existing project license is unchanged.
