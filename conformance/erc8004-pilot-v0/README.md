# ERC-8004 registry pilot

Second executable backend for the unchanged [Agent Conformance Harness](../agent-harness-v0/PROTOCOL.md). This finite profile runs third-party Identity and Validation registry implementations in a local EVM. It is independent of escrow and does not implement another generic verifier.

Source: `erc-8004/erc-8004-contracts@b9e466c250744a7e06b13dff9d3c2844ed64f825`. Normative draft: `ethereum/ERCs@503591a6e80e6e1affdd6403341e25269141f046:ERCS/erc-8004.md`. Exact files, packages and versions are pinned in [source-lock.json](source-lock.json) and [package-lock.json](package-lock.json).

## Reproduce

Use Python 3.12+ and Node 22.15.0. From the repository root:

```sh
python -B tools/agent_harness.py prepare
python -B tools/erc8004/prepare.py
python -B research/formal-v1/prepare_crypto.py
cd build/formal-v1/crypto
npm ci --ignore-scripts --no-audit --no-fund
cd ../../..
python -B tools/erc8004/validate.py
python -B tools/verify_artifacts.py
```

The crypto setup supports the unchanged ERC-8404 baseline regression. `prepare.py` downloads immutable Git blobs, verifies SHA-256 and installs lockfile dependencies in ignored `build/`. Once prepared, execution needs no network or public RPC. No production keys or real funds are used. Solidity deployment occurs only inside the in-process EDR simulation.

Run the new profile alone through the **same** CLI:

```sh
python -B tools/agent_harness.py run --suite conformance/erc8004-pilot-v0/suite.json --adapter conformance/erc8004-pilot-v0/adapter.json --out build/erc8004/run
python -B tools/erc8004/mutations.py
```

The full validation runs normal/repeated/Python `-O`, exact semantic comparison, physical mutations, source/history integrity, infrastructure negative controls, the original ERC-8404 profile and frozen Core conformance. Python `-O` does not optimize Solidity or constitute another EVM implementation.

## Supply another backend

Use the existing [adapter protocol](../agent-harness-v0/PROTOCOL.md). Preserve these independently authored `vectors.json` and `obligations.json`, write a separate argv adapter and pass it with `--adapter`. Execute your actual implementation; do not read expectations or manufacture transactions. Project operation results and authorization scope into the same response, keeping concrete addresses, transaction hashes, logs, runtime code hashes and full scope in `evidence`.

A backend unable to support an operation must fail closed or report noncoverage; it cannot hardcode a passing observation. Source review, mutations and independent replay are still required. This experiment demonstrates reuse across two different ERC profiles; it does **not** establish interoperability between two independent implementations of ERC-8004.

See [architecture](../../research/erc8004-pilot-v0/ARCHITECTURE.md), [profile and coverage](../../research/erc8004-pilot-v0/PROFILE.md), [results](../../research/erc8004-pilot-v0/RESULTS.md), and [limitations](../../research/erc8004-pilot-v0/LIMITATIONS.md).
