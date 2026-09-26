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
    item.SetMirrored(layer == pcbnew.B_SilkS)
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
    # Ground stitching outside component pads; no open via-in-pad here.
    for x, y in ((12,3.9),(12,4.9),(12,8.5),(12,10.3),
                 (22,3.9),(23,4.8),(22,8.5),(14,8.5)):
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
    "U6": (14.5, 5.5, 0),
    "U7": (9.5, 9.8, 0),
    "U8": (24.3, 30.0, 0),
    "L1": (19.2, 5.5, 0),
    "J4": (7.8, 1.9, 90),
    "C13": (23.0, 8.5, -90),
    "C14": (16.1, 2.5, 0),
    "C70": (12.6, 11.3, 0),
    "C71": (27.7, 28.8, 90),
    "R70": (18.0, 12.3, 0),
    "R71": (18.0, 14.3, 0),

    # USB-C input, protection, power, and UART programming.
    "F1": (4.0, 9.5, 90),
    "D1": (11.0, 16.0, 0),
    "D2": (6.8, 9.0, 90),
    "R1": (6.0, 25.0, 90),
    "R2": (8.0, 25.0, 90),
    "R3": (17.5, 24.8, 90),
    "R4": (3.2, 25.0, 0),
    "R5": (26.0, 24.0, 0),
    "R6": (26.0, 26.2, 0),
    "C1": (10.2, 6.5, 180),
    "C2": (18.7, 9.5, 180),
    "C3": (10.0, 24.5, 90),
    "C4": (12.2, 21.2, 180),
    "C5": (5.0, 28.0, 0),
    "C6": (12.2, 22.7, 180),
    "C7": (14.5, 23.75, -90),
    "C8": (10.0, 21.2, 90),
    "C9": (10.5, 13.0, 0),
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
    "C21": (48.3, 18.8, 180),
    "C22": (49.0, 21.6, 180),
    "C23": (55.7, 21.3, 0),
    "C24": (55.5, 15.6, 0),
    "C25": (53.6, 14.1, 90),
    "C26": (50.5, 14.1, 90),
    "C30": (48.3, 20.0, 180),
    "R30": (52.0, 14.1, 90),
    "Y1": (52.5, 23.2, -90),
    "C31": (49.8, 22.9, 180),
    "C32": (55.1, 24.5, 0),
    "R31": (60.0, 24.5, 0),
    "R32": (60.0, 26.5, 0),
    "R33": (56.5, 27.5, 0),
    "R34": (74.0, 28.5, 0),
    "R35": (77.0, 28.5, 0),

    # CC1101 differential port and broadband balun match.
    "C40": (54.7, 17.2, 0),
    "C41": (54.7, 19.3, 0),
    "C42": (52.95, 18.25, -90),
    "B1": (57.0, 18.25, 0),
    "L40": (59.2, 17.76, 0),
    "C43": (59.9, 19.4, -90),
    "L41": (61.2, 17.76, 0),
    "C44": (61.6, 19.4, -90),

    # Dual-SP4T switches use three filter paths and a terminated unused port.
    "U3": (64.8, 18.0, 90),
    "C60": (64.4, 14.8, 0),
    "R60": (64.0, 21.3, 180),
    "L42": (67.8, 13.0, 0),
    "L43": (69.8, 13.0, 0),
    "L44": (71.8, 13.0, 0),
    "L45": (68.8, 15.0, -90),
    "C45": (70.5, 15.0, 90),
    "C46": (71.1, 11.0, 90),
    "L46": (68.3, 17.25, 0),
    "C47": (69.1, 19.6, -90),
    "L47": (70.3, 17.25, 0),
    "C48": (71.1, 19.6, -90),
    "L48": (72.3, 17.25, 0),
    "C49": (73.1, 19.6, -90),
    "L49": (74.2, 17.25, 0),
    "L50": (67.5, 23.0, 0),
    "C50": (68.3, 25.0, -90),
    "L51": (70.0, 23.0, 0),
    "C51": (71.0, 25.0, -90),
    "U4": (78.0, 18.0, -90),
    "C61": (78.25, 22.7, -90),
    "R61": (78.3, 14.7, 0),
    "C52": (81.5, 9.5, 90),
    "L52": (83.0, 11.0, 0),
    "R41": (85.0, 11.0, 0),
    "C53": (84.0, 9.5, 90),
    "C54": (86.5, 9.5, 90),
    "D5": (88.2, 11.5, 0),
}

# Preserve the CC1101 local bypass/crystal geometry while making room for the
# larger, low-band-specified RF switches. Input balun/match stays on F.Cu.
for _ref in ("U2", "C21", "C22", "C23", "C24", "C25", "C26", "C30", "R30", "Y1", "C31", "C32"):
    _x, _y, _a = PLACEMENT[_ref]
    PLACEMENT[_ref] = (_x - 2.3, _y, _a)


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
    settings.m_TrackMinWidth = mm(0.15)

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

    add_text(board, "ESP32 + CC1101 MULTIBAND  REV A3", 72, 3.0,
             pcbnew.F_SilkS, 0.8, 0.12)
    add_text(board, "USB-C", 2.0, 6.5, pcbnew.F_SilkS, 0.8, 0.11)
    add_text(board, "RST", 9.5, 30.5, pcbnew.F_SilkS, 0.8, 0.10)
    add_text(board, "BOOT", 16.0, 30.5, pcbnew.F_SilkS, 0.8, 0.10)
    add_text(board, "SMA", 85.7, 24.5, pcbnew.F_SilkS, 0.8, 0.11)
    add_text(board, "J4: 1-2 AUTO / 2-3 EXT", 17, 12.5, pcbnew.B_SilkS, .8, .12)
    add_text(board, "CONFIGURE USB BEFORE FITTING J4", 22, 14, pcbnew.B_SilkS, .8, .12)
    add_text(board, "PLACEMENT DRAFT - NOT FOR MANUFACTURE", 45, 1.0,
             pcbnew.Dwgs_User, 0.8, 0.12)

    title = board.GetTitleBlock()
    title.SetTitle("ESP32-WROOM-32E + CC1101 Multiband")
    title.SetRevision("A3 - ENGINEERING DRAFT")
    title.SetCompany("Personal prototype")
    pcbnew.SaveBoard(str(OUTPUT), board)
    # pcbnew's SWIG interface does not expose mutable stackup items. Persist
    # the reviewed, public JLC04161H-7628 proposal in KiCad's native syntax.
    # This is a target stackup, not a fabricator-confirmed impedance coupon.
    stackup = '''\n\t\t(stackup
            (layer "F.SilkS" (type "Top Silk Screen"))
            (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
            (layer "F.Cu" (type "copper") (thickness 0.035))
            (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
            (layer "In1.Cu" (type "copper") (thickness 0.0152))
            (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
            (layer "In2.Cu" (type "copper") (thickness 0.0152))
            (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
            (layer "B.Cu" (type "copper") (thickness 0.035))
            (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
            (layer "B.SilkS" (type "Bottom Silk Screen"))
            (copper_finish "ENIG") (dielectric_constraints no)
        )'''
    OUTPUT.write_text(OUTPUT.read_text().replace('(setup\n','(setup'+stackup+'\n',1))
    print(f"Saved {OUTPUT}")
    print(f"Footprints: {len(list(board.GetFootprints()))}")
    print(f"Nets: {board.GetNetCount()}")
    print("Initial ground/thermal copper only; signal/power routing omitted")


if __name__ == "__main__":
    main()
