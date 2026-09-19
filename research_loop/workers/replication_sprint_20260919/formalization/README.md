# Workstream 5: formalization and bounded replication proposal

**September 19, 2026 — proposal only; not a registered or executed experiment.**

Scope: this directory only. No runtime/source changes, launches, live messages,
commits, publication, or changes to existing lives are part of this workstream.

## Recommendation

Test whether persistent, contingent parenting plus authentic-child LoRA updates
leaves useful behavior available after the parent and teaching context are gone.
The proposed mechanism is an interaction: parenting elicits useful thinking and
actions; the slow adapter loop may make those behaviors more readily initiated;
the fast context loop uses them to respond to new evidence. Neither articulate
self-description nor reproducing a parent's wording establishes this mechanism.

- [Formal definitions, estimands, and falsifiers](FORMALIZATION.md).
- [Bounded experiment and preregistration draft](PREREGISTRATION_DRAFT.md).
- [Machine-readable proposal parameters and unfilled bindings](proposal.json).

**Small primary design:** three independent seed blocks, each containing a
parented learner, a same-policy parented frozen sibling, and an unparented
learner. Forty-eight developmental cycles add reading, probing, writing, and
games to math. At the predeclared final age, score parent-free fresh-context
copies on an experimentally withheld, exactly checkable task family. The main
contrast is learner minus frozen sibling; the unparented learner tests whether
any gain specifically requires parenting. Nine trajectories are not nine
independent replicates of one treatment: there are **three blocks per contrast**.

The core permits at most **884,736 child-generated tokens and 73,728 parent
output tokens**, excluding input/prefill, optimizer work, retries, and optional
diagnostics. These are ceilings, not measured compute or a wall-time forecast.
This is a small preregistered pilot, not a powered confirmatory result.

An optional bounded parent-free deployment fork supplies the H2
parenting-history × continued-consolidation comparison. Announced tapering is a
separate, secondary policy comparison, not a prerequisite or presumed cause of
independence. Existing lives keep their checkpoints and continue; evaluation
copies have finite budgets and may finish.

## Evidence boundary

The submitted abstract is read from `origin/main` at
`9fd18cb9cd82112eb6d2be6c62c62cd5b0fe27f2`, not reconstructed from conversation:
`ABSTRACT_SCOPE_AND_RESEARCH_UPDATE_2026-09-19.md`, SHA256
`e3ebf0e6946ad38b1fd7810742c4393b74cde594c43b7f7d76a68df0e54dc0b7`.

The September 19 01:39 UTC correction review does not establish a complete
correction chain. The reconciled C2 checkpoint comparison is descriptive;
sleep51 was identified after examining outcomes. It can motivate training-only
refinement, not serve as a prospectively selected independent replication.
These bounded receipts are not a claim about the fleet's current live status.

The draft preserves H1/H2, the frozen Qwen2.5-7B-Instruct base, LoRA-only updates,
authentic-child targets, sealed-score blindness, controls, and evidence custody.
It creates no new demonstrated thesis and requires no new lease. A main-session
implementer must bind the actual task generator, code, prompts, budgets, and
checkpoint identities before the proposed measurements; those bindings are
explicitly unfilled here. Major thesis or invariant changes remain Rohin's
decision. This document adds no independent-review or per-run permission gate
to the builder's existing authorized experimental scope.
