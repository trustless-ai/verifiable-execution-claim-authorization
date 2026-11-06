"""Deterministic post-commit evidence pack. Never edits source or existing archives."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PROJECT=HERE.parent


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--replay',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    replay=a.replay.resolve();dest=a.out.resolve()
    if dest.exists() or replay==dest or replay in dest.parents:raise ValueError('new archive must be outside replay directory')
    result=json.loads((replay/'results.json').read_bytes())
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if result['head']!=head or not result['passed']:raise ValueError('no successful exact-head replay')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):raise ValueError('dirty source')
    files={}
    for f in sorted(replay.rglob('*')):
        if f.is_file():files['replay/'+f.relative_to(replay).as_posix()]=f.read_bytes()
    for f in sorted(PROJECT.rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc':
            files['research/'+f.relative_to(PROJECT).as_posix()]=f.read_bytes()
    files['candidate/artifacts.sha256.json']=(ROOT/'artifacts.sha256.json').read_bytes()
    files['candidate/diff.patch']=subprocess.check_output(['git','diff','--binary','a730515a0d7cfc04f52d137d44f3e92f99f972ee',head],cwd=ROOT)
    note={'head':head,'base':'999e7047df15585f8ce0629081a1369a4942353f',
          'original_research':'a730515a0d7cfc04f52d137d44f3e92f99f972ee',
          'reference':'ea1b613625513a658942af4bc79867d1c77412cd',
          'scope':'Finite MockSP1-backed research; no real ZK soundness or production exploit claim.',
          'independent_acceptance':'NOT_ESTABLISHED','result':result}
    files['REVIEW_RESULTS.json']=(json.dumps(note,indent=2,sort_keys=True)+'\n').encode()
    manifest={name:sha(data) for name,data in sorted(files.items())}
    files['SHA256SUMS.json']=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,data)
    with zipfile.ZipFile(dest) as z:
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('duplicate ZIP entry')
        if any(sha(z.read(name))!=digest for name,digest in manifest.items()):raise ValueError('archive digest mismatch')
    print(json.dumps({'head':head,'archive':str(dest),'sha256':sha(dest.read_bytes()),'verified_payloads':len(manifest),'files':len(files)},sort_keys=True))


if __name__=='__main__':main()
