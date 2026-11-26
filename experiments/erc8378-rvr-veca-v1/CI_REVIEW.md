# Current settlement CI and historical preservation

Status: ITERATE / Production HOLD. This is single-verifier settlement V1.

Federico's [independent review](https://github.com/trustless-ai/verifiable-execution-claim-authorization/pull/17#issuecomment-7199650050)
reproduced the 33-file payload at `f3a7ff83` from an unprivileged fresh clone.
The environment guidance and preflight below address his three reproduction
findings. That review does not establish independent custody or approval of later
CI-wrapper changes. V1 contracts and the original 33 files remain unchanged.

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

For a manual Linux x86-64 review, start in a fresh full clone at the exact review
SHA. A virtual environment supplies an actual executable named `python` for FFI:

```sh
python3 -m venv .venv
. .venv/bin/activate
python --version
python -m pip install -r experiments/erc8378-rvr-veca-v1/requirements-replay.txt
python -B experiments/erc8378-rvr-veca-v1/ci/replay.py --linux-tools --label fede-review-01
```

The wrapper refuses a missing `python` or a different Python environment before
the campaign. The Solidity FFI argv is literally `python`, not `python3`; a shell
alias is not an executable for `vm.ffi`. A missing command otherwise leaves the
two FFI cases failing at 66/68. Install requirements with the same active `python`.

`forge test --offline` never fetches a missing compiler. `--linux-tools` installs
and SHA-256 verifies Foundry 1.7.1 and solc 0.8.30 **before** offline execution.
Without that flag, preinstall the compiler in the SVM cache, put it on PATH, or
set `FOUNDRY_SOLC` to its executable. The wrapper verifies its hash and
`0.8.30+commit.73712a01` version, then explicitly selects that file for Foundry.
Unix SVM commonly uses `~/.svm/0.8.30/solc-0.8.30`; Windows also uses
`%APPDATA%\svm\0.8.30\solc-0.8.30` (an `.exe` suffix is also supported).

Official compiler hashes are pinned from solc-bin commit
`762a732061b3fdb0cd076f29a9be6d8c3cde293e`:

| Binary | SHA-256 |
| --- | --- |
| Linux amd64 | `f3e987dc6ecebd4bd350c48edcbc320b46cf9e3109bd3fc3d88f1acaf4c428f7` |
| Windows amd64 | `ccbd3ed44d5fbd26fe039702d403421f1212d2e8752e3cbe3bfd074986911586` |
| macOS amd64 | `738dcdc6afddeb505ee4e4ef24f1c1fdba2b8c924e614cbbf5801a5b062dd683` |

Preinstalled binaries must be executable on the host. A hash mismatch refuses
execution; a version or executable-permission mismatch gives a setup diagnostic.
Only Linux amd64 automatic tool installation is provided; other hosts need a
compatible, preinstalled pinned binary and Foundry 1.7.1.

Keep every run label unique. Reusing `fede-review-01` reports
`RUN_LABEL_IN_USE` with the existing directory and preserves all prior evidence.
Retry with `--label fede-review-02`; nothing needs deleting. The label accepts
1-48 ASCII letters/digits/hyphens. Manual outputs are under
`build/erc8378-ci-<label>/`; CI's default `ci-current` retains
`build/erc8378-ci/`. Local failure diagnostics name the private `.stdout` and
`.stderr` files, whose raw contents are not uploaded.

For the original direct `review_replay.py <label> --mutations` command, the old
refusal remains: `gate-v2/runs/<label>-normal`, `-repeat`, `-optimized` and
`gate-v2/mutations/<label>-campaign` must be fresh. Choose a new label for any
retry; do not delete or overwrite earlier evidence. The wrapper above provides
the early setup diagnostics while preserving those original scripts byte for byte.

The CI job uses its fresh checkout and the following default-label commands:

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
