# Specification drift and obligation evidence v0

Experiment `spec-drift-and-obligation-coverage-v0`, based exactly on PR #12
`6e8fabee9be170245f557a271b6d315176cc4a03`. This additive research layer reads the
existing harness protocol, fixtures, reports and source locks. It does not execute
or replace a new verification engine, alter expected behavior, or issue authorization.

Prepare the unchanged pinned grader once (three hash-checked source files):

```sh
python -B tools/agent_harness.py prepare
```

For an air-gapped checkout use `prepare --source /path/to/pinned/recompute-kit`.
Setup failure is a failed prerequisite, never a passing test. Then run offline:

```sh
python -B tools/spec_drift_coverage/validate.py --out build/spec-drift-coverage/replay
python -B tools/spec_drift_coverage/coverage.py --out build/coverage
python -B tools/spec_drift_coverage/drift.py --snapshot evidence/spec-drift-coverage-v0/SOURCE_CAPTURE.json --out build/drift-captured
```

Choose a new output directory for each validation so earlier evidence survives.
These commands reconcile preserved backend executions, not newly execute an EVM.
Normal/repeat/-O outputs are byte-compared. Native historical regression workflows
remain separate and unchanged. Fresh source/dependency validation of ERC-8004 can
also use its existing `tools/erc8004/prepare.py` and `tools/erc8004/integrity.py`.

Current live upstream check (public GitHub HTTPS, read-only):

```sh
python -B tools/spec_drift_coverage/drift.py --live --out build/drift-current
```

A content change requests review and does not alter pins or invalidate historical
results. Missing files or unavailable sources return exit 2. Exit 0 means the source
comparison completed, not that the specification or implementation is conformant.
JSON `comparison` and `review_required` remain the authoritative drift indicators.

See [architecture](ARCHITECTURE.md), [pins](SOURCE_PINS.md),
[coverage](OBLIGATION_COVERAGE.md), [results](RESULTS.md), and [limits](LIMITATIONS.md).
