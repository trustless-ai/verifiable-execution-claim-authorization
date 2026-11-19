"""Reconcile executed reports, never substitute a modeled result for execution."""
import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from erc8004_fuzz import generate, model
from erc8004_fuzz.shrink import divergence


def read(path):
    return json.loads(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    fixtures = generate.build()
    cases = {c['id']: c for c in fixtures['cases']}
    campaigns = {}
    for mode in ('normal', 'repeat', 'optimized'):
        folder = root / ('campaign-' + mode)
        summary = read(folder / 'summary.json')
        require(read(folder / 'fixtures.json') == fixtures, 'fixture drift: ' + mode)
        rows = []
        for batch in read(folder / 'batches.json'):
            directory = folder / batch['path']
            report = read(directory / 'run/report.json')
            corpus = read(directory / 'vectors.json')
            request_raw = (directory / 'run/request.json').read_bytes()
            require(read(directory / 'run/request.json') == h.detached_request(corpus), 'request contains unexpected fields')
            require(h.sha(request_raw) == report['request_sha256'], 'request digest mismatch')
            for sent in read(directory / 'run/request.json')['cases']:
                require(sent['input'] == cases[sent['id']]['input'], 'IUT received non-fixture input')
            require(report['exit_code'] == 0 and report['backend_conformance'] == 'PASS', 'failed batch: ' + mode)
            rows.extend(report['rows'])
        require(len(rows) == 300 and {r['id'] for r in rows} == set(cases), 'incomplete cases: ' + mode)
        projection = {r['id']: r['observed_behavior'] for r in rows}
        require(projection == read(folder / 'projection.json'), 'projection drift: ' + mode)
        for row in rows:
            want = model.expected(cases[row['id']]['input'])
            require(row['backend_conformance'] == 'PASS' and row['expected_behavior'] == want
                    and row['observed_behavior'] == want, 'row disagreement: ' + row['id'])
        operations = Counter()
        for row in rows:
            for op, step in zip(cases[row['id']]['input']['sequence'], row['observed_behavior']['behavior']['steps']):
                operations[op['kind'] + ':' + step['status']] += 1
        require(summary['passed'] and summary['executed'] == 300 and summary['conformance'] == {'PASS': 300}, 'summary failure')
        require(summary['fixture_sha256'] == h.sha(h.encode(fixtures)), 'fixture hash mismatch')
        require(summary['projection_sha256'] == h.sha(h.encode(projection)), 'projection hash mismatch')
        require(summary['operation_statuses'] == dict(operations), 'operation summary mismatch')
        require(summary['optimized'] == (mode == 'optimized'), 'optimization mode mismatch')
        campaigns[mode] = summary
    require(len({s['projection_sha256'] for s in campaigns.values()}) == 1, 'semantic repeatability failure')
    mutations = read(root / 'mutations/report.json')
    require(len(mutations['results']) == 6 and mutations['counts'] == {'KILLED': 6}
            and mutations['original_source_unchanged'], 'mutation closure failure')
    for record in mutations['results']:
        folder = root / 'mutations' / record['id']
        require(record['positive_controls'] and record['restored_pass'] and record['restored_source_bytes'], 'control failure')
        for phase in ('baseline', 'restored'):
            report = read(folder / phase / 'report.json')
            require(len(report['rows']) == 4 and report['backend_conformance'] == 'PASS', 'baseline/restoration failure')
        old = read(folder / 'original-matrix/report.json')
        require(len(old['rows']) == 29 and old['exit_code'] in (0, 1), 'old matrix not executed')
        mutated = read(folder / 'mutated/report.json')
        by_id = {r['id']: r for r in mutated['rows']}
        require(len(by_id) == 4 and mutated['exit_code'] == 1, 'missing determinate mutated execution')
        require(divergence(by_id[record['witness_id']], cases[record['witness_id']]['input']) == record['divergence'], 'mutated witness mismatch')
        require(all(by_id['control-%d' % i]['backend_conformance'] == 'PASS' for i in range(3)), 'mutant broke positive controls')
        require(h.sha((folder / 'mutated-source.sol').read_bytes()) == record['mutant_sha256'], 'mutated source drift')
        require(h.sha((folder / 'implementation' / record['source']).read_bytes()) == record['original_sha256'], 'restored source bytes differ')
        shrunk = read(folder / 'shrink/result.json')
        require(shrunk['deletion_1_minimal'] and not shrunk['global_minimum_claimed'], 'unsupported minimality')
        require(shrunk['attempts'][-1]['stage'] == 'final-replay' and shrunk['attempts'][-1]['retained'], 'missing final witness')
        final = shrunk['attempts'][-1]
        final_rows = {r['id']: r for r in read(folder / 'shrink' / final['report'])['rows']}
        require(divergence(final_rows[final['case']], shrunk['minimized']) == record['divergence'], 'final witness disagreement')
    baseline = read(h.ROOT / 'build/fuzz-start/baseline/summary.json')
    require(baseline['passed'] and baseline['conformant'] == 29 and baseline['mutations']['KILLED'] == 17, 'inherited baseline failure')
    checkpoint = read(h.ROOT / 'build/fuzz-continuation/checkpoint/manifest.json')
    fixture_path = 'conformance/erc8004-property-fuzz-v0/fixtures.json'
    require(checkpoint['files'][fixture_path] == h.sha((h.ROOT / fixture_path).read_bytes()), 'inherited fixture inputs changed')
    distinct_inputs = len({h.sha(h.encode(c['input'])) for c in cases.values()})
    distinct_sequences = len({h.sha(h.encode(c['input']['sequence'])) for c in cases.values()})
    return {'schema': 'erc8004.property-research-closure.v0', 'passed': True,
            'base': '80c91a09095eca362dbfb69d39d0c01fc31130cf', 'python': platform.python_version(),
            'unique_case_ids': len(cases), 'distinct_inputs': distinct_inputs, 'distinct_sequences': distinct_sequences,
            'sequence_lengths': dict(Counter(str(len(c['input']['sequence'])) for c in cases.values())),
            'campaigns': campaigns, 'semantic_repeatability': True,
            'mutations': mutations, 'inherited_baseline': baseline,
            'inherited_fixture_inputs_unchanged': True,
            'original_implementation_counterexamples': 0,
            'test_only_mutant_counterexamples': len(mutations['results']),
            'independent_implementation_coverage': 'NOT_COVERED', 'universal_erc_conformance': False,
            'new_publication': False, 'guarantee': 'LABORATORY_VERIFIED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=h.ROOT / 'build/fuzz-continuation')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify(args.root.resolve())
    if args.out:
        h.write(args.out, result)
    print(json.dumps({k: result[k] for k in ('passed', 'unique_case_ids', 'distinct_inputs', 'distinct_sequences',
                     'semantic_repeatability', 'original_implementation_counterexamples', 'test_only_mutant_counterexamples')}, sort_keys=True))
