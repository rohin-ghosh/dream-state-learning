# Dream-State Learning — Paper 1 (B) Design Doc v0.1

**Status:** first concrete draft, meant to be torn apart. Open questions flagged `[OPEN]`.
**Companion:** see `research_notes/` (INDEX.md, RANKED_READING_LIST.md, JOURNAL.md).

---

## 1. One-sentence thesis

Continual learning requires the Complementary Learning Systems split — a fast,
plastic episodic store separate from a slow, stable world-model — and we build
that fast store as a **standalone parametric memory whose sleep-time,
value-weighted consolidation provably keeps relational structure and sheds
episodic detail** (the "Missing Diagonal"), measured where no existing system
can measure it: against a ground-truth dependency graph.

## 2. Motivation / framing

- **It's a learning problem, not a memory problem.** Fine-tuning one big net on
  a stream of experience = one system, one timescale → catastrophic forgetting
  (this is a *baseline*, not our method). CLS uses two timescales: fast episodic
  encode without disrupting the slow model; offline replay selectively teaches.
- **Why structure-up/detail-down:** (a) it's what makes memory a reconstruction
  not a tape recorder; (b) **it's what makes a large memory *traversable*** —
  structure is its own index; flat memory must be scanned. This is the scaling
  motivation.
- **Attention as capital:** consolidation = allocating limited write-capacity
  across experiences by value. MoE routing is the existing "learned allocation"
  instance. (Grand-vision framing; contribution stays narrow.)
- **Formal foil:** transformer memory is provably write-once/stateless
  ("Transformers are Stateless DNCs", 2026). We add stateful, offline-
  consolidated, structure-selective memory.

## 3. Gap & competitive position

- The exact axis (structure-up/detail-down over time) is named the "Missing
  Diagonal" (Experience Compression Spectrum, 2604.15877) and implemented by
  no one. Learned when/what-to-consolidate named open (Modular Memory, 2603.01761).
- **Close concurrent works (differentiate crisply):** PEAM (2605.27762,
  parametric embodied memory), Auto-Dreamer (2605.20616, learned offline
  consolidation — baseline-to-beat), EVAF (2606.26806, goal-vs-fact split;
  declares forgetting unsolved), SCM (2604.20943, NREM downscaling donor).
- **Our moat:** the **ground-truth dependency-graph measurement** — nobody else
  can separately score structure vs. detail retention. Testing standalone (no
  LLM in loop) also dodges backbone-dependence and LLM-judge eval fragility.

## 4. Research questions

- **RQ1 (core):** Does value-weighted sleep consolidation into a capacity-
  limited parametric memory produce structure-up / detail-down retention,
  *without* an objective that hard-codes the split?
- **RQ2 (scaling / bitter-lesson):** Does the structure-retention advantage over
  flat storage GROW or hold as #experiences and memory size scale?
- **RQ3 (traversability):** Does structure-organized memory retrieve reliably at
  scale where flat/parametric baselines degrade?
- **RQ4 (mechanism ablation):** Which ingredient drives it — capacity limit,
  value-weighting, or recurrence of structural facts?

## 5. Architecture (v0.1)

**Standalone memory system. No LLM in the loop for the core experiments.**

- **Substrate:** ATLAS/Titans-style neural fast-weight memory `M` (small deep
  MLP), salience-gated gradient write + adaptive decay. **Backup / ablation
  arm:** Larimar-style Kanerva associative matrix (one-shot write).
- **Write (dream-time / sleep):** given a batch of episodes from the STM buffer,
  each episode `e_i` carries a weight `w_i = f(V(s_i), |TD_i|)` (value magnitude
  + surprise). Minimize weighted reconstruction loss
  `Σ_i w_i · L_recon(M(key_i), content_i)`. High-`w` imprints strongly;
  capacity-limited interference washes low-`w`. `[OPEN]` exact key/content
  encoding; exact form of `f`.
- **Read (probe):** query `M` with a key, get reconstructed content; score
  against ground truth.
- **Forgetting = native:** capacity superposition + decay gate. No explicit
  forget objective.
- **Value signal:** learned value `V(s)` (Dreamer-style λ-returns) refreshed
  each sleep cycle to handle policy non-stationarity. For v0.1 POC the "policy"
  can be a fixed heuristic value (progress-to-goal) `[OPEN]`: heuristic vs
  learned value for the first result.
- **Deferred to Paper A:** wiring `M` into LLM context (capital-allocation
  training), learned sleep schedule, live/waking reconsolidation-on-recall
  pathway, MCTS/planning.

## 6. Environment

Text crafting-sim (already built: `dream_state/environments/minecraft_sim.py`).
Persistent worlds, ground-truth crafting DAG + resource locations. Each episode
decomposes into:
- **Structural facts:** dependency edges ("wood → planks", "need pickaxe before
  ore", resource-location bindings).
- **Detail facts:** incidental attributes (which world instance, exact counts,
  surface descriptors).
Complement with a ScienceWorld/ALFWorld slice for comparability + a
LifelongAgentBench slice to defuse "bespoke benchmark" `[OPEN]` how much of this
in Paper 1 vs later.

## 7. Measurement

- **Primary metric:** structure-retention vs detail-retention, scored
  *programmatically* against the ground-truth graph (no LLM judge). Two numbers,
  reported separately — this is the Missing Diagonal made visible.
- **Scaling curves (RQ2):** retention vs #episodes and vs memory size, ours vs
  flat baseline.
- **Traversal (RQ3):** retrieval accuracy vs memory occupancy.
- **Usefulness readout `[OPEN]`:** a light probe/decoder (or minimal LLM readout
  as a *secondary* experiment) showing retained structure supports task queries
  at a fixed memory budget vs baselines.

## 8. Experiments

- **Exp 0 — Isolation probe (centerpiece, de-risk first):** write known
  structured memories, probe retrieval, find the capacity break point, confirm
  attention-weighting shifts it. Answers "can this net retrieve structure at
  all" before anything else.
- **Exp 1 — Structure-vs-detail (RQ1):** consolidate episodes + N interfering
  episodes; measure the two retention numbers vs baselines at matched budget.
- **Exp 2 — Scaling / bitter-lesson (RQ2):** the scaling curves.
- **Exp 3 — Traversability (RQ3):** retrieval vs occupancy.
- **Exp 4 — Ablations (RQ4):** capacity on/off, value-weight vs uniform vs
  surprise-only, gradient-imprint (ATLAS) vs one-shot (Larimar), value heuristic
  vs learned.

## 9. Baselines (all at matched active-memory budget)

no-memory floor · filled short-context · RAG (+ Mem0) · LoRA/parametric memory
(Remembering Transformer) · reflective-abstraction (CLIN) · classical-CL (A-GEM)
· **Auto-Dreamer (bar to beat)** · graph-oracle ceiling.

## 10. Eval-fragility guards

Programmatic graph scoring (no LLM judge); if any LLM readout, ≥2 backbones +
≥2 judges w/ agreement; average ≥3 curriculum orderings; tune replay fairly
(naive replay is a false floor); define budget as *active memory at inference*.

## 11. Risks

- **R1 Retrieval fails** from overtrained small net (the crux). → Exp 0 first;
  Larimar backup substrate if ATLAS-style retrieval is unreliable.
- **R2 Auto-Dreamer overlap** — differentiation must be real: structure-vs-detail
  bias + graph-grounded measurement. → state crisply in intro; if our structure
  advantage doesn't hold, we're a replication.
- **R3 Structure doesn't emerge** without hard-coding → then RQ1 is negative,
  which is still a publishable finding (interference alone insufficient; need
  explicit relational bias) and motivates the next design.
- **R4 Non-stationary value** mis-ranks imprint → refresh value each cycle;
  start with fixed heuristic value to isolate.

## 12. Compute plan

Standalone memory net is small → most experiments are cheap (no 7B in loop for
Exp 0–3). LLM only for the optional usefulness readout (Exp-1 secondary) and the
ScienceWorld/ALFWorld comparability slice. Fits comfortably in one cluster lease;
Exp 0 runnable locally.

## 13. What Paper 1 explicitly is NOT

Not the harness (A). Not live/learned attention. Not context integration. Not
masked-in-model memory. Not MCTS. Not the multi-module cognitive stack. Those
are the program map (`JOURNAL.md`), each a later paper.
