# Fresh committed-checkout replay

Actual replay completed in `D:/PAVLO HQ/Workspaces/veca-property-fresh-20261022`,
an isolated `git clone --no-hardlinks` of the research repository, detached at
`d0d1a4cb1bda7d1217da99a2f6a010859cdf8ad5` (tree `9b44bd7b2b3760ebe5f5cfe8b47836c50b7e6b4c`). No source or node_modules was shared through
a junction. Public byte-pinned sources and lockfile dependencies were prepared anew.
This is fresh-checkout reproducibility, not a second independent implementation.

The full `python -B tools/erc8004_fuzz/validate.py --out build/property-replay` command
passed: 300 cases in each normal/repeat/-O run, 1195 EVM calls each, six new physical
mutants KILLED, original 29-case comparison missing all six, real EVM shrinking and
passing positive/restoration controls. All 15 infrastructure tests pass in both
modes. The original pilot was also rerun: 29/29 in all three modes, 17/17 original
mutants killed, ERC-8404 18/18, source/dependency and Core/history checks passing.

All three fresh projections match the historical digest
`98cc0633b9add940124458a1f8cfe46ccec2606347e9cef5ff9101616075229c`.
Setup receipts retain exact argv, cwd, exit code, elapsed time and output hashes.
No missing dependency/setup failure is counted as success. Fresh result files are
distinct from historical evidence under `fresh-checkout/` inside EVIDENCE.zip.

The following publication-closure commit changes only documentation, archived fresh
evidence and their inventories/seals. `FRESH-SOURCE-PROOF.json` pins every executed
research code/fixture file; the final detached checkout is checked against these
same bytes. The final exact-head GitHub workflow also performs a full fresh replay.
GitHub CI outcomes are recorded separately in the PR/publication report, not inferred
from this local pass.

See ../../evidence/erc8004-property-fuzz-v0/FRESH-REPLAY.json and
../../evidence/erc8004-property-fuzz-v0/FRESH-SOURCE-PROOF.json for machine evidence.
The original unmodified contracts have no observed violation in this finite corpus;
independent implementation coverage remains NOT_COVERED. Recommendation: INTEGRATE
this additive regression/research profile after independent review, not universal
security/conformance certification.
