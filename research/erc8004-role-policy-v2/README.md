# ERC-8004 request-block agentWallet role separation v2

Policy: `erc8004-validator-role-separation-v2`.
Claim: `LAB_VALIDATOR_ROLE_SEPARATION`. This is a finite downstream research policy,
not a normative addition to ERC-8004 or an authorization credential.

This version responds to [Echo's review of 4799a726](https://github.com/trustless-ai/verifiable-execution-claim-authorization/pull/10#issuecomment-6382807754).
The reviewed v1 checks owner, global operator and token approval. Its scope did not
include agentWallet. The actual pinned contract permits an authorized caller to set
agentWallet using a valid new-wallet signature. The unchanged v1 then admits a
validator that equals this fourth registry role. This is a v1 coverage boundary,
not a demonstrated ERC-8004 vulnerability. Historical v0/v1 outcomes stay frozen.

## Exact scope and capture

The unchanged v0 local Hardhat EDR compiler/deployment/transaction helpers execute
`erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`.
The [source lock](../../conformance/erc8004-role-policy-v2/source-lock.json) reuses
the original implementation, normative and grader locks, and pins the new scenario
composition. No Solidity source, ERC draft or existing policy is changed.

At the successful validation-request receipt block, v2 executes four separate calls:

| Role | Exact call | Selector |
| --- | --- | --- |
| Owner | `ownerOf(agentId)` | `0x6352211e` |
| Global operator | `isApprovedForAll(owner, validator)` | `0xe985e9c5` |
| Token approval | `getApproved(agentId)` | `0x081812fc` |
| Agent wallet | `getAgentWallet(agentId)` | `0x00339509` |

The raw `eth_call` inputs/results, fixed block tag and independently queried local
block hash are preserved. Policy checks bind each call to the deployed Identity
Registry address, agent, validator, chain, request and request receipt block, then
compare exact ABI-encoded results with the role snapshot. The response block has a
separate capture for temporal controls; it cannot replace request-time roles.
`wallet_becomes_validator_after` remains `VERIFIED` when the validator signs an EIP-712 update to become `agentWallet` between request and response, because v2 checks request-time roles only and does not evaluate that later role change as a possible collusion signal.
These are observations from the trusted local EVM and adapter. A proof from an
untrusted remote RPC is not authenticated by this format or a `capture` label.

Existing owner/operator/token-approved refusals retain their v1 precedence and
reason. A validator equal to the established request-time wallet yields
`UNVERIFIABLE / SELF_ATTESTED_AGENT_WALLET`. Missing or malformed wallet/call
evidence yields distinct `MISSING_*` / `MALFORMED_*` reasons; unverified capture
yields `UNVERIFIED_ROLE_CALLS`. Binding contradictions yield `REFUTED`.
An established zero wallet after transfer is an empty role, not missing evidence.
Different addresses establish only absence of the four checked registry overlaps.
They do not establish independent human or organizational control.

The machine interface remains `agent-harness.request.v0` /
`agent-harness.observation.v0`; the policy version and
[role evidence schema](../../conformance/erc8004-role-policy-v2/role-evidence.schema.json)
are separate. Complete behavior includes policy reason, wallet-update status and
request/response wallets, as well as registry response behavior. A conformant refusal
is a test PASS even when its policy authorization is UNVERIFIABLE or REFUTED.

## Witnesses and physical controls

The declared expectation generator imports only standard serialization/path/hash
modules. It does not import the policy or inspect execution observations. The
existing harness strips vectors to case ID and input before invoking the adapter;
the backend never receives expected results or the obligation catalog.

Fifty distinct inputs cover four-role separation, each overlap, authorized wallet
updates by owner/operator/token-approved address, valid and invalid EIP-712 EOA
signatures, changes before/after the request, transfer clearing, and evidence faults.
`V2-SIGNATURE` and `V2-TRANSFER` identify pinned implementation behavior. Other
obligations are explicitly research-policy choices, not invented normative clauses.
Evidence faults are applied to copies of actual observations. Raw EVM execution
remains preserved and is not labeled a registry defect.

Five physical source edits remove the wallet comparison, substitute response-time
wallet, omit wallet-call binding, accept a missing wallet, or accept contradictory
call evidence. Each runs a distinguishing witness plus a separate positive control
on actual EVM baseline/mutant/restored executions. Only a complete incorrect
VERIFIED result with healthy controls is a semantic KILLED. SURVIVED, CRASHED,
NO_OP, NOT_APPLIED, MISSING_OUTPUT, CONTROL_BROKEN, RESTORATION_FAILED and
UNVERIFIABLE are recorded separately. Original v0 17 and v1 7 mutants are separate
populations; there is no combined denominator.

## Replay

Requirements: Git history through the source pins, Python 3.12 and Node 22.15.0.
Preparation uses GitHub and npm for pinned dependencies; execution uses local EDR
only, with no credentials, provider, QPU job or public-chain call.

```sh
python -B tools/verify_artifacts.py
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B research/formal-v1/prepare_crypto.py
npm ci --ignore-scripts --no-audit --no-fund --prefix build/formal-v1/crypto
python -B tools/erc8004/validate.py --out build/role-policy-v2/legacy
python -B -O tools/erc8004/mutations.py --out build/role-policy-v2/legacy-optimized
python -B tools/erc8004_role_policy/validate.py --out build/role-policy-v2/v1
python -B tools/erc8004_role_policy_v2/validate.py --out build/role-policy-v2/validation
python -B -m unittest discover -s tests/baseline_reconciliation -v
python -B -O -m unittest discover -s tests/baseline_reconciliation -v
python -B tools/verify_artifacts.py
```

Use `npm.cmd` in PowerShell if necessary. Do not run legacy negative-infrastructure
tests concurrently with EVM campaigns in the same checkout: those tests temporarily
remove a cached Solidity source and restore it. Run suites sequentially.

On the composed PR tree containing #11, additionally run:

```sh
python -B tools/harness_v0/validate.py --out build/role-policy-v2/harness
python -B -O tools/harness_v0/mutations.py --out build/role-policy-v2/harness-optimized
python -B tools/harness_v0/review_validate.py --out build/role-policy-v2/pr11
```

PR #11 retains its five cases (positive plus four coverage witnesses), four physical
mutants and separate historical five-probe comparison. The existing versioned
baseline reconciliation is reused unchanged. Source branch and composed PR tree
are different identities and must be recorded separately.

## Limitations and review

No independent controller, judgment truth, production authorization, remote-chain
authentication, universal ERC conformance or additional ERC-1271 campaign is claimed.
The EIP-712 path supplies the valid-signature reproduction requested here. The
original six-field ERC-8404 Core, old source locks, reports and archives stay frozen.
A fresh author checkout is reproducibility evidence, not independent review.

Review the final commit, all four ABI bindings, temporal witnesses, mutation
baseline/positive/restored evidence, inventory transitions and separate historical
digests. PR #10 remains Draft pending a new independent review. No merge is part
of this work. See [executed results](RESULTS.md) and the versioned evidence directory.
