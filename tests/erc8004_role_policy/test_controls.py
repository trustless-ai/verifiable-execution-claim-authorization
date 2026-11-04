"""Policy boundary and non-kill classification controls; EVM witnesses run separately."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from erc8004.adapter import authorize
from erc8004_role_policy.policy import evaluate, POLICY, CLAIM
from erc8004_role_policy.mutations import classify


class PolicyControls(unittest.TestCase):
    def setUp(self):
        self.inp = {'claim': {'type': CLAIM, 'policy': POLICY, 'agent_id': 0,
                             'operation': 'respond_validation', 'chain_id': 31337, 'registry_role': 'validation'},
                    'operation': {'kind': 'respond_validation', 'agent_id': 0}}
        self.obs = {'chain_id': 31337, 'registry_role': 'validation', 'registry_address': 'local',
                    'receipt': {}, 'status': 'ACCEPTED', 'transaction': {'hash': 'local'},
                    'validator': '0x' + 'ab' * 20, 'request_hash': '0x' + '12' * 32,
                    'request_receipt': {'status': '0x1', 'blockNumber': '0x1', 'blockHash': '0x' + '34' * 32}}
        self.obs['request_roles'] = {'owner': '0x' + '01' * 20, 'validator': self.obs['validator'],
            'approved': '0x' + '00' * 20, 'operator': False, 'agent_id': 0,
            'request_hash': self.obs['request_hash'], 'block_number': '0x1', 'block_hash': '0x' + '34' * 32}

    def result(self): return evaluate(self.inp, self.obs, authorize)

    def test_positive_scope(self):
        status, scope, reason = self.result()
        self.assertEqual(status, 'VERIFIED')
        self.assertEqual(scope['policy'], POLICY)
        self.assertEqual(reason, 'REQUEST_TIME_ROLE_SEPARATION')

    def test_owner_case_insensitive(self):
        self.obs['request_roles']['owner'] = '0x' + 'AB' * 20
        self.assertEqual(self.result()[2], 'SELF_ATTESTED_OWNER')

    def test_operator(self):
        self.obs['request_roles']['operator'] = True
        self.assertEqual(self.result()[2], 'SELF_ATTESTED_OPERATOR')

    def test_approved_case_insensitive(self):
        self.obs['request_roles']['approved'] = '0x' + 'AB' * 20
        self.assertEqual(self.result()[2], 'SELF_ATTESTED_TOKEN_APPROVED')

    def test_missing_distinct_from_malformed(self):
        self.obs.pop('request_roles')
        self.assertEqual(self.result()[2], 'MISSING_REQUEST_ROLES')
        self.obs['request_roles'] = {}
        self.assertEqual(self.result()[2], 'MALFORMED_REQUEST_ROLES')

    def test_malformed_operator_is_not_truthiness(self):
        for value in (0, 1, None, [], {}, 'false'):
            with self.subTest(value=value):
                self.obs['request_roles']['operator'] = value
                self.assertEqual(self.result()[2], 'MALFORMED_REQUEST_ROLES')

    def test_malformed_addresses(self):
        for field in ('owner', 'validator', 'approved'):
            with self.subTest(field=field):
                obs = copy.deepcopy(self.obs); obs['request_roles'][field] = 'untrusted'
                self.assertEqual(evaluate(self.inp, obs, authorize)[2], 'MALFORMED_REQUEST_ROLES')

    def test_request_bindings(self):
        for field, value in [('agent_id', 1), ('request_hash', '0x' + 'ff' * 32),
                             ('validator', '0x' + 'ee' * 20), ('block_number', '0x2'),
                             ('block_hash', '0x' + 'cc' * 32)]:
            with self.subTest(field=field):
                obs = copy.deepcopy(self.obs); obs['request_roles'][field] = value
                self.assertEqual(evaluate(self.inp, obs, authorize)[2], 'CONTRADICTORY_REQUEST_BINDING')

    def test_failed_request(self):
        self.obs['request_receipt']['status'] = '0x0'
        self.assertEqual(self.result()[0], 'REFUTED')

    def test_missing_request_receipt(self):
        self.obs.pop('request_receipt')
        self.assertEqual(self.result()[0], 'UNVERIFIABLE')

    def test_missing_response_receipt(self):
        self.obs.pop('receipt')
        self.assertEqual(self.result()[0], 'UNVERIFIABLE')

    def test_malformed_request_receipt(self):
        for receipt in ('invalid', {'status': 1, 'blockNumber': '0x1', 'blockHash': '0x' + '34' * 32},
                        {'status': '0x1', 'blockNumber': 1, 'blockHash': 'invalid'}):
            with self.subTest(receipt=receipt):
                self.obs['request_receipt'] = receipt
                self.assertEqual(self.result()[2], 'MALFORMED_REQUEST_RECEIPT')

    def test_missing_and_malformed_request_binding(self):
        self.obs.pop('validator')
        self.assertEqual(self.result()[2], 'MISSING_REQUEST_BINDING')
        self.obs['validator'] = 'invalid'
        self.assertEqual(self.result()[2], 'MALFORMED_REQUEST_BINDING')

    def test_reverted_response(self):
        self.obs['status'] = 'REJECTED'
        self.assertEqual(self.result()[0], 'REFUTED')

    def test_exact_version(self):
        self.inp['claim']['policy'] = 'erc8004-registry-observation-v0'
        self.assertEqual(self.result()[2], 'WRONG_POLICY')

    def test_v0_transition_semantics_unchanged(self):
        self.inp['claim'].update(type='LAB_REGISTRY_TRANSITION', policy='erc8004-registry-observation-v0')
        self.obs['request_roles']['owner'] = self.obs['validator']
        self.assertEqual(authorize(self.inp, self.obs)[0], 'VERIFIED')
        self.assertEqual(self.result()[0], 'REFUTED')

    def test_response_roles_cannot_replace_request_snapshot(self):
        self.obs['response_roles'] = {**self.obs['request_roles'], 'operator': True}
        self.assertEqual(self.result()[0], 'VERIFIED')
        self.obs['request_roles']['operator'] = True
        self.obs['response_roles']['operator'] = False
        self.assertEqual(self.result()[0], 'UNVERIFIABLE')


class MutationClassifierControls(unittest.TestCase):
    def test_only_semantic_kill(self):
        baseline = {'backend_conformance': 'PASS'}
        mutant = {'adapter_exit_code': 0, 'exit_code': 1, 'rows': [
            {'id': 'witness', 'backend_conformance': 'FAIL', 'observed_behavior': {'authorization': {'status': 'VERIFIED'}}},
            {'id': 'separate_validator', 'backend_conformance': 'PASS'}]}
        def check(m=mutant, b=baseline, r=baseline, changed=b'changed', restored=b'original'):
            return classify(b, m, r, 'witness', b'original', changed, restored)
        self.assertEqual(check(), 'KILLED')
        self.assertEqual(check(changed=b'original'), 'NO_OP')
        self.assertEqual(check(restored=b'bad'), 'RESTORATION_FAILED')
        self.assertEqual(check(b={'backend_conformance': 'FAIL'}), 'CONTROL_BROKEN')
        self.assertEqual(check(m={**mutant, 'adapter_exit_code': 2}), 'CRASHED')
        self.assertEqual(check(m={**mutant, 'exit_code': 2}), 'UNVERIFIABLE')
        self.assertEqual(check(m={**mutant, 'rows': []}), 'MISSING_OUTPUT')
        survived = copy.deepcopy(mutant); survived['rows'][0]['backend_conformance'] = 'PASS'
        self.assertEqual(check(m=survived), 'SURVIVED')


if __name__ == '__main__': unittest.main()
