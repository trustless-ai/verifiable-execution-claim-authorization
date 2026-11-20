"""Prepare exact public dependencies in build/, never upstream branches."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
from common import CACHE, RESEARCH, ROOT, check_sources, compiler_python, sha

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    lock=json.loads((RESEARCH/'source-lock.json').read_bytes())
    for name, digest in lock['files'].items():
        dest=CACHE/'source'/name
        if dest.is_file() and sha(dest.read_bytes())==digest: continue
        if args.source: raw=subprocess.check_output(['git','show',lock['commit']+':'+name],cwd=args.source)
        else:
            with urllib.request.urlopen(f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{name}",timeout=60) as r: raw=r.read()
        if sha(raw)!=digest: raise ValueError('source pin mismatch: '+name)
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    check_sources(CACHE/'source')
    if not compiler_python().exists(): subprocess.run([sys.executable,'-m','venv',str(CACHE/'venv')],check=True)
    subprocess.run([str(compiler_python()),'-m','pip','install','--disable-pip-version-check','--require-hashes','--only-binary=:all:','-r',str(RESEARCH/'requirements.txt')],check=True)
    print('Pinned Vyper source and compiler ready; host ERC8004/runtime and harness must be prepared separately')
if __name__=='__main__': main()
