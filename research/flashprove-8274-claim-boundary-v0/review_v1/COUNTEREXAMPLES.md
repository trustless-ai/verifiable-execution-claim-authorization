# Three independently runnable counterexamples

All three execute public FlashProve source at
`ea1b613625513a658942af4bc79867d1c77412cd`. File SHA-256s are in the unchanged
`../SOURCE_PINS.json`. Compilation and EDR execution use the existing pinned
VECA runtime. No network RPC, live deployment, private key export or real SP1
proof is involved. Each command emits original inputs, full native observations,
independently authored expected results, grader output and a specific negative
regression control. Exit 0 means the stated bounded observation was reproduced.

Prepare once from the repository root:

```text
python -B research/flashprove-8274-claim-boundary-v0/prepare.py --runtime
```

## A: Same profile, distinct committees

```text
python -B research/flashprove-8274-claim-boundary-v0/review_v1/counterexamples.py --finding A --out build/flashprove-8274/counterexample-A
```

Minimal operation input: `{"kind":"profiles","route":"attestation"}`.
Construct two `FlashProveAttestVerifier` instances with threshold 2 and disjoint
two-address committees, plus a threshold-1 discriminator. The exact deterministic
addresses are printed in the native `committees` field. No signature is needed
to read the profiles; this observation does not depend on MockSP1 soundness.

Expected and originally observed: distinct committee arrays, equal `profile` and
`other_profile`, and `same_threshold_profile:false`. The runner also observes the
outer profile's configuration limitations, separately from this committee claim.
Fresh observations are under `A/run/adapter.stdout`; assertions and actual
digests are in `A/result.json`.

Missing guarantee: `proofProfile` does not uniquely commit to committee storage.
This contradicts the source comment's suggestion that rotating the committee
necessarily gives a distinct profile. It is not a cryptographic hash collision.
Exploitability requires a downstream consumer that treats profile equality as
committee-policy equality. Signature verification is still NOT_IMPLEMENTED.

Proposed remediation, not implemented upstream: specify a versioned canonical
commitment to committee membership, threshold and relevant signature-domain
configuration. Decide explicitly whether ordering is semantic. Preserve any old
profile as historical rather than silently redefining its identity.

Negative regression: changing only `other_profile` in the captured observation
must make `equal_profile` false and the finding test fail without an exception.
The original different-threshold discriminator must also remain healthy.

## B: agentId is not caller authentication

```text
python -B research/flashprove-8274-claim-boundary-v0/review_v1/counterexamples.py --finding B --out build/flashprove-8274/counterexample-B
```

Minimal pair: `{"kind":"call","route":"zk"}` and the same input with
`"actor":1`. One additional `agent = 0x77...77` call is the unknown-agent refusal
control. The fixed authorized agent is bytes32 `0x11` repeated 32 times; input,
output, commitment, vkey and task use repeated bytes `22`, `33`, `44`, `55`, `66`.
The 128-byte FPV1 public-values encoding and placeholder proof are constructed
explicitly by the unchanged `evm.mjs`, not inferred from a result.

Expected and originally observed: both callers receive native inner/outer true
for the same agent, proof and contract; the unknown agent receives false. The
consumer separately refuses the different caller with `CALLER_NOT_AGENT`.
The native `caller`, `agent_id`, `contract`, `proof_sha256` and event commitment
are retained under `B/run/adapter.stdout`.

Missing guarantee: the supplied allowlisted identifier does not authenticate
the transaction caller as that agent. Permissionless proof verification may be
intentional; this is a consumer hazard only if the boolean is promoted into caller
authorization. The proof here is accepted by upstream MockSP1, not real SP1.

Proposed remediation: if caller authentication is required, bind the agent to an
authenticated caller or delegated authorization including the application context.
If permissionless verification is intended, document it and never interpret the
boolean as permission to act for that agent.

Negative regression: replace the second observed caller with the first; the
`different_caller` assertion must fail. The unknown-agent refusal and healthy
positive call remain separately asserted.

## C: Reuse across task, instance and chain

```text
python -B research/flashprove-8274-claim-boundary-v0/review_v1/counterexamples.py --finding C --out build/flashprove-8274/counterexample-C
```

Inputs: a positive call; `repeat:"same"`; `repeat:"fresh"` (second task bytes32
`77`); `instance:"other"`; and `chain:31338` instead of 31337. All other proof
bytes and public values are held constant. Each case resets its isolated state.
The other chain constructs the same contracts at the same deterministic addresses.

Expected and originally observed: same-task calls return `[true,false]`, fresh
task `[true,true]`, other instance true, and other chain true. All five cases have
the same `proof_sha256`. The consumer refuses task, instance and chain substitutions.
Native addresses, chain IDs, task IDs and booleans are in `C/run/adapter.stdout`.

Missing guarantee: local single-use bookkeeping does not make the proof a global
context-bound authorization or nullifier. The event digest includes context but
recording context is not enforcing proof replay prevention. ERC-8274 does not
promise universal replay prevention. No actual SP1 soundness failure is claimed.
Any production exploit would additionally require a real accepted proof and an
application whose required context is omitted from authenticated proof/policy.

Proposed remediation: define the application's replay scope; bind required task,
chain, verifier instance, agent and expiry/nullifier into authenticated public
inputs or separate authorization. Enforce consumption in that declared scope.
Do not mistake verification success for ACTION_AUTHORIZED or ORDER_EXECUTED.

Negative regression: alter only the other-chain `proof_sha256`; `same_proof_bytes`
must fail, so a test using a different proof cannot masquerade as replay evidence.
Same-task rejection remains the positive discriminator for the existing guard.

## Oracle and scope

These selectors reuse 9 case executions (8 distinct IDs) from the original 54
vectors unchanged. They introduce no new expected production result. The three
negative controls mutate local reports, not upstream source or a live service.
The 29 physical source mutations are a separate, unchanged executable catalog.
The actually executed precommit inputs, expected values, complete native results
and all three negative-control failures are preserved in
`counterexample-observations.json`. They are not substituted for the later clean
exact-commit normal/repeat/optimized replay required before publication.
All five guarantee axes stay independent. Real ZK verification, working
attestation, production policy authenticity, action authorization and order
execution remain unestablished.
