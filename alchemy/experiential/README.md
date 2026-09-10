# Recurrent continual experiential learning — V0

This is a **new experiment**, separate from the text-recurrent LANDS controller
and the frozen Paper 1 protocol. It tests the supplied hypothesis:

> Experience changes local expert transformations; those changes alter future
> latent recurrent computations and may compose on unseen tasks.

The runnable V0 uses dense Qwen2/Qwen2.5 decoder layers with explicit banks of
routed low-rank residual experts in the recurrent MLPs. It does not implement
native MoE V1 or claim that experts acquire human-readable procedures.

## Run with uv

From the repository root:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r alchemy/experiential/requirements.txt
uv run --python .venv/bin/python python -m pytest alchemy/experiential/test_experiential.py -q
uv run --python .venv/bin/python python -m alchemy.run_experiential_v0 \
  --smoke --output-dir outputs/experiential_smoke
```

The smoke test creates a tiny **randomly initialized Qwen2** locally. It requires
no model download or API key. Its few copy-task foundation/retrofit updates
exercise the code; its scores are **not evidence for the research hypothesis**.
Use a fresh output directory for each run: existing seed artifacts are protected.

A longer CPU instrument run:

```sh
uv run --python .venv/bin/python python -m alchemy.run_experiential_v0 \
  --seeds 0 1 2 --steps 200 --cycles 3 \
  --depths 1 2 4 8 16 --output-dir outputs/experiential_tiny
```

A pretrained experiment (downloads weights; CUDA recommended):

```sh
uv run --python .venv/bin/python python -m alchemy.run_experiential_v0 \
  --model Qwen/Qwen2.5-0.5B-Instruct --device cuda \
  --seeds 0 1 2 --rank 8 --experts 8 --top-k 2 --plastic-experts 2 \
  --retrofit-steps 200 --steps 500 --cycles 3 --train-loops 4 \
  --depths 1 2 4 8 16 --output-dir outputs/experiential_qwen
```

Pass `--revision <commit>` to pin model weights. The resolved model commit and
installed package versions are recorded. Decoder calls are tied to
[transformers 4.57.6 Qwen2](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/models/qwen2/modeling_qwen2.py).
Only dense Qwen2-family checkpoints with full causal attention are supported.
All commands above run Python through `uv`.

## Implemented mechanism

- **P → R^T → C:** one shared core, with actual residual attention, normalization,
  positional embeddings and causal masking. No cache is reused between passes;
  every pass recomputes attention. Token positions are unchanged across depth.
- **Re-entry:** the first pass uses `h0` directly; subsequent passes mix current
  state with `bridge(h0)` using a sigmoid gate. Before retrofit, the one-pass
  path equals the original model because all low-rank output factors are zero.
- **Two adapter timescales:** each core MLP has a slow recurrence adapter and an
  independent bank of plastic low-rank residual transformations. The latter
  implements `MLP_base(u) + recur(u) + sum_e p_e B_e A_e u / rank`.
  Only selected experts execute. Expert IDs are `(absolute_layer, expert)`.
- **Retrofit:** train only recurrence adapters, bridge, gate, and routers on a
  separate copy-task substrate corpus, with initial one-pass KL preservation
  and routing balance. Then freeze them. The tiny model first gets foundation
  training on that corpus; pretrained base weights never receive this update.
- **Online collection:** read-only closed-action inference, epsilon exploration,
  and public environment feedback. Records contain action, observation, reward,
  version, prompt, hidden-state summaries and per-pass/token routing weights.
- **Offline consolidation:** deduplicate interaction IDs, reject inconsistent or
  insufficiently repeated outcomes, emphasize prediction errors and observed
  recovery. Targets come only from witnessed final states. No latent rule table
  or transfer answer is accessible to the consolidator.
- **Eligibility:** average selected, renormalized routing weights across tokens,
  recurrent passes and repeated episodes. Apply a threshold and per-layer cap.
  Masks are derived from the *recorded prompt*, never from teacher-forced target
  token routing. Replay retains its original source masks and provenance.
- **Credit:** full BPTT through the actual recurrent model. Ineligible expert
  weights are detached while gradients through their input states still flow.
  There is no hidden-state truncation and no activation-only credit rule.
- **Consolidation loss:** new outcome CE + prior-cycle replay CE + old-model KL
  on unrelated prompts + normalized recurrent state MSE on those prompts +
  group norm of this cycle's adapter displacement. Answer-only labels mask all
  prompt tokens. KL direction is `KL(old || new)`; the teacher is the preceding
  version, not the foundation model.
- **Hard update isolation:** the optimizer contains only experiential parameters;
  ineligible gradients become `None`, preventing Adam momentum from moving them.
  Each cycle has a fresh optimizer, while experiential weights persist. Nonfinite
  loss or gradients roll back that cycle. Stable weights are checksummed.
- **Versioning:** save the shared substrate once and each arm's plastic state
  every cycle. Loading verifies topology and the frozen substrate identifier.

The bridge and pretrained expert weights are distinct from each expert's LoRA
`B` factor, despite the overlapping notation in the architecture brief.

## Environment and experimental controls

A state digit is transformed by a sequence of three named operations. Each
operation is a world-specific hidden permutation. An interaction asks the agent
to predict the final state, then reveals the actual final state and success or
failure. This is an informative-feedback transition environment, **not** a
binary-reward-only or multi-action tool-use benchmark.

Experience covers single operations and six of the nine ordered two-operation
combinations. Three entire ordered pairs and **every** length-three/four
composition are held out. The same held-out sample and world are used for all
arms. No experience text is retrieved at evaluation; only the task is supplied.
The tiny copy-task substrate never sees the world's rules.

| Arm | Inference depth | Experiential writes |
| --- | --- | --- |
| Base | 1 | None |
| Recurrent | T | None |
| Experiential one-pass | 1 | Train at T=1 |
| Experiential recurrent | T | Train at `--train-loops` |

All four arms share the same frozen, retrofitted substrate. Thus “base” means
**one-pass shared-substrate control**, not an untouched pretrained checkpoint.
Extra evaluations of the one-pass-trained adapter at T>1 are diagnostic; the
factorial interaction always uses its T=1 score:

`I(T) = ER(T) - R(T) - E(1) + Base(1)`.

The trained recurrent adapter is swept at 1, 2, 4, 8, 16 passes. Depths exceeding
retrofit/experiential training depths are explicitly extrapolation. Positive
interaction or monotonic depth gains are hypotheses, never pass conditions.
Per-depth task scores, cycle histories, unrelated copy accuracy, learned-task
retention, route weights and state norms remain inspectable in JSON.

Default arms have equal update counts and experience exposures, so recurrent
writes cost more. `--match-write-compute` gives the one-pass arm extra optimizer
steps to match core-pass counts; data touches and P/C compute then differ.
Reports include optimizer steps, training core/token passes and teacher passes.
Neither mode alone is a total-FLOP-matched causal test; use both and report their
budgets. Seed means are descriptive, not confidence intervals.

Mechanistic probes zero individual expert adapters selected by parameter-change
magnitude, run a one-expert least-changed control, and roll all experiential
weights back to initialization. Scores and answer-token routing per layer/pass
are saved for each intervention. These interventions test causal contribution;
selective collapse or procedural composition must be established from results,
not inferred from the mere existence of an adapter or a changed route.

## Artifacts and restoration

Each seed directory contains:

- `substrate.pt`, `initial.pt`, and per-arm/per-cycle adapter checkpoints;
- `split.json` with the committed task split (no private rule tables);
- episode JSONL with full provenance, observations and routing traces;
- accepted consolidation examples with source IDs and eligibility masks;
- `report.json` with loss components, evaluations, ablations and frozen hashes.

`summary.json` aggregates the interaction across seeds. Raw artifacts under
`outputs/` are ignored by git. Restore a saved version in Python invoked via uv:

```python
from alchemy.experiential.learning import restore_substrate, load_plastic

model = restore_substrate("outputs/experiential_smoke/seed_0/substrate.pt")
load_plastic(
    model,
    "outputs/experiential_smoke/seed_0/experiential_recurrent_v2.pt",
    model.stable_digest(),
)
```

For pretrained checkpoints, load the tokenizer saved alongside the substrate
and construct `Codec(tokenizer)`. The tiny codec uses ASCII directly. Serving
uses `model(input_ids, loops=T)`; this wrapper does not expose cached generation.

## Scope and next gates

This V0 implements outcome-supervised consolidation, not a learned abstraction
extractor or reward-only credit assignment across external actions. Its tiny
substrate and copy-only retrofit/preservation corpus are deliberately narrow;
pretrained competence, recurrence stability on general language, and procedural
transfer require broader substrate/preservation data and substantive runs.
There is no automatic performance-based promotion gate or online parameter
write. High-depth full BPTT is memory-intensive; this implementation favors
inspectable correctness over optimized training throughput.

Before claiming the stronger architecture result: establish a capable recurrent
substrate; run multiple world seeds and matched-budget controls; show transfer
on unseen compositions; show selective ablation effects with unrelated behavior
retained; and distinguish gains from extra training/inference compute. Native
MoE expert adapters, learned episode abstraction, router plasticity, and
multi-action agent environments are subsequent experiments.
