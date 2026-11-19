"""Observe executed Core frames without replacing any verifier or its results."""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from pr12_pr13_integration import preservation as p


def run(out):
    p.check()
    core = (h.ROOT/'evidence/erc8404/core/conformance/rvr-v0/adapter.py').resolve()
    pins = json.loads(p.git(p.MAIN, 'fixtures/erc8404/core-lock.json'))
    for name, digest in pins.items():
        p.require(h.sha((h.ROOT/'evidence/erc8404/core'/name).read_bytes()) == digest, 'pinned Core bytes')
    corpus = json.loads((h.DEFAULT.parent/'vectors.json').read_bytes())
    request = h.encode(h.detached_request(corpus))
    args = [str(h.ROOT/'tools/harness_v0/erc8404_adapter.py'), '--implementation-root', str(h.ROOT)]
    native = subprocess.run([sys.executable, '-B', *args], input=request, capture_output=True, timeout=300)
    p.require(native.returncode == 0, 'native backend failed')
    events = Counter()
    module_files = set()
    def observe(frame, event, arg):
        if event == 'call' and frame.f_code.co_filename == str(core):
            events[frame.f_code.co_name] += 1
            module_files.add(str(Path(frame.f_globals['__file__']).resolve()))
    saved = sys.stdin, sys.stdout, sys.argv, sys.getprofile()
    capture = io.BytesIO()
    try:
        sys.stdin = io.TextIOWrapper(io.BytesIO(request), encoding='utf-8')
        sys.stdout = io.TextIOWrapper(capture, encoding='utf-8')
        sys.argv = args
        sys.setprofile(observe)
        runpy.run_path(args[0], run_name='__main__')
        sys.stdout.flush()
        traced = capture.getvalue()
    finally:
        sys.setprofile(saved[3])
        sys.stdin, sys.stdout, sys.argv = saved[:3]
    p.require(traced == native.stdout, 'observation changed native output')
    p.require(events['recompute'] > 0 and module_files == {str(core)}, 'pinned Core not executed')
    out.mkdir(parents=True, exist_ok=False)
    (out/'request.json').write_bytes(request)
    (out/'native.stdout').write_bytes(native.stdout)
    (out/'traced.stdout').write_bytes(traced)
    result = {'schema': 'veca-core-runtime-binding-v1', 'passed': True,
              'core_commit': '9dd36e882dd372f264b77b179130948aa5adcbde',
              'adapter_path': str(core), 'adapter_sha256': h.sha(core.read_bytes()),
              'module_files': sorted(module_files), 'executed_calls': dict(events),
              'native_exit': native.returncode, 'observation_matches_native_bytes': True,
              'native_stdout_sha256': h.sha(native.stdout), 'cases': len(corpus['vectors']),
              'method': 'CPython profile call events through unchanged real adapter; no verifier replacement',
              'independent_implementation': False, 'core_modified': False}
    h.write(out/'RESULTS.json', result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out.resolve())
