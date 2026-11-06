"""Small, independently runnable selections of the original authored corpus."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import agent_harness as h

FINDINGS={
    'A':['configuration_profile_collision'],
    'B':['zk_mock_positive','caller_impersonates_agent','unknown_native_agent'],
    'C':['zk_mock_positive','repeat_same_task','reuse_proof_fresh_task','reuse_proof_other_contract','reuse_proof_other_chain'],
}


def evaluate(finding, observations):
    def native(name):return observations[name]['evidence']
    checks={}
    if finding=='A':
        n=native('configuration_profile_collision')
        checks={'different_committees':n['committees'][0]!=n['committees'][1],
                'equal_profile':n['profile']==n['other_profile'],
                'positive_threshold_discriminator':n['summary']['same_threshold_profile'] is False}
    elif finding=='B':
        base=native('zk_mock_positive'); attack=native('caller_impersonates_agent')
        checks={'same_agent_id':base['agent_id']==attack['agent_id'],
                'different_caller':base['caller']!=attack['caller'],
                'same_contract':base['contract']==attack['contract'],
                'same_proof':base['proof_sha256']==attack['proof_sha256'],
                'both_native_accepted':base['summary']['outer'] is True and attack['summary']['outer'] is True,
                'unknown_agent_refused':native('unknown_native_agent')['summary']['outer'] is False,
                'consumer_refused_caller':observations['caller_impersonates_agent']['behavior']['reason']=='CALLER_NOT_AGENT'}
    elif finding=='C':
        ns={name:native(name) for name in FINDINGS['C']}; base=ns['zk_mock_positive']
        checks={'same_proof_bytes':len({n['proof_sha256'] for n in ns.values()})==1,
                'same_task_refused':ns['repeat_same_task']['summary']['calls']==[True,False],
                'fresh_task_accepted':ns['reuse_proof_fresh_task']['summary']['calls']==[True,True],
                'different_task':ns['reuse_proof_fresh_task']['task_id']!=base['task_id'],
                'other_instance_accepted':ns['reuse_proof_other_contract']['summary']['outer'] is True,
                'different_instance':ns['reuse_proof_other_contract']['contract']!=base['contract'],
                'other_chain_accepted':ns['reuse_proof_other_chain']['summary']['outer'] is True,
                'different_chain':ns['reuse_proof_other_chain']['chain_id']!=base['chain_id'],
                'same_address_across_chains':ns['reuse_proof_other_chain']['contract']==base['contract'],
                'mock_explicit':all(n['provenance']=='UPSTREAM_MOCK_SP1' for n in ns.values())}
    else:raise ValueError('unknown finding')
    return {'finding':finding,'passed':bool(checks) and all(checks.values()),'checks':checks}


def main():
    p=argparse.ArgumentParser();p.add_argument('--finding',choices=['A','B','C','all'],default='all');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    original=json.loads((PROJECT/'vectors.json').read_bytes());suite=json.loads((PROJECT/'suite.json').read_bytes())
    outcomes=[]
    for finding in FINDINGS if a.finding=='all' else [a.finding]:
        d=a.out/finding;d.mkdir(parents=True,exist_ok=True)
        corpus={'profile':original['profile'],'vectors':[r for r in original['vectors'] if r['name'] in FINDINGS[finding]]}
        h.write(d/'vectors.json',corpus)
        (d/'obligations.json').write_bytes((PROJECT/'obligations.json').read_bytes())
        subset=copy.deepcopy(suite);subset['vectors']['sha256']=h.sha((d/'vectors.json').read_bytes());h.write(d/'suite.json',subset)
        report=h.execute(d/'suite.json',PROJECT/'adapter.json',d/'run')
        if report['exit_code']!=0:raise RuntimeError('counterexample execution/grading failed: '+finding)
        observations=json.loads((d/'run/adapter.stdout').read_bytes())['observations']
        outcome=evaluate(finding,observations)
        # A semantic result-tamper control must break the specific finding, not crash.
        altered=copy.deepcopy(observations)
        if finding=='A':altered['configuration_profile_collision']['evidence']['other_profile']='0x'+'00'*32
        if finding=='B':altered['caller_impersonates_agent']['evidence']['caller']=altered['zk_mock_positive']['evidence']['caller']
        if finding=='C':altered['reuse_proof_other_chain']['evidence']['proof_sha256']='0x'+'00'*32
        negative=evaluate(finding,altered)
        outcome.update(negative_control=negative,negative_control_passed=not negative['passed'],
                       source_commit=json.loads((PROJECT/'SOURCE_PINS.json').read_bytes())['flashprove']['commit'],
                       request_sha256=h.sha((d/'run/request.json').read_bytes()),
                       native_stdout_sha256=h.sha((d/'run/adapter.stdout').read_bytes()),
                       native_exit=report['adapter_exit_code'],grader_exit=report['exit_code'])
        h.write(d/'result.json',outcome);outcomes.append(outcome)
    result={'passed':all(x['passed'] and x['negative_control_passed'] for x in outcomes),'findings':outcomes}
    h.write(a.out/'results.json',result);print(json.dumps(result,sort_keys=True));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
