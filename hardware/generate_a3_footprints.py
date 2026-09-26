#!/usr/bin/env python3
"""Manufacturer land patterns for A3; dimensions in mm, viewed from top.

PE42442 DOC-33414-9.02 fig 18: 0.3x0.6 pads, 0.5 pitch,
4.4 outer span and 2.75 EP. Diodes DS41326 rev3-2 p17: 0.7x1.0,
0.95 pitch and 3.2 outer span. No open via-in-pad in these custom parts.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'lib/esp32_cc1101.pretty'

def footprint(name, body, courtyard, pads, ep=None):
    lines = [f'(footprint "{name}" (version 20240108) (generator "pcbnew") (layer "F.Cu")',
             '(attr smd)',
             '(property "Reference" "REF**" (at 0 -3 0) (layer "F.SilkS") (effects (font (size 0.8 0.8))))',
             f'(property "Value" "{name}" (at 0 3 0) (layer "F.Fab") (effects (font (size 0.8 0.8))))']
    for layer, x, y, width in [('F.Fab', *body, .1), ('F.CrtYd', *courtyard, .05)]:
        lines.append(f'(fp_rect (start {-x} {-y}) (end {x} {y}) (stroke (width {width}) (type solid)) (fill none) (layer "{layer}"))')
    lines.append(f'(fp_circle (center {-courtyard[0]} {-courtyard[1]}) (end {-courtyard[0]+.1} {-courtyard[1]}) (stroke (width .1) (type solid)) (fill solid) (layer "F.SilkS"))')
    for n,x,y,w,h in pads:
        lines.append(f'(pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Mask" "F.Paste"))')
    if ep:
        n, size = ep
        lines.append(f'(pad "{n}" smd rect (at 0 0) (size {size} {size}) (layers "F.Cu" "F.Mask"))')
        # Four paste windows, ~58% area; exposed pad must be soldered to ground.
        for x in (-.7,.7):
            for y in (-.7,.7):
                lines.append(f'(pad "" smd rect (at {x} {y}) (size 1.05 1.05) (layers "F.Paste"))')
    (OUT / f'{name}.kicad_mod').write_text('\n'.join(lines)+'\n)\n')

def main():
    pads = []
    for i in range(6):
        v = round(-1.25 + .5*i, 3)
        pads += [(i+1,-1.9,v,.6,.3), (i+7,v,1.9,.3,.6),
                 (i+13,1.9,-v,.6,.3), (i+19,-v,-1.9,.3,.6)]
    footprint('pSemi_PE42442_QFN24', (2,2), (2.45,2.45), pads, (25,2.75))
    pads = [(1,-1.1,-.95,1,.7),(2,-1.1,0,1,.7),(3,-1.1,.95,1,.7),
            (4,1.1,.95,1,.7),(5,1.1,0,1,.7),(6,1.1,-.95,1,.7)]
    footprint('Diodes_TSOT26', (.8,1.45), (1.85,1.75), pads)

if __name__ == '__main__': main()
