"""Execute pinned Vyper, then reuse the unchanged VECA laboratory policy.

Same policy/driver author and EVM as the Solidity pilot: no independent checker claim.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from common import CACHE, ROOT, check_sources, compiler_python, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=CACHE/'source');p.add_argument('--mutation')
    args=p.parse_args()
    request=json.load(sys.stdin)
    if request.get('schema')!='agent-harness.request.v0' or request.get('profile')!='erc8004-registry-observation-v0': raise ValueError('unsupported profile')
    hashes=check_sources(args.source,args.mutation)
    cmd=[str(compiler_python()),'-B','-m','vyper','-p','contracts','--evm-version','shanghai','-O','gas','-f','combined_json','contracts/IdentityRegistry.vy','contracts/ValidationRegistry.vy']
    compiled=subprocess.run(cmd,cwd=args.source,input=b'',capture_output=True,timeout=90)
    if compiled.returncode:
        sys.stderr.buffer.write(compiled.stderr);return 2
    data={key.replace('\\','/'):value for key,value in json.loads(compiled.stdout).items()}
    if data['version']!='0.4.3': raise ValueError('compiler version mismatch')
    artifacts={'compiler_version':data['version'],'source_sha256':hashes,'contracts':{}}
    for name in ('IdentityRegistry','ValidationRegistry'):
        a=data['contracts/'+name+'.vy'];artifacts['contracts'][name]={'abi':a['abi'],'bytecode':a['bytecode']}
    spec=importlib.util.spec_from_file_location('existing_policy',ROOT/'tools/erc8004/adapter.py')
    policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
    with tempfile.TemporaryDirectory(prefix='compiled-',dir=CACHE) as temp:
        path=Path(temp)/'artifacts.json';path.write_bytes(json.dumps(artifacts,sort_keys=True,separators=(',',':')).encode())
        proc=subprocess.run(['node',str(Path(__file__).with_name('evm.mjs')),str(path)],input=json.dumps(request).encode(),capture_output=True,cwd=ROOT,timeout=165)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr);return 2
    executed=json.loads(proc.stdout);observations={}
    for case in request['cases']:
        actual=executed['observations'][case['id']]
        if not case['input'].get('supply_receipt',True): actual.pop('receipt',None)
        status,scope=policy.authorize(case['input'],actual)
        projected=None if scope is None else {k:v for k,v in scope.items() if k not in ('transaction_hash','registry_address')}
        observations[case['id']]={'behavior':{'operation_status':actual['status'],'state':actual['state']},'authorization':{'status':status,'authorized':status=='VERIFIED','scope':projected},'evidence':{'execution':actual,'authorization_scope':scope,'runtime':executed['runtime'],'source_pin_check':'EXACT_MUTATION' if args.mutation else 'PASS','mutation':args.mutation,'compiler_stdout_sha256':sha(compiled.stdout),'assumptions':['trusted local EVM and observer','shared original laboratory policy; not an independent authorization implementation'],'guarantee':'LABORATORY_VERIFIED','authorization_credential':False}}
    print(json.dumps({'schema':'agent-harness.observation.v0','observations':observations},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
