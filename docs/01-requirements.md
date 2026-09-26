# Rev A Requirements

Status: initial requirements captured 2026-09-20; updated for A3 2026-09-26.
These are target requirements, not assertions that the draft already satisfies them.

## Functional requirements

1. Use an ESP32-WROOM-32E module with 8 MB flash.
2. Integrate one TI CC1101 transceiver directly on the main PCB.
3. Support software selection of 315, 433, and 868/915 MHz RF matching paths.
4. Use one standard 50-ohm SMA female antenna connector.
5. Place the SMA connector vertically at the short end opposite USB-C.
6. Provide USB-C power, serial programming, logging, and automatic bootloader
   entry.
7. Provide physical RESET and BOOT buttons.
8. Provide a power LED and a firmware-controlled status LED.
9. Expose spare GPIO, 3V3, 5V, and ground on a 2.54 mm expansion header.
10. Include accessible test points for all power rails, UART, SPI, CC1101 GDO
    signals, and RF-switch control signals.

## Electrical requirements

- USB input: nominal 5 V.
- Logic and radio rail: 3.3 V.
- A3 uses AP63203 fixed 3.3 V buck, rated 2 A as an IC, not as a board.
  Actual board current is limited by USB source capability, voltage drop,
  fuse derating and measured thermal behavior; full simultaneous Wi-Fi/RF
  load is not yet approved. Configure the USB descriptor with J4 open first.
- USB-C CC1 and CC2: independent 5.1 kohm pull-down resistors.
- USB D+ and D-: ESD protected and routed as a differential pair.
- ESP32 EN: RC power-on reset plus USB-UART automatic reset control.
- CC1101: dedicated local decoupling at every supply pin.
- RF switches: five 10 kohm pullups select the isolated `111` state during boot;
  firmware must keep the CC1101 idle during path changes.

## Mechanical requirements

- Nominal board outline: 90.0 mm x 36.0 mm.
- Four-layer stackup with uninterrupted internal ground plane.
- USB-C centered on one 36 mm edge.
- Straight through-hole SMA centered on the opposite 36 mm edge.
- Four M2.5 mounting holes, final coordinates subject to component clearance.
- ESP32 module PCB antenna located at a board edge with the Espressif keepout
  observed on every copper layer.
- A1 placement: module antenna tip projects 6.45 mm beyond the base PCB.
  Allow at least 42.45 mm total width before enclosure/RF clearances.
- Maintain maximum practical separation between the ESP32 antenna and the
  CC1101 RF section/SMA connector.

## User-facing behavior

- Power-up state: CC1101 idle, transmit disabled.
- Firmware band API: `315`, `433`, `868`, or `915`.
- Selecting a band first idles the radio, then changes the RF switches, waits
  for settling, loads band-specific CC1101 registers, and calibrates.
- A3 switch state `111` is the all-paths-isolated safe state; `000` selects RF4.
- Transmit operations require an explicit region profile and compatible
  antenna confirmation in production firmware.

## Prototype quantity

- Five assembled Rev A boards.
- Optional spare boards and band-appropriate antennas need a separately
  approved quote; no purchase is authorized by this requirements document.

## Explicitly out of scope for Rev A

- Battery charging or battery connector.
- Display, keypad, audio, NFC, SD card, or external power amplifier.
- Weatherproofing or production enclosure.
- FCC/CE certification.
- Simultaneous operation on multiple sub-GHz bands.
