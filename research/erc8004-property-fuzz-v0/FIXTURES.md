# Sequence fixture contract

Profile `erc8004-sequence-observation-v0` extends opaque harness input, not the
transport protocol. Three files separate inputs (`fixtures.json`), authored-model
expectations (`expectations.json`) and the pinned harness corpus (`vectors.json`).
The corpus is a deterministic join; adapter stdin contains only input and locator ID.
No expected status, property name, mutation ID or oracle state enters the input.

Each input supplies `sequence` (ordered symbolic calls), `claim` (existing
LAB_REGISTRY_TRANSITION format), and `supply_receipt`. The generator record outside
input supplies version, seed, case index and selected property family. Each call
specifies kind, actor index and agent ID plus typed arguments. Account indexes map
to four disposable local EOA accounts; null wallet/validator maps to zero address.

Initial state: initialized empty real registries, no agents or requests. Logical
agent IDs start at zero. Each sequence starts from the same post-deployment snapshot.
Each call mines one transaction; even expected reverts have receipts. Deadline
offsets refer to the timestamp of the next transaction, avoiding off-by-one clock
ambiguity. Fixture request labels generate exact UTF-8 request payloads and keccak
commitments inside the local executor; both bytes and digests are retained.

The observation is a list of per-call transaction status, selected ERC event names
and queried state. Raw receipts, logs, transactions, signatures, domains and deployed
code hashes remain in evidence. Normalization removes only concrete account/registry
addresses, block timestamps and hashes from the portable behavioral projection.
An address outside the fixture actor set must remain distinguishable, not map to a
valid actor. Nonexistent agents remain absent. No state is filled from the oracle.

Authorization reuses the unchanged existing projection on the last call. It
authorizes only that successful laboratory transition, not correctness of every
preceding transition, validator truth, task completion or payment. Conformance
compares the complete observed sequence separately. Consequently a faulty backend
can have conformance FAIL while its last accepted lab transition is VERIFIED;
this is reported, not repaired or promoted to overall authorization.

Shrinking removes calls and simplifies values only when an actual fresh local EVM
execution reproduces the chosen divergence. The original case remains preserved.
A resulting witness may be deletion-minimal in the attempted domain; no global
minimality claim follows. Infrastructure failures cannot satisfy the predicate.

Future adapters can map the same symbolic fixtures to independently authored
ERC-8004 implementations after reviewing supported semantics. WYRIWE would require
its own raw-input/transform/signature obligations and fixture fields; ERC-8274 would
require exact verifier statements and public-input bindings. Those profiles and
proof artifacts cannot be inferred from these registry results. No additional
adapter is implemented here. This is not the Ethereum consensus fixture format.

The final event-name projection also includes ERC721 Transfer, Approval and
ApprovalForAll. It checks their order alongside registry event names, while raw
logs retain arguments. Per-case obligation references include only applicable
operations and the shared state/policy checks. Referencing an obligation records
that the case exercises it; it is not a proof that every possible subcondition was
covered. Corpus generation retains all generated rejections; no assume/filter
discards unauthorized or reverting calls.
