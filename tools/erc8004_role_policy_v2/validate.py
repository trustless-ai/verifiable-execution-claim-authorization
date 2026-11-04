"""Run actual v2 evidence and compare whole observations, not PASS strings."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import agent_harness as h


def validate(out):
    out.mkdir(parents=True,exist_ok=True);commands=[]
    def run(name,args,optimized=False):
        argv=[sys.executable,'-B',*(['-O'] if optimized else []),*args]
        proc=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=1000)
        (out/(name+'.stdout')).write_bytes(proc.stdout);(out/(name+'.stderr')).write_bytes(proc.stderr)
        commands.append({'name':name,'argv':argv,'exit_code':proc.returncode,'stdout_sha256':h.sha(proc.stdout),'stderr_sha256':h.sha(proc.stderr)})
        h.write(out/'commands.json',commands);print(name,proc.returncode,flush=True)
        if proc.returncode: raise RuntimeError(name+' failed; retained raw logs are not a pass')
    run('inventory-before',['tools/verify_artifacts.py'])
    run('preservation-before',['tools/erc8004_role_policy_v2/integrity.py'])
    for mode,opt in [('normal',False),('repeat',False),('optimized',True)]:
        run(mode,['tools/agent_harness.py','run','--suite','conformance/erc8004-role-policy-v2/suite.json',
                  '--adapter','conformance/erc8004-role-policy-v2/adapter.json','--out',str(out/mode)],opt)
    for mode,opt in [('normal',False),('optimized',True)]:
        run('controls-'+mode,['-m','unittest','discover','-s','tests/erc8004_role_policy_v2','-v'],opt)
        run('mutations-'+mode,['tools/erc8004_role_policy_v2/mutations.py','--out',str(out/('mutations-'+mode))],opt)
        run('boundary-'+mode,['tools/erc8004_role_policy_v2/reproduce_v1.py','--out',str(out/('boundary-'+mode))],opt)
    run('preservation-after',['tools/erc8004_role_policy_v2/integrity.py'])
    run('inventory-after',['tools/verify_artifacts.py'])
    modes=('normal','repeat','optimized')
    projected={mode:h.sha((out/mode/'projected.json').read_bytes()) for mode in modes}
    whole={mode:h.sha((out/mode/'adapter.stdout').read_bytes()) for mode in modes}
    mutation_reports=[json.loads((out/('mutations-'+mode)/'report.json').read_bytes()) for mode in ('normal','optimized')]
    boundary_reports=[(out/('boundary-'+mode)/'result.json').read_bytes() for mode in ('normal','optimized')]
    corpus=json.loads((ROOT/'conformance/erc8004-role-policy-v2/vectors.json').read_bytes())['vectors']
    report=json.loads((out/'normal/report.json').read_bytes())
    captures=0;updates=0;requests=0
    for mode in modes:
        actual=json.loads((out/mode/'adapter.stdout').read_bytes())['observations']
        for row in actual.values():
            raw=row['evidence']['execution']
            for phase,receipt_key in [('request','request_receipt'),('response','receipt')]:
                roles=raw[phase+'_roles'];capture=raw[phase+'_role_calls'];receipt=raw[receipt_key]
                if (roles['block_number']!=receipt['blockNumber'] or roles['block_hash']!=receipt['blockHash']
                        or capture['block']!={'number':receipt['blockNumber'],'hash':receipt['blockHash']}
                        or any(call['block_tag']!=receipt['blockNumber'] for call in capture['calls'].values())
                        or set(capture['calls'])!={'owner','operator','approved','agent_wallet'}):
                    raise RuntimeError('actual four-role capture is not tied to its receipt')
                captures+=1
            for update in raw['wallet_updates']:
                accepted=update['status']=='ACCEPTED'
                if accepted != (update['receipt']['status']=='0x1'):
                    raise RuntimeError('wallet receipt/status mismatch')
                if accepted and (update['after']!=update['value']['newWallet'] or update['recovered']!=update['value']['newWallet']):
                    raise RuntimeError('accepted EIP-712 update lacks matching signer/state')
                if not accepted and (update['before']!=update['after'] or update['recovered']==update['value']['newWallet']):
                    raise RuntimeError('invalid signature control not established')
                updates+=1
    for path in out.rglob('request.json'):
        request=json.loads(path.read_bytes())
        if set(request)!={'schema','profile','cases'} or any(set(case)!={'id','input'} for case in request['cases']):
            raise RuntimeError('expectations entered adapter transport')
        requests+=1
    summary={'schema':'erc8004-role-policy.validation.v2','passed':len(set(projected.values()))==1 and len(set(whole.values()))==1
             and mutation_reports[0]==mutation_reports[1] and boundary_reports[0]==boundary_reports[1],
             'cases':len(report['rows']),'conformant':sum(r['backend_conformance']=='PASS' for r in report['rows']),
             'distinct_inputs':len({h.encode(v['input']) for v in corpus}),
             'authorization_counts':{s:sum(r['observed_behavior']['authorization']['status']==s for r in report['rows']) for s in ('VERIFIED','REFUTED','UNVERIFIABLE')},
             'controls':{mode:int(re.search(r'Ran (\d+) tests',(out/('controls-'+mode+'.stderr')).read_text()).group(1)) for mode in ('normal','optimized')},
             'behavioral_sha256':projected,'complete_observation_sha256':whole,'physical_mutations':mutation_reports[0]['counts'],
             'mutation_modes_equal':mutation_reports[0]==mutation_reports[1],'boundary_modes_equal':boundary_reports[0]==boundary_reports[1],
             'request_response_role_captures_audited':captures,'wallet_updates_audited':updates,'expectation_free_requests':requests,
             'python':sys.version,'node':subprocess.check_output(['node','--version'],text=True).strip(),'platform':platform.platform(),
             'independent_controller':'NOT_COVERED','independent_reviewer_replay':'NOT_COVERED','public_chain_authentication':'NOT_COVERED'}
    h.write(out/'summary.json',summary)
    if not summary['passed'] or summary['cases']!=summary['conformant']: raise RuntimeError('complete v2 validation did not pass')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'build/role-policy-v2/validation')
    print(json.dumps(validate(p.parse_args().out.resolve()),sort_keys=True))
