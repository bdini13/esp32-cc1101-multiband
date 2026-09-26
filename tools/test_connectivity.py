#!/usr/bin/env python3
"""Fault-inject temporary PCB copies; never modify the review candidate."""
from pathlib import Path
import sys
import tempfile
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hardware'))
from audit_connectivity import compare

source=ROOT/'hardware/A3-routing-candidate.kicad_pcb'
xml=ROOT/'hardware/esp32-cc1101-multiband.xml'
assert not compare(xml,source)
with tempfile.TemporaryDirectory(prefix='cc1101-parity-test-') as directory:
    out=Path(directory)/'injected.kicad_pcb'
    for kind in ('net','value','footprint','missing'):
        b=p.LoadBoard(str(source))
        f=next(f for f in b.GetFootprints() if f.GetReference()=='R31')
        if kind=='net':
            pad=next(q for q in f.Pads() if q.GetNumber()=='1')
            pad.SetNet(b.FindNet('/GND'))
        elif kind=='value':f.SetValue('WRONG')
        elif kind=='footprint':f.SetFPID(p.LIB_ID('Wrong','Wrong'))
        else:b.Remove(f)
        p.SaveBoard(str(out),b)
        assert compare(xml,out),kind+' fault was not detected'
        print('PASS: injected '+kind+' mismatch rejected')
print('PASS: fresh schematic parity and four fault-injected temporary boards')
