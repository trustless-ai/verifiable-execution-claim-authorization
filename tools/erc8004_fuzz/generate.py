"""Schema-aware fixed-budget generator; observations cannot influence fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h
from erc8004_fuzz.model import expected, POLICY, PROFILE, role

VERSION = 'erc8004-structured-sequences/0.1.0'
SEEDS = [8004, 8299, 8274]
ROOT = h.ROOT
PROFILE_DIR = ROOT / 'conformance/erc8004-property-fuzz-v0'
FAMILIES = ['registration', 'metadata_authority', 'operator_revocation', 'token_transfer',
            'wallet_deadline', 'wallet_domain', 'wallet_subject', 'unset_authority',
            'reserved_registration', 'request_authority', 'response_range', 'response_updates',
            'post_transfer', 'two_agents', 'policy_promotion', 'random_walk']


def op(kind, actor=0, agent_id=0, **kw):
    return dict(kind=kind, actor=actor, agent_id=agent_id, **kw)


def register(actor=0, agent_id=0, overload=1, uri='ipfs://lab', metadata=None):
    return op('register', actor, agent_id, overload=overload, uri=uri, metadata=metadata or [])


def wallet(actor=0, owner=0, **kw):
    args = dict(wallet=2, signature_actor=2, signature_chain=31337, signature_registry='identity',
                signed_agent=0, signed_owner=owner, deadline_offset=120)
    args.update(kw)
    return op('wallet', actor, **args)


def case(seed, index):
    rng = random.Random((seed << 32) + index)
    family = FAMILIES[index % len(FAMILIES)]
    value = '0x' + rng.randbytes(rng.choice([0, 1, 31, 32, 33, 64])).hex()
    key = rng.choice(['', 'role', 'agentwallet', 'capability', 'x' * 33])
    uri = rng.choice(['', 'ipfs://lab', 'data:application/json;base64,e30='])
    seq = [register(uri=uri)]
    if family == 'registration':
        seq = [register(rng.randrange(4), overload=rng.randrange(3), uri=uri),
               register(rng.randrange(4), 1, 2, uri, [{'key': key, 'value': value}])]
    elif family == 'metadata_authority':
        seq += [op('metadata', 0, key=key, value='0x01'), op('metadata', rng.choice([0, 1, 3]), key=key, value=value)]
    elif family == 'operator_revocation':
        seq += [op('operator', operator=1, enabled=True), op('metadata', 1, key=key, value=value),
                op('operator', operator=1, enabled=False), op('metadata', 1, key=key, value='0xff')]
    elif family == 'token_transfer':
        seq += [op('approve', operator=1), op('transfer', 1, **{'from': 0, 'to': 2}),
                op('uri', 1, uri=uri), op('uri', 2, uri='ipfs://new-owner')]
    elif family == 'wallet_deadline':
        seq += [wallet(deadline_offset=rng.choice([-1, 0, 1, 299, 300, 301, 600]))]
    elif family == 'wallet_domain':
        seq += [wallet(signature_chain=rng.choice([31337, 1]), signature_registry=rng.choice(['identity', 'validation']),
                       signature_actor=rng.choice([2, 3]))]
    elif family == 'wallet_subject':
        seq += [op('transfer', **{'from': 0, 'to': 1}), wallet(actor=1, owner=rng.choice([0, 1]), signed_agent=rng.choice([0, 1]))]
    elif family == 'unset_authority':
        seq += [wallet(), op('unset', rng.choice([0, 1, 3]))]
    elif family == 'reserved_registration':
        seq += [register(1, 1, 2, uri, [{'key': 'agentWallet', 'value': '0x' + '11' * 20}]), register(2, 1, uri=uri)]
    elif family == 'request_authority':
        seq += [op('operator', operator=1, enabled=True), op('request', 1, validator=2, label='a'),
                op('operator', operator=1, enabled=False), op('request', 1, validator=2, label='b'),
                op('request', validator=rng.choice([None, 2]), label='a')]
    elif family == 'response_range':
        seq += [op('request', validator=2, label='a'),
                op('respond', 2, label='a', response=rng.choice([0, 1, 99, 100, 101, 255]), response_hash='0x'+'12'*32, tag='final')]
    elif family == 'response_updates':
        seq += [op('request', validator=2, label='a')]
        for response in rng.sample([0, 1, 50, 99, 100], 3):
            seq += [op('respond', 2, label='a', response=response, response_hash='0x'+'34'*32, tag=str(response))]
        seq += [op('respond', 3, label='a', response=100, response_hash='0x'+'56'*32, tag='unrelated')]
    elif family == 'post_transfer':
        seq += [op('request', validator=2, label='a'), op('transfer', **{'from': 0, 'to': 1}),
                op('request', validator=2, label='b'), op('request', 1, validator=2, label='c'),
                op('respond', 2, label='a', response=100, response_hash='0x'+'78'*32, tag='after-transfer')]
    elif family == 'two_agents':
        seq += [register(1, 1), op('metadata', 0, 1, key=key, value=value),
                op('uri', 1, 1, uri=uri), op('request', 1, 1, validator=3, label='other'),
                op('respond', 2, 1, label='other', response=100, response_hash='0x'+'90'*32, tag='other')]
    elif family == 'policy_promotion':
        seq += [op('request', validator=2, label='a'), op('respond', 2, label='a', response=100, response_hash='0x'+'ab'*32, tag='yes')]
    else:
        # Varied actor ordering and changes; model, not generator, decides validity.
        for _ in range(rng.randrange(3, 8)):
            actor = rng.randrange(4)
            seq += [rng.choice([op('uri', actor, uri=uri), op('metadata', actor, key=key, value=value),
                                op('unset', actor), op('transfer', actor, **{'from': rng.randrange(4), 'to': rng.randrange(4)}),
                                op('operator', actor, operator=(actor+1)%4, enabled=bool(rng.randrange(2)))])]
    final = seq[-1]
    claim = dict(type='LAB_REGISTRY_TRANSITION', policy=POLICY, agent_id=final['agent_id'],
                 operation=final['kind'], chain_id=31337, registry_role=role(final))
    supply = True
    # Controlled research-policy perturbations independent of actual observations.
    variant = index % 13
    if family == 'policy_promotion': claim['type'] = rng.choice(['TASK_COMPLETED', 'PAYMENT_AUTHORIZED', 'VERIFIED_EXECUTION'])
    elif variant == 0: claim['policy'] = 'stale'
    elif variant == 1: claim['agent_id'] += 10
    elif variant == 2: claim['chain_id'] = 1
    elif variant == 3: claim['outputHash'] = '0x'+'ff'*32
    elif variant == 4: supply = False
    elif variant == 5: claim['registry_role'] = 'unrelated'
    elif variant == 6: claim['operation'] = 'unrelated'
    return {'id': f's{seed}-c{index:03}', 'seed': seed, 'index': index, 'family': family,
            'input': {'sequence': seq, 'claim': claim, 'supply_receipt': supply}}


def build(seeds=SEEDS, budget=100):
    return {'schema': 'veca.sequence-fixtures.v0', 'generator': VERSION, 'budget_per_seed': budget,
            'seeds': seeds, 'cases': [case(seed, i) for seed in seeds for i in range(budget)]}


def obligations_for(inp):
    active = {'I_STATE', 'P_CLAIM', 'P_EVIDENCE'}
    mapping = {'register': {'N_REG'}, 'metadata': {'I_METADATA'}, 'uri': {'N_URI'},
               'transfer': {'N_TRANSFER'}, 'wallet': {'I_WALLET'}, 'unset': {'I_UNSET'},
               'request': {'N_REQUEST', 'I_REQUEST'}, 'respond': {'N_RESPONSE'}}
    for operation in inp['sequence']:
        active.update(mapping.get(operation['kind'], set()))
        if operation.get('key') == 'agentWallet' or any(m['key'] == 'agentWallet' for m in operation.get('metadata', [])):
            active.add('N_RESERVED')
    return sorted(active)


def write_suite(cases, dest):
    expectations = {c['id']: expected(c['input']) for c in cases}
    obligations = json.loads((PROFILE_DIR/'obligations.json').read_bytes())
    corpus = {'profile': PROFILE, 'vectors': [{'name': c['id'], 'input': c['input'],
               'obligations': obligations_for(c['input']), 'expected': expectations[c['id']]} for c in cases]}
    for name, data in [('expectations', expectations), ('vectors', corpus), ('obligations', obligations)]:
        h.write(dest/(name+'.json'), data)
    h.write(dest/'suite.json', {'id': 'erc8004-property-fuzz-v0', **{n: {'path': n+'.json', 'sha256': h.sha((dest/(n+'.json')).read_bytes())} for n in ('vectors','obligations')}})
    return dest/'suite.json'


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, default=PROFILE_DIR); p.add_argument('--check', action='store_true')
    args = p.parse_args(); fixtures = build()
    if args.check:
        if (args.out/'fixtures.json').read_bytes() != h.encode(fixtures): raise SystemExit('fixture drift')
        exp = {c['id']: expected(c['input']) for c in fixtures['cases']}
        if (args.out/'expectations.json').read_bytes() != h.encode(exp): raise SystemExit('expectation drift')
        print('300 fixtures and independent expectations reproduced')
    else:
        h.write(args.out/'fixtures.json', fixtures); write_suite(fixtures['cases'], args.out)
        print('wrote', len(fixtures['cases']), 'fixtures')
