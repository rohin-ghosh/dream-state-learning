# Mini-sudoku external-oracle behavior material: frozen handoff

2026-09-12. Completed bounded CPU preparer; no Git, remote, GPU, model calls, fits or evaluation launches. Only these repository files were created/edited:

- `organism_v6/mini_sudoku_behavior_material.py` — SHA256 `0ba6ac4f6f05dfa374f2e127c4e7c3c29d03a74f33ff918255b40692d8f922b0`
- `tests/test_mini_sudoku_behavior_material.py` — SHA256 `918d770672a46d6beee141eca63c3b9e15062630ad52686f60625fa42b6d455c`

Files are frozen for main review/commit/deployment. No further source edits planned. The old /tmp coordination note's proposed born_at override and chat-template description are superseded by this handoff and final source.

## Exact CPU CLI

Use the actual deployed source checkout and its Python environment, local model files only:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  /path/to/venv/bin/python -B -m organism_v6.mini_sudoku_behavior_material \
  --out /fresh/material_inputs \
  --model-path /absolute/local/Qwen2.5-7B-Instruct \
  --training-root /separate/fresh/fit_outputs \
  --python /path/to/venv/bin/python
```

This command ONLY prepares material and trainer specifications. It never invokes a trainer, loads weights for inference, queries GPUs, or reserves a device. `--out` must not exist. Model, inputs and training roots must be disjoint; reserved trainer destinations/logs must not exist. Inputs are written exclusively, hashed, made read-only, with the input directory read-only. Failure before writing leaves no output root; filesystem failure during writing can leave a partial root, which must not be reused. A final `manifest.json` is written after the other files.

Programmatic API: `prepare(out, model_path, training_root, *, gym=None, tokenizer=None, python_executable=None) -> manifest`. Any injected gym/tokenizer labels all results `SYNTHETIC_CPU_FIXTURE`, not native package validation. Production CLI requires installed `reasoning_gym==0.1.25` and loads the tokenizer with `local_files_only=True`.

## Output files and integration shape

- `useful.json`, `corrupt.json`: top-level `recipe`, `boundary`, `corpus`. Exactly 32 training rows each. Row keys: `q`, `rendered_q`, `a`, `episode_id`, `group`, `category`, `spans`.
- Exact spans: `[[rendered_q, false, "native_context"], [a, true, "external_oracle_action"]]`. V3 sees explicit spans; q/a are preserved for audit, not a request to re-template.
- `oracle_sources.json`: all 48 native entries, puzzle/solution matrices, canonical ACT targets, native/raw and rendered prompts/hashes, actual CLOCK lines, board/entry hashes. Held-out oracle answers are here for CPU validation, never rows in either training corpus.
- `ids.json`: fixed train/canary IDs, full declared prior CPU examination history from Popper, disclosed cross-split completed-solution overlap, and a warning that general historical exposure was not audited.
- `local_pins.json`: actual local model/tokenizer inventory and hashes. These establish local byte identity only; official origin is unresolved. Reuses the existing local Qwen2.5-7B inventory check, hashes before/after preparation; may take noticeable CPU/disk time for full weights.
- `source_hashes.json`: actual implementation, bootstrap, families and dataset-class source-file hashes. Sources are compared again before writing.
- `validation.json`: 48-board validation, fixed donor mapping/native scores/given violations, actual token/label evidence per training row and arm, solution-overlap disclosure, expected 96 steps per fit, prospective first-ACT endpoint.
- `trainer_commands.json`: only useful/corrupt seed-0 commands. Each has `argv`, `cwd`, `env`, external exclusive stdout/stderr log path, `shell=false`, `execute=false`, expected examples/steps, and explicit caller-owned GPU selection. Future seeds 1/2 are listed as unscheduled, not emitted commands.
- `manifest.json`: schema, PREPARED status, boundary, SHA256 mapping of all preceding files. Read-only permissions plus recorded hashes are ordinary artifact hygiene, not a new tamperproof/clean-lineage certificate.

## Native prompt fix — no shared trainer edit

`one_tick_prompt` calls `batch_loop.driver_class_for(gym)(episode, gym.birth_prompt(), gym, None, budget_ticks=1).prompt()` once. Ledger=None is safe because the preparer never calls consume. **No state override remains.** `State.clock_line` actually treats born_at=0 as alive 0s, not huge uptime, but main's concern was resolved by removing the override entirely. An explicit test advances the native clock from 100 to 102 and verifies `alive 2s`, proving no clock suppression. Actual prompt/CLOCK bytes are retained; byte-identical timing with every later live render is not claimed.

Raw q, including its terminal newline, is passed unchanged to the actual tokenizer's `apply_chat_template([{"role":"user","content":q}], tokenize=False, add_generation_prompt=True)`. The output is the context span. The actual V3 plain encoder and segment encoder must agree; then actual collate labels must equal masked context plus every ACT-target token and supervised EOS. No silent truncation, split, missing target, or context supervision is accepted.

**Commands intentionally omit `--chat-template`.** This avoids V3's `.rstrip("\n")` path and double-templating. It is explicitly labeled the pre-rendered-native-context experimental recipe, not the unchanged old q/a chat-template recipe. Regression tests show raw-newline and stripped-newline renders differ and that only raw native rendering is used.

## Fixed data checks

Train seeds 1850000..1850031 (32); canary seeds 1900050..1900065 (16), mini_sudoku only. The builder checks current split classification. All 48 actual question/givens matrices must have distinct identities across both sets. Question rows and canonical answer must match native metadata puzzle/solution and blank count. Canonical rendering is checked exactly; an independent 4x4 row/column/2x2/givens validator checks every solution. Both original canonical answer and decoded semicolon action must score exactly 1 under native `dataset.score_answer`.

Corruption is a fixed cyclic +1 donor, modulo 32. No search/rerolls. Every donor target must score below 1 on the recipient AND violate at least one recipient given. Useful/corrupt have identical q per row, identical whole answer-string multiset, and identical actual supervised target-token-sequence multiset (including EOS). Input lengths may differ per paired row because the donor target changes; no whole-row exact-token equivalence is claimed. Global context and target marginals match.

Read `/tmp/astra_mini_sudoku_material_handoff_turing_20260912.md` from Popper. It reports actual node-3 CPU feasibility for these exact IDs: all puzzles unique, canonical native score1 and independent unique completion; cyclic corruption passes; 37 target tokens before EOS. It also reports four held-out completed solutions shared with training: 1900054, 1900055, 1900059, 1900065. **These are Popper's observations, not independently rerun locally.** The preparer recomputes solution overlap and records it without rerolling. It independently checks legal completions, but does not enumerate all 288 solutions or itself claim unique completion.

The recorded prior CPU-examined history includes:

- 1850000..1850031;
- 1900050..1900069 (the extra 66..69 are not selected);
- 1001000..1001031;
- 1002000..1002015;
- 1900020..1900042.

These are disclosed CPU examinations, not Qwen outcomes or untouched-confirmation provenance.

## Exact future trainer recipe; nothing launched

Both commands target `organism_v6.train_adapter_v3` with explicit local `--model`, `--rank 8 --lr 1e-4 --epochs 3 --seed 0 --batch-size 1 --grad-accum 1 --no-pack --max-len 4096`. No `--chat-template`. Other unchanged V3 defaults include alpha=2r, dropout .05, AdamW, all projection modules/all layers, shuffled groups and supervised EOS. With 32 items, one segment/item and batch1, expected 96 optimizer steps per fit, two fits initially.

Trainer outputs: `<training-root>/useful_seed0` and `<training-root>/corrupt_seed0`; external exclusive logs `<training-root>/useful_seed0.log` and `corrupt_seed0.log`. Main creates/manages the external root, assigns GPUs and performs subprocess execution. No auto-execution exists.

After training main should check actual corpus hashes/config, source/model pins, 32 items/96 steps, zero context/target truncation/splits, expected supervised token mass including EOS, finite loss, actual adapter hashes and logs. Then main-owned existing 16-canary fresh-process OFF/ON runs: primary first-ACT solved count, missing/invalid first ACT zero; retain all ACTs, with first-ACT continuous score/native best/nACTs and useful-minus-OFF/useful-minus-corrupt paired differences secondary. No first-person/reasoning-self-report success criterion. The preparer contains no model eval outcomes or reducer.

## Actual tests and remaining preflight

Commands executed locally:

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_mini_sudoku_behavior_material.py -v` — **19 tests passed in 1.208s** on final source. Covers exact native prompt/rendering, mask/collate, fixed order/corruption, actual givens rejection, native-score failure, puzzle collision, allowed solution overlap, metadata tampering, history, no held-out training rows, no launch, 96-step command config, truncation/EOS failures, source/model drift, fresh/read-only/hash outputs, clock behavior.
2. `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_train_adapter_v3.py` — exit0, script prints `9/9 passed (3 skipped: ...)`. Two optional torch/peft tests skip; one CLI/config test skips its optional LoRA-config portion due missing peft. Do not count this as nine fully executed deep-learning tests. Log `/tmp/astra_mini_sudoku_trainer_cpu_tests.log`.
3. `PYTHONDONTWRITEBYTECODE=1 python3 tests/test_sleep_compile_v3.py` — **22/22 passed**, exit0. Log `/tmp/astra_mini_sudoku_compiler_cpu_tests.log`.
4. `PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.mini_sudoku_behavior_material --help` — exit0, exact CLI verified.

The existing ReasoningGymGym constructor emits a ResourceWarning for an unclosed bootstrap read in the fixture tests; unrelated source was not edited. Local python3 has neither reasoning_gym nor transformers. Therefore the new module's actual production CLI still needs main's node CPU execution against the pinned package and real local tokenizer. No fabricated native preparation, GPU training, first-ACT gains, parenting, clean ancestry, or model-origin authentication is claimed.
