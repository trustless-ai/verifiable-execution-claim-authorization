# New PR12/PR13 integration evidence

This directory records newly executed integration replays, their pinned inputs and a new report. Historical captures used by offline replay retain their original observation times; reading them is not a new backend execution. Original research evidence is unchanged.

Executed source candidate: `5ebabe818173ffdb87dd9018d60c43ed77002c1a`. Production HOLD. Independent human review is NOT_ESTABLISHED.

`RESULTS.json` records actual suite results and scope. `EVIDENCE.zip` contains 10332 evidence members, including exact commands, outputs, fixtures, mutation descriptions and backend witnesses, restoration results, source pins and Git-object audits. Complete source snapshots and generated compiler caches are excluded from the committed archive; ARCHIVE_OMISSIONS.json binds their exact task-workspace paths and hashes. No complete mutated source copy is imported into the candidate. `SHA256.json` binds every member and these new closure artifacts.

Archive SHA-256: `086ddfaff99867c433c3ead9d82c570419f7ad17d8c6beed5902dcc11a970290`.

Read [the integration report](../../research/pr12-pr13-integration-v1/REPORT.md) and [replay instructions](../../research/pr12-pr13-integration-v1/README.md). Archive integrity is not an execution or independence attestation. The final local commit and tree are recorded in the task workspace FINAL_CLOSURE.json; source/config/fixture equality to the executed candidate is separately checked.
