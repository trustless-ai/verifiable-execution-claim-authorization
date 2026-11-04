# AgentWallet role policy v2 execution evidence

New author-operated Windows evidence; historical v0/v1 packages remain unchanged.
SUMMARY.json identifies tested candidate code hashes and both parent trees.
EVIDENCE.zip contains actual requests, raw observations, grader reports, command
receipts, source pins, original Echo reproduction, normal/repeat/-O comparisons,
and every mutation's baseline/positive/mutated/restored evidence. Deterministic
ZIP ordering/timestamps and SHA256.json protect all members. Dependencies/caches
are excluded. Timing and absolute path metadata in raw results are preserved.

The development-mutations folder is explicitly NOT a successful final campaign:
its final preservation guard detected a concurrent author refinement of the source.
DEVELOPMENT_NOTES.json explains this exit 1. Final validation uses the frozen source
and is kept under validation; no preliminary failure is relabeled a pass.
The completed pre-classifier-refinement run is also retained separately. The final
classifier labels incomplete required behavior as MISSING_OUTPUT, not SURVIVED;
both are non-kills. Final source validation was rerun after that refinement.

Fresh committed-checkout and exact-head GitHub CI results are recorded separately
after the commit, not invented inside this pre-commit archive. Author replay does
not imply independent organizational acceptance. See the versioned research README
for exact dependency preparation and replay commands.
