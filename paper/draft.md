# [DRAFT v0.1 — pre-lease] Felt Attention: Outcome-Trained Salience for What Agent Memory Keeps

**Target:** ICLR 2027 (abstract Sep 18, full Sep 25) · arXiv preprint immediately after
submission (pre-NeurIPS timestamp). Every `[SLOT]` fills from lease results. Numbers
already present are final CPU-tier results (reproducible in-repo). Tone rules: no hype
words; every claim carries its evidence or its slot; limitations are load-bearing text,
not boilerplate.

---

## Title candidates
1. *Felt Attention: Outcome-Trained Salience for What Agent Memory Keeps*
2. *What the Task Will Need: Outcome-Trained Write Policies for Agent Memory*
3. *Gist Under Budget: Measuring and Steering What Survives in Agent Memory*
(Pick after S3 results — 1 if the head wins, 3 if the benchmark is the stronger result.)

## Abstract (skeleton)

Long-running LLM agents must consolidate experience under a memory budget, yet the
write policies of current parametric memories are driven by *surprise* — what the
model finds novel — rather than *value* — what the task will need. We introduce
(i) a retention benchmark for agent memory with ground-truth relational structure:
episodes in procedurally generated crafting worlds emit labelled *gist* (recipe
edges, resource bindings) and *verbatim* (episodic detail) facts, scored under
enforced budget with floor-corrected probes, anti-gaming canaries, and paradigm-
ported measures (gist/verbatim dissociation, forgetting curves, importance-
stratified retention); and (ii) *Felt Attention*: a single scorer head on a frozen
LLM, distilled from an oracle value signal, whose per-event salience modulates
memory writes (w = surprise × (1+β·salience)). On real hidden states of a frozen
[MODEL], the head [SLOT: attains held-out ranking regret R vs mock baseline 0.03],
and value-modulated writes [SLOT: improve gist retention +X over surprise-only and
+Y over an action-keyword canary at matched budget; winnability +Z at fixed
context]. We report the full negative-control ledger: with mock embeddings, no
realistic policy — including our head — beats trivial canaries, and our initially
positive pipeline result was traced to three measurement artifacts we then
eliminated; the corrected instrument is what makes the [positive/negative] GPU-tier
finding credible.

## 1. Introduction

Paragraph 1 — the regime: agents that live longer than their context. Consolidation
is unavoidable; the question is not whether to forget but *what survives*. Current
evals measure recall accuracy, not the *kind* of knowledge retained.

Paragraph 2 — the objective gap: parametric memories (test-time-training line)
write by surprise/reconstruction — endogenous signals in service of next-token
prediction. KVP (Apple, ICML'26) learns eviction against *future decoding utility*
— still endogenous: what the model will attend to. Nothing writes by *task
outcome*: what the world will reward. One sentence of thesis: **KVP-style systems
learn what the model will want; Felt Attention learns what the task will need.**

Paragraph 3 — the measurement gap: you cannot claim structure-selective retention
without ground truth for structure. Our benchmark supplies it by construction
(script-before-text), scores gist and verbatim separately at enforced budget, and
polices itself with canaries that provably catch the gaming strategies we
ourselves fell for (§6.3).

Paragraph 4 — contributions: (1) the benchmark (memory-type-agnostic probe
interface: parametric, context, retrieval); (2) the head + write rule; (3) the
[SLOT: main GPU result]; (4) the negative-control ledger as a methodological
contribution (four reversals caught by adversarial code review, all preserved).

## 2. Related Work

- **Parametric / fast-weight memory:** TTT → Titans → ATLAS (2505.23735; Omega
  rule; surprise-driven; single-sequence only) → MIRAS/HOPE. None cross-episode,
  none outcome-driven. PEAM (2605.27762): MoE-LoRA skills, *heuristic* worthiness
  score. TMEM (2606.04536): RL-shaped LoRA writes but online, within-episode.
  COVE (2608.01234): offline cross-episode internalize-vs-external, rule+judge
  decision, surface-form volatility ≠ relational structure. GradMem (2603.13875):
  learned write, self-supervised.
- **Learned retention under budget:** KVP (2602.10238): per-head RL eviction,
  frozen LLM, *future-attention* reward — the context consumer, endogenous
  objective. TRIM-KV (2512.03324): learned per-token retention gate, distillation.
  Value-aware eviction diagnostics (2605.08234). Our delta: exogenous
  (task-outcome) objective; write-side (memory), not only KV.
- **Gated/heuristic memory routing:** D-MEM (2603.14597) — verified by direct
  read to be TRAINING-FREE (surprise z-score × prompted utility); our $0-training
  heuristic baseline. Mem-α/AgeMem/Memory-R1: RL tool-call memory ops on external
  stores.
- **Memory benchmarks:** ForgetBench (2607.26455) forgetting curves,
  parametric-only; RECON (2607.16716) provenance DAG, holistic; MemTrace
  (2606.17328) age-resolved, external-only; eMEM-Bench (2606.03374) cog-psych
  paradigms, embodied-only, system-coupled; Ground-Truth-First (2607.21962)
  script-first generation (we adopt); PM-Bench (2607.12385) Virtual-Week port.
  Unclaimed compound: gist/verbatim (fuzzy-trace) as paired probes × memory-type-
  agnostic interface × enforced budget. [Re-sweep scheduled ~Sep 20 — NeurIPS
  notification dump lands on the deadline.]
- **Cognitive grounding:** CLS (McClelland '95; Kumaran '16), synaptic tagging
  (Frey&Morris '97), behavioral tagging, SHY renormalization (Tononi&Cirelli),
  fuzzy-trace gist/verbatim — cited as *functional* motivation, no consciousness
  claims.

## 3. The Benchmark

3.1 Environment: FeltCraft — procedural crafting DAGs (depth/branching knobs),
persistent worlds, move-anywhere semantics (knowledge is actionable). Script-
before-text: every episode emits labelled facts — gist = recipe edges + resource
bindings; verbatim = per-episode decor + incidental counts — before text is
rendered, so labels are exact.
3.2 Calibration invariant: win(model+manual) ≥ 0.85; win(no-context) ≤ 0.35;
the gap is the room memory competes in. [SLOT: measured gates for MODEL.]
3.3 Probes: floor-corrected retention (score minus matched never-written fake —
removes generic-similarity credit), random detail sampling, gist/verbatim paired
dissociation, forgetting curves (within-type), importance strata (recipe-degree).
3.4 Canaries (each catches a documented failure): constant-scorer (position/tie
leaks), label permutation, frequency-dissociation≈0 (exposure confound),
keyword_gate (action-type ≡ label leak), oracle_weight ceiling.
3.5 Budget enforcement + memory-type-agnostic interface (write/query/probe_fact):
parametric fast-weights, context-FIFO, RAG store under one probe protocol.

## 4. Felt Attention (the method)

4.1 Setting: frozen LLM actor plays FeltCraft (ReAct); oracle value V = exact
remaining-cost over the crafting DAG (BFS closure); per-event salience = clipped
TD of V (signed TD logged; the oracle carries the full horizon, so one-step Δ is
not myopic).
4.2 The head: one attention-shaped scorer on frozen hidden states, σ(q·Wk h_t/√d),
distilled on oracle salience; never sees probe labels (firewall). KVP-style
offline training on logged traces; all-budgets ranking objective as eval.
4.3 The write rule: w_t = surprise_t × (1 + β·a_t). β=0 recovers the stock
surprise-driven substrate — the baseline is embedded in the formula.
4.4 What v1 is NOT: no live gating of the LLM's computation (scorer, not
modulator); no learned value net (oracle isolates the mechanism; learnability is
the follow-up); no LoRA consolidation surface (run 2).

## 5. Experiments

5.1 Setup: [MODEL(s)], A100-80GB, N episodes, worlds/seeds table. Baselines:
uniform, surprise-only (β=0), D-MEM-style heuristic gate, keyword_gate (canary),
felt at β∈{4,12}, oracle_weight (ceiling), context-FIFO, RAG-unbounded,
no-memory.
5.2 [SLOT: S0 gate table.] 5.3 [SLOT: S2 head quality — regret vs 0.03 mock
baseline, per layer.] 5.4 [SLOT: S3 main table — dissociation + AP(gist) per
policy; paired felt−keyword_gate and felt−surprise.] 5.5 [SLOT: S4 winnability
at fixed context for top conditions.] 5.6 [SLOT: second backbone replication.]
5.7 Ablations: β sweep, layer sweep, value-only vs surprise×value vs additive.

## 6. The Negative-Control Ledger (methodological contribution)

6.1 With mock embeddings, no realistic policy beats the canaries — reported, not
hidden. 6.2 The oracle-weight ceiling (+0.11/+0.22 at h≥128) shows the
instrument's dynamic range. 6.3 Four documented reversals, each caught by
adversarial code-level review and each now a permanent test: (a) tie-break
position leak (a zero-information ranker scored AP=1.0); (b) value-aggregation
frequency contamination (max/sum above chance at d′=0; z-score is the sufficient
statistic); (c) gist/verbatim exposure confound (frequency faked 0.21
dissociation); (d) the pipeline's own first positive result (a fallback constant
+ type≡action leak + cosine-floor confound + salted-hash irreproducibility).
Claim: benchmarks in this area need adversarial self-testing as a first-class
component; we ship ours.

## 7. Limitations

Synthetic environment (though externally anchored: [SLOT: ScienceWorld slice if
run]); oracle value (learnability of the signal untested here); scorer-only head
(no read-side gating); single-GPU scale; [SLOT: whatever S2/S3 verdicts impose];
the field moves monthly — comparisons frozen at [date].

## 8. Checklist before submission
- [ ] Final lit re-sweep (~Sep 20) — expect NeurIPS-notification arXiv wave
- [ ] Benchmark rename (StructMemEval collision) — candidate: FeltCraft-Bench
- [ ] ≥2 backbones on any LLM-tier claim; ≥3 seeds; programmatic scoring only
- [ ] Reproducibility: one-command repro for every table (already true CPU-tier)
- [ ] Strip vision/roadmap language ("self-determinance" etc.) from all sections
- [ ] Internal NVIDIA review pass + ICLR-author friend pass
