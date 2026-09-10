# Experience-scaled metacognition and affective parenting

Date: 2026-09-07  
Status: discussion-stage theory; not part of the one-parent v4 confirmatory
treatment, endpoint, or claim.

## Agent-level recurrence

The proposed recurrence lives across action--observation--consolidation cycles,
not as repeated depth inside one forward pass. This preserves parallel model
training and places serialized recurrence at an episode/lifetime timescale.
Unlike looped forward computation over a fixed input, each cycle receives new
world information and may commit a batched offline parameter update. This is a
useful architectural contrast, not yet an empirical superiority claim.

## Learned deliberation depth

The promising capability is not simply thinking more. It is estimating the
value of another layer of thought. A learned agent should distinguish:

- direct action or trigger;
- planning;
- plan verification;
- verification of its own evaluative process;
- recursive self-verification; and
- long-horizon or identity-level evaluation.

When no new information arrives, further recursion can have negative expected
value. A mature policy should sometimes recognize that it has climbed to an
unproductive meta-level, return to planning, and act. Flow may correspond to
free generation with evaluation deferred rather than inserted continuously.
Future assays should measure goal value per generated token and whether an
agent learns to allocate deliberation depth, not reward sheer chain length.

## Automatization and prospective intention

An internalized action still requires a forward pass, but may consume less
scarce agent workspace because the policy no longer reconstructs its full
rationale. Prospective memory is the complementary ability to maintain a
future-directed intention until a time, event, or milestone makes it relevant.
These suggest two future measurements: workspace/token savings after practice,
and milestone-triggered recall without continuous rehearsal.

## Affect as a pretrained teaching channel

Language models already contain rich structure for affective and social
situations. Strong positive or negative framing may therefore act as a
high-dimensional teaching signal that changes subsequent reasoning, rather
than merely describing a scalar reward. A remorse-like response can become a
second-order object: the agent may reason about its reaction, revise a policy,
and later consolidate that trajectory.

This does not establish phenomenology, sentience, or alignment. It motivates a
development heuristic: interact in ways coherent with the model's pretrained
social representations and measure downstream behavior. Negative intensity
must not be treated as automatically useful. Future development should track
positive/negative/self-directed valence, action rate, hesitation, calibration,
recovery after large errors, and whether the same public outcome produces a
different learned disposition under affective versus neutral framing.

The confirmatory parenting experiment deliberately excludes affective
free-text treatment. Development may discover useful process lessons through
rich human interaction; only a target-blind, closed, separately ratified
policy can enter confirmation.

## Intelligence about being

One conceptual framing is "sentience as intelligence about being": persistent
self-management across time--attention, intentions, experience
interpretation, identity, cognitive regulation, action evaluation, remembering,
forgetting, exploration, and indirect self-change. In the architecture:

```text
conscious workspace -> thought/action -> public experience
                    -> DREAM reconciliation -> SLEEP compilation
                    -> changed parametric prior -> changed future cognition
```

This is a research program, not a paper claim. The immediate technical work
remains read, write, compile, causal provenance, non-erasure, and learning-rate
allocation across a lifetime.

