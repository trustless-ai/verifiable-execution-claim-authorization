"""Versioned, finite laboratory role-separation policy; no normative ERC changes."""
import hashlib
import json
import re

POLICY = 'erc8004-validator-role-separation-v1'
CLAIM = 'LAB_VALIDATOR_ROLE_SEPARATION'


def evaluate(inp, observed, transition_authorize):
    claim = inp['claim']
    if claim.get('policy') != POLICY:  # guard: version
        return 'REFUTED', None, 'WRONG_POLICY'
    if claim.get('type') != CLAIM:  # guard: claim
        return 'REFUTED', None, 'WRONG_CLAIM'
    if inp['operation']['kind'] != 'respond_validation':
        return 'REFUTED', None, 'UNSUPPORTED_OPERATION'
    # Reuse all eight historical admission/execution guards without editing v0.
    mapped = {**inp, 'claim': {**claim, 'type': 'LAB_REGISTRY_TRANSITION',
                              'policy': 'erc8004-registry-observation-v0'}}
    status, _ = transition_authorize(mapped, observed)
    if status != 'VERIFIED':
        return status, None, 'TRANSITION_NOT_ESTABLISHED'
    evidence = observed.get('request_roles')
    if evidence is None:
        return 'UNVERIFIABLE', None, 'MISSING_REQUEST_ROLES'
    fields = {'owner', 'validator', 'approved', 'operator', 'agent_id',
              'request_hash', 'block_number', 'block_hash'}
    if not isinstance(evidence, dict) or set(evidence) != fields:
        return 'UNVERIFIABLE', None, 'MALFORMED_REQUEST_ROLES'
    address = lambda x: isinstance(x, str) and re.fullmatch(r'0x[0-9a-fA-F]{40}', x)
    hash32 = lambda x: isinstance(x, str) and re.fullmatch(r'0x[0-9a-fA-F]{64}', x)
    if (not all(address(evidence[k]) for k in ('owner', 'validator', 'approved'))
            or type(evidence['operator']) is not bool
            or type(evidence['agent_id']) is not int
            or not hash32(evidence['request_hash']) or not hash32(evidence['block_hash'])
            or not isinstance(evidence['block_number'], str)
            or not re.fullmatch(r'0x[0-9a-fA-F]+', evidence['block_number'])):
        return 'UNVERIFIABLE', None, 'MALFORMED_REQUEST_ROLES'
    receipt = observed.get('request_receipt')
    if receipt is None or (isinstance(receipt, dict) and not all(k in receipt for k in ('blockHash', 'blockNumber', 'status'))):
        return 'UNVERIFIABLE', None, 'MISSING_REQUEST_RECEIPT'
    if (not isinstance(receipt, dict) or not hash32(receipt['blockHash'])
            or not isinstance(receipt['blockNumber'], str)
            or not re.fullmatch(r'0x[0-9a-fA-F]+', receipt['blockNumber'])
            or receipt['status'] not in ('0x0', '0x1')):
        return 'UNVERIFIABLE', None, 'MALFORMED_REQUEST_RECEIPT'
    if observed.get('validator') is None or observed.get('request_hash') is None:
        return 'UNVERIFIABLE', None, 'MISSING_REQUEST_BINDING'
    if not address(observed['validator']) or not hash32(observed['request_hash']):
        return 'UNVERIFIABLE', None, 'MALFORMED_REQUEST_BINDING'
    if (receipt['status'] != '0x1' or evidence['agent_id'] != claim['agent_id']
            or evidence['request_hash'] != observed.get('request_hash')
            or evidence['validator'].lower() != str(observed.get('validator')).lower()
            or evidence['block_number'] != receipt['blockNumber']
            or evidence['block_hash'] != receipt['blockHash']):  # guard: binding
        return 'REFUTED', None, 'CONTRADICTORY_REQUEST_BINDING'
    validator = evidence['validator'].lower()
    if validator == evidence['owner'].lower():  # guard: owner
        return 'UNVERIFIABLE', None, 'SELF_ATTESTED_OWNER'
    if evidence['operator']:  # guard: operator
        return 'UNVERIFIABLE', None, 'SELF_ATTESTED_OPERATOR'
    if validator == evidence['approved'].lower():  # guard: approved
        return 'UNVERIFIABLE', None, 'SELF_ATTESTED_TOKEN_APPROVED'
    scope = {**claim, 'operation_sha256': hashlib.sha256(json.dumps(
        inp['operation'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}
    return 'VERIFIED', scope, 'REQUEST_TIME_ROLE_SEPARATION'
