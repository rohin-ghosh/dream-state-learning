# StructMem-Bench — a benchmark for structure-vs-detail retention in consolidated memory

**Status:** spec v0.1 (M1). The artifact to ship for lab entry. Builds on exp0–exp3.

## One-line pitch
Existing agent-memory methods are measured on *recall/QA accuracy* — none measure
whether **relational structure survives consolidation** while episodic detail is
shed. StructMem-Bench provides a persistent world with a **ground-truth dependency
graph**, so structural-retention and detail-retention can be scored *separately and
programmatically* — the "Missing Diagonal" (Experience Compression Spectrum,
2604.15877) made measurable. It lets you referee the crowded parametric-memory field
(COVE, TMEM, PEAM, D-MEM, EVAF) on an axis none of them report.

## Why it's defensible in a crowded field
- **Unowned:** no benchmark separates relational-structure retention from
  episodic-detail retention (confirmed across notes 03/06/09/17/18).
- **Scoop-immune:** a benchmark *gains* value as the method-paper field grows.
- **Home for our one real novelty:** relational value (exp3) is the natural headline
  result on it.

## Task substrate
Persistent-world crafting sim (`dream_state/environments/minecraft_sim.py`, already
built + verified). Each world has a fixed crafting DAG + resource locations. An
episode = a goal ("craft X") in a persistent world.

Every episode decomposes into ground-truth-labelled facts:
- **Structural facts** — dependency edges ("wood→planks", "need pickaxe before ore",
  resource-location bindings). Must be RETAINED.
- **Detail facts** — incidental attributes (world instance, exact counts, surface
  descriptors, recurring-but-useless distractors). Should be SHED.
Hard cases (from exp1/2.5/3): rare-but-critical structure, recurring-but-useless
detail, and relational (pair/dependency) value that per-item methods miss.

## Metrics (scored programmatically vs the ground-truth graph — no LLM judge)
- **Structural retention** (↑): fraction of true dependency edges recoverable from
  memory.
- **Detail retention** (↓ desirable): fraction of episodic details retained.
- **Diagonal** = structural − detail retention (the headline axis).
- **Relational retention** (↑): fraction of true *relations/pairs* preserved
  (per-dependency, the exp3 axis competitors miss).
- All at **fixed memory budget**, swept over **#episodes** (scaling) and **budget**.

## Protocol (the rigor that makes it trustworthy — from exp0/exp1-corrected)
- Measured **noise floor** + a **real null canary** (must collapse to chance).
- ≥20 seeds; **paired** per-seed tests for method comparisons.
- **Budget sweep** (report budget-free ranking metric: Average Precision) so results
  aren't a fill artifact.
- **Scale sweep** (does any method's structural advantage grow or hold as episodes
  exceed budget — the bitter-lesson axis).
- ≥3 curriculum orderings, averaged.

## Two evaluation tiers
1. **Abstract (CPU, seconds):** set-retention + logistic-value model — already built
   across exp0–exp3. Fast inner loop, no LLM. This is the reproducible core.
2. **LLM-in-the-loop (modest GPU/API):** a real small model as the agent, a few
   memory conditions, to show the benchmark transfers off the abstraction.

## Methods evaluated (the "referee the crowd")
no-memory floor · full-context @budget · RAG · frequency · surprise (ATLAS-style) ·
value (per-item) · **relational-value (ours, headline)** · graph-oracle ceiling.
Stretch: reimplement/approximate 1–2 published methods (COVE anti-recitation,
D-MEM-style routing) if time permits — otherwise cite and position.

## Deliverable milestones
- **M1 (this doc):** spec. ✅
- **M2 (CPU, days):** clean reusable package — generator + harness + metrics +
  cheap baselines with paired stats. ~80% exists in exp0–exp3; consolidate.
- **M3 (modest):** one LLM-in-the-loop demonstration.
- **M4:** workshop-length write-up. Framing: the benchmark + the gap it exposes +
  relational-value as the result. Cite COVE/TMEM/PEAM/D-MEM/EVAF as the field it
  measures.

## Positioning sentence for the paper/outreach
"Parametric memory is advancing fast, but the field measures recall, not *what kind*
of knowledge survives consolidation. We introduce a benchmark with ground-truth
relational structure that separates structural from episodic retention, show that
current methods preserve detail while losing structure, and that relational-value
consolidation closes the gap."
