"""Physical policy mutations with real EVM baseline/mutant/restored execution."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import agent_harness as h

PROFILE = ROOT / 'conformance/erc8004-role-policy-v1'
SOURCE = ROOT / 'tools/erc8004_role_policy/policy.py'


def classify(baseline, mutated, restored, witness, original, changed, restored_bytes):
    if original == changed: return 'NO_OP'
    if restored_bytes != original: return 'RESTORATION_FAILED'
    if baseline.get('backend_conformance') != 'PASS' or restored.get('backend_conformance') != 'PASS':
        return 'CONTROL_BROKEN'
    if mutated.get('adapter_exit_code', 1) != 0: return 'CRASHED'
    if mutated.get('exit_code') == 2: return 'UNVERIFIABLE'
    rows = {r['id']: r for r in mutated.get('rows', [])}
    if witness not in rows or 'separate_validator' not in rows: return 'MISSING_OUTPUT'
    bad, good = rows[witness], rows['separate_validator']
    if good['backend_conformance'] != 'PASS': return 'CONTROL_BROKEN'
    obs = bad.get('observed_behavior')
    if obs is None: return 'MISSING_OUTPUT'
    if bad['backend_conformance'] == 'FAIL' and obs['authorization']['status'] == 'VERIFIED':
        return 'KILLED'
    return 'SURVIVED'


def run(out):
    original = SOURCE.read_bytes()
    corpus = json.loads((PROFILE / 'vectors.json').read_bytes())
    by_name = {v['name']: v for v in corpus['vectors']}
    definitions = [('owner', 'owner_self', 'R1'), ('operator', 'operator_self', 'R2'),
                   ('approved', 'approved_self', 'R3'), ('binding', 'wrong_block', 'R7'),
                   ('version', 'wrong_version', 'R5'), ('claim', 'wrong_claim', 'R5'),
                   ('request_time', 'operator_revoked', 'R4')]
    results = []
    for marker, witness, obligation in definitions:
        folder = out / marker
        folder.mkdir(parents=True, exist_ok=True)
        h.write(folder / 'vectors.json', {'profile': corpus['profile'], 'vectors': [by_name[witness], by_name['separate_validator']]})
        shutil.copyfile(PROFILE / 'obligations.json', folder / 'obligations.json')
        h.write(folder / 'suite.json', {'id': marker, **{k: {'path': k + '.json', 'sha256': h.sha((folder / (k + '.json')).read_bytes())}
                                                      for k in ('vectors', 'obligations')}})
        target = folder / 'policy.py'
        target.write_bytes(original)
        h.write(folder / 'adapter.json', {'argv': ['{python}', '-B', str(ROOT / 'tools/erc8004_role_policy/adapter.py'), '--policy-file', str(target)]})
        baseline = h.execute(folder / 'suite.json', folder / 'adapter.json', folder / 'baseline')
        raw = original.decode()
        if marker == 'request_time':
            before = "evidence = observed.get('request_roles')"
            after = "evidence = {**observed['request_roles'], **{k: observed['response_roles'][k] for k in ('owner', 'operator', 'approved')}}"
        elif marker == 'binding':
            start = raw.index("    if (receipt['status']")
            end = raw.index('  # guard: binding', start)
            before, after = raw[start:end], '    if False:'
        else:
            lines = [line for line in raw.splitlines() if line.endswith('# guard: ' + marker)]
            if len(lines) != 1: raise ValueError('mutation site not unique')
            before, after = lines[0], '    if False:  # removed ' + marker
        if raw.count(before) != 1: raise ValueError('mutation site not unique')
        changed = raw.replace(before, after, 1).encode()
        record = {'id': marker, 'obligation': obligation, 'witness': witness, 'positive': 'separate_validator',
                  'source': SOURCE.relative_to(ROOT).as_posix(), 'original_sha256': h.sha(original),
                  'mutant_sha256': h.sha(changed), 'before': before, 'after': after}
        target.write_bytes(changed)
        (folder / 'mutated-policy.py.txt').write_bytes(changed)
        try:
            mutated = h.execute(folder / 'suite.json', folder / 'adapter.json', folder / 'mutated')
        finally:
            target.write_bytes(original)
        restored = h.execute(folder / 'suite.json', folder / 'adapter.json', folder / 'restored')
        record['classification'] = classify(baseline, mutated, restored, witness, original, changed, target.read_bytes())
        record['byte_restored'] = target.read_bytes() == original
        record['semantic_restored'] = (folder / 'baseline/projected.json').read_bytes() == (folder / 'restored/projected.json').read_bytes()
        record['same_request'] = len({(folder / phase / 'request.json').read_bytes() for phase in ('baseline', 'mutated', 'restored')}) == 1
        if not record['semantic_restored'] or not record['same_request']: record['classification'] = 'UNVERIFIABLE'
        results.append(record)
        report = {'schema': 'erc8004-role-policy.mutations.v1', 'results': results,
                  'counts': {s: sum(r['classification'] == s for r in results) for s in
                             ('KILLED', 'SURVIVED', 'CRASHED', 'NO_OP', 'MISSING_OUTPUT', 'CONTROL_BROKEN', 'RESTORATION_FAILED', 'UNVERIFIABLE')}}
        h.write(out / 'report.json', report)
        print(marker, record['classification'], flush=True)
    if SOURCE.read_bytes() != original: raise RuntimeError('production policy changed')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, required=True)
    result = run(p.parse_args().out.resolve())
    raise SystemExit(0 if result['counts']['KILLED'] == 7 else 1)
