"""Execute the current, authenticated 33-file payload in a disposable build copy.

Only an explicit public result allowlist is exported; runtime keys and raw logs
are never uploaded. Historical samples in the checkout are never overwritten.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import transition as t


def download(url, expected):
    with urllib.request.urlopen(url, timeout=120) as response:
        raw = response.read()
    t.require(t.sha(raw) == expected, 'tool_download_digest')
    return raw


def linux_tools(dest, env):
    t.require(sys.platform == 'linux', 'linux_tools_on_other_platform')
    tools = dest/'tools'
    tools.mkdir()
    raw = download('https://github.com/foundry-rs/foundry/releases/download/v1.7.1/foundry_v1.7.1_linux_amd64.tar.gz',
                   'cf7e688ed0c4c48adffca788b496076e31060b67ac5afe1e43dbb5499c20c88b')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        matches = [m for m in archive.getmembers() if m.name in ('forge', './forge') and m.isfile()]
        t.require(len(matches) == 1, 'forge_archive_member')
        (tools/'forge').write_bytes(archive.extractfile(matches[0]).read())
    (tools/'forge').chmod(0o755)
    solc = download('https://binaries.soliditylang.org/linux-amd64/solc-linux-amd64-v0.8.30+commit.73712a01',
                    'f3e987dc6ecebd4bd350c48edcbc320b46cf9e3109bd3fc3d88f1acaf4c428f7')
    (tools/'solc').write_bytes(solc)
    (tools/'solc').chmod(0o755)
    env['V2_FORGE'] = str(tools/'forge')
    env['FOUNDRY_SOLC'] = str(tools/'solc')


def run(args, cwd, env, name, public):
    proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, timeout=900)
    # Raw diagnostics stay in the private build runtime; no command/env export.
    (cwd/(name+'.stdout')).write_bytes(proc.stdout)
    (cwd/(name+'.stderr')).write_bytes(proc.stderr)
    print(json.dumps({'step': name, 'exit': proc.returncode,
                      'stdout_sha256': t.sha(proc.stdout), 'stderr_sha256': t.sha(proc.stderr)}), flush=True)
    t.require(proc.returncode == 0, 'replay_step_failed:' + name)
    return proc.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linux-tools', action='store_true')
    parser.add_argument('--dependency-cache', type=Path)
    args = parser.parse_args()
    binding = t.check()
    build = t.ROOT/'build/erc8378-ci'
    dest = build/'runtime'
    t.require(not (t.ROOT/'build').is_symlink() and not build.is_symlink(), 'unsafe_runtime_path')
    t.require(not dest.exists(), 'runtime_must_be_fresh')
    dest.mkdir(parents=True)
    public = build/'public'
    t.require(not public.exists() and not public.is_symlink(), 'public_output_must_be_fresh')
    public.mkdir()
    _, _, payload, _ = t.contract(str(t.ROOT))
    for name, digest in payload.items():
        raw = (t.ROOT/name).read_bytes()
        t.require(t.sha(raw) == digest, 'current_payload_identity')
        target = dest/Path(name).relative_to(t.PREFIX)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if args.linux_tools:
        linux_tools(build, env)
    prepare = [sys.executable, '-B', 'prepare_dependencies.py']
    if args.dependency_cache:
        prepare += ['--from-cache', str(args.dependency_cache.resolve())]
    run(prepare, dest, env, 'dependencies', public)
    run([sys.executable, '-B', 'gate-v2/offline_checker.py', 'evidence'], dest, env, 'committed-sample', public)
    run([sys.executable, '-B', 'review_replay.py', 'ci-current', '--mutations'], dest, env, 'settlement', public)
    # Separate invocation after the temporary issuer credentials have been removed.
    offline = run([sys.executable, '-B', 'gate-v2/offline_checker.py', 'evidence'], dest, env, 'independent-offline', public)
    (public/'independent-offline.json').write_bytes(offline)
    result = json.loads((dest/'evidence/review-results.json').read_bytes())
    for mode in ['normal', 'repeat', 'optimized']:
        for suite, count in [('foundry', 68), ('offline-checker', 48), ('issuer-controls', 43)]:
            t.require(result['modes'][mode][suite]['checks'] == count and
                      result['modes'][mode][suite]['passed'] == count, 'baseline_count_mismatch')
    t.require(result['mutations'] == {'KILLED':20,'SURVIVED':0,'INVALID':0}, 'mutation_count_mismatch')
    for name in ['review-results.json','ffi-issuance.json','native-payout.json','bridge-refusal.json','mutation-results.json']:
        shutil.copyfile(dest/'evidence'/name, public/name)
    binding['execution'] = {'current_payload': True, 'modes': result['modes'],
                            'mutations': result['mutations'], 'public_chain_deployment': False,
                            'independent_operational_custody': 'NOT_ESTABLISHED'}
    binding['after_execution'] = t.check()
    (public/'CURRENT_EXECUTION.json').write_bytes(t.canonical(binding))
    print(json.dumps({'current_head':binding['current_head'], 'modes':result['modes'],
                      'mutations':result['mutations'], 'production':'HOLD'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
