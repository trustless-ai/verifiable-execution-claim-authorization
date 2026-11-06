"""Executed contract controls; assertions remain active under Python -O."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import agent_harness as h


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=Path(os.environ.get('FLASHPROVE_TEST_OUT', ROOT/'build/flashprove-8274/tests'))
        cls.baseline=h.execute(HERE/'suite.json',HERE/'adapter.json',cls.out/'baseline')
        cls.data=json.loads((cls.out/'baseline/adapter.stdout').read_bytes())

    def test_01_complete_native_corpus(self):
        self.assertEqual(self.baseline['exit_code'],0,self.baseline.get('error'))
        self.assertEqual(len(self.baseline['rows']),54)
        self.assertTrue(all(r['backend_conformance']=='PASS' for r in self.baseline['rows']))

    def test_02_expectations_detached(self):
        request=json.loads((self.out/'baseline/request.json').read_bytes())
        self.assertTrue(all(set(row)=={'id','input'} for row in request['cases']))

    def test_03_no_guarantee_promotion(self):
        for row in self.data['observations'].values():
            for axis in ['ZK_PROOF_VERIFIED','ATTESTATION_ACCEPTED','ACTION_AUTHORIZED','ORDER_EXECUTED']:
                self.assertEqual(row['behavior']['guarantees'][axis],'UNVERIFIABLE')
            self.assertFalse(row['authorization']['authorized'])

    def replay(self, name, transform=None, corpus_transform=None, stale=False, argv=None):
        with tempfile.TemporaryDirectory(prefix='flashprove-test-') as td:
            d=Path(td).resolve(); data=json.loads(json.dumps(self.data))
            if transform: transform(data)
            h.write(d/'observations.json',data)
            corpus=json.loads((HERE/'vectors.json').read_bytes())
            if corpus_transform: corpus_transform(corpus)
            h.write(d/'vectors.json',corpus)
            (d/'obligations.json').write_bytes((HERE/'obligations.json').read_bytes())
            suite=json.loads((HERE/'suite.json').read_bytes())
            if not stale: suite['vectors']['sha256']=h.sha((d/'vectors.json').read_bytes())
            h.write(d/'suite.json',suite)
            h.write(d/'adapter.json',{'argv':argv or ['{python}','-B','{repo}/tools/harness_v0/replay.py',str(d/'observations.json')]})
            report=h.execute(d/'suite.json',d/'adapter.json',self.out/name)
            return report

    def test_04_missing_result_unverifiable(self):
        r=self.replay('missing',lambda d:d['observations'].pop('zk_mock_positive'))
        self.assertEqual(r['exit_code'],2)

    def test_05_extra_result_unverifiable(self):
        r=self.replay('extra',lambda d:d['observations'].update(extra=d['observations']['zk_mock_positive']))
        self.assertEqual(r['exit_code'],2)

    def test_06_genuine_mismatch_determinate(self):
        r=self.replay('mismatch',lambda d:d['observations']['zk_mock_positive']['behavior'].update(reason='FALSE_CLAIM'))
        self.assertEqual(r['exit_code'],1)

    def test_07_crash_not_refutation(self):
        r=self.replay('crash',argv=['{python}','-c','raise RuntimeError("synthetic execution failure")'])
        self.assertEqual(r['exit_code'],2)

    def test_08_missing_stdout_not_success(self):
        r=self.replay('empty-output',argv=['{python}','-c','pass'])
        self.assertEqual(r['exit_code'],2)

    def test_09_missing_expectation_not_refutation(self):
        r=self.replay('missing-expectation',corpus_transform=lambda d:d['vectors'][0].pop('expected'))
        self.assertEqual(r['exit_code'],2)

    def test_10_duplicate_identity_not_success(self):
        r=self.replay('duplicate',corpus_transform=lambda d:d['vectors'].append(d['vectors'][0]))
        self.assertEqual(r['exit_code'],2)

    def test_11_stale_pin_not_semantic(self):
        r=self.replay('drift',corpus_transform=lambda d:d.update(changed=True),stale=True)
        self.assertEqual(r['exit_code'],2)
        self.assertIn('suite pin mismatch',r['error'])

    def test_12_empty_corpus_not_success(self):
        r=self.replay('zero-cases',corpus_transform=lambda d:d.update(vectors=[]))
        self.assertEqual(r['exit_code'],2)

    def test_13_empty_request_owner_refusal(self):
        p=subprocess.run([sys.executable,'-B',str(HERE/'adapter.py')],input=b'{"schema":"agent-harness.request.v0","cases":[]}',capture_output=True)
        self.assertEqual(p.returncode,2)
        self.assertIn(b'NONEMPTY_REQUEST_REQUIRED',p.stderr)

    def test_14_generated_oracle_reproducible(self):
        with tempfile.TemporaryDirectory(prefix='flashprove-oracle-') as td:
            d=Path(td).resolve(); (d/'generate_vectors.py').write_bytes((HERE/'generate_vectors.py').read_bytes())
            p=subprocess.run([sys.executable,'-B',str(d/'generate_vectors.py')],capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr)
            for name in ['vectors.json','obligations.json','suite.json','adapter.json']:
                self.assertEqual((d/name).read_bytes(),(HERE/name).read_bytes())

    def test_15_attestation_counter_is_not_signature_validation(self):
        for name in ['attestation_illustrative_two_signatures','attestation_outsider_signatures','attestation_repeated_signature']:
            row=self.data['observations'][name]
            self.assertFalse(row['behavior']['native']['inner'])
            self.assertEqual(row['evidence']['provenance'],'UPSTREAM_SIGNATURE_TODO')


if __name__=='__main__':
    unittest.main(verbosity=2)
