"""Local research dependency binding; does not change frozen ERC profiles."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'research/erc8004-second-backend-v0'
CACHE = ROOT / 'build/erc8004-second-backend-v0'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True) + '\n').encode())
def compiler_python():
    return CACHE / 'venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
def check_sources(source, mutation=None):
    lock = json.loads((RESEARCH/'source-lock.json').read_bytes())
    recipe = None
    if mutation:
        catalog = json.loads((RESEARCH/'mutations.json').read_bytes())
        recipe = next((r for r in catalog if r['id'] == mutation), None)
        if recipe is None: raise ValueError('unknown mutation')
    observed = {}
    for name, digest in lock['files'].items():
        raw = (source/name).read_bytes()
        if recipe and name == recipe['path']:
            before, after = recipe['before'].encode(), recipe['after'].encode()
            if raw.count(after) != 1: raise ValueError('mutation representation mismatch')
            original = raw.replace(after, before, 1)
            if sha(original) != digest: raise ValueError('mutation outside exact baseline')
        elif sha(raw) != digest: raise ValueError('source pin mismatch: '+name)
        observed[name] = sha(raw)
    expected = set(lock['files'])
    actual = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file() and '.git' not in p.relative_to(source).parts}
    if actual != expected: raise ValueError('source inventory mismatch')
    return observed
