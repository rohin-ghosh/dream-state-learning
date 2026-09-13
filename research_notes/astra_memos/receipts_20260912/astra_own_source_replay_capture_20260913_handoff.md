# Own-source replay capture — EDITSTOP, September 13, 2026

## Status and exact implementation

Collection-only vertical slice is implemented; 20 CPU mock/regression tests
passed in 3.488s. CLI help passed. No native prepare, GPU/model execution,
network, launch, collection or repository edits were performed by this worker.
Main owns native CPU prepare and all placement/lifecycle decisions.

| File | SHA256 |
| --- | --- |
| `/tmp/astra_own_source_replay_capture_20260913.py` | `1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107` |
| `/tmp/test_astra_own_source_replay_capture_20260913.py` | `d6f3b09a2d3564122d6d641ba2eda0796ff5ceb3b67fe48e5f60983de758a25d` |

Frozen protocol: `research_notes/astra_memos/ASTRA_OWN_SOURCE_REPLAY_CAPTURE_2026-09-13.md`,
SHA256 `dba4390e07622022cc4610f426ce4b0ac73c379dda17798b3ae489ce40c1b17f`,
Main-reported commit `e9bc80d6`. The spec explicitly binds a separately copied
native protocol file; it does not assume the repository path exists natively.

## Stable API and schema

Scope/schema: `astra_own_source_replay_capture_20260913_v1`.

```python
prepare(root, spec_path, spec_sha256, allow_native=False)
verify(root, plan_sha256, native=False)  # returns (plan, bound)
worker(root, plan_sha256, seed, allow_gpu=False)
controller(root, plan_sha256, allow_gpu=False)
collect(root, plan_sha256, completion_sha256, out)
```

Prepare returns `plan_sha256`; controller returns `completion_sha256` for
`capture_complete.json`; collect returns `replay_report_sha256` and counts.
The controller starts workers sequentially in seed order 0,1,2; Main should
not launch worker subcommands separately. There is no fit/adoption API.

Closed spec template (replace all `MAIN_*` placeholders and the lease value;
the illustrative zero is not a valid lease). Do not add extra fields:

```json
{
  "runner_sha256": "1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107",
  "core": {"path": "/tmp/astra_own_source_replay_core_20260913.py", "sha256": "f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a"},
  "native": {"path": "/tmp/astra_level1_real_record_run_20260913.py", "sha256": "3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e"},
  "public": {"path": "/tmp/astra_birth_skill_probe_run_20260913.py", "sha256": "59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c"},
  "lifecycle": {"path": "/tmp/astra_real_record_memory_run_20260913.py", "sha256": "7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e"},
  "archive": {"path": "/MAIN_NATIVE_ARCHIVE_COPY", "sha256": "addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a"},
  "source_root": "/tmp/astra_level1_real_record_source_20260913_attempt1",
  "protocol": {"path": "/MAIN_NATIVE_PROTOCOL_COPY", "sha256": "dba4390e07622022cc4610f426ce4b0ac73c379dda17798b3ae489ce40c1b17f"},
  "gpu_index": 6,
  "gpu_uuid": "MAIN_CURRENT_GPU_UUID",
  "expected_boot_id": "MAIN_CURRENT_BOOT_ID",
  "lease_end": 0
}
```

`lease_end` is Unix seconds. UUID, boot, lease, native archive/protocol paths
and fresh root are Main-supplied bindings, not inferred historical facts.
Archive is the unchanged local
`gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar`
copied to the spec's native path. Live original adapter paths, base, Python,
environment, template and inference settings come from its pinned parent
plans, never memory descendants. They must exist at their original paths.

Additional frozen core dependencies at their original native paths:

- `/tmp/astra_level1_skill_run_20260913.py`:
  `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`.
- `/tmp/astra_level1_perception_reflection_material_20260913.py`:
  `4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941`.
- Frozen semantic tree at `source_root`, checked by the core.
- Lifecycle bootstrap requires its pinned `/tmp` path even if spec binding
  is another identical copy.

## Main-only commands

Original native Python:
`/localhome/local-rohing/v2/venv/bin/python`, pinned SHA256
`a92f0f95e883390c7256b2e441484aac06b1002dbe1d924141a77c8d82f96223`.
Set shell variables to Main's exact paths and returned hashes. These are
instructions, not commands executed by this author:

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
RUNNER=/tmp/astra_own_source_replay_capture_20260913.py
CUDA_VISIBLE_DEVICES='' "$PY" -B "$RUNNER" prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA" --allow-native

CUDA_VISIBLE_DEVICES='' "$PY" -B "$RUNNER" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu

CUDA_VISIBLE_DEVICES='' "$PY" -B "$RUNNER" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA" \
  --completion-sha256 "$COMPLETION_SHA" --out "$OUT"
```

Run controller under Main's reserving custodian: reservation holder remains
while controller CVD is empty; workers receive the bound GPU UUID. This module
does not replace the outer reservation/queue wrapper. Main checks node2 GPU6
UUID, all-process vacancy, environment, boot, queue and lease before launch.
Never infer vacancy from memory usage alone or release a holder without its
process exit/reconciliation. No foreign kills. Preserve the root and collected
directory in Main's immutable artifact archive; no new packaging/remote
transfer framework is included. Do not collect twice.

## Budgets, artifacts and admission

- Exactly 24 prospectively selected supported TRAIN prompts per original
  parent, 72 maximum calls; zero fits, optimizer updates or teacher calls.
- Three fresh sequential child processes; temperature0, max192 generated
  tokens, original generation seed0/settings. No shared conversation/cache/
  mutable weights. Parent adapter inventory checked before and after capture.
- Prepare cap180s; each seed cap900s including cleanup (worker860s with40s
  reserve); controller cap3000s includes verification/cleanup; separate
  collector180s includes verification. Six-hour lease-finish margin enforced.
- Prepared `bundle_seedN.json`, `calls_seedN.json`, `spec.json`, `plan.json`
  bind source/prompt/producer lineage and exact rendered token prefixes.
  Calls contain no expected raw-target strings.
- Each request is persisted before generation and raw response before
  validation. Native route, token prefix, decoded output bytes, token caps,
  timing and original adapter checks reuse frozen semantics. No repairs,
  regenerated outputs, retries, fallback targets or early admission.
- `run/seedN` contains identity, raw request/response, closure and process
  custody/release receipts. Controller validates three distinct, ordered,
  nonoverlapping processes before writing `capture_complete.json` with
  `admitted=false`. Failure stops subsequent seeds and preserves evidence.
- Collector checks all closures/releases before an exclusive sibling
  `.collection_claim.json`; then calls frozen `core.admit` once per seed
  (three total), with original text/finish bytes and exact source joins.
  Admission failure consumes the claim and preserves failure evidence.
- Collected `seedN_admission.json`, `replay_report.json`, `collection.json`
  retain all opportunities/rejects and native request/response-to-core joins.
  Costs are explicit per seed and total. Zero admitted is a valid completion,
  not grounds to rerun or expand the selection.

## Tests and limits

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_own_source_replay_capture_20260913.py' -q
```

20 tests cover pins/spec closure, TRAIN-only/no-target calls, source/settings
drift, raw-byte preservation/length/no retries, prompt/adapter mismatch,
failed-precheck no spawn, timeout cleanup and independent failure retention,
sequential chronology, mandatory release before admission, actual frozen
core admission for72 mocked malformed outputs with zero admissions, exclusive
collection, flags/CVD, and prohibition on old fit/collector paths. These are
CPU fixtures, not evidence of native execution or current GPU availability.

Default24 = 4skins ×3source-supported cases ×2outcomes with frozen earlier-event
relation selection. The original96 contain48source-inadmissible examples;
their exclusion is prospective and support-based, not output-based. Reports
show24opportunities and96source population per seed, not96-case coverage.
Frozen source judge stops at its first error: field/syntax/schema/source
counts are first-failure diagnostics, not exhaustive per-field accuracies.
Stop completion is separately required. Raw fences/content are not repaired.

Report explicitly sets `native_capture_receipts_checked=true`,
`core_native_identity_verified=false`, `automatic_pass=false`,
`fit_decision=null`. This preserves the frozen core's identity limitation
while checking native-layer receipts. These are original parents reading
externally curated observations already in birth training, not novel TRY
interaction, proven retention repair, consolidation, or scientific promotion.
Recipients, fit/replay dose and controls remain separate Main decisions.
