"""Declared expectations, authored without importing or executing the policy/backend."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'conformance/erc8004-role-policy-v1'
POLICY = 'erc8004-validator-role-separation-v1'


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def build():
    rows = []
    def case(name, auth, refs, validator=1, role='none', after='none', actor=None,
             update=False, control=None, patch=None):
        op = {'kind': 'respond_validation', 'agent_id': 0, 'validator': validator,
              'actor': validator if actor is None else actor, 'role': role, 'after': after, 'update': update}
        claim = {'type': 'LAB_VALIDATOR_ROLE_SEPARATION', 'policy': POLICY, 'agent_id': 0,
                 'operation': 'respond_validation', 'chain_id': 31337, 'registry_role': 'validation'}
        claim.update(patch or {})
        inp = {'operation': op, 'claim': claim}
        if control: inp['evidence_control'] = control
        accepted = actor is None or actor == validator
        scope = None
        if auth == 'VERIFIED':
            scope = {**claim, 'operation_sha256': hashlib.sha256(json.dumps(
                op, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}
        rows.append({'name': name, 'input': inp, 'obligations': refs,
            'expected': {'behavior': {'operation_status': 'ACCEPTED' if accepted else 'REJECTED',
                                      'state': 'RESPONSE_RECORDED' if accepted else 'RESPONSE_ABSENT'},
                         'authorization': {'status': auth, 'authorized': auth == 'VERIFIED', 'scope': scope}}})
    case('separate_validator', 'VERIFIED', ['R1', 'R2', 'R3', 'R4'])
    case('owner_self', 'UNVERIFIABLE', ['R1'], validator=0)
    case('operator_self', 'UNVERIFIABLE', ['R2'], role='operator')
    case('approved_self', 'UNVERIFIABLE', ['R3'], role='approved')
    case('owner_transfers_away', 'UNVERIFIABLE', ['R1', 'R4'], validator=0, after='transfer_away')
    case('operator_revoked', 'UNVERIFIABLE', ['R2', 'R4'], role='operator', after='revoke_operator')
    case('approved_revoked', 'UNVERIFIABLE', ['R3', 'R4'], role='approved', after='revoke_approved')
    case('later_operator', 'VERIFIED', ['R4'], after='grant_operator')
    case('later_approved', 'VERIFIED', ['R4'], after='grant_approved')
    case('later_owner', 'VERIFIED', ['R4'], after='transfer_to_validator')
    case('separate_update', 'VERIFIED', ['R4', 'R8'], update=True)
    case('wrong_responder', 'REFUTED', ['R8'], actor=2)
    case('wrong_version', 'REFUTED', ['R5'], patch={'policy': 'erc8004-registry-observation-v0'})
    case('wrong_claim', 'REFUTED', ['R5'], patch={'type': 'LAB_REGISTRY_TRANSITION'})
    case('task_truth', 'REFUTED', ['R5'], patch={'type': 'TASK_COMPLETED'})
    for name, patch in [('wrong_claim_subject', {'agent_id': 1}), ('wrong_chain', {'chain_id': 1}),
                        ('wrong_registry', {'registry_role': 'identity'}), ('extra_claim_field', {'independent': True}),
                        ('wrong_operation_claim', {'operation': 'release_payment'})]:
        case(name, 'REFUTED', ['R8'], patch=patch)
    for name, auth, rule in [('missing_roles', 'UNVERIFIABLE', 'R6'), ('malformed_roles', 'UNVERIFIABLE', 'R6'),
                             ('wrong_block', 'REFUTED', 'R7'), ('wrong_subject', 'REFUTED', 'R7'),
                             ('missing_request_receipt', 'UNVERIFIABLE', 'R6'), ('missing_response_receipt', 'UNVERIFIABLE', 'R8')]:
        case(name, auth, [rule], control=name)
    rules = {
        'R1': 'Request-time validator equal to owner is self-attested: UNVERIFIABLE.',
        'R2': 'Request-time isApprovedForAll(owner, validator) is self-attested: UNVERIFIABLE.',
        'R3': 'Request-time getApproved(agentId) equal to validator is self-attested: UNVERIFIABLE.',
        'R4': 'Only roles at the recorded request block govern this bounded claim; later changes do not alter it.',
        'R5': 'Only LAB_VALIDATOR_ROLE_SEPARATION with exact policy v1 is admitted.',
        'R6': 'Missing or malformed request-time evidence cannot establish role separation.',
        'R7': 'Contradictory request-block, subject, validator or request-hash binding is REFUTED.',
        'R8': 'Reuse v0 subject/domain/execution admission; actual designated-validator response and permitted updates.'}
    obligations = {k: {'kind': 'RESEARCH_POLICY', 'clause': k, 'requirement': v,
        'source': 'research/erc8004-role-policy-v1/README.md', 'coverage': 'finite explicit witnesses only'} for k, v in rules.items()}
    values = {'vectors.json': {'profile': POLICY, 'vectors': rows}, 'obligations.json': obligations,
              'adapter.json': {'argv': ['{python}', '-B', '{repo}/tools/erc8004_role_policy/adapter.py']}}
    PROFILE.mkdir(parents=True, exist_ok=True)
    for name, value in values.items(): (PROFILE / name).write_bytes(encode(value))
    suite = {'id': POLICY, **{k: {'path': k + '.json', 'sha256': hashlib.sha256(encode(values[k + '.json'])).hexdigest()}
                             for k in ('vectors', 'obligations')}}
    (PROFILE / 'suite.json').write_bytes(encode(suite))
    return len(rows)


if __name__ == '__main__':
    print(json.dumps({'cases': build()}))
