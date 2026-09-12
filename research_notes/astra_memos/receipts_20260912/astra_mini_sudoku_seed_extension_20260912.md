# Mini-sudoku bounded training-seed extension — frozen

2026-09-12. Only the owned preparer and its test file changed. Main's venv-interpreter symlink preservation is retained, with its regression passing. No launcher edits, Git, SSH, GPU calls or launches.

## Interface

- `prepare(..., training_seed=0)` and `trainer_commands(..., training_seed=0)` accept exactly integer 0, 1 or 2. Booleans, floats, strings and other values fail before preparation reads.
- CLI adds `--training-seed {0,1,2}`, default 0; all existing flags remain.
- Output adapters/logs use `useful_seedN`, `corrupt_seedN`, `useful_seedN.log`, `corrupt_seedN.log`; trainer argv uses `--seed N` and each command's `seed` field is N.
- `validation.json.training_seed` and `trainer_commands.json.training_seed` both equal N. Main's launcher can require its seed argument to equal both and each command seed/path.
- Post-training configuration guidance includes seedN. `future_seeds` lists only higher allowed seeds, with `future_seeds_scheduled=false`; no automatic repetitions or execution.

Example CPU preparation, not executed here:

```sh
/path/to/venv/bin/python -B -m organism_v6.mini_sudoku_behavior_material \
  --out /fresh/seed1/material --model-path /existing/local/base \
  --training-root /fresh/seed1/training --python /path/to/venv/bin/python \
  --training-seed 1
```

Use 2 for the second prospective replication. Fixed train/canary IDs, useful/corrupt material construction, plain pre-rendered native spans, no `--chat-template`, token checks, rank8/lr1e-4/3epochs/batch1 and 96 steps per fit are unchanged. Seed affects command/seed metadata only; it is not a data-generation seed. Tests verify byte-identical useful/corrupt corpora, IDs and oracle-source data across omitted seed, explicit0,1,2 with the native clock held fixed in the test; every validation field except the newly requested training_seed also matches. Actual repeated native prompt construction still retains real CLOCK text as before: main should compare regenerated corpus hashes with the fixed seed0 artifacts before calling a run same-corpus. No scientific claim follows from the seed0 2/16 observation; repetitions remain exploratory and use the same panel.

## Tests and freeze

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_mini_sudoku_behavior_material.py -v`

**25 passed in 1.852s** on final files. New tests cover exact seed1/2 argv/path deltas, default0 equivalence, bad seeds, CLI default/forwarding/rejections, per-seed output/log conflicts, corpus/token-validation invariance and both top-level seed fields. Existing venv-symlink/native-clock/masking tests remain green. Existing bootstrap ResourceWarning is unrelated and unchanged.

`PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.mini_sudoku_behavior_material --help` — exit0; new CLI choice shown. No package/tokenizer/GPU run was performed.

Frozen SHA256:

- `organism_v6/mini_sudoku_behavior_material.py`: `1f97aefe7e248affbb150f6d7abcfdd4d2e566cb6e61d8b3341e90ded473cf7e`
- `tests/test_mini_sudoku_behavior_material.py`: `4a3ffcadb6e5f76565207c4922fdea06e5aba27c5cde248ee1a7af03bc559e9d`

No further edits planned; main owns commit, launcher enforcement and sequential per-pair execution.
