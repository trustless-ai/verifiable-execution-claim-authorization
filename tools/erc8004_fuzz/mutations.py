"""Additional physical Solidity controls, original matrix contrast and shrinking."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from erc8004_fuzz import generate, model
from erc8004_fuzz.shrink import divergence, minimize

SOURCE = h.ROOT / 'build/erc8004/implementation'
PILOT = h.ROOT / 'conformance/erc8004-pilot-v0'
IDENTITY = 'contracts/IdentityRegistryUpgradeable.sol'
VALIDATION = 'contracts/ValidationRegistryUpgradeable.sol'


def definitions():
    authority = '''require(
            msg.sender == owner ||
            isApprovedForAll(owner, msg.sender) ||
            msg.sender == getApproved(agentId),
            "Not authorized"
        );'''
    return [
        ('registration_reserved', IDENTITY, 'function register(string memory agentURI, MetadataEntry[]', 'function getMetadata',
         'require(keccak256(bytes(metadata[i].metadataKey)) != RESERVED_AGENT_WALLET_KEY_HASH, "reserved key");', ''),
        ('metadata_authority', IDENTITY, 'function setMetadata', 'function setAgentURI',
         authority.replace('owner', 'agentOwner'), ''),
        ('unset_authority', IDENTITY, 'function unsetAgentWallet', 'function _authorizeUpgrade', authority, ''),
        ('wallet_future', IDENTITY, 'function setAgentWallet', 'function unsetAgentWallet',
         'require(deadline <= block.timestamp + MAX_DEADLINE_DELAY, "deadline too far");', ''),
        ('response_range', VALIDATION, 'function validationResponse', 'function getValidationStatus',
         'require(response <= 100, "resp>100");', ''),
        ('summary_unanswered', VALIDATION, 'function getSummary', 'function getAgentValidations',
         'matchValidator && matchTag && s.hasResponse', 'matchValidator && matchTag'),
    ]


def witness(name, cases):
    for case in cases:
        seq = case['input']['sequence']
        expected = model.expected(case['input'])['behavior']['steps']
        for op, step in zip(seq, expected):
            if ((name == 'registration_reserved' and op['kind'] == 'register' and step['status'] == 'REJECTED')
                or (name == 'metadata_authority' and op['kind'] == 'metadata' and op['key'] != 'agentWallet' and step['status'] == 'REJECTED')
                or (name == 'unset_authority' and op['kind'] == 'unset' and step['status'] == 'REJECTED')
                or (name == 'wallet_future' and op['kind'] == 'wallet' and op['deadline_offset'] > 300)
                or (name == 'response_range' and op['kind'] == 'respond' and op['response'] > 100)
                or (name == 'summary_unanswered' and op['kind'] == 'request' and step['status'] == 'ACCEPTED')):
                return copy.deepcopy(case)
    raise ValueError('no generated witness for ' + name)


def controls():
    sequences = [
        [generate.register(overload=0)],
        [generate.register(), generate.op('uri', uri='ipfs://control')],
        [generate.register(), generate.op('approve', operator=1), generate.op('transfer', 1, **{'from': 0, 'to': 2})],
    ]
    cases = []
    for i, seq in enumerate(sequences):
        op = seq[-1]
        cases.append({'id': 'control-%d' % i, 'input': {'sequence': seq, 'supply_receipt': True,
            'claim': {'type': 'LAB_REGISTRY_TRANSITION', 'policy': model.POLICY, 'agent_id': op['agent_id'],
                      'operation': op['kind'], 'chain_id': 31337, 'registry_role': model.role(op)}}})
    return cases


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    pristine = {p.relative_to(SOURCE).as_posix(): p.read_bytes() for p in (SOURCE / 'contracts').glob('*.sol')}
    fixtures = generate.build()['cases']
    reports = []
    for name, relative, begin, end, before, after in definitions():
        folder = out / name
        folder.mkdir()
        original = witness(name, fixtures)
        positive = controls()
        suite = generate.write_suite([original, *positive], folder / 'generated')
        record = {'id': name, 'classification': 'NOT_APPLIED', 'witness_id': original['id'],
                  'source': relative, 'before': before, 'after': after}
        target = folder / 'implementation'
        for path, raw in pristine.items():
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        config = {'argv': ['{python}', '-B', '{repo}/tools/erc8004_fuzz/adapter.py', '--implementation-root', str(target)]}
        h.write(folder / 'adapter.json', config)
        try:
            baseline = h.execute(suite, folder / 'adapter.json', folder / 'baseline')
            if baseline['backend_conformance'] != 'PASS':
                record['classification'] = 'UNVERIFIABLE'
                raise ValueError('generated baseline failure')
            raw = pristine[relative].decode()
            left, right = raw.index(begin), raw.index(end, raw.index(begin))
            section = raw[left:right]
            if section.count(before) != 1:
                raise ValueError('physical mutation site not unique')
            changed = (raw[:left] + section.replace(before, after, 1) + raw[right:]).encode()
            (target / relative).write_bytes(changed)
            (folder / 'mutated-source.sol').write_bytes(changed)
            record.update(original_sha256=h.sha(pristine[relative]), mutant_sha256=h.sha(changed))
            # Run the SAME original 29-case matrix against this real source variant.
            old_config = {'argv': ['{python}', '-B', '{repo}/tools/erc8004/adapter.py', '--implementation-root', str(target)]}
            h.write(folder / 'old-adapter.json', old_config)
            old = h.execute(PILOT / 'suite.json', folder / 'old-adapter.json', folder / 'original-matrix')
            record['original_matrix'] = {'exit_code': old['exit_code'],
                'conformance': old['backend_conformance'], 'rows': len(old['rows']),
                'failed': [r['id'] for r in old['rows'] if r['backend_conformance'] != 'PASS']}
            mutated = h.execute(suite, folder / 'adapter.json', folder / 'mutated')
            if mutated['exit_code'] == 2 or old['exit_code'] == 2:
                record['classification'] = 'CRASHED'
                raise ValueError('incomplete EVM execution, not a kill')
            by_id = {r['id']: r for r in mutated['rows']}
            category = divergence(by_id[original['id']], original['input'])
            controls_ok = all(by_id[c['id']]['backend_conformance'] == 'PASS' for c in positive)
            record.update(divergence=category, positive_controls=controls_ok, positive_count=len(positive))
            if category and controls_ok:
                reduced = minimize(original['input'], category, folder / 'adapter.json', folder / 'shrink')
                record['shrink'] = {k: reduced[k] for k in ('original_calls', 'minimized_calls', 'deletion_1_minimal', 'global_minimum_claimed')}
                record['classification'] = 'KILLED'
            else:
                record['classification'] = 'SURVIVED'
        except Exception as exc:
            record['error'] = type(exc).__name__ + ': ' + str(exc)
            if record['classification'] == 'KILLED':
                record['classification'] = 'UNVERIFIABLE'
        finally:
            # Restore the very same physical source copy, then execute again.
            for path, data in pristine.items():
                (target / path).write_bytes(data)
            record['restored_source_bytes'] = all((target / p).read_bytes() == raw for p, raw in pristine.items())
            restored = h.execute(suite, folder / 'adapter.json', folder / 'restored')
            record['restored_pass'] = restored['backend_conformance'] == 'PASS'
            if not record['restored_pass'] or not record['restored_source_bytes']:
                record['classification'] = 'UNVERIFIABLE'
        reports.append(record)
        result = {'schema': 'erc8004.generated-mutations.v0', 'results': reports,
                  'counts': dict(Counter(r['classification'] for r in reports)),
                  'original_source_unchanged': all((SOURCE / p).read_bytes() == raw for p, raw in pristine.items())}
        h.write(out / 'report.json', result)
        print(name, record['classification'], record.get('original_matrix'), record.get('shrink'), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    result = run(parser.parse_args().out.resolve())
    raise SystemExit(0 if len(result['results']) == 6 and result['counts'] == {'KILLED': 6}
                     and result['original_source_unchanged'] else 1)
