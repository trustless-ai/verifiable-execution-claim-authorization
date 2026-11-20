"""Exact documentation transition; existing executable sources stay frozen."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '4b6d7ef9aabd23932668711ee1d6cf774d9844d7'
BASE_INVENTORY = '9bd35455636bbfd40e06ddf066408d264d092dcb8e1a0d0ad2510ae339385edf'
POLICY = 'research/documentation-refresh-v1/TRANSITION.json'
POLICY_SHA256 = 'd0f11eb1ba94eef05916d3c34f2223a6bc27711adece15266e76072f6e5b1554'
ARCHIVE = 'research/history/README-4b6d7ef9.md'
VIEW = 'build/documentation-replay'
RECEIPT = 'build/documentation-refresh/REPLAY.json'
EXCLUDED = {'.git', 'build', '__pycache__', '.venv'}
UNCHANGED_WORKFLOWS = (
    '.github/workflows/coverage-v4.yml',
    '.github/workflows/erc8404-compatibility.yml',
    '.github/workflows/formal-v1.yml',
    '.github/workflows/real-artifact-v2.yml',
    '.github/workflows/real-chain-v3.yml',
    '.github/workflows/reproduce.yml',
)


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, 'duplicate JSON key')
        out[key] = value
    return out


def strict(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def baseline(root):
    raw = git(root, 'show', BASE + ':artifacts.sha256.json')
    require(sha(raw) == BASE_INVENTORY, 'baseline_manifest_identity')
    return raw, strict(raw)


def inventory(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()
            and p != root/'artifacts.sha256.json'
            and not set(p.relative_to(root).parts) & EXCLUDED and p.suffix != '.pyc'}


def workflow(raw):
    """Mechanical routing only: preserve every old command, tool pin and trigger."""
    text = raw.decode('utf8')
    require('    defaults:' not in text, 'unexpected existing workflow defaults')
    require(VIEW not in text, 'already routed workflow')
    checkout = '      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n'
    require(checkout in text, 'unexpected checkout action')
    text = text.replace(checkout + '      -', checkout + '        with:\n          fetch-depth: 0\n      -')
    require(text.count('          fetch-depth: 0\n') == text.count(checkout), 'full history required')
    text = text.replace('    steps:\n', '    defaults:\n      run:\n        working-directory: ' + VIEW + '\n    steps:\n')
    parts = text.split('    steps:\n')
    prepare = ('      - name: Verify documentation transition and prepare identical executable tree\n'
               '        working-directory: .\n'
               '        run: python -B tools/documentation_refresh/replay.py prepare\n')
    finish = ('      - name: Recheck current documentation transition\n'
              '        if: always()\n'
              '        working-directory: .\n'
              '        run: python -B tools/documentation_refresh/replay.py check\n')
    for i in range(1, len(parts)):
        part = parts[i]
        pos = part.find('      - run:')
        require(pos >= 0, 'workflow has no initial run')
        part = part[:pos] + prepare + part[pos:]
        upload = part.find('      - uses: actions/upload-artifact@')
        require(upload >= 0, 'workflow missing artifact upload')
        part = part[:upload] + finish + part[upload:]
        part = re.sub(r'(?m)^(        working-directory: )(build/(?!documentation-replay(?:/|$))[^\n]+)$', r'\g<1>' + VIEW + r'/\2', part)
        part = re.sub(r'(?m)^(          path: )(build/[^\n]+)$',
                      lambda m: m[1] + '|\n            ' + VIEW + '/' + m[2] + '\n            ' + RECEIPT, part)
        # Multiline upload paths (single-line conversion above is already prefixed).
        part = re.sub(r'(?m)^            (build/(?!documentation-)[^\n]+)$', r'            ' + VIEW + r'/\1', part)
        part = re.sub(r'(?m)^          path: \|\n((?:            [^\n]*\n)+)',
                      lambda m: m[0] if '            ' + RECEIPT + '\n' in m[1]
                      else m[0] + '            ' + RECEIPT + '\n', part)
        parts[i] = part
    return '    steps:\n'.join(parts).encode('utf8')


def check(root=ROOT):
    root = Path(root)
    raw = (root/POLICY).read_bytes()
    require(sha(raw) == POLICY_SHA256, 'transition_manifest_identity')
    policy = strict(raw)
    require(policy['schema'] == 'veca-documentation-refresh-v1' and policy['base'] == BASE,
            'transition_version_or_base')
    require(policy['core_changes_permitted'] is False, 'Core_transition_forbidden')
    _, old = baseline(root)
    expected = dict(old['files'])
    require(policy['before_readme_sha256'] == expected['README.md'], 'original_README_identity')
    require(sha((root/ARCHIVE).read_bytes()) == expected['README.md'], 'README_archive_identity')
    expected['README.md'] = policy['after_readme_sha256']
    workflows = sorted(p for p in old['files'] if p.startswith('.github/workflows/') and p not in UNCHANGED_WORKFLOWS)
    require(policy['workflows'] == workflows and len(workflows) == 11, 'exact_workflow_scope')
    for path in workflows:
        original = git(root, 'show', BASE + ':' + path)
        require(sha(original) == old['files'][path], 'original_workflow_identity')
        expected[path] = sha(workflow(original))
    new_paths = policy['new_files']
    require(len(new_paths) == len(set(new_paths)) and not set(new_paths) & set(expected), 'new_path_scope')
    current = strict((root/'artifacts.sha256.json').read_bytes())
    require({k: v for k, v in current.items() if k != 'files'} ==
            {k: v for k, v in old.items() if k != 'files'}, 'inventory_metadata')
    expected.update({p: current['files'].get(p) for p in new_paths})
    require(all(expected.values()), 'missing_new_inventory_entry')
    require(current['files'] == expected, 'inventory_transition')
    actual = inventory(root)
    require(set(actual) == set(expected), 'file_membership')
    bad = sorted(p for p in expected if actual[p] != expected[p])
    require(not bad, 'unexpected_bytes:' + ','.join(bad[:8]))
    return {'schema': 'veca-documentation-refresh-check-v1', 'passed': True,
            'base': BASE, 'baseline_inventory_sha256': BASE_INVENTORY,
            'transition_sha256': POLICY_SHA256, 'files': len(expected),
            'unchanged_baseline_files': len(old['files']) - 1 - len(workflows),
            'changed_baseline_paths': ['README.md', *workflows, 'artifacts.sha256.json'],
            'new_files': new_paths, 'existing_executable_sources_unchanged': True,
            'core_changes_permitted': False, 'independent_review': 'NOT_ESTABLISHED'}


def check_view(view, root=ROOT):
    view = Path(view)
    raw, old = baseline(root)
    require(view.is_dir() and not view.is_symlink(), 'replay_view_missing')
    require(git(view, 'rev-parse', 'HEAD').decode().strip() == BASE, 'replay_head_identity')
    require((view/'artifacts.sha256.json').read_bytes() == raw, 'replay_manifest_identity')
    require(inventory(view) == old['files'], 'replay_tree_identity')
    return {'passed': True, 'head': BASE, 'files': len(old['files']),
            'exact_pinned_baseline_tree': True}
