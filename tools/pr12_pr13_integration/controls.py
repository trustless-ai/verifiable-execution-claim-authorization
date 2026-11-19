"""Physical preservation attacks on disposable copies; Core is never mutated."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pr12_pr13_integration import preservation as p


def execute(out):
    out = out.resolve()
    p.require(out.is_relative_to(p.ROOT/'build'), 'control output must be in disposable build')
    out.mkdir(parents=True, exist_ok=False)
    expected = p.check()
    files = json.loads((p.ROOT/'artifacts.sha256.json').read_bytes())['files']
    rows = []
    # No hardlinks: writing test bytes cannot change the real candidate.
    temp_parent = Path(tempfile.gettempdir()).resolve()
    # Short system-temp path avoids Windows MAX_PATH without changing host policy.
    with tempfile.TemporaryDirectory(prefix='veca-pc-', dir=temp_parent) as tmp:
        root = Path(tmp).resolve()
        p.require(root.parent == temp_parent and root.name.startswith('veca-pc-'), 'disposable path boundary')
        for name in [*files, 'artifacts.sha256.json', '.git']:
            dest = root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p.ROOT/name, dest)
        p.require(p.check(root)['passed'], 'positive control fails')
        mutations = [
            ('historical_evidence_tamper', 'evidence/erc8004-property-fuzz-v0/SUMMARY.json', b'{"fabricated":true}\n', True),
            ('protected_file_deleted', 'tools/erc8004_fuzz/model.py', None, True),
            ('unauthorized_addition', 'research/pr12-pr13-integration-v1/UNAUTHORIZED.txt', b'unauthorized\n', True),
            ('transition_manifest_tamper', p.POLICY, (root/p.POLICY).read_bytes()+b'\n', True),
            ('source_lock_resealed', 'conformance/erc8004-property-fuzz-v0/source-lock.json', b'{}\n', True),
            ('old_integrity_restored', 'tools/erc8004/integrity.py', p.git(p.BASE, 'tools/erc8004/integrity.py'), True),
        ]
        original_inventory = (root/'artifacts.sha256.json').read_bytes()
        for name, path, altered, reseal in mutations:
            target = root/path
            original = target.read_bytes() if target.is_file() else None
            row = {'id': name, 'path': path, 'positive_control_passed': True,
                   'original_sha256': p.sha(original) if original is not None else None,
                   'mutant_sha256': p.sha(altered) if altered is not None else None,
                   'candidate_modified': False, 'core_modified': False, 'classification': 'NOT_RUN'}
            try:
                if altered is None:
                    target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(altered)
                current = json.loads(original_inventory)
                if altered is None:
                    current['files'].pop(path, None)
                else:
                    current['files'][path] = p.sha(altered)
                (root/'artifacts.sha256.json').write_text(json.dumps(current)+'\n', encoding='utf-8', newline='\n')
                try:
                    p.check(root)
                    row['classification'] = 'SURVIVED'
                except ValueError as exc:
                    row['classification'] = 'REJECTED'
                    row['reason'] = str(exc)
            finally:
                if original is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(original)
                (root/'artifacts.sha256.json').write_bytes(original_inventory)
                row['restoration_passed'] = p.check(root)['passed']
            rows.append(row)
    p.require(p.check()['passed'], 'candidate restoration fails')
    result = {'schema': 'veca-integration-preservation-physical-controls-v1', 'cases': rows,
              'passed': all(r['classification'] == 'REJECTED' and r['restoration_passed'] for r in rows),
              'classification_scope': 'Physical input tamper controls, not verifier-mutant completeness',
              'baseline': expected}
    (out/'RESULTS.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
    p.require(result['passed'], 'preservation attack survived')
    print(json.dumps({'passed': result['passed'], 'rejected': len(rows)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    execute(parser.parse_args().out)
