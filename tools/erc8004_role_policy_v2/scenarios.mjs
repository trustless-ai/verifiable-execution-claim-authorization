// Inputs only; no expectations, vectors or obligation catalog enter this runtime.
const walletTypes = {AgentWalletSet:[{name:'agentId',type:'uint256'},
  {name:'newWallet',type:'address'},{name:'owner',type:'address'},{name:'deadline',type:'uint256'}]};
async function captureRoles(subject, validator, receipt) {
  const blockTag = receipt.blockNumber;
  const block = await rpc.request({method:'eth_getBlockByNumber',params:[blockTag,false]});
  if (block.hash !== receipt.blockHash) throw Error('receipt block not established');
  const calls = {};
  async function read(key, method, args) {
    const data = id.interface.encodeFunctionData(method,args);
    const result = await rpc.request({method:'eth_call',params:[{to:id.target,data},blockTag]});
    calls[key] = {to:id.target,data,block_tag:blockTag,result};
    return id.interface.decodeFunctionResult(method,result)[0];
  }
  const owner = await read('owner','ownerOf',[subject]);
  const operator = await read('operator','isApprovedForAll',[owner,validator]);
  const approved = await read('approved','getApproved',[subject]);
  const agent_wallet = await read('agent_wallet','getAgentWallet',[subject]);
  const binding = {agent_id:Number(subject),validator,request_hash:requestHash,
    block_number:receipt.blockNumber,block_hash:receipt.blockHash};
  return {roles:{...binding,owner,operator,approved,agent_wallet},calls:{...binding,
    schema:'erc8004.request-role-calls.v2',capture:'LOCAL_EVM_ETH_CALL_AT_RECEIPT_BLOCK',
    registry:id.target,chain_id:31337,block:{number:block.number,hash:block.hash},calls}};
}
for (const test of request.cases) {
  if (!await rpc.request({method:'evm_revert',params:[snapshot]})) throw Error('snapshot restore failed');
  snapshot = await rpc.request({method:'evm_snapshot'});
  const op = test.input.operation;
  if (op.kind !== 'respond_validation') throw Error('unsupported operation');
  const subject = BigInt(op.agent_id), validator = addresses[op.validator];
  if (!validator || !signers[op.actor]) throw Error('unknown laboratory actor');
  const walletUpdates = [], transfers = [];
  let requestActor = 0;
  async function updateWallet(target, valid=true, actor=0) {
    const block = await rpc.request({method:'eth_getBlockByNumber',params:['latest',false]});
    const deadline = Number(BigInt(block.timestamp)) + 240;
    const domain = {name:'ERC8004IdentityRegistry',version:'1',chainId:31337,verifyingContract:id.target};
    const value = {agentId:op.agent_id,newWallet:addresses[target],owner:await id.ownerOf(subject),deadline};
    const signature = await signers[valid ? target : (target + 1) % signers.length].signTypedData(domain,walletTypes,value);
    const before = await id.getAgentWallet(subject);
    const result = await transact(() => id.connect(signers[actor]).setAgentWallet(subject,addresses[target],deadline,signature,txOptions));
    const after = await id.getAgentWallet(subject);
    walletUpdates.push({...result,domain,types:walletTypes,value,signature,
      recovered:ethers.verifyTypedData(domain,walletTypes,value,signature),before,after});
    if (valid && result.status !== 'ACCEPTED') throw Error('valid setup wallet update failed');
  }
  if (op.role === 'operator') await (await id.setApprovalForAll(validator,true,txOptions)).wait();
  else if (op.role === 'approved') await (await id.approve(validator,subject,txOptions)).wait();
  else if (op.role !== 'none') throw Error('unsupported role');
  if (op.before === 'wallet_validator') await updateWallet(op.validator);
  else if (op.before === 'wallet_other') await updateWallet(2);
  else if (op.before === 'invalid_wallet_signature') await updateWallet(op.validator,false);
  else if (op.before === 'wallet_validator_then_other') { await updateWallet(op.validator); await updateWallet(2); }
  else if (op.before === 'wallet_then_transfer') {
    await updateWallet(op.validator);
    transfers.push(await transact(() => id.transferFrom(addresses[0],addresses[3],subject,txOptions)));
    requestActor = 3;
  } else if (op.before === 'wallet_by_operator' || op.before === 'wallet_by_approved') {
    if (op.before === 'wallet_by_operator') await (await id.setApprovalForAll(addresses[2],true,txOptions)).wait();
    else await (await id.approve(addresses[2],subject,txOptions)).wait();
    await updateWallet(op.validator,true,2);
  } else if (op.before !== 'none') throw Error('unsupported wallet setup');
  const requested = await transact(() => val.connect(signers[requestActor]).validationRequest(
    validator,subject,'ipfs://laboratory-role-policy-v2',requestHash,txOptions));
  if (requested.status !== 'ACCEPTED') throw Error('request setup failed');
  const captured = await captureRoles(subject,validator,requested.receipt);
  if (op.after === 'wallet_validator') await updateWallet(op.validator,true,requestActor);
  else if (op.after === 'wallet_other') await updateWallet(2,true,requestActor);
  else if (op.after === 'unset_wallet') await (await id.connect(signers[requestActor]).unsetAgentWallet(subject,txOptions)).wait();
  else if (op.after === 'transfer_away' || op.after === 'transfer_to_validator')
    transfers.push(await transact(() => id.transferFrom(addresses[0],op.after === 'transfer_away' ? addresses[3] : validator,subject,txOptions)));
  else if (op.after === 'grant_operator') await (await id.setApprovalForAll(validator,true,txOptions)).wait();
  else if (op.after === 'grant_approved') await (await id.approve(validator,subject,txOptions)).wait();
  else if (op.after === 'revoke_operator') await (await id.setApprovalForAll(validator,false,txOptions)).wait();
  else if (op.after === 'revoke_approved') await (await id.approve(ethers.ZeroAddress,subject,txOptions)).wait();
  else if (op.after !== 'none') throw Error('unsupported subsequent transition');
  const result = await transact(() => val.connect(signers[op.actor]).validationResponse(requestHash,100,'',responseHash,'final',txOptions));
  const status = await val.getValidationStatus(requestHash);
  const response = await captureRoles(subject,validator,result.receipt);
  observations[test.id] = {...result,state:status[2] === 100n ? 'RESPONSE_RECORDED' : 'RESPONSE_ABSENT',
    chain_id:31337,registry_role:'validation',registry_address:val.target,identity_registry_address:id.target,
    agent_id:op.agent_id,validator:status[0],actors:addresses,request_hash:requestHash,response_hash:responseHash,
    request_payload_hex:ethers.hexlify(requestPayload),request_receipt:requested.receipt,request_transaction:requested.transaction,
    request_roles:captured.roles,request_role_calls:captured.calls,response_roles:response.roles,response_role_calls:response.calls,
    wallet_updates:walletUpdates,transfers};
}
