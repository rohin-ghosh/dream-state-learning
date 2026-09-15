# Finalized c56 hook: use v4, not the archived intermediate source

Native source root:
`/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_source_20260915_v4`.

The actual imported bootstrap, campaign-wait and per-generation launch functions
resolve to its `gpu/orch_r118_parallel_consolidation.py`, hash
`c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb`.
That hash was also recomputed on Main's canonical v4 source. Native startup and
campaign entry now enforce the exact hash. Math additionally requires the actual
bootstrap receipt's `startup_action=COLLECT_NEW_TWO_EPISODES` and
`canonical_adapter_actually_verified=true`; a missing or pending-replay action
cannot reach GO. No actual GPU bootstrap is claimed by these CPU checks.

194 local and 194 frozen node CPU tests pass. The earlier combined copy/test shell
exceeded its 30-second tool limit without producing a CPU receipt; no test process
remained. The standalone node gate completed in 6.681 seconds. No GPU/provider
calls or experiment retries occurred.

`V4_PRESTAGE_EXPORTS.json` mirrors the native `PRESTAGE_EXPORTS.json`, hash
`e68691371a1cfca227332df365e3969f5e5be84eb2393117047532d65fb871d9`.
It contains exact prepared-owner and separate `source_files` references for both
branches, available **before stage**, so Main can construct the campaign first.

Under `/localhome/local-rohing/orch_math_feedback_uptake_r118_parallel_20260915_attempt2/`:

| Branch | Prepared owner | SHA256 |
|---|---|---|
| F2 | `lane1/FRESH_OWNER_PREPARED_d3b6bfd8ec8de107.json` | `a2426862ce4636f520415cc1760f7b04b42a977def23ef00496acf5b81dc3e31` |
| A2 | `lane5/FRESH_OWNER_PREPARED_d3b6bfd8ec8de107.json` | `04516049579186ecfe039907483d98c6cac0f65fa8b7523fdd35f6c2552566df` |

Both `lane1/SOURCE_FILES_V4.json` and `lane5/SOURCE_FILES_V4.json` hash to
`86ebb5677d8e0927014ea8fc693de3ba51b8b18765dd9961a29a0467fea4516e`.
These maps bind the actual invoked c56 file, not merely an unused archive copy.
Both exported postcommit boundaries also pass the actual v4 common validator.

Use the existing HANDOFF stage/owner-envelope commands from the **v4 directory**,
with the Main campaign JSON and activation directory, before the common locked
dispatcher. Stage produces final `FRESH_OWNER.json`; no stage, timer retirement,
guard, model or parent launch has occurred during this update.

Original release and failure artifacts, PLAN, v3 SOURCE_UPGRADE and prepared owner
files remain unchanged. A new source-specific upgrade and source-tagged prepared
filename retain the version history. F2 remains next C11 at N274/P60; A2 remains
next C7 at N170/P36. Bounds, carry, sealed FINAL custody and accepted submissions
are unchanged. The separately frozen A2 broker runtime remains unchanged.

Publish only `STAGE_V4_PATHS.txt`; Main owns Git. Do not restage Herschel's source
as a math edit. Its exact runtime snapshot is included in the exported pin map.
