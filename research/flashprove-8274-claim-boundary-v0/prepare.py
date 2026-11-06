"""Fetch exact public source bytes into ignored build; never patch the reference repo."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / 'build/flashprove-8274/sources'


def verify(source=CACHE):
    pins = json.loads((HERE / 'SOURCE_PINS.json').read_bytes())
    for name, digest in pins['flashprove']['files'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise ValueError('SOURCE_DRIFT: ' + name)
    for name, digest in pins['veca_reuse'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('REUSE_DRIFT: ' + name)
    return len(pins['flashprove']['files']), len(pins['veca_reuse'])


def main():
    p = argparse.ArgumentParser(); p.add_argument('--source', type=Path); p.add_argument('--runtime', action='store_true')
    a = p.parse_args(); pins = json.loads((HERE / 'SOURCE_PINS.json').read_bytes())['flashprove']
    for name, digest in pins['files'].items():
        dest = CACHE / name
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == digest:
            continue
        if a.source:
            data = (a.source / name).read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/{pins['repository']}/{pins['commit']}/{name}"
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('FETCH_DRIFT: ' + name)
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
    if a.runtime:
        for script, args in [('tools/agent_harness.py', ['prepare']), ('tools/erc8004/prepare.py', [])]:
            subprocess.run([sys.executable, '-B', str(ROOT / script), *args], cwd=ROOT, check=True)
    print(json.dumps({'verified': verify()}))


if __name__ == '__main__':
    main()
