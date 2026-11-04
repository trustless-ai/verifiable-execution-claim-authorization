"""Five physical wallet-policy mutants, each replayed on the pinned EVM."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import agent_harness as h

PROFILE = ROOT / 'conformance/erc8004-role-policy-v2'
SOURCE = ROOT / 'tools/erc8004_role_policy_v2/policy.py'
STATES = ('KILLED','SURVIVED','CRASHED','NO_OP','NOT_APPLIED','MISSING_OUTPUT',
          'CONTROL_BROKEN','RESTORATION_FAILED','UNVERIFIABLE')
DEFINITIONS = (
    ('wallet','agent_wallet_self','V2-ROLES',
     "    if roles['validator'].lower() == wallet.lower():  # guard: wallet",
     '    if False:  # removed wallet comparison'),
    ('request_time','wallet_changes_after','V2-TIME',
     "    wallet = roles.get('agent_wallet', ZERO)  # guard: request_time",
     "    wallet = observed['response_roles']['agent_wallet']  # substituted response wallet"),
    ('wallet_binding','wrong_wallet_block','V2-BINDING',
     "    keys = ('owner', 'operator', 'approved', 'agent_wallet')  # guard: wallet_binding",
     "    keys = ('owner', 'operator', 'approved')  # wallet call not bound"),
    ('missing_wallet','missing_wallet','V2-AVAILABILITY',
     "        return 'UNVERIFIABLE', 'MISSING_AGENT_WALLET'  # guard: missing_wallet",
     '        return None  # missing wallet accepted'),
    ('contradictory_wallet','contradictory_wallet','V2-BINDING',
     "            return 'REFUTED', 'CONTRADICTORY_ROLE_CALL'  # guard: contradictory_wallet",
     '            return None  # contradictory call accepted'))


def classify(baseline, mutated, restored, witness, original, changed, restored_bytes, applied=True):
    if not applied: return 'NOT_APPLIED'
    if original == changed: return 'NO_OP'
    if original != restored_bytes: return 'RESTORATION_FAILED'
    if baseline.get('backend_conformance') != 'PASS' or restored.get('backend_conformance') != 'PASS':
        return 'CONTROL_BROKEN'
    if mutated.get('adapter_exit_code') is None: return 'MISSING_OUTPUT'
    if mutated['adapter_exit_code'] != 0: return 'CRASHED'
    rows = {r['id']:r for r in mutated.get('rows',[])}
    if witness not in rows or 'separate_validator' not in rows: return 'MISSING_OUTPUT'
    if rows['separate_validator']['backend_conformance'] != 'PASS': return 'CONTROL_BROKEN'
    row = rows[witness]
    actual, expected = row.get('observed_behavior'), row.get('expected_behavior')
    if not isinstance(actual,dict) or not isinstance(expected,dict): return 'MISSING_OUTPUT'
    if mutated.get('exit_code') == 2: return 'UNVERIFIABLE'
    if row['backend_conformance'] == 'PASS': return 'SURVIVED'
    # A semantic kill is a complete, wrong authorization, not any generic failure.
    try:
        if (not isinstance(actual.get('behavior'),dict) or not isinstance(actual.get('authorization'),dict)
                or set(expected['behavior']) - set(actual['behavior'])
                or {'status','authorized','scope'} - set(actual['authorization'])):
            return 'MISSING_OUTPUT'
        complete = set(actual) == {'behavior','authorization'} and set(actual['behavior']) == set(expected['behavior'])
        honest_execution = {k:v for k,v in actual['behavior'].items() if k != 'policy_reason'} == {
            k:v for k,v in expected['behavior'].items() if k != 'policy_reason'}
        admitted = actual['authorization']['status'] == 'VERIFIED' and actual['authorization']['authorized'] is True and isinstance(actual['authorization']['scope'],dict)
        incorrect = expected['authorization']['status'] != 'VERIFIED' and actual['behavior']['policy_reason'] == 'REQUEST_TIME_ROLE_SEPARATION'
    except (KeyError,TypeError): return 'MISSING_OUTPUT'
    return 'KILLED' if row['backend_conformance'] == 'FAIL' and complete and honest_execution and admitted and incorrect else 'SURVIVED'


def run(out):
    original = SOURCE.read_bytes()
    corpus = json.loads((PROFILE / 'vectors.json').read_bytes())
    rows = {v['name']:v for v in corpus['vectors']}
    records = []
    for name,witness,obligation,before,after in DEFINITIONS:
        folder = out / name; folder.mkdir(parents=True,exist_ok=True)
        record = {'id':name,'witness':witness,'positive':'separate_validator','obligation':obligation,
                  'source':SOURCE.relative_to(ROOT).as_posix(),'original_sha256':h.sha(original),
                  'before':before,'after':after}
        if original.decode().count(before) != 1:
            records.append({**record,'classification':'NOT_APPLIED'}); continue
        h.write(folder/'vectors.json',{'profile':corpus['profile'],'vectors':[rows[witness],rows['separate_validator']]})
        shutil.copyfile(PROFILE/'obligations.json',folder/'obligations.json')
        h.write(folder/'suite.json',{'id':name,**{k:{'path':k+'.json','sha256':h.sha((folder/(k+'.json')).read_bytes())} for k in ('vectors','obligations')}})
        target = folder/'policy.py'; target.write_bytes(original)
        h.write(folder/'adapter.json',{'argv':['{python}','-B',str(ROOT/'tools/erc8004_role_policy_v2/adapter.py'),'--policy-file',str(target)]})
        baseline = h.execute(folder/'suite.json',folder/'adapter.json',folder/'baseline')
        changed = original.decode().replace(before,after,1).encode()
        target.write_bytes(changed); (folder/'mutated-policy.py.txt').write_bytes(changed)
        try: mutated = h.execute(folder/'suite.json',folder/'adapter.json',folder/'mutated')
        finally: target.write_bytes(original)
        restored = h.execute(folder/'suite.json',folder/'adapter.json',folder/'restored')
        record.update(mutant_sha256=h.sha(changed),classification=classify(baseline,mutated,restored,witness,original,changed,target.read_bytes()),byte_restored=target.read_bytes()==original)
        def equal_file(name):
            paths = [folder/phase/name for phase in ('baseline','restored')]
            return all(p.is_file() for p in paths) and paths[0].read_bytes()==paths[1].read_bytes()
        record['semantic_restored'] = equal_file('projected.json')
        record['raw_execution_restored'] = equal_file('adapter.stdout')
        record['same_request'] = len({(folder/phase/'request.json').read_bytes() for phase in ('baseline','mutated','restored')})==1
        if not all(record[k] for k in ('semantic_restored','raw_execution_restored','same_request')):
            record['classification']='UNVERIFIABLE'
        records.append(record)
        h.write(out/'report.json',{'schema':'erc8004-role-policy.mutations.v2','results':records,
            'counts':{s:sum(r['classification']==s for r in records) for s in STATES}})
        print(name,record['classification'],flush=True)
    report={'schema':'erc8004-role-policy.mutations.v2','results':records,'counts':{s:sum(r['classification']==s for r in records) for s in STATES}}
    h.write(out/'report.json',report)
    if SOURCE.read_bytes()!=original or report['counts']['KILLED']!=len(DEFINITIONS):
        raise RuntimeError('physical mutation campaign did not close')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out.resolve())
