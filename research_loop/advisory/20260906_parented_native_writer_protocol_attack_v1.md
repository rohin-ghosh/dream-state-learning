# Parented native writer and learned-context protocol attack v1

Date: 2026-09-06

Status: **independent design advisory only**. This document authorizes no
architecture change, implementation, source or target enumeration, model call,
adapter fit, GPU use, external access, or scientific claim. Adoption requires
the complete `AGENTS.md` architecture workflow, exact-byte human ratification,
implementation tests, fresh review, and a separate pre-GPU gate.

## Verdict

**REWORK the current `organism_v6` writer before using it for the one-parent /
one-child headline. Adopt a typed, response-only, transactional writer with a
learned-but-reversible DREAM state. Do not train raw thought logs, parent prose,
tool results, or unverified model-written principles.**

The smallest coherent system has one model, one active life-LoRA, and three
operations distinguished by what they change:

| operation | what the same model does | persistent effect |
|---|---|---|
| `THINK` | freely deliberates, predicts, invokes tools, observes public results, and revises its plan | changes the live trace and ledger only |
| `DREAM` | runs the same inference process over the current trace plus ledger references and proposes a smaller successor conscious state | replaces active context only; the old trace remains recoverable |
| `SLEEP` | selects already supported child continuations, renders exact training rows, fits one LoRA, and transactionally accepts or rejects the candidate checkpoint | changes the one active life-LoRA only |

There is no learned thinker, dreamer, curator, verifier, or sleeper. `DREAM`
is a learned use of the same model under a context-reconciliation contract.
`SLEEP` may ask that model to inspect evidence, but model prose cannot admit
itself into training. Deterministic provenance, public outcomes, and frozen
behavioral gates control admission and commit.

## Why the current prototype is not this system

The audited code is useful failure evidence, not a basis for a confirmatory
writer:

1. `sleep_compile.compile_native()` admits any thought with `win` or the loose
   substring flag `had_note`; the live audit found 55/56 alleged NOTE rows had
   no canonical line-start NOTE marker.
2. It trains complete free-form chunks, including Markdown action imitations,
   rather than distinct thought, native tool-call, and successor-state targets.
3. `nursery_dialogue.py` computes `admitted = post >= pre` across different
   puzzles but never uses that variable to exclude rows. Every locally winning
   apply chunk remains eligible whether or not the parental correction helped.
4. Parent corrections and restatements are appended as ordinary notes, so
   `compile_native()` can turn them into recall targets. This violates the law
   that parent prose proposes credit assignment but is never learned as truth.
5. There is no scaffold-fading corpus. A live restatement prefix is not the
   same as training one verified child continuation with the parent gradually
   absent.
6. `train_adapter_v21.py` wraps every item as one generic user/assistant pair.
   It does not preserve the exact multi-message invocation, offered tool schema,
   native response envelope, generation boundary, or tool-control tokens.
7. The trainer silently skips non-finite batches, records attended rather than
   supervised tokens, has no per-row mask receipt, and allows ad hoc rank,
   learning-rate, and epoch choices. The nursery used rank 8, `5e-5`, five
   epochs without a treatment-neutral selection rule.
8. The current state manager truncates by characters and FIFO notes. There is
   no learned context-reconciliation action, reversible successor-state
   receipt, or proof that a compressed state supports the next action.
9. A format “canary” is reported after probing but cannot prevent a broken
   adapter from becoming the next life state. B2 demonstrates why commit must
   be transactional: useful actions survived in prose while the executable
   channel collapsed.

The repair is not a smarter parser. The strict typed interface remains world
truth; the writer must preserve it.

## Minimal live and context interface

### One continuous THINK stream

`THINK` is ordinary model inference. Its input is the current conscious state,
recent child outputs, recalled ledger entries, current task, clock/token
budget, and public tool results. It may emit visible deliberation and one of
the offered typed calls. Tool calls are a separate serialization channel, not
a separate cognitive module.

Every generated turn is persisted before parsing with:

- exact message JSON and rendered bytes;
- tokenizer, chat/tool-template, model and loaded-source revisions;
- intended and engine-consumed input IDs;
- raw assistant text and raw native tool-call envelope separately;
- generation seed/parameters and token count;
- parsed call, normalized arguments, dispatch result, reset-state identity,
  public outcome, and score; and
- immutable episode, turn, parent-child, and ledger offsets.

All raw turns remain evidence. Very few become training targets.

### DREAM is a reversible context action

The model may request `RECONCILE_CONTEXT` early. The harness also requires it
at a frozen token-pressure threshold so arms cannot obtain different usable
context merely by declining to dream. This trigger is scheduling, not a second
mind. A hard emergency fallback exists only to prevent overflow and is logged
as a failure; it never becomes a positive training target.

The same model receives the closed pre-dream context and permitted ledger
slice, thinks normally, and returns exactly one typed `SUCCESSOR_STATE` object:

```text
working_focus
beliefs[] = {claim, scope, status, evidence_ledger_ids[]}
open_surprise_ledger_ids[]
next_plan[]
recall_handles[]
```

The harness—not the model—carries immutable goal, metric, clock, token budget,
best public score/action, and tool state across the reset. A dream cannot edit
those fields. It can only propose the narrative state above.

Before old KV/context is dropped, the candidate must pass all of:

1. exact schema and size limits;
2. every cited ledger ID exists in the closed pre-dream prefix;
3. every still-open registered surprise is either retained or explicitly
   marked resolved with an evidence reference;
4. no purported public observation differs from the cited record;
5. the current focus and next plan are legal under the unchanged objective;
6. one frozen restoration query whose answer was deliberately omitted from
   the successor state can be recovered through a cited `recall_handle`; and
7. after replacement, the child can continue to one legal, pre-outcome action
   without using the dropped transcript.

Failure leaves the ledger and old context intact and records a failed dream.
Only a successor that passes all seven and is followed by the registered
world-supported continuation is eligible for later SLEEP training. Thus the
child learns how to reconcile context, while deletion remains reversible.

The initial canary does **not** train free model-generated cross-episode
theories. A later theory can become eligible only after it makes a frozen,
prospective prediction that is verified on new public experience. Eloquence,
parent agreement, evidence citation alone, or two similar anecdotes do not
admit a principle.

## Exact child-generated targets

SLEEP v0 has only two treatment-derived target families. Both targets are
bytes the child actually generated; neither is a parent or compiler rewrite.

| target | exact supervised suffix | admission requirement |
|---|---|---|
| `THINK_TO_ACT` | the child's visible pre-outcome assistant continuation, including its prediction/decision text and the complete native typed tool-call envelope through terminal EOS | call schema-valid and dispatched; action content is child-originated; parent supplied no action; public process criterion passes; the resulting task value meets the frozen support rule |
| `DREAM_STATE` | the child's exact native `SUCCESSOR_STATE` response through EOS | all seven reconciliation gates pass; post-reset continuation is legal; required recall succeeds; no required state/surprise is lost |

For `THINK_TO_ACT`, the target ends before the environment result. Outcome
information cannot leak backward into the child's prediction or action. A
later post-outcome reflection is not trained in the minimal writer unless it
becomes an admitted `DREAM_STATE` target. Plain NOTE text, generic
lesson recitation, unsupported self-criticism, rejected corrections, failed
actions, and raw transcripts remain ledger evidence only.

Do not fuse channels that the live backend emitted separately. If visible
deliberation and the native call are distinct assistant events, preserve them
as an ordered multi-event target with separate response spans. If the backend
cannot loss-mask its real native tool envelope, it is not eligible for this
writer; converting the call to an `ACT:` prose imitation would recreate the
B2 failure surface.

Each target is atomically bound to its source prompt, child, typed action or
state object, public outcome, admission test, and corpus row. Missing prompts
are fatal; nothing is reconstructed after generation.

The target must also pass a parent-copy audit: no verbatim span of eight or
more tokenizer tokens may be copied from the parent correction or restatement,
apart from a frozen list of generic process terms. The intended target is the
child's applied reasoning/action, not a delayed transcription of parent prose.

### What is masked

Every row uses the exact native chat/tool template used by the live child.
Loss is applied only to the complete child assistant suffix named above plus
EOS. These are always masked inputs:

- system/bootstrap/task messages and offered tool schema;
- current state, recalled ledger evidence, old transcript, and dream source;
- parent correction and all parent speech;
- child restatement of the parent's lesson;
- neutral self-review cue;
- public tool result, score, hidden evaluator state, and subsequent outcome;
- rehearsal history and provenance metadata; and
- padding, packing boundaries, and every earlier assistant turn.

The exact response-ID vector for one target must be identical across its
scaffold variants and matched causal cells. Prompt and response IDs are
concatenated at a frozen generation boundary; they are not retokenized as one
string. Any zero-label row, missing EOS, truncation of the target, non-finite
loss, role/template mismatch, or cross-cell target-ID mismatch aborts the
whole candidate fit. No skipped batches and no partial adapters.

## Scaffold fading

For every admitted target `y`, build one four-rung ladder. The target bytes are
identical at every rung:

1. `F3_PARENT`: ordinary pre-response state + exact parent correction + child
   restatement;
2. `F2_CHILD`: ordinary state + child restatement, parent absent;
3. `F1_CUE`: ordinary state + one frozen target-blind self-review or
   reconcile cue;
4. `F0_NONE`: ordinary state alone.

The parent, restatement, and cue are masked conditions, never labels. If `y`
is not a legal continuation from `F0_NONE`—for example because removing the
scaffold also removes task information—the entire target is rejected rather
than teacher-forced behind an ambiguous prompt.

The ladder is one training observation at four scaffold levels, not four
independent experiences. Every matched control receives the same response
target multiset, target-token count, update ordinal, and common anchor packet.
Report all four rungs separately at absorption time. Parent-visible success is
instruction following; only `F0_NONE` behavior can support parent-absent
transfer.

## Canonical dialect and retention anchors

Every SLEEP packet includes one treatment-independent anchor packet frozen
before parenting. It contains exact, model-native, target-blind child
responses in the same live template:

1. schema-valid typed tool calls whose task/action identities are disjoint
   from nursery and deployment targets;
2. ordinary free deliberation that does not call a tool;
3. valid `SUCCESSOR_STATE` responses with real in-packet ledger references;
4. one correct recall after successor-state replacement; and
5. one clean stop/no-action response when acting is inappropriate.

Anchors are response-only and carry no compiler winning sequence, held-out
program identity, parent lesson, or target score. They preserve the motor and
context dialect; they are not evidence that parenting worked. The same anchor
bytes, supervised tokens, row order, and replay count occur in every trained
cell, including unparented continual controls.

A post-fit candidate is quarantined unless a sealed anchor/sentinel panel
shows strict typed dispatch, exact call cardinality, DREAM schema validity,
recall routing, and generic answer quality within the frozen non-erasure
margins. The parser is never loosened to rescue a candidate. A rejected write
leaves the previous adapter active and its rejection is a reported life event.
Scientific held-out tasks are never used as commit canaries.

## Admission: the world admits; the parent proposes

Admission has three fail-closed layers.

### A. Provenance eligibility

The source prompt, child output, action/state bytes, environment reset,
outcome, and parent visibility must form one complete immutable chain. Parent
text must pass a lexical and semantic no-answer audit. Parent, child, compiler,
and trainer cannot see target identities or held-out scores.

### B. Process and outcome support

For parenting, the parent names one process failure and proposes one
correction. The child restates it, then acts on a separate homologous practice
task. Admission is not `post_score >= pre_score` across arbitrary tasks.
Before source generation, bind one objective process predicate and one task
support predicate. For the first reasoning canary these should be:

- after a contradicted prediction, the child preserves at least two surviving
  hypotheses, selects a legal action that makes them predict different public
  outcomes, and states its prediction before dispatch; and
- the action's public result removes at least one hypothesis, followed by a
  task score at or above the frozen floor.

The evaluator can compute those predicates from the public candidate rules
and action; the parent never sees the hidden rule or reference action. If the
correction is plausible but the predicates fail, it remains rejected advice
in the ledger and contributes zero positive labels.

### C. Transactional checkpoint commit

The corpus and masks pass static audits, the fit completes without skipped or
non-finite updates, the candidate adapter hash is sealed, and the independent
action/context sentinels pass. Otherwise SLEEP writes nothing. “No write” is
an outcome, not a replacement invitation or hidden hyperparameter search.

## One LoRA and one cumulative writer

At any instant the child mounts exactly one full-layer life-LoRA. Do not stack
a policy adapter, dream adapter, or sleep adapter.

The minimal SLEEP compiler makes **zero language-model calls**. It closes a
ledger prefix, applies the deterministic admission predicates, constructs the
two target families and scaffold rows from already persisted child bytes,
adds the frozen anchors, tokenizes, audits, and fits. A later “heavy dream” may
propose cross-episode theory rows, but that is a successor experiment and each
proposal would still need prospective public support before admission.

For auditability, each accepted SLEEP checkpoint is a clean cumulative rebuild:

- parenting cycle `j`: frozen base + the same rank-8 initialization + every
  accepted childhood ladder through `j` + the fixed anchor packet;
- deployment cut `t`: frozen base + the same initialization + the frozen
  childhood corpus for that child + every accepted deployment ladder through
  `t` + the same anchors.

Only the resulting single LoRA is mounted. Prior optimizer state and prior
adapter tensors are not stacked or used as a second learned state. The
append-only ledger is the provenance source that makes the cumulative rebuild
possible; ordinary active textual memory remains available equally in all
headline cells.

This clean rebuild is a proposed choice, not an empirical fact. It buys a
fixed corpus-to-adapter specification and removes accumulated optimizer/adapter
path drift from the lifetime estimand. Training stochasticity still exists and
must be controlled by the registered seed/determinism policy. A later
in-place-update arm may test a different continual-learning mechanism, but it
must not be mixed into the headline after results are seen.

## Treatment-neutral rank, heat, and dose calibration

Fix placement and capacity before parenting: rank 8, alpha 16, dropout 0,
no adapter stacking, and `q/k/v/o` plus gate/up/down MLP projections in every
transformer layer. Use bf16, unpacked rows, AdamW with one frozen optimizer
configuration, gradient-norm clipping at 1.0, and no loss on padding. Rank 16
is a later diagnostic only; it cannot rescue rank 8 after parenting data are
inspected.

Select optimization heat and dose on a target-, parent-, and treatment-free
native-writer packet. The packet contains only the canonical anchors plus
prospectively generated successful development continuations. It has no
parent correction, admitted lesson, nursery target, deployment program, or
repository result.

Race exactly this ordered grid:

```text
learning rate: {1e-6, 1e-5, 3e-5}
dose:          {1, 4} complete supervised-target-token exposures
```

All six fits share rank, initialization, bf16 precision, deterministic row
order, batch/accumulation, optimizer, schedule, gradient clipping, target
modules, dropout, and anchor/rehearsal bytes. Record supervised target tokens,
not merely attended tokens. “One exposure” means every loss-bearing target
token is presented exactly once; scaffold repetitions do not redefine the
unit.

Choose the passing cell with the smallest `learning_rate * exposure`; break a
tie by lower learning rate, then lower exposure. A cell passes only if it:

1. raises native-suffix log-probability by the frozen absorption margin;
2. preserves strict typed-call dispatch and call cardinality;
3. preserves typed-forced action quality within the frozen non-erasure margin;
4. preserves valid DREAM state plus ledger restoration;
5. stays within the generic/tool-use sentinel margin; and
6. reproduces under a second identical fit according to the prebound
   deterministic tensor/output rule.

Use one frozen 24-prompt neutral panel per candidate and duplicate: eight
native tool-routing prompts, eight DREAM/restoration prompts, and eight
generic/tool-use preservation prompts. These are engineering sentinels, not
scientific targets or independent replicates.

If no cell passes, the writer is NO-GO. Do not inspect parenting targets,
promote rank 16, increase dose, or choose the least bad cell. The chosen
rank/heat/dose is frozen for authentic, target-only, deranged, parented, and
unparented cells. Corpus size may change the total number of target tokens;
per-token exposure and optimizer law may not.

## Causal controls

The bounded canary needs these cells per child root:

| cell | purpose |
|---|---|
| `AUTH_PARENT_FADE` | authentic admitted child `THINK_TO_ACT` and `DREAM_STATE` ladders |
| `AUTH_TARGET_ONLY` | the same authentic child targets, but parent/restatement input slots contain frozen role- and token-length-matched target-blind neutral text |
| `STATE_TARGET_DERANGED` | identical scaffold/anchor/response-token marginals, but response targets are no-fixed-point swapped between two homologous source states within target type; tool calls must remain schema-legal under the other state |
| `UNPARENTED_SELF` | the matched no-parent child performs the same practice opportunities and SLEEP writes only its own world-admitted continuations at the same writer settings |
| `AUTH_ADAPTER_OFF` | exact authentic checkpoint served with the adapter absent; no fit |
| `BASE_OR_PRIOR_CHECKPOINT` | the exact pre-write child checkpoint |

The parent has two causally different roles that must not be conflated. It
first helps the child *produce* a better continuation; later its masked text
may condition consolidation. `AUTH_TARGET_ONLY` controls only the second role.
Because SLEEP is meant to store the child's corrected continuation rather than
the parent's wording, equality between `AUTH_PARENT_FADE` and
`AUTH_TARGET_ONLY` is compatible with success and is arguably desirable:
parent text has faded while its effect survives in the child's target.
Parenting specificity instead comes from the prospective comparison with
`UNPARENTED_SELF`, including the pre-SLEEP yield and quality of world-admitted
child continuations and their parent-absent post-write behavior.

`STATE_TARGET_DERANGED` asks whether correct state/continuation binding matters
rather than syntax and target-frequency alone. If a legal, no-fixed-point
within-type permutation does not exist, remove the binding claim and stop; do
not substitute a weak outcome-tail shuffle like the Fable control, which left
action strings intact.

Adapter-off localizes the effect to parametric state. A separate wrong-child
corpus is informative later but is not a guaranteed null: a genuinely general
thinking lesson should sometimes transfer between children. It should be
reported as transfer, not mislabeled as failed specificity.

For the paper's deployment experiment, all four parenting x continual-learning
cells retain identical files, tools, active textual memory, context budget,
token budget, task/RNG opportunities, and public feedback. Only the parenting
corpus and deployment write switch differ. The canary controls above diagnose
the writer; they are not extra headline agents.

All four headline cells also use the same DREAM trigger and successor-state
interface. Frozen cells still reconcile context with their frozen checkpoint;
continual cells may improve that behavior only through the same admitted
SLEEP rows. This prevents unequal context capacity from masquerading as a
parametric-learning benefit.

## Bounded pre-headline canary

The canary teaches one compound but measurable habit: **after a surprising
outcome, preserve the competing hypotheses in a reversible successor state,
then choose a cheap action that discriminates between them.** This connects
thought, learned context management, and action without supplying a task
answer.

Use four isolated one-parent/one-child roots. Each root receives two
homologous source tasks with different correct discriminating actions, so a
within-type no-fixed-point derangement exists. The parent sees only public
child traces/outcomes and gives one process correction. The child restates,
attempts the second task, reconciles context under the frozen pressure trigger,
and acts. Exactly one accepted `THINK_TO_ACT` target and one accepted
`DREAM_STATE` target may enter per source task.

Root eligibility is fixed **before** the parent speaks and cannot require a
successful correction, an admitted target, or a favorable post-write probe.
A root is eligible only when its bound task pair is structurally valid, the
unmodified child displays the predeclared process failure on the first task,
and both task action spaces support the frozen derangement construction.
Preserve the first 12 attempted roots and stop at the first four pre-parent
eligible roots. After inclusion, every failed correction, zero-admission
cycle, invalid dream, and harmful write remains a negative root and cannot be
replaced. Report the complete attempted-to-eligible-to-admitted funnel. Fewer
than four pre-parent eligible roots is a canary NO-GO, not permission to alter
tasks or loosen admission.

Spending is staged:

1. neutral calibration: at most six grid fits plus one duplicate of the
   selected cell;
2. two-root technical stage: authentic, authentic-target-only, deranged, and
   unparented-self = eight fits;
3. only if both roots pass action/context safety, expand the same frozen
   protocol using authentic, deranged, and unparented-self to two more roots =
   six fits.

Maximum: 21 small fits, four authentic parented child realizations, no target
or deployment fit. This is a plumbing/teachability expenditure, not a powered
parenting result.

Bind the following hard generation envelope for this canary unless the later
exact ratification chooses a smaller one: at most 12 attempted roots; two
practice tasks per parented and unparented branch; six child turns per task;
one parent turn, one restatement turn, and at most one forced DREAM turn per
task. Use at most four parent-absent probe tasks per served checkpoint, six
ordinary child turns plus one DREAM turn per task. Across the 18 maximum
root/checkpoint services (four each authentic, deranged, unparented and
adapter-off, plus two target-only), the complete canary is bounded by 1,032
logical model calls including the six-cell neutral panels. Cap every call at
512 generated tokens, giving a conservative ceiling of 528,384 generated
tokens. Record actual calls/tokens and stop at the first failed stage. This is
a resource ceiling, not a recommendation to consume it.

At parent-absent probes, use fresh homologous tasks, clean contexts, the same
active external-memory affordance, and common-random generation where the
backend supports it. Measure:

- strict native tool dispatch and exact call cardinality;
- prediction-before-action;
- fraction of large surprises followed by a discriminating rather than
  repeated action;
- task value and information gain per generated token;
- `SUCCESSOR_STATE` schema, evidence and open-surprise fidelity;
- exact restoration of the deliberately omitted ledger fact;
- post-dream legal action and task continuation; and
- generic tool/reasoning sentinel behavior.

### Pass gates

The canary advances to the four-cell headline pilot only if all are true:

1. all static provenance/template/mask/target/EOS receipts pass and no fit
   skips a row or update;
2. the treatment-neutral writer cell passes all six calibration gates and its
   duplicate rule;
3. every authentic child passes strict action-channel and DREAM-state commit
   canaries; no parser relaxation or target-panel score is used;
4. authentic parenting increases the prospective yield or quality of
   world-admitted child continuations over matched unparented practice in at
   least three of four roots;
5. authentic-versus-pre-write/adapter-off changes the registered
   surprise-to-discrimination disposition in the intended direction in at
   least three of four roots, with no root crossing the frozen adverse margin;
6. authentic exceeds `UNPARENTED_SELF` in at least three roots on the
   parent-absent disposition endpoint; otherwise the no-parent child's own
   admitted experience is sufficient in this canary;
7. on the two technical roots, `AUTH_TARGET_ONLY` remains within the frozen
   equivalence band of `AUTH_PARENT_FADE`; a large dependence on masked parent
   text means scaffold fading has not succeeded;
8. authentic exceeds state-target derangement in at least three roots on the
   joint thought/action and post-dream continuation endpoint;
9. required goal/surprise/reference fields survive every accepted dream and
   the omitted-fact restoration succeeds on at least 90% of parent-absent
   dream probes; and
10. typed-forced action quality and the generic sentinel remain within their
   prospectively ratified non-erasure margins.

This `3/4` rule is a spending gate, not inferential evidence. Every root-level
value and eligibility failure is reported. Margins, probe counts, task family,
seed policy, parent bytes/policy, and exact legal action derangement must be
ratified before source generation.

### Fail meanings

| failure | conclusion and next action |
|---|---|
| neutral writer fails | native low-rank writing is not safe at the registered rank/heat/dose; stop before parenting |
| absorption changes, behavior does not | the LoRA stores a suffix but does not acquire a usable habit |
| parent does not increase admitted-target yield/quality | no evidence that parenting improved the child's practiced behavior before writing |
| authentic matches unparented-self after write | the child's own admitted experience is sufficient here; no durable parenting increment |
| authentic depends on masked parent text and target-only falls | scaffold fading failed; the learned behavior remains teacher-conditioned |
| authentic matches deranged | state/action binding was not needed, or the endpoint is syntax-driven |
| parent-present works, parent-absent fails | ordinary instruction following, not durable parenting |
| action improves but DREAM fails | a procedural writer exists; learned context reconciliation does not |
| DREAM validates but later action fails | context was syntactically compressed without preserving useful state |
| strict tool behavior falls while permissive prose remains good | prospective B2 recurrence; reject the adapter, never rescue the endpoint |
| one or two roots drive the effect | writer realization is unstable; redesign before the headline pilot |

## Claim ceiling and what this deliberately does not solve

A full canary pass permits only:

> In four formative, target-blind, isolated dyads, a treatment-neutrally
> calibrated response-only rank-8 writer compiled world-admitted child
> thought/action and reversible successor-context continuations into a
> parent-absent behavioral change while preserving the typed action channel;
> adapter removal, an unparented self-write, target-only fading, and
> state-target derangement localized the effect.

It does not establish a population parenting effect, CompilerGym improvement,
continual learning, a positive parenting-by-deployment interaction, theory
formation, general creativity, or an Experience Model flywheel. Those claims
still require the frozen four-cell deployment lifetime, active-text and final
batch/LEAFE-style controls, multiple isolated child lives, forward transfer,
retention, and the registered interaction.

The canary is successful if it tells us whether the child can be taught and
written without corrupting its motor or conscious-state interface. It must not
be expanded into another paper-sized prerequisite.
