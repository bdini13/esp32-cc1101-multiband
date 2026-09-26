# A3 architecture

Current circuit source: `hardware/generate_schematic.py`. Detailed decisions,
sources and limits: [A3 engineering notes](06-A3-prototype-engineering.md).
Historical A1/A2 files are not interchangeable with A3.

## Power and programming

USB-C 5 V passes through a 750 mA PTC and transient protection. The CP2102N
internal regulator powers only its USB-side logic (`+3V3_USB`). Its SUSPENDb
output, via an initially unfitted J4 shunt, enables TPS22918. That switch
soft-starts the AP63203 3.3 V buck and the ESP32/radio supply. SN74LVC2G125
isolates the UART while the main rail is off. Manual BOOT/RESET and the
two-transistor DTR/RTS auto-programming circuit are retained.

J4 ships open. Configure/read back a bus-powered 500 mA USB descriptor before
using AUTO (1–2). EXT (2–3) needs a separately verified regulated 5 V source.
There is no USB-PD negotiation, battery support or external-power source ORing.
The buck's IC rating is not a board/USB current rating. High combined Wi-Fi/RF
loads are not approved. USB suspend shuts down the main rail.

The RF rail passes through a ferrite and local bypass capacitors. CC1101
DGUARD is supplied, not grounded. A 26 MHz four-pad crystal provides its clock;
load capacitance and the longer oscillator connection need bench verification.

## Radio path

CC1101 differential RF → broadband balun → PE42442 input selector → one of
three filter branches → PE42442 output selector → tuning network → vertical
standard SMA female. Branches target 315, 433 and shared 868/915 MHz.

Both switches use 10 kohm external control pullups and boot in 111 isolation.
Their fourth RF ports are terminated in 49.9 ohm. U4's outer branches are
reversed physically, with independent GPIO controls; see the
[pin map](03-pin-map.md). Firmware currently performs digital checks only,
keeps every path isolated, and provides no RX/TX command.

Reference-derived matching values are starting points. The CC1101 tuning
range alone does not establish a four-band antenna match, sensitivity, range
or emissions compliance. Prototype RF tuning and measurement are required.

## Mechanical and layout

90 × 36 mm four-layer base, nominal 1.6 mm. USB-C opens at the left end;
SMA is vertical at the right. The ESP32-WROOM-32E-N8 antenna overhangs the
top edge. Proposed L2 is uninterrupted ground; no signal routing is allowed
there. Main RF and oscillator traces stay on top. USB has a short bottom-side
connector crossover. Actual impedance requires fabricator confirmation.

Two in-pad vias require filled/capped processing, not ordinary open drills:
C21 at (46.5,18.9) mm and U5 exposed pad at (16,19.4) mm. All coordinates
are KiCad board coordinates. Supplier review must also inspect nearby vias,
paste coverage, component orientation and connector fit.
