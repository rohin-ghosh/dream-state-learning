# P0 raw-wake exploratory fork launcher — frozen handoff, 2026-09-12

## Owned files

- `gpu/astra_parent_wake_diagnostic.py`
  SHA256 `78acbdea44a20bd8673b3068aa49f322e7316d183a3554688a1326082f15312e`
- `tests/test_astra_parent_wake_diagnostic.py`
  SHA256 `b038eb166444645d9ff3beebc31da566ad8c11426bfd5a4ff69401c66a49ff94`

No existing modules changed. No Git, SSH, GPU query, model load, training, or launch was performed by this worker. The tests substitute GPU/process boundaries; existing cleanup tests run ordinary CPU subprocesses. Files frozen for main review/commit.

## Two separate operations — inspect preparation before launch

From the fresh source checkout, using the intended venv interpreter (symlink is NOT resolved):

```sh
/path/to/venv/bin/python -B gpu/astra_parent_wake_diagnostic.py \
  --material "$HOME/astra_diagnostics/astra_P0_raw_wake_export_20260912_attempt1" \
  --root "$HOME/astra_diagnostics/astra_P0_raw_wake_diagnostic_seed0_20260912_attempt1"
```

This ONLY prepares. It performs no GPU query or subprocess execution. Main must inspect `plan.json` and `PREPARED.json` and native question audit before choosing to launch. No autoqueue or implicit launch.

After that inspection and main's live reservation checks, a separate explicit command is available (NOT executed here):

```sh
/path/to/venv/bin/python -B gpu/astra_parent_wake_diagnostic.py \
  --root "$HOME/astra_diagnostics/astra_P0_raw_wake_diagnostic_seed0_20260912_attempt1" \
  --device 1 --launch
```

`--launch` reuses existing `check_free`, then starts one dedicated controller with CUDA_VISIBLE_DEVICES retained across **lesson train → lesson OFF/ON → sham train → sham OFF/ON**, sequentially on that device. It returns LAUNCHED_NOT_COMPLETED, not scientific success. `--execute` is the internal controller entrypoint, requiring the matching inherited single-device selector. Main retains ownership of the continuous cooperative reservation; this does not create an OS-level GPU lock.

## Exact training and output contract

- Only bound `EXPORT/lesson.json` and `EXPORT/sham.json` are passed to V3 `--corpus`. Source maps are read for audit/mask verification but never given to training.
- 32 fixed measured-source episodes, original export ordering and exact spans. No recollection, reranking, rewriting, additional NOTE gate, partial fit, or changed tokenization recipe.
- Rank8, explicit alpha16, dropout0.05, lr1e-4, epochs3, seed0, batch1, grad_accum1, `--no-pack`, maxlen4096. No `--chat-template`, no `--no-grad-checkpoint`; existing V3 defaults retain gradient checkpointing. Fresh adapter paths `training/lesson_seed0` and `training/sham_seed0`; external logs `logs/{arm}/train.log`.
- Post-fit checks: actual LoRA config and adapter hashes, DONE, 96 steps, finite loss/no nonfinite batches, exact corpus hash and 32 encoded examples, no skipped/split/dropped data, exact per-arm input/context/target counts and 3× input tokens seen.
- Pair spec `logs/{arm}/probe_spec.json`; pair stdout `logs/{arm}/pair.log`; raw outputs `probes/{arm}/{off,on}/`; existing worker/cleanup receipts remain preserved.
- Existing neutral supervisor supplies fresh OFF/ON workers, parent-free/no-recall probes, existing source receipt validation, and owned-process cleanup. Fit cap900 seconds; neutral pair outer cap2100 seconds (each condition's existing worker cap900 seconds). Two arms' subprocess caps sum to6000 seconds; CPU hashing/preparation overhead is additional.
- Existing fixed16 IDs `rg/mini_sudoku/1900050..1900065`, gen_seed0, seed_salt15420, one tick, wake400/note100, total cap38400, maxlen4096. No parent text or source events passed into probe; source-root paths are protection metadata only.
- `logs/{arm}/result.json` preserves per-arm completion evidence. Earlier arm adapters/pair receipts are revalidated after the second arm. `COMPLETED.json` retains both arms and unequal token totals; no computed H1/scientific success gate. Missing pair output rejects completion.
- `LAUNCHED.json`, `STARTED.json`, `COMPLETED.json`, `FAILED.json`, and per-arm result receipts have real timezone-aware UTC timestamps. Launch records source root and script SHA256.
- Existing outputs/logs are exclusive; failure preserves completed-arm evidence, stops without retries, and records GPU process-query status without inventing reservation release. Main inspects inherited cleanup receipts before releasing a failed reservation.

## Question overlap, capsule check, and claim limits

The actual local copied export was read (not modified):
`/tmp/astra_raw_wake_export_capture_20260912/astra_P0_raw_wake_export_20260912_attempt1`.

- Actual question parser CPU test passed for both arms' actual native prompt envelopes and all **five selected mini-Sudoku episodes**. Native task head is extracted before the original ACT-format suffix; regenerated native question bytes must agree after the native `.strip()` behavior.
- With native reasoning_gym available, preparation compares these source QUESTION bytes against all16 canary questions and rejects exact puzzle overlap. Canonical answer-grid overlaps, if present, are reported as pairs, never used to exclude or reroll IDs.
- Native package is unavailable locally: no claim of actual canary-question validation or solution-overlap measurement here. Without the package the helper records `EPISODE_DISJOINT_ONLY`, explicitly no unseen-puzzle claim; native node preparation will perform the package check.
- All64 original source schedule IDs in each arm are checked against canaries and must match their historically bound schedule file hashes. All64 is an **episode-ID** check; selected mini question disjointness is a separate narrower check.
- Corpus is mixed-family:32 examples, five mini-Sudoku. Primary observations are only the existing16 mini canaries; other families are untested. Main reduces first-ACT solved count, missing/invalid first ACT=0, and retains all actions/secondary scores. Launcher does not use best-of-many as a computed success gate.
- Copied export reports lesson31747 input/4289 target tokens and sham31527/5360; source teacher token doses203/158. Equal examples/96steps is not equal target-token exposure or an isolated parenting semantic contrast. Model origin remains unresolved/local hashes only. No G5/clean/H1 promotion.
- Actual model/source paths needed for full prepare exist on node3 according to main, not this machine. No native full preparation was faked locally.

## Validation commands and results

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_astra_parent_wake_diagnostic.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_astra_mini_sudoku_diagnostic.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_run_reasoning_neutral.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu/astra_parent_wake_diagnostic.py --help
```

- New launcher17/17 passed,0.143s, including actual local P0 prompt parser (not skipped).
- Existing oracle launcher9/9 passed,0.010s.
- Existing neutral supervisor22/22 passed,1.957s, including actual CPU descendant timeout/failure/interrupt cleanup.
- CLI help exit0. Total48 passed. An initial `python` invocation failed because that executable is absent locally; rerun with `python3` passed.
- Logs: `/tmp/astra_parent_wake_diagnostic_tests.log`, `/tmp/astra_parent_wake_prior_launcher_tests.log`, `/tmp/astra_parent_wake_neutral_tests.log`.

Native preparation capsule inspection, live GPU reservation, training, and outcome reduction remain main-owned. No further edits outstanding.
