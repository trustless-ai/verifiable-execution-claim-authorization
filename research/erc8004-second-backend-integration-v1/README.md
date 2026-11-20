# Second-backend integration v1

This version composes merged PR15 `29155372c6a16f23d1bc2091f2f3671c51e0da4c`
and preserved pilot `1ce2b4e0f3e83faf1a16d5ced0507aca20e4ba90`. The pilot's
19 added files are imported byte-for-byte, including its Windows wheel pins,
source lock, adapters and historical report/evidence. The Git merge preserves
both parents; no previous integration was replayed as duplicated changes.

## Three explicit execution locations

1. Current candidate: new Vyper/Solidity campaign, new transition controls,
   root inventory and the six unchanged early/Core workflows.
2. `build/base15`, pinned PR15 merge: original documentation guard and controls.
3. `build/base15/build/documentation-replay`, pinned `4b6d7ef9aabd23932668711ee1d6cf774d9844d7`:
   unchanged legacy campaigns under their original composed integrity contract.

`tools/second_backend_integration/replay.py prepare` checks current membership
and bytes before creating these views; it refuses an existing incorrect/dirty
view and never resets it. `check` rechecks all existing views. The binding receipt
records heads and whether campaign execution has occurred (preparation does not
execute campaigns). Results in legacy views are newly executed, not read from
old result JSON. Their SHA identity is never relabelled as current-head execution.

## Exact preservation contract

- All old main files remain unchanged except root README, twelve enumerated
  workflow routing files, and the aggregate inventory.
- Six early/Core workflows, every old verifier/guard, Core baseline, source lock,
  normative pin, fixture, historical report and evidence remain byte-identical.
- The previous README is archived exactly. The old aggregate inventory is read
  from its pinned Git object; only explicitly approved entries/new entries change.
- All 19 pilot files must match its exact Git objects. The new transition lists
  exact new paths, immutable executable/config/doc hashes, and the normalized
  verifier body. Its own digest is pinned in that verifier. Closing report/evidence
  entries may be added under exactly four named paths, never whole directories.
- Git review is the trust root. A mutable manifest cannot authenticate itself;
  this verifier is trusted code, not an adversarial-code sandbox.
- Physical controls reseal the ordinary inventory and verify rejection of old
  evidence changes, deletion, unauthorized additions, transition substitution,
  executable/guard substitution, workflow test removal and README rewriting.
  Each mutation occurs in a disposable test copy with restoration checks. Core
  source is not mutated.

The frozen original pilot's additive-only preservation command and PR15's root
guard intentionally reject this composed root. They are preserved and checked
against their own origins; those refusals are not silently redefined as PASS.
This outer version proves exactly the allowed composition instead.

## Replay and CI

New campaign: Windows x64, Python 3.12.10, Node 22.15.0; all nine Python wheels
remain exactly pinned from the pilot. The new GitHub job uses `windows-latest`
and exact setup/action pins. Other platforms for this new compiler environment
are NOT_COVERED. All eighteen inherited workflow families retain their original
commands, triggers, platforms, versions and action pins; twelve only gain exact
view routing and current-to-view checks. Six remain byte-identical.

```powershell
python -B tools/verify_artifacts.py
python -B tools/second_backend_integration/replay.py prepare
python -B -m unittest discover -s tests/second_backend_integration -v
python -B -O -m unittest discover -s tests/second_backend_integration -v
python -B tools/second_backend_integration/ci.py
python -B tools/second_backend_integration/replay.py check
```

The campaign refuses an existing output directory. Use `--out build/another-run`
for a new execution. `--prepared` skips preparation only; source pins and the
grader remain checked and both implementations/mutations actually execute.
Run inherited replay commands from their workflow-defined checked directories.
Results and exact commands for this task are in [REPORT.md](REPORT.md) and
[evidence](../../evidence/erc8004-second-backend-integration-v1/RESULTS.json).

## Claims and limits

The same original 29-vector profile, policy and grader are used. Vyper is a
reference-informed upstream AGPL-3.0-only port, not a clean-room implementation.
The adapter operation loop, EVM, authorization policy and grader are shared.
The six Vyper guard mutations are different from the six historical Solidity
fuzz mutants. No common-model result is promoted to full ERC correctness,
semantic truth, execution permission, real-world independence or external
execution/payment. These are locally executed finite research tests; production
remains HOLD. All original licenses and upstream authorship remain in force.
