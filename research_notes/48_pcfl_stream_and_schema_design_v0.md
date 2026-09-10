# 48 — PCFL-Stream and prospective schema design v0

**Date:** 2026-09-01

**Status:** science design draft, not ratified and not executable. It extends
the PCFL-13 mechanism microscope in note 47; it does not modify the hash-bound
D0 proposal or authorize GPU work.

## 1. Why this extension is necessary

PCFL-13 contains only thirteen reusable mappings:

```text
6 preparation transformations + 4 site predicates + 3 route requirements
```

The complete hidden backbone is `log2(6! * 4! * 3!) ~= 16.66` bits. Once these
relations are supported, longer transcripts add delay, exposure, or distractors,
not new world knowledge. PCFL-13 can test the organism's causal chain and its
post-working-window retention, but not developmental learning, compression
scale, or continued acquisition.

The smallest honest scale repair is to repeat the same exact causal module under
fresh persistent public namespaces. The engine, actions, support rules,
counterfactual twins, and target-local Bayes oracle remain unchanged. Only the
number of genuinely new relations grows.

## 2. PCFL-Stream causal cohorts

A life contains ordered cohorts `c = 0..M-1`. Cohort `c` introduces:

```text
P[c,0..5]  fresh preparation-family labels, fresh permutation of 6 transforms
S[c,0..3]  fresh site-family labels, fresh permutation of 4 predicates
R[c,0..2]  fresh route-family labels, fresh permutation of 3 requirements
```

All labels persist for the rest of the life. Hidden assignments are independent
across cohorts in the scale-only condition. Entity/site/route/mission handles
remain fresh per episode. Natural-language skins are meaningful but carry zero
mutual information about assignments, and twin involutions apply independently
inside every cohort.

Each cohort contributes thirteen new one-edge causal relations. Coverage is
reported as unique supported mappings, not tokens, replay views, exposures, or
proposal counts. Repeating evidence for an old relation never counts as growth.

The source schedule is interleaved rather than cohort-complete: each geometric
life block introduces new cohorts, confirms some earlier proposals, and revisits
age-stratified old cohorts. This preserves chronological validation without
turning the stream into a sequence of fully solved mini-datasets.

## 3. Target cohorts

Every scale checkpoint freezes three target cohorts with fresh handles:

1. **new acquisition:** decisive relations all belong to cohorts introduced
   since the prior checkpoint;
2. **old retention:** decisive relations belong to the earliest quartile of
   cohorts and their last public support lies outside native context;
3. **cross-era composition:** at least one decisive preparation mapping is old
   and the site/route mapping is recent (or vice versa).

A cross-era mission can carry an old-cohort preparation tool into a recent
field site. Preparation semantics are tool-local and remain valid across field
locations; site and route predicates are destination-local. This makes the
join natural while preserving independent roots.

Every successful target still needs a causal memory-cut intervention: masking
all cited decisive atoms must change the action, and twin substitution must
produce the twin-valid action/set. Correct behavior without this intervention
is not constructive-memory credit.

## 4. Bounded retrieval and exact inference

The system must not replace a long context with an unbounded exhaustive reader.
The primary resolver queries only model-visible anchors. For a target kit, it
queries each of at most four visible preparation labels, the visible site
family, and the surveyed route family. Each anchor has constant incident degree.
It never queries a desired literal against all lifetime preparations, and the
reader never receives the goal, kit, hidden cohort, or target.

The generic A3 budget therefore permits six one-atom reads, twelve resolver
operations, and six world actions. These caps are independent of `M`. Candidate
enumeration, reader FLOPs, index bytes, and latency are plotted against `M`.
Any efficiency/scaling statement requires per-query candidate work to remain
sublinear in total lifetime atoms; an O(total-life) hidden scan is reported as
an external-search scaling result, not parametric recall.

The no-lifetime Bayes controller never enumerates the cross-cohort product.
Unrelated cohorts are behaviorally irrelevant to a target. Exact inference
marginalizes them and uses the same target-local quotient as PCFL-13—at most
480 A2 or 4,320 A3 hypotheses—plus the public source-selection prior. A
property test compares this factorization against small complete multi-cohort
products. Without that proof it is not called Bayes-optimal.

## 5. Native-context scale axis

Let `L_native` be the pinned model's maximum input tokens minus exact frozen
system prompt, goal, public state, workspace, operation history, and output
reserve. The tokenizer and serialization bytes determine it mechanically; it
is not a rounded marketing context length.

Calibration remains `0.5C/1C/2C` in PCFL-13. The developmental study uses at
least three checkpoints strictly larger than `L_native`, provisionally
`2L_native`, `4L_native`, and `8L_native`, plus one pre-native reference. Each
checkpoint must add new cohorts and unique mappings. If compute makes three
post-native points infeasible, the study cannot use curve, scaling, saturation,
or crossover language.

At each checkpoint report:

- raw lifetime tokens and source actions;
- introduced and supported unique mappings;
- minimal exact sufficient-statistic bytes;
- active/retained external-memory and adapter bytes;
- new, old, and cross-era action value;
- atomic read fidelity and constructive trace rate;
- writer/compiler/training/retrieval/resolver compute.

## 6. Capacity and baseline response surface

The paper-scale study compares PCFL-Stream against:

- no lifetime memory and exact accepted-deck Bayes no-memory;
- honest native context while the life fits;
- hierarchical summary/reflection memory;
- raw episodic RAG;
- native A-MEM linked memory;
- direct-QA LoRA;
- compiled text memory;
- recognition-assisted compiled LoRA;
- unaided generative LoRA read;
- authentic twin swap and composition-matched binding shuffle.

For text/graph/LoRA systems, sweep a small preregistered active-capacity or LoRA
rank grid rather than choosing a favorable point. Plot value versus lifetime and
retained bytes. If adapter rank/bytes must grow linearly with unique mappings to
preserve performance, the study may demonstrate parametric storage but not
fixed-substrate compression scaling. If a tiny explicit graph remains lossless
and dominates under resources, say so.

The developmental result requires all three simultaneously:

```text
continued new-cohort acquisition
+ preserved old-cohort value
+ above-baseline cross-era composition
```

A single aggregate score can hide catastrophic forgetting or stalled
acquisition and is never sufficient.

## 7. PCFL-Schema: the compression/generalization rung

PCFL-Stream with independent cohorts tests accumulating constructive knowledge;
it does not yet test whether lossy compression discovers a higher-order schema.
That requires a prospective, counterfactually paired meta-structure.

The minimal future rung samples a small hidden regime law linking public cohort
descriptors to a family of causal permutations. Several source cohorts expose
enough local mappings to propose a target-independent schema. Before a later
cohort is observed, DREAM must commit predictions for that cohort. The later
public outcomes support or contradict the schema. Evaluation then presents a
fresh sparsely observed cohort where local atomic memories leave one decisive
mapping unknown but the supported schema predicts it.

Required controls are:

- all local atomic memories without the schema;
- a schema written after seeing the evaluation cohort (leaked ceiling);
- descriptor/mapping counterfactual twins with identical marginals;
- a schema-binding shuffle preserving local memories;
- exact explicit symbolic schema versus text and LoRA transport;
- mask/twin-swap intervention on the cited schema atom.

The schema result is positive only if it improves fresh-cohort action beyond
atomic memory and the prediction was committed before confirmation. If atomic
memory matches it, no higher-order compression claim is earned. If the schema
only restates all local mappings, it is not compression.

## 8. Paper interpretation ladder

- **PCFL-13 pass:** the fixed organism can transform public experience into
  supported local relations and reconstruct them into multi-step action; text
  and LoRA transport are attributed separately.
- **PCFL-Stream pass:** the same organism continues acquiring, retaining, and
  composing genuinely new causal knowledge across post-native lifetimes under
  reported capacity/compute.
- **PCFL-Schema pass:** consolidation forms a prospectively verified lossy
  abstraction that improves action where local atoms are insufficient.
- **On-policy pass (later):** memory changes evidence acquisition; resulting
  experience changes later memory and action.

Only the last rung is the complete action--experience--memory flywheel. The
first three can still form a coherent systems/benchmark paper if their claim
boundaries remain explicit.

## 9. Hard falsifiers

- Unique mappings or minimal sufficient statistic plateaus while raw tokens
  grow: retention/exposure only, not developmental learning.
- Fewer than three strictly post-native checkpoints: no scaling curve.
- New-cohort value stalls or old-cohort value collapses: no continuing learner.
- Cross-era action survives memory-cut masking/twin substitution: no causal
  constructive-memory credit.
- Reader candidate work grows linearly with total-life atoms: no scalable
  parametric-read claim.
- Compiled LoRA fails direct-QA LoRA, native A-MEM, or same-corpus text under
  preregistered tests: no LoRA moat.
- Binding perturbations preserve gain: behavior was not conditioned on the
  authentic learned assignments.
- Required adapter capacity grows linearly: storage result, not fixed-capacity
  compression.
- Prospective schema adds no fresh-cohort value over atoms: no abstraction
  result.

## 10. Still deferred

This design does not authorize or establish on-policy evidence acquisition,
A4 durable revision, learned `phi`, long-sequence loop training, recurrent
versus batch sleep, standard-environment external validity, or unbounded
continual learning. Each remains a separately measurable paper stage rather
than rhetoric attached to PCFL.
