"""Explicit composition contract; no Core transition and no historical resealing."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_artifacts

MAIN = '999e7047df15585f8ce0629081a1369a4942353f'
BASE = '80c91a09095eca362dbfb69d39d0c01fc31130cf'
PR12 = '6e8fabee9be170245f557a271b6d315176cc4a03'
PR13 = 'c0d3862a590b62a059c1a923ab93b380d609876f'
POLICY = 'research/pr12-pr13-integration-v1/TRANSITION.json'
POLICY_SHA256 = 'cb1f1afcd6836e183f481607a7f8ba08aa444ac109f96c0b4253bf86c91f3af7'
MANIFEST_PINS = {'80c91a09095eca362dbfb69d39d0c01fc31130cf': '46f11963412be66b3b0602c2f2da93a706c516ce844eff0c71ef1472cbbb9719', '999e7047df15585f8ce0629081a1369a4942353f': '5e20a46f3004a4afa869ca014accc7505cb9a3c7ae0536fb7c8cc9909700b30a', '6e8fabee9be170245f557a271b6d315176cc4a03': 'f7f5f7fc26fad06a0c16462156a8403f828058bb12305714d4acc5715f6ff329', 'c0d3862a590b62a059c1a923ab93b380d609876f': '87ab212682566d86fb725153b5b91ae01894e8974e2e412896e00ab3e1ed6014'}
TRANSITIONS = ('conformance/agent-harness-v0/README.md',
               'research/harness-v0/LIMITATIONS.md', 'tools/erc8004/integrity.py')
WORKFLOWS = {
    '.github/workflows/erc8004-property-fuzz.yml': (
        (b'tools/erc8004_fuzz/validate.py', b'tools/pr12_pr13_integration/fuzz_validate.py'),),
    '.github/workflows/spec-drift-coverage.yml': (
        (b'tools/spec_drift_coverage/validate.py', b'tools/pr12_pr13_integration/spec_validate.py'),
        (b'tools/spec_drift_coverage/drift.py', b'tools/pr12_pr13_integration/spec_cli.py drift')),
}
NEW_FILES = (
    POLICY,
    'research/pr12-pr13-integration-v1/README.md',
    'research/pr12-pr13-integration-v1/REPORT.md',
    'tools/pr12_pr13_integration/preservation.py',
    'tools/pr12_pr13_integration/controls.py',
    'tools/pr12_pr13_integration/fuzz_validate.py',
    'tools/pr12_pr13_integration/spec_validate.py',
    'tools/pr12_pr13_integration/spec_cli.py',
    'tools/pr12_pr13_integration/spec_controls.py',
    'tools/pr12_pr13_integration/runtime_binding.py',
    'evidence/pr12-pr13-integration-v1/README.md',
    'evidence/pr12-pr13-integration-v1/RESULTS.json',
    'evidence/pr12-pr13-integration-v1/EVIDENCE.zip',
    'evidence/pr12-pr13-integration-v1/SHA256.json',
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def git(ref, path, root=ROOT):
    return subprocess.check_output(['git', 'show', ref + ':' + path], cwd=root)


def manifest(ref, root=ROOT):
    raw = git(ref, 'artifacts.sha256.json', root)
    require(sha(raw) == MANIFEST_PINS[ref], 'historical manifest identity: ' + ref)
    return json.loads(raw)['files']


def policy(raw):
    require(sha(raw) == POLICY_SHA256, 'transition_manifest_identity')
    return json.loads(raw)


def contract(root=ROOT):
    p = policy((root / POLICY).read_bytes())
    base, main, twelve, thirteen = [manifest(ref, root) for ref in (BASE, MAIN, PR12, PR13)]
    require(set(n for n, d in base.items() if main.get(n) != d) == set(TRANSITIONS),
            'main historical transition scope')
    require(p['core_changes_permitted'] is False, 'Core transition forbidden')
    require(set(p['transitions']) == set(TRANSITIONS), 'exact transition paths required')
    for path in TRANSITIONS:
        row = p['transitions'][path]
        require(row['before_sha256'] == base[path] and row['after_sha256'] == main[path],
                'transition identities: ' + path)
        require(sha(git(row['review_commit'], path, root)) == main[path], 'reviewed transition bytes')
        require(subprocess.run(['git', 'merge-base', '--is-ancestor', row['review_commit'], MAIN],
                               cwd=root, capture_output=True).returncode == 0, 'review ancestry')
    expected = dict(main)
    for old, new, count in ((base, twelve, 36), (twelve, thirteen, 38)):
        require(all(new.get(n) == d for n, d in old.items()), 'historical PR is not additive')
        additions = {n: d for n, d in new.items() if n not in old}
        require(len(additions) == count and not set(additions) & set(expected), 'disjoint exact PR payload')
        expected.update(additions)
    for path, substitutions in WORKFLOWS.items():
        raw = git(PR13, path, root)
        for before, after in substitutions:
            require(raw.count(before) == 1, 'workflow replacement not unique')
            raw = raw.replace(before, after)
        expected[path] = sha(raw)
    require(p['new_files'] == list(NEW_FILES), 'new-file scope')
    # Source manifests, original vectors, all Core files and original reports
    # retain their independently authenticated Git-baseline identities.
    require(all(expected[n] == d for n, d in main.items()), 'main files must remain unchanged')
    return expected


def evaluate(expected, observed, inventory):
    bad = []
    if set(expected) != set(observed) or set(expected) != set(inventory):
        bad.append('inventory_membership')
    for path, digest in expected.items():
        if observed.get(path) != digest or inventory.get(path) != digest:
            bad.append('preservation:' + path)
    return {'passed': not bad, 'mismatches': sorted(bad)}


def check(root=ROOT):
    root = Path(root)
    expected = contract(root)
    current = json.loads((root / 'artifacts.sha256.json').read_bytes())
    require(current['schema'] == 'sha256-inventory-v0' and
            current['excludes'] == ['self', 'git', 'build', 'pycache', 'venv'], 'inventory contract unchanged')
    require(not set(expected) & set(NEW_FILES), 'new file collides with historical file')
    expected.update({n: current['files'].get(n) for n in NEW_FILES})
    require(all(expected[n] for n in NEW_FILES), 'missing new-file inventory')
    # Same enumeration as the unchanged complete-inventory verifier.
    old = verify_artifacts.ROOT
    try:
        verify_artifacts.ROOT = root
        old_manifest = verify_artifacts.MANIFEST
        verify_artifacts.MANIFEST = root / 'artifacts.sha256.json'
        observed = verify_artifacts.inventory()
    finally:
        verify_artifacts.ROOT = old
        verify_artifacts.MANIFEST = old_manifest
    result = evaluate(expected, observed, current['files'])
    require(result['passed'], '; '.join(result['mismatches'][:12]))
    result.update(schema='veca-pr12-pr13-preservation-v1', historical_files=len(expected)-len(NEW_FILES),
                  new_files=len(NEW_FILES), core_transition_allowed=False,
                  main=MAIN, pr12=PR12, pr13=PR13,
                  conformance_claim=False, independent_review='NOT_ESTABLISHED')
    return result


def fuzz_history():
    # Retain every old dependency/archive/fixture guard and demand exactly the
    # documented old-contract refusal, not a successful historical verdict.
    from erc8004_fuzz import integrity
    original = integrity.check()
    require(original['passed'] is False and set(original['mismatches']) ==
            set(TRANSITIONS) | {'root_inventory_changed_historical_entry', 'research_inventory'},
            'unexpected historical fuzz integrity result: ' + repr(original))
    return {'classification': 'EXPECTED_OLD_CONTRACT_REFUSAL', 'original': original,
            'integration': check()}


if __name__ == '__main__':
    print(json.dumps(fuzz_history() if '--fuzz' in sys.argv else check(), sort_keys=True))
