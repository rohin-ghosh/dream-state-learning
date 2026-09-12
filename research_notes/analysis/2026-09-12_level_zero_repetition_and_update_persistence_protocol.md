# Level-zero repetition and update-conditioned persistence

**Date:** 2026-09-12
**Status:** prospective developmental protocol; no run or implementation is
authorized by this memo.
**Scope:** the smallest experiment that separates acquisition, rehearsal,
interference, dose, and plasticity for the established global
`PREDICT`-before-`ACT` habit. It is not H1.

## Evidence entering the experiment

Across optimizer seeds 0--2, the teaching adapter produced a correct
`PREDICT` before a correct `ACT` on `96/96` development prompts. The matched
task-only adapter produced it on `0/96`; both made the correct action on
`96/96`. This establishes carriage of one global response-order habit, not
input-conditional intelligence.

The 16 balanced device--colour bindings were not acquired: teaching scored
`14/48` and task-only `12/48` on held wording (chance `12/48`), with constant
or segment shortcuts. Seed 0 also scored `4/16` on the *exact training
prompts*. Each fact had one unique authored row replayed over four epochs, so
this localizes the failure to extractable acquisition at that exposure; it is
not merely a paraphrase failure.

The builder's already-running seed-0 short-row versus long-context repetition
sentinel asks a different question: it holds 16-copy token mass and 80 updates
fixed while changing whether copies share one context. That can identify a
context-packaging effect, but one root at one dose cannot identify a dose
curve or persistence. Preserve it as development evidence; do not pool it
with the roots below.

## The estimands

There is no parametric "fading with wall-clock time" when the weights do not
change. The experiment therefore asks four different questions:

1. **Acquisition:** at what repeated exposure does the habit, and separately
   a fact binding, become extractable immediately after writing?
2. **Passive control:** does an unchanged serialized adapter give the same
   answer after repeated unload/reload and evaluation?
3. **Interference:** what survives a specified number of genuine updates on
   unrelated material?
4. **Rehearsal:** at the same total update count, how does old-material replay
   change survival during later learning?

An item absent at the start of phase B cannot later be called "retained." If
it appears during `SAME` or `MIXED`, that is delayed acquisition.

## Phase A: immediate acquisition as a dose curve

Create three new, presealed **material roots**. A root fixes an independently
generated arithmetic set, balanced 16-item fact map, held prompts, and
optimizer seed. The root, not a prompt or checkpoint, is the experimental
unit. Pair every arm within a root.

One balanced pass has exactly 128 examples:

- 64 distinct arithmetic cases. `TEACH` targets a correct `PREDICT` followed
  by the same correct `ACT`; `TASK_ONLY` targets the correct `ACT` followed by
  the already token-matched `COMPUTED`. Inputs and correct actions are shared.
- 16 device--colour bindings, each in four fixed training phrasings. The four
  colours occur exactly four times. Facts and their targets are identical in
  `TEACH` and `TASK_ONLY`.

Repeat this identical 128-example support in independently pre-shuffled
passes. Four views are present from pass 1 onward, so later checkpoints add
repetition rather than cue diversity. Save after passes **1, 4, and 16**:

| checkpoint | updates, batch 4 | exposures / arithmetic case | exposures / fact |
|---|---:|---:|---:|
| `A1` | 32 | 1 | 4 |
| `A4` | 128 | 4 | 16 |
| `A16` | 512 | 16 | 64 |

Cross only learning rate: `3e-4` and `1e-4`. Hold rank 8, alpha 16, dropout
`.05`, target modules, optimizer, loss masking, batch size, chat template,
and example order fixed. Thus phase A is
`2 corpus arms x 2 learning rates x 3 roots = 12` trajectories, with dose
observed as nested checkpoints rather than 36 separate fits.

Read each checkpoint only after serialization and fresh-process reload.
Use 16 disjoint held arithmetic prompts, the 16 canonical fact prompts, one
fifth unseen fact phrasing per device, and eight native-interface cases.
Strict generation is primary. Also record a prevalidated correct-label
probability and a complete-response target-versus-control log-likelihood
margin; these are diagnostics for movement hidden by ceilinged generation.

`A1` and `A4` are development checkpoints. `A16` uses a separately sealed
prompt/form panel opened only after all 12 trajectories finish. Acquisition is
reported independently for the habit and facts. A useful operational gate is:

- habit: `TEACH >=15/16`, `TASK_ONLY <=1/16`, and correct `ACT >=15/16` in
  every root;
- fact binding in a state: at least `12/16` on both canonical and unseen
  wording, with no interface drop greater than `.05` from OFF.

The existing 96/96 result remains the prior development result; it is not
pooled with these new material roots.

## Phase B: persistence through later updates

Use the `TEACH, 3e-4, A4` checkpoint as the starting child. It is fixed here,
before phase-A outcomes, because it gives a moderate initial dose and matches
the known-acquirable habit. If it misses the habit gate in any root, phase B
does not launch. Facts enter the retention analysis only in roots where they
meet the phase-A fact gate at `A4`.

Clone each root's bytes into four histories:

| history | later material | what it identifies |
|---|---|---|
| `QUIET` | no optimizer step and no generated output re-enters training | passive reload/evaluator control |
| `SAME` | only fresh cases expressing the old habit plus the old fact map | reinforcement under rehearsal |
| `UNRELATED` | only a disjoint response habit and disjoint nonce fact bank | interference from actual new learning |
| `MIXED` | 50% `SAME`, 50% `UNRELATED` | replay-assisted survival while learning something else |

The unrelated bank uses disjoint identifiers, answer labels, tasks, and
markers; it shares only the frozen base and adapter. It must be learnable and
must not contain `PREDICT`, `ACT`, devices, colours, or old evaluation text.
Preflight all active histories to exactly 128 rows and the same supervised
target-token count per block. `MIXED` rotates deterministic halves so every
old and new item is revisited by block 4. No evaluation response is ever
compiled.

Cross the three active histories with continuation learning rates **`1e-4`
and `3e-5`**. These are the reduced-plasticity settings; rank remains 8.
`QUIET` has no learning rate. Save after continuation blocks **1, 4, and 16**,
again corresponding to **32, 128, and 512 later optimizer updates**. The full
phase is `3 roots x (1 QUIET + 3 histories x 2 rates)`: 18 trained
descendants plus three unchanged controls.

At `B1` and `B4`, use development forms. At `B16`, open a disjoint sealed
confirmation form panel only after every descendant is terminal. Each active
readout contains 16 old-habit prompts, 16 old canonical fact prompts, 16 old
unseen-form fact prompts, 16 new-habit prompts, 16 new held-fact prompts, and
eight interface cases (`88` calls). `QUIET` needs only the 56 old/interface
calls. Temperature is zero; every call has a fresh context and process state.

## Root-level analysis

Show all three roots and their mean/range; do not treat prompts, checkpoints,
or the two learning rates as independent `n`.

For each old endpoint `Y`, report change from the shared start `Y0`:

- passive stability: `QUIET(t) - Y0`;
- update interference: `UNRELATED(t) - QUIET(t)`;
- same-habit reinforcement: `SAME(t) - QUIET(t)`;
- rehearsal versus unrelated learning at equal total updates:
  `SAME(t) - UNRELATED(t)`;
- the practical mixed-replay policy: `MIXED(t) - UNRELATED(t)`.

The last contrast holds total optimizer steps and supervised target tokens
fixed, but replaces half the unrelated material with old material. It is the
deployment-relevant replay-policy effect, not a pure additive mediation of
rehearsal at equal unrelated exposure.

Report the two continuation learning rates separately, then the paired
root-level difference between them. A lower rate has demonstrated a useful
plasticity--stability tradeoff only if it preserves more old signal **and**
the unrelated material itself qualifies: new habit at least `13/16`, new
facts at least `12/16`, and interface validity at least `.95`. If the new
material is not learned, apparent retention is merely failure to update.

For the old habit, report exact adherence, correct action, and response-margin
change. For facts, report exact and unseen-form accuracy plus correct-colour
probability gain over OFF. A retention ratio is allowed only when the
phase-A gain denominator is at least `.10`; keep its absolute endpoint beside
it. Never call a paraphrase-only ratio "percent of memory retained."

The narrow technical greenlight requires, in every root: unchanged `QUIET`
weights and no more than one changed old item; qualified new learning in the
relevant active history; at least `.90` of starting habit adherence at `B16`;
and action/interface validity at least `.95`. If old facts qualified at `A4`,
they additionally require at least `12/16` held accuracy and at least `.75` of
their starting correct-colour probability gain. This is a writer-setting
greenlight only.

## Staging, stopping, and cost

1. Run one root's four phase-A trajectories first. Expand only if at least one
   rate meets the habit gate and no arm loses more than `.05` interface/action
   validity. If neither rate acquires the habit by `A16`, stop.
2. Expand phase A to roots 2--3. If no state reaches `8/16` canonical facts by
   `A16`, close fact acquisition as null at 64 presentations; do not improvise
   more epochs, rank, or phrasings. Habit phase B may still proceed.
3. Run one root's seven phase-B histories. Stop further updates on a history
   after a checkpoint with action/interface validity below `.95`, preserving
   that checkpoint as the adverse result. Expand only if at least one
   `UNRELATED` setting actually learns the new habit by `B16` and cleanup and
   hashes are sound.
4. Stop at `B16` regardless of outcome. Do not extend the sequence to force
   forgetting or rescue a null.

Maximum work is 30 trained trajectories, 15,360 optimizer updates, and 7,440
generation calls including one OFF panel per root. The observed level-zero
campaign used 7.94 aggregate A40-minutes for two 80-step fits plus 144 calls.
Scaling that receipt for longer in-process fits, reloads, and the larger
panels gives a planning estimate of **6--7 aggregate A40-hours**, with a hard
stop at **8 aggregate A40-hours**. Eight-way parallelism reduces wall time,
not the scientific sample size.

## What the result can and cannot justify

A full result can justify only statements of this form:

> A narrow authored response-order habit was acquired at a measured exposure,
> and its survival through a measured amount of unrelated LoRA training
> depended on continuation learning rate and old-material rehearsal.

Fact acquisition and persistence may be added only if their separate gates
pass. `QUIET` establishes technical stability, not human-like passive memory.

This experiment cannot establish conditional policy learning, intelligent
prediction, child-authored DREAM, grounded SLEEP, parenting, continual
improvement, H1/H2, or the full Think--Dream--Sleep organism. Its successful
outcome chooses a defensible write dose, continuation plasticity, and replay
cadence for the next **input-selective opposite-action** qualifier. Only after
that qualifier should the child-authored parent--DREAM--SLEEP bridge run.

Conversely, if qualified unrelated learning destroys the habit even at
`3e-5` **and** `MIXED` cannot preserve it through `B16` without more than
`.05` interface harm, the current writer recipe is a no-go for repeated
SLEEP. The honest fallback is one-shot habit carriage plus a measured
plasticity/interference failure, not a Dream--LoRA--Think claim.

## Controlling evidence and design sources

- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_SEED0_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/receipts_20260912/astra_fundamental_memory_diagnostic_handoff_20260912.md`
- `research_loop/COORDINATION.md`, SEQ-098--100 and the independent 18:24 / 18:28 recounts
- `research_loop/changes/chg_20260908_extractable_sleep_compiler_v1/interpretation_substrate.md`
- `research_notes/2026-09-11_full_claim_closure_ladder_v2.md`
