"""Authenticate current additions before replaying unchanged historical checks.

The historical view proves only the pinned baseline. A separate current-payload
job executes the new gate. Neither view establishes independent verifier custody.
"""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = '29155372c6a16f23d1bc2091f2f3671c51e0da4c'
BASE_MANIFEST = '1ecb8c7042653e4e63f145b81a8e8c331d9675ed02da6df57b3ed990255e5115'
PAYLOAD = 'f3a7ff83f639c92508e15069d7ca522b7abe92b4'
POLICY_SHA256 = '8806e6bebcff1b534763252c1c7d749b7cf24adec1334420c4cc6d8aa4306cec'
PREFIX = 'experiments/erc8378-rvr-veca-v1'
VIEW = 'build/erc8378-baseline'
RECEIPT = 'build/erc8378-ci/CURRENT_BINDING.json'
WORKFLOW = '.github/workflows/erc8378-settlement-v1.yml'
ADDITIONS = tuple(PREFIX + '/' + p for p in (
    'CI_TRANSITION.json', 'CI_REVIEW.md', 'ci/transition.py',
    'ci/test_transition.py', 'ci/replay.py')) + (WORKFLOW,)
EXCLUDED = {'.git', 'build', '__pycache__', '.venv'}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate_JSON_key')
        result[key] = value
    return result


def strict(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def inventory(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if set(rel.parts) & EXCLUDED or path.suffix == '.pyc':
            continue
        require(not path.is_symlink(), 'symlink:' + rel.as_posix())
        if path.is_file() and rel.as_posix() != 'artifacts.sha256.json':
            result[rel.as_posix()] = sha(path.read_bytes())
    return result


def route(raw):
    """Only execution/artifact paths change; every old command and pin remains."""
    text = raw.decode('utf8')
    require(VIEW not in text, 'already_routed')
    checkout = '      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n'
    text = re.sub(re.escape(checkout) + r'(?!        with:\n)',
                  checkout + '        with:\n          fetch-depth: 0\n', text)
    require(text.count(checkout) == text.count('          fetch-depth: 0\n'), 'full_history_required')
    text = re.sub(r'(?m)^(        working-directory: )([^\n]+)$',
                  lambda m: m[1] + VIEW + ('' if m[2] == '.' else '/' + m[2]), text)
    text = re.sub(r'(?m)^(          path: )(build/[^\n]+)$',
                  lambda m: m[1] + '|\n            ' + VIEW + '/' + m[2] + '\n            ' + RECEIPT, text)
    text = re.sub(r'(?m)^            (build/(?!erc8378-)[^\n]+)$',
                  lambda m: '            ' + VIEW + '/' + m[1], text)
    text = re.sub(r'(?m)^          path: \|\n((?:            [^\n]*\n)+)',
                  lambda m: m[0] if '            ' + RECEIPT + '\n' in m[1]
                  else m[0] + '            ' + RECEIPT + '\n', text)
    parts = text.split('    steps:\n')
    require(len(parts) > 1, 'workflow_steps_missing')
    # Every workflow here has one job or one shared matrix job, except the
    # spec-drift monitor, which has a second job with its own defaults.
    for i in range(1, len(parts)):
        prior = parts[i-1].rsplit('\n  ', 1)[-1]
        if '    defaults:\n' not in prior:
            # Detect defaults in this job's header, not in a preceding job.
            header = parts[i-1].split('    runs-on:')[-1]
            if '    defaults:\n' not in header:
                parts[i-1] += '    defaults:\n      run:\n        working-directory: ' + VIEW + '\n'
        blocks = re.split(r'(?m)(?=^      - )', parts[i])
        first = next(n for n, b in enumerate(blocks)
                     if re.search(r'(?m)^      - run:|^        run:', b))
        before = ('      - name: Authenticate current ERC8378 transition and prepare baseline\n'
                  '        working-directory: .\n'
                  '        run: python -B ' + PREFIX + '/ci/transition.py prepare\n')
        blocks.insert(first, before)
        upload = next(n for n, b in enumerate(blocks) if 'uses: actions/upload-artifact@' in b)
        blocks.insert(upload, '      - name: Recheck current ERC8378 transition and baseline bytes\n'
                      '        if: always()\n        working-directory: .\n'
                      '        run: python -B ' + PREFIX + '/ci/transition.py check\n')
        parts[i] = ''.join(blocks)
    return '    steps:\n'.join(parts).encode()


def native_workflow():
    return ("""name: ERC8378 current verifier-gated settlement V1
on: [push, pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  current-settlement-and-transition:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: '3.12'
      - run: python -B tools/verify_artifacts.py
      - run: python -B """ + PREFIX + """/ci/transition.py check
      - run: python -B -m unittest discover -s """ + PREFIX + """/ci -p 'test_*.py' -v
      - run: python -B -O -m unittest discover -s """ + PREFIX + """/ci -p 'test_*.py' -v
      - run: python -B -m pip install -r """ + PREFIX + """/requirements-replay.txt
      - run: python -B """ + PREFIX + """/ci/replay.py --linux-tools
      - name: Recheck current source and frozen Core after replay
        if: always()
        run: |
          python -B """ + PREFIX + """/ci/transition.py prepare
          python -B tools/verify_artifacts.py
          python -B build/erc8378-baseline/tools/erc8404/integrity.py
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        if: always()
        with:
          name: erc8378-current-settlement-v1
          path: build/erc8378-ci/public
""").encode()


@lru_cache(maxsize=8)
def contract(root):
    root = Path(root)
    raw = git(root, 'show', BASE + ':artifacts.sha256.json')
    require(sha(raw) == BASE_MANIFEST, 'baseline_manifest_identity')
    base = strict(raw)
    workflows = sorted(p for p in base['files'] if p.startswith('.github/workflows/'))
    require(len(workflows) == 18, 'baseline_workflow_scope')
    expected = dict(base['files'])
    for path in workflows:
        original = git(root, 'show', BASE + ':' + path)
        require(sha(original) == base['files'][path], 'baseline_workflow_identity')
        expected[path] = sha(route(original))
    published = PREFIX + '/PUBLISHED_FILES.json'
    raw = git(root, 'show', PAYLOAD + ':' + published)
    rows = strict(raw)['files']
    payload = {PREFIX + '/' + r['path']: r['sha256'] for r in rows}
    payload[published] = sha(raw)
    require(len(rows) == 32 and len(payload) == 33 and not set(payload) & set(expected), 'payload_scope')
    expected.update(payload)
    policy = {'schema': 'veca-erc8378-ci-transition-v1', 'base': BASE,
              'baseline_inventory_sha256': BASE_MANIFEST, 'payload_commit': PAYLOAD,
              'payload_files': payload, 'new_ci_files': list(ADDITIONS),
              'workflow_routes': workflows, 'core_changes_permitted': False,
              'historical_evidence_changes_permitted': False,
              'production': 'HOLD', 'independent_operational_custody': 'NOT_ESTABLISHED'}
    return base, expected, payload, policy


def check_view(root):
    root = Path(root)
    view = root/VIEW
    require(not (root/'build').is_symlink() and not view.is_symlink(), 'unsafe_baseline_path')
    require(view.resolve().is_relative_to((root/'build').resolve()), 'baseline_outside_build')
    require(git(view, 'rev-parse', 'HEAD').decode().strip() == BASE, 'baseline_head_identity')
    base, _, _, _ = contract(str(root))
    require(sha((view/'artifacts.sha256.json').read_bytes()) == BASE_MANIFEST, 'baseline_view_manifest_identity')
    require(inventory(view) == base['files'], 'baseline_view_bytes')
    return {'head': BASE, 'files': len(base['files']), 'exact_baseline_tree': True}


def check(root=ROOT):
    root = Path(root)
    base, expected, payload, policy = contract(str(root))
    expected = dict(expected)
    policy_raw = (root/PREFIX/'CI_TRANSITION.json').read_bytes()
    require(sha(policy_raw) == POLICY_SHA256 and policy_raw == canonical(policy), 'transition_policy_identity')
    current = strict((root/'artifacts.sha256.json').read_bytes())
    require({k:v for k,v in current.items() if k != 'files'} ==
            {k:v for k,v in base.items() if k != 'files'}, 'inventory_metadata')
    expected.update({p: current['files'].get(p) for p in ADDITIONS})
    expected[WORKFLOW] = sha(native_workflow())
    require(all(expected.values()) and current['files'] == expected, 'inventory_transition')
    actual = inventory(root)
    require(set(actual) == set(expected), 'file_membership')
    bad = sorted(p for p in expected if actual[p] != expected[p])
    require(not bad, 'unexpected_bytes:' + ','.join(bad[:8]))
    result = {'schema': 'veca-erc8378-current-binding-v1', 'passed': True,
              'base': BASE, 'current_head': git(root, 'rev-parse', 'HEAD').decode().strip(),
              'files': len(expected), 'review_payload_files_unchanged': len(payload),
              'unchanged_baseline_files': len(base['files']) - 18,
              'modified_existing_scope': ['artifacts.sha256.json', *policy['workflow_routes']],
              'core_changes_permitted': False, 'production': 'HOLD',
              'independent_operational_custody': 'NOT_ESTABLISHED'}
    if (root/VIEW).exists():
        result['historical_baseline_view'] = check_view(root)
    return result


def prepare(root=ROOT):
    root = Path(root)
    result = check(root)
    require(not (root/'build').is_symlink(), 'unsafe_build_path')
    view = root/VIEW
    if not view.exists():
        view.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-c', 'core.autocrlf=false', 'worktree', 'add', '--detach', str(view), BASE], cwd=root, check=True)
    result['historical_baseline_view'] = check_view(root)
    result['prepare_executed_historical_tests'] = False
    target = root/RECEIPT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical(result))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['check', 'prepare'])
    args = parser.parse_args()
    try:
        print(json.dumps(prepare() if args.operation == 'prepare' else check(), sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({'passed': False, 'reason': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
