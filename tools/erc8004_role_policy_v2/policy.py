"""Finite request-block registry role policy v2. Not controller independence."""
import copy
import hashlib
import json
import re

from erc8004_role_policy.policy import evaluate as evaluate_v1

POLICY = 'erc8004-validator-role-separation-v2'
CLAIM = 'LAB_VALIDATOR_ROLE_SEPARATION'
ZERO = '0x' + '00' * 20
SELECTORS = {'owner': '0x6352211e', 'operator': '0xe985e9c5',
             'approved': '0x081812fc', 'agent_wallet': '0x00339509'}


def address(value):
    return isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{40}', value) is not None


def word(value):
    return format(value, '064x')


def capture_error(observed, roles):
    """Bind locally executed eth_call records to the request receipt and roles.

    These are trusted local EVM observations, not authenticated remote RPC proofs.
    A caller-supplied assertion of verification is never an input to the adapter.
    """
    if 'agent_wallet' not in roles:
        return 'UNVERIFIABLE', 'MISSING_AGENT_WALLET'  # guard: missing_wallet
    if not address(roles['agent_wallet']):
        return 'UNVERIFIABLE', 'MALFORMED_AGENT_WALLET'
    capture = observed.get('request_role_calls')
    if capture is None:
        return 'UNVERIFIABLE', 'MISSING_ROLE_CALLS'
    fields = {'schema', 'capture', 'registry', 'chain_id', 'agent_id', 'validator',
              'request_hash', 'block_number', 'block_hash', 'block', 'calls'}
    if not isinstance(capture, dict) or set(capture) != fields:
        return 'UNVERIFIABLE', 'MALFORMED_ROLE_CALLS'
    if capture['schema'] != 'erc8004.request-role-calls.v2':
        return 'UNVERIFIABLE', 'MALFORMED_ROLE_CALLS'
    if capture['capture'] != 'LOCAL_EVM_ETH_CALL_AT_RECEIPT_BLOCK':
        return 'UNVERIFIABLE', 'UNVERIFIED_ROLE_CALLS'
    registry = observed.get('identity_registry_address')
    if (not address(registry) or not address(capture['registry'])
            or type(capture['chain_id']) is not int or type(capture['agent_id']) is not int
            or not isinstance(capture['block'], dict) or set(capture['block']) != {'number', 'hash'}
            or not isinstance(capture['calls'], dict)):
        return 'UNVERIFIABLE', 'MALFORMED_ROLE_CALLS'
    if set(SELECTORS) - set(capture['calls']):
        return 'UNVERIFIABLE', 'MISSING_ROLE_CALL'
    if set(capture['calls']) != set(SELECTORS):
        return 'UNVERIFIABLE', 'MALFORMED_ROLE_CALLS'
    bindings = {'agent_id': roles['agent_id'], 'validator': roles['validator'],
                'request_hash': roles['request_hash'], 'block_number': roles['block_number'],
                'block_hash': roles['block_hash'], 'chain_id': observed['chain_id']}
    if (any(capture[k] != value for k, value in bindings.items())
            or capture['registry'].lower() != registry.lower()
            or capture['block'] != {'number': roles['block_number'], 'hash': roles['block_hash']}):
        return 'REFUTED', 'CONTRADICTORY_ROLE_CALL_BINDING'
    keys = ('owner', 'operator', 'approved', 'agent_wallet')  # guard: wallet_binding
    for key in keys:
        call = capture['calls'][key]
        if not isinstance(call, dict) or set(call) != {'to', 'data', 'block_tag', 'result'}:
            return 'UNVERIFIABLE', 'MALFORMED_ROLE_CALL'
        if (not address(call['to']) or not isinstance(call['data'], str)
                or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', call['data']) is None
                or not isinstance(call['result'], str)
                or re.fullmatch(r'0x[0-9a-fA-F]{64}', call['result']) is None
                or not isinstance(call['block_tag'], str)
                or re.fullmatch(r'0x[0-9a-fA-F]+', call['block_tag']) is None):
            return 'UNVERIFIABLE', 'MALFORMED_ROLE_CALL'
        arguments = (roles['owner'][2:].lower().zfill(64) + roles['validator'][2:].lower().zfill(64)
                     if key == 'operator' else word(roles['agent_id']))
        expected_result = ('0x' + word(int(roles['operator'])) if key == 'operator'
                           else '0x' + roles[key][2:].lower().zfill(64))
        if (call['to'].lower() != registry.lower() or call['data'].lower() != SELECTORS[key] + arguments
                or call['block_tag'] != roles['block_number'] or call['result'].lower() != expected_result):
            return 'REFUTED', 'CONTRADICTORY_ROLE_CALL'  # guard: contradictory_wallet
    return None


def evaluate(inp, observed, transition_authorize):
    if inp['claim'].get('policy') != POLICY:
        return 'REFUTED', None, 'WRONG_POLICY'
    # Reuse the frozen v1 policy for all prior admission and overlap semantics.
    mapped = copy.deepcopy(inp)
    mapped['claim']['policy'] = 'erc8004-validator-role-separation-v1'
    old_observed = copy.deepcopy(observed)
    if isinstance(old_observed.get('request_roles'), dict):
        old_observed['request_roles'].pop('agent_wallet', None)
    status, _, reason = evaluate_v1(mapped, old_observed, transition_authorize)
    if status != 'VERIFIED':
        return status, None, reason
    roles = observed['request_roles']
    error = capture_error(observed, roles)
    if error is not None:
        return error[0], None, error[1]
    # The fallback is unreachable in an admitted unmodified evaluation: presence
    # and address shape were checked above. Physical controls exercise that gate.
    wallet = roles.get('agent_wallet', ZERO)  # guard: request_time
    if roles['validator'].lower() == wallet.lower():  # guard: wallet
        return 'UNVERIFIABLE', None, 'SELF_ATTESTED_AGENT_WALLET'
    scope = {**inp['claim'], 'operation_sha256': hashlib.sha256(json.dumps(
        inp['operation'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}
    return 'VERIFIED', scope, 'REQUEST_TIME_ROLE_SEPARATION'
