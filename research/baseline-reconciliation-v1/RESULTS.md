# Executed baseline reconciliation results

The read-only comparison identified exactly two documentation transitions from
#11. Both full file SHA-256 values, Git blobs, commit histories and original bytes
are preserved. Re-executing the exact historical integrity checker against the
composed tree reproduced exactly those two failures before reconciliation.

Before accepting the transition, the unchanged #11 checkout at `25f7c45f` was
replayed: scope, scenario, definitions and supported_contract each had an isolated
REFUTED witness that was a conformance PASS, a passing positive control, a physical
KILLED mutant and byte-exact/semantic restoration. Normal/repeat/-O agreed.
The five-probe comparison on the old 18 vectors remains 1 KILLED / 4 SURVIVED.

The following were actually executed with the same reconciliation code on the
source-head candidate and on the isolated GitHub test-merge candidate:

| Population | Source candidate | Composed candidate |
| --- | --- | --- |
| Original ERC-8004 scenarios | 29/29 normal/repeat/-O | 29/29 normal/repeat/-O |
| Original ERC-8004 physical mutations | 17/17 normal and -O | 17/17 normal and -O |
| Role-policy v1 scenarios | 26/26 normal/repeat/-O | 26/26 normal/repeat/-O |
| Role-policy v1 physical mutations | 7/7 normal and -O | 7/7 normal and -O |
| Role-policy infrastructure methods | 18/18 normal and -O | 18/18 normal and -O |
| Baseline transition controls | 16/16 normal and -O | 16/16 normal and -O |

On the composed checkout the original ERC-8404 harness also passed 18/18 in
normal/repeat/-O, with its separate original 12/12 physical mutations in normal
and -O. The supplemental profile passed 5/5, with its separate 4/4 mutations in
normal and -O, matching the pre-reconciliation raw mutation records and semantic
projections. These mutation populations are not added together.

Original 29-case projections match the preserved pilot evidence byte for byte:
`837dbe977cb3bf66470ffe7ed2b4311e001776bbed95057f3b366d16af25e211`. Role-policy projections retain
`0ed522131509603602adbb90d8c6111a3347d8b5c19ce90d75440c67953a7617`.
Supplemental projections retain
`aa134ea900784fbb4f69d972babafa1b579b64e16771de554f906ef47dd909cc`.

The original 12,193-entry harness inventory has 12,191 unchanged files in the
composition plus exactly two reviewed document transitions. Relative to the
12,667-entry pilot inventory, 12,664 are unchanged in that composition: two docs
and the explicitly versioned preservation-checker update are listed separately.
On the source candidate the docs stay original, leaving 12,666 pilot files
unchanged plus the checker transition. All original source locks, normative pins,
Solidity, harness/grader, expectations, and frozen evidence remain byte-identical.
The role-policy preservation entry point is also deliberately updated to invoke
the versioned check; it is not falsely counted as unchanged from `aee0f9f`.

The archive SHA-256 is `fb2023689a87ffcb37b9375c30cae3360ec9c76a0634cc100b9019ac4d2433ae`
(2721 members, 6419855 bytes). See
../../evidence/baseline-reconciliation-v1/SUMMARY.json for exact candidate source
hashes, runtime versions and machine results. The raw evidence includes all
completed command receipts. Missing history, wrong manifests, rehashed corruption,
mixed document versions and incomplete PR11 payloads fail the negative controls.

Recommendation: READY_FOR_INDEPENDENT_REVIEW for this bounded reconciliation.
This does not authorize merge, claim universal conformance or establish independent
human/controller validation. PR #10 stays Draft. #12/#13 require their own later
integration checks and have not been changed. Existing frozen reports retain
their original meaning; new CI results are recorded separately on the PR.
