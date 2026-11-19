"""Read-only, hash-bound input access; no conformance engine lives here."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'conformance/spec-drift-coverage-v0'
EVIDENCE = ROOT / 'evidence/spec-drift-coverage-v0'
BASE = '6e8fabee9be170245f557a271b6d315176cc4a03'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode(value))


class Reader:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.used = {}
        self.archives = {}
        self.archive_hashes = {}

    def raw(self, ref):
        name = ref['path']
        path = (self.root / name).resolve()
        require(path.is_relative_to(self.root.resolve()), 'input escapes root')
        if 'member' in ref:
            if name not in self.archives:
                self.archive_hashes[name] = sha(path.read_bytes())
                self.archives[name] = zipfile.ZipFile(path)
            require(self.archive_hashes[name] == ref['archive_sha256'], 'archive identity mismatch: ' + name)
            raw = self.archives[name].read(ref['member'])
        else:
            raw = path.read_bytes()
        require(sha(raw) == ref['sha256'], 'input identity mismatch: ' + name)
        self.used[name + ('!' + ref['member'] if 'member' in ref else '')] = ref['sha256']
        return raw

    def json(self, ref):
        return strict(self.raw(ref))
