// Executes pinned upstream Solidity, without reading expected outcomes.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import crypto from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtime = path.join(root, 'build/erc8004/runtime');
const sourceRoot = path.resolve(process.argv[2]);
const requireRuntime = createRequire(path.join(runtime, 'package.json'));
const ethers = requireRuntime('ethers');
const solc = requireRuntime('solc');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const request = JSON.parse(fs.readFileSync(0, 'utf8'));
const sourceNames = ['HardhatMinimalUUPS', 'ERC1967Proxy', 'IdentityRegistryUpgradeable', 'ValidationRegistryUpgradeable'];
const sources = Object.fromEntries(sourceNames.map(n => [`contracts/${n}.sol`, {content: fs.readFileSync(path.join(sourceRoot, `contracts/${n}.sol`), 'utf8')}]));
const compileInput = {language: 'Solidity', sources, settings: {evmVersion: 'shanghai', optimizer: {enabled: true, runs: 200}, outputSelection: {'*': {'*': ['abi', 'evm.bytecode.object', 'evm.deployedBytecode.object']}}}};
const compiled = JSON.parse(solc.compile(JSON.stringify(compileInput), {import: name => {
  const filename = path.join(runtime, 'node_modules', name);
  return fs.existsSync(filename) ? {contents: fs.readFileSync(filename, 'utf8')} : {error: `missing import ${name}`};
}}));
const errors = (compiled.errors ?? []).filter(e => e.severity === 'error');
if (errors.length) throw Error(JSON.stringify(errors));
process.chdir(runtime);
const {network} = await import(pathToFileURL(requireRuntime.resolve('hardhat')).href);
const connection = await network.connect('laboratory');
const rpc = connection.provider;
// Wall-clock time must not affect signatures, receipts or replay evidence.
const originalRequest = rpc.request.bind(rpc);
rpc.request = async args => {
  if (args.method === 'eth_sendTransaction' || args.method === 'eth_sendRawTransaction') {
    const block = await originalRequest({method:'eth_getBlockByNumber', params:['latest',false]});
    await originalRequest({method:'evm_setNextBlockTimestamp', params:[Number(BigInt(block.timestamp))+1]});
  }
  return originalRequest(args);
};
const provider = new ethers.BrowserProvider(rpc, undefined, {cacheTimeout: -1});
provider.pollingInterval = 10;
const signers = await Promise.all([0,1,2,3].map(n => provider.getSigner(n)));
const addresses = await Promise.all(signers.map(s => s.getAddress()));
const artifacts = Object.fromEntries(sourceNames.map(n => [n, compiled.contracts[`contracts/${n}.sol`][n]]));
async function deploy(name, args=[]) {
  const a=artifacts[name];
  const c=await new ethers.ContractFactory(a.abi, a.evm.bytecode.object, signers[0]).deploy(...args);
  await c.waitForDeployment(); return c;
}
const minimal = await deploy('HardhatMinimalUUPS');
async function registry(name, init) {
  const proxy = await deploy('ERC1967Proxy', [minimal.target, minimal.interface.encodeFunctionData('initialize', [ethers.ZeroAddress])]);
  const impl = await deploy(name);
  const iface = new ethers.Interface(artifacts[name].abi);
  await (await new ethers.Contract(proxy.target, artifacts.HardhatMinimalUUPS.abi, signers[0]).upgradeToAndCall(impl.target, iface.encodeFunctionData('initialize', init))).wait();
  return {contract: new ethers.Contract(proxy.target, artifacts[name].abi, signers[0]), implementation: impl.target};
}
const identity = await registry('IdentityRegistryUpgradeable', []);
const validation = await registry('ValidationRegistryUpgradeable', [identity.contract.target]);
const id = identity.contract, val = validation.contract;
await (await id['register(string)']('data:application/json;base64,e30=')).wait();
await (await id['register(string)']('data:application/json;base64,e30=')).wait();
const requestPayload = ethers.toUtf8Bytes('{"agent":0,"job":"laboratory-validation"}');
const requestHash = ethers.keccak256(requestPayload);
const responseHash = ethers.keccak256(ethers.toUtf8Bytes('laboratory validator assertion'));
let snapshot = await rpc.request({method:'evm_snapshot'});
const observations = {};
const txOptions = {gasLimit: 3000000};
async function transact(fn) {
  let receipt;
  try { receipt = await (await fn()).wait(); }
  catch (error) { if (error.receipt?.status !== 0) throw error; receipt = error.receipt; }
  const raw = await rpc.request({method:'eth_getTransactionReceipt', params:[receipt.hash]});
  const tx = await rpc.request({method:'eth_getTransactionByHash', params:[receipt.hash]});
  return {status: receipt.status === 1 ? 'ACCEPTED' : 'REJECTED', transaction: tx, receipt: raw};
}
for (const test of request.cases) {
  if (!await rpc.request({method:'evm_revert', params:[snapshot]})) throw Error('snapshot restore failed');
  snapshot = await rpc.request({method:'evm_snapshot'});
  const op = test.input.operation;
  const actor = signers[op.actor];
  if (!actor) throw Error('unknown laboratory actor');
  const subject = BigInt(op.agent_id);
  if (op.approve) await (await id.approve(addresses[op.actor], subject, txOptions)).wait();
  if (op.transfer_first) await (await id.transferFrom(addresses[0], addresses[1], subject, txOptions)).wait();
  let result, state, role='identity', signature=null;
  if (op.kind === 'set_uri') {
    result=await transact(() => id.connect(actor).setAgentURI(subject, 'data:application/json;base64,eyJuYW1lIjoicGlsb3QifQ==', txOptions));
    state=(await id.tokenURI(subject)) === 'data:application/json;base64,eyJuYW1lIjoicGlsb3QifQ==' ? 'URI_UPDATED' : 'URI_UNCHANGED';
  } else if (op.kind === 'set_wallet') {
    const block=await rpc.request({method:'eth_getBlockByNumber', params:['latest', false]});
    const deadline=Number(BigInt(block.timestamp)) + (op.expired ? -1 : 240);
    const domain={name:'ERC8004IdentityRegistry',version:'1',chainId:op.signature_chain ?? 31337,verifyingContract:op.signature_registry === 'other' ? val.target : id.target};
    const types={AgentWalletSet:[{name:'agentId',type:'uint256'},{name:'newWallet',type:'address'},{name:'owner',type:'address'},{name:'deadline',type:'uint256'}]};
    signature=await signers[op.signature_actor ?? 2].signTypedData(domain,types,{agentId:subject,newWallet:addresses[2],owner:await id.ownerOf(subject),deadline});
    result=await transact(() => id.connect(actor).setAgentWallet(subject,addresses[2],deadline,signature,txOptions));
    state=(await id.getAgentWallet(subject))===addresses[2] ? 'WALLET_SET' : 'WALLET_UNCHANGED';
  } else if (op.kind === 'transfer') {
    result=await transact(() => id.connect(actor).transferFrom(addresses[0],addresses[1],subject,txOptions));
    state=(await id.getAgentWallet(subject))===ethers.ZeroAddress ? 'WALLET_CLEARED' : 'WALLET_RETAINED';
  } else if (op.kind === 'reserved_metadata') {
    result=await transact(() => id.connect(actor).setMetadata(subject,'agentWallet',addresses[2],txOptions));
    state=(await id.getAgentWallet(subject))===addresses[2] ? 'WALLET_SET' : 'WALLET_UNCHANGED';
  } else if (op.kind === 'request_validation') {
    role='validation';
    if (op.duplicate) await (await val.validationRequest(addresses[2],subject,'ipfs://laboratory',requestHash,txOptions)).wait();
    result=await transact(() => val.connect(actor).validationRequest(addresses[2],subject,'ipfs://laboratory',requestHash,txOptions));
    state=(await val.getAgentValidations(subject)).length ? 'REQUEST_RECORDED' : 'REQUEST_ABSENT';
  } else if (op.kind === 'respond_validation') {
    role='validation';
    if (!op.unknown_request) await (await val.validationRequest(addresses[2],subject,'ipfs://laboratory',requestHash,txOptions)).wait();
    if (op.update) await (await val.connect(signers[2]).validationResponse(requestHash,50,'',responseHash,'soft',txOptions)).wait();
    result=await transact(() => val.connect(actor).validationResponse(requestHash,100,'',responseHash,'final',txOptions));
    const hashes=await val.getAgentValidations(subject);
    state=hashes.length && (await val.getValidationStatus(requestHash))[2]===100n ? 'RESPONSE_RECORDED' : 'RESPONSE_ABSENT';
  } else { throw Error('unsupported operation'); }
  observations[test.id]={...result,state,chain_id:Number((await provider.getNetwork()).chainId),registry_role:role,registry_address:role==='identity'?id.target:val.target,
    agent_id:op.agent_id,actors:addresses,signature,request_payload_hex:ethers.hexlify(requestPayload),request_hash:requestHash,response_hash:responseHash};
}
const output={observations,runtime:{node:process.version,solc:solc.version(),hardhat:'3.0.6',evm:'shanghai',chain_id:31337,
  source_sha256:Object.fromEntries(Object.entries(sources).map(([n,v])=>[n,sha(Buffer.from(v.content))])),
  compiler_input_sha256:sha(Buffer.from(JSON.stringify(compileInput))),
  identity_implementation:identity.implementation,validation_implementation:validation.implementation,
  identity_codehash:ethers.keccak256(await provider.getCode(identity.implementation)),validation_codehash:ethers.keccak256(await provider.getCode(validation.implementation)),
  deployment_method:'upstream HardhatMinimalUUPS bootstrap -> real UUPS registry implementation; local EDR only'}};
await connection.close();
process.stdout.write(JSON.stringify(output));
