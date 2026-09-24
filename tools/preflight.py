#!/usr/bin/env python3
"""Run fresh KiCad checks; report prototype-order blockers, never order/export.

Exit 2 = blocked, 1 = execution/input failure, 0 = still requires owner approval.
Human review records are declarations, not proof or substitutes for inspection.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REVIEWS = {'power', 'rf', 'impedance', 'parts', 'mechanical', 'independent'}

def evaluate(erc, drc, bom, reviews):
    blockers = []
    erc_count = sum(len(sheet['violations']) for sheet in erc['sheets'])
    counts = {
        'erc_violations': erc_count,
        'candidate_drc_violations': len(drc['violations']),
        'candidate_unconnected': len(drc['unconnected_items']),
        'populated_positions_without_exact_part': sum(
            int(row['Qty per board']) > 0 and not row['Proposed part'].strip()
            for row in bom),
    }
    for name, value in counts.items():
        if value: blockers.append(f'{name}: {value}')
    if drc.get('schematic_parity'):
        blockers.append(f"candidate_schematic_parity: {len(drc['schematic_parity'])}")
    by_id = {entry['id']: entry for entry in reviews}
    if len(by_id) != len(reviews): blockers.append('Duplicate human review IDs')
    for name in sorted(REQUIRED_REVIEWS):
        entry = by_id.get(name, {})
        if (entry.get('status') != 'approved' or not entry.get('reviewer', '').strip()
                or not entry.get('evidence', '').strip()):
            blockers.append(f'Human review pending: {name}')
    return counts, blockers

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-cli', default='kicad-cli')
    parser.add_argument('--output', type=Path, help='Optional generated JSON report')
    args = parser.parse_args()
    version = subprocess.check_output([args.kicad_cli, 'version'], text=True).strip()
    with tempfile.TemporaryDirectory(prefix='cc1101-preflight-') as directory:
        reports = {}
        for kind, source, mode in [
            ('erc', 'hardware/esp32-cc1101-multiband.kicad_sch', 'sch'),
            ('drc', 'hardware/A2-routing-candidate.kicad_pcb', 'pcb'),
        ]:
            destination = Path(directory) / f'{kind}.json'
            # KiCad's default exit status does not reject unconnected items;
            # parse the generated JSON explicitly below. Do not hide exclusions.
            subprocess.run([args.kicad_cli, mode, kind, '--format', 'json',
                            '--output', str(destination), source],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            reports[kind] = json.loads(destination.read_text())
    with (ROOT / 'hardware/bom-draft.csv').open() as file:
        bom = list(csv.DictReader(file))
    reviews = json.loads((ROOT / 'hardware/preorder-reviews.json').read_text())
    counts, blockers = evaluate(reports['erc'], reports['drc'], bom, reviews['reviews'])
    # Bind this snapshot to exact project inputs. Re-run after every change.
    inputs = sorted(p for p in (ROOT / 'hardware').rglob('*') if p.is_file()
                    and p.suffix in {'.kicad_sch', '.kicad_pcb', '.kicad_pro',
                                     '.kicad_sym', '.kicad_mod', '.csv', '.json'})
    snapshot = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'revision': reviews['revision'], 'kicad_version': version,
        'status': 'BLOCKED' if blockers else 'REQUIRES_OWNER_ORDER_APPROVAL',
        'scope': 'Prototype pre-order checks only; no bench/RF/compliance validation.',
        'schematic_parity': 'Not requested: candidate has a separate basename. Independent connectivity review is mandatory.',
        'counts': counts, 'blockers': blockers,
        'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in inputs},
        'erc': reports['erc'], 'candidate_drc': reports['drc'],
    }
    if args.output:
        args.output.write_text(json.dumps(snapshot, indent=2) + '\n')
    print(snapshot['status'])
    for blocker in blockers: print(f' - {blocker}')
    print('No fabrication files generated; no order placed.')
    return 2 if blockers else 0

if __name__ == '__main__':
    raise SystemExit(main())
