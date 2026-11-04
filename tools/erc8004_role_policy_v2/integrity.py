"""Additive v2 preservation, including the exact existing PR11 reconciliation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from baseline_reconciliation import policy as baseline
from erc8004.integrity import check as legacy_check
from erc8004_role_policy.integrity import check as v1_check


def check():
    lock=json.loads((ROOT/'conformance/erc8004-role-policy-v2/source-lock.json').read_bytes())
    raw=subprocess.check_output(['git','show',lock['historical_base']+':artifacts.sha256.json'],cwd=ROOT)
    sha=lambda value:hashlib.sha256(value).hexdigest()
    if sha(raw)!=lock['historical_inventory_sha256']: raise ValueError('reviewed baseline inventory drift')
    historical=json.loads(raw)['files']
    expected=dict(historical)
    preservation=baseline.check(ROOT,baseline.PILOT)
    if preservation['document_state']=='PR11_DOCUMENTS' and preservation['passed']:
        reviewed=baseline.manifest(ROOT,baseline.REVIEW)
        expected.update({p:reviewed[p] for p in baseline.DOCUMENTS})
    current=json.loads((ROOT/'artifacts.sha256.json').read_bytes())['files']
    bad=list(preservation['mismatches'])
    for name,digest in expected.items():
        path=ROOT/name
        if not path.is_file() or sha(path.read_bytes())!=digest: bad.append('historical:'+name)
        if current.get(name)!=digest: bad.append('inventory:'+name)
    for name,digest in lock['reused_files'].items():
        if sha((ROOT/name).read_bytes())!=digest: bad.append('reuse:'+name)
    if sha((ROOT/'tools/erc8004_role_policy_v2/scenarios.mjs').read_bytes())!=lock['scenarios_sha256']:
        bad.append('v2_scenario_pin')
    legacy=legacy_check();v1=v1_check()
    bad.extend('v0:'+p for p in legacy['mismatches']);bad.extend('v1:'+p for p in v1['mismatches'])
    return {'schema':'erc8004-role-policy.preservation.v2','passed':not bad,'historical_base':lock['historical_base'],
            'historical_files':len(historical),'historical_inventory_sha256':sha(raw),
            'unchanged_historical_files':sum((ROOT/p).is_file() and sha((ROOT/p).read_bytes())==v for p,v in historical.items()),
            'baseline_reconciliation':preservation,'v0':legacy,'v1':v1,'mismatches':sorted(set(bad))}


if __name__=='__main__':
    result=check();print(json.dumps(result,sort_keys=True));raise SystemExit(not result['passed'])
