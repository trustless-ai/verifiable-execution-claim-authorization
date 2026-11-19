# Architecture and stable interfaces

## Source identity monitor

`tools/spec_drift_coverage/drift.py` consumes `sources.json` plus either a captured
GitHub response snapshot or fresh public responses. A branch commit is resolved
first; content is fetched at that exact commit, avoiding a branch/file race. Each
response retains its URL, HTTP status, exact base64 bytes, SHA-256 and observation
time. Pinned bytes are checked against their frozen hash before comparison.

`veca.spec-source-capture.v0` preserves observations. `veca.spec-drift-report.v0`
records source identity, pinned/latest commit and SHA-256, branch, timestamp,
evidence references, affected profiles/obligations and one comparison:
UNCHANGED, UPSTREAM_MOVED_CONTENT_UNCHANGED, SOURCE_CHANGED_REVIEW_REQUIRED,
SOURCE_MISSING or UNVERIFIABLE. A missing branch, rate limit, timeout, malformed
response or identity mismatch is UNVERIFIABLE; a file 404 at a resolved commit is
SOURCE_MISSING. This is byte drift, not semantic diff or normative interpretation.

The ERC-8404 draft source is the pinned author's fork/feature branch. It is not
silently substituted with an adopted ethereum/ERCs document. Its frozen RVR v0
normative specification is monitored separately. Draft context drift requests
profile review; only source-linked normative obligation IDs are listed explicitly.

## Evidence reporter

`coverage.py` reads hash-bound file or ZIP-member references. Original profile
fixtures and executed corpus bytes must agree. Suite, request, observation and
report hashes must match. Requests must equal the existing harness's expectation-free
`detached_request`. The unchanged pinned recompute-kit validates corpus shape and
canonical expected/observed equality. Its historical runner-graded results are
reconciled, not replaced by a new ERC verifier. No stored PASS label is sufficient.

`veca.obligation-evidence-report.v0` has profiles, per-case expected/observed values,
obligation records, separate mutation populations, input digests and explicit
limitations. An obligation's `outcomes` contains IDs resolved in the same profile's
`case_outcomes`, avoiding repeated large state sequences. Normative anchors,
implementation pins and declared policies remain distinct; these new annotations
do not change the interpretation of legacy reports.

Levels are separate evidence facts, not a universal compliance score:

- DECLARED: requirement catalog entry exists.
- REFERENCED_BY_TEST: a pinned fixture explicitly names it.
- EXECUTED_AND_MATCHED: a captured determinate run matches that fixture under the pinned grader.
- ENFORCEMENT_DEMONSTRATED: a reviewed specific guard mapping plus actual physical mutation, a distinguishing witness, passing positive controls and restored behavior are present.
- INDEPENDENTLY_REPLAYED: reserved; no independent reviewer attestation is admitted by this v0 importer.
- NOT_COVERED: no admitted support for that axis; all independent replay and unmapped enforcement axes use it.
- UNVERIFIABLE: supplied evidence cannot establish its claimed result.

`highest_supported_level` is a convenience for displayed observation strength;
`enforcement_status` and `independent_replay` are independent fields. A reference or
passing test cannot automatically earn enforcement. Explicit mappings identify a
specific guard/subcase, not full obligation enforcement completeness. Some passing
witnesses legitimately have authorization REFUTED or UNVERIFIABLE.

`--claims file.json` validates proposed metadata against derived evidence and
rejects unsupported levels or unrelated mutation links. The reviewed mappings and
input catalog are trusted research policy, protected by a source seal; semantic
adequacy of those mappings still needs independent review.

## Mutation populations and restoration

Keep PR9 original 12, PR10 original 17, PR11 supplemental 4 and PR12 generated 6
separate, with exact source/report locators. PR11 is imported read-only from
`e5263f47325a81b0647f3de3a7bc36ad858aea5a`; it is not integrated into the base.
PR12's preserved 29-case comparisons are associated only with its six mutants.

The reporter reconstructs each exact one-site change inside its pinned function
window and verifies the retained mutant bytes/hash. PR10 policy mutants additionally
relocate the implementation root; that exact infrastructure change is recorded.
PR10 restored runs select the pristine backend while retaining disposable mutant
copies. PR12 restores the same copy. These different historical practices remain
explicit; no same-copy restoration is backfilled onto PR10.

## Execution Specs concepts adapted

Inspected `ethereum/execution-specs@05420bce40492ca7ff11bc79cf3feb24778dce83`:
[spec references](https://github.com/ethereum/execution-specs/blob/05420bce40492ca7ff11bc79cf3feb24778dce83/docs/writing_tests/reference_specification.md),
[checklist markers](https://github.com/ethereum/execution-specs/blob/05420bce40492ca7ff11bc79cf3feb24778dce83/docs/writing_tests/eip_checklist.md),
[GitReferenceSpec](https://github.com/ethereum/execution-specs/blob/05420bce40492ca7ff11bc79cf3feb24778dce83/packages/testing/src/execution_testing/base_types/reference_spec/git_reference_spec.py).
Exact inspected file hashes are in `conformance/spec-drift-coverage-v0/eels-reference.json`.

REFERENCE_SPEC_GIT_PATH supplies source location; REFERENCE_SPEC_VERSION tracks a
Git blob identity in EELS. VECA retains its existing commit SHA plus file SHA-256
rather than conflating a commit, Git blob SHA and SHA-256. EIP checklist markers
inspire explicit obligation references; our report adds distinct execution and
physical-enforcement evidence levels. Fixture/implementation separation is already
provided by the existing expectation-free harness. No EELS engine or architecture
was copied, and no EELS/Foundry/Echidna execution is claimed.

## CI and preservation

The new workflow runs deterministic offline controls on push/PR. Read-only live
checks are available for workflow_dispatch/schedule; schedules only become active
on the default branch under GitHub's scheduler rules. This research PR does not
modify main or activate a default-branch schedule. Warnings upload raw evidence;
no job rewrites drafts, expectations, pins or historical evidence.

The exact PR12 inventory is archived and verified before any new source sealing.
The root inventory is extended for additive files only. Historical source locks,
Core, adapters, grader pins and workflows remain unchanged. Dependencies live in
ignored build directories. Source integrity is identity evidence, not authenticity
of an arbitrary report or proof of universal correctness.
