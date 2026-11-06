# Review finalization v1 addendum

The original 29-entry physical catalog and 6 non-kill classifiers remain byte-identical.
The finalization replay runs all of them normally, repeatedly and with Python -O
from a clean exact-commit checkout. `review_v1/replay.py` refuses publication-grade
success if any count, result, restoration or deterministic comparison differs.
The separate inventory and counterexample controls are not added to the 29 kills.

The original executed mutation report below remains historical evidence. Current
run commands, actual exits, old/new predicates, healthy controls and deterministic
results are retained in the new replay directory and deterministic archive.

---

# Physical mutation report

29 primary mutants: 19 consumer-policy mutations and 10 upstream-Solidity
predicate mutations. Normal and exact single-`-O` runs both report 29 KILLED,
0 SURVIVED, 0 CRASHED, 0 NOT_APPLIED. Finite catalog only, not coverage completeness.

Each replacement occurred exactly once. Every baseline was green. Each kill
has adapter exit 0, grader exit 1, its named differing witness and a healthy named
positive control. Source hashes and exact old/new predicates are recorded in
`evidence/mutation-results.json`. Upstream Solidity mutations were compiled and
run in EDR. Consumer mutations physically changed a disposable policy module and
replayed the complete hash-recorded native EVM evidence through that module and
the unchanged VECA grader. This distinction is explicit per mutation.

Some consumer removals change the asserted reason without changing the final
REFUTED/UNVERIFIABLE axis; some native removals change an inner/outer result while
the stricter consumer still refuses. The complete projected result asserts these
fields. These are semantic observation differences, not necessarily an issued
authorization. No crash is used as a distinguishing witness.

| Mutant | Witness | Healthy control | Result |
|---|---|---|---|
| `consumer-policy` | `missing_policy` | `zk_mock_positive` | KILLED |
| `consumer-route` | `wrong_route_claim` | `zk_mock_positive` | KILLED |
| `consumer-chain` | `reuse_proof_other_chain` | `zk_mock_positive` | KILLED |
| `consumer-contract` | `reuse_proof_other_contract` | `zk_mock_positive` | KILLED |
| `consumer-agent` | `unknown_native_agent` | `zk_mock_positive` | KILLED |
| `consumer-caller` | `caller_impersonates_agent` | `zk_mock_positive` | KILLED |
| `consumer-task` | `reuse_proof_fresh_task` | `zk_mock_positive` | KILLED |
| `consumer-input` | `wrong_input_claim` | `zk_mock_positive` | KILLED |
| `consumer-output` | `wrong_output_claim` | `zk_mock_positive` | KILLED |
| `consumer-committee` | `attestation_wrong_committee` | `zk_mock_positive` | KILLED |
| `consumer-operators` | `attestation_two_keys_one_operator` | `zk_mock_positive` | KILLED |
| `consumer-revocation` | `attestation_revoked_assumption` | `zk_mock_positive` | KILLED |
| `consumer-signer-admission` | `attestation_untrusted_signer_assumption` | `zk_mock_positive` | KILLED |
| `mock-as-zk` | `zk_mock_positive` | `attestation_no_signatures` | KILLED |
| `signatures-as-attestation` | `attestation_illustrative_two_signatures` | `zk_mock_positive` | KILLED |
| `attestation-as-zk` | `attestation_is_not_zk` | `zk_mock_positive` | KILLED |
| `proof-as-claim` | `zk_mock_positive` | `attestation_no_signatures` | KILLED |
| `proof-as-action_authorized` | `zk_mock_positive` | `attestation_no_signatures` | KILLED |
| `proof-as-order_executed` | `zk_mock_positive` | `attestation_no_signatures` | KILLED |
| `native-input` | `wrong_input_call` | `zk_mock_positive` | KILLED |
| `native-output` | `wrong_output_call` | `zk_mock_positive` | KILLED |
| `native-commitment` | `wrong_commitment` | `zk_mock_positive` | KILLED |
| `native-verdict` | `unaccepted_verdict` | `zk_mock_positive` | KILLED |
| `native-call-status` | `failed_call_status` | `zk_mock_positive` | KILLED |
| `native-single-use` | `repeat_same_task` | `zk_mock_positive` | KILLED |
| `native-agent-allowlist` | `unknown_native_agent` | `zk_mock_positive` | KILLED |
| `native-duplicate-committee` | `committee_duplicate` | `zk_mock_positive` | KILLED |
| `native-zero-signer` | `committee_zero-signer` | `zk_mock_positive` | KILLED |
| `native-signature-todo-bypass` | `attestation_illustrative_two_signatures` | `zk_mock_positive` | KILLED |

Six separately executed classifier controls produce CRASHED, MISSING_OUTPUT,
NOT_APPLIED, NO_OP, SURVIVED and CONTROL_BROKEN. They are deliberately not primary
mutant kills. In particular, empty stdout and a broken baseline cannot manufacture
coverage. A missing replacement returns NOT_APPLIED; identical bytes return NO_OP.

Working consumer/oracle files and all 26 source-cache pins were verified after
the sweeps. Original FlashProve files and VECA historical evidence were never
mutation targets. Native mutations were only in deleted disposable copies.
The `return 999` counter mutant is an explicitly unsafe counterfactual; its kill
does not establish working signature verification in the actual `return 0` source.

Exact commands are in README.md and the raw evidence archive. The separate
historical ERC-8404 catalog still reports 16 KILLED / 1 SURVIVED; no old result is
rewritten or included in the new 29 count.
