# Bounded reasoning neutral probe integration — 2026-09-12

`organism_v6.reasoning_neutral_probe.run_probe` is evaluation-only q14 §5:
child-authored measured action records after actual feedback in a neutral
Scratchpad. It does not test strategy/H2 or implement a new message12 policy.
No training admission, clean ancestry claim, model loading or launch occurs.

The main process owner must arrange actual ON/OFF **fresh-process** runs with
one selected backend per invocation, identical held-out IDs/seeds/budgets, and
distinct new output directories. No ON/OFF comparison is performed here.

Call `run_probe(model, gym, episode_ids=[...], output_dir=...,
probe_root=..., training_life_roots=[...], lineage_roots=[...], model_path=...,
adapter_path=..., expected_model_hashes=..., expected_adapter_hashes=...,
gen_seed=..., budget_ticks=..., wake_max_tokens=..., scratchpad_max_tokens=...,
total_token_budget=..., max_episodes=...)`. Both exclusion lists are required;
declare **all** training lives and lineage roots. The existing probe root must
contain the NEW output directory, whose parent already exists. Symlink-resolved
overlaps with protected roots or configured sources are rejected.

Use `ReasoningGymGym(strict_verifier=True)`; IDs must be classified as held out
(canary/gate/exam). Configure the supplied backend with local model and adapter
directories. `file_hashes(path)` supplies full relative-path/SHA256 manifests;
pin and independently verify those manifests before passing them. For OFF,
use `adapter_path=None`, `expected_adapter_hashes={}` and a base-only backend.
All local model files are hashed before and after (potentially expensive).
Configured backend paths/adapter hashes and identity stability are checked.
This is **not authentication of loaded weights or base origin**: that remains
externally verified by the caller. CPU tests use openly synthetic protocol
fixtures, not evidence of any real model or GPU execution.

Each episode has a fresh driver and isolated ledger, with recall disabled and
only `gym.birth_prompt()` as bootstrap. There is no teacher/history argument.
Actual user-text prompts and outputs are retained in `generations.jsonl`;
existing slot instrumentation retains source/action/feedback/prompt/output
identity receipts. Scope is before the backend chat template, not rendered
token IDs. Total budget reserves maximum output tokens before each call; it is
not a measurement of generated tokens or a wall-clock timeout.

`results.json` labels evidence `EVALUATION_ONLY`, with measured action counts,
correct grounded scratchpad counts, per-episode judgments and null rates for
zero denominators. The existing strict content judge is reused unchanged.
No percentages are substituted for raw counts. Failed invocations preserve
failure/evidence artifacts and do not write successful results. Files are
exclusive-create and sealed read-only with a SHA256 manifest; this protects
against accidental overwrites, not a privileged actor. Never point training
harvesting or parent feedback at these outputs. No existing life or lineage
is modified, and no new clean ancestry is asserted.

CPU verification (standard library, no dependencies required):
`python3 -m unittest discover -s tests -p test_reasoning_neutral_probe.py -v`.
