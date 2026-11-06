"""Expectation-free adapter to the existing VECA transport/grader."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from policy import consume
from prepare import ROOT, CACHE, verify


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mutation-source', type=Path, help='trusted local mutation harness only')
    a = p.parse_args()
    request = json.load(sys.stdin)
    if request.get('schema') != 'agent-harness.request.v0' or not request.get('cases'):
        raise ValueError('NONEMPTY_REQUEST_REQUIRED')
    ids = [row['id'] for row in request['cases']]
    if len(ids) != len(set(ids)):
        raise ValueError('DUPLICATE_CASE')
    verify()
    source = a.mutation_source or CACHE
    proc = subprocess.run(['node', str(Path(__file__).with_name('evm.mjs')), str(ROOT), str(source)],
                          input=json.dumps(request).encode(), capture_output=True, timeout=150)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr)
        return 2
    if not proc.stdout.strip():
        raise ValueError('MISSING_OUTPUT')
    native = json.loads(proc.stdout)
    if set(native) != set(ids):
        raise ValueError('INCOMPLETE_NATIVE_RESULTS')
    observations = {row['id']: consume(row['input'], native[row['id']]) for row in request['cases']}
    print(json.dumps({'schema': 'agent-harness.observation.v0', 'observations': observations}, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
