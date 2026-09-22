#!/usr/bin/env python3
"""Offline checks for the staged/public repository, not an electrical review."""
from pathlib import Path
import csv
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    tracked = [p for p in tracked if p]
    problems = []
    for name in tracked:
        p = ROOT / name
        if any(part in ('.pio', '__pycache__', 'tmp', 'logs', 'checkpoints') for part in p.relative_to(ROOT).parts):
            problems.append(f'Local-only content tracked: {name}')
        if p.suffix in ('.kicad_prl', '.pem', '.key') or p.name.startswith('.env'):
            problems.append(f'Private/editor-state file tracked: {name}')
        if p.suffix != '.md':
            continue
        content = p.read_text()
        targets = re.findall(r'\]\(([^)]+)\)', content)
        targets += re.findall(r'(?:src|href)="([^"]+)"', content)
        for target in targets:
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            target = target.split('#')[0]
            if target and not (p.parent / target).exists():
                problems.append(f'Broken local link in {name}: {target}')
    audit = json.loads((ROOT / 'reports/design-audit.json').read_text())
    assert audit['status'] == 'PASS'
    assert len(audit['checks']) == 115 and all(c['pass'] for c in audit['checks'])
    for report, unconnected in [('drc-A2-placement.json', 217), ('drc-A2-routing-candidate.json', 23)]:
        data = json.loads((ROOT / 'reports' / report).read_text())
        assert len(data['violations']) == 0, report
        assert len(data['unconnected_items']) == unconnected, report
    with (ROOT / 'hardware/bom-draft.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert sum(int(r['Qty per board']) for r in rows) == 81
    assert sum(r['Status'] == 'VERIFY_STOCK_AND_ASSEMBLY' for r in rows) == 63
    assert sum(r['Status'] == 'SELECT_EXACT_PART' for r in rows) == 18
    if problems:
        raise SystemExit('\n'.join(problems))
    print(f'PASS: {len(tracked)} tracked files; Markdown links and published A2 counts checked.')
    print('This is not a secret-scanning guarantee, license opinion or engineering approval.')


if __name__ == '__main__':
    main()
