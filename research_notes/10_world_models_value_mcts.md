# World Models, Model-Based Planning, Value/Policy & MCTS

Date: 2026-07-13
Cluster: world models, model-based planning, value/policy, MCTS
Scope: triage the Dreamer / MuZero / TD-MPC / planning lineage for what to BORROW into
Dream-State's value/PFC policy and its role in **weighting memory consolidation**, plus the
non-stationarity warning for a **changing policy**, and a Paper-1-vs-Paper-2 call on MCTS.

Project mapping reminder:
- CURRENCY = reward (frozen).
- POLICY = value/PFC mechanism that assigns credit to **delayed** reward by judging value at
  the current state; this value signal **weights attention during consolidation** (high-value
  experiences imprint strongly).
- Future role: "subconscious simulation" = imagined rollouts.
- Hard constraint: our POLICY is **non-stationary** (keeps changing during continual learning).

---

## THE 3 CRITICAL DELIVERABLES

### (1) Best existing mechanism for credit assignment under DELAYED reward — to adapt as a consolidation weight

**Recommendation: use a learned value function as the salience signal, and estimate its targets
with Dreamer-style λ-returns computed over (imagined or replayed) rollouts. Prioritize/weight
consolidation by a blend of value magnitude V(s) (salience) and |TD-error|/advantage (surprise).**

Why this is the right primitive:
- The whole point of a **value** V(s) is that it is "expected future return judged at the current
  state" — i.e. it stands in for delayed reward **before the reward has arrived**. That is exactly
  the project's definition of the POLICY's job. So the value head *is* the credit-assignment engine;
  you do not need the reward to land to get a per-experience weight.
- **Dreamer (V1→V3)** computes **λ-returns** (a TD(λ) mixture of n-step bootstraps) over short
  imagined rollouts to train the actor/critic. λ-returns are the cheapest principled way to smear a
  sparse/delayed terminal reward back onto every intermediate state. Each visited state gets a scalar
  return estimate you can read off directly as an imprint weight. This runs **offline in latent
  space** — a natural fit for a "sleep" consolidation pass over replayed experience.
- **MuZero / EfficientZero** give a *higher-fidelity* version of the same idea: the **MCTS-refined
  root value** (visit-count-weighted) is a better value target than a raw return, and it is what you
  would use if you later want tree-search-quality credit. **EfficientZero's "value prefix"** (an LSTM
  that predicts the *sum* of rewards over a horizon rather than per-step rewards) is a purpose-built
  fix for **delayed/sparse** reward credit assignment — worth borrowing conceptually even without the
  full MuZero stack.
- Established prior art for "weight replay by value-surprise": **Prioritized Experience Replay**
  (|TD-error| priority). Our consolidation-weighting is essentially PER generalized — but we also want
  the **value-magnitude** term (high-value episodes imprint strongly), not only surprise. So:
  `w(experience) ≈ f( V(s) , |TD-error| )` — salience × learning-progress.

Concrete adaptation for Paper 1: attach a small learned critic; during the sleep pass, recompute
λ-return targets over replayed trajectories with the *current* critic; set each experience's
consolidation weight from (normalized value) blended with (|TD-error|). No tree search required.

### (2) The key WARNING about learned models/values when the policy is NON-STATIONARY

**Headline (from "What Model Does MuZero Learn?", He, Suau, Oliehoek et al., ECAI 2024,
arXiv:2306.00840): a value-equivalent learned model is only accurate for the policy that
*collected the data*, and its accuracy degrades monotonically as the evaluated policy deviates
from that data-collection policy. The model does NOT generalize to off-distribution policies —
so planning improvement from it is fundamentally bounded.** They further show MuZero's model is
often not even accurate enough to evaluate its *own* behavior policy.

Why this is the load-bearing caution for us:
- Our POLICY keeps changing. Any value/model fit under an **old** policy becomes **systematically
  biased** for the **new** policy. Two direct consequences:
  1. **Consolidation weights computed with a stale value head will mis-rank experiences** for the
     current policy — you can imprint the wrong memories strongly.
  2. **"Subconscious simulation" (imagined rollouts) will silently break** once the policy moves off
     the model's training distribution — the model looks fine on-distribution and lies off-it.
- Corroborating evidence across the cluster:
  - **EfficientZero** needs an explicit **off-policy correction** (recompute value targets with the
    *latest* model) precisely because stale, off-policy targets are wrong — an admission of the same
    non-stationarity problem.
  - **Dreamer** sidesteps it by doing imagination **on-policy** from recent states with a critic
    trained on-policy — a design tax you inherit if you plan.
  - **UniZero** (arXiv:2406.10667) traces MuZero's collapse on long-horizon tasks to **entanglement
    of the latent state with implicit history**, and fixes it by decoupling memory from state with a
    transformer — a reminder that "what the latent encodes" is fragile and history-contaminated.
- **Mitigations to bake in:** (a) refresh value targets with the current critic every sleep cycle
  (EfficientZero-style); (b) trust-region / KL regularization on how far the policy moves per cycle
  so the value stays approximately valid — this is exactly **Policy Consolidation** (Kaplanis et al.,
  ICML 2019, arXiv:1902.00255): a cascade of policy copies at multiple timescales, KL-coupled, so the
  current policy is regularized by its own history without needing task boundaries; (c) treat any
  learned model used for imagination as **valid only near the current policy's distribution**.

### (3) Does MCTS/planning belong in Paper 1 (B) or Paper 2 (A)?

**Recommendation: DEFER MCTS/planning to Paper 2 (A). Paper 1 should use a plain scalar learned
value (Dreamer λ-return style) to weight consolidation — no tree search.**

Reasons:
1. **Scope/claim purity.** Paper 1's thesis is *wake-sleep consolidation with value-weighted
   attention*. You only need a *value scalar per experience* to test that. MCTS is a heavy,
   orthogonal mechanism that confounds the core ablation (was the gain from consolidation-weighting,
   or from search?).
2. **The non-stationarity warning makes planning low-ROI in Paper 1's regime.** Deliverable (2) shows
   planning gains are bounded exactly when the policy is off-distribution — which is our continual
   setting. Adding MCTS before you've stabilized the value under a moving policy spends a lot of
   engineering for fragile returns.
3. **Planning's natural home is the "subconscious simulation" story**, which is already earmarked for
   later. Imagined rollouts + tree search (MuZero/EfficientZero/TD-MPC2 for control; **LATS** for the
   LLM-agent flavor: MCTS with an LLM value function + reflection) is a clean Paper 2 contribution,
   and Paper 2 is where you can afford the off-policy correction machinery it demands.
4. **Cost.** MCTS + learned dynamics is the single biggest complexity/compute sink in this lineage;
   Dreamer-style latent imagination gives most of the value-estimation benefit at a fraction of the
   cost.

Paper-1 stance: value head + λ-returns for consolidation weighting. Paper-2 stance: introduce a
learned world model, imagined rollouts (subconscious simulation), and MCTS-refined values, with
explicit off-policy correction and policy-move KL constraints.

---

## TOP-5 RANKED SHORTLIST (by usefulness to our value/consolidation design)

| # | Paper | One-line thesis (≤12 words) | Why we care | TAG |
|---|-------|------------------------------|-------------|-----|
| 1 | **Dreamer V1–V3** (Hafner et al., 2019–2023) | Learn latent world model; train actor-critic by imagination. | λ-returns = the delayed-reward credit engine → per-experience consolidation weight; imagination = subconscious sim; on-policy imagination is the safe-under-nonstationarity template. | **BUILD-ON** |
| 2 | **What Model Does MuZero Learn?** (He/Oliehoek, ECAI 2024) | Value-equivalent model only valid near data-collection policy. | THE warning for a changing policy: stale value/model mis-weights consolidation and breaks imagined rollouts off-distribution. | **CAUTION** |
| 3 | **EfficientZero V1/V2** (Ye 2021 / 2024) | Sample-efficient MuZero via consistency, value-prefix, off-policy correction. | Value-prefix = targeted delayed/sparse-reward credit; off-policy correction = the concrete fix for non-stationary targets. | **MECHANISM-TO-BORROW** |
| 4 | **Policy Consolidation for Continual RL** (Kaplanis, ICML 2019) | KL-cascade of multi-timescale policy copies resists forgetting. | Directly about non-stationary policy + consolidation; gives a trust-region way to keep value valid as policy moves. | **MECHANISM-TO-BORROW** |
| 5 | **MuZero** (Schrittwieser et al., 2019/20) | Value-equivalent model + MCTS planning, no known rules. | MCTS-refined root value = gold-standard credit target; but defer the search itself to Paper 2 (see Deliverable 3). | **CONTEXTUAL-HISTORY** |

---

## Secondary notes (triaged, not deep-read)

- **World Models** (Ha & Schmidhuber, 2018) — VAE+RNN "dream" env; train controller inside it.
  First "subconscious simulation" proof-of-concept. TAG: CONTEXTUAL-HISTORY.
- **PlaNet** (Hafner et al., 2018/19) — latent dynamics (RSSM) + CEM planning, pixels. Direct
  Dreamer precursor; planning-in-latent. TAG: CONTEXTUAL-HISTORY.
- **Dreamer 4** (Hafner et al., 2025, arXiv:2509.24527) — "imagination training": learn to achieve
  goals **purely from offline data** inside a fast scalable world model (mines diamonds in Minecraft,
  100× less data than VPT, no env interaction). Highly relevant to a **sleep/offline** subconscious-
  simulation phase learning from replay without acting. TAG: MECHANISM-TO-BORROW (Paper 2).
- **UniZero** (Pu et al., 2024, arXiv:2406.10667) — transformer world model that **decouples latent
  state from latent history**, fixing MuZero's long-horizon collapse from history entanglement.
  Relevant to memory-architecture: keep "what the state is" separate from "what happened." TAG:
  MECHANISM-TO-BORROW.
- **TD-MPC / TD-MPC2** (Hansen et al., 2022/2024) — plan with a learned *value* + latent model via
  short-horizon MPC, bootstrapped by a value beyond the horizon. Clean "value-guided planning"
  template for Paper 2 control tasks. TAG: MECHANISM-TO-BORROW (Paper 2).
- **Language Agent Tree Search / LATS** (Zhou et al., 2023/24, arXiv:2310.04406) — MCTS over an LLM
  agent's action/reasoning tree; LLM acts as generator + **value function** + reflection. The direct
  analogue of "MCTS in our agent"; the natural Paper-2 planning mechanism for the LLM-agent setting.
  TAG: BUILD-ON (Paper 2).

---

## Design takeaways for Dream-State

1. **Paper 1 consolidation weight:** `w = normalize(V(s)) ⊕ |TD-error|`, with V's targets recomputed
   each sleep cycle via λ-returns using the *current* critic. No MCTS.
2. **Guardrail against non-stationarity:** refresh value targets every cycle (EfficientZero) and
   bound per-cycle policy movement with a KL/trust-region term (Policy Consolidation). Never assume a
   value/model fit under an old policy is valid for the new one.
3. **Paper 2 = subconscious simulation:** learned latent world model + imagined rollouts (Dreamer 4's
   offline imagination-training is the closest template for a sleep phase) + MCTS-refined values
   (MuZero/EfficientZero for control, LATS for LLM-agent), all with explicit off-policy correction.
4. **Latent hygiene (UniZero):** if we learn latents, decouple state-representation from history so
   consolidation compresses "what happened" without corrupting "what the state is."

## Sources
- What model does MuZero learn? — https://arxiv.org/abs/2306.00840 ; https://www.fransoliehoek.net/docs/He24ECAI.pdf
- Dreamer 4 (Training Agents Inside of Scalable World Models) — https://arxiv.org/abs/2509.24527 ; https://danijar.com/project/dreamer4/
- UniZero — https://arxiv.org/abs/2406.10667
- Policy Consolidation for Continual RL — https://arxiv.org/abs/1902.00255 ; https://proceedings.mlr.press/v97/kaplanis19a.html
- Language Agent Tree Search (LATS) — https://arxiv.org/abs/2310.04406
