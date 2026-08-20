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

## Sizing v2 REVISION (2026-08-19, after Rohin's context-capacity catch)
Rohin: "learnable" must mean learnable BEYOND context, not from-the-log —
the accrual phase itself has to outrun the context window, and 60 eps is
nothing. Confirmed by MC: old config's accrual ended at ~120 eps ≈ 42k
tokens (fits in 128k — regime not hard). RE-LOCKED: N=256 (32 inert),
K=32 essences (528 rules), inv 6, points 60/240/960/3840. Ceiling
0.00→0.20→0.46→flat; 128k context breaks between 240 (45k tok) and 960
(184k tok) WHILE info is still arriving. Full evidence, context-budget
table, throughput plan, pre-registered predictions: SPEC_V2.md Part II (single doc
per Rohin: overview on top, depth below). Perf fixes en route: recipe-map cache
(960-ep life: minutes → 0.1s), nonce space 256→2048 names (N=256 worlds
exhausted it and hung). Doc structure per Rohin: spec = high-level top +
constants below; all depth in the same doc's Part II.

## Connected-data principle + two ceilings (2026-08-19, Rohin)
DOCUMENTED PER ROHIN: (1) The experiment's data must be CONNECTED/
STRUCTURAL — memory must learn high-dim patterns that extrapolate; the
game latent is intelligently generated as a structure spectrum: Stratum R
(i.i.d. random core, incompressible, tests retention-at-scale), Stratum G
(hidden geometric meta-pattern over essence classes → predicts rules never
observed in any form; retrieval structurally cannot; 🔴 v2 inclusion),
Stratum D (distractors/false correlates, tests not-learning). Not a
"couple games into LoRA" problem — a scale+throughput problem.
(2) Ceiling metric upgraded after Rohin's perfect-reasoner challenge: the
i.i.d. core IS underivable (incompressibility is the design point — data
is the only winning resource), but the learner's evidence model was too
weak; ceiling v2 transfers any observed outcome across proven same-class
pairs: asymptote 0.46→0.77 (residual = inert pairs, 1−(7/8)²). Report
both ceilings; normalize by perfect-reasoner one.
(3) Sizing requirement raised (Rohin): accrual phase alone must span
5–10× context. N=512/K=64: accrual ~1920 eps ≈ 377k tok (3× of 128k,
12× of Qwen native 32k). N=1024/K=96 sweep pending → target ≥5× of 128k.

## Final size lock (2026-08-19): N=1024, K=96
Sweep (both ceilings): accrual to ~6k eps ≈ 1.2M log-tokens = 8-11x of a
128k window, 30x+ of Qwen native 32k — Rohin's 5-10x requirement MET.
Even 1M-token context breaks inside accrual. N=2048/K=128 rejected (12x
but first 2k episodes at ceiling 0.01 = dead points). Points:
960/1920/3840/7680/15360. Perfect-reasoner ceiling 0.43/0.75/0.77/flat.
Nonce generator made exhaustion-proof (numeric fallback) after N=1024 hang.
