#!/usr/bin/env python3
"""Describe a routing candidate; never equate electrical DRC with RF approval."""
import json
from collections import Counter
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent


def main():
    board = pcbnew.LoadBoard(str(HERE / "A2-routing-candidate.kicad_pcb"))
    project = json.loads((HERE / "A2-routing-candidate.kicad_pro").read_text())
    classes = {p['pattern']: p['netclass'] for p in project['net_settings']['netclass_patterns']}
    counts = Counter()
    lengths = Counter()
    violations = []
    narrow_power = []
    for t in board.GetTracks():
        net = t.GetNetname()
        cls = classes.get(net, 'Default')
        if isinstance(t, pcbnew.PCB_VIA):
            counts['vias'] += 1
            if cls in ('RF_LOCAL', 'ANALOG_LOCAL', 'USB'):
                violations.append({'net': net, 'issue': 'Via on top-only net'})
            continue
        layer = board.GetLayerName(t.GetLayer())
        counts[layer] += 1
        length = pcbnew.ToMM(t.GetLength())
        lengths[net] += length
        if t.GetLayer() == pcbnew.In1_Cu:
            violations.append({'net': net, 'issue': 'Trace on ground-reference layer'})
        if cls in ('RF_LOCAL', 'ANALOG_LOCAL', 'USB') and t.GetLayer() != pcbnew.F_Cu:
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
        'not_validated': ['RF impedance/matching', 'USB differential coupling/skew',
                          'Power voltage drop and thermal behavior',
                          'Local bypass loops', 'Digital exclusion beneath RF/crystal'],
    }
    out = HERE.parent / 'reports' / 'routing-audit-A2.json'
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'counts': dict(counts), 'layer_violations': len(violations),
                      'narrow_power_segments': len(narrow_power)}, indent=2))


if __name__ == '__main__':
    main()
