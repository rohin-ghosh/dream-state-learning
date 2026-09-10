# RML-G1 selected-slice control-ceiling audit

Date: 2026-09-04

## Finding

The ratified G1 contract conflates two different quantities for `ATOMS_REC`:

1. an empirical integer gate requiring the pinned model to score 0/2; and
2. a pre-dispatch claim that the selected two-side P slice has an exact
   information-theoretic success capacity of 0/2.

The second quantity is impossible in the unchanged D0 construction. For every
publicly indistinguishable P H/twin pair, either side's certified nine-action
plan is a fixed visible-policy action sequence. Running the H plan on the two
sides yields `(success, nonsuccess) = (1, 0)`. Therefore the best fixed-policy
capacity is at least 1/2, never 0/2. D0's existing `1/4` P result ranges over
four valve completions and cannot be transferred to the selected two-side
slice.

The same audit found that R03 does not permit target-derived GOLD construction:
the GOLD/ATOMS/TWIN stores must be built from the frozen public source before
pair, target, side, or parent selection. Passing `TargetSpec.transforms`,
`TargetSpec.valve_truth`, or `useful_pairs(TargetSpec)` into a gold builder is
therefore a leak, not an implementation choice.

## Narrow repair proposed

- Keep the exact 18-trajectory roster, 234 registered opportunities, all
  prompts, model/runtime/resource limits, all causal interventions, the
  empirical `ATOMS_REC = 0/2` pass predicate, and the claim firewall unchanged.
- Replace only T03's impossible pre-dispatch `ATOMS_REC = 0/2` capacity claim
  with an exact enumeration of the selected arm's true visible-policy capacity,
  expected to be 1/2, including a replayable witness.
- State explicitly that empirical 0/2 is a stringent observed control gate, not
  a structural ceiling guaranteed by the fixture.
- Require the source-only pretarget builder and its hidden-target mutation test;
  this clarifies rather than changes ratified R03.
- If independent review finds the empirical 0/2 gate uninterpretable once its
  true 1/2 capacity is disclosed, stop G1 and return a new arm/roster choice for
  human taste rather than changing it after model calls.

No model/GPU call has occurred. The unchanged D0 CPU gate passes before this
repair, and the implementation remains blocked from GPU until the inconsistency
is resolved.
