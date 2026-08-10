# Prior-Art Check: Titans/ATLAS baselines, learned-value writes, cross-episode eval

Date: 2026-08-10. Scope: focused prior-art check for the dream-state project's core novelty
(replace Titans/ATLAS surprise-weighting with a *learned / RL-trained value function* that
decides what/how strongly to consolidate into **parametric** neural memory).

Papers grounding the question:
- Titans: "Learning to Memorize at Test Time" — arXiv 2501.00663 (Behrouz, Zhong, Mirrokni;
  Google), NeurIPS 2025.
- ATLAS: "Learning to Optimally Memorize the Context at Test Time" — arXiv 2505.23735 (Behrouz
  et al., Google), 2025.
- Related Google line: MIRAS / "It's All Connected" (arXiv 2504.13173); Nested Learning / HOPE
  (arXiv 2512.24695); research.google blog "Titans + MIRAS".

---

## QUESTION 1 — What did Titans/ATLAS benchmark against, and what claim were they defending?

**Core claim being defended (both papers): an in-context, test-time-trained parametric memory
(a deep MLP whose weights are updated by gradient descent on a surprise loss) is a better
sequence-modeling primitive than attention and than other sub-quadratic recurrent models,
especially at long context and recall-heavy tasks.** They are defending an *architecture*
position, not a retrieval-vs-parametric position.

### Baseline set (mostly other sequence-model architectures, NOT retrieval systems)

ATLAS (Table 1 and experiments) compares against:
- Modern recurrent / linear-attention models: **Titans, RWKV-7, Gated DeltaNet, DeltaNet,
  Longhorn, GLA (Gated Linear Attention), RetNet, (Poly)Sketch-Former, TTT, Linear Attention.**
- Attention variants: **standard Transformer(++), Sliding-Window Attention.**
- Its own new variants: DeepTransformers, Deep Linear Attention (DLA), OmegaNet, Dot.

Titans compares against the same family: **Transformer++, RetNet, GLA, Mamba, Mamba2,
DeltaNet, TTT, Gated DeltaNet.**

### Was RAG / external retrieval a baseline?

- **ATLAS: No.** No RAG or external-retrieval system appears as a baseline. ATLAS is purely an
  in-context-memory architecture comparison.
- **Titans: Partially / only in the needle-in-haystack + BABILong setting.** Titans includes
  large instruction models **with RAG** as reference points in the long-context retrieval/
  reasoning tables — specifically **Llama-3.1-8B + RAG** and a **RAG-augmented Llama-3.1-70B**,
  alongside **GPT-4, RecurrentGemma-9B, Llama-3.1-70B, Mistral.** These are used to argue Titans
  (a ~small model) beats much larger RAG-augmented models on BABILong. This is a "we beat RAG on
  this benchmark" point, NOT a systematic study of retrieval memory. RAG is used as a strawman
  reference, not as a co-designed baseline family.

### Benchmarks used

- **Language modeling perplexity** (e.g., on standard LM corpora) and **common-sense reasoning**
  (zero-shot suite: PIQA, HellaSwag, WinoGrande, ARC, etc.).
- **Recall-intensive / associative recall**: single- and multi-needle-in-a-haystack (S-NIAH /
  RULER-style), in-context recall, MAD synthetic benchmark, associative recall.
- **Long-context reasoning**: **BABILong** (reasoning over facts scattered in very long docs).
  ATLAS headline: **+80% accuracy at 10M-token context on BABILong**; Titans headline: beats
  GPT-4 / RAG-Llama-3.1-70B on BABILong despite far fewer parameters; scales past ~2M tokens on
  NIAH.

### What they claim to beat, on what

- Beat Transformer++ and all listed linear-recurrent models (Mamba2, DeltaNet, Gated DeltaNet,
  RWKV-7, TTT, GLA, RetNet) on **LM perplexity, common-sense reasoning, recall-intensive tasks,
  and long-context**.
- Beat much larger models (GPT-4, Llama-3.1-70B, RecurrentGemma-9B) **and RAG-augmented Llama**
  on **BABILong / needle-in-haystack** specifically.

**Takeaway for the project:** Titans/ATLAS are defending "parametric test-time memory > attention/
other recurrences" on long-context LM. They do NOT seriously benchmark against learned retrieval /
episodic-store memory systems, and RAG appears only as a beaten reference on BABILong. This leaves
the "learned-value write vs surprise write" comparison entirely open in their evaluations.

---

## QUESTION 2 — Learned / RL-trained VALUE-weighted WRITE into parametric/fast-weight memory?

**VERDICT: OPEN (at most PARTIAL). I found no published work that puts a trained value/policy
head in charge of the WRITE decision — what/how strongly to consolidate — into *parametric*
fast-weights / an MLP memory, trained by an *outcome/RL* signal.** The closest works each miss on
exactly one axis: they either (a) use surprise/gradient-magnitude (not learned value), (b) learn
the write but into an *external text/episodic store* (not parametric weights), or (c) learn the
write into parametric memory but via *meta-learned self-supervised reconstruction*, not an
outcome/value signal that weights write strength.

### Axis definition (to keep the claim precise)
The project's novelty = **[trained value/policy head] × [decides write strength/selection] ×
[writes into parametric weights] × [trained on outcome/RL reward]**. No single paper hits all four.

### Closest works and exactly how they differ

1. **Titans / ATLAS / MIRAS / Nested-Learning (HOPE)** — Google, 2025.
   - Write into parametric memory: YES (MLP weights via GD). Write decision: **surprise =
     gradient magnitude**, plus data-dependent momentum/forget gates learned as part of ordinary
     pretraining. **Not** a value/outcome-trained head. MIRAS generalizes the *internal loss*
     (attentional bias) and retention regularizer, but it is still an online-optimization/surprise
     objective, not an RL value. **This is exactly what the project proposes to replace.**

2. **GradMem: "Learning to Write Context into Memory with Test-Time Gradient Descent"** —
   arXiv 2603.13875 (Kuratov et al.), ICML 2026. *Closest on the "learned write into parametric
   memory" axis.*
   - WRITE = inner-loop GD on a small set of prefix **memory tokens** (a parametric memory) using
     a self-supervised **reconstruction** loss; READ objective is **meta-learned** by backprop
     through the write updates. So the write *rule* is trained — but via self-supervised
     reconstruction + meta-learning, **not** an RL/outcome value, and there is **no value head
     weighting which content to write or how strongly** (it optimizes memory tokens per example,
     not a consolidate/skip decision). Differs from the project on the "value/outcome-trained
     write-strength decision" axis.

3. **Auto-Dreamer: "Learning Offline Memory Consolidation for Language Agents"** —
   arXiv 2605.20616, 2026. *Closest on the "outcome-trained consolidation decision" axis, and the
   single most relevant paper to the project overall.*
   - Learns an **offline consolidator** (complementary-learning-systems / wake-sleep framing) that
     decides what to keep/abstract across sessions, **trained via GRPO with end-to-end agent task
     success as reward.** This IS learned, outcome-trained "what to consolidate." BUT it
     consolidates a **typed natural-language memory bank (external episodic store)** — it rewrites
     text entries — **not** the parametric weights of an MLP memory. Differs from the project on
     the "parametric weights" axis. NOTE: extremely close to the dream-state thesis; the project's
     differentiator vs Auto-Dreamer is *writing into parametric fast-weights rather than a text
     store*. Worth a direct positioning/citation.

4. **Memory-R1 / MemRL / AgeMem and similar (2024-2026)** — learn RL/agent policies over an
   **external episodic/vector store**, and they learn what to **READ / select / retrieve** (and
   sometimes add/delete text entries). Differ on BOTH the "parametric weights" axis and the
   "write-into-weights" axis. (Confirmed as out-of-scope per the task framing.)

5. **RL-trained memory-writer lineage in RL agents** (e.g., write-network "reservoir sampling"
   memory, Hadamard/fast-weight memory for RL agents; Schmidhuber-style "learning to control
   fast-weight memories"). Some *do* train a write policy by downstream reward, and some target
   fast-weight matrices — but these write into a **slot/associative external memory or a linear
   fast-weight matrix for control**, on RL control tasks, not a Titans-style deep-MLP parametric
   memory for language/consolidation, and the "value" is generic RL return rather than a
   consolidation value head. Partial overlap on "RL-trained write," but different memory substrate
   and domain.

6. Neuroscience-side: "Memory consolidation from a reinforcement-learning perspective"
   (Front. Comput. Neurosci. 2024) — conceptual/biological support for RL-guided consolidation,
   not an ML method with parametric fast-weight memory.

### Net for Question 2
The specific combination — **a trained value/policy head that weights parametric-memory WRITES,
supervised by outcome/RL reward, replacing surprise** — appears **unpublished (open)**. GradMem
owns "learned write into parametric memory (but self-supervised, no value head)"; Auto-Dreamer
owns "outcome-trained consolidation decision (but into an external text store)." The project sits
in the *unoccupied intersection* of these two. Recommend citing both as the nearest neighbors and
framing novelty precisely as that intersection. (Caveat: this is a fast-moving area — 2606-2607
arXiv preprints exist, e.g. "Scaling Self-Evolving Agents via Parametric Memory" 2606.04536,
"AutoMem" 2607.01224 — worth a final sweep before submission; I did not find any that close the
gap, but confidence is moderate, not absolute.)

---

## QUESTION 3 — Are Titans/ATLAS evaluated CROSS-EPISODE / continual, or only long-context?

**VERDICT: ONLY long-context within a single continuous sequence. No cross-episode / continual /
lifelong evaluation.**

- ATLAS full text: all evaluations are within single continuous sequences (LM perplexity,
  common-sense zero-shot, S-NIAH, MAD, associative recall, BABILong up to 10M tokens). The test-
  time memory writes happen *within* the forward pass over one sequence and are **not carried
  across independent tasks/episodes**; the model's pretrained ("slow") parameters are not updated
  by the deployment stream. There is no protocol where memory persists and consolidates across
  separate episodes/tasks.
- Titans: same — long-context LM, NIAH, BABILong, DNA/time-series as long single sequences. "Long-
  term memory" here means "memory of earlier tokens in the same stream," reset per sequence.
- Important framing for the project: **"compresses a long stream" ≠ "consolidated long-term memory
  across episodes."** Titans/ATLAS demonstrate the former only. The Google *Nested Learning / HOPE*
  and MIRAS blog posts *gesture* at continual learning as motivation (multi-timescale "Continuum
  Memory System"), but the published Titans/ATLAS *evaluations* are single-sequence long-context,
  not lifelong/cross-episode benchmarks (no ALFWorld/agentic multi-episode continual eval).

**Takeaway for the project:** the cross-episode / continual-consolidation regime (memory persisting
and consolidating across separate ALFWorld-style episodes) is **genuinely unoccupied by
Titans/ATLAS's evaluations** — this is a clean, defensible axis of novelty independent of the
value-vs-surprise write question.

---

## Bottom-line answers

1. **ATLAS baseline set = sequence-model architectures only** (Titans, RWKV-7, Gated DeltaNet,
   DeltaNet, Longhorn, GLA, RetNet, TTT, (Poly)SketchFormer, Linear Attention, Transformer++, SWA,
   plus its own DLA/OmegaNet/Dot). **RAG was NOT an ATLAS baseline.** Titans additionally cites
   **Llama-3.1-8B/70B + RAG, GPT-4, RecurrentGemma-9B** as beaten reference points on BABILong/NIAH
   only. Benchmarks: LM perplexity, common-sense reasoning, S-NIAH/needle, MAD, associative recall,
   BABILong (ATLAS: +80% @10M ctx).

2. **Learned-value-write into parametric memory = OPEN (unpublished).** Nearest neighbors:
   **GradMem** (learned/meta-learned write into parametric memory tokens, but self-supervised
   reconstruction, no value head) and **Auto-Dreamer** (GRPO/outcome-trained consolidation
   decision, but into an external text memory bank, not parametric weights). Titans/ATLAS/MIRAS use
   surprise = gradient magnitude, not a trained value. Memory-R1/MemRL/AgeMem learn READ/retrieval
   over external stores. The project's exact combination is the unoccupied intersection.

3. **ATLAS (and Titans) are tested only on long-context within a single sequence — NOT
   cross-episode / continual / lifelong.** The continual-consolidation-across-episodes setting is
   open.

## Key URLs
- Titans: https://arxiv.org/abs/2501.00663
- ATLAS: https://arxiv.org/abs/2505.23735
- MIRAS "It's All Connected": https://arxiv.org/abs/2504.13173
- Nested Learning/HOPE: https://arxiv.org/abs/2512.24695
- GradMem: https://arxiv.org/abs/2603.13875 (code: github.com/yurakuratov/gradmem)
- Auto-Dreamer: https://arxiv.org/abs/2605.20616
- Google blog "Titans + MIRAS": https://research.google/blog/titans-miras-helping-ai-have-long-term-memory/
</content>
</invoke>
