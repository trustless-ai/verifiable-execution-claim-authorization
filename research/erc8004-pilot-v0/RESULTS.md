# ERC-8004 pilot results

Status: LABORATORY_VERIFIED for this finite profile. Ready for independent technical review; no production authorization or universal ERC conformance claim.

| Check | Observed result |
| --- | --- |
| Normal scenarios | 29/29 expected outcomes |
| Repeated scenarios | 29/29 expected outcomes |
| Python -O scenarios | 29/29 expected outcomes |
| Authorization projection, each mode | 8 VERIFIED / 20 REFUTED / 1 UNVERIFIABLE |
| Original transport regression | 13 tests passed |
| Original ERC-8404 executable profile | 18/18 expected outcomes |
| New infrastructure negative controls | 5 tests passed |
| Physical mutations | 17 KILLED / 0 SURVIVED / 0 CRASHED / 0 NOT_APPLIED / 0 UNVERIFIABLE |
| Restored originals and mutant positive controls | Passed for every counted kill |
| Frozen ERC-8404 conformance | Passed |
| Preserved baseline | All 12,193 prior inventoried file hashes unchanged |
| Normal/repeat/-O semantic projection | Byte-identical |
| Normal/repeat/-O raw adapter output on this host | Byte-identical, SHA-256 `9fde155e682c31602cbbf4e9f4adb4aa78d4184c4f105563b3e8b845cd1f78af` |

The 17 mutations comprise nine Solidity enforcement/state changes and eight external-policy changes. Kills are finite distinguishing observations, not a proof of completeness or an upstream vulnerability. A designated validator's repeated response is a permitted positive control, not a replay attack.

[Machine-readable summary](../../evidence/erc8004-pilot-v0/local-replay/summary.json), [exact commands, timing and exit codes](../../evidence/erc8004-pilot-v0/local-replay/commands.json), [all scenario observations](../../evidence/erc8004-pilot-v0/local-replay/normal/report.json), [physical mutation report](../../evidence/erc8004-pilot-v0/local-replay/mutations/report.json), and [SHA-256 evidence inventory](../../evidence/erc8004-pilot-v0/SHA256.json) preserve the results. The inventory seals 451 files. Fresh checkout and remote CI must be associated with the eventual exact commit; this frozen local capture does not assert a future CI result.

Development infrastructure failures and their corrections remain in [the development record](../../evidence/erc8004-pilot-v0/development/NOTES.json). They were not counted as kills or conformance failures of the upstream ERC implementation.

The reusable result is that the same unchanged harness/grader executes two real, distinct ERC backends with separate semantic profiles. A second independently implemented ERC-8004 backend under this same profile remains NOT_COVERED. See [limitations](LIMITATIONS.md) and [reproduction commands](../../conformance/erc8004-pilot-v0/README.md).
