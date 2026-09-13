# Minimum Level-1 parenting-receptivity experiment

**Date:** 2026-09-13 UTC  
**Status:** prospective design and adversarial audit only; no implementation,
model/tokenizer call, fit, adapter mutation, GPU execution, or scientific claim  
**Fresh red-team disposition:** minimal **REWORK applied; prospective PASS**.
The repair makes the crossover order unambiguous, makes process use
task-bound and mechanically scoreable, freezes leak-free read cues, and
corrects the maximum call arithmetic.
**Scope ruling:** Rohin message 37: Level 1 is not self-learning. It should
show repetition, specific steering, conversion of parent/world input into a
child-authored learnable record, and survival of that record across one SLEEP.

## Ruling

Run one small, staged assay upstream of PCFL:

```text
fixed process lesson
  -> child restates it
  -> next homologous input is processed with that lesson
  -> real action/outcome enters an exact child-authored record
  -> one low-heat, replay-protected SLEEP
  -> source-withdrawn record read after parent/context removal
```

Use an **aligned-versus-swapped lesson crossover plus a no-parent anchor**, not
the current process-versus-neutral proposal. Both lesson siblings receive the exact same two
lesson strings, twice each, and solve the same tasks. Only lesson-to-task
alignment differs. This controls parent contact, semantic richness, token dose,
restatement, repetition, and generic “think harder” effects. The no-parent
anchor determines whether alignment helped rather than merely hurting less.

The minimum pass is not better autonomous task performance. It is:

1. the repeated aligned lesson changes the child's processing of the next
   input in the lesson-specific direction;
2. that use is visible in a source-faithful child record containing real world
   facts absent from the lesson; and
3. the record remains parametrically readable after one SLEEP and complete
   parent/context removal, without material loss of the inherited Level-1
   skill.

Fresh parent-free task application after SLEEP is a useful secondary endpoint,
not a Level-1 gate. Connected use, two-SLEEP recurrence, and useful action
improvement remain PCFL v2.2's job.

## 1. Clean child and contamination boundary

Use the three original, hash-bound **pre-memory Level-1 perception adapters**
(learner seeds 0/1/2) as three roots. They contain only the registered authored
Level-1 curriculum. They are exposed development roots, not untouched final
children, but their weights have received no nursery or deployment result.
Fork every aligned, swapped, no-parent, and no-update state from the
same root tensors with a fresh optimizer and process. Prohibit every descendant
from the actual-record writes, lower-LR repair, post-memory formation, RuleGame
DEV parenting, CompilerGym, PCFL DEV, or any deployment gym.

Before seeing output, bind fresh task IDs and two micro-task families disjoint
from all prior nursery, PCFL, confirmation, and deployment namespaces. These
roots and every resulting adapter are disposable development artifacts: none
may initialize the final child, enter a future parenting corpus, or update the
parent. Preserve all failures.

The parent is a fixed intervention, not a model call. It sees no hidden rule,
answer, future outcome, held item, score, or sibling output. This assay tests
receptivity to an answer-free process lesson, not adaptive-parent quality.

## 2. Two lessons and the lesson-swap control

Freeze these meanings before task construction; wording is then tokenized and
length-matched without changing meaning.

- **P — prior/outcome separation:** keep the prediction stated before acting
  separate from the observation returned afterward; preserve both and compare
  them rather than replacing the prior with the outcome.
- **C — chronological source selection:** when several public events are
  visible, select the most recent actually executed event and bind its action
  and outcome from the same receipt rather than an earlier distractor.

Task family P contains one executed event and deliberately varies agreement
between the explicit prior and real outcome; chronology is trivial. Task family
C contains two public executed events and makes prior/outcome comparison
uninformative; selecting the latest same-receipt event is decisive.

Freeze the **task-family** block order first. Seeds 0/2 use P-C-P-C and seed 1
uses C-P-C-P. `ALIGNED` receives the matching lesson before each block;
`SWAPPED` receives the other lesson. Thus, for a P-C-P-C task schedule, the
lesson schedules are P-C-P-C for `ALIGNED` and C-P-C-P for `SWAPPED`. The two
siblings solve the exact same task bytes in the same order and each receives
the exact same lesson multiset and repetition count. Within each family, make
the two four-item blocks structurally matched and reverse their first/second
delivery assignment for seed 1. Freeze this rotation before model output so a
nominal repetition effect cannot be only an easier second block.

After each contact the child emits one unrestricted restatement. Then the
parent turn is removed. The next task context contains only the ordinary task
state and the child's exact restatement as its current NOTE. This makes the
causal bridge visible:

```text
parent words -> child-owned NOTE -> processing of the next input
```

Reset active context between blocks: no earlier lesson, restatement, task, or
receipt survives except through the newly repeated lesson and its new child
restatement. There is no weight update before SLEEP. “Repetition” at this
stage therefore means that the same reminder can be reactivated and used
reliably on a second matched block; it is not yet cumulative parametric
learning.

The restatement is audit material, not a training target. Four fresh apply
tasks follow each contact, giving **16 fixed opportunities per arm/root**:
eight per lesson family and eight after the first versus second deliveries.
The `NO_PARENT` anchor receives the same 16 apply tasks in the same order with
ordinary task context only: no parent contact, restatement, or NOTE. It is an
absolute behavioral anchor, not a token-matched control; ALIGNED-versus-SWAPPED
remains the matched lesson-content contrast.

Make the task-bound operation mechanically observable rather than asking a
model judge whether the child sounded thoughtful. Every apply task starts with
lawful public environment receipts and then permits one fresh child action:

- a P item exposes one earlier receipt containing an explicit prior and its
  returned observation. The values vary independently across items. Before
  its new action, the child's NOTE must bind those exact two values and their
  equality/mismatch relation;
- a C item exposes two earlier receipts whose chronological order is
  independent of display order. Before its new action, the child's NOTE must
  bind the exact latest receipt ID and the action/outcome pair from that same
  receipt.

The ordinary task instruction asks for one relevant-state NOTE and an action;
it does not name P, C, comparison, or recency. Those operations come only from
the current child-owned restatement in the lesson arms. The new action then
produces another real, previously unknown world receipt for the child's
post-outcome record. No value needed by either family-specific checker occurs
in a lesson.

## 3. Exact observed endpoints before SLEEP

For every opportunity preserve the raw pre-action generation, strict typed
action, real environment receipt, raw post-outcome record, and all failures.
Score separately:

1. `RESTATE`: the child states the correct operation and scope in its own NOTE;
2. `PROCESS_USE`: a frozen deterministic parser, not a model judge, verifies
   the family-specific task bindings in the pre-action NOTE: P requires the
   exact public prior, observation, and relation; C requires the exact latest
   receipt ID and its same-receipt action/outcome pair. Generic descriptions,
   a bare claim that the lesson was followed, or values from the wrong receipt
   fail. The NOTE is emitted before the new action's outcome exists;
3. `EXECUTED`: its strict action dispatches once;
4. `RECORD_FAITHFUL`: its unchanged record keeps the task-specific public
   source binding from `PROCESS_USE` separate from, and correctly binds, the
   child's fresh pre-action prediction, action, returned outcome, and new
   receipt ID. It may not splice fields from two receipts; and
5. `FULL_MATERIAL`: `PROCESS_USE & EXECUTED & RECORD_FAITHFUL`.

The record's event values and receipt identity do not occur in either parent
lesson, so a pure lesson copy cannot pass. `PROCESS_USE` is a content score
under a finite parser whose accepted shapes are frozen before inference;
canonical NOTE form remains a separate score so dialect brittleness cannot be
mistaken for absence of the operation. Report exact phrase overlap and raw
output diversity, but do not discard a child merely for repeating the parent:
repetition is part of the treatment. Content, strict format, action validity,
field errors, length finishes, and not-called slots remain separate.

### Pre-write gate

Do not fit unless all are true:

- aligned restatements are correct after at least `3/4` contacts in at least
  two roots;
- `PROCESS_USE(ALIGNED) - PROCESS_USE(SWAPPED) >= 4/16` in at least two roots,
  with no root at `<= -4/16`;
- `PROCESS_USE(ALIGNED) - PROCESS_USE(NO_PARENT) >= 2/16` in at least two
  roots, with no root below NO_PARENT by more than `2/16`;
- aligned performance after the second lesson delivery is not lower than after
  the first in at least two roots; and
- at least two aligned roots produce `>= 8/16` FULL_MATERIAL rows.

This is a development feasibility gate, not a population hypothesis test.
Tasks are repeated measurements; learner roots (`n=3`) are the replication
units. If the gate fails, the result is “fixed repetition did not establish
specific receptivity,” and no stronger writer can rescue it.

## 4. One-SLEEP write

For each aligned root with at least eight FULL_MATERIAL rows, take the first
eight in frozen chronological order. No score ranking or regeneration is
allowed. Before fitting, require those first eight to have eight unique
addresses and at least four distinct semantic record targets; otherwise the
root is ineligible and later rows may not be substituted to manufacture
diversity. Each supplies two exact child targets from its real interaction:

- the pre-action process/action continuation; and
- the post-outcome source-faithful record continuation.

The inputs are their exact native contexts. Parent bytes are absent because the
parent was removed before application; the child's NOTE, task state, and world
result are masked inputs. Only the child's unchanged continuations plus native
EOS receive loss. Parent text, restatement text, expected fields, evaluator
labels, rejected records, and compiler prose never receive loss. There is no
synthetic corrected target and no scaffold-faded counterfactual context.

Protect the inherited skill by mixing all 96 original, bound perception
training rows with the 16 new child continuations. Use the evidence-backed
candidate only: warm-start the corresponding perception adapter, rank 8,
alpha 16, dropout `.05`, LR `3e-5`, fresh optimizer, batch 4, eight epochs,
and final checkpoint only. This is `112` rows, `28` batches/epoch, and exactly
**224 updates/root**. In every epoch, put each of the 16 NEW rows in a distinct
batch beside three OLD rows; no batch repeats a source or target. The remaining
48 OLD rows occupy 12 OLD-only batches. Freeze order independently of outputs.

This directly tests the missing repair suggested by the terminal evidence:
LOW preserved `140/143` inherited items while carrying `18/30` exact memories,
but still failed `2/3` strict screens; HIGH carried `20/30` while erasing
`45/143`. Low heat **plus full skill replay** is therefore a candidate, not a
known-safe writer.

Do not train the SWAPPED sibling: it is needed to identify immediate
lesson-specific steering, not to double writer cost. Reload the written child
and its unchanged root in fresh processes with no parent, NOTE, ledger,
retrieval state, or source transcript.

## 5. Post-SLEEP endpoints and decision

On each of the eight written records, query once by a source-withdrawn exact
address and once through a frozen paraphrase. The exact cue contains only the
opaque record address and the frozen read instruction; it contains no lesson,
NOTE, action, outcome, relation, receipt contents, or target prefix. The
paraphrase changes only the wrapper around the same address and also leaks no
target content. Freeze both renderers before formation. Score semantic record
fidelity, exact target bytes, strict form, per-field errors, wrong-key
assignments, and unique outputs. The unchanged root receives byte-identical
requests.

Re-run the original 48-item Level-1 perception panel and 12 generic canaries
on every written child. Historical root outputs may supply the bound C0 item
labels; only descendant calls are new. Gains cannot offset lost C0-correct
items.

Call a root `ONE_SLEEP_CARRIAGE` only if:

- exact semantic recall is `>= 4/8` and paraphrase recall is `>= 4/8`;
- the unchanged root is `<= 1/8` on each read surface;
- at least four addressed targets are recovered (not one repeated output);
- at most two C0-correct perception items are lost; and
- no generic canary item is lost.

The minimum Level-1 result is `PARENTING_RECEPTIVITY_ONE_SLEEP` only if the
pre-write steering gate passes and at least two of three roots meet
`ONE_SLEEP_CARRIAGE`. Otherwise report the exact partial link: repetition,
steering, material formation, carriage, or retention. Never average across a
failed noncompensatory link.

As a prespecified descriptive readout, give the written child and unchanged
root eight fresh parent-free homologous inputs and score `PROCESS_USE` from
one pre-action generation per input. No post-outcome record call is needed for
this optional diagnostic. A gain is evidence for a stronger persistent habit.
A null does **not** negate the minimum record-carriage result and must not be
hidden; Level 1 was not asked to establish autonomous self-learning.

## 6. Scale, stop rules, and information/GPU-hour

Maximum new work:

- three clean roots, three inference-only conditions/root;
- `312` formation/restatement/application child calls: per root,
  `ALIGNED=(16 pre-action + <=16 record + 4 restatement)`, the same for
  `SWAPPED`, and `NO_PARENT=(16 pre-action + <=16 record)`;
- at most three fits and `672` optimizer updates;
- `96` exact/paraphrase memory-read calls;
- `180` descendant retention calls;
- optional fresh-task readout: `48` calls;
- therefore at most `636` child calls including the optional readout;
- zero parent-model calls and no more than **5 aggregate A40-hours**.

Stage it: finish and reduce all inference-only formation arms before any fit.
Stop on source/hash/lineage mismatch, task leakage or ambiguity, parser/world
disagreement, parent bytes in supervised labels, target truncation, nonfinite
fit, bad ownership/release, pre-write-gate failure, or the resource cap. Never
replace a failed task/root, loosen thresholds, add dose, choose a favorable
seed, or send held results back to the child/parent/compiler.

## 7. Adversarial interpretation audit

- **“It only followed an instruction in context.”** Correct for the immediate
  endpoint; that endpoint is called steering, not learning. Source-withdrawn
  post-SLEEP reads test the separate persistence link.
- **“The wrong control is weaker prose.”** Both arms receive the identical P
  and C lesson bytes twice; only their alignment to the next task changes.
- **“Aligned only wins because swapped advice hurts.”** ALIGNED must also
  improve over the ordinary no-parent anchor; SWAPPED is the matched semantic
  control and NO_PARENT is the absolute anchor.
- **“The child copied the parent.”** Copying may explain the NOTE, but cannot
  supply the unseen world receipt or pass pre-outcome process execution.
- **“The compiler wrote the lesson.”** It does not: parent/restatement bytes
  are excluded from targets, and no corrected or counterfactual continuation
  is synthesized.
- **“More good rows mean more training.”** Formation yield is reported on all
  16 opportunities; every fitted root uses exactly eight selected rows,
  16 NEW continuations, the same 96 OLD rows, and 224 updates.
- **“Direct recall proves useful learning.”** It does not. It proves only
  bounded parametric carriage of child-authored lesson-use records. The fresh
  task readout is separate and PCFL owns connected/native utility.
- **“The child is clean because the filename says so.”** Cleanliness is the
  exact original pre-memory tensor hash plus a negative ancestry manifest;
  every experimental descendant is quarantined and disposable.
- **“Rows are independent.”** They are not. Report three root-level outcomes,
  not binomial confidence from records/tasks.

## 8. Relationship to PCFL v2.2

This assay fills PCFL's upstream missing edge:

```text
parent lesson -> child processing -> authentic child material
```

PCFL v2.2 tests the harder downstream edge:

```text
authentic EVENT/LINK material -> retained connected parametric memory
-> causal service/native use across two sleeps
```

Neither substitutes for the other. Parenting receptivity cannot validate the
PCFL writer, connected-memory claim, recurrence, lifetime improvement, or
memory-baseline superiority. PCFL cannot show that a person/parent can steer
the child into producing better learnable material. PCFL remains the
claim-bearing mechanism priority; this assay is a bounded, cheaper upstream
test and must not delay or rescue a failed PCFL v2.2 result.
