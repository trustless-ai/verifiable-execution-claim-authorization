"""Physical guard removals in disposable copies, graded by the existing harness.

Consumer mutants replay the complete, hash-recorded baseline native EVM evidence.
Solidity mutants rerun the actual EVM. A wrong-reason crash is never a kill.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from prepare import CACHE, ROOT, verify

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import agent_harness as h


def catalog():
    entries=[]
    def add(id,file,old,new,target,control='zk_mock_positive'):
        entries.append(dict(id=id,file=file,old=old,new=new,target=target,control=control))
    policy=(HERE/'policy.py').read_text(encoding='utf-8')
    clauses=[
        ('policy',"if fixture not in POLICIES:",'missing_policy'),
        ('route',"elif claim['route'] != native['route']:",'wrong_route_claim'),
        ('chain',"elif native['chain_id'] != 31337 or claim['chain_id'] != 31337:",'reuse_proof_other_chain'),
        ('contract',"elif native['instance'] != 'selected' or claim['instance'] != 'selected':",'reuse_proof_other_contract'),
        ('agent',"elif claim['agent_id'] != AGENT or native['agent_id'] != AGENT:",'unknown_native_agent'),
        ('caller',"elif not native['caller_bound']:",'caller_impersonates_agent'),
        ('task',"elif claim['task_id'] != TASK or native['task_id'] != TASK:",'reuse_proof_fresh_task'),
        ('input',"elif claim['input_hash'] != INPUT or native['input_hash'] != INPUT:",'wrong_input_claim'),
        ('output',"elif claim['output_hash'] != OUTPUT or native['output_hash'] != OUTPUT:",'wrong_output_claim'),
        ('committee',"elif native['route'] == 'attestation' and not native['committee_bound']:",'attestation_wrong_committee'),
        ('operators',"elif native['route'] == 'attestation' and len(set(POLICIES[fixture]['operators'])) < native['threshold']:",'attestation_two_keys_one_operator'),
        ('revocation',"elif native['route'] == 'attestation' and POLICIES[fixture]['revoked']:",'attestation_revoked_assumption'),
        ('signer-admission',"elif native['route'] == 'attestation' and len(POLICIES[fixture]['admitted']) < native['threshold']:",'attestation_untrusted_signer_assumption'),
    ]
    for id,old,target in clauses:
        add('consumer-'+id,'policy.py',old,('if' if old.startswith('if ') else 'elif')+' False:',target)
    add('mock-as-zk','policy.py',"axes['ZK_PROOF_VERIFIED'] = 'UNVERIFIABLE'", "axes['ZK_PROOF_VERIFIED'] = 'VERIFIED' if native['route'] == 'zk' and native['summary']['inner'] else 'UNVERIFIABLE'",'zk_mock_positive','attestation_no_signatures')
    add('signatures-as-attestation','policy.py',"axes['ATTESTATION_ACCEPTED'] = 'UNVERIFIABLE'", "axes['ATTESTATION_ACCEPTED'] = 'VERIFIED' if native['route'] == 'attestation' and native['summary']['distinct_signers'] == 2 else 'UNVERIFIABLE'",'attestation_illustrative_two_signatures')
    add('attestation-as-zk','policy.py',"axes['ZK_PROOF_VERIFIED'] = 'UNVERIFIABLE'", "axes['ZK_PROOF_VERIFIED'] = 'VERIFIED' if native['route'] == 'attestation' and native['summary']['distinct_signers'] == 2 else 'UNVERIFIABLE'",'attestation_is_not_zk')
    add('proof-as-claim','policy.py',"axes['CLAIM_AUTHORIZED'] = status", "axes['CLAIM_AUTHORIZED'] = 'VERIFIED' if native['summary']['outer'] else status",'zk_mock_positive','attestation_no_signatures')
    for axis in ['ACTION_AUTHORIZED','ORDER_EXECUTED']:
        add('proof-as-'+axis.lower(),'policy.py',f"axes['{axis}'] = 'UNVERIFIABLE'",f"axes['{axis}'] = 'VERIFIED' if native['summary']['outer'] else 'UNVERIFIABLE'",'zk_mock_positive','attestation_no_signatures')
    zk='contracts/src/zk/FlashProveZKVerifier.sol'
    outer='contracts/src/examples/ExampleAgentVerifier.sol'
    att='contracts/src/attestation/FlashProveAttestVerifier.sol'
    add('native-input',zk,'values.inputDigest == inputHash && values.resultV1Digest == outputHash','values.resultV1Digest == outputHash','wrong_input_call')
    add('native-output',zk,'values.inputDigest == inputHash && values.resultV1Digest == outputHash','values.inputDigest == inputHash','wrong_output_call')
    add('native-commitment',outer,'if (values.commitmentId != commitmentId) return false;','if (false) return false;','wrong_commitment')
    add('native-verdict',outer,'if ((acceptedVerdicts & (uint16(1) << values.verdict)) == 0) return false;','if (false) return false;','unaccepted_verdict')
    add('native-call-status',outer,'if (requireStatusZero && values.callStatus != 0) return false;','if (false) return false;','failed_call_status')
    add('native-single-use',outer,'!usedTasks[taskId] && authorizedAgents[agentId]','authorizedAgents[agentId]','repeat_same_task')
    add('native-agent-allowlist',outer,'!usedTasks[taskId] && authorizedAgents[agentId]','!usedTasks[taskId]','unknown_native_agent')
    add('native-duplicate-committee',att,'signer == address(0) || _isSigner[signer]','signer == address(0)','committee_duplicate')
    add('native-zero-signer',att,'signer == address(0) || _isSigner[signer]','_isSigner[signer]','committee_zero-signer')
    add('native-signature-todo-bypass',att,'return 0;','return 999;','attestation_illustrative_two_signatures')
    return entries


def classify(report, target, control, applied, same=False):
    if applied!=1: return 'NOT_APPLIED'
    if same: return 'NO_OP'
    if report.get('adapter_exit_code',0)!=0: return 'CRASHED'
    if report['exit_code']==2: return 'MISSING_OUTPUT'
    rows={r['id']:r for r in report['rows']}
    if rows.get(control,{}).get('backend_conformance')!='PASS': return 'CONTROL_BROKEN'
    if report['exit_code']==1 and rows.get(target,{}).get('backend_conformance')=='FAIL': return 'KILLED'
    return 'SURVIVED'


def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    a.out=a.out.resolve(); a.out.mkdir(parents=True,exist_ok=True)
    verify()
    originals={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['policy.py','adapter.py','evm.mjs','vectors.json']}
    baseline=h.execute(HERE/'suite.json',HERE/'adapter.json',a.out/'baseline')
    if baseline['exit_code']!=0:
        h.write(a.out/'results.json',{'status':'CONTROL_BROKEN','baseline':baseline}); return 2
    baseline_data=json.loads((a.out/'baseline/adapter.stdout').read_bytes())
    native={k:v['evidence'] for k,v in baseline_data['observations'].items()}
    h.write(a.out/'native.json',native)
    entries=catalog(); h.write(a.out/'catalog.json',entries)
    results=[]
    for entry in entries:
        with tempfile.TemporaryDirectory(prefix='flashprove-mutant-') as td:
            d=Path(td).resolve(); file=entry['file']; old=entry['old']; new=entry['new']
            source=(HERE/file if file=='policy.py' else CACHE/file).read_bytes()
            count=source.count(old.encode()); modified=source.replace(old.encode(),new.encode(),1)
            dest=d/file; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(modified)
            if count!=1:
                results.append({**entry,'classification':'NOT_APPLIED','applied_count':count}); continue
            if file=='policy.py':
                runner=d/'runner.py'
                runner.write_text("import json,sys\nfrom pathlib import Path\nfrom policy import consume\nr=json.load(sys.stdin)\nn=json.loads(Path(sys.argv[1]).read_bytes())\nprint(json.dumps({'schema':'agent-harness.observation.v0','observations':{v['id']:consume(v['input'],n[v['id']]) for v in r['cases']}},sort_keys=True))\n",encoding='utf-8',newline='\n')
                argv=['{python}','-B',str(runner),str(a.out/'native.json')]
            else:
                # Copy pinned bytes first, then apply exactly one predicate change.
                shutil.copytree(CACHE,d/'source')
                dest=d/'source'/file; dest.write_bytes(modified)
                argv=['{python}','-B',str(HERE/'adapter.py'),'--mutation-source',str(d/'source')]
            # agent_harness.execute propagates -O; do not add a second flag here.
            h.write(d/'adapter.json',{'argv':argv})
            report=h.execute(HERE/'suite.json',d/'adapter.json',a.out/entry['id'])
            failed=[r['id'] for r in report['rows'] if r['backend_conformance']=='FAIL']
            outcome=classify(report,entry['target'],entry['control'],count,modified==source)
            results.append({**entry,'applied_count':count,'original_sha256':h.sha(source),'mutant_sha256':h.sha(modified),
                            'classification':outcome,'exit_code':report['exit_code'],'adapter_exit_code':report.get('adapter_exit_code'),
                            'baseline':'PASS','failures':failed,'healthy_control':entry['control'] not in failed,
                            'replay':'captured complete native EVM evidence' if file=='policy.py' else 'fresh EVM execution'})
            print(entry['id'],outcome,flush=True)
    # Real executions for classifier sentinels; none belongs in the semantic kill count.
    sentinels=[]
    for name,argv,applied,same in [
        ('CRASHED',['{python}','-c','raise RuntimeError("sentinel")'],1,False),
        ('MISSING_OUTPUT',['{python}','-c','pass'],1,False),
        ('NOT_APPLIED',None,0,False),('NO_OP',None,1,True),('SURVIVED',None,1,False),
        ('CONTROL_BROKEN',None,1,False)]:
        with tempfile.TemporaryDirectory(prefix='flashprove-sentinel-') as td:
            d=Path(td).resolve()
            data=json.loads(json.dumps(baseline_data))
            if name=='CONTROL_BROKEN': data['observations']['zk_mock_positive']['behavior']['reason']='BROKEN_CONTROL'
            h.write(d/'observations.json',data)
            h.write(d/'adapter.json',{'argv':argv or ['{python}','-B','{repo}/tools/harness_v0/replay.py',str(d/'observations.json')]})
            report=h.execute(HERE/'suite.json',d/'adapter.json',a.out/('sentinel-'+name))
            observed=classify(report,'wrong_input_call','zk_mock_positive',applied,same)
            sentinels.append({'expected':name,'observed':observed,'exit_code':report['exit_code'],'passed':name==observed})
    verify()
    restored=all(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==v for n,v in originals.items())
    counts=dict(Counter(r['classification'] for r in results))
    passed=restored and counts=={'KILLED':len(entries)} and all(s['passed'] for s in sentinels)
    h.write(a.out/'results.json',{'passed':passed,'results':results,'counts':counts,'sentinels':sentinels,
        'restored':restored,'native_sha256':h.sha((a.out/'native.json').read_bytes()),'historical_mutants_unchanged':True})
    print(json.dumps({'passed':passed,'counts':counts,'restored':restored})); return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
