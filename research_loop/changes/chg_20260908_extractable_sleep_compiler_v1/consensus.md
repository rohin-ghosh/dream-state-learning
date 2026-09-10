# Extractable SLEEP compiler v1 — adjudicated consensus

Date: 2026-09-08

Status: exact proposal for human ratification. It authorizes no
implementation, model/tokenizer execution, benchmark generation, adapter
training, GPU use, resource acquisition, or scientific claim.

## Plain-language ruling

The architecture remains simple:

```text
THINK   live thought/action/outcome stream
DREAM   rebuild the finite active context; no weight write
SLEEP   compile grounded lived experience, then write the child LoRA
```

Parenting is upstream data generation: it helps the child produce useful
thoughts, experiments, corrections, and actions. SLEEP is ordinary
post-training applied to an unusual, provenance-bound dataset. Its first gate
is not whether it fits its rows, but whether the written experience can be
extracted and used without textual retrieval or behavioral damage.

Development may begin from a separately identified **teachability
bootstrap**: ordinary, target-blind post-training that teaches how to convert
feedback into the child's own prediction, experiment, revision, and action.
The developmental sequence is therefore:

```text
general teachability bootstrap -> interactive parenting -> lived learning
```

The bootstrap is schooling, not personal experience and not the scientific
SLEEP claim. Parent utterances during childhood remain outside the SLEEP
target corpus.

## What sleep dosage means

Track five independent quantities:

1. unique grounded evidence;
2. supported learning transitions;
3. compiler views per transition;
4. loss-bearing target-token exposures and optimizer updates;
5. cadence: when a committed write becomes available to generate later
   on-policy experience.

“More frequent sleep” is not assumed to store better. With cumulative
clean-base training, identical terminal corpus, order, initialization,
trainer, and RNG produce the same terminal adapter regardless of discarded
intermediate writes. Frequency matters at the system level because an earlier
adapter can alter later thought/action/outcome data, and because current
sleep packages also alter briefs, compiler history, and gate decisions.

## Canonical evidence and support levels

One immutable `evidence_id` identifies one valid public dispatched
action/outcome, success or failure. It binds exact life occurrence, episode,
turn, rendered public state/prompt, child response, normalized action,
dispatch/reset receipt, public outcome, and model/tokenizer/template hashes.

One `lesson_id` binds an ordered evidence bundle and one of three support
levels:

- **episodic:** a directly observed action/outcome; scope cannot exceed that
  situation;
- **corrective:** an adverse/surprising outcome followed by a child-authored
  revised diagnosis/prediction/action whose public result validates the
  correction;
- **generalized:** a scoped relation supported by at least two independent
  episodes or one support plus prospective confirmation.

Later verified use can raise salience, replay dose, and permitted scope. It is
not required before the first episodic write, avoiding a circular gate.

All valid failures remain evidence. Favorability is a label, never an
admission rule.

## Training views and targets

A derived view records `view_id`, `lesson_id`, ordered `evidence_ids`, cue
family, renderer/version/seed, exact prompt/response hashes, loss mask, dose
ordinal, and truth/scope validation.

The initial writer supervises a minimal persisted child-native continuation:
supported `PREDICT:/NOTE:/RECALL:` clauses when present, exactly one dispatched
`ACT:` or typed tool action, then EOS. Prompt/context tokens, parent speech,
public outcome/score, provenance text, and unsupported explanations are
loss-masked. A failed action is not a desired-action target; its grounded
post-outcome correction and later validated action may be.

The first compiler experiment varies **cue/input views while keeping the
grounded child target fixed**:

- `EXACT_EVIDENCE`: the exact earlier public experience;
- `ALT_EVIDENCE`: the same facts under reordered fields and changed connective
  wording;
- `STATE_ONLY`: the deployment surface without ledger, brief, parent, or
  source trace;
- optional `CONTRAST`: a grounded failure/recovery pair whose source IDs are
  both bound.

`STATE_ONLY` is called deployment-surface training, not proof of recollection.
Multiple alternative target thought paths are a later, separate factor because
they change both representation and factuality.

No free model-written principle or unsupported connection is a supervised
target in this minimum writer. A fixed treatment-independent native-interface
anchor pack may be mixed into every arm.

## Teachability bootstrap and repetition

The bootstrap corpus is task-blind and domain-diverse. A first bounded design
uses 192–240 grounded child continuations spanning six reusable computations
across four unrelated microdomains:

- predict from named features;
- distinguish and test competing hypotheses;
- stop unproductive recursion and act;
- revise a belief after surprise;
- scope a conclusion;
- retrieve and reuse a relevant correction.

Parent advice may condition a demonstration but is response-loss-masked. Only
the child's committed thought and executed action are targets. Exclude all
CompilerGym/final-gym vocabulary, actions, tasks, scores, and solutions. Use a
surface- and token-matched neutral bootstrap control.

Repetition means repeating the **computation** across varied relevant
situations, not copying one phrase. During parenting, the same core lesson may
be restated and practiced until the behavior appears; reminders then fade and
return only on relapse. Parent words never enter the life SLEEP corpus.
Child-authored thoughts may enter normally only when they are part of a
grounded thought/action/outcome episode.

To keep the boundary clean and make the bootstrap survive cumulative
clean-base personal writes, materialize it as an exact schooled birth
checkpoint (for example by merging and freezing the bootstrap LoRA once).
Every later personal LoRA trains from its lineage's frozen birth checkpoint.
Do not silently mix childhood parent messages into each sleep or average
bootstrap and personal adapters.

Test a matched 2x2:

| | no parent | parent |
|---|---|---|
| neutral bootstrap | control | parenting alone |
| teachability bootstrap | bootstrap alone | bootstrap + parenting |

Separate entry level from acceleration. The acceleration estimand is
`(bootstrap+parent - bootstrap-only) - (parent-only - control)`, plus
entry-adjusted time/AUC to a fixed parent-absent threshold. Start with two
independent curriculum roots and treat this as a spend-licensing canary.

Phrase overlap is not uptake. The repeated computation must appear without a
prompt, in different words, only when relevant, change the next action, improve
a public outcome, and persist after context reset. Wrong/shuffled advice must
remove or redirect the effect. Harm worse than -0.05, action-format failure,
or work-turn collapse below half the previous child stops the condition.

## First GPU-eligible experiment after separate implementation authority

Run a dose-matched compiler 2x2 on one immutable development evidence set:

| Factor | Level 0 | Level 1 |
|---|---|---|
| cue diversity | repeat exact cue | exact + alternative ordered/worded cues |
| deployment-surface mix | no state-only targets | fixed fraction state-only |

Every cell uses the same lesson IDs, grounded target continuations, total
loss-bearing target-token exposure, optimizer-step count, token-balanced
batch plan, LR schedule, initialization/data-order seeds, clipping, rank, and
interface-anchor dose. Compiler views never change independent evidence count.

Use one evidence root and two training seeds as a safety/information screen.
Replicate surviving contrasts on a second independent evidence root. This is
at most sixteen moderate fits if all four cells survive; stop bad or
uninformative cells early under the frozen rule. Do not use 12k rows or long
lives before this gate.

Required readouts after clean context/KV reset and adapter reload:

1. **storage:** exact-source-prompt target NLL/log probability;
2. **extraction:** held-out cue wording/order/partial/contradiction recovery,
   with ledger, RECALL tool, brief, source trace, and parent absent;
3. **behavioral use:** free native thought/action on fresh homologous tasks
   with new identifiers and action combinations;
4. **preservation:** previous-child paired marker/action validity,
   chunks/episode, DONE-first, generic anchor behavior, and no-material-harm.

Controls: adapter-off/previous child, equal-dose exact repetition,
state-target derangement, action/outcome shuffle, and wrong-life adapter. Use
training root/seed blocks—not rows, tasks, or probes—as the inferential unit.

## Training-dose contract

The trainer must record supervised response tokens separately from attended
prompt tokens. Bind exact ordered training multiset, token-balanced batch
boundaries, optimizer updates, gradient accumulation, LR schedule,
initialization seed, data-order seed, clipping, rank/alpha, truncation, and
nonfinite-batch disposition. If exact target-token equality is impossible,
predeclare and report the residual tolerance before results.

## Plasticity and rank

Rank controls capacity, not update strength. With `alpha/r` fixed, increasing
rank adds learnable directions but does not directly make a write stronger.
Plasticity is controlled by LR, supervised target-token exposure, update
count, replay mixture, and LoRA scale.

Only after selecting a compiler surface, calibrate rank `{8,16}` crossed with
low/high target-token exposure on a representative corpus. Measure extraction,
use, adapter delta norm, anchor-prompt distribution drift, and interface harm.
Choose the smallest rank that passes; no age-based rank schedule is claimed
without this interaction measurement.

## Cadence experiment, deferred until writer gate passes

Prospectively compare matched lives:

- `K4`: periodic committed sleeps during 128 episodes;
- `K1`: no sleep weights or brief until one terminal sleep at episode 128.

Match task order, occurrence-aware generation seeds, trainer-seed schedule,
writer/rank/gates, probe seeds, and episode budget. Train standardized terminal
adapters from both ledgers under one writer.

- natural K4-K1 estimates total sleep-package cadence;
- standardized K4-ledger minus K1-ledger estimates mediation through changed
  future evidence;
- natural K4 minus standardized K4-ledger estimates historical
  rendering/availability conditional on the periodic ledger;
- checkpoint AUC measures the value/harm of earlier availability.

Disable waking briefs for a weight-cadence claim, or add a brief-only arm.
Otherwise use the package label. Rejected sleep corpora/briefs cannot become
canonical descendants.

## Retention

Reserve an early lesson cohort that is written once and excluded from later
replay. Later retrieval/use of continuously replayed rows is maintenance under
rehearsal, not forgetting resistance.

## Evidence status and code-path correction

- R2/RP long lives actually use `compile_sleep` -> `train_adapter`
  (`v1_frozen`, bare text, `lr=1e-4`, three epochs), not the intended native
  response-masked v2.1 path.
- The existing write swarm varied row count and optimizer exposure across
  arms, so it does not isolate diversity or replay.
- Existing positive/negative behavior, dialect drift, late harm, and gate
  catches remain valuable old-writer engineering evidence.
- No existing result certifies this writer, a frequency effect, extractable
  parametric memory, or a rank schedule.

## Acceptance and falsifiers

Reject a candidate and keep the previous child if native dispatch,
required-action validity, chunks/episode, generic ability, or task performance
crosses the frozen adverse margin.

- source-row fit without held-out cue recovery = stored/reproduced, not
  extractable;
- cue recovery without fresh-task action value = extractable description, not
  useful experience;
- gain requiring ledger/brief/RECALL/source text = contextual retrieval, not
  parametric extraction;
- gain surviving binding derangement, source shuffle, or wrong-life adapter =
  style/frequency/prior effect;
- diverse cues failing to beat equal-dose repetition at matched source fit =
  no evidence for diversity in this regime;
- state-only gain disappearing on novel identifiers/combinations = direct task
  memorization, not transferable experiential use;
- frequent sleep failing to exceed the practical margin in prospective K4-K1
  = no evidence that higher cadence helps the system;
- maintenance disappearing when sentinel replay stops = rehearsal-dependent,
  not retained memory.

## Human boundary

Separate exact human ratification is required before any code change or
execution. A later implementation packet must bind compiler/trainer/runner,
schemas, source files, model/tokenizer revisions, corpus and evidence
manifests, seeds, budgets, rank/alpha, loss mask, gates, and requested scope.
