# Prior Art: Human Memory-Testing Paradigms Applied to LLM / Agent Memory

Date: 2026-08-10. Scope: arXiv/Scholar 2022–2026 + cog-sci venues.
Question: has anyone measured LLM/agent memory using validated human memory paradigms, and is there a psychology-grounded, memory-type-agnostic AGENT-memory benchmark?

Legend: **Target** = raw LLM (in-context/parametric) vs agent memory system (RAG/banks/consolidation). **Type** = one-off study vs reusable benchmark.

---

## 1. Ebbinghaus forgetting curves (retention vs time/interference)

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| Forgetting Curve: A Reliable Method for Evaluating Memorization Capability for Long-context Models | arXiv:2410.04727 | 2024 | reusable eval method | raw LLMs (long context) | Uses "forgetting curve" name; measures memorization vs context distance, not wall-clock/session time |
| Human-like Forgetting Curves in Deep Neural Networks | arXiv:2506.12034 | 2025 | study | DNNs generally | Retention-interval framing; not agent memory |
| ForgetBench: Benchmarking Forgetting Dynamics of Long-Term Parametric Memory | arXiv:2607.26455 | 2026 | benchmark | parametric memory (model editing) | Key finding: LLM forgetting **diverges** from smooth Ebbinghaus decay (anomalous, non-monotonic) |
| FOREVER: Forgetting Curve-Inspired Memory Replay | arXiv:2601.03938 | 2026 | method (not eval) | continual learning | Ebbinghaus as design inspiration for replay scheduling |
| MemoryBank | arXiv:2305.10250 (AAAI'24) | 2023 | method (not eval) | agent memory bank | Ebbinghaus-inspired **decay mechanism** in the memory system; the eval itself is ad-hoc QA, not a retention-curve probe |
| Ebbinghaus Forgetting Curve and LLM Memory Management | ACM ICICT 2026 (10.1145/3803291.3803294) | 2026 | position/framework | long-context | Design prospects paper |
| eMEM-Bench v1 "foil-augmented retention curve" | arXiv:2606.03374 | 2026 | benchmark (embodied) | embodied agent memory | See §8 — one of its 8 paradigms |

**Status: ported as a metaphor/mechanism many times; ported as a controlled retention-vs-delay-vs-interference EVAL only for parametric memory (ForgetBench) and embodied agents (eMEM). No text-agent-memory retention-curve probe.**

## 2. Gist vs verbatim / fuzzy-trace theory (our structure-vs-detail axis) — CRITICAL

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| ReadAgent: Human-Inspired Reading Agent with Gist Memory | arXiv:2402.09727 (DeepMind) | 2024 | method | agent (long-doc reading) | Gist memory as **architecture** (gisting + lookup); evaluated on QuALITY/NarrativeQA/QMSum, not on gist-vs-verbatim probes |
| MM-Mem: From Verbatim to Gist (Semantic Information Bottleneck) | arXiv:2603.01455 | 2026 | method | multimodal video-agent memory | Explicitly grounded in **Fuzzy-Trace Theory** (verbatim→gist pyramid: sensory buffer / episodic stream / symbolic schema). Architecture, not an evaluation paradigm |
| DRM-adjacent: gist-based false memory (see §6) | arXiv:2509.17138 | 2025 | study | raw LLMs | FTT is the standard explanation of DRM; false-memory results are indirect evidence of gist-dominant encoding, but no paper separates gist vs verbatim **retention as measured axes** |

**Status: FTT used only as ARCHITECTURE inspiration. Nobody has ported the gist/verbatim dissociation as an EVALUATION paradigm (paired verbatim-probe vs gist-probe over the same stored content, tracking dissociation over delay/consolidation). This axis is open — and it is exactly our structure-vs-detail axis.**

## 3. Free recall vs cued recall vs recognition

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| Memory GAPS: Would LLMs pass the Tulving Test? (Chauvet) | arXiv:2402.16505 | 2024 | one-off, exploratory | raw LLMs | Tulving's GAPS framework + Remember/Know; recognition vs recall |
| Assessing Episodic Memory in LLMs with Sequence Order Recall Tasks (SORT) (Pink et al., incl. Hasson, Norman, Huth, Toneva) | arXiv:2410.08133 / OpenReview | 2024 | reusable benchmark (Book-SORT) | raw LLMs (in-context + fine-tuned + RAG ablations) | Explicitly adapted from human episodic-memory order-recall tasks; strong cog-neuro author team |
| Episodic Memories Generation and Evaluation Benchmark (Huet, Ben Houidi, Rossi) | arXiv:2501.13121 (ICLR'25 proceedings) | 2025 | reusable benchmark | raw LLMs | **Cue-based recall with varied cue combinations** (time/place/entity), mirroring human cued recall; contamination-free synthetic events; found frontier LLMs fail at 10k–100k tokens |
| Analyzing Memory Effects... (see §6) | arXiv:2509.17138 | 2025 | study | raw LLMs | Includes recall/recognition-style list-learning probes; reports immediate recognition good, delayed recognition + recall weaker |
| BEAM / LIGHT (Beyond a Million Tokens) | arXiv:2510.27246 | 2025 | benchmark + method | agent memory (episodic/working/scratchpad) | Broad ability probes, NOT psychology paradigms — representative of the current agent-memory-benchmark style |

**Status: recall/recognition distinction ported to raw LLMs (Tulving Test one-off; two episodic benchmarks). No agent-memory benchmark makes free/cued/recognition a controlled factor.**

## 4. Serial-position effects (primacy/recency)

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| Serial Position Effects of Large Language Models (Guo & Vosoughi) | arXiv:2406.15981, **ACL Findings 2025** | 2024/25 | study (systematic) | raw LLMs | Explicit human-paradigm framing; U-shape + primacy dominance in MCQA; mitigation via prompting |
| Lost in the Middle (Liu et al.) | TACL 2024 (arXiv:2307.03172) | 2023 | study, hugely influential | raw LLMs (long context/RAG inputs) | The canonical U-curve result — framed as positional bias, NOT serial position; later work (2406.15981, 2510.10276) supplies the psych framing |
| Lost in the Middle: An Emergent Property from IR Demands | arXiv:2510.10276 | 2025 | study | raw LLMs | Ties middle-loss to retrieval demands, memory-psychology framing |
| Aspects of human memory and LLMs (Janik) | arXiv:2311.03839 | 2023 | study | raw LLM (GPT-J) | Direct human/LLM comparison of U-shaped recall; argues effects learned from training-data statistics, not architecture |
| Primacy effect in SSMs / Mamba | arXiv:2502.13729, 2506.15156 | 2025 | mechanistic studies | raw models | Architecture-level accounts |

**Status: heavily ported (the most saturated paradigm). "Lost in the middle" IS serial position, and the explicit reframing is already published (ACL Findings 2025). Do not pitch this as novel; use it as the anchor probe.**

## 5. Proactive / retroactive interference

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| Unable to Forget: Proactive Interference Reveals Working Memory Limits (PI-LLM) | arXiv:2506.08184 (OpenReview) | 2025 | reusable eval (released) | raw LLMs (in-context) | Classic PI paradigm (semantically related key-value updates); log-linear decline to zero |
| Transformers Remember First, Forget Last: Dual-Process Interference | arXiv:2603.00270 | 2026 | study (39 LLMs) | raw LLMs | PI **dominates** RI universally — opposite of humans (recency-protected). Great motivating citation |
| Learning to Forget: Sleep-Inspired Consolidation (SleepGate) | arXiv:2603.14517 | 2026 | method | KV-cache / architecture | Sleep-cycle consolidation to resolve PI — adjacent to our dream-state framing |
| MINTEval: Memory under Multi-Target Interference in Long-Horizon Agent Systems | arXiv:2605.18565 | 2026 | benchmark | **agent memory systems** | Interference in long-horizon agents — closest interference work at agent level |
| Fan effect probe in 2509.17138 | arXiv:2509.17138 | 2025 | study | raw LLMs | Anderson's fan effect (associative interference) |

**Status: ported for raw LLMs (well); one agent-level interference benchmark exists (MINTEval, single-paradigm).**

## 6. False memory / DRM paradigm

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| Analyzing Memory Effects in LLMs through the Lens of Cognitive Psychology (Cao, Schooler, Zafarani) | arXiv:2509.17138 | 2025 | one-off battery study | raw LLMs (in-context) | **The closest thing to a human-paradigm memory battery**: list length, list strength, fan effect, DRM-style false memory, positional bias, nonsense-material effect, cross-domain generalization. Not released as a maintained benchmark; no agent memory systems |
| eMEM-Bench v1 DRM lures | arXiv:2606.03374 | 2026 | benchmark (embodied) | embodied agent memory | DRM lures as one of 8 paradigms |
| MIT Media Lab / Loftus line (Pataranutaporn, Chan, Loftus, Maes): "Conversational AI ... Amplifies False Memories in Witness Interviews" (arXiv:2408.04681); "Slip Through the Chat" (IUI 2025) | 2024–25 | human-subject studies | **humans** (reverse direction) | LLMs implant false memories in people — misinformation-effect paradigm, but measuring HUMAN memory. Cite for framing, not prior art on agent memory |

**Status: DRM ported to raw LLMs (one battery study) and embodied agents (eMEM). Not ported to text-agent memory systems (schema-consistent intrusion rates in RAG/banks after consolidation = open).**

## 7. Spacing / testing effects

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| List-strength (repetition) effect in 2509.17138 | arXiv:2509.17138 | 2025 | study | raw LLMs | Massed repetition only; no spaced-vs-massed manipulation |
| (No direct hits) | — | — | — | — | No paper found porting spaced-vs-massed presentation or retrieval-practice (testing effect) as an eval for LLM/agent memory consolidation |

**Status: essentially OPEN. For a wake-sleep consolidation system this is a natural, unclaimed probe (does retrieval practice during wake protect a memory through sleep consolidation? does spaced exposure beat massed?).**

## 8. Psychology-grounded benchmarks / batteries ("machine psychology")

| Work | ID / venue | Year | Type | Target | Notes |
|---|---|---|---|---|---|
| CogBench: a LLM walks into a psychology lab (Coda-Forno et al.) | arXiv:2402.18225, **ICML 2024** | 2024 | reusable benchmark | raw LLMs | 10 metrics from 7 cog-psych experiments — but bandits/planning/risk/metacognition; **no memory paradigms** |
| CogArena: Multimethod Evaluation of Cognitive Ability Structure | arXiv:2607.24999 | 2026 | benchmark | raw LLMs | Psychometric structure, not memory-focused |
| **eMEM-Bench v1** (Rasheed & Kabtoul) | arXiv:2606.03374 | 2026 | reusable benchmark (code released) | **embodied** agent memory (ProcTHOR scenes) | 8 paradigms: DRM lures, pattern separation, pattern completion, source monitoring, context-dependent retrieval, long-horizon interference, serial position, foil-augmented retention curve. **Closest existing thing to our pitch — but embodied/spatial, coupled to their eMEM system, not memory-type-agnostic for text agents** |
| **EvolMem: Cognitive-Driven Benchmark for Multi-Session Dialogue Memory** | arXiv:2601.03543 | 2026 | reusable benchmark | raw LLMs + agent memory mechanisms | Grounded in the declarative/non-declarative **memory-type taxonomy** (what kinds of memory), not in validated **testing paradigms** (how memory is probed). Found agent memory mechanisms don't reliably help |
| MemoryAgentBench | arXiv:2507.05257 | 2025 | benchmark | agent memory systems | Four competencies (accurate retrieval, test-time learning, long-range understanding, conflict resolution/selective forgetting) — "cognitively inspired" labels, not paradigm ports |
| MemGym | arXiv:2605.20833 | 2026 | benchmark harness | agent memory systems (7 memory families, swappable) | **Memory-type-agnostic harness with a shared memory contract — but zero psychology grounding.** The harness pattern to emulate/complement |
| MemBench (Tan et al.) | arXiv:2506.21605, ACL Findings 2025 | 2025 | benchmark | LLM-agent memory | Factual+reflective memory; cog-psych used loosely as inspiration |
| Standard agent-memory benchmarks: LoCoMo, LongMemEval, DialSim, MSC, BEAM, MemoryBench, MemGround, StreamMemBench, MemDelta | 2023–26 | benchmarks | agent memory | All ability/task-taxonomy driven; none paradigm-grounded. MemDelta (arXiv:2606.29914) shows current agent-memory evals have hidden confounds — supports the case for controlled psychophysics-style probes |

### Cog-sci venue crossover ("do LLMs remember/forget like humans")
- **Towards LLMs with human-like episodic memory** — *Trends in Cognitive Sciences* opinion, 2025 (Cell S1364-6613(25)00179-2): lists human episodic properties (dynamic updating, event segmentation, selective encoding/retrieval, temporal contiguity, retrieval competition) that current memory-augmented LLMs are "misaligned" with. Framing/agenda paper, no benchmark.
- **Human-Like Remembering and Forgetting in LLM Agents: ACT-R-Inspired Memory Architecture** — HAI 2025 (10.1145/3765766.3765803): ACT-R activation (decay + frequency + noise) as agent memory mechanism. Method, not eval.
- Janik arXiv:2311.03839 (human/LLM recall-curve comparison); Transformers Remember First, Forget Last (PI/RI human-comparison); Human-like Forgetting Curves in DNNs. No dedicated PNAS/NHB "LLM forgetting curve" flagship study found.

---

## VERDICT

**(a) Which paradigms are already ported, and by whom**
- **Ported, well-established (raw LLMs):** serial position (Guo & Vosoughi ACL'25; Lost-in-the-Middle literature; Janik), proactive/retroactive interference (PI-LLM 2506.08184; 39-model PI/RI study 2603.00270), forgetting/retention curves (2410.04727; ForgetBench), recognition-vs-recall (Tulving Test 2402.16505; SORT 2410.08133; Huet episodic benchmark 2501.13121).
- **Ported once, one-off:** DRM false memory + list length/strength + fan effect — the Cao/Schooler/Zafarani battery (2509.17138), raw LLMs only.
- **Ported to agents only in niches:** eMEM-Bench v1 (8 paradigms, embodied/spatial only); MINTEval (interference only).
- **NOT ported as evaluation:** gist-vs-verbatim / fuzzy-trace dissociation (only used as architecture inspiration: ReadAgent, MM-Mem) and spacing/testing effects. These are our two most defensible novel axes, and both align with wake-sleep consolidation.

**(b) Is there an existing psychology-grounded AGENT-memory benchmark?**
No general-purpose one. The landscape splits cleanly: paradigm-grounded work targets raw LLMs in-context (one-off studies or single-paradigm evals), while agent-memory benchmarks (LoCoMo, LongMemEval, MemBench, MemoryAgentBench, BEAM, MemGym) are ability-taxonomy driven with no validated-paradigm probes. The two near-misses: **eMEM-Bench v1** (paradigm-grounded but embodied-only and system-coupled) and **EvolMem** (agent-facing and "cognitive-driven," but grounded in the memory-type taxonomy, not in testing paradigms).

**(c) Is the combination open?**
**Yes, narrowly.** "Validated human testing paradigms as probe types × memory-type-agnostic harness (RAG / parametric / banks / consolidation, MemGym-style swappable contract) × text/general agent setting" is unclaimed as of Aug 2026. Requirements to hold the claim: (1) differentiate explicitly from eMEM-Bench v1 (embodied, spatial, single-system) — it proves the framing is in the air; (2) don't claim novelty on serial position or PI (cite as ported anchors); (3) lead with the unported axes — gist/verbatim dissociation probes and spacing/testing-effect probes — plus paradigm probes applied ACROSS memory backends under controlled conditions (MemDelta's confound critique is the motivation). Move fast: eMEM-Bench (June 2026) and EvolMem (Jan 2026) show convergence on this idea.

## Closest works (ranked by threat/overlap)
1. **eMEM-Bench v1** — arXiv:2606.03374 (2026). 8 cog-psych paradigms incl. DRM, serial position, interference, retention curve — but embodied agents only.
2. **Cao, Schooler & Zafarani, "Analyzing Memory Effects in LLMs through the Lens of Cognitive Psychology"** — arXiv:2509.17138 (2025). The paradigm battery, but one-off and raw-LLM only.
3. **EvolMem** — arXiv:2601.03543 (2026). Cognitive-driven agent-memory benchmark, taxonomy- not paradigm-grounded.
4. **SORT / Book-SORT** — arXiv:2410.08133 (2024). Cleanest single-paradigm port with cog-neuro credibility; template for probe design.
5. **PI-LLM** — arXiv:2506.08184 (2025) + **2603.00270** (2026). Interference paradigms, raw LLMs; the "opposite of humans" finding is a key motivator.
6. **MemGym** — arXiv:2605.20833 (2026). The memory-type-agnostic harness (no psychology) we'd want our probes to run inside of.
7. **CogBench** — arXiv:2402.18225 (ICML 2024). Proves the "psychology lab for LLMs" pitch lands at top venues; contains no memory paradigms.
