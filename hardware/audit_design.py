#!/usr/bin/env python3
"""Targeted regression checks; not a substitute for ERC/DRC or RF validation.

Run with KiCad's bundled Python after regenerating schematic, XML, PCB and BOM.
Checks the generated artifacts, not just the generator's intended assignments.
"""
import csv
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew

HERE = Path(__file__).resolve().parent


def main():
    root = ET.parse(HERE / "esp32-cc1101-multiband.xml").getroot()
    board = pcbnew.LoadBoard(str(HERE / "esp32-cc1101-multiband.kicad_pcb"))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    comps = {c.attrib["ref"]: c for c in root.findall("components/comp")
             if c.findtext("footprint", "")}
    nets = {}
    for net in root.findall("nets/net"):
        for node in net.findall("node"):
            nets[(node.attrib["ref"], node.attrib["pin"])] = net.attrib["name"]
    checks = []
    measurements = {}

    def check(condition, description):
        checks.append({"check": description, "pass": bool(condition)})

    def net_is(ref, pin, expected):
        check(nets.get((ref, str(pin))) == "/" + expected,
              f"{ref}.{pin} -> {expected}")

    def pad(ref, pin):
        return next(p for p in footprints[ref].Pads() if p.GetNumber() == str(pin))

    def xy(item):
        pos = item.GetPosition()
        return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)

    def distance(a, b):
        ax, ay = xy(a)
        bx, by = xy(b)
        return math.hypot(ax - bx, ay - by)

    for pin in (4, 9, 11, 14, 15, 18):
        net_is("U2", pin, "+3V3_RF")
    for pin in (16, 19, 21):
        net_is("U2", pin, "GND")
    net_is("U2", 5, "CC1101_DCOUPL")
    for pin in (5, 6, 7):
        net_is("U5", pin, "+3V3")
    net_is("U5", 8, "USB_VBUS_SENSE")
    for ref, p1, p2, value in (
        ("R5", "VBUS_PROTECTED", "USB_VBUS_SENSE", "22.1k 1%"),
        ("R6", "USB_VBUS_SENSE", "GND", "47.5k 1%"),
    ):
        net_is(ref, 1, p1)
        net_is(ref, 2, p2)
        check(comps[ref].findtext("value") == value, f"{ref} divider value {value}")
    for ref, positive in (("D3", "STATUS_LED_A"), ("D4", "POWER_LED_A")):
        net_is(ref, 1, "GND")
        net_is(ref, 2, positive)
    net_is("D2", 1, "VBUS_PROTECTED")
    net_is("D2", 2, "GND")
    check(comps["D2"].findtext("footprint") == "Diode_SMD:D_SOD-882",
          "PESD5V0S1UL uses SOD-882")
    check(comps["U6"].findtext("value") == "AP7361C-33E-13",
          "Regulator is E, not different-pinout ER")
    for pin, net in ((1, "VBUS_PROTECTED"), (2, "GND"), (3, "+3V3")):
        net_is("U6", pin, net)
    check(comps["U6"].findtext("footprint") == "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
          "Regulator tab is pin 2 (GND)")

    for ref in ("U3", "U4"):
        for pin, net in ((1, "+3V3_RF"), (2, "RF_SW0"), (3, "RF_SW1"), (8, "GND")):
            net_is(ref, pin, net)
    for ref in ("C3", "C4", "C6", "C7", "C8", "C9", "C11", "C12"):
        net_is(ref, 1, "+3V3")
        net_is(ref, 2, "GND")
    for ref in ("C21", "C22", "C23", "C24", "C25", "C26", "C60", "C61"):
        net_is(ref, 1, "+3V3_RF")
        net_is(ref, 2, "GND")

    # Component-to-pin distances are placement checks, not routed lengths.
    for ic, pin, cap, limit in (
        ("U1", 2, "C11", 3.0), ("U1", 2, "C12", 3.0),
        ("U2", 4, "C21", 3.5), ("U2", 9, "C22", 3.5),
        ("U2", 11, "C23", 3.5), ("U2", 14, "C24", 3.5),
        ("U2", 15, "C25", 3.5), ("U2", 18, "C26", 3.5),
        ("U3", 1, "C60", 2.5), ("U4", 1, "C61", 2.5),
        ("U5", 5, "C4", 2.5), ("U5", 6, "C6", 2.5),
        ("U5", 7, "C7", 2.5),
    ):
        d = distance(pad(ic, pin), pad(cap, 1))
        key = f"{ic}.{pin}_to_{cap}.1_mm"
        measurements[key] = round(d, 3)
        check(d <= limit, f"{key} <= {limit}")
    for crystal_pin, net in ((1, "CC1101_XOSC_Q1"), (3, "CC1101_XOSC_Q2"), (2, "GND"), (4, "GND")):
        net_is("Y1", crystal_pin, net)
    check(comps["Y1"].findtext("footprint") == "ESP32_CC1101_RF:Abracon_ABM8_4Pin_3.2x2.5mm",
          "ABM8 uses manufacturer four-pad footprint")
    for ref in ("C31", "C32"):
        check(comps[ref].findtext("value") == "15pF C0G", f"{ref} initial 10 pF crystal load assumption")
    # 3.5 mm center distance accommodates the selected 3225 crystal; final
    # routed lengths and oscillator startup remain separate release gates.
    for pin, crystal_pin in ((8, 1), (10, 3)):
        d = distance(pad("U2", pin), pad("Y1", crystal_pin))
        measurements[f"U2.{pin}_to_Y1.{crystal_pin}_mm"] = round(d, 3)
        check(d < 3.5, f"CC1101 crystal pin {pin} within 3.5 mm")
    bx, by = xy(footprints["B1"])
    check(abs(footprints["B1"].GetOrientationDegrees()) < 0.001,
          "Balun orientation matches top-view audit frame")
    for pin, x, y in ((1, .65, -.49), (2, 0, -.49), (3, -.65, -.49),
                      (4, -.65, .49), (5, 0, .49), (6, .65, .49)):
        px, py = xy(pad("B1", pin))
        check(abs(px-bx-x) < .001 and abs(py-by-y) < .001,
              f"Balun pin {pin} manufacturer TOP-view location")
    for pin, net in ((1, "BALUN_50R"), (2, "GND"), (3, "BAL_N"), (4, "BAL_P")):
        net_is("B1", pin, net)
    usb = footprints["J1"]
    ux, _ = xy(usb)
    check(comps["J1"].findtext("footprint") == "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
          "HRO TYPE-C-31-M-12 connector footprint")
    check(abs(usb.GetOrientationDegrees() + 90) < .001 and abs(ux - 3.65) < .001,
          "HRO connector mouth at x=0, opening faces left")
    check(all(xy(p)[0] > 0 for p in usb.Pads() if p.GetNumber().startswith(("A", "B"))),
          "USB signal pad row is inside PCB")
    _, ey = xy(footprints["U1"])
    check(abs(footprints["U1"].GetOrientationDegrees()) < .001 and ey <= 6.56,
          "ESP32 antenna feed lies beyond y=0 board edge")
    measurements["ESP32_antenna_tip_y_mm"] = round(ey - 12.75, 3)
    check(board.GetCopperLayerCount() == 4, "Four copper layers")
    check(sum(isinstance(t, pcbnew.PCB_VIA) for t in board.GetTracks()) == 8,
          "Eight initial regulator thermal vias")
    copper_zones = [z for z in board.Zones() if not z.GetIsRuleArea()]
    check(len(copper_zones) == 3 and all(z.GetNetname() == "/GND" for z in copper_zones),
          "Initial F.Cu / In1.Cu / B.Cu ground heat-spreading zones")

    mismatches = []
    for ref, comp in comps.items():
        if ref not in footprints:
            mismatches.append(f"{ref}: missing footprint")
            continue
        fp = footprints[ref]
        if fp.GetValue() != comp.findtext("value"):
            mismatches.append(f"{ref}: value mismatch")
        for p in fp.Pads():
            number = p.GetNumber()
            if number and nets.get((ref, number), "") != p.GetNetname():
                mismatches.append(f"{ref}.{number}: PCB/netlist net mismatch")
    check(not mismatches, "All generated PCB pad nets and values match schematic XML")
    with (HERE / "bom-draft.csv").open() as source:
        rows = list(csv.DictReader(source))
    check(len(rows) == len(comps) and {r["Reference"] for r in rows} == set(comps),
          "BOM contains exactly every schematic footprint once")
    check(all(r["Value"] == comps[r["Reference"]].findtext("value") and
              r["Footprint"] == comps[r["Reference"]].findtext("footprint") for r in rows),
          "BOM values and footprints match schematic")
    report = {"status": "PASS" if all(c["pass"] for c in checks) else "FAIL",
              "scope": "Corrected draft only; not manufacturing approval",
              "checks": checks, "measurements": measurements,
              "parity_mismatches": mismatches, "footprints": len(footprints)}
    output = HERE.parent / "reports" / "design-audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['status']}: {sum(c['pass'] for c in checks)}/{len(checks)} checks")
    for c in checks:
        if not c["pass"]:
            print("FAIL:", c["check"])
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
