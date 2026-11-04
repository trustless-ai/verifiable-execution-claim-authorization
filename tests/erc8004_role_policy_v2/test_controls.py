"""Synthetic unit controls supplement, and never stand in for, actual EVM witnesses."""
import ast
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from erc8004.adapter import authorize
from erc8004_role_policy_v2.policy import evaluate, POLICY, CLAIM, SELECTORS
from erc8004_role_policy_v2.mutations import classify
import agent_harness as harness


class PolicyControls(unittest.TestCase):
    def setUp(self):
        self.inp={'claim':{'type':CLAIM,'policy':POLICY,'agent_id':0,'operation':'respond_validation','chain_id':31337,'registry_role':'validation'},
                  'operation':{'kind':'respond_validation','agent_id':0}}
        self.obs={'chain_id':31337,'registry_role':'validation','registry_address':'local',
                  'receipt':{},'status':'ACCEPTED','transaction':{'hash':'local'},
                  'validator':'0x'+'ab'*20,'request_hash':'0x'+'12'*32,
                  'identity_registry_address':'0x'+'cd'*20,
                  'request_receipt':{'status':'0x1','blockNumber':'0x10','blockHash':'0x'+'34'*32}}
        self.roles={'owner':'0x'+'01'*20,'validator':self.obs['validator'],'approved':'0x'+'00'*20,
                    'agent_wallet':'0x'+'02'*20,'operator':False,'agent_id':0,'request_hash':self.obs['request_hash'],
                    'block_number':'0x10','block_hash':'0x'+'34'*32}
        self.obs['request_roles']=self.roles
        self.calls={}
        for key,selector in SELECTORS.items():
            args=(self.roles['owner'][2:].zfill(64)+self.roles['validator'][2:].zfill(64) if key=='operator' else '0'*64)
            value='0'*64 if key=='operator' else self.roles[key][2:].zfill(64)
            self.calls[key]={'to':self.obs['identity_registry_address'],'data':selector+args,'block_tag':'0x10','result':'0x'+value}
        self.capture={**{k:self.roles[k] for k in ('agent_id','validator','request_hash','block_number','block_hash')},
                      'schema':'erc8004.request-role-calls.v2','capture':'LOCAL_EVM_ETH_CALL_AT_RECEIPT_BLOCK',
                      'registry':self.obs['identity_registry_address'],'chain_id':31337,
                      'block':{'number':'0x10','hash':self.roles['block_hash']},'calls':self.calls}
        self.obs['request_role_calls']=self.capture

    def result(self): return evaluate(self.inp,self.obs,authorize)

    def test_positive_scope_and_version(self):
        status,scope,reason=self.result()
        self.assertEqual((status,reason),('VERIFIED','REQUEST_TIME_ROLE_SEPARATION'))
        self.assertEqual(scope['policy'],POLICY)

    def test_wallet_overlap_case_insensitive(self):
        self.roles['agent_wallet']='0x'+'AB'*20
        self.calls['agent_wallet']['result']='0x'+('ab'*20).zfill(64)
        self.assertEqual(self.result()[2],'SELF_ATTESTED_AGENT_WALLET')

    def test_missing_wallet_distinct(self):
        self.roles.pop('agent_wallet')
        self.assertEqual(self.result()[2],'MISSING_AGENT_WALLET')

    def test_wallet_malformed_shapes(self):
        for value in (None,False,0,{},[],'','0x00','0x'+'gg'*20):
            with self.subTest(value=value):
                self.roles['agent_wallet']=value
                self.assertEqual(self.result()[2],'MALFORMED_AGENT_WALLET')

    def test_zero_wallet_established_not_missing(self):
        self.roles['agent_wallet']='0x'+'00'*20;self.calls['agent_wallet']['result']='0x'+'00'*32
        self.assertEqual(self.result()[0],'VERIFIED')

    def test_missing_capture(self):
        self.obs.pop('request_role_calls')
        self.assertEqual(self.result()[2],'MISSING_ROLE_CALLS')

    def test_unverified_capture(self):
        self.capture['capture']='HOST_ASSERTION'
        self.assertEqual(self.result()[2],'UNVERIFIED_ROLE_CALLS')

    def test_capture_schema_and_shape(self):
        for value in (None,{},[],{'schema':'other'}):
            with self.subTest(value=value):
                self.obs['request_role_calls']=value
                self.assertEqual(self.result()[0],'UNVERIFIABLE')

    def test_capture_binding_mismatches(self):
        for key,value in [('agent_id',1),('chain_id',1),('validator','0x'+'ff'*20),('request_hash','0x'+'ff'*32),
                          ('block_number','0x11'),('block_hash','0x'+'ff'*32),('registry','0x'+'ee'*20)]:
            with self.subTest(key=key):
                obs=copy.deepcopy(self.obs);obs['request_role_calls'][key]=value
                self.assertEqual(evaluate(self.inp,obs,authorize)[2],'CONTRADICTORY_ROLE_CALL_BINDING')

    def test_bool_cannot_be_chain_or_agent_integer(self):
        for key in ('chain_id','agent_id'):
            obs=copy.deepcopy(self.obs);obs['request_role_calls'][key]=True
            self.assertEqual(evaluate(self.inp,obs,authorize)[2],'MALFORMED_ROLE_CALLS')

    def test_block_resolution_mismatch(self):
        self.capture['block']['hash']='0x'+'ff'*32
        self.assertEqual(self.result()[2],'CONTRADICTORY_ROLE_CALL_BINDING')

    def test_each_call_is_separately_bound(self):
        for key in SELECTORS:
            for field,value in [('to','0x'+'ff'*20),('data','0xdeadbeef'),('block_tag','0x11'),('result','0x'+'ff'*32)]:
                with self.subTest(call=key,field=field):
                    obs=copy.deepcopy(self.obs);obs['request_role_calls']['calls'][key][field]=value
                    self.assertEqual(evaluate(self.inp,obs,authorize)[2],'CONTRADICTORY_ROLE_CALL')

    def test_noncanonical_abi_address_padding(self):
        self.calls['agent_wallet']['result']='0x'+'ff'*12+self.roles['agent_wallet'][2:]
        self.assertEqual(self.result()[2],'CONTRADICTORY_ROLE_CALL')

    def test_malformed_call_values(self):
        for field,value in [('to',None),('data','0x0'),('result','0x01'),('block_tag',16)]:
            obs=copy.deepcopy(self.obs);obs['request_role_calls']['calls']['agent_wallet'][field]=value
            self.assertEqual(evaluate(self.inp,obs,authorize)[2],'MALFORMED_ROLE_CALL')

    def test_call_cannot_be_missing_or_have_extra_fields(self):
        for kind in ('missing','extra'):
            obs=copy.deepcopy(self.obs)
            if kind=='missing': obs['request_role_calls']['calls'].pop('agent_wallet')
            else: obs['request_role_calls']['calls']['agent_wallet']['verified']=True
            self.assertEqual(evaluate(self.inp,obs,authorize)[0],'UNVERIFIABLE')

    def test_prior_overlap_priorities_preserved(self):
        for key,value,reason in [('owner',self.obs['validator'],'SELF_ATTESTED_OWNER'),('operator',True,'SELF_ATTESTED_OPERATOR'),('approved',self.obs['validator'],'SELF_ATTESTED_TOKEN_APPROVED')]:
            obs=copy.deepcopy(self.obs);obs['request_roles'][key]=value
            self.assertEqual(evaluate(self.inp,obs,authorize)[2],reason)

    def test_request_receipt_required(self):
        self.obs.pop('request_receipt');self.assertEqual(self.result()[0],'UNVERIFIABLE')

    def test_wrong_request_receipt_block(self):
        self.obs['request_receipt']['blockNumber']='0x11'
        self.assertEqual(self.result()[2],'CONTRADICTORY_REQUEST_BINDING')

    def test_response_wallet_cannot_override_request(self):
        self.obs['response_roles']={**self.roles,'agent_wallet':self.obs['validator']}
        self.assertEqual(self.result()[0],'VERIFIED')
        self.roles['agent_wallet']=self.obs['validator']
        self.calls['agent_wallet']['result']='0x'+self.obs['validator'][2:].zfill(64)
        self.obs['response_roles']['agent_wallet']='0x'+'00'*20
        self.assertEqual(self.result()[2],'SELF_ATTESTED_AGENT_WALLET')

    def test_wrong_policy_and_claim(self):
        self.inp['claim']['policy']='erc8004-validator-role-separation-v1'
        self.assertEqual(self.result()[2],'WRONG_POLICY')
        self.inp['claim']['policy']=POLICY;self.inp['claim']['type']='INDEPENDENT_HUMAN'
        self.assertEqual(self.result()[2],'WRONG_CLAIM')

    def test_reverted_validation_response_not_authorized(self):
        self.obs['status']='REJECTED';self.assertEqual(self.result()[0],'REFUTED')

    def test_missing_response_receipt(self):
        self.obs.pop('receipt');self.assertEqual(self.result()[0],'UNVERIFIABLE')

    def test_expectation_free_transport(self):
        corpus=json.loads((ROOT/'conformance/erc8004-role-policy-v2/vectors.json').read_bytes())
        request=harness.detached_request(corpus)
        self.assertEqual(set(request),{'schema','profile','cases'})
        for case in request['cases']:
            self.assertEqual(set(case),{'id','input'})
            self.assertFalse(set(case['input']) & {'expected','obligations','outcome'})

    def test_expectation_generator_has_no_policy_or_backend_import(self):
        tree=ast.parse((ROOT/'tools/erc8004_role_policy_v2/build_vectors.py').read_bytes())
        imports=[alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names]
        imports += [node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        self.assertEqual(set(imports),{'hashlib','json','pathlib'})


class MutationControls(unittest.TestCase):
    def setUp(self):
        self.base={'backend_conformance':'PASS'}
        self.expected={'behavior':{'state':'RESPONSE_RECORDED','policy_reason':'SELF_ATTESTED_AGENT_WALLET'},
                       'authorization':{'status':'UNVERIFIABLE','authorized':False,'scope':None}}
        self.actual={'behavior':{'state':'RESPONSE_RECORDED','policy_reason':'REQUEST_TIME_ROLE_SEPARATION'},
                     'authorization':{'status':'VERIFIED','authorized':True,'scope':{}}}
        self.mut={'adapter_exit_code':0,'exit_code':1,'rows':[
            {'id':'witness','backend_conformance':'FAIL','expected_behavior':self.expected,'observed_behavior':self.actual},
            {'id':'separate_validator','backend_conformance':'PASS'}]}

    def check(self,mut=None,base=None,changed=b'changed',restored=b'original',applied=True):
        return classify(self.base if base is None else base,self.mut if mut is None else mut,self.base,'witness',b'original',changed,restored,applied)

    def test_semantic_kill(self): self.assertEqual(self.check(),'KILLED')
    def test_no_op(self): self.assertEqual(self.check(changed=b'original'),'NO_OP')
    def test_not_applied(self): self.assertEqual(self.check(applied=False),'NOT_APPLIED')
    def test_crash(self): self.assertEqual(self.check(mut={**self.mut,'adapter_exit_code':2}),'CRASHED')
    def test_missing_output(self): self.assertEqual(self.check(mut={**self.mut,'rows':[]}),'MISSING_OUTPUT')
    def test_missing_behavior_field_is_not_kill(self):
        self.actual['behavior'].pop('state');self.assertEqual(self.check(),'MISSING_OUTPUT')
    def test_broken_positive(self):
        self.mut['rows'][1]['backend_conformance']='FAIL';self.assertEqual(self.check(),'CONTROL_BROKEN')
    def test_broken_baseline(self): self.assertEqual(self.check(base={'backend_conformance':'FAIL'}),'CONTROL_BROKEN')
    def test_failed_restoration(self): self.assertEqual(self.check(restored=b'bad'),'RESTORATION_FAILED')
    def test_infrastructure_unverifiable(self): self.assertEqual(self.check(mut={**self.mut,'exit_code':2}),'UNVERIFIABLE')
    def test_survived(self):
        self.mut['rows'][0]['backend_conformance']='PASS';self.assertEqual(self.check(),'SURVIVED')
    def test_unrelated_behavior_failure_is_not_kill(self):
        self.actual['behavior']['state']='OTHER';self.assertEqual(self.check(),'SURVIVED')


if __name__=='__main__': unittest.main()
