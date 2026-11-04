"""Actual profile, mutation and preservation checks through unchanged harness/grader."""
import argparse
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import agent_harness as h


def validate(out):
    out.mkdir(parents=True, exist_ok=True)
    commands = []
    def run(name, args, optimized=False):
        argv = [sys.executable, '-B', *(['-O'] if optimized else []), *args]
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=900)
        (out / (name + '.stdout')).write_bytes(proc.stdout)
        (out / (name + '.stderr')).write_bytes(proc.stderr)
        commands.append({'name': name, 'argv': argv, 'exit_code': proc.returncode,
                         'stdout_sha256': h.sha(proc.stdout), 'stderr_sha256': h.sha(proc.stderr)})
        h.write(out / 'commands.json', commands)
        print(name, proc.returncode, flush=True)
        if proc.returncode: raise RuntimeError(name + ' failed; see preserved logs')
    run('preservation-before', ['tools/erc8004_role_policy/integrity.py'])
    for mode, optimized in [('normal', False), ('repeat', False), ('optimized', True)]:
        run(mode, ['tools/agent_harness.py', 'run', '--suite', 'conformance/erc8004-role-policy-v1/suite.json',
                   '--adapter', 'conformance/erc8004-role-policy-v1/adapter.json', '--out', str(out / mode)], optimized)
    for mode, optimized in [('normal', False), ('optimized', True)]:
        run('controls-' + mode, ['-m', 'unittest', 'discover', '-s', 'tests/erc8004_role_policy', '-v'], optimized)
        run('mutations-' + mode, ['tools/erc8004_role_policy/mutations.py', '--out', str(out / ('mutations-' + mode))], optimized)
    run('preservation-after', ['tools/erc8004_role_policy/integrity.py'])
    digests = {mode: h.sha((out / mode / 'projected.json').read_bytes()) for mode in ('normal', 'repeat', 'optimized')}
    mutations = [json.loads((out / ('mutations-' + mode) / 'report.json').read_bytes()) for mode in ('normal', 'optimized')]
    report = json.loads((out / 'normal/report.json').read_bytes())
    control_counts = {mode: int(re.search(r'Ran (\d+) tests', (out / ('controls-' + mode + '.stderr')).read_text()).group(1))
                      for mode in ('normal', 'optimized')}
    requests = 0
    for p in out.rglob('request.json'):
        request = json.loads(p.read_bytes())
        if set(request) != {'schema', 'profile', 'cases'} or any(set(c) != {'id', 'input'} for c in request['cases']):
            raise RuntimeError('unexpected adapter request fields')
        requests += 1
    for mode in ('normal', 'repeat', 'optimized'):
        actual = json.loads((out / mode / 'adapter.stdout').read_bytes())['observations']
        for row in actual.values():
            evidence = row['evidence']['execution']
            for snapshot, receipt in [('request_roles', 'request_receipt'), ('response_roles', 'receipt')]:
                if (evidence[snapshot]['block_number'] != evidence[receipt]['blockNumber']
                        or evidence[snapshot]['block_hash'] != evidence[receipt]['blockHash']):
                    raise RuntimeError('snapshot block label disagrees with actual receipt')
    summary = {'schema': 'erc8004-role-policy.validation.v1', 'passed': len(set(digests.values())) == 1 and mutations[0] == mutations[1],
               'cases': len(report['rows']), 'conformant': sum(r['backend_conformance'] == 'PASS' for r in report['rows']),
               'controls': control_counts, 'behavioral_sha256': digests, 'physical_mutations': mutations[0]['counts'],
               'mutation_modes_equal': mutations[0] == mutations[1], 'expectation_free_requests': requests,
               'snapshot_receipt_bindings': True,
               'python': sys.version, 'platform': platform.platform(),
               'node': subprocess.check_output(['node', '--version'], text=True).strip(),
               'independent_controller': 'NOT_COVERED', 'independent_reviewer_replay': 'NOT_COVERED'}
    h.write(out / 'summary.json', summary)
    if not summary['passed']: raise RuntimeError('determinism failed')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, default=ROOT / 'build/role-policy-v1/validation')
    print(json.dumps(validate(p.parse_args().out.resolve()), sort_keys=True))
