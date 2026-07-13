# Ranked Reading List (skimmable)

Tags: **CITE-FOIL** = frame our contribution against it · **DIFFERENTIATE** = concurrent, must distinguish · **BUILD-ON** = reuse mechanism · **BASELINE** = in our comparison table · **GAP** = names the hole we fill · **CONTEXT** = know the shape, no deep read.

Verdict column: 🔴 read closely · 🟡 skim + cite · ⚪ context only.

---

## TIER 1 — load-bearing for B's design (know these cold)

| # | Paper (ID) | One line | Role | V |
|---|---|---|---|---|
| 1 | **PEAM** (2605.27762) | Parametric embodied memory (MoE-LoRA) + governs when/what to consolidate | DIFFERENTIATE — closest *system* | 🔴 |
| 2 | **Auto-Dreamer** (2605.20616) | Learned offline "dreaming" consolidation, CLS-inspired, ALFWorld/ScienceWorld | DIFFERENTIATE + BASELINE-to-beat | 🔴 |
| 3 | **EVAF / Memory Depth** (2606.26806) | Explicit keep-parametric vs discard-to-retrieval split; declares forgetting unsolved | DIFFERENTIATE + GAP-ammo | 🔴 |
| 4 | **ATLAS / Titans** (2505.23735 / 2501.00663) | Small fast-weight memory, salience-gated gradient write, decay gate | BUILD-ON — **our substrate** | 🔴 |
| 5 | **SCM: Sleep-Consolidated Memory** (2604.20943) | NREM proportional synaptic downscaling + REM recombination + importance tags | BUILD-ON — richest donor (detail-down primitive) | 🔴 |
| 6 | **Larimar** (Kanerva assoc. matrix) | Fixed-slot superposition + one-shot write + explicit forget op | BUILD-ON — backup substrate / ablation arm | 🟡 |
| 7 | **Transformers are Stateless DNCs** (2026) | Proves transformer memory is write-once + stateless | CITE-FOIL — the formal boundary we cross | 🟡 |
| 8 | **Dreamer V1–V3** | Actor-critic via imagination; λ-returns | BUILD-ON — value = consolidation weight | 🟡 |
| 9 | **What Model Does MuZero Learn?** (2306.00840) | Learned value only valid near data-policy; degrades off-policy | CITE-CAUTION — non-stationarity risk | 🟡 |
| 10 | **Experience Compression Spectrum** (2604.15877) | Names the "Missing Diagonal" (structure-up/detail-down); builds nothing | GAP — cite for the hole | 🟡 |
| 11 | **Modular Memory is the Key** (2603.01761) | 24-author position: learned when/what-to-consolidate is open | GAP — cite for open problem | 🟡 |

## TIER 2 — shape the comparison + framing

| # | Paper | One line | Role | V |
|---|---|---|---|---|
| 12 | **Neural Attention Memory** (2023) | Attention as one read+write QKV memory op (outer-product imprint) | BUILD-ON — unify read/write | 🟡 |
| 13 | **Associative Transformer** (2023, CVPR'25) | GWT top-k write into low-rank memory + Hopfield read | DIFFERENTIATE — online vs our offline | 🟡 |
| 14 | **Coordination / Shared Global Workspace** (2021) | Modules compete via attention → broadcast; capacity bottleneck | BUILD-ON — control-plane ancestor + framing | 🟡 |
| 15 | **CLIN** (2310.10134) | Causal-abstraction textual memory, no weight updates, same env family | BASELINE — non-parametric structure | 🟡 |
| 16 | **Mem0** (2025) | Production RAG memory, small active bank | BASELINE — strong RAG bar | ⚪ |
| 17 | **Remembering Transformer** (2024) | Mixture-of-adapters + novelty routing | BASELINE — parametric/CL analog | ⚪ |
| 18 | **A-GEM** (2018) / **EWC** (2017) | Gradient-projection / Fisher weight protection | BASELINE — classical CL | ⚪ |
| 19 | **Anatomy of Agentic Memory** (2602.19320) | Memory results fragile to judge/backbone/scale | METHODOLOGY — eval traps | 🟡 |
| 20 | **LifelongAgentBench** (2505.11942) | Naive replay fails for LLM agents; interdependent tasks | METHODOLOGY + complementary bench | 🟡 |
| 21 | **SleepGate / Learning to Forget** (2603.14517) | Learned forgetting gate on KV cache | BUILD-ON — gate existence proof | ⚪ |
| 22 | **EfficientZero V2** / **Policy Consolidation** (2019) | Value-prefix for sparse reward / KL-bounded policy drift | BUILD-ON (Paper A) — delayed-credit + non-stationarity fix | ⚪ |

## TIER 3 — historical context (know the shape only)

| # | Paper | One line | V |
|---|---|---|---|
| 23 | **Neural Turing Machine** (2014) / **DNC** (2016) | Original attention-addressed external R/W memory | ⚪ |
| 24 | **Complementary Learning Systems** (1995) | Fast hippocampus trains slow cortex — the biological spine | ⚪ |
| 25 | **Voyager** (2023) | Minecraft skill-library, continual improvement, no weight updates | ⚪ |
| 26 | **MuZero** (2019) | Value-equivalent latent model + MCTS (defer MCTS to Paper A) | ⚪ |
| 27 | **MemGPT / Generative Agents / Reflexion / ExpeL** | Agent-memory canon (external-managed, no learned consolidation) | ⚪ |

---

## The competitive picture in one paragraph

The orbit tightened: **PEAM, Auto-Dreamer, EVAF, SCM** are all 2026 and all close — parametric/offline consolidation for agents is now an active race, not an empty lane. Our wedge survives but is **narrow and must be defended crisply**: (1) consolidation explicitly biased **structure-up / detail-down** (others blob-compress or split goal-vs-fact), driven by **value/attention-weighted imprinting**; (2) the **ground-truth dependency-graph measurement** — our strongest unique asset, because *nobody else can even measure* structure-vs-detail retention. EVAF literally declares forgetting unsolved; the Missing Diagonal paper names the exact gap and builds nothing. So the hole is real — but we're now racing 4 concurrent groups to fill it, and the ground-truth-graph eval is the moat.
