# Experience Model v6 / CompilerGym revision

Status: non-authoritative synthesis for architecture deliberation. The
verbatim owner directive controls. This revision supersedes the unratified
KernelBench candidate; it does not erase its useful critique artifacts.

## Scientific object

The experiment has two primary lifelong agents and one causal difference:

1. **Harness control**: the frozen base model, bootstrap, context-state loop,
   tools, public ledger/retrieval, clock, budgets, and CompilerGym feedback.
   It receives no parameter update.
2. **Experiential treatment**: the identical system plus periodic compilation
   of its own public thought--action--outcome history into one life-local LoRA
   mounted on the same model for later context selection, thought, and action.

No arm is scored by whether its private thoughts match an expected theory.
Primary evidence is objective held-out action quality over lifetime: valid
CompilerGym reward, checkpoint AUC/terminal performance, retention, transfer,
and statistically estimated slope. Thought/theory traces are post-hoc causal
diagnostics only.

## One model, one recurrent loop, two invocation states

`ORIENT` and `THINK_ACT` are phases of one recurrent state machine, not
separately trained agents or modules. Both call the same base model, tokenizer,
bootstrap policy family, and (in treatment) the same mounted LoRA.

- `ORIENT` asks what should occupy the next working context: current focus,
  relevant retrieved experience, unresolved surprise, and next operation.
- `THINK_ACT` reasons within that packet and emits a typed action such as
  inspect, apply an LLVM pass, evaluate, revise focus, reflect, or stop.
- The public environment outcome updates authoritative state and the loop
  repeats.

For v1 every call reconstructs its prompt from structured authoritative state.
Stable-prefix KV reuse is an optional later efficiency optimization and has no
scientific role.

## Context window as conscious state

Every invocation is deterministically assembled from bounded fields:

1. `ANCHOR`: immutable birth/bootstrap, objective, rules, action grammar.
2. `CLOCK`: elapsed/remaining wall time, tokens, model calls, environment
   steps, sleep cadence, and current public best score.
3. `LIFE`: life ID, current task ID, checkpoint, public cumulative progress,
   and declared persistent resources.
4. `FOCUS`: current subgoal, active question, proposed strategy, and reason for
   selecting it. This is rewritten by `ORIENT`.
5. `ENVIRONMENT`: current public LLVM/CompilerGym observation, legal actions,
   and the public outcomes returned so far on the current task.
6. `RECALLED_EXPERIENCE`: records selected through the same bounded retrieval
   interface and budget in both arms.
7. `RECENT_TAIL`: a bounded verbatim suffix of recent thought/action/outcome
   events.

The model may change `FOCUS`, request different recalled experience, or act;
it may not change `ANCHOR`, forge `CLOCK`, inspect hidden evaluation state, or
write unbounded undeclared lifetime files. Ordinary tools and external
artifacts remain available under the same explicit budget and persistence
rules in both arms, so the control is a strong contemporary agent rather than
a memoryless strawman.

## Sleep compiler under discussion

SLEEP is a write boundary, not a separately learned sleeper. It consumes only
sealed public life records. The first version should be a deterministic
compiler and fixed LoRA trainer; richer calls to the same THINK loop are a
later ablation only if the simple compiler fails or leaves clear headroom.

Canonical experience records contain: reconstructible pre-decision context
state; selected/recalled evidence IDs; emitted focus/thought/action; official
public outcome; resource cost; and any later recovery/revision linkage.

Candidate fixed training views:

- `ORIENT`: pre-decision state -> the focus packet that preceded a verified
  useful trajectory.
- `ACT`: focused state -> the action on a correctness-preserving improvement
  trajectory.
- `REVISE`: failed state + observed outcome -> a later corrective focus/action
  that recovered.

Arbitrary self-authored theories are never positive targets merely because
they were written. They can be input context or audit metadata; they become
loss-bearing only through a predeclared relation to later public improvement.
Selection must account for delayed pass interactions rather than retaining
only immediately positive steps.

At each sleep, rebuild the cumulative LoRA from the clean base using the
sealed cumulative selected corpus and a reset optimizer. This is slower than
incremental training but leaves one learned life object, makes every checkpoint
reproducible, and avoids optimizer moments as hidden adaptive state. Fixed
old/new quotas, corpus cap, deduplication, row multiplicity, loss masks,
training-token budget, rank, target modules, and preservation rows must be
ratified before a scientific run.

## Gym decision and fit risk

Use the official CompilerGym LLVM environment if an unchanged pinned release
passes a hard installation/semantics canary. The project was archived on
2026-05-27 and release 0.2.5 depends on LLVM 10, so compatibility cannot be
assumed. The first objective should favor deterministic, platform-independent
LLVM IR instruction count rather than experimental runtime timing. If the
official environment cannot run unchanged or cannot supply related but
nonduplicate train/evaluation programs, reject this gym and return to design;
do not repair the benchmark inside this change.

The life should traverse related but nonduplicate programs. Held-out panels
must include near-family transfer, opposite-condition cases, and compositions
of motifs encountered separately. Context and LoRA persist across acquisition
tasks within a life; independent lives share no adaptive state or progress.
Evaluation forks are sterile and never feed outcomes back into the life.

## Measurement

Primary endpoints are objective environment outcomes, not thought matching:

- correctness/validity and deterministic instruction-count reward;
- held-out checkpoint AUC and final checkpoint score;
- first-action quality and steps to best valid result;
- retention on early families;
- near-family, opposite-condition, and composite transfer;
- authentic LoRA minus same-checkpoint adapter-off;
- authentic outcome binding minus outcome-shuffled LoRA;
- treatment versus the full harness control under matched visible resources.

Estimate lifetime slopes over multiple independent lives with a predeclared
hierarchical or piecewise model and confidence intervals. Raw finite
differences, especially second differences, are too noisy to carry the claim.
Curvature may be exploratory. A saturation claim requires a near-zero control
slope with demonstrated headroom while the treatment slope remains positive.

## Immediate design questions

1. Exact CompilerGym release/commit, environment, datasets, legal observation
   and action projection, deterministic reward, and fit-canary rejection rule.
2. Exact context-state schema, ORIENT/THINK_ACT prompts, persistence/reset map,
   retrieval budget, recent-tail cap, and clock/budget fields.
3. Exact trajectory credit assignment, training rows, outcome thresholds,
   cumulative replay, rank/target modules, and fixed LoRA recipe.
4. Minimal scout task count/checkpoints/lives and indispensable causal controls.
5. Exact statistical estimand and practical signal threshold before scaling.

The first scout is mechanism work. It cannot by itself establish creativity,
consciousness, general intelligence, universal continual learning, baseline
degradation, or paper-ready population evidence.
