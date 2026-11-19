# Documentation refresh v1 — executed results

Verdict: **LOCAL_SCOPED_VALIDATION_PASS**. **ERC8404_CORE_UNCHANGED: PASS**.
Production HOLD. Hosted CI for this new local branch: **NOT_RUN**.

Base main: `4b6d7ef9aabd23932668711ee1d6cf774d9844d7`. Branch: `docs/readme-post-pr14-v1`.
Final source tested in a clean ordinary clone: `f1563d931a21c7f887ecfa1e720dfeed76862afe`.
The final local commit is obtained with `git rev-parse HEAD`; it is recorded in
the external task closure to avoid a self-referential commit ID in this report.

## README changes

Updated the October 21 / PR2-8 checkpoint to the observed November 19 PR14 merge.
Added the implemented adapter protocol, ERC8004 pilot, role-policy v1/v2, 300-case
generated campaign and 51-obligation evidence map. Added the current integration
replay entrypoints and separated live drift from deterministic offline replay.
Replaced the already-implemented harness next step with independent same-profile
backend/replay work. Preserved original denominators and added the separate
unexecuted v2 UNVERIFIABLE target. Retained evidence limits and Production HOLD.

All 49 local README link targets exist. Existing commands and their pinned
versions were checked against actual code/workflows; new setup/replay commands
were executed. External publication URLs were not exhaustively revalidated.

## Preservation and CI routing

Archived the previous root README exactly (SHA-256
`ca021c56b2ed76d2eeb5f940677ef15691f2d74e29e40e436b558b2cf030103f`). The new README hash is
`a576e40cca6242d90b7e1028689f5c13b090fbb98465c68443a567e348260c66`. Existing Core, guards, policies, source locks,
fixtures, reports and evidence were not changed. Eleven later workflows receive
an exact mechanically checked routing change; six earlier/Core workflows remain
byte-identical. All old commands, tool/action pins and triggers are preserved.
Bun 1.3.14 parsed all 18 YAML files; structured comparison confirmed only the
declared routing differences. One additional workflow runs the new controls.

The current root transition and complete inventory are verified before replay.
The old PR14 contract correctly refuses the updated checkout directly; it passes
unchanged in the isolated historical-documentation worktree. That is an explicit
version boundary, not a relabelled historical refusal. The old and new worktrees
have identical existing executable/config/fixture bytes except the specifically
listed workflow routing; the current checker rejects other source changes.

An early scratch attempt routed all workflows. The unchanged Core history guard
correctly rejected five frozen workflow changes. Those five and the ERC8404
workflow were restored from pinned Git objects before final validation. Raw failed
output is retained in the new evidence; it is not counted as a passing check.

## Newly executed checks

- 13/13 controls in normal, repeat and Python -O. Their 13 semantic outcome lines
  are identical; timings are not claimed deterministic. Nine physical tamper
  witnesses reject substituted README, archived README, historical evidence,
  deleted protected file, added file, transition manifest, workflow, external
  ERC8004 executable and an unlisted file. Inventory resealing does not authorize
  the substitutions. Pristine/restored positive checks pass; no Core is mutated.
  The final control driver supports both a linked-worktree .git file and a normal
  CI-clone .git directory. All three final runs used the clean ordinary clone.
- Complete current inventory and explicit transition pass; git diff check passes.
- Frozen Core integrity passes. Independent Git-object comparison within this
  same author session verifies 4,653 Core-related paths, 75 upstream files and 13
  vendored files against the existing pins, without changing any baseline.
- Original Python, Python -O and TypeScript/Bun Core conformance checks pass;
  outputs match after removing only the implementation label.
- Actual pinned-Core runtime tracing through the unchanged 18-case adapter:
  36 recompute calls; traced/native output bytes match.
- Existing synthetic v0 validator ran in both current and replay checkouts.
- Existing integrated spec validator: 32 controls (31 unchanged semantic + one
  historical integration-preservation control), 13 transport controls, offline
  normal/repeat/-O deterministic outputs. This reconciles historical backend
  evidence; it is not itself a new ERC8004 EVM execution.
- Original escrow integrity checker passes in the replay worktree.
- An additional physical dirty-replay-view control refuses the altered historical
  README without resetting it; pristine and byte-restored controls pass.
- Existing public pinned grader/npm caches were copied into task-owned ignored
  directories for replay; no production/provider credentials or transactions.

Machine-readable commands, exit codes, semantic controls and runtime binding:
`evidence/documentation-refresh-v1/RESULTS.json`.
Raw local logs and full Git-object audit:
`D:/PAVLO HQ/Workspaces/veca-readme-v1/`.

## Limits and replay

Full 300-case, role-policy and Solidity mutation campaigns were not rerun for
this documentation change. Existing backend bytes and expectations remain exact;
the routed CI still executes its original campaigns afresh when published. No
hosted Linux CI, independent implementation or independent human review is claimed
for this local change. Executor: Codex in Pavlo's Windows workspace.

Use the commands in README.md and this directory's README.md. The old baseline
worktree remains at `4b6d7ef9aabd23932668711ee1d6cf774d9844d7`; its HEAD is recorded separately from the
documentation candidate. New source/config/tests were fixed before final tests.
Only this result report, the new evidence JSON and their two aggregate inventory
entries are updated afterward. The external closure records a clean candidate
checkout and verifies that every other validated file byte is identical.

No push, merge, new PR, deployment, payment or old-evidence rewrite was performed.
