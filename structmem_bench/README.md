# StructMem-Bench

A benchmark for **structure-vs-detail retention in consolidated agent memory**.

Parametric-memory methods are measured on recall/QA accuracy — none report *what
kind* of knowledge survives consolidation. StructMem-Bench provides tasks with a
**ground-truth dependency graph**, so **structural retention** (dependency edges /
relations) and **detail retention** (episodic specifics) can be scored *separately
and programmatically* — no LLM judge. It lets you referee the crowded
parametric-memory field on an axis none of the methods report.

## What it measures
- **structural retention** ↑ — are the causal dependency edges recoverable from memory?
- **detail retention** ↓ — are episodic details (correctly) shed?
- **relational retention** ↑ — are the true *dependency pairs* preserved (the axis
  per-item methods miss)?
- all at a **fixed memory budget**, swept over **#episodes** (scaling) and **budget**.

## Design invariants (each guards a specific self-deception, learned the hard way)
- **Frequency is uninformative on matched facts.** Structural-frequent (SF) and
  recurring-detail (DR) share identical appearance marginals → frequency cannot
  separate them (verified: dP ≈ 0). Frequency's *failure* is on the hard cases
  (drops rare-critical structure, keeps recurring-useless detail), which is the point.
- **Continuous overlapping value**, swept by discriminability `value_dprime` — no
  degenerate label-threshold oracle.
- **Collinear confounds** (`confound_a`): recurring details correlate with a
  structural partner but share its marginal, so naive co-occurrence can't separate
  them — only a joint/relational fit can.
- **Rigor layer:** measured noise floor, a random-sampler canary AND a
  label-permutation canary (both must sit at chance), and **paired** per-seed tests.
- **Methods never see the labels** — only (presence, value samples, outcomes).

## Two tiers
1. **Abstract (CPU, seconds):** set-retention + a trained value/logreg model. The
   reproducible core (this package). No LLM.
2. **LLM-in-the-loop (GPU/API):** a real small model as the agent over the crafting
   sim; a few memory conditions. See `structmem_bench/llm_tier.py` (scaffold).

## Quickstart
```bash
cd /path/to/dream-state
PYTHONPATH=. python3 run_benchmark.py          # headline table + rigor checks
PYTHONPATH=. python3 tests/test_structmem.py   # 14 invariant tests
```

## Methods included
`random` (null) · `truncation` (recency) · `frequency` · `surprise` (ATLAS-style
proxy) · `value_max` / `value_mean` (per-item) · `trained_value` (outcome-trained
per-item) · `relational` (learned per-pair, ours) · `item_lifted` (per-item→pair
baseline) · `oracle` (ceiling).

## Status & honesty
v0.1, abstract tier. Adversarially red-teamed (see `research_notes/redteam_*.md`).
Known limitation under active fix: relational-pair enumeration does not scale with
the fact universe — which is itself a finding (it motivates *learned* relational
keys over explicit enumeration). This is an abstract-tier necessary-condition
instrument, not a claim that any full memory *system* works; that is the LLM tier.

## Layout
```
structmem_bench/
  config.py    BenchConfig — one struct fully specifies an instance
  tasks.py     ground-truth-labelled stream generation
  memory.py    methods under test (per-fact + relational)
  metrics.py   AP / d' / retention / diagonal (programmatic, vs ground truth)
  stats.py     noise floor, canaries, paired tests
  harness.py   run methods across seeds; canary + sanity checks
  llm_tier.py  GPU/LLM-in-the-loop scaffold (M3)
run_benchmark.py, tests/test_structmem.py, BENCHMARK_SPEC.md
```
