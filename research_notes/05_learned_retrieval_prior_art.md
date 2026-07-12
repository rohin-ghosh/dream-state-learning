# Prior Art: Learned "Second Attention" for Agent Context Composition

Survey date: 2026-07-11. Question: has anyone built a learned mechanism that decides WHAT to
retrieve from long-term memory, short-term memory, and policy/goal state to compose an LLM
agent's working context — distinct from the transformer's internal self-attention — trained
end-to-end against task reward?

---

## 1. Learned / trainable retrieval (not fixed cosine-sim RAG)

### R2A — Retrieval-Augmented Reinforcement Learning (Goyal et al., DeepMind)
- arXiv:2202.08417, ICML 2022
- **How retrieval is decided:** a parametric neural retrieval network attends over an external
  dataset of trajectories; retrieval shapes the Q-network's predictions in a **fully
  differentiable** manner.
- **Trained against task reward:** yes — end-to-end with the RL objective (R2D2 on Atari).
- **Benchmark:** Atari; retrieval-augmented R2D2 learns faster and scores higher.
- **Limitation:** pre-LLM, small-scale RL agent; retrieves raw trajectories, no notion of
  heterogeneous memory streams or an LLM working context. This is the canonical proof that
  "learned retrieval trained by reward" works, but not in the LLM-agent setting.

### Memory-R1 (arXiv:2508.19828, 2025)
- Two RL-fine-tuned agents: a **Memory Manager** learning discrete ops (ADD/UPDATE/DELETE/NOOP)
  and an **Answer Agent** that pre-selects and reasons over retrieved entries.
- Trained with outcome-driven PPO/GRPO. Benchmark: long-horizon dialogue QA (LOCOMO-style).
- Limitation: retrieval selection is discrete text-level filtering by an LLM policy, not a
  dense attention mechanism; single memory store, no policy/goal-state stream.

### Mem-α (arXiv:2509.25911, 2025)
- Learns memory **construction** via RL; reward = downstream QA accuracy over full history.
- Limitation: optimizes what to write, not a retrieval attention at read time.

### MemRL (arXiv:2601.03192, 2026)
- Non-parametric RL over an episodic memory: Two-Phase Retrieval selects experiences by
  **learned Q-values / utility from environmental feedback**, explicitly moving beyond passive
  semantic similarity. No weight updates to the base model.
- **Benchmarks: ALFWorld** (0.507 last-epoch acc, +82% vs memory-free), HLE, BigCodeBench,
  Lifelong Agent Bench.
- Limitation: value-tagging of memory items, not a trained attention/controller network;
  episodic memory only.

### AgeMem — Agentic Memory (arXiv:2601.01885, 2026)
- **Unified LTM + STM management**: store/retrieve/update/summarize/discard exposed as tool
  calls inside the agent policy; three-stage training (SFT warm-up → task-level RL on outcome
  reward → step-wise GRPO for per-operation credit assignment).
- Benchmarks: five long-horizon agent benchmarks, multiple LLM backbones.
- Limitation: memory decisions are discrete tool calls made by the same LLM (in-band,
  "conscious" control), not a separate learned attention mechanism composing context out-of-band.

### Mem-π (arXiv:2605.21463, 2026)
- Trains a **generative memory policy** ("what and when to generate" into memory), optimized
  against downstream agent outcomes (decision-content decoupled policy optimization).
- Benchmarks include **ALFWorld**; ~20% relative gain over base agent, beats retrieval baselines.

### Classic MANN lineage
- Neural Turing Machine (2014), DNC (Nature 2016): fully differentiable **learned content +
  location-based addressing** into external memory — the original "learned second attention."
  Limitation: tiny memories, trained per-task, never scaled to LLM context composition.

## 2. Attention INTO external memory — learned or fixed?

| System | ID / venue | Retrieval decision | Learned? |
|---|---|---|---|
| kNN-LM | arXiv:1911.00172, ICLR 2020 | fixed kNN in frozen embedding space, fixed interpolation | No |
| RETRO (DeepMind) | arXiv:2112.04426, 2022 | frozen BERT retriever, chunked cross-attention | Retriever frozen; only the read (cross-attn) is learned |
| Memorizing Transformers | arXiv:2203.08913, ICLR 2022 | kNN over cached (k,v); **learned per-head gate** blends local vs memory attention | Gate learned; no gradients through memory itself; similarity fixed |
| Memformer | arXiv:2010.06891 | learned read/write cross-attention to fixed-size memory slots | Yes, but LM-loss-trained, tiny memory |
| RMT / Memory Transformer | arXiv:2207.06881 | memory tokens propagated by recurrence | Learned implicitly via LM loss |
| **Titans** (Google) | arXiv:2501.00663, NeurIPS 2025 | neural long-term memory module updates its own weights at test time via gradient "surprise" + momentum + adaptive forgetting; attention = STM, neural memory = LTM | Yes — meta-learned what to memorize/forget; but it's what to **write**, retrieval is implicit in the module's forward pass |
| Test-time regression / TTT layers | arXiv:2501.12352 etc. | memory as online regression | Learned write, implicit read |

Key point: in all of these, the "what to attend to" decision is either fixed similarity or a
learned gate/write rule trained on **language-modeling loss**, never on agent task reward, and
none composes context from separate LTM/STM/goal streams.

## 3. Two-level / hierarchical attention over memory

- **HMT — Hierarchical Memory Transformer** (arXiv:2405.06067, NAACL 2025): model-agnostic
  segment recurrence; compresses segments into memory embeddings and **recalls relevant
  memories via a learned retrieval step** across memory tiers. Trained on LM/QA loss, not
  reward. Follow-up: H2MT (arXiv:2605.24930).
- **Pretraining with hierarchical memories** (arXiv:2510.02375): separates long-tail vs common
  knowledge into memory banks routed at pretraining time.
- **Retrieval-Augmented Decision Transformer** (arXiv:2410.07071, 2024): external episodic
  memory for in-context RL; retrieval of past subtrajectories conditions the policy. Closest
  hierarchical design in the RL setting; retrieval is similarity-based, not reward-trained.

## 4. Auxiliary "subconscious" network composing context for a main model

This is the hottest and closest cluster (all 2025–2026):

- **ContextCurator** — "Escaping the Context Bottleneck: Active Context Curation for LLM Agents
  via RL" (arXiv:2604.11462, 2026). A **lightweight separate policy model** manages the working
  memory of a **frozen** TaskExecutor LLM: prunes noise, preserves "reasoning anchors."
  Trained with Multi-Turn GRPO **against task reward**. Benchmarks: WebArena (36.4%→41.2%),
  DeepSearch (8x token reduction). Limitation: curation/pruning of the existing transcript —
  it deletes/compresses; it does not *retrieve and fuse* from LTM + policy/goal streams.
- **AdaCoM** — "Learning Agent-Compatible Context Management" (arXiv:2605.30785, 2026):
  external LLM trained end-to-end with RL to edit a frozen agent's context via flexible
  modification actions. Same limitation as above.
- **CompactionRL** (arXiv:2607.05378, 2026): RL with context compaction for long-horizon agents.
- **D-Mem** (arXiv:2603.18631) and "Memory Beyond Recall" (arXiv:2606.09483): dual-process
  memory (fast vector retrieval + slow deliberation, quality gating). Gating is heuristic/LLM-
  prompted rather than a trained attention network.
- Cross-attention memory retrieval for generative agents (PMC12092450, 2025): trains a small
  cross-attention network on LLM-generated labels to rank memories — learned retrieval scorer,
  but supervised (LLM-distilled), not task-reward-trained.
- **Auto-Dreamer** (arXiv:2605.20616, 2026) — directly relevant to *this project's* wake-sleep
  framing: **offline memory consolidation** for language agents, fast per-session acquisition
  decoupled from slow cross-session consolidation, trained with **GRPO using end-to-end agent
  performance as reward**. Benchmarks: ScienceWorld (train), transfer to **ALFWorld** and
  WebArena (+7 pts, 6–12x less memory). Limitation: learns the consolidation (write/rewrite)
  side; retrieval at wake time remains standard.

---

## VERDICT: PARTIALLY PUBLISHED — the space is crowded, but the exact mechanism is open

**Already published (do not claim novelty on these):**
1. Learned retrieval trained end-to-end against task reward — yes, since R2A (2022) in classic
   RL, and now heavily in LLM agents (MemRL, Memory-R1, AgeMem, Mem-π, ContextCurator, AdaCoM,
   Auto-Dreamer; several evaluated on **ALFWorld**).
2. An auxiliary network that manages a frozen LLM's context, RL-trained on task reward —
   yes (ContextCurator, AdaCoM), as of early 2026.
3. Wake/sleep-style offline consolidation trained by agent reward — yes (Auto-Dreamer), on
   ALFWorld among others.

**Not found / genuinely open:**
- A **dense, differentiable "second attention" mechanism** — a trained attention network (not
  discrete tool calls, not text-level pruning) that jointly attends over **heterogeneous
  streams** (long-term memory + short-term memory + policy/goal state) and composes the working
  context by soft selection, trained against task reward. Existing systems either (a) use
  discrete LLM tool-call memory ops (AgeMem, Memory-R1), (b) prune/edit an existing transcript
  (ContextCurator, AdaCoM), (c) learn only writes/consolidation (Titans, Mem-α, Auto-Dreamer),
  or (d) do dense learned addressing but at toy scale on LM loss (NTM/DNC, Memformer, HMT).
- In particular, **treating the goal/policy state as one of the attended streams** and
  coupling retrieval attention with sleep-phase consolidation into a single learned system
  appears unpublished as of July 2026.

**Three closest existing systems:**
1. **AgeMem** (arXiv:2601.01885) — unified LTM+STM management learned via staged RL with
   step-wise GRPO; closest in scope (both memory levels, task reward), but decisions are
   discrete in-band tool calls, not a separate attention mechanism.
2. **ContextCurator** (arXiv:2604.11462) — closest in *architecture*: a separate lightweight
   "subconscious" policy composing a frozen executor's working context, RL-trained on task
   reward; but it only curates/prunes, doesn't retrieve from LTM or attend over goal state.
3. **MemRL** (arXiv:2601.03192) — closest in *retrieval semantics*: replaces cosine similarity
   with utility/Q-value-based selection from episodic memory driven by environmental reward,
   evaluated on ALFWorld; but non-parametric value tagging, not a trained attention network.

(Also flag: **Auto-Dreamer**, arXiv:2605.20616, is the closest prior art to the dream-state
*consolidation* half of this project specifically — ALFWorld transfer, GRPO on end-to-end
reward. Any paper must position against it.)

## Positioning implication
The defensible novelty claim is the **mechanism**, not the goal: a single differentiable
attention layer over typed memory + policy streams as the context composer (vs. discrete ops /
transcript editing), plus its joint training with wake-sleep consolidation. The claim "learned
memory retrieval for LLM agents trained by task reward" alone is no longer novel in 2026.
