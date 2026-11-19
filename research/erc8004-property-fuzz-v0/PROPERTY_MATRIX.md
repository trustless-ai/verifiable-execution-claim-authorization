# Oracle contract, v0

Specification: `ethereum/ERCs@503591a6e80e6e1affdd6403341e25269141f046`,
`ERCS/erc-8004.md`. Implementation:
`erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`.
All actors are distinct laboratory EOA keys, not independently identified people.

| ID | Source / kind | Expected property and observable witness | Oracle dependencies / sensitivity control |
| --- | --- | --- | --- |
| N_REG | Registration; normative | Successful registration emits Registered and wallet metadata; initial owner/wallet is caller; IDs advance only on successful registration | Empty local proxy state, ERC721 mint semantics; all three overloads and rejected reserved metadata |
| N_RESERVED | On-chain metadata; normative | agentWallet cannot be supplied through generic metadata or registration metadata | Exact case-sensitive reserved key; remove registration overload check |
| N_TRANSFER | On-chain metadata; normative | Transfer clears wallet; ownership and token approval reflect transfer | ERC721 authority semantics; old-owner/old-token-operator follow-up actions |
| N_URI | Identity Registry / Update agentURI; normative | Current owner or approved operator can set URI, unrelated actor cannot | Explicit actor permission relation, stored URI, URIUpdated event |
| I_METADATA | setMetadata; implementation behavior | Current owner, token-approved or globally approved actor can set arbitrary nonreserved metadata; others cannot | Access policy interpreted from pinned function, not an invented normative MUST; remove only its authority check |
| I_UNSET | unsetAgentWallet; implementation behavior | Wallet clear uses same authority relation and emits metadata event | Remove only unset authority check |
| I_WALLET | setAgentWallet; implementation behavior | EOA signature binds agent, wallet, current owner, domain and deadline; permitted interval is transaction time through +300 seconds inclusive | Lab typed-data signer, next-block timestamp; remove upper deadline check |
| N_REQUEST | Validation Request; normative | Only current owner/operator can request; validator and subject are recorded in state/event | Independent ownership model; attempt request after transfer/revocation |
| I_REQUEST | validationRequest; implementation behavior | Duplicate request hash and zero validator rejected | Unique fixture labels map to locally computed payload commitments; no external input-admission claim |
| N_RESPONSE | Validation Response; normative | Only designated validator can respond, response in 0..100; multiple updates permitted | Integer range and request map; remove response upper-bound check |
| I_STATE | Pinned read functions / atomic EVM revert; implementation behavior | Metadata, URI, wallet, approvals, request membership/status and unfiltered response summaries agree after each step; rejected transitions leave modeled state unchanged | Python state model does not read implementation observations; bounded queried projection, not full storage equivalence |
| P_CLAIM | Existing laboratory policy; research policy | Wrong type, subject, operation, registry/chain, policy or unknown claim field refuses authorization | Independent expected decision; reuse actual existing authorize function |
| P_EVIDENCE | Existing laboratory policy; research policy | Missing receipt is UNVERIFIABLE; conformant revert remains REFUTED, never authorization PASS | Actual receipt availability and last transaction status; conformance and authorization separate |

Registration URI resolution and full registration-file schema are outside this
contract-behavior profile: strings exercise storage, not external URI conformance.
EOA-only signatures do not cover ERC1271/7702. Validation asserts that the designated
key submitted a value; it does not establish that the value is true.

Every sequence begins from empty initialized local registries. The model specifies
preconditions and state effects independently in Python. The Node executor only
submits fixture operations and queries actual contracts. Expected state includes
successful and rejected steps; no rejection is discarded with an assume/filter.
The property catalog is derived from these clauses and declared assumptions,
not from whichever checks the adapter happens to expose.

## Exact source anchors and limits

The pinned draft's Identity Registry section (line 48) describes ERC721 ownership
and operator delegation; On-chain metadata (lines 138-154) supplies the reserved
wallet and transfer-reset rules; Registration (lines 157-177) supplies overloads
and events; Update agentURI (lines 180-188) supplies URI mutation and its event.
Validation Request (lines 349-361) supplies owner/operator authority and request
bindings; Validation Response (lines 366-383) supplies designated-validator authority,
the 0..100 range and allowed repeated responses. These anchors refer to the exact
specification commit above, not a claim about the latest evolving draft.

The table combines normative clauses with explicitly labeled implementation
consequences. In particular, sequential local agent IDs, exact selected-event order,
ERC721 token-approval clearing, the wallet deadline ceiling and summary arithmetic
come from the pinned implementation/dependencies, not additional ERC MUSTs.
The normative IDs are traceability labels for mixed observable witnesses; they do
not turn every detail in an expected state object into a normative obligation.

The generated profile compares event names/order and queried state, not every
event argument or every storage slot. Raw event arguments remain available for
inspection. Request-list order/duplication and filtered summary variants are not
fully graded. A response value of zero is distinguished from an unanswered request
through actual response events and the contract's summary count. State snapshots
do not cover balances, gas, timestamps or full proxy/upgrade behavior.

The generated reserved-key family targets the registration metadata overload;
generic `setMetadata(agentWallet, ...)` is not a generated family here. Likewise,
some generated invalid calls have more than one failing precondition (for example,
a duplicate request label combined with a zero validator). Their correct rejection
does not independently demonstrate that every individual guard is load-bearing.
The six physical controls establish guard sensitivity only for their specified sites.
