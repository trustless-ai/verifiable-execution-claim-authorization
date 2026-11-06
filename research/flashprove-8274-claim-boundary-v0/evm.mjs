// Isolated EDR execution of exact pinned upstream sources. No network RPC.
// MockSP1Verifier is upstream's explicit test double, not a cryptographic proof.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const [root, source] = process.argv.slice(2);
const runtime = path.join(root, 'build/erc8004/runtime');
const req = createRequire(path.join(runtime, 'package.json'));
const { ethers } = req('ethers');
const solc = req('solc');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const sources = {};
function scan(dir) {
  for (const e of fs.readdirSync(dir, {withFileTypes:true})) {
    const p = path.join(dir,e.name);
    if (e.isDirectory()) scan(p);
    else if (e.name.endsWith('.sol')) sources[path.relative(path.join(source,'contracts'),p).replaceAll('\\','/')] = {content:fs.readFileSync(p,'utf8')};
  }
}
scan(path.join(source,'contracts/src'));
const compiled = JSON.parse(solc.compile(JSON.stringify({language:'Solidity',sources,settings:{optimizer:{enabled:true,runs:200},viaIR:true,evmVersion:'shanghai',outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}})));
if ((compiled.errors || []).some(e=>e.severity==='error')) throw Error(JSON.stringify(compiled.errors));
const artifact = name => Object.values(compiled.contracts).map(x=>x[name]).find(Boolean);
process.chdir(runtime);
const {network} = await import(pathToFileURL(req.resolve('hardhat')).href);
const abi = ethers.AbiCoder.defaultAbiCoder();
const H = n => '0x'+n.repeat(32);
const A=H('11'), I=H('22'), O=H('33'), CID=H('44'), VK=H('55'), T=H('66'), X=H('77');
const contexts = new Map();
async function context(chainId) {
  if (contexts.has(chainId)) return contexts.get(chainId);
  const conn=await network.connect({network:'laboratory',override:{chainId}});
  const raw=conn.provider;
  const rpc={request:async ({method,params=[]})=>{
    if (method==='eth_sendTransaction' || method==='eth_sendRawTransaction') {
      const b=await raw.request({method:'eth_getBlockByNumber',params:['latest',false]});
      await raw.request({method:'evm_setNextBlockTimestamp',params:[Number(BigInt(b.timestamp))+1]});
    }
    return raw.request({method,params});
  }};
  const provider=new ethers.BrowserProvider(rpc,undefined,{cacheTimeout:-1}); provider.pollingInterval=10;
  const signers=await Promise.all([0,1,2,3].map(n=>provider.getSigner(n)));
  const addresses=await Promise.all(signers.map(s=>s.getAddress()));
  const construct=async (name,args)=>{
    const a=artifact(name); const c=await new ethers.ContractFactory(a.abi,a.evm.bytecode.object,signers[0]).deploy(...args);
    await c.waitForDeployment(); return c;
  };
  const mock=await construct('MockSP1Verifier',[true]);
  await (await mock.setExpectedProgramVKey(VK)).wait();
  const zk=await construct('FlashProveZKVerifier',[await mock.getAddress()]);
  const att=await construct('FlashProveAttestVerifier',[[addresses[0],addresses[1]],2]);
  const otherAtt=await construct('FlashProveAttestVerifier',[[addresses[2],addresses[3]],2]);
  const thresholdAtt=await construct('FlashProveAttestVerifier',[[addresses[0],addresses[1]],1]);
  const agentArgs=[await zk.getAddress(),VK,CID,2,true,[A]];
  const agent=await construct('ExampleAgentVerifier',agentArgs);
  const otherAgent=await construct('ExampleAgentVerifier',agentArgs);
  const policyAgent=await construct('ExampleAgentVerifier',[await zk.getAddress(),VK,X,4,false,[X]]);
  const attAgent=await construct('ExampleAgentVerifier',[await att.getAddress(),VK,CID,2,true,[A]]);
  const x={conn,rpc,provider,signers,addresses,construct,mock,zk,att,otherAtt,thresholdAtt,agent,otherAgent,policyAgent,attAgent};
  x.snapshot=await rpc.request({method:'evm_snapshot'}); contexts.set(chainId,x); return x;
}
function pv(op) {
  let b=Buffer.alloc(128); b.write('FPV1'); b.writeUInt16BE(1,4); b[8]=op.verdict || 1;
  b.writeUInt16BE(op.status || 0,10);
  Buffer.from((op.cid || CID).slice(2),'hex').copy(b,16);
  Buffer.from(I.slice(2),'hex').copy(b,48); Buffer.from(O.slice(2),'hex').copy(b,80);
  if (op.pv==='magic') b[0]=0;
  if (op.pv==='version') b.writeUInt16BE(2,4);
  if (op.pv==='reserved') b[127]=1;
  if (op.pv==='short') b=b.subarray(0,127);
  return '0x'+b.toString('hex');
}
const result={};
for (const row of request.cases) {
  const op=row.input.operation, route=op.route || 'zk', chain=op.chain || 31337;
  const c=await context(chain);
  await c.rpc.request({method:'evm_revert',params:[c.snapshot]}); c.snapshot=await c.rpc.request({method:'evm_snapshot'});
  const summary={inner:null,outer:null,calls:[],constructor_accepted:null,same_committee_profile:null,same_threshold_profile:null,chain_digest_equal:null,contract_digest_equal:null,outer_profile_equal:null,distinct_signers:null};
  const input=op.input || I, output=op.output || O, agentId=op.agent || A, task=op.task || T;
  const selectedTarget=route==='attestation'?c.attAgent:c.agent;
  const actualTarget=route==='attestation'?c.attAgent:op.instance==='other'?c.otherAgent:c.agent;
  const actualCommittee=await (op.committee==='other'?c.otherAtt:c.att).signers();
  const selectedCommittee=[c.addresses[0],c.addresses[1]];
  const n={route,chain_id:Number(BigInt(await c.rpc.request({method:'eth_chainId'}))),
    instance:(await actualTarget.getAddress())===(await selectedTarget.getAddress())?'selected':'other',
    agent_id:agentId,task_id:task,input_hash:input,output_hash:output,
    caller_bound:c.addresses[op.actor || 0]===c.addresses[0],
    committee_bound:JSON.stringify(actualCommittee)===JSON.stringify(selectedCommittee),
    committee:actualCommittee,selected_committee:selectedCommittee,threshold:Number(await c.att.threshold()),
    provenance:route==='zk'?'UPSTREAM_MOCK_SP1':'UPSTREAM_SIGNATURE_TODO',summary};
  if (op.kind==='constructor') {
    let keys=[c.addresses[0],c.addresses[1]], threshold=2;
    if(op.config==='empty') keys=[];
    if(op.config==='zero-threshold') threshold=0;
    if(op.config==='high-threshold') threshold=3;
    if(op.config==='duplicate') keys=[c.addresses[0],c.addresses[0]];
    if(op.config==='zero-signer') keys=[c.addresses[0],ethers.ZeroAddress];
    try {await c.construct('FlashProveAttestVerifier',[keys,threshold]);summary.constructor_accepted=true;}
    catch(e) {if (!['CALL_EXCEPTION'].includes(e.code)) throw e; summary.constructor_accepted=false; n.constructor_refusal=e.shortMessage;}
  } else if(op.kind==='profiles') {
    summary.same_committee_profile=(await c.att.proofProfile())===(await c.otherAtt.proofProfile());
    summary.same_threshold_profile=(await c.att.proofProfile())===(await c.thresholdAtt.proofProfile());
    summary.outer_profile_equal=(await c.agent.agentProofProfile())===(await c.policyAgent.agentProofProfile());
    n.committees=[await c.att.signers(),await c.otherAtt.signers()];
    n.profile=await c.att.proofProfile(); n.other_profile=await c.otherAtt.proofProfile();
  } else if(op.kind==='domains') {
    const d=await context(31338), mh=ethers.keccak256(VK);
    const digest=await c.att.attestationDigest(I,O,mh);
    summary.chain_digest_equal=digest===(await d.att.attestationDigest(I,O,mh));
    summary.contract_digest_equal=digest===(await c.otherAtt.attestationDigest(I,O,mh));
    n.domain_addresses=[await c.att.getAddress(),await d.att.getAddress()]; n.digest=digest;
  } else {
    let metadata=op.metadata==='short'?'0x01':op.metadata==='wrong'?X:VK;
    let proofBytes=op.proof==='bad'?'0x00000000':'0x46502d504c41424f5241544f5259';
    let bundle=abi.encode(['bytes','bytes'],[pv(op),proofBytes]);
    if(op.proof==='empty') bundle='0x';
    if(op.proof==='malformed') bundle='0x'+'00'.repeat(160);
    const verifier=route==='attestation'?(op.committee==='other'?c.otherAtt:c.att):c.zk;
    if(route==='attestation' && op.signatures) {
      const digest=await verifier.attestationDigest(input,output,ethers.keccak256(metadata));
      const indexes=op.signatures==='duplicate'?[0,0]:op.signatures==='outsider'?[2,3]:[0,1];
      const sigs=await Promise.all(indexes.map(i=>c.signers[i].signMessage(ethers.getBytes(digest))));
      summary.distinct_signers=new Set(sigs.map(s=>ethers.verifyMessage(ethers.getBytes(digest),s))).size;
      bundle=abi.encode(['bytes[]'],[sigs]);
      n.signature_format='LAB_EIP191_BYTES_ARRAY_NOT_AN_UPSTREAM_FORMAT';
    }
    summary.inner=await verifier.verify(input,output,metadata,bundle);
    const target=route==='attestation'?c.attAgent:op.instance==='other'?c.otherAgent:c.agent;
    n.contract=await target.getAddress(); n.verifier=await verifier.getAddress(); n.caller=c.addresses[op.actor || 0];
    n.proof_sha256=ethers.sha256(bundle); n.public_values= pv(op);
    const tasks=op.repeat==='same'?[task,task]:op.repeat==='fresh'?[task,X]:[task];
    for(const t of tasks) {
      const receipt=await (await target.connect(c.signers[op.actor || 0]).verify(t,agentId,input,output,bundle)).wait();
      const event=receipt.logs.map(l=>{try{return target.interface.parseLog(l);}catch{return null;}}).find(e=>e?.name==='VerificationCompleted');
      if(!event) throw Error('MISSING_NATIVE_EVENT');
      const a=event.args;
      const independentDigest=ethers.keccak256(abi.encode(['bytes32','bytes32','bytes32','bytes32','bool','bytes32','uint256','bytes','bytes'],[t,agentId,input,output,a.valid,await target.agentProofProfile(),a.timestamp,await target.getAddress(),abi.encode(['uint256'],[chain])]));
      if (independentDigest!==a.verificationDigest) throw Error('EVENT_DIGEST_MISMATCH');
      summary.calls.push(a.valid); n.verification_digest=a.verificationDigest;
      n.task_used=await target.usedTasks(t);
    }
    summary.outer=summary.calls.at(-1);
    if(op.repeat==='fresh') n.task_id=X;
  }
  result[row.id]=n;
}
for(const c of contexts.values()) await c.conn.close();
process.stdout.write(JSON.stringify(result)+'\n');
