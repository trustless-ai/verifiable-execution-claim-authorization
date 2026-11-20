"""Indeterminate transport/source failures never become conformance success."""
import argparse
import json
import shutil
import subprocess
import sys
from common import CACHE, ROOT, save, sha
from validate import execute, config

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=__import__('pathlib').Path,required=True);args=parser.parse_args();out=args.out.resolve()
    if out.exists(): raise ValueError('refuse to overwrite evidence')
    out.mkdir(parents=True);results=[]
    for kind in ('changed-source','extra-source','missing-source'):
        copy=out/kind;shutil.copytree(CACHE/'source',copy)
        if kind=='changed-source':
            path=copy/'contracts/ValidationRegistry.vy';path.write_bytes(path.read_bytes()+b'\n# unauthorized byte\n')
        elif kind=='extra-source': (copy/'unexpected.vy').write_bytes(b'# unapproved source\n')
        else: (copy/'contracts/IdentityRegistry.vy').unlink()
        r=execute(kind+'-result',config(out,kind+'-config',copy),out)
        results.append(dict(control=kind,passed=r['backend_conformance']=='UNVERIFIABLE' and r['exit_code']==2,verdict=r['backend_conformance'],adapter_exit=r.get('adapter_exit_code'),error=r.get('error')))
    crash=out/'crash.json';save(crash,{'argv':['{python}','-c','raise SystemExit(7)']})
    r=execute('crashing-backend',crash,out)
    results.append(dict(control='crash-not-killed-or-pass',passed=r['backend_conformance']=='UNVERIFIABLE' and r['exit_code']==2,verdict=r['backend_conformance'],adapter_exit=r.get('adapter_exit_code')))
    request={'schema':'agent-harness.request.v0','profile':'unsupported-profile','cases':[]}
    proc=subprocess.run([sys.executable,'-B',str(ROOT/'tools/erc8004_second_backend/adapter.py')],input=json.dumps(request).encode(),capture_output=True,cwd=ROOT)
    (out/'unsupported.stdout').write_bytes(proc.stdout);(out/'unsupported.stderr').write_bytes(proc.stderr)
    results.append(dict(control='unsupported-profile',passed=proc.returncode!=0 and not proc.stdout,exit_code=proc.returncode))
    original=(ROOT/'tools/erc8004/evm.mjs').read_text(encoding='utf-8');other=(ROOT/'tools/erc8004_second_backend/evm.mjs').read_text(encoding='utf-8')
    def loop(s):return s[s.index("await (await id['register(string)']"):s.index('const output={observations,runtime:')]
    results.append(dict(control='existing-operation-loop-identical',passed=loop(original)==loop(other),sha256=sha(loop(original).encode())))
    save(out/'RESULTS.json',results);print(json.dumps(results,indent=2));return 0 if all(r['passed'] for r in results) else 1
if __name__=='__main__': raise SystemExit(main())
