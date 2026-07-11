# 03 — Agent Memory Systems & Benchmarks: Literature Survey (as of July 2026)

Survey for the dream-state project (wake-sleep consolidation with learned routing policy). Focus: how agents store/retrieve/consolidate experience, and how the field currently *evaluates* cross-episode memory and continual learning. Prioritized 2024–2026; foundational 2023 systems included for lineage.

---

## Part 1 — Agent memory systems

### 1.1 Foundational systems (2023–2024, still the standard baselines)

#### MemGPT / Letta
- **arXiv:** 2310.08560 (2023); now productized as Letta.
- **Method:** OS-inspired virtual context management. Three tiers: core memory (always in-context, "RAM"), recall memory (conversation history), archival memory (external vector store, "disk"). The LLM itself issues function calls to page memory in/out.
- **Setup/results:** Document QA and multi-session chat; large gains over fixed-context baselines on deep multi-session recall.
- **2025–2026 evolution:** Letta's **"sleep-time compute"** (blog + paper, 2025): a second agent runs during idle time to reorganize memory, converting "raw context" into "learned context." Directly the closest industrial analogue to a wake-sleep split — but the consolidation policy is hand-designed, not learned.
- **Limitations:** Consolidation is prompt-engineered summarization; no notion of what *should* be forgotten; evaluated mostly on conversational recall, not embodied/task competence.

#### Generative Agents (Park et al.)
- **arXiv:** 2304.03442, UIST 2023.
- **Method:** Memory stream of natural-language observations; retrieval scored by recency × importance × relevance; periodic **reflection** synthesizes higher-level abstractions from clusters of memories (an early consolidation mechanism).
- **Setup:** 25 agents in a Smallville sandbox; believability evaluations (information diffusion, relationship memory, party coordination).
- **Limitations:** Believability metrics, not task success; reflection tree grows unboundedly; no forgetting; no quantitative cross-episode benchmark.

#### Reflexion (Shinn et al.)
- **arXiv:** 2303.11366, NeurIPS 2023.
- **Method:** Verbal self-reflection on failures stored in an episodic buffer, prepended to subsequent attempts. Memory = short natural-language lessons, within a task's retry loop.
- **Key numbers:** ALFWorld 130/134 tasks (97%) with retries vs ~75% ReAct; HumanEval 91% pass@1.
- **Limitations:** Memory scoped to retries of the *same* task; no cross-task/cross-episode transfer; buffer is small and unconsolidated.

#### ExpeL (Zhao et al.)
- **arXiv:** 2308.10144, AAAI 2024.
- **Method:** Experiential learning without weight updates: collects trajectories across training tasks, then distills two stores — (1) natural-language *insights* extracted by comparing success/failure pairs (with upvote/downvote/edit ops on the insight list), (2) retrieved successful trajectories as few-shot exemplars.
- **Key numbers:** ALFWorld 59% → ~54–59% base vs ExpeL ~59–73% (setup-dependent); consistent gains on HotpotQA, WebShop; showed positive cross-task transfer.
- **Relevance:** The insight-extraction step is a primitive consolidation policy (extract/merge/edit/prune) — a hand-coded ancestor of a learned routing policy.
- **Limitations:** One-shot offline distillation, not continual; insight list flat and small; no study of what gets lost in abstraction.

#### Voyager (Wang et al.)
- **arXiv:** 2305.16291 (2023), later NeurIPS-era standard.
- **Method:** Lifelong learning in Minecraft via a **skill library**: verified JS code snippets stored with embedding keys, retrieved by task similarity; automatic curriculum; iterative prompting with environment feedback. Memory = executable procedures, not facts.
- **Key numbers:** 3.3× more unique items, 2.3× longer tech-tree progression, 15.3× faster than ReAct/Reflexion/AutoGPT baselines; skills transfer to a new world.
- **Limitations:** Stores only *procedural* memory; no episodic/spatial memory (does not remember where resources were); tech tree measures acquisition, not retention/forgetting.

#### JARVIS-1 (Wang et al.)
- **arXiv:** 2311.05997 (2023/2024).
- **Method:** Multimodal (MineCLIP-style) memory-augmented planner in Minecraft: stores (task, plan, multimodal state) triples; retrieves by situation similarity to condition new plans; self-improves via self-instruct + memory growth.
- **Key numbers:** ~12.5% success on the long-horizon ObtainDiamondPickaxe (≈5× prior VPT-era SOTA); >93% average on 200+ short tasks.
- **Limitations:** Memory grows monotonically; retrieval-only usage; no consolidation or forgetting; evaluation is single-episode success, memory helps only as exemplars.

#### Mem0 / Mem0-g
- **arXiv:** 2504.19413 (2025).
- **Method:** Production memory layer: extraction LLM proposes candidate memories; update LLM decides ADD/UPDATE/DELETE/NOOP against existing store (an explicit, hand-designed write policy). Mem0-g variant stores directed labeled graphs.
- **Key numbers:** 67.1% LLM-judge on LoCoMo, ~90% token savings vs full context, p95 search 0.2 s; Mem0-g 58.1% vs OpenAI memory 21.7% on temporal questions.
- **Limitations:** Conversational/personalization focus; write policy is fixed prompts; no embodied or task-execution evaluation.

#### A-MEM (2025) & HippoRAG (2024)
- **A-MEM** (arXiv 2502.12110): Zettelkasten-style agentic memory — each note gets LLM-generated links to prior notes; new memories can trigger updates ("evolution") of old ones; supersede detection for staleness.
- **HippoRAG** (arXiv 2405.14831, NeurIPS 2024): hippocampal-index theory — KG as index, personalized PageRank as pattern completion; single-step multi-hop retrieval; HippoRAG 2 (2025) extends to continual knowledge integration.
- **Limitations:** Both are retrieval/knowledge oriented; neither addresses skill consolidation or embodied experience.

### 1.2 New memory/consolidation systems (2025–2026)

#### Sleep-Like Memory Consolidation in LLMs
- **arXiv:** 2605.26099 (May 2026).
- **Method:** Periodically converts recent KV context into persistent **fast weights** via offline recurrent passes with a learned local update rule, then clears the cache — a literal wake/sleep alternation at the architecture level (parametric, not textual, consolidation).
- **Relevance:** Strongest parametric analogue to the dream-state wake-sleep design; but the consolidation rule is fixed once learned, not a per-experience routing policy.

#### SCM: Sleep-Consolidated Memory for LLMs
- **arXiv:** 2604.20943 (2026).
- **Method:** Multi-stage sleep cycle over an external memory store: consolidation, "dreaming" (generative recombination/replay), and intentional algorithmic forgetting.
- **Limitations:** Evaluated on conversational/QA memory benchmarks, not embodied task competence.

#### PEAM: Parametric Embodied Agent Memory (Minecraft)
- **arXiv:** 2605.27762 (2026).
- **Method:** Slow LLM reasoner + fast MoE-LoRA module that **internalizes failure→correction trajectory pairs** (behavioral cloning + contrastive objective). Two policy-like components highly relevant to us: a **"parameterization-worthiness score"** deciding *which* experiences get consolidated into weights, and a **self-triggered consolidation mechanism** deciding *when*. Per-category isolated adapters limit catastrophic forgetting.
- **Results:** Beats retrieval-based and parametric baselines on long-horizon Minecraft tasks; reduced forgetting of consolidated skills.
- **Limitations:** Minecraft-only; worthiness score is heuristic/learned offline, not an RL-trained routing policy; no evaluation of episodic/spatial memory (resource locations).

#### TiMem: Temporal-Hierarchical Memory Consolidation
- **arXiv:** 2601.02845 (2026).
- **Method:** Hierarchical consolidation for long-horizon conversational agents: raw turns → session summaries → cross-session themes, with temporal indexing so consolidation preserves when-information.
- **Limitations:** Conversational domain; consolidation schedule fixed.

#### FadeMem: Biologically-Inspired Forgetting
- **arXiv:** 2601.18642 (2026).
- **Method:** Ebbinghaus-style decay over memory entries with utility-modulated retention; low-utility fragments go dormant rather than deleted, revivable by strong cues.
- **Relevance:** One of the few papers treating forgetting as a *designed feature* with a tunable policy — a natural baseline for a learned forgetting/routing policy.

#### RecMem: Recurrence-based Memory Consolidation
- **arXiv:** 2605.16045 (2026).
- **Method:** Recurrent consolidation passes for long-running agents, amortizing memory maintenance cost; targets efficiency of lifelong agents.

#### "Useful Memories Become Faulty When Continuously Updated by LLMs" ⭐
- **arXiv:** 2605.12978 (2026).
- **Core finding:** Under repeated LLM-driven consolidation (Retain/Delete/Consolidate action space on ARC-AGI-style tasks), **memory utility rises then degrades, eventually falling below the no-memory baseline**. GPT-5.4 failed 54% of previously-solved problems when using consolidated memories; episodic-only (raw trajectory) retention **doubled** accuracy vs forced consolidation. Identical trajectories yield qualitatively different memories under different update schedules — degradation is caused by the consolidation process itself ("useful details dropped, spurious rules introduced").
- **Relevance:** This is the strongest published evidence for the exact failure mode dream-state targets: naive consolidation destroys load-bearing details. It *measures* degradation but does not decompose it into structural vs detail retention, and proposes no learned policy to fix it.
- **Limitations:** Abstract puzzle domain (ARC-AGI), not embodied; consolidation policies tested are fixed prompt strategies.

#### Position: Modular Memory is the Key to Continual Learning Agents
- **arXiv:** 2603.01761 (2026, position paper).
- **Argument:** Compressed encodings over raw trajectories; parameter modularity so consolidation updates stay localized; instance-weighted learning policies over stored experience (regularization/replay adapted from CL). Good framing citation for a learned consolidation-routing policy.

#### Other notable 2026 systems (brief)
- **SimpleMem** — efficient lifelong memory layer for LLM agents (2026).
- **ZenBrain** (arXiv 2604.23878) — neuroscience-inspired 7-layer memory architecture.
- **Continuum Memory Architectures** (arXiv 2601.09913) — background workers do replay walks, cluster abstraction, and gist extraction; detailed episodes fade once schemas emerge; abstract nodes keep back-links to source fragments. Conceptually closest published articulation of "keep the gist, drop the detail — but recoverably."
- **Experience Transfer for Multimodal LLM Agents in Minecraft** (arXiv 2604.05533) — cross-agent/cross-world experience reuse.
- **Hierarchical Skill Meta-Evolving** ("You Live More Than Once," arXiv 2605.28390) — multi-life skill evolution, Voyager lineage.
- **ACT-R-inspired remembering/forgetting for LLM agents** (HAI 2025, ACM 3765766.3765803) — activation-based recall/decay.

---

## Part 2 — Benchmarks for agent memory & continual learning

### 2.1 Established environments (pre-2025)

| Benchmark | ID/venue | What it measures | Memory relevance |
|---|---|---|---|
| **ALFWorld** | 2010.03768, ICLR 2021 | 6 household task families, text-parallel to ALFRED; 3,553 train tasks / 120 rooms | Single-episode success; no built-in cross-episode memory eval — memory papers bolt it on |
| **ALFRED** | CVPR 2020 | Vision-language embodied instruction following | Single-episode |
| **MineDojo** | 2206.08853, NeurIPS 2022 | 1000s of open-ended Minecraft tasks + internet knowledge base | Task breadth, not memory retention |
| **Voyager tech tree** | 2305.16291 | Unique items unlocked, tech-tree milestones over lifelong play | Measures skill *acquisition*; retention untested (no revisit-after-delay protocol) |
| **TextCraft** | ADaPT, 2311.05772 | Text-based Minecraft-style recipe crafting; difficulty = crafting-tree depth (1–4); deterministic | Compositional decomposition only; **no persistent world, no resource locations, episodes independent** |
| **Crafter** | 2109.06780 | 2D survival/crafting with achievement tree | Within-episode; procedurally regenerated worlds preclude cross-episode spatial memory |
| **SmartPlay / BALROG** | 2310.01557 / 2411.13543 | Game-suite reasoning evals (incl. Crafter, NetHack, MineDojo) | Include "learning from interaction" axes but reset between episodes |
| **LoCoMo** | 2402.17753 | Very-long conversational memory QA | Dialogue only |
| **LongMemEval (v1)** | 2410.10813, ICLR 2025 | 5 chat-memory abilities incl. temporal reasoning, knowledge updates, abstention | Dialogue only; static |
| **MEMTRACK** | 2510.01353 (2025) | Long-term memory + state tracking across multi-platform dynamic environments (Slack/Linear/Git-style) | Cross-tool state, not embodied |

### 2.2 Purpose-built memory / continual-learning benchmarks (2025–2026)

#### EvoMemBench ⭐
- **arXiv:** 2605.18421 (May 2026).
- **Design:** First unified 2×2 framework: **memory scope (in-episode vs cross-episode) × memory content (knowledge-oriented vs execution-oriented)**. Evaluates 15 memory methods + strong long-context baselines under one protocol.
- **Key findings:** Long-context models remain competitive with dedicated memory systems; memory helps most when context is limited or tasks complex; retrieval methods win on knowledge tasks; procedural/long-term memory wins on execution tasks *when stored experience aligns with task structure*; no method wins everywhere.
- **Limitations:** Composed from existing environments; does not test degradation of memory quality over long consolidation horizons; no spatial/embodied axis.

#### LongMemEval-V2
- **arXiv:** 2605.12493 (2026).
- **Design:** "Experienced colleague" framing — 451 curated questions over up to 500 trajectories/question, 115M tokens of history, in customized web environments. Five abilities: static state recall, dynamic state tracking, workflow knowledge, **environment gotchas**, premise awareness.
- **Numbers:** best system (AgentRunbook-C) 72.5% vs RAG 48.5%, coding-agent baseline 69.3% (high latency).
- **Relevance:** "Environment gotchas" ≈ retention of hard-won environmental facts across episodes — conceptually close to remembering resource locations, but in web domains and QA form (memory queried, not *used* for acting).

#### WorldLines ⭐
- **arXiv:** 2606.18847 (June 2026).
- **Design:** Long-horizon embodied household traces (dialogues, actions, feedback, object/device state changes) → **Memory QA + Embodied Task Planning** tasks. Companion framework ObsMem: visibility-aware memories + action-native state trails.
- **Findings:** Persistent failures on partial observability, **overwritten world states**, and translating retrieved memory into embodied plans.
- **Relevance:** Closest embodied analogue to "remember where things are / what state they're in" across long horizons — household, not crafting/resources.

#### WorldMemArena
- **arXiv:** 2605.29341 (2026).
- **Design:** 400 multi-session multimodal tasks (Lifelong Evolution + Agentic Execution), modeled as a 4-stage memory lifecycle (write, maintain, retrieve, use) with gold memory points, updates, distractors, evidence chains → **stage-level failure localization**.
- **Findings:** Better writing ≠ better performance; multimodal systems underuse visual evidence; self-managing memory agents flexible but costly/unreliable.
- **Relevance:** The stage-level diagnostic methodology is the right evaluation template for a routing policy (which stage does routing fix?).

#### EMemBench
- **arXiv:** 2601.16690 (Jan 2026).
- **Design:** Programmatic benchmark generating questions from *the agent's own trajectory* in 15 text games + visual seeds; 6 skills: single-hop, multi-hop, induction, temporal, **spatial reasoning**, adversarial memory; verifiable ground truth from game signals.
- **Findings:** Induction and spatial reasoning are persistent bottlenecks (worst in visual settings); persistent memory helps open-source LMs on text games, inconsistent for VLMs.
- **Limitations:** Primarily within-trajectory (single-episode) memory, per its own framing.

#### MineNPC-Task
- **arXiv:** 2601.05215 (2026).
- **Design:** User-authored Minecraft task suite (co-play with 8 expert players, 216 subtasks) normalized into parametric templates with preconditions/dependencies; machine-checkable validators; logs plan/action/**memory events** and memory persistence across tasks.
- **Findings (GPT-4o):** recurring breakdowns in code execution, inventory/tool handling, referencing, navigation; players explicitly flagged weak memory persistence across tasks.
- **Limitations:** Single model snapshot; human-in-the-loop protocol limits scale; memory persistence observed, not systematically scored.

#### SkillLearnBench
- **arXiv:** 2604.20087 (2026).
- **Design:** First benchmark for continual **skill generation**: 20 real-world tasks / 15 sub-domains; evaluates skill quality, execution trajectory, and task outcome across the generate-store-reuse cycle.
- **Findings:** No continual-skill method wins across tasks/LLMs; stronger base LLMs don't reliably help; external feedback enables genuine improvement while **self-feedback alone causes recursive drift**.
- **Relevance:** "Recursive drift under self-feedback" parallels the consolidation-degradation finding — self-generated abstractions corrupt the store.

#### Momento
- **arXiv:** 2606.00832 (2026).
- **Design:** Persistent multi-session service environments; consequential tool-mediated actions; temporal dependencies and evolving user goals across sessions.
- **Key failure mode found:** agents treat prior-session history as reliable current state instead of **stale information requiring re-validation**.

#### MemTrace
- **arXiv:** 2606.17328 (2026). Probes what final-accuracy metrics miss in long-term memory — process-level tracing of memory use. Useful methodological reference.

#### Others (brief)
- **AMA-Bench** (2602.22769) — long-horizon memory for agentic apps; self-declared limitation: **in-episode only**, calls for cross-task/lifelong extension.
- **MINTEval** (2605.18565) — memory under multi-target interference in long-horizon systems.
- **From Recall to Forgetting** (2604.20006) — benchmarks *forgetting* (incl. desirable forgetting) for personalized agents.
- **MemoryBench** — memory + continual learning for LLM systems (2025).
- **Mem2ActBench** — long-term memory *utilization* in task-oriented agents (retrieved memory → action).
- **ATANT v1.1** (2604.10981) — positions "continuity evaluation" vs memory/long-context/agentic-memory benchmarks.
- **ODYSSEY** (IJCAI 2025) — open-world Minecraft skills + benchmark, Voyager successor; skill library focus, not retention.
- **Cross-Scenario Generality of Agentic Memory** (2606.04315) — diagnostics showing memory systems overfit to their home scenario + a strong general baseline.
- **Memory survey** (2603.07670, 2026): taxonomy = temporal scope × representational substrate × **control policy**; 5 families (context compression, retrieval stores, reflective self-improvement, hierarchical virtual context, **policy-learned management**); names *continual consolidation* and *learned forgetting* as open frontiers — direct positioning support for dream-state.

---

## Part 3 — Cross-episode memory evaluation: state of play

What exists, by increasing relevance to "success requires remembering prior episodes":

1. **Dialogue/QA cross-session recall** — LoCoMo, LongMemEval v1/v2, Momento, MEMTRACK. Memory is *queried*, mostly not *used for acting* (Momento/MEMTRACK partially act).
2. **Cross-episode as an evaluation axis** — EvoMemBench explicitly scores cross-episode × execution-oriented memory; the closest thing to a standardized cross-episode protocol. Composed of existing environments; no persistent spatial world.
3. **Embodied persistent state** — WorldLines (household object/device states across long traces), WorldMemArena (evolving world state across sessions). Both test "the world persists and changes; stale memory hurts."
4. **Skill retention over lifetimes** — Voyager tech tree (acquisition only), PEAM (forgetting of consolidated skills, Minecraft), SkillLearnBench (skill libraries over task sequences), Hierarchical Skill Meta-Evolving.
5. **Consolidation-degradation measurement** — "Useful Memories Become Faulty" (2605.12978): the only work directly quantifying how consolidation itself erodes task-relevant memory over updates.

### Gap analysis (for dream-state positioning)
- **No benchmark decomposes retention into structural/schematic vs detail/episodic components.** WorldMemArena localizes failures by lifecycle *stage*; 2605.12978 measures aggregate degradation; EvoMemBench splits knowledge vs execution. None asks: after consolidation, does the agent retain the *map/recipe-graph/causal structure* while forgetting *specific instances* (or vice versa)? This axis appears unclaimed as of July 2026.
- **No text-based crafting environment with persistent resource locations across episodes.** TextCraft is deterministic, recipe-only, episode-independent. Crafter regenerates worlds. Minecraft benchmarks (MineNPC-Task, ODYSSEY, JARVIS-1/Voyager settings) have persistent worlds but are heavyweight, visually grounded, and none *scores* spatial-resource recall across episodes. Closest composites: MineNPC-Task (Minecraft, memory persistence across tasks, unscored) + WorldLines (persistent object locations/states, household QA+planning) + EvoMemBench (cross-episode execution axis, no space).
- **Consolidation policies are uniformly hand-designed** (Mem0's ADD/UPDATE/DELETE prompts, ExpeL's insight ops, PEAM's worthiness score, FadeMem's decay). The 2603.07670 survey explicitly lists "policy-learned management" as a thin, emerging family — a learned routing policy trained against retention outcomes is well-positioned.
- **Evidence base for the problem is strong:** consolidation degrades memory below no-memory baselines (2605.12978); self-feedback causes recursive drift (SkillLearnBench); stale memory misleads action (Momento, WorldLines); better writing ≠ better use (WorldMemArena).

---

## Key references (quick list)
MemGPT 2310.08560 · Generative Agents 2304.03442 · Reflexion 2303.11366 · ExpeL 2308.10144 · Voyager 2305.16291 · JARVIS-1 2311.05997 · Mem0 2504.19413 · A-MEM 2502.12110 · HippoRAG 2405.14831 · ALFWorld 2010.03768 · MineDojo 2206.08853 · TextCraft/ADaPT 2311.05772 · LongMemEval 2410.10813 · MEMTRACK 2510.01353 · EvoMemBench 2605.18421 · LongMemEval-V2 2605.12493 · WorldLines 2606.18847 · WorldMemArena 2605.29341 · EMemBench 2601.16690 · MineNPC-Task 2601.05215 · SkillLearnBench 2604.20087 · Momento 2606.00832 · Useful-Memories-Faulty 2605.12978 · PEAM 2605.27762 · Sleep-Like Consolidation 2605.26099 · SCM 2604.20943 · TiMem 2601.02845 · FadeMem 2601.18642 · RecMem 2605.16045 · Modular-Memory position 2603.01761 · Memory survey 2603.07670 · AMA-Bench 2602.22769 · MINTEval 2605.18565 · Recall-to-Forgetting 2604.20006 · Continuum Memory 2601.09913 · Cross-Scenario Generality 2606.04315
