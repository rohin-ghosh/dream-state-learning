# Vision Roadmap — Rohin's long-term program (as articulated 2026-08-12, night of lease 1)

**Status: PRIVATE / NOT PAPER MATERIAL.** The ICLR paper claims exactly what the
instrument validates (draft checklist: strip vision language). This file exists so
the direction is articulated once, cleanly — for research statements, lab
conversations, and future-us. Rohin's core reframe: *this is not a memory system;
it is a reframe of policy systems* — attention as the interface through which a
learned policy propagates into every allocation decision an agent makes (memory
writes, memory reads, context, compute/model allocation, consolidation targets).

## The staged ladder

**v1 (now, Paper 1):** Frozen policy, frozen LLM, oracle value, ONE trained
attention-shaped salience head gating parametric memory writes + the retention
benchmark. Purpose: attribution — prove the signal trains the gate, with every
confound frozen out. (ATLAS gave retrieval involved with context via parametric
memory; v1 adds *meaningful representation* via policy-derived value.)

**v2:** Learned value head replaces the oracle (learnability of the signal);
possibly salience-weighted LoRA consolidation as a second consumer — "use the
same attention head to weight a LoRA fine-tune, just to see if it works" (this is
already the planned run-2 consolidation surface; salience-weighted replay).

**v3:** Unfreeze the POLICY on ambiguous goals (model still frozen): a sandbox
env (maybe not a classic RL env) where goals are underdetermined and conflicting —
the "expensive lunch problem" — hunger/thrift/self-reward as simultaneous value
heads. Memory unfrozen (it already is), policy now learned; the felt head(s)
become the coupling between the learned policy and the memory substrate.

**v4:** Multi-headed policy ↔ multiple policy-attention heads. Open design
question Rohin flagged: mapping is probably not 1:1 — more like a policy matrix
training a *set* of attention heads jointly. NAMED DANGER (his instinct, and it
has a literature): goal-oriented attention heads must not overwrite the model's
world-representation — "losing world understanding for its own goal
understanding." Known as representation narrowing/collapse under RL; standard
remedies: auxiliary self-supervised losses (MERLIN's remedy, again), KL-to-base
constraints (the RLHF trick), frozen backbone + adapter isolation, explicit
capacity partition (goal heads compete with each other, not with world heads).
His proposed remedy: unfreeze ALL attention (so competition is symmetric) while
keeping non-goal world representations maintained by data/objective mix.

**v5:** Salience-weighted LoRA consolidation with partially unfrozen policy +
fully unfrozen memory → an agent whose weights, memory, and policy co-adapt
online: "online learning that genuinely grows alongside interaction."

## Known hard problems on the ladder (name them early)
1. **Non-stationarity** (note 10's warning): once the policy learns, the salience
   distribution shifts under the memory; value chases a moving policy →
   two-timescale updates, target networks, or periodic re-distillation.
2. **Representation collapse under goal pressure** (v4 above).
3. **Credit assignment across heads**: which policy head's TD gets to gate which
   write when concerns disagree (the lunch problem is a write-gate problem too —
   what should the agent REMEMBER about the expensive lunch?).
4. **Goal generation** ("existentially ambiguous agency"): where goals come from
   at all — autotelic/intrinsic-motivation literature; permanently out of paper
   scope, permanently in private scope.
5. **Paradigm invariance** (established tonight, note 25): retention-under-budget
   is an organ both the LLM paradigm and the world-model paradigm (AMI's
   "persistent memory" bullet) lack a mechanism for. The ladder does not require
   betting on either winner. Robotics/VLA is where the paradigms are being forced
   to merge; language-backbone-with-peripheral-modules is currently winning there.

## One-sentence version
Train the scalar that says "this matters"; then let everything an agent
allocates — memory, context, compute, its own weights — be spent proportional
to it; v1 proves the scalar is trainable and its effect measurable.

## v6 / endgame sketch (2026-08-12, later that night)
Single-scalar-outcome autonomous loop: pick a domain where the reward function
already exists and is instant/dense/exactly denominated — trading (synthetic
book first, graduated real access). Policy online-learned on P&L; world
representation maintained IN TENSION with goal pressure at the attention level
(in this domain that tension is survival, not aesthetics — naive P&L-RL learns
tail-risk-loading degenerates); memory reads/writes agent-decided; FIXED sleep
cycle for heavy consolidation (the project's founding metaphor, closing the
loop); eventually self-reconfiguration on own outcomes ("super loop").
Named requirements discovered en route: reward channel outside agent
write-access (wireheading/containment — an architecture problem, not ML);
sandbox graduation gated by adversarial eval, since sim-profitable ≈
sim-exploiting (the FeltCraft lesson at scale); reward-vs-reality tension as
first-class design objective. Rejected on the way: "efficient research market"
(requires building the reward function; pricing research fast is itself
unsolved).

## v2 design brief, sharpened (Rohin, 2026-08-12)
The scalar write-weight is v1's measurable shadow of the real idea. The real
idea: salience integrated into the memory's full KQV geometry — value-shaped
Q/K projections so that effective weighting EMERGES (where a memory is
written, what it binds to, what it may overwrite), not just how hard the
gradient presses. Amplitude says "how much"; geometry says "where and with
what". v1's scalar result — either sign — sets v2's baseline: an effect at
the gate motivates asking whether geometry beats the gate; a null at the
gate with a live oracle gap is direct evidence the aperture (not the signal)
is the bottleneck, making geometric integration the motivated next step.

## Memory-hierarchy sketch (Rohin, 2026-08-12): files = external notes;
context = STM (task-switch cost = push-to-LTM + refill — the human analogy);
parametric = internal LTM. Rewrite loop = reconsolidation: retrieval cue
("let me think about this") → memory labile in context → re-reason with the
cueing signal steering → re-write, with Ks stable so updates land in the same
representational neighborhood (in-place reconsolidation; v2-geometry
requirement). Executive = reasoning, memory-aware (metamemory), learning
access patterns → post-training on memory USE (read-policy sequel).
Scaling frame: Rubin-Ultra/Feynman-class compute → longer-lived agents →
retention becomes the binding constraint; this project tests the slice
without requiring the scale.

## Positioning language locked (Rohin, 2026-08-12 night)
- **Past-relevance vs future-relevance:** trained attention = "what from the
  past explains what comes next" (relevance := predictive, shaped by language
  loss). Felt attention = "what from the present will the task need later"
  (relevance := outcome-shaped). KVP refines the contrast: they predict future
  ATTENTION (endogenous); we score content against future TASK USE (exogenous).
- **The hierarchy axis (Figure-1 candidate):** file system / RAG → context
  window → felt parametric memory → LoRA/post-training — monotone UP in
  representational integration, DOWN in retrieval fidelity/addressability.
  Pitch: the intermediary tier was missing an organ; each neighbor fails its
  own way (RAG retrieves sentences not understanding; post-training can't
  same-day recall; context is finite+unselective). NOT "we beat everything."
- **Two products, ordered:** (1) vision — trained future-relevance scorer as
  a universal allocation signal (writes, STM reads, LoRA weighting);
  (2) evidence — one consumer proven rigorously (parametric writes), second
  consumer (salience-weighted LoRA) = cheapest generality demo, run 2.

## Bitter-lesson calibration (Rohin, 2026-08-13): scalar-gate + top-k is a
structured-prior design — strongest exactly where data/complexity are scarce
(anti-bitter-lesson regime). Full-KV end-to-end memory (v2+) is the
bitter-lesson-side bet. Crossover governed by HORIZON, not novelty: longer
games multiply pathways past what a max-k deque read carries; novel-but-short
games are covered by frozen-LLM generalization the head inherits. Prediction:
v2 > v1 appears as game length grows; test with horizon as the knob. S4's
k-sweep (12 vs 18) measures the first data point: does the felt−surprise gap
shrink as read budget loosens?

## Read-side explore/exploit (Rohin + external researcher, 2026-08-13)
The agency risk of good memory: enough refined retention and the agent
optimizes over its own past ("when you think you know things, you don't try
to get to know things") — plasticity-stability, behaviorally. Formalism: UCB
at the memory interface — read policy surfaces value-retained facts PLUS an
uncertainty/exploration term; "you have NO binding for raw_4" (a known gap)
is maximally decision-relevant retrieval. Symmetry: surprise, demoted from
the write gate (lost to value), belongs on the READ side as the exploration
term. v1 structurally immune (frozen actor can't overfit to memory); risk
activates at v3 (learning policy) — on the register with the UCB sketch.
S4's no-memory-explores vs memory-trusts anomaly (if it survives the full
table) is this phenomenon measured — motivates the exploration-aware read.

## Cross-config principle: vary statistics, hold semantics — depth/branching
shift, fact schema fixed. Domain shift (crafting→chemistry) tests the LLM,
not the head → external-anchor slot, post-paper.

## Surprise, resolved (Rohin, 2026-08-13 night)
Taxonomy: (1) retrospective surprise = prediction error — needs NO head, it
IS a loss value (memory's native reconstruction error); dumb because
unexpectedness ≠ importance. (2) Prospective exploration value = UCB bonus —
belongs to the ACTION policy/planner, not memory. (3) Information gain
(Bayesian surprise) = "did this restructure my model" — the only respectable
write-side form. SYNTHESIS: novelty is the value function of goals you don't
know yet — value degenerates into surprise as the goal distribution blurs.
v1 measured the sharp-goal limit (value dominates, surprise < uniform);
v3's ambiguous goals re-weight novelty as a prior on future value; a broad
enough goal-trained value absorbs novelty entirely (bitter-lesson limit).
Write rule endgame: goal-certainty-weighted blend. One discussion line in
paper 1, machinery later.

## Analogical-transfer benchmark idea (v2+): worlds sharing relational
MOTIFS so memory supports role-mapping across worlds ("this world's raw_2
plays raw_7's old role") — structural transfer, the thing RAG
constitutionally cannot do; the strongest eventual answer to "why
representational memory." (Memory contents never transfer across unrelated
worlds — the HEAD transfers; cross-config tests exactly that.)

## v3 actor = value-guided search (Rohin, 2026-08-13 night)
The AlphaZero shape, transplanted: frozen LLM = policy prior; felt head =
leaf evaluator; UCB = explore/exploit arbitration; MCTS = the decision layer
— "the decision ends up not on the attention policy but on the tree search
which is a CONSEQUENCE of the attention policy." Exploration becomes the
procedure, not a signal; novelty stays passive (write-side prediction
error). Deep loop: search visit-counts are high-quality salience labels
(heavily-visited branches ARE load-bearing) → search amplifies the head,
amplified play trains the better head — AlphaZero self-improvement for
memory. NOT paper-1: needs world-model rollouts (large new component),
actor isn't the bottleneck (S0 0.90), and it confounds the retention
attribution. It is v3's actor, consuming everything v1/v2 validate.

## The architecture, stated whole (Rohin, 2026-08-13, verbatim-adjacent)
"The LLM harness becomes a cohesive continual-learning decision system:
memory systems and the action system all arbitrated by the attention core
against the value function — search as a CONSEQUENCE of the attention
policy, not a separate module. The program is unfreezing it one organ at a
time, value function first." Rollout legality: imagination-rollouts legal
(equal search budget per condition; memory quality → imagination fidelity →
planning quality = thesis act two); extra REAL env queries = cheating.
MCTS pilot: appendix-if-time (one world, felt vs surprise memory, fixed
imagined-rollout budget); else paper 2's opening experiment.
