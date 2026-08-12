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
