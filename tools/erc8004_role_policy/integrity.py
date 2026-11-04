"""Preserve every historical inventory entry; additions do not reseal old evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = '80c91a09095eca362dbfb69d39d0c01fc31130cf'
sys.path.insert(0, str(ROOT / 'tools'))
from baseline_reconciliation.policy import check as preservation_check


def check():
    raw = subprocess.check_output(['git', 'show', BASE + ':artifacts.sha256.json'], cwd=ROOT)
    historical = json.loads(raw)['files']
    preservation = preservation_check(ROOT, BASE)
    bad = list(preservation['mismatches'])
    lock = json.loads((ROOT / 'conformance/erc8004-pilot-v0/source-lock.json').read_bytes())
    reused = json.loads((ROOT / 'conformance/erc8004-role-policy-v1/source-lock.json').read_bytes())
    for name, expected in reused['reused_files'].items():
        p = ROOT / name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected: bad.append('reused:' + name)
    for kind in ('implementation', 'specification'):
        entry = lock[kind]
        for name, expected in entry.get('files', {entry.get('path'): entry.get('sha256')}).items():
            p = ROOT / 'build/erc8004' / kind / name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected: bad.append('pin:' + name)
    return {'schema': 'erc8004-role-policy.preservation.v1', 'passed': not bad, 'base': BASE,
            'historical_files': len(historical), 'historical_inventory_sha256': hashlib.sha256(raw).hexdigest(),
            'preservation': preservation, 'mismatches': sorted(bad)}


if __name__ == '__main__':
    result = check(); print(json.dumps(result, sort_keys=True)); raise SystemExit(not result['passed'])
