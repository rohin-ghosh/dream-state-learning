# 19. Benchmark Prior-Art Re-Check (StructMem-Bench), August 2026

**Scope:** Targeted re-verification of the July 2026 survey conclusion ("no benchmark separates
structural from detail retention") plus six specific adjacent benchmark designs the survey did not
cover. Searches: arXiv/Scholar/web, Aug 2025 - Aug 2026. Benchmarks only, not methods.

---

## 0. Two corrections to the earlier survey

**(a) The "Missing Diagonal" citation is misattributed.** arXiv:2604.15877 is *"Experience
Compression Spectrum: Unifying Memory, Skills, and Rules in LLM Agents"* (Apr 17, 2026). Its
"missing diagonal" names a **different gap**: no memory *system* supports adaptive cross-level
compression along the episodic-memory (5-20x) -> skills (50-500x) -> rules (1000x+) spectrum. It is
a systems gap, not a benchmark gap, and it does not name structural-vs-detail retention scoring.
Do not cite it for our gap claim.

**(b) The core claim is now WEAKENED but not dead.** As of ~Aug 2026, **ForgetBench**
(arXiv:2607.26455) explicitly "disentangle[s] isolated factual retention from structured relational
knowledge preservation" via concept-based QA vs scenario-based QA — but **only for parametric
memory under continual knowledge editing** (MEMIT, AlphaEdit, etc.). No RAG, no text banks, no
budget, no unified probe across memory types. The precise claim we can still make: *no benchmark
scores structural and episodic-detail retention separately, programmatically against a ground-truth
dependency graph, across arbitrary memory types at a fixed budget.*

**Naming hazard:** **StructMemEval** (arXiv:2602.11243, Yandex Research, Feb 2026,
github.com/yandex-research/StructMemEval) already exists. It tests whether agents *organize*
memory into latent structures (ledgers, to-do lists, trees) — memory-organization ability, not
structural-vs-detail retention scoring. Different benchmark, dangerously similar name.
**Recommend renaming StructMem-Bench** (e.g., RetainGraph-Bench, DualTrace-Bench).

---

## 1. New/verified benchmarks in the window (key hits)

| Benchmark | ID | What it measures |
|---|---|---|
| **ForgetBench** | arXiv:2607.26455 | Forgetting dynamics of parametric memory under continual knowledge editing; forgetting curves (temporal decay, retention strength, cross-instance stability); concept QA (isolated facts) vs scenario QA (relational, multi-agent interaction graphs). |
| **RECON** | arXiv:2607.16716 | Compositional reasoning over long contexts; **code-first deterministic provenance DAG** (events/evidence/conclusions; typed causal/revisionary/invalidating edges); cascade-propagation tests; evaluates long-context, RAG variants, memory systems (Mem0, Mem0-Graph, Hindsight, Supermemory) + oracle. |
| **MemTrace** | arXiv:2606.17328 | "Knowledge point" (single typed fact) probe unit; controlled dims: **memory age (sessions)**, question type (current/past/trajectory), evidence condition (present/missing/contradicted); 13 configs across 4 paradigms (long-context, RAG, external-memory, agentic). No parametric. |
| **Ground Truth First** | arXiv:2607.21962 | Ground truth **generated before text** (seeded life-script sampler; validity intervals; volatility classes permanent->ephemeral; channel provenance); questions mechanically instantiated. Finds **"tenure crossover"**: architecture rankings invert with history length (budgeted curated map wins wk 3, graph wins wk 9) driven by budget eviction. Includes 42 injection probes. 5 architectures + no-memory control; no parametric. |
| **EvoMemBench** | arXiv:2605.18421 | 2x2: memory scope (in-episode vs cross-episode) x content (knowledge vs execution); 15 memory methods + long-context baselines, standardized protocol; context budgets 16K-128K on execution tasks. No parametric, no age curves, no separate rule-vs-detail metrics. |
| **LongMemEval-V2** | arXiv:2605.12493 | 451 questions, 1,870 trajectories, up to **115M-token** histories (WebArena/ServiceNow-style); 5 abilities incl. workflow knowledge, environment gotchas, dynamic state tracking; memory system returns compact evidence; scores accuracy + latency. |
| **WorldMemArena** | arXiv:2605.29341 | Multimodal agent memory as 4-stage lifecycle (write/maintain/retrieve/use), 400 multi-session tasks, stage-level diagnosis; 19 baselines (RAG, embedding, long-context VLM, terminal-agent harness). No parametric. |
| **SubtleMemory** | arXiv:2606.05761 | Fine-grained **relational memory discrimination**: relation-controlled latent artifacts instantiating complementary/nuanced/contradictory relations; diagnostics across preserve/retrieve/reason stages; 11 systems. |
| **BEAM** | (mem0/Hindsight ecosystem, 2026) | 100K/500K/1M/**10M**-token conversations, 2,000 questions; full-context physically infeasible at 10M; exact-match + tokens-per-query reporting; abstention (_abs) questions as anti-fabrication probes. Budget is *reported*, not *enforced*. |
| **WorldLines** | arXiv:2606.18847 | Long-horizon stateful **embodied** household agents; memory QA + embodied planning; state overwrites, partial observability. No budget/age/structural split. |
| **MemoryArena** | memoryarena.github.io | Interdependent multi-session agentic tasks; memorization coupled to action; LoCoMo-saturating agents fail here. |
| **MemGym** | arXiv:2605.20833 | Unified agent-gym harness; **memory-isolated scores** (decouple memory from reasoning/retrieval/tool-use confounders). |
| **Memora** ("From Recall to Forgetting") | arXiv:2604.20006 | Personalized-agent LTM; **FAMA** metric penalizes reliance on obsolete/invalidated memory; weekly->quarterly spans. |
| **StructMemEval** | arXiv:2602.11243 | Memory *organization* into task-appropriate structures (ledgers/lists/trees); RAG degrades when latent structure must be maintained. |
| **PMD-Bench** | arXiv:2607.04118 | Addressability of **LoRA-based memory banks** (coarse domain / fine document / task capability). Parametric-only. |
| **MemoryBench** | arXiv:2510.17281 | Memory + continual learning in LLM systems (earlier; still cited). |
| Adjacent (safety/contamination): MemEvoBench (2604.15774), MemContam/ConsistencyGate (2607.22962), MemSyco-Bench (2607.01071) | | Memory poisoning/mis-evolution/sycophancy — relevant precedent for canary design, not retention scoring. |

---

## 2. Six-axis verdict table

| # | Axis | Verdict | Closest prior art & what's missing |
|---|---|---|---|
| 1 | **Forgetting-curve (retention vs memory age)** | **LARGELY COVERED** (fragmented) | **ForgetBench** produces true Ebbinghaus-style forgetting curves but *parametric-editing only*. **MemTrace** measures retention vs memory age (in sessions) for long-context/RAG/external/agentic. **Ground Truth First** shows accuracy-vs-tenure crossovers (3->9 wk). Missing: one curve protocol spanning parametric + non-parametric at fixed budget. Do not claim this axis as novel on its own. |
| 2 | **LTM-vs-STM in same harness** | **PARTIALLY COVERED** | **EvoMemBench**'s in-episode vs cross-episode axis is exactly a short- vs long-horizon split in one harness (also BEAM's 100K->10M scale buckets). Missing: retention-probe (fact-level) scoring rather than task success; no parametric arm. Weak novelty claim. |
| 3 | **Graded-importance recall (critical vs incidental, scored by class)** | **OPEN** | No benchmark found with ground-truth importance labels scoring retention by importance class. Nearest: **FadeMem** (arXiv:2601.18642, method paper) self-reports "82.1% retention of critical facts at 55% storage"; HTM-EAR uses importance-aware eviction (method); Ground Truth First has *volatility* classes (change-rate, not importance). A benchmark-grade importance-stratified retention score does not exist. **Strong novelty.** |
| 4 | **Relational retention (KG-grounded, relations not isolated facts)** | **LARGELY COVERED** | **RECON** has a deterministic, code-first provenance DAG with typed edges and cascade-invalidation tests — the closest thing to our ground-truth dependency graph. **SubtleMemory** tests fine-grained relation discrimination. **ForgetBench** scenario-QA covers relational retention for parametric. Missing everywhere: relation-retention and fact-retention are *not scored as separate headline metrics* (RECON scores holistically). The *separation* is ours; the graph-grounded eval is not. |
| 5 | **Cross-memory-type, one probe interface (RAG + parametric/LoRA + text bank + gated)** | **OPEN** | Every multi-paradigm harness stops at external memory: MemTrace (4 paradigms, no parametric), EvoMemBench (15 methods, no parametric), WorldMemArena (19 baselines, no parametric), RECON, Ground Truth First — none includes LoRA/parametric. PMD-Bench and ForgetBench are parametric-*only*. **No benchmark bridges the two worlds through one probe interface. Strongest novelty axis.** MemTrace's "knowledge point" probe is the design to cite-and-extend. |
| 6 | **Scale >> budget, fixed memory budget, retention curves** | **PARTIALLY COVERED** | Scale >> context exists: **BEAM** (10M tokens, context-stuffing infeasible; reports tokens/query, *recommends* same-budget comparison but doesn't enforce) and **LongMemEval-V2** (115M tokens; scores compactness via latency). **Ground Truth First** observes budget-eviction effects but budgets only one of five systems. EvoMemBench sweeps context 16K-128K. Missing: an *enforced* fixed memory budget with data-horizon sweep and retention curves as the primary readout. Novel as a protocol, not as a scale regime. |
| — | (Anti-gaming canaries) | PARTIAL PRECEDENT | Ground Truth First injection probes (42), BEAM/LongMemEval abstention questions, BIG-Bench canary GUIDs, MemContam. Retention-specific canaries (planted never-probed facts, paraphrase probes vs verbatim leakage) still unclaimed. |

---

## 3. Overall redundancy verdict

**StructMem-Bench is NOT redundant, but its novelty claim must be rewritten.** The July 2026
framing ("nothing separates structural from detail retention") is no longer safe: ForgetBench does
the separation for parametric editing, RECON supplies code-first dependency-DAG ground truth, and
MemTrace supplies the fact-level ("did you retain X") probe interface with memory-age curves.
Reviewers will know these papers.

**What remains genuinely unclaimed — the defensible core:**
1. **Axis 5 (strongest):** one probe interface spanning parametric/LoRA *and* RAG/text-bank/gated
   memory. Nobody bridges this; the field is split into two non-communicating eval literatures.
2. **Axis 3:** importance-stratified retention scoring with ground-truth labels.
3. **The conjunction on axes 1/4/6:** separate structural-vs-detail headline scores from one
   dependency graph (RECON has the graph, not the split), under an *enforced* fixed budget with
   horizon >> budget (BEAM has the scale, not the enforcement), with retention-by-age curves
   across all memory types (ForgetBench/MemTrace each have half).

**Recommended repositioning:** pitch as *"the first memory-type-agnostic retention benchmark:
structural vs detail vs importance-stratified retention curves at enforced budget"* — citing
ForgetBench, RECON, MemTrace, BEAM, and Ground Truth First as partial coverage to be unified,
rather than claiming a virgin gap. And rename (StructMemEval collision).

**Design elements worth adopting from prior art:**
- Ground Truth First's *script-before-text* generation (facts with validity intervals emitted
  deterministically, then LLM-rendered, then fidelity-verified) — exactly our programmatic-scoring
  requirement, and its "tenure crossover" result is the best motivation yet for budget-enforced,
  age-resolved evaluation.
- MemTrace's knowledge-point probe with evidence conditions (present/missing/contradicted) —
  extend with our canary conditions.
- RECON's typed-edge provenance DAG — extend with separate relation-probe vs detail-probe scoring.

## Sources
- ForgetBench: https://arxiv.org/abs/2607.26455
- RECON: https://arxiv.org/html/2607.16716v1
- MemTrace: https://arxiv.org/abs/2606.17328
- Ground Truth First: https://arxiv.org/html/2607.21962v1
- EvoMemBench: https://arxiv.org/abs/2605.18421
- LongMemEval-V2: https://arxiv.org/abs/2605.12493
- WorldMemArena: https://arxiv.org/abs/2605.29341
- SubtleMemory: https://arxiv.org/pdf/2606.05761
- WorldLines: https://arxiv.org/pdf/2606.18847
- MemoryArena: https://memoryarena.github.io/
- MemGym: https://arxiv.org/pdf/2605.20833
- Memora / From Recall to Forgetting: https://arxiv.org/html/2604.20006v1
- StructMemEval (name collision): https://arxiv.org/abs/2602.11243
- PMD-Bench: https://arxiv.org/pdf/2607.04118
- FadeMem: https://arxiv.org/pdf/2601.18642
- BEAM: https://mem0.ai/blog/ai-memory-benchmarks-in-2026 ; https://hindsight.vectorize.io/blog/2026/04/02/beam-sota
- Experience Compression Spectrum ("missing diagonal"): https://arxiv.org/abs/2604.15877
- MemEvoBench: https://arxiv.org/pdf/2604.15774 ; ConsistencyGate/MemContam: https://arxiv.org/html/2607.22962v1
