# ERC-8004 second-backend research pilot v0

This local experiment executes the existing **29-case
erc8004-registry-observation-v0 profile** against two pinned implementations.
It reuses VECA's existing harness, recompute-kit grader, exact vectors and
laboratory authorization policy. It adds no verifier core or ERC requirement.

- Host baseline: `4b6d7ef9aabd23932668711ee1d6cf774d9844d7`.
- Solidity: `erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`.
- Vyper: `vyperlang/erc-8004-vyper@661278f72d312a2cef0cbaea32b89d3842996967`.
- Normative reference remains the original
  `ethereum/ERCs@503591a6e80e6e1affdd6403341e25269141f046:ERCS/erc-8004.md`.

See [RESULTS.md](RESULTS.md), [CANDIDATE_AUDIT.md](CANDIDATE_AUDIT.md),
[source-lock.json](source-lock.json), [mutations.json](mutations.json) and
[machine evidence](../../evidence/erc8004-second-backend-v0/RESULTS.json).

## Replay

Observed platform: Windows x64, Python 3.12.10, Node 22.15.0. Python requirements
pin the nine observed wheel digests, including Windows CPython 3.12 wheels;
Linux/macOS dependency resolution has not been tested. Preparation fetches only
public pinned source/packages. Execution uses Hardhat 3.0.6 local EDR with the
original Shanghai configuration. No RPC, wallet funds, deployment keys or public
network execution is required.

From a complete-history checkout at the reviewed commit:

```powershell
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B tools/erc8004_second_backend/prepare.py
python -B tools/erc8004_second_backend/validate.py --out build/second-normal --mutations
python -B tools/erc8004_second_backend/validate.py --out build/second-repeat
python -B -O tools/erc8004_second_backend/validate.py --out build/second-optimized --mutations
python -B tools/erc8004_second_backend/negative_controls.py --out build/second-negative
python -B tools/erc8404/integrity.py
python -B tools/erc8004_second_backend/preservation.py
```

Commands refuse existing result directories. Compare `semantic.json` exactly
between the three runs. `--source <git checkout>` on the new prepare command
reads exact pinned Git objects instead of downloading them. The original
29-case vectors, expectations, obligations and suite remain unchanged.

## Interpretation

The Vyper source is separately authored upstream code with a distinct language,
compiler and implementation layout. Its history explicitly follows and checks
the Solidity reference. **Clean-room independence is not established.**
Both adapters share the original operation loop, local EVM, policy and grader;
this is not an independently implemented authorization checker or human audit.

The normative, implementation-specific and research-policy obligations remain
separate in every report. Constructor deployment vs UUPS bootstrap, concrete
registry addresses, transaction hashes, bytecode and gas need not be equal.
Portable behavior/authorization projections must match the same fixed expected
values. Execution-specific identity is preserved in raw evidence, not discarded.

Vyper bounds strings/arrays, uses direct constructors and has its own dependency
semantics. The pilot does not test arbitrary sizes, proxy upgrades, full ERC-721,
ERC-1271 branches, ReputationRegistry, all upstream tests or full ERC conformance.
Matching observations do not establish task truth, external execution, payer
authority, permission to act, real-world controller independence or payment.

## Preservation and publication boundary

This is an **additive local research snapshot**, not a merge-ready CI migration.
Every one of the 12,828 baseline tracked files, including the original complete
inventory, old guards, all workflows and ERC-8404 materials, remains byte-identical.
New files are sealed separately by `ADDITIONS.sha256.json`; the local Git commit
is the review identity. The seal is not an independent trust root and cannot
authorize itself. No inherited guard is disabled, edited or replaced.

The inherited `tools/verify_artifacts.py` intentionally **fails** on the new
additions because its old inventory does not include them. Its refusal is
recorded, not relabelled PASS. The additive audit proves baseline preservation;
it does not claim satisfaction of that old whole-tree contract. Before a future
PR, a separately reviewed, exact versioned preservation/CI transition must
account for these additions and the then-current main (including PR15 if merged).
Do not blanket-rehash old manifests or append broad directory exclusions.

ERC-8404 Core is not involved in the ERC-8004 backend path. Its original Python
and TypeScript conformance commands are separately replayed as preservation
checks, and its pinned upstream Git objects are checked byte-for-byte.

## Licensing

New VECA integration code is MIT; the driver adapts the existing MIT VECA driver.
Fetched Vyper contracts at the selected SHA are **AGPL-3.0-only**, including their
interfaces; the complete upstream LICENSE is preserved in the external source
cache. They are not relicensed as MIT or vendored into VECA source directories.
The upstream license-history correction is explicitly recorded in the audit.
Snekmate and all other dependencies retain their own licenses. This task does
not publish a hosted service or redistribute an unlabelled upstream code copy.

Production remains HOLD. No push, PR, merge or upstream change is part of this
local pilot.
