"""Execute ERC-8004, then interpret only a finite laboratory observation claim.

No expected outcomes or obligation catalog are imported by this adapter.
This profile projection is not a general authorization engine or credential.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:\\PAVLO HQ\\Workspaces\\veca-erc8004-pilot-20261021')
POLICY = 'erc8004-registry-observation-v0'


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def authorize(inp, observed):
    claim = inp['claim']
    op = inp['operation']
    if claim.get('type') != 'LAB_REGISTRY_TRANSITION':  # guard: claim type
        return 'REFUTED', None
    if claim.get('policy') != POLICY:  # guard: policy
        return 'REFUTED', None
    if False:  # physically removed fields
        return 'REFUTED', None
    if claim['agent_id'] != op['agent_id']:  # guard: subject
        return 'REFUTED', None
    if claim['operation'] != op['kind']:  # guard: operation
        return 'REFUTED', None
    if claim['chain_id'] != observed['chain_id'] or claim['registry_role'] != observed['registry_role']:  # guard: domain
        return 'REFUTED', None
    if observed.get('receipt') is None:  # guard: availability
        return 'UNVERIFIABLE', None
    if observed['status'] != 'ACCEPTED':  # guard: execution
        return 'REFUTED', None
    scope = dict(claim)
    scope.update(operation_sha256=hashlib.sha256(canon(op)).hexdigest(),
                 registry_address=observed['registry_address'],
                 transaction_hash=observed['transaction']['hash'])
    return 'VERIFIED', scope


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--implementation-root', type=Path, default=ROOT / 'build/erc8004/implementation')
    args = p.parse_args()
    request = json.load(sys.stdin)
    if request.get('schema') != 'agent-harness.request.v0' or request.get('profile') != 'erc8004-registry-observation-v0':
        raise ValueError('unsupported request profile')
    proc = subprocess.run(['node', str(ROOT / 'tools/erc8004/evm.mjs'), str(args.implementation_root.resolve())],
                          input=json.dumps(request).encode(), capture_output=True, cwd=ROOT, timeout=165)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr)
        return 2
    executed = json.loads(proc.stdout)
    observations = {}
    for case in request['cases']:
        actual = executed['observations'][case['id']]
        if not case['input'].get('supply_receipt', True):
            actual.pop('receipt', None)
        status, scope = authorize(case['input'], actual)
        # Transaction hashes/addresses are raw evidence, not required to be portable
        # across conformant alternative implementations in the common projection.
        projected_scope = None if scope is None else {k: v for k, v in scope.items()
                                                      if k not in ('transaction_hash', 'registry_address')}
        observations[case['id']] = {
            'behavior': {'operation_status': actual['status'], 'state': actual['state']},
            'authorization': {'status': status, 'authorized': status == 'VERIFIED', 'scope': projected_scope},
            'evidence': {'execution': actual, 'authorization_scope': scope, 'runtime': executed['runtime'],
                         'assumptions': ['trusted local EVM and adapter execution', 'finite research policy adequacy'],
                         'guarantee': 'LABORATORY_VERIFIED', 'authorization_credential': False}}
    print(json.dumps({'schema': 'agent-harness.observation.v0', 'observations': observations}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
