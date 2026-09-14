# Independent result: two-hop parametric memory write

Reviewed September 14, 2026, after the terminal capsule arrived. This is a bounded local evidence review, not an ancestry audit, implementation review, or launch authorization. Only this memo is edited; no model loading, GPU, remote action, or experiment is performed.

## Finding

**The saved traces support an actual parametric-read-to-action interface, without a captured-text fallback in the PARAMETRIC condition. They do not support reliable two-hop control.** After one mixed memory write, all four written records are recalled exactly under the declared serialization, including all 16 in-episode reader responses. Those actual native responses enter the subsequent actor prompts unchanged. Two tasks then reach their final goals through two legal committed routes; two fail despite having received every correct record.

The AFTER PARAMETRIC and OWN_TEXT conditions have the same taskwise successes, read-address sequences, route commands, commits, and failure types: tasks 1 and 2 succeed, tasks 0 and 3 fail. UNAVAILABLE succeeds on none. This establishes the observed interface behavior on this one now-written DEV graph, not universal planning, a whole-life comparison, an isolated memory-gradient effect, or H1/H2.

## Capsule and direct checks

All artifact paths below are relative to:

`gpu_artifacts_local/astra_event_two_hop_memory_terminal_20260914_attempt1/extracted`

- Independently hashed sibling `terminal.tar.gz`: `82313377e0a72f79ebb6a1cca2439f27a54b97718ce2db6fd6aaf8ed190ba7e4`, matching the supplied capsule digest.
- `launch/source_commit.txt`: `7c773aacaf0c6a47f510d6f38459ac8270521335`; guardian `398924`.
- Guardian interval: **2026-09-14 15:58:28–16:08:55 UTC**. Individual saved intervals: BEFORE 15:58:28.815–16:00:51.485; TRAIN 16:00:52.580–16:04:47.035; AFTER 16:04:48.090–16:08:54.686 UTC.
- BEFORE/TRAIN/AFTER are COMPLETE, with fits 0/1/0 and no phase-level FAILED artifact. Their bindings and copied source collection agree. `STATES.json` agrees with each receipt's input/output state fields.
- Independently verified every listed BEFORE/AFTER output-file hash (67 and 230 respectively), all four training-file hashes, and all three saved adapter-file hashes. Each phase's entry hash matches the archived memory driver. Inventories and saved CALL indices/errors match the receipts.
- Direct JSON reduction, without invoking the author's evaluator, checked episode seals, native-call/trace equality, subsequent actor-message construction, committed transitions against the world edges, success from final arrival plus two commits, recall comparisons, and scheduled token counts.

### Saved-state joins

| Stage | Loaded state | Final state | Receipt SHA-256 |
| --- | --- | --- | --- |
| BEFORE | `37ec…8c0` | `37ec…8c0` | `4f6d9ecdccd941f5a7f1090bad051ac8adffba8e95c6296951ec56803a025520` |
| TRAIN | `37ec…8c0` | `9d3674…9c86` | `35fdd06530f68a8e2555fb72c4a212741a089f3f15298bcd5bd769e0136632c3` |
| AFTER | `9d3674…9c86` | `9d3674…9c86` | `9df89e6f1c2f808fa4ce9199dc405df28e1e8a7ca1afecdce9cabd48d08017a5` |

Full initial state: `37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
Full written state: `9d36743c85f82ef0e064484369393a4761c8e2cdd512e1527818f9c4ca5a9c86`.

TRAIN and AFTER reference the exact BEFORE receipt hash; AFTER references the exact TRAIN receipt hash. The saved adapter weight file hashes to `396c03cd191d1fb75bfcdbfecb262005f6a75ba8f6ae44d789fa178817508530`. This file hash is distinct from the logical tensor-state hash. Frozen-base and readonly tensor-state checks are reported by the native receipts; this review verifies their joins and saved-file integrity, **not an independent recomputation of model/base tensor hashes**.

## What was written and how much

`train/TRAINING_ROWS.json`, `MASKS.json`, `RECIPE.json`, and all 100 `LOSSES.jsonl` entries agree on 254 rows: 128 old-memory, 20 cue, 62 audit, 12 prior trajectory, and 32 new-memory rows. The latter cover four actual captured child EVENTs under W0–W7, with no replacement facts. Their source-raw hashes and target hashes match `COLLECTION_SOURCE.json`; all four source records agree with their carried event captures and recorded world edges.

For zero-based update offset `u`, the four row indices are exactly:

`[u % 128, 128 + u % 94, 222 + (2*u) % 32, 222 + (2*u+1) % 32]`.

The independent sum of causally shifted, unmasked labels equals both the per-update logs and **16,175 total supervised labels**, including target EOT labels:

| Group | Row presentations | Active labels |
| --- | ---: | ---: |
| Old memory | 100 | 5,143 |
| Cue | 26 | 296 |
| Audit | 62 | 400 |
| Prior trajectory | 12 | 136 |
| New memory | 200 | 10,200 |
| **Total** | **400** | **16,175** |

Each of the four new facts receives 50 presentations. Recipe: 100 updates, batch four, fresh AdamW at `3e-5`, seed 0, rank 8, mean causal CE. There is no token-equality claim. This is a **mixed write with rehearsal and trajectory targets**, not a memory-only intervention. W8 recall is an additional wrapper relative to the new rows' W0–W7 coverage, not an unseen-world test.

## Recall, actual reader output, and action context

| Measurement | BEFORE | AFTER |
| --- | ---: | ---: |
| New exact recall W0 | 0/4 | 4/4 |
| New exact recall W8 | 0/4 | 4/4 |
| Exact PARAMETRIC responses within tasks | 0/16 | 16/16 |
| PARAMETRIC task success | 0/4 | 2/4 |
| OWN_TEXT task success | Not rerun in BEFORE | 2/4 |
| UNAVAILABLE task success | Not rerun in BEFORE | 0/4 |

The 16 responses repeat **four unique facts**, not 16 independent memories. BEFORE returned incorrect EVENT bodies carrying the requested addresses, not `MISS`. Its four tasks made one legal route and then stopped on a duplicate address. UNAVAILABLE is a declared external service response, not evidence that the parametric reader learned to abstain.

AFTER's four PARAMETRIC tasks each request all four addresses. For every read, the saved native `role=memory` call has an address-only W0 prompt, its complete response matches the episode's memory trace, and the next actor prompt contains precisely `MEMORY RESULT\n` followed by that response's raw text. Actor calls also match their saved traces. The reader is not supplied a source table, a route witness, or a substituted intermediate goal. Archived `source/gpu/astra_event_two_hop_memory.py`, `evaluate_graph`, dispatches PARAMETRIC to `generate(memory_messages(...))`; only OWN_TEXT uses the captured store. Thus the existence of the store in the evaluator does not constitute a fallback on this branch.

**Serialization qualification:** captured child EVENTs have no final LF; new training targets and exact parametric returns have one final LF under `FINAL_LF_ONLY`. The source bodies/identifiers match, but PARAMETRIC and OWN_TEXT contexts are not byte-identical at that trailing LF. The actor receives the actual parametric LF unchanged; the review found no read-time repair or substitution. Their observed commands/commits nevertheless match taskwise.

## Taskwise committed outcomes

From `after/FRESH_PARAMETRIC_EPISODE_00.json` through `_03.json`, cross-checked against the corresponding native CALLs and OWN_TEXT episodes:

| Task | Final goal / display order | Actual ROUTE commands | Commits | Terminal outcome |
| --- | --- | --- | ---: | --- |
| 0 | `N_JHDSMLVMTV` / forward | `P_AYK4AJ3M7N`, then `P_OSJB7PXJ7E` | 2 | Wrong legal branch reaches `N_44AN3UAXYD`; `dead_end` |
| 1 | `N_JHDSMLVMTV` / reversed | `P_YW4FRYEBND`, then `P_T6RLPFRTVW` | 2 | `reached_goal` |
| 2 | `N_44AN3UAXYD` / forward | `P_AYK4AJ3M7N`, then `P_OSJB7PXJ7E` | 2 | `reached_goal` |
| 3 | `N_44AN3UAXYD` / reversed | `P_OSJB7PXJ7E` immediately after the four reads | **0** | `invalid_route` at original root `N_P4NCI2CBPM` |

Task 3 proposes a downstream port prematurely; it does **not** first commit an incorrect first hop. Task 0 makes two legal transitions but pursues the other goal. Both failures occur after all four correct records are in context, locating the observed remaining failure after retrieval, in route selection/sequencing. These are two goals × two display orders on one fixed graph, not four independent worlds.

AFTER's 166 calls independently total 94 actor, 16 memory, 8 new-recall, 32 old-recall, and 16 held-audit calls. All native capture error fields are null; task failures remain in the results rather than being dropped.

## Retention and interpretation limits

- Old recall is 16/16 at W0 and 16/16 at W8 against the saved expected records; the 32 recall artifacts match native calls. This review does not reopen the old facts' ancestry.
- Held audit is 16/16: eight true and eight fault cases. Captures match native calls and each case's expected answer. This diagnostic explicitly supplies a receipt-grounded source table; it is not a demonstration of autonomous parametric truth checking inside the route loop.
- Taught-graph OWN_TEXT remains 3/4, with tasks 0–2 successful and task 3 ending at the wrong dead end; actor calls and final-arrival scoring agree with the saved episodes.
- The capsule embeds the earlier trained transfer baseline at fresh OWN_TEXT **3/4**, versus **2/4** after this write. That baseline is reused, not a fresh learner or contemporaneous no-write rerun. Memory improvement must not be described as monotonic controller improvement.
- No conclusion here isolates the new-memory gradient from this write's other rehearsal, claims a clean/unseen graph after its facts were trained, or treats the audit/recall scores as H1/H2 evidence.

**Bottom line:** exact learned record retrieval is achieved on the written facts; actual parametric responses are delivered to the action loop without text fallback; two tasks execute successful two-hop paths. The remaining failures are visible even with perfect available records. Accept that narrow result, not a stronger claim of reliable planning or a fully isolated causal learning mechanism.
