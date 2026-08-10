# archive/ — the original Dream-State system (superseded)

This is the first-phase codebase: a full wake-sleep continual-learning agent
(ReAct + LoRA consolidation + routing policy + ALFWorld harness). It was the
scaffold that the research *reasoned its way out of* — the literature review and
the exp0–exp3 experiments showed the parametric-memory space was crowded and the
defensible contribution was the **measurement instrument**, not this system.

**Nothing in the shipping artifact imports this.** It is kept for provenance only.
It is NOT experiment-ready (an external audit flagged CLI↔harness interface gaps,
missing ALFWorld config, sleep/LoRA-min mismatch, checkpoint-gate and adapter-reload
bugs) — do not allocate GPU to it without those fixes. The live artifact is
`structmem_bench/` at the repo root.

See `research_notes/JOURNAL.md` for the full story of why this was set aside.
