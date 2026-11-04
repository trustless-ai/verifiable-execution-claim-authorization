# Request-time validator role separation v1

This additive research policy implements the bounded proposal in [the PR #10 review comment](https://github.com/trustless-ai/verifiable-execution-claim-authorization/pull/10#issuecomment-6377253151).
It does not change ERC-8004, its pinned implementation, the original observation policy,
the harness protocol or the recompute-kit grader.

Historical base: `80c91a09095eca362dbfb69d39d0c01fc31130cf`.
Contract implementation: `erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`.
ERC draft: `ethereum/ERCs@503591a6e80e6e1affdd6403341e25269141f046`.
The [original source lock](../../conformance/erc8004-pilot-v0/source-lock.json) and dependency lock are reused unchanged.

## Separate claim and policy

| Field | Historical profile | Additive profile |
| --- | --- | --- |
| Policy | `erc8004-registry-observation-v0` | `erc8004-validator-role-separation-v1` |
| Claim | `LAB_REGISTRY_TRANSITION` | `LAB_VALIDATOR_ROLE_SEPARATION` |
| Meaning of VERIFIED | This transition was accepted in the local EVM | Successful response plus no observed owner/operator/token-approval overlap at its request block |
| Self-response | May verify the narrow transition | UNVERIFIABLE for role separation |

All new R1-R8 obligations are explicitly **RESEARCH_POLICY**, not additional ERC requirements.
The v1 adapter calls the original v0 admission/execution function with a translated internal claim,
then applies the new policy. Its returned scope names the new claim and exact version and commits
to the complete operation input. Unknown fields and wrong subject/domain still fail through the
unchanged historical checks. No production authorization credential is issued.

At the mined validation-request block, capture `ownerOf(agentId)`,
`isApprovedForAll(owner, validator)` and `getApproved(agentId)` using explicit historical block tags.
The validator must differ from the owner and token-approved address, and global approval must be false.
Known overlap yields `UNVERIFIABLE` with a specific self-attestation reason.
Missing evidence and malformed evidence have distinct reasons, also UNVERIFIABLE.
Contradictory request/subject/validator/block binding yields REFUTED.
A reverted response cannot establish this claim. A designated validator's repeated response is permitted.

Roles changing after the request do not change this deliberately request-time claim. A validator
becoming owner or operator later can still meet it; that does not assert response-time separation.
A correct policy refusal can be conformance PASS. Contract acceptance and policy admission remain separate.

Different keys do **not** establish independent people, organizations, controllers or absence of collusion.
Task execution, response truth, public-chain deployment, payment permission and production authorization
remain NOT_COVERED. Runtime and local adapter execution are trusted laboratory assumptions.

## Reuse architecture

The EVM launcher checks the SHA256 of historical `tools/erc8004/evm.mjs`, retains its compiler,
deployment, local EDR setup, snapshots, transaction/receipt capture and runtime output, and substitutes
only the scenario loop from `scenarios.mjs`. A data-URL module runs that composed local source;
it performs no network fetch. The root-path substitution only preserves the original runtime location.
This is a scenario extension of the pinned runner, not another verification engine. Neither that runner
nor any Solidity or historical evidence is edited. Source composition fails closed on upstream drift.

All expected results are declared by `build_vectors.py`, which imports neither the adapter nor its
observations. The existing harness sends only case IDs and inputs to the implementation. Raw receipts,
request-time and response-time role snapshots are retained. Six evidence controls deliberately withhold
or corrupt the policy's observation copy; the original execution is preserved separately in each result.
Those controls are not claims of defects in the registry.

## Finite coverage

The 26-case catalog comprises 12 EVM transition/role scenarios, eight claim-admission controls and six
evidence controls. Each executes actual pinned contracts. The owner, globally approved operator and
token-approved operator each have an isolated self-attestation witness. Separate-validator and repeated
response cases are positive controls. Role-revocation/transfer cases distinguish request-time from
response-time evaluation.

Seven physical mutations remove owner, global-operator, token-approved, request-binding, version and
claim guards, or substitute response-time roles. Each runs the same inputs against the original policy,
the physically altered policy and byte-restored policy in the real local EVM. A kill requires a
distinguishing false VERIFIED result, passing positive control, identical requests, byte restoration and
restored behavior. Crashes, no-ops, missing output and broken controls cannot count as kills.
The 18 infrastructure test methods include separate classifier controls; they are not extra physical mutants.

Historical **29 scenarios / 17 mutants** and new **26 cases / 7 mutants** are separate populations.
Do not combine their totals or relabel old evidence. The new preservation checker verifies every
historical inventory entry and file. Root inventory changes may only add new paths; original entries
retain their exact digests. The historical inventory itself remains available at the exact base Git object.

## Reproduce

Use Python 3.12+ and pinned Node 22.15.0. Prepare the unchanged dependencies from the repository root:

```sh
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B research/formal-v1/prepare_crypto.py
npm ci --ignore-scripts --no-audit --no-fund --prefix build/formal-v1/crypto
python -B tools/erc8004/validate.py --out build/role-policy-v1/legacy
python -B -O tools/erc8004/mutations.py --out build/role-policy-v1/legacy-mutations-optimized
python -B tools/erc8004_role_policy/validate.py
python -B tools/verify_artifacts.py
git diff --check
```

Preparation downloads only pinned public sources and npm dependencies; executions use no external RPC,
credentials or production keys. Once prepared, execution is offline. The new validator runs normal,
repeat and Python -O cases, normal/-O tests and physical mutations, and before/after preservation checks.
Python -O is not a second EVM implementation. Raw command receipts and results go to ignored `build/`.
Run the legacy validator sequentially with other campaigns sharing this checkout: its negative
infrastructure controls deliberately remove/change a cached Solidity file and restore it in `finally`.
For parallel runs, use separately prepared isolated checkouts.

The dedicated workflow checks the exact source head (including on pull_request), while inherited
workflows retain their original behavior. A passing source-head run does not establish correctness of
a future merge tree containing #11. No rebase, merge or later-stack integration is part of this change.
PR #10 stays Draft. New independent reviewer acceptance is NOT_COVERED.
