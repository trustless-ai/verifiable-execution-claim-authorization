# PR12 / PR13 integration v1

Local research candidate on main 999e7047df15585f8ce0629081a1369a4942353f.
Production HOLD. No claim of independent human review.

The two merge commits preserve PR ancestry. Original research sources, source
locks, evidence, reports and initial manifests remain byte-identical. Only the
two new workflows select explicitly versioned integration entrypoints. Their
original bytes remain authenticated at the PR13 Git object and in original seals.

TRANSITION.json binds three already-reviewed main differences outside Core and
exact workflow substitutions. preservation.py pins its raw SHA256 and all four
historical inventory hashes. No Core transition is permitted. The inventory
addition scope is an exact file list, including this report and the new archive.
Historical manifests are not regenerated. New evidence is identified separately.

PR13's original preservation test is intentionally incompatible with main.
The original 32 controls run at its exact SHA. The integrated suite runs 31
unchanged semantic tests plus a versioned preservation test that requires both
the old checker's exact refusal and the new contract's acceptance. The old test
and checker remain untouched. This population distinction is reported explicitly.
The integrated semantic reporter and drift classifier call the unchanged APIs.

## Replay

Use full Git history, Python 3.12 and Node 22.15.0. Prepare dependencies:

```sh
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B research/formal-v1/prepare_crypto.py
npm ci --ignore-scripts --no-audit --no-fund --prefix build/formal-v1/crypto
python -B tools/pr12_pr13_integration/preservation.py
python -B tools/pr12_pr13_integration/fuzz_validate.py --out build/property-replay
python -B tools/pr12_pr13_integration/spec_validate.py --out build/spec-drift-coverage/validation
python -B tools/pr12_pr13_integration/runtime_binding.py --out build/core-runtime-binding
python -B tools/pr12_pr13_integration/controls.py --out build/preservation-controls
python -B tools/pr12_pr13_integration/spec_cli.py drift --live --out build/spec-drift-live
```

Run mutation campaigns serially. The six Solidity mutants modify disposable
ERC8004 implementation copies only. External ERC8404 consumer mutations never
modify Core. No Core adapter/schema/vector/preimage/pin is changed or regenerated.

See REPORT.md for actual executions and evidence/pr12-pr13-integration-v1 for
the separately sealed evidence. Archive presence alone is not an execution proof.
