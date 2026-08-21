# Felt Attention — Implementation Spec v0.1 (the pre-GPU logic harness)

**Purpose (per Rohin):** (1) lay out the driving logic precisely enough to verify and
learn from; (2) serve as the harness Claude implements against — every implementation
must trace to a numbered item here; deviations require a spec change first.
**Status legend:** each item is [LOGIC] (verify the reasoning), [PROVEN-TECH] (adopt,
cite), [DECIDE] (Rohin's call), [IMPL] (Claude builds to this contract).

---

## 0. The stack, one screen

```
ENV (crafting sim, text)          ──rollouts──►  outcomes / per-step progress
        │                                              │
        ▼                                              ▼
FROZEN LLM (actor, ReAct)                   VALUE NET V(s)   [Stage 1]
  hidden states h_t ─────────►  FELT HEAD   ◄── value loss   [Stage 2 = THE paper]
                                   │ per-event salience a_t
                                   ▼
              ┌────────────────────┼─────────────────────┐
              ▼                    ▼                      ▼
      context selection    ATLAS-style MLP memory   LoRA consolidation
      (v2, read-side)      write_strength =         weighting (sleep)
                           surprise × (1+β·a_t)
                                   │
                                   ▼
                    BENCHMARK PROBES (held-out exam; never in any loss)
```

## 1. Stage 1 — value net [PROVEN-TECH]

1.1 Environment: crafting sim. Reward = task outcome; dense progress signal =
    recipes-completed / goal-distance. [DECIDE: dense vs sparse-only for v1 —
    recommend dense; sparse is an ablation.]
1.2 V(s) target: λ-returns (Dreamer-style) over rollouts. Recipe: standard TD(λ);
    refresh targets each sleep cycle (non-stationarity guard, arXiv:2306.00840).
1.3 Model: small MLP/transformer over the LLM's pooled hidden state or env state.
    [DECIDE: env-state (cheap, cheats nothing) vs hidden-state (richer) — recommend
    env-state v1.]
1.4 GATE before proceeding (exp2's bar): measured d′ of V-derived per-event salience
    vs ground-truth structural relevance ≥ ~2, AND |corr(salience, frequency)| < 0.3
    on held-out rollouts. If it fails, iterate here — do NOT proceed to Stage 2 with
    a weak signal (garbage-in).

## 2. Stage 2 — the Felt head [LOGIC + IMPL]

2.1 Form: ONE attention-shaped head reading frozen hidden states h_t: queries from
    a learned goal/value embedding; keys/values from h_t. Output: per-event salience
    a_t ∈ [0,1] over tokens/events. ~1-10M params.
    **[DECIDED, audit-forced] v1 = HEAD-AS-SCORER:** the head's output drives
    EXTERNAL ops only (memory writes, LoRA weighting, context ranking); it does NOT
    feed back into the frozen model's forward pass. Zero interference (RLHF-value-
    head pattern). HEAD-AS-MODULATOR (output gates the model's own computation —
    "next token interested in outcome") = v2, via Flamingo zero-init gating; its
    central risk (frozen-model degradation) is out of v1's scope by design.
2.2 Loss (v1): DISTILLATION — a_t regresses the value net's per-event signal
    (TD-error magnitude |δ_t| and/or advantage). Supervised, stable. This is
    Pattern A: an RLHF-style value/probe head — different loss, frozen backbone,
    zero interference with token computation. [PROVEN-TECH: PPO value heads]
2.3 Loss (v2, ablation): end-to-end REINFORCE through task return. Expect
    instability; report honestly.
2.4 Live gating of KV/context (read-side) is v2, via Flamingo-style zero-init
    tanh gate. [PROVEN-TECH: gated cross-attention] NOT in v1.
2.5 The head trains on rollout data ONLY. It never sees benchmark labels, fact
    types, or probe outcomes. [FIREWALL — audit item]

## 3. Stage 3 — consumers [IMPL]

3.1 MEMORY WRITES (v1 primary): ATLAS-style fast-weight MLP (Omega-rule window
    variant, arXiv:2505.23735). Write strength per event:
        w_t = surprise_t × (1 + β · a_t)      [multiplicative; ablate additive]
    surprise_t = the substrate's native gradient-surprise (KEEP it — complementary:
    surprise is frequency-anticorrelated, value is frequency-neutral).
    β=0 recovers stock ATLAS = the baseline.
3.2 LoRA CONSOLIDATION (v1 secondary): sleep-time fine-tune on replayed episodes,
    per-example weight = aggregated a over the episode. Metaplasticity guard
    (EWC-style) deferred to v2.
3.3 CONTEXT SELECTION (v2): a_t ranks what stays in the window. Deferred —
    read/write coupling keeps v1 attributable.
3.4 Sleep schedule: fixed every K episodes (K swept). Adaptive = later.

## 4. Evaluation [IMPL — exists]

4.1 The benchmark (abstract tier built; 26 tests): gist/verbatim paired probes,
    forgetting curves, importance-stratified retention, enforced budget.
4.2 LLM-tier probe protocol for parametric memory: behavioral probes / cued
    generation / log-prob deltas (adapt ForgetBench 2607.26455). [IMPL, hardest 20%]
4.3 Ablation spine (the paper's table): stock-ATLAS (surprise-only) | value-only |
    surprise×value | surprise+value | D-MEM-style heuristic gate ($0-training,
    verified heuristic by direct read) | uniform | no-memory | oracle.
4.3b **KVP-ablation (novelty-isolating, audit-adopted):** a KVP-style retention
    policy (arXiv:2602.10238, ICML 2026 — RL head, frozen LLM, budget) with reward
    swapped from decoding-utility to task-outcome, all else held fixed. If
    outcome-trained beats decoding-trained on the agentic task, that single result
    IS the objective claim against a published baseline. Read 2605.08234 (regime
    diagnostic for value-aware eviction) BEFORE designing this.
4.4 Rules: ≥2 backbones for any LLM claim; ≥3 orderings; programmatic scoring;
    budget = active memory at inference; final lit re-sweep before submission.

## 5. What Rohin puts in

5.1 Compute confirmation (GPUs, hours, dates) — blocks Stage 1.
5.2 Verification passes on [LOGIC] items + the two [DECIDE] calls (1.1, 1.3).
5.3 Constraint edits to this spec — Claude implements only what's spec'd.
5.4 The Stage-1 gate sign-off (1.4) before any Stage-2 spend.
5.5 External review round (ICLR-author friend) on this spec + PAPER_SHEET.

## 5b. Spec amendments (2026-08-12, post-redteam_6 — recorded changes)

- **§1.4 d′ gate REPLACED for run 1:** with V = oracle the gate is vacuous by
  construction. Run-1 gate = **head regret on REAL hidden states** vs the mock
  baseline (0.03): proceed if ≤ ~3× mock; STOP and rethink if ≥0.15 (the
  KVP-vulnerability made measurable). The original d′ gate applies from run 2
  (learned value net).
- **§2.1 amendment:** v1 head is GOAL-AGNOSTIC (single learned query) — a
  recorded deviation; goal-conditioned queries (goal-text embedding → q) are a
  GPU-tier upgrade once real states are in. Rationale: CPU tier showed the
  binding constraint is elsewhere (probe expressiveness), and goal-conditioning
  adds a moving part before the real-state signal is verified.
- **§2.2 amendment:** distillation target is sign-clipped progress max(0,ΔV) in
  v1; |δ| (setback-inclusive) is a GPU-tier ablation — LLM play has setbacks that
  scripted play lacks, so the choice only matters there.
- **§3.2 correction:** LoRA consolidation has NO code — it is run-2 scope, not
  "wired but off" (honesty fix).
- **§4.3 addition:** value_only and surprise+value(additive) arms; keyword_gate
  and oracle_weight are PERMANENT canaries/ceiling in every table.

## 6. Known risks carried forward

R1 value-net quality below the d′ bar (gate 1.4 exists for this). R2 field moves
(re-sweep). R3 parametric probe protocol subtleties. R4 distillation head learns
V's biases — mitigation: report head-vs-V agreement AND head-vs-outcome ablation.
R5 read/write coupling temptation — resist until v2.
