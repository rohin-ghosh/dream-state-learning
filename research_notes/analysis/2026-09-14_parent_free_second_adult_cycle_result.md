# Second parent-free adult cycle: bounded independent reduction

2026-09-14 UTC. All eight stages are terminal and independently replayed from
captured outputs. No model, tokenizer, forward pass, GPU call, fit, remote write,
native-source edit, or commit was performed by this worker. This is offered
experience plus format scaffolding, not autonomous selection, parenting, H1/H2,
or an unconfounded learning-rate comparison.

## Result

The new bank is `ASTRA-CUE-ADULT-CYCLE-20260914-A2`. Actual learned-reader calls
use **W0 in both BEFORE and AFTER**. Standalone W8 remains separately scored;
cycle1's primary W8 endpoint is not retroactively replaced.

| Raw-recomputed panel | CUE_REPLAY BEFORE → AFTER | CUE_LOSS_OFF BEFORE → AFTER |
|---|---:|---:|
| New own-parametric GOAL | 2/4 → 4/4 | 2/4 → 2/4 |
| Own episodes with READ | 4/4 → 4/4 | 0/4 → 0/4 |
| Own episodes with second READ | 4/4 → 2/4 | 0/4 → 0/4 |
| Own actual reader calls | 8 → 6 | 0 → 0 |
| Reader-disabled GOAL | 2/4 → 2/4 | 2/4 → 2/4 |
| Reader-disabled READ / second READ episodes | 4/4 / 4/4 → unchanged | 0/4 / 0/4 → unchanged |
| New exact recall W0 | 0/4 → 4/4 | 0/4 → 4/4 |
| New exact recall W8 | 0/4 → 4/4 | 0/4 → 4/4 |
| Old exact recall W0 | 8/8 → 8/8 | 8/8 → 8/8 |
| Old exact recall W8 | 7/8 → 8/8 | 7/8 → 8/8 |
| Held external-text GOAL | 8/8 → 8/8 | 4/8 → 4/8 |
| Unseen exact MISS | 0/4 → 0/4 | 0/4 → 0/4 |

Original four-fact retention is 4/4 at both wrappers throughout. Prior-adult
four-fact retention is W0 4/4 throughout, W8 3/4 → 4/4 in both arms. Aggregate
eight-fact totals must not obscure this distinction.

### Exact behavior changes and retained failures

Cue own episodes2/3 are newly successful. Before fitting, the actual W0 reader
returns fabricated field content for new addresses, not exact new-bank records.
Both goals then receive the first listed port. After fitting, the reader returns
the exact new records; episode2 changes `ROUTE P_MLFJXQ3WZH` to
`ROUTE P_X3KIPDIW4F`, and episode3 changes `ROUTE P_FWMNJO5UYN` to
`ROUTE P_ONQCERJ5LE`. Episodes1/4 remain successful and now stop after one READ;
episodes2/3 use two. All six actual AFTER learned-reader returns are correct.

Off own episodes2/3 remain wrong and never consult memory, despite successful
standalone recall of all four new facts. Its episodes3/4 merely lose an allowed
terminal LF on their ROUTE output; that is not a content or outcome improvement.
Cue reader-disabled still reads twice per episode and succeeds only2/4. Held
panels and unseen-MISS failures remain in the evidence; nothing is dropped or
rescored permissively.

The sole old W8 failure before this fit is again prior-adult fact3,
`E_3FIXU7HBPN` (old-retention row7). The following are exact raw strings, shown
with escaped final LF:

```text
cue BEFORE: EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ4 DID P_XN2MTIYXEC GOT N_7G6JCNMNEQ EVIDENCE R_IU33SBN5QW\n
off BEFORE: EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZQ DID P_XN2MTIYXIAZ GOT N_7G6JCNMNEFC EVIDENCE R_IU33SBN5FVJ\n
both AFTER: EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ DID P_XN2MTIYXOF GOT N_7G6JCNMNEO EVIDENCE R_IU33SBN5QW\n
```

Thus this is correction of field-content corruption, not newline repair. This
retention improvement occurs under rehearsal of the prior-adult material; it
does not establish general wrapper robustness on untrained banks.

## Collection, prior binding, and mixture

Both collections replay to4/4 grounded events,8 calls,32 new rows, no parent,
and no collection-time fit. Both have identical full COLLECTION SHA-256:
`d5d9162827c5f621644d96791c751283b50cde954c30c9ac87e2ed9a273f55c5`.
Captured EXPLORE prompts, environment receipts, EVENT outputs, failure fields,
and FINAL_LF_ONLY canonicalization are recomputed by the frozen pure helper.
Identity exclusions are replayed against original memory, both collector banks,
both held banks, prior adult bank, and unseen-MISS bank. This is new material,
not a clean scientific claim; collection calls are not a public teacher.

`--prior-capture-root` binds each arm's cycle1 collection and training receipt
to its cycle2 initial child. The prior collection SHA is
`8f9c66609077f15af1469caed513513d2db731a2a10cce65298dfbc81b53924a`.
The reducer joins the prior collection's own initial receipt to the cycle1 fit's
initial receipt, **not** to the cycle2 initial receipt. The latter is the cycle1
train RESULT hash:

| Binding | CUE_REPLAY | CUE_LOSS_OFF |
|---|---|---|
| Prior train RESULT SHA | `3eaad009cc1546fa62209a1871b0b129140db485afc4676f057a93333faf8046` | `9fe1d0ebf5874749132b4f52b074f7f18a6f2e86bb1df79146386b1c543b75ba` |
| Loaded initial state | `07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300` | `b0693f1a3645796f78e9e98298ac92376aad7c408472584bf76af35aee6fb617` |
| Saved/reloaded AFTER state | `dedc0efa29cd3245cdf01414ba0f4ddadf2e012a28a29e3b88c19ed6c9ec16c5` | `524c97c489bbefd894a3a139f719956eaa9a6f6393d52c1b7de27ce8a99d3772` |

The initial adapters differ between arms. Within each arm, collection/train/
BEFORE bind to the same initial adapter, and AFTER loads the recorded changed
training state. Saved adapter-file receipts, prior collection paths, base hash,
memory/cue provenance, tokenizer signature, and cycle/master are joined.
This worker does not independently load tensors to remeasure these native
state attestations. Declared unchanged frozen base state is
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.

Both fits have116 masks: OLD64 + CUE20 + NEW32. Original old rows0:32 match
`99258bf00abe7854b86b3497a5b0e8cb9db0b59b4269a77d7641ef72653f830a`;
old rows32:64 exactly equal the replayed prior collection. New rows exactly
equal current child-generated material. All32 new row target-ID sequences join
actual EVENT generation IDs; all20 cue targets join the existing actual cue
captures. All116 masks satisfy contiguous final-target-only supervision,
matching input/label/target IDs, EOT151645, and masked template LF198.

All400 logged updates replay the independent schedule: update1 `(0,64,84,85)`,
update400 `(15,83,114,115)`. Group presentations are400old/400cue/800new.
Old rows0–15 receive7 presentations and16–63 receive6: original memory receives
208 versus prior adult192, not equal subgroup doses. Each cue row receives20
and each new row25. CUE_LOSS_OFF suppresses slot1 cue gradients with the original
denominator: both original label totals66912; active totals cue66912/off62332.
Logged scale and label counts are checked at every update. Whole trajectories,
including prior fits and initial adapters, differ; this is not a pure learning-
rate or single-adult-fit causal isolation.

## Time, cost, raw retention, and reproduction

| Stage (UTC, 2026-09-14) | Cue completion / elapsed | Off completion / elapsed |
|---|---|---|
| Collection | 10:30:38.628 /65.887s | 10:30:37.805 /65.092s |
| Training | 10:38:14.517 /381.111s | 10:38:14.808 /381.457s |
| BEFORE | 10:34:21.400 /148.039s | 10:33:52.440 /119.038s |
| AFTER | 10:40:35.480 /140.060s | 10:40:10.158 /114.374s |

Native stage durations include setup and overlap; they are not GPU-kernel time
or additive campaign wall time. Total captured generation calls276 (collection
16, BEFORE132, AFTER128), with41792 prompt and8466 emitted tokens. Fits add800
updates across arms. Dollar cost is not available from these receipts.

Local root: `gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/`.
`capture/{arm}/{collect,train,before,after}` preserves all bounded completed-stage
raw/config/result files, including TRAINING_ROWS, MASKS, LOSSES, old-retention
rows01–08, nested PANELS, CALL files, and individual episodes. `remote_completed.sha256`
and `remote_after.sha256` match local bytes for352 files totaling2375637 bytes.
The reducer replays64 routing episodes, joins64 old-retention calls, and checks
all collection and probe outputs. Exact mechanisms above can be inspected at
`capture/{arm}/{before,after}/new_task/OWN_PARAMETRIC_EPISODE_02.json`,
`OWN_PARAMETRIC_EPISODE_03.json`, and sibling `OLD_RECALL_W8_07.json`.
Failures remain in full raw evidence. No base/tokenizer cache or adapter tensors
were retrieved for this bounded reduction.

Frozen source snapshot is archived locally from commit
`c56170d36d8dbbe76cf5971c9f5a0ef458d335b8`, not the changing worktree. Remote source
root is `/tmp/astra_adult_cycle2_source_20260914_attempt1`; remote runner/helper
hashes matched the local snapshot:

- Runner: `1c9993bd48fd94b596b5150b03391b181d4d72fe5789a8c5fedb0fe7a8dd360d`.
- Pure material: `95a6bac9303937056a8cd646c15f0cebd356780237ec14decdd881d040cac0b2`.

```bash
python3 -B tools/astra_adult_cycle_reduce.py \
  --capture-root gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/capture \
  --source-root gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/source \
  --prior-capture-root gpu_artifacts_local/astra_adult_cycle_first_result_20260914/after_snapshot \
  --cue-capture gpu_artifacts_local/astra_adult_cycle_first_result_20260914/upstream/cue \
  --output gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/ANALYSIS.json

PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  tests.test_astra_adult_cycle_reduce \
  tests.test_experienced_event_adult_cycle \
  tests.test_experienced_event_microloop -q
```

Validation:50 focused+adjacent tests pass. Tests cover116-mask schedule/doses,
prior receipt/adapter/master drift, prior target drift, cycle replay, eight-fact
retention, actual-reader W0 versus legacy W8, target-only masks, raw failures,
and missing/failed stages. Full cycle1 evidence also reduces successfully in a
separate process against its original frozen source (legacy callback has no
`old_count` keyword). Cycle2 returns `ALL_STAGES_TERMINAL`, no pending stages,
and `no_native_imports=true`.

Remaining limitations: one fixed new bank and one trajectory per arm, offered
rather than self-selected experience, repeated same-bank evaluation, rehearsed
old targets, pre-existing between-arm confounding, absent exact abstention,
and native receipt rather than independently loaded tensor verification.
Reducer/tests/this memo are released to Main for integration; no commit made.
