# Future independent implementation replay

Status: **NOT_COVERED**. This campaign executes one pinned Solidity implementation
on one local Hardhat EVM. Test-only mutations and another deployment of the same
code do not establish independent implementation coverage.

The existing input/expectation/observation separation permits a later backend adapter
without changing the harness protocol. A future comparison must first pin the
second implementation, its dependencies, supported draft version and author/provenance
evidence. A fork with only cosmetic changes is not an independently authored backend.

1. Review the same normative clause table against both backends. Keep implementation
   details, such as the 300-second wallet deadline and duplicate-request policy,
   separate from the normative comparison. Unsupported features are NOT_COVERED;
   do not silently coerce schemas or make the first implementation the oracle.
2. Send identical input fixtures to each expectation-free adapter. Each must initialize
   empty real registries and preserve transaction outcomes, logs and queried state.
   Map only declared symbolic addresses/locators; retain raw evidence and exact code hashes.
3. Grade each observation independently with a reviewed oracle for the common normative
   domain. Then compare the supported projections across implementations. A disagreement
   is a research finding to investigate, not automatic evidence that one backend is wrong.
4. Replay the same distinguishing input on both fresh states, preserve both evidence sets,
   and shrink it with a predicate that requires a determinate disagreement. Crashes,
   unsupported schemas or missing execution remain separate from counterexamples.
5. Recheck shared oracle assumptions and independently inspect the relevant draft clause.
   Publish the exact boundary and minimized witness only after these checks.

Additional EVM engines would test a different independence axis. ERC-8299 and
ERC-8274 need their own obligations and native adapters; the present registry
transitions do not establish WYRIWE input truth, native proof validity, task completion,
payment authority or any broader execution guarantee.
