"""Prove the base is unchanged. Does not reseal or bypass historical inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from prepare import ROOT, HERE, verify


def sha(data): return hashlib.sha256(data).hexdigest()
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT)


def inspect():
    pins=json.loads((HERE/'SOURCE_PINS.json').read_bytes())
    base=pins['base']
    old_manifest=git('show',base+':artifacts.sha256.json')
    saved=json.loads(old_manifest)['files']
    mismatches=[name for name,digest in saved.items() if not (ROOT/name).is_file() or sha((ROOT/name).read_bytes())!=digest]
    core=json.loads((ROOT/'fixtures/erc8404/core-lock.json').read_bytes())
    core_bad=[name for name,digest in core.items() if sha((ROOT/'evidence/erc8404/core'/name).read_bytes())!=digest]
    base_paths=git('ls-tree','-r','--name-only',base).decode().splitlines()
    # git diff catches tracked changes, but old manifest proves actual byte identity.
    changed=git('diff','--name-only',base,'--','.').decode().splitlines()
    unexpected=[name for name in changed if not name.startswith('research/flashprove-8274-claim-boundary-v0/')]
    inventory_proc=subprocess.run(['python','-B','tools/verify_artifacts.py'],cwd=ROOT,capture_output=True)
    inventory=json.loads(inventory_proc.stdout)
    known_additions=all(n.startswith('research/flashprove-8274-claim-boundary-v0/') and n not in saved for n in inventory['mismatches'])
    manifest_unchanged=(ROOT/'artifacts.sha256.json').read_bytes()==old_manifest
    report={'base':base,'core_files':len(core),'core_mismatches':core_bad,
            'historical_files':len(saved),'historical_mismatches':mismatches,
            'existing_manifest_sha256':sha(old_manifest),'existing_manifest_unchanged':manifest_unchanged,
            'unexpected_diff':unexpected,'unchanged_root_inventory_exit':inventory_proc.returncode,
            'unchanged_root_inventory_result':inventory,'only_new_unregistered_additions':known_additions,
            'registration_status':'NOT_INTEGRATED; existing manifest intentionally unchanged',
            'source_pins':verify()}
    report['preservation_passed']=not mismatches and not core_bad and not unexpected and manifest_unchanged and known_additions
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path); a=p.parse_args()
    result=inspect(); data=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_bytes(data.encode())
    print(data,end=''); raise SystemExit(0 if result['preservation_passed'] else 1)
