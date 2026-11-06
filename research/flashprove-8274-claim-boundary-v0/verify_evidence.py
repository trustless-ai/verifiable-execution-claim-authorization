"""Verify only this new research package's inventory and archived raw evidence."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent


def main():
    saved=json.loads((HERE/'SHA256SUMS.json').read_bytes())['files']
    actual={p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json'
            and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    bad=sorted(k for k in set(saved)|set(actual) if saved.get(k)!=actual.get(k))
    archive=HERE/'evidence/raw-evidence.zip'
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('SHA256SUMS.json'))
        names=z.namelist()
        if len(names)!=len(set(names)): raise ValueError('duplicate archive entries')
        archived=sorted(k for k in set(manifest)|set(names)-{'SHA256SUMS.json'}
                        if k not in manifest or k not in names or hashlib.sha256(z.read(k)).hexdigest()!=manifest[k])
    result={'passed':not bad and not archived,'files':len(saved),'mismatches':bad,
            'archive_files':len(manifest),'archive_mismatches':archived,
            'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    print(json.dumps(result,sort_keys=True)); return 0 if result['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
