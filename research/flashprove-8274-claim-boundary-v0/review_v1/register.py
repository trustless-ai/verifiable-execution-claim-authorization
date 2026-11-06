"""Explicit maintainer-only additive registration; never rehash historical entries."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from integrity import ROOT, PROJECT, HERE, PREFIX

REASONS={
    'prepare.py':'Distinguish the preserved historical root-manifest identity from its additive current extension.',
    'preservation.py':'Require a green unchanged root checker and a bounded additive registration.',
    'README.md':'Versioned finalization addendum; retain original a730515 narrative.',
    'REPORT.md':'Versioned review and counterexample addendum; retain original report.',
    'MUTATION_REPORT.md':'Document exact normal/repeat/optimized replay contract; retain old evidence.',
    'INTEGRATION_PLAN.md':'Record authorized inventory resolution without changing historical integration work.',
}


def sha(data):return hashlib.sha256(data).hexdigest()
def write(p,value):p.write_bytes((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())


def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true',required=True);p.parse_args()
    for name,pin in json.loads((HERE/'historical-pins.json').read_bytes()).items():
        data=(HERE/name).read_bytes()
        if sha(data)!=pin['sha256'] or data!=subprocess.check_output(['git','show',pin['commit']+':'+pin['path']],cwd=ROOT):
            raise ValueError('HISTORICAL_SNAPSHOT_DRIFT: '+name)
    original=json.loads((HERE/'baseline-inventory.json').read_bytes())
    current_manifest=json.loads((ROOT/'artifacts.sha256.json').read_bytes())
    for name,digest in original['files'].items():
        if current_manifest['files'].get(name)!=digest:
            raise ValueError('EXISTING_HISTORICAL_ENTRY_DRIFT: '+name)
    if any(not n.startswith(PREFIX) for n in set(current_manifest['files'])-set(original['files'])):
        raise ValueError('UNEXPECTED_EXISTING_EXTENSION')
    for name,digest in original['files'].items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError('HISTORICAL_FILE_DRIFT: '+name)
    prior=json.loads((HERE/'original-research-inventory.json').read_bytes())['files']
    for name,digest in prior.items():
        if name not in REASONS and sha((PROJECT/name).read_bytes())!=digest:
            raise ValueError('UNAUTHORIZED_RESEARCH_CHANGE: '+name)
    transitions={n:{'before':prior[n],'after':sha((PROJECT/n).read_bytes()),'reason':r} for n,r in REASONS.items()}
    write(HERE/'transitions.json',transitions)
    files={f.relative_to(PROJECT).as_posix():sha(f.read_bytes()) for f in sorted(PROJECT.rglob('*'))
           if f.is_file() and f!=PROJECT/'SHA256SUMS.json' and '__pycache__' not in f.parts and f.suffix!='.pyc'}
    write(PROJECT/'SHA256SUMS.json',{'schema':'flashprove-research-inventory-v1',
          'previous':'review_v1/original-research-inventory.json','files':files})
    current=dict(original['files'])
    current.update({PREFIX+name:digest for name,digest in files.items()})
    current[PREFIX+'SHA256SUMS.json']=sha((PROJECT/'SHA256SUMS.json').read_bytes())
    for name,digest in original['files'].items():
        if current[name]!=digest:raise ValueError('NONADDITIVE_INVENTORY_CHANGE')
    write(ROOT/'artifacts.sha256.json',{**original,'files':current})
    print(json.dumps({'preserved_entries':len(original['files']),'added_entries':len(current)-len(original['files']),
                      'current_entries':len(current),'historical_hashes_changed':0,'transitions':list(transitions)},sort_keys=True))


if __name__=='__main__':main()
