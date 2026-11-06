"""Finite laboratory consumer policy. Not a credential issuer or production verifier.

Policy fixtures are independently selected by the trusted test invocation. Claim
fields cannot supply a trust root, proof implementation or grant of authority.
"""
AGENT = '0x' + '11' * 32
INPUT = '0x' + '22' * 32
OUTPUT = '0x' + '33' * 32
TASK = '0x' + '66' * 32
AXES = ('ZK_PROOF_VERIFIED', 'ATTESTATION_ACCEPTED', 'CLAIM_AUTHORIZED',
        'ACTION_AUTHORIZED', 'ORDER_EXECUTED')
# Assumptions, not inferred beneficial ownership. Indexes refer to the selected
# committee's two laboratory accounts; no claim field can override this map.
POLICIES = {
    'lab-v0': {'operators': ('operator-a', 'operator-b'), 'revoked': (), 'admitted': (0, 1)},
    'one-operator': {'operators': ('operator-a', 'operator-a'), 'revoked': (), 'admitted': (0, 1)},
    'revoked': {'operators': ('operator-a', 'operator-b'), 'revoked': (1,), 'admitted': (0, 1)},
    'unknown-signer': {'operators': ('operator-a', 'operator-b'), 'revoked': (), 'admitted': ()},
}


def consume(item, native):
    claim = item['claim']
    fixture = item['policy_fixture']
    axes = {key: 'UNVERIFIABLE' for key in AXES}
    status, reason = 'UNVERIFIABLE', 'MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE'
    # Trusted local fixture selection; there is no production policy bootstrap here.
    if fixture not in POLICIES:
        reason = 'POLICY_NOT_ESTABLISHED'
    elif claim['route'] != native['route']:
        status, reason = 'REFUTED', 'ROUTE_MISMATCH'
    elif native['chain_id'] != 31337 or claim['chain_id'] != 31337:
        status, reason = 'REFUTED', 'CHAIN_MISMATCH'
    elif native['instance'] != 'selected' or claim['instance'] != 'selected':
        status, reason = 'REFUTED', 'CONTRACT_MISMATCH'
    elif claim['agent_id'] != AGENT or native['agent_id'] != AGENT:
        status, reason = 'REFUTED', 'AGENT_MISMATCH'
    elif not native['caller_bound']:
        status, reason = 'REFUTED', 'CALLER_NOT_AGENT'
    elif claim['task_id'] != TASK or native['task_id'] != TASK:
        status, reason = 'REFUTED', 'TASK_MISMATCH'
    elif claim['input_hash'] != INPUT or native['input_hash'] != INPUT:
        status, reason = 'REFUTED', 'INPUT_MISMATCH'
    elif claim['output_hash'] != OUTPUT or native['output_hash'] != OUTPUT:
        status, reason = 'REFUTED', 'OUTPUT_MISMATCH'
    elif native['route'] == 'attestation' and not native['committee_bound']:
        status, reason = 'REFUTED', 'COMMITTEE_MISMATCH'
    elif native['route'] == 'attestation' and len(set(POLICIES[fixture]['operators'])) < native['threshold']:
        status, reason = 'REFUTED', 'OPERATOR_THRESHOLD_NOT_ESTABLISHED'
    elif native['route'] == 'attestation' and POLICIES[fixture]['revoked']:
        status, reason = 'REFUTED', 'SIGNER_REVOKED_BY_LAB_POLICY'
    elif native['route'] == 'attestation' and len(POLICIES[fixture]['admitted']) < native['threshold']:
        status, reason = 'REFUTED', 'SIGNER_NOT_ADMITTED_BY_LAB_POLICY'
    elif native['route'] == 'attestation':
        reason = 'ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED'
    elif not native['summary']['outer']:
        status, reason = 'REFUTED', 'LAB_NATIVE_CALL_REJECTED'
    # These are deliberately separate. An accepted mock call establishes none.
    axes['ZK_PROOF_VERIFIED'] = 'UNVERIFIABLE'
    axes['ATTESTATION_ACCEPTED'] = 'UNVERIFIABLE'
    axes['CLAIM_AUTHORIZED'] = status
    axes['ACTION_AUTHORIZED'] = 'UNVERIFIABLE'
    axes['ORDER_EXECUTED'] = 'UNVERIFIABLE'
    return {'behavior': {'native': native['summary'], 'guarantees': axes, 'reason': reason},
            'authorization': {'status': status, 'authorized': False, 'scope': None},
            'evidence': native}
