# Limits and independent review checklist

IMPLEMENTED: a second adapter/backend through the unchanged harness protocol and recompute-kit grader; byte-pinned source fetching, actual Solidity compilation/local execution, explicit policy projection, raw observations and physical mutation controls.

EXPERIMENTALLY VERIFIED results are reported only after execution in [RESULTS.md](RESULTS.md). This is a finite laboratory profile, not universal ERC conformance or production authorization. Existing broader research remains PARTIAL_CHAIN_VERIFIED.

NOT_COVERED / UNSUPPORTED:

- Public deployments, live chain finality, independent execution providers and production upgrade authority.
- A second independently authored implementation of ERC-8004 under the same profile. ERC-8404 and ERC-8004 are different profiles/backends.
- The Reputation Registry, complete registration-file validation, HTTPS endpoint ownership, ERC-1271 wallet branches, all ERC-721 behaviors and all upgrade paths.
- An ERC-mandated interpretation of every implementation-specific deadline, domain or duplicate-request rule.
- Provenance, inference correctness, judgment truth, real-world controller independence, arbitrary agent execution and release of funds.
- Full upstream test-suite reproduction. This experiment compiles the selected actual contracts with matching pinned Solidity/OZ/Hardhat versions and executes its independently specified finite suite.
- Protection against a malicious adapter hardcoding public vectors. The transport is not a sandbox or proof of honest execution.
- A normative standardized adapter API; the v0 protocol is experimental and still uses pinned private recompute-kit grader functions.
- Equivalence to PR #7's authorization contract or an ERC-8404 receipt. This pilot's observation policy is a separate finite profile; no cross-system authorization composition is claimed.

No upstream vulnerability is inferred from a laboratory mutation. No new scientific novelty, official governance agreement, maintainer appointment or security certification is claimed. Upstream licenses and authorship remain unchanged; Solidity sources retain their original SPDX notices and are fetched from exact Git revisions.

Independent reviewers should verify source and dependency pins, examine obligation classifications, replay without access to expected outcomes in adapter stdin, check raw receipts and state, reproduce all mutations, and supply another independently implemented registry backend. Review especially the separation between portable comparison scope and concrete evidence scope: neither the conformance report nor its `authorized` projection is a transferable permission.
