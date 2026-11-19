"""Bounded serial campaign over the unchanged harness and pinned grader."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from erc8004_fuzz import generate

PROFILE = generate.PROFILE_DIR


def run(destination, batch_size=20, fixtures=None):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    fixtures = generate.build() if fixtures is None else fixtures
    h.write(destination / 'fixtures.json', fixtures)
    cases = fixtures['cases']
    if not cases or len({c['id'] for c in cases}) != len(cases) or not 1 <= batch_size <= 25:
        raise ValueError('finite nonempty unique cases and bounded batch size required')
    rows, batches = [], []
    for start in range(0, len(cases), batch_size):
        batch = destination / ('batch-%03d' % (start // batch_size))
        chosen = cases[start:start + batch_size]
        suite = generate.write_suite(chosen, batch)
        report = h.execute(suite, PROFILE / 'adapter.json', batch / 'run')
        rows.extend(report['rows'])
        batches.append({'path': batch.name, 'exit_code': report['exit_code'],
                        'backend_conformance': report['backend_conformance'], 'cases': len(chosen),
                        'request_sha256': report.get('request_sha256'),
                        'observation_sha256': report.get('observation_sha256'), 'error': report.get('error')})
        h.write(destination / 'batches.json', batches)
        print(batch.name, report['backend_conformance'], len(chosen), flush=True)
        if report['exit_code'] == 2:
            break
    expected_ids = {c['id'] for c in cases}
    actual_ids = [r['id'] for r in rows]
    complete = len(actual_ids) == len(expected_ids) and set(actual_ids) == expected_ids
    counts = Counter(r['backend_conformance'] for r in rows)
    auth = Counter(r['evidence_supported_authorization']['status'] for r in rows if r['evidence_supported_authorization'])
    operations = Counter()
    for row in rows:
        if row['observed_behavior']:
            for op, observed in zip(next(c['input']['sequence'] for c in cases if c['id'] == row['id']), row['observed_behavior']['behavior']['steps']):
                operations[op['kind'] + ':' + observed['status']] += 1
    summary = {'schema': 'erc8004.generated-campaign.v0', 'complete': complete,
               'passed': complete and counts['PASS'] == len(cases) and all(b['exit_code'] == 0 for b in batches),
               'seeds': fixtures['seeds'], 'budget_per_seed': fixtures['budget_per_seed'],
               'generated': len(cases), 'executed': len(rows), 'conformance': dict(counts),
               'authorization': dict(auth), 'operation_statuses': dict(operations),
               'operations': sum(operations.values()), 'families': dict(Counter(c['family'] for c in cases)),
               'failures': [r['id'] for r in rows if r['backend_conformance'] != 'PASS'],
               'batch_count': len(batches), 'optimized': bool(sys.flags.optimize),
               'fixture_sha256': h.sha(h.encode(fixtures)),
               'projection_sha256': h.sha(h.encode({r['id']: r['observed_behavior'] for r in rows})),
               'obligation_cases': dict(Counter(k for c in cases for k in generate.obligations_for(c['input']))),
               'universal_conformance': False, 'independent_implementation_coverage': 'NOT_COVERED'}
    h.write(destination / 'summary.json', summary)
    h.write(destination / 'projection.json', {r['id']: r['observed_behavior'] for r in rows})
    print(json.dumps(summary, sort_keys=True), flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--batch-size', type=int, default=20)
    args = parser.parse_args()
    result = run(args.out, args.batch_size)
    raise SystemExit(0 if result['passed'] else 1 if result['complete'] else 2)
