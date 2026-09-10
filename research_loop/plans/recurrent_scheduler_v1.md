# Draft fixed recurrent scheduler v1

Date: 2026-08-31 PT. Status: design-only. This is a transparent teacher/
ceiling scheduler for the amortized system, not evidence that scheduling has
been learned.

Architecture update: this target-blind breadth/depth scheduler remains the
intrinsic-dream control. The principal cyclic design in
`interleaved_organism_v1.md` adds bounded `frontier_breadth` slots after an
identical intermediate thinker in every arm. Thinker agenda changes selection
only and can never serve as evidence. The implementation must support repeated
`DREAM -> MEMORY -> THINK -> FEEDBACK` phases rather than terminating after one
sleep.

## Purpose

The v0 runner performs one WAKE per possibly multi-row episode and reactivates
only the newest eligible node. That can preserve at most one relation from a
15-row episode and creates a single recency chain rather than recurrent
branching. A failure under that schedule is ambiguous.

Counterfactual Confluence v0.3 should emit one atomic lived event per episode,
so one WAKE per event is sufficient for intake. The sleep schedule must still
support both breadth (revisit different memories) and depth (continue a useful
path) without consulting a goal, solver, hidden truth, or offline score.

## Fixed public/internal state

For every active node, maintain only:

```text
node_id, status, depth, created_cycle, last_reactivated_cycle,
reactivation_count, outgoing_live_edges, unresolved_question_links
```

All fields derive from the live append-only memory trace. No target answer,
parent truth, evaluator label, or goal-conditioned relevance enters selection.

## Schedule

1. Process atomic public episodes in temporal order.
2. Run one WAKE proposal per event.
3. After every four WAKE events, run two REACTIVATE proposals.
4. After the lifetime, run a fixed 32-step sleep budget.
5. Alternate trigger selection:
   - **breadth step:** select the active supported/unresolved node with the
     smallest `(reactivation_count, last_reactivated_cycle, created_cycle,
     node_id)` tuple, prioritizing nodes linked to unresolved questions;
   - **depth step:** if the previous reactivation created a valid local child,
     select that child; otherwise fall back to the breadth rule.
6. A contradicted, malformed-check, or superseded node is never a trigger.
7. The triggering node is always included in bounded retrieval. Other nodes
   use the declared public lexical/typed retrieval rule.
8. A duplicate semantic edge is logged and consumes its call budget but cannot
   create a node, depth, or support. A failed branch does not silently gain
   another call.

This alternation is search-tree-like, but it is not called MCTS: it has no
learned value, reward backpropagation, or visit-dependent upper-confidence
rule. It is a deterministic breadth/depth recurrent expansion schedule.

## Matched conditions

The principal `self_check_drift` and its `no_gate_drift` false-memory control
share exactly the same WAKE and REACTIVATE opportunities. Self-check calls are
reported separately. `*_no_drift` removes reactivation and is a component
ablation, not total-compute matched. A separate sensitivity reallocates the
removed reactivation budget to additional duplicate-guarded WAKE/reflection
calls; it must not fabricate new experience.

## Required accounting

Publish:

- scheduled, attempted, parsed, accepted, duplicate, malformed, and PASS calls;
- trigger selection reason (`breadth`, `depth_child`, `breadth_fallback`);
- trigger counts and fraction of eligible nodes reactivated at least once;
- reactivation depth transitions and supported-lineage depth;
- unresolved-question coverage and closure;
- calls/tokens per condition, including self-check overhead;
- exact deterministic replay of every scheduled trigger.

The contract must reject a missing, extra, reordered, or substituted trigger,
not merely a malformed reactivation record.

## Development gates

Before GPU execution:

1. CPU fixtures prove deterministic schedule replay and breadth/depth
   alternation under ADD, REVISE, OPEN_QUESTION, PASS, duplicates, and
   contradictions.
2. Every eligible node in a small fixture receives a breadth opportunity
   before any node receives a second breadth opportunity.
3. A valid child can extend its parent on the following depth step, while a
   failed/duplicate child cannot hijack the depth trigger.
4. Removing or reassigning a trigger, call, status event, or corpus node fails
   the deterministic artifact audit.
5. The Counterfactual Confluence public stream is atomic and the declared
   total dream/self-check budget fits the selected GPU/time budget.

The learned LOOP adapter may later imitate or improve this trajectory. Until
then, report the scheduler as hand-specified process scaffolding.
