// Scenario extension evaluated inside the pinned v0 local EVM runtime.
// Receives inputs only, never vectors/obligations/expected outcomes.
for (const test of request.cases) {
  if (!await rpc.request({method:'evm_revert', params:[snapshot]})) throw Error('snapshot restore failed');
  snapshot = await rpc.request({method:'evm_snapshot'});
  const op = test.input.operation;
  if (op.kind !== 'respond_validation') throw Error('unsupported operation');
  const subject = BigInt(op.agent_id);
  const validator = addresses[op.validator];
  if (!validator || !signers[op.actor]) throw Error('unknown laboratory actor');
  if (op.role === 'operator') await (await id.setApprovalForAll(validator, true, txOptions)).wait();
  else if (op.role === 'approved') await (await id.approve(validator, subject, txOptions)).wait();
  else if (op.role !== 'none') throw Error('unsupported setup role');
  const requested = await transact(() => val.validationRequest(validator, subject, 'ipfs://laboratory-role-policy', requestHash, txOptions));
  if (requested.status !== 'ACCEPTED') throw Error('request setup failed');
  // Query the request block, not response-time state; use the same fixed block
  // for owner, global approval and token approval. No intervening transaction.
  const blockTag = Number(BigInt(requested.receipt.blockNumber));
  const owner = await id.ownerOf(subject, {blockTag});
  const requestRoles = {owner, validator, approved: await id.getApproved(subject, {blockTag}),
    operator: await id.isApprovedForAll(owner, validator, {blockTag}), agent_id: op.agent_id,
    request_hash: requestHash, block_number: requested.receipt.blockNumber, block_hash: requested.receipt.blockHash};
  if (op.after === 'revoke_operator') await (await id.setApprovalForAll(validator, false, txOptions)).wait();
  else if (op.after === 'revoke_approved') await (await id.approve(ethers.ZeroAddress, subject, txOptions)).wait();
  else if (op.after === 'grant_operator') await (await id.setApprovalForAll(validator, true, txOptions)).wait();
  else if (op.after === 'grant_approved') await (await id.approve(validator, subject, txOptions)).wait();
  else if (op.after === 'transfer_away') await (await id.transferFrom(addresses[0], addresses[3], subject, txOptions)).wait();
  else if (op.after === 'transfer_to_validator') await (await id.transferFrom(addresses[0], validator, subject, txOptions)).wait();
  else if (op.after !== 'none') throw Error('unsupported role transition');
  if (op.update) await (await val.connect(signers[op.validator]).validationResponse(requestHash,50,'',responseHash,'soft',txOptions)).wait();
  const result = await transact(() => val.connect(signers[op.actor]).validationResponse(requestHash,100,'',responseHash,'final',txOptions));
  const status = await val.getValidationStatus(requestHash);
  const responseOwner = await id.ownerOf(subject);
  const responseRoles = {owner:responseOwner,validator,approved:await id.getApproved(subject),
    operator:await id.isApprovedForAll(responseOwner,validator),agent_id:op.agent_id,
    request_hash:requestHash,block_number:result.receipt.blockNumber,block_hash:result.receipt.blockHash};
  observations[test.id] = {...result, state:status[2] === 100n ? 'RESPONSE_RECORDED' : 'RESPONSE_ABSENT',
    chain_id:31337, registry_role:'validation', registry_address:val.target, agent_id:op.agent_id,
    validator:status[0], actors:addresses, request_hash:requestHash, response_hash:responseHash,
    request_payload_hex:ethers.hexlify(requestPayload), request_receipt:requested.receipt,
    request_transaction:requested.transaction, request_roles:requestRoles, response_roles:responseRoles};
}
