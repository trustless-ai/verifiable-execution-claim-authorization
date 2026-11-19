"""Integration v1 orchestration; unchanged PR12 engine/oracle and explicit preservation."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from erc8004_fuzz.verify_results import verify


def validate(out):
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    def run(name, args, optimized=False):
        argv = [sys.executable, '-B', *(['-O'] if optimized else []), *args]
        started = time.monotonic()
        proc = subprocess.run(argv, cwd=h.ROOT, capture_output=True, timeout=3600)
        (out / (name + '.stdout')).write_bytes(proc.stdout)
        (out / (name + '.stderr')).write_bytes(proc.stderr)
        commands.append({'name': name, 'argv': argv, 'exit_code': proc.returncode,
                         'seconds': time.monotonic() - started,
                         'stdout_sha256': h.sha(proc.stdout), 'stderr_sha256': h.sha(proc.stderr)})
        h.write(out / 'commands.json', commands)
        print(name, proc.returncode, flush=True)
        if proc.returncode:
            h.write(out / 'failure.json', {'passed': False, 'failed_stage': name, 'exit_code': proc.returncode})
            raise RuntimeError(name + ' failed; execution is not successful')
    run('package', ['tools/erc8004_fuzz/package.py', '--extract'])
    run('repository-inventory', ['tools/verify_artifacts.py'])
    run('frozen-integrity', ['tools/pr12_pr13_integration/preservation.py', '--fuzz'])
    run('pinned-sources-and-dependencies', ['tools/erc8004/integrity.py'])
    run('core-history', ['tools/erc8404/integrity.py'])
    run('core-conformance', ['evidence/erc8404/core/conformance/rvr-v0/adapter.py', '--check'])
    run('fixtures', ['tools/erc8004_fuzz/generate.py', '--check'])
    for mode in ('normal', 'optimized'):
        run('tests-' + mode, ['tools/erc8004_fuzz/tests.py', '-v'], mode == 'optimized')
    run('historical-report-consistency', ['tools/erc8004_fuzz/verify_results.py'])
    for mode in ('normal', 'repeat', 'optimized'):
        run('campaign-' + mode, ['tools/erc8004_fuzz/campaign.py', '--out', str(out / ('campaign-' + mode))], mode == 'optimized')
    run('six-physical-mutations', ['tools/erc8004_fuzz/mutations.py', '--out', str(out / 'mutations')])
    run('six-physical-mutations-optimized', ['tools/erc8004_fuzz/mutations.py', '--out', str(out / 'mutations-optimized')], True)
    # Execute the original pilot and all 17 physical controls afresh, separately
    # from the preserved historical evidence. This also exercises ERC-8404.
    run('legacy-pilot-and-17-mutations', ['tools/erc8004/validate.py', '--out', str(out / 'legacy')])
    run('final-integrity', ['tools/pr12_pr13_integration/preservation.py', '--fuzz'])
    run('final-inventory', ['tools/verify_artifacts.py'])
    result = verify(out)
    historical = json.loads((h.ROOT / 'build/fuzz-continuation/campaign-normal/summary.json').read_bytes())
    if result['campaigns']['normal']['projection_sha256'] != historical['projection_sha256']:
        raise ValueError('fresh-checkout projection differs from the captured campaign')
    result.update(phase='fresh-checkout-replay',
                  head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=h.ROOT).decode().strip(),
                  tree=subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=h.ROOT).decode().strip(),
                  platform=platform.platform(), node=subprocess.check_output(['node', '--version']).decode().strip(),
                  commands=commands, fresh_legacy=json.loads((out / 'legacy/summary.json').read_bytes()),
                  matches_historical_projection=True)
    extra = json.loads((out / 'mutations-optimized/report.json').read_bytes())
    if extra['counts'] != {'KILLED': 6} or not extra['original_source_unchanged']:
        raise ValueError('optimized physical mutation failure')
    for population in (result['mutations'], extra):
        for row in population['results']:
            old = row['original_matrix']
            if (old != {'exit_code': 0, 'conformance': 'PASS', 'rows': 29, 'failed': []}
                    or not row['positive_controls'] or row['positive_count'] != 3
                    or not row['restored_pass'] or not row['restored_source_bytes']
                    or not row['shrink']['deletion_1_minimal'] or row['shrink']['global_minimum_claimed']):
                raise ValueError('original matrix / witness / positive / restoration comparison failed')
    result.update(integration_profile='veca-pr12-pr13-integration-v1', optimized_mutations=extra['counts'], independent_review='NOT_ESTABLISHED')
    h.write(out / 'summary.json', result)
    print(json.dumps({'passed': result['passed'], 'cases': result['unique_case_ids'],
                      'mutants': result['mutations']['counts'], 'head': result['head']}, sort_keys=True))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=h.ROOT / 'build/property-replay')
    validate(parser.parse_args().out.resolve())
