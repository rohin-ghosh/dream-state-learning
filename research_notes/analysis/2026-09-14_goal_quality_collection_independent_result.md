# SEQ262 quality collection — independent terminal review, 2026-09-14

**Released.** Frozen-source replay and independent call/episode/row reductions
confirm Main's collection counts: **696 new calls, 116/116 complete new coached
episodes; 756 reused rows; 1,452 admitted rows from 242 episodes/121 pairs**.
The discarded old pair and all source failures remain evidence. No substantive
count or admission discrepancy with `2026-09-14_goal_quality_collection_first_result.md`;
one small timing-label distinction is noted below. This review does not wait
for, gate, or approve any subsequent fit preparation.

## Bound evidence and checks

Root `C`:
`gpu_artifacts_local/astra_goal_quality_terminal_20260914_attempt1/extracted/astra_goal_quality_20260914_attempt1`.
The sibling `terminal.tar.gz` verifies as
`10d2bccf87dc65638710c64b546da2120e951370f23497f93f92c8e2514b4d1c`.
Source: `cefc1955f508a6f7d444f19271b1d89b3e217e08`; frozen protocol:
`cf742f62dc45810caeea3ec68272a9e1a8c97d3b7c6c06f148639252ba1738f1`.
Checked 758 prepare/assembled/unit evidence files against archive bytes and
42 imported frozen Python files against local Git objects. The protocol file
and helper bindings match. This is bounded checking, not full ancestor custody.

Using only frozen `gpu/astra_goal_quality_collection.py` and
`organism_v6/experienced_event_goal_quality.py`, replayed `source_plan`,
`reused_quality`, all four native `read_unit`/`replay_unit` checks and `assemble`.
The reconstructed capsule exactly equals `assembled/CAPSULE.json`'s inner
capsule, whose sealed document hash is
`6ad54ecbc52eccb81b1530c0ce3dcfbba647c552b7f2f150f711271f28aaab66`.
Prepare, unit and assembly bindings, output inventories/file hashes and unit
result references join. Private scale/goal runtime namespaces remain intact;
no old unbound default runtime or live input/model loader was used.

All eight embedded original exposure documents and four reused teaching
documents match the local SEQ258 originals and bound result hashes. Directly
joined their 640 exposure and 768 teaching calls to original native captures,
including actual prompts/responses/errors and order. Native unit readback joins
all 696 new calls. These are old-call reuse checks, not regenerated calls or a
repeat baseline/ancestor audit.

## Actual outcomes and admitted rows

| New unit | TRAIN worlds | Calls / actual rows | Complete episodes | Admitted pairs |
|---|---:|---:|---:|---:|
| 0 | 7 | 168 / 168 | 28/28 | 14/14 |
| 1 | 8 | 192 / 192 | 32/32 | 16/16 |
| 4 | 7 | 168 / 168 | 28/28 | 14/14 |
| 6 | 7 | 168 / 168 | 28/28 | 14/14 |
| Total new | 29 | 696 / 696 | 116/116 | 58/58 |

Direct episode checks require six actual commands matching the coached plan,
four memory reads, two committed routes, final CURRENT equal to GOAL and
`reached_goal` termination. Pairs additionally bind the same initial node/port
display, opposite goals and distinct correct first ports. Frozen scoring and
direct reductions agree; no new failed episode or missing attempt was found.

Reused shards 2/3/5/7 contain **768 calls, 128 attempted episodes and 127
complete episodes**, not 128 complete episodes. The pair filter retains 126
episodes/63 pairs/756 rows: 192 rows each from shards 2/3/5 and 180 from shard7.
Original shard7 still records `ready=false`, original admitted rows=0. Its
180 rows are admission under this new recipe, not a rewritten original success.

The rejected pair is shard7, `BLOCK-2-TRAIN-A`, tasks **(0,2)**:

- Task0 succeeds in six calls/four reads/two routes but contributes no rows
  because its opposite-goal counterpart fails.
- Task2 has six calls/four reads/one committed route and terminates
  `invalid_route`. Its last response is `ROUTE P_YIK66TWWIW` while CURRENT is
  `N_FBL4WYH7LC` and the offered port is `P_MVGXYEPFPA`.
- Both full episodes, all twelve captures, outcomes and rejection reason remain
  in the assembled evidence. Neither a canonical response nor a teacher answer
  substitutes for them; neither task contributes an admitted target.

Across old and new work, **1,464 teaching calls and 244 attempted episodes**
are preserved. Of these, 243 episodes complete, but 242 are admitted: the one
failure and its one successful partner explain all twelve unretained calls.
All 1,452 output rows join exactly to actual response bytes, actual student
prefixes, call index/hash, source collection hash and episode identity. Every
admitted episode contributes six rows; every rejected episode contributes zero.

## Source population and PROBE preservation

Recomputed original source totals: **320 successful actual ROUTEs, 316 valid
EVENT responses, four failed EVENT responses**. The original population stays
64 TRAIN worlds/256 tasks/128 pairs. Three source-invalid TRAIN worlds exclude
12 tasks/six pairs before teaching; the eligible population is therefore
61 worlds/244 tasks/122 pairs, not an unbiased replacement sample.

Source exclusions, with zero-based world indexes:

| Shard/world | Failed EVENT | Recorded source failure |
|---|---|---|
| 0/1 TRAIN | `E_TVGFKY6VPR` | `not exact EVENT` |
| 4/7 TRAIN | `E_2P4JMFEOJV` | `EVENT_not_grounded_in_actual_receipt` |
| 6/5 TRAIN | `E_IC5TU6ZLTQ` | `not exact EVENT` |
| 1/8 PROBE | `E_W5YA3H6TNF` | `not exact EVENT` |

The fourth failure does **not** remove a PROBE world. All 16 original PROBE
worlds and their four-address maps are present, preserving the intended future
64-goal/32-pair denominator. Exactly one address, `E_W5YA3H6TNF`, maps to literal
`MEMORY UNAVAILABLE`; its three valid siblings remain original actual text.
All other PROBE entries are original actual responses. This verifies the
stored future-readout source contract, **not execution of that future readout**.
No corrected SEQ259 candidate is substituted and no baseline is repeated here.

Relative to the original 1,536-row maximum, the 84-row reduction is exactly
72 from source-excluded worlds plus twelve from the rejected eligible pair.
The resulting 121 pairs are 121/122 eligible pairs, or 121/128 original pairs;
both denominators matter. Outcome/source filters are explicit, adaptive DEV
selection, not random attrition or evidence of general transfer.

## Visibility, state, cost and limits

All old/new teaching captures are source-informed coached responses; they are
not autonomous planning. Replayed native prompts and public student prefixes
join; parent guidance is absent from every row prefix. None of the 272 current
PROBE identifiers occurs in any teaching guided/student prompt. No score input
or correction-diagnostic candidate participates in this selection. New and
reused targets are actual child outputs, not researcher-authored replacements.

All 696 new calls have null native errors, terminal=true/truncated=false,
recorded contexts <=2,048 and generated token-ID counts <=160. The four units
complete with no `FAILED.json`. Each records loaded/before/after state
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`,
unchanged base, zero fits/updates and training disabled. Prepare and assembly
record zero model calls. **Recorded state/hash joins are not live tensor/base
authentication.** There is no learning-dose, retention or efficacy result.

New native elapsed seconds by unit0/1/4/6 are
185.747419/199.119869/188.427423/183.441456; sum **756.736168 seconds**, about
0.210 allocated A40-hours, including setup and excluding prior reused work.
Generated token IDs total 7,718, not supervised training labels. Guardians
83105–83108 start 19:09:57 UTC; finish 19:13:04/19:13:17/19:13:07/19:13:01.
These are phase/guard records, not GPU utilization or summed campaign wall time.

Minor timing precision: Main's 26.702149s “prepare” value is the recorded
input-admission timer; total prepare start-to-finish wall is 26.751752s.
Assembly wall is 35.032524s, including its own 26.317934s admission work.
Do not count that internal assembly admission a second time.

Commands/checks: local `sha256sum`, `git show`, bounded `sed`/`find`/JSON
inspection, and inline standard-library Python with frozen helper replay,
hash/byte comparisons and direct reductions. An import blocker excluded torch,
transformers, tokenizers, peft, numpy and HTTP clients; none was imported.
Final whitespace check: `git diff --no-index --check /dev/null <this memo>`.
Only this memo is written: no GPU, network, tokenizer/model loading, new native
calls, replay files, code changes or broader framework. No future L2/fit outcome,
SEQ258 recovery, checkpoint promotion or H1/H2 claim is licensed. Ownership
released for Main to bind independently of ongoing branches.
