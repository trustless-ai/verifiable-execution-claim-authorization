# Captured ERC-8004 property research evidence

This package preserves actual execution captured before publication. SUMMARY.json
and COUNTEREXAMPLES.json are byte-exact copies of the completed local closure;
their recorded uncommitted/no-publication status describes that historical phase.
Current publication/replay status belongs to the research report and PR.

EVIDENCE.zip includes the original 29/29 baseline and 17/17 physical controls,
ERC-8404 regression, 300 generated cases with seeds 8004/8299/8274, normal/repeat/-O
reports, all six mutant pristine/modified/restored runs, positive controls,
original/minimized counterexamples and every EVM shrink trial, source-restoration
copies/digests, command logs, environment/pins, and prior integrity/checkpoint data.
Old absolute paths inside raw argv are historical provenance, not portable commands.
Archived source/docs represent the original execution snapshot and are never
extracted over current source. The publication changes packaging and replay checks,
not the generator, state model, adapter, executor or mutation semantics.

No caches, node_modules, credentials or installed dependencies are included.
Archive entries are lexically sorted with fixed timestamp 2026-10-22 00:00:00.
SHA256.json records every loose file except itself and every ZIP member. Hashes
identify bytes; they are not provider authentication or an external attestation.

## Fresh clone and replay

Use a full Git checkout containing base commit
80c91a09095eca362dbfb69d39d0c01fc31130cf. Use Python 3.12 and Node 22.15.0 with npm.
Run from the repository root, serially. Dependency preparation accesses only public
pinned source/package downloads; it does not submit transactions to a network provider.
The existing preparation scripts reject source digest mismatch and npm uses lockfiles.

```text
git clone --branch research/erc8004-property-fuzz-v0 https://github.com/trustless-ai/verifiable-execution-claim-authorization.git veca-property-replay
cd veca-property-replay
git checkout --detach <exact-PR-head-SHA>
python -B tools/verify_artifacts.py
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B research/formal-v1/prepare_crypto.py
npm ci --ignore-scripts --no-audit --no-fund --prefix build/formal-v1/crypto
python -B tools/erc8004_fuzz/validate.py --out build/property-replay
```

Use a new --out directory for another run. validate.py verifies/extracts historical
evidence into ignored build paths (refusing conflicting existing files), then runs
all 300 cases normal/repeat/-O, six new physical controls with shrinking/restoration,
15 infrastructure tests in both modes, original pilot/17 mutations/ERC-8404 regression,
pinned source/dependency checks and original Core/history checks. Failures and logs
are retained; missing dependencies or failed setup never count as passing tests.
The actual harness transports inputs only; expected outcomes remain outside the IUT.

For readback without rerunning contracts after dependency preparation:

```text
python -B tools/erc8004_fuzz/package.py --extract
python -B tools/erc8004_fuzz/verify_results.py
python -B tools/erc8004_fuzz/integrity.py
```

Fresh-checkout results, when added, are a separate evidence phase and do not replace
the preserved historical runs. See ../../research/erc8004-property-fuzz-v0/RESULTS.md
for interpretation, limitations, recommendation and independently reviewed scope.

## Completed fresh replay

FRESH-REPLAY.json records actual passing execution at `d0d1a4cb1bda7d1217da99a2f6a010859cdf8ad5`.
FRESH-SOURCE-PROOF.json binds the final publication to the same executed code/fixtures.
EVIDENCE.zip preserves all previous members and adds newly executed raw reports under
`fresh-checkout/`, plus dependency setup receipts. Extraction deliberately leaves
these supplemental captures inspectable in the archive instead of overwriting a
caller's fresh run. See the research FRESH_REPLAY.md for the precise evidence boundary.
