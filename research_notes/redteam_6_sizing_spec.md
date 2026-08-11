# Red-team 6 — SIZING.md arithmetic + spec↔code consistency audit

Audited 2026-08-11 against: SIZING.md, IMPLEMENTATION_SPEC.md v0.1, PREWORK.md,
`felt/` (head, fastweight, baselines, harness), `game/` (dag, engine, generator),
`structmem_bench/llm_tier.py`. Empirical checks run with `PYTHONPATH=. python3`;
throughput/calibration claims checked against external benchmarks.

---

## 1. SIZING.md arithmetic — verified / corrected

### §2 knowledge load — mostly checks out, one wrong number
- **18 facts at defaults: VERIFIED.** depth=4 × branching=3 = 12 recipes + 6
  location bindings = 18 (`World.generate` confirms). ~250 tok: each canonical
  fact string is ~10–14 tok → 180–250; plausible.
- **CORRECTION: "depth ↑ (4→6 ⇒ 18→28 facts)" is wrong.** depth=6, branching=3,
  n_raw=6 gives 18 recipes + 6 bindings = **24 facts**, not 28 (verified by
  running `gen_dag`). 28 would need branching↑ too. Doesn't change any budget,
  but it's an arithmetic error in the knob table.
- The "512-tok window holds ~35% of manual" figure is prompt-design-dependent
  (assumes ~420 tok obs/goal/instruction overhead). Soft but defensible; the
  "5-6× budget at 3 worlds" claim then follows (750 tok load vs ~90–180 tok free).

### §3 rollout throughput — conservative and structurally correct, with one
### internal inconsistency
- **steps/episode: VERIFIED.** Scripted solver on depth-4 goals: mean 24.2
  (min 15, max 40) over 20 worlds — "~25 at depth 4" is accurate; "LLM ≈ 40"
  (1.5×) is a reasonable planning assumption.
- **The sequential-stepping concern is handled correctly.** The estimate charges
  full re-prefill every step (40 × 1k = 40k prefill/episode — i.e., no prefix-cache
  credit), and the batch is explicitly ACROSS 32 environments. Latency math for
  lockstep batch-32: prefill 32k tok ≈ 0.3–1 s (1.5B on A100 ≈ 1e14 FLOPs at
  30–50% MFU) + decode. At 10 decode tok/step: ~0.5–1.3 s/step → 40-step episode
  ≈ 20–50 s per batch of 32 → **~2,300–5,700 eps/hr**. So 600–1200 is conservative
  by 2–4×, which is the safe direction.
- **External anchor:** Qwen2.5-1.5B-Instruct official vLLM numbers: ~183 tok/s
  decode at batch 1 on A100-80GB (BF16). Batch-32 aggregate decode of 3–6k tok/s
  (SIZING's number) = 32 × ~100–180 tok/s — consistent with near-linear batch
  scaling for a 1.5B model. The claim is realistic.
- **INCONSISTENCY: "decode ~400/episode" (10 tok/step) assumes action-only
  output, but IMPLEMENTATION_SPEC §0 specifies a ReAct actor.** With THOUGHT+ACTION
  (~60–100 decode tok/step), decode ≈ 2.5–4k tok/episode and decode latency
  dominates: per-step ≈ 1–2 s → **~1,200–2,000 eps/hr**. The 600–1200 planning
  number *still holds*, but only because it was 2–4× conservative to begin with;
  the line-item token math doesn't describe the workload the spec defines. Fix the
  line or note "ReAct thoughts eat the slack."
- One unbudgeted assumption: batch-32 lockstep wastes capacity as episodes finish
  at different lengths (15–40+ steps observed). An async env pool feeding vLLM
  continuous batching fixes this — **that driver does not exist in the repo** (§4).

### §4 hidden-state cache — arithmetic right, design mostly right
- 10,000 × 40 × 1536 × 2 B = **1.229 GB ≈ 1.2 GB. VERIFIED** (1.14 GiB).
- Matches the head's contract: `felt/head.py` consumes one d_h vector per EVENT
  (event = step, obs+action), so one layer's last-token state per event in fp16
  is exactly what `train_batch`/`salience` need (head trains in fp32 on top;
  fp16 storage is fine for inputs).
- **Gap:** SIZING §5 gate-3's own fallback is "try later layers / concat layers."
  If only one layer is cached, that fallback costs a full re-forward of the S1
  corpus (~S3-scale GPU-h). Caching all ~28 layers is ~34 GB on disk — trivial.
  Recommendation: cache several candidate layers in S1; the 1.2 GB line sizes
  only the single-layer plan.
- Unwritten and non-trivial: the token-span → event mapping (which token's hidden
  state is "the event") — no extraction code exists at all (§4).

### §4 GPU-h table — internally consistent
- S1: 10k eps ÷ 600–1200 eps/hr = 8.3–16.7 h → "10-17" ✓ (slightly conservative).
- S0: 300 eps → 0.25–0.5 h → "0.5-1" ✓. S4: 2,400 eps → 2–4 h → "4-8" ✓
  (2× headroom is warranted: memory-injected contexts are longer).
- Column sum: low 23.5 h, high 42 h; ×1.5 → **35.25–63 ≈ "35-65" ✓.**
- Nit: gate-3's mock-regret reference says 0.03; exp6/PREWORK report 0.025.

## 2. Calibration gates — realism verdict

**win@no-mem ≤ 0.35: almost certainly satisfiable** (if anything it will be near
0, which is fine for the gate).

**win@manual ≥ 0.85 for Qwen2.5-1.5B-Instruct: AT SERIOUS RISK.** External
evidence on ALFWorld-class text games:
- Qwen2.5-1.5B **zero-shot direct prompting: ~4%** success on ALFWorld; PPO-trained
  reaches ~54%; heavily trained (BEACON / milestone-RL) 1.5B reaches 91–95%.
- I.e., 1.5B models only clear 0.85 on comparable tasks **after RL fine-tuning**,
  which is exactly what this plan does NOT do (frozen backbone by design).

Mitigating: FeltCraft is far easier than ALFWorld — 5 exact verbs, deterministic,
and the manual literally contains every recipe edge + location. The failure mode
that remains is not knowledge but 25–40 steps of format adherence + dependency-DAG
resolution + inventory tracking, which is precisely where 1–2B instruct models
break. **Verdict: treat 1.5B-clears-0.85 as unlikely-to-marginal; plan the budget
for the 3B escalation path (≈2× S0–S4 inference cost, +~15–25 GPU-h) rather than
treating it as a tail case.** The gate itself is well-designed (it's checkable in
hour 1) — but note PREWORK says this exact check happens "in prework via a handful
of local rollouts," and **there is no LLM-rollout code, so the check has not
happened and cannot happen with the current repo** (§4). If 3B becomes primary,
the ≥2-backbone rule still holds with Llama-3.2-3B (different family), but the
"1.5B is 4-5× cheaper" rationale in SIZING §1 dissolves.

## 3. Spec ↔ code deviations (IMPLEMENTATION_SPEC is explicit: deviations require
## a spec change first — none of these have one)

1. **§2.1 head form — DEVIATION.** Spec: "queries from a learned goal/value
   embedding." Code (`felt/head.py`): a single free learned vector `q` — no goal
   input, no value-embedding input; the same query for every goal/world/episode.
   The docstring quietly renames it "learned goal-query." Consequence: the head is
   a goal-agnostic event-type scorer; it cannot score the same event differently
   under different goals, though oracle TD-salience (its target) is goal-relative.
   Works on CPU because scripted play makes event-type ≈ progress; may not survive
   LLM play. Either amend the spec to "learned static query (v1)" or condition q
   on a goal embedding at the GPU tier.
2. **§1.4 Stage-1 d′ GATE — NOT IMPLEMENTED ANYWHERE.** No code computes d′ of
   V-derived salience vs structural ground truth, nor |corr(salience, freq)| < 0.3,
   on real rollouts. exp1 uses d′ as a *synthetic generator knob*; exp2 measures
   freq-corr on synthetic streams only. Worse, the gate is *unmeasurable as specced*
   in run 1: V is the BFS oracle (SIZING §6 defers the learned value net to run 2),
   so d′ is trivially high and the gate is vacuous. Spec §5.4 makes Rohin's 1.4
   sign-off a blocker "before any Stage-2 spend" — run 1 as planned spends on
   Stage 2 with the gate skipped by construction. Needs a recorded spec change
   ("gate 1.4 applies to the run-2 learned V; run 1 substitutes oracle").
3. **§2.2 loss target — PARTIAL DEVIATION.** Spec: distill |δ_t| and/or advantage.
   Code: `td_salience = max(0, V_before − V_after)` (sign-clipped progress),
   max-normalized per episode. Negative-progress events get salience 0 by
   construction. Invisible under scripted-optimal play (δ ≥ 0), but LLM play will
   produce setbacks that |δ_t| would rank salient and this target zeroes out.
4. **§1 value net — absent** (oracle only). Consistent with SIZING §6's deferral,
   inconsistent with the spec's "Stage 1 [PROVEN-TECH]" framing. Spec unamended.
5. **§3.1 write rule — MATCHES.** `value_modulated_weights` = surprise × (1+β·a),
   β=0 = stock baseline, exactly as specced. Caveats (both self-declared in
   docstrings, acceptable): "surprise" is pre-write MSE (a gradient-magnitude
   proxy), and the substrate is a plain SGD MLP in the "Omega-rule window spirit,"
   not literal ATLAS.
6. **§4.3 ablation spine — MISMATCH.** Spec spine: stock-ATLAS | value-only |
   surprise×value | surprise+value | D-MEM | uniform | no-memory | oracle.
   Code `PROBE_POLICIES`: uniform, surprise_only, dmem_style, felt_b4, felt_b12,
   no_memory, context_fifo, rag_unbounded. **Missing: value-only, surprise+value
   (the spec explicitly says "ablate additive"), and oracle-salience.** The
   PREWORK ledger's "8 policies" is a different eight. Note SIZING §5 gate 4
   references the oracle-salience policy — which doesn't exist (a ~5-line add to
   `_weights`, but absent).
7. **dmem_style is not D-MEM.** Code: surprise z-score > 0.5 threshold. D-MEM:
   surprise × prompted-utility. Docstring admits it's a CPU stand-in; the faithful
   LLM-tier version (the one the paper's table needs) has no code.
8. **§4.3b KVP-ablation (the novelty-isolating baseline): no code.**
9. **§3.2 LoRA consolidation: zero code** (grep for "lora" over the repo: nothing
   outside archive). SIZING §6 says the LoRA surface is "wired but off" — it is
   **not wired**.
10. **§2.5 firewall — COMPLIANT.** Head trains only on rollout salience; probe
    labels never enter any loss. Verified across head.py / harness.py / exp6.
11. **§4.2 LLM-tier probes — scaffold only.** `make_parametric_backend` raises
    NotImplementedError; the real ReAct loop is a one-line comment inside
    `run_llm_tier`; `MockLLM` returns a canned "inspect".

## 4. Missing-from-plan (the honest gap between "ledger GREEN" and reality)

**S4 closed-loop winnability has NO code.** `felt/harness.py` docstring itself:
"closed-loop winnability is a GPU-tier stage; slot reserved." What's absent:
- LLM player loop (prompt template, ReAct parsing, retry-on-garbage handling);
- vLLM integration (client or in-process engine) — no torch/transformers/vllm
  import exists anywhere outside comments;
- **memory→context injection** — the mechanism SIZING gate 5's own remediation
  ("context-injection format iteration") presumes exists; there is nothing to
  iterate on, not even a manual-rendering function for the win@manual condition;
- win-rate measurement + the S0 gate harness;
- hidden-state extraction/caching (layer choice, event↔token-span mapping);
- async batched env-stepping driver (the batch-32 assumption in §3);
- LLM-faithful D-MEM baseline; KVP-ablation; LoRA sleep stage; logprob-delta
  probe backend.

By PREWORK's own per-item costing (~1–2 days each), that is **roughly 5–8 days of
prework-grade build** — comparable to everything built in session 2. Calling the
ledger "✅ ALL BUILT — GREEN, ready for audit → lease" is **not honest**: PREWORK
item 7 promised "eval (probes + winnability)" and item 6's parametric-probe
backend raises NotImplementedError. What's true: the CPU *mechanism* pipeline
(game → oracle → head → memory → probe tier) is genuinely built and integrated
(exp6). What's false: that the lease can start with "a frozen plan; nothing
designed on GPU time" — the entire LLM-facing half would be designed on the lease.
(Nit: the ledger is dated 2026-08-12 — tomorrow.)

## 5. Gate coverage — which of SIZING §5's five gates are day-1 measurable

| gate | code status |
|---|---|
| 1. win@manual ≥ 0.85 | **NOT measurable** — no LLM player, no manual renderer |
| 2. win@no-mem ≤ 0.35 | **NOT measurable** — same missing loop |
| 3. head regret real vs mock (0.025) | **HALF-ready** — train/eval + all-budgets regret code exist and are tested; blocked on hidden-state extraction (unwritten) |
| 4. oracle→felt gap in S3 | **NEARLY ready** — probe harness runs and checkpoints, but the oracle-salience policy is missing from `felt/baselines.py:_weights` (trivial add) |
| 5. S4 flat vs S3 differs | **VIBES** — requires unbuilt S4 |

Net: **0 of 5 gates are runnable on day 1 of the lease; 3 of 5 are blocked on the
same unbuilt LLM-player loop.** Since gates 1–2 are the recalibration mechanism
the whole sizing leans on, the LLM loop is the critical-path prework item, and it
should be smoke-tested locally (0.5B on CPU/MPS, per PREWORK's own plan) before
any lease.

## Bottom line
The arithmetic is sound (one wrong knob number: 24 not 28 facts at depth 6; one
internal inconsistency: decode budget assumes non-ReAct output) and the throughput
range is conservative against both FLOPs math and published Qwen2.5-1.5B vLLM
numbers. The plan's two real exposures are (a) the ≥0.85 manual gate for a frozen
1.5B — external evidence says budget for 3B; and (b) the ledger overstates
readiness: everything LLM-facing (S0 gates, S4, extraction, vLLM, faithful
baselines) is unbuilt, and the spec's own Stage-1 gate (§1.4) is skipped by
construction in run 1 without a recorded spec change.

Sources: [Qwen2.5 speed benchmark](https://qwen.readthedocs.io/en/v2.5/benchmark/speed_benchmark.html), [Milestone-guided policy learning (ALFWorld small-model numbers)](https://arxiv.org/pdf/2605.06078), [vLLM A100 benchmarks](https://www.databasemart.com/blog/vllm-gpu-benchmark-a100-80gb).
