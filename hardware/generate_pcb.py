#!/usr/bin/env python3
"""Generate the unrouted Rev A placement PCB from the KiCad XML netlist.

This deliberately stops at placement and initial ground/thermal copper.
It does not route signal/power traces or create Gerbers. RF routing begins only
after a board-house stackup and an independent schematic/footprint review.

Run with KiCad's bundled Python so the pcbnew module is available.
"""

from pathlib import Path
import os
import xml.etree.ElementTree as ET

import pcbnew


HERE = Path(__file__).resolve().parent
NETLIST = HERE / "esp32-cc1101-multiband.xml"
OUTPUT = HERE / "esp32-cc1101-multiband.kicad_pcb"
_FP_CANDIDATES = (
    Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"),
    Path.home() / "Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
    Path("/usr/share/kicad/footprints"),
)
KICAD_FP_ROOT = Path(os.environ["KICAD_FP_ROOT"]) if os.environ.get("KICAD_FP_ROOT") else next(
    (p for p in _FP_CANDIDATES if p.is_dir()), _FP_CANDIDATES[0]
)
CUSTOM_FP_ROOT = HERE / "lib" / "esp32_cc1101.pretty"


def mm(value):
    return pcbnew.FromMM(value)


def point(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def add_outline_segment(board, x1, y1, x2, y2):
    segment = pcbnew.PCB_SHAPE(board)
    segment.SetShape(pcbnew.SHAPE_T_SEGMENT)
    segment.SetLayer(pcbnew.Edge_Cuts)
    segment.SetStart(point(x1, y1))
    segment.SetEnd(point(x2, y2))
    segment.SetWidth(mm(0.10))
    board.Add(segment)


def add_text(board, text, x, y, layer, size=1.0, thickness=0.15):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(point(x, y))
    item.SetLayer(layer)
    item.SetTextSize(point(size, size))
    item.SetTextThickness(mm(thickness))
    board.Add(item)


def footprint_path(library):
    if library == "ESP32_CC1101_RF":
        return str(CUSTOM_FP_ROOT)
    return str(KICAD_FP_ROOT / f"{library}.pretty")


def add_ground_copper(board):
    """Initial heat spreading, not a completed return-path or thermal design."""
    ground = board.FindNet("/GND")
    if ground is None:
        raise RuntimeError("GND net missing")
    for layer, bounds in (
        (pcbnew.In1_Cu, (0.6, 0.6, 89.4, 35.4)),
        (pcbnew.B_Cu, (0.6, 0.6, 89.4, 35.4)),
        (pcbnew.F_Cu, (8.0, 1.0, 25.0, 10.5)),
    ):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(ground)
        zone.SetLocalClearance(mm(0.25))
        zone.SetMinThickness(mm(0.20))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        outline = zone.Outline()
        outline.NewOutline()
        x1, y1, x2, y2 = bounds
        for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            outline.Append(mm(x), mm(y))
        board.Add(zone)
    # Outside the SOT-223 body: no open via-in-pad solder-wicking hazard.
    for x in (21.8, 23.5):
        for y in (3.5, 5.5, 7.5, 9.5):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(point(x, y))
            via.SetWidth(mm(0.60))
            via.SetDrill(mm(0.30))
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(ground)
            board.Add(via)
    board.BuildConnectivity()
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("Ground zone fill failed")


PLACEMENT = {
    # Connectors and primary ICs.
    "J1": (3.65, 18.0, -90),
    "J2": (85.7, 18.0, 0),
    "J3": (21.0, 34.0, 90),
    "U1": (35.0, 6.30, 0),
    "U2": (52.0, 18.0, 0),
    "U5": (16.0, 20.0, 0),
    "U6": (17.0, 6.5, 0),

    # USB-C input, protection, power, and UART programming.
    "F1": (6.5, 9.5, 90),
    "D1": (11.0, 16.0, 0),
    "D2": (10.5, 7.0, 0),
    "R1": (6.0, 25.0, 90),
    "R2": (8.0, 25.0, 90),
    "R3": (17.5, 24.8, 90),
    "R4": (3.2, 25.0, 0),
    "R5": (26.0, 24.0, 0),
    "R6": (26.0, 26.2, 0),
    "C1": (10.8, 4.2, 180),
    "C2": (10.8, 8.8, 180),
    "C3": (10.0, 24.5, 90),
    "C4": (12.2, 21.2, 180),
    "C5": (5.0, 28.0, 0),
    "C6": (12.2, 22.7, 180),
    "C7": (14.5, 23.75, -90),
    "C8": (10.0, 21.2, 90),
    "C9": (14.8, 26.5, 90),
    "Q1": (22.3, 19.0, 0),
    "Q2": (22.3, 23.0, 0),
    "R20": (19.5, 18.0, 90),
    "R21": (19.5, 23.0, 90),

    # ESP32 boot controls and indicators.
    "R10": (22.0, 11.6, 0),
    "C10": (22.0, 13.7, 0),
    "C11": (23.7, 1.5, 180),
    "C12": (24.0, 2.9, 180),
    "R11": (22.0, 15.8, 0),
    "SW1": (9.5, 33.0, 0),
    "SW2": (16.0, 33.0, 0),
    "R12": (9.0, 29.0, 0),
    "D3": (12.5, 29.0, 0),
    "R13": (16.0, 29.0, 0),
    "D4": (19.5, 29.0, 0),

    # CC1101 power, crystal, and local decoupling.
    "FB1": (46.5, 10.8, 0),
    "C20": (50.0, 11.5, 0),
    "C21": (48.3, 18.5, 180),
    "C22": (49.0, 21.6, 180),
    "C23": (55.7, 21.3, 0),
    "C24": (55.5, 15.6, 0),
    "C25": (53.6, 14.1, 90),
    "C26": (50.5, 14.1, 90),
    "C30": (48.3, 20.0, 180),
    "R30": (52.0, 14.1, 90),
    "Y1": (52.5, 22.4, 0),
    "C31": (51.35, 25.2, 90),
    "C32": (55.7, 23.2, 0),
    "R31": (60.0, 24.5, 0),
    "R32": (60.0, 26.5, 0),

    # CC1101 differential port and broadband balun match.
    "C40": (57.0, 17.2, 0),
    "C41": (57.0, 19.3, 0),
    "C42": (55.25, 18.25, 90),
    "B1": (59.3, 18.25, 0),
    "L40": (61.5, 17.76, 0),
    "C43": (61.2, 20.0, 90),
    "L41": (63.5, 17.76, 0),
    "C44": (63.2, 20.0, 90),
    "R40": (64.5, 15.8, 90),

    # Dual-SP3T band-selection network. Keep the topology visually obvious.
    "U3": (66.2, 18.0, 180),
    "C60": (68.5, 16.7, 0),
    "L42": (67.8, 13.0, 0),
    "L43": (69.8, 13.0, 0),
    "L44": (71.8, 13.0, 0),
    "L45": (67.8, 15.0, 90),
    "C45": (69.8, 15.0, 90),
    "C46": (71.8, 15.0, 90),
    "L46": (68.0, 18.0, 0),
    "C47": (68.0, 20.0, 90),
    "L47": (70.0, 18.0, 0),
    "C48": (70.0, 20.0, 90),
    "L48": (72.0, 18.0, 0),
    "C49": (72.0, 20.0, 90),
    "L49": (74.0, 18.0, 0),
    "L50": (67.5, 23.0, 0),
    "C50": (67.5, 25.0, 90),
    "L51": (70.0, 23.0, 0),
    "C51": (70.0, 25.0, 90),
    "U4": (76.5, 18.0, 0),
    "C61": (75.0, 19.5, 180),
    "C52": (76.5, 20.5, 90),
    "L52": (78.3, 18.0, 0),
    "R41": (80.2, 18.0, 0),
    "C53": (74.8, 22.5, 90),
    "C54": (77.0, 22.5, 90),
    "D5": (79.2, 22.5, 90),
}


def main():
    if not NETLIST.exists():
        raise SystemExit(f"Missing {NETLIST}; export the KiCad XML netlist first")

    root = ET.parse(NETLIST).getroot()
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    settings = board.GetDesignSettings()
    settings.SetBoardThickness(mm(1.6))
    # These match common prototype-fab capabilities and the exposed-pad via
    # arrays in KiCad's official ESP32/CC1101 footprints.
    settings.m_MinThroughDrill = mm(0.20)

    # Exact Rev A mechanical envelope: USB-C on the left short edge and SMA on
    # the right short edge. Corners stay square until enclosure requirements exist.
    add_outline_segment(board, 0, 0, 90, 0)
    add_outline_segment(board, 90, 0, 90, 36)
    add_outline_segment(board, 90, 36, 0, 36)
    add_outline_segment(board, 0, 36, 0, 0)

    components = {}
    for comp in root.find("components").findall("comp"):
        ref = comp.attrib["ref"]
        footprint_id = comp.findtext("footprint", "")
        if not footprint_id:
            continue
        library, name = footprint_id.split(":", 1)
        footprint = pcbnew.FootprintLoad(footprint_path(library), name)
        if footprint is None:
            raise RuntimeError(f"Unable to load {footprint_id} for {ref}")
        footprint.SetReference(ref)
        footprint.SetValue(comp.findtext("value", ""))
        # Dense prototypes are more readable with functional labels added below;
        # fabrication references remain available in the schematic and BOM.
        footprint.Reference().SetVisible(False)
        footprint.Value().SetVisible(False)
        # The module antenna intentionally overhangs the PCB. Its fabrication
        # outline and 3D model remain; do not print its off-board silk outline.
        if ref in ("U1", "J1"):
            for graphic in list(footprint.GraphicalItems()):
                if graphic.GetLayer() == pcbnew.F_SilkS:
                    graphic.SetLayer(pcbnew.F_Fab)
        if "DNP" in comp.findtext("value", "").upper() or ref == "J3":
            footprint.SetDNP(True)
        board.Add(footprint)
        components[ref] = footprint

    # Attach net objects to every copper pad sharing the requested pad number.
    for net_node in root.find("nets").findall("net"):
        net_name = net_node.attrib["name"]
        net = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net)
        for node in net_node.findall("node"):
            footprint = components.get(node.attrib["ref"])
            if footprint is None:
                continue
            pin = node.attrib["pin"]
            matched = False
            for pad in footprint.Pads():
                if pad.GetNumber() == pin:
                    pad.SetNet(net)
                    matched = True
            if not matched:
                raise RuntimeError(
                    f"Netlist pin {node.attrib['ref']}.{pin} has no footprint pad"
                )

    # Place test pads in two accessible rows near the lower-right edge.
    for index in range(12):
        ref = f"TP{index + 1}"
        PLACEMENT[ref] = (50.0 + (index % 6) * 4.0,
                          30.0 + (index // 6) * 3.0, 0)

    unplaced = []
    for ref, footprint in components.items():
        placement = PLACEMENT.get(ref)
        if placement is None:
            unplaced.append(ref)
            continue
        x, y, angle = placement
        footprint.SetPosition(point(x, y))
        footprint.SetOrientationDegrees(angle)

    if unplaced:
        raise RuntimeError("No placement supplied for: " + ", ".join(unplaced))

    # Mechanical-only mounting holes, intentionally absent from the schematic.
    for ref, x, y in (
        ("MH1", 3.0, 3.0), ("MH2", 3.0, 33.0),
        ("MH3", 87.0, 3.0), ("MH4", 87.0, 33.0),
    ):
        hole = pcbnew.FootprintLoad(
            str(KICAD_FP_ROOT / "MountingHole.pretty"),
            "MountingHole_2.7mm_M2.5",
        )
        if hole is None:
            raise RuntimeError("Unable to load M2.5 mounting-hole footprint")
        hole.SetReference(ref)
        hole.Reference().SetVisible(False)
        hole.SetPosition(point(x, y))
        board.Add(hole)

    add_ground_copper(board)

    add_text(board, "ESP32 + CC1101 MULTIBAND  REV A2", 72, 3.0,
             pcbnew.F_SilkS, 0.8, 0.12)
    add_text(board, "USB-C", 3.2, 9.5, pcbnew.F_SilkS, 0.8, 0.11)
    add_text(board, "RST", 9.5, 30.5, pcbnew.F_SilkS, 0.8, 0.10)
    add_text(board, "BOOT", 16.0, 30.5, pcbnew.F_SilkS, 0.8, 0.10)
    add_text(board, "SMA", 85.7, 24.5, pcbnew.F_SilkS, 0.8, 0.11)
    add_text(board, "PLACEMENT DRAFT - NOT FOR MANUFACTURE", 45, 1.0,
             pcbnew.Dwgs_User, 0.8, 0.12)

    title = board.GetTitleBlock()
    title.SetTitle("ESP32-WROOM-32E + CC1101 Multiband")
    title.SetRevision("A2 - ROUTING DRAFT")
    title.SetCompany("Personal prototype")
    pcbnew.SaveBoard(str(OUTPUT), board)
    print(f"Saved {OUTPUT}")
    print(f"Footprints: {len(list(board.GetFootprints()))}")
    print(f"Nets: {board.GetNetCount()}")
    print("Initial ground/thermal copper only; signal/power routing omitted")


if __name__ == "__main__":
    main()
