# Independent review package v1

This is a finalization of `a730515a0d7cfc04f52d137d44f3e92f99f972ee`, not a new
proof system or replacement policy. VECA base remains
`999e7047df15585f8ce0629081a1369a4942353f`; FlashProve stays pinned to
`ea1b613625513a658942af4bc79867d1c77412cd`. Review the exact enclosing commit,
not an unpinned moving branch.

## Inventory mechanism

The unchanged `tools/verify_artifacts.py` requires a complete file inventory; it
does not have an extension-file discovery feature. Its established current
manifest is versioned in Git. Existing role-policy preservation checks prove
historical subsets against prior Git manifests while allowing current additions.
This finalization uses that same additive mechanism, not a new checker exception.

`baseline-inventory.json` is the exact original 12,739-entry root manifest, SHA-256
`5e20a46f3004a4afa869ca014accc7505cb9a3c7ae0536fb7c8cc9909700b30a`.
`original-research-inventory.json` is the exact a730515 research manifest, SHA-256
`75ac489fb940a1491d9b1d45f784e0e99bad741f2d2d1efdd2dbeb6a67eebe1b`.
Both are compared with their original Git blobs. The current root adds only paths
under this research directory. Every old key/digest and every old file byte must
still match. No exclusions, checker logic or old digest are changed.

The original source pin for the root manifest continues to identify the preserved
historical manifest. `prepare.py` now requires a bounded additive registration
instead of wrongly requiring the current extended file to equal that old blob.
Seven other VECA reuse pins and all 26 FlashProve source pins retain direct byte
checks. `transitions.json` explains exactly six research source/document updates.
All original fixtures, native/consumer implementations, tests, mutations, source
pins and raw evidence remain unchanged. The active research inventory is v1;
its original v0 bytes are preserved, not overwritten in history.

Maintainer-only registration command (not needed for replay):

```text
python -B research/flashprove-8274-claim-boundary-v0/review_v1/register.py --write
```

It refuses any historical mismatch or unapproved research transition before
writing. It copies old digest entries rather than recomputing them. Never use
blind `tools/verify_artifacts.py --write` to hide a failure.

## Exact replay

Clone with LF before checkout (`core.autocrlf=false`, `core.eol=lf`), fetch full
history, and detach at the exact candidate SHA. Require clean `git status`.
From that checkout run:

```text
python -B research/flashprove-8274-claim-boundary-v0/prepare.py --runtime
python -B research/flashprove-8274-claim-boundary-v0/review_v1/replay.py --legacy --out build/flashprove-review-v1
python -B research/flashprove-8274-claim-boundary-v0/review_v1/archive.py --replay build/flashprove-review-v1 --out ../flashprove-review-v1.zip
git diff --check
git status --porcelain
```

`--legacy` executes existing RVR composition, harness, ERC-8004 and role-policy
v1/v2 validators and reconciliation tests unchanged. It needs their existing
public pinned dependencies (including Node/npm, Python and Rust where the old
preparation requires it). Missing tooling is a failed environment gate, not a
semantic mutant kill. No live chain or confidential input is used.

Required new counts in EACH normal/repeat/optimized mode: 54 scenarios, 15 original
regression tests, 29 physical mutation kills, 6 distinct non-kill controls,
8 inventory tests, 3 reproduced counterexamples and 3 result-tamper controls.
Commands, exit codes, stdout/stderr, complete native output, graded projections,
source restoration and source/evidence hashes are retained. Timing logs and
absolute command paths are not expected byte-identical. Full deterministic native
stdout, request, projection and mutation result JSONs must match exactly.

The archive has sorted paths and fixed ZIP member metadata. Building it twice
from identical replay bytes must yield the same SHA-256. It includes the original
raw evidence ZIP unchanged, all new raw replay files, source documents, exact HEAD,
current inventory, binary diff and an internal payload hash manifest. Post-commit
evidence is kept outside source to avoid a self-referential commit/hash claim.

## Reviewer checklist

- Confirm exact base, candidate HEAD and read-only reference source SHA.
- Root checker exits 0; all old 12,739 entries retain their values.
- Original manifest snapshots match both recorded digests and Git blobs.
- Missing/modified/substituted research file and unlisted-file controls each fail
  at the intended inventory relation; repinning historical tampering still fails.
- Frozen RVR Core stays 13/13; historical survivor stays SURVIVED.
- All original 54 case expectations, 29 predicates, 6 classifiers and native
  consumer outputs remain unchanged.
- Run A/B/C separately using COUNTEREXAMPLES.md. Check caller, task, contract,
  chain, committee and proof-byte evidence rather than PASS markers alone.
- Check each physical mutation applies exactly once, with the named negative
  witness and a healthy control. CRASHED and absent output are not kills.
- Distinguish mock acceptance, actual cryptographic proof, policy permission and
  execution; positive attestation remains NOT_IMPLEMENTED.
- Confirm source restoration, deterministic comparisons and archive hashes.
- Inspect actual CI statuses if a branch is published; no dedicated new FlashProve
  CI job is implied. Existing workflows are unchanged.

## Refusal and remaining limits

Any genuine inventory, preservation, conformance or mutation failure blocks
publication and a READY verdict. Do not repair frozen hashes or weaken the gate.
An unavailable runtime is an environment blocker, not a semantic finding.
No SP1 soundness, production exploit, real attester independence, production
authorization, public-chain finality, order execution or independent reviewer
acceptance is established by these self-replays. The three findings describe the
pinned implementation and a documented laboratory threat model only.
