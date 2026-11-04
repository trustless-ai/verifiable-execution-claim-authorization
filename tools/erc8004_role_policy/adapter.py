"""Existing harness transport with an additive, explicitly versioned policy."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from erc8004.adapter import authorize as transition_authorize
from erc8004_role_policy import policy


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--policy-file', type=Path)
    args = p.parse_args()
    evaluator = policy
    if args.policy_file:  # Trusted local mutation runner, never taken from a claim.
        spec = importlib.util.spec_from_file_location('physical_policy', args.policy_file)
        evaluator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evaluator)
    request = json.load(sys.stdin)
    if request.get('schema') != 'agent-harness.request.v0' or request.get('profile') != policy.POLICY:
        raise ValueError('unsupported request profile')
    proc = subprocess.run(['node', str(ROOT / 'tools/erc8004_role_policy/evm.mjs'),
                           str(ROOT / 'build/erc8004/implementation')], input=json.dumps(request).encode(),
                          capture_output=True, cwd=ROOT, timeout=165)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr)
        return 2
    executed = json.loads(proc.stdout)
    observations = {}
    for case in request['cases']:
        raw = executed['observations'][case['id']]
        actual = copy.deepcopy(raw)
        control = case['input'].get('evidence_control')
        if control == 'missing_roles': actual.pop('request_roles')
        elif control == 'malformed_roles': actual['request_roles']['operator'] = 'false'
        elif control == 'wrong_block': actual['request_roles']['block_hash'] = '0x' + '00' * 32
        elif control == 'wrong_subject': actual['request_roles']['agent_id'] = 1
        elif control == 'missing_request_receipt': actual.pop('request_receipt')
        elif control == 'missing_response_receipt': actual.pop('receipt')
        elif control is not None: raise ValueError('unsupported evidence control')
        status, scope, reason = evaluator.evaluate(case['input'], actual, transition_authorize)
        observations[case['id']] = {
            'behavior': {'operation_status': raw['status'], 'state': raw['state']},
            'authorization': {'status': status, 'authorized': status == 'VERIFIED', 'scope': scope},
            'evidence': {'execution': raw, 'policy_observation': actual, 'policy_reason': reason,
                         'runtime': executed['runtime'], 'authorization_credential': False,
                         'guarantee': 'LABORATORY_REQUEST_TIME_ROLE_SEPARATION',
                         'independent_controller': 'NOT_COVERED', 'judgment_truth': 'NOT_COVERED'}}
    print(json.dumps({'schema': 'agent-harness.observation.v0', 'observations': observations}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
