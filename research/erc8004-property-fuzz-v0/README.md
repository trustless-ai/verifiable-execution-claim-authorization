# ERC-8004 bounded property-based conformance experiment

Continuation of the existing workspace on `research/erc8004-property-fuzz-v0`,
base `80c91a09095eca362dbfb69d39d0c01fc31130cf`. This is a local research extension
of the frozen pilot, not a new implementation or a replacement for the pilot.
The original fourteen uncommitted research files were preserved in
`build/fuzz-continuation/checkpoint/inherited-research.zip` before continuation.
The original baseline and smoke reports remain byte-identical.

Read [ARCHITECTURE.md](ARCHITECTURE.md), [PROPERTY_MATRIX.md](PROPERTY_MATRIX.md)
and [FIXTURES.md](FIXTURES.md) for the oracle, obligation sources and transport.
Executed outcomes, recommendation and publication status are recorded in
[RESULTS.md](RESULTS.md). For a clean checkout, first follow dependency preparation
and full replay in [the evidence README](../../evidence/erc8004-property-fuzz-v0/README.md).

## Fixed campaign

Generator `erc8004-structured-sequences/0.1.0` uses seeds **8004, 8299, 8274**,
100 cases per seed, 16 structured state-transition families per seed, four local
EOA actors and a bounded random-walk family. Seeds and the 300 input fixtures were
already present before this continuation; they were not selected from observed
contract results. This is a custom schema-aware bounded generator, not an
Echidna/Forge/Hypothesis run, coverage-guided fuzzing or a statistical proof.

`conformance/erc8004-property-fuzz-v0/fixtures.json` contains inputs and generation
locators; `expectations.json` is produced solely by `model.py`. The harness corpus
joins the two. Applicable obligation IDs are attached per case instead of attaching
the entire catalog to every case. The unchanged pinned recompute-kit grader compares
each observed behavior with its authored expectation.

## Offline replay in the prepared workspace

The existing pinned sources, Hardhat runtime/node_modules and recompute-kit cache
must already be present. Node 22.15.0 and Python 3.12.10 were used. No runtime
installation, provider credential or external chain is required by these commands.
Use fresh output paths: campaign and mutation runners refuse an existing directory.
Run serially because the adapter assembles one shared ignored EVM runner file.

```powershell
Set-Location -LiteralPath 'D:\PAVLO HQ\Workspaces\veca-erc8004-property-fuzz-20261022'
python -B tools/erc8004_fuzz/integrity.py
python -B tools/erc8004_fuzz/generate.py --check
python -B tools/erc8004_fuzz/tests.py -v
python -B -O tools/erc8004_fuzz/tests.py -v
python -B tools/erc8004_fuzz/campaign.py --out build/fuzz-replay/campaign-normal
python -B tools/erc8004_fuzz/campaign.py --out build/fuzz-replay/campaign-repeat
python -B -O tools/erc8004_fuzz/campaign.py --out build/fuzz-replay/campaign-optimized
python -B tools/erc8004_fuzz/mutations.py --out build/fuzz-replay/mutations
```

Existing closure readback, without executing EVM cases again:

```powershell
python -B tools/erc8004_fuzz/verify_results.py --out build/fuzz-continuation/closure-readback.json
python -B tools/erc8004_fuzz/integrity.py
```

`verify_results.py` also checks the preserved baseline/checkpoint, so its default
root is the original evidence directory. Each campaign independently emits its
fixture and behavioral projection digests for comparing a fresh replay. Raw receipt
hashes/timestamps may differ; the portable behavioral projection is the reproducibility
target. `-O` propagates into the Python adapter; the EVM and Solidity compiler stay
the same. This is Python optimization robustness, not a second EVM implementation.

## Physical controls and minimization

Six isolated Solidity variants remove one guard or summary filter at a time.
For each variant the runner executes a generated witness and three positive controls
on pristine source, runs the unchanged 29-case deterministic matrix on the variant,
runs the generated witness on the variant, minimizes through fresh EVM execution,
then restores the same source copy byte-for-byte and reruns the original controls.
The actual implementation checkout is never edited. Every trial, receipt and source
digest is retained, including the original and minimized input.

A kill requires a determinate behavioral divergence with positive controls still
passing and pristine restoration passing. Infrastructure errors do not count.
Shrinking preserves the divergence category and tries deletion of every single call
until none preserves it, plus bounded value simplification. The result is 1-minimal
under nonempty single-call deletion in this fixture domain, not a global minimum.
These deliberately broken variants are sensitivity controls, not discovered
vulnerabilities in the unmodified upstream contracts.

## Integrity boundary

The exact original root inventory is preserved as `baseline-inventory.json`, checked
against the base Git blob. The current root inventory adds only deliberate new files;
all original 12,667 entries and frozen Core remain byte-identical. The unchanged
complete-inventory verifier still checks the entire checkout. The research extension
also has a finite `campaign-lock.json`, covering its source/docs and isolated workflow.
The research checker validates pinned implementation/specification/bootstrap bytes
and the preserved baseline/smoke checkpoint. `--seal` is only for intentional source
updates; ordinary replay uses check mode. These hashes are not an attestation.

Historical workflows are unchanged. The new isolated workflow executes the full
generated campaign and all required regression checks. This PR is stacked on #10;
publication does not merge or modify its base branch.
