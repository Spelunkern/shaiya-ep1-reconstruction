#!/usr/bin/env python3
"""Require exactly the published PE corpus in Git; exclude original data/config/log files."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    original = json.loads((ROOT/'manifests/originals.json').read_text())
    public = json.loads((ROOT/'manifests/public-binaries.json').read_text())
    expected = [f for f in original['files'] if 'pe' in f]
    assert public['scope'] == 'pe-binaries-only' and public['files'] == expected
    assert public['binaries'] == original['binaries']
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    actual = {p for p in tracked if p.startswith(('Client/','Server/'))}
    wanted = {f['path'] for f in expected}
    assert actual == wanted, f'Distribution mismatch; missing={sorted(wanted-actual)}, forbidden={sorted(actual-wanted)}'
    print(f'PASS public distribution: {len(actual)} PE paths only; no client assets, server databases, configurations or logs')

if __name__ == '__main__':
    main()
