#!/usr/bin/env python3
"""Generate explicit A2 project routing classes. No rule-error exclusions."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
RF_PREFIXES = ("/RF315", "/RF433", "/RF868", "/RF_315", "/RF_433",
               "/RF_868", "/RF_COMBINED", "/RF_FEED", "/RF_SMA",
               "/RF_SWITCH_IN", "/BAL", "/CC1101_RF_")
ANALOG = ("/CC1101_XOSC_Q1", "/CC1101_XOSC_Q2", "/CC1101_RBIAS", "/CC1101_DCOUPL")


def main():
    path = HERE / "esp32-cc1101-multiband.kicad_pro"
    project = json.loads(path.read_text())
    default = next(c for c in project["net_settings"]["classes"] if c["name"] == "Default")
    classes = [default]
    for name, width, clearance, priority in (
        ("RF_LOCAL", .20, .15, 1), ("ANALOG_LOCAL", .20, .15, 2),
        ("POWER", .40, .15, 3), ("USB", .20, .15, 4),
    ):
        c = dict(default)
        c.update(name=name, track_width=width, clearance=clearance, priority=priority)
        classes.append(c)
    project["net_settings"]["classes"] = classes
    patterns = []
    root = ET.parse(HERE / "esp32-cc1101-multiband.xml").getroot()
    for n in root.findall("nets/net"):
        name = n.attrib["name"]
        cls = None
        if name.startswith(RF_PREFIXES):
            cls = "RF_LOCAL"
        elif name in ANALOG:
            cls = "ANALOG_LOCAL"
        elif name in ("/+3V3", "/+3V3_RF", "/VBUS_IN", "/VBUS_PROTECTED"):
            cls = "POWER"
        elif name in ("/USB_DP", "/USB_DM", "/USB_DP_CONN", "/USB_DM_CONN"):
            cls = "USB"
        if cls:
            patterns.append({"netclass": cls, "pattern": name})
    project["net_settings"]["netclass_patterns"] = patterns
    project["board"]["design_settings"]["rules"]["min_track_width"] = .15
    path.write_text(json.dumps(project, indent=2) + "\n")
    print("Configured", len(patterns), "net-class assignments; no DRC exclusions added")


if __name__ == "__main__":
    main()
