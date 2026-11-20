# ERC-8004 second-backend pilot results

Observed 2026-11-20. **GO_SCOPED_RESEARCH**: a real second implementation runs
through the unchanged harness. **Not ready for a PR/merge** until a separately
reviewed preservation/CI transition accounts for these additive research files.
Production HOLD.

## Source and execution

- Base main: `4b6d7ef9aabd23932668711ee1d6cf774d9844d7`.
- Local branch: `research/erc8004-second-backend-v0`.
- Solidity: `b9e466c250744a7e06b13dff9d3c2844ed64f825`.
- Vyper: `661278f72d312a2cef0cbaea32b89d3842996967`.
- Existing 29 vectors, expected outcomes, obligations, policy and grader unchanged.
- Python 3.12.10; Node 22.15.0; Vyper 0.4.3; Snekmate 0.1.2;
  Hardhat 3.0.6/EDR Shanghai; Solidity compiler 0.8.24/OZ 5.4.0.
- Only exact public-source/package preparation used networking. Execution uses
  the original local EDR network configuration without public RPC or funds.

## Newly executed results

| Check | Observation |
| --- | --- |
| Solidity, normal/repeat/Python -O | 29/29 in each mode |
| Vyper, normal/repeat/Python -O | 29/29 in each mode |
| Portable semantic comparison | Byte-identical between both backends and all modes |
| Vyper physical mutations, normal | 6 KILLED / 0 survived / 0 crashed |
| Vyper physical mutations, Python -O | The same 6 KILLED; not 6 additional unique mutants |
| Positive controls and restoration | 4 specified positive controls per mutant; all 29 pass after each restoration |
| Negative/transport and operation-loop controls | 6/6 PASS |
| Original Core Python and TypeScript conformance | Both commands exit 0 |
| Original Core integrity | PASS, 13 vendored files and historical lock |
| Independent Git-object byte comparison | All 12,828 baseline files unchanged; all 75 upstream Core files and 13 vendored files match pins |
| Old aggregate artifact guard | Exit 1 on new additions, preserved as expected refusal; not PASS |

Each run's laboratory authorization population is `{'VERIFIED': 8, 'REFUTED': 20, 'UNVERIFIABLE': 1}`. These are
scenario decisions, not permissions to act. Semantic SHA-256:
`837dbe977cb3bf66470ffe7ed2b4311e001776bbed95057f3b366d16af25e211`.

Six mutants remove URI owner checking, wallet signature rejection, transfer
wallet clearing, validation-request ownership, designated-validator checking,
or duplicate-request rejection. Every required field-specific killer and
positive control is recorded in `mutations.json`; `unexpected_changes` is empty.
Each mutant recompiles actual Vyper source, changes the executed contract
codehash, and is tested through the same grader. Original bytes are restored and
the full 29-case positive baseline passes afterward. This is a new six-mutant
campaign, **not** the older PR12 Solidity fuzz campaign whose six mutants escaped
the old matrix. No mutation-completeness claim is made.

Source mismatch, unauthorized additional source, deleted required source and a
deliberately crashing adapter produce UNVERIFIABLE. Unsupported profile is
rejected before observation. Failures/crashes are not counted as semantic kills.

## Fresh checkout and preservation

Fresh committed-checkout replay: NOT_RUN at this source checkpoint; final closure records the subsequent run separately.

`ERC8404_CORE_BYTES_UNCHANGED: PASS`. Core is not substituted into, or used by,
the ERC8004 registry comparison. Its original conformance adapters were executed
separately. No frozen Core, expected hash, dependency pin, source-lock, historical
report or original manifest was changed. The complete baseline Git blob/SHA-256
comparison is in the archive. The new additive seal does not override the old
inventory contract; no inherited workflow or guard was edited.

The final report/evidence closure may add only new documentation/evidence and
reseal the new additions inventory. Its executed source/config bytes must remain
equal to the fresh-checkout source commit; see the external CLOSURE.json for the
final commit/tree identity and check.

## Findings and limits

The first Vyper adapter attempt failed because Windows compiler output used
backslash path keys. Only the new adapter's artifact-key handling was corrected;
the failed run remains UNVERIFIABLE in raw logs. Two preparatory command-path
mistakes are retained; they are not backend defects or passing checks.

The discovery corrected an early legacy/current-directory confusion for
ChaosChain; the audit distinguishes its current `src/` and historical `legacy/`.
No source-level defect was established by the 29-case Vyper comparison. No
upstream vulnerability is implied by deliberately injected mutants.

This is same-Codex local execution of third-party source, not independent human
review. Vyper is reference-informed, not proven clean-room. Both implementations
share EVM, operation loop, policy and grader. Full ERC conformance, Reputation,
ERC-1271 branches, proxy upgrades, large inputs, independent adapters/runtimes,
all upstream test suites, original 300-case fuzz replay, production authorization
and external execution remain NOT_COVERED/NOT_RUN for this pilot.

## Recommendation

Keep this second backend as a bounded comparison target. Next, review the exact
new-code/source/licensing boundary and integrate the experiment through a narrow
versioned preservation/CI transition on the then-current main. A later profile
can investigate a concrete differing boundary (for example size limits) without
rewriting this profile's historical expectations. No push, PR, public deployment
or changes to existing PR statuses were performed.

Replay commands are in [README.md](README.md). Exact commands, exit codes, raw
stdout/stderr, source metadata, mutated/restored hashes and reports are in
[EVIDENCE.zip](../../evidence/erc8004-second-backend-v0/EVIDENCE.zip), with
[SHA256.json](../../evidence/erc8004-second-backend-v0/SHA256.json).
