# Minimal post-positive assay for parametric reuse versus storage

**Date:** 2026-09-13 UTC  
**Role:** fresh independent compression/reuse audit  
**Status:** prospective analysis only; no source, benchmark, model, tokenizer,
adapter, job, or GPU change

## Verdict

**REWORK the current compression sidecar.** After a positive PCFL mechanism
and lifetime result, add one small **zero-new-fit predictive-reuse assay** to
the already trained confirmation lineages. It can establish that the mounted
LoRA contains useful, reusable structure rather than only recalled rows. It
must not be called physical LoRA compression.

**DEFER physical parametric compression.** The current rank-8 adapter is about
`80.8 MB`, while the complete PCFL life is much smaller. No behavioral probe,
short DREAM text, zero returned-memory tokens, or favorable rank number can
reverse that byte accounting.

The current successor's separate `SCHEMA_LORA` fit is not the minimum test.
Training a new adapter on a compact, supplied schema and then applying that
schema shows compact-rule transport. It does not show that the ordinary DLT
writer extracted reusable structure from its accumulated action--outcome
experience. It also adds 16 fits before using the already available learned
states. Test the existing states first.

If the assay below passes, the allowed phrase is **parametric predictive
reuse** or, with the code-length gate, **conditional predictive semantic
compression**. The paper must print the unfavorable `80.8 MB` physical rate
beside it. The word *compressed* without those qualifiers remains unavailable.

## 1. The one distinction the assay must make

Exact recall of a seen `(key -> answer)` row is storage. Retrieval of that row
from text is also storage. Reusable structure is present only if experience
from earlier modules improves a prediction or action on a fresh module for
which the exact answer row has never existed.

The smallest clean test is therefore:

```text
earlier public action--outcome modules
  -> ordinary child EVENT/LINK rows
  -> ordinary qualified DLT SLEEP writes
  -> freeze the adapter before target outcomes exist
  -> predict and act in fresh structure-governed modules
```

No special schema sentence is added to the sleep corpus. No target outcome is
available to the writer, text store, or actor. Success must disappear when the
same predictions are scored against a matched independent continuation and
when the adapter is removed.

This tests the complete DREAM-plus-LoRA compiler already used by the proposed
system. It does not test whether a separately authored compact formula can be
memorized.

## 2. Reuse the paper lineages; add no training arm

Entry requires all of the following:

1. both PCFL DEV v2.2 roots pass `CONNECTED_MEMORY_SERVICE_DEV`, writer
   qualification, locality, generic-canary, and PCFL task-retention gates;
2. the paper successor's `REUSABLE_STRUCTURE` generator is frozen and passes
   its model-free identifiability, shortcut, marginal, and exact-solver checks;
3. the core DLT-versus-SLEEP_FROZEN lifetime gate is positive; and
4. the relevant DLT cut passes its own acquisition, oldest/newest retention,
   legality, and native-use gates.

Then reuse the first `16` untouched confirmation lineages, including every
failed lineage. Do not create replacement roots and do not fit a new adapter.
At the final core cut, preseal `8` fresh reusable-structure target modules per
root. Every target's identifiers and exact relations are absent from all prior
events, child rows, replay views, corpora, adapters' source manifests, and text
stores. Byte/hash absence is an exact gate, not a lexical search.

For each target, freeze a paired `INDEPENDENT` answer assignment with the same
input bytes, candidate sets, answer marginals, lengths, and source prefix. The
same frozen model predictions are scored against both assignments; the
independent side causes no second generation and can never affect training.

## 3. Token-sufficient conditions

Use the same actor, task state, action allowance, and up-to-`2048` generated
tokens in every behavioral condition. This is deliberately a
**token-sufficient** regime. Reasoning or action is never shortened to create
an apparent memory advantage.

Score these conditions:

1. `DLT_ON`: the authentic final-cut adapter, with no returned memory text;
2. `DLT_OFF`: the byte-identical child with that adapter removed;
3. `ACTIVE_LINKED_TEXT`: the already frozen strong text system at its
   pre-result `q/B` setting, with its unlimited persistent store; and
4. `FULL_SOURCE_TEXT`: every relevant source EVENT/LINK row, losslessly and in
   causal order, provided in context.

The source prefix for this assay must be small enough that `FULL_SOURCE_TEXT`,
the complete task/state, and the full `2048`-token output reserve fit under the
pinned context limit by tokenizer receipt. If they do not fit, the assay is
invalid; do not truncate the source or the actor. `ACTIVE_LINKED_TEXT` keeps
its already calibrated `q <= 16`, `B <= 8192` access as the deployable strong
opponent, while `FULL_SOURCE_TEXT` rules out a result manufactured by retrieval
misses.

Also run the already frozen exact-schema/text ceiling. It must solve the
targets; it is not ranked as a deployable system.

## 4. Predictive code readout

The reusable PCFL module consists of permutations over `6`, `4`, and `3`
relations. Freeze one public relation order. For each relation in turn, score
all still-legal remaining values and normalize their next-answer likelihoods.
One module therefore needs exactly

```text
(6+5+4+3+2+1) + (4+3+2+1) + (3+2+1) = 37
```

candidate continuations. The correct assignment's code length is the sum of
`-log2 p` under those finite normalized choices. Call the eight-module total
for condition `c`, root `r`, and continuation `z`:

```text
C[r,c,z] = total predictive bits for all 104 fresh relation assignments.
```

This is a valid **conditional prequential code**: it asks how many residual
bits the fixed model state needs for genuinely new outcomes. It is not total
storage rate because the adapter bytes are conditioning side information.
Always report, separately:

```text
adapter package bytes
packed witnessed-graph bytes
active-text persistent bytes
returned-memory tokens
candidate-scoring and actor inference work
```

The independent twin is scored from the identical probabilities. It therefore
tests whether savings follow the registered structure rather than generic
confidence or answer priors.

## 5. Behavioral and causal readout

After predictive scoring is sealed, run `16` fresh action tasks per root whose
unique legal action requires one or more of the withheld target relations.
There is no exact target answer in any memory carrier. Invalid, missing, late,
or illegal actions are zero.

Add one inference-only relation-cue twin: replace the public structure cue by
its predeclared paired cue while leaving all noncausal surface fields fixed.
The registered correct action changes. This is not a new fit and does not
expose an answer. It tests whether the learned behavior follows the relevant
relation rather than a memorized surface routine.

## 6. Prospective pass gates

All gates use roots as the independent units. The `8` modules, `104`
relations, candidate choices, and `16` actions are nested observations.

### Assay validity

- target/source byte custody and exact target non-occurrence are `1.00`;
- structured and independent target decks match on every declared marginal;
- the exact graph and explicit-schema/text ceiling each solve at least
  `15/16` action tasks on every valid root;
- all four neural conditions receive the frozen, sufficient task/output
  allowance; and
- every DLT state used passes the inherited task-retention and canary gates.

### Parametric predictive reuse

Let `R_code[r] = C[r,DLT_ON,STRUCTURED] / C[r,DLT_OFF,STRUCTURED]`.
Require:

- `R_code < .80` on at least `12/16` roots;
- the root-bootstrap one-sided 95% upper bound on mean `R_code`, with failed
  roots filled as `1`, is below `.80`;
- on `INDEPENDENT`, the corresponding ratio is at least `.95` on the root
  mean and its structured-minus-independent saving has a one-sided 95% lower
  bound above zero; and
- no usable false target row is emitted on absent/wrong-root probes.

These gates reject a generally sharper or more confident adapter that did not
learn the registered reusable relation.

### Useful reuse

- `DLT_ON - DLT_OFF` exact action utility has point estimate at least `.10`
  and a one-sided root-level 95% lower bound above zero;
- the relation-cue twin redirects at least `12/16` registered actions in at
  least `12/16` roots, with no increase in illegal-action rate above `.05`;
  and
- earliest-cohort retention remains within the already registered `.05`
  adverse bound.

`DLT_ON` beating `ACTIVE_LINKED_TEXT` is a separate, stronger result. Claim a
carrier advantage only if the strong baseline certificate passed unchanged,
the root-paired utility difference is at least `.05`, and its one-sided 95%
lower bound is above zero. Matching or losing to text does not erase a valid
parametric-reuse result; it only removes superiority language.

## 7. Cost and stop rule

The main predictive panel is exactly:

```text
16 roots * 8 modules * 37 candidates * 4 conditions = 18,944
candidate-scored continuations

16 roots * 16 tasks * 4 conditions = 1,024
behavioral generations
```

The independent twin reuses the same probabilities and adds zero calls. The
cue twin adds only its predeclared action generations and must be itemized in
the final manifest. There are **zero new fits** and zero additional childhood
or lifetime collection.

Profile one excluded-root sentinel before confirmation and bind an exact
request/token manifest. Hard-stop if the complete assay projects above
`4 aggregate A40-hours`; do not shrink reasoning tokens, delete a condition,
or reduce target difficulty after seeing a result. In that case defer the
assay rather than delaying the main PCFL campaign.

## 8. Paper disposition

This belongs as a **bounded secondary result**, ideally one main-paper panel if
it passes and the appendix otherwise. The headline remains own-experience
connected carriage, traversal/expansion, lifetime improvement, and the strong
memory comparison.

Promote one abstract clause only if all predictive-use gates pass on the
powered roots. The maximum sentence is:

> After ordinary experiential SLEEP, the fixed adapter assigned shorter
> conditional predictive codes to previously unseen outcomes generated by a
> learned cross-module relation and improved actions that required those
> outcomes; the saving disappeared on matched independent continuations and
> with the adapter removed.

Do not say that the LoRA, whole life, or organism is physically compressed.
Do not say the child discovered a universal schema. Do not call a text-memory
loss saturation. If only exact seen-row recall passes, report storage. If new
outcome action passes but the code gate fails, report reusable generalization
without compression. If code savings pass but action does not, report a
predictive diagnostic, not useful experiential knowledge.

The existing supplied-schema/residual sidecar remains optional future work. It
can measure exact two-part semantic-code bytes against packed and zstd-coded
graphs, but it answers a different question: prospective selection of a
supplied code. It should not replace this cheaper test of whether the ordinary
DLT adapter itself learned reusable structure.

## Evidence inspected

- `AGENTS.md`
- `research_loop/COORDINATION.md` through the 2026-09-13 PCFL/writer entries
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_scalable_sleep_writer_bridge.md`
- `research_notes/analysis/2026-09-13_downstream_compression_and_strong_memory_gate.md`
- `research_notes/analysis/2026-09-12_smallest_honest_compression_claim_route.md`
- `research_notes/analysis/2026-09-12_baseline_compression_full_paper_watcher_audit.md`
- `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md`
- `research_notes/48_pcfl_stream_and_schema_design_v0.md`
- `research_loop/advisory/20260911_compression_rate_distortion_assay_fresh_v1.md`
- `research_loop/advisory/20260911_compression_rate_distortion_assay_fresh_v1_adversarial_critique.md`
- `research_loop/advisory/20260911_compression_rate_distortion_assay_repaired_v2.md`
- `research_loop/advisory/20260911_compression_rate_distortion_assay_repaired_v2_closure_review.md`
- `research_notes/2026-09-11_active_text_compression_design_adjudication.md`
