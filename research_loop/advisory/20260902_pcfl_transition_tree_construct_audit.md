# PCFL-Stream transition-tree construct audit

**Date:** 2026-09-02

**Status:** read-only scientific advisory preserved at the owner's request. This
is not an architecture consensus, ratification, implementation scope, model or
GPU authorization, or scientific result.

## Verdict

PCFL-Stream as drafted is a strong fixed-source causal-memory microscope, but
not yet a valid self-learning-agent benchmark. Its defensible current construct
is fixed-source acquisition, retention, and clean-base composition of
life-specific causal atoms. It does not identify learned connected-memory
organization, policy-selected experiential learning, higher-order compression,
or the complete action--experience--memory flywheel.

| Construct | Current validity |
|---|---|
| Action--outcome experiential learning | Partial. Facts originate in interventions, but a scripted common source deck tests off-policy learning from experience, not action-selected experience. |
| Connected memory | Not identified. Local atoms plus a clean-base planner can solve the targets; the minimal J/P consensus explicitly shows that full semantic facts remain sufficient after explicit graph-edge deletion. |
| Goal-conditioned multi-hop action | Partial. A3 executes several actions, but its solution is chiefly a join over preparation, site, and route lookup tables under a supplied grammar. Depth 1--4 is not operationally defined. |
| Lifetime growth | Partial. Independent cohorts increase storage demand. Without paired earlier/later snapshot tests, this is sustained lookup capacity rather than demonstrated growth in capability. |
| Full online flywheel | No. Evaluation actions never change later source experience, recompilation, or later return. |

The preparation/site/route design is therefore too close to dressed-up
key--value QA for a connected-memory or multi-hop-action headline. Sequential
execution improves the behavioral surface, but it does not change the fact that
the decisive computation is normally retrieval of a few independent mappings
followed by a supplied planner grammar.

## Smallest construct-valid replacement

Replace the predicate-join world with a transition-tree world.

Each cohort is one public depth-4 binary transition tree containing 15
persistent internal state classes and 16 persistent leaf classes. Every
internal state exposes two persistent action labels. One independent hidden bit
per internal node swaps which action label leads to the left rather than right
child, so each cohort contributes exactly 15 fresh causal bits. Cohort bits are
independent in the scale-only condition.

A counterfactual twin flips all 15 bits. State names, action-label inventories,
target bytes, goal bytes, action caps, event counts, action counts, and marginal
outcome counts remain identical. Only the action-to-child bindings and hence
the correct plans change.

The source policy visits every internal node on fresh practice specimens and
executes both available labels in a presealed balanced order. A first pass
permits a target-independent transition proposal. A later pass on different
fresh specimens supports or contradicts it. Schedule, reset states, and action
choices are target-blind and outcome-blind; realized outcomes never select a
later action, target, cohort, or retained item.

The ordinary public source event is only:

```text
current_state, chosen_action -> ARRIVED(next_state), cost
```

It never emits a transition rule, edge label, proof, target path, support label,
or answer. The only legal semantic memory atom is one witnessed transition:

```text
(parent_state, action_label, child_state, public provenance)
```

At evaluation, a fresh specimen receives a public start state and goal leaf.
The model sees the current state, the two currently available action labels,
the goal, the last public outcome, and remaining budgets. `MOVE(label)` changes
the public state one edge at a time. `COMMIT` succeeds only at the goal. The
tree is directed, so a wrong branch cannot be repaired within the minimal cap.
No opaque `COMMIT(plan)` or plan-string answer is scored.

The target-blind reader accepts only `INCIDENT(public_state)` and returns one
immutable incident transition atom or `NOT_FOUND`. Backward reconstruction from
a goal leaf therefore takes one read per edge. Every query after the first uses
a semantic state first introduced by the preceding read. This creates genuine
bounded traversal of connected transition content without opaque random
pointers. Any open-versus-recurrent advantage remains explicitly a property of
this pinned reader API, not a general theorem about recurrence.

This replacement tests a learned transition model used for action. It still
does not prove that DREAM autonomously discovered a special graph data
structure: a flat set of correctly indexed transition atoms may suffice. The
honest phrase is connected semantic content used compositionally unless an
edge-specific intervention holding leaf facts fixed establishes more.

## Depth and era mechanics

- **D1:** the start is the goal leaf's direct parent. Success requires one
  learned transition followed by `COMMIT`. With uniform independent binding,
  target-only value is exactly `1/2`. D1 is primarily an installation/read
  diagnostic.
- **D4:** the start lies exactly four edges above the goal. Success requires
  four ordered transition choices followed by `COMMIT`. Target-only value is
  exactly `1/16`.
- **Depth certificate:** depth is the independently enumerated unique shortest
  chain of life-specific transition bindings. It is not prompt steps, query
  count, cited-edge count, or padded environment actions. Every D4 item must
  have one successful path of length four and none of length less than four.
- **Fixed budget:** all conditions receive the same maximum query, resolver,
  and action cap appropriate to the declared depth surface; actual work is
  reported. A deterministic eligible-memory controller must score one on every
  item under those exact caps before model use. Physical action length is
  reported separately from epistemic depth.
- **New:** every decisive edge was introduced since the preceding checkpoint.
- **Old:** every decisive edge belongs to the earliest cohort quartile and its
  last public support lies outside the native model-visible window.
- **Cross-era D4:** exactly two decisive edges come from an old cohort and two
  from the recent cohort, joined by a forced public, non-memory-bearing
  handoff. Removing either era makes success impossible.
- **Invalid cell:** D1 crossed with cross-era is structurally impossible and is
  declared absent prospectively rather than manufactured or silently omitted.
- **Primary surface:** D1 and D4 are the primary endpoints. D2 and D3 may be
  sparse mechanism diagnostics unless independently powered.

Pair each target with a second target in the same world and from the same start
but with a different goal leaf that requires a different first action. This
goal twin directly tests goal conditioning: a cached state policy cannot solve
both.

All target, depth, age, and cohort allocations must be sealed before source
support, compiler success, or arm outcomes exist. Introduced, supported,
compiled, readable, and action-usable mappings are separate denominators.
Unsupported, uncompiled, duplicate, malformed, timeout, and runtime-failed
items remain in their assigned world-life denominator.

## Lifetime estimands

Do not infer learning from a later endpoint or from more lifetime tokens. Use
paired snapshot interventions on the same presealed targets:

```text
acquisition_k = V(M_k, T_new,k) - V(M_k-1, T_new,k)

retention_k   = V(M_k, T_old) - V(M_acquisition, T_old)

cross-era_k   = V(M_k, T_cross,k)
                versus old-cut, new-cut, and both-cut forks
```

Capability growth means that additional presealed target families become
solvable after their evidence arrives while old-target value remains within a
predeclared noninferiority margin and cross-era D4 construction remains above
its causal controls. Report new acquisition, old retention, and cross-era
construction separately; an aggregate cannot compensate for forgetting or
stalled acquisition.

Count unique introduced and supported causal bits, not tokens, repeated
evidence, replay views, paraphrases, or distractors. Independent cohorts test
finite-rate accumulation and retention, not semantic compression. Use
"compiled per-life parametric memory" unless exact serialized incremental bits
and all information-bearing external state grow sublinearly relative to the
minimal sufficient statistic at predeclared noninferior action value.

## Decisive interventions

1. **World-by-memory twin factorial.** Evaluate `H/M_H`, `H/M_tau`,
   `tau(H)/M_H`, and `tau(H)/M_tau`. Matched memory should succeed; crossed
   memory should follow the counterpart plan and fail in the actual world.
2. **Lagged snapshot.** `M_k-1` must fail new-cohort targets that `M_k` solves.
   This is the direct acquisition intervention.
3. **Complete decisive-binding cut.** Remove every route carrying one
   environment-precertified required transition. For text, remove all
   equivalent records, candidates, indexes, and caches. For LoRA, use a paired
   binding-deleted or twin-trained adapter; deleting a displayed citation is
   not a weight intervention.
4. **Matched sham cut.** Replace an equal-sized unused transition. It should
   not reduce action value.
5. **Outcome-binding derangement.** Permute action--outcome bindings within
   cohort while preserving action counts, outcome counts, chronology bins,
   interface shapes, and training exposure.
6. **Goal twin.** Change only the public goal and require the first divergent
   action and subsequent trajectory to follow the new goal.
7. **Execution necessity.** Constructive credit requires the correct public
   state trajectory and terminal outcome, not merely a reported plan,
   plausible citation, or final action.

Report intervention effects both unconditionally and among authentic-memory
successes. Mere action change is insufficient: twin substitution must redirect
behavior toward the twin-valid plan, and cuts must reduce value relative to
matched sham cuts.

## Falsifiers and abandonment conditions

- A lagged snapshot solves new targets: acquisition is leaked or prior-driven.
- Wrong-twin or binding-shuffled memory preserves action value: authentic life
  bindings were not causally used.
- Changing only the goal does not redirect the decisive action: behavior is
  not goal-conditioned.
- A D4 target has a shorter successful path, or one legitimate record closes
  its plan: multi-hop construction is not identified.
- A complete decisive-binding cut does not reduce value relative to a sham
  cut: the cited memory was not necessary.
- Full semantic facts with connection metadata removed match the claimed
  connected-memory system: learned link or graph organization is unnecessary.
- Raw episodic recurrent RAG or an exact public transition graph matches or
  dominates compiled memory on the registered resource frontier: there is no
  compiled-memory moat.
- Recognition-assisted LoRA loses its advantage when candidate/index bytes and
  work are counted: the condition is an external enumerator plus reranker, not
  parametric recall.
- Unique causal bits plateau while tokens grow, or post-native checkpoints
  require filler or repeated evidence: there is no developmental scale axis.
- New acquisition stalls or old value collapses: there is no continuing
  learner across the tested range.
- Retained information or adapter capacity grows linearly while the report
  says compression: the result is storage, not compression.
- A named baseline continues improving under its legitimate capacity/resource
  policy: no saturation claim is permitted for that baseline.
- The compiler merely canonicalizes visible transitions and compiled memory
  does not beat raw episodes: DREAM contributes no demonstrated mechanism.
- The intended headline requires memory-directed evidence acquisition: abandon
  fixed-source PCFL as the primary benchmark or add a separately ratified
  on-policy randomized-memory-clone study in which memory changes information-
  seeking actions, those actions change public evidence, and later memory and
  return improve.

PCFL should be retained only as a finite, synthetic, fixed-source causal
lifetime benchmark unless an on-policy and externally validating rung is added.
If the intended paper claim remains that a self-learning agent broadly beats
state-of-the-art agents over increasing lifetimes, PCFL-Stream should be
abandoned as the sole paper benchmark.

## Authority boundary

This advisory records a construct-validity opinion only. The reviewed
`chg_20260902_pcfl_stream_paper_target_v1` intake remains at
`awaiting_consensus`, and the minimal J/P consensus remains
`human_required`. Nothing here authorizes editing or implementing a generator,
writer, memory substrate, resolver, baseline, evaluator, or analysis; making a
model, provider, network, training, or GPU call; selecting confirmation
thresholds or outcomes; promoting a stage; or stating a scientific result.
Exact human ratification, a separately bound execution scope, pre-GPU tests,
and fresh independent review remain mandatory under `AGENTS.md`.
