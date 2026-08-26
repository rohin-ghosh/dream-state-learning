# 37 — Semantic World v0.2: identifiable depth-growth diagnostic

Status: CPU prototype implemented on branch `semantic-world-v02`; no GPU model
result is claimed here. Semantic World v0 remains frozen for D0-D2 and for
reproducing the completed C-ladder.

## Why v0 D3 is retired

The original Blendyland tier had two independent observational shortcuts.

1. **Operator/parent underdetermination.** Across 500/500 audited seeds, the
   complete Blendyland role-to-color signature exactly equaled one ordinary
   land. `copy(land_X)` and `PIGMENT_UNION(parent_X,parent_Y,parent_Z)` therefore
   fit all observed and held-out cells equally. The FactorSolver recovered a
   unique parent set only after being handed `PIGMENT_UNION` as the operator.
2. **Same-role lookup.** V0 observes Blendyland for three anchors, exactly one
   per animal role. Once an agent has learned animal-role equivalence for D2,
   it can answer every held-out Blendyland cell by copying the observed target
   value for the same role. It never needs the operator or parent set.

Consequently every historical D3 score remains an underspecified diagnostic,
not evidence for or against higher-order dreaming. D0-D2 are unaffected.

## V0.2 mechanic

V0.2 preserves the ordinary six-land source world:

```text
animal role + land rotation -> primary/secondary source color
```

It changes only the meta layer. Colors carry pigment *amounts*, not only a
Boolean set:

```text
red=(1,0,0), yellow=(0,1,0), blue=(0,0,1)
orange=(1,1,0), green=(0,1,1), purple=(1,0,1)
```

The blend operator adds the vectors and reduces them to a primitive ratio.
This distinguishes, for example, red+orange = `(2,1,0)` (red-orange) from
Boolean union's plain orange. Three-parent outputs such as `(3,1,1)` become
red-brown and lie outside the ordinary-land family.

Before the temporal gap, a provenance-bearing color-workshop phase grounds
the complete answer vocabulary through labeled mixture samples. In the neutral
skin, for example, a record can state that one unit of one primitive token plus
two units of another is labeled `vexa00`. This is lived calibration evidence,
not an evaluator lookup: it appears for every baseline, contains no target
parents or target-to-answer assignments, and makes the arbitrary neutral vocabulary learnable
rather than relying on English color priors. Workshop and known-parent demo
evidence occur before the dispersion buffer; sparse animals and target-land
observations occur after it.

### Operator demonstrations

Two demonstration lands expose their source topology as lived world facts:

```text
streams from Candyland and Dandyland jointly feed Mixingland
```

All three anchor roles are then observed in each demonstration land. Their
rich pair-mixture outcomes reject these declared alternatives:

- ratio-preserving pigment sum;
- Boolean pigment union (the v0 rule);
- copying any parent;
- constant brown.

Only pigment sum survives both demonstrations. The feed relation is evidence,
not an evaluator query: it appears in the public lifetime with provenance and
is available equally to every memory baseline.

### Held-out target lands

There are twelve target blend lands. Each has:

- a provenance-bearing survey observation identifying it as the same
  jointly-fed/confluence class as the demonstrations, without revealing its
  sources;
- a hidden parent set containing two, three, four, or five source lands;
- observations for only two of the three animal roles;
- the third role completely absent from that target's lifetime; and
- one held-out goal using a distinct non-anchor animal of the missing role.

Four targets withhold each of roles 0, 1, and 2. Every evaluation animal is
used exactly once, producing 12 distinct `(target, hidden-role)` cases and 12
distinct answer ratios (majority floor 1/12). Parent counts are balanced 3/3/3/3
across sizes 2-5. Each parent set is selected so its two visible roles identify
it uniquely even when the search ranges over *all* source subsets of sizes 2-5.
No target signature matches an ordinary land or either demonstration land, and
no queried role has a same-role target exemplar. The twelve latent target cases
are randomly reassigned to surface target names per seed; a complete 180-cell
surface audit verifies that no target-name/animal-name pair has a fixed answer
across seeds in any skin.

The class observation is necessary in the neutral skin. Without it, a model
has no evidence that nonce target zones should share the demonstration-zone
operator; English names would silently provide that cue only to the aligned
arm.

The required computation is now:

```text
demonstration experiences
  -> infer one reusable additive blend operator
  -> use two visible target roles to infer a target's hidden parents
  -> recover the held-out animal's role from dispersed source experience
  -> derive its three parent colors
  -> apply the learned operator
  -> answer the unseen target role
```

This is the intended dreams-over-dreams chain: an operator memory is learned
from demonstrations, then reused to construct a target-specific structural
memory, then used by the thinker for a held-out consequence.

## Acceptance contract

`PYTHONPATH=. python3 -m lands.v02 audit --seeds 1000` must report:

- exactly one surviving declared operator: `pigment_sum`;
- exactly one parent set for every target using only its two observed roles;
- zero ordinary-source copy candidates for every target;
- zero observations of each target's held-out role;
- no exact goal cell in the lifetime;
- one public confluence-class observation per target, with no parent IDs;
- 12 goals, balanced four per hidden role, one per target and evaluation
  animal, with 12 distinct answers; and
- every legal answer token grounded in workshop/lived evidence, including in
  the neutral skin, without exposing which target takes which answer; and
- no fixed surface target/animal cell determines an answer across seeds; and
- 1,000/1,000 valid, byte-deterministic worlds with unique fingerprints.

The current implementation passes all of these checks. This is identifiability
within the declared operator family, not a claim that no arbitrary program
could interpolate the observations.

## Model experiment order

Do not resume unconstrained D3 prompt or model-scale searches on v0. The v0.2
ladder is:

1. **Gameability gate:** clean model, complete v0.2 public lifetime, generous
   reasoning prompt. Require materially above-floor hidden-role accuracy. If a
   strong model cannot solve it with all evidence visible, repair the game.
2. **Oracle-memory ceiling:** provide correct atomic operator, parent, role,
   and source-factor reads. Compare direct context composition with
   recognition-read composition.
3. **Fixed-memory substrate:** place the same oracle/dream corpus in context
   and in LoRA weights under the same recognition-read protocol. At small
   memory the expected equality is a control; scale beyond context is the
   substrate test.
4. **Oracle-free four-arm ladder:** no-gate / model self-check /
   self-check+dream-drift / perfect-gate ceiling. The exact solver remains
   offline and never changes proposals or stored memories.
5. **Depth-growth ablation:** one dream pass versus recurrent dreams over
   accepted/provisional memories. Report whether operator and target-parent
   memories appear, their provenance, depth, precision, and success@k.
6. Only after the mechanism works: seeds, skins, dreamer scale, lifetime
   length, batch-vs-stream crossover, and Action World.

## Required reporting

- operator proposal success and operator precision;
- target-parent success@k per target;
- hidden-role D3 accuracy and majority floor;
- same-role/copy shortcut audits;
- self-check confusion matrix and false-memory rate;
- prompt tokens, memory lines, recognition-query count, and model calls;
- context vs LoRA at a matched read protocol; and
- all results per seed and skin, never pooled alone.

## Deliberate boundaries

- D0-D2 stay on v0 until v0.2 is accepted; this module is initially a
  separate D3 diagnostic so old evidence remains reproducible.
- The feed topology for demonstration lands is observed. Discovering causal
  topology from actions belongs to Action World and is not conflated here.
- Text prompts remain the controller for Paper 1. Prefix/prompt tuning is a
  later amortization mechanism, not needed to establish the memory result.
- Weighted pigment names are a controlled semantic scaffold. Neutral and
  conflicting skins preserve the same latent ratios for the prior ablation.
