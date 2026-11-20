"""Run both backends and physical Vyper controls through the unchanged grader."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from common import CACHE, ROOT, RESEARCH, check_sources, save, sha

def execute(name, adapter, out):
    dest=out/name
    cmd=[sys.executable,'-B']+(['-O'] if sys.flags.optimize else [])+[str(ROOT/'tools/agent_harness.py'),'run','--suite',str(ROOT/'conformance/erc8004-pilot-v0/suite.json'),'--adapter',str(adapter),'--out',str(dest)]
    start=time.monotonic();p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=210)
    dest.mkdir(parents=True,exist_ok=True);(dest/'command.stdout').write_bytes(p.stdout);(dest/'command.stderr').write_bytes(p.stderr)
    save(dest/'command.json',{'argv':cmd,'exit_code':p.returncode,'seconds':time.monotonic()-start})
    report=json.loads((dest/'report.json').read_bytes())
    if report['exit_code']!=p.returncode: raise ValueError('harness exit mismatch')
    return report

def config(out,name,source,mutation=None):
    argv=['{python}','-B','{repo}/tools/erc8004_second_backend/adapter.py','--source',str(source)]
    if mutation: argv+=['--mutation',mutation]
    path=out/(name+'.json');save(path,{'argv':argv});return path

def field(row, key):
    value=row['observed_behavior']
    for part in key.split('.'): value=value[part]
    return value

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--mutations',action='store_true');args=parser.parse_args()
    out=args.out.resolve()
    if out.exists(): raise ValueError('refuse to overwrite existing evidence')
    out.mkdir(parents=True)
    suite=ROOT/'conformance/erc8004-pilot-v0/suite.json'
    lock=json.loads((RESEARCH/'source-lock.json').read_bytes())
    if sha(suite.read_bytes())!=lock['existing_suite_sha256']: raise ValueError('original suite changed')
    check_sources(CACHE/'source')
    a=execute('solidity',ROOT/'conformance/erc8004-pilot-v0/adapter.json',out)
    b=execute('vyper',RESEARCH/'adapter.json',out)
    for label,r in [('solidity',a),('vyper',b)]:
        if r['backend_conformance']!='PASS' or len(r['rows'])!=29: raise ValueError(label+' did not conform to original 29-case profile')
    ap={r['id']:r['observed_behavior'] for r in a['rows']};bp={r['id']:r['observed_behavior'] for r in b['rows']}
    if ap!=bp: raise ValueError('cross-backend semantic mismatch')
    save(out/'semantic.json',ap)
    baseline_rows={r['id']:r for r in b['rows']}
    mutants=[]
    if args.mutations:
        for recipe in json.loads((RESEARCH/'mutations.json').read_bytes()):
            name=recipe['id'];copy=out/'sources'/name;shutil.copytree(CACHE/'source',copy)
            path=copy/recipe['path'];original=path.read_bytes();before=recipe['before'].encode();after=recipe['after'].encode()
            if original.count(before)!=1: raise ValueError('mutation target must occur exactly once')
            path.write_bytes(original.replace(before,after,1));changed_sha=sha(path.read_bytes())
            result=execute('mutation-'+name,config(out,name,copy,name),out)
            rows={r['id']:r for r in result['rows']}
            changed=[k for k,v in rows.items() if v['observed_behavior']!=baseline_rows[k]['observed_behavior']]
            controls=all(rows.get(k,{}).get('backend_conformance')=='PASS' for k in recipe['positive_controls'])
            witnesses=all(k in rows and field(rows[k],recipe['expected_changed_field'])!=field(baseline_rows[k],recipe['expected_changed_field']) for k in recipe['required_killers'])
            runtime_changed=False
            if rows:
                old=baseline_rows['uri_owner']['evidence']['runtime'];new=rows['uri_owner']['evidence']['runtime']
                key='identity_codehash' if 'IdentityRegistry' in recipe['path'] else 'validation_codehash'
                runtime_changed=old[key]!=new[key]
            path.write_bytes(original);check_sources(copy)
            restored=execute('restored-'+name,config(out,'restored-'+name,copy),out)
            restoration=restored['backend_conformance']=='PASS' and {r['id']:r['observed_behavior'] for r in restored['rows']}==bp
            unexpected=sorted(set(changed)-set(recipe['expected_changed_cases']))
            classification='KILLED' if result['exit_code']==1 and controls and witnesses and runtime_changed and restoration and not unexpected else 'NOT_KILLED'
            if result['exit_code']==2: classification='UNVERIFIABLE'
            row={'id':name,'classification':classification,'changed_cases':changed,'unexpected_changes':unexpected,'required_killers':recipe['required_killers'],'expected_changed_field':recipe['expected_changed_field'],'positive_controls_passed':controls,'runtime_code_changed':runtime_changed,'source_before_sha256':sha(original),'source_mutated_sha256':changed_sha,'source_restored_sha256':sha(path.read_bytes()),'restoration_passed':restoration,'exit_code':result['exit_code']}
            mutants.append(row);save(out/'mutations.json',mutants)
            print(name,classification,flush=True)
    summary={'schema':'erc8004-second-backend.pilot.v0','solidity_cases':len(a['rows']),'vyper_cases':len(b['rows']),'same_semantics':ap==bp,'semantic_sha256':sha((out/'semantic.json').read_bytes()),'mutations':mutants,'passed':all(r['classification']=='KILLED' for r in mutants),'independent_organizational_review':'NOT_ESTABLISHED','public_network_execution':'NOT_RUN','authorization_credential':False}
    save(out/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='mutations'}));return 0 if summary['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
