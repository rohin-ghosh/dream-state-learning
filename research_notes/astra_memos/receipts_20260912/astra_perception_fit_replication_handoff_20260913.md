# Perception learner-seed replications: ready queue only

## Scope and delta

Self-contained derivative of the accepted seed-0 driver, parent SHA-256
`f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`.
The live driver is neither imported nor modified. Only training configuration
seed and `trainer.epoch_order` seed change experimentally; both training anchor
arms use the same selected learner seed. Metadata and validation bind that seed.
This is AUTHOR_SOURCED_DEVELOPMENT_ONLY perception record-fidelity work, not
sleep, teacher-generated context distillation, L2 qualification, persistence,
or evidence of activated connections.

## Interface

- New driver: `/tmp/astra_perception_fit_replication_run_20260913.py`.
- `prepare` requires `--learner-seed 1` or `--learner-seed 2`, with all existing
  source/model/probe/binding/corpus/GPU/lease arguments unchanged. Use a separate
  new disjoint root per seed. No implicit seed and no seed-0 replication route.
- Python `prepare(..., learner_seed=1)` or `learner_seed=2` has the same rule;
  booleans, floats and other integers are rejected.
- Controller, worker and collect consume the hash-bound plan; they do not
  accept a second learner-seed override. `learner_recipe` clones the parent
  recipe, changing only `seed`. `train_adapter_v3` remains unmodified.
- Preparation intent, plan, prepared training files, fit/process/readout
  receipts, completion and scores carry the learner seed. Plan verification
  checks the parent hash, effective config and both prepared seeds. Fit workers
  recompute epoch orders and reject mismatches before calling the trainer.
- Main supplies Boyle's final probe source/hash, unchanged:
  `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`.
- CPU fixtures accept `PERCEPTION_DRIVER`, `PERCEPTION_PROBE_DRIVER` and
  `PERCEPTION_PUBLIC_SOURCE` overrides for unique frozen-source imports; do not
  replace original `/tmp` drivers to test frozen copies.

## Unchanged experiment per learner seed

| Item | Fixed value |
| --- | --- |
| Data | Same ordered 12 TRAIN and 12 DEV public-situation examples/raw targets |
| Training | Two fresh fits: anchor absent/present; exact Boyle anchor |
| Recipe | Rank 8, alpha 16, dropout .05, LR 1e-4, epochs 4, batch 4, grad accumulation 1, no packing, max length 1024 |
| Exposure | 12 updates / 48 presentations per fit; 24 updates / 96 presentations per selected learner seed |
| Readout | Six fresh processes: OFF/fitAbsent/fitPresent crossed with readout anchor absent/present |
| Generation | Seed 0, same fixed 12 DEV per cell, 72 calls total, max 192 tokens/call (13,824-token ceiling) |
| Engine | Seed 0, same frozen base and engine settings; every cell enables LoRA, max rank 32; OFF uses `lora_request=None` |
| Time | 600s fit ceiling, 240s readout ceiling, 2700s global cap, separate 180s collection |
| Release | 30s NVML query allowance, 40s cleanup/release reserve, owned process groups only |

Corpus API/default ordering and probe generation remain unchanged; learner seed
does not change examples, targets, rendered prompts or readout randomness.
Native full-assistant targets plus explicit EOS remain supervised with
`chat_template=False`, `add_eos=False`; template trailing whitespace is masked.
The inherited trainer overflow option remains `truncate`, but preparation and
receipt checks forbid actual truncation, dropping, skipped batches or altered
exposure. No target/token/threshold changes. All raw captures must close before
any scores; no dev-driven selection, checkpoint tuning, retry or outcome-based
seed choice. Stage ceilings are not guaranteed summed runtimes: the global cap
can abort and failure evidence must remain.

Each invocation is one prospective learner-seed diagnostic. If both seed-1 and
seed-2 runs are eventually authorized and completed, their planned combined
counts are four fits and 144 readout calls; no such runs or multi-seed evidence
are claimed here. Repeated OFF cells provide matched runtime controls, not
independent learner replications.

## CPU validation and hashes

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s /tmp -p test_astra_perception_fit_replication_run_20260913.py -v
```

Final CPU fixture run: **39 PASS in 6.600s**. Tests cover restricted/required
seeds, reproducible order across roots, matched anchor-arm ordering, seed-only
config/order differences with identical inputs, forbidden/resealed seed
mismatches, worker epoch-order rejection, strict integer binding, and native
`run_receipts` settings through CPU mocks. Inherited masking, budgets, release,
fresh-process/capture completeness, OFF routing and import-override tests pass.
No actual tokenizer/model/native/GPU/NVML/network/Git operation was performed.
No live run artifacts or outcomes were inspected. Only the three owned files
were changed.

- Driver SHA-256: `5d646e993408cbf91fd4e2a0657f59b87c0197281d9e451e578a45263bbd09f8`
- Tests SHA-256: `a66deb9fca11cafc36626e55abff3f65e39a6f13d3eba0349f5f766fc1b2657b`
- Handoff SHA-256 is reported externally at EDITSTOP to avoid self-hashing.

## Main acceptance still required

This is preparation, not fit authorization evidence. Main must first accept the
initial native fit path and conduct separate fresh GPU checks before launching
either replication. Native preparation must confirm actual token masks,
consistent learner-seed epoch orders and native trainer receipts on the frozen
replication source. Main reported seed-0 preparation measured 372 supervised
tokens/epoch per arm, with total tokens 3024 absent / 3444 present; those are
Main-reported reference counts, not measurements from this task. Encoding is
unchanged here, but CPU mocks cannot substitute for that native acceptance.
No successful fit, numerical reproducibility or persistent skill is asserted.
