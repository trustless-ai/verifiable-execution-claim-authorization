"""Additive registration, preserving historical manifests and every old digest."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ROOT = HERE.parents[2]
PREFIX = 'research/flashprove-8274-claim-boundary-v0/'


def sha(data): return hashlib.sha256(data).hexdigest()


def check(root=ROOT, check_git=True):
    project=root/PREFIX
    pins=json.loads((project/'review_v1/historical-pins.json').read_bytes())
    bad=[]
    for filename,pin in pins.items():
        raw=(project/'review_v1'/filename).read_bytes()
        if sha(raw)!=pin['sha256']: bad.append('snapshot:'+filename)
        if check_git:
            blob=subprocess.check_output(['git','show',pin['commit']+':'+pin['path']],cwd=root)
            if raw!=blob: bad.append('git_snapshot:'+filename)
    previous=json.loads((project/'review_v1/baseline-inventory.json').read_bytes())
    current=json.loads((root/'artifacts.sha256.json').read_bytes())
    if {k:v for k,v in previous.items() if k!='files'}!={k:v for k,v in current.items() if k!='files'}:
        bad.append('inventory_schema_or_exclusions')
    for name,digest in previous['files'].items():
        f=root/name
        if not f.is_file() or sha(f.read_bytes())!=digest:bad.append('historical_bytes:'+name)
        if current['files'].get(name)!=digest:bad.append('historical_entry:'+name)
    additions=set(current['files'])-set(previous['files'])
    if not additions or any(not n.startswith(PREFIX) for n in additions):bad.append('unexpected_addition_scope')
    # Explicitly bounded changes from the original research commit. All evidence,
    # vectors, native source bridge and consumer semantics stay byte-identical.
    old=json.loads((project/'review_v1/original-research-inventory.json').read_bytes())['files']
    transitions=json.loads((project/'review_v1/transitions.json').read_bytes())
    allowed={'prepare.py','preservation.py','README.md','REPORT.md','MUTATION_REPORT.md','INTEGRATION_PLAN.md'}
    if set(transitions)!=allowed:bad.append('transition_scope')
    for name,digest in old.items():
        expected=digest
        if name in transitions:
            t=transitions[name]
            if t['before']!=digest:bad.append('transition_before:'+name)
            expected=t['after']
        f=project/name
        if not f.is_file() or sha(f.read_bytes())!=expected:bad.append('research_bytes:'+name)
    return {'passed':not bad,'historical_entries':len(previous['files']),
            'original_research_files':len(old),'new_registered_entries':len(additions),
            'baseline_inventory_sha256':sha((project/'review_v1/baseline-inventory.json').read_bytes()),
            'transitions':sorted(transitions),'mismatches':sorted(bad)}


def require(root=ROOT):
    result=check(root)
    if not result['passed']:raise ValueError('ADDITIVE_INVENTORY_DRIFT: '+str(result['mismatches']))
    return result


if __name__=='__main__':
    result=check();print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['passed'] else 1)
