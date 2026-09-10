---
name: user-profile-rohin
description: "Rohin Ghosh's background, skills, and working style preferences"
metadata: 
  node_type: memory
  type: user
  originSessionId: d66e193e-e075-475c-96de-a582e32ee6c5
---

Rohin Ghosh (rohing@nvidia.com). B.S. Applied & Computational Math, UC Irvine (expected 2028). Currently NVIDIA SWE intern (June 2026–present).

**Core technical strengths:**
- GPU systems: CUDA, CUPTI, Nsight, NVLink, cuBLASLt, CUTLASS, CUDA Graphs
- Agent infrastructure: Kubernetes, vLLM, async queues, durable state, Ray
- ML/systems: PyTorch, PEFT/LoRA, Transformers, HuggingFace, continual learning
- Quantitative finance: market microstructure, rough volatility, order books, Monte Carlo
- Languages: Python, C++20, CUDA C/C++, Go, SQL

**Working style:**
- Prefers to manage research direction; wants Claude to execute end-to-end with minimal check-ins
- Comfortable with orchestrated subagents and long autonomous runs
- Wants to be asked when genuinely blocked, not for routine decisions
- Strong enough technically to evaluate outputs critically — don't oversimplify explanations

**Competitions/honors:** USACO Gold Division, Google Coding Competitions Farewell 2023 Top 10%

**Note:** Rohin's writing is often casual/abbreviated in chat (typos, shorthand) — this is style, not a signal of confusion.

## RL background (added 2026-08-11)
Rohin's RL knowledge is LLM-post-training-centric (RLHF/RLVR/GRPO for math/code); he has not worked with classic agent-environment RL. When classic-RL concepts arise (replay buffers, off-policy vs on-policy, TD learning, value functions, PER), explain them from first principles and explicitly bridge to the post-training corner he knows. He learns fast from precise first-principles explanations that leverage his math background.

## Output format preference (correction, 2026-08-15)
Rohin skims; long flowing prose across multiple messages goes UNREAD ("I
didn't read your past outputs because they weren't all that organized").
Deliver research findings and status as organized, scannable digests:
clear headers, tight bullets, bold verdicts, one idea per line. Reserve
flowing prose for single focused explanations he explicitly asks for.

## Document structure preference
Rohin prefers ONE document per artifact with layered altitudes — important
high-level info at the top, in-depth/low-level detail in lower sections —
rather than splitting an overview doc and a companion deep-dive doc. When I
split SPEC_V2 and SIZING_V2 into two files he asked for them merged ("should
this really be in two documents? i think it should be one"). Same spirit as
his scannable-digest preference: he skims top-down, so structure documents
so skimming the top gives the whole picture and depth is available below.

## Communication: unpack jargon (2026-08-21)
Rohin said my explanations sometimes lean on jargon, acronyms, and coined
shorthand without unpacking them — he isn't always reading the docs where
terms were defined. Standing preference: in messages to him, spell out
terms on first use, prefer plain phrasing over acronym-dense writing, and
don't assume vocabulary from earlier artifacts is remembered.

## Division of labor: Rohin writes the paper prose himself (2026-08-21)
He decided the paper must be written by him, not AI — both because
reviewers/mentors will probe his understanding in conversation and
because he needs to have reasoned through what he defends. My role:
data, figures, tables, citations, checking, and drafts of *supporting*
material only when asked. Same spirit: he wants to be closer to
low-level experiment design (my experiment-design intuitions have missed
scale marks, e.g., proposing setups that fit in a context window); big
design moves get co-designed, and I should surface scale sanity-checks
explicitly rather than assume my defaults are right.

## Pacing calibration (2026-08-24)
When advisors or I scope timelines by conventional research pace, Rohin
corrects it: with agentic tooling his project moves much faster (e.g.,
"V3 first run in 3 days" where conventional advice said >25). Don't
recommend deferring milestones based on standard-pace assumptions;
scope plans to his demonstrated build speed and let measured blockers,
not calendar conservatism, drive scope decisions.
