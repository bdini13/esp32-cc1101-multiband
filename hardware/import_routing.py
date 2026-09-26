#!/usr/bin/env python3
"""Import a router experiment to a separate candidate for native KiCad DRC."""
from pathlib import Path
import sys
import shutil
import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    source = ROOT / sys.argv[2] if len(sys.argv) > 2 else HERE / "esp32-cc1101-multiband.kicad_pcb"
    session = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "tmp/A3-route-v1.ses")
    board = pcbnew.LoadBoard(str(source))
    if not pcbnew.ImportSpecctraSES(board, str(session)):
        raise RuntimeError("SES import failed")
    board.BuildConnectivity()
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("Refill failed")
    out = HERE / "A3-routing-candidate.kicad_pcb"
    pcbnew.SaveBoard(str(out), board)
    shutil.copyfile(source.with_suffix('.kicad_pro'), out.with_suffix('.kicad_pro'))
    print(out)


if __name__ == "__main__":
    main()
