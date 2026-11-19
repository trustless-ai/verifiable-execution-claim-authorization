"""Check the published capture and optionally restore ignored evidence, never source."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'evidence/erc8004-property-fuzz-v0'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check(extract=False):
    seals = json.loads((PACKAGE / 'SHA256.json').read_bytes())
    actual = {p.name: sha(p.read_bytes()) for p in PACKAGE.iterdir() if p.is_file() and p.name != 'SHA256.json'}
    if actual != seals['files']:
        raise ValueError('package file inventory mismatch')
    restored = 0
    with zipfile.ZipFile(PACKAGE / 'EVIDENCE.zip') as archive:
        names = archive.namelist()
        members = seals['members']
        if len(names) != len(set(names)) or names != sorted(names) or set(names) != set(members):
            raise ValueError('archive membership/order mismatch')
        for name in names:
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
                raise ValueError('unsafe archive path')
            raw = archive.read(name)
            if sha(raw) != members[name]:
                raise ValueError('archive member digest mismatch: ' + name)
            if archive.getinfo(name).date_time != (2026, 10, 22, 0, 0, 0):
                raise ValueError('noncanonical timestamp')
            # Historical source snapshots are inspectable only. Never overwrite
            # current source/docs, even if they have evolved for publication.
            if extract and name.startswith(('build/fuzz-start/', 'build/fuzz-smoke/', 'build/fuzz-continuation/')):
                target = ROOT.joinpath(*relative.parts)
                if target.is_file() and target.read_bytes() != raw:
                    raise ValueError('refusing to overwrite existing evidence: ' + name)
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                    restored += 1
    return {'passed': True, 'members': len(names), 'restored_files': restored,
            'archive_sha256': seals['files']['EVIDENCE.zip']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract', action='store_true')
    print(json.dumps(check(parser.parse_args().extract), sort_keys=True))
