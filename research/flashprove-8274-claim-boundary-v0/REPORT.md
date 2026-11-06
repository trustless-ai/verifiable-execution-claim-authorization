# Independent FlashProve claim-boundary experiment

Verdict: **READY_FOR_INDEPENDENT_REVIEW**, scoped to this local research experiment.
Not merge-ready, not canonical-CI-green, not production security or normative ERC
conformance. No push or PR is part of this result.

## Exact sources and method

- VECA base: `999e7047df15585f8ce0629081a1369a4942353f`.
- Branch: `research/flashprove-8274-claim-boundary-v0`.
- Implementation commit: the Git commit containing this report; record with
  `git rev-parse HEAD`. Post-commit fresh-checkout results are supplied in the
  separate final replay package so this report does not hash-reference itself.
- FlashProve: `ea1b613625513a658942af4bc79867d1c77412cd`, public main still at that
  exact SHA on recheck. 26 source/document/test pins verified. Its inner FlashProve
  submodule identity is recorded, not built or represented as a proven SP1 circuit.
- Frozen RVR Core: `9dd36e882dd372f264b77b179130948aa5adcbde`, 13/13 locked files.
- Existing grader/runtime reuse: 8 VECA file pins, unchanged recompute-kit grader
  source lock, npm lock and Hardhat EDR configuration.
- Existing ERC-8274 historical proposal snapshot at
  `JimmyShi22/ERCs@3f014d07a0ceac39fe6fb6dec0efdc30640a9653`; no claim about adoption
  or a newer normative revision. Its existing VECA SHA-256 is preserved.
- Windows 11, Python 3.12.10, Node 22.15.0, Bun 1.3.14, solc 0.8.24,
  Hardhat 3.0.6, ethers 6.15.0. No Linux/macOS execution claimed.

`generate_vectors.py` authored the oracle before the first native execution.
The vector SHA-256 remained
`1fcb2a38223fac1937c57ed3f94fbd03696f54b0128407d030721a04e86deaf1`.
The first run reproduced all 54 cases. Native adapter requests contain only IDs
and inputs, never expected results. Source and result bytes are in the evidence
archive; exact commands and exits are retained. All research Python invocations
disable bytecode writes with `-B`; copies are fresh and mutation modules execute
from distinct temporary source paths.

## Findings established by actual execution

| Observation | Witness and control | Classification / practical limit |
|---|---|---|
| Different committees with the same threshold yield identical attestation `proofProfile()` | `configuration_profile_collision`: committee arrays differ; profile equal. Changing threshold changes profile. | Configuration-identity design gap. Counterexample to the source comment that committee rotation alone gives a distinct profile; not a SHA/Keccak collision. Storage keys are absent from the runtime code hash. |
| Supplied authorized agentId is accepted from a different caller | `caller_impersonates_agent` has inner/outer true; local caller policy refuses | Application-boundary hazard if outer validity is read as caller authentication. Permissionless verification can be intentional; not by itself a production exploit. |
| Same proof is accepted for a fresh task, another verifier instance, and another simulated chain | `repeat_same_task` gives true/false; `reuse_proof_fresh_task` true/true; other-contract/chain true | Task/context policy gap for stronger consumers. ERC-8274 does not promise universal proof replay prevention. All positive ZK calls use MockSP1. |
| Attestation digest is equal across chain IDs at the same address; differs for another contract | `attestation_digest_domains` has true/false, with actual chain IDs 31337/31338 and addresses recorded | Unsettled domain design. Signature recovery is TODO, so no presently accepted cross-chain attestation exploit is established. |
| Outer profile is identical for different commitment/verdict/status/agent policies with the same verifier and metadata | `configuration_profile_collision` records equal outer profiles | A consumer must not assume this profile authenticates all application configuration. The formula follows the inspected interface snapshot. |
| Signature bundles never produce a positive attestation on the pinned source | Empty, malformed, outsider, duplicate, and two locally signed EIP-191 illustrative bundles all return false | Unimplemented feature, not demonstrated signature rejection. No upstream signature bundle format is settled. |
| Two keys do not establish two operators; revocation is not furnished by the contract | Explicit one-operator/revoked/unknown-signer policy fixtures refuse | Independently selected laboratory assumptions only; no real-world ownership or revocation authenticity established. |
| Inner digest checks and outer commitment/verdict/status/task checks are load-bearing | Ten physical Solidity mutations have exact witnesses and healthy controls | Finite local implementation evidence; neither full formal verification nor actual SP1 cryptography. |

Malformed metadata tests deliberately distinguish a direct inner call from the
outer call's own stored metadata: inner false and outer true is the correct
expected result for those inputs. No field is silently normalized into a verdict.

## Guarantee boundary

The five named guarantees are separate machine-readable fields. `ZK_PROOF_VERIFIED`
and `ATTESTATION_ACCEPTED` are UNVERIFIABLE throughout this bounded experiment.
`CLAIM_AUTHORIZED` is REFUTED when an explicit laboratory policy relation is
contradicted; otherwise it is UNVERIFIABLE because the required proof/trust has
not been established. `ACTION_AUTHORIZED` and `ORDER_EXECUTED` remain UNVERIFIABLE.
Native true is retained as evidence but issues no authorization credential.

The EIP-191 signatures used for committee probes are genuine local signatures,
but that illustrative encoding is NOT claimed to be the upstream attestation
protocol. A successful two-signature local recovery does not stand in for an
accepted upstream attestation, independent operators, or a ZK proof.

## Executed gates

| Gate | Result |
|---|---|
| New corpus normal / repeat / Python -O | 54/54 each |
| New transport/expectation/empty/output/exception tests | 15/15 each mode |
| New physical mutation sweep normal / -O | 29 KILLED, 0 SURVIVED, 0 CRASHED, 0 NOT_APPLIED each |
| Classifier sentinels | 6/6 distinct non-kill classifications each mode |
| Existing RVR composition | 45 cases; 17 tests normal/repeat/-O; 16 KILLED / 1 historical SURVIVED preserved |
| Existing harness | 18 cases; 12 KILLED |
| Existing ERC-8004 pilot | 29 cases; 17 KILLED |
| Existing role policy v1 | 26 cases; 18 controls normal/-O; 7 KILLED |
| Existing role policy v2 | 50 cases; 36 controls normal/-O; 5 KILLED |
| Candidate unchanged regression invocation set | 19/19 commands exit 0; test groups 13, 5, 18, 36, 16 in normal/-O |
| Old Core / old root inventory entries | 13/13 / 12,739/12,739 exact bytes preserved |
| Root canonical inventory on candidate | **FAIL (exit 1)**, solely new research additions; old manifest deliberately unchanged |
| GitHub CI for this unpublished branch | NOT RUN |

Full adapter stdout, detached request and projected result are byte-identical
across the three new conformance modes. The four unchanged native suite outputs
and projections are byte-identical between baseline and candidate. Unit-test
duration logs and command paths are not claimed byte-identical. The normal/-O
mutation result JSONs compare equal. See `evidence/results.json` for full digests.

An initial optimized mutation invocation redundantly propagated `-O` twice
(effective `-OO` in child processes); it also passed. That attempt is preserved
as `candidate/mutations-optimized/`. The dispatcher was corrected and the exact
single-`-O` replay rerun in `mutations-optimized-final/`. It is the latter that
supports the optimized claim. No oracle or upstream source changed to pass it.

## Complete conformance matrix

| Case | Native inner / outer | Consumer reason | Graded |
|---|---|---|---|
| `zk_mock_positive` | True / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `missing_policy` | True / True | `POLICY_NOT_ESTABLISHED` | PASS |
| `unknown_policy` | True / True | `POLICY_NOT_ESTABLISHED` | PASS |
| `wrong_route_claim` | True / True | `ROUTE_MISMATCH` | PASS |
| `wrong_chain_claim` | True / True | `CHAIN_MISMATCH` | PASS |
| `wrong_contract_claim` | True / True | `CONTRACT_MISMATCH` | PASS |
| `wrong_agent_claim` | True / True | `AGENT_MISMATCH` | PASS |
| `wrong_task_claim` | True / True | `TASK_MISMATCH` | PASS |
| `wrong_input_claim` | True / True | `INPUT_MISMATCH` | PASS |
| `wrong_output_claim` | True / True | `OUTPUT_MISMATCH` | PASS |
| `wrong_input_call` | False / False | `INPUT_MISMATCH` | PASS |
| `wrong_output_call` | False / False | `OUTPUT_MISMATCH` | PASS |
| `wrong_commitment` | True / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `unaccepted_verdict` | True / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `failed_call_status` | True / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `wrong_inner_metadata` | False / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `short_inner_metadata` | False / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `zk_proof_empty` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `zk_proof_bad` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `zk_proof_malformed` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `public_values_magic` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `public_values_version` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `public_values_reserved` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `public_values_short` | False / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `unknown_native_agent` | True / False | `AGENT_MISMATCH` | PASS |
| `caller_impersonates_agent` | True / True | `CALLER_NOT_AGENT` | PASS |
| `substitute_task` | True / True | `TASK_MISMATCH` | PASS |
| `repeat_same_task` | True / False | `LAB_NATIVE_CALL_REJECTED` | PASS |
| `reuse_proof_fresh_task` | True / True | `TASK_MISMATCH` | PASS |
| `reuse_proof_other_contract` | True / True | `CONTRACT_MISMATCH` | PASS |
| `reuse_proof_other_chain` | True / True | `CHAIN_MISMATCH` | PASS |
| `no_promotion_zk_proof_verified` | True / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `no_promotion_attestation_accepted` | True / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `no_promotion_claim_authorized` | True / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `no_promotion_action_authorized` | True / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `no_promotion_order_executed` | True / True | `MOCK_SP1_NOT_CRYPTOGRAPHIC_EVIDENCE` | PASS |
| `attestation_no_signatures` | False / False | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `attestation_invalid_bundle` | False / False | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `attestation_illustrative_two_signatures` | False / False | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `attestation_repeated_signature` | False / False | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `attestation_outsider_signatures` | False / False | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `attestation_two_keys_one_operator` | False / False | `OPERATOR_THRESHOLD_NOT_ESTABLISHED` | PASS |
| `attestation_revoked_assumption` | False / False | `SIGNER_REVOKED_BY_LAB_POLICY` | PASS |
| `attestation_untrusted_signer_assumption` | False / False | `SIGNER_NOT_ADMITTED_BY_LAB_POLICY` | PASS |
| `attestation_wrong_committee` | False / False | `COMMITTEE_MISMATCH` | PASS |
| `attestation_is_not_zk` | False / False | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `committee_valid` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `committee_empty` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `committee_zero-threshold` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `committee_high-threshold` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `committee_duplicate` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `committee_zero-signer` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `configuration_profile_collision` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |
| `attestation_digest_domains` | None / None | `ATTESTATION_SIGNATURE_VERIFICATION_UNIMPLEMENTED` | PASS |

## Limits and review obligations

No real SP1 verifier/proof, working attestation verifier, authenticated production
policy, actual operator independence, public chain finality, action execution,
order fulfillment, production exploit, confidential client input or independent
reviewer acceptance is established. No formal proof or full mutation coverage is
claimed. Only the finite catalog was tested. The historical RVR survivor remains
a survivor. Frozen source, expectations and historical evidence were not changed.

The new directory needs a separately authorized inventory/CI integration change
before merge. Existing complete-inventory semantics have not been weakened.
See INTEGRATION_PLAN.md; PR #12/#13 and their source branches remain untouched.
