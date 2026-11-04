# Baseline reconciliation execution evidence

New author-operated Windows runs, separate from all frozen historical packages.
SUMMARY.json identifies the tested source files and source/merge parent commits.
EVIDENCE.zip preserves exact document bytes, comparisons, commands, stdout/stderr,
baseline/mutant/restored observations, positive controls and source identities.
SHA256.json records archive and member hashes. ZIP order/timestamps are fixed;
raw runtime timing/path metadata is preserved, so separate executions need not
have identical archive hashes. Build caches and installed dependencies are absent.

These are candidate-tree results, not a claim of independent organizational review
or GitHub CI. The PR records the final commit and later exact-head CI separately.
Reproduction commands: ../../research/baseline-reconciliation-v1/README.md.
