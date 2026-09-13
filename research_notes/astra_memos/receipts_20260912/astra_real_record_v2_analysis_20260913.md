# SEQ149 — actual record formation v2 versus preserved v1

**Qualification:** exploratory external instruction-bundle formation on inspected DEV IDs, with mandatory prior prediction and state-dependent actual experiences. No model update, write, learning-improvement, closed-loop, or H1/H2 claim.

## Main finding

V1 failed before any world execution: all four states0/16 executions and0 record calls. V2 reaches all16 scheduled world executions per state and elicits16 records each, but source-faithful production acceptance remains7/16,14/16,8/16,8/16. The transition follows an external prompt-bundle amendment in these preserved runs, not a demonstrated learned improvement or isolated ACT-prefix mechanism.

| V2 state | Source-faithful production/content /16 | Strict canonical /16 | First-turn /8 | Second-turn /8 | try /16 | observed /16 | predicted /16 | relation /16 | Distinct triples | Example2,5,9 |
|---|---|---|---|---|---|---|---|---|---|---|
| OFF | 7 | 0 | 5 | 2 | 16 | 16 | 13 | 7 | 4 | 1 |
| perception_seed0 | 14 | 6 | 8 | 6 | 16 | 16 | 14 | 14 | 2 | 0 |
| perception_seed1 | 8 | 0 | 4 | 4 | 16 | 16 | 8 | 8 | 4 | 0 |
| perception_seed2 | 8 | 0 | 0 | 8 | 11 | 16 | 11 | 11 | 5 | 1 |

Production and permissive content counts coincide here; canonical correctness does not. OFF/seed1/seed2 have16 noncanonical JSON outputs each. Seed0 has8 exact-format and8 noncanonical outputs, but only6 strict-correct: exact JSON formatting alone is not content correctness.

## Errors are nested, not missing

All v2 top-level turn.errors arrays are empty. Read score.production_errors, score.content_errors and field_correct instead. There are27 rejected records:
- OFF9: prediction mismatch3, relation mismatch6. All16 selected triples and observed outcomes copied correctly; wrong relations dominate.
- Seed0 two: prediction mismatch2, both on turn2. First turn8/8; second6/8.
- Seed1 eight: prediction mismatch8, four per turn. Returned prior null8 despite an explicit false prior in every execution.
- Seed2 eight: record schema5 plus prediction mismatch3, all on first turn. Five schema failures omit try and instead emit an unavailable key; some additional field errors coexist. Second turn8/8.

Field diagnostics are not exclusive failure categories: for example, observed can be correct even in a schema-invalid record. Every raw failing record, raw wake, exact execution fields, nested score object and archived response hash is retained in JSON under versions.2.states.*.raw_turns and failed_record_indices.

## Prior availability and turn position

All64 v2 executions carry an explicit unambiguous prior: OFF/seed0/seed1 false16/16 each; seed2 true11/16,false5/16. No absent-prior or ambiguous-prior execution occurs. Returned null counts: OFF3, seed0 two, seed1 eight, seed2 five. Thus null/unavailable errors cannot be excused as genuinely absent source predictions.
Seed2 first turn has true8/8 and0/8 eligible; second has true3/8,false5/8 and8/8 eligible. OFF drops5/8→2/8, seed0 drops8/8→6/8, seed1 stays4/8→4/8. These are nonrandomized descriptive strata, not evidence of within-run learning: tick2 includes earlier actual wake/outcome/record history and changes selected actions/outcomes.

## Chosen actions and example copying

- OFF: [2, 5, 9]×1; [3, 7, 11]×8; [4, 6, 8]×6; [4, 8, 12]×1.
- perception_seed0: [3, 7, 11]×8; [4, 6, 8]×8.
- perception_seed1: [2, 4, 6]×1; [3, 7, 11]×8; [4, 6, 8]×4; [4, 8, 12]×3.
- perception_seed2: [1, 2, 3]×4; [2, 3, 5]×5; [2, 3, 7]×2; [2, 5, 9]×1; [3, 4, 7]×4.

The literal prompt example[2,5,9] occurs twice in64 executions: OFF first episode/tick2 and seed2 episode real-record-dev-9e711dc90f1ac92f90df/tick2. Seed2 also copies its example prior T; OFF uses F. These are observed literal matches, not proof of a copying mechanism. Seed0 uses only two distinct triples and never the example; high formation acceptance is not action diversity or hidden-rule discovery.

| State pair | Same executed triple /16 | Same triple+prior+outcome /16 |
|---|---|---|
| OFF vs perception_seed0 | 14 | 14 |
| OFF vs perception_seed1 | 13 | 13 |
| OFF vs perception_seed2 | 0 | 0 |
| perception_seed0 vs perception_seed1 | 12 | 12 |
| perception_seed0 vs perception_seed2 | 0 | 0 |
| perception_seed1 vs perception_seed2 | 0 | 0 |

OFF/seed0/seed1 choose[3,7,11] on every first turn, giving the same first-turn action/prior/outcome; their second-turn actions diverge. Seed2 matches none of their actions at corresponding slots. Aligned triples do not guarantee matched full second-turn histories, which include previous record outputs. JSON records all differing action slots; aggregate seed comparisons are not controlled record-only causal effects.

## What changed from v1

V1 all64 wake calls produced zero executable actions and therefore zero records; its0/16 field counts are missing-opportunity zeros, not observed field inaccuracies. OFF/seed0/seed1 each have16 unanchored/additional-action errors, commonly PREDICT followed by bare TRY without ACT:. Seed2 has14 length-truncated wakes plus two stopped invalid wakes (one unanchored/additional action, one multiple-action-marker error). Do not retroactively repair those strings or call their literal numbers actual executed triples.
V2 preserves source/world/parser pins, adapter identity metadata and the same eight episode IDs. The wake bundle now requires a prediction, two lines, ACT: prefix, no fence/explanation and provides a concrete syntax example. V1 allowed prior omission. A source diff confirms unchanged load_dependencies, score_record, _execute, run_state, audit_capture and compare_states function bytes; schema/episode derivation bookkeeping, contract wording and WAKE_TEMPLATE changed.
Actual native cost differs because valid actions trigger records: v1 64calls/455.289seconds; v2 128calls/514.042seconds. Same scheduled wake budget is not equal realized compute or identical experience. V2 follows inspection of v1 DEV failure data, so this is exploratory amendment evidence.

## Exact replay and custody

CPU replay PASS:8/8 captures, both full comparisons exact;192 native archived request/response pairs join to core event objects (64v1+128v2). World outcomes and source/record scores reproduce through the unchanged pinned cores and sources. No native/model/network calls, collection, fit, protocol edit, extraction or source writes.

- V1 tar `gpu_artifacts_local/real_record_20260913/astra_real_record_20260913_attempt1.tar`: `ccbcdf6c89921609116d751a2b0b8fe295ba200bde574d00c8f319173509d445`.
- V1 report `/tmp/astra_real_record_formation_report_20260913_attempt1.json`: `2b9bb4d5539d6e26e75933af8d45e21e1dc3c93ad7320fc2bc6c64d1cf93420a`.
- V1 core `/tmp/astra_level1_real_record_core_20260913.py`: `1c7723fcbb07ad75464d9ceae9fbd1cb8953f6dc0cb7a2e22d3046421167a15c`.
- V2 tar `gpu_artifacts_local/real_record_20260913/astra_real_record_20260913_attempt2.tar`: `71671dc02e175be0dafba595aa4e9ef30c409953a0366cc082b4d7e319c055c0`.
- V2 report `/tmp/astra_real_record_formation_report_20260913_attempt2.json`: `9d04155a0103377e41f80ad25b7b1b4ed9cd2ffd014503e74b27a0992b4c81f1`.
- V2 core `/tmp/astra_level1_real_record_core_20260913_v2.py`: `b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5`.

Core/source payloads are available locally and verified against saved pins, but were deliberately packaged separately from the formation tar archives. The v2 protocol payload is available at `research_notes/astra_memos/ASTRA_REAL_RECORD_FORMAT_AMENDMENT_2026-09-13.md`; its SHA256 `5448a3f5e072dd385f8c33e7ea38fb27fa39b61aeddb76b9dc023f3c7b05296b` matches the exact native plan/report pin. The separate frozen source archive is now locally hash-verified, including both versions' source/core/protocol/spec payload pins; Main reports native/VM archive hash agreement. CPU replay validates deterministic consistency, not independently authenticated model origin. Original captures, source files, reports and tar bytes are unchanged. This correction adds no causal False-versus-None mechanism beyond the observed errors.

## Limitations

- Exploratory inspected DEV episode IDs, not clean held-out confirmatory evidence. No learning, fit, improved-learning, recursive-learning, H1/H2, or automatic-promotion claim.
- V2 is an externally supplied instruction bundle: it strengthens ACT-prefix/two-line/no-fence instructions, includes the literal example 2,5,9 and requires a prior prediction that v1 allowed to be omitted. Not an isolated formatting-only intervention.
- All states share episode IDs and scheduled wake budgets but choose their own actions and receive different realized outcomes and histories. Seed effects cannot be isolated as record-only effects.
- First versus second turn is descriptive, not randomized: histories, selected triples, priors and world outcomes differ. Earlier actual records are fed into subsequent prompts.
- Production eligibility is source-faithful public record acceptance, not correctness of the prior prediction, discovery of the hidden rule, or a write/learning endpoint.
- CPU replay validates captured request/event/source/score consistency; it does not independently authenticate a GPU/model origin. Native custody assertions are bound archived wrapper evidence, not a new native check.
- Formation tar files deliberately omit standalone dependency payloads. A separate frozen dependency/spec/protocol tar is now available and locally hash-verified; both versions' source/core/protocol/spec payloads match recorded pins. Main reports native/VM archive hash agreement; no fresh native access was performed.
- V1 archive SHA256 is computed from the preserved local tar and report cross-bindings; v2 archive/report also match user-supplied pins. No new native copy/hash confirmation was performed.
- Field counts are descriptive diagnostics and can remain true when another schema field makes the whole record ineligible; error arrays are hierarchical/overlapping, not independent counts.

## Reproduction and output scope

Local stdlib-only replay: import the report-pinned core without bytecode writes; dependencies=core.load_dependencies(source_root=plan["source"]); core.audit_capture(each archived formation,dependencies=dependencies); compare core.compare_states(captures,dependencies=dependencies) with archived report["comparison"]. Verify tar/report/core/source SHA256 first, then compare each archived native request.core_request and response with its capture event. No native collection function is invoked.
Validation asserts128v2 native calls,64v2 records,all64priors available,27nested record failures,exact expected7/14/8/8 counts,and two literal example-triple matches. Detailed request/response hashes and source/function pins are in JSON.
Only `/tmp/astra_real_record_v2_analysis_20260913.json` and `/tmp/astra_real_record_v2_analysis_20260913.md` created. Reserved finding sequence149; no use of148.

## Separate frozen provenance bundle

`gpu_artifacts_local/real_record_20260913/astra_actual_record_frozen_sources_20260913.tar` SHA256 `e2ec97cad381ae4686be3830d02bd7533a20406bb5eb84164a92d369a144b749`. Local whole-archive hash and 12 distinct source/core/protocol/spec payload pins verified. Both original capture tar files remain unchanged. Native/VM bundle agreement is Main-reported, not a new native check by this sidecar. The previously unavailable v1 protocol bytes also match their recorded pin.
