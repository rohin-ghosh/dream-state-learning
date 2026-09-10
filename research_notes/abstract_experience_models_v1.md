# Abstract draft v1 — Experience Models (2026-09-06; superseded)

Historical synthesis from the 09-04 → 09-06 ideation sessions. It is
superseded by `abstract_experience_models_v2_positioning.md` and the current
manuscript. In particular, population/classroom language below is not part of
the paper: the registered direction is one frozen parent teaching one child,
followed by parent-absent deployment.

> **Positioning warning (2026-09-06):** preserve this as the original vision
> draft, not paper-ready prose. A same-day literature audit found direct
> precedents for training an acting model on its own action/future-state data
> (Early Experience), distilling reflection/rollback corrections into model
> weights with the guidance absent at test time (LEAFE), and learned online
> textual-memory updating (MemoPilot). The opening and several novelty claims
> below are therefore too broad. See
> `related_work/20260906_experience_learning_neighbors.md` and the v2
> positioning draft.

## Title candidates
1. Experience Models: Continual Experiential Post-Training for Prospective
   Agents
2. Raising Machines: Parenting, Dreaming, and Sleep for Self-Learning Agents
3. The Model Edits Its Weights by Thinking: Experience Models for
   Lifetime-Learning Agents

## Abstract (~250 words)

Large language models arrive omniscient and amnesiac: pretrained on
humanity's records, yet unable to learn from their own lives. Their agentic
behavior is fixed by fleet-level post-training before deployment; afterward,
nothing an agent does, notices, or is told changes how it thinks. We
introduce **experience models**: agents that convert lived experience into a
persistent parametric worldview. The architecture is deliberately minimal —
one frozen base model, one thinking loop, and a low-rank adapter as the only
thing that learns. The agent thinks in a free-flowing self-conversation in
which acting is tool use; every action is preceded by a prediction, and the
resulting ledger of expectation violations makes a coherence loss computable
over the agent's own history: the error lives in experiences. Dreaming —
taught first, learned later — reconciles the agent's finite conscious space
against an unbounded, lossless episodic ledger; sleep compiles verified
experience (wins, recoveries, contrasts, cross-episode principles, and the
thinking pathways that produced them) into training data and commits it to
the adapter: the model edits its weights by thinking. In a
compiler-optimization gym providing dense, deterministic external feedback,
we compare identical agent loops differing only in consolidation, measuring
held-out improvement as a function of lifetime — with measured noise bands,
adapter-removal and outcome-shuffling controls, and absorption assays over
facts, procedures, and dispositions. We characterize when consolidation
helps, when it harms (naive recipes measurably poison behavior), and where
it saturates: self-learning without further teaching asymptotes, and
thinking quality beyond the parent will require populations of diverse,
competing learners. Finally, we introduce **parenting** — a transferable
kickstart of how-to-learn priors — and evaluate a parented learning agent
against its never-learning twin.

## One-sentence versions
- Long: We put a frozen language model in a body made of three mechanisms —
  a thinking loop, a dream that manages its consciousness, and a sleep that
  compiles its verified experience into a low-rank adapter — and measure
  whether living longer makes it think better.
- Short: Agents that learn from their own lives, where the only thing that
  trains is what the agent experienced.

## Claim-to-evidence map (which experiment backs which sentence)
- "identical loops differing only in consolidation" → v6/v6.1 A-vs-B arms.
- "measured noise bands" → noise_probes (9 reps).
- "naive recipes measurably poison behavior" → sleep-v1 result (cell-counted,
  with contamination caveat; long-run replication pending).
- "held-out improvement vs lifetime" → 1024-episode run (sealed split), d1/d2.
- "absorption assays" → recognition reads (built), behavioral deltas
  (running), disposition analysis (to build).
- "adapter-removal / outcome-shuffling" → running / planned.
- "parenting + parented-vs-regular final" → the Rohin-parented finals (plan).
- "asymptote + populations" → stated as bound + future work, not claimed.
