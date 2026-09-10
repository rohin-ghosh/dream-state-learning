# PCFL-lite code-feasibility advisory

**Date:** 2026-09-02  
**Status:** nonauthoritative implementation audit; this is not ratification or
GPU authority.

## Bottom line

PCFL-lite is feasible as a bounded, fixed-source, synthetic calibration without
a privileged runtime. The fastest honest substrate is the historical
`action-world-v0` branch, restored as an ordinary package only after the design
is ratified. It is the only existing game with a real legal-action endpoint:
the environment returns consequences of the action actually executed, and
`A0`--`A3` require remembered danger, procedural transfer, law inference, and
multi-crossing composition.

The current `lands` and `alchemy` worlds are useful supporting fixtures, but
their existing endpoints are answers/ratios or text predictions rather than a
behavioral legal-action success measure. `v03r` is a good causal/text
sentinel; it is not the PCFL-lite headline world. The smallest scientifically
defensible implementation is approximately five new adaptor/runner/test
modules (about 500--800 lines, plus a few dozen lines of glue), with the six
existing Action World files restored unchanged. No online-learning,
lifelong-scaling, saturation, compression, or learned-scheduler claim should
be attached to this calibration.

## Existing pieces and reuse decision

### Reuse directly

- `action-world-v0:action_world/world.py`: deterministic 16-threshold world,
  12 experienced feature patterns and 4 held-out patterns, hidden parity law,
  and `ActionSession.step()` feedback from executed actions.
- `action-world-v0:action_world/model.py`: typed `ActionDepth`, `Goal`,
  `Lifetime`, `StepRecord`, `StepResult`, legal-action and public-state
  schemas.
- `action-world-v0:action_world/solver.py`: `cautious_policy`, observed
  lookup, parity context-oracle, latent oracle, and per-depth evaluation. The
  parity and latent solvers remain evaluator-only ceilings.
- `action-world-v0:action_world/artifacts.py`: public/evaluator separation,
  manifest hashes, and refusal to overwrite a non-empty output directory.
- `action-world-v0:action_world/cli.py`, `__init__.py`, `README.md`, and
  `test_world.py`: command surface, integration contract, and baseline tests.
- `research_loop/cyclic_organism_contract.py` and
  `research_loop/trajectory_contract.py`: append-only trace and typed
  experience/checkpoint validation.
- `research_loop/scientific_dream_adapter.py`: strict target-blind request and
  parser boundary. Reuse the boundary shape, not its v03r-specific semantic
  admission rules (`animal_00`, route/effect keys).
- `research_loop/goal_conditioned_thinker.py` and
  `research_loop/scientific_thinker_adapter.py`: operation-only thinker,
  immutable reader/checkpoint shape, and deterministic control-plane tests.
  Replace the v03r agenda/compiler with Action World state and action schemas.
- `research_loop/microdream_world.py`, `model_call_ledger.py`,
  `capture_environment.py`, `verify_artifacts.py`, and `freeze.py`: public
  export, provenance, checksums, token/resource ledger, and freeze utilities.
- `alchemy/rag.py`: dependency-light TF-IDF raw-RAG baseline.
- `alchemy/lora_mem.py` and `alchemy/backend.py`: LoRA training/loading and
  HF/vLLM adapter plumbing for a later GPU sentinel. They need a PCFL wrapper
  enforcing fresh-base/per-life reset, corpus hash binding, target blindness,
  and adapter lineage; do not call them unchanged as a scientific arm.

### Reuse as reference, not as the primary world

- `lands/world.py`, `lands/v02.py`, `lands/solver.py`, `lands/v03.py`, and
  `lands/v03r.py` provide deterministic generation, exact oracles, paired
  collision/twin construction, and shortcut audits. Their final answer is a
  ratio/state token, so adding a legal-action wrapper would be slower and less
  diagnostic than using Action World.
- `lands/artifacts.py`, `lands/corpus.py`, `lands/audit_v02_shortcuts.py`, and
  `feltcraft_symbolic_kernel/` are useful patterns for evaluator separation,
  exhaustive CPU checks, and finite shortcut/property tests.
- `alchemy/world.py`, `env.py`, `player.py`, `dreamer.py`, and
  `run_lands_v02_organism.py` are a richer later habitat/pipeline. Existing
  logs expose exact values to the dreamer or evaluator-facing episode state,
  and the task goal is visible, so they are not target-blind PCFL-lite without
  redesign.
- `research_loop/recurrent_text_organism.py` is a reusable lifecycle/trace
  skeleton, but its default 46-event frozen schedule is v03r-specific: seed 1
  has 49 events, seed 3 has 43, and seed 2 lacks matched distractor endpoints.
  It currently supports a seed-0 dry-run fixture, not a multi-world canary.

## Missing minimum

The Action World branch is a world and policy baseline, not yet a PCFL
calibration. The missing pieces are small but scientifically essential:

1. **Target-blind life adapter.** Preseal one source lifetime and held-out
   goals; serialize only public lifetime rows, observations, action results,
   and public target state. Bind world/goal/life hashes and reset sessions and
   readers for every cell.
2. **Behavioral reader/controller runner.** Mount one canonical target-blind
   corpus through the same bytes as structured text, raw RAG, wrong-life, and
   shuffled controls. Parse only legal actions, step `ActionSession`, and
   score success, steps, reward, terminal reason, and action trace. Include a
   no-memory arm and an honest full-context arm.
3. **Shortcut audit.** Add finite target-only, current-state, rendered-text/order,
   threshold-ID, and public-feature predictors, with held-out relabel/render
   tests and leave-one-world/root checks. Existing Action World tests do not
   measure these shortcuts.
4. **Memory/LoRA binding.** Canonicalize memory lines once, hash the bytes,
   prohibit goal/answer/hidden-law fields, and ensure text and LoRA consume the
   same corpus. LoRA needs fresh base and per-life adapter reset, exact
   train/eval split, and ledger fields for examples/tokens/steps/rank/dtype/
   wall time.
5. **Artifact and CPU gate.** Emit public and evaluator-only trees, manifests,
   all failed actions, and a single reproducible report. Fail closed on leaked
   fields, stale state, missing cells, or overwrite.

## Exact minimal file/module plan

After ratification, the minimal implementation can be:

```
action_world/                         # restore six files from action-world-v0
pcfl_lite/world_adapter.py            # source/held-out sealing + public view
pcfl_lite/shortcuts.py                # finite predictors + relabel/render audit
pcfl_lite/memory.py                   # canonical corpus + text/RAG/LoRA arms
pcfl_lite/runner.py                   # reader/controller, action score, resets
pcfl_lite/artifacts.py                # manifests, ledgers, public/evaluator IO
research_loop/test_pcfl_lite.py       # CPU contract, leakage, reset, controls
research_loop/run_pcfl_lite.py        # --stage cpu|text|lora, fail-closed CLI
```

`pcfl_lite` may instead live under `research_loop/pcfl_lite/`; the important
boundary is that existing v03r/alchemy modules are not silently mutated. The
world files should initially be restored unchanged. Expected net new code is
roughly 500--800 lines; a first CPU-only implementation need not touch model
weights or remote execution.

## Feasibility and measured cost

The existing deterministic suites are comfortably CPU-sized:

| Check | Result | Measured wall time |
|---|---:|---:|
| Action World v0 `test_world.py` (9 tests, 100 seeds) | pass | 0.25 s |
| `lands/test_world.py` | 11 tests pass | 1.41 s |
| `lands/test_v02.py` (1,000-seed sweep) | pass | 10.39 s |
| `lands/test_v03.py` (1,000 paired audit) | pass | 33.86 s |
| `lands/test_v03r.py` (1,000 paired audit) | pass | 78.02 s |
| selected `research_loop` plain tests | 99 pass | 2.96 s |

Thus a one-root Action World export, shortcut suite, exact CPU oracle, and all
reset/leakage contracts should be seconds, not minutes. The execution-bundle
gate of 1,000 simulator steps under five CPU minutes is a generous ceiling;
the branch’s environment test is already orders of magnitude below it.

There is no local measured LoRA-training wall time in this audit. Existing
repository estimates are scale estimates: the older 7B/A100 plan puts a
960-episode life at about 8M tokens and 30--45 minutes, fresh evaluation at
about 20 minutes per arm/point, and LoRA at minutes; the full historical sweep
was estimated at under three A100-days. These numbers are not PCFL-lite
measurements and should not be copied into a result table. Existing adapter
metadata shows a Qwen2.5-7B-Instruct rank-64 q/k/v/o adapter (~154 MB), while
the tiny 0.5B rank-8 artifact is a practical smoke-test candidate if its model
is already available.

The only directly observed GPU evidence here is the 32B dreamer log: one
single-prompt generation takes roughly 26--43 seconds at about 44 output
tokens/s, with a large (~61 GiB) model load. PCFL-lite should not require that
dreamer. A one-world, one-goal GPU sentinel with a cached small model and
rank-8 adapter is therefore operationally plausible, but its wall time depends
on cache, backend, sequence length, and hardware and must be measured in the
resource ledger. No GPU run is justified until CPU gates and corpus equality
pass.

## Smallest post-ratification canary

1. **CPU instrumentation canary (development only):** Action World seed 0,
   one presealed source lifetime, all four held-out goals at `A0`--`A3`, with
   latent/parity solvers evaluator-only. Run no-memory, cautious, observed
   lookup, honest full-context, raw-RAG, wrong-life, and shuffled controls;
   run the finite shortcut/relabel/render audit and verify fresh reset for every
   cell. Also run a deterministic target-blind gold reader through the exact
   legal-action controller to prove the endpoint and budgets. This should be
   under a few seconds and produces no model claim.
2. **GPU sentinel (only if step 1 is green):** one held-out `A2` goal and one
   held-out `A3` goal from that root, one fresh base/model, one per-life adapter,
   canonical text and LoRA using byte-identical corpus, plus no-memory,
   full-context, raw-RAG, wrong-life, and shuffled arms. Prefer the cached
   0.5B/rank-8 artifact for plumbing; use 7B/rank-64 only when the intended
   runtime is available. Record every token, step, reset, and wall-time field.
   This is a plumbing sentinel, not evidence of generalization. Any directional
   paper result requires multiple independently sealed roots and held-out goals
   after the canary.

## Scientific stop conditions

Stop before LoRA if target-only/current-state/render/order predictors solve the
held-out action, if goal/answer/hidden-law fields enter the public corpus, if
wrong-life or shuffle performs like the causal memory arm, if text and LoRA do
not use identical bytes, or if state/adapter lineage crosses a reset. Treat a
failure of LoRA to beat text as a valid result. This remains a finite,
off-policy, synthetic calibration; it does not establish online evidence
acquisition, lifelong improvement, or compression.

