"""Run the new finite corpus/tests without changing any historical inventory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from prepare import verify, ROOT

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1','FLASHPROVE_TEST_OUT':str(a.out.resolve()/'tests')}
    command=[sys.executable,'-B',*(['-O'] if sys.flags.optimize else []),str(HERE/'tests.py')]
    proc=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=300)
    (a.out/'stdout.txt').write_bytes(proc.stdout); (a.out/'stderr.txt').write_bytes(proc.stderr)
    report={'command':command,'exit_code':proc.returncode,'python':sys.version,'os':platform.platform(),
            'source_pins':verify(),'stdout_sha256':hashlib.sha256(proc.stdout).hexdigest(),
            'stderr_sha256':hashlib.sha256(proc.stderr).hexdigest()}
    (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report)); return proc.returncode


if __name__=='__main__':
    raise SystemExit(main())
