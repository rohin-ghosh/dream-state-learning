# PREWORK — everything before the first Colossus lease (Stage 1)

**Rule:** the lease executes a frozen plan; nothing is designed on GPU time (July's
lesson). Everything below is CPU-buildable and testable in-repo first.

## What the Apple paper (KVP) did for us vs what it didn't

DONE-FOR-US (adopt): the proof that a small policy head trains against a NON-token
objective with everything else frozen (per-head MLPs, ~600K params, REINFORCE w/
leave-one-out baseline, offline on precomputed traces); the all-budgets ranking
objective Σ_b R_b; attention-free inference from (k,v,pos) features.
NOT done for us: (1) their target is endogenous (future attention, free from traces)
— ours is exogenous (task outcome, needs rollouts + a value signal); (2) they stop at
KV eviction — our head also drives LTM writes + consolidation; (3) no memory system,
no cross-episode anything, no benchmark. That's the work.

## Regime sweep verdict (exp5, done)

Two windows, two signals:
- value_z (per-event salience tags): wide EVERYWHERE (+0.31..+0.52) — robust.
- trained (outcome-trained): grows with DATA and structure — widest at long horizon
  + ample capacity + richer recipes (n_ep=800, d=128, recipes=8: **+0.24** and
  climbing). Consistent with exp4's bitter-lesson curve.
→ **LLM-tier game setting: long horizons (≥800 episodes/world-run), ample-but-
bounded memory, rich recipe structure (8+ recipes, deep chains).** The trained
window grows with data ⇒ the game generator must make rollouts CHEAP (it does).

## Status ledger

### ✅ Done (in repo)
- Benchmark abstract tier (27 tests, red-teamed, audited) + paradigm probes
- exp0–exp5 (mechanism miniature + regime map)
- Specs: IMPLEMENTATION_SPEC (the harness), PAPER_SHEET, BENCHMARK_SPEC v0.2
- Text-game engine EXISTS but is ARCHIVED: `archive/dream_state/environments/
  minecraft_sim.py` (persistent worlds, crafting DAG, verified scripted-agent run)

### ✅ ALL BUILT (2026-08-12) — ledger GREEN, ready for audit → lease

Original list with outcomes:
1. **Game v2** (resurrect + upgrade the archived sim): deep crafting HIERARCHIES
   (chains, not just pairs — per regime verdict), script-before-text fact labelling
   (every episode emits ground-truth structural/detail facts), long-horizon
   persistent worlds, config-driven complexity knobs. [~2 days]
2. **Oracle value fn**: BFS distance-to-goal over the crafting DAG + per-step TD
   salience (Δ distance). 20 lines + tests. [half day]
3. **Rollout infrastructure**: batch world/goal/curriculum generation ("a fuck ton
   of synthetic games"), trajectory log format (text, events, outcomes, per-step
   oracle values), replayable + seedable. [~2 days]
4. **The head** (KVP-adapted): reads frozen hidden states; distillation loss on
   oracle TD-salience + all-budgets ranking objective; unit-tested on CPU with a
   tiny model (Qwen2.5-0.5B) so GPU is pure scale-up. [~2–3 days]
5. **ATLAS-style memory module**: fast-weight MLP, window/Omega-style update,
   surprise term, value modulation w = surprise×(1+β·a). CPU-testable at small dims
   (upgrade of exp4's linear store). [~2 days]
6. **Parametric probe protocol** (benchmark LLM tier): behavioral probes / cued
   generation / logprob deltas; mock-tested on CPU. [~2 days, hardest 20%]
7. **Run harness**: wake (play w/ memory) → sleep (consolidate) → eval (probes +
   winnability); config-driven; **checkpoint/resume sized to 48h leases**. [~2 days]
8. **Baselines wiring**: no-memory, full-context@budget, RAG, surprise-only (β=0 =
   stock ATLAS), D-MEM-style heuristic gate, uniform. [1 day]

#### Session-2 outcomes
- items 1-3: `game/` (9/9 tests) — procedural DAGs, oracle, rollout infra
- items 4-5: `felt/head.py` + `felt/fastweight.py` — head learns+transfers
  (regret 0.025), memory expresses allocation under capacity
- item 6 (numpy tier): `mem.probe()` = the parametric probe; LLM logprob variant = GPU week
- items 7-8: `felt/harness.py` (checkpoint/resume, tested) + `felt/baselines.py`
  (8 policies incl. dmem_style heuristic gate)
- INTEGRATION (exp6): full pipeline SIG on held-out worlds — surprise-only retains
  detail>gist (-0.125); felt head flips it (+0.121, AP 0.707, t=5.9)
- SIZING.md: calibration invariant, budget arithmetic (35-65 GPU-h), sanity gates

## [DECIDE] Base model
- **Primary: Qwen2.5-1.5B-Instruct** (fast rollouts on 1×A100, competent at text
  games). **Second backbone: Llama-3.2-3B-Instruct** (different family — satisfies
  the ≥2-backbones eval rule). **CPU plumbing: Qwen2.5-0.5B.** 7B only if the 1.5B
  can't play the game at all (checked in prework via a handful of local rollouts).

## Sequencing questions answered (Rohin's)
- **Game complexity on CPU?** Yes — generator + verified engine, all CPU.
- **Policy on CPU?** Yes — the oracle value is graph traversal (BFS), exact, free.
  The LEARNED value net comes later as the "signal is learnable" result.
- **Train head + memory simultaneously?** NO for v1 — staged: (a) generate rollouts
  (GPU inference), (b) train head offline on logged traces vs oracle salience
  (KVP-style, cheap), (c) freeze head, run memory system through immense re-runs
  with head-weighted writes, (d) benchmark + winnability. Simultaneous training is
  a coupling confound; staging keeps every result attributable. (Joint training =
  explicitly a v2 experiment.)

## Stage 1 (first lease) — what actually runs on GPU
i. Sanity: 1.5B plays game v2 (few hundred rollouts) — success-rate floor check.
ii. Bulk rollout generation w/ logging (the main inference spend).
iii. Head training (forward passes + head backprop — cheap).
iv. Wake/sleep memory runs: head-weighted vs surprise-only vs baselines.
v. Benchmark probes + winnability table. All checkpointed for 48h leases.
