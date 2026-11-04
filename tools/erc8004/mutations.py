"""Physical mutations in disposable copies; crashes are never kills."""
import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent_harness as h

PROFILE = h.ROOT / 'conformance/erc8004-pilot-v0'
SOURCE = h.ROOT / 'build/erc8004/implementation'
ADAPTER = h.ROOT / 'tools/erc8004/adapter.py'


def definitions():
    identity = 'contracts/IdentityRegistryUpgradeable.sol'
    validation = 'contracts/ValidationRegistryUpgradeable.sol'
    authority = '''require(
            msg.sender == owner ||
            isApprovedForAll(owner, msg.sender) ||
            msg.sender == getApproved(agentId),
            "Not authorized"
        );'''
    request_authority = '''require(
            msg.sender == owner ||
            registry.isApprovedForAll(owner, msg.sender) ||
            registry.getApproved(agentId) == msg.sender,
            "Not authorized"
        );'''
    # section bounds select a single enforcement site where identical syntax recurs.
    rows = [
        ('uri_authority',identity,'function setAgentURI','function getAgentWallet',authority,'','uri_stranger','uri_owner','ACCEPTED'),
        ('wallet_signature',identity,'function setAgentWallet','function unsetAgentWallet',
         'require(ok && res.length >= 32 && abi.decode(res, (bytes4)) == ERC1271_MAGICVALUE, "invalid wallet sig");','',
         'wallet_wrong_signer','wallet_valid','ACCEPTED'),
        ('wallet_deadline',identity,'function setAgentWallet','function unsetAgentWallet',
         'require(block.timestamp <= deadline, "expired");','','wallet_expired','wallet_valid','ACCEPTED'),
        ('transfer_reset',identity,'function _update','function isAuthorizedOrOwner',
         '$._metadata[tokenId]["agentWallet"] = "";','','transfer_clears_wallet','uri_owner','WALLET_RETAINED'),
        ('reserved_wallet',identity,'function setMetadata','function setAgentURI',
         'require(keccak256(bytes(metadataKey)) != RESERVED_AGENT_WALLET_KEY_HASH, "reserved key");','',
         'reserved_wallet_metadata','wallet_valid','ACCEPTED'),
        ('request_authority',validation,'function validationRequest','function validationResponse',request_authority,'',
         'request_stranger','request_owner','ACCEPTED'),
        ('request_duplicate',validation,'function validationRequest','function validationResponse',
         'require($.validations[requestHash].validatorAddress == address(0), "exists");','',
         'request_duplicate','request_owner','ACCEPTED'),
        ('response_authority',validation,'function validationResponse','function getValidationStatus',
         'require(msg.sender == s.validatorAddress, "not validator");','','response_stranger','response_validator','ACCEPTED'),
        ('reject_permitted_updates',validation,'function validationResponse','function getValidationStatus',
         'require(response <= 100, "resp>100");','require(!s.hasResponse, "mutant rejects update");\n        require(response <= 100, "resp>100");',
         'response_update_permitted','response_validator','REJECTED')]
    policies=[('claim_type','claim type','unsupported_claim'),('policy','policy','stale_policy'),
              ('fields','fields','unconsumed_output_hash'),('subject','subject','wrong_subject'),
              ('operation','operation','wrong_operation'),('domain','domain','wrong_chain_scope'),
              ('availability','availability','missing_receipt'),('execution','execution','uri_stranger')]
    return rows, policies


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    corpus=json.loads((PROFILE/'vectors.json').read_bytes())
    by_name={r['name']:r for r in corpus['vectors']}
    definitions_sol, policies=definitions()
    results=[]
    all_defs=[{'id':r[0],'kind':'SOLIDITY','data':r,'witness':r[-3],'positive':r[-2],'effect':r[-1]} for r in definitions_sol]
    all_defs += [{'id':'policy_'+name,'kind':'POLICY','marker':marker,'witness':witness,'positive':'uri_owner','effect':'VERIFIED'} for name,marker,witness in policies]
    for definition in all_defs:
        folder=out/definition['id'];folder.mkdir(parents=True,exist_ok=True)
        selected={'profile':corpus['profile'],'vectors':[by_name[definition['witness']],by_name[definition['positive']]]}
        h.write(folder/'vectors.json',selected)
        shutil.copyfile(PROFILE/'obligations.json',folder/'obligations.json')
        suite={'id':definition['id'],**{key:{'path':key+'.json','sha256':h.sha((folder/(key+'.json')).read_bytes())} for key in ['vectors','obligations']}}
        h.write(folder/'suite.json',suite)
        base_config={'argv':['{python}','-B',str(ADAPTER),'--implementation-root',str(SOURCE)]}
        h.write(folder/'baseline-adapter.json',base_config)
        record={k:v for k,v in definition.items() if k not in ('data','marker')}
        record['classification']='NOT_APPLIED'
        try:
            baseline=h.execute(folder/'suite.json',folder/'baseline-adapter.json',folder/'baseline')
            if baseline['backend_conformance']!='PASS':
                record['classification']='UNVERIFIABLE'
                raise ValueError('baseline controls did not pass')
            config=json.loads(json.dumps(base_config))
            if definition['kind']=='SOLIDITY':
                _,relative,start,end,before,after,*_=definition['data']
                target=folder/'implementation'
                for source in SOURCE.glob('contracts/*.sol'):
                    dest=target/'contracts'/source.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
                filename=target/relative
                raw=filename.read_text(encoding='utf-8')
                left=raw.index(start);right=raw.index(end,left)
                section=raw[left:right]
                if section.count(before)!=1: raise ValueError('mutation site is not unique')
                changed=raw[:left]+section.replace(before,after,1)+raw[right:]
                filename.write_text(changed,encoding='utf-8',newline='\n')
                config['argv'][-1]=str(target)
                record.update(original_sha256=h.sha((SOURCE/relative).read_bytes()),mutant_sha256=h.sha(filename.read_bytes()),source=relative,before=before,after=after)
            else:
                raw=ADAPTER.read_text(encoding='utf-8')
                matches=[line for line in raw.splitlines() if line.endswith('# guard: '+definition['marker'])]
                if len(matches)!=1: raise ValueError('policy site is not unique')
                before=matches[0];after='    if False:  # physically removed '+definition['marker']
                # Only infrastructure relocation plus one semantic change; original
                # ROOT resolution is preserved semantically by its absolute value.
                relocated=raw.replace('ROOT = Path(__file__).resolve().parents[2]','ROOT = Path('+repr(str(h.ROOT))+')')
                filename=folder/'mutant_adapter.py'
                filename.write_text(relocated.replace(before,after,1),encoding='utf-8',newline='\n')
                config['argv'][2]=str(filename)
                record.update(source='tools/erc8004/adapter.py',original_sha256=h.sha(ADAPTER.read_bytes()),mutant_sha256=h.sha(filename.read_bytes()),before=before,after=after)
            h.write(folder/'mutant-adapter.json',config)
            mutated=h.execute(folder/'suite.json',folder/'mutant-adapter.json',folder/'mutated')
            if mutated['exit_code']==2:
                record['classification']='CRASHED'
            else:
                rows={r['id']:r for r in mutated['rows']}
                witness=rows[definition['witness']];positive=rows[definition['positive']]
                actual=witness['observed_behavior']
                effect=actual['authorization']['status'] if definition['kind']=='POLICY' else actual['behavior']['state'] if definition['effect']=='WALLET_RETAINED' else actual['behavior']['operation_status']
                record['observed_effect']=effect
                record['classification']='KILLED' if witness['backend_conformance']=='FAIL' and positive['backend_conformance']=='PASS' and effect==definition['effect'] else 'SURVIVED'
            restored=h.execute(folder/'suite.json',folder/'baseline-adapter.json',folder/'restored')
            record['restored_pass']=restored['backend_conformance']=='PASS'
            if not record['restored_pass']: record['classification']='UNVERIFIABLE'
        except Exception as error:
            record['error']=type(error).__name__+': '+str(error)
        results.append(record)
        report={'schema':'erc8004.physical-mutations.v0','results':results,'counts':{s:sum(r['classification']==s for r in results) for s in ['KILLED','SURVIVED','CRASHED','NOT_APPLIED','UNVERIFIABLE']}}
        h.write(out/'report.json',report)
        print(definition['id'],record['classification'],flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=h.ROOT/'build/erc8004/mutations')
    report=run(p.parse_args().out.resolve())
    print(json.dumps(report['counts']))
    raise SystemExit(0 if report['counts']['KILLED']==17 else 1)
