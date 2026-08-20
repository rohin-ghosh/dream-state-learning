# 32 — v2 experiment design (adopted decisions, 2026-08-19)

Source: Rohin's design session (state/salience/dream/scaling). Canonical
one-pager: SPEC_V2.md. This note records the WHY behind each pin.

## Adopted
1. **Vocabulary:** "vibey memory" → **induced regularities** — generalizations
   over experience present in no single episode. The paper hangs on this term.
2. **Claim form:** not "we beat RAG" — **different scaling curve** (x = episodes,
   y = performance, one line per substrate) + measured crossover. Report the
   regime where RAG wins (exact recall) as instrument calibration. Map, not
   victory.
3. **Salience, two information sets (reconciled):** encoding-time salience =
   state, online, NO hindsight (filter into STM); consolidation-time salience =
   dream, offline, HAS episode outcomes (policy for LTM). The encoding/dream
   gap is a prediction error → dopamine = RPE, one predictor + supervisor.
   Two losses from one renorm pass (salience error trains state layer; corrected
   valuation trains prompter). **Formalize all four boxes (state/dream/use/
   salience), implement amortized, train none — that's papers 2–3.**
4. **Dreamer v2 = one prompted LLM call** over the life log (state, experiences,
   outcomes, value logs) → look-back memories as TEXT. Cross-episode patterns,
   NOT per-episode summaries (that's the thing RAG structurally can't produce).
   Dumb dreamer = raw transcription → separates substrate claim from policy
   claim (2×2). Renormalize-then-write: dream re-scores with hindsight.
5. **Append-only resolution:** the LOG is append-only; the LoRA is retrained
   from the full curated corpus each dream cycle (wasteful, clean, no drift
   ambiguity). Drift allowed by design; measurement uses frozen checkpoints.
6. **Reads:** LoRA read = just generation from the adapted model. No ReAct.
   The open question is WHEN to read, not how.
7. **Compute parity:** same reasoner + same prompter in every arm; only the
   memory substrate varies. (Reviewer-proofing; also isolates the variable.)
8. **Environment:** custom AlchemyWorld (built, alchemy/). Latent parameters:
   stable across life, never stated, randomized per run (contamination-proof
   via nonce names + randomized rules). Compositional: essences predict unseen
   pairs. Complexity taxonomy: exact recall / attribute composition / chain
   depth / distractors (incl. visible false-correlate features). NOT meta-RL:
   latent fixed for the whole life (continual, not fast adaptation).
9. **Long-context arm:** don't handicap — let the real window break; the break
   is a result ("not applicable beyond N episodes"). Small base model = honest
   limit.
10. **Metrics:** held-out pair prediction (ground truth free — we set the
    latent) with confabulation priced (abstain=0.25, confident-wrong=0 +
    confab rate) + task success. Gates: G1 seen-pair recall ≥0.9 (LoRA arms),
    G2 zero essence-token leakage (grep over all emitted text — property in
    the physics), G3 no_memory flat.
11. **Scale:** episodes 60/240/960; LoRA rank {8,32} (ceiling moves with rank
    ⇒ capacity limit, not mechanism failure). Batched episode generation =
    throughput only, no claim. Parallel agents with separate memories = v2.1+
    (union raw logs, retrain — the P-ladder from a new angle).
12. **A-Mem** (NeurIPS'25): strong published baseline to add after naive RAG;
    also the PROBE — run their explicit importance heuristic vs our dreamer
    over the same log, compare what each keeps (agree/disagree figure). Tune
    their k honestly.
13. **Domain shift / memory refresh / multi-goal lives:** real, deferred —
    discussion-section future work. One environment, one latent set, one life.

## Deferred (written down, not built)
- Off-policy RL reading of renormalize-then-write (learned value fn + policy
  improvement) — paper 3.
- KV-space dreaming (train on raw KV): own research project, no precedent —
  v2 dreams on TEXT.
- Salience-weighted replay ("simulate more similar memories" = generative
  upsampling of salient memories) — needs its own gate (synthetic-data risk).

## Status
SPEC_V2.md written (red-pen items: arm list, memory text format, episode
counts). alchemy/ package built: world/env/player/dreamer/lora_mem/evals/
run_smoke. Smoke = 8 ingredients, 20 eps, ScriptedExplorer for coverage,
Qwen2.5-0.5B local (MPS) for dream+LoRA+read.

## Sizing pre-registration (2026-08-19, alchemy/sizing_mc.py + sizing_mc.json)
Method: information-availability ceiling — fraction of held-out pairs an
IDEAL learner (union-find over product-family evidence; conservative,
product-only) can deduce from the life log. No memory system can beat it.
- 4 essences saturates by 30 eps (latent too small — no scaling regime).
- LOCKED: N=64 ingredients (8 inert), K=12 essences, inventory 6, 30%
  structural holdout. Ceiling: 0.13@30 → 0.39@60 → 0.47@120 → flat@960.
- Two regimes named for the paper: ACCRUAL (≤~120 eps) vs REPETITION
  (>120): info constant, exposure grows — consolidation's home turf,
  retrieval's failure mode. MC uses the fastest-coverage explorer, so real
  LLM play shifts accrual right = conservative.
- Memory format LOCKED (Rohin): mix — declarative facts + cross-episode
  patterns + QA slice + negative knowledge.
- Capacity estimate: ≤~2k pair facts + 64 class memberships; LoRA r=16 on
  7B ≈ 30M params — capacity not binding at this scale (lit: ~2 bits/param,
  Physics-of-LMs 3.3); exposure/repetition is the binding constraint,
  which is the thesis. Rank sweep {8,32} still runs (ceiling-moves test).
- Compute estimate (A100, vLLM, 7B player): one 960-ep life ≈ 8M tok ≈
  30–45 min; measurement points are prefixes (no extra lives); fresh-task
  eval ≈ 20 min/arm/point; dreams negligible; LoRA trains minutes.
  Full 2×2 + rails × 3 points × 5 seeds ≲ 3 A100-days — inside quota.
