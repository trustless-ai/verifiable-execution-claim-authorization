"""Finite profile replay, physically discriminating mutations and baseline checks."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import agent_harness as h


def validate(out):
    out.mkdir(parents=True,exist_ok=True)
    commands=[]
    def run(name,args,optimized=False):
        cmd=[sys.executable,'-B',*(['-O'] if optimized else []),*args]
        start=time.perf_counter();proc=subprocess.run(cmd,cwd=h.ROOT,capture_output=True,timeout=900)
        (out/(name+'.stdout')).write_bytes(proc.stdout);(out/(name+'.stderr')).write_bytes(proc.stderr)
        commands.append({'name':name,'argv':cmd,'exit_code':proc.returncode,'seconds':time.perf_counter()-start,
                         'stdout_sha256':h.sha(proc.stdout),'stderr_sha256':h.sha(proc.stderr)})
        h.write(out/'commands.json',commands);print(name,proc.returncode,flush=True)
        if proc.returncode:raise RuntimeError(name+' failed; inspect raw logs')
    run('integrity-before',['tools/erc8004/integrity.py'])
    run('transport-regression',['-m','unittest','discover','-s','tests/harness_v0','-v'])
    # Both real backends use the exact same unchanged harness/grader.
    run('erc8404-pilot-regression',['tools/agent_harness.py','run','--out',str(out/'erc8404')])
    observations=[]
    for name,optimized in [('normal',False),('repeat',False),('optimized',True)]:
        run('erc8004-'+name,['tools/agent_harness.py','run','--suite','conformance/erc8004-pilot-v0/suite.json',
                            '--adapter','conformance/erc8004-pilot-v0/adapter.json','--out',str(out/name)],optimized)
        observations.append((out/name/'projected.json').read_bytes())
    run('physical-mutations',['tools/erc8004/mutations.py','--out',str(out/'mutations')])
    run('negative-infrastructure',['-m','unittest','discover','-s','tests/erc8004','-v'])
    run('core-conformance',['evidence/erc8404/core/conformance/rvr-v0/adapter.py','--check'])
    run('integrity-after',['tools/erc8004/integrity.py'])
    report=json.loads((out/'normal/report.json').read_bytes());mut=json.loads((out/'mutations/report.json').read_bytes())
    deterministic=len(set(observations))==1
    summary={'schema':'erc8004.validation.v0','passed':deterministic,'semantic_determinism':deterministic,
             'scenarios':len(report['rows']),'conformant':sum(r['backend_conformance']=='PASS' for r in report['rows']),
             'authorization_counts':{s:sum(r['observed_behavior']['authorization']['status']==s for r in report['rows']) for s in ['VERIFIED','REFUTED','UNVERIFIABLE']},
             'mutations':mut['counts'],'python':sys.version,'platform':platform.platform(),'commands':commands,
             'source_lock_sha256':h.sha((h.ROOT/'conformance/erc8004-pilot-v0/source-lock.json').read_bytes()),
             'guarantee':'LABORATORY_VERIFIED','universal_erc_conformance':False,'external_execution_verified':False}
    h.write(out/'summary.json',summary)
    if not deterministic:raise RuntimeError('semantic determinism failed')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=h.ROOT/'build/erc8004/validation')
    result=validate(p.parse_args().out.resolve());print(json.dumps({k:result[k] for k in ['passed','scenarios','conformant','mutations']}))
