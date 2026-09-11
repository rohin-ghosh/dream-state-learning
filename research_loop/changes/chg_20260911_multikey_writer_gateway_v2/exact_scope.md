# Multi-key writer gateway — exact implementation scope v2

**Change ID:** `chg_20260911_multikey_writer_gateway_v2`  
**State:** proposal only. Exact human ratification of these bytes authorizes
only the named source implementation and deterministic CPU/fault tests. It
does not authorize model or tokenizer execution, source generation, fitting,
GPU use, parenting, child-lineage mutation, scientific claims, C11 work,
release, or submission. A later immutable execution manifest, two independent
PASS reviews, and separate exact human ratification are required before the
first model call.

## 1. Purpose and boundary

Cell F produced large owner-associated probability changes but 0.333–0.439
spill, and R5 amplified one supplied routine while proliferating actions. The
next gateway therefore asks the smallest higher-information question:

> Can one target-masked adapter carry several already-achieved,
> condition-specific child actions at once without becoming a broad action
> habit?

This is a development-only necessary-capability assay. It tests
success-filtered, seen-key endpoint-policy carriage under unseen renderings.
It does not test outcome-token causality, autonomous credit assignment,
reasoning-path learning, unseen-key generalization, retention, writer
qualification, parenting, a clean child, or the complete Dream–LoRA–Think
organism.

The superseded two-key v1 gateway is not implemented or run. The C11 guard is
not changed, completed, invoked, or claimed by this scout.

## 2. Authorized files

After exact human ratification, implementation may add or modify only:

- `organism_v6/multikey_writer_gateway.py`;
- `gpu/multikey_writer_gateway.sh`;
- `tests/test_multikey_writer_gateway.py`; and
- proposal, review, manifest, and receipt artifacts inside this change
  directory.

The implementation must not import from, write into, mount, mutate, or invoke
any live-child, parent, CompilerGym, PCFL, C11, model-server, adapter, or
benchmark output root during CPU tests. Model-facing code may be authored but
not executed under the implementation grant.

## 3. Two independent mirrored roots

One fail-if-exists development run contains roots `R0` and `R1`. The roots use
disjoint opaque tool and mode strings, case identities, source and report
surfaces, and generation seeds. They share only the frozen algorithms,
model/tokenizer revision, recipe, thresholds, and action grammar. Results are
never pooled to rescue a failed root; both roots must pass independently.

Each root predeclares 24 candidate tools: 12 in orientation stratum A and 12
in orientation stratum B. Every tool has visible modes `m0` and `m1`, and the
only legal actions are opaque `a0` and `a1`. Tokenization preflight must prove
that all visible identifiers are distinct and that every declared
near-neighbour control is a different token sequence.

For the eight selected tools, the two hidden maps are:

- stratum A tools: `M+` maps `m0→a0, m1→a1`;
- stratum B tools: `M+` maps `m0→a1, m1→a0`;
- `M−` complements every one of those sixteen tool×mode assignments.

Thus each map contains sixteen keys, eight targets of each action, and two
eight-key orientation strata. Both strata must pass separately so a global
mode→action rule cannot masquerade as tool-conditioned binding.

## 4. Lived source and result-blind eligibility

Before any model call, each candidate tool×mode key receives eight opaque,
provenance-only case identities in each mirror world. Case IDs never enter
model-visible text. For each source trajectory, the frozen base child:

1. sees the visible tool, mode, and unordered legal-action vocabulary;
2. emits one strict initial action;
3. receives only the public binary success/failure outcome; and
4. authors one strict final action for the next occurrence of that visible
   condition.

No parent, correct action, mapping, worked example, admission bit, report
surface, historical LLVM routine, or evaluator-authored replacement target
is visible. Every attempt, invalid output, outcome, and final action is
preserved with immutable hashes.

A case is pair-eligible for one key only when the child-authored final action
is correct in both mirrored worlds. For each key, retain the lowest two
pair-eligible case IDs. A tool is eligible only when both modes supply two
such cases. Within each preassigned orientation stratum, select the lowest
four eligible tools. Fewer than four in either stratum is `SOURCE_INVALID`;
do not top up, redraw, switch strata, or change dose. Publish every source
failure and the complete eligibility vector before fitting.

Each world therefore has exactly 32 retained child-authored endpoints:
sixteen keys × two cases, balanced sixteen `a0` and sixteen `a1`.

## 5. DREAM derivative and target-masked write

The underlying lived initial action and outcome remain in provenance but are
not model-visible training context. This prevents the two-action shortcut
“repeat after success, flip after failure.” The fixed DREAM derivative is:

`visible tool + visible mode + neutral endpoint frame -> child-authored successful ACT`.

For each retained endpoint, compile four predeclared native-dialect
renderings. Across the two endpoints, a key receives eight distinct visible
surfaces. The tool and mode occur in masked context. The child-authored final
action occurs exactly once, solely as terminal supervised target
`ACT: <action>`, followed by EOS. Correctness, outcome, admission, mapping,
case identity, and evaluator metadata are absent from model-visible training
bytes. No target is authored or repaired by the evaluator.

Each adapter contains exactly:

`16 keys × 2 independent endpoints × 4 renderings = 128 items`.

Within each root, `W+` and `W−` must have identical target multisets,
rendering indices, tokenizer-counted target and context length vectors,
supervised-position vectors, EOS counts, item order, optimizer steps,
initialization/dropout seed, and node. The roots use different predeclared
optimizer seeds, applied symmetrically within root. Any mismatch is
`SOURCE_INVALID`.

Train four independent adapters—`R0/W+`, `R0/W−`, `R1/W+`, `R1/W−`—from the
same locally cached frozen Qwen2.5-7B-Instruct revision. Use the standalone
unpacked chat-templated target-masked trainer: all-projection LoRA rank 8,
alpha 16, dropout 0.05, AdamW learning rate `3e-5`, two epochs, batch size 1,
maximum length 2048, EOS on, and no packing or SVD initialization. Each
encoded item is at most 256 tokens. The four fits therefore contain at most
262,144 token-passes.

## 6. Frozen reads

All prompts, action candidates, parsers, seeds, reducers, and surfaces are
hash-bound before source generation. No efficacy-driven change or retry is
allowed after any source output is seen.

### Primary generation

For each root and key, use four source-disjoint held forms and two common-
random replicates under `OFF`, `W+`, and `W−`: 384 calls per root. One output
is one trial. Score only the first authoritative action. Empty, invalid,
DONE-first, or multiple-ACT output scores zero. Later actions can never
improve the score. Constant `a0` and `a1` routines are reported analytically;
each has balanced accuracy 0.5 by construction.

### Teacher-forced binding and held NLL

On four additional held forms per key, score both legal continuations under
`OFF`, `W+`, and `W−`. For key `k`, orient log odds toward its `M+` action:

`q_z(k) = mean_h log[p_z(a_M+(k)|h) / p_z(a_M−(k)|h)]`.

Define `I_k = q_W+(k) - q_W−(k)`. Also compute each own-map target's NLL
reduction from OFF. These forms are disjoint from source, training, primary,
oracle, spill, and interface forms.

### Explicit-map assay oracle

The frozen base receives the complete explicit map and one copy of every
primary held form under both maps. Exact-action accuracy must be at least
0.90 in each root, map, and orientation stratum or the root is
`ASSAY_INVALID`. This tests whether the prompt/interface permits the required
conditional action when the mapping is supplied.

### Four spill families

Use exactly sixteen fixed prompts per family, two common-random replicates,
under `OFF`, `W+`, and `W−`:

1. unseen tool with a known mode;
2. tokenizer-verified near-neighbour unseen tool with a known mode;
3. trained tool and mode appearing in a wrong, explicitly non-policy
   relation; and
4. trained tool with mode omitted.

For every family, root, and adapter separately, report legal-ACT emission-rate
change from OFF and teacher-forced total-variation distance over `a0/a1` from
OFF. Never average an easy spill family with a failed one.

### Interface canary

Run eight fixed four-tick tasks per root under `OFF`, `W+`, and `W−`, with a
hard maximum of 512 generated tokens per task and 128 per turn. Require at
most one authoritative ACT in any generated turn, at most four authoritative
actions per task, no action after DONE (including later text in the same
turn), and no best-of-action or best-of-trajectory scoring.

## 7. Gates and labels

Apply decision precedence independently to each root:

1. `SOURCE_INVALID`: insufficient eligible tools or endpoints; any hidden
   answer/example visibility; any provenance, target-author, balance,
   identity, mask, count, or matched-geometry failure.
2. `OPTIMIZATION_INCONCLUSIVE`: median held-target NLL reduction is below
   0.50 nat for any key, or the two adapters' mean NLL reductions differ by
   more than 0.25 nat.
3. `ASSAY_INVALID`: explicit-map oracle fails 0.90 in either map or stratum.
4. `INTERFACE_OR_FLOOD_INVALID`: strict one-ACT validity is below 0.95 overall
   or 0.875 in either stratum; any generated turn contains multiple ACTs; a
   required interface task is empty/zero-action/DONE-first/invalid; a task
   exceeds four actions; any action occurs after DONE; or any spill family
   has legal-ACT emission increase above 0.05 or legal-action TV above 0.05.
5. `BINDING_WITH_SPILL`: every non-spill binding gate passes but any spill or
   flood gate fails.
6. `MULTIKEY_BINDING_PASS`: every source, optimization, assay, interface,
   flood, spill, and binding gate passes.
7. `GATEWAY_NEGATIVE`: every other valid completed failure.

For one root, binding gates are:

- own-map generated balanced accuracy at least 0.80 for both adapters;
- own-map generated accuracy at least 0.75 in each eight-key orientation
  stratum for both adapters;
- `q_W+(k) >= +0.50` and `q_W−(k) <= -0.50` for at least 12/16 keys,
  including at least 6/8 keys in each orientation stratum;
- mean `I_k >= 1.00` and a paired bootstrap lower 95% bound over keys above
  zero;
- mirrored `tau >= 0.50`, where
  `tau = 0.5[(BA_W+^M+ - BA_W−^M+) + (BA_W−^M− - BA_W+^M−)]`; and
- mirrored gain over OFF `g >= 0.20`, where
  `g = 0.5[(BA_W+^M+ - BA_OFF^M+) + (BA_W−^M− - BA_OFF^M−)]`.

Both roots must independently reach `MULTIKEY_BINDING_PASS`; no pooled mean,
best root, best adapter, or follow-up dose can rescue a failed root.

## 8. Exact permitted reading and next step

A two-root pass permits only:

> In two independent development-only roots, target-masked adapters trained
> on correctness-selected child-authored endpoints produced mapping-specific
> single-action behavior for a counterbalanced sixteen-key tool-by-mode policy
> under unseen surface forms, with both mapping strata succeeding and no
> detected spill on the four bound control families.

A pass authorizes no automatic scientific claim or parenting scale-up. It
supports proposing one later cumulative-interference/retention scout. A
failure is preserved under its exact label. There is no automatic larger-key,
higher-rank, higher-dose, or alternate-recipe follow-up.

## 9. Simple hygiene and later execution gate

The future run must use one unique fail-if-exists, realpath-resolved
development root disjoint from every child, parent, CompilerGym, PCFL, and
C11 root. It binds exact source/compiler/trainer/evaluator/parser bytes;
model/tokenizer revisions; identifier and prompt bytes; seed derivations;
expanded counts; run arguments; workload cap; and forbidden roots. Stages use
`PLANNED -> RUNNING -> COMMITTED|FAILED` markers. Only infrastructure failures
may retry under identical bytes. All failures and rejected rows remain.

The first bound fit may expose timing and resource use but no binding output.
If its conservative projection exceeds three A40-hours for all four fits and
bound reads, stop as `NOT_RUN`; do not change the recipe or add a smoke fit.

Before model/GPU authority, deterministic materialization and fault tests must
pass, the immutable execution manifest must exist, and one fresh independent
reviewer plus one author-side scientific advocate must both return PASS. Rohin
must then ratify that exact execution manifest. These are ordinary
development-scout checks, not the parked C11 guard.
