# Literature Survey: Wake-Sleep / Memory Consolidation for Continual LLM Agents

_Survey date: 2026-07-11. Scope: wake-sleep / sleep-phase consolidation, Complementary Learning Systems (CLS) applied to ML, and selective/prioritized replay. Focus 2024-2026 with foundational anchors._

---

## Part A — Foundational Papers (pre-2024 anchors)

### A1. Hinton, Dayan, Frey & Neal (1995) — The Wake-Sleep Algorithm for Unsupervised Neural Networks
- **Venue/year:** *Science* 268:1158-1161, 1995.
- **Core method:** Two-phase unsupervised learning for the Helmholtz machine. **Wake phase:** a bottom-up *recognition* model infers latent generators for real inputs, and the top-down *generative* model is updated to make those generators more likely to have produced the input. **Sleep phase:** the generative model "fantasizes" inputs by sampling generators stochastically, and the recognition model is trained to reproduce those generators. Uses only local delta-rule updates (no backprop through the full model).
- **Setup:** Toy/small generative modeling; density estimation. Related to EM; optimizes a variational bound on data likelihood.
- **Findings:** Established that alternating recognition/generation with local rules can train layered generative models. The "sleep = generate-then-learn-to-recognize" template is the direct ancestor of modern generative-replay and dreaming schemes.
- **Limitations:** Sleep-phase samples come from the model's own prior, so learning can be biased when the generative model is poor early on (mode mismatch); no notion of task sequences or forgetting. (Later addressed by Reweighted Wake-Sleep, arXiv:1406.2751.)

### A2. McClelland, McNaughton & O'Reilly (1995) — Why There Are Complementary Learning Systems in the Hippocampus and Neocortex
- **Venue/year:** *Psychological Review* 102:419-457, 1995. (The canonical CLS reference; extended by Kumaran, Hassabis & McClelland 2016.)
- **Core claim:** The brain needs two differentially specialized systems. The **hippocampus** is a sparse, pattern-separated store that rapidly encodes specific episodes in one/few exposures. The **neocortex** is a distributed, overlapping system that slowly integrates across episodes to extract latent semantic structure. Memories are first stored hippocampally, then *replayed/reinstated* to the neocortex, whose synapses change a little on each reinstatement; remote memory rests on accumulated neocortical change.
- **Why it matters for ML:** Directly motivates dual-memory architectures — fast episodic buffer + slow parametric model — and explains *why interleaved replay (not sequential training) avoids catastrophic forgetting*. This is the theoretical backbone for essentially every paper below.
- **Limitation for ML translation:** Biological CLS assumes slow, gradual cortical consolidation; LLMs are pretrained once and fine-tuned in large steps, so the "slow, small changes per reinstatement" prescription is non-trivial to map onto gradient updates or to in-context/external memory.

### A3. Tadros, Krishnan, Ramyaa & Bazhenov (2022) — Sleep-like Unsupervised Replay Reduces Catastrophic Forgetting in ANNs (Sleep Replay Consolidation, SRC)
- **Venue/year:** *Nature Communications* 13, 2022. Code: github.com/tmtadros/SleepReplayConsolidation.
- **Core method:** After standard (task-sequential) training, convert the ANN to a spiking net (activations → Heaviside, weights scaled by max layer-wise activation). Drive it with stochastic Poisson spike trains whose rates reflect feature-wise average intensities of past data, and apply *unsupervised Hebbian* updates during this "sleep" phase; then map weights back to the ANN. No stored raw exemplars — replay is synthetic/noise-driven.
- **Setup:** Class-incremental MNIST/CIFAR-style tasks; fully-connected and small conv nets.
- **Findings:** Sleep phases move weights back toward a joint manifold representing *all* tasks, mitigating catastrophic forgetting; interleaving new-task training with offline reactivation recovers old-task accuracy.
- **Limitations:** Demonstrated on small nets/datasets; ANN↔SNN conversion and Hebbian sleep are hard to scale; no language/agent tasks.

### A4. Tadros et al. follow-up (AAAI 2024, arXiv:2402.10956) — Sleep-Like Unsupervised Replay Improves Performance when Data are Limited or Unbalanced
- **Core method:** Same ANN→SNN→Hebbian-sleep→ANN pipeline as SRC, applied to data-scarcity/imbalance rather than only sequential tasks.
- **Setup:** MNIST and Fashion-MNIST; 2-hidden-layer FC net trained on 0.5%-100% of data.
- **Key numbers:** **+20-30% accuracy** in the 0.5-10% data regime; slight decline (10-15%) above 10% data, recoverable via fine-tuning; helps underrepresented classes; increases synaptic sparsity.
- **Limitations:** Simple datasets/architectures; scalability unexplored. Establishes that sleep replay is most valuable precisely when data is *limited* — relevant to sparse-reward agent settings.

---

## Part B — Wake-Sleep / Sleep-Phase Consolidation, 2024-2026

### B1. Sorrenti et al. (2024) — Wake-Sleep Consolidated Learning (WSCL), arXiv:2401.08623
- **Core method:** Synchronizes wake and sleep phases for continual visual classification. **Wake:** process input with dynamic parameter freezing + store episodic memories. **Sleep = NREM + REM.** NREM consolidates weights via replay of stored episodes; **REM "dreams"** by exposing the model to realistic *unseen* visuals to prepare for future knowledge and enable positive forward transfer.
- **Setup:** CIFAR-10, Tiny-ImageNet, FG-ImageNet; continual (class-incremental) classification.
- **Findings:** Outperforms baselines/prior CL methods; ablations show all three stages (wake, NREM, REM) contribute; REM/dreaming specifically produces positive *forward* transfer.
- **Limitations:** Vision-only, three datasets; leans on biological CLS analogy that may not transfer perfectly; no LLM/agent evaluation.

### B2. "Language Models Need Sleep: Learning to Self-Modify and Consolidate Memories" (2026), arXiv:2606.03979
- **Core method:** A "Sleep" paradigm with two stages. (1) **Memory Consolidation via "Knowledge Seeding":** transfer knowledge from high-frequency (frequently-updated) parameters into newly-expanded low-rank / low-frequency modules using on-policy distillation + RL-based imitation. (2) **"Dreaming":** self-generate synthetic data with gradient-based importance scoring for recursive self-improvement while controlling forgetting. Built atop a "Hope" self-modifying architecture; uses parameter masking rather than tensor resizing.
- **Setup:** Broad — class-incremental (CLINC, Banking, DBpedia), long-context QA (LongHealth, QASPER, MK-NIAH), math reasoning (AIME, HMMT), knowledge incorporation (SQuAD), few-shot reasoning (ARC), ultra-long context (BABILong up to **10M tokens**). Models: Llama-3.2-1B/3B, Llama3-8B, Qwen3 variants.
- **Key numbers:** Beats ICL, EWC, InCA on class-incremental tasks; higher consolidation stages monotonically improve long-context; **80% success on few-shot ARC vs 72.5% for SEAL**; near-perfect scaling to 10M tokens on BABILong; Qwen3-8B **79.2 AIME-24 vs 76.6** OPSD baseline.
- **Limitations:** Large compute overhead (SFT needs 3.6-4.8x wall-clock to match Sleep); implementation complexity (parameter masking); quality-sensitive to synthetic "dream" data. **This is the closest prior art to a full "LLM sleep consolidation" system — position novelty against it carefully.**

### B3. SCM: Sleep-Consolidated Memory with Algorithmic Forgetting for LLMs (2026), arXiv:2604.20943
- **Core method:** Brain-inspired *external* memory system (not weight updates): MeaningEncoder (semantic concept extraction), ValueTagger (4-D importance scores), a 7-item WorkingMemory buffer, a LongTermMemory graph, and a SleepCycle orchestrator. **NREM** replays recent episodes, strengthens co-occurring concepts via Hebbian plasticity, and applies proportional synaptic downscaling; **REM** selects high-importance concepts and generates novel combinations (random walks) to form new associative links; adaptive forgetting prunes low-value memories.
- **Setup:** 8 benchmark tests (recall accuracy, memory efficiency, consolidation benefit, latency) on multi-turn conversation. Prototype: local Llama-3.2-2B + all-MiniLM-L6-v2 embeddings on an 8GB laptop, no GPU.
- **Key numbers:** Perfect recall (22/22 facts) over 10-turn conversations; **90.9% noise reduction** via adaptive forgetting; sub-ms retrieval at 360+ concepts; beats vector-DB baselines on recall and footprint.
- **Limitations:** No "continuous existence" between API calls; extraction quality bounded by the small local LLM; text-only; NetworkX graph bottlenecks at ~10k concepts (needs a real graph DB to scale).

### B4. SleepGate — Learning to Forget: Sleep-Inspired Memory Consolidation for Resolving Proactive Interference in LLMs (2026), arXiv:2603.14517
- **Core method:** Augments a transformer with periodic "sleep" cycles over the **KV cache**. Three components: (1) a *conflict-aware temporal tagger* that detects when new entries supersede old ones; (2) a lightweight *learned forgetting gate* that selectively evicts/compresses stale cache entries; (3) a *consolidation module* that merges survivors into compact summaries.
- **Setup:** Small transformer (4 layers, 793K params); measured retrieval accuracy at increasing *proactive-interference (PI) depth* vs 5 baselines (full KV, sliding window, H2O, StreamingLLM, decay-only).
- **Key numbers:** **99.5% retrieval @ PI depth 5, 97.0% @ depth 10, while all 5 baselines stay below 18%.** Reduces interference horizon from O(n) to O(log n).
- **Limitations:** Tiny model (793K params) — scalability to real LLMs untested; focused narrowly on proactive interference. Notable because it targets *forgetting the right things* (interference resolution), a dimension most replay methods ignore.

### B5. Phasor Agents: Oscillatory Graphs with Three-Factor Plasticity and Sleep-Staged Learning (2026), arXiv:2601.04362
- **Core method:** Oscillatory graph networks with phase-based representations and *three-factor* synaptic plasticity (pre/post timing × neuromodulatory signal). Alternates wake (task learning) and sleep (consolidation) phases. Argues sleep should be modeled as *temporally precise write windows/gates* rather than a uniform offline block.
- **Setup:** RL / continuous-control benchmarks; compared to standard NN baselines on learning efficiency.
- **Findings:** Three-factor plasticity improves convergence/sample efficiency; sleep-staged phases improve retention and reduce forgetting.
- **Limitations:** Overhead of maintaining oscillatory dynamics/phase tracking; scalability to large nets unclear; sensitive to frequency/plasticity hyperparameters. Conceptually useful ("gated write windows") but far from LLM-scale.

### B6. (Related, not fetched in depth) Slumbering to Precision: Enhancing ANN Calibration Through Sleep-like Processes (2026), arXiv:2603.07867
- **Core idea:** Applies SRC-style sleep-like offline processing to improve *model calibration* (not just accuracy/forgetting). Signals that the "sleep phase" primitive is being repurposed beyond forgetting — relevant if the project wants to claim consolidation improves calibration/uncertainty.

---

## Part C — Complementary Learning Systems / Dual-Memory Architectures for LLMs

### C1. HiCL: Hippocampal-Inspired Continual Learning (2025), arXiv:2508.16651
- **Core method:** A **dentate-gyrus-gated Mixture-of-Experts**. A DG-inspired module does sparse *pattern separation* (top-k sparsity) and routes inputs to specialized experts by cosine similarity to learned task prototypes — no explicit gating network or task label at inference. CA3/CA1-style MLP stages follow; grid-cell encoding on input.
- **Setup:** Split CIFAR-10 (5 tasks) and Split Tiny-ImageNet (10 tasks); LeNet/CNN backbones; DG layer 1024 units at 5% sparsity. Metrics: Task-IL & Class-IL accuracy, MFLOPs.
- **Key numbers:** On Split CIFAR-10 (200-sample buffer): **92.38% Task-IL, 65.58% Class-IL using only 84.18 MFLOPs vs 219.60** for comparable baselines. Graceful degradation: 500→100 examples/task costs only 2.7 pts Task-IL.
- **Limitations:** Needs known task boundaries at train time (Task-IL); fixed hyperparameters may not generalize; ~5% routing confusion from overlapping sparse codes; vision-only, small backbones. Good template for *sparse hippocampal routing* — directly relevant to a "learned routing policy" project.

### C2. HEMA: Hippocampus-Inspired Extended Memory Architecture for Long-Context AI Conversations (2025), arXiv:2504.16754
- **Core method:** Dual external memory: **Compact Memory** (a continuously-updated one-sentence running summary preserving the global narrative) + **Vector Memory** (episodic store of chunk embeddings retrieved via cosine similarity). Age-weighted pruning manages growth.
- **Setup:** 6B-param transformer; conversations >300 turns; Vector Memory indexed up to 10k chunks. Metrics: factual recall, human coherence (5-pt), P@5, R@50, AUPRC.
- **Key numbers:** Factual recall **41%→87%**; coherence **2.7→4.3**; P@5 ≥ 0.80, R@50 ≥ 0.74; age-weighted pruning cut retrieval latency 34%; supports month-long dialogue within a 3,500-token prompt.
- **Limitations:** Needs a two-level summary hierarchy to avoid cascade errors beyond ~1,000 turns; scaling and privacy of long-term indexing unaddressed. This is the "compressed always-visible summary + latent episodic store" instantiation of CLS.

### C3. TiMem: Temporal-Hierarchical Memory Consolidation for Long-Horizon Conversational Agents (2026), arXiv:2601.02845
- **Core method:** Multi-level memory across temporal scales; recent exchanges are consolidated into progressively more abstract summaries, enabling efficient retrieval while preserving salient context over long horizons.
- **Setup:** Long-context conversation / RAG dialogue; LLMs with extended context. Metrics: recall accuracy, response relevance, efficiency, coherence.
- **Findings:** Maintains contextual consistency over thousands of turns with lower compute than flat memory.
- **Limitations:** Hierarchical abstraction can lose fine-grained detail; performance hinges on intermediate-summary quality; consolidation schedule needs per-domain tuning. (Abstract-level detail only; full PDF not machine-readable.)

### C4. (Context) Kumaran, Hassabis & McClelland (2016) — What Learning Systems Do Intelligent Agents Need? CLS Theory Updated
- **Relevance:** The modern restatement of CLS that DeepMind used to justify experience replay in DQN. Worth citing as the bridge between A2 (1995 CLS) and replay-based deep RL/CL. Key update: the hippocampus can also support *generalization* via replay statistics, not only episodic recall — motivating *selective* (non-uniform) replay.

---

## Part D — Selective / Prioritized Replay vs Random Reservoir Sampling

### D1. SuRe: Surprise-Driven Prioritised Replay for Continual LLM Learning (2025), arXiv:2511.22367
- **Core method:** Uses **surprise (prediction-error magnitude)** to decide which past examples to store and replay during continual LLM fine-tuning, concentrating replay budget on examples the model finds hard/novel. Explicitly framed against uniform/random replay.
- **Setup:** GLUE / SuperGLUE; LoRA-based PEFT on LLMs; metrics track retention on old tasks + acquisition of new. Motivated by neuroscience (event boundaries / prediction errors structure episodic encoding; hippocampal replay is biased toward surprising, behaviorally valuable content).
- **Findings:** Surprise-based selection outperforms uniform random replay and other heuristic prioritizations across CL scenarios.
- **Limitations:** Overhead of computing prediction errors; sensitive to surprise-threshold and buffer-size tuning; effectiveness varies with task similarity and architecture. **Most direct competitor to a "learned routing/selection policy" claim — a novel project should beat or subsume surprise-based heuristics, ideally with a learned policy rather than a fixed surprise rule.**

### D2. Improvements of Dark Experience Replay and Reservoir Sampling (2025), arXiv:2504.20932 (also Frontiers in AI 2026)
- **Core method:** Analyzes the consolidation-vs-plasticity trade-off in **Dark Experience Replay (DER)** and **Reservoir Sampling (RS)**. Improves DER via automatic weight adaptation, blocking replay of erroneous data, and correcting past outputs; improves RS via generalized acceptance probability, stratified/plural buffers, and intentional omission of unnecessary data.
- **Setup:** Standard CL image benchmarks (Split-CIFAR / Tiny-ImageNet family).
- **Findings:** Both improved DER and improved RS shift the Pareto front toward better stability-plasticity balance; targeted omission (a mild form of selectivity) helps RS.
- **Takeaway:** Establishes the *baseline* that pure reservoir sampling gives unbiased coverage but is suboptimal; selective retention that keeps a "maximally informative core" beats it under non-stationarity — the exact gap a learned selective-replay policy targets.

### D3. Rolnick et al. (2019) — Experience Replay for Continual Learning (CLEAR), NeurIPS
- **Relevance (foundational baseline):** Showed reservoir-sampled replay + behavior cloning ("CLEAR") is a strong, simple CL baseline in RL. The canonical "random reservoir" reference that selective-replay papers must outperform. Useful to cite as the plain-replay anchor.

### D4. (Context) Information-Theoretic Online Memory Selection for Continual Learning (2022), arXiv:2204.04763
- **Relevance:** Selects buffer contents by information-theoretic surprise/uncertainty criteria — a pre-LLM precursor to SuRe. Establishes that *which* samples you keep matters as much as how many; provides principled selection objectives (e.g., surprise, learnability) to compare a learned policy against.

---

## Part E — Agent-Memory Experience Consolidation (project-adjacent, ALFWorld/BabyAI)

### E1. When Continual Learning Moves to Memory: A Study of Experience Reuse in LLM Agents (2026), arXiv:2604.27003
- **Core method:** Recasts memory-augmented LLM agents as continual learning via a **(key, value)** framework: *value* = how experience is represented (raw trajectories vs abstract insights); *key* = how memory is organized (storage granularity, retrieval frequency). Frozen backbone, non-parametric learning; sequential Task A → Task B with accumulated external memory.
- **Setup:** ALFWorld ("put X in Y" → "put clean X in Y") and BabyAI (heterogeneous nav → homogeneous search). Qwen-Plus backbone (frozen), BM25 retriever. Metrics: Forward Transfer (FWT), Backward Transfer (BWT), plus Retention-Rate/New-Learning splits on easy vs hard cases; 200 train + 100 test per phase.
- **Key numbers:** **Raw trajectory reuse causes negative forward transfer (−9.5% ALFWorld, −7.5% BabyAI); abstract insights flip it positive (+6.5%, +9.0%).** Negative transfer concentrates on *hard* cases (ALFWorld ΔRR=+4.6 but ΔNL=−26.1). Fine-grained storage helps only when source memories are diverse; homogeneous queries cause "retrieval diversity collapse." A clear memory-dilution stability-plasticity trade-off: the design best for the new task degrades most on the old.
- **Limitations:** Only two environments, one task pair each, one retriever (BM25), two runs — controlled but narrow. **Highly relevant baseline for a wake-sleep agent project: it quantifies that *abstraction beats raw replay* and that *selection/organization* is the bottleneck — exactly what a learned consolidation/routing policy should optimize.**

### E2. (Related) MemSkill / SkillRL / SkillLearnBench (2026)
- **MemSkill (arXiv:2602.02474):** RL for skill *selection* + LLM-guided skill *evolution* from hard cases; continual refinement of a skill bank.
- **SkillRL (arXiv:2602.08234):** distills redundant trajectories into a hierarchical SkillBank; recursive co-evolution of skill library and policy under RL.
- **SkillLearnBench (arXiv:2604.20087):** benchmark for continual agent skill generation on real-world tasks.
- **Relevance:** These frame consolidation as *skill abstraction/distillation* rather than sleep phases — an alternative mechanism the project should compare against or hybridize with. Note a recurring failure mode reported across this line (and arXiv:2605.12978 "Useful Memories Become Faulty When Continuously Updated by LLMs"): iterative self-abstraction can improve then **degrade** — a "consolidation collapse" the wake-sleep framing could claim to prevent.

---

## Synthesis: Positioning Novel Research

**Landscape structure.** Three mechanistic families now exist: (1) **weight-space sleep consolidation** (WSCL, SRC, "LMs Need Sleep", Phasor) that replays/dreams into parameters; (2) **external dual-memory CLS systems** (HEMA, TiMem, SCM, HiCL) that keep a fast episodic store + slow/compressed summary; and (3) **selective-replay policies** (SuRe, info-theoretic selection, improved DER/RS) that decide *what* to consolidate. Most work lives in exactly one family and (except "LMs Need Sleep") is evaluated on vision or conversation, not embodied agents.

**Five findings most useful for positioning:**

1. **"Language Models Need Sleep" (arXiv:2606.03979) is the closest prior art and the bar to clear.** It already does NREM-style consolidation ("knowledge seeding") + REM-style "dreaming" for LLMs and reports strong numbers (beats SEAL, EWC, InCA; 10M-token scaling). A novel project must differentiate on axis it does *not* cover: it is expensive (3.6-4.8x compute), operates on parameters, and is not evaluated on interactive/embodied agents. **The open lane is wake-sleep consolidation with a *learned routing/selection policy* on *agentic* continual tasks (ALFWorld/AI2-THOR), not weight distillation on QA/math.**

2. **Selective replay beats random reservoir sampling, but current selectors are fixed heuristics (surprise/prediction-error, info-theoretic).** SuRe (arXiv:2511.22367) and improved DER/RS (arXiv:2504.20932) show reservoir sampling is a beatable baseline. No one has shown a *learned* consolidation policy that outperforms surprise-based selection in an agent memory setting — a clean novelty claim.

3. **In LLM-agent memory specifically, abstraction beats raw-trajectory replay, and organization is the real bottleneck (arXiv:2604.27003).** Raw replay gives *negative* transfer (−9.5%); abstract insights give +6.5%. This empirically motivates a consolidation phase that *abstracts and selects* rather than stores raw episodes — and provides ready-made FWT/BWT metrics + ALFWorld/BabyAI baselines to benchmark against.

4. **CLS-style sparse hippocampal routing is under-explored for LLM agents.** HiCL (arXiv:2508.16651) shows DG-gated sparse MoE routing gives strong CL at low FLOPs but only in vision with known task boundaries. Porting learned, task-label-free sparse routing to an LLM-agent's episodic-vs-semantic memory is novel and aligns with a "learned routing policy" thesis.

5. **"Consolidation collapse" is an documented, unsolved failure mode.** Multiple agent-memory papers (arXiv:2604.27003, 2605.12978, MemSkill/SkillRL line) report that naive iterative memory updating *improves then degrades*. A wake-sleep framework with principled selective replay + forgetting (cf. SleepGate's interference resolution, arXiv:2603.14517, and SCM's algorithmic forgetting) can be positioned as a *stability mechanism* that prevents this collapse — a concrete, measurable contribution.

**Recommended novelty statement (draft):** _A wake-sleep continual-learning agent for ALFWorld/AI2-THOR in which a **learned routing policy** decides, during "sleep," which episodic experiences to abstract, replay, or forget — combining CLS dual-memory structure with prioritized (non-reservoir) selective replay — evaluated on forward/backward transfer and tested specifically for resistance to consolidation collapse._ This sits in the white space between weight-space LLM sleep (2606.03979), heuristic selective replay (2511.22367), and agent-memory reuse studies (2604.27003).

---

## Reference Index
- Hinton, Dayan, Frey, Neal 1995 — Wake-Sleep — *Science* 268:1158.
- McClelland, McNaughton, O'Reilly 1995 — CLS — *Psych. Review* 102:419. (Update: Kumaran, Hassabis, McClelland 2016, *Trends Cog. Sci.*)
- Tadros et al. 2022 — SRC — *Nature Communications* 13.
- Tadros et al. 2024 — Sleep replay w/ limited data — AAAI / arXiv:2402.10956.
- Rolnick et al. 2019 — CLEAR — NeurIPS.
- Sun et al. 2022 — Info-theoretic memory selection — arXiv:2204.04763.
- Sorrenti et al. 2024 — WSCL — arXiv:2401.08623.
- 2025 — Improved DER & Reservoir Sampling — arXiv:2504.20932 / Frontiers AI 2026.
- 2025 — HEMA — arXiv:2504.16754.
- 2025 — HiCL — arXiv:2508.16651.
- 2025 — SuRe — arXiv:2511.22367.
- 2026 — TiMem — arXiv:2601.02845.
- 2026 — Phasor Agents — arXiv:2601.04362.
- 2026 — SleepGate (Learning to Forget) — arXiv:2603.14517.
- 2026 — Slumbering to Precision (calibration) — arXiv:2603.07867.
- 2026 — SCM — arXiv:2604.20943.
- 2026 — Experience Reuse in LLM Agents — arXiv:2604.27003.
- 2026 — "Language Models Need Sleep" — arXiv:2606.03979.
- Agent-skill line: MemSkill 2602.02474, SkillRL 2602.08234, SkillLearnBench 2604.20087, faulty-memory 2605.12978.
