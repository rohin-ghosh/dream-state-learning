# Felt Attention *(working title)*

Research project: **value-weighted memory for continual LLM agents** — a single
attention head, trained on a *value* signal instead of token loss, that allocates
what an agent keeps in context, writes to long-term memory, and consolidates into
weights. Plus the instrument to measure it: a **psychology-grounded,
memory-type-agnostic retention benchmark** (working name pending; formerly
"StructMem-Bench", to be renamed — name collision with arXiv:2602.11243).

**Start here:**
- [`PAPER_SHEET.md`](PAPER_SHEET.md) — the complete, testable state of the work:
  every claim with an evidence status, real numbers, and declared gaps.
- [`research_notes/JOURNAL.md`](research_notes/JOURNAL.md) — full decision history.
- [`research_notes/INDEX.md`](research_notes/INDEX.md) — 20+ literature surveys and
  red-team reports.

## The two deliverables

1. **The benchmark (Paper 1, in progress).** Measures whether a memory keeps
   relational structure ("gist") and sheds episodic detail ("verbatim") as
   experience outgrows a fixed budget — scored programmatically against
   ground-truth dependency graphs, through one probe interface that works for RAG,
   parametric/LoRA, and text-bank memories. Abstract (CPU) tier: built, 26+ tests (see tests/),
   adversarially red-teamed and externally audited. LLM tier: scaffolded, needs GPU.

2. **Felt Attention (Paper 2, designed).** Value net trained on task outcomes →
   one value-loss attention head on a frozen LLM → head weights allocate context,
   fast-weight memory writes, and LoRA consolidation. End-to-end miniature proven
   on CPU (`experiments/exp4_end_to_end.py`).

## Reproduce (CPU, minutes)

```bash
PYTHONPATH=. python3 run_benchmark.py            # benchmark + rigor checks
PYTHONPATH=. python3 tests/test_structmem.py     # 27 invariant tests
PYTHONPATH=. python3 experiments/exp4_end_to_end.py  # end-to-end miniature
```

## Layout

```
structmem_bench/    the benchmark package (see its README)
experiments/        exp0–exp4 + reports (reversals preserved with banners)
research_notes/     literature surveys, red-team reports, JOURNAL, INDEX
tests/              27 invariant tests
PAPER_SHEET.md      claim-by-claim evidence state (for reviewers)
BENCHMARK_SPEC.md   benchmark design spec
DESIGN_DOC.md       historical design doc (superseded; banner inside)
archive/            the original wake-sleep agent system (superseded; see its README)
```

## Provenance

This project began as "Dream-State Learning" (a wake-sleep consolidation agent —
now in `archive/`) and was reshaped by ~10 adversarial literature searches, two
red-team rounds, and an external execution audit. Every retraction and reversal is
preserved in-repo rather than deleted. The journal is the honest record.
