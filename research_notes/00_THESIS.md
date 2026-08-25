# 00 — THE THESIS (read this first)
*(Consolidated 2026-08-26 from ~3 months of design sessions. This is the
project's theory in one place, for humans and agents. Deep detail:
DESIGN_SUPER.md (architecture), SPEC_V2.md I–III (experiments),
research_notes/32 (decision log), VISION_ROADMAP.md (far vision),
REVIEW_PACK.md (current state + results).)*

## The one-sentence thesis
An agent should get better the longer it lives — its second month better
than its first — by consolidating its own lived experience into weights
("dreaming") and reading that consolidated experience back as
intermediary intelligence for new decisions ("thinking").

## The claim, stated honestly against the field
Post-training already IS experiential learning. Our claim is moving it
OFFLINE → ONLINE and POPULATION → INDIVIDUAL: one agent's own outcome-
stamped history, consolidated continually during deployment, not a
million users' trajectories baked in once before shipping. Labs don't do
this because online individual updates mean catastrophic forgetting, no
held-out eval, unbounded drift, no rollback — this project builds the
measurement machinery for exactly that gap. Nobody optimizes for
agent-lifetime throughput because no agent has a lifetime.

## The architecture (organs, and what's amortized when)
Frozen central REASONER (desire never touches deduction). Around it:
- DREAMER: offline; consumes context-window batches of experience;
  emits multi-perspective, engine-verified memories; "a fixed function
  with a changing argument" — how-to-dream is slow capability,
  what-to-dream-about moves fast because its input (the evaluator) moves.
- DAYDREAMER: same operation, online, between tasks, targeted at what
  recent episodes needed-and-missed.
- THINKER: builds context from memories + present state; forces
  commitment (no abstention in play — retries are the safety valve);
  reads and writes are co-designed (writes resemble reads).
- EVALUATOR (critic): the ONLY component that ever needs RL — judges
  states/outcomes; everything else distills from its judgments
  (actor-critic factorization; minimal RL surface).
- LTM: a LoRA adapter as the second person of a person-hierarchy
  (context=1st, adapter=2nd, base weights=3rd). Not a database — a world
  being built out of experiences replayed through each other; as the
  built world grows, raw reality fades ("a puzzle off a light-projected
  real world"). Memory hands context INTERMEDIARY INTELLIGENCE, not
  answers; it is a POLICY PRIOR: state + goal in → what-has-worked out.
Paper 1 amortizes everything except the substrate; papers 2–3 learn the
curator and the loop.

## The scaling ideology
- Lived experience is serial; dreamed experience is parallel and
  buyable — compute converts into training signal over what was lived
  (why animals dream). Dream-budget-per-episode is a scaling axis.
- Sleep pressure = compute contention, not a clock: consolidate when
  its marginal value beats acting.
- Parallelism (population) converts the serial-experience bottleneck
  into a staleness problem (async-RL shape), never eliminates it.
- Store-everything is measurably impossible (capacity wall) ⇒ SELECTION
  is forced; the reasoner composes given structure (oracle 0.91) but
  won't induce spontaneously in-context ⇒ ABSTRACTION is forced and the
  leap must be elicited (thinker) or precomputed (dreamer).
- Invalidation is emergent: contradicting info attracts daydreaming,
  which shifts the corpus, and full-corpus retraining reverses old
  weights — deep memories need repeated evidence to flip (robustness,
  not a bug). Forgetting = omission from the next dream cycle
  (= spaced repetition for free).

## The measurement inventions (the field measures playback; we measure becoming)
- Induction unit = the PROCEDURE, not the fact: "did this-this-that a
  few ways; this situation is that shape; do this-this-that."
- Headline metric: paired per-goal TRIES-TO-GOAL falling with lifetime
  (graded; every game informative), split analogy-goals vs lookup-goals
  (iid stays as the control: equal improvement on both = general
  improvement, not induction — THE GAP IS THE EVIDENCE).
- Instruments: information-availability ceilings (tiered ideal
  learners), structural holdout (physics, not bookkeeping), leakage as
  a grep, reference numbers (abstain floor, majority-class traps),
  engine verification of every dream, controls that can fail, no number
  without a repo script.

## Game-design doctrine (learned across three worlds)
The game is the crux: our scale is deliberately small, so the world must
match idealized architecture patterns for small data to show observable
capability. Rules compact (≤ a context window), evidence diffuse
(≫ context window of episodes) — memory does that compression. Patterns
one-hop and SET-SCOPED (learn once, applies to a whole class), never
IMO-puzzle ciphers. Given the memories, the model must be able to
in-context induce at 70–90%, else the game is bad. Chess/checkers dial:
inducible rules, non-trivial strategy, nothing in pretraining.

## Trajectory
v1 (felt head): thesis untested-not-false; instruments validated.
v2 (dreamed LoRA vs retrieval): falsifier failed honestly; produced the
capacity wall, the oracle result, the induction-refusal finding, and the
eval discipline. v3 (in design): mini-game ladder (L0: 4 patterns) —
prove the write→verify→consolidate→think→read machinery at the smallest
scale, then climb complexity until context breaks and memory carries.
