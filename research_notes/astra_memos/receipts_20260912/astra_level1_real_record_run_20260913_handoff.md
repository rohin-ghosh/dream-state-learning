# Formation-only native runner handoff — 2026-09-13

Owned files only: `/tmp/astra_level1_real_record_run_20260913.py`, `/tmp/test_astra_level1_real_record_run_20260913.py`, this handoff. Parfit owns the core and its tests/handoff; original Level1/public runtimes, existing collections, repositories and all live runs remain unchanged. No native/model/GPU/network/Git operations were performed for this coding task. Core RuleGame execution in CPU fixtures is simulated child evidence, never a native result. Main owns deployment, final binding, native preflight and launch.

## Implemented core API (coordination resolved)

Uses the published core unchanged: `episode_ids()`, `load_dependencies(source_root)`, `contract(dependencies)`, `run_state(state, backend, dependencies=..., binding=...)`, `audit_capture(...)`, `compare_states(...)`. The obsolete provisional `run_episode` interface is NOT used.

Main confirmed and Parfit implemented **wake96 / record192**. The runner rejects any core declaring different states or token caps. Tested core SHA256: `1c7723fcbb07ad75464d9ceae9fbd1cb8953f6dc0cb7a2e22d3046421167a15c`; deployment still uses Main's explicit spec pin, not an implicit latest version.

The backend receives one exact core request dictionary. It renders `input_messages` through the unchanged public tokenizer/template mechanism, checks the dynamic prompt+output cap, writes the full request before inference, invokes temperature0/seed0 native generation with explicit96/192cap and LoRARequest, then writes and validates the actual response. It returns `{request_id, state, raw, finish_reason, native_response}` to core. `raw` is exactly native text, never reconstructed or repaired. Extra `native_response` is permitted by the core API and retains native token/route/finish/timing evidence.

Core captures are saved **unchanged** as `formation.json`, including their declared `native_identity_verified=false`; no per-state scientific fields are injected or overwritten. Wrapper identity/cost/process receipts are separate. Core CPU audit cannot prove a model ran; wrapper native custody checks are reported separately, not disguised as core identity certification.

Core owns wake parsing, real RuleGame.evaluate response, source joins, subsequent prompts and formation diagnostics. No host-selected action, host record target, forced correct record, parent, training, memory-write intervention, quiz or held-readout endpoint is added. Native infrastructure failures abort the state: `NativeCaptureFailure` bypasses core's ordinary backend-error-to-refusal handling, preserving partial requests/responses rather than silently continuing an invalid native run.

## Workload and finite envelope

- Four states in fixed order: OFF, perception_seed0, perception_seed1, perception_seed2; a separate fresh process/engine for each. OFF has no adapter; the three routes use immutable completed Level1 perception adapters directly, not cloned mutable or warm-started adapters.
- Eight common fresh DEV IDs, two scheduled wakes/episode. Record generation occurs only after a valid stop-completed actual TRY. At most32calls/state,128total; invalid/unfinished wakes can lower actual counts to16/state. Fixed possible-record denominator16/state; missing records are not invented or removed from that denominator.
- Same IDs/caps, differing actual child actions/transcripts: interactive record formation, not an identical-experience comparison. Production eligibility uses core's original judge; fenced content may pass its separate diagnostic content check but stays fenced and is not promoted into production grammar.
- Total controller1800s includes verification, process startup, all states and cleanup;900s per-state ceiling constrained by remaining total. Collection180s.40s cleanup reserve includes unchanged30s all-process XML release query and bounded owned-group cleanup. Six-hour lease finish margin required. These are prospective caps, not measured guarantees; no automatic retry or timeout increase.
- Public helper's XML vacancy/release query is unchanged, including graphics processes. Only the owned worker group is cleaned up. No foreign kills, compute-only substitution or GPU check during collection.

## Main's native source/layout prerequisites

Deploy byte-identical owned runner, final core, frozen Level1/public helpers, and a new `.git`-free immutable source snapshot. All source files must be enumerated exactly in `source_files`; symlinks/unlisted files fail. The snapshot must contain the **union of all three upstream plan source inventories** plus the core dependencies below. No training code is executed merely because its bytes are retained for source provenance.

- `organism_v6/rulegame.py`: `88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`
- `organism_v6/rulegame_parenting_diagnostic.py`: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`
- Public binding also needs pinned `organism_v6/birth_skill_corpus.py`; upstream inventories normally additionally contain `__init__.py`, `train_adapter_v3.py`, `birth_reflection_probe.py`. Use actual completed-plan inventories, not a guessed reduced list.

Core is loaded through its explicit `load_dependencies(spec.source)` API; no monkeypatch, environment-root workaround or archive edit. No reflection helper is required by this new wrapper: frozen Level1 helpers supply environment/adapter validation, public helper supplies model binding/tokenizer/XML/cleanup.

Each upstream root must be available under the **exact absolute root in its original plan**. If Main mirrors artifacts to the execution node, preserve bytes and original absolute paths. Required readable provenance/artifacts: original `plan.json`, `capture_complete.json`, `run/fit/fit.json`, complete `run/fit/adapter/` inventory, external `ROOT.collection_claim.json`, external native `collection.json` and `scores.json`. Other old response files need not be replayed by this wrapper. `scores.json` is hashed only; its readout values are never loaded or used for selection.

Upstream plan/completion hashes must match spec; completion must represent120closed old calls and OFF/fit/post. Collection receipt/hash/claim must bind that same completion and scores-file hash. Adapter path is derived only as `UPSTREAM_ROOT/run/fit/adapter`; explicit adapter file inventory must match both filesystem and completed fit inventory/receipt. Root failure or collection-failure marker rejects. Plans must be completed perception learners0/1/2 from the exact frozen Level1 runtime, same frozen model files and same model path. Old material/protocol/source pins remain bound via the original pinned plan and are retained as provenance without re-running old scoring/material APIs.

## Exact spec shape

All paths must be absolute and the new formation root must be disjoint from every input, upstream root and collection directory. Replace placeholders with Main's actual pinned bytes; no placeholder is an observed allocation or hash.

```json
{
  "runner_sha256": "FINAL_OWNED_RUNNER_SHA256",
  "source": "/tmp/astra_level1_real_record_source_20260913_attempt1",
  "source_files": {"ALL_RELATIVE_SOURCE_FILENAMES": "EXACT_SHA256_EACH"},
  "model": "ABSOLUTE_OFFICIAL_MODEL_PATH_MATCHING_UPSTREAM_PLANS",
  "core": {"path": "/tmp/astra_level1_real_record_core_20260913.py", "sha256": "MAIN_FINAL_CORE_SHA256"},
  "level1_runtime": {"path": "/tmp/astra_level1_skill_run_20260913.py", "sha256": "6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e"},
  "public": {"path": "/tmp/astra_birth_skill_probe_run_20260913.py", "sha256": "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"},
  "protocol": {"path": "ABSOLUTE_MAIN_FORMATION_PROTOCOL_PATH", "sha256": "MAIN_PROTOCOL_SHA256"},
  "binding": {"path": "ABSOLUTE_NATIVE_PUBLIC_MODEL_BINDING_PATH", "sha256": "BINDING_SHA256"},
  "gpu_index": 0,
  "gpu_uuid": "MAIN_OBSERVED_GPU_UUID",
  "lease_end": "REPLACE_WITH_NUMERIC_UNIX_UTC_SECONDS",
  "upstream": [
    {"seed": 0, "root": "ABSOLUTE_COMPLETED_PERCEPTION_SEED0_ROOT", "plan_sha256": "PLAN0_SHA256", "completion_sha256": "CAPTURE_COMPLETE0_SHA256", "collection": {"path": "ABSOLUTE_COLLECTION0_DIR/collection.json", "sha256": "COLLECTION0_SHA256"}, "adapter_files": {"ALL_RELATIVE_ADAPTER_FILENAMES": "EXACT_SHA256_EACH"}},
    {"seed": 1, "root": "ABSOLUTE_COMPLETED_PERCEPTION_SEED1_ROOT", "plan_sha256": "PLAN1_SHA256", "completion_sha256": "CAPTURE_COMPLETE1_SHA256", "collection": {"path": "ABSOLUTE_COLLECTION1_DIR/collection.json", "sha256": "COLLECTION1_SHA256"}, "adapter_files": {"ALL_RELATIVE_ADAPTER_FILENAMES": "EXACT_SHA256_EACH"}},
    {"seed": 2, "root": "ABSOLUTE_COMPLETED_PERCEPTION_SEED2_ROOT", "plan_sha256": "PLAN2_SHA256", "completion_sha256": "CAPTURE_COMPLETE2_SHA256", "collection": {"path": "ABSOLUTE_COLLECTION2_DIR/collection.json", "sha256": "COLLECTION2_SHA256"}, "adapter_files": {"ALL_RELATIVE_ADAPTER_FILENAMES": "EXACT_SHA256_EACH"}}
  ]
}
```

`gpu_index=0` above is illustrative only; Main supplies the actual planned index/UUID. `adapter_files` is the exact flat relative-path hash map from each completed fit receipt, not the whole fit directory.

## CLI / preflight before GPU

Use Main's chosen native interpreter; preparation records its exact executable path/hash and all subsequent invocations must use it.

```sh
"$PY" -B /tmp/astra_level1_real_record_run_20260913.py prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA" --allow-native

"$PY" -B /tmp/astra_level1_real_record_run_20260913.py controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu

"$PY" -B /tmp/astra_level1_real_record_run_20260913.py collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" \
  --completion-sha256 "$COMPLETE_SHA" --out "$FRESH_EXTERNAL_COLLECTION"
```

Prepare is CPU-native tokenizer/model-file verification only, never model loading/generation. It validates core/dependency/upstream/model/environment pins and renders the eight actual first-wake prompts. Later prompts depend on real actions/outcomes and are rendered/checked immediately before each native call; no prospective record target or fabricated transcript is generated during prepare. `worker --state STATE` is internal and requires an isolated group. Main can use its existing simple guarded launch pattern, no new launcher required.

## Artifacts and collection

- New root: `prepare_started.json`, `initial_prompts.json`, `plan.json`, `controller_started.json`; states under `run/STATE/` contain launch/start/release receipts, stdout/stderr, `identity.json`, numbered exact `.request.json`/`.response.json`, unchanged `formation.json`, and `closed.json` with actual calls/prompt tokens/output tokens/generation seconds and exact hashes.
- Controller validates all four process identities are distinct, checks core deterministic replay, exact core-event/native-file joins and unchanged adapters, then closes `capture_complete.json`. Early failure preserves partial evidence and no successful completion marker. Native refusal/invalid action differs from infrastructure failure.
- Collection is one-shot, external to root, claimed with `ROOT.collection_claim.json`. It rechecks source/helper/protocol/interpreter/upstream/native-file pins, replay/source joins and cost accounting without a model/GPU call. Writes `formation_report.json` and `collection.json`; no old readout scores are interpreted, and no incomplete state gets a fabricated success/zero score.
- Report retains core `compare_states` output (production eligibility, content/format/field diagnostics and refusals with denominator16/state), separate native costs and upstream provenance. `automatic_pass=false`, `scientific_pass=null` always. Raw36 formation only, not write success, improved learning, closed-loop, clean ancestry, P1/H1/H2 or formal C11 qualification.

## CPU validation / freeze

`python3 -B -m unittest discover -s /tmp -p test_astra_level1_real_record_run_20260913.py -v`

**12 tests PASS,12.234s**, using actual final96/192 core/RuleGame/public parsing under CPU scripted child fixtures and mocked native tokenizer/backend/model environment/processes. Covers128full calls,64calls with invalid/unfinished wakes, exact sequential source joins and raw fences, fresh per-state routes, core-capture preservation, non-swallowed native failures, upstream/adapter/collection/source bindings, runtime pin drift, call/context caps, immutable one-shot collection, and owned timeout cleanup/no foreign intervention. Test fixtures are not native child evidence.

Final owned-file hashes follow in EDITSTOP. No edits to Parfit's files or any frozen runtime were made.
