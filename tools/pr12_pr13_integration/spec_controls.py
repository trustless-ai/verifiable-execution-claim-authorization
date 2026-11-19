"""31 unchanged semantic controls + one explicit versioned preservation control.

The original 32nd assertion requires the pre-main inventory. It must fail on
this composition. Its source stays frozen and all original 32 run on PR13.
This suite neither monkeypatches that checker nor calls its refusal a PASS.
"""
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from pr12_pr13_integration import preservation
spec = importlib.util.spec_from_file_location('historical_spec_controls', ROOT/'tests/spec_drift_coverage/test_controls.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)


class IntegratedPreservation(unittest.TestCase):
    def test_old_contract_refuses_and_exact_new_contract_accepts(self):
        with self.assertRaisesRegex(ValueError, 'historical root inventory entries modified'):
            original.integrity.frozen()
        self.assertTrue(preservation.check()['passed'])
        self.assertFalse(preservation.check()['core_transition_allowed'])


if __name__ == '__main__':
    suite = unittest.TestSuite()
    for cls in (original.DriftControls, original.CoverageControls):
        for name in unittest.defaultTestLoader.getTestCaseNames(cls):
            if name != 'test_all_historical_bytes_unchanged':
                suite.addTest(cls(name))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(IntegratedPreservation))
    if suite.countTestCases() != 32:
        raise ValueError('control population changed')
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
