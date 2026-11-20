# Candidate discovery and reuse audit

Observed 2026-11-20 using GitHub API metadata, exact source bytes and commit
history. Repository ownership, non-fork metadata and commit author strings are
observations, not authentication of human authorship or proof of clean-room work.
Search was bounded, not an exhaustive inventory of all ERC-8004 implementations.

| Repository / exact observed SHA | Source findings | Decision |
| --- | --- | --- |
| [vyperlang/erc-8004-vyper](https://github.com/vyperlang/erc-8004-vyper/tree/661278f72d312a2cef0cbaea32b89d3842996967) `661278f72d312a2cef0cbaea32b89d3842996967` | Vyper Identity/Validation implementations and separate compiler. Current headers and LICENSE are AGPL-3.0-only. Same selected registration IDs and EIP-712 message shape; constructor-based deployment. | Selected and executed. Separately authored, reference-informed implementation; clean-room or organizational independence NOT_ESTABLISHED. |
| [erc-8004/erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts/tree/b9e466c250744a7e06b13dff9d3c2844ed64f825) `b9e466c250744a7e06b13dff9d3c2844ed64f825` | Current head equals the existing pilot pin. Existing byte-locked Solidity/OZ/runtime source is reused without updating it. Selected Solidity sources carry their original MIT SPDX notices; dependencies retain their notices. | Reference side of the comparison; not counted as a second implementation. |
| [aadeexyz/erc-8004](https://github.com/aadeexyz/erc-8004/tree/5e1f5cdc19a383ce6f631ade5363da28b14d4a21) `5e1f5cdc19a383ce6f631ade5363da28b14d4a21` | MIT. Identity uses `newAgent(domain,address)`; validation uses validator/server agent IDs and dataHash. Older API shape differs from the fixed suite. | Not selected for this profile. Incompatibility is not a defect against its own historical draft. |
| [ChaosChain/trustless-agents-erc-ri](https://github.com/ChaosChain/trustless-agents-erc-ri/tree/2e5e79d872b6f3c22f2d5f805cd57632fa3d5f59) `2e5e79d872b6f3c22f2d5f805cd57632fa3d5f59` | Current `src/` does implement ERC-721 registries; old `legacy/` is distinct. Current IDs start at 1 and its wallet signature type differs from the selected Solidity/Vyper message. Root LICENSE is MIT while selected source SPDX and README identify CC0. | Plausible later candidate with an explicit compatibility and license-scope review. Not executed here; do not describe the entire repo as legacy-only. |
| [shola-devv/ERC-8004-Experimental](https://github.com/shola-devv/ERC-8004-Experimental/tree/ef8163c9616604099746f28a66e08126109ba6e6) `ef8163c9616604099746f28a66e08126109ba6e6` | README describes current-shaped registries and claims CC0; API license metadata is null and the linked root LICENSE was not found in the fetched tree. | Not selected; license grant and source ancestry require more review before reuse. No execution or license conclusion inferred from README alone. |

## Vyper provenance and compatibility

The fetched history contains a distinct initial implementation by the recorded
author `lufa23`, subsequent spec-alignment changes, and an explicit reference to
the Solidity wallet message in source. Its final license correction changes the
headers to AGPL-3.0-only. We select the current exact SHA, not an older apparently
permissive license revision. The complete tracked source inventory is pinned in
`source-lock.json`; original upstream checkout remains clean.

Source-level independence is bounded: separate Vyper code/compiler, no direct
Solidity bytecode substitution. It is a reference-informed port. The experiment
does not assert independent design, an independently implemented EVM, an
independent adapter/policy/grader, or independent organizational review.

The new adapter changes compilation and deployment bootstrap. The original
operation loop is byte-identical and separately checked. Its authorization
projection imports the original VECA policy directly, so it cannot be counted
as a second independent authorization implementation. Vectors/expectations are
sent only to the grader; adapter stdin contains exact inputs, not expectations.
This does not sandbox an adapter against reading public fixture files.

The original profile retains N1-N7 normative classifications, I1/I2 pinned
implementation behaviors and P1-P8 external laboratory policy classifications.
Agreement on I1/I2 or P1-P8 does not convert them into universal ERC requirements.
No source pin, original obligation or expected result was edited.

## Explicitly untested scope

Vyper bounds strings, metadata and arrays; uses constructors rather than UUPS;
and uses Snekmate rather than OpenZeppelin. The 29 cases do not establish equal
behavior for large inputs, upgrades, every wallet/signature form, registration
files, ReputationRegistry or the full upstream test populations. Published
addresses, advertised deployment/test counts and upstream production claims
were not independently validated. This is an offline finite conformance pilot.

## Discovery evidence

The evidence archive contains GitHub metadata/tree snapshots, fetched-file
digests, exact source selection and the Vyper commit-history record. The full
read-only discovery files remain in the external workspace `discovery/` folder.
No upstream branch, issue, pull request or deployment was modified.
