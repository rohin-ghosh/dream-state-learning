# Retention Benchmark — spec (working name; rename pending)

> ⚠️ **Spec v0.2 banner (2026-08-11) — supersedes v0.1 framing below where they
> conflict.** Three updates: (1) **RENAME pending** — "StructMem-Bench" collides
> with StructMemEval (arXiv:2602.11243). (2) The 2604.15877 "Missing Diagonal"
> citation is **retracted as a benchmark-gap claim** (it names a *systems* gap);
> the current gap analysis is research_notes/19 — the virgin-gap framing is unsafe
> post-July-2026 (ForgetBench 2607.26455, RECON 2607.16716, MemTrace 2606.17328
> each cover a fragment). (3) **Positioning upgraded** (notes 19–20): *the first
> psychology-grounded, memory-type-agnostic retention benchmark* — probes as ports
> of validated human-memory paradigms (**gist/verbatim from fuzzy-trace theory =
> the unported headline**; forgetting curves / interference / serial position as
> cited anchors), **one probe interface across RAG + parametric/LoRA + text-bank
> memories** (verified open — the two literatures never compare), importance-
> stratified retention (open), **enforced** budget (BEAM only reports), adopting
> script-before-text generation (2607.21962). Differentiate vs eMEM-Bench
> (2606.03374): general text-agent vs embodied-only; backend-agnostic vs
> system-coupled.

**Status:** spec v0.1 body below (built: abstract tier, 23 tests, red-teamed +
audited). Builds on exp0–exp4.

## One-line pitch (v0.2)
Memory methods are measured on recall accuracy — none report **what kind of
knowledge survives**: relational structure ("gist") vs episodic detail
("verbatim"). We provide ground-truth dependency graphs and paradigm-ported
probes so gist and verbatim retention are scored separately, programmatically,
at an enforced budget — through one interface that works for RAG, parametric,
and text-bank memories alike.

## Why it's defensible in a crowded field (v0.2 per note 19)
- **Open axes:** cross-memory-type single probe interface; importance-stratified
  retention; gist/verbatim + spacing as unported paradigms; enforced budget.
- **The conjunction** (graph-grounded split + budget + age curves, across all
  memory types) exists nowhere; fragments cited generously.
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
