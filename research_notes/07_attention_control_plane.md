# 07 — Attention as a Control Plane / Router Between Modules and Memory

**Cluster goal:** trace the architectural ancestry of our core thesis — *attention as
general compute-allocation, extended beyond the transformer's own inputs to external
memory + policy + context*. Paper 1 (B) = sleep-time consolidation writing an
attention-weighted small parametric memory net (structure-up / detail-down). Paper 2 (A)
= make that attention **learned/live** and unify **read** (context composition) + **write**
(consolidation) into ONE external→internal attention "control plane."

Tags: **BUILD-ON** (mechanism we extend) / **BUILD-PAST** (limitation we supersede) /
**CONTEXTUAL-HISTORY** (cite for lineage, not load-bearing).

---

## TIER 1 — True architectural ancestors of "attention as control plane"

These three ARE the lineage of routing-by-attention across modules/memory. Flag in intro.

### 1. Coordination Among Neural Modules Through a Shared Global Workspace (2021) ★ANCESTOR
- **Thesis:** Modules compete via attention to write a shared bottleneck workspace, then read it back.
- **WHY WE CARE:** This is the cleanest prior instantiation of our "control plane": a
  limited-capacity shared workspace that specialized modules write to (attention-gated
  competition) and broadcast-read from. Our read+write control plane is a
  memory-persistent, currency-weighted generalization of this selection–broadcast loop.
- **TAG:** BUILD-ON.
- **Mechanism:** Each module produces key/query/value; top-k **write competition** selects
  which modules update the fixed-size workspace slots; workspace is **broadcast-read** by
  all modules next step. Capacity limit = the interference/compression bottleneck — directly
  analogous to our capacity-limited memory net where weakly-imprinted detail washes out.
- arXiv 2103.01197.

### 2. Differentiable Neural Computer (2016) + Neural Turing Machine (2014) ★ANCESTOR
- **Thesis:** A controller reads/writes an external memory matrix via differentiable content-based attention.
- **WHY WE CARE:** The original "attention *is* the read/write addressing into an external
  store." Every design choice we make (content addressing = high-attention imprint;
  allocation/usage weighting = currency; erase+add = consolidation write) has a named
  antecedent here. DNC's usage-based allocation and temporal link matrix are the most
  relevant precedents for *which* memory gets overwritten under capacity pressure.
- **TAG:** BUILD-ON (mechanism) / CONTEXTUAL-HISTORY (framing).
- **Mechanism:** Read/write heads emit key + sharpness → content-based softmax over slots;
  DNC adds **dynamic memory allocation** (usage vector) and **temporal linkage**. Write =
  erase (gate) then add (outer product). NTM = same minus allocation/linkage.
- NTM arXiv 1410.5401; DNC = Graves et al., Nature 2016.

### 3. Recurrent Independent Mechanisms — RIMs (2019/21) ★ANCESTOR
- **Thesis:** Sparse, independently-parameterized modules compete via attention for input and communicate by attention.
- **WHY WE CARE:** Establishes the "many specialized modules + attention decides who is
  active / who exchanges info" pattern that our policy/memory/context control plane routes
  over. The **input-attention competition** (only top-k active modules) is the direct
  precursor to currency/policy-weighted selection of what to consolidate.
- **TAG:** BUILD-ON.
- **Mechanism:** (a) input attention: modules compete for the input, only top-k activate;
  (b) communication attention: active modules read each other. Inactive modules' state is
  frozen — a built-in "detail decay by non-selection" prior we can borrow for sleep.

---

## TIER 2 — Load-bearing mechanisms for read/write-as-one-attention (Paper 2 core)

### 4. Neural Attention Memory — NAM (2023) ★BEST READ/WRITE PRIMITIVE
- **Thesis:** Recast attention itself as a readable+writable memory matrix.
- **WHY WE CARE:** This is the single cleanest formalization of our "one attention op does
  both read and write." Gives us the exact primitive to unify context-composition (read)
  and consolidation (write) under identical QKV algebra — the mathematical backbone for
  Paper 2's unified control plane.
- **TAG:** BUILD-ON (load-bearing).
- **Mechanism:** Memory matrix M. **Write** = M += (unit key ⊗ value) — an outer-product
  imprint. **Read** = M · (unit query) — matrix-vector retrieval; reading with a written key
  returns the most-recent value. Note: linear associative memory, so *interference between
  overlapping keys* is exactly our "capacity-limited detail washout" — free structure/detail
  separation story if keys are relational.
- arXiv 2302.09422.

### 5. Associative Transformer — AiT (2023, CVPR'25) ★LOAD-BEARING
- **Thesis:** Global-workspace layer: bottleneck-attention write to low-rank explicit memory + Hopfield read.
- **WHY WE CARE:** The most complete existing fusion of the two ancestors above — GW
  bottleneck competition (write) + explicit persistent memory + associative (Hopfield)
  broadcast-read. Closest published system to our read+write control plane; primary
  BUILD-ON to differentiate from (we add sleep-time offline consolidation + currency/policy
  weighting rather than purely online per-forward-pass memory).
- **TAG:** BUILD-ON (load-bearing).
- **Mechanism:** top-k **bottleneck cross-attention** (k ≪ tokens) squashes tokens into a
  low-rank explicit memory (write competition); contents **broadcast back** and reconstructed
  via Hopfield associative retrieval (read). Shallow AiT > deeper ViT → evidence the
  bottleneck imposes useful structure-preserving compression.

### 6. Compositional Attention: Disentangling Search and Retrieval (Mittal et al., 2021) ★LOAD-BEARING
- **Thesis:** Decouple *where to look* (search) from *what to retrieve* (value), recombined flexibly.
- **WHY WE CARE:** Directly supports splitting our control plane into "which memory/policy
  to attend" (search) vs "what content to compose/imprint" (retrieval). Justifies a factored
  attention where currency/policy drives search and the value path carries episodic detail —
  the mechanistic seam along which structure survives and detail decays.
- **TAG:** BUILD-ON.
- **Mechanism:** Replaces standard head=fixed(search,retrieval) binding with separate search
  heads and retrieval heads combined by a second ("meta") attention — number of
  search/retrieval pairs decoupled from head count.

---

## TIER 3 — Formal boundary of transformer memory (what we ADD)

### 7. Transformers are Stateless Differentiable Neural Computers (2026) ★BEST "CANNOT-DO" STATEMENT
- **Thesis:** A causal transformer layer = a *stateless, write-once* DNC.
- **WHY WE CARE:** **This is the single best formal statement of what a transformer's memory
  CANNOT do.** Proves the controller has **no recurrent state** and memory is a **write-once
  matrix of value vectors** — i.e. transformers cannot update, consolidate, or overwrite a
  stored memory in place; they only append and re-read within the context window. Our
  architecture adds exactly the missing capability: a **stateful, re-writable, consolidatable**
  parametric memory updated offline. Use this as the formal foil in both papers' intros.
- **TAG:** BUILD-PAST.
- **Mechanism (their equivalence):** (1) controller = no recurrent state; (2) external memory
  = write-once matrix of values; (3) content addressing via keys = attention; (4) multi-head =
  parallel read heads; cross-attention = distinct read-from / write-to memories. The
  "write-once + stateless" pair is precisely the gap we fill.
- arXiv 2603.19272 (Tang & Xie, WPI).

---

## TIER 4 — Context / persistence lineage (cite, mostly not load-bearing)

### 8. TransformerFAM: Feedback Attention is Working Memory (2024)
- **Thesis:** Feed block-level latent state back in as attendable "working memory," no new weights.
- **WHY WE CARE:** Precedent that a transformer can attend to *its own* compressed latent
  state as memory — a mild step toward statefulness, but still in-context/online and
  weight-frozen. Contrast case: we move consolidation OUT of the forward pass into offline
  post-training of a separate net. **TAG:** CONTEXTUAL-HISTORY.
- **Mechanism:** FAM tokens appended to Block Sliding-Window Attention; each block compresses
  global context into FAM and propagates it forward via the feedback loop.

### 9. Recurrent Memory Transformer (RMT) + Memory Transformer (2020)
- **Thesis:** Special [mem] tokens carry a summary across segments (RMT recurs them).
- **WHY WE CARE:** Establishes "dedicated memory tokens written/read by ordinary attention"
  — cheap precedent for a separable memory slot, but memory is transient activations, not a
  consolidated parametric store. **TAG:** CONTEXTUAL-HISTORY.
- **Mechanism:** read/write memory tokens prepended to the sequence; RMT passes them segment
  to segment as recurrent state.

### 10. Compositional Attention Networks for Machine Reasoning — MAC (2018)
- **Thesis:** Recurrent MAC cell separates control (attend to question) from read/write memory.
- **WHY WE CARE:** Early explicit **control ↔ memory ↔ read/write** decomposition — a
  conceptual ancestor of a "control plane" governing memory ops, predating the GW line.
  **TAG:** CONTEXTUAL-HISTORY.
- **Mechanism:** each MAC cell = control unit (attends over question words) + read unit
  (attends over knowledge base, gated by control + memory) + write unit (updates recurrent
  memory).

### 11. Meta Attention Networks (ICLR 2021)
- **Thesis:** Meta-learn attention that modulates info flow among modular mechanisms (RIMs-adjacent).
- **WHY WE CARE:** Precedent for making the routing attention itself *learned/meta-learned* —
  supports Paper 2's "learned, live" control plane. Thin as a standalone contribution.
  **TAG:** CONTEXTUAL-HISTORY (mild BUILD-ON for the "learned router" claim).

### 12. Neural Field Turing Machine (2025)
- **Thesis:** Differentiable spatial computer: controller + continuous memory *field* + movable local R/W heads.
- **WHY WE CARE:** Interesting alternative to slot memory (local updates, O(N), Turing-complete),
  but the spatial-field framing is orthogonal to our compute-allocation thesis. Cite as
  "memory geometry" alternative only. **TAG:** CONTEXTUAL-HISTORY.
- arXiv 2509.03370.

---

## TIER 5 — Peripheral (GWT applications + shared-weight specialization; light cite)

- **Global Workspace Theory and Real-Time AI (2025, Frontiers / arXiv 2505.13969):** argues
  the selection–broadcast cycle gives dynamic/real-time/experience-based adaptation. Useful
  *motivation* prose for why an online control plane helps continual agents; no mechanism to
  build on. **TAG:** CONTEXTUAL-HISTORY.
- **Emergent Specialization in a Shared Recurrent Transformer / "One Model, Two Roles" (2026,
  arXiv 2605.17811):** shared-weight recurrent transformer spontaneously splits into a
  committed "H" proposal state vs a local-uncertain "L" state given an identity signal.
  Relevant analogy: functional roles can emerge in shared params without hard module
  partition — supports doing consolidation in a small *shared* net rather than many modules.
  **TAG:** CONTEXTUAL-HISTORY.
- **Semi-Supervised Multimodal Global Workspace (2023/24):** aligns modalities through a
  shared GW latent; domain-specific, not load-bearing. **TAG:** CONTEXTUAL-HISTORY.
- **Global Workspace Modular Arithmetic (2025):** toy/probing study of GW on modular
  arithmetic; evidence-only, no mechanism. **TAG:** CONTEXTUAL-HISTORY.

---

## Flags requested

- **True architectural ancestors of "attention as control plane":**
  (1) **Shared Global Workspace / Coordination Among Neural Modules (2021)**,
  (2) **DNC/NTM (2016/2014)**,
  (3) **RIMs (2019/21)**. (Runner-up for the *learned/unified* variant: NAM + Associative Transformer.)
- **Single best formal statement of "what a transformer's memory CANNOT do":**
  **"Transformers are Stateless Differentiable Neural Computers" (2026)** — proves
  transformer memory is *stateless and write-once*; our stateful, re-writable, offline-
  consolidated parametric memory is precisely the added capability.
