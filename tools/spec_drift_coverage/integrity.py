"""Preserve exact PR12 inventory; seal only this additive research layer."""
import argparse
from pathlib import Path
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spec_drift_coverage.common import BASE, CONFIG, EVIDENCE, ROOT, Reader, require, sha, strict, write

LOCK = CONFIG/'source-lock.json'
FOLDERS = ['conformance/spec-drift-coverage-v0', 'tools/spec_drift_coverage',
           'tests/spec_drift_coverage', 'research/spec-drift-coverage-v0']


def inventory():
    files = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for name in FOLDERS
             for p in (ROOT/name).rglob('*') if p.is_file() and p != LOCK and '__pycache__' not in p.parts}
    workflow = ROOT/'.github/workflows/spec-drift-coverage.yml'
    if workflow.is_file():files[workflow.relative_to(ROOT).as_posix()] = sha(workflow.read_bytes())
    return files


def frozen():
    archived = (CONFIG/'baseline-inventory.json').read_bytes()
    original = subprocess.check_output(['git', 'show', BASE+':artifacts.sha256.json'], cwd=ROOT)
    require(archived == original, 'archived PR12 inventory changed')
    baseline = strict(archived)['files']
    require(baseline, 'empty baseline')
    mismatches = [n for n, expected in baseline.items() if not (ROOT/n).is_file() or sha((ROOT/n).read_bytes()) != expected]
    current = strict((ROOT/'artifacts.sha256.json').read_bytes())['files']
    require(all(current.get(n) == expected for n, expected in baseline.items()), 'historical root inventory entries modified')
    require(not mismatches, 'frozen files changed: ' + repr(mismatches[:10]))
    return {'passed': True, 'frozen_entries': len(baseline), 'baseline_inventory_sha256': sha(archived)}


def check():
    result = frozen()
    require(strict(LOCK.read_bytes())['files'] == inventory(), 'new research source seal mismatch')
    reader = Reader()
    imports = strict((CONFIG/'external-sources.json').read_bytes())['pr11']
    require(imports['integrated_into_base'] is False, 'PR11 integration falsely claimed')
    for item in imports['imports']:
        require(item['source_commit'] == imports['commit'], 'PR11 source commit mismatch')
        reader.raw(item['bytes'])
    path = EVIDENCE/'external/pr11/evidence/harness-review-v0'
    manifest = strict((path/'archive.json').read_bytes())
    with zipfile.ZipFile(path/'replay.zip') as z:
        require(set(z.namelist()) == set(manifest['members']), 'PR11 archive inventory mismatch')
        require(all(sha(z.read(n)) == digest for n, digest in manifest['members'].items()), 'PR11 archive byte drift')
    result.update(pr11_commit=imports['commit'], pr11_integrated=False, pr11_archive_members=len(manifest['members']), research_files=len(inventory()))
    seal=EVIDENCE/'SHA256.json'
    if seal.is_file():
        saved=strict(seal.read_bytes())['files']
        actual={p.relative_to(EVIDENCE).as_posix():sha(p.read_bytes()) for p in EVIDENCE.rglob('*') if p.is_file() and p!=seal}
        require(saved and saved==actual,'new evidence inventory mismatch')
        result['evidence_files']=len(actual)
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--seal',action='store_true');args=p.parse_args()
    if args.seal:
        frozen()
        write(LOCK, {'schema':'veca.spec-drift-research-source-lock.v0','base':BASE,'files':inventory()})
    print(__import__('json').dumps(check(),sort_keys=True))
