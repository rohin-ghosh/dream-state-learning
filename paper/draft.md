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
[MODEL], the head [SLOT: attains held-out ranking regret R vs the mock-embedding baseline (0.00-0.04 across CPU configs; comparator constant 0.03)],
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
  Value-aware eviction diagnostics (2605.08234). **EMBER (2606.05894)**: closest
  on the objective axis — GRPO fine-tunes the writer LLM with delayed answer-gated
  outcome reward over budgeted *text capsules*; differentiation: sparse terminal
  reward vs our dense TD-value distillation, RL-tuned writer vs frozen backbone +
  tiny head, binary retain vs graded write strength, text vs parametric weights,
  per-episode vs cross-episode. **OSL-MR (2606.10616)**: supervised evidence-label
  scorer under hard token budget; its own motivation — "reward is a sequence-level
  scalar that cannot be decomposed into per-memory credit" [verify quote at
  write-up] — names exactly the gap dense TD salience fills. Our delta: exogenous
  (task-outcome) objective; write-side (memory), not only KV; both 2026 competitors
  select *text to keep*, we learn *how strongly to write into weights*.
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
- **Classic memory-augmented RL (note 24):** the line learned *where to read,
  never what to write* — MERLIN (1803.10760), NEC ("we elect to write all
  experiences"), HCAM, NGU/Agent57, TVT all write everything or on schedule;
  learned gating lives on the read side. PER (1511.05952) prioritized replay
  *sampling* over an intact buffer and explicitly left "which memories to store
  and when to erase them" as future work — the question our write-gate executes.
  MERLIN's insufficiency result targets end-to-end reward gradients through long
  encode-use delays; our frozen pretrained LLM instantiates its unsupervised-
  representation remedy by construction, and our salience is a dense immediate
  per-write scalar (PHRASING RULE: value *modulates* write strength over
  predictive surprise; never "reward decides memory content"). Empirical
  obligations inherited: Isele&Cosgun'18 (reward/TD-selected *storage* caused
  forgetting; distribution-matching won) and d'Autume'19 (random writes matched
  surprisal selection) ⇒ random-write and coverage-matched baselines at equal
  budget are mandatory, and β=0 vs β>0 is load-bearing.
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
the gap is the room memory competes in. Measured (Qwen2.5-7B-Instruct, ReAct,
120-step cap, 30 eps/mode): win@manual = 0.90, win@none = 0.233, room = 0.667.
Smaller backbones fail the reasoning gate honestly (1.5B: 0.03; 3B: 0.17 at
60 steps) — the gate table doubles as a capability ladder. [SLOT: per-depth
breakdown from s0_gates.json ledger; 2nd backbone.]
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
5.2 S0 gates (Qwen2.5-7B, ReAct, 120 steps): 0.90 / 0.233, room 0.667;
capability ladder 1.5B 0.03 → 3B 0.17 → 7B 0.90.
5.3 Head quality (fact-level, layer −8, held-out episodes): attention-form
AUC 0.9803 / regret 0.0148; +hidden-layer control 0.9967 / 0.0022. Signal
readability chain preserved in §6: step-TD text-keyed 0.216 → ctx-keyed
0.125 (linear) → 0.055 (MLP) → binary fact-credit ~solved. Interpretability
check: within structural facts, used-vs-unused AUC 0.943 (score means 0.952
vs 0.691; detail 0.001) — the head learned dependency credit, not fact type.
5.4 S3 main table (2000 eps, matched budget): felt_b12 +0.391/0.944 vs
label_ref +0.386/0.944 (RENAMED from "oracle_weight": binary type-label
weighting is a label-informed REFERENCE, not a supremum — graded credit can
legitimately allocate a finite write budget better than a 0/1 label, and felt
edges past it twice with consistent sign/magnitude; state this in one
sentence or a reviewer will assume leakage). Keyword canary +0.326
(felt−canary +0.065, t=34.4 SIG); uniform +0.306; random +0.300; surprise
+0.279 (felt−surprise +0.112, t=8.0 SIG); dmem +0.214.
Held-out-SEED robustness (same generator config, worlds 2-3 never seen in
head training): felt +0.436 vs label_ref +0.431, felt−canary +0.066 (t=29.5),
felt−surprise +0.119 (t=6.3). NOTE: absolute dissociation levels shift with
world subset (easier worlds lift every policy); PAIRED within-world gaps are
the primary statistics and are stable across subsets (0.065 vs 0.066).
[SLOT: cross-CONFIG generalization — frozen head evaluated on depth-3 and
depth-5/branching-4 worlds; the "property of value-trained salience vs
property of the generator" defense.]
5.5 [SLOT: S4 winnability at fixed context for top conditions.]
5.6 [SLOT: second backbone replication.]
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
