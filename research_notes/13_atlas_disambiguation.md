# ATLAS Naming Collision + Parametric-Memory Landscape (2024-2026)

Date: 2026-08-10. Scope: (JOB 1) disambiguate the two "ATLAS" papers; (JOB 2) refresh the
parametric / fast-weight memory landscape. Companion to `12_atlas_baselines_learned_write.md`.

---

## JOB 1 — ATLAS naming collision: VERDICT

There are **two genuinely different papers that both go by "ATLAS."** They share nothing but the
acronym — different authors, institutions, mechanisms, and problem domains.

### ATLAS (a) — the fast-weight MLP memory (Behrouz / Google)
- **Title:** "ATLAS: Learning to Optimally Memorize the Context at Test Time"
- **arXiv:** **2505.23735** (submitted 29 May 2025)
- **Authors:** Ali Behrouz, Zeman Li, Praneeth Kacham, Majid Daliri, Yuan Deng, Peilin Zhong,
  Meisam Razaviyayn, Vahab Mirrokni — **Google Research.** Direct follow-up to **Titans**
  (arXiv 2501.00663).
- **Mechanism:** A sequence-model long-term-memory module where **memory = the weights of a small
  deep MLP**, written by **gradient descent at test time** and read by a forward pass. ATLAS's
  contribution over Titans is the **Omega rule**: instead of updating memory only w.r.t. the *last*
  token (the online "delta rule" / momentary surprise used by Titans and DeltaNet), it optimizes
  the memory weights against a **sliding context window of current + past tokens** (a local
  higher-capacity objective), with a Muon/2nd-order-style optimizer for the inner loop. It also
  introduces higher-capacity feature maps (polynomial/exponential) and the DeepTransformers /
  Dot variants generalizing softmax attention.
- **Write decision:** still **surprise-driven** — the write is a gradient step on a
  memory/reconstruction loss over the window (Omega rule), modulated by learned data-dependent
  momentum and forget/retention gates that are fixed during ordinary pretraining. **No learned
  value/outcome/reward head decides what to consolidate.**
- **Benchmarks:** language-modeling perplexity, common-sense reasoning (PIQA/HellaSwag/WinoGrande/
  ARC), recall-intensive (S-NIAH / RULER, MAD, associative recall), and long-context reasoning
  **BABILong** — headline **+80% accuracy at 10M-token context**. Baselines are sequence-model
  architectures only (Titans, RWKV-7, Gated DeltaNet, DeltaNet, Longhorn, GLA, RetNet, TTT,
  (Poly)SketchFormer, Transformer++, SWA). **Single-sequence long context only; no cross-episode /
  continual eval.**

### ATLAS (b) — the topological "dreaming" planner (Lawlor & Brown)
- **Title:** "ATLAS: Adaptive Topological Learning with Abstract Successors for Continual Learning"
- **arXiv:** **2608.04334** (Aug 2026)
- **Authors:** R. Blake Lawlor, Daniel S. Brown. (Different authors, RL / continual-learning venue —
  NOT Google's memory-architecture line.)
- **Mechanism:** A **reinforcement-learning** agent that builds a discrete **Grow-When-Required
  (GWR) topological graph** of the environment and attaches **Successor Features (SFs)** to nodes.
  It performs **offline planning called "dreaming"** — computing global Successor Features across
  the discrete GWR graph offline — to get sample efficiency by **bypassing slow parametric
  updates.** It structurally decouples transition dynamics (the graph) from the reward signal (the
  SFs), which yields near-instant adaptation to relocated goals and positive backward transfer.
- **Write decision / consolidation:** structural — nodes are added when the GWR criterion fires;
  "consolidation" is graph/SF propagation during offline dreaming, not weight surprise.
- **Domain:** spatial-navigation / non-stationary continual RL; **explicitly cross-episode / lifelong
  continual learning** (catastrophic-forgetting robustness, goal relocation).

### Which is which — and which to build on
- These are **NOT the same paper and NOT versions of each other.** Same acronym, coincidental.
- **(a) 2505.23735 is the "fast-weight MLP memory."** It is the correct **parametric-memory
  substrate** for the dream-state project to build on: memory-as-MLP-weights, written by test-time
  gradient descent. It is the Titans lineage.
- **(b) 2608.04334 is a topological-graph RL planner** whose "dreaming" is *offline SF propagation
  over a graph*, NOT parametric fast-weights. It is thematically adjacent to the project's
  wake-sleep/"dreaming" framing (offline consolidation, cross-episode continual RL, ALFWorld-style
  spirit) and is worth citing as related work on the **consolidation/dreaming + continual** axis —
  but it is **not** the parametric-memory substrate.
- **Caution / naming hygiene:** because both are "ATLAS," always cite by arXiv ID. If a source says
  "ATLAS does dreaming over a topological graph," that is (b) 2608.04334 — do NOT attribute that to
  Behrouz's memory paper, and vice versa.

---

## JOB 2 — Parametric / fast-weight memory landscape (2024-2026)

Table format: mechanism (one line) · write decision · consolidation scope.

| Work | ID | Mechanism (one line) | Write decided by | Consolidation scope |
|---|---|---|---|---|
| **Titans** | 2501.00663 | Long-term memory = deep-MLP weights updated by test-time GD (delta rule) alongside attention; "learning to memorize at test time." | **Surprise** = gradient magnitude of memory loss on the *current* token, with learned momentum + forget gates. | **Single-sequence long context** (NIAH, BABILong). No cross-episode. |
| **ATLAS (Behrouz)** | 2505.23735 | Same memory-as-MLP-weights, but Omega rule optimizes weights over a **context window** (current + past tokens), higher-capacity feature maps. | **Surprise** over a window (reconstruction/memory loss GD) + learned gates. No value/reward head. | **Single-sequence long context** (BABILong +80% @10M). No cross-episode. |
| **MIRAS** ("It's All Connected") | 2504.13173 | Unifying framework: sequence models = associative memory w/ 4 knobs — architecture, **attentional bias** (internal loss), **retention gate**, learning algorithm; yields Moneta/Yaad/Memora. | Generalized **attentional-bias loss + retention regularizer** (robust p-norm surprise), still online optimization — **not** reward. | Single-sequence; framework, not a continual protocol. |
| **Nested Learning / HOPE** | 2512.24695 | Model = nested multi-level optimization problems at different update frequencies; **HOPE** = self-modifying Titans variant + **Continuum Memory System** (modules updating at a spectrum of rates). | Self-referential/**self-modifying** update rules (learns its own update algorithm); still self-supervised, no external reward head. | **Gestures at continual learning** (multi-timescale CMS, forgetting) and tests continual LM, but evals are still LM/long-context, not agentic cross-episode. |
| **Test-Time Training (TTT)** | (Sun et al. 2024, 2407.04620) | RNN whose hidden state **is a model** updated by a self-supervised gradient step per token; memory = fast weights. | **Self-supervised reconstruction** loss gradient per token (surprise-like). | Single-sequence. |
| **GradMem** | 2603.13875 | Write context into a small set of **parametric memory tokens** via inner-loop test-time GD; the read/write objective is **meta-learned** by backprop through the write. | **Meta-learned self-supervised reconstruction** — learned *write rule*, but no value head choosing what/how strongly to consolidate; per-example optimization. | Single-sequence write; no reward-driven cross-episode consolidation. |
| **Auto-Dreamer** | 2605.20616 | Offline "consolidator" (CLS / wake-sleep framing) that decides what to keep/abstract across agent sessions. | **Outcome/RL reward (GRPO)** on agent task success — a *learned, outcome-trained consolidation decision*. | **Cross-episode consolidation** — but into an **external natural-language memory bank**, NOT parametric weights. |
| **ATLAS (Lawlor&Brown)** | 2608.04334 | GWR topological graph + Successor Features; offline "**dreaming**" propagates global SFs over the graph. | Structural (GWR node-add) + SF propagation; reward decoupled from transitions. | **Cross-episode / lifelong continual RL** — but graph+SF substrate, not parametric fast-weights. |

### State of parametric memory (one paragraph)
The 2024-2026 "memory-as-weights" line — TTT → Titans → ATLAS(Behrouz) → MIRAS → Nested
Learning/HOPE — has converged on a clear primitive: **a small neural network whose weights are the
memory, written by gradient descent at test time and read by a forward pass.** The frontier within
this line is about the *write objective and capacity* (per-token delta rule → windowed Omega rule →
generalized attentional-bias/retention losses → self-modifying nested optimizers) and about
*multi-timescale* memory (HOPE's Continuum Memory System). But every member of this family decides
writes by **surprise / self-supervised reconstruction**, never by a **learned value or outcome/RL
reward**, and every one is evaluated on **single-sequence long context** (LM, NIAH, BABILong) —
none does **cross-episode, reward-driven consolidation.** The two axes the dream-state project
targets — (1) a **trained value/policy head deciding write strength into parametric weights**, and
(2) **consolidation persisting across independent episodes** — are each occupied only *partially* by
neighbors that miss on the other axis: **GradMem** learns a write rule into parametric memory but
self-supervised and single-sequence; **Auto-Dreamer** does outcome-trained cross-episode
consolidation but into an external text store; **ATLAS(Lawlor&Brown)** does cross-episode continual
"dreaming" but over a topological graph, not fast-weights. The intersection —
**RL/value-weighted writes into fast-weight parametric memory, consolidated across episodes** —
remains **open**.

---

## Deliverables (quick answers)
1. **Disambiguation verdict:** Two distinct papers. **(a) ATLAS = arXiv 2505.23735**, Behrouz et
   al. (Google) — fast-weight MLP memory, Omega rule, Titans follow-up, single-sequence long
   context. **(b) ATLAS = arXiv 2608.04334**, Lawlor & Brown — "Adaptive Topological Learning with
   Abstract Successors," GWR topological graph + Successor Features with offline "dreaming,"
   cross-episode continual RL. Same acronym only; cite by ID.
2. **Correct fast-weight-MLP-memory substrate to build on: (a) arXiv 2505.23735 (ATLAS/Behrouz),**
   in the Titans (2501.00663) lineage. (b) is a graph planner, not parametric memory — cite it as
   related work on the dreaming/continual axis, not as the memory substrate.
3. **State of parametric memory:** see paragraph above — surprise-written memory-as-weights is
   mature and single-sequence; value-weighted, cross-episode parametric consolidation is open.

## Key URLs
- ATLAS (Behrouz, fast-weight MLP): https://arxiv.org/abs/2505.23735
- ATLAS (Lawlor & Brown, topological dreaming): https://arxiv.org/abs/2608.04334
- Titans: https://arxiv.org/abs/2501.00663
- MIRAS "It's All Connected": https://arxiv.org/abs/2504.13173
- Nested Learning / HOPE: https://arxiv.org/abs/2512.24695
- TTT: https://arxiv.org/abs/2407.04620
- GradMem: https://arxiv.org/abs/2603.13875
- Auto-Dreamer: https://arxiv.org/abs/2605.20616
