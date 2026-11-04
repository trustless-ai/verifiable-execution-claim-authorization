# PR11 baseline reconciliation v1

PR #10's inherited ERC-8004 integrity gate rejected the GitHub test merge with
its current base because two documentation files had the reviewed PR #11 bytes.
The source-head gate passed because that tree still had the original bytes.
This addition makes those two states explicit without changing historical pins,
execution expectations, consumer guards, the harness transport, or the grader.

## Exact provenance

- Original harness baseline: `0e17c97e896916b4d9505072cc9ebe2018329b01`.
- Frozen ERC-8004 pilot: `80c91a09095eca362dbfb69d39d0c01fc31130cf`.
- Supplemental PR #11: `e5263f47325a81b0647f3de3a7bc36ad858aea5a`.
- PR #9 after integrating #11: `25f7c45f20cfd4f892f7387cd3d3842105d8b214`.
  Its tree is identical to the exact #11 source tree.
- PR #10 before this reconciliation: `aee0f9fe9aab1c90807846a6e37999be27265af2`.
- GitHub test merge before this reconciliation:
  `a6e0c6011a92c78b34ed929e992e444912a891cb`.

The documents originated at `b80f0ec6592642226e504025cf6785ed1b1bf797` and were
extended in #11. [DOCUMENT_COMPARISON.json](DOCUMENT_COMPARISON.json) records
Git blob IDs, full SHA-256, lengths and commit history. The exact textual changes
are in [documentation.diff](documentation.diff). The README adds full-clone
prerequisites and a supplemental-controls link; LIMITATIONS records that the old
18 vectors did not distinguish four existing policy guards. Neither changes an
ERC requirement or the original scenario results.

| File | Historical SHA-256 | Exact #11 SHA-256 |
| --- | --- | --- |
| `conformance/agent-harness-v0/README.md` | `cacfd2e3c9ce216fc318044fc08d96ed56d1fa9322ceabd3aaec764bd124eb66` | `19aecd97a84bb78ae1d65791193b92e90f46dda1badc72ecc754b29d88558f04` |
| `research/harness-v0/LIMITATIONS.md` | `b4656d1261f4f1b7eb88bbc9af88d9a8f9a32e1472e42dd337b5708b967d3fb8` | `074b81b07e3b4d679e91e6d83e7d969986b8a67a1e574633280fccf6aaaab882` |

## Bounded preservation policy

`tools/baseline_reconciliation/policy.py` implements
`veca-pr11-baseline-reconciliation-v1`. It checks the original Git inventories
against independently fixed manifest SHA-256 values. It admits either both
original documents without the supplemental payload, or both exact #11
documents with **all 13 exact supplemental files** and matching current
inventory entries. Mixed states, changed bytes, missing payload and resealed
corruption fail. Missing historical Git objects are a prerequisite failure.

The existing ERC-8004 integrity entry point delegates its historical-byte check
to this versioned policy. Source/dependency checks and the 451-file historical
evidence seal remain intact. The role-policy preservation entry point uses the
same policy and retains all reused-source and implementation/specification pin
checks. The precisely hashed update of `tools/erc8004/integrity.py` is recorded
as a separate checker transition when compared with the pilot commit; it is
not attributed to #11 and is not described as an unchanged historical file.

The old manifests, source locks, reports and archives are not rewritten.
`unchanged_baseline_files` counts actual unchanged bytes. Reviewed transitions
are listed separately. This policy does not automatically authorize later
changes, rebase a branch, establish conformance, or update #12/#13's policies.
The branch keeps the original documents; the PR merge tree exercises #11's
documents. Both sets of tests are retained in that composition.

## Reproduction

Use a full clone with LF checkout, Python 3.12 and Node 22.15.0. Preserve the
historical Git objects above. From the checkout root:

```sh
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B research/formal-v1/prepare_crypto.py
npm ci --ignore-scripts --no-audit --no-fund --prefix build/formal-v1/crypto
python -B tools/verify_artifacts.py
python -B -m unittest discover -s tests/baseline_reconciliation -v
python -B -O -m unittest discover -s tests/baseline_reconciliation -v
python -B tools/erc8004/validate.py --out build/reconcile/legacy
python -B -O tools/erc8004/mutations.py --out build/reconcile/legacy-optimized
python -B tools/erc8004_role_policy/validate.py --out build/reconcile/roles
```

On the composed checkout also run the unchanged original and supplemental gates:

```sh
python -B tools/harness_v0/validate.py --out build/reconcile/harness
python -B -O tools/harness_v0/mutations.py --out build/reconcile/harness-optimized
python -B tools/harness_v0/review_validate.py --out build/reconcile/review
python -B tools/verify_artifacts.py
```

Run ERC-8004 validation and role-policy validation sequentially: the historical
infrastructure controls temporarily alter their shared cached Solidity source.
Do not classify that deliberate setup failure as a successful conformance run.

The new workflow uses the default pull-request merge checkout, including the
role-policy validator; it does not substitute the PR source head for the merge
tree. Existing workflows remain unchanged. Windows local evidence and Linux
Actions are distinct execution sources; neither is independent organizational
certification. No merge or readiness approval is implied.

See RESULTS.md and the separate evidence package for actually executed results.
