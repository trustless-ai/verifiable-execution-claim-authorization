# PR12 / PR13 integration v1: executed review candidate

Verdict: **READY_FOR_INDEPENDENT_REVIEW**. **ERC8404_CORE_UNCHANGED: PASS**.
Production remains **HOLD**. This is a local integration candidate, not a deployment,
an authorization credential, universal ERC conformance, or an independent human audit.

## Source identity and integration

Repository: `https://github.com/trustless-ai/verifiable-execution-claim-authorization`.
Local branch: `review/veca-pr12-pr13-integration-v1`.

| Role | Exact commit |
| --- | --- |
| Verified main | `999e7047df15585f8ce0629081a1369a4942353f` |
| PR12's original base | `80c91a09095eca362dbfb69d39d0c01fc31130cf` |
| PR12 | `6e8fabee9be170245f557a271b6d315176cc4a03` |
| PR13 | `c0d3862a590b62a059c1a923ab93b380d609876f` |
| Merge PR12 into main | `e381642352f795ff0ed80ffc8ca0e5b368c5f65e` |
| Merge PR13 | `f00757bc17f5d35d203f00639a1d20b01f1ed438` |
| Executed integration source candidate | `5ebabe818173ffdb87dd9018d60c43ed77002c1a` |
| Executed candidate Git tree | `9960cb23dd78b0202ae5c370f8713eb76b35e413` |

Live refs matched the supplied checkpoints at preflight. `REMOTE_CLOSURE.json`
records the final read-only observation. Full VECA history is available. A new
task-owned Git store and worktrees were used; pre-existing worktrees were not reset.
Main already contains #9/#10 and the #11 supplement. PR12 is additive on 80c91a0;
PR13 is additive on PR12. Two actual merge commits retain this ancestry rather
than copying the already-integrated base again.

Both merges conflicted only in `artifacts.sha256.json`: independently added
inventory entries were reconciled by exact, disjoint union. No blanket ours/theirs
resolution was used. Main's 12,739 inventory entries remained byte-identical;
PR12 contributes 36 paths and PR13 contributes 38. The external integration adds
14 explicitly named files. Final inventory: 12,827 entries, plus its self-excluded
manifest. Detailed path/digest lists are in `integration-pr12.json`,
`integration-pr13.json` and `HISTORICAL_GIT_AUDIT.json` in the evidence archive.

The closing commit changes only this report, the four new evidence files, and
their entries in the root inventory. `SOURCE_CLOSURE.json` records the allowed
path list and Git-object comparison against the executed candidate. The final
local commit/tree are recorded outside the commit in `FINAL_CLOSURE.json` to
avoid a self-referential commit identifier. Obtain them independently with
`git rev-parse HEAD HEAD^{tree}` in the integration worktree.
The aggregate root inventory is the explicit byte-change exception: only the
five new report/evidence leaf digests change; schema, exclusions, membership and
all source/config/fixture entries remain identical. `FINAL_SOURCE_CLOSURE.json`
in the task workspace records that exact delta after closure. No assertion that
the aggregate manifest itself is byte-identical is made.

## Frozen Core: byte identity and actual execution

Executable Core remains `pipavlo82/recomputable-verification-receipts`
at `9dd36e882dd372f264b77b179130948aa5adcbde`. The formal draft remains
`pipavlo82/ERCs@7a9e63a80bce04db53c6550103c1d41eca35f3d1:ERCS/erc-8404.md`,
SHA-256 `63f1ad56b6a8a5099a12afbacd511c1271f50b1af6ef674a12b7aeb28850ad85`.
Selected Core profile digest:
`51f79442e96339ca45e9e6cc0c8232833efbee20e7480df00987dbc97da72948`;
package digest: `c56fa659590247b302cf670245523ed3b02902157c27b0d710bad653cb3a0eee`.
Historical RC2 identities and differences remain frozen; this does not reinterpret RC2.

The unchanged `tools/erc8404/integrity.py` was executed before integration,
after PR12, after PR13, and on the final source candidate. An additional external
Git-object audit authenticates all 75 upstream files against the frozen upstream
inventory and all 13 vendored Core files against upstream objects and core-lock.
It compares 4,653 Core-related main paths, including baseline definitions,
schemas, original vectors, historical evidence and external consumers. Complete
main preservation additionally covers paths outside that subset. Each audit
retains the expected Git blob ID, expected SHA-256 and observed SHA-256. Neither
the protected set, its exclusions, nor any baseline digest was changed.
The immediate post-merge filesystem/checker audits ran after conflict resolution
and before each merge commit. `COMMITTED_MERGE_CORE_AUDIT.json` additionally binds
all 4,653 paths to the exact committed PR12 and PR13 merge trees, whose Core-related
path sets and Git blobs match main. The two different observation stages are not
misrepresented as the same commit.

Runtime observation uses CPython call events through the unchanged real adapter.
It observed 36 calls to `recompute` in the pinned vendored adapter over the 18-case
harness. The module path and adapter SHA-256 were checked; observed and unobserved
native output bytes match. Adapter SHA-256:
`03505efc8ee993f118fad2c71f706870d25de0da61a393a1f18f7b310bded235`.
No mock, fallback Core, modified status interpretation or replacement implementation
was introduced. Python normal/repeat/-O and Bun normal/repeat Core checks pass;
cross-runtime JSON semantics agree except for the declared implementation label.

No physical mutation in this work edits Core. Solidity mutations use isolated
ERC8004 implementation copies. Other inherited mutations target external
consumers or separate laboratory components. Original Core bytes and file
membership were verified again after execution and at closure.
No complete mutated source copy is imported into the committed candidate, even
inside its evidence archive. Those snapshots and generated compiler caches remain
at their original disposable execution paths in the task workspace.
`ARCHIVE_OMISSIONS.json` lists their exact paths and SHA-256. The archive retains
mutation replacements, input vectors, source/compiler/deployed-code hashes and
actual backend observations. Active source files match the pristine executed
commit objects. The mutations can be reconstructed against the pinned originals.

## Explicit preservation transition

The original PR12/13 preservation contracts bind the old base inventory. Main
already contains three changes relative to that base, pinned to these provenance commits:

| Path | Original provenance anchor |
| --- | --- |
| `conformance/agent-harness-v0/README.md` | `e5263f47325a81b0647f3de3a7bc36ad858aea5a` |
| `research/harness-v0/LIMITATIONS.md` | `e5263f47325a81b0647f3de3a7bc36ad858aea5a` |
| `tools/erc8004/integrity.py` | `4799a7260d8f99e489541cffe471e53c50411459` |

`TRANSITION.json` pins the exact before/after hashes and four original manifest
identities. Its raw SHA-256 is pinned in the new external verifier. It permits
**zero Core changes** and requires all main entries to remain unchanged. Initial
manifests are retained as their original Git objects and embedded frozen inventories;
they were not regenerated. Historical reports, evidence archives, normative pins,
fixtures, expectations, grader and old guards are unchanged.
The policy field `review_commit` identifies a provenance anchor in the selected
main history; its name is not an independently authenticated human-review attestation.

Only the two newly imported workflows select new, explicitly versioned orchestration
entrypoints (three exact command substitutions). Their original bytes remain
authenticated at PR13 and in the original seals. The original PR12 engine, oracle,
Solidity mutation runner, shrinker, PR13 semantic reporter and drift classifier
are reused unchanged.

The old fuzz checker still returns `passed: false` with exactly the three named
paths plus `root_inventory_changed_historical_entry` and `research_inventory`.
The new wrapper records `EXPECTED_OLD_CONTRACT_REFUSAL`; it does not relabel that
old result as PASS or suppress any other mismatch.

For PR13, all original 32 tests pass at the pinned PR13 commit. On main composition,
the old preservation assertion must refuse. The integrated 32-test population is
explicitly **31 unchanged semantic controls + 1 versioned preservation control**
requiring both that exact old refusal and acceptance by the new contract. This is
not a claim that the unchanged original 32 all pass on a different baseline.

Six physical input-tamper controls exercise the new contract: changed historical
evidence, deleted protected file, unauthorized addition, altered transition manifest,
resealed source lock, and substitution of the old integrity checker. Each attack
also reseals the disposable inventory, so detecting only an unresealed hash change
would not suffice. Positive controls and restored bytes are checked for every case.
All six attacks are REJECTED in normal/repeat/-O, with passing positive and restoration controls in every mode.
These are input-tamper controls, not a claim of verifier-mutant completeness. As
usual, a trusted reviewed commit/verifier is required; arbitrary replacement of
the verifier and all trust roots is outside the contract.

## Executed replay and comparisons

All results below are newly executed unless explicitly labelled historical.
Raw command receipts contain argv, cwd, UTC start, duration, exit code and stdout/
stderr hashes. The evidence archive retains the raw streams and per-case reports.

| Execution population | Newly observed result |
| --- | --- |
| Pinned PR12 baseline | 300/300 per normal/repeat/-O; 6/6 physical mutants KILLED in normal and -O; original 29 misses all six. |
| Pinned PR13 baseline | Original 32 controls and 13 transport controls in normal/-O; offline normal/repeat/-O bytes identical. |
| Pinned main baseline | 29/29 ERC8004, 17/17 mutations; 18/18 Core harness, 12/12 consumer mutations; behavioral repeats pass. |
| Candidate generated profile | 300/300 per normal/repeat/-O; 6/6 Solidity mutants KILLED in normal and -O; source/backend restoration passes. |
| Candidate spec/drift | 32 integrated controls (31 original + 1 versioned preservation) and 13 transport controls in all three modes; 51 obligations audited. |
| Candidate original ERC8004 pilot | 29/29; 17 KILLED; extra optimized mutation campaign passes. |
| Candidate original 18-case harness | 18/18; 12 KILLED; extra optimized mutations pass. |
| PR11 supplement | 5 cases; isolated 4 KILLED; original-matrix probe separately 1 KILLED, 4 SURVIVED. |
| Role policy v1 | 26/26 cases; controls {'normal': 18, 'optimized': 18}; 7 KILLED. |
| Role policy v2 | 50/50 cases; controls {'normal': 36, 'optimized': 36}; 5 KILLED. |
| External ERC8404 consumer | 45 scenarios; 16 KILLED, 1 SURVIVED; historical survivor remains classified separately; all three semantic repeats agree. |
| v0 | PASS; complete raw validator report retained. |
| formal-v1 | PASS; complete raw validator report retained. |
| v2 | PASS; 18 KILLED, 2 SURVIVED, 1 UNVERIFIABLE; complete raw validator report retained. |
| v2-survivors | PASS; 2 KILLED; complete raw validator report retained. |
| v3 | PASS; 14 KILLED; complete raw validator report retained. |
| v4 | PASS; 54 scenarios; 44 KILLED; complete raw validator report retained. |
| claim-integration | PASS; 61 scenarios; 22 KILLED; complete raw validator report retained. |
| escrow | PASS; 31 scenarios; 22 KILLED; 8 negative CI controls; complete raw validator report retained. |
| v0-python313 | PASS; complete raw validator report retained. |
| v4.1 | 57 cases / 7 reuse checks; 9 KILLED; normal/-O tests and mutations pass. |
| Preservation transition | All six attacks are REJECTED in normal/repeat/-O, with passing positive and restoration controls in every mode. |

Determinism claims concern the specified behavioral outputs. Wall-clock timings
remain raw observations. The unchanged escrow validator separately retains gas
measurements and compares decisions, statuses, evidence and token deltas exactly;
its existing explicit gas-field exclusions were not broadened.
Escrow's negative CI controls additionally create a redundant scope guard in a
disposable copy, execute an intentional 16 KILLED / 1 SURVIVED campaign, and require
the CI gate to refuse it for mutation coverage failure. This control is separate
from the stock 17 adapter + 5 Solidity mutations; it is not a newly found stock
survivor and is not counted as KILLED.

PR12's 300 cases use seeds 8004, 8299 and 8274, 100 each. There are 243 distinct
inputs, 186 distinct sequences and 1,195 EVM calls per full campaign; these are not
300 independent implementations. The 300-case authorization distribution is
57 VERIFIED / 222 REFUTED / 21 UNVERIFIABLE, with 300 conformant observations.
Normal/repeat/-O behavioral projection SHA-256:
`98cc0633b9add940124458a1f8cfe46ccec2606347e9cef5ff9101616075229c`.
The new candidate and pinned baselines also match byte-for-byte for the original 29-case and 18-case behavioral projections. All four executed physical mutation campaigns (baseline/candidate, normal/-O) have identical semantic witness, source, compiler and deployed-code audit records. See REPLAY_COMPARISON.json.

The six physical Solidity mutations have three passing positive controls each.
Each is missed by the original 29-case matrix (29 conformant observations) and
distinguished by a generated witness. Source SHA, compiler-input SHA and deployed
EVM code hash are reconciled from actual backend outputs. Minimized witnesses
execute that same mutated backend. Restoration checks cover source bytes and
compiler/deployed-code hashes, not merely a successful cleanup command.

| Mutation | Minimized calls | Distinguishing field |
| --- | ---: | --- |
| registration_reserved | 1 | register status |
| metadata_authority | 1 | metadata status |
| unset_authority | 2 | unset status |
| wallet_future | 2 | wallet status |
| response_range | 3 | respond status |
| summary_unanswered | 3 | summary state |

Minimization establishes deletion-1-minimal nonempty sequences, not a global
minimum. A compile failure, timeout, infrastructure error or missing run is never
counted as KILLED. Normal and optimized child adapter argv are retained to verify
that optimization reached the actual Python backend.

## PR13 coverage and live drift

All 51 obligation mappings were reconciled against source locators, suites,
execution evidence and concrete guard/witness mappings: 39 guard-mapped and 12
executed-only. `OBLIGATION_AUDIT.json` retains the per-obligation detail. A test
reference or plain PASS is not upgraded to enforcement. The original 18/29/300/5
case populations and 12/17/6/4 mutation populations remain separate. PR13's
coverage output is an audit of historical evidence (`new_backend_execution:false`),
not itself a new backend execution or proof of independent implementation.
Its retained PR11 `integrated_into_base:false` describes the original pinned PR13
base; it does not describe current main, which already contains the supplement.
This integration report and the new executions provide the current-state context
without rewriting that historical metadata.
The 39 mapped obligations have specific observed guard/witness evidence, not
exhaustive enforcement of every clause or path. The 12 executed-only obligations
are not promoted to physical mutation coverage.

The controls distinguish changed, moved, missing and unavailable sources; network
error/rate limit do not become UNCHANGED. They reject unrelated mutations, absent
execution, inconsistent independence claims and expectation leakage. Offline
normal/repeat/-O output bytes match each other and the pinned PR13 replay:

| Output | SHA-256 |
| --- | --- |
| COVERAGE.json | `a69e5774afdea3c7115d0959a528a743f18dd68038f2c9a3638f7ffc9678f1d2` |
| SOURCE_DRIFT.json | `56e97a4d0a81fef4f8343e0f27bfa29daee5d76cc9d08e04e0974ef0be0aaf7e` |
| OBLIGATION_COVERAGE.md | `836258a4d882066208a2dacf9b803d6aae01373006e49e177dd7cd49c03f5174` |

A separate live capture retained observed UTC time, requested URL, HTTP status,
raw response bytes and SHA-256. ERC8004's latest source commit moved to
`10eca3cea34986aeeac0af98ad061ab8928dc15d` with unchanged pinned document content
(`UPSTREAM_MOVED_CONTENT_UNCHANGED`). ERC8404 draft and RVR v0 were UNCHANGED.
The exact observation is in `fresh/build/final/live-drift/SOURCE_CAPTURE.json`.
No source pin, expectation or historical verdict was automatically changed.
This trusts the selected public HTTPS/API source and observed refs; local hashes
are not an independent upstream attestation or a semantic compatibility proof.

## Environment, setup and failed attempts

Windows PowerShell; CPython 3.12.10; Node 22.15.0; Bun 1.3.14; Rust/cargo 1.97.1;
Forge 1.7.1. The reproduce workflow's additional Python 3.13 matrix uses task-local
CPython 3.13.15. Full tool outputs and executable identity are retained. Dependencies
use the repository's existing lock files, exact source commits and hash checks.
No global project configuration or historical dependency lock was changed.

Four preparation/orchestration failures are retained, with their corrected runs:

1. A precommit preservation-control copy exceeded Windows MAX_PATH. The new
   control runner now uses a short, validated disposable system-temp directory,
   without changing Windows policy or weakening enumeration.
2. An early precommit spec smoke run detected concurrent edits to two new files
   and correctly refused their inventory mismatch. The complete spec replay was
   repeated against the committed, clean candidate. The failed smoke is not PASS.
3. The first escrow dependency preparation used LF checkout bytes while its
   historical lock requires CRLF. A separate clone was prepared with the exact
   existing workflow's `core.autocrlf=true` recipe and pinned commit. No lock or
   original dependency bytes were redefined; the first failed preparation remains
   in the logs.
4. The first full escrow replay selected `build/final/escrow`, outside the frozen
   Foundry `fs_permissions` write subtree. Its EVM tests refused to write evidence;
   this is a failed execution, not a mutation kill. The complete suite was repeated
   at `build/escrow/ci-integration-v1`, already permitted by the existing config.
   No source, permissions, Core, expectations or dependency pins were changed.
   Both attempts and the final source/Core checks are retained.

No additional unresolved execution failure remains. Raw failed setup/smoke attempts are retained separately from successful corrected runs in EXECUTION_INDEX.json.

## Replay commands and evidence

Use full Git history and the pinned dependency preparation in this directory's
README. The exact executed command sequence is preserved in `final_serial.py`,
`fresh_semantics.py`, `baselines.py`, `post_replay.py` and their command receipts
inside the evidence archive. Run physical mutation campaigns serially in isolated
copies. Principal commands:

```sh
python -B tools/verify_artifacts.py
python -B tools/erc8404/integrity.py
python -B tools/pr12_pr13_integration/preservation.py --fuzz
python -B tools/pr12_pr13_integration/fuzz_validate.py --out build/review-fuzz
python -B tools/pr12_pr13_integration/spec_validate.py --out build/review-spec
python -B tools/pr12_pr13_integration/controls.py --out build/review-preservation
python -B tools/pr12_pr13_integration/runtime_binding.py --out build/review-core-binding
python -B tools/pr12_pr13_integration/spec_cli.py drift --live --out build/review-live
python -B tools/escrow_ci.py --out build/escrow/review-ci
git diff --check
```

Historical entrypoints run unchanged on detached original PR commits:

```sh
python -B tools/erc8004_fuzz/validate.py --out build/original-pr12
python -B -O tools/erc8004_fuzz/mutations.py --out build/original-pr12-optimized
python -B tools/spec_drift_coverage/validate.py --out build/original-pr13
```

The new archive is `evidence/pr12-pr13-integration-v1/EVIDENCE.zip`.
SHA-256: `086ddfaff99867c433c3ead9d82c570419f7ad17d8c6beed5902dcc11a970290`. `SHA256.json` binds every archived member plus the
new report, results and archive. Original evidence directories and archives remain
byte-identical. This packaging supplies inspectable execution observations; archive
integrity alone does not establish that an execution occurred.

## Remaining boundaries and review decision

No unresolved integration defect was observed in the required executed checks. All 17 repository workflow families have local command coverage; hosted GitHub Actions on this new branch is NOT_RUN because no push was authorized. Windows local success does not establish Ubuntu-hosted CI success. Independent human/organizational review and a same-profile independent implementation remain NOT_ESTABLISHED/NOT_COVERED.

Published finite-coverage limits remain visible: the old external Core-consumer mutation campaign retains its survivor; the original v2 campaign retains 18 KILLED / 2 SURVIVED / 1 UNVERIFIABLE, separately from the two later survivor controls; the PR11 original-matrix probe remains 1 KILLED / 4 SURVIVED, separately from its 4 KILLED isolated controls; escrow retains 6 NOT_APPLIED absent on-chain checks. These denominators are not merged or relabelled. Existing laboratory escrow checks were replayed without real funds or a new end-to-end pilot. The candidate is ready for an independent reviewer to inspect and replay; production remains HOLD.

Inherited NOT_COVERED v3 boundaries: `wyriwe_provenance`, `external_model_authority`, `inference_judgment_binding`, `external_execution`, `historical_input_bytes`, `historical_execution`. Inherited v4 uncovered scope: `universal contract adequacy`, `external artifact acquisition`, `missing contract double fail-closed branch`. Public-chain authentication and exhaustive coverage of every defensive parser branch are not established. These are retained domain/coverage limits, separate from the successfully executed required integration checks.

Executor: this Codex session operating Pavlo's local Windows environment. The
external Git-object and runtime-binding checks are additional verification methods
by the same executor, not an independent organization, human auditor or independently
authored implementation. A clean checkout, a second execution and language comparison
do not change that independence level. No claim of universal ERC conformance,
general compiler correctness, live provider/hardware authenticity, or production
execution follows. Authorization remains external application policy; it does not
rewrite frozen ERC8404 Core semantics.

No upstream main or PR branch was modified. No push, remote merge, comment, PR
status change, deployment, real payment or new end-to-end pilot was performed.
