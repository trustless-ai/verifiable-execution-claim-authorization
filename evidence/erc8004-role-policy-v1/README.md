# Captured local replay

`EVIDENCE.zip` contains actual raw local execution output. `SUMMARY.json` identifies final
results; `SHA256.json` seals the archive, summary and every archive member. ZIP members use
sorted paths and fixed timestamps. Dependencies and caches are excluded.

Final populations are separate: historical 29 cases / 17 physical mutations; new 26 cases /
7 physical mutations. `preliminary-*` members retain unsuccessful preflight runs and must
not be counted as final successes. `REPLAY_NOTES.json` explains the shared-cache test collision
and correction of response-role diagnostic block labels. Original historical evidence remains
in its original paths without modification.

The archive records author execution on Windows, not independent reviewer acceptance or
GitHub CI. Fresh source-head and CI runs are separate observations. See the
[policy and commands](../../research/erc8004-role-policy-v1/README.md) and
[executed report](../../research/erc8004-role-policy-v1/RESULTS.md).
