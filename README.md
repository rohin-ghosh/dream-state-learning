# Dream-State Learning
### Adaptive Memory Consolidation for Continual Agents

A wake–sleep continual learning agent that consolidates experience into three memory types — episodic, semantic, and parametric (LoRA weights) — using a **learned routing policy** trained via meta-learning. Evaluated on 48 sequential tasks across ALFWorld.

---

## Key Idea

Standard continual learning agents either store everything in external memory (expensive retrieval, no weight adaptation) or fine-tune blindly (catastrophic forgetting). Dream-State Learning does both, selectively:

- **Wake phase**: ReAct agent interacts with the environment, recording full trajectories and computing four routing features per episode.
- **Routing policy**: A meta-learned MLP maps `[utility, transfer_potential, retrieval_cost, interference_risk]` to a routing decision: store episodically, distill semantically, or consolidate parametrically via LoRA.
- **Sleep phase**: Episodic entries go to FAISS. Semantic entries get distilled into procedure summaries via the LLM. Parametric entries trigger O-LoRA fine-tuning with orthogonal subspace constraints and a checkpoint accept/revert safety gate.

The routing policy is the central contribution — it implements selective consolidation (Manohar et al., PNAS 2022) rather than uniform reservoir sampling used by all prior wake-sleep systems.

---

## Results (Target)

| Metric | Dream-State | Naive FT | ExpeL | O-LoRA only |
|--------|------------|----------|-------|-------------|
| FGT (↓) | **2.3 pp** | ~18 pp | — | ~6 pp |
| MFN (↑) | **90.4%** | ~71% | ~59% | ~78% |
| BWT (↑) | **+1.1 pp** | −16 pp | — | −4 pp |
| Retrieval tokens (↓) | **−36%** | baseline | baseline | — |

Evaluated on 48 sequential ALFWorld tasks (8 × 6 task types), 3 seeds × 4 curriculum orderings.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Wake Phase                        │
│  ALFWorld env → ReAct loop (Qwen2.5-7B + LoRA)     │
│  → EpisodeResult + TrajectoryFeatures                │
└──────────────────┬──────────────────────────────────┘
                   │ routing features
                   ▼
┌─────────────────────────────────────────────────────┐
│              Routing Policy (MLP)                    │
│  [utility, transfer_potential,                       │
│   retrieval_cost, interference_risk]                 │
│  → EPISODIC | SEMANTIC | PARAMETRIC | NONE           │
└──────┬──────────────┬───────────────┬───────────────┘
       │              │               │
       ▼              ▼               ▼
  FAISS index    SQLite + LLM    O-LoRA fine-tune
  (episodic)     distillation    + accept/revert
                 (semantic)      (parametric)
```

---

## Installation

**Local (Mac/Linux, for development):**
```bash
git clone https://github.com/rohin-ghosh/dream-state-learning.git
cd dream-state-learning
pip install -e ".[dev]"
```

**Cluster (first session — run once after cloning):**
```bash
export HF_TOKEN=<your_hf_token>
export WANDB_API_KEY=<your_wandb_key>
bash setup_cluster.sh
```

`setup_cluster.sh` creates a conda env (`dream-state`), downloads ALFWorld game files, prefetches the Qwen2.5-7B tokenizer, and installs all dependencies. Do **not** hardcode credentials — set them as environment variables only.

---

## Project Structure

```
dream_state/
├── config.py               # Pydantic config system (DreamStateConfig)
├── system.py               # DreamStateAgent — top-level integration
├── agent/
│   └── react_agent.py      # ReAct agent with LoRA adapter management
├── environments/
│   └── alfworld_env.py     # ALFWorldEnv wrapper + curriculum builder
├── memory/
│   ├── episodic.py         # FAISS-backed episodic buffer
│   ├── semantic.py         # SQLite semantic procedure store
│   └── features.py         # Trajectory feature extractor (4 routing features)
├── training/
│   ├── lora_trainer.py     # O-LoRA fine-tuning with orthogonal penalty
│   └── sleep_phase.py      # Sleep phase orchestrator
├── routing/
│   ├── policy.py           # RoutingPolicy MLP + HeuristicRouter baseline
│   └── meta_train.py       # REINFORCE meta-learning for routing policy
└── eval/
    └── harness.py          # 48-task sequential eval harness (FGT/BWT/FWT/MFN)

scripts/
├── run_baselines.py        # Run all baseline methods
├── run_ablations.py        # Run ablation study
└── submit_cluster.sh       # SLURM job launcher

configs/
├── base.yaml               # Default DreamStateConfig
└── alfworld_base.yaml      # ALFWorld environment config
```

---

## Running Experiments

**Baselines:**
```bash
python scripts/run_baselines.py --config configs/base.yaml --baseline naive_ft --ordering blocked
python scripts/run_baselines.py --config configs/base.yaml --baseline frozen_episodic --ordering blocked
python scripts/run_baselines.py --config configs/base.yaml --baseline olora_only --ordering blocked
python scripts/run_baselines.py --config configs/base.yaml --baseline expel --ordering blocked
```

Available baselines: `naive_ft`, `frozen_episodic`, `olora_only`, `random_routing`, `no_sleep`, `ewc`, `expel`

**Ablations:**
```bash
python scripts/run_ablations.py --config configs/base.yaml --ablation no_routing_policy
python scripts/run_ablations.py --config configs/base.yaml --ablation no_orthogonal
python scripts/run_ablations.py --config configs/base.yaml --ablation no_checkpoint_safety
python scripts/run_ablations.py --config configs/base.yaml --ablation full_system
```

Available ablations: `no_routing_policy`, `no_orthogonal`, `no_checkpoint_safety`, `no_semantic_memory`, `no_episodic_memory`, `full_system`

**Dry run (check config without launching):**
```bash
python scripts/run_baselines.py --config configs/base.yaml --baseline naive_ft --dry-run
```

---

## Configuration

All hyperparameters live in `configs/base.yaml`. Key knobs:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lora.rank` | 16 | LoRA adapter rank |
| `lora.orthogonal_lambda_end` | 1.0 | O-LoRA penalty strength (annealed from 0.1) |
| `lora.revert_threshold_bwt` | −0.03 | Revert checkpoint if any task degrades >3 pp |
| `sleep.trigger_every_k_tasks` | 4 | Sleep phase frequency |
| `sleep.min_trajectories_for_lora` | 8 | Min PARAMETRIC trajectories before LoRA fires |
| `routing.meta_lr` | 3e-4 | Routing policy meta-learning rate |
| `memory.episodic_capacity` | 2000 | Max episodic buffer entries |

---

## Evaluation Metrics

| Metric | Meaning | Target |
|--------|---------|--------|
| **FGT** (↓) | Mean forgetting across task types after full sequence | < 2.5 pp |
| **BWT** (↑) | Backward transfer — how much learning a new task improves old ones | > 0 |
| **FWT** (↑) | Forward transfer — how much past learning accelerates new tasks | > 5 pp |
| **MFN** (↑) | Mean final accuracy across all task types | > 90% |

---

## Cluster Setup (NVIDIA Colossus)

After the lease starts and you have SSH credentials:

```bash
ssh <user>@ipp1-1619.ipp1a1.colossus.nvidia.com
git clone https://github.com/rohin-ghosh/dream-state-learning.git
cd dream-state-learning
export HF_TOKEN=...
export WANDB_API_KEY=...
bash setup_cluster.sh
conda activate dream-state
```

Session plan:
- **Session 1 (28h)**: Env setup + baseline runs
- **Session 2 (50h)**: LoRA fine-tuning + sleep phase
- **Session 3 (50h)**: Routing policy meta-training + full eval

---

## Venue Target

**Primary:** NeurIPS 2026 Continual Learning workshop (~Sep–Oct 2026 deadline)  
**Full paper:** ICLR 2027

---

## Citation

```bibtex
@article{ghosh2026dreamstate,
  title={Dream-State Learning: Adaptive Memory Consolidation for Continual Agents},
  author={Ghosh, Rohin},
  year={2026}
}
```
