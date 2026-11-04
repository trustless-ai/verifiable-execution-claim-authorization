"""Independently authored finite profile; does not call or import the adapter."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'conformance/erc8004-pilot-v0'
POLICY = 'erc8004-registry-observation-v0'


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def build():
    lock = json.loads((PROFILE / 'source-lock.json').read_bytes())
    spec = lock['specification']
    spec_url = f"https://github.com/{spec['repository']}/blob/{spec['commit']}/{spec['path']}"
    obligations = {}
    def obligation(key, kind, clause, rule):
        obligations[key] = {'kind': kind, 'source': spec_url if kind == 'NORMATIVE_SPECIFICATION' else
                            'research/erc8004-pilot-v0/PROFILE.md', 'clause': clause, 'requirement': rule,
                            'coverage': 'finite explicit witnesses only'}
    for key, clause, rule in [
        ('N1', 'Identity Registry', 'Agent owner or approved operator may update the agent URI; unrelated actors may not.'),
        ('N2', 'On-chain metadata', 'Changing agentWallet requires proof of control of the new wallet.'),
        ('N3', 'On-chain metadata', 'Transfer clears the agentWallet.'),
        ('N4', 'On-chain metadata', 'agentWallet cannot be set using generic metadata.'),
        ('N5', 'Validation Request', 'Only the owner or operator may request validation.'),
        ('N6', 'Validation Response', 'Only the designated validator may respond to its request.'),
        ('N7', 'Validation Response', 'Multiple responses to the same request are permitted.')]:
        obligation(key, 'NORMATIVE_SPECIFICATION', clause, rule)
    obligation('I1', 'IMPLEMENTATION_BEHAVIOR', 'Pinned IdentityRegistry setAgentWallet', 'The implementation checks signature deadline and EIP-712 domain.')
    obligation('I2', 'IMPLEMENTATION_BEHAVIOR', 'Pinned ValidationRegistry validationRequest', 'The implementation rejects a duplicate requestHash.')
    for key, rule in [
        ('P1', 'Only LAB_REGISTRY_TRANSITION is admitted; no task truth or payment authorization.'),
        ('P2', 'The requested policy version must equal this scenario policy.'),
        ('P3', 'Unknown claim fields are rejected, not silently consumed.'),
        ('P4', 'Claim agent_id must match the actual operation subject.'),
        ('P5', 'Claim operation must match the executed operation.'),
        ('P6', 'Claim chain ID and registry role must match the executed domain.'),
        ('P7', 'A required unavailable transaction receipt makes the claim UNVERIFIABLE.'),
        ('P8', 'An actually reverted transaction cannot support a successful transition claim.')]:
        obligation(key, 'RESEARCH_POLICY', 'Laboratory observation policy v0', rule)
    rows=[]
    def case(name, kind, actor=0, changes=None, expected_status='ACCEPTED', state='URI_UPDATED',
             auth='VERIFIED', refs=('N1',), claim_changes=None, available=True):
        op={'kind':kind,'actor':actor,'agent_id':0,**(changes or {})}
        claim={'type':'LAB_REGISTRY_TRANSITION','policy':POLICY,'agent_id':0,'operation':kind,
               'chain_id':31337,'registry_role':'validation' if 'validation' in kind else 'identity'}
        claim.update(claim_changes or {})
        inp={'operation':op,'claim':claim,'supply_receipt':available}
        scope=None
        if auth=='VERIFIED':
            canonical=json.dumps(op,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode()
            scope={**claim,'operation_sha256':hashlib.sha256(canonical).hexdigest()}
        rows.append({'name':name,'input':inp,'obligations':list(refs),
                     'expected':{'behavior':{'operation_status':expected_status,'state':state},
                                 'authorization':{'status':auth,'authorized':auth=='VERIFIED','scope':scope}}})
    case('uri_owner','set_uri')
    case('uri_operator','set_uri',1,{'approve':True})
    case('uri_stranger','set_uri',3,expected_status='REJECTED',state='URI_UNCHANGED',auth='REFUTED',refs=('N1','P8'))
    case('old_owner_after_transfer','set_uri',0,{'transfer_first':True},'REJECTED','URI_UNCHANGED','REFUTED',('N1','P8'))
    case('wallet_valid','set_wallet',state='WALLET_SET',refs=('N2',))
    for name, changes in [('wallet_wrong_signer',{'signature_actor':3}),('wallet_wrong_chain',{'signature_chain':31338}),
                          ('wallet_wrong_registry',{'signature_registry':'other'}),('wallet_expired',{'expired':True})]:
        case(name,'set_wallet',changes=changes,expected_status='REJECTED',state='WALLET_UNCHANGED',auth='REFUTED',refs=('N2','I1'))
    case('transfer_clears_wallet','transfer',state='WALLET_CLEARED',refs=('N3',))
    case('reserved_wallet_metadata','reserved_metadata',expected_status='REJECTED',state='WALLET_UNCHANGED',auth='REFUTED',refs=('N4',))
    case('request_owner','request_validation',state='REQUEST_RECORDED',refs=('N5',))
    case('request_operator','request_validation',1,{'approve':True},state='REQUEST_RECORDED',refs=('N5',))
    case('request_stranger','request_validation',3,expected_status='REJECTED',state='REQUEST_ABSENT',auth='REFUTED',refs=('N5',))
    case('request_duplicate','request_validation',changes={'duplicate':True},expected_status='REJECTED',state='REQUEST_RECORDED',auth='REFUTED',refs=('I2',))
    case('response_validator','respond_validation',2,state='RESPONSE_RECORDED',refs=('N6',))
    case('response_update_permitted','respond_validation',2,{'update':True},state='RESPONSE_RECORDED',refs=('N7',))
    case('response_stranger','respond_validation',3,expected_status='REJECTED',state='RESPONSE_ABSENT',auth='REFUTED',refs=('N6',))
    case('response_unknown_request','respond_validation',2,{'unknown_request':True},'REJECTED','RESPONSE_ABSENT','REFUTED',('N6',))
    for name, key, patch in [
        ('unsupported_claim','P1',{'type':'TASK_COMPLETED'}),
        ('stale_policy','P2',{'policy':'erc8004-registry-observation-v-1'}),
        ('unconsumed_output_hash','P3',{'outputHash':'0x'+'00'*32}),
        ('wrong_subject','P4',{'agent_id':1}),
        ('wrong_operation','P5',{'operation':'release_payment'}),
        ('wrong_chain_scope','P6',{'chain_id':1}),
        ('wrong_registry_scope','P6',{'registry_role':'unrelated'})]:
        case(name,'set_uri',auth='REFUTED',refs=(key,),claim_changes=patch)
    case('missing_receipt','set_uri',auth='UNVERIFIABLE',refs=('P7',),available=False)
    case('validation_promoted_to_execution','respond_validation',2,state='RESPONSE_RECORDED',auth='REFUTED',refs=('P1',),claim_changes={'type':'TASK_COMPLETED'})
    case('validation_promoted_to_payment','respond_validation',2,state='RESPONSE_RECORDED',auth='REFUTED',refs=('P1',),claim_changes={'type':'PAYMENT_AUTHORIZED'})
    values={'obligations.json':obligations,'vectors.json':{'profile':POLICY,'vectors':rows},
            'adapter.json':{'argv':['{python}','-B','{repo}/tools/erc8004/adapter.py','--implementation-root','{implementation}/build/erc8004/implementation']}}
    for name,value in values.items(): (PROFILE/name).write_bytes(encode(value))
    suite={'id':'erc8004-registry-observation-v0'}
    for key in ('vectors','obligations'):
        name=key+'.json';suite[key]={'path':name,'sha256':hashlib.sha256((PROFILE/name).read_bytes()).hexdigest()}
    (PROFILE/'suite.json').write_bytes(encode(suite))
    print(json.dumps({'scenarios':len(rows),'obligations':len(obligations)}))


if __name__ == '__main__':
    build()
