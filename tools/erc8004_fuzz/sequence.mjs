// Included after the unchanged pinned pilot bootstrap. No oracle or expectations.
const observations = {};
const actorId = address => address.toLowerCase() === ethers.ZeroAddress ? null :
  (addresses.findIndex(a => a.toLowerCase() === address.toLowerCase()) >= 0 ?
   addresses.findIndex(a => a.toLowerCase() === address.toLowerCase()) : 'external:' + address.toLowerCase());
const addr = index => index === null ? ethers.ZeroAddress : addresses[index];
let snapshot = await rpc.request({method: 'evm_snapshot'});
for (const test of request.cases) {
  if (!await rpc.request({method: 'evm_revert', params: [snapshot]})) throw Error('snapshot restore failed');
  snapshot = await rpc.request({method: 'evm_snapshot'});
  const sequence = test.input.sequence;
  const metadataKeys = [...new Set(sequence.flatMap(o => o.kind === 'metadata' ? [o.key] :
    (o.metadata ?? []).map(m => m.key)))].filter(k => k !== 'agentWallet').sort();
  const candidates = [...new Set([...sequence.map(o => o.agent_id),
    ...sequence.filter(o => o.kind === 'register').map((_, i) => i)])].sort((a,b) => a-b);
  const pairs = [...new Set(sequence.filter(o => o.kind === 'operator' && o.operator !== null)
    .map(o => `${o.actor}:${o.operator}`))].sort();
  const labels = [...new Set(sequence.filter(o => ['request','respond'].includes(o.kind)).map(o => o.label))].sort();
  const payloads = Object.fromEntries(labels.map(l => [l, ethers.toUtf8Bytes(JSON.stringify({laboratory_request: l}))]));
  const hashes = Object.fromEntries(labels.map(l => [l, ethers.keccak256(payloads[l])]));
  const responded = new Set();
  const steps = [], raw = [];
  for (const op of sequence) {
    const who = signers[op.actor], subject = op.agent_id;
    const identityActor = id.connect(who), validationActor = val.connect(who);
    let action, signed = null;
    if (op.kind === 'register') {
      action = op.overload === 0 ? () => identityActor['register()'](txOptions) : op.overload === 1 ?
        () => identityActor['register(string)'](op.uri, txOptions) :
        () => identityActor['register(string,(string,bytes)[])'](op.uri, op.metadata.map(m => [m.key,m.value]), txOptions);
    } else if (op.kind === 'operator') action = () => identityActor.setApprovalForAll(addr(op.operator), op.enabled, txOptions);
    else if (op.kind === 'approve') action = () => identityActor.approve(addr(op.operator), subject, txOptions);
    else if (op.kind === 'uri') action = () => identityActor.setAgentURI(subject, op.uri, txOptions);
    else if (op.kind === 'metadata') action = () => identityActor.setMetadata(subject, op.key, op.value, txOptions);
    else if (op.kind === 'unset') action = () => identityActor.unsetAgentWallet(subject, txOptions);
    else if (op.kind === 'transfer') action = () => identityActor.transferFrom(addr(op.from), addr(op.to), subject, txOptions);
    else if (op.kind === 'wallet') {
      const block = await rpc.request({method:'eth_getBlockByNumber', params:['latest',false]});
      const deadline = Number(BigInt(block.timestamp)) + 1 + op.deadline_offset;
      const domain = {name:'ERC8004IdentityRegistry', version:'1', chainId:op.signature_chain,
        verifyingContract:op.signature_registry === 'identity' ? id.target : val.target};
      const types = {AgentWalletSet:[{name:'agentId',type:'uint256'},{name:'newWallet',type:'address'},
        {name:'owner',type:'address'},{name:'deadline',type:'uint256'}]};
      const message = {agentId:op.signed_agent, newWallet:addr(op.wallet), owner:addr(op.signed_owner), deadline};
      const signature = await signers[op.signature_actor].signTypedData(domain, types, message);
      signed = {domain, types, message, signature};
      action = () => identityActor.setAgentWallet(subject, addr(op.wallet), deadline, signature, txOptions);
    } else if (op.kind === 'request') action = () => validationActor.validationRequest(addr(op.validator), subject, 'ipfs://laboratory', hashes[op.label], txOptions);
    else if (op.kind === 'respond') action = () => validationActor.validationResponse(hashes[op.label], op.response, '', op.response_hash, op.tag, txOptions);
    else throw Error('unknown sequence operation');
    const tx = await transact(action);
    const decoded = tx.receipt.logs.map(log => {
      const iface = log.address.toLowerCase() === id.target.toLowerCase() ? id.interface : val.interface;
      try { const e = iface.parseLog(log); return e ? {name:e.name, args:e.args.toArray().map(v => typeof v === 'bigint' ? v.toString() : v)} : null; }
      catch { return null; }
    }).filter(Boolean);
    if (decoded.some(e => e.name === 'ValidationResponse')) responded.add(op.label);
    const agents = {}, operators = [], requests = {}, summaries = {};
    for (const aid of candidates) {
      let owner;
      try { owner = await id.ownerOf(aid); }
      catch (error) { if (error.code === 'CALL_EXCEPTION' && error.revert?.name === 'ERC721NonexistentToken') continue; throw error; }
      const metadata = {};
      for (const key of metadataKeys) metadata[key] = await id.getMetadata(aid, key);
      agents[String(aid)] = {owner:actorId(owner), wallet:actorId(await id.getAgentWallet(aid)),
        approved:actorId(await id.getApproved(aid)), uri:await id.tokenURI(aid), metadata};
      const summary = await val.getSummary(aid, [], '');
      summaries[String(aid)] = {count:Number(summary[0]), average:Number(summary[1])};
    }
    for (const pair of pairs) {
      const [a,b] = pair.split(':').map(Number);
      if (await id.isApprovedForAll(addr(a),addr(b))) operators.push(pair);
    }
    const registeredHashes = new Set();
    for (const aid of candidates) for (const hash of await val.getAgentValidations(aid)) registeredHashes.add(hash);
    for (const label of labels) {
      if (!registeredHashes.has(hashes[label])) continue;
      const s = await val.getValidationStatus(hashes[label]);
      requests[label] = {validator:actorId(s[0]), agent_id:Number(s[1]), response:Number(s[2]),
        response_hash:s[3], tag:s[4], responded:responded.has(label)};
    }
    const selected = new Set(['Transfer','Approval','ApprovalForAll','Registered','MetadataSet','URIUpdated','ValidationRequest','ValidationResponse']);
    steps.push({status:tx.status, events:decoded.filter(e => selected.has(e.name)).map(e => e.name),
      state:{agents,operators,requests,summaries}});
    raw.push({...tx, signed, decoded_events:decoded});
  }
  observations[test.id] = {steps, raw, chain_id:31337, registry_address: ['request','respond'].includes(sequence.at(-1).kind) ? val.target : id.target,
    registry_role:['request','respond'].includes(sequence.at(-1).kind) ? 'validation' : 'identity',
    actors:addresses, request_payloads:Object.fromEntries(labels.map(l => [l,ethers.hexlify(payloads[l])])),request_hashes:hashes};
}
