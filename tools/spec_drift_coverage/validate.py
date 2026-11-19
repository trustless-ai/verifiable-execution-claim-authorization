"""Execute offline research controls and preserve actual command receipts."""
import argparse
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spec_drift_coverage.common import ROOT, CONFIG, EVIDENCE, sha, strict, write, require


def validate(out):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    source_seal=sha((CONFIG/'source-lock.json').read_bytes())
    commands=[]
    def run(name,args,optimized=False):
        argv=[sys.executable,'-B',*(['-O'] if optimized else []),*args]
        start=time.monotonic()
        process=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=600)
        (out/(name+'.stdout')).write_bytes(process.stdout)
        (out/(name+'.stderr')).write_bytes(process.stderr)
        commands.append({'name':name,'argv':argv,'exit_code':process.returncode,'seconds':time.monotonic()-start,
                         'stdout_sha256':sha(process.stdout),'stderr_sha256':sha(process.stderr)})
        write(out/'commands.json',commands)
        print(name,process.returncode,flush=True)
        require(process.returncode==0,'failed gate: '+name+'; raw logs retained')
    run('integrity',['tools/spec_drift_coverage/integrity.py'])
    run('inventory',['tools/verify_artifacts.py'])
    run('core-history',['tools/erc8404/integrity.py'])
    run('integration-history',['tools/integration/integrity.py'])
    run('core-conformance',['evidence/erc8404/core/conformance/rvr-v0/adapter.py','--check'])
    for mode,opt in [('normal',False),('optimized',True)]:
        run('negative-controls-'+mode,['-m','unittest','discover','-s','tests/spec_drift_coverage','-v'],opt)
        run('transport-'+mode,['-m','unittest','discover','-s','tests/harness_v0','-v'],opt)
    for mode,opt in [('normal',False),('repeat',False),('optimized',True)]:
        run('coverage-'+mode,['tools/spec_drift_coverage/coverage.py','--out',str(out/mode)],opt)
        run('drift-'+mode,['tools/spec_drift_coverage/drift.py','--snapshot',str(EVIDENCE/'SOURCE_CAPTURE.json'),'--out',str(out/mode)],opt)
    digests={name:{mode:sha((out/mode/name).read_bytes()) for mode in ['normal','repeat','optimized']}
             for name in ['COVERAGE.json','SOURCE_DRIFT.json','OBLIGATION_COVERAGE.md']}
    require(all(len(set(d.values()))==1 for d in digests.values()),'repeat/optimized output mismatch')
    coverage=strict((out/'normal/COVERAGE.json').read_bytes())
    require(coverage['complete'],'incomplete coverage evidence')
    require([p['matched_count'] for p in coverage['profiles']]==[18,29,300,5],'historical case population mismatch')
    summary={'schema':'veca.spec-drift-validation.v0','passed':True,'python':sys.version,'platform':platform.platform(),
             'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
             'research_source_lock_sha256':source_seal,
             'working_tree_status':subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).decode().splitlines(),
             'commands':commands,'deterministic_normal_repeat_optimized':True,'output_sha256':digests,
             'profiles':{p['id']:{'matched_cases':p['matched_count'],'obligation_levels':p['coverage_summary']} for p in coverage['profiles']},
             'mutation_populations':{p['id']:p['counts'] for p in coverage['mutation_populations']},
             'drift_counts':strict((out/'normal/SOURCE_DRIFT.json').read_bytes())['counts'],
             'historical_backend_reports_reconciled':True,'new_backend_execution':False,'independent_replay':'NOT_COVERED'}
    require(sha((CONFIG/'source-lock.json').read_bytes())==source_seal,'source seal changed during validation')
    write(out/'SUMMARY.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'build/spec-drift-coverage/validation');a=p.parse_args()
    print(__import__('json').dumps({'passed':validate(a.out)['passed']}))
