# Literature Synthesis & Positioning — July 2026

Source notes: `01_wake_sleep_consolidation.md`, `02_parametric_memory.md`, `03_agent_memory_benchmarks.md`.
Caveat: several 2026 arXiv IDs were retrieved via web search — verify each against arXiv before citing.

---

## The one-paragraph positioning

As of July 2026, sleep-style consolidation for LLMs exists (weight-space, QA-only), LoRA-as-memory exists (online, no sleep phase, no learned write policy), masked parameter regions as memory exist (factual edits and task-level CL, not agent experience), and selective replay reliably beats random — but **every existing selector/write-rule is a fixed heuristic**, **no system consolidates embodied agent experience through a learned policy**, and **no benchmark separates structural retention from detail forgetting**. A 24-author position paper (Modular Memory, arXiv:2603.01761) explicitly names the learned when/what-to-consolidate policy as an open problem. That intersection — learned consolidation policy × embodied agent × structural-retention benchmark — is unoccupied.

---

## Threats (closest prior art, cite and differentiate)

| Paper | What it does | Why we're different |
|---|---|---|
| **TMEM** (2606.04536, Alibaba, Jun 2026) | Online LoRA fast-weight memory for agents, beats RAG on LoCoMo | No sleep phase, no learned write policy, no embodied eval. **Biggest threat — window is narrowing.** |
| **"Language Models Need Sleep"** (2605.26099/2606.03979) | NREM/REM consolidation into fast weights, +52% synthetic reasoning | QA/math only, never agentic; 3.6–4.8× compute cost; fixed consolidation rule |
| **PEAM** (2605.27762) | Minecraft parametric consolidation, "parameterization-worthiness score" → MoE-LoRA | Score is heuristic, not learned; no structural retention measurement |
| **MEMOIR** (2506.07899, NeurIPS 2025) | Masked residual param module + sparse per-item masks | Factual edits, not agent experience/skills |
| **SuRe** (2511.22367) | Surprise-based selective replay beats reservoir | Fixed heuristic selector — our learned policy is the direct upgrade claim |

## Ammunition (motivating citations)

- **"Useful Memories Become Faulty..."** (2605.12978): LLM-driven consolidation makes memory utility rise then fall *below no-memory baseline*; 54% of previously-solved problems failed. Documents the failure we fix; proposes no fix.
- **"Consolidation collapse"** is now a named, unsolved failure mode across multiple 2026 papers.
- **Abstraction beats raw replay on ALFWorld** (2604.27003): raw trajectories −9.5% transfer, abstracted insights +6.5%. Direct support for "keep structure, drop detail."
- **Modular Memory position paper** (2603.01761, 24 authors): names learned consolidation policy as open problem.
- **ICLR 2026 MemAgents workshop** lists Hopfield associative layers for agent memory as an open direction — no system paper exists.

## Open lanes (ranked by claimability)

1. **Benchmark: structural retention vs. detail forgetting.** No benchmark separates these. Closest (TextCraft) has no world persistence; persistent Minecraft benchmarks are heavyweight/visual. Our lightweight text crafting sim with persistent resource locations fills a real hole. *Highest confidence, lowest risk.*
2. **Learned consolidation routing policy for agent experience.** All existing selectors are heuristics (surprise, info-theoretic, worthiness scores). A policy learned against retention outcomes is a clean novelty claim. *Core method contribution.*
3. **Masked weight region as experience memory.** Exists for facts (MEMOIR) and tasks (MoSEs) — not for embodied agent skills written by an offline consolidation policy. *Most novel, most risky.*
4. **Hopfield ↔ agent memory bridge.** Theory mature, system unbuilt. *Stretch goal / future work section.*

## Recommended paper shape (from earlier discussion)

Analysis + benchmark hybrid:
1. Introduce the benchmark (persistent-world crafting sim, ground-truth dependency graphs, structural-vs-detail metrics)
2. Run existing memory families through it: long-context, RAG, naive LoRA fine-tune, TMEM-style online LoRA, sleep-style consolidation
3. Characterize the gap (hypothesis: retrieval keeps detail but not structure; fine-tuning keeps structure but collapses)
4. Position the learned consolidation policy as the fix; measure resistance to consolidation collapse

## Verification TODO before citing

- [ ] Confirm each 2026 arXiv ID resolves to the described paper
- [ ] Check TMEM for any embodied follow-up
- [ ] Check whether "Language Models Need Sleep" ID is 2605.26099 or 2606.03979 (agents disagreed)
- [ ] Read PEAM in full — closest methodological neighbor
