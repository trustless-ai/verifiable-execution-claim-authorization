"""Full reviewer replay. Results are written only to ignored build or an external out."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
ROOT=HERE.parents[2]
REL=PROJECT.relative_to(ROOT).as_posix()


def sha(data):return hashlib.sha256(data).hexdigest()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(data,indent=2,sort_keys=True)+'\n').encode())


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--legacy',action='store_true');a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):raise RuntimeError('CLEAN_CHECKOUT_REQUIRED')
    commands=[]
    def run(name,args,optimized=False,env=None):
        cmd=[sys.executable,'-B',*(['-O'] if optimized else []),*args]
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=2400,
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1',**(env or {})})
        (out/(name+'.stdout')).write_bytes(result.stdout);(out/(name+'.stderr')).write_bytes(result.stderr)
        commands.append({'name':name,'argv':cmd,'exit_code':result.returncode,'stdout_sha256':sha(result.stdout),'stderr_sha256':sha(result.stderr)})
        write(out/'commands.json',commands);print(name,result.returncode,flush=True)
        if result.returncode:raise RuntimeError('required gate failed: '+name)
    run('root-before',['tools/verify_artifacts.py'])
    run('research-before',[REL+'/verify_evidence.py'])
    run('additive-registration',[REL+'/review_v1/integrity.py'])
    for mode in ['normal','repeat','optimized']:
        optimized=mode=='optimized'
        run('conformance-'+mode,[REL+'/validate.py','--out',str(out/mode)],optimized)
        run('inventory-controls-'+mode,[REL+'/review_v1/test_inventory.py'],optimized,{'FLASHPROVE_INVENTORY_OUT':str(out/('inventory-'+mode))})
        run('counterexamples-'+mode,[REL+'/review_v1/counterexamples.py','--out',str(out/('counterexamples-'+mode))],optimized)
        run('mutations-'+mode,[REL+'/mutations.py','--out',str(out/('mutations-'+mode))],optimized)
    if a.legacy:
        run('legacy-prepare',['tools/v3/prepare.py','--online'])
        for group,script in [('core','tools/erc8404/validate.py'),('harness','tools/harness_v0/validate.py'),('erc8004','tools/erc8004/validate.py'),('v1','tools/erc8004_role_policy/validate.py'),('v2','tools/erc8004_role_policy_v2/validate.py')]:
            run('legacy-'+group,[script,'--out',str(out/'legacy'/group)])
        for mode,optimized in [('normal',False),('optimized',True)]:
            run('baseline-reconciliation-'+mode,['-m','unittest','discover','-s','tests/baseline_reconciliation','-v'],optimized)
    run('preservation',[REL+'/preservation.py','--out',str(out/'preservation.json')])
    run('research-after',[REL+'/verify_evidence.py'])
    run('root-after',['tools/verify_artifacts.py'])
    modes=['normal','repeat','optimized'];det={}
    for filename in ['adapter.stdout','projected.json','request.json']:
        det[filename]={m:sha((out/m/'tests/baseline'/filename).read_bytes()) for m in modes}
        if len(set(det[filename].values()))!=1:raise RuntimeError('determinism failed: '+filename)
    counts={};mutation_reports=[]
    for m in modes:
        report=json.loads((out/m/'tests/baseline/report.json').read_bytes())
        passed=sum(r['backend_conformance']=='PASS' for r in report['rows'])
        count=int(re.search(r'Ran (\d+) tests',(out/m/'stderr.txt').read_text()).group(1))
        inventory=int(re.search(r'Ran (\d+) tests',(out/('inventory-controls-'+m+'.stderr')).read_text()).group(1))
        mutation=json.loads((out/('mutations-'+m)/'results.json').read_bytes());mutation_reports.append(mutation)
        examples=json.loads((out/('counterexamples-'+m)/'results.json').read_bytes())
        counts[m]={'scenarios':passed,'regression_tests':count,'inventory_tests':inventory,
            'mutation_counts':mutation['counts'],'nonkill_controls':sum(x['passed'] for x in mutation['sentinels']),
            'counterexamples':sum(x['passed'] for x in examples['findings']),
            'counterexample_negative_controls':sum(x['negative_control_passed'] for x in examples['findings'])}
        if (passed,count,inventory)!=(54,15,8) or mutation['counts']!={'KILLED':29} or not mutation['passed'] or not examples['passed']:
            raise RuntimeError('incomplete or unexpected result counts')
    if not all(m==mutation_reports[0] for m in mutation_reports):raise RuntimeError('mutation reports differ')
    for finding in ['A','B','C']:
        for filename in ['adapter.stdout','projected.json']:
            hashes={m:sha((out/('counterexamples-'+m)/finding/'run'/filename).read_bytes()) for m in modes}
            if len(set(hashes.values()))!=1:raise RuntimeError('counterexample nondeterminism')
            det[f'counterexample-{finding}-{filename}']=hashes
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT):raise RuntimeError('SOURCE_RESTORATION_FAILED')
    result={'head':head,'passed':True,'counts':counts,'determinism':det,'mutation_reports_byte_identical':True,
            'timing_logs_and_absolute_paths_identical':False,'legacy_executed':a.legacy,
            'preservation':json.loads((out/'preservation.json').read_bytes()),'independent_acceptance':'NOT_ESTABLISHED'}
    write(out/'results.json',result);print(json.dumps({'head':head,'passed':True,'counts':counts},sort_keys=True))


if __name__=='__main__':main()
