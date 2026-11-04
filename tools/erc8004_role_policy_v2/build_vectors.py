"""Declared finite expectations; no policy, EVM or observation imports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'conformance/erc8004-role-policy-v2'
POLICY = 'erc8004-validator-role-separation-v2'
# Public deterministic laboratory accounts, not real credentials.
OWNER = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
VALIDATOR = '0x70997970C51812dc3A010C7d01b50e0d17dc79C8'
OTHER = '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC'
ZERO = '0x' + '00' * 20


def encode(value): return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def build():
    rows = []
    def case(name, auth='VERIFIED', reason='REQUEST_TIME_ROLE_SEPARATION', refs=('V2-ROLES',),
             validator=1, role='none', before='none', after='none', actor=None, control=None,
             wallet=OWNER, response_wallet=None, updates=(), patch=None):
        op = {'kind':'respond_validation','agent_id':0,'validator':validator,
              'actor':validator if actor is None else actor,'role':role,'before':before,'after':after}
        claim = {'type':'LAB_VALIDATOR_ROLE_SEPARATION','policy':POLICY,'agent_id':0,
                 'operation':'respond_validation','chain_id':31337,'registry_role':'validation'}
        claim.update(patch or {})
        inp = {'operation':op,'claim':claim}
        if control: inp['evidence_control'] = control
        scope = None
        if auth == 'VERIFIED':
            scope = {**claim,'operation_sha256':hashlib.sha256(json.dumps(op,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
        accepted = actor is None or actor == validator
        rows.append({'name':name,'input':inp,'obligations':list(refs),'expected':{
            'behavior':{'operation_status':'ACCEPTED' if accepted else 'REJECTED',
                'state':'RESPONSE_RECORDED' if accepted else 'RESPONSE_ABSENT','policy_reason':reason,
                'wallet_update_statuses':list(updates),'request_wallet':wallet,
                'response_wallet':wallet if response_wallet is None else response_wallet},
            'authorization':{'status':auth,'authorized':auth == 'VERIFIED','scope':scope}}})
    case('separate_validator',refs=('V2-ROLES','V2-BINDING','V2-AVAILABILITY'))
    case('agent_wallet_self','UNVERIFIABLE','SELF_ATTESTED_AGENT_WALLET',before='wallet_validator',wallet=VALIDATOR,updates=('ACCEPTED',),refs=('V2-ROLES','V2-SIGNATURE'))
    for name,role,validator,reason in [('owner_self','none',0,'OWNER'),('operator_self','operator',1,'OPERATOR'),('approved_self','approved',1,'TOKEN_APPROVED')]:
        case(name,'UNVERIFIABLE','SELF_ATTESTED_' + reason,role=role,validator=validator)
    case('wallet_other',before='wallet_other',wallet=OTHER,updates=('ACCEPTED',))
    case('wallet_changes_before',before='wallet_validator_then_other',wallet=OTHER,updates=('ACCEPTED','ACCEPTED'),refs=('V2-TIME','V2-SIGNATURE'))
    case('wallet_changes_after','UNVERIFIABLE','SELF_ATTESTED_AGENT_WALLET',before='wallet_validator',after='wallet_other',wallet=VALIDATOR,response_wallet=OTHER,updates=('ACCEPTED','ACCEPTED'),refs=('V2-TIME',))
    case('wallet_becomes_validator_after',after='wallet_validator',response_wallet=VALIDATOR,updates=('ACCEPTED',),refs=('V2-TIME',))
    case('wallet_unset_after','UNVERIFIABLE','SELF_ATTESTED_AGENT_WALLET',before='wallet_validator',after='unset_wallet',wallet=VALIDATOR,response_wallet=ZERO,updates=('ACCEPTED',),refs=('V2-TIME',))
    case('wallet_cleared_before_request',before='wallet_then_transfer',wallet=ZERO,updates=('ACCEPTED',),refs=('V2-TRANSFER',))
    case('wallet_cleared_after_request','UNVERIFIABLE','SELF_ATTESTED_AGENT_WALLET',before='wallet_validator',after='transfer_away',wallet=VALIDATOR,response_wallet=ZERO,updates=('ACCEPTED',),refs=('V2-TIME','V2-TRANSFER'))
    case('invalid_signature',before='invalid_wallet_signature',updates=('REJECTED',),refs=('V2-SIGNATURE',))
    for setup in ('wallet_by_operator','wallet_by_approved'):
        case(setup,'UNVERIFIABLE','SELF_ATTESTED_AGENT_WALLET',before=setup,wallet=VALIDATOR,updates=('ACCEPTED',),refs=('V2-SIGNATURE',))
    for role,reason in [('operator','OPERATOR'),('approved','TOKEN_APPROVED')]:
        case(role + '_revoked','UNVERIFIABLE','SELF_ATTESTED_' + reason,role=role,after='revoke_' + role,refs=('V2-TIME',))
        case('later_' + role,after='grant_' + role,refs=('V2-TIME',))
    case('owner_transfers_away','UNVERIFIABLE','SELF_ATTESTED_OWNER',validator=0,after='transfer_away',response_wallet=ZERO,refs=('V2-TIME',))
    case('later_owner',after='transfer_to_validator',response_wallet=ZERO,refs=('V2-TIME',))
    case('wrong_responder','REFUTED','TRANSITION_NOT_ESTABLISHED',actor=2,refs=('V2-ADMISSION',))
    for name,patch,reason in [('wrong_version',{'policy':'erc8004-validator-role-separation-v1'},'WRONG_POLICY'),
                              ('wrong_claim',{'type':'TASK_COMPLETED'},'WRONG_CLAIM'),
                              ('wrong_claim_subject',{'agent_id':1},'TRANSITION_NOT_ESTABLISHED'),
                              ('wrong_chain',{'chain_id':1},'TRANSITION_NOT_ESTABLISHED'),
                              ('wrong_registry',{'registry_role':'identity'},'TRANSITION_NOT_ESTABLISHED'),
                              ('extra_claim_field',{'independence':True},'TRANSITION_NOT_ESTABLISHED')]:
        case(name,'REFUTED',reason,patch=patch,refs=('V2-ADMISSION',))
    controls = {
        'missing_wallet':('UNVERIFIABLE','MISSING_AGENT_WALLET'),
        'malformed_wallet':('UNVERIFIABLE','MALFORMED_AGENT_WALLET'),
        'contradictory_wallet':('REFUTED','CONTRADICTORY_ROLE_CALL'),
        'wrong_wallet_block':('REFUTED','CONTRADICTORY_ROLE_CALL'),
        'wrong_wallet_agent':('REFUTED','CONTRADICTORY_ROLE_CALL'),
        'wrong_wallet_registry':('REFUTED','CONTRADICTORY_ROLE_CALL'),
        'missing_calls':('UNVERIFIABLE','MISSING_ROLE_CALLS'),
        'missing_wallet_call':('UNVERIFIABLE','MISSING_ROLE_CALL'),
        'malformed_wallet_result':('UNVERIFIABLE','MALFORMED_ROLE_CALL'),
        'unverified_calls':('UNVERIFIABLE','UNVERIFIED_ROLE_CALLS'),
        'wrong_call_chain':('REFUTED','CONTRADICTORY_ROLE_CALL_BINDING'),
        'wrong_call_block_hash':('REFUTED','CONTRADICTORY_ROLE_CALL_BINDING'),
        'wrong_call_subject':('REFUTED','CONTRADICTORY_ROLE_CALL_BINDING'),
        'wrong_call_validator':('REFUTED','CONTRADICTORY_ROLE_CALL_BINDING'),
        'wrong_call_request':('REFUTED','CONTRADICTORY_ROLE_CALL_BINDING'),
        'wrong_block':('REFUTED','CONTRADICTORY_REQUEST_BINDING'),
        'wrong_subject':('REFUTED','CONTRADICTORY_REQUEST_BINDING'),
        'missing_roles':('UNVERIFIABLE','MISSING_REQUEST_ROLES'),
        'malformed_roles':('UNVERIFIABLE','MALFORMED_REQUEST_ROLES'),
        'missing_request_receipt':('UNVERIFIABLE','MISSING_REQUEST_RECEIPT'),
        'missing_response_receipt':('UNVERIFIABLE','TRANSITION_NOT_ESTABLISHED')}
    for name,(status,reason) in controls.items():
        case(name,status,reason,control=name,refs=('V2-BINDING' if status == 'REFUTED' else 'V2-AVAILABILITY',))
    case('substituted_wallet_result','REFUTED','CONTRADICTORY_ROLE_CALL',before='wallet_validator',after='wallet_other',wallet=VALIDATOR,response_wallet=OTHER,updates=('ACCEPTED','ACCEPTED'),control='substituted_wallet_result',refs=('V2-BINDING','V2-TIME'))
    rules = {'V2-ROLES':('RESEARCH_POLICY','No observed request-block owner/global-operator/token-approval/agentWallet overlap; zero wallet is an established empty role, not missing evidence.'),
             'V2-TIME':('RESEARCH_POLICY','Request-block roles govern; subsequent changes cannot replace them.'),
             'V2-AVAILABILITY':('RESEARCH_POLICY','Missing, malformed or unverified request-role evidence cannot authorize.'),
             'V2-BINDING':('RESEARCH_POLICY','Bind all four exact eth_call inputs/results to identity registry, agent, validator, request, chain and receipt block; contradictions are REFUTED.'),
             'V2-ADMISSION':('RESEARCH_POLICY','Exact v2 claim with unchanged v0/v1 admission; no independent-controller or judgment-truth claim.'),
             'V2-SIGNATURE':('IMPLEMENTATION_SPECIFIC','Pinned setAgentWallet requires new-wallet EIP-712/1271 signature and an authorized caller. These vectors execute EIP-712 EOA path only.'),
             'V2-TRANSFER':('IMPLEMENTATION_SPECIFIC','Pinned IdentityRegistryUpgradeable._update clears agentWallet on transfer.')}
    obligations = {key:{'kind':kind,'clause':key,'requirement':text,'source':'research/erc8004-role-policy-v2/README.md',
                        'coverage':'finite explicit witnesses; not a new normative ERC requirement'} for key,(kind,text) in rules.items()}
    values = {'vectors.json':{'profile':POLICY,'vectors':rows},'obligations.json':obligations,
              'adapter.json':{'argv':['{python}','-B','{repo}/tools/erc8004_role_policy_v2/adapter.py']}}
    PROFILE.mkdir(parents=True,exist_ok=True)
    for name,value in values.items(): (PROFILE / name).write_bytes(encode(value))
    suite = {'id':POLICY,**{k:{'path':k + '.json','sha256':hashlib.sha256(encode(values[k + '.json'])).hexdigest()} for k in ('vectors','obligations')}}
    (PROFILE / 'suite.json').write_bytes(encode(suite))
    return len(rows)


if __name__ == '__main__': print(json.dumps({'cases':build()}))
