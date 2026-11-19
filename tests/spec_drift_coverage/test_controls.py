"""Deterministic controls; source network access is never needed by these tests."""
import base64
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'))
from spec_drift_coverage.common import CONFIG, Reader, encode, sha, strict
from spec_drift_coverage import drift, coverage, integrity


class DriftControls(unittest.TestCase):
    def setUp(self):
        self.raw=b'Normative pinned text\n'
        self.pin={'id':'mock','erc':8004,'repository':'example/specs','path':'ERCS/erc-8004.md',
                  'commit':'a'*40,'sha256':sha(self.raw),'upstream_branch':'master','profiles':['mock'],
                  'obligations':[{'profile':'mock','id':'N1'}]}

    def response(self,url,raw,status=200):
        return {'url':url,'http_status':status,'body_base64':base64.b64encode(raw).decode(),
                'body_sha256':sha(raw),'error':None if status==200 else 'HTTP_ERROR'}

    def snapshot(self,commit=None,raw=None):
        commit=commit or self.pin['commit'];raw=self.raw if raw is None else raw
        branch=drift.urls(self.pin);file=drift.urls(self.pin,commit)
        return {'schema':'veca.spec-source-capture.v0','observed_at':'2026-10-22T00:00:00+00:00',
                'evidence_source':'DETERMINISTIC_MOCK_NOT_LIVE',
                'responses':{branch:self.response(branch,encode({'sha':commit})),file:self.response(file,raw)}}

    def result(self,s):return drift.compare(self.pin,s,self.raw)

    def test_unchanged(self):self.assertEqual(self.result(self.snapshot())['comparison'],'UNCHANGED')
    def test_normative_change_detected(self):
        r=self.result(self.snapshot('b'*40,b'Changed requirement\n'))
        self.assertEqual(r['comparison'],'SOURCE_CHANGED_REVIEW_REQUIRED')
        self.assertTrue(r['review_required']);self.assertEqual(r['affected_obligations'],self.pin['obligations'])
        self.assertFalse(r['implementation_failure_proven']);self.assertFalse(r['historical_execution_invalidated'])
    def test_commit_moved_content_unchanged(self):self.assertEqual(self.result(self.snapshot('b'*40))['comparison'],'UPSTREAM_MOVED_CONTENT_UNCHANGED')
    def test_unreachable_ref(self):
        s=self.snapshot();s['responses'][drift.urls(self.pin)]['http_status']=None
        self.assertEqual(self.result(s)['comparison'],'UNVERIFIABLE')
    def test_rate_limit(self):
        s=self.snapshot();s['responses'][drift.urls(self.pin)]['http_status']=429
        self.assertEqual(self.result(s)['comparison'],'UNVERIFIABLE')
    def test_missing_file(self):
        s=self.snapshot();s['responses'][drift.urls(self.pin,self.pin['commit'])]['http_status']=404
        self.assertEqual(self.result(s)['comparison'],'SOURCE_MISSING')
    def test_missing_ref_is_not_missing_file(self):
        s=self.snapshot();s['responses'][drift.urls(self.pin)]['http_status']=404
        self.assertEqual(self.result(s)['comparison'],'UNVERIFIABLE')
    def test_changed_source_does_not_update_pin_or_snapshot(self):
        p=encode(self.pin);s=self.snapshot('b'*40,b'changed');before=encode(s)
        self.result(s);self.assertEqual(p,encode(self.pin));self.assertEqual(before,encode(s))
    def test_tampered_response(self):
        s=self.snapshot();s['responses'][drift.urls(self.pin)]['body_sha256']='0'*64
        self.assertEqual(self.result(s)['comparison'],'UNVERIFIABLE')
    def test_wrong_url(self):
        s=self.snapshot();s['responses'][drift.urls(self.pin)]['url']='https://example.invalid/'
        self.assertEqual(self.result(s)['comparison'],'UNVERIFIABLE')
    def test_bad_pinned_bytes(self):
        self.assertEqual(drift.compare(self.pin,self.snapshot(),b'bad')['comparison'],'UNVERIFIABLE')
    def test_malformed_commit(self):
        s=self.snapshot();u=drift.urls(self.pin);s['responses'][u]=self.response(u,b'{"sha":"bad"}')
        self.assertEqual(self.result(s)['comparison'],'UNVERIFIABLE')
    def test_deterministic_comparison(self):self.assertEqual(encode(self.result(self.snapshot())),encode(self.result(self.snapshot())))


class CoverageControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=strict((CONFIG/'catalog.json').read_bytes())
        cls.bindings=strict((CONFIG/'guard-bindings.json').read_bytes())['bindings']
        cls.reporter=coverage.Reporter()
        cls.report=cls.reporter.build(cls.catalog,cls.bindings)
        cls.pop=cls.catalog['populations'][0];cls.desc=cls.pop['mutations'][0]
        cls.record=cls.reporter.reader.json(cls.pop['report'])['mutations'][0]
        cls.binding=next(b for b in cls.bindings if b['id']==cls.desc['binding'])

    def test_real_frozen_campaigns_admitted_separately(self):
        self.assertTrue(self.report['complete'])
        self.assertEqual([p['counts'] for p in self.report['mutation_populations']],
                         [{'KILLED':12},{'KILLED':17},{'KILLED':4},{'KILLED':6}])
    def test_reference_only_does_not_prove_enforcement(self):
        c=copy.deepcopy(self.catalog);c['profiles'][0]['runs']=[];c['populations']=[]
        r=self.reporter.build(c,[])
        row=r['profiles'][0]['obligations'][0]
        self.assertEqual(row['highest_supported_level'],'REFERENCED_BY_TEST')
        self.assertEqual(row['enforcement_status'],'NOT_COVERED')
    def test_pass_without_distinguishing_mutation(self):
        row=next(o for o in self.report['profiles'][0]['obligations'] if o['id']=='RVR-IDENTITY')
        self.assertEqual(row['highest_supported_level'],'EXECUTED_AND_MATCHED')
        self.assertEqual(row['physical_mutation_bindings'],[])
    def test_incorrect_enforcement_claim_rejected(self):
        with self.assertRaises(ValueError):coverage.check_claims(self.report,[{'profile':'agent-harness-v0','obligation':'RVR-IDENTITY','level':'ENFORCEMENT_DEMONSTRATED'}])
    def test_missing_mutant_not_killed(self):
        d=copy.deepcopy(self.desc);d['mutant_source']['path']='absent-physical-source.py'
        with self.assertRaises(OSError):self.reporter.mutation(self.pop,d,self.record,self.binding)
    def test_crashed_label_not_killed(self):
        r=copy.deepcopy(self.record);r['classification']='CRASHED'
        with self.assertRaises(ValueError):self.reporter.mutation(self.pop,self.desc,r,self.binding)
    def test_killed_label_with_crashed_adapter_not_admitted(self):
        reporter=coverage.Reporter();original=reporter.reader.json
        def read(ref):
            x=original(ref)
            if ref==self.desc['mutated']['report']:x['adapter_exit_code']=1
            return x
        reporter.reader.json=read
        with self.assertRaises(ValueError):reporter.mutation(self.pop,self.desc,self.record,self.binding)
    def test_genuine_kill_maps_specific_obligation(self):
        r=self.reporter.mutation(self.pop,self.desc,self.record,self.binding)
        self.assertEqual(r['obligation'],'POL-AUTHORITY');self.assertEqual(r['classification'],'KILLED')
    def test_unrelated_mutation_cannot_upgrade_claim(self):
        with self.assertRaises(ValueError):coverage.check_claims(self.report,[{'profile':'agent-harness-v0','obligation':'POL-SUBJECT','level':'ENFORCEMENT_DEMONSTRATED','mutation_bindings':['pr9-original-12/authority']}])
    def test_unrelated_mapping_fails_witness_check(self):
        b=copy.deepcopy(self.binding);b['obligation']='RVR-AVAILABLE'
        with self.assertRaises(ValueError):self.reporter.mutation(self.pop,self.desc,self.record,b)
    def test_independent_oracle_is_not_reviewer(self):
        with self.assertRaises(ValueError):coverage.check_claims(self.report,[{'profile':'erc8004-property-fuzz-v0','obligation':'I_STATE','level':'INDEPENDENTLY_REPLAYED'}])
    def test_claimed_independent_replay_metadata_rejected(self):
        c=copy.deepcopy(self.catalog);c['profiles'][0]['independent_replay']['status']='INDEPENDENTLY_REPLAYED'
        with self.assertRaises(ValueError):self.reporter.build(c,self.bindings)
    def test_positive_control_must_exist(self):
        b=copy.deepcopy(self.binding);b['positive_controls']=[]
        with self.assertRaises(ValueError):self.reporter.mutation(self.pop,self.desc,self.record,b)
    def test_unchanged_mutant_source_is_not_kill(self):
        b=copy.deepcopy(self.binding);b['after']=b['before']
        with self.assertRaises(ValueError):self.reporter.mutation(self.pop,self.desc,self.record,b)
    def test_expectations_in_adapter_request_rejected(self):
        reporter=coverage.Reporter();original=reporter.reader.json;unit=self.catalog['profiles'][0]['runs'][0]
        def read(ref):
            x=original(ref)
            if ref==unit['request']:x['expected']='forbidden'
            return x
        reporter.reader.json=read
        with self.assertRaises(ValueError):reporter.unit(unit)
    def test_conformant_refusal_keeps_refuted_authorization(self):
        case=self.report['profiles'][1]['case_outcomes']['uri_stranger']
        self.assertEqual(case['conformance'],'PASS');self.assertEqual(case['authorization']['status'],'REFUTED')
    def test_pr11_is_external_not_integrated(self):
        p=next(p for p in self.report['profiles'] if p['id']=='agent-harness-review-v0')
        self.assertFalse(p['integrated_into_base']);self.assertEqual(p['source_commit'],'e5263f47325a81b0647f3de3a7bc36ad858aea5a')
    def test_all_historical_bytes_unchanged(self):self.assertTrue(integrity.frozen()['passed'])
    def test_repeat_report_deterministic(self):self.assertEqual(encode(self.report),encode(coverage.Reporter().build(self.catalog,self.bindings)))


if __name__=='__main__':unittest.main()
