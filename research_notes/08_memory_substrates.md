# Memory Substrates — What Should the Small Separate Memory Net BE?

Date: 2026-07-13
Cluster: memory substrates (test-time / latent / parametric / compressive memory)
Scope question: For Dream-State Paper 1 (B/POC), the sleep procedure does **attention-weighted post-training of a small separate parametric memory net**. This note surveys candidate substrates and picks the one that best supports: (a) attention-weighted imprinting during sleep, (b) capacity-limited interference as the *forgetting* mechanism, (c) measurement of the memory in isolation.
Caveat: 2605.*/2509.* arXiv IDs are recent — verify before citing. Classics (Transformer-XL, Compressive, Memorizing Transformers, Infini-attention, RMT) are well-established.

---

## Decision axes (how each paper is scored)

The small net must be a **separate parametric module** we own, distinct from the frozen thinking model. For each paper:
- **SUBSTRATE** = external KV DB / compressed hidden states / neural fast-weights / adapter / latent tokens.
- **WRITE** = how memory is populated; learned-vs-fixed rule.
- **READ** = how memory is queried; learned-vs-fixed.
- **Test-time adapt?** = does the memory change its own parameters/contents at inference.
- **Fit for us on (a)/(b)/(c)** and a **TAG**:
  - `CANDIDATE-SUBSTRATE` — a small separate parametric store we could adopt as the memory net.
  - `BUILD-PAST` — a mechanism/idea to borrow, but not the substrate itself.
  - `CONTEXTUAL` — memory that lives in context/KV/hidden states, not a separate parametric net; wrong shape for us (this is what we measure *against*, not build).

---

## Tier 1 — Neural fast-weight memory (best structural match)

### Titans: Learning to Memorize at Test Time (2501.00663, Behrouz/Google, NeurIPS 2025)
- Thesis (≤12w): Deep MLP "long-term memory" learns to memorize via surprise at test time.
- SUBSTRATE: **neural fast-weights** — a separate deep MLP memory module M_t, small relative to the backbone.
- WRITE: **learned, gradient-based.** Per-token update is gradient descent on an associative loss, gated by a **surprise** signal (gradient magnitude = novelty) with **momentum** (surprise persistence) and an **adaptive weight-decay / forgetting gate** α_t that shrinks stored magnitude. Write rule ≈ online post-training of M with a salience weight.
- READ: query projection into M_t as a forward pass (learned); three integration modes — memory-as-context, memory-as-layer, memory-as-gated-branch.
- Test-time adapt? **Yes** — M's parameters change during the sequence.
- Fit: (a) **native** — surprise gate is an attention/salience weight on the imprint; batch it over a session = "attention-weighted post-training." (b) **native** — the α_t forgetting gate is exactly capacity-limited decay; a fixed-size MLP in superposition interferes. (c) **good** — M is a standalone module; probe it by querying without the backbone.
- TAG: **CANDIDATE-SUBSTRATE (top).**

### ATLAS: Learning to Optimally Memorize the Context at Test Time (2505.23735, Behrouz/Google, 2025)
- Thesis: Titans successor; memorize a *window* of context, not just the last token.
- SUBSTRATE: **neural fast-weights** (deep memory module), same family as Titans.
- WRITE: **learned** — the **Omega rule** optimizes the memory over a sliding window of c past tokens (context-level, not token-level), with polynomial feature maps + Muon optimizer for locally-optimal updates. Directly fixes Titans' "online-only, one-token-at-a-time" weakness — closer to a *batched* sleep update over an episode.
- READ: forward pass through memory module (learned).
- Test-time adapt? **Yes**, with higher-capacity, better-managed updates.
- Fit: (a) **native + better than Titans** for our sleep batch (window objective = imprint a whole session's salient content at once). (b) native (capacity + decay). (c) good.
- TAG: **CANDIDATE-SUBSTRATE (co-top; the batched-write variant we'd actually build on).**

---

## Tier 2 — Associative / parametric memory matrices (best interference story)

### Larimar: LLMs with Episodic Memory Control (2403.11901, IBM, 2024)
- Thesis: Couple decoder to a Kanerva associative memory for one-shot edit/forget.
- SUBSTRATE: **associative memory matrix** (fixed-slot, Kanerva-style) between an encoder and decoder — a small separate parametric store.
- WRITE: **one-shot, training-free** — least-squares solve to write latent vectors into the memory matrix (reformulated Kanerva Bayesian update). No gradient descent; a write can be **scaled/weighted** per item.
- READ: address the matrix by encoded query, decode conditioned on retrieved latent (learned addressing).
- Test-time adapt? **Yes** — writes/edits/forgets at inference with no retraining.
- Fit: (a) **partial** — write is one-shot solve, not gradient post-training; salience must be injected as a write-strength scalar rather than a surprise gradient. (b) **native + cleanest of all** — a fixed-capacity Kanerva matrix stores items in superposition; adding items past capacity causes **graceful, lossy interference** — weak detail washes out first. This is *literally* capacity-limited forgetting, and it also has an explicit selective-forget op. (c) **excellent** — encoder/matrix/decoder are separate; you can read the matrix in isolation and measure recall degradation vs. #items directly.
- TAG: **CANDIDATE-SUBSTRATE (backup / strongest for the interference-as-forgetting claim).**

### M+: Extending MemoryLLM with Scalable Long-Term Memory (2502.00592, ICML 2025) & MemoryLLM (2602.00398 v.)
- Thesis: Latent memory pool + co-trained retriever holds info across 160k+ tokens.
- SUBSTRATE: **parametric hidden-state memory pool** (~1B memory tokens across layers) + learned retriever; a separate self-updating store.
- WRITE: **learned self-update** — new content compressed into memory hidden states; older states drop out (natural decay). M+ adds a retriever so long-tail memories aren't lost to interference.
- READ: **learned retriever** pulls relevant latent memory into generation.
- Test-time adapt? Yes (memory pool updates online).
- Fit: (a) partial (self-update rule is fixed, not salience-weighted). (b) **good** — MemoryLLM's known forgetting curve *is* capacity-limited interference; M+ documents exactly where it collapses (~20k) and patches it with retrieval. Useful as an interference baseline. (c) good but heavy (1B memory) — larger than our "small net" budget.
- TAG: **CANDIDATE-SUBSTRATE (heavier; good interference-baseline, likely too big for the POC budget).**

### Compressive Transformer (1911.05507, DeepMind) & Transformer-XL (1901.02860)
- Thesis: Compress old activations into a coarse memory instead of discarding.
- SUBSTRATE: **compressed hidden states** (XL: raw cached segment states; Compressive: learned pooling/conv compression of evicted states).
- WRITE: XL = fixed FIFO caching; Compressive = **learned** compression function on evicted memories.
- READ: extended self-attention over [compressed mem | mem | current] (fixed attention).
- Test-time adapt? No parametric self-update; it's a rolling cache.
- Fit: (b) has a compression-ratio knob = a coarse detail-loss dial (borrowable), but memory is context-attached, not a separate net. Wrong shape for isolation.
- TAG: **CONTEXTUAL / BUILD-PAST** (borrow the "compress-old-states" idea; don't adopt substrate).

---

## Tier 3 — External KV / retrieval memory (measure against, don't build)

### Memory3: Language Modeling with Explicit Memory (2407.01178, 2024)
- Thesis: Third memory form — sparsified explicit KV between params and context.
- SUBSTRATE: **external KV DB** — reference chunks stored as heavily-sparsified attention key-values, retrieved and read via attention.
- WRITE: **fixed** — encode reference corpus to sparse KV offline (sparsification across layers/heads/tokens/dim). No salience imprint, no interference-based forgetting (it's a DB; you delete rows).
- READ: retrieve relevant KV, attend (fixed).
- Fit: this is essentially **structured RAG at the KV level** — a *baseline* in our comparison, not the parametric net.
- TAG: **CONTEXTUAL** (fixed-budget-KV baseline).

### Memorizing Transformers (2203.08913) & LongMem (2306.07174)
- Memorizing Transformers: **external KV DB** with **non-differentiable kNN** lookup into one attention layer; write = append KV (fixed), read = kNN + gated attention. Test-time adapt only in the sense the DB grows.
- LongMem: **cached KV memory bank** + a trainable **SideNet** decoupled from a frozen backbone; write = enqueue KV (fixed), read = learned SideNet attention. The SideNet is a separate trainable module (borrowable idea), but the memory itself is a KV cache, not parametric.
- Fit: both are retrieval-over-KV; interference = eviction, not superposition. Baselines, not substrate.
- TAG: **CONTEXTUAL** (LongMem's decoupled SideNet = **BUILD-PAST** idea for read-side).

### MemoRAG (2409.05435)
- Thesis: A light "memory model" drafts clues to guide retrieval over a huge corpus.
- SUBSTRATE: global-memory LM + **external corpus** (RAG). Write = index corpus (fixed); read = memory-guided retrieval (learned draft).
- Fit: a smarter RAG — squarely a **baseline**, not our net.
- TAG: **CONTEXTUAL** (RAG baseline).

---

## Tier 4 — Latent-token & recurrent-state memory (mechanism ideas)

### MemGen: Weaving Generative Latent Memory for Self-Evolving Agents (2509.24704, NUS, 2025)
- Thesis: A "memory weaver" generates latent tokens woven into the agent's reasoning.
- SUBSTRATE: **latent tokens** produced on demand by a learned weaver (+ a trigger deciding when to invoke). Machine-native memory injected mid-reasoning.
- WRITE/READ: both **learned & generative** — no persistent parametric store; memory is re-synthesized each call from the agent state. Spontaneously forms planning/procedural/working sub-clusters.
- Test-time adapt? The weaver is trained (RL); at inference it generates, doesn't store.
- Fit: (a) attractive learned read-side, but (b) **no capacity-limited interference** — nothing to overwrite; forgetting isn't native. (c) hard to measure in isolation (memory only exists interleaved with reasoning).
- TAG: **BUILD-PAST** (borrow: learned trigger + latent-token read interface, layered on a persistent store).

### TransformerFAM: Feedback Attention Memory (2404.09173, Google, 2024)
- Thesis: Feedback loop lets attention attend to its own latent state = working memory.
- SUBSTRATE: **latent feedback state** (no new weights; reuses attention). Working memory, not long-term.
- WRITE/READ: fixed architectural feedback; nothing persisted across sessions.
- Fit: working-memory scope; not a consolidatable long-term store.
- TAG: **CONTEXTUAL.**

### Latent Recurrent Transformer (2605.26797, 2026)
- Thesis: Reuse prior-token high-level hidden state as recurrent memory (+0.3% params).
- SUBSTRATE: **recurrent latent pathway** (compressed hidden state carried across positions).
- WRITE/READ: fixed architectural recurrence; no separate store, no forgetting op.
- TAG: **CONTEXTUAL** (efficiency trick, not a memory substrate we can imprint).

### Recurrent Memory Transformer (2207.06881) & Infini-attention (2404.07143)
- RMT: **special memory tokens** passed segment-to-segment (recurrent read/write via the tokens; fixed rule). CONTEXTUAL.
- Infini-attention: **compressive associative matrix** inside each attention head — a bounded fast-weight matrix with a **delta-rule write** and linear-attention read, unbounded context at fixed memory. The bounded-matrix + delta-rule write is a **real fast-weight interference substrate** (borrowable), but it's fused per-head into the backbone, not a separable module.
- TAG: RMT = CONTEXTUAL; Infini-attention = **BUILD-PAST** (delta-rule bounded-matrix write is the same math family as Titans/Larimar).

---

## Ranked shortlist (fitness as OUR small separate parametric memory net)

| Rank | Substrate | (a) attn-weighted imprint | (b) capacity-limited interference forgetting | (c) measurable in isolation | Tag |
|---|---|---|---|---|---|
| 1 | **ATLAS / Titans neural memory module** (deep MLP fast-weights) | **Native** — surprise/window gate = salience weight on a gradient (post-training) write | **Native** — adaptive decay gate + fixed-capacity superposition | **Good** — standalone module, query without backbone | CANDIDATE |
| 2 | **Larimar** (Kanerva associative matrix) | Partial — one-shot solve, salience via write-strength scalar | **Native+cleanest** — fixed-slot superposition + explicit selective-forget | **Excellent** — encoder/matrix/decoder fully separable | CANDIDATE |
| 3 | **MemoryLLM / M+** (latent memory pool) | Partial — fixed self-update rule | Good — documented forgetting curve; retriever patches collapse | Good but **heavy (~1B)** — likely over budget | CANDIDATE |
| 4 | **Infini-attention** (bounded delta-rule matrix) | Partial — delta-rule write, no salience gate | Good — bounded matrix interferes by design | Poor — fused per-head into backbone | BUILD-PAST |
| 5 | **Memory3** (sparsified explicit KV) | No — offline encode, no imprint | No — DB deletion, not superposition | Good, but it's a **RAG-family baseline** | CONTEXTUAL/baseline |

(Below the line, measure-against baselines: Memorizing Transformers, LongMem, MemoRAG, Compressive/XL, RMT, TransformerFAM, MemGen, Latent-Recurrent.)

---

## RECOMMENDATION

**Top choice: a Titans/ATLAS-style neural fast-weight memory module — a small separate deep-MLP memory net with a gradient-based, salience-gated write and an adaptive decay (forgetting) gate.**

Reasoning against our three requirements:
- **(a) Attention-weighted imprinting during sleep is the module's native write semantics.** Titans/ATLAS already write via *gradient descent on an associative loss weighted by a surprise/salience signal* — which is exactly "attention-weighted post-training of a small parametric net." Our sleep procedure is a re-scheduling of this online rule into a **batched** update over a session's episodic buffer, with our attention weights replacing (or multiplying) the surprise gate. **Use the ATLAS Omega-rule (window/batch) variant, not vanilla Titans**, precisely because ATLAS was built to memorize a *context window* rather than one token — matching a sleep batch.
- **(b) Capacity-limited interference is built in twice over:** a fixed-size MLP stores associations in superposition (adding memories past capacity degrades weak ones first = detail washes out, structure survives), and the explicit adaptive **decay/forgetting gate** gives a tunable knob = our "salience bottleneck" hyperparameter (how many structural nodes survive per episode).
- **(c) Isolation measurement is clean:** the memory M is a standalone module; probe recall by querying M directly, independent of the frozen thinking model, and plot recall-vs-#items and structure-vs-detail retention as capacity/decay vary. Reports directly against filled-context / RAG / LoRA-memory at matched parameter budget.

Why over the LoRA-on-frozen-model option (the other framing in the project brief): a Titans-style module is a **separate** net (requirement met by construction), whereas a LoRA adapter is entangled with the backbone and cannot be read/measured in isolation — you can't cleanly separate "what the memory holds" from "what the base model does," which breaks requirement (c) and muddies the interference story. Keep LoRA-memory as one of the *baselines* you beat, not the substrate.

**Backup: Larimar's Kanerva associative memory matrix.** Adopt this if the gradient-based write proves unstable at sleep-batch scale or if you want the *cleanest possible interference-as-forgetting demonstration*. Its fixed-slot matrix makes capacity-limited interference mathematically transparent (superposition + least-squares write), it ships with an explicit selective-forget operator, one-shot writes are far cheaper than gradient post-training (fast sleep phase), and encoder/matrix/decoder are fully separable for isolated measurement. The trade-off is (a): a one-shot least-squares solve is not "post-training," so attention weighting enters as a per-item write-strength scalar rather than a salience-scaled gradient — slightly weaker fit to the paper's "attention-weighted post-training" framing, but a strong fallback and an excellent second substrate for an ablation ("gradient-imprint vs. one-shot-imprint").

**Discard as substrate (keep as baselines):** all external-KV / retrieval memories (Memory3, Memorizing Transformers, LongMem, MemoRAG) — they forget by deletion/eviction, not superposition, and are the RAG family we measure against. Discard pure latent/recurrent memories (MemGen, TransformerFAM, Latent-Recurrent, RMT) as the store — no persistent, capacity-limited, imprintable parametric state — though MemGen's learned trigger + latent-token read interface and Infini-attention's bounded delta-rule matrix are worth borrowing on the read/write side.

---

## Sources
- [Titans (2501.00663)](https://arxiv.org/abs/2501.00663) · [ATLAS (2505.23735)](https://arxiv.org/abs/2505.23735) · [Larimar (2403.11901)](https://arxiv.org/abs/2403.11901)
- [Memory3 (2407.01178)](https://arxiv.org/pdf/2407.01178) · [M+ (2502.00592)](https://arxiv.org/abs/2502.00592) · [MemGen (2509.24704)](https://arxiv.org/abs/2509.24704)
- [Latent Recurrent Transformer (2605.26797)](https://arxiv.org/abs/2605.26797) · [Recurrent Memory Transformer (2207.06881)](https://arxiv.org/pdf/2207.06881)
- Classics: Transformer-XL (1901.02860), Compressive Transformer (1911.05507), Memorizing Transformers (2203.08913), LongMem (2306.07174), Infini-attention (2404.07143), TransformerFAM (2404.09173), MemoRAG (2409.05435)
