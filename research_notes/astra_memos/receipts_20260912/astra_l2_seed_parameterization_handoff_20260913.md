# EDITSTOP — L2 learner-seed CPU readiness

Recorded 2026-09-13 06:16:37 UTC. Bounded, non-material optional-seed wiring;
no change to the frozen scientific/core contract and no replication commitment.
Main decides whether to pursue replications after the first L2 terminal results.

## Changed paths and exact SHA256

Only these persistent files were edited by this sidecar:

- `gpu/astra_l2_public_record_dev.py`
  - Before: `213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e`
  - After: `d1965ddc571ec393ef0ec656eda8556b3db91d7de81fafa87310900706d96a3d`
- `tests/test_astra_l2_public_record_dev.py`
  - Before: `d2ebe1e3a37c7ad7ee42e07aab583494d86819be7dfa7fd7cac25b392baed3f2`
  - After: `14fbbc06b9f748685069bcb978df388791408f679e71025c7c95c324d7be4272`
- `/tmp/astra_l2_seed_parameterization_handoff_20260913.md`
  - Its post-write hash is reported in the final EDITSTOP response, not recursively embedded here.

Read-only dependencies checked before and after; unchanged:

- `organism_v6/l2_public_record_dev.py`:
  `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`
- `organism_v6/train_adapter_v3.py`:
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`

No Git, native, GPU, network, remote, live-root, or live-snapshot operations.
No manuscript, notes, state, launcher, framework, C11, core, or trainer edits.
Tests used temporary synthetic fixture directories and cleaned them up.

## Runtime contract

- Optional numeric JSON spec field `learner_seed`; omission means 0. Only exact
  integers 0, 1, 2 pass. Boolean, float, string, null, collection, nonfinite,
  out-of-range and duplicate-field inputs reject. Other extra spec fields still reject.
- Explicit flow: spec -> `fit_config` / plan `seeds` -> `fit_stage` ->
  `encode_training(..., learner_seed=...)` -> collection re-encoding.
  No global seed/recipe monkeypatching or trainer changes.
- Fit `TrainConfig.seed` changes only the existing trainer's fit RNG path
  (initialization/dropout/shuffling); epoch-order audits pass that same seed
  to the pinned trainer. No added RNG manipulation or stage-dependent seed offsets.
- Preparation returns `learner_seed`; the durable plan records fixed vocabulary,
  truth and selected learner seeds plus the selected fit config. Every new
  `training.json` records `learner_seed`. Successful replay summaries report `seeds`.
- Verify binds spec/plan/config seeds before imports. Fit rejects inconsistent
  plan/config seeds before tokenizer/model work or fit artifacts. Manifest
  validation binds its config to the training receipt. Collection exactly
  re-encodes training under the plan seed, rejecting cross-seed epoch/receipt
  substitutions, including bool-versus-int and float-versus-int aliases.
- Vocabulary 2026091301, truth 2026091302, engine seed 0 and sampling seed 0
  remain fixed. No child targets, prompt bytes, masks, EOS, PROMOTE/SHADOW routing,
  three cold fits, 100 updates, 128 calls, stage/deadline/lease budgets, or
  hardware-independent spec GPU fields were changed.
- Core bytes/schema and runtime schema remain unchanged. New metadata/source
  pins necessarily change artifact hashes; this is not byte identity of new
  prepared roots with old roots. Default seed0 config and synthetic training
  encoding, excluding the newly added seed receipt, retain pre-edit hashes.
- Final four-file source inventory, running-runtime SHA, helper pins and caller
  plan pin remain mandatory. No relaxed pin or legacy-root compatibility path.
  Old roots MUST always use their archived accepted runtime/source snapshot.

## CPU evidence and commands

All commands ran from `/data/home/rohing/dream-state` with bytecode disabled.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p '*l2_public_record_dev.py' -v
```

- Before edits: 89 tests passed in 10.440 s (61 runtime + 28 core).
- Final source: 102 tests passed in 17.434 s (all prior 89 + 13 new).

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_astra_l2_public_record_dev.py' -k seed -v
```

- Final focused result: 13 tests passed in 6.693 s.
- Initial focused attempt failed only the new epoch-order test oracle: it
  omitted the pinned trainer's existing `pack_by_group(..., pack=False)` ordering.
  Corrected the oracle, not the runtime or experimental recipe, then reran both suites.
- Initial baseline attempt using `python` exited 127 because that alias is absent;
  all executed tests used `python3`.
- Both changed Python files passed `ast.parse` and a per-line trailing-whitespace
  assertion, without importing a native framework or writing bytecode.
- `sha256sum` checked the two changed Python files and unchanged core/trainer.

New coverage includes default/explicit0/1/2 spec preparation and verification,
decoder rejection, pre-fit seed rejection, manifest receipts, cross-seed and
malformed epoch replay rejection, fixed inference identities, and complete
mocked seed1/seed2 paired loops preserving 128 calls / 3 fits / 100 updates.

Pre-edit synthetic seed0 golden hashes, retained in regression tests:

- Encoding without optional target newline: `7800ef957a7a35dc801ed973bbb8c725d312949c92ad8661ac85fdeff7a68ff5`
- Encoding with optional target newline: `0e9cad6abdea9da920594eca00949eb93e1eeff6a422024998f68c5db4b4563a`
- Fixture-model fit config: `c188517d43550a4bf347fed433b75c88a6129b1a66c1abadc8292381ee1ee409`
- Fixed core world: `39ebd6a4307bff2c3d4da5added98a9980689972c9cc648e70072329e8ba3370`

## Minimal prospective native preparation — Main only, NOT executed

1. First await the original L2 terminal results and Main's replication decision.
   Do not edit/reopen/reseed any existing run root or accepted immutable snapshot.
2. If Main chooses to proceed, Main creates a NEW pinned four-file source
   snapshot containing the runtime hash above and unchanged final core/trainer;
   retain the final helper/model-binding/protocol pins. Use a new disjoint spec
   and root per seed, with the actual target GPU UUID/index and adequate lease.
3. In each new spec add `"learner_seed": 1` or `"learner_seed": 2` as an integer;
   omit it or use 0 only for a prospective seed0 preparation. There is no new
   seed CLI option and no new launcher. Pin the exact new spec bytes.
4. Main may then use the existing preparation interface, capturing its receipt
   outside the new root (placeholders below are intentionally not runnable):

```sh
PYTHONDONTWRITEBYTECODE=1 /ABS/PINNED_PYTHON -B /NEW/SNAPSHOT/gpu/astra_l2_public_record_dev.py prepare --spec /NEW/SPEC.json --spec-sha256 EXACT_NEW_SPEC_SHA256 --root /NEW/UNUSED_ROOT --allow-native
```

5. Retain the returned exact plan SHA and learner-seed receipt; any later
   authorized native commands must use that same new snapshot and plan pin.
   No launch, commit, source promotion or new native preparation was performed here.

## Limitations

This establishes CPU wiring/provenance readiness only. No native tokenizer,
adapter initialization/dropout tensors, GPU execution, memory/performance,
cross-device numerical determinism, scientific outcomes or replication success
were validated. Fit execution and preparation helpers were mocked in tests;
actual epoch ordering and encoding used the pinned pure trainer functions.
No real outputs were consulted and no outcome-driven tuning was performed.
Successful fixture replay is not a native/scientific pass.
