# ERC-8004 property-based conformance: executed research closure

## Publication and research recommendation

**Recommendation: INTEGRATE** as an additive bounded research/regression profile,
subject to independent review. Six concrete guard/filter regressions missed by the
unchanged 29-case deterministic matrix are detected by generated witnesses; pristine
and restored sources pass. This supports retaining the new coverage alongside the
original matrix, not replacing it or claiming universal conformance/security.
No observed defect in the unmodified upstream contracts was found.

Publication is stacked on PR #10, branch feat/agent-harness-erc8004-v0, exact base
80c91a09095eca362dbfb69d39d0c01fc31130cf. Main and PR #9/#10/#11 are not modified.
The historical local closure below remains an account of its execution phase.
Its former "uncommitted/no publication" statements do not describe the later PR.

The published evidence is in ../../evidence/erc8004-property-fuzz-v0/. Its README
contains dependency preparation and exact serial replay commands. SHA256.json seals
loose files and every deterministically ordered/timestamped archive member. The
original root inventory is preserved byte-exact as baseline-inventory.json; the
current root inventory is extended only for intentionally added research/evidence
and the isolated research workflow. All 12,667 historical entries remain unchanged.
Historical workflows and check logic remain byte-identical. The separate research
source seal and existing complete repository inventory both remain enforced.

Fresh committed-checkout replay passed on commit `d0d1a4cb1bda7d1217da99a2f6a010859cdf8ad5`. See
[FRESH_REPLAY.md](FRESH_REPLAY.md) for exact execution identity, dependency preparation,
new raw evidence and the unchanged-code proof for the publication closure. All three
300-case runs, six new mutants, the original 29-case/17-mutant pilot and Core checks passed.

### Reuse for ERC-8299 and ERC-8274

Reuse the fixture layers, seeds/locators, expectation-free transport, explicit
obligation categories, state-machine oracle interface and replay-based shrinking.
The existing registry sequences can provide identity/ownership preconditions in a
composition experiment, but the 300 current inputs are not direct conformance vectors
for either new ERC. ERC-8299 requires its actual input/transform/signature schema,
normative Section 5 obligations and separate evidence-policy assumptions. ERC-8274
requires a pinned concrete verifier, exact public-input/statement binding and actual
native proof verification. Each needs independently authored expectations, its own
positive/negative controls and physical mutations. Do not infer data truth, proof
validity or expanded authorization from the present registry observations.

Same-profile independently authored second ERC-8004 implementation: **NOT_COVERED**.
No Foundry, Echidna or differential EVM fuzzing execution is claimed. The next step is
independent replay/review of this contribution and then a separately pinned compatible
backend; preserving these limits is part of the integration recommendation.

---

Completed locally on 2026-10-22 in the existing workspace. **300/300 generated cases
passed** against the pinned real Identity and Validation Registry implementations.
Normal, repeat and Python optimized runs each passed all 300 cases with identical
portable behavioral projections. **Six physical source mutants were killed**, with
fresh replay-based minimization and byte-exact restoration passing in every case.
No counterexample to the unmodified implementation was found in this bounded domain.

## Historical local execution identity and preserved work

- Repository: `trustless-ai/verifiable-execution-claim-authorization`.
- Historical execution branch: `research/erc8004-property-fuzz-v0`; then-current base/HEAD `80c91a09095eca362dbfb69d39d0c01fc31130cf`.
- Workspace: `D:/PAVLO HQ/Workspaces/veca-erc8004-property-fuzz-20261022`.
- Specification: `ethereum/ERCs@503591a6e80e6e1affdd6403341e25269141f046`, Draft ERC-8004.
- Implementation: `erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`.
- Grader: `trustless-ai/recompute-kit@f7308cdd5ba55ac8229103e82ebc5fc14f81b88b`.
- Execution: local Hardhat 3.0.6, ethers 6.15.0, solc 0.8.24, OpenZeppelin 5.4.0,
  Node 22.15.0, Python 3.12.10. One implementation and one EVM backend.

All prior tracked files, frozen Core, harness protocol, grader pin, authorization
projection, original profiles and source inventory remain unchanged. The fourteen
inherited uncommitted research files were backed up before edits. The original
baseline and smoke evidence remain preserved. During that historical local phase,
no reset, clean, reinitialization, commit, push, new PR, merge or network-provider
execution was performed. The new research directories were then untracked; the
subsequent publication phase commits them and its separately recorded evidence.

## What was completed

The inherited smoke covered only 16 cases. Continuation inspected its generator,
oracle, transport, real EVM executor and source locks; added serial full-campaign
execution, real physical mutation comparisons, EVM-based shrinking, integrity and
closure readback, infrastructure tests and replay documentation. The 300 inherited
input fixtures remained byte-identical. Expected event coverage now includes ERC721
Transfer/Approval/ApprovalForAll. Obligation references are selected by the operations
actually present in each case rather than attaching the entire catalog to every case.

The independent Python transition model takes only symbolic inputs. It does not read
EVM results or import the implementation/authorization adapter. The unchanged harness
sends only IDs and inputs to the adapter; expectations, obligations, property-family
labels and mutant IDs do not enter that request. A deliberately incorrect expectation
was rejected by the actual pinned grader. A tampered suite pin was rejected before
adapter execution. This is an authored oracle with explicit assumptions, not an
independent organization attestation or proof of oracle completeness.

## Full fixed campaign

Seeds **8004, 8299, 8274**, **100 cases each**, generator
`erc8004-structured-sequences/0.1.0`. These seeds predated the continuation.
Every seed exercises all 16 structured families, including a bounded random-walk
family. Sequence lengths are 2-8 calls; four local EOA actors are used.

| Run | Cases | EVM calls | Result |
| --- | ---: | ---: | --- |
| Normal | 300 | 1195 | PASS |
| Repeat | 300 | 1195 | PASS |
| Python `-O` | 300 | 1195 | PASS |

These are 300 generated case IDs, **243 distinct complete inputs**
and **186 distinct operation sequences**. Replays are not new
coverage: the three runs total 900 case executions and 3585 EVM calls over the same
fixed corpus. Shrinker trials, physical controls and original-matrix comparisons are
separate from that budget. The campaign is custom schema-aware generation; no
Hypothesis, Echidna or Forge campaign was executed.

Each run observed **902 accepted calls and 293 reverted calls**, with modeled state
checked after every call. No generated rejection was filtered out.

| Operation | Accepted | Reverted |
| --- | ---: | ---: |
| approve | 21 | 0 |
| metadata | 54 | 71 |
| operator | 96 | 0 |
| register | 357 | 18 |
| request | 126 | 54 |
| respond | 98 | 46 |
| transfer | 59 | 11 |
| unset | 11 | 24 |
| uri | 45 | 32 |
| wallet | 35 | 37 |

Boundaries include metadata values of 0/1/31/32/33/64 bytes, all three registration
overloads, owner/token-approved/global-operator permissions and revocation, transfers
and old-owner follow-up calls, wallet deadlines -1/0/1/299/300/301/600 seconds relative
to the next transaction, signature-domain/subject/owner errors, validation responses
0/1/50/99/100/101/255, and allowed repeated response updates. Not every possible
permission or ABI combination is covered.

Authorization per run: **57 VERIFIED, 222 REFUTED, 21 UNVERIFIABLE**. These statuses
are distinct from the **300 conformance PASS** results. VERIFIED is only the existing
`LAB_REGISTRY_TRANSITION` scope for the final call. A correct refusal can be PASS with
authorization REFUTED; withholding a receipt from the authorization projection yields
UNVERIFIABLE while raw execution remains retained. No task-completion, payment or
general verified-execution claim is promoted from registry success.

Fixture SHA-256: `38d8d24f95277e385312565bf0b5e451de4668dbfd1ca98dcc121d72bdd1e85c`.

Portable projection SHA-256, identical across all three runs:
`98cc0633b9add940124458a1f8cfe46ccec2606347e9cef5ff9101616075229c`.

Raw transaction hashes, addresses and timestamps are retained in evidence; their
byte identity is not the portable reproducibility claim.

## Comparison with the deterministic matrix and physical mutants

The inherited 29/29 deterministic baseline, 17/17 killed physical mutations,
18/18 ERC-8404 regression and source-integrity results were already executed. Their
reports and command receipts were verified and preserved, not relabeled as new runs.
The unchanged 29-case matrix was additionally executed against each of the following
six new physical source variants, using the same exact variant as the generated test.

| Removed guard/filter | Original 29-case matrix | Generated witness | Calls before -> after shrinking | Divergence |
| --- | --- | --- | ---: | --- |
| registration_reserved | PASS | KILLED | 3 -> 1 | status:register |
| metadata_authority | PASS | KILLED | 3 -> 1 | status:metadata |
| unset_authority | PASS | KILLED | 3 -> 2 | status:unset |
| wallet_future | PASS | KILLED | 2 -> 2 | status:wallet |
| response_range | PASS | KILLED | 3 -> 3 | status:respond |
| summary_unanswered | PASS | KILLED | 6 -> 3 | state:summaries |

The original matrix missed **6/6** of these deliberately introduced
changes: `registration_reserved`, `metadata_authority`, `unset_authority`, `wallet_future`, `response_range`, `summary_unanswered`. This establishes additional
sensitivity for these specific mutants only, not a completeness score or evidence
that all kinds of regressions are detected. The original 17 controls and these six
controls are separate mutation populations.

Every kill required a determinate mismatch, three positive controls still passing,
an initially passing pristine witness and a passing replay after the same physical
source copy was restored byte-for-byte. No crash, missing execution or unsupported
result counts as a kill. All original implementation source bytes remain unchanged.

Every original/minimized witness, simplification trial, fresh EVM receipt and source
digest is retained under `build/fuzz-continuation/mutations/<id>/`. Shrinking preserves
the observed divergence category, attempts all single-call deletions and bounded
value simplifications, and replays the final witness. Results are deletion-1-minimal
over nonempty sequences in this fixture domain; **global minimality is not claimed**.
A reduced sequence can expose the same removed guard with a different prerequisite
state; the original generated witness remains available. These counterexamples apply
to test-only mutants, not the unmodified upstream implementation.

## Integrity, source boundaries and future differential testing

The research checker separately validates the original 12,667-entry inventory, pinned
specification/implementation/bootstrap, the new finite research-source seal, all 456
inherited baseline/smoke evidence files and the fourteen-file original research backup.
The original root inventory is not rewritten to absorb this extension. Infrastructure
checks passed 15/15 in normal and optimized Python modes; no Python assert is needed
to enforce the campaign/minimization acceptance gates.

`PROPERTY_MATRIX.md` separates six normative traceability IDs, five implementation
behavior IDs and two research-policy IDs. Clause anchors use the pinned Draft. Exact
event order, local sequential IDs, deadline ceiling and summary arithmetic are not
invented normative ERC MUSTs. EELS fixture separation and Foundry/Echidna ideas informed
the design; this is not an Ethereum consensus fixture or a run of those frameworks.

Coverage is bounded to selected state and event-name/order projections. Full event
arguments are retained but not all graded. Full storage equivalence, request-array
order/duplication, filtered summaries, reputation, external URI resolution, ERC1271,
EIP-7702, upgrades, reentrancy and exhaustive malformed ABI inputs remain outside this
campaign. The fixtures are schema-aware, not arbitrary-byte fuzzing. No source/branch
coverage percentage or statistical probability of conformance is claimed.

Independent implementation comparison remains **NOT_COVERED**. Another deployment,
a mutant or Python `-O` is not an independent registry implementation. The saved
`DIFFERENTIAL_PLAN.md` defines how to pin a second independently authored backend,
review a common normative domain, replay identical fixtures, preserve mismatches
and shrink them without using either implementation as ground truth.

Result: **bounded local conformance and mutation sensitivity established** under the
trusted-local-runtime and authored-oracle assumptions. Universal ERC compliance,
production safety, external execution and broader authorization are not established.

## Reproduction and evidence map

See `research/erc8004-property-fuzz-v0/README.md` for serial offline commands in the
prepared workspace. Existing caches/dependencies are required; no package-install
or external-provider command is part of this continuation.

- `build/fuzz-continuation/campaign-*/`: fixtures, pinned batch suites, requests,
  raw adapter output/receipts, projections, grader reports and summaries.
- `build/fuzz-continuation/mutations/`: original-matrix comparisons, mutant source,
  baselines, positive controls, all minimization trials and restoration evidence.
- `build/fuzz-continuation/checks/`: exact quick-check argv, exit codes and log hashes.
- `build/fuzz-continuation/checkpoint/`: pre-continuation backup and 470-file inventory.
- `build/fuzz-start/baseline/` and `build/fuzz-smoke/`: unchanged inherited execution.
- `SUMMARY.json`: reconciled machine-readable closure, source pins and integrity.
- `COUNTEREXAMPLES.json`: original and minimized inputs plus final observations for
  the six test-only mutant witnesses.
- `EVIDENCE.zip`: research sources and retained execution evidence with member hashes.

At the historical local closure, the source tree was uncommitted. The subsequent
publication and fresh replay are documented above. Independent reviewer approval
and later upstream changes are not implied by either execution phase.
