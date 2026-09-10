# Extractable SLEEP + teachability bootstrap v2: systems attack

Date: 2026-09-09

Role: independent systems adversary. Scope is limited to
`v2_rework_resolution.md`, the bound v1 critique/consensus, `AGENTS.md`, and
the current `organism_v6` writer/LoRA paths. No model, tokenizer, benchmark,
adapter, or GPU execution was performed.

## Verdict

**REWORK.** The v2 note is directionally better and does select one causal
birth topology: bootstrap LoRA -> one merged BF16 birth -> fresh personal
LoRAs. That topology is constructible in principle. The present bytes are not
an executable or ratifiable construction, however:

1. “the same frozen writer recipe” does not identify a writer, precision path,
   initializer, dependency set, or base-checkpoint interface;
2. “zero-initialized” is ambiguous between a correct zero *effective delta*
   and an all-zero factor initialization that cannot learn;
3. the receipt and rollback paragraph does not close the data, brief,
   optimizer, evaluator, or crash ancestry;
4. the neutral rules are internally incompatible for adverse examples and
   audit only response targets even though masked prompt/state text conditions
   every supervised token; and
5. the source/auditor rule sends final-derived hashes back toward the builder,
   contradicting structural target blindness.

The authorization language at lines 5-7 is correct. The stronger sentence at
lines 9-10 should say that this note **proposes repairs** to the five v1
proposal-byte blockers; it does not itself dispose of them. It is absent from
the v1 source-binding manifest and intake state, and the v1 consensus remains
`human_required` with recommendation `rework`.

## Binding and governance blocker

### G1 — this is not yet a successor proposal

Selecting merged BF16 births, changing the control corpus, and changing the
estimands are material graph, loop, visibility, test, and claim changes under
`AGENTS.md`. They require a new exact change artifact, at least two new
fresh-context interpretations, cross-critique, adjudicated consensus, new
hashes, and explicit human ratification. The old v1 ratification request and
source manifest cannot authorize these bytes.

**Repair.** Give the successor a new change/version identity. Bind this note
and every normative source by SHA-256, place exact tests in the new change
rather than promising that they will be added later, and rerun the complete
deliberation path. Preserve separate post-implementation independent review and
GPU authorization.

**Lowest-cost test.** A no-model source-closure check must fail while any
normative file is unhashed, any recorded hash is stale, any concern/test lacks
a disposition, or the requested implementation scope differs from the
ratified scope.

## Birth and personal-LoRA constructibility

### B1 — there is no uniquely identified “frozen writer recipe”

The repository currently has materially different writers:

- `organism_v6/train_adapter.py` is the explicitly frozen v1 bare-text writer:
  rank 16, full-token loss, three epochs, LR `1e-4`.
- `organism_v6/train_adapter_v21.py` is chat-templated, response-masked,
  gradient-checkpointed, rank 8 by default, two epochs, LR `3e-5`.
- `organism_v6/run_life_v2.py` still invokes `train_adapter.py`, while
  `organism_v6/classroom_round.py` invokes `train_adapter_v21.py` with three
  epochs. `DESIGN.md` also still names clean-base rank 16.

The phrase at v2 lines 18-19 therefore cannot be implemented uniquely, and
“the writer's exact dose tolerance” at line 60 has no referent. In addition,
the current v2.1 receipt records `attention_mask.sum()` as `tokens`, which
includes the loss-masked prompt; it does not record supervised response-token
count.

**Repair.** Bind one writer artifact/hash and a closed config: model and
tokenizer roots/revisions, chat-template bytes, PEFT/Torch/Transformers/
Safetensors versions, target modules, task type, rank, alpha and scaling,
dropout, bias mode, initialization rule, max length and truncation, padding and
position-ID behavior, batch/accumulation plan, loss normalization, epochs,
update count, optimizer implementation and every hyperparameter, scheduler,
clipping, precision/autocast, parameter order, all RNG states, nonfinite rule,
and serialization options. Count both attended input tokens and labels unequal
to `-100`; call only the latter supervised tokens.

**Lowest-cost test.** Static manifest/schema validation plus an AST-level
route test should prove that bootstrap-T, bootstrap-N, and personal writers
invoke the same bound entry point and reject every default or environment-only
configuration value.

### B2 — literal zero initialization can permanently disable LoRA learning

For a LoRA update `delta_W = scale * B @ A`, initializing both `A` and `B` to
zero gives zero gradient to both factors on the first step and thereafter.
Current PEFT behavior normally creates a *functionally* zero adapter by making
one factor nonzero and the other zero, but that is an unpinned library default,
not what v2 line 23 says.

**Repair.** Replace “newly zero-initialized” with “newly initialized to an
exact zero effective delta.” State which factor is sampled, its distribution,
seed and dtype, which factor is zero, and require `delta_W == 0` before the
first update while at least one factor is nonzero. Bind `optimizer_state_in =
null`; a later write must never resume bootstrap or prior-personal moments.
Paired arms should use the same initialization tensor hashes wherever shapes
match.

**Lowest-cost test.** On a tiny CPU linear fixture, assert zero pre-update
effective delta, nonzero trainable gradient, changed effective delta after one
step, and identical initialization hashes across paired treatments. An
all-zero/all-zero negative fixture must fail.

### B3 — “merge in BF16” leaves multiple byte- and behavior-distinct merges

The result differs depending on whether `B @ A` and addition are performed in
BF16, FP32 then rounded once, or a mixed/autocast path. Small learned deltas can
round to zero against BF16 base weights. PEFT merge implementation and version,
device, tensor traversal order, tied-weight treatment, safe-merge behavior,
and shard serialization are unspecified. “Same architecture and parameter
count” does not detect unequal rounding loss or residual adapter tensors.

**Repair.** Define an explicit reference equation and arithmetic path. A
constructible default is: load the exact BF16 base on CPU; promote each base
weight and the LoRA product to FP32; add once; round once to BF16; restore
declared tied tensors; save with a pinned safe-serialization/sharding routine.
If a true BF16 product/add is intended instead, bind it literally and accept
its measured loss. “Unload” must mean runtime detachment, not destruction:
retain sealed BT/BN adapter artifacts for provenance and reproduction, but make
them impossible to mount in a personal run.

**Lowest-cost tests.** First use fixed tiny tensors to compare saved weights
against the reference equation and serialize twice in fresh processes for byte
identity. Before spending on development, test the real births for:

- tensor names, shapes, dtypes, tied aliases, architecture, tokenizer, and
  parameter-count equality across arms;
- absence of PEFT/adapter keys or mounted adapters;
- per-module pre-merge delta norm, realized BF16 delta norm, nonzero fraction,
  and rounding-loss ratio; and
- fixed-input parity between unmerged `M0+BT/BN` and reloaded merged births
  under a preregistered numeric tolerance.

Large or arm-asymmetric merge loss is a failed birth, not permission to change
precision after seeing results.

### B4 — current loaders do not bind a lineage birth

`train_adapter_v21.py`, `model_backend.py`, and `absorption_probe.py` all
resolve the base from mutable `V6_MODEL`/`MODEL`; none requires a birth hash.
The backend can mount one adapter but does not verify that its declared base is
the loaded birth. Consequently a T adapter can be trained, probed, or served on
M0 or on the N birth without an early failure.

**Repair.** Every trainer, runtime, probe, merge, and adapter-off path must take
an explicit content-addressed birth root plus expected hash. Eliminate fallback
to a symbolic model name for successor runs. Verify the root before and after
every phase, and verify that adapter metadata contains the same cryptographic
base identity. Adapter-off means that arm's merged birth, never M0.

**Lowest-cost test.** A no-model routing fixture passes T/N/incorrect birth
manifests through all commands. T-on-N, T-on-M0, a one-byte shard mutation, and
an unset birth argument must fail before imports that can initialize a model.

### B5 — the proposed hash is not yet a checkpoint identity

Hashing “every model/config/tokenizer shard” does not define the singular
`birth_checkpoint_sha256` used later. It omits a canonical file inventory and
may omit generation config, chat template, tokenizer auxiliary files, special
tokens, shard index, code/config files, and symlink targets. File order,
volatile metadata, and whether a manifest hashes itself are unspecified.
Likewise, “same serialized architecture” does not establish equal file sets,
tensor maps, dtypes, or personal trainable parameter counts.

**Repair.** Define a detached, canonical directory manifest sorted by relative
path, with size and SHA-256 for every allowed regular file; reject extra files,
symlinks, and path escapes. Derive one Merkle/root hash from that manifest and
state exactly which detached signature/manifest file is excluded to avoid a
self-hash cycle. Record a tensor inventory and an equality report between the
two births. Store births in content-addressed, read-only locations.

**Lowest-cost test.** A fake two-shard checkpoint fixture must produce the same
root under different directory enumeration order and fail on an extra file,
renamed file, symlink, tokenizer change, config change, or one-byte mutation.

### B6 — candidate provenance is incomplete

The five fields at v2 lines 27-29 do not bind the causal input to a cumulative
fresh-from-birth write. The previous adapter is a state parent but not a weight
parent; the weight parent is the birth, while the previous committed evidence,
lesson, view, and corpus roots are data ancestry. Those roles must not share a
generic “previous” field.

**Repair.** A candidate receipt must at minimum bind:

- M0 root; bootstrap corpus/evidence root; BT/BN tensor/config root; merge
  algorithm/toolchain; birth root;
- lineage/arm/root IDs and transaction ID;
- weight parent (`birth`), state parent (last committed personal adapter or an
  explicit null sentinel), and canonical data parent;
- canonical evidence-index root, support-resolver output, lesson root,
  rendered-view root, exact encoded IDs/labels/masks/batch plan, and compiler
  code/config root;
- personal initializer tensors, complete RNG states, optimizer empty-state
  assertion, trainer/environment root, candidate tensors/config, and all
  counts/dose residuals; and
- fixed evaluation panel root, raw results, decision rule/verdict, prior and
  resulting active-head roots, timestamps used only outside hashed build
  inputs, and fault/restart status.

Paths or model names are metadata, not identities. Hash adapter config and all
tensor shards, not only a directory label.

**Lowest-cost test.** Delete or mutate each receipt edge one at a time and
require lineage validation to fail. A candidate should be reproducible from
its roots without consulting mutable “latest” directory scans.

### B7 — rollback is neither atomic nor complete in the current organism

The existing marker-based flows demonstrate why “restore the previous
personal adapter” is insufficient:

- `classroom_round.py` lines 292-297 imports corpora from every earlier round
  with a corpus file, including rejected rounds.
- `run_life_v2.py` lines 203-211 likewise chooses the latest prior corpus
  without requiring a committed adapter.
- `run_life_v2.py` lines 117-136 can render waking and parent briefs from a
  rejected sleep because it tests file existence, not commit ancestry.
- candidate, manifest, exam, and marker writes are separate renames with no
  single atomic lineage-head update; crash/restart behavior is not bound.

Thus the previous adapter may remain mounted while rejected data or briefs
still affect the next child. That violates v1 C10 and the v2 claim.

**Repair.** Use a content-addressed staging transaction and one atomic
`lineage_head` commit. Only the head's transitive committed data manifest may
feed future compilation, briefs, runtime context, evaluation baselines, or
selection. Rejected/staged artifacts remain audit-only and are never discovered
by directory scan. The commit record must bind the exact previous head; use
compare-and-swap semantics to prevent concurrent/stale promotion. Verify and
fsync staged files and their parent directory before promotion. Define recovery
for birth build, compile, train, evaluate, commit-before-rename,
rename-before-receipt, and restart boundaries.

**Lowest-cost test.** A model-free fault matrix injects failure after every
persistent write/rename/fsync boundary. After each restart, the active head,
adapter, corpus, brief, optimizer state, selection state, and evaluation panel
must equal the last committed closure byte-for-byte. A rejected corpus/brief
sentinel must never appear in the next compiler input or rendered context.

## Neutral-corpus attack

### N1 — “same public state” and “state additionally reveals” are different
conditions

V2 lines 38-42 call public states the same and then add an operative rule or
action only to neutral. The latent environment instance may be shared, but the
attended observations are not. This distinction matters because masked prompt
tokens still condition response gradients, as v1 BSD03 already established.

**Repair.** Name three objects separately: shared latent transition, shared
public-state fields, and arm-specific conditioning block. Store and hash the
fully rendered attended sequence for each arm. State the resulting estimand as
the effect of the complete compute-practice curriculum versus the explicit-
state/action curriculum, not “teachability versus an otherwise identical
corpus.”

**Lowest-cost test.** A paired-row diff must permit changes only inside named
arm-specific spans and target-computation spans. Any unclassified byte is a
hard failure.

### N2 — revealed answers, matched adverse outcomes, and a non-harmful sham
cannot generally coexist

For deterministic microtasks, if neutral reveals the correct rule/action but
must reproduce a teachability example's unsuccessful action/outcome, it trains
the child to ignore the revealed answer or intentionally fail. If neutral
instead executes the revealed correct action, its success/failure stratum no
longer matches. A two-percentage-point aggregate balance does not repair this
per-example contradiction.

**Repair.** Sample a canonical transition `(state, action, public outcome)`
before arm-specific rendering and preserve that exact transition in the pair.
Include an adverse transition only when the action was preregistered as a
rational information-gathering action and “adverse” is not evidence that the
target ignored known correctness. Otherwise exclude the pair or restrict the
bootstrap to valid non-harmful transitions and drop the adverse-outcome
requirement. Pair inclusion/exclusion must be arm-independent and recorded;
never fill an outcome quota by separately cherry-picking arm continuations.

**Lowest-cost test.** Replay every normalized action in the versioned CPU
microdomain and require exact paired action/outcome identity. A rule-revealed
row whose target contradicts its revealed rule/action must fail semantic
validation.

### N3 — auditing only targets misses the strongest contamination channel

The neutral audit at lines 52-56 scores “targets,” yet the neutral prompt itself
contains a rule/action and the teachability prompt contains computation advice.
Both are attended. A neutral target can contain no named computation while the
full training row still practices following a correction, retrieving a supplied
rule, scoping a supplied conclusion, or mapping advice to action. This is
especially dangerous because “retrieve a relevant correction” is itself one
of the proposed six computations.

**Repair.** Enumerate the six computations normatively—currently they exist
only in a v1 interpretation: predict from named features; test competing
hypotheses; stop unproductive recursion and act; revise after surprise; scope a
conclusion; retrieve a relevant correction. Define positive, negative, and
ambiguous span-level examples for each. Audit the entire attended prompt plus
response and report prompt-only, target-only, and joint contamination.

**Lowest-cost test.** Run the rubric over all 192-240 paired rows, not a sample.
Require a second independent rater and report the full 2x6 confusion table,
disagreements, adjudication, and arm-inference accuracy. A target-only pass is
not sufficient.

### N4 — “token bucket” and semantic padding do not match optimization dose

A bucket permits unequal supervised tokens. Supervised “semantically inert”
padding is still a gradient-bearing target; masked prompt padding can still
alter length, truncation, position handling, and attention context. Under the
current v2.1 encoder, the response is capped, prompt retention depends on
response length, and input rather than supervised tokens are reported. Thus
line 46's mask/dose claim is not presently implementable.

**Repair.** Freeze the tokenizer and exact serialized chat template before
generation. Bind, per pair, encoded input IDs, label IDs, attention mask,
response start, truncation decision, action-token span, and batch/update slot.
Use naturally length-matched authored responses where possible. Any filler must
be explicitly classified as supervised treatment content or nonsupervised
padding; never call it inert. Freeze numeric tolerances for supervised tokens,
attended tokens, sequence-length distribution, and within-family x computation
dose before seeing results. Optimizer opportunities and update count should be
exactly equal.

**Lowest-cost test.** A tokenizer-only receipt compares per-pair and aggregate
mask geometry, labels unequal to `-100`, action positions, truncation, batches,
updates, and arm totals. Include boundary fixtures at 2048 tokens and answers
near the response cap.

### N5 — the neutral is deliberately easier, so “task difficulty” remains
unresolved

Revealing the rule or action lowers conditional response uncertainty by design.
Matching turns, valid actions, tokens, and final outcome does not match base
difficulty, learning signal, gradient scale, or opportunity to practice
uncertainty. This is a semantic treatment bundle, not a nuisance already
removed. No single neutral can both omit the six computations and be identical
in the cognitive work that produces them.

**Repair.** Narrow the claim to the curriculum-package contrast and measure the
remaining imbalance. Before bootstrap training, use a held-out calibration pool
to compare M0 response NLL, valid-action rate, attempts, and outcome magnitude
by family and stratum under the two renderers. Freeze matching/rejection rules
on that calibration pool. If the copy-neutral is grossly easier, add a second
workload-matched active control that performs an equally demanding but
predeclared orthogonal computation; do not tune it on later receptivity
results.

**Lowest-cost test.** Human rubric scores can run first. Only after the
successor's model-execution gate, compute preregistered M0 difficulty metrics on
the calibration split. Fail rather than post-hoc reauthor if standardized
imbalances exceed the frozen limits.

### N6 — aggregate parity permits selection and mixture confounding

Two-percentage-point overall outcome parity can hide family-, computation-, and
difficulty-specific imbalance (including Simpson reversals). Selecting targets
after observing validity/outcomes also favors different demonstrator failures
unless the pair is retained or dropped as one unit. The current provenance list
does not say whether T and N targets share a demonstrator trajectory, are
independently sampled, or are transformations of one canonical transition.

**Repair.** Assign a permanent pair ID. Generate/select the canonical
environment transition before arm rendering; retain/drop the pair under one
arm-independent mechanical rule. Match or report exact action and outcome
magnitude within family x computation x difficulty cells, not only aggregate
favorable/adverse fractions. Bind demonstrator weight hash, inference code,
sampling parameters, generation seed and occurrence ID, raw continuation,
parser version, dispatch trace, environment version, and all rejected attempts.

**Lowest-cost test.** A pure-data join must show one T and one N row per pair,
one canonical transition receipt, no orphan or duplicate pair, and no
treatment-dependent admission. Recompute all strata mechanically from raw
outcomes.

### N7 — “label-blinded” is not credible and the 80%/5% rules are underspecified

An auditor can usually infer the arm from an explicit rule/action in the prompt
or a computation-rich target. Random order hides a label, not treatment.
Neither the auditor identity/prompt/version nor ambiguity, multi-label rows,
rater disagreement, denominator, or uncertainty is specified. Allowing 20% of
T to omit its intended computation and 5% of N to contain any intended
computation may be too permissive for a corpus this small.

**Repair.** Call this an independent randomized semantic audit, not blinded.
Freeze the rubric, rater identities or model hashes/prompts/seeds, multi-label
rules, ambiguity disposition, adjudicator, denominators, and exact pass rule.
Report per-computation prevalence and intervals as well as aggregates. Keep
corpus builders unable to tune on row-level audit feedback: they receive a
fixed predeclared failure code or must version a new corpus and restart audit.

**Lowest-cost test.** Seed the audit set with known positive, negative,
ambiguous, prompt-only, and target-only fixtures. Require the rubric to recover
their labels before it can score the real corpus.

## Structural blindness and provenance

### P1 — disjoint names/APIs do not establish disjoint policy structure

The four family labels are not source bindings. No generator paths, commits,
schemas, rule sets, reward functions, splits, or held-out roots are named. A
Boolean hidden-rule `QUERY` domain is also structurally close to the current
`organism_v6/rulegame.py` development/evaluation machinery even if its nouns
and action token differ. Excluding only the final compiler gym does not protect
standardized-advice and ecological-development assays from homologous bootstrap
practice.

**Repair.** Bind exact generator sources and immutable split manifests now.
Define disjointness against *all* later development and evaluation domains:
latent task family, state schema, transition structure, action grammar,
reward/feedback function, identifiers, prompts, examples, and generator RNG
state—not merely final compiler vocabulary. Any intentional structural overlap
must become a named transfer condition, not pass as target-blind evidence.

**Lowest-cost test.** Static dependency closure and schema/API/reward diffs must
run before generation. A deliberately renamed clone of a downstream generator
must fail, proving the check is more than lexical.

### P2 — advice informativeness and target generation remain free choices

“May identify which computation” can nearly determine the next action in a
small domain. The receipt list does not define who authored the target, what
information that demonstrator saw, whether advice was chosen after the action,
or whether selection distilled only successful teacher-policy traces. A banned
exact action string is not a semantic information cap.

**Repair.** Advice must be selected from a frozen computation-level template
before the child continuation and must not observe hidden state, answer, future
action, or outcome. Bind its eligibility function and causal timestamp. Define
a task-specific action-equivalence set and an advice-only action-prediction
ceiling; reject paraphrased prescriptions, not only exact token overlap. Retain
all generation attempts and make pair selection independent of later final or
development performance.

**Lowest-cost test.** Mechanical timestamp/visibility fixtures plus adversarial
paraphrase examples must fail if advice is created after dispatch or maps to a
single action-equivalence class above the frozen cap.

### P3 — auditor hashes sent to the builder violate isolation

V2 lines 121-125 correctly isolate the final-task mutation auditor, then say it
emits “hashes to the builder path.” A hash of a final manifest is still derived
from forbidden final bytes and changes under mutation, so it both contaminates
the builder's dependency closure and prevents birth-build inputs from remaining
byte-identical. A hash can also act as an opaque condition or cache key.

**Repair.** The auditor keeps original/mutated final roots in a restricted
audit-only receipt outside the builder and birth DAG. The builder receives no
final-derived bytes or identifiers. A release controller may consume a signed
pass binding only the already-built bootstrap root, audit-policy version, and
auditor identity; that release receipt must not be an input to corpus or birth
construction.

**Lowest-cost test.** Information-flow taint the original and mutated final
manifests. No tainted value—including hashes, filenames, exit-dependent seeds,
cache keys, timing, or row-level diagnostics—may reach the builder process,
environment, filesystem namespace, or birth manifest. Both hermetic builds
must have identical allowed input roots and output bytes.

### P4 — deterministic rebuild requires canonical outputs and a real seed path

JSON ordering, timestamps, absolute paths, demonstrator nondeterminism, library
versions, and filesystem enumeration can defeat the byte-invariance test even
without leakage. Conversely, rebuilding from a cached frozen corpus can make
the test vacuous. The current `VLLMBackend.__call__` accepts a `seed` argument
but drops it when delegating to `batch`, so current code cannot substantiate a
single-call seed receipt.

**Repair.** Separate (a) dependency-closure proof, (b) deterministic builder
reproduction from raw allowed sources, and (c) final-mutation noninterference.
Use canonical serialization, occurrence-aware seeds actually consumed by the
backend, pinned generation/runtime versions, and no volatile bytes in build
inputs. Record volatile operational metadata only in a detached receipt.

**Lowest-cost test.** A spy backend records the actual seed and allowed inputs
without loading a model. Fresh-process builds with permuted file enumeration
must match; changing one allowed source must change the root; changing only a
forbidden final fixture must not change any builder-observable value.

## Receptivity assay confound exposed by the neutral design

R3a's unaided-then-advised change is not advice-specific by itself. The second
attempt benefits from task repetition, the first action/outcome, and ordinary
within-context revision. A teachability birth is intended to improve precisely
that feedback use, so it can show a larger second-attempt gain even if the
standardized advice has no effect.

**Repair.** Add a randomized, byte/dose-matched second-attempt no-advice or
irrelevant-advice control on paired disposable task clones. Either withhold the
first outcome in both conditions or provide the same frozen public outcome and
factor it explicitly. The advice effect is the attempt-2 contrast relative to
that repeated-attempt control, compared across birth treatments. Never feed
assay transcripts into the continuing child or any personal SLEEP corpus.

**Lowest-cost test.** A deterministic mock child that improves only from
repetition/outcome—but ignores advice—must yield zero advice-specific effect.
The current pre/post score would incorrectly pass this fixture.

## Minimum repair packet before any implementation

The successor proposal should not be accepted until it contains, in exact
bytes:

1. the complete governed successor chain required by `AGENTS.md`;
2. one content-addressed writer/base/tokenizer/toolchain and exact
   zero-effective-delta initializer;
3. a reference merge algorithm, directory/tensor manifests, BF16 rounding-loss
   gate, and runtime base-binding contract;
4. a typed ancestry DAG and atomic lineage-head/fault-recovery state machine
   that excludes rejected data and briefs;
5. a paired neutral-row construction that resolves the revealed-answer versus
   adverse-outcome contradiction;
6. whole-sequence semantic audit, exact six-computation ontology, encoded dose
   receipt, task-difficulty calibration, and package-limited causal claim;
7. exact source/generator/split closure against every downstream assay and an
   auditor that returns no final-derived value to the builder; and
8. a repetition-controlled standardized-advice estimand.

Until those bytes are independently adjudicated and human-ratified, the only
supported conclusion is that merge-once BF16 birth plus fresh personal LoRA is
an implementable *architecture sketch*. It is not yet a uniquely reproducible
system, a complete rollback protocol, or a confound-controlled bootstrap test.
