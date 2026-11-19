# Spec drift and obligation evidence package

SOURCE_CAPTURE.json contains exact public GitHub responses from the live check.
SOURCE_DRIFT.json and COVERAGE.json are deterministic derived reports. SUMMARY.json
retains the actual local validation command receipts and execution phase identity.
RAW.zip contains raw validation logs and newly executed unchanged-profile reports.
SHA256.json seals each loose member and each RAW.zip member; it excludes itself.

Historical evidence remains in its original locations. PR12 evidence is referenced
from its unchanged EVIDENCE.zip. PR11 files are copied byte-exact into external/pr11
from commit e5263f47325a81b0647f3de3a7bc36ad858aea5a, with original archive member hashes.
This read-only sibling import does not merge PR11 or claim independent acceptance.
All paths and hashes used by the reporter are available in the new input catalog.

Replay commands and setup requirements: ../../research/spec-drift-coverage-v0/README.md.
The fresh-checkout phase, when present, is author reproducibility, not independent review.
