#!/usr/bin/env python3
"""Describe a routing candidate; never equate electrical DRC with RF approval."""
import json
from collections import Counter
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent


def main():
    board = pcbnew.LoadBoard(str(HERE / "A3-routing-candidate.kicad_pcb"))
    project = json.loads((HERE / "A3-routing-candidate.kicad_pro").read_text())
    classes = {p['pattern']: p['netclass'] for p in project['net_settings']['netclass_patterns']}
    counts = Counter()
    lengths = Counter()
    violations = []
    narrow_power = []
    in_pad = []
    usb_crossover_vias = []
    for t in board.GetTracks():
        net = t.GetNetname()
        cls = classes.get(net, 'Default')
        if isinstance(t, pcbnew.PCB_VIA):
            counts['vias'] += 1
            pos = [round(pcbnew.ToMM(t.GetPosition().x),3),round(pcbnew.ToMM(t.GetPosition().y),3)]
            allowed = net == '/USB_DM_CONN' and pos in ([6.1,17.25],[8.7,18.25])
            if allowed: usb_crossover_vias.append(pos)
            if cls in ('RF_LOCAL', 'ANALOG_LOCAL', 'USB') and not allowed:
                violations.append({'net': net, 'issue': 'Via on top-only net'})
            for f in board.GetFootprints():
                for pad in f.Pads():
                    if (pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and pad.GetNumber()
                            and pad.IsOnLayer(pcbnew.F_Cu) and pad.HitTest(t.GetPosition())):
                        in_pad.append({'reference':f.GetReference(),'pad':pad.GetNumber(),
                                       'position_mm':pos,'requirement':'RESIN_FILLED_COPPER_CAPPED'})
            continue
        layer = board.GetLayerName(t.GetLayer())
        counts[layer] += 1
        length = pcbnew.ToMM(t.GetLength())
        lengths[net] += length
        if t.GetLayer() == pcbnew.In1_Cu:
            violations.append({'net': net, 'issue': 'Trace on ground-reference layer'})
        if (cls in ('RF_LOCAL', 'ANALOG_LOCAL', 'USB') and t.GetLayer() != pcbnew.F_Cu
                and not (net=='/USB_DM_CONN' and t.GetLayer()==pcbnew.B_Cu)):
            violations.append({'net': net, 'issue': 'Off-top route', 'layer': layer})
        if cls == 'POWER' and pcbnew.ToMM(t.GetWidth()) < .399:
            narrow_power.append({'net': net, 'width_mm': round(pcbnew.ToMM(t.GetWidth()), 3),
                                 'length_mm': round(length, 3)})
    report = {
        'status': 'EXPERIMENT_ONLY_NOT_RELEASED',
        'track_segments_by_layer_and_vias': dict(counts),
        'total_trace_length_by_net_mm': {k: round(v, 3) for k, v in sorted(lengths.items())},
        'layer_constraint_violations': violations,
        'power_segments_below_0_40_mm_require_review': narrow_power,
        'intentional_USB_DM_connector_crossover_vias_mm': usb_crossover_vias,
        'via_centers_inside_numbered_SMD_pads': in_pad,
        'via_screen_limit': 'Center-inside-pad screen only; assembler must review every pad-adjacent via too.',
        'crystal_review': 'Pin-10 placement exceeds the retained 3.5 mm screening target. Total net lengths include load-cap branches, not just IC-to-crystal length.',
        'not_validated': ['RF impedance/matching', 'USB differential coupling/skew',
                          'Power voltage drop and thermal behavior',
                          'Local bypass loops', 'Digital exclusion beneath RF/crystal'],
    }
    out = HERE.parent / 'reports' / 'routing-audit-A3.json'
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'counts': dict(counts), 'layer_violations': len(violations),
                      'narrow_power_segments': len(narrow_power)}, indent=2))


if __name__ == '__main__':
    main()
