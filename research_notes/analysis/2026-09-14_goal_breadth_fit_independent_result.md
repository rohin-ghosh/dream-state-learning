# SEQ260 breadth fit — independent terminal review, 2026-09-14

**Released.** Independent raw-call/episode reductions agree with
`2026-09-14_goal_breadth_fit_first_result.md`. Both fits and readouts complete;
both fail the conjunctive target. FULL acquires all TRAIN goals/pairs but has
no incremental PROBE advantage over the active label-masked control. Old
recall matches; audit and previously-fresh retention do not. This is bounded
result verification, not promotion or approval of broader scientific claims.

## Bound evidence

Let `C` denote
`gpu_artifacts_local/astra_goal_breadth_train_terminal_20260914_attempt1/extracted/astra_goal_breadth_train_20260914_attempt1`.
The sibling `terminal.tar.gz` SHA256 verifies as
`2294116da812f48bfac1beba25b43d64c89a88e477c2976c55c22444bf19e323`.
Bound source is `712d5f2b738f3c33dc905037e57580eee9319441`; protocol
`2026-09-14_goal_breadth_recipe_design.md` hashes to
`3f2e4307dab0ad7aa2d8cf62accf14203da1b6ac32fd58779c62840929640ed7`.
Checked 1,018 evidence files against archive payload bytes (prepare, both arm
trees, saved adapters/launch records, root source marker), and 11 bounded
frozen source/helper/test files against local Git objects. This is not a
complete archive/extraction inventory certification.

## Recomputed outcomes

Counts below come from captured responses and frozen replay, with independent
legal-transition, final-goal and strict-pair reductions, not summary totals
alone. A strict pair requires both same-display opposite-goal tasks to succeed,
including the required legal commits and correct distinct source first ports.

| Readout | FULL_TARGET | NEW_TRAJECTORY_LOSS_OFF |
|---|---:|---:|
| TRAIN OWN_TEXT goals / pairs | 32/32; 16/16 | 17/32; 4/16 |
| PROBE OWN_TEXT goals / pairs | 5/8; 1/4 | 6/8; 2/4 |
| PROBE A / B pairs | 1/2; 0/2 | 2/2; 0/2 |
| UNAVAILABLE goals / pairs | **1/8; 0/4** | 0/8; 0/4 |
| Old recall W0 / W8 | 16/16; 16/16 | 16/16; 16/16 |
| Held audit | 15/16 | 16/16 |
| Original taught graph | 2/4 | 2/4 |
| Previously fresh graph | 4/4 | 3/4 |

Exact failure identities (task/world indexes are zero-based):

- PROBE A: FULL succeeds tasks 0/2/3, control all four. FULL A1 is a
  wrong-first-port dead end: this single task accounts for the control's extra
  goal and pair. Both arms succeed B1/B2 and fail B0/B3 as wrong-first-port
  dead ends. The replayed first-current-port/no-READ reference gets 2/4 goals,
  0/2 pairs in each world, using zero native calls.
- UNAVAILABLE: FULL B1 succeeds; its other cases have five duplicate-address
  and two dead-end failures. Control has eight duplicate-address failures.
  Thus zero unavailable *pairs* must not become zero FULL unavailable *goals*.
- Original taught: both succeed tasks 0/2 and dead-end on 1/3. Previously
  fresh: control task 3 fails `invalid_route` at five calls; FULL succeeds all.
- Held audit: FULL fails case 10 (true case, skin 1, `E_VEEAOY3IIH`), returning
  the bare event plus newline instead of `NONE`: true 7/8, fault 8/8. Control
  passes both 8/8. Expected values were independently checked against source
  tuples and native case prefixes replayed.
- Control TRAIN successes by worlds 0–7 are `[0,3]`, `[0]`, `[1,2]`,
  `[0,1,2]`, `[0,1,2,3]`, `[0,1,2]`, `[3]`, `[2]`. Successful pairs are
  world 3 pair(0,2), both world 4 pairs, and world 5 pair(0,2). Its 15 failures
  are 13 dead ends, one duplicate address and one invalid route.

Both fail PROBE >=3/4 pairs, >=1 pair in **each** PROBE world, and original
taught >=3/4 tasks. Both pass old recall >=15/16 separately at W0/W8, audit
>=15/16, and previously fresh >=3/4. Matching recall is not identical retention.

The hash-joined SEQ257 baseline, using its already released review, is TRAIN
18/32 goals and 2/16 pairs; PROBE 4/8 and 0/4; UNAVAILABLE 2/8 and 0/4.
LOSS_OFF is an active old-row/rehearsal fit, not a no-update baseline.

## Inputs, supervision and actual dose

Both arms have 414 identical material rows/reference encodings: 128 memory,
20 cue, 62 audit, 12 original trajectories, 192 new actual TRAIN trajectories.
New rows exactly match SEQ257 `teach/LESSONS.json`, including captured student
prefixes without parent procedural/source-hint sections. No current PROBE
identifiers occur in the training material. Old 222 encodings and four old
material groups match bounded SEQ256 FULL references; the SEQ257 collection
binding and exposure/teach/baseline result hashes join. No ancestor audit was
repeated.

Only control rows 222–413 lose labels (all `-100`); input/target IDs and earlier
labels stay identical. Stored masks have contiguous target-only supervision,
masked prefixes/initial causal label and target EOT 151645. Input lengths are
<=2,048; new targets <=160. These are encoded-artifact checks, not retokenization.

Both record one fresh-AdamW fit, rank 8, seed 0, batch 4, learning rate 3e-5,
exactly 1,632 updates. For zero-based update offset `u`, recomputed batches are
`[u%128, 128+u%82, 210+(2*u)%204, 210+(2*u+1)%204]`.
This gives 1,632 memory and 1,632 cue/audit presentations, 192 original-trajectory
presentations and **3,072 new-target presentations**: each of the 204 trajectory
targets appears 16 times. FULL supervises those 3,072 new presentations;
control supervises none. Actual/reference labels are **133,272/133,272** versus
**98,744/133,272**, a 34,528-label difference, not matched active label dose.
All 1,632 batch entries in each `train/DOSE.json` and `LOSSES.jsonl` join to
indexes, presentations, finite losses and active/reference normalization.

## Calls, states and cost

Replayed all **758** captured native calls: FULL 384/384 cap, control 374/384.
Each joins messages, metadata, response/error and downstream readout. All
native errors are null, terminal true, truncated false; recorded contexts
<=2,048 and generated IDs <=160. FULL roles are actor336/audit16/recall32;
control actor326/audit16/recall32. No cases are dropped: three control TRAIN
successes (world3/task2, world6/task3, world7/task2) take four instead of six
calls; TRAIN world7/task1 invalid-route termination saves three; fresh/task3
saves one. This explains all ten fewer calls. Training has zero generation
calls, not zero optimizer forwards. No `FAILED.json` was found.

Recorded initial state in both arms:
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
Saved states:

- FULL: `8a94f4ff0eb297c49c0383e7522db17a66eb6baf17a7b4c79f564ec3a99abb42`.
- LOSS_OFF: `aa282d0ba3c34b398fd7795f5daaec759f786aef7f023623b641655c42a8908e`.

Train/`STATES.json`/saved/AFTER loaded/AFTER final joins agree, including the
training-result hash and recorded unchanged base. AFTER is training-disabled,
zero fits/updates. Adapter byte hashes and AFTER inventories (491/481 output
JSONs excluding RESULT) verify. **These are recorded state/file joins, not
authentication of live tensors or the actual frozen base.**

FULL train/AFTER elapsed: 3,149.808513403/341.226235628 seconds; control:
3,145.064271927/344.527446508. Sum 6,980.626467466 seconds, approximately
1.939 allocated A40-hours, excludes prior collection/prepare and outer guard
overhead. Guardians 412377/412378 record 18:00:35→18:58:48/18:58:47 UTC
(3,493/3,492 seconds). These are phase/guard elapsed records, not kernel
utilization or campaign wall time; the protocol ceiling is not actual cost.

## Checks and limits

Commands/checks used: local `sha256sum`, `git show <source>:<path>` byte
comparisons, `find`/`ls`/`sed` inspection; inline standard-library Python
(`json`, `hashlib`, `tarfile`, counters/assertions) for archive, mask, schedule,
label and episode reductions. Frozen CPU replay used `evaluate_goal_world`,
`first_port_reference`, `memory.recall`, audit `build_cases`/`collect_cases`,
and old-graph `memory.hop.run_episode`/score. Private breadth helper namespaces
were retained, not replaced with old unbound hop defaults. `unittest.mock.patch`
intercepted writes, comparing 80 would-be episode/recall writes per arm plus
summaries/audit/old-graph artifacts; no replay files were created. Final memo
whitespace check: `git diff --no-index --check /dev/null <this memo>`.

No GPU, network, launch, model/tokenizer/torch load, live tensor inspection,
TeX engine, source modification or new audit framework. One seed/lineage and
two fixed PROBE worlds do not establish population efficacy, robust semantic
composition or H1/H2. Coverage and legacy rehearsal changed together relative
to SEQ256, so this result does not isolate those changes. Only this memo is
written; ownership is released for Main to bind.
