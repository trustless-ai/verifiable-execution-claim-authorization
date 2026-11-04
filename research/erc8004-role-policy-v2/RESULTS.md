# Executed results: agentWallet role policy v2

Starting reviewed source: `4799a7260d8f99e489541cffe471e53c50411459`.
Evidence source: author-operated Windows execution on the source candidate and
isolated composition with PR #11. Exact candidate file hashes and parent refs are
in [SUMMARY.json](../../evidence/erc8004-role-policy-v2/SUMMARY.json).

## Before and after

A valid EIP-712 signature from validator `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`
was used by the owner to call the actual pinned `setAgentWallet` before requesting
validation. The contract accepted the update and `getAgentWallet` at the request
block equaled the validator. Unchanged v1 returned `VERIFIED /
REQUEST_TIME_ROLE_SEPARATION`. Separate v2 returns `UNVERIFIABLE /
SELF_ATTESTED_AGENT_WALLET` on the same recorded execution. Positive separate-validator
and owner-self controls remain correct. No defect in the upstream ERC is claimed.

Pinned contract commit: `b9e466c250744a7e06b13dff9d3c2844ed64f825`.
IdentityRegistryUpgradeable SHA256:
`18c8ca8c88493b46e54d000c96eaf7470d1f9dbfe55493fd7fa923bae543ff75`.
Raw evidence includes typed-data domain/value/signature, recovered signer, transaction,
receipt, pre/post wallet values, four ABI call records at each receipt block,
compiler-input hash and deployed implementation code hashes.

| Separate population | Source candidate | Composition with #11 |
| --- | --- | --- |
| Original ERC-8004 v0 | 29/29, normal/repeat/-O | 29/29, normal/repeat/-O |
| Original v0 physical mutations | 17/17 normal and -O | 17/17 normal and -O |
| Historical role policy v1 | 26/26, normal/repeat/-O | 26/26, normal/repeat/-O |
| V1 physical mutations | 7/7 normal and -O | 7/7 normal and -O |
| New role policy v2 | 50/50 distinct inputs, normal/repeat/-O | 50/50, normal/repeat/-O |
| New v2 physical mutations | 5/5 normal and -O | 5/5 normal and -O |
| New unit/control methods | 36/36 normal and -O | 36/36 normal and -O |
| Frozen ERC-8404 harness | 18/18 in legacy regression | 18/18 normal/repeat/-O; separate 12/12 mutants in both modes |
| PR #11 supplemental profile | Present on the composed base | 5/5 including positive + four witnesses; separate 4/4 mutants in both modes |

V1 infrastructure controls remain 18/18 per mode. Existing baseline reconciliation
controls pass 16/16 normal and -O. PR #11's historical five-probe comparison stays
**1 KILLED / 4 SURVIVED**, separate from its four new distinguishing witnesses.
These populations are not combined into one mutation denominator.

V2 authorizations: {'REFUTED': 19, 'UNVERIFIABLE': 22, 'VERIFIED': 9}. Every declared expectation matches;
registry execution success is separate from downstream research-policy authorization.
The 50 cases comprise 22 operation configurations, six claim-admission controls and
22 evidence-fault controls. All cases execute pinned contracts, but repeated EVM
setups for evidence faults are not claimed as 50 distinct contract transitions.
All five physical mutants are KILLED with healthy positives, identical requests,
byte-exact source restoration and complete raw-observation restoration. SURVIVED,
CRASHED, NO_OP, NOT_APPLIED, MISSING_OUTPUT, CONTROL_BROKEN, RESTORATION_FAILED
and UNVERIFIABLE are each zero in the final campaigns.

V2 complete behavioral SHA256: `2c16d8ef34c1c12874f75b378f8a66470138e01cf8d374603517698258292a22`.
V2 complete adapter-observation SHA256: `57bc6824cddf695fd44c4afa85b4b4a217ccefc2038c286f7fe4f907a5a9cce9`.
Both hashes match normal/repeat/-O and source/composed executions. Original v0 and
v1 complete behavioral digests remain `837dbe977cb3bf66470ffe7ed2b4311e001776bbed95057f3b366d16af25e211` and
`0ed522131509603602adbb90d8c6111a3347d8b5c19ce90d75440c67953a7617`. The original ERC-8404 and PR #11 digests remain
`1c12db717dc43d6b9568b902089cde8906e53951aa2ccf22e4b04404620a106b` and `aa134ea900784fbb4f69d972babafa1b579b64e16771de554f906ef47dd909cc`.

All 12,703 files inventoried at the reviewed source HEAD remain byte-identical on
the source branch. The composed tree retains the existing exact two-document #11
transition and all 13 frozen supplemental payload files; its remaining 12,701
reviewed-source files are identical. The old reconciliation policy is unchanged.
Historical source locks, v0/v1 fixtures, reports, archives, ERC-8404 six-field Core,
harness transport and pinned recompute-kit grader remain unchanged.

Runtime: Python 3.12.10, Node v22.15.0, Windows-11-10.0.26200-SP0.
Archive SHA256: `895e33b38a325e78860540c91e442383a86fb0f8d91f6df73fa5aa4fdfaa4c76`; 4123 members,
8984094 bytes. See [member hashes](../../evidence/erc8004-role-policy-v2/SHA256.json).

A preliminary mutation run ended with exit 1 because its preservation guard detected
an author edit to the source during development. Its five intermediate semantic
records are not final closure evidence. It is retained separately with an explanation;
all reported final campaigns started after code freeze and completed successfully.
The later completed pre-classifier-refinement run is retained separately as well:
incomplete behavior is now classified MISSING_OUTPUT instead of SURVIVED. Neither
classification is a kill. Final source validation was fully rerun after this change.

Recommendation: **READY_FOR_INDEPENDENT_REVIEW** for this finite v2 candidate.
Fresh committed-checkout and Linux CI results are recorded after commit separately
on the PR and in publication evidence. No new independent review, macOS replay,
ERC-1271 campaign, organizational independence, public-chain authentication,
judgment truth, production authorization or universal compliance is established.
PR #10 stays Draft; main, #12 and #13 remain outside this change.
