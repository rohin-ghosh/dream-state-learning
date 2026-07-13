# 11 — Baselines, Benchmarks & Eval Fragility (for Paper B / POC)

Scope: cluster on agent-memory systems, reflective/self-improving agents, benchmarks, and
classical continual-learning (CL) baselines. Goal = arm Paper B (attention-weighted sleep
consolidation into a small parametric memory; structure-up/detail-down; evaluated on a text
crafting-sim with ground-truth dependency graphs at a FIXED memory budget) with the right
baseline set, benchmark decisions, and eval-fragility guardrails.

NOTE: MemGPT, Generative Agents, ExpeL, Reflexion, Voyager, EvoMemBench, WorldLines were
covered by the prior survey — NOT repeated here except where a role changes. This file ADDS
depth on baselines + eval fragility.

Roles: {BASELINE-TO-BEAT / EVAL-LESSON / ABSTRACTION-PRIOR-ART / CONTEXTUAL}

---

## CRITICAL DELIVERABLE 1 — Recommended BASELINE SET for B's comparison table

All arms must be run at a **matched memory budget** (tokens for context/RAG arms; parameter
count / adapter rank for parametric arms; entry count for structured arms). Report task
success at fixed budget AND a budget-sweep curve, plus the structural-vs-detail retention split.

| # | Arm | Concrete instantiation | What it isolates |
|---|-----|------------------------|------------------|
| 0 | **No-memory lower bound + Oracle upper bound** | base agent w/ no persistent memory; and an oracle given the ground-truth dependency graph | frames the achievable band |
| 1 | **Filled short-context (recency)** | concatenate most-recent raw trajectories up to the token budget, truncate oldest | shows raw context ≠ good memory; the "just stuff the window" strawman reviewers demand |
| 2 | **RAG over trajectories** | dense-embed trajectory snippets, retrieve top-k to fill budget (vanilla) + a strong variant = **Mem0** (extract/consolidate salient facts, ECAI'25) | tests whether learned *consolidation* beats retrieve-raw-details; Mem0 is the current production-grade RAG-memory bar |
| 3 | **Parametric / LoRA memory** | fine-tune a small LoRA adapter on the trajectory stream, rank chosen to match B's memory param budget; optional stronger form = **Remembering Transformer** (mixture-of-adapters + novelty routing) | isolates "parametric memory" without B's attention-weighted structure-up bias; Remembering Transformer is the routing-aware version closest to B |
| 4 | **Reflective-abstraction agent** | **CLIN** (causal-abstraction textual memory, no weight updates) as primary; **AWM** (workflow induction) as secondary | the "turn experience into reusable abstractions" bar — same env family (ScienceWorld/craft), targets structure directly |
| 5 | **Classical-CL method** | **A-GEM** (gradient-projection replay) or **EWC** (Fisher-anchored) over the parametric arm; **Experience Replay/CLEAR** as the replay reference | the CL-literature anchor; shows B is not just re-deriving EWC/replay |
| 6 | **Learned-consolidation SOTA (baseline-to-beat)** | **Auto-Dreamer** (learned offline consolidator, GRPO, CLS-inspired) | nearest neighbor to B's thesis; if B can't beat or match this at equal budget, the contribution is weak |

Minimum viable table = arms **1, 2(Mem0), 3(LoRA), 4(CLIN), 5(A-GEM)** + the 0 band, i.e. the
requested 5 spanning filled-context / RAG / parametric / reflective-abstraction / classical-CL.
**Strongly add arm 6 (Auto-Dreamer)** — it is the direct prior art and the real bar.

Budget-matching caveat: Auto-Dreamer and Mem0 both report *X-times-smaller* active banks — so
"fixed budget" must be defined as **active memory consumed at inference**, not total stored, or
those systems will look artificially penalized/favored. Fix the definition before running.

---

## CRITICAL DELIVERABLE 2 — Top-3 eval-fragility warnings to design around

From **"Anatomy of Agentic Memory" (2602.19320)** and **LifelongAgentBench (2505.11942)**:

1. **Judge/metric misalignment — don't score verbatim recall as if it were reasoning.**
   Anatomy shows current memory benchmarks reward verbatim recall over reasoning quality and
   that LLM-as-judge outcomes swing with the judge model (judge sensitivity). *Design around it:*
   B's crafting-sim already has a ground-truth dependency graph — score **task success + graph
   correctness programmatically**, not with an LLM judge. If any LLM-judge metric is used,
   report results under ≥2 judge backbones and show agreement.

2. **Backbone dependence — a memory win on one base model may vanish on another.**
   Anatomy: memory-system effectiveness varies significantly across backbone LLMs. *Design around
   it:* run B's full table on **≥2 backbones** (e.g., one small, one strong) and report per-backbone
   deltas; claim gains only where they persist. Otherwise reviewers read your win as backbone luck.

3. **Benchmark saturation / underscaling + naive replay is a false floor.**
   Anatomy: benchmarks are underscaled and saturate (ceiling effects hide differences).
   LifelongAgentBench: **conventional experience replay has limited effectiveness for LLM agents**
   because irrelevant retrieved info and context-length limits swamp the signal — so a weak replay
   baseline flatters any method. *Design around it:* (a) scale the crafting-sim so top methods are
   NOT at ceiling (deep dependency chains, held-out recombinations); (b) make replay a *tuned*,
   not strawman, baseline; (c) report **cost/latency per task** (Anatomy's overlooked axis) so B's
   "small parametric memory" wins on efficiency, not just accuracy.

Bonus guardrail (both papers + AgentCL 2606.02461, "Toward Rigorous Evaluation of CL in Language
Agents"): **fix task ORDER and report order-sensitivity** — CL results flip with curriculum order;
average over ≥3 shuffles.

---

## CRITICAL DELIVERABLE 3 — Can an existing benchmark substitute for / complement the crafting-sim?

**Substitute: No.** No existing benchmark gives you B's core instrument — a *ground-truth
dependency graph* enabling the **structural-vs-detail retention split** at a controlled memory
budget. LoCoMo / LongMemEval (used by Mem0, MAGMA) are conversational-recall, not dependency-
structured tasks; they measure the wrong thing for structure-up/detail-down.

**Complement: Yes, adopt as external-validity arms.**
- **LifelongAgentBench (2505.11942)** — skill-grounded *interdependent* tasks over DB/OS/KG with
  automatic label verification. Closest in spirit (interdependency + auto-verification); use it to
  show B generalizes beyond a bespoke sim, and to borrow its group-self-consistency and
  reproducibility protocol.
- **ScienceWorld / ALFWorld** — the env family CLIN and Auto-Dreamer both use; running B here makes
  B directly comparable to those baselines-to-beat with no new harness.
- **Cross-scenario diagnostic (2606.04315, "Exploring Cross-Scenario Generality… a Strong
  Baseline")** — provides a strong general baseline + generality diagnostics; useful as an
  additional "is this just overfit to one env" check.

Recommendation: **keep the crafting-sim as the primary instrument** (it uniquely enables the
structure/detail claim), and add **ScienceWorld/ALFWorld + a LifelongAgentBench slice** as
secondary generalization evidence to defuse the "bespoke-benchmark" reviewer objection.

---

## TOP-5 RANKED SHORTLIST (by usefulness to B)

1. **Auto-Dreamer (2605.20616)** — *Learned offline memory consolidation for language agents.*
   ROLE: **BASELINE-TO-BEAT + ABSTRACTION-PRIOR-ART.** Decouples fast online acquisition from slow
   cross-session consolidation; GRPO-trained consolidator rewrites a memory region into a compact
   abstracted set; CLS-inspired; beats fixed/RL/prompted memory on ScienceWorld by 7 pts with a
   12× smaller active bank, transfers to ALFWorld/WebArena. This is B's thesis nearly verbatim —
   MUST cite, MUST compare against, and its fixed-budget-vs-bank-size protocol is a ready-made eval
   template. If B differs, the difference must be crisp (attention-weighted structure-up bias +
   dependency-graph-grounded eval).

2. **Anatomy of Agentic Memory (2602.19320)** — *Taxonomy + empirical analysis of eval/system
   limits.* ROLE: **EVAL-LESSON (primary).** Source of the judge-sensitivity, backbone-dependence,
   saturation, and cost-overhead warnings above. Cite as the methodological backbone of B's eval.

3. **CLIN (2310.10134)** — *Continually learning agent with causal-abstraction textual memory,
   no weight updates.* ROLE: **ABSTRACTION-PRIOR-ART + BASELINE-TO-BEAT.** Same env family; memory
   centered on *causal abstractions* (structure) rather than raw hints — the non-parametric
   structure baseline. As a table arm it = "textual reflective structure without a parametric
   budget."

4. **LifelongAgentBench (2505.11942)** — *Benchmark for lifelong learning of LLM agents.*
   ROLE: **EVAL-LESSON + complementary benchmark.** Key finding (replay fails for agents; context
   length + irrelevant info) directly shapes B's baseline tuning; interdependent-task design is the
   closest external benchmark to the crafting-sim.

5. **Agent Workflow Memory / AWM (2409.07429, ICML'25)** — *Induce reusable workflows from
   trajectories.* ROLE: **ABSTRACTION-PRIOR-ART.** "Structure-up" via workflow induction (abstracted
   action templates); online+offline modes; the procedural-abstraction point of comparison and a
   secondary reflective baseline. Note it targets web nav (Mind2Web/WebArena), so it's prior-art
   framing more than a same-env baseline.

---

## Remaining cluster papers (condensed)

- **Mem0 (2504.19413, ECAI'25)** — scalable extract/consolidate/retrieve memory; graph variant.
  ROLE: **BASELINE-TO-BEAT (RAG arm).** Current production-grade RAG-memory bar; first broad
  10-system head-to-head on LoCoMo. Use as the *strong* RAG baseline (not vanilla dense retrieval).
- **Meta-Policy Reflexion / MPR (2509.03990)** — consolidate reflections into predicate-like
  Meta-Policy Memory + hard rule-admissibility; no weight updates; tested on ALFWorld.
  ROLE: **ABSTRACTION-PRIOR-ART.** Reusable *cross-task* reflective structure (vs Reflexion's
  ephemeral traces) — closest reflective-agent to B in the ALFWorld setting; good secondary
  reflective baseline / related work.
- **A Control Architecture for Training-Free Memory Use (2604.18206)** — separates memory *content*
  from memory-*use policy*; uncertainty routing + selective acceptance + bank governance under a
  locked compute-matched protocol. ROLE: **EVAL-LESSON + CONTEXTUAL.** Its "locked, compute-matched
  protocol" and content/policy split are a model for how to run B's ablations fairly. B's "learned
  routing policy" overlaps its routing — cite to position B as the *learned* (vs uncertainty-
  heuristic) counterpart.
- **MUSE-Autoskill (2605.27366)** — skill lifecycle (create/store/manage/eval/refine) with
  skill-level memory; self-created skills beat human-authored. ROLE: **ABSTRACTION-PRIOR-ART.**
  Turning experience into reusable *skills*; related work for the abstraction claim, not a direct
  baseline (SkillsBench env).
- **MAGMA (2601.03236, ACL'26)** — multi-graph (semantic/temporal/causal/entity) memory, retrieval
  = policy-guided traversal. ROLE: **CONTEXTUAL / structured-memory prior art.** Relevant to
  structure-up; retrieval-as-policy echoes B's routing. Not a same-env baseline (LoCoMo/LongMemEval).
- **Rosetta Memory / RoMem (2606.07711)** — profile-conditioned interface to write transferable
  evidence, read target-aware; cross-LLM memory transfer. ROLE: **CONTEXTUAL.** Relevant only to the
  backbone-dependence warning (memory written under one backbone consumed by another) — supports
  running B across backbones. Not a baseline.
- **Graph-based Agentic Memory: Taxonomy, Techniques, Applications (2602.05665)** — survey of
  extraction/storage/retrieval/evolution. ROLE: **CONTEXTUAL.** Related-work map for structural
  memory; positions B's dependency-graph grounding within the graph-memory line.

### Classical continual-learning baseline menu (for the parametric arm)
- **EWC (2017)** — Fisher-weighted quadratic anchor on important weights. BASELINE: regularization-
  based CL; "anchor old-task params" reference.
- **Synaptic Intelligence (2017)** — online path-integral per-synapse importance. BASELINE: online
  EWC variant; cheaper regularizer.
- **Learning Without Forgetting (2016)** — distill old-task outputs while learning new. BASELINE:
  distillation-based, replay-free CL.
- **GEM (2017) / A-GEM (2018)** — constrain gradients so loss on an episodic buffer can't increase
  (A-GEM = averaged, cheaper). **BASELINE (recommended)** for the CL arm — memory-buffer method
  that pairs naturally with B's replay/consolidation framing.
- **Experience Replay for CL / CLEAR (2018)** — replay buffer + behavioral cloning. BASELINE:
  the replay reference; note LifelongAgentBench's warning that naive replay underperforms for
  LLM agents — tune it or it's a strawman.
- **Progressive Neural Networks (2016)** — add a column per task + lateral connections; zero
  forgetting but params grow. ROLE: CONTEXTUAL upper-bound-on-capacity; violates B's FIXED-budget
  premise, so cite as "what you'd do without a budget" contrast, not a matched arm.
- **Remembering Transformer (2404.07518)** — mixture-of-adapters + generative novelty routing,
  CLS-inspired. ROLE: **BASELINE-TO-BEAT (parametric+routing arm).** The parametric baseline most
  similar to B (learned routing + adapters); strongest CL-side comparison for B's routing policy.

---

## One-line takeaways
- The single most important add is **Auto-Dreamer** — same idea, same envs, budget-vs-bank-size
  protocol; treat as the bar, not just related work.
- Score with the **ground-truth graph programmatically**, run **≥2 backbones** and **≥3 task
  orders**, tune the **replay** baseline, and report **cost/latency** — this defuses the three
  Anatomy/LifelongAgentBench fragility failure modes.
- Keep the crafting-sim as primary (only source of the structure/detail split); add
  **ScienceWorld/ALFWorld + a LifelongAgentBench slice** for external validity and direct CLIN/
  Auto-Dreamer comparability.
