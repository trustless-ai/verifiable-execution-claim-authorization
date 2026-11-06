# FlashProve ERC-8274 claim boundary v0

Independent, finite VECA research experiment by Pavlo Tvardovskyi. Not normative,
not a credential issuer, not production security certification.

The exact upstream Solidity is executed in an ephemeral in-process EDR EVM.
Constructor/call transactions exist only in that simulation. There is no HTTP
RPC listener, public chain connection, key export, or external contract deployment.
Upstream `MockSP1Verifier` is explicitly a test double. Upstream attestation
signature recovery is unimplemented and returns zero. There is **no successful
cryptographic ZK proof or accepted attestation claimed by this experiment**.

`policy.py` is a small laboratory consumer, not another verification engine. It
returns separate states for ZK proof, attestation, claim authorization, action
authorization and order execution. `VERIFIED` is not synthesized from an EVM
boolean. The existing VECA transport and pinned recompute-kit grader perform the
conformance comparison. A test PASS means agreement with an independently
authored finite expectation; it grants no execution permission.

## Replay

From the repository root, with Python 3.12+, Node 22 and npm available:

```text
python -B research/flashprove-8274-claim-boundary-v0/prepare.py --runtime
python -B research/flashprove-8274-claim-boundary-v0/validate.py --out build/flashprove-8274/normal
python -B research/flashprove-8274-claim-boundary-v0/validate.py --out build/flashprove-8274/repeat
python -B -O research/flashprove-8274-claim-boundary-v0/validate.py --out build/flashprove-8274/optimized
python -B research/flashprove-8274-claim-boundary-v0/mutations.py --out build/flashprove-8274/mutations-normal
python -B -O research/flashprove-8274-claim-boundary-v0/mutations.py --out build/flashprove-8274/mutations-optimized
python -B research/flashprove-8274-claim-boundary-v0/preservation.py --out build/flashprove-8274/preservation.json
python -B research/flashprove-8274-claim-boundary-v0/verify_evidence.py
git diff --check
```

Preparation downloads public, pinned source/dependencies into ignored `build/`.
It reuses `tools/erc8004/prepare.py`, its exact npm lock, Hardhat configuration,
and the existing `tools/agent_harness.py` grader. It never downloads private inputs.
For offline source preparation, `--source <exact-read-only-FlashProve-checkout>`
is supported; every file is still hash-verified.

`generate_vectors.py` reconstructs the authored oracle, without importing the
consumer or executing the implementation. The first 54-case oracle was frozen
before the first EVM run and did not need an expectation change. Do not regenerate
expected values from adapter output.

## Input and trust boundary

Each fixture separates `operation`, untrusted `claim`, and trusted laboratory
`policy_fixture`. The last is selected by the experiment invocation, never by an
untrusted receipt. `lab-v0` selects two deterministic EDR accounts and an explicit
operator mapping. The adverse policy fixtures deliberately assume one operator,
a revoked key, or no admitted signers. These assumptions are not real-world
beneficial-ownership or revocation proofs. The consumer cannot bootstrap trust
from a caller-selected production policy: no production bootstrap is implemented.

The EVM bridge obtains chain ID from RPC, committee membership and threshold from
contract getters, actual target/caller addresses from the simulation, and checks
the emitted verification digest independently. Native fields remain evidence,
including accepted mock calls that the consumer refuses to promote.

Malformed transport, absent required expectations, missing/extra observations,
empty corpus, missing stdout and execution failure produce exit 2 through the
existing harness. A completed result that contradicts an expectation produces
exit 1. Pin mismatches remain infrastructure refusals, not semantic kills.

## Preservation and integration

All new files are confined to this directory. See [REPORT.md](REPORT.md),
[MUTATION_REPORT.md](MUTATION_REPORT.md) and [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md).
The existing complete root inventory deliberately remains unchanged. Therefore
`python -B tools/verify_artifacts.py` on this branch reports unregistered research
additions and exits 1. This is **not** green canonical CI or merge readiness.
`preservation.py` proves that every existing entry still matches; it does not
replace the root inventory gate.

## Provenance

VECA main: `999e7047df15585f8ce0629081a1369a4942353f`.
FlashProve: `ea1b613625513a658942af4bc79867d1c77412cd`.
Exact paths and SHA-256 digests: [SOURCE_PINS.json](SOURCE_PINS.json).

Reference authors own their original work. FlashProve's repository carries
Apache-2.0, NOTICE and THIRD_PARTY notices; the inspected Solidity files carry MIT
SPDX. Original files are fetched unchanged into build cache, not relicensed.
The new independent VECA experiment follows this repository's MIT license.
Mutation predicates are attributed excerpts from the exact files named in the
catalog. Existing ERC-8404 Core, specifications, vectors, licenses and source
locks remain untouched.
