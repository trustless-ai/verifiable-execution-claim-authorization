# Executed results: request-time role policy v1

Evidence source: local author execution, not independent organizational review.
Base: `80c91a09095eca362dbfb69d39d0c01fc31130cf`.

| Population | Observed result |
| --- | --- |
| Historical v0 cases | 29/29 PASS; normal/repeat/Python -O identical |
| Historical physical mutations | 17/17 KILLED normal; 17/17 KILLED Python -O |
| New v1 cases | 26/26 PASS; normal/repeat/Python -O identical |
| New physical mutations | 7/7 KILLED in each mode; normal/-O reports identical |
| New infrastructure test methods | 18/18 normal and 18/18 Python -O |
| Historical preservation | 12667 original file bytes and inventory entries unchanged |

New case authorizations: 5 VERIFIED, 11 REFUTED, 10 UNVERIFIABLE. Self-attested owner,
global operator and token-approved validator are UNVERIFIABLE while conforming to their
declared policy expectations. Different keys do not establish independent controllers.

New behavioral SHA256: `0ed522131509603602adbb90d8c6111a3347d8b5c19ce90d75440c67953a7617`.
The unchanged historical validator also passed transport tests, original ERC-8404 profile,
negative infrastructure tests, frozen Core conformance and before/after source integrity.
The new mutation records preserve baseline/mutated/restored executions, positive controls,
identical input requests and exact byte restoration. Mutation populations remain separate.

An initial overlapping run correctly failed when legacy infrastructure negative controls
temporarily removed a cached source file. The first optimized legacy mutation attempt had
14 kills and 3 UNVERIFIABLE baselines; it is not counted as 17/17. After legacy controls
completed and restored the file, the affected campaigns were rerun. The preliminary new
response-role diagnostic also had a request-block label; final output uses the actual
response receipt block. Preliminary results and explanations remain in the archive under
separate names and do not establish final passes. No historical tracked source was changed.

Runtime: Node v22.15.0; Python 3.12.10; Windows-11-10.0.26200-SP0.
Exact commands and raw output are archived; see [replay instructions](README.md).

[Evidence archive](../../evidence/erc8004-role-policy-v1/EVIDENCE.zip):
SHA256 `eeb81a761feed81d4e322b0315b53702ca66693fb765989bd9f57262079442a1`, 1820 members.
[Machine summary](../../evidence/erc8004-role-policy-v1/SUMMARY.json) and
[per-member hashes](../../evidence/erc8004-role-policy-v1/SHA256.json).

This capture does not claim GitHub CI success, independent acceptance, a second implementation,
or verification of a future #10 + #11 merge tree. Fresh source-head and GitHub execution results
are checked separately after committing. PR #10 must remain Draft; no merge is authorized here.
