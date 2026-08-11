# 21 — Compute precedents: what comparable projects actually used

- Date: 2026-08-10
- Purpose: ground our compute budget in reported/inferable numbers from the closest published
  projects (RL-trained memory writing, offline consolidation, memory benchmarks) plus open GRPO/PPO
  reproduction folklore. Where a paper does not report compute, the estimate is marked **[est]** and
  the inputs used are stated.
- Method note: numbers pulled from arXiv HTML/PDF appendices and GitHub repos, Aug 2026.

---

## 1. Main precedent table

| Project | Model size | Training method | Episodes / steps | Hardware | Wall-clock / GPU-hours |
|---|---|---|---|---|---|
| **TMEM** (2606.04536) | Qwen3-4B & 8B (policy itself RL-trained; online LoRA r=6, FFN of last 4 layers) | GRPO on task-outcome reward, stop-grad through online LoRA; online SFT LR 5e-4, 5 epochs, batch 16 | **200 GRPO steps**, batch 64, n=8 rollouts/prompt, LR 1e-6, ≤1024 resp tokens → **~13k–102k rollouts [est]** (batch convention ambiguous) | **Not reported.** Eval on ≥80 GB-class GPUs (baseline peaks 78.5 GB) | **Not reported.** [est] ~100–400 H100-h: 4B/8B model, ~10⁴–10⁵ short rollouts, no env in loop |
| **Auto-Dreamer** (2605.20616) | Qwen3-14B consolidator (trained); frozen Qwen3.5-9B task agent; Qwen2.5-3B embedder | GRPO (verl + OpenTinker), KL β=1e-3, LR 1e-6, counterfactual-drop reward shaping | **200 steps**, batch 16, group N=8 → **~25.6k consolidator rollouts**; trained on ScienceWorld only (3,604 train tasks, ≤50 env steps/ep), zero-shot to ALFWorld/WebArena | **8× H100 80GB** (train); 4× GH200 96GB (eval, all endpoints) | Wall-clock **not reported.** [est] ~300–900 H100-h: 14B, ≤18k-token responses, + frozen-9B reward rollouts (reward eval likely dominates) |
| **D-MEM** (2603.14597) | GPT-4o-mini (API, frozen) | **NONE — training-free.** "Critic router" = embedding z-score surprise × prompted utility classification (JSON-schema call); heuristic thresholds 0.3/0.7 | n/a | n/a (API only) | **$0 training.** Eval: ~319K tokens for LoCoMo (199 Qs); >80% token reduction claimed |
| **PEAM** (2605.27762) | Qwen3-VL-8B frozen + 3 category LoRAs (r=32, ~83M each) + DistilBERT router | BC + contrastive DPO (λ=1.0, β=0.1), LR 2e-4 | **100 steps × eff. batch 16** per consolidation; ~80 failure trajectories logged (success count not reported) | Single **A100 80GB** (serving; 3.2 s/call median) | Training time **not reported.** [est] ≤ a few A100-hours per consolidation — tiny |
| **Memory-R1** (2508.19828) | LLaMA-3.1-8B / Qwen2.5-7B (3B/7B/14B scaling study) | PPO **and** GRPO (verl); actor/critic LR 1e-6/1e-5; 4096/2048 prompt/resp | **152 training QA pairs** (!), batch 128; total steps not reported | **4× H100** (8× for 14B) | **Not reported.** [est] O(10–100) H100-h given 152 samples, few hundred verl steps |
| **Mem-α** (2509.25911) | Qwen3-4B memory agent | GRPO (verl), QA-accuracy reward | **562 training instances**, batch 32, rollout n=8, **205 steps**; sequences ≤30K tokens | **32× H100** | **~3 days ≈ 2,300 H100-hours** — the only fully-reported figure in this set |
| **MemRL** (2601.03192) | GPT-4o/-mini, Gemini-3-Pro (all frozen APIs) | **No gradient training** — per-memory-item Q-values via Monte-Carlo EMA at runtime | 10 epochs over BigCodeBench/ALFWorld/LAB/HLE (counts unstated) | n/a (API) | **$0 GPU training**; cost = inference tokens only |

Sources: [TMEM](https://arxiv.org/html/2606.04536v1) · [Auto-Dreamer](https://arxiv.org/html/2605.20616v1) · [D-MEM](https://arxiv.org/html/2603.14597v1) · [PEAM](https://arxiv.org/html/2605.27762v1) · [Memory-R1](https://arxiv.org/html/2508.19828) · [Mem-α](https://arxiv.org/html/2509.25911) · [MemRL](https://arxiv.org/html/2601.03192v1)

**Corrections to our earlier mental model** (matters for baseline selection):
- D-MEM's "critic router" is **training-free** (heuristic + prompt). It costs nothing to train and is
  therefore a mandatory cheap baseline for our learned head — if we can't beat a $0 heuristic gate,
  the head is dead.
- MemRL trains no weights either (Q-table over memory items). Same implication.
- TMEM uses **GRPO**, not vanilla PG as note 16 assumed.
- The *entire field's* trained-memory runs are small: 152–3,604 training items, 100–205 update
  steps. Nobody is doing 10⁶-episode RL. Mem-α's 2,300 H100-h is the ceiling, and it's inflated by
  full-model GRPO on 30K-token sequences.

---

## 2. What running a memory benchmark costs

| Benchmark | Models in the eval | Scale | Reported cost |
|---|---|---|---|
| **eMEM-Bench** (2606.03374) | Qwen 3.6-27B agent+extractor, gemma3:27b judge, local embeddings via Ollama — "no proprietary APIs" | **988 probes**, 8 paradigms, 20 ProcTHOR scenes; ≤5 ReAct steps/probe; retention curve = 480 probes × 6 delays | No $/GPU-h. Systems numbers on **1× RTX A5000** (ingest 0.6–2.6k obs/s; ≤223 MiB @10⁵ obs). [est] single-digit GPU-days, $0 API |
| **MemTrace** (2606.17328) | 13 configs / 4 paradigms; gpt-4o-mini generator, **GPT-4o judge** | 20 users, 835 knowledge points, 5,677 base probes, **200,453 scored answers**, 8 checkpoints/user | **Not reported.** [est] hundreds of $ API per full sweep (200k judged answers) |
| **ForgetBench** (2607.26455) | Llama-3/3.1-8B, Qwen2.5-7B, DS-R1-7B (all local); knowledge-editing only | 6,431 questions; edit sequences to T=500, eval every 10 steps | **4× RTX 4090** reported; runtime not. [est] days-scale on that box |
| (context) LoCoMo / LongMemEval | API models | ~9K tok/conv · 500 Qs, ~115K tok/instance | Never reported |

**Field norm: nobody reports eval dollars/GPU-hours** — probe counts and sometimes hardware only.
Two of three run entirely on local open models (consumer/workstation GPUs). Implication for our
benchmark: a full multi-backend sweep is a **workstation-GPU workload plus at most a few hundred
dollars of judge API** — and reporting cost/latency per backend would itself be a differentiator
(only LongMemEval-V2 scores latency).

---

## 3. GRPO/PPO folklore, 1.5B–8B agent tasks

| Data point | What's reported | Take-away |
|---|---|---|
| **Search-R1** (2503.09516) | Qwen2.5-3B/7B, **8× H100**, 500 steps, batch 512, 5 rollouts/prompt (~1.3M rollouts), 4k ctx. Wall-clock unreported | [est] 1–3 days on the node ≈ **200–600 H100-h**, inflated by retrieval-server latency |
| **AgentGym-RL** (2509.08755) | Qwen2.5-3B/7B on A100s + Ascend 910B; GPU count/time unreported; e.g. WebArena 372 queries × 4 trajs, 15 turns | Env throughput, not FLOPs, was their bottleneck (parallel-rollout engineering emphasized) |
| **OpenRLHF** (2405.11143, Tbl 2) | LLaMA2-7B PPO, **16× A800: 1,024 prompts/epoch in 471 s** | ≈ **2 GPU-h per 1k short rollouts** — the optimistic floor |
| **simpleRL-reason** | 7B: **2×8 H100, ~100 steps ≈ 15 h** (~240 H100-h) on 8K examples; 32B: ~2,300 H100-h | Best-documented "one paper-grade 7B GRPO run" anchor |
| **TinyZero** | Qwen2.5-3B countdown R1-Zero: **< $30 on 2× H200**; 1 GPU suffices ≤1.5B | ~10–20 GPU-h — a credible-prototype exists at this scale |
| **Logic-RL** (2502.14768) | 7B, 3,600 steps, ~5K problems; repo: **4× A100 80G** | 4×80GB is the observed floor for 7B full-model RL |
| **RAGEN** (2504.20073) | Main results **0.5B**, ≤200 iters × (8 prompts × 16 trajs) ≈ 25.6k trajectories; **7B OOM'd on 4× H100** (WebShop) | Multi-turn agent RL at 7B full-model wants a full 8-GPU node |
| verl docs | 7B GRPO examples assume one 8-GPU node; GRPO-**LoRA** 7B runs at batch 64 on 8 GPUs | LoRA/head-only training relaxes the hardware quantum substantially |

**Consensus [synthesis, not reported]:** ~**5–20 H100-h per 1k rollouts** for 7B GRPO at 4–8k
tokens/episode (2 GPU-h/1k floor for short episodes), **×2–5 when a live environment sits in the
rollout loop**. Standard quantum = one 8×H100 node; a "small" published 7B run ≈ 200–800 H100-h ≈
**$500–2,500** at ~$2.50/H100-h spot.

---

## 4. Bottom line for OUR project — three tiers

Our structural advantage over every precedent above: **the 7B backbone is frozen and only a small
head + fast-weight memory take gradients.** No FSDP training node, no actor/critic sharding — the
run is *rollout-inference-dominated* (vLLM serving), and our env (crafting-sim text world) is local
and fast, unlike WebArena/search-in-the-loop. So we should land well below Search-R1/Mem-α.

**Assumptions (all tiers):** $2.50/H100-h spot (A100 ~$1.20–1.80); vLLM 7B bf16 batched throughput
~2–4k gen-tok/s per H100; episodes ~2–4k generated tokens; head/fast-weight updates negligible
FLOPs next to rollouts; GRPO-style group 8, 100–300 update steps (field norm, §1); env step cost ~0.

### Tier (a) — CPU-only abstract prototype (no LLM)
Set-retention + logistic-value model (exp0–exp3, `structmem_bench`) — **already built and run.**
20 seeds × budget/scale sweeps × 8 methods = minutes–hours on a laptop; full M2 package with 3
curriculum orderings ≈ **< 1 CPU-day, $0 GPU.** This is the reproducible core; precedent (D-MEM,
MemRL) shows training-free/abstract tiers are publishable components.

### Tier (b) — minimum credible LLM prototype (smallest model, one environment)
- Setup: Qwen2.5-1.5B or Qwen3-4B frozen backbone, one crafting-sim env, head + fast-weight memory
  trained on ~5k–20k episodes, retention probes on ~1–2k questions, 3 seeds, 2–3 baseline
  conditions (no-memory, RAG, heuristic-gate).
- Anchors: TinyZero (<$30, 2 GPUs, 3B, full-model); RAGEN (0.5B, 25.6k trajectories, few GPUs);
  PEAM consolidation (~hours). Head-only makes us cheaper per step than all of these.
- **Estimate: 1× A100/H100 80GB (a 48GB card works at 1.5B), ~50–150 GPU-hours ≈ $100–400,
  ~3–7 days wall-clock on one GPU.** Fits a single workstation or one cluster GPU lease.

### Tier (c) — workshop-paper-grade full run (7B, multiple baselines, seeds)
- Training: frozen 7B, head-RL on ~30k–100k episodes. Rollout math: 50k eps × 3k tok ≈ 1.5×10⁸
  gen tokens ≈ 15–25 H100-h per run; × 3 seeds × ~5 learned conditions (ours + ablations:
  per-item value, no-sleep, surprise-gated, random-gate) ≈ **250–450 H100-h**.
- Baselines: RAG/text-bank/full-context/D-MEM-style are inference-only ≈ 50–100 H100-h. A
  TMEM-style or Auto-Dreamer-style trained baseline, if reimplemented *head-only or LoRA-only*,
  adds ~100–200 H100-h (skip full-model GRPO reproduction — that alone is a Search-R1-sized 200–600
  H100-h line item; cite instead).
- Benchmark sweep (memory-type-agnostic harness, MemTrace-scale ~5k probes × ~10 backends × age
  checkpoints, local 7–8B judge): **~50–150 GPU-h**, or ~$200–500 API if using a judge model.
- **Total: ≈ 500–1,000 H100-hours ≈ one 8×H100 node for 3–5 days ≈ $1,300–2,600 spot.**
  Sanity check: below Mem-α (2,300 H100-h, full-model 4B GRPO at 30K tokens) and in the
  simpleRL/Search-R1 band despite more conditions — consistent with frozen-backbone savings; the
  DESIGN_DOC §12 claim ("fits comfortably in one cluster lease") holds.

**Biggest risk to these numbers:** episode length. If retention probing requires long multi-episode
streams *in context* during training rollouts (Auto-Dreamer hit 18–21K-token sequences), token
counts — and cost — scale linearly with it. Keeping wake-phase context short (that's the whole
point of the parametric memory) is also the cost-control mechanism.
