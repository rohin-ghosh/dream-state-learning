# S-stage authentic action--outcome source: adversarial design audit

Date: 2026-09-12 UTC  
Status: watcher-side design recommendation only. No builder-owned source,
model/tokenizer, adapter, GPU job, experiment, or external state was changed.

## Verdict

**REWORK the lived-mirror assay before S.** Its current target is the child's
success-selected final `ACT`. Because situation alone determines that target,
the writer can pass while ignoring the public outcome. Merely training a
second adapter after permuting outcome text does not repair the construct if
the direct action label remains recoverable from situation.

The smallest construct-valid replacement is a **balanced bidirectional event
write** made only from the child's actual initial action and the world's
actual public outcome:

```text
own action in opaque situation -> public outcome
                 SLEEP renders two views
forward:  situation + action  -> outcome
inverse:  situation + outcome -> action
```

Pair that TRUE corpus with an `OUTCOME_SHUFFLED` corpus built from the **same
admitted event identities and action fields**, changing only which public
outcome is bound to each event while preserving every supervised target
multiset. Exact balancing makes every constant, situation-only,
action-only, outcome-only, template-only, and order-only policy chance. TRUE
can then pass only by carrying the joint situation--action--outcome relation;
SHUFFLED contains the same marginals and dose but no conditional relation.

This is deliberately smaller than connected PCFL. A pass can establish that
an exact mechanically compiled view of authentic child action--outcome events
carried a seen-situation relation and changed later goal-conditioned action.
It cannot establish autonomous credit assignment, spontaneous reflection,
connected knowledge, discovery, generalization, retention, parenting,
increasing-lifetime learning, compression, or the whole organism.

## Why the current endpoint cannot answer the question

The ratified lived-mirror blueprint selects cases on which the child writes a
correct final action, then places that action directly in the supervised
target. Within a world, the mapping is:

```text
situation s0 -> final action a0
situation s1 -> final action a1
```

The masked context also contains the initial action and outcome, but neither
is necessary. A high-capacity learner may learn `situation -> final ACT`.
TRUE and outcome-shuffled variants can therefore behave identically even when
the public outcome contributes nothing. This is not repaired by matched token
counts, a spill panel, or opposite worlds; those rule out marginal and broad
habit explanations, not the direct situation label.

The source must remove the success-selected final action entirely. The only
action target in the inverse view should be the action the child actually
took, paired with the outcome it actually caused. Both possible actions must
occur under both possible desired outcomes in the SHUFFLED corpus, and both
desired outcomes must be queried for every situation at evaluation.

## Exact proposed source geometry

### Independent root

For each root `r` create:

- eight fresh opaque situation keys `k0..k7`;
- two visible legal actions, exactly `ACT: a0` and `ACT: a1`;
- two equal-token-length public outcome strings, `o0` and `o1`;
- a hidden orientation bit `b_k`, with exactly four zero and four one per
  root; and
- deterministic public law `outcome_index = action_index XOR b_k`.

Identifiers, orientation, source surfaces, generation seeds, row order, and
optimizer seed are independently predeclared per root. Situation identifiers
are disjoint across roots. The actions and outcome vocabulary stay common so
wrong-root mounts test whether the adapter learned a global habit.

The frozen child repeatedly sees one situation, the unordered legal action
set, and its own prior public trials for that situation. It chooses one strict
action; the environment returns one public outcome. There is no correct
action, reward, final-answer turn, evaluator replacement, hidden mapping,
parent advice, or admission bit in model-visible source text. The generic
instruction may ask it to explore both actions, but may not prescribe an
action or expose orientation.

All attempts are preserved. Give each key at most 16 opportunities. The root
is `SOURCE_INVALID` unless the child itself executes each action at least
twice for every key. Do not force, top up, substitute, or manufacture the
missing action.

### Admission

For every key, admit exactly the first two provenance-valid events for `a0`
and the first two for `a1`. Thus each root has exactly:

```text
8 situations x 2 actions x 2 occurrences = 32 admitted events
```

Admission depends only on action coverage and immutable provenance, never on
success, outcome value, a later answer, or evaluator preference. For every
admitted event bind the source prompt hash, child output hash, strict parsed
action, public environment response hash, situation, occurrence, chronology,
and engine/replay identity. Re-execution must reproduce the outcome.

Coverage is a hard source gate:

- exactly four admitted events per situation;
- exactly two events per action per situation;
- both public outcomes present per situation in TRUE;
- both orientation strata contain four situations;
- no invalid or evaluator-authored action; and
- all source attempts, including rejected/extra attempts, published in the
  audit projection.

This is a balanced subset of authentic events, not an unfiltered lifetime.

## TRUE and OUTCOME_SHUFFLED material

Close and hash the source ledger before deriving either branch. Both branches
use the same 32 event IDs, situation bytes, action targets, renderer indices,
source chronology, corpus order, masks, EOS count, optimizer steps, seed,
node, base bytes, and writer recipe.

For each situation, index the four admitted events as `(a0,0)`, `(a0,1)`,
`(a1,0)`, `(a1,1)`. TRUE retains the public outcome. SHUFFLED applies one
predeclared donor permutation within that four-row block so that each action
receives exactly one `o0` and one `o1`. It therefore:

- preserves exactly two `o0` and two `o1` tokens per situation;
- preserves every target-action count;
- preserves global and per-stratum outcome/action marginals; and
- makes action independent of outcome conditional on situation.

The permutation is frozen before any model output and reported as recipient
event ID -> donor event ID. Donor outcome is the only semantic field that may
change. The SHUFFLED branch is explicitly synthetic and may never be admitted
to a child lineage.

### Bidirectional SLEEP projection

Render four crossed training surfaces per admitted event: two forward and two
inverse. Across events, each surface index occurs equally with both actions,
both outcomes, and both orientation strata.

```text
forward masked context: situation k + executed action a
forward target:         public outcome o

inverse masked context: situation k + desired/public outcome o
inverse target:         ACT: a
```

The compiler performs only this registered reversible rendering. It does not
write a principle, infer a better action, select a success, or author a
replacement target. In inverse rows the action appears exactly once and only
in the supervised target. In forward rows the outcome appears exactly once
and only in the supervised target. Case IDs, mapping bits, correctness,
admission metadata, donor identities, and report labels never enter encoded
training text.

This yields exactly 128 training rows per fit. Under the current two-epoch,
batch-one writer recipe that is 256 optimizer steps, matching W0's dose. TRUE
and SHUFFLED must have identical encoded item counts, target-token multisets,
total/supervised token counts, target positions, EOS counts, and ordered
optimizer-step count. Outcome strings must be chosen by real-tokenizer
preflight to have identical length and boundary behavior.

## Frozen evaluation and estimands

Use four train-disjoint held renderings for each direction. Primary inverse
items cross `8 keys x 2 desired outcomes x 4 forms = 64` requests per
condition. Forward items cross `8 keys x 2 actions x 4 forms = 64`.
Generation and candidate scoring use prompt bytes and seeds shared across
OFF, TRUE, and SHUFFLED; no wall-clock text may enter a prompt.

For inverse item `i=(k,o,t)`, let `y_i` be the unique authentic action that
causes outcome `o`. For condition `c`, define:

```text
IBA_c = mean_k mean_o mean_t 1[strict_generated_ACT_c(i) = y_i]
ILM_c = mean_k mean_o median_t
        (log p_c(ACT:y_i | i) - log p_c(ACT:not-y_i | i))
```

Invalid, multiple, or truncated actions score zero. Define forward `FBA_c`
and `FLM_c` analogously, replacing action candidates with the two outcome
continuations under `(k,a,t)`.

The root-level causal contrasts are:

```text
delta_inverse_r = IBA_TRUE_r - IBA_SHUFFLED_r
delta_forward_r = FBA_TRUE_r - FBA_SHUFFLED_r
delta_ILM_r     = ILM_TRUE_r - ILM_SHUFFLED_r
delta_FLM_r     = FLM_TRUE_r - FLM_SHUFFLED_r
```

OFF does not enter the subtraction because it is common, but all
`TRUE-OFF` and `SHUFFLED-OFF` values are reported. The exact estimand is the
effect of preserving the within-event outcome binding in this fixed compiled
representation and writer recipe. It is not the effect of having more data,
different target counts, or a different training dose.

### Per-root gates

After integrity/source/oracle precedence, a root qualifies only if all are
true:

1. `IBA_TRUE >= .75` and `FBA_TRUE >= .75`;
2. `delta_inverse >= .20` and `delta_forward >= .20`;
3. `delta_ILM >= .50 nat` and `delta_FLM >= .50 nat`;
4. both desired outcomes produce opposite strict actions on at least 6/8
   situations in TRUE, so one situation-level action cannot pass;
5. at least 3/4 keys in each orientation stratum have positive TRUE-minus-
   SHUFFLED inverse and forward candidate margins;
6. an in-context GOLD view of the exact authentic events reaches inverse and
   forward BA at least `.90`, and exceeds OFF by at least `.20`;
7. strict legal-action validity is at least `.95` overall and `.90` per
   orientation stratum;
8. generic task value is at least `OFF - .05`; and
9. every new-situation, wrong-relation, no-situation, wrong-root, interface,
   and broad-spill gate passes.

Use the W0 interface/locality thresholds unchanged where their measurement
applies: absolute legal-ACT-rate change and per-key normalized candidate TV
on a neutral surface no greater than `.05`. A TRUE adapter that stores the
forward relation but cannot change inverse/native action receives the narrow
label `FORWARD_RELATION_ONLY`; it does not pass S.

The same-semantic text carrier is an assay-validity diagnostic, not a claim of
parametric superiority. A target-blind lookup by situation must return all
four admitted events, cite them exactly, and reach at least `.90` inverse and
forward BA. If GOLD/TEXT cannot expose the relation, the query/interface is
invalid rather than evidence against LoRA.

## Minimum roots and inference

Three roots are enough only for a **developmental repeatability gate**. With
three independent paired fits, even all three effects positive give a
one-sided exact sign probability of `1/8 = .125`; that cannot carry a
paper-facing population claim.

Use this staged rule:

1. Run one prospectively frozen source root and its TRUE/SHUFFLED pair.
2. Only if it qualifies, finish two more disjoint roots. Advancement to the
   connected relay requires all three `delta_inverse` and `delta_forward`
   signs positive, at least two roots meeting every numerical gate, and no
   interface/source failure. Call this `S_THREE_ROOT_FEASIBILITY`, not
   confirmatory evidence.
3. For a paper sentence, extend the identical frozen assay to **eight total
   independent roots**. Eight is the smallest practical count that tolerates
   one directional miss while retaining an exact one-sided sign result:
   `P(Binomial(8,.5) >= 7) = 9/256 = .03515625`.

The paper gate requires at least 7/8 roots positive in both forward and
inverse contrasts, root-equal mean TRUE BA at least `.75` in both directions,
root-median deltas at least `.20`, the exact paired sign/randomization result
at most `.05`, and all root-level source/oracle/interface validity gates.
Report root-level values and intervals; prompts, forms, decodes, and keys are
nested observations, not extra independent samples. No failed root may be
replaced.

If the desired wording is restricted to “three tested micro-world roots,”
the three-root result can be reported descriptively. It must not be written as
a general writer reliability result.

## Shortcut, leakage, and falsification suite

Before any fit, prove by enumeration on TRUE and SHUFFLED train/held tables:

- constant, situation-only, action-only, outcome-only, renderer-only,
  occurrence-only, source-order-only, and declared pairwise nuisance policies
  have BA exactly `.50`;
- `situation x action` is the unique registered forward oracle and
  `situation x outcome` the unique inverse oracle in TRUE;
- both joint oracles fall to `.50` in SHUFFLED;
- action and outcome targets are balanced globally, per situation, per
  renderer, and per orientation stratum; and
- target-visible byte length, token length, prefix/suffix, choice order, and
  padding do not encode orientation or target.

Also require:

- raw-byte scanning of every system/source/compiler/train/eval prompt for
  hidden mapping, event IDs, correctness, donor identity, answers, historical
  compiler routines, and report labels;
- full source chronology and outcome replay from the public engine;
- cyclic wrong-root mounts and a target/action-marginal audit;
- outcome-token swap at read time, which must redirect TRUE's preferred
  action rather than preserve one situation-level action;
- train/order/template permutation tests in CPU fixtures;
- exact candidate-token masks and no target-boundary-straddling token;
- fresh process per fit/read, complete cache/context deletion, and no adapter
  stacking; and
- branch quarantine: neither TRUE nor SHUFFLED artifact may become a nursery
  or paper-child ancestor.

The most important falsifier is simple: if SHUFFLED matches TRUE, the writer
did not need the authentic action--outcome binding. Do not explain that result
away as insufficient downstream transfer while retaining an outcome-learning
claim.

## Stop rules and labels

Order is fixed:

1. W0 must first seal an actual selective-writer pass; W1 must then establish
   replay-supported OLD+NEW coexistence. An infrastructure abort is neither.
2. Any construction, source-coverage, provenance, replay, token-geometry, or
   shortcut failure is `S_NOT_RUN` or `S_SOURCE_INVALID`; do not fit.
3. GOLD/TEXT failure is `S_ASSAY_INVALID`; do not interpret adapter output.
4. Nonfinite loss, missing steps, or shared fit-canary failure is
   `S_OPTIMIZATION_INCONCLUSIVE`; no scientific result.
5. Interface, generic non-harm, or broad-spill failure is
   `S_WRITER_UNUSABLE`, even if TRUE beats SHUFFLED.
6. Forward-only success is `S_FORWARD_RELATION_ONLY`.
7. TRUE action success without a TRUE-minus-SHUFFLED margin is
   `S_ENDPOINT_OR_PRIOR_WITHOUT_OUTCOME_CAUSALITY`.
8. A qualifying three-root block is `S_THREE_ROOT_FEASIBILITY`.
9. Only the frozen eight-root conjunction is
   `S_AUTHENTIC_BINDING_ACTION_PASS`.

After outputs exist: no dose, prompt, outcome vocabulary, root, threshold,
renderer, seed, admission count, or compiler change; no retry-until-pass; no
pooling a failed root away. A source failure may motivate a new version, but
its identities are burned and its outcome is preserved.

## Staged GPU cost

These are planning bounds to replace with measured W0 throughput before an
execution manifest:

- each arm uses 128 rows and 256 steps, the same nominal fit size as one W0
  fit;
- one root is two fits, TRUE and SHUFFLED;
- three-root feasibility is six fits;
- eight-root paper confirmation is sixteen fits total.

Using W0's conservative three-A40-hour envelope for four fits plus a much
larger 1,504-request suite, budget at most **1.5 A40-hours per S root**,
**4.5 A40-hours through three roots**, and **12 A40-hours through eight**,
then add a 25% operations margin for a hard planning cap of **15 A40-hours**.
Do not treat this interpolation as measured runtime. Recompute after a real
W0 fit, bind actual forward/inverse request counts, and stop result-blind if
the cap is exceeded.

Parallel wall time can be short without changing the unit: each root's paired
fits may occupy two GPUs, and eight roots may occupy sixteen GPUs. Roots—not
GPUs, fits, prompts, or decode seeds—remain the independent units.

## Exact claim boundary

If the eight-root gate passes, the strongest warranted sentence is:

> Across eight predeclared opaque micro-world roots, preserving the authentic
> within-event action--outcome binding in a fixed bidirectional SLEEP rendering
> improved held-rendering outcome prediction and goal-conditioned native
> action relative to a marginal- and dose-matched outcome-shuffled write.

Add explicitly: the situations were seen during the source phase; admission
used a balanced subset of the child's own actions; SLEEP used a registered
reversible compiler; and the comparison does not show autonomous
credit-assignment discovery or cross-situation generalization.

This closes only the authentic-source arrow:

```text
own executed action + public outcome -> binding-sensitive parametric use
```

Connected formation/traversal/expansion remains M; retention remains W1/L;
increasing-lifetime improvement and strong-baseline superiority remain L/B;
compression remains C.

## Sources inspected

- `research_notes/2026-09-12_end_to_end_goal_closure_synthesis.md`
- `research_notes/2026-09-11_decisive_evidence_path.md`
- `research_loop/changes/chg_20260911_lived_mirror_writer_gateway_v1/`
- `research_loop/plans/rml_paper_claim_audit.md`
- `research_loop/advisory/count_native_writer_source_rows.py`
- `organism_v6/sleep_compile.py`
- `organism_v6/multikey_writer_gateway_simple.py`
- `research_notes/analysis/2026-09-12_w1_cumulative_replay_readiness_audit.md`
