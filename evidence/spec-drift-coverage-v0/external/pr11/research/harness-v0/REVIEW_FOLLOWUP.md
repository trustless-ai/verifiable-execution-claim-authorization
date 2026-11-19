# Independent reproduction of the reviewer coverage finding

Reviewed source: PR #9, `0e17c97e896916b4d9505072cc9ebe2018329b01`.
PR #10 is stacked on that commit at `80c91a09095eca362dbfb69d39d0c01fc31130cf`;
that dependency was checked through GitHub refs and Git ancestry, not file counts.
This follow-up is an isolated local research branch. It does not change either PR.

## Evidence provenance

Pavlo forwarded Echo's report on 2026-10-22. Echo reports a fresh macOS arm64
replay using Python 3.12.13 and Node 25.6.0 instead of pinned Node 22.15.0:
18/18 scenarios, 2 VERIFIED / 13 REFUTED / 3 UNVERIFIABLE, 12 killed mutants,
12,193 matching inventory entries, and matching observation/request/profile hashes.
These are externally reported results. No raw macOS replay files accompanied the
forwarded message; this follow-up does not independently attest that host or turn
the Node version deviation into a new supported-runtime guarantee.

This follow-up independently executes the unchanged reviewed consumer on Windows,
Python 3.12.10, Node 22.15.0. Native zkIE verification and external task execution
are not new claims of this adapter or replay.

## Finding and resolution

The original suite reproduces the reported behavior: disabling `reuse` is detected
by `tampered_admission`, while deleting `scope`, `scenario`, `definitions`, or
`supported_contract` leaves all original 18 vectors passing. The four survivors
are real gaps in the finite test corpus. They are not equivalent mutations over
the expanded input domain and cannot be dismissed as redundant checks.

The [supplemental profile](../../conformance/agent-harness-review-v0/README.md)
contains one positive and four isolated negatives. For each negative, all checks
except the target are VERIFIED. With the original implementation, authorization is
REFUTED. Removing the target physical source check produces VERIFIED authorization;
the positive still passes; restoration reproduces the original refusal.

This is a coverage correction. No authorization defect is demonstrated in the
unmodified consumer by these four witnesses, and no ERC-8404 Core change is needed.

| Experiment | Result |
| --- | --- |
| Original profile, normal/repeat/-O | 18/18; 2 VERIFIED / 13 REFUTED / 3 UNVERIFIABLE |
| Original physical mutation set | 12 KILLED; historical report unchanged |
| Reviewer's additional five mutations on original profile | 1 KILLED (`reuse`), 4 SURVIVED |
| Supplemental profile | 5/5: 1 VERIFIED / 4 REFUTED |
| Four isolated physical mutations | 4 KILLED / 0 SURVIVED / 0 CRASHED |
| Tampered expected outcome without updating suite commitment | Exit 2 / NOT_COVERED before adapter execution |
| Depth-one clone, exact base inventory read | Missing Git object; exit 128 |
| Same clone after fetching the exact research base | Inventory bytes restored exactly; exit 0 |

The machine-readable normal/optimized reports and exact commands are preserved
with the [evidence](../../evidence/harness-review-v0/README.md). Original results
and supplementary results are not retroactively combined into one historical run.
Successful conformance and authorization remain separate: a conformant refusal
is a PASS for conformance while its authorization remains REFUTED or UNVERIFIABLE.

## Reproduction prerequisite

`tools/harness_v0/validate.py` intentionally reads the pinned base inventory with
`git show 2e329fffbee103047d034b97056aea9e49cf1c58:artifacts.sha256.json`.
The README now requires a full clone or an explicit fetch of that base. Integrity
enforcement is not skipped when Git history is absent. CI already fetches full
history. This experiment reproduced the prerequisite failure and recovery in an
isolated depth-one clone; it did not classify missing history as a consumer failure.

## Remaining limits

One witness per guard is not exhaustive condition coverage. The supported-contract
witness isolates the unsupported claim type; it does not individually cover the
schema, scope and nonempty-requirements conjuncts. A catalog's agreement with an
external contract does not establish that contract's adequacy. Signature validity
does not establish judgment truth or controller independence. The broader chain
remains PARTIAL_CHAIN_VERIFIED; arbitrary execution/payment authorization remains
unsupported. PR #10 still requires its own independent replay.

Recommendation: review and replay this supplemental coverage change before treating
the first profile as a community yardstick. No merge or reviewer approval is implied.
