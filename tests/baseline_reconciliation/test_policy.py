"""Reject resealed drift and incomplete PR11 compositions without editing history."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from baseline_reconciliation import policy as p


class TransitionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = p.context(ROOT, p.PILOT)

    def state(self, integrated=True):
        historical, original, reviewed, payload = self.context
        actual = dict(historical)
        actual[p.BRIDGE] = p.BRIDGE_SHA256
        if integrated:
            actual.update({path: reviewed[path] for path in p.DOCUMENTS})
            actual.update(payload)
        return actual, dict(actual)

    def result(self, actual, inventory):
        return p.evaluate(*self.context, actual, inventory)

    def test_original_state_preserves_original_document_hashes(self):
        result = self.result(*self.state(False))
        self.assertTrue(result['passed'])
        self.assertEqual(result['document_state'], 'ORIGINAL_DOCUMENTS')
        self.assertEqual(set(result['reviewed_transitions']), {p.BRIDGE})

    def test_integrated_state_requires_exact_three_transitions(self):
        result = self.result(*self.state())
        self.assertTrue(result['passed'])
        self.assertEqual(result['pr11_payload_files'], 13)
        self.assertEqual(set(result['reviewed_transitions']), {*p.DOCUMENTS, p.BRIDGE})
        self.assertEqual(result['unchanged_baseline_files'], len(self.context[0]) - 3)

    def test_resealed_document_drift_is_rejected(self):
        for path in p.DOCUMENTS:
            with self.subTest(path=path):
                actual, inventory = self.state()
                actual[path] = inventory[path] = '0' * 64
                self.assertFalse(self.result(actual, inventory)['passed'])

    def test_mixed_document_versions_are_rejected(self):
        actual, inventory = self.state()
        path = p.DOCUMENTS[0]
        actual[path] = inventory[path] = self.context[1][path]
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_missing_document_is_rejected(self):
        actual, inventory = self.state()
        del actual[p.DOCUMENTS[0]]
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_every_missing_payload_file_is_rejected(self):
        for path in self.context[3]:
            with self.subTest(path=path):
                actual, inventory = self.state()
                del actual[path]
                self.assertIn('bytes:' + path, self.result(actual, inventory)['mismatches'])

    def test_resealed_supplemental_vectors_are_rejected(self):
        actual, inventory = self.state()
        path = 'conformance/agent-harness-review-v0/vectors.json'
        actual[path] = inventory[path] = '1' * 64
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_payload_with_old_documents_is_rejected(self):
        actual, inventory = self.state(False)
        actual.update(self.context[3]); inventory.update(self.context[3])
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_inventory_only_payload_is_rejected(self):
        actual, inventory = self.state(False)
        inventory.update(self.context[3])
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_stale_current_inventory_is_rejected(self):
        actual, inventory = self.state()
        inventory[p.DOCUMENTS[0]] = self.context[1][p.DOCUMENTS[0]]
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_resealed_historical_runtime_and_evidence_are_rejected(self):
        for path in ('tools/agent_harness.py', 'tools/erc8004/adapter.py',
                     'conformance/erc8004-pilot-v0/vectors.json',
                     'conformance/erc8004-pilot-v0/source-lock.json',
                     'evidence/erc8004-pilot-v0/SHA256.json'):
            with self.subTest(path=path):
                actual, inventory = self.state()
                actual[path] = inventory[path] = '2' * 64
                self.assertFalse(self.result(actual, inventory)['passed'])

    def test_unreviewed_checker_change_is_rejected(self):
        actual, inventory = self.state()
        actual[p.BRIDGE] = inventory[p.BRIDGE] = '3' * 64
        self.assertFalse(self.result(actual, inventory)['passed'])

    def test_missing_git_history_is_not_success(self):
        with patch.object(p.subprocess, 'check_output', side_effect=RuntimeError('missing Git object')):
            with self.assertRaises(RuntimeError):
                p.context(ROOT, p.PILOT)

    def test_incorrect_manifest_bytes_are_rejected(self):
        with patch.object(p.subprocess, 'check_output', return_value=b'{"files":{}}'):
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                p.manifest(ROOT, p.REVIEW)

    def test_unknown_baseline_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            p.manifest(ROOT, 'main')

    def test_comparison_does_not_modify_historical_maps(self):
        before = copy.deepcopy(self.context)
        self.result(*self.state())
        self.assertEqual(before, self.context)


if __name__ == '__main__':
    unittest.main()
