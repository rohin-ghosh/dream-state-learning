# PAPER SHEET — Felt Attention (project) + retention benchmark (Paper 1)

**Date:** 2026-08-11 · **Purpose:** the complete, testable state of the work for external
review. Every claim carries an evidence status: **[PROVEN-CPU]** (running code, numbers
reproducible in the repo), **[VERIFIED-LIT]** (checked by direct read or multi-agent
search with IDs), **[DESIGNED]** (specified, not yet built), **[NOT-DONE]** (declared gap).
Reviewers: please attack the statuses, not just the prose — anything marked DESIGNED or
NOT-DONE is explicitly unproven and we say so.

Repo: github.com/rohin-ghosh/dream-state-learning · Reproduce:
`PYTHONPATH=. python3 run_benchmark.py` and `PYTHONPATH=. python3 experiments/exp4_end_to_end.py`
(CPU, minutes) · Tests: `PYTHONPATH=. python3 tests/test_structmem.py` (27/27).

---

## 1. One-paragraph thesis

Continual agents need a long-term memory that, as experience outgrows capacity, keeps
**relational structure** (dependencies, rules — "gist") and sheds **episodic detail**
("verbatim"). We propose (a) **a benchmark** that measures exactly this — the first
psychology-grounded, *memory-type-agnostic* retention benchmark, probing RAG, parametric,
and text-bank memories through one interface against ground-truth dependency graphs; and
(b) **Felt Attention**: a single attention head grafted onto a frozen LLM, trained on a
*value* signal (not token loss), whose weights allocate context selection, memory writes,
and consolidation fine-tuning. The value function trains on task outcomes only; the
benchmark is a held-out exam it never sees.

## 2. Claims and their evidence

### C1. Outcome-trained allocation beats UNIFORM allocation in a real interference-limited memory, and the advantage grows with data horizon; where a per-event value signal exists, it beats both. [PROVEN-CPU]
*(Wording corrected per external audit: the untrained per-event z-score (value_z)
beats the outcome-trained per-item head at every capacity — 0.63 vs 0.25 AP at
d=128 — because per-item post-hoc credit is weak under relational outcomes (exp2.5).
The measured statistic is trained−uniform; value_z's superiority is itself a
finding: per-event tags ≫ post-hoc credit, see C2.)*
`experiments/exp4_end_to_end.py` (20 seeds, paired tests). Memory = linear associative
store in R^d (real superposition crosstalk); all policies get identical total write
budget (pure allocation comparison); value heads see ONLY (presence, outcome).
- Scale sweep @d=64: trained−uniform advantage −0.010 (n.s., 100 eps) → +0.030 → +0.054
  (t=3.4) → **+0.099 (t=7.8) at 800 episodes / 3,246 facts** — monotone.
- Relational binding memory: outcome-trained pair-weights **AP 0.481 vs co-occurrence
  0.013 at d=128 (+0.468, t=9.3)**; oracle = 1.0.
- Falsified en route (kept honestly): "advantage grows as capacity→0" is FALSE — at
  d=16 interference swamps even the oracle (0.437). Correct claim: helpful scarcity =
  data ≫ capacity, with capacity large enough to express selection.
- Canary: at value-signal d′=0, value_z does NOT beat uniform (−0.177).
- LIMIT: linear associative memory, not a deep fast-weight MLP; synthetic streams.

### C2. The value signal must be frequency-decorrelated and per-event; naive aggregations are frequency-contaminated. [PROVEN-CPU]
Three-flip history, fully documented (exp1 → exp1-corrected → external audit):
- max/sum aggregations of a noisy per-event value sit ABOVE chance at d′=0 (0.204/0.137
  vs chance 0.024) = frequency contamination, measured.
- **value_z = vsum/√count** (the sufficient statistic) passes the d′=0 canary AND beats
  frequency **+0.464 (t=41.1)** at d′=1.5. Per-EVENT tags ≫ post-hoc per-item credit
  (0.63 vs 0.25 AP in exp4).
- Trained per-item value ties frequency on the hardened benchmark (+0.012, n.s.) — the
  exp2 "green light" for per-item trained value is RETRACTED in-repo.
- Meta-method: every one of these reversals was found by adversarial code-level review,
  not narrative review. Reports of record: `experiments/REPORT_exp1_corrected.md`,
  `REPORT_exp2.md` (with retraction banners), `REPORT_exp4.md`.

### C3. Relational (per-pair) value recovers structure that per-item value cannot, in an intermediate-concentration regime. [PROVEN-CPU]
- Under conjunctive outcomes, per-item value collapses (dP 7.84→1.8, exp2.5); learned
  per-pair value recovers (benchmark: relational−item_lifted **+0.202 (t=3.8) @ 4
  recipes, +0.200 (t=3.9) @ 3**, n.s. at 8 (data-starved) and 1 (per-item suffices) —
  an inverted-U, reported as such, not as a monotone win).
- item_lifted baseline is relu-product (audit-corrected from signed product; relational
  wins by MORE vs the corrected baseline).

### C4. The benchmark itself is adversarially hardened. [PROVEN-CPU]
`structmem_bench/` (27 tests). Rigor layer: random-sampler, constant-scorer, and
label-permutation canaries all at chance (~0.03 vs base 0.024); frequency provably
uninformative on marginal-matched facts (dP −0.06) and provably failing the designed
hard cases (rare-critical kept 0.000; recurring-useless kept 0.703). Survived: 3-agent
red-team + independent execution audit. Catalogue of caught-and-fixed exploits: a
zero-information index-ranking method scored AP=1.000 via stable-sort tie-breaking
(fixed: seeded layout permutation + tie-safe ranking + constant-scorer canary); "surprise
recovers rare structure" was a layout artifact (0.53→0.02); degenerate linear-outcome
base rate (2.1%→~0.5); budget-fill artifacts (budget-free AP is primary metric).

### C5. The competitive intersection is open (as of 2026-08-11). [VERIFIED-LIT]
Verified by ~10 searches + direct reads; IDs in research_notes/12–21. The load-bearing
verifications:
- **D-MEM (2603.14597) is TRAINING-FREE** — direct read of method: surprise = embedding
  z-score; utility = zero-shot GPT-4o-mini JSON call; "RPE" = min(1, 1[U≥τ]·U·(S+β)).
  No gradients. Routes to external buffers/KG. ⇒ the *trained* gate has no direct
  competitor; D-MEM is the mandatory $0-training heuristic baseline.
- **TMEM (2606.04536):** RL(GRPO)-shaped LoRA writes but ONLINE, WITHIN-episode, no
  head, no consolidation phase, no forgetting. Cousin + baseline.
- **COVE (2608.01234):** offline cross-episode internalize-vs-external split with
  anti-recitation — but rule+LLM-judge decision (not learned head), per-item, surface-
  form volatility (not relational-vs-episodic). Closest on the consolidation axis.
- **ATLAS (2505.23735, Google):** fast-weight MLP substrate, surprise-driven, single-
  sequence only (never cross-episode). Substrate to adopt. (Distinct from ATLAS
  2608.04334, topological-graph continual RL — acronym collision, cite by ID.)
- **PEAM (2605.27762):** MoE-LoRA parametric skills, heuristic worthiness score.
- Benchmarks: **ForgetBench (2607.26455)** forgetting curves, parametric-only;
  **RECON (2607.16716)** provenance DAG, holistic scoring; **MemTrace (2606.17328)**
  age-resolved, external-only; **eMEM-Bench (2606.03374)** 8 cog-psych paradigms,
  embodied-only + system-coupled; **Ground Truth First (2607.21962)** script-first
  generation + tenure-crossover. **No benchmark bridges parametric + external memory
  through one probe interface; gist-vs-verbatim (fuzzy-trace) and spacing effects are
  UNPORTED as eval paradigms; importance-stratified retention is unclaimed.**
- **C5 amendments (2026-08-11 external audit + follow-up):**
  - **KVP, "Learning to Evict from Key-Value Cache" (2602.10238, Apple, ICML 2026):**
    per-head RL policies on a FROZEN LLM allocate KV retention under budget, reward =
    future *decoding utility*. ⇒ the CONTEXT consumer of our tri-consumer claim is
    OCCUPIED. Surviving differentiators: (a) our reward = distance-to-task-OUTCOME
    (KVP learns what the model will want; we learn what the TASK will need); (b) the
    tri-consumer unification (context + LTM writes + weight consolidation from ONE
    head/one value signal) — nothing found crosses it. KVP = mandatory citation AND
    the cheapest novelty-isolating experiment: swap KVP's reward for task-outcome,
    hold all else fixed.
  - **TRIM-KV (2512.03324):** learned per-token importance gate, frozen LLM, enforced
    budget (KV-scope, distillation-trained, no outcomes/cross-episode). "Importance-
    stratified retention is unclaimed" is WEAKENED → cite TRIM-KV, claim the
    outcome-trained + cross-episode + consolidation deltas.
  - **PM-Bench (2607.12385):** ports the Virtual-Week paradigm to agent-memory eval
    ⇒ "paradigm-porting" has precedent (with eMEM-Bench); our compound (paradigm
    probes × memory-type-agnostic × enforced budget) still unclaimed.
  - AgeMem revised (Jul 2026): now unifies LTM+STM under one GRPO policy — re-read
    before submission; occupies more of the LTM-writes consumer than note 05 said.
- KNOWN RISK: field moves monthly; **final re-sweep scheduled ~Sep 20** (NeurIPS
  notifications ~Sep 29 will dump currently-invisible accepted work onto arXiv).
  Naming: "StructMemEval" (2602.11243) exists — our benchmark will be renamed.

### C6. Compute feasibility. [VERIFIED-LIT]
Precedent-grounded (note 21): minimum credible LLM tier ≈ **50–150 GPU-h (~$100–400)**;
workshop-grade ≈ **500–1,000 H100-h** (one 8×H100 node, 3–5 days). Field's trained-memory
runs are small (Memory-R1: 152 training pairs; typical 100–205 GRPO steps; ceiling
Mem-α ≈ 2,300 H100-h). Cost lever: parametric memory keeps wake-context short — the
architecture is its own cost control.

## 3. Architecture of record (Felt Attention) [DESIGNED]

1. **Stage 1 — value net V(s)** trained separately on task outcomes (λ-returns / PRM
   recipes; mature). For text envs the LLM is the action model (ReAct).
2. **Stage 2 — THE new object:** one attention head grafted onto the frozen LLM,
   trained on VALUE loss (v1: distillation of per-event TD-error/advantage — supervised,
   stable; end-to-end REINFORCE is v2/ablation). Everything else frozen.
3. **Stage 3 — three consumers of the head's weights:** (a) context/KV selection,
   (b) fast-weight LTM writes, (c) LoRA consolidation weighting. Write-side wired first
   (offline, benchmark-measurable); read-side second (read/write coupling).
Ablation spine: learned head vs D-MEM-style heuristic gate vs surprise vs uniform.
Non-stationarity guard: refresh value targets each sleep cycle; bound per-cycle policy
drift (the "What Model Does MuZero Learn?" caution, 2306.00840).

## 4. Benchmark v2 design (Paper 1) [DESIGNED]

Positioning: **first psychology-grounded, memory-type-agnostic retention benchmark.**
- **Probes as validated-paradigm ports:** gist/verbatim paired probes (fuzzy-trace —
  UNPORTED, our headline), age-stratified forgetting curves, interference and serial-
  position anchor probes (already-ported paradigms, cited as anchors: 2406.15981,
  2603.00270, 2410.08133), spacing-effect probes (unported).
- **One probe interface across backends** (`write/query/probe_fact`): RAG, parametric/
  LoRA, text banks — the two literatures currently never compared (axis verified open).
- **Importance-stratified retention** (open axis) + **enforced budget** (BEAM reports,
  doesn't enforce) + script-before-text generation (adopting 2607.21962's recipe).
- Environments: crafting sim (ground-truth DAG; built) + ScienceWorld slice
  (comparability with Auto-Dreamer/CLIN).
- Eval-fragility rules (from 2602.19320 + 2505.11942): programmatic graph scoring (no
  LLM judge), ≥2 backbones for any LLM-tier claim, ≥3 curriculum orderings, fair
  baseline tuning, budget = active memory at inference.

## 5. Declared gaps [NOT-DONE] — attack these; we already have

- **No LLM has touched any experiment.** All results are abstract-tier simulations.
  The LLM tier is scaffolded (`structmem_bench/llm_tier.py`, plumbing CPU-tested) but
  no real backend implemented, no GPU run.
- **The parametric probe protocol** ("did the *weights* retain fact X") is designed-only;
  hardest 20% of the benchmark.
- **The Felt-Attention head does not exist** — no code, only the architecture + the
  exp4 miniature standing in for the loop.
- **Gist/verbatim probes not yet implemented** (design only); construct-validity review
  by someone who knows fuzzy-trace theory is wanted.
- exp4's memory is linear-associative, not a deep fast-weight MLP; "surprise" there is
  a 1/count proxy, NOT ATLAS's gradient surprise — its failure there must not be read
  as "ATLAS fails."
- Value-net quality for the real environment is unmeasured (exp2's d′ bar: hand-set
  signals need d′≈3 or frequency-decorrelation to help; whether a trained net clears
  this on crafting-sim rollouts is an open empirical question).
- No human baselines; "psychology-grounded" means paradigm-ported probes, NOT validated
  human-comparison claims.
- Single-author project; no second implementation of any result.

## 6. Provenance / method note

Every headline number in §2 has a runnable script and per-seed data in-repo; every
reversal (three on the value-aggregation question alone) is preserved with banners
rather than deleted. Adversarial review protocol: critics read code and per-seed
numbers, prompted to refute; two full red-team rounds + one external execution audit
are in `research_notes/redteam_*.md` and reflected in the fixes. The journal
(`research_notes/JOURNAL.md`) is the complete decision history.
