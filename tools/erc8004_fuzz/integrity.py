"""Verify frozen baseline plus a separate finite research-source seal."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h

FOLDERS = ('conformance/erc8004-property-fuzz-v0', 'research/erc8004-property-fuzz-v0', 'tools/erc8004_fuzz')
LOCK = h.ROOT / FOLDERS[0] / 'campaign-lock.json'
BASELINE = h.ROOT / FOLDERS[0] / 'baseline-inventory.json'
BASE = '80c91a09095eca362dbfb69d39d0c01fc31130cf'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    result = {p.relative_to(h.ROOT).as_posix(): digest(p) for directory in FOLDERS
            for p in (h.ROOT / directory).rglob('*')
            if p.is_file() and p != LOCK and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    workflow = h.ROOT / '.github/workflows/erc8004-property-fuzz.yml'
    if workflow.is_file():
        result[workflow.relative_to(h.ROOT).as_posix()] = digest(workflow)
    return result


def check():
    original_inventory = subprocess.check_output(['git', 'show', BASE + ':artifacts.sha256.json'], cwd=h.ROOT)
    baseline = json.loads(BASELINE.read_bytes())['files']
    problems = [name for name, expected in baseline.items() if not (h.ROOT / name).is_file() or digest(h.ROOT / name) != expected]
    if original_inventory != BASELINE.read_bytes():
        problems.append('baseline_inventory_not_exact_base_blob')
    current = json.loads((h.ROOT / 'artifacts.sha256.json').read_bytes())['files']
    if any(current.get(name) != value for name, value in baseline.items()):
        problems.append('root_inventory_changed_historical_entry')
    sources = json.loads((h.ROOT / FOLDERS[0] / 'source-lock.json').read_bytes())
    for name, expected in sources['preserved'].items():
        if digest(h.ROOT / name) != expected:
            problems.append('preserved:' + name)
    for name, expected in sources['implementation']['files'].items():
        if digest(h.ROOT / 'build/erc8004/implementation' / name) != expected:
            problems.append('implementation:' + name)
    spec = sources['specification']
    if digest(h.ROOT / 'build/erc8004/specification' / spec['path']) != spec['sha256']:
        problems.append('specification')
    saved = json.loads(LOCK.read_bytes())
    actual = inventory()
    if saved.get('files') != actual or not actual:
        problems.append('research_inventory')
    baseline_inventory_preserved = saved.get('baseline_inventory_sha256') == digest(BASELINE)
    if not baseline_inventory_preserved:
        problems.append('baseline_inventory_identity')
    checkpoint = json.loads((h.ROOT / 'build/fuzz-continuation/checkpoint/manifest.json').read_bytes())
    archive = h.ROOT / 'build/fuzz-continuation/checkpoint/inherited-research.zip'
    if digest(archive) != checkpoint['archiveSha256']:
        problems.append('inherited_research_archive')
    original_research = {name: value for name, value in checkpoint['files'].items() if not name.startswith('build/')}
    with zipfile.ZipFile(archive) as backup:
        if set(backup.namelist()) != set(original_research) or any(
                hashlib.sha256(backup.read(name)).hexdigest() != value for name, value in original_research.items()):
            problems.append('inherited_research_archive_members')
    retained = {name: value for name, value in checkpoint['files'].items() if name.startswith('build/')}
    for name, expected in retained.items():
        if digest(h.ROOT / name) != expected:
            problems.append('inherited_evidence:' + name)
    if (h.ROOT / FOLDERS[0] / 'fixtures.json').read_bytes() != (h.ROOT / 'build/fuzz-continuation/campaign-normal/fixtures.json').read_bytes():
        problems.append('campaign_fixture_identity')
    return {'passed': not problems, 'mismatches': problems, 'frozen_files': len(baseline),
            'research_files': len(actual), 'inherited_evidence_files': len(retained),
            'inherited_research_archive_files': len(original_research),
            'baseline_inventory_preserved': baseline_inventory_preserved,
            'root_inventory_extension_only': not any(current.get(n) != v for n, v in baseline.items())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seal', action='store_true')
    args = parser.parse_args()
    if args.seal:
        h.write(LOCK, {'schema': 'erc8004.generated-research-source-lock.v0',
                      'baseline_inventory_sha256': digest(BASELINE), 'files': inventory()})
    result = check()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(not result['passed'])
