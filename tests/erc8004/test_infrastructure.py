"""Infrastructure failures must not become conformance successes."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import agent_harness as h


class InfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'build')
        self.path=Path(self.temp.name)
        self.profile=ROOT/'conformance/erc8004-pilot-v0'

    def tearDown(self):self.temp.cleanup()

    def execute(self,argv):
        h.write(self.path/'adapter.json',{'argv':argv})
        return h.execute(self.profile/'suite.json',self.path/'adapter.json',self.path/'result')

    def test_missing_adapter_is_not_pass(self):
        r=self.execute(['{python}',str(self.path/'absent.py')])
        self.assertNotEqual(r['backend_conformance'],'PASS');self.assertEqual(r['exit_code'],2)

    def test_crash_is_not_pass(self):
        r=self.execute(['{python}','-c','raise RuntimeError("controlled crash")'])
        self.assertNotEqual(r['backend_conformance'],'PASS');self.assertEqual(r['exit_code'],2)

    def test_empty_report_is_not_pass(self):
        r=self.execute(['{python}','-c','print(\'{"schema":"agent-harness.observation.v0","observations":{}}\')'])
        self.assertNotEqual(r['backend_conformance'],'PASS');self.assertNotEqual(r['exit_code'],0)

    def test_source_drift_is_detected(self):
        spec=importlib.util.spec_from_file_location('pilot_integrity',ROOT/'tools/erc8004/integrity.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        target=ROOT/'build/erc8004/implementation/contracts/ERC1967Proxy.sol'
        original=target.read_bytes()
        try:
            target.write_bytes(original+b'\n// controlled drift\n')
            r=mod.check();self.assertFalse(r['passed']);self.assertIn('source:implementation/contracts/ERC1967Proxy.sol',r['mismatches'])
        finally:target.write_bytes(original)

    def test_missing_source_is_detected(self):
        spec=importlib.util.spec_from_file_location('pilot_integrity_missing',ROOT/'tools/erc8004/integrity.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        target=ROOT/'build/erc8004/implementation/contracts/ERC1967Proxy.sol'
        original=target.read_bytes()
        try:
            target.unlink();r=mod.check();self.assertFalse(r['passed'])
        finally:target.write_bytes(original)


if __name__=='__main__':unittest.main()
