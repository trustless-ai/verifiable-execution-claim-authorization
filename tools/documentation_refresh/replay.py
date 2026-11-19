"""Explicit historical-docs replay worktree, after checking the actual current tree."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from documentation_refresh import preservation as p


def prepare(root=p.ROOT):
    root = Path(root).resolve()
    current = p.check(root)
    view = root/p.VIEW
    p.require(not view.is_symlink(), 'replay_path_is_symlink')
    p.require(view.resolve().is_relative_to(root/'build'), 'replay_path_outside_build')
    if not view.exists():
        view.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', '-c', 'core.autocrlf=false', 'worktree', 'add', '--detach', str(view), p.BASE],
                       cwd=root, check=True)
    historical = p.check_view(view, root)
    # Distinguish source identity from a later command's execution/outcome.
    receipt = {'schema': 'veca-documentation-replay-binding-v1',
               'current_head': p.git(root, 'rev-parse', 'HEAD').decode().strip(),
               'current_worktree_status': p.git(root, 'status', '--porcelain').decode().splitlines(),
               'current_transition': current, 'historical_view': historical,
               'execution_performed_by_prepare': False, 'independent_review': 'NOT_ESTABLISHED'}
    target = root/p.RECEIPT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode())
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('check', 'prepare'))
    args = parser.parse_args()
    try:
        result = prepare() if args.operation == 'prepare' else p.check()
        if args.operation == 'check' and (p.ROOT/p.VIEW).exists():
            result['historical_view'] = p.check_view(p.ROOT/p.VIEW)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({'passed': False, 'reason': str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
