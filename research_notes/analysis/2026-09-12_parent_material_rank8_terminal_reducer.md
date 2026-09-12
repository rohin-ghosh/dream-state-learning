# Terminal reducer for the exploratory parent-material rank-8 pair

Date: 2026-09-12 UTC

Scope: docs-only watcher audit of origin/main commit `6c798231` and the
already-running 64-schedule material pair. No source, run, node, adapter or
claim authority changed. This is deliberately a scout reducer, not C11.

## Plain verdict

The planned fit/probe is worth completing. It can causally show whether each
**specific trained adapter artifact** changes parent-free record-writing on
the four fixed probe tasks, and it can reveal immediate interface/task harm.
It can also localize where the exact lesson package stops working:

```text
fixed prompt -> grounded child material -> rank-8 write -> parent-free record
```

It cannot identify the semantic effect of parenting. The lesson is 203 tokens
per presentation and the sham 158; both are repeated in every model context,
so the 45-token difference compounds across the life. The two selected
corpora also have equal rows/steps but not necessarily equal supervised child
tokens. There is one formation schedule, one optimizer draw per arm and only
four probe episodes. The base is locally pinned but not officially
authenticated, and neither descendant has clean lineage.

Therefore the terminal label is always **exploratory exact-package evidence**,
never H1, durable parenting, writer qualification, or a final-child result.

## What is actually being tested

The formation stage is target-blind with respect to the final CompilerGym
deployment domain: all 64 tasks are from the task-disjoint Reasoning Gym train
split, the fixed teacher examples contain no task answers, and the probe uses
different gate families. The “parent” is not adaptive here. It is one static
lesson about writing a faithful first-person record after a measured action.

Teacher bytes are excluded from training. The writer takes the first 64
unique, source-joined child `NOTE_AFTER` records in physical ledger order,
masks the Situation prefix, and supervises only the child's record text. It
fits two clean-base rank-8 adapters for 48 steps each (`3` epochs, `lr=1e-4`,
optimizer seed `6102`). If either arm has fewer than 64 eligible records,
neither fit runs.

The probe starts fresh processes, supplies no teacher, childhood transcript,
retrieval state or training rows, and compares OFF then ON for each adapter on
four fixed gate episodes. Its narrow endpoint is faithful `Scratchpad` text
after an actual measured action. This is a raw child-record write, not the
full replay/paraphrase/contrast SLEEP compiler and not better puzzle solving.

## What the mismatch does and does not destroy

The 203-versus-158 mismatch does **not** make the scout meaningless. If the
isolated executions are valid, a formation difference is caused by the two
exact prompt packages, and an ON/OFF difference is caused by enabling that
specific adapter artifact on these four tasks.

It does destroy narrower attributions:

- lesson meaning cannot be separated from 45 extra teacher tokens per
  presentation;
- material content cannot be separated from differing child-token training
  dose;
- lesson-versus-sham adapter differences cannot be separated from one-draw
  optimizer variance (and device variance if the fits use different GPUs);
- a four-episode probe cannot establish a population effect or equivalence;
- selecting exactly 64 rows conditions the write on successful formation and
  discards any lesson advantage in producing *more* than 64 usable records;
- a positive articulation effect is a learned output habit, not evidence of
  task reasoning, long-term development, or the whole THINK/DREAM/SLEEP loop.

No normalization by prompt length repairs these facts. Report the doses.

## Exact terminal reducer

### 0. Verdict precedence

Emit exactly one terminal execution status before interpreting numbers:

1. `INVALID_OR_INCOMPLETE` if either formation, input/source check, fit,
   cleanup, probe, identity check or final revalidation is missing/failed;
2. `PAIRED_SKIP_INSUFFICIENT_MATERIAL` if either formation supplies fewer
   than 64 unique grounded records; or
3. `COMPLETE_EXPLORATORY` otherwise.

Never fill a failed arm, lower 64, reuse a partial root, or turn a skip into a
zero. Numerical directions below exist only under `COMPLETE_EXPLORATORY`.

### 1. Formation table: all 64 schedules, before first-64 selection

For arm `a` and episode `e`, recompute from source-joined rows:

```text
M[a,e] = number of measured executed ACTs
G[a,e] = number of unique grounded child NOTE_AFTER records
Y[a,e] = G[a,e] / M[a,e] when M>0, otherwise 0
C[a,e] = 1 if G[a,e] > 0, otherwise 0
B[a,e] = best authoritative task score
```

Report all 64 paired rows and, per arm:

- measured/invalid/unmeasured ACT counts;
- post-outcome, grounded and unique-grounded record counts;
- episodes covered (`sum C`), `mean Y`, and aggregate `sum G / sum M`;
- every rejection-reason count, missing NOTE_AFTER count, mean best score and
  mean ACT count;
- actual generation requests and teacher presentations;
- teacher tokens per presentation and
  `teacher_tokens_per_presentation * presentations`.

Report paired lesson-minus-sham differences in `Y`, `C`, best score and ACT
count. Use schedule as `n=64`; give paired bootstrap/randomization intervals
only as exploratory descriptions. Never use individual ACTs as independent
replicates.

Define the descriptive material direction exactly:

```text
F = mean_e(Y[lesson,e] - Y[sham,e])
FORMATION_POSITIVE = F > 0
  and count_e(Y[lesson,e] > Y[sham,e])
      > count_e(Y[lesson,e] < Y[sham,e])
  and mean_e(C[lesson,e] - C[sham,e]) >= 0
```

This is a directional label, not a significance or generalization claim.

### 2. Selected-corpus and fit table

For each arm report:

- available unique records and the exact first 64 selected source IDs;
- family, episode, source-score and rejection composition of those 64;
- input, supervised-child and masked-prefix tokens per epoch and over all
  three epochs;
- mean/min/max child-body tokens, corpus hash and source-map hash;
- exact rank, alpha, LR, epochs, steps, seed, final loss, adapter hash and
  device.

Give lesson-minus-sham supervised-token difference explicitly. Final loss
alone is not “absorption”: there is no bound pre-fit loss/read assay here.

### 3. Parent-free probe table

For each arm `a`, condition `c` (`OFF`, `ON`) and each of the four fixed
episode IDs, compute:

```text
m[a,c,e] = measured ACTs
g[a,c,e] = correct grounded Scratchpads
r[a,c,e] = g/m when m>0, otherwise 0
q[a,c,e] = 1 if at least one measured ACT occurred, otherwise 0
b[a,c,e] = authoritative best_score
```

Report the complete 4 x 4 episode table plus aggregate raw counts. Then report:

```text
L = mean_e(r[lesson,ON,e] - r[lesson,OFF,e])
S = mean_e(r[sham,ON,e]   - r[sham,OFF,e])
D = L - S
d[e] = (r[lesson,ON,e] - r[lesson,OFF,e])
     - (r[sham,ON,e]   - r[sham,OFF,e])
OFF_GAP = mean_e(r[lesson,OFF,e] - r[sham,OFF,e])
TASK_L = mean_e(b[lesson,ON,e] - b[lesson,OFF,e])
ACT_L  = mean_e(q[lesson,ON,e] - q[lesson,OFF,e])
```

Also report the corresponding sham task/action changes, ON/OFF output hashes,
action counts, reserved tokens and all judgment reasons.

Four episodes permit no conventional significance claim: even four same-sign
paired effects have a minimum two-sided sign-flip p-value of `0.125`. Do not
pool actions to manufacture a larger `n`.

### 4. Mechanical flags

- `PROBE_SATURATED` if both OFF aggregate articulation rates are at least
  `0.80`; an adapter null then has little headroom.
- `OFF_INSTABILITY` if `abs(OFF_GAP) >= abs(D)`; base-run variation is at
  least as large as the reported interaction.
- `TASK_ADVERSE` if `TASK_L < -0.05`.
- `ACTION_ADVERSE` if `ACT_L <= -0.25` (at least one of four episode-equivalents
  lost).
- `TRAINING_DOSE_UNMATCHED` whenever supervised child tokens differ (expected).
- `PARENT_DOSE_UNMATCHED` always for this run, with actual total exposure.

These are diagnostic flags, not accept/reject thresholds for H1.

## Interpretation table

| Observed pattern | Honest reading |
|---|---|
| `FORMATION_POSITIVE`; `L>0`, `D>0`; at least 3/4 `d[e]>0`; no adverse/saturation/instability flag | **Directional full-chain signal for the exact package.** The longer fixed lesson produced different child material and its specific rank-8 artifact expressed more faithful records without teacher text on this tiny panel. Semantic parenting and reliability remain unidentified. |
| `FORMATION_POSITIVE`, but the probe does not meet the directional criterion or is saturated | Lesson changes material formation; this probe does not show that the writer carries a usable difference. Saturation/probe sensitivity may be the bottleneck. |
| `L>0` and `S>0`, but `D<=0` or fewer than 3/4 `d[e]>0` | Generic child-record SFT may change record behavior. No demonstrated lesson advantage. |
| Formation is similar, but `D>0` | Possible content/optimizer accident after first-64 selection, not evidence the lesson improved formation. Inspect corpora and replicate; do not tell a parenting story. |
| `S>=L` or sham formation >= lesson | The exact lesson package has no demonstrated advantage over active sham. More words/repetition did not rescue it. |
| `OFF_INSTABILITY` | Runtime/base observation noise is as large as the apparent cross-arm interaction. ON/OFF artifact descriptions remain, but lesson-versus-sham comparison is indeterminate. |
| `TASK_ADVERSE` or `ACTION_ADVERSE` | The lesson-material adapter damages useful behavior/interface at this heat. A higher articulation rate cannot rescue that harm. |
| Either arm skips below 64 | Formation failed the material-sufficiency prerequisite. There is no adapter comparison. |

Avoid the word “null” as equivalence. Use `NO_DIRECTIONAL_SEPARATION` when
the positive pattern is absent without a harm flag.

## One smallest next clean experiment for each outcome

### If directionally positive: `M1-MATCHED`

Repeat the same narrow record lesson on one new 64-item train schedule, but
make the active sham exactly 203 tokens under the actual tokenizer. Preserve
all teacher bytes before generation. Cross **two common optimizer seeds** over
both corpora (four rank-8 fits) and use all 12 already-listed gate episodes,
counterbalancing ON/OFF order across seeds. Keep teacher text out of targets
and fresh probes. This single development replication removes the known
parent-dose and one-draw fit confounds without importing final deployment
material or C11 bureaucracy. A repeat signal would justify a later clean
lineage parenting canary; this scout itself never becomes its ancestor.

### If no directional separation: `P0-COACH`

Do not increase rank, epochs or parenting duration yet. Run the no-write
target-blind experiment in the prior parenting-gate audit: from one persisted
child failure, the strongest parent selects a fixed answer-free process card;
the active sham receives a tokenizer-matched card selected for another
same-family/pre-score child. Only the child's own plan reaches a fresh
homologous task. This asks whether adaptive process diagnosis can improve a
decision before SLEEP. If it cannot, the static q14 lesson was not merely
being lost by the writer.

Exception: if `PROBE_SATURATED` is the only reason for no separation, keep the
same material and replace only the four-task assay with a prebound harder
12-task parent-free record panel; do not regenerate or refit.

### If harmful: `W-SAFETY`

If harm first appears only with adapter ON, hold one frozen child-record
corpus fixed and compare the current `rank8, 3 epochs, 1e-4` write with one
predeclared cooler write (`rank8, 1 epoch, 3e-5`) on the same 12-task neutral
panel, each ON/OFF. This is the smallest test of whether heat rather than the
lesson caused the damage. Do not expose or continue a harmed child.

If the lesson already harms formation before any write, skip `W-SAFETY` and
run the tokenizer-matched no-training lesson/sham replication instead; the
writer cannot repair a harmful teaching package.

## Lineage and claim boundary

Every root in this scout is disposable. No adapter, prompt, selected row,
probe output or evaluation-informed revision returns to a final parenting
line. The tasks remain disjoint from CompilerGym, but task-disjointness alone
does not create clean ancestry. A positive result selects the *next protocol*,
not the final child.

This preserves the simple architecture: THINK produced the child records;
this experiment directly writes them with a minimal SLEEP; DREAM/context
management is not tested. The laboratory decomposition is not extra cognitive
machinery—it only tells us which of those simple links needs work.

## Inspected identities

- integration commit: `6c798231`
- `parent_material_pipeline.py`:
  `c084f774e212b401ed662547e585f5f41fd8247b247d25a4f7a73dc714e08071`
- `parent_material_write.py`:
  `57025d725e0825deaa795ee334864fa36bb6c5ed3a3ba17cc51931dc2d9d197a`
- formation producer `parent_material_diagnostic.py`:
  `bbda9f086f3070cee5f708ad71772a99a7a65715dfb08ff32d97927d7f5b2d5d`
- parenting-gate audit:
  `research_notes/analysis/2026-09-12_parenting_next_gate_audit.md`
