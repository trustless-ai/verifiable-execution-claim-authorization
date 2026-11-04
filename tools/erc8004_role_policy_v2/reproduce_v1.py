"""Replay the agentWallet boundary with frozen v1 and separate v2 interpretations."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import agent_harness as h
from erc8004.adapter import authorize
from erc8004_role_policy.policy import evaluate as v1
from erc8004_role_policy_v2.policy import evaluate as v2


def run(out):
    out.mkdir(parents=True,exist_ok=True)
    rows=json.loads((ROOT/'conformance/erc8004-role-policy-v2/vectors.json').read_bytes())['vectors']
    selected=[v for v in rows if v['name'] in ('separate_validator','agent_wallet_self','owner_self')]
    request=h.detached_request({'profile':'erc8004-validator-role-separation-v2','vectors':selected})
    h.write(out/'request.json',request)
    argv=['node',str(ROOT/'tools/erc8004_role_policy_v2/evm.mjs'),str(ROOT/'build/erc8004/implementation')]
    proc=subprocess.run(argv,input=json.dumps(request).encode(),capture_output=True,cwd=ROOT,timeout=180)
    (out/'evm.stdout').write_bytes(proc.stdout);(out/'evm.stderr').write_bytes(proc.stderr)
    h.write(out/'command.json',{'argv':argv,'exit_code':proc.returncode,'cwd':str(ROOT)})
    if proc.returncode: raise RuntimeError('actual contract replay failed')
    executed=json.loads(proc.stdout);results={}
    for case in request['cases']:
        obs=executed['observations'][case['id']]
        previous=copy.deepcopy(obs);previous['request_roles'].pop('agent_wallet')
        old_input=copy.deepcopy(case['input']);old_input['claim']['policy']='erc8004-validator-role-separation-v1'
        old=v1(old_input,previous,authorize);new=v2(case['input'],obs,authorize)
        results[case['id']]={'v1':{'status':old[0],'reason':old[2]},'v2':{'status':new[0],'reason':new[2]},
                             'validator':obs['validator'],'request_wallet':obs['request_roles']['agent_wallet'],
                             'request_block':obs['request_receipt']['blockHash']}
    witness=results['agent_wallet_self']
    passed=(witness['v1']=={'status':'VERIFIED','reason':'REQUEST_TIME_ROLE_SEPARATION'}
            and witness['v2']=={'status':'UNVERIFIABLE','reason':'SELF_ATTESTED_AGENT_WALLET'}
            and witness['validator']==witness['request_wallet']
            and results['separate_validator']['v2']['status']=='VERIFIED'
            and results['owner_self']['v2']['reason']=='SELF_ATTESTED_OWNER')
    summary={'schema':'erc8004.agent-wallet-boundary.v2','passed':passed,'results':results,
             'runtime':executed['runtime'],'evidence_source':'LOCAL_AUTHOR_ACTUAL_PINNED_CONTRACT_EXECUTION',
             'interpretation':'New versioned research-policy coverage; not an upstream ERC vulnerability.'}
    h.write(out/'result.json',summary)
    if not passed: raise RuntimeError('agentWallet boundary reproduction failed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    print(json.dumps(run(p.parse_args().out.resolve()),sort_keys=True))
