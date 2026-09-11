# Conditional writer canary — exact scout scope v1

**Change ID:** `chg_20260911_conditional_writer_canary_v1`  
**State:** proposed; non-executable until Rohin ratifies these exact bytes.  
**Purpose:** qualify or reject one SLEEP writer for a later exploratory clean
parenting canary. This is not a clean child, a parenting test, or C11.

## 1. Fixed scientific question

Can a single frozen sleep recipe carry a coherent, bank-specific synthetic
`(tool identity, mode) -> action` association into a rank-8 LoRA such that it
changes strict native actions on unseen phrasings, rather than merely changing
global action frequencies or learning a broad completion habit?

## 2. Isolated synthetic experience banks

Generate exactly six independently seeded banks with seeds
`8111, 8112, 8113, 8114, 8115, 8116`. Every generated JSON or text run artifact
carries `synthetic=true` or the canonical synthetic header; binary artifacts
are quarantined by realpath and inventory hash. Authorized source and test
files remain at the paths named in section 9 and are hash-bound by the pair
plan. All generated fixtures, plans, attempts, weights, reads, failure records,
and reports live beneath one realpath-resolved
`CANARY_ROOT/chg_20260911_conditional_writer_canary_v1/<run-id>`. The root must
be disjoint from every life, clone-group, parent, and C11 root; symlinks and
writes outside it are refused. At root creation, atomically write an immutable
quarantine-root marker binding the scope hash, change ID, run ID, resolved
root, and forbidden roots. At terminal closure, atomically write
`SYNTHETIC_QUARANTINE.json`, once, hashing every previously generated artifact
beneath the run root except the quarantine manifest itself; it is the final
permitted write and is never rewritten.

No corpus, weight, ledger, retrieved row, model output, derivative, path,
change ID, or denylisted hash from this canary may become a child, parent, or
C11 input or ancestor. Only the generic writer configuration may later be
proposed for promotion under a separate approval.

Each bank contains 64 opaque four-character tool identities. Tools are
stratified across four mode pairs and four two-action pairs. Within every
mode-pair x action-pair stratum, half the tools use one mapping direction and
half the opposite direction. Thus no mode-only, action-only, or
first-position policy solves the task.

For each tool and each of its two modes, create one internally consistent
scripted experience containing the state, a failed alternative action and its
world outcome, the successful action and its world outcome, and the resulting
child action. These are controlled writer-assay experiences, not autonomous
discoveries and not parenting data.

The compiler renders every successful `(tool, mode)` association in exactly
16 predeclared surface forms. The forms vary wording and ordering but preserve
the same state, actions, and outcomes. Context tokens are loss-masked; the only
supervised continuation is exactly `ACT: <ACTION>`. Add a byte-identical bank
of generic native-interface anchors to both training arms, containing 20% of
the realised supervised target tokens. No parent text, reflection rating,
report output, or evaluator text enters training.

## 3. The paired intervention

For every bank, train two adapters from the same frozen base checkpoint:

- **T (true):** tool identities retain their experienced mappings.
- **PI (permuted):** within each matched stratum, a fixed-point-free
  permutation swaps complete tool identities between opposite-direction
  mappings. Formally, for visible identity `t`, the PI item is copied from T
  identity `pi(t)`: every occurrence of source ID `pi(t)` is rewritten to
  `t`, while modes, actions, outcomes, and the `ACT:` target remain those of
  the source item. Thus `M_PI(t,m)=M_T(pi(t),m)`, and a machine check requires
  this to differ from `M_T(t,m)` for both modes of every tool.

PI therefore describes a coherent alternate synthetic bank history. It does not contradict an
outcome within a tool. T and PI must have identical target-token multisets,
action counts, success/failure counts, exposure per key, number and order of
items, tokenizer-counted context and target budgets, post-collate supervised
positions, EOS count, optimizer steps, rank, initialization/dropout seed, and
node. A machine receipt must prove every equality and the per-key mapping
  relation before training.

## 4. Frozen writer/trainer candidate

Use `Qwen/Qwen2.5-7B-Instruct` from the locally cached exact revision and the
standalone v3 masked trainer in unpacked mode:

- chat template on;
- context loss masked, `ACT:` continuation loss on;
- rank 8, alpha 16, dropout 0.05;
- target modules `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`;
- AdamW, learning rate `3e-5`, two epochs, batch size 1;
- maximum length 2048, add EOS, no packing, no SVD initialization;
- one stored training seed per root, shared by T and PI;
- cumulative reconstruction from the frozen base, never incremental fitting
  over another adapter.

The exact model revision, tokenizer revision, container, dependency lock,
source bytes, expanded arguments, corpus SHA-256, encoded target count, and
training seed are written before training. A mismatch refuses that root.

## 5. Shared read conditions

Evaluate on four unseen prompt forms for every tool-mode pair, with two common-
random generation replicates. OFF, T, and PI prompts contain only the opaque
tool identity, mode, task instruction, and native interface. They contain no
candidate list, action ordering, past action, success/failure outcome,
retrieved experience, or answer. The four templates are hash-bound before the
GPU gate.

Generation uses temperature `0.7`, top-p `0.9`, maximum 12 new tokens, no
retries, and stops at the first newline, EOS, or 12-token limit. Seeds derive
from `SHA256(eval_root_hash, bank, tool, mode, prompt_form, replicate)`. One
`eval_root_hash` is shared byte-identically by OFF, T, PI, GOLD, and TEXT for a
bank and excludes condition, adapter identity, GPU, launch order, and wall-
clock time. CPU fixtures must prove condition-invariant prompt seeds.
Generation must end in a
strict parseable `ACT: <ACTION>`; invalid or extra-action outputs score zero.

For every bank report:

- **OFF:** the frozen base without either adapter;
- **T:** its true adapter;
- **PI:** its permuted adapter, scored separately against the true and its own
  permuted bank mapping;
- **GOLD:** OFF with the one correct eligible raw experience for that
  tool-mode supplied in the same native wake context;
- **TEXT:** OFF with a frozen candidate-blind lexical retriever over the
  eligible raw bank, top-2 rows, at a 256-token context budget.

The GOLD row rendering, TEXT query tokenizer, lexical scoring function,
tie-break, row rendering, left-truncation to 256 tokens, and empty/miss
behaviour are hash-bound before the GPU gate. The retriever receives only the
current visible tool/mode state, is frozen before results, and never receives
the answer or candidate action. Retrieval misses remain misses. GOLD is an
accessibility control, not an upper bound on what weights can learn.

Also evaluate 64 unexposed tool identities, one-character-neighbour tool IDs,
and no-mode/wrong-relation prompts. In addition to strict generation, score the
teacher-forced distribution normalized over the eight legal actions. For each
control family separately report mean per-prompt total-variation shift from
OFF, worst-family mean shift, neighbour-following rate relative to the exposed
identity, and wrong-relation action dependence. Global action marginals are a
secondary diagnostic only. Compute the best single-action, mode-only,
action-pair-position, and the complete fixed-routine set on the same balanced
bank before opening adapter outputs. That set is exactly: every constant legal
action; every policy keyed only by visible mode token; every policy keyed only
by mode-pair and visible mode; every policy choosing the first or second member
of the action pair; and every policy keyed by mode-pair, action-pair, and
visible mode but not tool identity.

For each control family and each arm, also report strict generated-action
change rate versus paired OFF, conditioned separately by mode and action-pair
stratum. No cancellation across strata or control families is permitted.

## 6. Retention and safety

After the initial read, generate one equal-sized unrelated bank with disjoint
tool identities for each root. That new bank is byte-identical for T and PI,
balanced under the original strata, compiled by the same renderer, and merged
in one identical deterministic old/new item order. Reconstruct both T and PI
adapters from the same frozen base using an exact 1:1 old/new supervised-
target-token mixture, the same writer/trainer, and shared seeds. Re-read the
original bank. This is called survival through one cumulative interference
write, not general retention.

Before either initial or retention adapter is read scientifically, T and PI
must each:

1. produce a strict valid `ACT:` on at least 95% of 32 fixed train-split
   interface-canary prompts; and
2. remain within `-0.05` of OFF on a fixed 32-item generic-action non-harm
   canary.

The canaries may reject an adapter but never select among T and PI. A rejected
arm invalidates that root's binding contrast; it is never counted as a low-
performing comparator. No report item appears in a canary.

Before scientific generation, evaluate a hash-bound audit row for every
training key using one held-out target-form prefix. For each arm, the median
per-key supervised-token NLL must fall by at least 0.50 nat from OFF, and the
absolute difference between T's and PI's mean NLL reduction must be at most
0.25 nat. Otherwise the root is `optimization-inconclusive`.

## 7. Fixed measurements and decision

For each root and condition, first average decoding replicates per prompt,
then prompt forms within `(tool, mode)`, then tools within each predeclared
mode-pair x action-pair source group, then source groups equally. Call this
balanced native-action accuracy `BA`.

Let `BA_z^M` mean balanced accuracy of adapter `z` when scored against mapping
`M`. The symmetric primary per-root contrast is:

`tau_bind(r) = 0.5 * [(BA_T^T - BA_T^PI) + (BA_PI^PI - BA_PI^T)]`.

The directional `BA_T^T-BA_PI^T` remains secondary. This symmetry prevents a
failed PI adapter from manufacturing a favourable result: each adapter must
prefer the coherent mapping it was actually trained on.

Supporting quantities are each arm's own-mapping gain over OFF,
`BA_TEXT-BA_OFF`, GOLD accuracy,
advantage over the best fixed routine, wrong/unexposed spill, interface rate,
and each arm's retained fraction of its own-mapping gain over OFF after the
unrelated write. OFF is shared calibration; common-random T/PI generation
supplies the primary pairing.

The candidate qualifies for a later exploratory parenting canary only if:

- GOLD accuracy is at least 0.85 in every root;
- both arms' interface rates are at least 0.95 initially and after retention
  in every root;
- both arms pass the optimization-fit rule in every root;
- all six `tau_bind(r)` values are positive, their mean is at least 0.02, and
  the lower endpoint of the predeclared two-sided 95% t-interval over the six
  root values exceeds zero;
- in every root, T and PI each improve at least 0.02 over OFF when scored on
  their own mapping;
- in every root, T and PI each beat their own mapping's best fixed routine by
  at least 0.05;
- for T and PI separately, each control family's mean per-prompt total-
  variation shift is at most 0.05, neighbour following rises by at most 0.05,
  wrong-relation action dependence rises by at most 0.05, and each mode-by-
  action-pair stratum's paired generated-action change rate on every control
  family is at most 0.05;
- after the unrelated write, all six `tau_bind` values remain positive, their
  mean remains at least 0.02, the lower endpoint of the same two-sided 95%
  root-level t-interval exceeds zero, each arm's own-mapping gain remains at
  least 0.02 and at least 80% of its own initial value, each arm still beats
  its own best fixed routine by at least 0.05, and every teacher-forced and
  generated-action spill gate still passes; and
- both arms' generic non-harm canaries pass initially and after retention in
  every root.

TEXT is reported but is not an admission gate. If it fails, no weights-versus-
text statement is allowed. This scout makes no equivalence claim from a null.
Any missing or invalid root makes the six-root qualification incomplete; a
scientific failure is preserved and not replaced. There is no efficacy stop,
arm addition, threshold change, or recipe change after the first adapter
output is opened.

## 8. Interpretation and scope boundary

If every gate passes, the only allowed reading is:

> Across six predeclared synthetic tool-mode banks in this two-action assay,
> adapters trained on either of two marginal-matched coherent mappings
> preferentially followed the mapping present in their own scripted
> experience under unseen prompt templates, preserved native ACT output, and
> retained the association after one cumulative unrelated-bank write.

The tool identities themselves are seen during training; only the prompt
forms are unseen.

This qualifies one writer representation for a separately approved
exploratory parenting canary. It does not establish autonomous experience
selection, a persistent child, parenting efficacy, faster learning, general
memory, connected memory, goal traversal, recurrence, or a paper-grade
population effect.

If T shifts behaviour but fails specificity, label it `association component
mixed with broad habit`. If T and PI are similar while both shift marginals,
label it `broad habit`. If adapters do not reduce NLL on their own target-form
audit rows, label it `optimization-inconclusive`. If GOLD fails, the assay is
invalid for a memory conclusion. No failed outcome is rewritten as a positive
claim.

Ratification of this document authorizes only scoped implementation,
deterministic materialization, and CPU fixtures. GPU execution requires a
later hash-bound run manifest containing exact implementation bytes, generated
bank/permutation hashes, all prompt/rendering/retriever bytes, expanded
training and evaluation arguments, source and output roots, fixed generation
counts, a result-blind throughput estimate, a maximum of 72 total GPU-hours
and 24 wall-clock hours on at most six GPUs, test results, and two independent
read-only PASS verdicts. If the pilot predicts that cap will be exceeded, the
run is `NOT_RUN` until re-ratified; roots, forms, controls, or replicates are
never silently reduced.

The later GPU grant may authorize exactly 12 initial adapter fits, 12
cumulative retention fits, the five named initial read conditions, T/PI-only
retention reads, fixed aggregation, and artifact hashing. It may not authorize
a child lineage, parenting, compiler/deployment gym, new lifetime, C11 work,
external release, paper claim, or submission. Existing v6 mechanism and
parenting scouts continue independently under their pinned identities and
remain exploratory.

## 9. Scoped implementation and publication state machine

The implementation grant permits only these new canary-specific components:

- `organism_v6/conditional_writer_canary.py` (fixture, pair-plan, evaluator,
  reducer, and immutable run-state driver);
- `organism_v6/synthetic_quarantine.py` (containment and denylist helpers);
- `tests/test_conditional_writer_canary.py` and dedicated golden fixtures; and
- `gpu/conditional_writer_canary.sh` plus the later generated run manifest.

It may call the existing standalone v3 trainer but may not modify or invoke a
live-life runner, clone coordinator, parent process, or C11 component. The
driver passes an offline resolved local model/tokenizer snapshot to the
trainer and sets local-only/offline execution. It treats the trainer's `DONE`
as attempt telemetry, never as scientific publication.

Before either paired fit starts, atomically write one immutable pair plan that
binds the exact scope, source, fixture, parser, retriever, reducer, dependency,
base-weight, tokenizer, corpus, permutation, seed derivation, and expanded
argument hashes. It also binds the actual v3-normalized item order and hashes
of every post-collate input length, label mask, target sequence, EOS count,
epoch order, and expected step count. `group` and `order` are invariant to the
visible tool identity. T and PI in a root use fresh processes and fresh base
loads on the same physical GPU UUID and software stack. Any mismatch refuses
both before training.

The publication state is
`PLANNED -> RUNNING attempt-N -> VALIDATED -> COMMITTED`. Each attempt gets a
new directory. A crash preserves the attempt and restarts from the frozen base
with the identical plan and seed; partial optimizer state is never resumed.
Only a validated adapter tree is atomically published. `COMMITTED.json` binds
the plan hash and adapter-tree hash. Nonfinite batches, wrong step counts,
missing files, or hash drift can never commit. An exact committed cell skips;
a mismatched resume aborts the root. Every read cell writes atomically with
stateless seeds, so read reordering or restart is byte-identical. A scientific
or canary failure is never replaced; only an infrastructure attempt may repeat
under the identical plan.

The later immutable GPU execution packet contains exact bytes for every train
and read form, identity/action/mode pool, anchor, canary, ID generator,
retriever, tie-break, truncation, parser, generation setting, fixed-routine
enumeration, spill formula, retention denominator, reducer, and output path.
It declares one disjoint retention bank per root, shared byte-for-byte by T
and PI, and the exact deterministic old/new order. Report outputs remain
sealed until both arms and their registered failure states are terminal.

CPU and fault tests required before a GPU manifest may pass are:

- quarantine realpath, symlink, and outside-write refusal;
- synthetic-marker/path/hash refusal by the clean-birth deny helper;
- pair receipt over the actual v3 collator and epoch order;
- refusal on one-byte corpus, group, revision, seed, or pair drift;
- fresh offline base load per arm;
- no commit after nonfinite loss or wrong step count;
- deterministic restart after kills at plan, train, save, and read boundaries;
- committed-cell skip and mismatched-resume abort;
- condition-invariant evaluation seeds and byte-identical reordered reads;
- identical T/PI retention bank and old/new token mix;
- sealed results until paired termination; and
- zero reads or writes beneath any child, parent, or C11 root.

The full canonical C11 guard stays ready but is neither completed nor enforced
for this scout. It is finished and enforced only for the final paper-grade C11
run, per Rohin's directive.
