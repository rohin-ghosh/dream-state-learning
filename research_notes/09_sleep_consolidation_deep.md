# Sleep / Dreaming / Consolidation — Deep Dive (Paper B prior art)

Scope: component decomposition of sleep-style consolidation systems, ranked by closeness to **Paper B** =
*sleep-time consolidation procedure that does **attention-weighted post-training of a small parametric memory**, such that **STRUCTURE survives and DETAIL is forgotten** (structure-up / detail-down = the "Missing Diagonal").* Embodied target: ALFWorld / AI2-THOR.

All arXiv IDs below were verified against arXiv/HF on 2026-07-13 (each resolves to the described paper). Verification column at the end.

Component vocabulary used throughout: **IMP** = importance/salience tagging · **NREM** = abstraction / Hebbian-strengthen + synaptic-downscale · **REM** = recombination / dreaming · **VF** = value-based forgetting · **RPL** = replay (raw or generative) · **DN** = downscaling / renormalization · **WHEN/WHAT** = learned-or-heuristic governance of consolidation timing & selection.

---

## TL;DR verdict

- **Single closest prior-art SYSTEM to B: PEAM (2605.27762)** — *Parametric Embodied Agent Memory, Minecraft.* It is the only system that matches B on all three structural axes at once: (parametric small-memory substrate = MoE-LoRA) × (embodied agent experience) × (explicit governance of when/what to consolidate). It is our nearest neighbor by mechanism+substrate+domain.
- **Closest on the *retention-selectivity* axis: EVAF / "Memory Depth, Not Memory Access" (2606.26806)** — the only system that explicitly separates *what to keep parametrically* (durable goal-conditioned tendencies) from *what to leave to retrieval* (shallow facts). This is the closest thing in the literature to a keep-X / discard-Y consolidation split — but it is **goal-vs-fact, not structure-vs-detail**, and it names forgetting as unsolved.
- **Richest component donor: SCM (2604.20943)** — full NREM/REM/importance/value-forgetting/self-model stack, and it is the only one whose NREM stage contains an explicit **synaptic downscaling** step, which is the mechanistic seed of our "detail-down."
- **The Missing Diagonal is still missing.** No verified paper (a) measures a structure-retention-vs-detail-forgetting curve, (b) uses an **attention-weighted consolidation loss** to enforce structure-up/detail-down, or (c) learns the consolidation routing policy against retention outcomes. Those three are ours to build.

---

## Top-5 ranked shortlist (closest → farther)

| # | Paper (ID) | One-line thesis (≤12 words) | Tag | Precise gap to structure-up/detail-down |
|---|---|---|---|---|
| 1 | **PEAM** (2605.27762) | Internalize embodied experience into parameter-resident skills via MoE-LoRA | CLOSEST-PRIOR-ART | Internalizes *skills* (procedural), not a structure/detail retention split; worthiness score is heuristic, not attention-weighted; no structural-retention metric |
| 2 | **EVAF / Memory Depth** (2606.26806) | Surprise/valence-gated LoRA consolidation for durable goal persistence | CLOSEST-PRIOR-ART (retention axis) | Split is goal-vs-fact, not structure-vs-detail; gating heuristic not attention loss; GPT-2/TinyLlama on conversational event streams, not embodied |
| 3 | **SCM** (2604.20943) | Sleep-stage memory with NREM/REM, tagging, value forgetting, self-model | BORROW-COMPONENT | Substrate is a symbolic NetworkX graph, **not parametric weights**; conversational; forgetting is a fixed algorithm |
| 4 | **Language Models Need Sleep** (2606.03979) | Sleep = upward distillation (NREM) + RL dreaming (REM) into weights | BORROW-COMPONENT | Parametric + sleep, but QA/reasoning not embodied; no structure/detail selectivity; consolidation rule fixed; 3.6–4.8× compute |
| 5 | **SleepGate / "Learning to Forget"** (2603.14517) | Learned sleep gate evicts/compresses stale KV-cache entries | CONTEXTUAL | Operates on **KV cache, not parametric weights**; blob summary-merge; goal = interference reduction (O(n)→O(log n)), not structure retention |

---

## Per-paper decomposition (relevant set, newest first)

### PEAM — Parametric Embodied Agent Memory (2605.27762, May 2026)  ·  CLOSEST-PRIOR-ART
- Thesis: *Turn embodied experience into parameter-resident reflex skills.*
- Components: **WHAT** = parameterization-worthiness score; **WHEN** = scale-free self-triggered consolidation; substrate = multimodal **MoE-LoRA** with per-category physically-isolated adapters (parameter-level CL, no catastrophic forgetting); objective = joint behavioral-cloning + **contrastive** on failure-correction trajectory pairs (learns "what succeeds" and "how corrected differs from failed"). Slow LLM (deliberate) + fast parametric module (reflex).
- Keeps vs discards: keeps *consolidated skills* (procedural competence); discards raw trajectories. This is **procedural compression, not structure-vs-detail-aware.** It never asks whether relational/world structure is retained while episodic detail is dropped.
- Gap to B: worthiness score + self-trigger are **heuristics, not learned against retention**; no attention-weighting of the loss; no structural-retention benchmark; "keep" axis is skill-vs-nothing, not structure-vs-detail.
- **BORROW:** MoE-LoRA isolated-adapter substrate (our small parametric memory that resists forgetting); scale-free self-triggered "when to sleep"; failure-correction contrastive signal.

### EVAF / "Memory Depth, Not Memory Access" (2606.26806, Jun 2026)  ·  CLOSEST-PRIOR-ART (retention axis)
- Thesis: *Consolidate goal-conditioned tendencies into a small LoRA; leave facts to retrieval.*
- Components: **IMP** = surprise + valence gating; **write** = LoRA consolidation, very sparse (~2–3 writes / 200 events); **eval** = "loop-drift protocol" (retrieval index intact, working context unloaded, goal behavior must persist under long-loop interference); test-retest follow-up EVAF protocol at 2606.29916.
- Keeps vs discards: **keeps durable goal-conditioned behavior; discards/defers shallow factual recall** (retrieval wins facts, EVAF wins goal-persistence & post-unload recovery). This is the closest existing analogue to a keep/discard consolidation split — but the split is **behavioral-goal vs fact**, orthogonal to our **relational-structure vs episodic-detail**.
- Explicit self-critique (ammunition for us): *"negative cross-entropy and anti-training are the wrong object for stale-memory invalidation"* → **forgetting is unsolved**; they call for validity-gated reactivation/reconsolidation.
- Gap to B: gating is surprise/valence heuristic (not attention-weighted post-training); GPT-2/TinyLlama on conversational Memora event streams (not embodied); no structure-retention curve.
- **BORROW:** surprise+valence write-trigger as a baseline selector; the loop-drift / test-retest protocol as an eval template (unload context, measure persistence) — adapt to ALFWorld.

### SCM — Sleep-Consolidated Memory w/ Algorithmic Forgetting (2604.20943, Apr 2026)  ·  BORROW-COMPONENT (richest donor)
- Thesis: *Five-part biologically-faithful sleep memory: tag, NREM, REM, forget, self-model.*
- Components (full stack): **WM** = 7-item working memory bottleneck (Miller) creating consolidation pressure; **IMP** = 4-D tag `0.30·novelty + 0.20·|valence| + 0.35·task + 0.15·repetition`; **NREM** = Hebbian-strengthen co-occurring pairs **then proportional synaptic downscaling (~20%/cycle)** ← *this is the "detail-down / renormalization" primitive*; **REM** = random-walk recombination over the memory graph (novel non-contradictory links); **VF** = retention score = importance × temporal decay, adaptive threshold toward target size (~100 concepts); **self-model** = system as high-priority node.
- Keeps vs discards: **structure-aware selective retention** — keeps typed relational structure + high-importance associations, discards low-importance noise (90.9% noise reduction). Closest in spirit to structure-up, BUT via graph pruning, not parametric.
- Gap to B: substrate is a **symbolic NetworkX semantic graph, not weights**; conversational; forgetting is a fixed algorithm, not learned; "detail" here = noise concepts, not fine-grained episodic detail.
- **BORROW (high value):** NREM synaptic-downscaling as the mechanistic core of detail-down / renormalization; 4-D importance tag as the attention-weighting prior; REM random-walk as a cheap recombination/dreaming step.

### Language Models Need Sleep (2606.03979, Jun 2026)  ·  BORROW-COMPONENT
- Thesis: *Sleep = upward distillation + RL dreaming into slow weights.*
- Components: **NREM** = "Knowledge Seeding," distill smaller-self memories **upward into a larger network** (add capacity while preserving knowledge); **REM** = "Dreaming," RL-generated synthetic curriculum to rehearse new knowledge unsupervised (**generative replay**); fast unstable → slow low-frequency components. +52% synthetic reasoning; 3.6–4.8× compute.
- Keeps vs discards: consolidates in-context knowledge into parameters; **blob compression, no structure/detail selectivity.**
- Gap to B: QA/math/knowledge-incorporation, never embodied; fixed consolidation rule; no attention-weighting; no retention curve.
- **BORROW:** REM "dreaming" RL curriculum as our generative-replay component; the fast→slow framing.
- Note: **distinct from** 2605.26099 *"Do Language Models Need Sleep? Offline Recurrence for Improved Online Inference"* — different paper (offline recurrence, not consolidation). The earlier ID confusion in `00_synthesis.md` is now resolved: our target is **2606.03979**.

### SleepGate / "Learning to Forget: Sleep-Inspired… Proactive Interference" (2603.14517, Mar 2026)  ·  CONTEXTUAL
- Thesis: *Learned sleep gate over the KV cache resolves proactive interference.*
- Components: conflict-aware temporal **tagger**; learned **forgetting gate** (evict/compress stale entries); **consolidation module** merges survivors into compact summaries; cites synaptic downscaling / selective replay / targeted forgetting. Interference horizon O(n)→O(log n). 4-layer 793K-param toy transformer.
- Keeps vs discards: keeps current, evicts superseded — **blob summary-merge, not structure-aware.**
- Gap to B: operates on **KV cache, not parametric weights**; objective is interference/compute, not structure retention.
- **BORROW:** the *learned* forgetting gate is a nice existence proof that gating can be learned (most others are heuristic) — but on the wrong substrate.

### WSCL — Wake-Sleep Consolidated Learning (2401.08623, 2024, IEEE TPAMI)  ·  CONTEXTUAL (template anchor)
- Thesis: *CLS-based wake/NREM/REM loop for continual visual classification.*
- Components (clean template): **wake** = adapt + dynamic parameter freezing (stability) + short-term hippocampal store; **NREM** = replay short+long-term memory, Hebbian plasticity (strengthen important / weaken unimportant); **REM** = "dreaming" over unseen realistic inputs to pre-shape future feature space. Beats baselines on CIFAR-10 / Tiny-ImageNet / FG-ImageNet.
- Keeps vs discards: replay-based blob CL; **no structure/detail split.**
- Gap to B: vision classification, not agent experience; raw+generative replay, no attention weighting.
- **BORROW:** the explicit wake→NREM(replay+plasticity)→REM(dream) procedure template and dynamic parameter-freezing for stability.

### Others reviewed (CONTEXTUAL, farther)
- **ComMem** (2606.28719, Jun 2026): complementary fast-detailed (hippocampal cache) + slow-abstract (cortical text prototypes) for **VLM test-time adaptation**. Genuinely fast-detail/slow-abstract, but per-sample TTA on VLMs, not agent sleep-consolidation; abstract memory is *textual prototypes*, not attention-weighted weights. Tag: CONTEXTUAL (nice fast/slow framing to cite).
- **Pattern separation/completion → HiCL** (2508.16651, 2025): DG-inspired sparse pattern separation + CA3 pattern completion + DG-gated MoE + replay. Architecture-level hippocampal CL, not a sleep-consolidation procedure over agent experience; no structure/detail retention metric. Tag: CONTEXTUAL.
- **Semi-parametric Memory Consolidation** (2504.14727, 2025): brain-like deep CL, semi-parametric (fast episodic + slow parametric). Component ancestor of the fast/slow split; not embodied, no structure/detail curve. Tag: CONTEXTUAL/BORROW (fast-slow scaffold).
- **Neural Manifolds & Cognitive Consistency** (2503.01867, 2025) = the "A New Approach to Memory Consolidation in Artificial Systems" paper: low-dim manifold + sharp-wave-ripple + Heider balance energy. Neuroscience-simulation, no learning system to borrow. Tag: CONTEXTUAL.
- **Modular Memory is the Key to Continual Learning Agents** (2603.01761, ICML 2026 spotlight position, 24 authors): argues IWL+ICL via modular memory is the path; **explicitly names learned when/what-to-consolidate as open.** Not a system. Tag: CONTEXTUAL (cite as the open-problem statement B answers).
- **"Learning to Forget Attention"** (2602.12204): consolidation loss trains semantic memory to approximate episodic retrieval; router shifts episodic→semantic, 37.8× attention-compute cut. Closest string-match to "attention-weighted consolidation" but the goal is **compute reduction via routing**, not structure-up/detail-down retention. Tag: CONTEXTUAL (differentiate: our attention-weighting is a *retention* objective, not a compute-routing one).
- Historical anchors (context only): **CLS (McClelland 1995)** — dual fast-hippocampal/slow-cortical; **Generative Replay** — component, appears inside 2606.03979/WSCL as REM/dreaming.

---

## Closest prior-art verdict + reuse vs build-new

**Closest system = PEAM (2605.27762).** Same problem shape (internalize embodied agent experience into a small parametric memory during an offline consolidation phase) on the same kind of substrate (isolated LoRA adapters). Treat PEAM as the system to beat and to differentiate against. **EVAF (2606.26806)** is the closest on the retention-selectivity axis and its "forgetting is unsolved / anti-training is the wrong object" admission is direct ammunition for our contribution.

### Components we can REUSE (borrow, with source)
1. **Parametric substrate** — MoE-LoRA isolated adapters as the small parametric memory (PEAM 2605.27762). Resists catastrophic forgetting, supports parameter-level CL.
2. **Detail-down primitive** — NREM proportional **synaptic downscaling** (SCM 2604.20943) as the mechanistic renormalization that forgets detail while sparing high-importance structure.
3. **Importance prior** — 4-D salience tag / surprise+valence gating (SCM 2604.20943; EVAF 2606.26806) as the *initialization* of our attention weights (before we make weighting learned).
4. **When/what governance skeleton** — scale-free self-triggered consolidation + worthiness gate (PEAM); learned forgetting gate existence proof (SleepGate 2603.14517).
5. **Dreaming / generative replay** — RL synthetic-curriculum (2606.03979) and REM random-walk recombination (SCM) as the replay source during sleep.
6. **Procedure template** — wake→NREM(replay+plasticity)→REM(dream) loop + dynamic parameter freezing (WSCL 2401.08623).
7. **Eval template** — EVAF loop-drift / test-retest protocol (unload working context, measure persistence under interference) — adapt to ALFWorld/AI2-THOR.

### Components we must BUILD NEW (the Missing Diagonal)
1. **Attention-weighted consolidation LOSS** that enforces structure-up/detail-down — up-weight structural/relational tokens, down-weight episodic detail in the post-training objective. No verified system does this; the nearest (2602.12204) uses attention for compute-routing, not retention selectivity.
2. **Structure-retention vs detail-forgetting metric + benchmark** — nobody measures the diagonal. Existing evals measure recall accuracy (SCM), goal-persistence (EVAF), interference horizon (SleepGate), classification accuracy (WSCL).
3. **Learned routing/consolidation policy** — trained against retention outcomes, replacing PEAM's worthiness heuristic and EVAF's surprise/valence heuristic. This is exactly the open problem the Modular Memory position paper (2603.01761) names.
4. **Embodied instantiation on ALFWorld/AI2-THOR** with the structure/detail separation — PEAM is Minecraft-skills, EVAF is conversational LLM; neither reports a structural-retention curve in an embodied task.

---

## Verified arXiv IDs (checked 2026-07-13)

| ID | Title | Note |
|---|---|---|
| 2605.27762 | PEAM: Parametric Embodied Agent Memory… Minecraft | verified — closest system |
| 2606.26806 | Memory Depth, Not Memory Access: Selective Parametric Consolidation… | verified — EVAF; closest retention axis |
| 2606.29916 | EVAF: A Test-Retest Protocol for Selective Parametric Consolidation | verified — EVAF eval follow-up |
| 2604.20943 | SCM: Sleep-Consolidated Memory with Algorithmic Forgetting | verified — richest donor |
| 2606.03979 | Language Models Need Sleep: Learning to Self-Modify and Consolidate Memories | verified — dreaming/self-train variant |
| 2605.26099 | Do Language Models Need Sleep? Offline Recurrence… | verified — **different paper**, not ours |
| 2603.14517 | Learning to Forget: Sleep-Inspired… Proactive Interference (SleepGate) | verified |
| 2401.08623 | Wake-Sleep Consolidated Learning (WSCL) | verified — IEEE TPAMI 2024 |
| 2606.28719 | ComMem: Complementary Memory Systems for TTA of VLMs | verified — VLM TTA, contextual |
| 2508.16651 | HiCL: Hippocampal-Inspired Continual Learning | verified — the pattern-sep/completion paper |
| 2504.14727 | Semi-parametric Memory Consolidation: Towards Brain-like Deep CL | verified (2025) |
| 2503.01867 | Neural Manifolds & Cognitive Consistency: A New Approach to Memory Consolidation | verified — = "A New Approach…" paper |
| 2603.01761 | Position: Modular Memory is the Key to Continual Learning Agents | verified — ICML 2026 spotlight |
| 2602.12204 | Learning to Forget Attention: Memory Consolidation for Adaptive Compute Reduction | verified — compute-routing, differentiate |

Resolved from earlier `00_synthesis.md` TODO: "Language Models Need Sleep" is **2606.03979** (self-modify/consolidate); 2605.26099 is a separate offline-recurrence paper. PEAM ID confirmed 2605.27762.
