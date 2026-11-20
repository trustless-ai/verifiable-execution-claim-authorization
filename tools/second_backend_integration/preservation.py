"""Exact composition of merged PR15 and the frozen second-backend pilot.

Historical guards run unchanged in pinned views. Current Vyper execution is
separate and is never replaced by historical outputs. Git review is the trust root.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE='29155372c6a16f23d1bc2091f2f3671c51e0da4c'
PILOT='1ce2b4e0f3e83faf1a16d5ced0507aca20e4ba90'
PILOT_BASE='4b6d7ef9aabd23932668711ee1d6cf774d9844d7'
POLICY='research/erc8004-second-backend-integration-v1/TRANSITION.json'
POLICY_SHA256='3440d2e4a250021ce10946735881e8dcdecc0b5fe6c880aa3bae3fbda179d98c'
VIEW='build/base15'
INNER=VIEW+'/build/documentation-replay'
RECEIPT='build/second-backend-integration/REPLAY.json'
ARCHIVE='research/history/README-29155372.md'
EXCLUDED={'.git','build','__pycache__','.venv'}
sys.path.insert(0,str(ROOT/'tools'))
from documentation_refresh import preservation as old
UNTOUCHED=old.UNCHANGED_WORKFLOWS
NEW_PATHS=(
    '.github/workflows/erc8004-second-backend.yml',
    'tools/second_backend_integration/preservation.py',
    'tools/second_backend_integration/replay.py',
    'tools/second_backend_integration/ci.py',
    'tests/second_backend_integration/test_preservation.py',
    'research/erc8004-second-backend-integration-v1/README.md',
    'research/erc8004-second-backend-integration-v1/REPORT.md',
    POLICY,ARCHIVE,
    'evidence/erc8004-second-backend-integration-v1/RESULTS.json',
    'evidence/erc8004-second-backend-integration-v1/EVIDENCE.zip',
    'evidence/erc8004-second-backend-integration-v1/SHA256.json',
)
REPORTS={
    'research/erc8004-second-backend-integration-v1/REPORT.md',
    'evidence/erc8004-second-backend-integration-v1/RESULTS.json',
    'evidence/erc8004-second-backend-integration-v1/EVIDENCE.zip',
    'evidence/erc8004-second-backend-integration-v1/SHA256.json',
}
def require(ok,reason):
    if not ok:raise ValueError(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root)
def strict(raw):return old.strict(raw)
def inventory(root):
    root=Path(root);result={}
    for folder,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDED)
        for d in dirs:
            p=Path(folder)/d
            require(not p.is_symlink() and not p.is_junction(),'linked_protected_directory')
        for name in sorted(files):
            path=Path(folder)/name
            if name=='.git' or path.suffix=='.pyc' or path==root/'artifacts.sha256.json':continue
            require(not path.is_symlink(),'linked_protected_file')
            result[path.relative_to(root).as_posix()]=sha(path.read_bytes())
    return result
def workflow(name,raw):
    text=raw.decode()
    if name=='.github/workflows/documentation-refresh.yml':
        require('    defaults:' not in text,'unexpected_workflow_defaults')
        text=text.replace('    steps:\n','    defaults:\n      run:\n        working-directory: '+VIEW+'\n    steps:\n')
        text=text.replace('working-directory: build/documentation-replay','working-directory: '+INNER)
        text=text.replace('path: build/documentation-refresh','path: |\n            '+VIEW+'/build/documentation-refresh\n            '+RECEIPT)
        pos=text.index('      - run:')
        text=text[:pos]+('      - name: Check current integration and prepare historical views\n        working-directory: .\n        run: python -B tools/second_backend_integration/replay.py prepare\n')+text[pos:]
        pos=text.index('      - uses: actions/upload-artifact@')
        text=text[:pos]+('      - name: Recheck current and historical identities\n        if: always()\n        working-directory: .\n        run: python -B tools/second_backend_integration/replay.py check\n')+text[pos:]
    else:
        require('build/documentation-replay' in text,'missing_previous_routing')
        text=text.replace('build/documentation-replay',INNER)
        text=text.replace('tools/documentation_refresh/replay.py','tools/second_backend_integration/replay.py')
        text=text.replace('build/documentation-refresh/REPLAY.json',VIEW+'/build/documentation-refresh/REPLAY.json\n            '+RECEIPT)
    return text.encode()
def normalized_verifier(raw):
    # Binds this file's body without a circular policy-digest dependency.
    value,count=re.subn(rb"(?m)^POLICY_SHA256='[^']*'$",b"POLICY_SHA256='TO_BE_SEALED'",raw)
    require(count==1,'verifier_digest_slot');return value
def pilot_files(root):
    changes=git(root,'diff','--name-status',PILOT_BASE,PILOT).decode().splitlines()
    require(len(changes)==19 and all(v.startswith('A\t') for v in changes),'pilot_origin_shape')
    names=[v.split('\t',1)[1] for v in changes]
    return {p:sha(git(root,'show',PILOT+':'+p)) for p in names}
def check(root=ROOT):
    root=Path(root);raw=(root/POLICY).read_bytes()
    require(sha(raw)==POLICY_SHA256,'transition_manifest_identity')
    policy=strict(raw)
    require(policy['schema']=='veca-second-backend-integration-v1' and policy['base']==BASE and policy['pilot']==PILOT,'transition_identity')
    require(policy['core_changes_permitted'] is False,'Core_transition_forbidden')
    original=git(root,'show',BASE+':artifacts.sha256.json')
    require(sha(original)==policy['base_inventory_sha256'],'baseline_manifest_identity')
    baseline=strict(original);expected=dict(baseline['files'])
    imported=pilot_files(root)
    require(imported==policy['pilot_files'] and not set(imported)&set(expected),'pilot_origin_identity')
    require((root/ARCHIVE).read_bytes()==git(root,'show',BASE+':README.md'),'README_archive_identity')
    require(policy['before_readme_sha256']==expected['README.md'],'original_README_identity')
    expected['README.md']=policy['after_readme_sha256']
    workflows=sorted(p for p in expected if p.startswith('.github/workflows/') and p not in UNTOUCHED)
    require(workflows==policy['workflows'] and len(workflows)==12,'workflow_scope')
    for path in workflows:expected[path]=sha(workflow(path,git(root,'show',BASE+':'+path)))
    expected.update(imported)
    require(list(NEW_PATHS)==policy['new_files'] and not set(NEW_PATHS)&set(expected),'new_file_scope')
    current=strict((root/'artifacts.sha256.json').read_bytes())
    require({k:v for k,v in current.items() if k!='files'}=={k:v for k,v in baseline.items() if k!='files'},'inventory_metadata')
    immutable=set(NEW_PATHS)-REPORTS-{POLICY,'tools/second_backend_integration/preservation.py'}
    require(set(policy['immutable_new_files'])==immutable,'immutable_new_scope')
    expected.update(policy['immutable_new_files'])
    verifier=(root/'tools/second_backend_integration/preservation.py').read_bytes()
    require(sha(normalized_verifier(verifier))==policy['verifier_body_sha256'],'verifier_body_identity')
    expected['tools/second_backend_integration/preservation.py']=sha(verifier)
    expected[POLICY]=POLICY_SHA256
    for path in REPORTS:
        require(path in current['files'],'missing_report_entry')
        expected[path]=current['files'][path]
    require(current['files']==expected,'inventory_transition')
    actual=inventory(root)
    require(set(actual)==set(expected),'file_membership')
    bad=sorted(p for p,d in expected.items() if actual[p]!=d)
    require(not bad,'unexpected_bytes:'+','.join(bad[:8]))
    return {'schema':'veca-second-backend-integration-check-v1','passed':True,'base':BASE,'pilot':PILOT,'transition_sha256':POLICY_SHA256,'files':len(expected),'baseline_files_unchanged':len(baseline['files'])-13,'baseline_changed':['README.md',*workflows,'artifacts.sha256.json'],'pilot_files_preserved':len(imported),'core_changes_permitted':False,'independent_review':'NOT_ESTABLISHED'}
def check_view(view,root=ROOT):
    view=Path(view);require(view.is_dir() and not view.is_symlink() and not view.is_junction(),'view_missing_or_linked')
    require(git(view,'rev-parse','HEAD').decode().strip()==BASE,'view_head_identity')
    raw=git(root,'show',BASE+':artifacts.sha256.json');expected=strict(raw)['files']
    require((view/'artifacts.sha256.json').read_bytes()==raw,'view_manifest_identity')
    require(inventory(view)==expected,'view_tree_identity')
    old.check(view)
    if (view/old.VIEW).exists():old.check_view(view/old.VIEW,view)
    return {'head':BASE,'passed':True,'files':len(expected),'old_guard_executed':True}
