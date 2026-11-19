"""Reproduce the reviewer experiment and isolate four previously untested guards.

Only temporary source copies are mutated. Original reports and vectors stay frozen.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from review_vectors import GUARDS

SUITE = h.ROOT / 'conformance/agent-harness-review-v0/suite.json'
ADAPTER = h.DEFAULT.parent / 'adapter.json'
SOURCE = h.ROOT / 'src/erc8404/engine.py'
REVIEWED_HEAD = '0e17c97e896916b4d9505072cc9ebe2018329b01'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def physical_edit(source, guard):
    if guard == 'reuse':
        old = "return check(record == fresh['authorization_scope'])"
        new = 'return V'
    else:
        matches = [line for line in source.splitlines() if f"statuses['{guard}'] =" in line]
        require(len(matches) == 1, 'mutation site not unique: ' + guard)
        old = matches[0]
        new = f"    statuses['{guard}'] = V  # review physical mutation"
    require(source.count(old) == 1, 'mutation not applied exactly once')
    return source.replace(old, new).encode(), old, new


def classify(baseline, mutant, restored, witness):
    row = next((r for r in mutant['rows'] if r['id'] == witness), None)
    positive = next((r for r in mutant['rows'] if r['id'] == 'permitted_review'), None)
    if mutant.get('adapter_exit_code', 0) != 0:
        return 'CRASHED'
    if baseline['exit_code'] != 0 or restored['exit_code'] != 0 or mutant['exit_code'] == 2:
        return 'UNVERIFIABLE'
    if (mutant['exit_code'] == 1 and row and positive and
            row['backend_conformance'] == 'FAIL' and positive['backend_conformance'] == 'PASS' and
            row['observed_behavior']['authorization']['authorized'] is True):
        return 'KILLED'
    return 'SURVIVED'


def subset(folder, corpus, witness):
    vectors = [r for r in corpus['vectors'] if r['name'] in ('permitted_review', witness)]
    require(len(vectors) == 2, 'missing isolated witness or positive')
    h.write(folder / 'vectors.json', {**corpus, 'vectors': vectors})
    shutil.copyfile(SUITE.parent / 'obligations.json', folder / 'obligations.json')
    h.write(folder / 'suite.json', {'id': witness,
        'vectors': {'path': 'vectors.json', 'sha256': h.sha((folder / 'vectors.json').read_bytes())},
        'obligations': {'path': 'obligations.json', 'sha256': h.sha((folder / 'obligations.json').read_bytes())}})
    return folder / 'suite.json'


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    original = SOURCE.read_bytes()
    pinned = subprocess.check_output(['git', 'show', REVIEWED_HEAD + ':src/erc8404/engine.py'], cwd=h.ROOT)
    require(original == pinned, 'consumer differs from reviewed HEAD')
    source = original.decode()
    corpus = json.loads((SUITE.parent / 'vectors.json').read_bytes())
    projections = []
    for name in ('normal', 'repeat'):
        report = h.execute(SUITE, ADAPTER, out / name)
        require(report['exit_code'] == 0, 'supplemental suite failed: ' + name)
        projections.append((out / name / 'projected.json').read_bytes())
    # Validate the finite non-redundancy claim using exact observed check outputs.
    for row in report['rows']:
        nonverified = {k: v for k, v in row['evidence']['decision']['checks'].items() if v != 'VERIFIED'}
        guard = row['id'].removesuffix('_only')
        require(nonverified == ({} if row['id'] == 'permitted_review' else {guard: 'REFUTED'}),
                'witness not isolated: ' + row['id'])
    require(projections[0] == projections[1], 'semantic replay differs')
    old_results, new_results = [], []
    with tempfile.TemporaryDirectory(prefix='review-physical-', dir=out) as temp:
        target = Path(temp)
        for name in ('src/erc8404/engine.py', 'src/v2/crypto.mjs', 'fixtures/erc8404/core-lock.json'):
            dest = target / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(h.ROOT / name, dest)
        shutil.copytree(h.ROOT / 'evidence/erc8404/core', target / 'evidence/erc8404/core')
        shutil.copytree(h.ROOT / 'build/formal-v1/crypto', target / 'build/formal-v1/crypto')
        edited = target / 'src/erc8404/engine.py'
        for group, guards, result_rows in [('original-18', ('reuse', *GUARDS), old_results),
                                           ('isolated', GUARDS, new_results)]:
            for guard in guards:
                folder = out / group / guard; folder.mkdir(parents=True, exist_ok=True)
                witness = 'tampered_admission' if guard == 'reuse' else guard + '_only'
                suite = h.DEFAULT if group == 'original-18' else subset(folder, corpus, witness)
                mutated, old, new = physical_edit(source, guard)
                baseline = h.execute(suite, ADAPTER, folder / 'baseline', target)
                edited.write_bytes(mutated)
                (folder / 'mutant.py').write_bytes(mutated)
                try:
                    observed = h.execute(suite, ADAPTER, folder / 'mutant', target)
                finally:
                    edited.write_bytes(original)
                restored = h.execute(suite, ADAPTER, folder / 'restored', target)
                result = {'guard': guard, 'witness': witness if group == 'isolated' or guard == 'reuse' else None,
                          'classification': classify(baseline, observed, restored, witness),
                          'baseline_exit': baseline['exit_code'], 'mutant_exit': observed['exit_code'],
                          'restored_exit': restored['exit_code'], 'old': old, 'new': new,
                          'original_sha256': h.sha(original), 'mutant_sha256': h.sha(mutated),
                          'restored_sha256': h.sha(edited.read_bytes())}
                result_rows.append(result)
                h.write(out / 'progress.json', {'original_18': old_results, 'isolated': new_results})
                print(group, guard, result['classification'], flush=True)
    require(SOURCE.read_bytes() == original, 'original source changed')
    old_counts = dict(Counter(r['classification'] for r in old_results))
    new_counts = dict(Counter(r['classification'] for r in new_results))
    passed = old_counts == {'KILLED': 1, 'SURVIVED': 4} and new_counts == {'KILLED': 4}
    summary = {'schema': 'agent-harness.supplemental-review.v0', 'passed': passed,
               'reviewed_head': REVIEWED_HEAD, 'consumer_sha256': h.sha(original),
               'scenario_count': len(corpus['vectors']), 'semantic_determinism': True,
               'original_18': {'mutations': old_results, 'counts': old_counts},
               'isolated': {'mutations': new_results, 'counts': new_counts},
               'consumer_source_restored': SOURCE.read_bytes() == original,
               'python': sys.version, 'platform': platform.platform(),
               'node': subprocess.check_output(['node', '--version'], text=True).strip()}
    h.write(out / 'report.json', summary)
    require(passed, 'review result differs; inspect raw evidence')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, default=h.ROOT / 'build/harness-review/controls')
    args = p.parse_args(); result = run(args.out.resolve())
    print(json.dumps({k: result[k] for k in ('passed', 'scenario_count', 'semantic_determinism')}))
