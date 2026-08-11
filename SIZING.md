# SIZING — the estimation math for the first GPU run

**Principle (Rohin):** doesn't need to be perfect first time; needs to be good
enough that the first run tells us exactly what to tweak. Every estimate below
comes with the sanity measurement that recalibrates it (§5).

## 1. Model ↔ game difficulty calibration

**The invariant to engineer:** game difficulty must come from MISSING WORLD
KNOWLEDGE, not from reasoning depth. Operationally:

    win_rate(model + full manual in context)  ≥ 0.85     [reasoning is easy]
    win_rate(model + no memory, tight window) ≤ 0.35     [knowledge is the wall]
    → the gap is the room memory systems compete in.

Where "manual" = the world's structural facts (recipes + locations) injected into
context. If the first inequality fails → the game's ACTION side is too hard for
the model (simplify verbs/parsing, add few-shot examples), NOT a memory problem.
If the second fails high → deepen the DAG / widen worlds (more knowledge to miss).

**Model: Qwen2.5-1.5B-Instruct.** Rationale: instruction-following is sufficient
for 5-verb text games with examples; rollouts are ~4-5× cheaper than 7B; the head
reads hidden states (d=1536) which are rich at 1.5B. Escalate to 3B only if the
manual-win-rate gate fails after prompt iteration.

## 2. Knowledge load vs context budget (the "data ≫ capacity" regime, in tokens)

Per world (defaults depth=4, branching=3, n_raw=6, locations=8):
  structural facts = recipes (12) + location bindings (6) ≈ **18 facts ≈ 250 tok**
Context budget for the memory-constrained condition: **512 tok window** → holds
~35% of one world's manual after obs/goal overhead. Cross-world (agent serves N
worlds interleaved): knowledge load scales ×N while budget stays fixed —
**interleave 3 worlds → load ≈ 5-6× budget** (the exp4/5 regime). Knob order if
differentiation is weak: interleaved worlds ↑, depth ↑ (4→6 ⇒ 18→28 facts), decor
noise ↑.

## 3. Rollout + token arithmetic (per episode, 1.5B, A100, vLLM)

  steps/episode ≈ 25-45 (solver: ~25 at depth 4; LLM: assume 1.5× worse ≈ 40)
  tokens: obs ~80, action ~10, window ≤1k → prefill ~40×1k=40k, decode ~400
  A100 + vLLM, 1.5B, batch 32 envs: decode ~3-6k tok/s, prefill ≫ →
  **throughput ≈ 600-1200 episodes/hour** (conservative planning number: 600).

## 4. Stage-1 GPU budget (arithmetic, not vibes)

| stage | units | est. GPU-h |
|---|---|---|
| S0 sanity gates (§5): manual/no-memory win rates, 300 eps | 300 eps | 0.5-1 |
| S1 bulk rollouts for head training: **10k eps** (KVP-scale traces; exp6 needed 75 w/ mocks — 10k gives real-state headroom), hidden states cached to disk (~10k×40 events×1536×2B ≈ 1.2 GB) | 10k eps | 10-17 |
| S2 head training on cached states (1-10M params, distillation) | — | 1-2 |
| S3 probe-tier eval: FIXED-TRAJECTORY replay — one rollout set, all 8 policies scored on retention probes (embedding passes only) | 3k eps replayed | 2-4 |
| S4 closed-loop winnability: memory feeds context, behavior changes — TOP-4 conditions only × 3 seeds × 200 eps | 2.4k eps | 4-8 |
| S5 second backbone (Llama-3.2-3B) repeat of S3+S4-lite | — | 6-10 |
| slack/re-runs (×1.5) | | ×1.5 |
| **TOTAL first full pass** | | **≈ 35-65 GPU-h** |

Fits in **one or two 48h single-A100 leases**, ~4% of monthly quota. The expensive
mistake this table prevents: running closed-loop (S4) for ALL policies — the
two-tier design (broad probe tier / narrow closed-loop) is the main cost lever.

## 5. Sanity gates → recalibration rules (what the first hours tell us)

| measurement (S0) | if it says | tweak |
|---|---|---|
| win@manual < 0.85 | game too hard to PLAY | simplify verbs, add few-shot, (then 3B) |
| win@no-mem > 0.35 | game too easy to KNOW | interleave worlds ↑, depth ↑, window ↓ |
| head regret on real states ≫ mock regret (0.03) | hidden states don't carry salience | try later layers / concat layers; if still bad at ~0.15+, STOP — the KVP-vulnerability (note 23 §3) is real and the architecture needs rethink, cheap to know at hour 12 |
| oracle-salience → felt gap tiny in S3 | value signal not differentiating on real game | raise β sweep, check salience→fact attachment granularity |
| S4 winnability flat while S3 probes differ | retained facts not USED by the model | context-injection format iteration (how memory is rendered into prompt) |

## 6. What is deliberately NOT in run 1

Learned value net (oracle only — net is run 2, after the mechanism is proven on
real states); relational/pair head; adaptive sleep; joint head+memory training;
LoRA third surface (S3 slot reserved, wired but off); Minecraft skin.
