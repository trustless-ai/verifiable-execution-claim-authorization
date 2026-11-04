# Independent profile and coverage boundary

Specification source: [ERC-8004 draft, exact revision](https://github.com/ethereum/ERCs/blob/503591a6e80e6e1affdd6403341e25269141f046/ERCS/erc-8004.md). Implementation: [exact registry revision](https://github.com/erc-8004/erc-8004-contracts/tree/b9e466c250744a7e06b13dff9d3c2844ed64f825).

The obligations and expected outcomes were authored from the specification, declared laboratory policy and source behavior before execution. `build_vectors.py` imports neither the adapter nor its outputs. Coverage is finite and does not imply that this catalog exhausts ERC-8004.

| Obligation | Classification | Witnesses / interpretation |
| --- | --- | --- |
| N1 | Normative specification | Owner/operator URI update; stranger and transferred-away owner refused |
| N2 | Normative specification | Actual EIP-712 wallet control; unrelated signer refused |
| N3 | Normative specification | Transfer clears the old wallet |
| N4 | Normative specification | Reserved wallet metadata cannot bypass signature checks |
| N5 | Normative specification | Owner/operator validation request; stranger refused |
| N6 | Normative specification | Response comes from the validator selected for that request |
| N7 | Normative specification | A designated validator may update its response; this is not prohibited replay |
| I1 | Implementation behavior | Expiration and concrete EIP-712 chain/contract domain checks |
| I2 | Implementation behavior | Duplicate requestHash rejection in this implementation |
| P1 | Research policy | Only `LAB_REGISTRY_TRANSITION`; no task-completion/payment claims |
| P2 | Research policy | Exact policy `erc8004-registry-observation-v0` |
| P3 | Research policy | Reject unconsumed fields, including an asserted outputHash |
| P4–P6 | Research policy | Exact subject, operation, chain and registry role |
| P7 | Research policy | Required receipt unavailable implies UNVERIFIABLE |
| P8 | Research policy | A reverted operation cannot support a successful transition claim |

The seven normative, two implementation-behavior and eight research-policy obligations are independently labeled in [the machine-readable catalog](../../conformance/erc8004-pilot-v0/obligations.json). A failure against I1/I2 or P1–P8 is not automatically an ERC violation. The method name or a successful transaction alone does not justify a broader guarantee.

## Laboratory observation policy

`LAB_REGISTRY_TRANSITION` means that this exact operation was accepted in the local EVM under the observed registry configuration. The portable scope commits to the exact symbolic operation via SHA-256, agent ID, operation kind, chain ID, registry role and policy. The full evidence scope additionally contains the concrete registry address and mined transaction hash. It does not assert that the agent's advertised task happened, that a validator's statement is true, that the signer is a distinct person, or that payment is permitted.

The adapter records actual execution and separately applies this narrow policy. Backend conformance compares the observed state transition with independent expected behavior. Thus a mutant can produce a real accepted transaction while failing conformance. These two outcomes must not be conflated.

Raw evidence contains transactions, receipts, logs, actor addresses, actual signatures, request payload/hash, source hashes, compiler-input hash and runtime code hashes. No caller-supplied `authorized` flag is accepted as execution evidence. Missing receipts are deliberately withheld from the policy even though the laboratory has executed the underlying operation; this is an evidence-availability control.

## Mutation contract

Nine Solidity changes target URI authority, wallet signature, deadline, transfer reset, reserved metadata, validation-request authority, duplicate request, response authority and prohibited rejection of permitted updates. Eight adapter changes independently remove the policy guards above. Each mutant is physically written in a disposable directory, compiled/executed, compared against a targeted witness and a positive control, then the unchanged original is replayed.

KILLED requires the intended behavioral change, a failed targeted comparison, a passing positive control and a passing restored baseline. CRASHED, NOT_APPLIED, UNVERIFIABLE and SURVIVED are distinct. Not every kill represents a false downstream authorization: rejecting a permitted update and retaining a wallet are observable conformance counterexamples.
