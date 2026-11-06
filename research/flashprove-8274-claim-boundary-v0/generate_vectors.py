"""Authored oracle from the pinned source contract, before first execution.

No evaluator import, adapter invocation or observed output is used here. Changes
to this oracle require review; regenerating fixtures is not a way to fix failures.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = lambda n: '0x' + n * 32
A,I,O,T,X = map(H, ['11','22','33','66','77'])
AXES = ['ZK_PROOF_VERIFIED','ATTESTATION_ACCEPTED','CLAIM_AUTHORIZED','ACTION_AUTHORIZED','ORDER_EXECUTED']
MOCK = 'MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE'
TODO = 'ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED'
NATIVE = 'LAB_NATIVE_CALL_REJECTED'
rows=[]


def case(name, operation=None, *, reason=MOCK, status='UNVERIFIABLE', inner=True, outer=True,
         calls=None, claim=None, policy='lab-v0', summary=None, guarantee='CLAIM_AUTHORIZED'):
    op={'kind':'call','route':'zk', **(operation or {})}
    claimed={'route':op['route'],'chain_id':31337,'instance':'selected','agent_id':A,
             'task_id':T,'input_hash':I,'output_hash':O,'requested_guarantee':guarantee, **(claim or {})}
    native={'inner':inner,'outer':outer,'calls':([outer] if calls is None else calls),
            'constructor_accepted':None,'same_committee_profile':None,'same_threshold_profile':None,
            'chain_digest_equal':None,'contract_digest_equal':None,'outer_profile_equal':None,'distinct_signers':None}
    native.update(summary or {})
    axes={k:'UNVERIFIABLE' for k in AXES}; axes['CLAIM_AUTHORIZED']=status
    rows.append({'name':name,'input':{'operation':op,'claim':claimed,'policy_fixture':policy},
                 'expected':{'behavior':{'native':native,'guarantees':axes,'reason':reason},
                             'authorization':{'status':status,'authorized':False,'scope':None}},
                 'obligations':[name]})


case('zk_mock_positive')
case('missing_policy',policy=None,reason='POLICY_NOT_ESTABLISHED')
case('unknown_policy',policy='content-supplied-authority',reason='POLICY_NOT_ESTABLISHED')
case('wrong_route_claim',claim={'route':'attestation'},reason='ROUTE_MISMATCH',status='REFUTED')
case('wrong_chain_claim',claim={'chain_id':1},reason='CHAIN_MISMATCH',status='REFUTED')
case('wrong_contract_claim',claim={'instance':'other'},reason='CONTRACT_MISMATCH',status='REFUTED')
case('wrong_agent_claim',claim={'agent_id':X},reason='AGENT_MISMATCH',status='REFUTED')
case('wrong_task_claim',claim={'task_id':X},reason='TASK_MISMATCH',status='REFUTED')
case('wrong_input_claim',claim={'input_hash':X},reason='INPUT_MISMATCH',status='REFUTED')
case('wrong_output_claim',claim={'output_hash':X},reason='OUTPUT_MISMATCH',status='REFUTED')
case('wrong_input_call',{'input':X},inner=False,outer=False,reason='INPUT_MISMATCH',status='REFUTED')
case('wrong_output_call',{'output':X},inner=False,outer=False,reason='OUTPUT_MISMATCH',status='REFUTED')
case('wrong_commitment',{'cid':X},outer=False,reason=NATIVE,status='REFUTED')
case('unaccepted_verdict',{'verdict':2},outer=False,reason=NATIVE,status='REFUTED')
case('failed_call_status',{'status':1},outer=False,reason=NATIVE,status='REFUTED')
case('wrong_inner_metadata',{'metadata':'wrong'},inner=False)
case('short_inner_metadata',{'metadata':'short'},inner=False)
for mode in ['empty','bad','malformed']:
    case('zk_proof_'+mode,{'proof':mode},inner=False,outer=False,reason=NATIVE,status='REFUTED')
for mode in ['magic','version','reserved','short']:
    case('public_values_'+mode,{'pv':mode},inner=False,outer=False,reason=NATIVE,status='REFUTED')
case('unknown_native_agent',{'agent':X},outer=False,reason='AGENT_MISMATCH',status='REFUTED')
case('caller_impersonates_agent',{'actor':1},reason='CALLER_NOT_AGENT',status='REFUTED')
case('substitute_task',{'task':X},reason='TASK_MISMATCH',status='REFUTED')
case('repeat_same_task',{'repeat':'same'},calls=[True,False],outer=False,reason=NATIVE,status='REFUTED')
case('reuse_proof_fresh_task',{'repeat':'fresh'},calls=[True,True],reason='TASK_MISMATCH',status='REFUTED')
case('reuse_proof_other_contract',{'instance':'other'},reason='CONTRACT_MISMATCH',status='REFUTED')
case('reuse_proof_other_chain',{'chain':31338},reason='CHAIN_MISMATCH',status='REFUTED')
for guarantee in AXES:
    case('no_promotion_'+guarantee.lower(),guarantee=guarantee)
case('attestation_no_signatures',{'route':'attestation','proof':'empty'},inner=False,outer=False,reason=TODO)
case('attestation_invalid_bundle',{'route':'attestation','proof':'malformed'},inner=False,outer=False,reason=TODO)
case('attestation_illustrative_two_signatures',{'route':'attestation','signatures':'two'},inner=False,outer=False,reason=TODO,summary={'distinct_signers':2})
case('attestation_repeated_signature',{'route':'attestation','signatures':'duplicate'},inner=False,outer=False,reason=TODO,summary={'distinct_signers':1})
case('attestation_outsider_signatures',{'route':'attestation','signatures':'outsider'},inner=False,outer=False,reason=TODO,summary={'distinct_signers':2})
case('attestation_two_keys_one_operator',{'route':'attestation','signatures':'two'},policy='one-operator',inner=False,outer=False,reason='OPERATOR_THRESHOLD_NOT_ESTABLISHED',status='REFUTED',summary={'distinct_signers':2})
case('attestation_revoked_assumption',{'route':'attestation','signatures':'two'},policy='revoked',inner=False,outer=False,reason='SIGNER_REVOKED_BY_LAB_POLICY',status='REFUTED',summary={'distinct_signers':2})
case('attestation_untrusted_signer_assumption',{'route':'attestation','signatures':'outsider'},policy='unknown-signer',inner=False,outer=False,reason='SIGNER_NOT_ADMITTED_BY_LAB_POLICY',status='REFUTED',summary={'distinct_signers':2})
case('attestation_wrong_committee',{'route':'attestation','committee':'other'},inner=False,outer=False,reason='COMMITTEE_MISMATCH',status='REFUTED')
case('attestation_is_not_zk',{'route':'attestation','signatures':'two'},inner=False,outer=False,reason=TODO,summary={'distinct_signers':2},guarantee='ZK_PROOF_VERIFIED')
for config in ['valid','empty','zero-threshold','high-threshold','duplicate','zero-signer']:
    case('committee_'+config,{'kind':'constructor','route':'attestation','config':config},inner=None,outer=None,calls=[],reason=TODO,summary={'constructor_accepted':config=='valid'})
case('configuration_profile_collision',{'kind':'profiles','route':'attestation'},inner=None,outer=None,calls=[],reason=TODO,summary={'same_committee_profile':True,'same_threshold_profile':False,'outer_profile_equal':True})
case('attestation_digest_domains',{'kind':'domains','route':'attestation'},inner=None,outer=None,calls=[],reason=TODO,summary={'chain_digest_equal':True,'contract_digest_equal':False})


def write(name,value):
    data=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    (HERE/name).write_bytes(data); return hashlib.sha256(data).hexdigest()


if __name__=='__main__':
    vp=write('vectors.json',{'profile':'flashprove-erc8274-claim-boundary-v0','vectors':rows})
    op=write('obligations.json',{r['name']:{'description':r['name'],'normative':False,
        'scope':'Pinned contract behavior and finite independently selected laboratory consumer policy'} for r in rows})
    write('suite.json',{'id':'flashprove-erc8274-claim-boundary-v0','vectors':{'path':'vectors.json','sha256':vp},'obligations':{'path':'obligations.json','sha256':op}})
    write('adapter.json',{'argv':['{python}','-B','{implementation}/research/flashprove-8274-claim-boundary-v0/adapter.py']})
    print(json.dumps({'authored_cases':len(rows),'vectors_sha256':vp}))
