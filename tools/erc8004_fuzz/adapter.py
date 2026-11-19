"""Sequence adapter: actual EVM observations + unchanged narrow policy projection."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from erc8004.adapter import authorize


def assemble():
    original = (ROOT/'tools/erc8004/evm.mjs').read_text(encoding='utf-8')
    lock = json.loads((ROOT/'conformance/erc8004-property-fuzz-v0/source-lock.json').read_bytes())
    if hashlib.sha256((ROOT/'tools/erc8004/evm.mjs').read_bytes()).hexdigest() != lock['preserved']['tools/erc8004/evm.mjs']:
        raise ValueError('bootstrap drift')
    prefix = original.split("await (await id['register(string)']", 1)[0]
    prefix = prefix.replace("const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');", 'const root = '+json.dumps(str(ROOT))+';')
    capture = original[original.index('const txOptions ='):original.index('for (const test of request.cases)')]
    suffix = original[original.index('const output={observations,runtime:'):]
    code = prefix + capture + (ROOT/'tools/erc8004_fuzz/sequence.mjs').read_text(encoding='utf-8') + '\n' + suffix
    target = ROOT/'build/erc8004/fuzz-runner.mjs'
    target.write_text(code, encoding='utf-8', newline='\n')
    return target


def main():
    p = argparse.ArgumentParser(); p.add_argument('--implementation-root', type=Path, default=ROOT/'build/erc8004/implementation')
    args = p.parse_args(); request = json.load(sys.stdin)
    if request.get('schema') != 'agent-harness.request.v0' or request.get('profile') != 'erc8004-sequence-observation-v0':
        raise ValueError('unsupported sequence profile')
    if any(set(c) != {'id','input'} or set(c['input']) != {'sequence','claim','supply_receipt'} for c in request['cases']):
        raise ValueError('expectation-free request required')
    proc = subprocess.run(['node', str(assemble()), str(args.implementation_root.resolve())],
                          input=json.dumps(request).encode(), capture_output=True, cwd=ROOT, timeout=170)
    if proc.returncode:
        sys.stderr.buffer.write(proc.stderr); return 2
    output = json.loads(proc.stdout); observations = {}
    for case in request['cases']:
        inp = case['input']; actual = output['observations'][case['id']]
        last = actual['raw'][-1]
        observed = {**last, 'chain_id':actual['chain_id'], 'registry_role':actual['registry_role'], 'registry_address':actual['registry_address']}
        if not inp['supply_receipt']: observed.pop('receipt')
        status, scope = authorize({'operation': inp['sequence'][-1], 'claim':inp['claim']}, observed)
        projected = None if scope is None else {k:v for k,v in scope.items() if k not in ('transaction_hash','registry_address')}
        observations[case['id']] = {'behavior':{'steps':actual['steps']},
          'authorization':{'status':status,'authorized':status=='VERIFIED','scope':projected},
          'evidence':{'execution':actual,'authorization_scope':scope,'runtime':output['runtime'],
                      'guarantee':'LABORATORY_VERIFIED','authorization_credential':False,
                      'assumptions':['trusted local EVM and adapter','authored oracle adequacy','EOA laboratory actors only']}}
    print(json.dumps({'schema':'agent-harness.observation.v0','observations':observations},sort_keys=True))
    return 0


if __name__ == '__main__': raise SystemExit(main())
