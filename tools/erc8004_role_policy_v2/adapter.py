"""Unchanged harness transport; trusted local EVM evidence and v2 policy."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from erc8004.adapter import authorize
from erc8004_role_policy_v2 import policy


def controlled(raw, control):
    """Declared laboratory evidence faults, never alterations of raw execution."""
    value = copy.deepcopy(raw)
    if control is None: return value
    roles = value['request_roles']
    calls = value['request_role_calls']
    wallet = calls['calls']['agent_wallet']
    if control == 'missing_wallet': roles.pop('agent_wallet')
    elif control == 'malformed_wallet': roles['agent_wallet'] = 'not-an-address'
    elif control == 'contradictory_wallet': roles['agent_wallet'] = raw['actors'][2]
    elif control == 'wrong_wallet_block': wallet['block_tag'] = '0x1'
    elif control == 'wrong_wallet_agent': wallet['data'] = '0x00339509' + format(1, '064x')
    elif control == 'wrong_wallet_registry': wallet['to'] = raw['registry_address']
    elif control == 'substituted_wallet_result':
        wallet['result'] = raw['response_role_calls']['calls']['agent_wallet']['result']
    elif control == 'missing_calls': value.pop('request_role_calls')
    elif control == 'missing_wallet_call': calls['calls'].pop('agent_wallet')
    elif control == 'malformed_wallet_result': wallet['result'] = '0x01'
    elif control == 'unverified_calls': calls['capture'] = 'UNVERIFIED_REMOTE_ASSERTION'
    elif control == 'wrong_call_chain': calls['chain_id'] = 1
    elif control == 'wrong_call_block_hash': calls['block']['hash'] = '0x' + '00' * 32
    elif control == 'wrong_call_subject': calls['agent_id'] = 1
    elif control == 'wrong_call_validator': calls['validator'] = raw['actors'][2]
    elif control == 'wrong_call_request': calls['request_hash'] = '0x' + '00' * 32
    elif control == 'wrong_block': roles['block_hash'] = '0x' + '00' * 32
    elif control == 'wrong_subject': roles['agent_id'] = 1
    elif control == 'missing_roles': value.pop('request_roles')
    elif control == 'malformed_roles': roles['operator'] = 'false'
    elif control == 'missing_request_receipt': value.pop('request_receipt')
    elif control == 'missing_response_receipt': value.pop('receipt')
    else: raise ValueError('unsupported evidence control')
    return value


def main():
    p = argparse.ArgumentParser(); p.add_argument('--policy-file', type=Path)
    args = p.parse_args()
    evaluator = policy
    if args.policy_file:  # Trusted physical mutation runner only, never a claim.
        spec = importlib.util.spec_from_file_location('physical_policy_v2', args.policy_file)
        evaluator = importlib.util.module_from_spec(spec); spec.loader.exec_module(evaluator)
    request = json.load(sys.stdin)
    if (set(request) != {'schema', 'profile', 'cases'}
            or request['schema'] != 'agent-harness.request.v0' or request['profile'] != policy.POLICY
            or any(set(c) != {'id', 'input'} or set(c['input']) - {'claim', 'operation', 'evidence_control'}
                   or set(c['input']['operation']) != {'kind','agent_id','validator','actor','role','before','after'} for c in request['cases'])):
        raise ValueError('unsupported or expectation-bearing request')
    proc = subprocess.run(['node', str(ROOT / 'tools/erc8004_role_policy_v2/evm.mjs'),
                           str(ROOT / 'build/erc8004/implementation')], input=json.dumps(request).encode(),
                          capture_output=True, cwd=ROOT, timeout=240)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr); return 2
    executed = json.loads(proc.stdout)
    observations = {}
    for case in request['cases']:
        raw = executed['observations'][case['id']]
        observed = controlled(raw, case['input'].get('evidence_control'))
        status, scope, reason = evaluator.evaluate(case['input'], observed, authorize)
        observations[case['id']] = {
            'behavior': {'operation_status': raw['status'], 'state': raw['state'], 'policy_reason': reason,
                         'wallet_update_statuses': [r['status'] for r in raw['wallet_updates']],
                         'request_wallet': raw['request_roles']['agent_wallet'],
                         'response_wallet': raw['response_roles']['agent_wallet']},
            'authorization': {'status': status, 'authorized': status == 'VERIFIED', 'scope': scope},
            'evidence': {'execution': raw, 'policy_observation': observed, 'runtime': executed['runtime'],
                         'policy': policy.POLICY, 'authorization_credential': False,
                         'guarantee': 'LABORATORY_REQUEST_TIME_FOUR_REGISTRY_ROLE_SEPARATION',
                         'assumptions': ['trusted local EVM, adapter and source-lock validation'],
                         'independent_controller': 'NOT_COVERED', 'judgment_truth': 'NOT_COVERED',
                         'public_chain_authentication': 'NOT_COVERED'}}
    print(json.dumps({'schema': 'agent-harness.observation.v0', 'observations': observations}, sort_keys=True))
    return 0


if __name__ == '__main__': raise SystemExit(main())
