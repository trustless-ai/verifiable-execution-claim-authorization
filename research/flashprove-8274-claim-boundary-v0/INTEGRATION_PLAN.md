# Authorized finalization v1

The owner authorized additive inventory registration and publication of this same
branch after all gates pass. Step 5 of the original plan below is now implemented:
current inventory extension only, historical snapshots and every old digest preserved,
root checker unchanged, eight explicit integrity controls. New replay/counterexample
commands are documented in `review_v1/REVIEW.md`. No new PR or merge is authorized.

PR #12/#13, main, Jimmy's repository and frozen ERC-8404 remain untouched. Existing
GitHub workflows are unchanged; remote CI results must be observed, not presumed.
The new research replay is explicitly executable locally; no absent dedicated
FlashProve CI job is described as green.

The original integration plan remains below for provenance.

---

# Integration plan

This branch is an additive research review surface. No push, PR, merge, live
contract deployment or source change in FlashProve is part of this delivery.

1. Independently replay the exact local commit and inspect both native execution
   and consumer decisions. Check `configuration_profile_collision`,
   `caller_impersonates_agent`, `reuse_proof_fresh_task`, `reuse_proof_other_chain`
   and `attestation_digest_domains`; none is a production exploit demonstration.
2. Agree with the FlashProve design owner on the committee profile commitment,
   signature format/domain, distinct-signer counting and rotation/revocation
   assumptions. The current TODO must not be treated as working verification.
3. Decide whether agent/caller, task, chain and verifier-instance bindings belong
   in a future application policy. ERC-8274 interface compliance alone does not
   supply those application guarantees. Do not backfill them onto this source pin.
4. Provide an authenticated real SP1 verifier/program/proof fixture before adding
   a positive `ZK_PROOF_VERIFIED` witness. Provide an implemented, specified
   attestation route before adding positive `ATTESTATION_ACCEPTED`. No expected
   value in this experiment authorizes execution or proves an order occurred.
5. Only in a separately authorized integration change, register the new research
   files in the repository's complete inventory and CI workflow while preserving
   all old digests. This task explicitly prohibited changes to existing integrity
   manifests, so the unchanged root gate correctly refuses these unlisted files.
   Do not suppress or reinterpret that failure as a canonical PASS.
6. PR #12 (`6e8fabee9be170245f557a271b6d315176cc4a03`) and PR #13
   (`c0d3862a590b62a059c1a923ab93b380d609876f`) stay separate. Rebase/stack composition,
   inventory transitions and their independent reviews are outside this task.

Frozen ERC-8404 source at `9dd36e882dd372f264b77b179130948aa5adcbde` is checked against
its existing 13-file lock. This work introduces no RVR field, profile semantics,
canonicalization rule, source-lock transition or historical evidence revision.

Acceptance for independent review: all authored observations reproduced, missing
evidence refuses, source pins exact, physical guards have distinguishing witnesses,
positive controls healthy, every baseline byte preserved. Acceptance for production
or merge is separate and has not been established.
