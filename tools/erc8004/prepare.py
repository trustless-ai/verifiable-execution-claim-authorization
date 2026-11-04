"""Fetch byte-pinned public sources and prepare a local-only EVM runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'conformance/erc8004-pilot-v0'
CACHE = ROOT / 'build/erc8004'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(local=None):
    lock = json.loads((PROFILE / 'source-lock.json').read_bytes())
    for category, entry in [('implementation', lock['implementation']), ('specification', lock['specification'])]:
        files = entry.get('files', {entry.get('path'): entry.get('sha256')})
        for name, expected in files.items():
            target = CACHE / category / name
            if target.is_file() and digest(target.read_bytes()) == expected:
                continue
            if local and category == 'implementation':
                # Git blobs, not checkout line-ending conversions, are source evidence.
                raw = subprocess.check_output(['git', 'show', entry['commit'] + ':' + name], cwd=local)
            else:
                url = f"https://raw.githubusercontent.com/{entry['repository']}/{entry['commit']}/{name}"
                with urllib.request.urlopen(url, timeout=60) as response:
                    raw = response.read()
            if digest(raw) != expected:
                raise ValueError('Source pin mismatch: ' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    runtime = CACHE / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for name in ['package.json', 'package-lock.json', 'hardhat.config.js']:
        shutil.copyfile(PROFILE / name, runtime / name)
    npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
    subprocess.run([npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], cwd=runtime, check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source')
    prepare(parser.parse_args().source)
