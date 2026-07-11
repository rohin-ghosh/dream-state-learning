# Literature Survey: Parametric Memory for Continual LLM Agents

**Compiled:** 2026-07-11 | **Scope:** weights-as-memory, knowledge editing, Hopfield/associative memory, parameter isolation, small-model-as-memory. Prioritizes 2024–2026 work.
**Relevance frame:** dream-state project — wake-sleep consolidation with a learned routing policy on ALFWorld/AI2-THOR.

---

## 1. Parametric Memory: Weights as Memory (LoRA-as-memory, knowledge editing, continual FT)

### 1.1 ROME — Locating and Editing Factual Associations in GPT
- **ID/Venue:** arXiv:2202.05262, NeurIPS 2022 (Meng et al.)
- **Method:** Causal tracing localizes factual recall to mid-layer MLP modules; treats the MLP as a linear associative (key-value) memory and applies a closed-form rank-one update to rewrite one fact.
- **Setup:** GPT-2 XL / GPT-J; zsRE and CounterFact; metrics: efficacy, generalization (paraphrase), specificity (locality).
- **Key findings:** Established the "MLPs are key-value memories" view underpinning the whole field. One edit at a time only.
- **Limitations:** Does not scale to batches or sequences of edits; sequential ROME edits cause model collapse ("gradual then sudden" degradation).

### 1.2 MEMIT — Mass-Editing Memory in a Transformer
- **ID/Venue:** arXiv:2210.07229, ICLR 2023 (Meng et al.)
- **Method:** Extends ROME by spreading least-squares updates across a range of critical MLP layers, enabling thousands of simultaneous fact insertions.
- **Setup:** GPT-J 6B, GPT-NeoX 20B; CounterFact/zsRE at 10k-edit scale.
- **Key findings:** ~10,000 edits in one batch with good efficacy/specificity — orders of magnitude beyond ROME.
- **Limitations:** Degrades badly under *sequential* (lifelong) editing; later work (AlphaEdit, WilKE) shows accumulated perturbations disrupt preserved knowledge and cause "toxicity flash" failures.

### 1.3 AlphaEdit — Null-Space Constrained Knowledge Editing
- **ID/Venue:** arXiv:2410.02355, ICLR 2025 **Oral** (Fang et al.)
- **Method:** Within locate-then-edit, projects each parameter perturbation onto the null space of preserved-knowledge activations before applying it, so edits provably leave preserved-knowledge outputs unchanged. Adds ~1 line of code (a projection) to existing editors.
- **Setup:** LLaMA-3, GPT2-XL, GPT-J; sequential editing up to ~3,000 facts; CounterFact/zsRE + downstream-ability (general capability) probes.
- **Key numbers:** Average **+36.7%** performance boost when bolted onto most locate-then-edit methods; sustains ~3,000 sequential edits without collapse.
- **Limitations:** Null space estimated from a fixed knowledge sample; overhead/behavior at much larger edit counts and on non-factual (procedural/skill) knowledge unexplored. Successor **EvoEdit** (arXiv:2510.13851) evolves the null-space alignment over time for robustness/efficiency.

### 1.4 WISE — Rethinking Knowledge Memory for Lifelong Model Editing
- **ID/Venue:** arXiv:2405.14768, NeurIPS 2024 (Wang et al., ZJU)
- **Method:** Dual parametric memory: frozen main memory (pretrained weights) + a **side memory** (a copied FFN region) that receives edits; a learned **router** decides per-query whether to read main or side memory. Knowledge sharding merges edit shards to avoid conflicts. Explicitly frames the reliability–locality–generalization "impossible triangle" of editing either main weights or retrieval.
- **Setup:** LLaMA-2, Mistral, GPT-J; zsRE, CounterFact, hallucination (SelfCheckGPT), OOD; hundreds–thousands of sequential edits.
- **Key findings:** First to show that routing between a pristine backbone and an edited parametric side-region beats both direct-weight editing and pure retrieval in lifelong settings.
- **Limitations:** Side memory is a single dense region; routing is activation-threshold based, not a learned policy over consolidation; QA-style facts, not agent skills.
- **Project note:** WISE is the closest prior in the *editing* literature to "dedicated parametric memory region + router" — but the router is a read-time gate, not a wake-sleep consolidation policy.

### 1.5 MEMOIR — Lifelong Model Editing with Minimal Overwrite and Informed Retention
- **ID/Venue:** arXiv:2506.07899, NeurIPS 2025 (Wang, Qin, Dimitriadis, Favero, Frossard — EPFL)
- **Method:** Adds a **residual memory module** (dedicated parameter block parallel to an FFN). Each edit is confined to a distinct sparse subset of the memory parameters via **sample-dependent sparse input-activation masks** (TopHash-style), minimizing inter-edit interference. At inference, sparse activation patterns of the query are matched against stored edit patterns to activate only relevant edits; unrelated queries bypass the memory entirely.
- **Setup:** LLaMA-3-8B, Mistral-7B; QA (zsRE), hallucination correction, OOD generalization; thousands of sequential edits; reliability/generalization/locality metrics.
- **Key numbers:** SOTA across reliability, generalization, locality; scales to thousands of sequential edits with minimal forgetting, beating WISE/AlphaEdit-class baselines.
- **Limitations:** Facts, not skills/experiences; memory module capacity vs. edit count at extreme scale not characterized; no consolidation from episodic traces — edits arrive as supervised (subject, relation, object) targets.
- **Project note:** This IS "masked subnetwork of a dedicated parametric region as memory" — but for factual editing of a static LLM, not for agent experience consolidation.

### 1.6 AnyEdit — Edit Any Knowledge Encoded in Language Models
- **ID/Venue:** arXiv:2502.05628, ICML 2025
- **Method:** Autoregressive editing paradigm: decomposes long-form/free-form knowledge (code, math, poetry, not just triplets) into sequential chunks and iteratively edits the key token in each chunk; grounded in a mutual-information chain-rule argument.
- **Setup:** UnKEBench, AKEW, and new **EditEverything** long-form benchmark; LLaMA/Qwen backbones.
- **Key numbers:** ~21%+ improvement over prior editors on long-form knowledge.
- **Limitations:** Still supervised target text; sequential-edit robustness inherits base editor issues.

### 1.7 O-LoRA — Orthogonal Subspace Learning for LM Continual Learning
- **ID/Venue:** arXiv:2310.14152, EMNLP 2023 Findings (Wang et al.)
- **Method:** Learns each new task in a low-rank LoRA subspace constrained orthogonal to subspaces of all previous tasks' LoRAs; past LoRAs frozen, no replay data stored.
- **Setup:** Standard CL benchmark (AfriSenti/T5 + LLaMA-7B on 15-task sequences); metrics: average accuracy, forgetting.
- **Key findings:** Marginal parameter cost, no replay; became the reference PEFT-CL baseline.
- **Limitations:** Rank/subspace budget exhausts with many tasks; orthogonality restricts forward transfer; task identity needed at train time.

### 1.8 O-LoRA successors (2025–2026)
- **OPLoRA** (arXiv:2510.13003): SVD-decomposes pretrained W, projects LoRA updates orthogonal to top-k singular subspaces on *both* sides (left/right projections), provably preserving dominant pretrained directions; introduces ρ_k metric for subspace interference. Matches LoRA on math/code/chat while retaining prior knowledge significantly better.
- **Merge before Forget** (arXiv:2512.23017): maintains a **single** LoRA over the whole task stream — orthogonal basis initialization per task, then time-aware-scaled continual merging into one unified LoRA. Reduces forgetting vs. O-LoRA without growing adapter count. Relevant to consolidation: it is essentially "merge new experience-adapter into a consolidated adapter."
- **Dynamic orthogonal continual fine-tuning** (arXiv:2509.23893) and **Lie-group orthogonal LoRA** (arXiv:2509.06100): refine the orthogonality constraint (dynamic subspace re-estimation; multiplicative Lie-group updates).
- **SAME** (2026): sliding-window online SVD of LoRA parameter covariance retains spectral anchors as task-anchoring directions with curvature-aware consolidation scores.

### 1.9 How LoRA Remembers? A Parametric Memory Law for LLM Finetuning
- **ID/Venue:** arXiv:2605.30260, May 2026 (Xu, Zhang et al., ZJU/Alibaba)
- **Method:** Uses LoRA as a controlled probe of parametric memory capacity. Establishes a **power law linking loss reduction to effective parameter count and sequence length**; finds token-level **phase transitions** — once prediction probability crosses ~0.5, greedy decoding recalls verbatim. Proposes **MemFT**, which reallocates training compute to below-threshold tokens.
- **Setup:** Controlled fact-injection fine-tuning across LoRA ranks/model scales; metrics: ΔLoss, recall probability, memory fidelity/efficiency.
- **Key numbers:** Quantitative capacity law for LoRA-as-memory (how many facts fit in rank r); MemFT improves fidelity and efficiency over uniform fine-tuning.
- **Limitations:** Marked "ongoing work"; verbatim factual recall, not skill memory; capacity law not yet validated on agentic/procedural data.
- **Project note:** Directly useful for sizing the sleep-phase LoRA memory budget.

### 1.10 TMEM — Scaling Self-Evolving Agents via Parametric Memory
- **ID/Venue:** arXiv:2606.04536, June 2026 (Ren et al., Alibaba/Tongyi)
- **Method:** Agents absorb distilled supervision into **fast LoRA weights via lightweight online updates within a single episode** — an "agentic decision process with fast-weight rollout dynamics": actions sampled from π_{θ0+Δt}; special extraction actions produce supervision that updates Δt. SVD-based LoRA subspace initialization accelerates convergence.
- **Setup:** LoCoMo, LongMemEval-S, multi-objective search, CL-Bench; vs. summary-based and retrieval-based memory baselines across model scales.
- **Key findings:** Consistently outperforms summary/retrieval memory baselines; behavior genuinely changes mid-episode rather than being conditioned on frozen context.
- **Limitations:** Online (wake-time) updates, no offline/sleep consolidation phase or learned write policy; conversational/search tasks rather than embodied benchmarks.
- **Project note:** The most important 2026 competitor paper — "LoRA-as-agent-memory" is now published. Differentiator for dream-state: offline wake-sleep consolidation + learned routing policy + embodied (ALFWorld) setting.

### 1.11 User as Engram — Internalizing Per-User Memory as Local Parametric Edits
- **ID/Venue:** arXiv:2606.19172, June 2026 (Bojie Li)
- **Method:** Stores per-user facts as surgical edits to a **hash-keyed parametric memory table** (Engram model): each fact toggles a lookup at its exact trigger and adds the needed value, leaving all else unchanged; different users occupy disjoint hash slots of one shared table; shared reasoning lives in one common adapter. Explicitly brain-inspired episodic/semantic separation.
- **Setup:** Personalization QA with indirect reasoning over user facts; vs. per-user LoRA and retrieval pipelines; ~100 facts per user.
- **Key numbers:** ~**33,000× smaller** per-user footprint than per-user LoRA; **5.6×** higher indirect-reasoning accuracy; never degrades base model on unrelated tasks; beats retrieval on 2.5×-larger models after ~100 facts/user.
- **Limitations:** Hash-collision management; facts only; single-author preprint, limited eval breadth.

### 1.12 Language Models Need Sleep (sleep-like consolidation into fast weights)
- **ID/Venue:** arXiv:2605.26099, May 2026
- **Method:** Hybrid SSM-attention models get a **sleep phase at context-window boundaries**: N offline recurrent passes over accumulated context update fast weights in SSM blocks via a learned local rule, then the KV cache is cleared. Converts context (episodic) into fast-weight (parametric) memory while keeping single-pass inference latency.
- **Setup:** Jet-Nemotron 2B, Ouro 1.4B; Rule-110 CA, multi-hop graph retrieval (up to 16 hops), GSM-Infinite (1–8 ops); accuracy/test loss vs. sleep depth N.
- **Key numbers:** Accuracy scales with sleep duration N; up to **52%** accuracy gain with sliding-window eviction + sleep; largest gains on deepest sequential reasoning.
- **Limitations (stated):** Synthetic tasks only; no comparison to test-time training or RAG; training instability at large N; no analysis of what fast weights encode.

### 1.13 SCM — Sleep-Consolidated Memory with Algorithmic Forgetting
- **ID/Venue:** arXiv:2604.20943, 2026
- **Method:** Biologically-inspired memory stack: bounded working memory (7 episodes), multi-dimensional importance tagging (novelty/valence/task-relevance/repetition), offline **NREM/REM sleep-stage consolidation**, value-based algorithmic forgetting, and a self-model for introspection. Consolidation is into a symbolic/graph store (NetworkX), not weights.
- **Setup:** Llama-3.2 (Q4_K_M) for semantic parsing; 8 tests of recall/latency/consolidation/forgetting; runs on an M1 MacBook Air up to 360 concepts.
- **Key numbers:** Perfect recall (1.00) in 10-turn conversations; **90.9%** memory-noise reduction via adaptive forgetting; sub-ms retrieval; bounded memory size.
- **Limitations (stated):** NetworkX scaling beyond 10K nodes; dependent on local-LLM extraction fidelity; no multimodal, no continuous background operation. Small-scale system paper — sleep metaphor without parametric consolidation.

### 1.14 Position: Modular Memory is the Key to Continual Learning Agents
- **ID/Venue:** arXiv:2603.01761, 2026 (Dorovatas et al., 24 authors — CL community position paper)
- **Method/Argument:** Continual agents need **modular memory** (episodic/semantic/procedural modules on different timescales) rather than monolithic weights or a single buffer; argues for hybrids of parametric memory (general knowledge) and non-parametric stores (specific experiences), with consolidation between them; provides a taxonomy.
- **Key claims:** Modularity resolves stability–plasticity conflicts; open problems include module granularity and *learning when/what to consolidate* — i.e., exactly the routing-policy question dream-state targets.
- **Limitations:** Position paper — no system or numbers.

---

## 2. Modern Hopfield Networks ↔ Transformer Attention

### 2.1 Hopfield Networks is All You Need
- **ID/Venue:** arXiv:2008.02217, ICLR 2021 (Ramsauer et al., Hochreiter lab)
- **Method:** Continuous-state modern Hopfield network with log-sum-exp energy; its one-step update rule **is exactly transformer softmax attention** (Q/K/V as state/stored patterns). Storage capacity is exponential in dimension; retrieval converges in ~1 step with exponentially small error.
- **Setup:** Hopfield layers as drop-in modules (pooling, associative memory, attention) on immune repertoire classification (MIL), UCI benchmarks, drug design.
- **Key findings:** The theoretical bridge: attention = one read from a dense associative memory. Basis for interpreting KV caches, in-context learning, and retrieval heads as associative recall.
- **Limitations:** Static stored-pattern setting; no writing/consolidation dynamics; metastable states (attention over many patterns) blur retrieval.

### 2.2 Provably Optimal Memory Capacity for Modern Hopfield Models (spherical codes)
- **ID/Venue:** arXiv:2410.23126, NeurIPS 2024 (Hu et al.)
- **Method:** Recasts memory storage as spherical coding; derives tight optimal capacity bounds for transformer-compatible dense associative memories and a construction (U-Hop+) approaching them.
- **Key findings:** Exact characterization of how many patterns an attention-style memory can store/retrieve reliably at a given dimension — the theoretical budget for any attention-as-memory design.
- **Limitations:** Theory-first; assumes well-separated patterns; no LLM-scale empirical memory system.

### 2.3 On the Role of Hidden States of Modern Hopfield Network in Transformer (MHA)
- **ID/Venue:** arXiv:2511.20698, NeurIPS 2025 (Masumura & Taki)
- **Method:** Goes beyond the adiabatic approximation of Ramsauer et al.: retains MHN **hidden-state dynamics** inside self-attention ("modern Hopfield attention"), letting attention scores propagate from input to output layers.
- **Setup:** ViT and GPT-style models; rank-collapse/token-uniformity analyses + accuracy.
- **Key findings:** Mitigates rank collapse in deep transformers; accuracy gains in ViT and GPT **without additional trainable parameters**.
- **Limitations:** Architectural study; no explicit memory-system application; overhead of hidden-state recurrence not fully characterized.

### 2.4 Hopfield-Fenchel-Young Networks
- **ID/Venue:** arXiv:2411.08590, JMLR/2024-25 (Santos, Niculae, Martins et al.)
- **Method:** Unifies Hopfield retrieval via Fenchel-Young losses; sparse variants (sparsemax/entmax attention) yield **exact** retrieval and larger effective capacity; connects margins to retrieval guarantees.
- **Key findings:** Sparse attention = exact associative retrieval — relevant to designing sparse read/write memory heads.
- **Limitations:** Again pattern-retrieval benchmarks (MIL, memory tasks), not LLM memory systems.

### 2.5 Test-Time Regression: unifying sequence models with associative memory
- **ID/Venue:** arXiv:2501.12352, 2025 (Wang, Yu et al.)
- **Method:** Framework showing linear attention, SSMs, fast-weight programmers, online learners, and softmax attention are all instances of **test-time regression onto an associative memory**; memorization = regression fit, retrieval = prediction.
- **Key findings:** Gives design axes (regressor class, weighting, optimizer) that generate existing and new architectures; the conceptual bridge from Hopfield/attention to Titans-style learned memory.
- **Limitations:** Framework paper; modest-scale experiments.

### 2.6 Titans — Learning to Memorize at Test Time
- **ID/Venue:** arXiv:2501.00663, NeurIPS 2025 (Behrouz, Zhong, Mirrokni — Google)
- **Method:** A **neural long-term memory module whose weights are updated at test time** by gradient steps on a "surprise" (reconstruction) signal with momentum and weight decay (forgetting); composed with attention in three variants: Memory-as-Context (MAC), Memory-as-Gate (MAG), Memory-as-Layer (MAL). Parallelizable training, fast inference.
- **Setup:** Language modeling, commonsense, needle-in-haystack, BABILong, genomics, time series; vs. Transformers, Mamba-family, DeltaNet; contexts to **>2M tokens**.
- **Key numbers:** Outperforms Transformer and modern linear-recurrent baselines at comparable scale; scales past 2M-token contexts; on BABILong beats much larger models incl. GPT-4-class with retrieval.
- **Limitations:** Memory is per-sequence/test-time (wiped across sessions); requires custom architecture — not applicable post-hoc to a frozen pretrained LLM agent; consolidation rule is fixed (surprise+decay), not learned per-task.
- **Follow-ups:** ATLAS (2505.23735), Nested Learning / HOPE (Google, NeurIPS 2025) extend capacity and treat architectures as nested optimization ("self-modifying" memory) — same lineage.

### 2.7 Hopfield → LLM-memory connections (state of play, mid-2026)
- In-context denoising (arXiv:2502.05164) shows one-layer transformers implement associative-memory retrieval in context; Context-Gated Associative Retrieval (arXiv:2605.10970) and Graph Hopfield Networks (arXiv:2603.03464) extend theory. The ICLR 2026 **MemAgents workshop** proposal explicitly lists Hopfield-based associative layers as a retrieval channel for agent memory — i.e., the connection to *agent* memory systems is recognized as an open direction, but **no published system yet uses a modern Hopfield network as the consolidated memory of an LLM agent**. Gap confirmed.

---

## 3. Parameter Isolation / Masked Subnetworks as Memory Regions

### 3.1 Foundations (pre-LLM, for context)
- **PackNet** (arXiv:1711.05769, CVPR 2018): iterative prune-and-retrain packs multiple tasks into one network via binary masks; frozen past-task parameters give zero forgetting; capacity exhausts.
- **HAT** (arXiv:1801.01423, ICML 2018): learns near-binary hard attention masks per task end-to-end; masks gate units, protecting prior tasks while allowing reuse.
- **SupSup / supermasks** (arXiv:2006.14769, NeurIPS 2020): fixed random weights; each task = a learned binary supermask; task inference by minimizing output entropy over masks; thousands of tasks in superposition.

### 3.2 ExSSNeT — Exclusive Supermask Subnetwork Training
- **ID/Venue:** arXiv:2210.10209, ACL Findings 2023 (Yadav & Bansal)
- **Method:** Learns a supermask per task, then **trains only mask-selected weights not already claimed by earlier tasks** (exclusion), fixing SupSup's no-weight-training limitation; KNN-based mask sharing for related tasks.
- **Setup:** NLP (T5-style) and vision CL sequences; accuracy + forgetting.
- **Key findings:** Outperforms SupSup and strong CL baselines with zero forgetting on NLP task streams.
- **Limitations:** Task identity needed; pre-LLM scale; masks per task, not per memory/experience.

### 3.3 MoSEs — Mixtures of SubExperts for Large Language Continual Learning
- **ID/Venue:** arXiv:2511.06237, Nov 2025 (Haeyong Kang)
- **Method:** Inserts **sparse SubExperts** (masked parameter subsets) into transformer layers with **task-specific routing**; an adaptive router composes previously learned sparse parameters for new tasks (transfer) while isolation protects old ones; capacity grows sublinearly with tasks.
- **Setup:** TRACE continual-learning benchmark for LLMs; retention + scalability metrics vs. conventional CL baselines.
- **Key findings:** SOTA knowledge retention on TRACE with substantial memory/compute savings; demonstrates masked-subnetwork memory *with a learned router* inside an LLM.
- **Limitations:** Task-level granularity (not experience-level); supervised task streams, not agent trajectories; router trained per task arrival.

### 3.4 Related 2025–26 isolation/routing work (brief)
- **SwitchCIT**: switch network routes instructions to per-task LoRA-tuned models.
- **L2R**: isolates new PEFT modules; **memory-based router** (small example memory) learns to compose modules at inference — routing policy learned from a replay-like store.
- **Learning without Isolation (LwI, arXiv:2505.18568)**: pathway-protection alternative — model fusion preserves old-task pathways instead of hard masks.
- **Parameter-level soft-masking (SPG, ICML 2023)**: per-parameter importance soft-masks gradient flow rather than hard isolation.
- **Fine-grained sparse allocation for continual RL** (arXiv:2503.05246): neuron-level masks + dormant-neuron exploration for RL agents — closest masked-subnetwork work in a *decision-making* setting.
- **MEMOIR** (§1.5) is the strongest 2025 instance of the idea "dedicated parametric region + per-item sparse masks + activation-matched read routing."

### 3.5 Verdict on "masked model region as memory" for LLM agents
Masked-subnetwork memory exists for (a) task-level continual learning of LLMs (MoSEs, ExSSNeT lineage) and (b) fact-level lifelong editing (MEMOIR, WISE side memory; Engram hash-slots). **No published work as of mid-2026 uses a masked region of an LLM's weights as consolidated *experience/skill* memory for an embodied/interactive agent, written by an offline consolidation phase under a learned policy.** Circuit-level analyses of agent memory (arXiv:2605.03354) are diagnostic only.

---

## 4. Small Model as Memory (auxiliary network as learned compressed memory)

### 4.1 Larimar — LLMs with Episodic Memory Control
- **ID/Venue:** arXiv:2403.11901, ICML 2024 (Das et al., IBM + Princeton)
- **Method:** CLS-inspired: a small **encoder + generative associative memory matrix + decoder-conditioning** module acts as a hippocampal fast-learning system beside the neocortical LLM. New facts are written by **one-shot, gradient-free** pseudo-inverse updates to the memory during inference; supports selective forgetting and read/write control.
- **Setup:** GPT-2/GPT-J-class decoders; knowledge editing (CounterFact, zsRE) incl. sequential editing; fact forgetting; context generalization.
- **Key numbers:** Editing accuracy comparable to best editors with **8–10× speedups** (no gradient editing); strong selective-forgetting results.
- **Limitations:** Memory sized in slots (K×d matrix) — capacity limited; decoder must be trained/adapted to condition on memory readouts; fact-level episodes, not agent skills.
- **Project note:** The canonical "small associative module as memory for a big LM"; its memory is essentially a linear Hopfield-style associative store — bridge between §2 and §4.

### 4.2 Memory³ — Language Modeling with Explicit Memory
- **ID/Venue:** arXiv:2407.01178, 2024 (Yang et al., Shanghai IAAR / Moqi / PKU)
- **Method:** Adds a third memory tier between weights (implicit) and KV-cache (working): knowledge pre-compressed offline into sparse **explicit memory** (quantized KV blocks) retrieved during inference; memory-circuitry theory motivates externalizing specific knowledge so the backbone stores only "abstract knowledge."
- **Setup:** 2.4B model trained from scratch with explicit memory bank; vs. larger LLMs and RAG.
- **Key numbers:** 2.4B + explicit memory **beats much larger LLMs and RAG baselines**; lower train/inference cost; faster decoding than RAG.
- **Limitations:** Requires from-scratch pretraining with memory; static knowledge bank, not agent-updated memory.

### 4.3 MemoryLLM / M+ — latent memory pool inside the model + retriever
- **ID/Venue:** MemoryLLM arXiv:2402.04624 (ICML 2024); **M+** arXiv:2502.00592 (ICML 2025; Wang et al., UCSD+IBM)
- **Method:** MemoryLLM: 1B-parameter pool of memory tokens in every layer of a 7B model, self-updated by mixing new context in with partial random dropping (exponential decay of old info). M+ adds **long-term memory: evicted memory tokens go to CPU-side storage and a co-trained retriever** pulls relevant vectors back per layer during generation (256 compressed vectors/layer).
- **Setup:** Llama-2-7B backbone; SQuAD/NaturalQA-derived knowledge-retention probes, LongBench-style long-context tasks.
- **Key numbers:** Knowledge retention horizon extended from <20k to **>160k tokens** at similar GPU memory; outperforms MemoryLLM and strong long-context baselines.
- **Limitations:** Retention still decays (soft forgetting by design); requires fine-tuning backbone to read memory tokens; conversational/document memory, not skill consolidation.

### 4.4 MemoRAG — a light long-range LLM as global memory
- **ID/Venue:** arXiv:2409.05591, 2024-25 (Qian et al., BAAI); WWW 2025
- **Method:** Dual-system: a **small/cheap long-context "memory model"** ingests the whole corpus and forms a compressed global memory; at query time it drafts clue answers that guide a retriever, then a large expressive LLM composes the final answer. Literally "small model as memory for a large model."
- **Setup:** ULTRADOMAIN (long-context QA across domains), needle tasks; vs. vanilla RAG and long-context LLMs.
- **Key numbers:** Consistent wins over standard RAG on ambiguous/unstructured global queries; handles corpora far beyond the large model's context.
- **Limitations:** Memory model quality caps recall; two-model latency; memory is per-corpus, rebuilt rather than continually consolidated.

### 4.5 LightMem — Lightweight LLM Agent Memory with Small Language Models
- **ID/Venue:** arXiv:2604.07798, 2026 (Zhang et al.)
- **Method:** Small LMs run the agent-memory subsystem: three tiers (STM context, MTM reusable summaries, LTM consolidated knowledge); fixed-budget two-stage retrieval (vector coarse → semantic re-rank); **offline consolidation** integrates evidence into LTM; multi-user via IDs.
- **Setup:** LoCoMo; F1 vs. A-MEM and other memory systems; latency profiling.
- **Key numbers:** ~**+2.5 F1** over A-MEM; median retrieval latency **83 ms**, end-to-end **581 ms**; gains consistent across scales.
- **Limitations:** Memory content remains text/summaries (non-parametric); small LM used as memory *manager*, not as a learned compressed parametric store.

### 4.6 ApCM — Auxiliary-predicted Compress Memory Model
- **ID/Venue:** arXiv:2601.11609, Jan 2026 (v2 Apr 2026)
- **Method:** Neural memory storage combining invertible compression with a **learnable auxiliary predictor**: the auxiliary net predicts reconstructable content so only residuals are stored — a trained small network acting as lossy-but-correctable memory for a larger system.
- **Setup/numbers:** Storage-fidelity/compression-rate benchmarks (details thin; early-stage preprint).
- **Limitations:** Not yet integrated with an LLM agent loop; single-group preprint.

### 4.7 Verdict on "small model as memory"
The pattern exists in several forms: small associative module (Larimar), latent memory pool + retriever (M+), small long-context LM as global memory (MemoRAG), small LM as memory manager (LightMem), auxiliary predictive compressor (ApCM). **None yet trains a small network as the consolidated *skill/experience* memory of an LLM agent with a learned wake-sleep write policy.** Closest conceptual neighbors: Larimar (CLS framing, fast/slow systems) and Titans (learned neural memory module, but in-architecture and per-sequence).

---

## 5. Cross-Cutting Synthesis & Gaps (for dream-state)

1. **Convergent architecture across all four threads:** frozen backbone + dedicated parametric memory region + sparsity/masking to localize writes + a router/retriever to gate reads (WISE, MEMOIR, Engram, MoSEs, M+, Titans-MAC). The field has converged on the *read* path; the *write/consolidation policy* is everywhere hand-designed (surprise+decay in Titans, least-squares in editors, importance tags in SCM).
2. **What is NOT yet done (as of 2026-07):**
   - Masked weight region as **experience/skill** memory for an embodied LLM agent (ALFWorld/AI2-THOR-class), written offline.
   - A **learned routing/consolidation policy** deciding what goes to parametric vs. non-parametric memory during a sleep phase (named as an open problem by the Modular Memory position paper, arXiv:2603.01761).
   - Modern Hopfield networks used as the consolidated memory substrate of an LLM agent (flagged as a direction by the ICLR 2026 MemAgents workshop; no system paper).
3. **Nearest competitors to monitor:** TMEM (2606.04536) — online LoRA fast-weight agent memory; MEMOIR (2506.07899) — masked residual memory + activation routing; Sleep-consolidation line (2605.26099, 2604.20943); Titans/ATLAS/HOPE lineage (Google) — learned test-time memory modules.
4. **Useful tools/measures:** Parametric Memory Law (2605.30260) for LoRA memory budgeting; spherical-code capacity bounds (2410.23126) for associative memory sizing; AlphaEdit null-space projection (2410.02355) as a drop-in interference guard for sleep-phase weight writes; TRACE and EvoMemBench (2605.18421) as evaluation candidates.

## Quick Reference Table

| # | Paper | ID | Year | Thread | One-liner |
|---|-------|----|------|--------|-----------|
| 1 | ROME | 2202.05262 | 2022 | editing | rank-one MLP fact edit |
| 2 | MEMIT | 2210.07229 | 2023 | editing | 10k batch edits across layers |
| 3 | AlphaEdit | 2410.02355 | 2025 | editing | null-space projection, +36.7% |
| 4 | WISE | 2405.14768 | 2024 | editing/routing | side memory + read router |
| 5 | MEMOIR | 2506.07899 | 2025 | editing/masks | sparse-masked residual memory |
| 6 | O-LoRA | 2310.14152 | 2023 | continual FT | orthogonal LoRA subspaces |
| 7 | OPLoRA / Merge-before-Forget | 2510.13003 / 2512.23017 | 2025 | continual FT | projection / continual LoRA merging |
| 8 | Parametric Memory Law | 2605.30260 | 2026 | LoRA-as-memory | capacity power law, MemFT |
| 9 | TMEM | 2606.04536 | 2026 | agent | online fast-LoRA agent memory |
| 10 | User as Engram | 2606.19172 | 2026 | parametric memory | hash-slot per-user edits |
| 11 | LMs Need Sleep | 2605.26099 | 2026 | consolidation | offline passes → fast weights |
| 12 | SCM | 2604.20943 | 2026 | consolidation | NREM/REM symbolic consolidation |
| 13 | Modular Memory position | 2603.01761 | 2026 | position | modular memory taxonomy |
| 14 | Hopfield Is All You Need | 2008.02217 | 2020 | Hopfield | attention = Hopfield retrieval |
| 15 | Optimal MHN capacity | 2410.23126 | 2024 | Hopfield | spherical-code capacity bounds |
| 16 | Modern Hopfield Attention | 2511.20698 | 2025 | Hopfield | MHN hidden states fix rank collapse |
| 17 | Test-time Regression | 2501.12352 | 2025 | Hopfield/theory | sequence models = assoc. memory |
| 18 | Titans | 2501.00663 | 2025 | learned memory | test-time-trained memory module |
| 19 | SupSup / ExSSNeT | 2006.14769 / 2210.10209 | 2020/23 | masks | supermask subnetworks |
| 20 | MoSEs | 2511.06237 | 2025 | masks/routing | sparse subexperts + router |
| 21 | Larimar | 2403.11901 | 2024 | small-model memory | episodic memory controller, 8–10× |
| 22 | Memory³ | 2407.01178 | 2024 | explicit memory | third memory tier, 2.4B beats larger |
| 23 | M+ | 2502.00592 | 2025 | latent memory | retriever + memory pool, 160k+ |
| 24 | MemoRAG | 2409.05591 | 2024 | small-model memory | light LLM as global memory |
| 25 | LightMem | 2604.07798 | 2026 | small-model memory | small-LM memory manager, 83ms |
