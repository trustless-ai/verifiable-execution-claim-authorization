"""Additive research audit. Never updates or overrides an inherited guard.

All baseline tracked blobs remain exact, including its complete inventory.
New files have a separate sealed inventory. This is not a CI migration contract.
"""
import json
from pathlib import Path
import subprocess
from common import ROOT, RESEARCH, sha
BASE='4b6d7ef9aabd23932668711ee1d6cf774d9844d7'
SEAL=RESEARCH/'ADDITIONS.sha256.json'
def audit():
    raw=subprocess.check_output(['git','ls-tree','-r','-z',BASE],cwd=ROOT)
    baseline={}
    for line in raw.split(b'\0'):
        if not line: continue
        header,name=line.split(b'\t',1);mode,kind,oid=header.split();baseline[name.decode()]=oid.decode()
    changed=[]
    import hashlib
    for name,oid in baseline.items():
        path=ROOT/name
        if not path.is_file(): changed.append(name);continue
        data=path.read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=oid: changed.append(name)
    additions=json.loads(SEAL.read_bytes())['files']
    actual_files={p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file() and not ({'.git','build','__pycache__','.venv'} & set(p.relative_to(ROOT).parts)) and p.suffix!='.pyc'}
    extra=set(actual_files)-set(baseline)-{SEAL.relative_to(ROOT).as_posix()}
    bad_additions=sorted(k for k in set(additions)|extra if k not in actual_files or additions.get(k)!=sha(actual_files[k].read_bytes()))
    result={'base':BASE,'baseline_files':len(baseline),'baseline_changed':changed,'new_files':len(additions),'new_mismatches':bad_additions,'passed':not changed and not bad_additions,'inherited_inventory':'UNCHANGED; DOES NOT INCLUDE NEW RESEARCH FILES','ci_migration':'NOT_IMPLEMENTED'}
    return result
if __name__=='__main__':
    result=audit();print(json.dumps(result,sort_keys=True,indent=2));raise SystemExit(0 if result['passed'] else 1)
