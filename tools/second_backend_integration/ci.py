"""Execute the current second backend; never reuse historical verdict files."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from second_backend_integration import preservation as p

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((json.dumps(obj,indent=2,sort_keys=True)+'\n').encode())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=p.ROOT/'build/second-backend-integration/campaign');parser.add_argument('--prepared',action='store_true',help='Use already prepared, still checked pinned dependencies');args=parser.parse_args()
    out=args.out.resolve();p.require(not out.exists(),'output_exists');out.mkdir(parents=True)
    before=p.check();commands=[]
    def run(label,argv):
        start=time.monotonic();r=subprocess.run([str(v) for v in argv],cwd=p.ROOT,capture_output=True,timeout=1800)
        path=out/'commands'/label;path.parent.mkdir(parents=True,exist_ok=True)
        path.with_suffix('.stdout').write_bytes(r.stdout);path.with_suffix('.stderr').write_bytes(r.stderr)
        commands.append({'label':label,'argv':list(map(str,argv)),'exit_code':r.returncode,'seconds':time.monotonic()-start,'stdout_sha256':p.sha(r.stdout),'stderr_sha256':p.sha(r.stderr)})
        write(out/'COMMANDS.json',commands);print(label,r.returncode,flush=True)
        p.require(r.returncode==0,'command_failed:'+label)
    if not args.prepared:
        for label,script in [('grader','tools/agent_harness.py'),('solidity','tools/erc8004/prepare.py'),('vyper','tools/erc8004_second_backend/prepare.py')]:
            run('prepare-'+label,[sys.executable,'-B',script]+(['prepare'] if label=='grader' else []))
    summaries={}
    for mode,flags in [('normal',[]),('repeat',[]),('optimized',['-O'])]:
        dest=out/mode
        run(mode,[sys.executable,'-B',*flags,'tools/erc8004_second_backend/validate.py','--out',dest]+(['--mutations'] if mode!='repeat' else []))
        row=json.loads((dest/'summary.json').read_bytes());summaries[mode]=row
        p.require(row['passed'] and row['solidity_cases']==29 and row['vyper_cases']==29 and row['same_semantics'],'case_or_semantic_failure')
        if mode!='repeat':
            p.require(len(row['mutations'])==6,'mutation_population')
            p.require(all(m['classification']=='KILLED' and m['positive_controls_passed'] and m['runtime_code_changed'] and m['restoration_passed'] and not m['unexpected_changes'] for m in row['mutations']),'mutation_failure')
    semantics=[(out/m/'semantic.json').read_bytes() for m in summaries]
    p.require(len(set(semantics))==1,'semantic_nondeterminism')
    for mutation in summaries['normal']['mutations']:
        name='mutation-'+mutation['id']
        p.require((out/'normal'/name/'projected.json').read_bytes()==(out/'optimized'/name/'projected.json').read_bytes(),'mutation_nondeterminism:'+name)
    run('negative',[sys.executable,'-B','tools/erc8004_second_backend/negative_controls.py','--out',out/'negative'])
    controls=json.loads((out/'negative/RESULTS.json').read_bytes());p.require(len(controls)==6 and all(r['passed'] for r in controls),'negative_controls')
    run('core-integrity',[sys.executable,'-B','tools/erc8404/integrity.py'])
    after=p.check();p.require(before==after,'current_tree_changed')
    result={'schema':'veca-second-backend-ci-v1','passed':True,'current_head':p.git(p.ROOT,'rev-parse','HEAD').decode().strip(),'execution_root':str(p.ROOT),'current_transition':after,'semantics_sha256':p.sha(semantics[0]),'cases_per_backend':29,'unique_mutations':6,'modes':summaries,'controls':controls,'existing_core_unchanged':True,'independent_review':'NOT_ESTABLISHED','production':'HOLD'}
    write(out/'RESULTS.json',result);print(json.dumps({'passed':True,'cases_per_backend':29,'unique_mutations':6}));return 0
if __name__=='__main__':raise SystemExit(main())
