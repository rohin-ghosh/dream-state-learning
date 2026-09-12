# Neutral pair custody helper — frozen handoff

2026-09-12 08:18 UTC. Bounded non-material custody repair; existing evaluator and scientific claim boundaries unchanged. Main owns runner integration, lifecycle, environment, shared GPU-query repair, and all other tests. No Git/network/GPU actions or repository edits outside the two owned new files.

## Files frozen

- `organism_v6/neutral_pair_custody.py`
- `tests/test_neutral_pair_custody.py`

SHA256:

```text
49ae8d5f9a215fb42abe51dee60f0084218973fcc81f43d161ecfef7abaeda6b  organism_v6/neutral_pair_custody.py
84bc39aa1922d748ac640573d28e751bbdfe3a47e7f65b2bafc9c72d3473af12  tests/test_neutral_pair_custody.py
```

## Agreed APIs implemented

- `source_snapshot()` returns JSON-safe `{schema, source_root, bootstrap_path, sha256}`. `sha256` maps trusted-root-relative paths to digests. The closure is the wrapper, custody/probe helpers, backend, reasoning gym, gym interfaces, loop/state/ledger, preschool policies, package initializer, and `BOOTSTRAP_PATH`. It does not hash the moving entire repository or inactive compiler/training branches.
- `verify_source_snapshot(snapshot)` raises on changed/missing/redirected source files, changed root/bootstrap path, incomplete inventory, or altered schema. Returns `None` on success; call it directly, not inside a truthiness assertion.
- `verify_condition(output_dir, condition, spec_sha256, expected_receipt=None)` returns the parsed receipt after verification. `output_dir` is the PAIR root, not the condition directory. All original receipt fields are compared when `expected_receipt` is supplied; extra lifecycle/runtime receipt fields are supported and remain bound.
- `validate_pair(output_dir, spec_sha256, receipts, snapshot)` requires exactly the ORIGINAL `off` and `on` receipt dictionaries. It returns **`{"off": receipt_file_sha256, "on": receipt_file_sha256}`**, keyed by condition. It checks both original receipts and full manifests twice, checks the snapshot before/after, requires distinct worker PIDs, compares shared config/code/package/birth text, and binds birth/code bytes to the trusted snapshot.

## Validation details

- Required manifest artifacts: `configuration.json`, `results.json`, `source_check.json`, `generations.jsonl`, and each `episode_NNNN.jsonl` referenced by the exact configured/result episode order.
- Every manifest-listed file is hashed; the directory must contain exactly those files plus `manifest.json`. Missing/unmanifested artifacts, condition failures, pair failure markers (including dangling symlinks), malformed manifests, duplicate JSON keys, nonfinite JSON numbers, and wrong labels/spec/condition/PID reject.
- Artifacts must be regular, nonsymlink files with flat safe names, matching the current helper's output shape. Traversal, absolute filenames, slash/backslash names, symlink condition/root directories, and symlink receipts reject. Code entries must be canonical local paths inside the trusted root, with checked hashes and the required probe inventory.
- Configuration checks retain the existing configured-backend identity validator, enforce OFF/ON adapter presence, source path identity, adapter config/weight hashes, and successful before/after source checks.
- Shared-config comparison removes ONLY `source_identity.adapter_input`, `source_identity.adapter_files`, `sources.adapter`, and `hashes_before.adapter`. Model paths, seeds, budgets, panel, protected roots, package version, birth prompt, code inventories, and any additional shared config fields must match. No scores are recomputed or invented.

## Main integration sequence

1. Capture `snapshot = source_snapshot()` before any worker; persist it in PAIR_STARTED.
2. Worker loads that historical snapshot and calls `verify_source_snapshot` before/after work, as main proposed. Do not create replacement snapshots after observing changed sources.
3. After each completed worker, retain `receipts[condition] = verify_condition(pair_root, condition, spec_sha256)` in controller memory. Do not refresh originals from disk before final validation.
4. Immediately before PAIR_DONE, call `receipt_hashes = validate_pair(pair_root, spec_sha256, receipts, snapshot)` and persist the returned condition-keyed receipt-file digests with the original receipts.
5. Keep main's existing spec/model/families revalidation and lifecycle/environment checks. This API has a spec digest, not a spec document; it cannot replace the runner's spec preflight or independently compare its configuration against every original spec field.

### Fixture compatibility

Use actual `run_probe` artifacts and valid EVALUATION_ONLY receipts. The positive fixture in the new tests uses existing `FixtureGym` / `FixtureBackend` read-only but sets:

```python
gym._bootstrap = Path(reasoning_gym_gym.BOOTSTRAP_PATH).read_text()
```

This is essential: merely using the old fixture's arbitrary `"Solve the current puzzle."` text must fail the new prospective bootstrap binding. Synthetic files, fixture-generated measurements, and synthetic worker PIDs are explicitly CPU test evidence, not claims of GPU execution, real fresh processes, or authenticated model origin.

## Tests / commands

Final focused run:

```text
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=tests:. python3 -B -m unittest test_neutral_pair_custody -v
32 tests passed in 1.426s
log: /tmp/astra_neutral_pair_custody_tests.log
```

Final adjacent combined run:

```text
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=tests:. python3 -B -m unittest test_neutral_pair_custody test_reasoning_neutral_probe -v
50 tests passed in 1.936s
log: /tmp/astra_neutral_pair_custody_combined.log
```

Coverage includes prior-arm result/trace changes, rehashed replacement receipt rejection, receipt extra-field changes, missing originals, shared bootstrap conflicts and identical-but-unpinned bootstrap, seed/package conflicts, local source/bootstrap drift in temporary copies, ignored unrelated files, required artifact/ledger omission, failures, unmanifested files, traversal/symlinks, duplicate/nonfinite JSON, false spec/condition, omitted/false code inventories, wrong adapter mode, unsuccessful source check, changed model paths, and reused PIDs. The positive test uses both actual helper executions and confirms originals are not mutated by validation.

An earlier first-pass run reported 39 tests because importing the existing TestCase class into the new test module caused unittest to discover its 18 cases too. Fixed by importing the fixture module instead. Final counts above are 32 distinct new tests plus 18 existing adjacent tests, with no duplicate imported TestCase discovery.

## Remaining boundaries

- Runner integration and its revised process tests are main-owned and were not edited/run here while main was changing them. Changing wrapper source after a snapshot intentionally invalidates that snapshot; main's in-progress body/hash changes are expected, not a reason to weaken validation.
- These checks reject detected custody drift; they do not provide adversarial same-UID filesystem immutability or an atomic cross-file filesystem transaction. The caller must publish final markers only after success and preserve the original evidence.
- Source snapshots bind on-disk local implementation bytes; they do not attest GPU state, loaded weights, external package contents, origin, or panel-selection history. No GPU measurements or runtime cleanup claims were fabricated.

Files frozen for main combined validation. No further source/test edits planned.
