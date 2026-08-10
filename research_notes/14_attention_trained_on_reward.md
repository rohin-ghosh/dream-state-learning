# Prior Art: Attention / Gating Head Trained on an External Value/Reward Function (Frozen Backbone) to Shape Memory

Question: Has "a small trainable attention (or gating) head, trained on an EXTERNAL objective
(RL/reward, a learned value function, or task-outcome signal) rather than the primary
next-token/language-model loss, on a FROZEN backbone, used to decide/shape what gets written
into or read from memory" been done — in ANY domain?

Search scope: arXiv / Google Scholar / venues, 2014–2026. Searched 5 framings:
(1) reward-modulated / RL-trained attention, (2) gating/MoE routers on external signals,
(3) value/goal-conditioned attention, (4) auxiliary-objective attention heads on frozen backbones,
(5) neuroscience value/dopamine-gated attention & memory-write gating.

---

## VERDICT

**PARTIALLY PUBLISHED — heavily anticipated in spirit, but the EXACT four-way combination
(small ATTENTION head + trained on a LEARNED VALUE/REWARD function + FROZEN backbone + shaping
MEMORY WRITES) is not published as a single named method.**

- The individual ingredients are all published and well-established:
  - Attention/gating weights trained by RL reward (RAM/Mnih 2014; Reinforced Attention Learning 2026; MoE RL routers).
  - Learned gates trained on an external outcome/value signal, on a frozen backbone, controlling memory writes (AURA 2026; D-MEM 2026).
  - RL-trained memory-write policies optimized on task-outcome reward (Mem-α 2025).
- What is NOT nailed down anywhere as an explicit claim: the gate being specifically a
  **trainable attention head** (Q/K/V-style, not an MLP/scalar gate) that is trained on a
  **learned value function** (not just terminal reward / RPE), while the backbone is **frozen**,
  used to **weight memory writes**. D-MEM (2026) comes within one design decision of this.
- Net: the *conceptual* claim is essentially occupied; the *precise mechanism* (attention head +
  learned value function + frozen backbone + memory-write shaping) has a narrow, defensible gap,
  mostly around "attention head" (vs generic gate) and "learned value function" (vs raw reward/RPE).

Bottom line for the dream-state project: you cannot claim novelty on "RL/reward-trained gating of
memory writes on a frozen backbone" (that's D-MEM / AURA / Mem-α territory). A defensible novelty
angle is the *specific instantiation*: an **attention head** whose weights are supervised by a
**learned value/routing head** (a value function, not sparse terminal reward), trained on a frozen
backbone, and used at **consolidation (wake-sleep) time** to shape what is written — plus your
routing-policy framing. Differentiate on (a) attention-head mechanism, (b) learned value function
as the training signal, (c) offline consolidation use, not just online write gating.

---

## THREE CLOSEST WORKS (ranked)

### 1. D-MEM — Dopamine-Gated Agentic Memory via Reward Prediction Error Routing (CLOSEST)
- ID/venue: arXiv:2603.14597, q-bio.NC / cs.AI, submitted March 2026.
- Mechanism: a **"Critic Router"** (described as a trainable attention-based gate) that scores each
  incoming item for surprise/utility and routes it via a Fast/Slow system — a cheap O(1) buffer for
  routine inputs vs. costly O(N) memory "evolution" for high-value inputs.
- External objective: **Reward Prediction Error (RPE)** — the discrepancy between predicted and
  actual reward gates whether/how information is written and restructured. This is an external
  value/reward signal, NOT the LM next-token loss.
- Backbone: **frozen** LLM; only the gating/routing components are trainable.
- Domain: agentic long-term memory for LLM agents (LoCoMo-style conversational memory).
- How it differs from the target claim: framed as a critic/router (surprise+utility scorer) rather
  than explicitly an "attention head weighting memory writes"; the training signal is RPE (terminal
  reward error) rather than a standalone *learned value function*; the emphasis is write/restructure
  routing and cost, not read-side attention shaping. But conceptually this is ~90% of the target.

### 2. AURA — Action-Gated Memory for Robot Policies at Constant VRAM
- ID/venue: arXiv:2606.02775, cs.RO/cs.LG, 2026.
- Mechanism: a **learned gate** that writes to memory ONLY when the current observation would change
  the next action (an action-utility criterion), keeping VRAM constant.
- External objective: the gate is trained against a **closed-loop action-error signal** (does the
  write change/improve the action?) rather than a reconstruction or token loss — i.e., an external
  outcome/value-style signal.
- Backbone: memory gate is an add-on module to a robot policy; write decisions are decoupled from the
  base policy's primary loss (partial-frozen / modular).
- Domain: robot manipulation / continuous-control policies.
- How it differs: the gate is a scalar/MLP action-utility gate, not an attention (Q/K/V) head; the
  training signal is action-error (behavioral outcome) rather than a learned value function; robotics
  rather than LLM memory. Very close on "learned gate, external outcome signal, controls memory writes."

### 3. Mem-α — Learning Memory Construction via Reinforcement Learning
- ID/venue: arXiv:2509.25911, Sept 2025 (code: github.com/wangyu-ustc/Mem-alpha).
- Mechanism: an LLM **memory-management policy** with tool calls (core/episodic/semantic memory) that
  learns what to store, how to structure it, and when to update.
- External objective: **RL (PPO-style) with reward = downstream QA accuracy + memory-quality metrics**
  over the full interaction — a pure task-outcome reward, not the LM loss. Generalizes from 30k to 400k+
  token contexts.
- Backbone: the memory-controller LLM is **fine-tuned by RL** (NOT frozen); write decisions are LLM
  tool calls, not a small attention/gating head.
- Domain: long-context LLM agent memory / QA.
- How it differs: write decisions are emitted by a fine-tuned generative LLM policy via tool-calling —
  not a lightweight attention/gating head, and NOT a frozen backbone. Closest on "RL/task-outcome
  reward trains the memory-write decision," farthest on the "small head + frozen backbone" axis.

---

## Broader landscape (supporting evidence, less close)

RL-trained attention (attention weights as a policy, but not memory / not frozen):
- Recurrent Models of Visual Attention (Mnih et al., NIPS 2014) and successors (RAM-VO;
  Diversified Visual Attention Nets; DeepRL Attention Selection for Person Re-ID, arXiv:1707.02785):
  **hard attention / glimpse location trained by REINFORCE reward**. But the whole model trains
  end-to-end (no frozen backbone), and there is no external memory being written. Canonical precedent
  for "attention-as-action trained by reward."
- Reinforced Attention Learning (arXiv:2602.04884, 2026): treats the final-layer attention distribution
  of a multimodal LLM **as a policy** and adds an advantage-weighted attention-divergence RL loss
  ("optimize where to attend, not what to generate"). Vision encoder frozen, but the LM backbone IS
  updated and it's combined WITH the token-level RL loss; no memory component. Closest on
  "attention distribution trained by reward," but not frozen-backbone and not memory.
- Learning Wake-Sleep Recurrent Attention Models (arXiv:1509.06812): wake-sleep training of hard
  attention — relevant to the project's wake-sleep framing, but not reward-gated memory writes.

MoE / gating routers trained on external signals:
- S-BASE / RL-gated MoE (Clark et al.; A Survey on MoE, arXiv:2407.06204): top-1 routing trained by
  **RL with reward = negative cross-entropy of the predicted token**. But that reward is a proxy for
  the primary task loss (not an independent value function), and the router is trained jointly with
  the experts (not a frozen backbone). Gated Attention (NeurIPS 2025) and auxiliary load-balancing
  losses: gating trained on auxiliary objectives, but those are still task-aligned, not RL/value.
- FlashMorph / "Morphing into Hybrid Attention": layerwise learnable gates on a **frozen** backbone
  trained on synthetic retrieval data — frozen-backbone gating precedent, but the objective is
  supervised retrieval, not reward/value.

Value/goal-conditioned attention:
- Goal-conditioned policies with multi-head attention steered by a goal query; Dagr (arXiv:2607.13731)
  goal cross-attention; Action-Aware Attention Pooling value heads. Attention conditioned on value/goal,
  but trained with the main policy loss, not as a separate externally-trained head gating memory.

Neuroscience / value-gated memory (mechanistic motivation, not an ML method):
- Dopamine "gating theory" of working memory: phasic DA (a reward-prediction signal) opens the gate to
  write to PFC working memory; tonic DA closes it for maintenance (Braver/O'Reilly gating models;
  Journal of Comp. Neuro. 2006). VTA dopamine RPE as the biological gate for memory consolidation
  ("encode only high-RPE / high-utility events" — eLife 89743).
- Attention-Gated MEmory Tagging (AuGMEnT / CT-AuGMEnT) and "Flexible Working Memory Through Selective
  Gating and Attentional Tagging" (Neural Computation 33:1): on-policy SARSA (RL) trains attention-gated
  feedback that tags which units write to memory — the biologically-grounded ancestor of exactly this idea.
- Neuromodulation-inspired gated associative memory (arXiv:2512.13859).
These establish that "value/reward-gated memory writing via an attention-like gate" is the
neuroscience prior that D-MEM/AURA operationalize — reinforcing that the concept is occupied.

---

## Key references (IDs)
- D-MEM: arXiv:2603.14597 (2026) — RPE-gated agentic memory, frozen backbone. CLOSEST.
- AURA: arXiv:2606.02775 (2026) — action/value-gated memory writes, learned gate.
- Mem-α: arXiv:2509.25911 (2025) — RL/task-reward memory construction (LLM fine-tuned, not frozen).
- Reinforced Attention Learning: arXiv:2602.04884 (2026) — attention distribution as RL policy.
- Recurrent Models of Visual Attention: Mnih et al., NIPS 2014 — hard attention via REINFORCE.
- MoE survey / RL routers: arXiv:2407.06204; Expert-Choice routing (NeurIPS 2022).
- Dopamine gating / attention-gated memory: J.Comp.Neuro 2006; eLife 89743; Neural Computation 33:1 (AuGMEnT).
</content>
</invoke>
