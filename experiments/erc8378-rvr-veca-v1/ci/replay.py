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
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import transition as t


SOLC_VERSION = '0.8.30+commit.73712a01'
# Official solc-bin list.json at 762a732061b3fdb0cd076f29a9be6d8c3cde293e.
SOLC_SHA256 = {
    'linux': 'f3e987dc6ecebd4bd350c48edcbc320b46cf9e3109bd3fc3d88f1acaf4c428f7',
    'win32': 'ccbd3ed44d5fbd26fe039702d403421f1212d2e8752e3cbe3bfd074986911586',
    'darwin': '738dcdc6afddeb505ee4e4ef24f1c1fdba2b8c924e614cbbf5801a5b062dd683',
}


class ReproductionError(ValueError):
    """Actionable environment/setup refusal, before the settlement campaign."""


def ffi_python(env):
    command = shutil.which('python', path=env.get('PATH', ''))
    hint = ("FFI executes the executable 'python'; python3 alone or a shell alias "
            "is insufficient. Activate a Python 3.12 virtual environment and "
            "install requirements with 'python -m pip'. See CI_REVIEW.md.")
    if command is None:
        raise ReproductionError('FFI_PYTHON_REQUIRED: ' + hint)
    try:
        probe = subprocess.run([command, '-B', '-c',
            'import json,sys;print(json.dumps([sys.executable,sys.prefix]))'],
            env=env, capture_output=True, timeout=10, check=True)
        executable, prefix = json.loads(probe.stdout)
        normalize = lambda p: os.path.normcase(os.path.realpath(p))
        if (normalize(executable), normalize(prefix)) != (normalize(sys.executable), normalize(sys.prefix)):
            raise ValueError('different Python environment')
    except (OSError, ValueError, subprocess.SubprocessError):
        raise ReproductionError('FFI_PYTHON_ENVIRONMENT: ' + hint) from None
    return command


def offline_solc(env, home=None):
    """Select exactly the verified compiler that offline Forge will execute."""
    home = Path.home() if home is None else Path(home)
    configured = env.get('FOUNDRY_SOLC')
    candidates = []
    if configured:
        candidates.append(Path(shutil.which(configured, path=env.get('PATH', '')) or configured))
    else:
        roots = [home/'.svm', home/'.local/share/svm']
        if env.get('SVM_HOME'):
            roots.insert(0, Path(env['SVM_HOME']))
        for variable in ['APPDATA', 'LOCALAPPDATA']:
            if env.get(variable):
                roots.append(Path(env[variable])/'svm')
        for root in roots:
            for name in ['solc-0.8.30', 'solc-0.8.30.exe']:
                candidates.append(root/'0.8.30'/name)
        command = shutil.which('solc', path=env.get('PATH', ''))
        if command:
            candidates.append(Path(command))
    compiler = next((p.resolve() for p in candidates if p.is_file()), None)
    if compiler is None:
        raise ReproductionError('SOLC_REQUIRED: offline Foundry cannot download solc 0.8.30. '
            'Preinstall it in the SVM cache or set FOUNDRY_SOLC to its executable; '
            'Linux x86-64 can use --linux-tools before offline execution. See CI_REVIEW.md.')
    expected = SOLC_SHA256.get(sys.platform)
    if expected is None or t.sha(compiler.read_bytes()) != expected:
        raise ReproductionError('SOLC_SHA256: expected the pinned official solc 0.8.30 binary '
            'for this platform. The compiler was not executed. See CI_REVIEW.md.')
    try:
        version = subprocess.run([str(compiler), '--version'], env=env,
            capture_output=True, timeout=10, check=True)
    except (OSError, subprocess.SubprocessError):
        raise ReproductionError('SOLC_EXECUTABLE: the verified compiler cannot execute on '
            'this host. Check executable permissions and platform compatibility.') from None
    if SOLC_VERSION not in (version.stdout + version.stderr).decode(errors='replace'):
        raise ReproductionError('SOLC_VERSION: expected ' + SOLC_VERSION)
    env['FOUNDRY_SOLC'] = str(compiler)
    return {'version': SOLC_VERSION, 'sha256': expected}


def fresh_run(root, label):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,47}', label):
        raise ReproductionError('RUN_LABEL: use 1-48 ASCII letters, digits or hyphens; start with a letter or digit.')
    build = Path(root)/'build'/('erc8378-ci' if label == 'ci-current' else 'erc8378-ci-' + label)
    if (Path(root)/'build').is_symlink() or build.is_symlink():
        raise ReproductionError('RUN_PATH: build directories must not be symlinks.')
    if build.exists() and not build.is_dir():
        raise ReproductionError('RUN_PATH: build path is not a directory: ' + str(build))
    for name in ['runtime', 'public', 'tools']:
        path = build/name
        if path.exists() or path.is_symlink():
            raise ReproductionError("RUN_LABEL_IN_USE: label '" + label + "' already has " + str(path) +
                '. Existing evidence was preserved. Retry with --label <new-unique-label>; '
                'do not delete old runs. See CI_REVIEW.md.')
    return build


def download(url, expected):
    with urllib.request.urlopen(url, timeout=120) as response:
        raw = response.read()
    t.require(t.sha(raw) == expected, 'tool_download_digest')
    return raw


def linux_tools(dest, env):
    t.require(sys.platform == 'linux', 'linux_tools_on_other_platform')
    tools = dest/'tools'
    tools.mkdir(parents=True)
    raw = download('https://github.com/foundry-rs/foundry/releases/download/v1.7.1/foundry_v1.7.1_linux_amd64.tar.gz',
                   'cf7e688ed0c4c48adffca788b496076e31060b67ac5afe1e43dbb5499c20c88b')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        matches = [m for m in archive.getmembers() if m.name in ('forge', './forge') and m.isfile()]
        t.require(len(matches) == 1, 'forge_archive_member')
        (tools/'forge').write_bytes(archive.extractfile(matches[0]).read())
    (tools/'forge').chmod(0o755)
    solc = download('https://raw.githubusercontent.com/ethereum/solc-bin/762a732061b3fdb0cd076f29a9be6d8c3cde293e/linux-amd64/solc-linux-amd64-v0.8.30+commit.73712a01',
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
    t.require(proc.returncode == 0, 'replay_step_failed:' + name +
              '; private diagnostics: ' + str(cwd/(name+'.stdout')) +
              ' and ' + str(cwd/(name+'.stderr')) + '; existing evidence was preserved')
    return proc.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linux-tools', action='store_true')
    parser.add_argument('--dependency-cache', type=Path)
    parser.add_argument('--label', default='ci-current', help='Unique run label; reuse refuses without deleting evidence')
    args = parser.parse_args()
    binding = t.check()
    build = fresh_run(t.ROOT, args.label)
    dest = build/'runtime'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    ffi_python(env)
    if args.linux_tools:
        linux_tools(build, env)
    toolchain = offline_solc(env)
    print(json.dumps({'preflight': 'PASS', 'ffi_python': 'same interpreter/environment',
                      'solc': toolchain, 'label': args.label}), flush=True)
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
    prepare = [sys.executable, '-B', 'prepare_dependencies.py']
    if args.dependency_cache:
        prepare += ['--from-cache', str(args.dependency_cache.resolve())]
    run(prepare, dest, env, 'dependencies', public)
    run([sys.executable, '-B', 'gate-v2/offline_checker.py', 'evidence'], dest, env, 'committed-sample', public)
    run([sys.executable, '-B', 'review_replay.py', args.label, '--mutations'], dest, env, 'settlement', public)
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
    try:
        main()
    except ReproductionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
