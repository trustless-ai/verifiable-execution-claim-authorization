# Current settlement CI and historical preservation

Status: ITERATE / Production HOLD. This is single-verifier settlement V1.

The original 33 review files and their public samples remain byte-identical to
`f3a7ff83f639c92508e15069d7ca522b7abe92b4`. The previous CI stopped before test
execution: the complete inventory did not list the additions, and the exact
documentation transition refused extra membership. Prior local settlement
results did not constitute a passing repository CI run.

`ci/transition.py` authenticates the complete current tree against the immutable
VECA main `29155372c6a16f23d1bc2091f2f3671c51e0da4c` and its pinned inventory,
the exact 33-file review payload, a fixed new-CI file list, and deterministic
workflow routing. It rejects resealed historical/Core/payload substitutions,
extra files and removal/replacement of old CI commands or action pins.

The only existing file changes are the root inventory and mechanical routing of
18 workflows. All old commands, tool pins, triggers and historical checkers are
preserved. Those workflows run in `build/erc8378-baseline`, an authenticated Git
worktree at the exact main baseline. The previous documentation replay boundary
still runs inside that view. A receipt names the actual current head and exact
historical tree; preparing a view does not mean its tests passed.

The separate **ERC8378 current verifier-gated settlement V1** workflow runs the
current payload in a build copy, independently of historical workflow outcomes:

```sh
python -B tools/verify_artifacts.py
python -B experiments/erc8378-rvr-veca-v1/ci/transition.py check
python -B -m unittest discover -s experiments/erc8378-rvr-veca-v1/ci -v
python -B -O -m unittest discover -s experiments/erc8378-rvr-veca-v1/ci -v
python -B -m pip install -r experiments/erc8378-rvr-veca-v1/requirements-replay.txt
python -B experiments/erc8378-rvr-veca-v1/ci/replay.py --linux-tools
```

Use a fresh clone with full Git history and no generated dependencies outside
`build/`. On an existing Windows machine with Foundry 1.7.1 / solc 0.8.30 already
installed, omit `--linux-tools`. Pinned dependency downloads verify 110 hashes.
Linux Forge and solc binaries have hardcoded SHA-256 pins in `ci/replay.py`.
Normal/repeat/-O must each return 68 contract, 48 offline and 43 issuer checks;
20 physical mutations must be KILLED, with zero SURVIVED or INVALID. A separate
offline invocation checks the generated public evidence after issuer credentials
have been deleted. These are required expectations, not a claim about a run that
has not completed. Consult the exact-head GitHub run and its execution receipt.

Only seven explicitly selected public JSON result files are uploaded. Runtime
keys, raw logs, dependency trees and private evidence ZIPs are excluded. Existing
evidence is never overwritten. CI source authenticity ultimately rests on review
of the immutable commit; a checker cannot authenticate its own malicious rewrite.

The old ERC8404 integrity checker also pins five historical workflow files, so
it runs unchanged in the authenticated baseline view. The current complete-tree
check separately demands identical Core/source/evidence bytes and exactly the
mechanically routed workflow bytes. A legacy integrity refusal in the current
extended tree is an expected old-contract refusal, never relabeled as a pass.

Historical tests cover their pinned tree. The current job covers the new gate;
neither proves off-chain assessment truth or independent operational key custody.
A compromised authorized verifier remains able to approve fabricated evidence.
No Core, historical evidence, specification or existing integration source is
modified. No merge, public-chain deployment or production approval is performed.
