#!/usr/bin/env python3
"""Compare a PCB against a freshly exported schematic XML; never repair it."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import pcbnew

def compare(xml, pcb):
    root=ET.parse(xml).getroot()
    board=pcbnew.LoadBoard(str(pcb))
    fps={f.GetReference():f for f in board.GetFootprints()}
    comps={c.attrib['ref']:c for c in root.findall('components/comp') if c.findtext('footprint','')}
    nets={(n.attrib['ref'],n.attrib['pin']):net.attrib['name']
          for net in root.findall('nets/net') for n in net.findall('node')}
    problems=[]
    for ref,c in comps.items():
        if ref not in fps:
            problems.append(ref+': missing PCB footprint');continue
        f=fps[ref]
        if f.GetValue()!=c.findtext('value'): problems.append(ref+': value mismatch')
        # Generated footprints have local name IDs; compare actual leaf names.
        expected=c.findtext('footprint').split(':')[-1]
        if str(f.GetFPID().GetLibItemName())!=expected: problems.append(ref+': footprint mismatch')
        numbers=set()
        for p in f.Pads():
            number=p.GetNumber()
            if not number:continue
            numbers.add(number)
            if nets.get((ref,number),'')!=p.GetNetname():
                problems.append(ref+'.'+number+': net mismatch')
        for r,number in nets:
            if r==ref and number not in numbers: problems.append(ref+'.'+number+': missing pad')
    for ref in fps.keys()-comps.keys():
        if not ref.startswith('MH'):problems.append(ref+': unexpected electrical footprint')
    return problems

if __name__=='__main__':
    problems=compare(Path(sys.argv[1]),Path(sys.argv[2]))
    Path(sys.argv[3]).write_text(json.dumps(problems,indent=2)+'\n')
    print('Schematic/PCB connectivity: '+('FAIL' if problems else 'PASS'))
    for problem in problems:print(problem)
    raise SystemExit(bool(problems))
