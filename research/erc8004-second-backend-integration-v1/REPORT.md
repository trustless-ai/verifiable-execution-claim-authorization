# ERC-8004 second-backend integration v1: executed candidate

**READY_FOR_INDEPENDENT_REVIEW (local candidate). ERC8404_CORE_UNCHANGED: PASS.**
Production **HOLD**. Candidate GitHub Actions: **NOT_RUN**; no branch publication,
PR, remote status change, remote merge or deployment was performed in this task.

## Source and integration

Repository: `trustless-ai/verifiable-execution-claim-authorization`.
Branch: `review/erc8004-second-backend-integration-v1`.

| Identity | Exact SHA |
| --- | --- |
| Verified PR15 merge / canonical main | `29155372c6a16f23d1bc2091f2f3671c51e0da4c` |
| Preserved second-backend pilot | `1ce2b4e0f3e83faf1a16d5ced0507aca20e4ba90` |
| Actual merge of both parents, no conflicts | `0d426315700d43fa3b88ae19cc04156decdbebe5` |
| Executed source commit | `169fe90d81c94919ccc3eac4c218d69c1c685f8f` |
| Executed Git tree | `dffd7c9b1d7a1e0c724588c5a5a56c3fdf176428` |

PR15 was confirmed merged on 2026-11-20 at 14:24:12 UTC. All 18 main workflow
runs succeeded; exact run URLs and observation time are in `replay/MAIN_CI.json`.
Remote main was checked again at 2026-11-20T17:10:08.359166+00:00
and still matched the pinned merge (`replay/FINAL_REMOTE.json`).
Those runs are main evidence, not evidence that this unpublished candidate ran in
GitHub Actions. Full Git history was used. A genuine two-parent merge imports
exactly the pilot's 19 added files, without importing prior integrations twice.
There were no merge conflicts. The separate source commit adds the integration
contract, routing, tests, CI job and current README explanation.
The contract requires these pinned Git objects to remain available. Preserve the
two-parent merge ancestry when eventually merging; squashing away the pilot
history and deleting its last reachable reference is not a supported migration.
Missing historical objects fail closed rather than establishing a new baseline.

The source was replayed from a clean ordinary clone with its own object store,
created using `git clone --no-hardlinks --no-checkout` and detached checkout.
The final report/evidence commit may change only four named closing artifacts
and their four leaf digests in `artifacts.sha256.json`. All executed source,
configuration, fixtures, policies and test expectations remain the exact bytes
of the executed source commit. The final commit/tree are recorded externally in
`D:/PAVLO HQ/Workspaces/veca-second-backend-integration-v1/CLOSURE.json` to avoid
a self-referential commit identifier; verify them with `git rev-parse HEAD 'HEAD^{tree}'`.

## Preservation and execution locations

All 12,823 unchanged old tracked files match their
Git blobs. The only 14 changed old paths are README, twelve named workflow routing
files, and the aggregate inventory. All 19 pilot files remain byte-identical,
including old reports, archive, original additions seal and source locks.
The previous main README is archived byte-for-byte. Inventory membership is
12,867 entries plus its self-excluded manifest. The new policy digest is
`3440d2e4a250021ce10946735881e8dcdecc0b5fe6c880aa3bae3fbda179d98c`.

The [transition](TRANSITION.json) permits **zero Core changes**. It names exact
new paths and immutable hashes, binds the verifier body with only its own digest
slot normalized, and pins the policy's raw digest in that verifier. Only four
explicit closing report/evidence paths are mutable under the ordinary inventory;
no complete directory is exempted. Git review remains the trust root; arbitrary
replacement of the verifier and all trusted Git identities is outside this check.

Three execution identities are deliberately separate:

1. Current source `169fe90d81c94919ccc3eac4c218d69c1c685f8f`: the new comparison, transition tests,
   original Core adapters and six byte-frozen early/Core workflow families.
2. `build/base15` at main291: the unchanged PR15 documentation guard and controls.
3. `build/base15/build/documentation-replay` at
   `4b6d7ef9aabd23932668711ee1d6cf774d9844d7`: unchanged inherited campaigns.

The final escrow replay uses that same third identity in the additional short
worktree `D:/vca-escrow-1120`; the Windows environment recovery is detailed below.

The historical campaigns below are **new executions at their historical SHA**,
bound to the current source through exact byte checks. They are not old JSON
presented as a new run, nor current-head executions with their SHA relabelled.
Preparation receipts explicitly say preparation does not run campaigns.

New transition tests: 16/16 normal and 16/16 Python -O in the fresh clone, plus
an earlier local 16/16. Old documentation controls: 13/13 normal and -O on their
own baseline. Four additional disposable-copy controls reject a dirty view,
missing file, unauthorized addition and wrong HEAD without resetting the copy;
positive/restored checks pass. Core is never altered by these controls.
The original pilot guard passes at pilot1ce and correctly returns failure at the
composed root. The old documentation guard also correctly refuses the composed
root. These expected old-contract refusals are retained verbatim, not labelled
old-guard PASS. No original guard, manifest, pin or expectation was weakened.

A separate YAML parser/structural comparison confirms 18 inherited workflows:
six byte-identical and twelve with only explicit routing/binding changes, keeping
commands, triggers, tool/action pins and platforms. One new Windows x64 job runs
the current backend comparison. Local execution validates commands on Windows;
candidate hosted execution and Linux/macOS operation of the new wheel lock remain
NOT_RUN/NOT_COVERED.

## Current Solidity/Vyper comparison

Solidity: `erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`.
Vyper: `vyperlang/erc-8004-vyper@661278f72d312a2cef0cbaea32b89d3842996967`,
AGPL-3.0-only. It is a reference-informed port, not established clean-room work.
The original 29-vector profile, expected outcomes, research authorization policy,
operation loop, local EVM and pinned recompute-kit grader are reused unchanged.

Both real backends passed **29/29** in normal/repeat/-O. Exact semantic bytes
agree across backends and modes, SHA-256:
`837dbe977cb3bf66470ffe7ed2b4311e001776bbed95057f3b366d16af25e211`. Per-run laboratory decisions: `{"REFUTED":20,"UNVERIFIABLE":1,"VERIFIED":8}`.
These decisions are not external action credentials.

| Physical Vyper mutant | Verdict in normal and -O | Required killers | Changed field | Changed / unexpected cases |
| --- | --- | --- | --- | --- |
| uri-owner-guard | KILLED | uri_stranger, old_owner_after_transfer | `behavior.operation_status` | 2 / 0 |
| wallet-signature-guard | KILLED | wallet_wrong_signer, wallet_wrong_chain, wallet_wrong_registry | `behavior.operation_status` | 3 / 0 |
| transfer-wallet-clear | KILLED | transfer_clears_wallet | `behavior.state` | 1 / 0 |
| validation-request-owner | KILLED | request_stranger | `behavior.operation_status` | 1 / 0 |
| designated-validator | KILLED | response_stranger | `behavior.operation_status` | 1 / 0 |
| duplicate-request | KILLED | request_duplicate | `behavior.operation_status` | 1 / 0 |

Each mutant changes actual source, recompiles and changes the executed runtime
codehash, preserves specified positive controls, and is followed by byte restoration
and another full 29-case baseline. Normal and optimized mutant projections are
byte-identical. Six unique mutants were executed twice, not twelve unique mutants.
They are separate from the six historical Solidity fuzz mutants. Mutation
completeness and universal backend equivalence are not claimed.

All six source/transport/operation-loop controls pass. Modified, missing or extra
source and an intentionally crashing adapter produce UNVERIFIABLE; unsupported
profile is rejected; the preserved operation loop is checked. A crash is not KILLED.

## Newly executed inherited replay

All required validation entrypoints ultimately completed with exit 0. The first
escrow attempt failed because this audit's output argument selected
`build/inherited/escrow`, outside the unchanged Foundry write permission for
`build/escrow`. Its EVM `vm.writeJson` errors and complete failed command receipts
are preserved. The allowed-path retry passed all 28 escrow validation commands,
but its later negative CI controls could not create a disposable-copy file at a
261-character Windows path while `LongPathsEnabled=0` (read-only registry
observation in `replay/LONG_PATH_DIAGNOSTIC.json`). A fresh short-path worktree at
`D:/vca-escrow-1120`, pinned to the exact same historical `4b6d7ef...` source,
first refused the positive authorization case because this audit's offline
preparation had created the npm manifest without installing its crypto packages.
After executing `npm ci --ignore-scripts --no-audit --no-fund --prefix
build/formal-v1/crypto` with the existing lockfile, an explicit positive preflight
returned VERIFIED. The complete unchanged wrapper then passed at
`build/escrow/ci-ready`.
The complete short tree was compared to its Git blobs; final source and config
bytes are unchanged. No permission, expectation or frozen configuration was
edited. All three earlier failures are recorded as orchestration/environment failures,
not semantic findings or mutation kills.
`replay/INHERITED_DONE.json` retains the failed initial aggregate;
`replay/INHERITED_RESOLVED.json` retains the unsuccessful first retry;
`replay/INHERITED_CLOSURE.json` retains the failed incomplete-setup short run;
`replay/INHERITED_FINAL.json` binds all three failed attempts and the successful
complete short-path replay. The short worktree is another execution location for
the same frozen source, not a different implementation or independent executor.
The two exact old-contract refusals above are separate expected exit-1 controls. Detailed
command receipts record argv, cwd, UTC time, duration, exit and stream hashes.
Raw per-case evidence, positive witnesses, minimized sequences and restoration
results remain in the archive. Counts below are distinct historical populations;
repeats do not add unique cases, mutations or independent reviews.

| Campaign | Actual source location | Observed fields |
| --- | --- | --- |
| claim-integration | historical4b6-newly-executed | `{"mutations":{"CRASHED":0,"KILLED":22,"NOT_APPLIED":0,"SURVIVED":0,"UNVERIFIABLE":0},"passed":true,"scenarios":61}` |
| core-consumer | current | `{"mutations":{"CRASHED":0,"KILLED":16,"NOT_APPLIED":0,"SURVIVED":1,"UNVERIFIABLE":0},"passed":true,"scenarios":45}` |
| escrow | historical4b6-newly-executed | `{"escrow_scenarios":31,"new_mutations":{"CRASHED":0,"KILLED":22,"SURVIVED":0},"passed":true}` |
| formal | current | `{"passed":true}` |
| fuzz | historical4b6-newly-executed | `{"mutations":{"KILLED":6},"passed":true,"unique_case_ids":300}` |
| harness | historical4b6-newly-executed | `{"mutations":{"KILLED":12},"passed":true,"scenario_count":18}` |
| old-preservation | historical4b6-newly-executed | `{"cases":6,"passed":true}` |
| role-v1 | historical4b6-newly-executed | `{"cases":26,"passed":true,"physical_mutations":{"CONTROL_BROKEN":0,"CRASHED":0,"KILLED":7,"MISSING_OUTPUT":0,"NO_OP":0,"RESTORATION_FAILED":0,"SURVIVED":0,"UNVERIFIABLE":0}}` |
| role-v2 | historical4b6-newly-executed | `{"cases":50,"passed":true,"physical_mutations":{"CONTROL_BROKEN":0,"CRASHED":0,"KILLED":5,"MISSING_OUTPUT":0,"NOT_APPLIED":0,"NO_OP":0,"RESTORATION_FAILED":0,"SURVIVED":0,"UNVERIFIABLE":0}}` |
| spec | historical4b6-newly-executed | `{"control_population":"31 unchanged semantic controls + 1 explicit preservation transition control; original 32 on PR13 baseline","deterministic":true,"passed":true}` |
| supplement | historical4b6-newly-executed | `{"isolated_mutation_counts":{"KILLED":4},"passed":true,"reviewer_experiment_counts":{"KILLED":1,"SURVIVED":4},"scenario_count":5}` |
| v0 | current | `{"passed":true}` |
| v0-py313 | current | `{"passed":true}` |
| v2 | current | `{"mutations":{"CRASHED":0,"KILLED":18,"NOT_APPLIED":0,"SURVIVED":2,"UNVERIFIABLE":1},"passed":true}` |
| v2-survivors | current | `{"counts":{"CRASHED":0,"KILLED":2,"NOT_APPLIED":0,"SURVIVED":0,"UNVERIFIABLE":0},"passed":true}` |
| v3 | current | `{"mutations":{"CRASHED":0,"KILLED":14,"NOT_APPLIED":0,"SURVIVED":0,"UNVERIFIABLE":0},"passed":true}` |
| v4 | current | `{"mutations":{"CRASHED":0,"KILLED":44,"NOT_APPLIED":0,"SURVIVED":0,"UNVERIFIABLE":0},"passed":true,"scenarios":54}` |
| v4.1-comparison | historical4b6-newly-executed | `{"cases":57,"passed":true,"reuse":7}` |
| v4.1-mutations | historical4b6-newly-executed | `{"counts":{"CRASHED":0,"KILLED":9,"NOT_APPLIED":0,"SURVIVED":0,"UNVERIFIABLE":0},"mutations":9,"passed":true}` |
| v4.1-mutations-O | historical4b6-newly-executed | `{"counts":{"CRASHED":0,"KILLED":9,"NOT_APPLIED":0,"SURVIVED":0,"UNVERIFIABLE":0},"mutations":9,"passed":true}` |

PR12 uses seeds 8004, 8299 and 8274 with 100 generated cases each, normal/repeat/-O,
six physical Solidity mutants in normal/-O, positive controls, distinguishing and
deletion-1-minimal witnesses, and byte restoration. The original 29-case matrix
still misses those six mutants; generated witnesses detect them. The original
29-case/17-mutant registry pilot and 18-case/12-mutant Core harness are executed
separately. No mutation edits ERC8404 Core.

PR13 retains 31 original semantic controls plus one explicit preservation control
(32 integrated), and 13 transport controls, in normal/repeat/-O. Offline coverage
and drift files are byte-identical across modes; the 51-obligation mapping retains
historical campaign identities and denominators. Simple PASS, unrelated mutations,
missing execution and unsupported independence metadata do not upgrade enforcement.
The historical mapping is `{"ENFORCEMENT_DEMONSTRATED":39,"EXECUTED_AND_MATCHED":12}`. The new Vyper observations
are recorded separately and do not retroactively upgrade this frozen map.

Live drift is a separate public-source observation with timestamps, URLs, HTTP
statuses, raw response bytes and hashes retained. Observed classifications:
`{"UNCHANGED":2,"UPSTREAM_MOVED_CONTENT_UNCHANGED":1}`. Source changes do not update pins,
expected outcomes, historical verdicts or authorization status.

Historical survivors remain visible. In particular v2's 18 KILLED / 2 SURVIVED /
1 UNVERIFIABLE target and its separate two-survivor audit are not combined into a
rewritten original campaign. The original external Core consumer and supplemental
matrix likewise retain their own surviving populations. Replay PASS means the
declared finite checks reproduce; it does not erase their documented limitations.

## ERC8404 Core: bytes and runtime

Executable pin: `9dd36e882dd372f264b77b179130948aa5adcbde`.
Draft pin: `7a9e63a80bce04db53c6550103c1d41eca35f3d1:ERCS/erc-8404.md`.
External Git-object audits compare 4,653 Core-related protected main paths,
75 complete upstream baseline files and 13 vendored files, retaining Git blob IDs
and SHA-256. Complete old-tree preservation also protects baseline material whose
path does not contain `erc8404`. Core interfaces, canonicalization/preimages,
statuses, vectors, expected outcomes, locks and dependency pins are unchanged.

Original Python normal/-O and TypeScript adapters execute from the current source.
The unchanged runtime-binding instrument at the historical execution view observed
36 actual `recompute` calls over 18 harness cases in the pinned
adapter, SHA-256 `03505efc8ee993f118fad2c71f706870d25de0da61a393a1f18f7b310bded235`. Traced and native outputs match
byte-for-byte. This is call observation, not a replacement verifier or fallback.
Final source checks confirm restoration and identical pinned Core in every view.

## Reproduction and evidence

Windows x64: Python 3.12.10, Node 22.15.0, Bun 1.3.14, Rust 1.97.1, Forge 1.7.1;
new Vyper compiler 0.4.3 with the original exact nine-wheel hash lock. Public-source
caches were checked against pins before reuse and build/runtime preparation was
executed anew. No private credentials, public-chain transaction or funds were used.
The host and installed toolchain remain trusted execution dependencies.

From a full-history checkout of the candidate:

```powershell
python -B tools/verify_artifacts.py
python -B tools/second_backend_integration/replay.py prepare
python -B -m unittest discover -s tests/second_backend_integration -v
python -B -O -m unittest discover -s tests/second_backend_integration -v
python -B tools/second_backend_integration/ci.py --out build/review-second-backend
python -B tools/second_backend_integration/replay.py check
python -B tools/erc8404/integrity.py
```

Run inherited commands from their checked workflow-defined locations. The archive
contains `replay/inherited_replay.py`, `replay/recover_escrow.py`,
`replay/recover_escrow_short.py`, `replay/recover_escrow_deps.py`, exact preparation commands and all command
receipts; the root [README](../../README.md) and [integration guide](README.md)
explain portable setup. Mutation campaigns must run sequentially and output paths
must be unused. For escrow, use the unchanged workflow's allowed `build/escrow/`
output subtree, and a short checkout path on Windows; earlier attempts in the
archive are retained as failures, not as recommended commands. No old evidence
is regenerated.

Evidence archive: `7945` entries, `21050580` bytes,
SHA-256 `c2578a9325b853698c091a2c532af8610e171422fd7d8531131e99e584b7aaed`. Its `MANIFEST.json` checks every other entry.
`ARCHIVE_OMISSIONS.json` identifies 1818 generated source snapshots/caches
omitted by exact path and digest; no complete mutated source file is committed.
Raw mutation recipes, executed observations and source/code hashes remain available.
The outer [SHA256.json](../../evidence/erc8004-second-backend-integration-v1/SHA256.json)
binds this report, results and archive. The source audit binds all
12,868 tracked files in the clean current/fresh trees to Git blobs.

## Limits and next step

Executor: this same Codex session on Pavlo's Windows machine. A second execution,
clean checkout and GitHub CI do not establish independent human review or an
independent observer/grader. The Vyper implementation shares the EVM, observation
loop and interpretation layers; passing finite vectors does not prove arbitrary
contract correctness, complete ERC conformance, Reputation/ERC-1271 coverage,
all upstream tests, public-chain authenticity or production authorization.

No product defect was established by this comparison. Deliberately injected
mutants are test controls, not claims of upstream vulnerabilities. Existing
published limitations and non-killed historical populations remain unresolved.
Next: review this exact candidate and its preservation contract; after separate
publication authorization, create a Draft PR and run candidate hosted CI. Keep
production HOLD and preserve all original artifacts.
