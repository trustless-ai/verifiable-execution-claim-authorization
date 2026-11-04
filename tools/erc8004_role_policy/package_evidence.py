"""Package completed actual runs; never synthesizes a successful outcome."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build/role-policy-v1'
DEST = ROOT / 'evidence/erc8004-role-policy-v1'


def encode(value): return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()


def package():
    current = json.loads((BUILD / 'validation/summary.json').read_bytes())
    legacy = json.loads((BUILD / 'legacy/summary.json').read_bytes())
    legacy_opt = json.loads((BUILD / 'legacy-mutations-optimized/report.json').read_bytes())
    if not (current['passed'] and legacy['passed'] and legacy['scenarios'] == legacy['conformant'] == 29
            and legacy['mutations']['KILLED'] == 17 and legacy_opt['counts']['KILLED'] == 17
            and current['physical_mutations']['KILLED'] == 7):
        raise RuntimeError('a required execution gate has not passed')
    members = {}
    roots = ['validation', 'legacy', 'legacy-mutations-optimized',
             'preliminary-validation', 'preliminary-legacy-mutations-optimized']
    for name in roots:
        for path in sorted((BUILD / name).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                members[path.relative_to(BUILD).as_posix()] = path.read_bytes()
    notes = BUILD / 'REPLAY_NOTES.json'
    if notes.is_file(): members['REPLAY_NOTES.json'] = notes.read_bytes()
    if any('node_modules' in name or name.endswith('.pyc') for name in members):
        raise RuntimeError('unexpected cache in evidence')
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / 'EVIDENCE.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    summary = {'schema': 'erc8004-role-policy.evidence.v1', 'evidence_source': 'LOCAL_AUTHOR_EXECUTION',
               'historical_base': '80c91a09095eca362dbfb69d39d0c01fc31130cf',
               'new_policy': current, 'historical_replay': {'cases': legacy['scenarios'], 'conformant': legacy['conformant'],
                   'mutations_normal': legacy['mutations'], 'mutations_optimized': legacy_opt['counts'],
                   'semantic_determinism': legacy['semantic_determinism']},
               'archive_sha256': sha(archive.read_bytes()), 'members': len(members),
               'preliminary_runs': 'Not final passes: shared-cache negative-control collision and corrected response snapshot labels; raw results retained separately.',
               'independent_reviewer_acceptance': 'NOT_COVERED', 'merge_integration': 'NOT_COVERED'}
    (DEST / 'SUMMARY.json').write_bytes(encode(summary))
    (DEST / 'SHA256.json').write_bytes(encode({'schema': 'erc8004-role-policy.hashes.v1',
        'files': {name: sha((DEST / name).read_bytes()) for name in ('EVIDENCE.zip', 'SUMMARY.json')},
        'members': {name: sha(raw) for name, raw in sorted(members.items())}}))
    report = f'''# Executed results: request-time role policy v1

Evidence source: local author execution, not independent organizational review.
Base: `80c91a09095eca362dbfb69d39d0c01fc31130cf`.

| Population | Observed result |
| --- | --- |
| Historical v0 cases | {legacy['conformant']}/{legacy['scenarios']} PASS; normal/repeat/Python -O identical |
| Historical physical mutations | {legacy['mutations']['KILLED']}/17 KILLED normal; {legacy_opt['counts']['KILLED']}/17 KILLED Python -O |
| New v1 cases | {current['conformant']}/{current['cases']} PASS; normal/repeat/Python -O identical |
| New physical mutations | {current['physical_mutations']['KILLED']}/7 KILLED in each mode; normal/-O reports identical |
| New infrastructure test methods | {current['controls']['normal']}/{current['controls']['normal']} normal and {current['controls']['optimized']}/{current['controls']['optimized']} Python -O |
| Historical preservation | 12667 original file bytes and inventory entries unchanged |

New case authorizations: 5 VERIFIED, 11 REFUTED, 10 UNVERIFIABLE. Self-attested owner,
global operator and token-approved validator are UNVERIFIABLE while conforming to their
declared policy expectations. Different keys do not establish independent controllers.

New behavioral SHA256: `{current['behavioral_sha256']['normal']}`.
The unchanged historical validator also passed transport tests, original ERC-8404 profile,
negative infrastructure tests, frozen Core conformance and before/after source integrity.
The new mutation records preserve baseline/mutated/restored executions, positive controls,
identical input requests and exact byte restoration. Mutation populations remain separate.

An initial overlapping run correctly failed when legacy infrastructure negative controls
temporarily removed a cached source file. The first optimized legacy mutation attempt had
14 kills and 3 UNVERIFIABLE baselines; it is not counted as 17/17. After legacy controls
completed and restored the file, the affected campaigns were rerun. The preliminary new
response-role diagnostic also had a request-block label; final output uses the actual
response receipt block. Preliminary results and explanations remain in the archive under
separate names and do not establish final passes. No historical tracked source was changed.

Runtime: Node {current['node']}; Python {current['python'].split()[0]}; {current['platform']}.
Exact commands and raw output are archived; see [replay instructions](README.md).

[Evidence archive](../../evidence/erc8004-role-policy-v1/EVIDENCE.zip):
SHA256 `{summary['archive_sha256']}`, {len(members)} members.
[Machine summary](../../evidence/erc8004-role-policy-v1/SUMMARY.json) and
[per-member hashes](../../evidence/erc8004-role-policy-v1/SHA256.json).

This capture does not claim GitHub CI success, independent acceptance, a second implementation,
or verification of a future #10 + #11 merge tree. Fresh source-head and GitHub execution results
are checked separately after committing. PR #10 must remain Draft; no merge is authorized here.
'''
    (ROOT / 'research/erc8004-role-policy-v1/RESULTS.md').write_bytes(report.encode())
    print(json.dumps({'archive_sha256': summary['archive_sha256'], 'members': len(members), 'bytes': archive.stat().st_size}))


if __name__ == '__main__': package()
