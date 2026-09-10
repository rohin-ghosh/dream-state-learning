# Extractable SLEEP + teachability bootstrap v2 rework resolution

Date: 2026-09-09

Status: successor-proposal input only. This document authorizes no code,
model/tokenizer execution, benchmark generation, adapter work, GPU use,
resource acquisition, scientific execution, or claim.

This is a first repair of the five proposal-byte blockers in `critique.json`
and `consensus.json`. It does not modify or reinterpret the rejected v1 bytes,
and it is not considered resolved until fresh review closes every item below.

## R1 — one exact schooled-birth mechanism

The birth mechanism is **merge once, freeze, and hash**:

1. Start both bootstrap treatments from the same exact BF16 child checkpoint
   `M0`.
2. Train either the teachability-bootstrap adapter `BT` or the direct-solution
   adapter `BD` using the exact writer contract below.
3. On CPU, load each BF16 base tensor, promote the base and LoRA product to
   FP32, compute `W' = FP32(W) + (alpha/r) * FP32(B) @ FP32(A)`, then round
   exactly once to BF16. Restore declared tied tensors, unload every adapter,
   and serialize with the pinned safe-tensor sharder. No autocast or PEFT
   convenience merge defines the reference result.
   The resulting immutable checkpoints are `M_birth_T` and `M_birth_D`.
4. Every personal SLEEP adapter is newly zero-initialized on its own immutable
   birth checkpoint in the functional sense: `A ~ Normal(0, 0.02)` from the
   bound initialization seed and `B = 0`, so the initial effective delta is
   exactly zero but gradients can flow. Its optimizer state is also new.
   Personal adapters never
   inherit bootstrap-adapter tensors or optimizer state, and the bootstrap
   adapter is never left mounted or averaged with personal adapters.
5. Every candidate receipt binds `birth_checkpoint_sha256`, previous committed
   personal-adapter hash, candidate hash, trainer/config hash, and optimizer
   initialization. Rollback restores the previous personal adapter on the same
   immutable birth checkpoint.

Both birth checkpoints have the same serialized architecture, tensor inventory,
dtype map, tied-weight map, and parameter count. Bootstrap parameters are
counted as schooling cost, not personal-memory capacity. Personal
rank/modules/alpha are identical across treatments.

The merge receipt records per-module pre-merge delta norm, realized BF16 delta
norm, nonzero fraction, and rounding-loss ratio. The birth fails if merged and
unmerged fixed-input logits exceed the preregistered tolerance, if rounding
loss is arm-asymmetric, or if material intended deltas disappear. The numeric
tolerance is fixed in the later exact implementation packet after a model-free
reference fixture and before either real birth is inspected.

Every checkpoint identity is a detached canonical directory manifest: sorted
relative regular-file path, size, and SHA-256 for every allowed file. Symlinks,
extra files, absolute paths, and escapes fail. The detached manifest itself is
excluded from its root to avoid a self-hash cycle. Tensor names/shapes/dtypes,
tokenizer/config/chat-template files, shard index, and generation config are
all included. Births live at content-addressed read-only roots.

Every trainer, runtime, probe, merge, adapter-off comparison, and rollback
command requires an explicit birth root and expected content hash. Symbolic
model-name or environment fallbacks are forbidden. Adapter metadata binds the
same birth root; T-on-D, D-on-T, personal-on-M0, missing-root, and mutated-root
requests fail before importing a model runtime.

### R1a — one writer contract, not an existing ambiguous default

The successor implementation introduces one writer entry point used by both
bootstrap arms and personal SLEEP. It is response-only chat-template SFT over
the seven all-layer projections (`q/k/v/o/gate/up/down`), with rank 8,
`alpha=16`, no bias, LoRA dropout 0, BF16 base/forward, FP32 optimizer state,
AdamW (`lr=3e-5`, betas `0.9/0.999`, epsilon `1e-8`, weight decay 0), no
warmup/scheduler, gradient-norm clipping at 1.0, microbatch 4, accumulation 1,
and maximum sequence length 2048. Prompt tokens and padding have label `-100`;
loss is normalized over response tokens only. Oversize or all-masked rows fail
rather than truncate silently. Each epoch uses an occurrence-aware seeded
permutation that is recorded with the encoded input IDs, labels, masks, batch
boundaries, and parameter-initialization hashes. Nonfinite loss aborts the
transaction; it is never skipped. The implementation packet must bind exact
base/tokenizer/chat-template roots, dependency versions, parameter traversal,
position/padding behavior, precision/autocast settings, save sharding, RNG
states, and code/config hashes. It records attended tokens and supervised
response tokens separately.

Rank 8 here is a bounded screening writer, not a claim that it is the mature
capacity. A later rank-by-exposure calibration may select a different frozen
personal writer for the long horizon only through a separately ratified
successor; it cannot change rank inside one developmental comparison.

### R1b — committed lineage, not directory discovery

Each write occurs in a content-addressed staging transaction. A receipt binds
`M0`, bootstrap corpus/evidence root, BT/BD adapter root, merge/toolchain root,
birth root, lineage/arm/root/transaction IDs, weight parent (birth), state
parent (previous committed personal adapter or null), data parent, evidence
index, support resolver, lessons, views, exact encoded batches, initializer,
RNG/optimizer assertion, candidate tensors, evaluation panel/results, decision,
and next active head.

Only one fsynced, compare-and-swap atomic `lineage_head` promotion makes a
candidate visible. Future compilation, briefs, context rendering, evaluation,
and selection traverse only that head's committed closure. Rejected/staged
corpora, views, briefs, adapters, optimizer states, and evaluations are
audit-only and cannot be found through directory scans. A model-free fault
matrix injects crashes after every persistent write/fsync/rename boundary and
must recover the exact previous committed closure.

## R2 — direct-solution active control and no-bootstrap reference

The treatment ontology contains exactly six reusable computations:

1. predict from named observable features before acting;
2. distinguish competing hypotheses and choose an informative test;
3. stop unproductive recursion and perform the selected action;
4. revise a named belief after a surprising public outcome;
5. scope a conclusion to the evidence that supports it;
6. retrieve and apply a relevant prior correction.

For each permanent `pair_id`, sample one canonical latent microtask transition
`(state, rational valid action, public outcome)` before rendering either arm.
Retain or reject the pair once under one arm-independent mechanical rule. The
teachability rendering supplies the evidence needed to derive that action and
targets the relevant feedback-to-learning computation. The direct-solution
rendering reveals that exact canonical action and targets reading the supplied
state and executing it. Both dispatch the identical normalized action into the
same engine state and therefore receive the identical public outcome. An
adverse transition is eligible only when the action is a preregistered rational
information-gathering action; no target is trained to contradict a known answer
or intentionally fail.

Thus the pair shares latent state, declared public fields, action, and outcome,
but differs in a named arm-specific conditioning block and target-computation
span. The estimand is feedback-computation schooling versus equally dosed
direct-solution task practice—not otherwise identical semantic experience.

Author paired responses to match supervised token count exactly and place the
action at the same token position and optimizer slot. Loss-bearing filler is
treatment content and may not be called inert; non-supervised padding remains
masked. Every pair records fully rendered attended input IDs, labels, masks,
response boundary, truncation decision, action span, batch/update slot, and
pairwise byte diff. Only the named conditioning and target-computation spans
may differ.

An independent randomized semantic audit receives every full attended
prompt-plus-target row and scores prompt-only, target-only, and joint presence
of each of the six normatively defined computations using frozen positive,
negative, ambiguous, and span-level examples. It is not called blinded because
treatment may be inferable. Two independently identified coders adjudicate
every disagreement before training. Before execution, require:

- every teachability row contains its declared computation;
- no direct-solution row contains any of the six computations;
- exact pairwise normalized action and public-outcome identity;
- exact supervised target tokens, action positions, optimizer slots, updates,
  and treatment-level dose; attended-length distributions satisfy the frozen
  tolerance;
- no orphan/duplicate pairs or treatment-dependent admission.

Call this `B_direct`, never "neutral." Carry the untouched `M0` as a diagnostic
no-bootstrap reference. Before development, require `M_birth_D` to be
noninferior to `M0` on the frozen native interface, generic-capability, and
advice-selectivity panels under the -0.05 adverse bound. The arm is a
nuisance-matched active control, not a claim that the two corpora have equal
conditional information, entropy, or cognitive difficulty. Those irreducible
differences are measured on an independent calibration pool with `M0` before
training: target NLL, valid-action rate, attempts, public outcome, and cue
informativeness by family/computation/difficulty. Freeze matching/rejection
rules before corpus construction. If the direct condition remains grossly
easier under those rules, add one predeclared workload-matched orthogonal-
computation control or fail the proposal; never tune a control from later
receptivity results.

## R3 — separate receptivity from ecological development

There are two estimands and they must never be combined.

### R3a. Standardized-advice receptivity at birth

This is the first bootstrap spend-license assay. Before any personal SLEEP,
make disposable clones of each frozen direct-solution and teachability birth.
From the same initial task state and sampling seed, one clone receives no
advice, one receives byte-identical correct process advice, one receives a
prespecified irrelevant advice item, and one receives a specifically wrong
process item. No clone writes, sleeps, updates a parent, changes the continuing
lineage, or reveals its result to later development. Advice wording, evaluation
families, task skins, and action tokens are absent from both bootstrap corpora.

The estimand is
`Delta_R = [Y_T(correct)-Y_T(none)] - [Y_D(correct)-Y_D(none)]`, where
`Y` is the mechanically scored successful strategy-dependent action within the
fixed action budget. Correct advice must improve selectively; irrelevant advice
must be approximately null and wrong advice must redirect or reduce the
specific strategy-dependent action under frozen directional predictions.

This estimates whether schooling made the child more able to turn the same
advice into better thought/action. It does not establish lifetime learning.

### R3b. Fixed-policy child learning acceleration

Run direct-solution/teachability birth x fixed-advice/solo development. The
task sequence, advice bytes, advice timing, repetition opportunities, context
budget, action budget, SLEEP opportunities, writer, and evaluation schedule are
identical across births. The fixed parent policy cannot inspect child text or
outcomes. Personal SLEEP remains active and is explicitly part of the learning
mechanism.

The primary screen is the entry-normalized parent-absent gain-curve interaction:
`Delta_F = [AUC(T,fixed)-AUC(T,solo)] - [AUC(D,fixed)-AUC(D,solo)]`.
This estimates whether the schooling treatment changes learning from the same
teaching curriculum; it does not isolate weights from the rest of SLEEP.

### R3c. Ecological adaptive parented-development package

Run the direct-solution/teachability birth x parent absent/present 2x2 with the frozen
personal SLEEP mechanism active in every cell. Record parent model/prompt,
information visible, messages, tokens, interventions, and latency. Report the
entry-normalized gain-curve interaction
`Delta_E = [AUC(T,parent)-AUC(T,solo)] - [AUC(D,parent)-AUC(D,solo)]`
and time/AUC to a fixed parent-absent exam threshold.
This estimates the complete parent + child + SLEEP developmental package.
Personal SLEEP is an intended mediator here, not "parenting alone."

Solo cells receive the same developmental tasks, turns, action opportunities,
context budget, wall-clock policy, and SLEEP opportunities; a frozen neutral
resource controller occupies only parent compute/time without emitting advice.

Every exam uses a disposable checkpoint clone with clean context, parent,
briefs, retrieval, ledger writes, and training disabled. Exam items come from
frozen parallel folds; no exam output can enter a parent, compiler, ledger, or
continuing child. Also evaluate every saved child on a fixed standardized-advice
panel. Adaptive-parent results without the standardized and fixed-policy panels
cannot support a child-receptivity or child-learning-acceleration claim.

## R3d — repetition is a behavioral process, not an echoed sentence

Every parented lesson receives an immutable `lesson_id`. Log reminder count and
spacing, varied relevant opportunities, matched irrelevant opportunities,
unprompted computation use, next dispatched action/outcome, reminder fade,
context-reset persistence, relapse, and restoration.

The behavioral endpoint is
`P(strategy-dependent action | relevant, no current cue) -
 P(strategy-shaped action | irrelevant, no current cue)`.
Paraphrastic restatement is a separate diagnostic and cannot rescue a null or
harmful action effect. A lesson is acquired only after a frozen number of novel
relevant successes, low irrelevant misapplication, and a context-reset pass;
only then does the reminder fade, returning on a frozen relapse rule. Until a
separate one-exposure-versus-spaced-repetition randomization is run, reminder
dose is descriptive and no causal claim that repetition itself helped is made.

## R4 — bootstrap source eligibility and structural target blindness

The bootstrap is generated only from four separately versioned public
microdomain families with disjoint surface nouns and action APIs:

1. Boolean rule discovery via `QUERY`;
2. calibrated interval estimation via `ESTIMATE`;
3. small resource allocation via `ALLOCATE`;
4. causal intervention toys via `INTERVENE`.

No compiler, program, kernel, pass, benchmark identifier, final reward key,
final action token, final prompt fragment, or final solution may enter the
bootstrap builder, teacher prompt, demonstrator context, corpus, or birth
checkpoint metadata. Shared ordinary language and the child's native
THINK/NOTE envelope are allowed and enumerated.

Every target binds generator family/version/seed, public state, pinned
demonstrator model/prompt/inference code/sampling seed and occurrence, all raw
attempts, parent-conditioning text if any, child continuation, normalized
dispatched action, public outcome, intended-computation tag, and mechanical
selection result. Selection requires a valid dispatched action and the declared
public outcome condition; it cannot select by future final-task performance.
The permanent pair and canonical transition are generated before arm rendering;
pair retention/drop is arm-independent.

Bootstrap advice is process-only: it may identify which of the six computations
to perform but may not state the hidden rule, correct answer, or exact next
action. It is selected from a frozen computation template before the child
continuation and cannot observe hidden state, future action, or outcome. A
task-specific action-equivalence scan rejects semantic prescriptions even when
the exact action string is absent. Parent conditioning is response-loss-masked,
but all attended prompt tokens remain part of the manipulation audit.

Freeze and hash generators, prompts, corpora, selection receipts, and both birth
checkpoints before sealed final instances, keys, or solution-bearing metadata
are generated or mounted. The bootstrap build runs in an allowlisted environment
with no final-task repository, manifest, generator, probe, or result store.
Bind the source-code dependency closure, generator schemas/rules/rewards/splits,
RNG namespaces, demonstrator visibility, and builder mount allowlist. The four
bootstrap families must also be disjoint from standardized-advice, fixed-policy,
and ecological evaluation generators—not merely from CompilerGym.

Predeclare a structural-overlap table covering observation topology, horizon,
feedback timing, hidden-state inference, action semantics/cardinality,
transition dynamics, reward shape, and solution algorithm. An independent
reviewer must reject any one-to-one policy isomorphism even when nouns differ.

An isolated leakage auditor—not the corpus builder—receives both frozen
manifests after construction. It checks source dependencies and declared
vocabulary/API/reward/identifier intersections and rebuilds the bootstrap after
mutating all final-task-only bytes. The bootstrap corpus and birth-build inputs
must remain byte-identical. No final-derived value—including hashes, filenames,
cache keys, timing, row diagnostics, or exit-dependent seeds—may reach the
builder or birth DAG. A separate release controller may receive a signed pass
that binds only the already-built bootstrap root, audit-policy version, and
auditor identity; original/mutated final roots remain audit-only.

The defensible claim is **no incremental final-task-derived information in the
bootstrap construction**, never that `M0` or its pretrained demonstrator lacks
prior knowledge of the final task family. Evaluate `M0`, `M_birth_D`, and
`M_birth_T` on sealed final tasks and interpret only the incremental schooling
contrast.

## R5 — cadence contrasts without mediation overclaim

After the static writer is certified, randomize matched lives to periodic K4
or delayed K1 SLEEP.

- Natural K4 minus natural K1 checkpoint AUC and terminal performance is the
  **total cadence-package effect**.
- Rewriting each arm's terminal canonical ledger once with the same terminal
  compiler/writer measures the behavioral consequence of their different
  treatment-induced ledgers under one writer. It is a **standardized-ledger
  contrast**, not an identified weight-mediated path.
- Comparing a natural terminal adapter with its standardized-ledger adapter is
  a descriptive writer/history/gate contrast conditional on that ledger. It
  is not proof that earlier weight availability alone caused the difference.

Earlier availability is represented by randomized cadence and checkpoint AUC.
Any downstream contribution of earlier weights already appears in later
on-policy evidence. No unique natural direct/indirect mediation claim is made.

## R6 — screening arithmetic and claim boundary

For all nursery assays the primary public score is binary task success within
the frozen action budget, averaged within a curriculum root and therefore in
`[0,1]`. Invalid or missing actions score zero; terminated lineages retain zero
thereafter for horizon summaries; non-crossers are assigned the full horizon
for threshold-time summaries. Entry-normalized trapezoidal AUC over the exact
frozen ages is primary for development; absolute threshold time is secondary.

The first spend-license screen uses two independently generated curriculum
roots and fixed training seeds:

- `Delta_R >= +0.05` on each root for immediate selective advice use;
- `Delta_F >= +0.03` on each root for fixed-policy child learning;
- `Delta_E >= +0.03` on each root for the ecological package;
- no action-interface, generic-capability, work-turn, or task preservation
  contrast worse than `-0.05`.

Each stage is sequential: failure stops downstream spending; mixed root signs
permit one preregistered rerun with two new roots and no design changes. Passing
licenses a separately frozen replication, not a scientific claim. A claim needs
at least six new independent curriculum roots analyzed as the independent
units, with the exact interval/multiplicity procedure fixed in the later
execution packet. Tasks, ages, advice items, and training seeds are repeated
measurements, not independent samples.

## Acceptance-test repairs required in the successor change

- Add exact birth materialization, serialization, capacity, and rollback test.
- Add standardized byte-identical advice receptivity test with personal SLEEP
  disabled.
- Add the longitudinal byte-identical fixed-parent-policy x birth test before
  the adaptive ecological parent test.
- Add neutral-corpus blinded semantic and nuisance-parity audit.
- Add bootstrap source-provenance, structural-disjointness, and isolated
  final-mutation-invariance test.
- Freeze score, normalization, threshold, horizon, practical margin, root as
  statistical unit, uncertainty method, missing-data rule, and replication
  rule before any benchmark generation.
- Give every derangement/wrong-life/wrong-advice control a directional
  prediction before results.
- Apply the unreplayed retention sentinel only to personal SLEEP evidence;
  birth retention needs a separate counterfactual-birth ablation.
- Restrict rank x exposure conclusions to capacity x exposure for the selected
  compiler. Do not call rank a generic plasticity or age variable.
- Replace cadence-mediation labels with the three contrasts in R5.
- Retain sequential spend gates: CPU fixtures -> one-root/two-seed writer
  safety -> second root for survivors -> rank/exposure -> standardized bootstrap
  receptivity -> fixed-policy development -> ecological 2x2 -> prospective
  cadence.

## Plain-language successor

The bootstrap is ordinary schooling that creates two exact birth models: one
practiced at learning from feedback and one equally trained on matched
direct-solution task completion, with the untouched base retained as a damage
check. We first give both the exact same new advice and ask which one uses it
better, before either has personal SLEEP. Then we test whether they learn at
different rates from the exact same fixed lessons. Only after that do we compare
their full childhoods with an adaptive parent. Parenting remains interactive;
parent text never becomes personal SLEEP targets; only grounded child
thought/action/outcome experience does.
