#!/usr/bin/env python3
"""Remove machine-local source paths from generated netlist metadata only."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for suffix in ('.net','.xml'):
    path=ROOT/'hardware'/('esp32-cc1101-multiband'+suffix)
    text=path.read_text()
    text=text.replace(str(ROOT)+'/', '')
    path.write_text(text)
