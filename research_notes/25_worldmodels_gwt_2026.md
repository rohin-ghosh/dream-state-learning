# Note 25 — World-model & GWT landscape, Aug 2026 (agent-verified sweep)

Triggered by Rohin's amodal-central-model musing (2026-08-11, night of lease 1).
Sources verified by a web-research agent against primary pages; arXiv IDs listed.
**Caveat: re-verify all 2026 IDs at write-up (standing rule).**

## 1. LeCun / world-model program
- JEPA line: I-JEPA (2301.08243) → V-JEPA → V-JEPA 2 (2506.09985, action-conditioned,
  zero-shot Franka manipulation) → LeJEPA (2511.08544, provable anti-collapse via
  SIGReg) → identifiability theory (2605.26379, 2607.22430).
- LeCun left Meta Nov 19 2025 → **AMI Labs** (Paris, CEO Alexandre LeBrun);
  $1.03B seed at ~$4.5B post (Mar 2026; NVIDIA, Bezos Expeditions, Temasek…).
  Agenda names **persistent memory** as a pillar. NOTHING SHIPPED as of mid-2026
  (BBC July 2026: refining through year-end).
- Arena: Genie 3 → Project Genie (public Jan 2026); Waymo World Model (Feb 2026);
  World Labs Marble (commercial, $1B raise Feb 2026); Odyssey-2/Starchild/Agora;
  Decart; NVIDIA Cosmos 3 (June 2026, open omnimodel).

## 2. GWT in AI
- Architecture thread lives mainly in VanRullen's group: **Multimodal Dreaming**
  (2502.21142) = GW latent as fusion space for Dreamer-style world-model RL —
  the closest world-model×workspace combination. Also chained-operations routing
  (2025), ASAC attention-schema (2509.16058).
- **Headline: Anthropic, "Verbalizable Representations Form a Global Workspace in
  Language Models" (Transformer Circuits, July 2026)** — sparse mid-layer "J-space"
  (~10% activation variance, found via open-sourced Jacobian lens) behaves like a
  GWT workspace inside Claude-family LLMs. Formal commentaries by Dehaene & Naccache
  and Eleos AI. Directly relevant to us: workspace-like structure EXISTS in frozen
  LLM hidden states — the substrate our head reads.
- Consciousness-assessment thread: Butlin & Long rubric updated (TiCS Jan 2026,
  19 authors incl. Bengio/Chalmers/VanRullen); J-space is its main empirical case.

## 3. Verdict for us
- **No one in either camp does memory-write selection.** World-model camp treats
  persistent memory architecturally (AMI pitch, Genie memory horizon), never as a
  learned retention decision. GWT camp has the concept (workspace admission = a
  salience gate) but trains routing for within-episode computation, never against
  long-horizon outcomes over an external store.
- Positioning sentence banked: an outcome-trained salience head on a frozen LLM is
  an **operationalized GWT broadcast gate supplying the persistent-memory leg of
  the world-model agenda** — an open seam between the two programs. (Discussion
  section material; the paper stays anchored to memory/RL literature.)
- Anthropic J-space gives a concrete follow-up experiment: does our head's learned
  direction live in / near the J-space? (If their Jacobian lens is open-sourced,
  this is cheap and would be a striking interpretability tie-in. Post-paper-1.)

## 4. ACTION ITEMS (competitive)
- Agent-flagged possible NEW competitors not in notes 12-19:
  **2606.10616 "Learning What to Remember"** and **2606.05894 "EMBER" (budgeted
  retention)** — deep-read dispatched 2026-08-11 (night); verdict to be appended.
- Memory-R1 (2508.19828) confirmed ACL 2026 — already in our landscape (RL memory
  ops on external store; tool-call line, not a collision).

## 5. Deep-read verdicts (appended same night; direct arXiv reads by agent)

**OSL-MR (2606.10616)** — "Learning What to Remember: Observability-Safe Memory
Retention via Constrained Optimization for Long-Horizon Language Agents" (HKUST +
Huawei Noah's Ark). Supervised (BCE on realized-evidence labels), external text
store, within-conversation, hard token budget, no typed eval, frozen backbone.
They EXPLICITLY reject outcome supervision: "reward is a sequence-level scalar
that cannot be decomposed into per-memory credit" — quotable motivation for our
dense TD-value distillation, which is precisely the decomposition they say is
missing. **Threat: baseline** (budgeted-retention foil).

**EMBER (2606.05894)** — "Efficient Memory via Budgeted Evidence Retention for
Long-Horizon Agents" (UW-Madison + NVIDIA Research — Tong Che; internal-colleague
flag: worth a conversation pre-publication). GRPO RL fine-tunes the WRITER LLM
itself (Qwen2.5-7B/14B) with delayed answer-gated outcome reward; external
verbatim text capsules; within-episode protocol; soft token budget via reward
penalty; no typed eval; writer NOT frozen. **Threat: cousin — collides on axis 1
(outcome-trained write signal), must cite + differentiate.** Differentiators:
sparse terminal GRPO reward vs dense oracle TD distillation; RL-tuned writer vs
frozen backbone + tiny head; binary retain decisions vs graded write strength
w = surprise×(1+β·salience); text capsules vs parametric fast weights; per-episode
vs cross-episode; F1/recall vs gist-verbatim-typed probes.

**Net: 3 of 4 novelty axes survive both (parametric writes, cross-episode,
retention-typed eval); axis 1 is now shared with EMBER and differentiation is
methodological, not cosmetic.** Positioning line: both competitors select TEXT to
keep; Felt Attention learns HOW STRONGLY to write into WEIGHTS.

## 6. Aug-12 intake (agent deep-reads)

**Memory Decoder (2508.09874, NeurIPS'25, SJTU/Shanghai AI Lab)** — small
decoder pretrained to imitate a kNN-LM retriever over a domain corpus;
plugs into frozen LLMs by output-distribution interpolation. NO write policy,
no selection, no budget, no incremental writes — pretrain-once domain
adaptation. Verdict: not a competitor, not a substrate. STEALABLE: (a) the
output-interpolation READ path (merge memory predictions without touching
internals); (b) KL-distillation as a slow consolidated tier under fast
weights — salience-weighted distillation = a literal sleep phase.

**"Memory in the Age of AI Agents" survey (2512.13564, 48 authors, Dec'25)**
— Forms/Functions/Dynamics taxonomy; our slot: parametric form ×
factual+experiential function × importance-driven formation/retention.
No standalone write-policy chapter (concept smeared across Formation /
importance-driven forgetting / RL-assisted). Their benchmark table has NO
typed gist-vs-verbatim retention benchmark → supports our eval claim; §7
open problems match ours ("manually engineered rules", no long-term
consolidation, agents lack gist-like constructive memory). Coverage gap in
the survey itself: ATLAS/TTT/fast-weights/KVP/EMBER absent — our corner is
essentially unmapped there. THREAT FLAG to verify by direct read: Mem-α
(RL-trained memory-construction policy) + MEM1/MemAgent RL-write family
(believed token-level external stores, not value-gated parametric — confirm).

## 7. Aug-13 landscape sweep (online-learning SOTA verification)
Baseline HOLDS: no lab updates deployed weights from traffic; shipped memory
= text retrieval; continual FT still costs frontier models 15-32%
(2601.18699); METR declines to claim measured RSI acceleration (Jul 2026).
NEW + relevant: **OpenAI "Dreaming"** (Jun 2026) — sleep-time consolidation
building weighted memory chains, TOKEN-SPACE ONLY, heuristic curation → the
industry productized our founding metaphor and stopped at exactly the
boundary we cross (learned salience, parametric store, outcome-derived
importance). Intro-signal + related-work cite. **TTT-Discover** (2601.16175,
Stanford/NVIDIA/Together) — verifier-gated weight updates at inference, real
SOTAs, single-problem scope: outcome-gated TTT, adjacent axis (solve-one vs
retain-lifetime); cite + NVIDIA-internal conversation thread. **Memory
amplifies sycophancy 25x** (Jun 2026 study) — ecological echo of our S4
toxic-memory result (bad retention < no retention). Predictions ≠ results:
Amodei/Douglas forecast continual learning falls 2026 — statements only.

## 8. Aug-17 batch (verified deep-reads; advisor lit-dump triaged)
AgeMem (2601.01885): COUSIN, closest to claim-(a) — memory ops as policy
actions, 3-stage RL + step-wise GRPO on task reward, whole backbone tuned,
external store. Must-cite + head-to-head. Our (a) survives narrowly:
frozen backbone + explicit head + dependency credit.
D-MEM (2603.14597) CONFLICT RESOLVED: v1 only, never revised — "Dopamine-
Gated via RPE Routing" is branding; mechanism = training-free (z-score
embedding surprise + prompted 3-tier utility; zero learned params; KG
consolidation pipeline). Our May direct read stands. Must-cite (they own
the surprise+utility-gating vocabulary); baseline by mechanism.
ALMA (2602.07755): baseline — meta-agent PROGRAM SEARCH over executable
memory designs; nothing gradient-trained. The "search vs learn" alternative.
U-Mem (2602.22406): baseline — cost-aware acquisition cascade + Thompson
sampling; explicitly avoids training. Strong non-parametric comparator.
Self-Guide (2604.03098): conceptual cousin — co-evolved internal reward
gates ACTIONS, no memory module. Cite for learned-internal-signal lineage.
INSPO/MetaSkill-Evolve/AutoSci/Sophia: none (optional cites).
NET: claim (a) crowded (state narrowly); claim (b) — generative gist LTM,
felt-curated dreamed consolidation, analogical-completion reads — NOVEL
across all nine; (a)+(b) combination untouched. Paper-1 flagship = (b),
independently ratifying the locked scoping.

## 8b. AgeMem full evidence audit (2601.01885, Alibaba+Wuhan, Jan 2026)
Method: 6 memory tools (Add/Update/Delete on vector store; Retrieve/
Summary/Filter on context) as RL actions; Qwen2.5-7B + Qwen3-4B; GRPO
trained on HotpotQA ONLY, zero-shot to ALFWorld/SciWorld/PDDL/BabyAI.
Numbers: avg 41.96 vs Mem0 37.14 vs no-mem 28.05 (7B); RL alone +8.5.
CREDIT: "step-wise GRPO" = trajectory-level advantage broadcast uniformly
to all steps; zero intermediate reward; NO usage tracing / per-write
credit / counterfactual ablation. Reward partly gameable (maintenance=1
if any update/delete fired; tool counts inflate under RL).
CONFOUNDS (their gaps = our contributions): (1) backbone fine-tuned
(full vs PEFT unstated), baselines run untrained model — generic-
capability confound uncontrolled; frozen backbone is exactly the missing
control. (2) Qwen-Max is BOTH training judge and eval judge; trained and
evaluated on HotpotQA; no contamination/leakage analysis. (3) never
swaps trained vs heuristic WRITE SIGNALS inside own system. (4) no
capacity-pressure ablation, no seeds/error bars, no code.
REINFORCEMENT FOR US: (i) outcome-trained memory ops > all heuristic
systems, independently confirmed at 7B — premise de-risked. (ii) Their
tables REPLICATE our S4: untrained tools < no-memory on PDDL+BabyAI;
Mem0/LangMem < no-memory on Qwen3. "Naive memory hurts" is now a
cross-paper regularity. (iii) Positioning: "AgeMem shows it works; we
show why/when with the confounds removed" — head-to-head framing.
Untouched by them: per-write credit, frozen-backbone isolation, leakage
gates, capacity regimes, anything parametric/generative (claim b).

## 9. Doc-to-LoRA lineage audit (2026-08-20, verified deep-read)
Line: T2L (Sakana, ICML'25, task-desc->adapter, task style only) ->
Generative Adapter (MSR/UW, ICLR'25, 7B, StreamingQA F1 31.5 vs weak-SFT
19.5) -> Doc-to-LoRA (Sakana 2602.15902, Gemma-2-2B, Perceiver hypernet
309M, per-chunk rank-8 LoRAs concat along rank; amortized context
distillation) -> SHINE (2602.06358) -> Doc-to-Atom (2606.12400, typed
micro-LoRA atoms + query router; unverified claims).
KEY NUMBERS: D2L = 82-86% of the in-context ceiling on factual QA; ~4-5pt
below ORACLE gradient context-distillation on same data; <1s vs 40-100s.
QUERY-SWAP RED FLAG: unrelated queries collapse precision 0.720->0.044 —
a resident generated adapter corrupts unrelated behavior (fatal for an
always-mounted memory LoRA). No continual/multi-doc accumulation study
anywhere in the line. All evals 2B-8B, single-doc, short-horizon.
VERDICT for us: (b) citable amortized ALTERNATIVE, not a replacement —
their value prop is write LATENCY, which our sleep cycle gets for free;
gradient consolidation recovers the 15-18% quality gap. NOT (c): these DO
inject facts — the "task-adaptation only" objection died Feb 2026.
Position: "quality-first consolidation where write latency is free."
STEAL: (1) the context-distillation objective as our consolidation loss —
teacher = base model WITH the dream chunk in context, student = adapted
model WITHOUT it; better-grounded than plain next-token SFT on corpus
lines (candidate v2.1 ablation). (2) rank-concat composition trick.
PAPER-2 NOTE: hypernetwork trained on outcome credit emitting the adapter
= the amortized learned write policy (von Oswald Hnet-CL lineage; HyLoVQA).
ENGRAM (startup): $98M @ $600M post (Jun'26; GC/KP/Sequoia, Karpathy
angel; Biderman/Eyuboglu/Lin/Morris/Re) — productized docs->weights
"learned memory layer" for orgs; partners Notion/Microsoft/Harvey.
Commercial validation of weights-as-memory; watch Cartridges/self-study
lineage (Eyuboglu) for their mechanism.

## 10. Meta-Harness (2603.28052, Stanford IRIS — Lee/Finn/Khattab, Mar'26)
Searches over HARNESS CODE (what gets stored/retrieved/shown to a frozen
model); agentic proposer with filesystem access to prior candidates'
source, scores, and full traces. Same diagnosis as us (harness matters
as much as the model, still hand-designed); their fix = search over
code, ours = consolidate into weights. MUST-CITE. Three carries:
(1) CHALLENGE: their ablation — raw traces beat scores+summary; summaries
can HURT by compressing away diagnostic detail. Our dreamer is
summarization; counter = their proposer can grep raw traces on demand,
weights have no grep — compression is our substrate's constraint, not a
choice. Address head-on in the paper.
(2) GIFT: they name co-evolving harness and model weights as the open
next step — our architecture, flagged open by Stanford.
(3) GAP -> ARM BACKLOG: filesystem+grep agentic retrieval is a strong
beyond-context baseline missing from our six arms. Queue as arm 8
("agentic-grep": model gets search tools over the raw life log) —
probably the strongest honest retrieval baseline available.
Related: Rohin's CURE debug agent (field_evidence/) = the real-world
manual/amortized version of harness self-improvement; its self-report is
ground truth for dreamer design.
