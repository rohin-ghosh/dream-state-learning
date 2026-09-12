# Fresh audit of the committed Level-1 conditional corpus

**Date:** 2026-09-12  
**Scope:** committed `organism_v6/conditional_behavior_corpus.py` and
`tests/test_conditional_behavior_corpus.py` at source commit `5f6e1f1d`, read
against the current Level-1 PROSPECT+REVISE design and the adjudicated
Q0-before-Level-1 ordering. No builder code, coordination file, VM file, model,
GPU process, or job was changed or inspected.  
**Validation:** the 41 committed conditional-corpus tests pass locally. That is
CPU source evidence only.

## Verdict

**REWORK the material before any Level-1 GPU fit.** The paired truth tables,
AUTH/DERANGED target swaps, counterfactual twins, strict parser, provenance
labels, train/dev template separation, group-preserving schedule, and
target-token parity machinery are mostly strong. However, the visible case
identifier leaks a latent construction coordinate for REVISE. The current
panel therefore admits a perfect train-to-dev shortcut that does not compare
the explicitly stated expected and observed outcomes.

Even after that source repair, this commit is **not an executable Level-1
experiment**. It deliberately contains no model runner, OFF panel, locality or
interface panels, interaction reducer, composition dialogue panel, or L1
decision function. More importantly, the current ordering requires the
adjudicated Q0 complementary conditional-writer gate to pass first. The source
may remain a CPU candidate while Q0 is resolved; it must not be fitted merely
because its unit tests and tokenizer audit pass.

## 1. Blocking semantic shortcut: the visible REVISE case number reveals `expected`

`_square` renders an identifier such as
`r0-dev-revise-02` directly into every prompt. For REVISE it also fixes

```text
expected = local_outcomes[0]
local_outcomes rotation = floor(square / 2) mod 2
```

The train and dev splits both reuse square suffixes `00..07` under the same
rule. The literal strings differ by `train` versus `dev`, so the current set
disjointness tests pass, but the informative numeric suffix and its meaning are
shared across splits.

I enumerated finite lookup policies from the committed source for every root.
For AUTH, on both train and dev, the key

```text
(numeric square suffix, OBSERVED, PRIOR action)
```

predicts the complete joint REVISE target
`(COMPARE, POLICY, NEXT)` with accuracy **1.000**. The same construction gives
1.000 on the registered complementary DERANGED map after complementing the
decision. By contrast, the committed audit only checks `observed_only`,
`prior_action_name`, `template`, and repeated batch slot separately. It never
checks the visible partial instance identifier or its combinations.

This shortcut passes the important-looking tests:

- outcome twins, because changing `OBSERVED` changes the lookup;
- prior-action twins, because changing `PRIOR` changes `NEXT`;
- all four response fields and strict syntax;
- held template families, because the square-number rule is unchanged; and
- AUTH/DERANGED redirection, because either map can learn the same shortcut
  with an opposite final decision.

It can therefore satisfy the present Level-1 endpoint without using the
explicit `expected` outcome in `PRIOR: PREDICT ... -> expected`. This is target
leakage through the generator, not merely a weak baseline.

The test `assert row["id"] not in row["context"]` does not close it: the full
corner/view `id` is absent, but the shared `instance_id` containing the square
coordinate is present.

### Exact repair

Make REVISE a complete three-factor cube within each visible instance:

```text
prior action x expected outcome x observed outcome
```

Equivalently, cross `expected` inside every public `instance_id` rather than
fixing it from the square number. Four eight-corner cubes give the existing 32
dev rows and 16 outcome/prior-action pairs; matching view replication can keep
the 64 training rows. The authentic response is then computed from the literal
`expected == observed` relation. Keep construction coordinates only in sealed
metadata, never in visible text.

Add a regression audit over at least these public-feature projections:

```text
instance_id
(instance_id, observed)
(instance_id, prior_action)
(instance_id, observed, prior_action)
```

The last policy must be at most `.50` on the full joint REVISE decision unless
the explicit expected outcome is included. Also make the public identifier an
opaque nuisance or omit it; do not expose root/split/operation/square
coordinates. Re-run AUTH/DERANGED per-batch token parity after the cube repair.

PROSPECT does not have the same defect: belief and goal are already completely
crossed inside each visible instance, so neither the identifier plus goal nor
the identifier plus belief determines the full decision. Reading one visible
binding plus the goal is sufficient, but that is a valid implementation of the
registered two-action problem, not leakage.

## 2. Source/corpus readiness after that repair

The following parts are suitable to retain:

- AUTH and DERANGED use byte-identical inputs and complementary coherent maps;
- each four-row optimizer group has a closed target-sequence permutation,
  including EOS under the audited native path;
- PROSPECT goal/belief twins and REVISE outcome/prior-action twins require the
  intended complete decision changes;
- invalid, incomplete, duplicated, or prose-contaminated outputs cannot rescue
  strict joint scoring;
- absent outputs abort a panel instead of disappearing from denominators;
- oracle-authored diagnostic provenance and the prohibition on treating this
  as child experience are explicit; and
- the module correctly returns `supplies_l1_verdict=False`.

Two source-level qualifications must remain visible:

1. The panel tests a small supplied conditional operator. It does not contain
   new Boolean structure at dev: the binary truth table repeats under held
   wording/identifiers. A pass is installed finite conditional form, not broad
   reasoning generalization.
2. The committed default outcome spellings `mip/zot` do not pass the recorded
   native Qwen token-length parity check. Coordination records a later CPU
   materialization using `fep/nup`, but those VM artifacts were outside this
   audit. Before a runner exists, bind the accepted label configuration and
   candidate hash in committed launch material rather than relying on API
   defaults or an uncommitted override.

## 3. The current training recipe is not yet licensed

`training_recipe` exposes the older v3 full-response target-only CE recipe:
rank 8, alpha 16, dropout `.05`, four epochs, batch four, and a caller-selected
learning rate. The handoff illustrates `1e-4`. That was a reasonable source
stub when the corpus was written, but it is not a current launch decision.

The adjudicated order is now:

```text
repaired L0 pass -> adjudicated Q0 complementary pass -> Level 1
```

Q0 uses a fixed `3e-5` pairwise decision objective and prospectively decides
whether a pairwise or full-vocabulary objective is carried forward. The prior
decision memo also requires that selected objective to be requalified on the
exact Level-1 surface. Consequently:

- do not release Level 1 from the L0 result or the native corpus audit;
- do not independently choose `1e-4` for Level 1;
- do not silently fall back to ordinary full-response CE if Q0 selects the
  pairwise objective; and
- if Q0 fails either complementary map, do not fit this corpus at all.

The clean repair is to leave this module as material/scoring only and mark its
recipe `WAIT_Q0_WRITER_SELECTION`. After Q0 passes, bind its selected
objective, rate, prefix convention, initialization, optimizer, dose, and
readout into a successor Level-1 runner. If the pairwise objective is selected,
define in advance how it supervises the multi-field PROSPECT and REVISE
decisions without conditioning later fields on a gold earlier field. A
complete-continuation AUTH-versus-DERANGED contrast from the common input-only
prefix is one nonleaking option; ordinary CE is a different recipe.

## 4. Readout/runner readiness: absent, by design

The committed code can construct, audit, encode, and score supplied strings.
It cannot execute or adjudicate Level 1. Before GPU use a successor must add:

1. a contemporary OFF state plus fresh, identical initialization receipts for
   paired AUTH/DERANGED fits;
2. native-token audits for **dev candidates and twin pairs**, not only the
   training corpus;
3. fixed fresh-process exact and dev generation with no retry and complete
   denominators;
4. a precise teacher-forced interaction formula. For a twin `(x0,x1)` with
   swapped complete candidates `(y0,y1)`, a nonleaking interaction is
   `[(log p(y0|x0)-log p(y1|x0)) + (log p(y1|x1)-log p(y0|x1))]`, with the
   normalization (`sum` or `mean`), EOS treatment, and `1 nat` threshold bound
   before outputs. Do not prefix gold `COMPARE`, `POLICY`, or `PREDICT` values;
5. the 16 no-phase/task controls and 16 unrelated native-interface cases,
   including OFF-relative validity and tag-spill reductions;
6. exact gate code for operation-specific surface/semantic counts, every
   `.75` physical-label/branch/template stratum, all four `14/16` twin gates,
   both own-map training gates, interaction, OFF deltas, interface, spill, and
   the all-roots noncompensatory rule; and
7. the separately constructed zero-training
   `PROSPECT -> outcome -> REVISE -> PROSPECT` dialogues. The current
   `composition.cases=[]` and `teacher_forcing_interface` are declarations,
   not assays.

`threshold_requirements` is intentionally incomplete. It also maps both
surface carriage and strict validity to the same `strict_surface` predicate:
the apparent `30/32` surface threshold is effectively `31/32` once `.95`
validity is applied. Preserve that explicitly or define two genuinely
different predicates; do not report 30/32 as 95%. For DERANGED, add own-map
strata explicitly rather than relying on the present AUTH-grounded binary
relabeling, even though the current balanced complement makes aggregate counts
numerically symmetric.

## Decision

The committed work is useful **preparation**, not wasted work: after the
REVISE cube/identifier repair it is a credible finite Level-1 material and
scorer. It is not ready for a scientific GPU fit, and no runner repair should
skip the upstream Q0 gate. The next execution remains Q0. Only a full
`P_AUTH + P_DERANGED` Q0 qualification licenses building and running the
repaired Level-1 successor.

