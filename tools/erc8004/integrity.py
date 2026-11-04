"""Check pinned sources, preserved baseline and the optional captured evidence seal."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/'conformance/erc8004-pilot-v0'
sys.path.insert(0,str(ROOT/'tools'))
from baseline_reconciliation.policy import check as preservation_check


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    lock=json.loads((PROFILE/'source-lock.json').read_bytes())
    bad=[]
    for kind in ['implementation','specification']:
        entry=lock[kind]
        files=entry.get('files',{entry.get('path'):entry.get('sha256')})
        for name,expected in files.items():
            p=ROOT/'build/erc8004'/kind/name
            if not p.is_file() or sha(p)!=expected:bad.append('source:'+kind+'/'+name)
    for name in ['package.json','package-lock.json','hardhat.config.js']:
        if sha(PROFILE/name)!=sha(ROOT/'build/erc8004/runtime'/name):bad.append('runtime:'+name)
    packages=json.loads((PROFILE/'package.json').read_bytes())['dependencies']
    for name,version in packages.items():
        p=ROOT/'build/erc8004/runtime/node_modules'/name/'package.json'
        if not p.is_file() or json.loads(p.read_bytes())['version']!=version:bad.append('dependency:'+name)
    preservation=preservation_check(ROOT,lock['research_base'])
    bad.extend('baseline:'+name for name in preservation['mismatches'])
    seal=ROOT/'evidence/erc8004-pilot-v0/SHA256.json'
    count=0
    if seal.is_file():
        saved=json.loads(seal.read_bytes())
        actual={p.relative_to(seal.parent).as_posix():sha(p) for p in seal.parent.rglob('*') if p.is_file() and p!=seal}
        count=len(saved)
        bad.extend('evidence:'+p for p in set(saved)|set(actual) if saved.get(p)!=actual.get(p))
    return {'passed':not bad,'mismatches':sorted(bad),'unchanged_baseline_files':preservation['unchanged_baseline_files'],
            'preservation':preservation,'evidence_files':count}


if __name__=='__main__':
    result=check();print(json.dumps(result,sort_keys=True));raise SystemExit(not result['passed'])
