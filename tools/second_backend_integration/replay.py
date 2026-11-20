"""Bind the current candidate to two checked historical execution views."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from second_backend_integration import preservation as p

def prepare(root=p.ROOT):
    root=Path(root).resolve();current=p.check(root);view=root/p.VIEW
    p.require(view.resolve().is_relative_to(root/'build'),'view_outside_build')
    p.require(not view.is_symlink() and not view.is_junction(),'linked_view')
    if not view.exists():
        view.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','-c','core.autocrlf=false','worktree','add','--detach',str(view),p.BASE],cwd=root,check=True)
    historical=p.check_view(view,root)
    # Executes the old guard and worktree recipe unchanged, not a substitute.
    subprocess.run([sys.executable,'-B','tools/documentation_refresh/replay.py','prepare'],cwd=view,check=True)
    historical=p.check_view(view,root)
    result={'schema':'veca-second-backend-replay-binding-v1','current_head':p.git(root,'rev-parse','HEAD').decode().strip(),'current_status':p.git(root,'status','--porcelain').decode().splitlines(),'current':current,'historical':historical,'legacy_execution_head':p.old.BASE,'new_backend_execution_root':'current candidate','prepare_executes_campaigns':False,'independent_review':'NOT_ESTABLISHED'}
    path=root/p.RECEIPT;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((json.dumps(result,sort_keys=True,indent=2)+'\n').encode());return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('check','prepare'));args=parser.parse_args()
    try:
        result=prepare() if args.operation=='prepare' else p.check()
        if args.operation=='check' and (p.ROOT/p.VIEW).exists():result['historical']=p.check_view(p.ROOT/p.VIEW)
        print(json.dumps(result,sort_keys=True));return 0
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print(json.dumps({'passed':False,'reason':str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
