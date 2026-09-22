#!/usr/bin/env python3
"""Export a constrained local routing experiment; never an order release."""
from pathlib import Path
import re
import json
import xml.etree.ElementTree as ET
import pcbnew
import configure_routing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    configure_routing.main()
    board = pcbnew.LoadBoard(str(HERE / "esp32-cc1101-multiband.kicad_pcb"))
    data = json.loads((HERE / "esp32-cc1101-multiband.kicad_pro").read_text())["net_settings"]
    out = ROOT / "tmp" / "A2-route-input.dsn"
    if not pcbnew.ExportSpecctraDSN(board, str(out)):
        raise RuntimeError("DSN export failed")
    text = out.read_text()
    # Replace ALL exported classes, not just kicad_default. Standalone export
    # may load project classes, but omits the top-only circuit constraints.
    spans = []
    for match in re.finditer(r'\(class\s', text):
        start = match.start()
        depth = 0
        quoted = False
        for end in range(start, len(text)):
            c = text[end]
            if c == '"':
                quoted = not quoted
            if not quoted:
                depth += (c == '(') - (c == ')')
                if depth == 0:
                    spans.append((start, end + 1))
                    break
        else:
            raise RuntimeError("Unbalanced exported class")
    if not spans:
        raise RuntimeError("No exported net classes")
    assignments = {p["pattern"]: p["netclass"] for p in data["netclass_patterns"]}
    root = ET.parse(HERE / "esp32-cc1101-multiband.xml").getroot()
    nets = [n.attrib["name"] for n in root.findall("nets/net")]
    blocks = []
    for spec in data["classes"]:
        name = spec["name"]
        members = [n for n in nets if assignments.get(n, "Default") == name]
        layer = "(use_layer F.Cu)" if name in ("RF_LOCAL", "ANALOG_LOCAL", "USB") else ""
        blocks.append('(class ' + name + ' ' + ' '.join(json.dumps(n) for n in members)
                      + '\n(circuit (use_via "Via[0-3]_600:300_um") ' + layer + ')'
                      + f'\n(rule (width {spec["track_width"]*1000:g})'
                      + f' (clearance {spec["clearance"]*1000:g})))')
    for start, end in reversed(spans[1:]):
        text = text[:start] + text[end:]
    start, end = spans[0]
    text = text[:start] + '\n'.join(blocks) + text[end:]
    for name in ("RF_LOCAL", "ANALOG_LOCAL", "POWER", "USB"):
        if text.count(f'(class {name} ') != 1:
            raise RuntimeError(f"Missing or duplicate routing class {name}")
    out.write_text(text)
    print(out)


if __name__ == "__main__":
    main()
