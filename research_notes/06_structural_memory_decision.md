# Prior-Art Check: Structure-Preserving, Detail-Discarding Memory Consolidation for LLM Agents

Date: 2026-07-11
Author: prior-art sweep (arXiv / Scholar / Semantic Scholar, 2022–2026 priority)

## Target mechanism being checked

A long-term memory for LLM agents that, during an offline/"sleep" phase, consolidates experience by **compressing it in a structure-preserving, detail-discarding way**:

- KEEPS relational/structural info: object dependency graphs ("cup on coaster, move cup first"), schemas, causal rules, co-occurrence structure, procedural skeletons.
- DISCARDS episodic detail: specific attribute values (colors, exact positions), one-off specifics that don't generalize.
- Ideally via a **downscaling / renormalization / abstraction** process analogous to synaptic homeostasis (SHY) — prune + renormalize, not just strengthen.
- Key property: memory gets **MORE structural and LESS detailed over time** (schema-up, detail-down).
- Motivation: Complementary Learning Systems (schema extraction) + Synaptic Homeostasis (Tononi & Cirelli).

---

## Relevant systems found (by framing)

### A. Offline/"sleep" consolidation that abstracts across episodes

**Auto-Dreamer — Learning Offline Memory Consolidation for Language Agents** (arXiv 2605.20616, 2026). *Closest on the "offline sleep consolidation" axis.*
- Learned (GRPO-trained) offline consolidator; decouples fast per-session write from slow cross-session consolidation. Treats a memory region as read-only, inspects entries + provenance trajectories, synthesizes a **fresh compact replacement set that abstracts across sessions** and supersedes the originals.
- KEEPS: recurring cross-session patterns/procedures. DISCARDS: redundant per-session entries.
- Structure preservation: **incidental**. It keeps provenance links but the objective is generic abstraction + compression, not typed "keep-graph / drop-attributes."
- Benchmark: ScienceWorld (+7 pts, 12× smaller memory), transfers to ALFWorld + WebArena (6× less memory).
- Limitation: abstraction is a learned summarizer; no explicit structural target, no renormalization semantics, no notion of retaining a dependency graph while dropping surface detail.

**SCM — Sleep-Consolidated Memory with Algorithmic Forgetting** (arXiv 2604.20943, 2026). *Closest on the renormalization/downscaling axis.*
- Explicit SHY implementation: NREM Hebbian strengthening of co-occurring concepts, then **proportional synaptic downscaling** (s_ij ← 0.8·s_ij per cycle); REM random-walk "dreaming" to form novel links; importance+decay thresholded forgetting.
- Maintains a **structured semantic graph** with typed relations (has_property, prefers, contradicts…). Preserves schema/structure; prunes **entire low-importance concepts** (node-level).
- Structure preservation: partial. It keeps a graph and renormalizes edge weights, but it does **not** do intra-item structure-vs-detail separation — it doesn't keep a dependency graph while forgetting attribute values of the nodes; it drops whole nodes by importance.
- Benchmark: toy factual-recall suite (10-turn dialogs, 100–360 concepts, NetworkX). No agentic/embodied tasks. Bottlenecks >10k concepts; text-only; no continuous background loop.

**"Learning to Forget" / SleepGate — Sleep-Inspired Consolidation for Proactive Interference** (arXiv 2603.14517, 2026). *(name/ID verify)*
- Operates on the **KV cache at inference**, not weights or a persistent store. Conflict-aware temporal tagger + learned forgetting gate + consolidation module. Consolidates related surviving entries into compact summaries; evicts/downweights **stale** superseded values (e.g., old address after update).
- Structure preservation: narrow — keeps the "slot/schema" a value occupies (via learned semantic signatures) and discards stale values for that slot. This is stale-value eviction, not schema *extraction* from experience.
- Benchmark: synthetic PI-LLM, 793K-param model only. Degrades past ~15 updates. Unclear transfer to production models.

### B. The exact conceptual axis (but a position paper)

**Experience Compression Spectrum — Unifying Memory, Skills, and Rules** (arXiv 2604.15877, 2026). *Names the target axis explicitly.*
- Frames memory → skills → rules as one axis of increasing compression: L0 raw trace, L1 episodic (5–20×), L2 procedural skill (50–500×), L3 declarative rule (1000×+). Higher levels **retain structure (procedural patterns, decision principles) and discard contextual detail (timestamps, names, specific values)** — this is essentially the target property, stated as a taxonomy.
- Key finding: the **"Missing Diagonal"** — across 20+ surveyed systems, **none supports adaptive level selection**; all operate at fixed, predetermined compression levels (10 at L1, 8 at L2, L3 nearly empty). Maintenance (consolidation over time) is "neglected across all systems."
- Status: **conceptual, not empirically validated** (authors' own words). It is a map of the gap, not a system.

### C. Procedural-memory / schema abstraction in the project's domain (ALFWorld/AI2-THOR)

**Mem^p — Exploring Agent Procedural Memory** (arXiv 2508.06433, 2024/2025). ALFWorld + TravelPlanner.
- Distills trajectories into **both** fine-grained step traces **and** script-like abstractions ("Proceduralization"). Build/Retrieve/Update lifecycle; memory refined iteratively.
- Gap: it **keeps both** granularities (does not discard episodic detail); no explicit dependency graph / procedural skeleton; vector-retrieval based; retrieval degrades with memory size. No renormalization / over-time detail-decay.

**Learning Hierarchical Procedural Memory for LLM Agents** (arXiv 2512.18950, 2025/26). ALFWorld; exploration→consolidation→exploitation phases, meta-procedure formation during consolidation. Hierarchical procedure abstraction, but no explicit structure-vs-detail renormalization; keeps procedures, doesn't model object-dependency graphs + attribute forgetting.

**ExpeL — LLM Agents Are Experiential Learners** (arXiv 2308.10144, 2023). ALFWorld/HotpotQA/WebShop/FEVER.
- Extracts discriminative "insights/rules of thumb" from contrasted success/failure trajectories + exemplar pool; ADD/EDIT/UPVOTE/DOWNVOTE importance counts.
- Gap: abstraction to natural-language rules, **no structural/graph target**, no consolidation-time detail-discarding of a relational schema, no downscaling. Insights accumulate; structure is not the object.

### D. Structure-preserving graph memories (build/maintain a graph)

**Graph-based Agent Memory: Taxonomy** (arXiv 2602.05665, 2026) surveys Mem0, Zep, Graphiti, MemTree, A-MEM, HippoRAG.
- These maintain relational graphs, bi-temporal fact validity, hierarchical clustering. The survey mentions the *idea* of "merging multiple similar events into a generalized schema node," but **explicitly concludes no surveyed system implements progressive detail-abstraction while maintaining graph structure** (schema-up/detail-down over time). Graph maintenance ≠ structure-preserving detail-discarding consolidation.

### E. Selective / gist-vs-verbatim forgetting

**FSFM — Biologically-Inspired Selective Forgetting of Agent Memory** (arXiv 2604.20300, 2026). Importance scoring: keep high-value verbatim, aggressively compress/evict low-value.
- Gap: selection axis is **importance/recency**, not **information type**. It doesn't forget detail *while keeping structure*; it forgets whole low-value items.
- Related: ACT-R-inspired agent memory, MemoryBank (Ebbinghaus decay). All decay by importance/time, not by structure-vs-detail.

### F. Parametric (weight-space) analogues

- **Synaptic-Intelligence / hierarchical importance regularization for LoRA** (e.g., arXiv 2501.13669) and **synaptic renormalization** continual-learning frameworks periodically globally weaken weights (LTD-inspired) and protect important params. This is the **SHY renormalization idea in weight space**, but for catastrophic-forgetting mitigation on task sequences — **not** a memory that extracts task schemas/dependency graphs while shedding instance detail. No agentic/episodic-structure semantics. **SPICED** (2509.17439) applies SHY to EEG continual decoding — same story, different domain.
- No LoRA/fine-tuning method found that consolidates *structure* (relational schema of a task space) while forgetting *instance detail*.

---

## What keeps vs discards — at a glance

| System | Year | Keeps | Discards | Structure-preservation | Renormalize? | Benchmark |
|---|---|---|---|---|---|---|
| Auto-Dreamer | 2026 | cross-session patterns/procedures | redundant session entries | incidental | no | ScienceWorld/ALFWorld/WebArena |
| SCM | 2026 | typed semantic graph, co-occurrence | whole low-importance nodes | partial (graph, but node-level prune) | **yes (0.8×)** | toy factual recall |
| SleepGate | 2026 | current slot values (schema slot) | stale superseded values | narrow (slot) | downweight | synthetic PI, 793K model |
| Exp. Compression Spectrum | 2026 | (taxonomy: structure at higher tiers) | (detail at higher tiers) | **explicit — but position paper** | n/a | none (conceptual) |
| Mem^p | 2024/25 | fine + abstract procedures (both) | nothing (keeps both) | no graph | no | ALFWorld/TravelPlanner |
| ExpeL | 2023 | NL insights + exemplars | low-vote insights | no | no | ALFWorld etc. |
| Graph memories (Mem0/Zep/A-MEM…) | 2024–26 | relational graph + temporal validity | outdated/invalid facts | graph maintained, not consolidated toward structure | no | mixed |
| FSFM | 2026 | high-importance items verbatim | low-importance items | no (importance axis) | no | agent memory |

---

## VERDICT

**(b) PARTIAL — the ingredients exist, but the specific structure-vs-detail consolidation mechanism does not exist off-the-shelf.**

Every component of the target has been demonstrated *separately* in 2024–2026 work, but no released system implements a memory that, through offline consolidation, becomes **more structural (dependency graph / schema / procedural skeleton) and less detailed (attribute values / one-off specifics) over time**. The literature's own framework (Experience Compression Spectrum) names exactly this as the **"Missing Diagonal"**: no system does adaptive, over-time movement along the detail→structure axis, and consolidation/maintenance is "neglected across all systems." The graph-memory survey independently confirms no system explicitly abstracts detail while preserving graph structure.

### The gap, precisely
1. **Renormalization exists but is node-level, not type-level.** SCM downscales edge weights and prunes whole concepts by importance — it never keeps a node's relational role while stripping that node's surface attributes. There is no "keep the dependency edge, forget the color" operation.
2. **Abstraction consolidation exists but is untyped summarization.** Auto-Dreamer / ExpeL / Mem^p abstract across episodes, but treat structure and detail as one undifferentiated blob to compress; none has an explicit objective that *targets* relational/procedural structure for retention and episodic detail for deletion.
3. **The exact axis is only a taxonomy, not a mechanism.** Experience Compression Spectrum articulates schema-up/detail-down perfectly but is explicitly conceptual and unvalidated, and reports that no system moves along the diagonal adaptively over time.
4. **No structural target in the project's domain.** For ALFWorld/AI2-THOR, procedural-memory methods (Mem^p, hierarchical procedural memory) keep procedures but don't model object-dependency graphs, and they retain detail rather than shedding it via a homeostatic downscaling process.

### 3 closest existing systems and how they fall short
1. **SCM (Sleep-Consolidated Memory, 2604.20943)** — has the SHY renormalization + typed graph, but forgetting is node-importance-based (drops whole concepts), not detail-vs-structure separation; validated only on toy factual recall, no agent tasks.
2. **Auto-Dreamer (2605.20616)** — has the learned offline "sleep" consolidator that abstracts across sessions on ALFWorld/ScienceWorld/WebArena, but abstraction is generic compression with no explicit structure-preserving/detail-discarding objective and no renormalization.
3. **Experience Compression Spectrum (2604.15877)** — states the target property exactly (structure retained, detail discarded up the compression ladder) and proves the gap ("Missing Diagonal"), but is a position/survey paper with no implemented system.

### Implication for the project
The specific mechanism — a sleep-phase consolidator that explicitly retains object-dependency graphs / schemas / procedural skeletons while renormalizing away episodic attribute detail, driving the memory to get more structural and less detailed over time — is **genuinely open and unclaimed**. It sits precisely on the "Missing Diagonal" the field has named but not built. This is a defensible, novel research direction; the closest prior art (SCM, Auto-Dreamer) can be cited as partial ingredients rather than as a system that already does it.

Caveat: several 2026 arXiv IDs above are recent; the SleepGate name/ID for 2603.14517 in particular should be double-checked against the canonical title before citing. The landscape conclusion is robust across many independent sources regardless of any single ID.
