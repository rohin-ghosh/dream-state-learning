# PCFL own-write cold readout — EDITSTOP, 2026-09-13

Implemented only `gpu/astra_pcfl_own_write_readout.py` and its new test file.
This handoff is the only additional authored file. Other workers' formation,
writer, capture inspector, rules, C0 actor/controller and old receipts are
untouched. No native/model/tokenizer/GPU/network execution, process signals,
allocation, commit or push by this worker. No current C0 output was inspected.

## Frozen hashes

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_own_write_readout.py` | `d8d4ef962ca80933f3c3a60681c8375198197855f8d5f00a2b7835461e8427c4` |
| `tests/test_astra_pcfl_own_write_readout.py` | `8dbf41844122b528b9e5d24f66ab8e53e3647647059dcc5a684836f8fd348368` |
| Existing native helper `gpu/astra_pcfl_native_actor.py` | `f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26` |
| Existing public READ/parser/wrappers `organism_v6/pcfl_vertical_dev.py` | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |
| `research_notes/astra_memos/ASTRA_PCFL_OWN_WRITE_SCOPE_2026-09-13.md` | `0eb146caa29ee9ad29cd09a32a7455a700c2ee9211bfc2e2680ca46abac846f9` |
| Inspected old LoRARequest seam `/tmp/astra_level1_real_record_run_20260913.py` | `3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e` |

The old runner is a reference only, not a runtime dependency. Its science,
training/collection schemas and max-rank32 setting are not imported.

## Concrete Main interface

```python
from gpu import astra_pcfl_own_write_readout as readout

actor = readout.ReadoutActor(config)
try:
    actor.start()  # optional; otherwise the first generate starts it
    for row in config["roster"]:
        response = actor.generate(
            {"id": row["id"]},
            {"deadline": frozen_call_deadline, "device_seconds": frozen_call_seconds},
        )
finally:
    close_receipt = actor.close()
```

Illustrative only: Main supplies prospectively frozen real paths/hashes, roster,
seeds and budgets. Each arm runs in a fresh process with a new output directory.
There is no CLI, scorer, collector, resource allocator, process cleanup or
training entry here. This deliberately is not a drop-in full-history C0 actor.

Configuration is a **closed** dictionary: the existing NativeActor CONFIG_FIELDS
plus `arm`, `adapter`, `roster`, `roster_sha256`, and `shutdown_binding`.

- `schema`: `pcfl.own_write_readout.v1` (never the inherited C0 schema).
- `engine`: exactly `readout.ENGINE`: same existing frozen bf16 Qwen engine
  settings, but `enable_lora=True` and `max_lora_rank=8` in BOTH arms.
- `arm`: `NO_WRITE_C0` or `AUTH_WRITE`.
- `adapter`: null for NO_WRITE_C0. AUTH_WRITE requires exactly
  `{"name":"pcfl-own-write", "id":1, "path":"/absolute/saved/adapter", "files":{...}}`.
  File-map entries are `{"size":positive_integer,"sha256":"exact_byte_sha256"}`.
  Require `adapter_config.json` and `adapter_model.safetensors`; `README.md` is
  the only optional extra. No optimizer, alternate adapter, nested file or
  unbound file is accepted. Pin the completed saved artifact, not an intended
  or still-being-written checkpoint.
- `roster`: ordered list of closed rows
  `{"id":"read/0", "request":"READ EVENT E_AAAAAAAAAA", "view":0,
    "seed":42, "output_tokens":256}` (example IDs/seed/cap are synthetic).
  `view` is integer 0..8; `request` passes the existing strict READ grammar.
  `roster_sha256` is `readout.digest(roster)`. Both arms must bind the SAME roster
  hash. `max_calls` must equal its length, 1..1952. No duplicate IDs, skipping,
  replay, appended requests or outcome-selected views/caps.
- `max_input_tokens`, `max_output_tokens`, `max_calls`, absolute monotonic
  `deadline`, and `device_seconds_cap` retain explicit native-style limits.
  Each row's output cap is frozen; per-call limits accept only deadline and
  device_seconds, not replacement prompts/token caps. Main freezes those time
  limits in its outer plan. The actor has no inferred schedule or default seeds.
- Base/tokenizer fields retain the existing exact official public-receipt,
  four tokenizer-file, actual loaded template/probe, environment/package and
  GPU UUID bindings. `model_path` is the cached base, never the adapter path.
- `source_files` must pin every path from `required_source_paths()` (this actor,
  native helper, core public grammar/wrappers and own-write scope), plus any
  additional Main source bindings. Hashes must match the actually imported files.
- `shutdown_binding` is exactly `{"path":"/absolute/installed/source.py",
  "sha256":"exact_file_sha256"}` for the defining source file of the actual
  bound `LLM.llm_engine.engine_core.shutdown` method. This is an installed-source
  identity supplied by Main, not a guessed vLLM filename/version or a model file.

## Query visibility, adapter route and evidence

Only `{id}` enters `generate`. The actor looks up the next sealed row and builds
exactly two messages: the existing `core.MEMORY_SYSTEM` plus its existing
W0..W8 wrapper substituted with that single strict READ request. No supplied
messages, contexts, targets, expected banks, teacher rows, assistant history,
world transcript, sealed scorer state or task graph can be passed through this
API. Roster IDs, view labels, arm/adapter metadata and seeds do not enter the
model-visible prompt. The actor does not score or normalize responses.

NO_WRITE_C0 sends `lora_request=None` into a fresh LoRA-enabled LLM. AUTH_WRITE
constructs exactly `LoRARequest(name, id, path)`, following the inspected old
native seam. Its actual `lora_name`, `lora_int_id` and `lora_path` are checked and
captured at generation. The raw result must carry the exact arm/LoRARequest/file-
map hash route; a mismatch preserves raw evidence and fails without retry.

Base verification reuses the existing native identity checks, including exact
14-file public receipt and byte hashing. The base-only identity is explicitly
nested under `base_identity`, with inherited mount/LoRA labels removed; all new
load, request, render, raw and close receipts identify the actual readout route.
Adapter file inventory, sizes and hashes are independently checked before load.
Adapter metadata must declare rank8/alpha16/dropout.05, LORA, no bias/modules-to-
save, rank/alpha overrides, DoRA or RSLoRA. This is checkpoint byte/metadata
custody, not numerical proof of the training history; Main binds writer receipts.

Output files are exclusive-create under a fresh disjoint directory:
`config.json`, `identity.json`, `load.json`, numbered `.request.json`,
`.render.json`, `.raw.json`, `.response.json`, failure receipts, and `close.json`.
Raw evidence includes actual prompt/output IDs, text, finish/stop reason,
generation timestamps, exact route, and invalid-cardinality captures when
available. Successful response receipts retain UTF-8 hash/hex. Length termination
is explicitly returned as `truncated=true`, never silently repaired or retried;
Main's frozen reducer must interpret it. Errors after an attempted read consume
that ID and leave the actor failed; repeated calls do not regenerate.

## Engine shutdown and lifecycle limits

The new session uses **`llm.llm_engine.engine_core.shutdown()`**, NOT
`LLM.shutdown`. Before generation it checks that method exists, accepts a
zero-argument bound call, and that `inspect.getsourcefile(method)` and its bytes
match Main's shutdown binding. Close rechecks the seam and invokes it directly.
If unavailable, mismatched or failing, the close receipt reports failure rather
than inventing successful shutdown. A successfully returned method still does
not establish worker exit or GPU vacancy.

**Native installed-source verification remains for Main.** No local vLLM
distribution or frozen installed shutdown source was available to this worker;
the seam is CPU-tested with injected objects and will be identity-checked against
the actual bound method at native execution. Do not describe that as an already
observed native shutdown/lifecycle success. Main can now provide the installed
method source binding and exercise its detached fresh-process lifecycle.

Close is idempotent and always has `owned_group_released=null`, `gpu_vacant=null`,
`outer_release_required=true`. No new /proc/env fallback, kill policy, SSH handling
or C11 guard was added. The native loader permits only one engine from this module
per process and never resets for another arm. This does not authenticate the
entire prior process history: Main owns truly fresh processes and exact isolation.

Actor timings include synchronous identity/load/generation/close operation
intervals, not GPU-active time. The absolute deadline covers waits between calls;
Main's outer hard timeout covers blocking engine creation/generation/shutdown,
process teardown and cold-to-release accounting. In-process checks cannot
interrupt a blocked native method or certify OS/GPU release. Existing C0 reports,
failed finalizers and mid-run custody sidecars are not amended or reinterpreted.

## CPU validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_astra_pcfl_own_write_readout -q
```

**33 tests PASS, 0.718s.** AST and trailing-whitespace checks pass on both new
files. Fixtures use tiny synthetic base/adapter files, fake model modules and
injected sessions; no real model/tokenizer/native stack is loaded. Tests cover:

- both actual loader call shapes, enabled engine parity, LoRARequest fields and
  None route, nested EngineCore shutdown rather than LLM.shutdown;
- source-withdrawn W0/W8 prompts and rejection of extra request/roster data;
- an unmocked existing public CPU memory scorer over a captured synthetic
  response, with its expected target kept outside actor input;
- exact raw bytes/tokens, route disagreement, cardinality/decode-related input
  identity, length termination, caps, deadline, no retry and fresh outputs;
- base/source/environment/tokenizer/adapter drift, wrong rank, extra artifact
  files, overlapping output, shutdown source mismatch/missing method/failure;
- no release assertion, idempotent close, and native-loader same-process reuse
  rejection. Existing actor tests are not rerun; only their synthetic Clock and
  Tokenizer helpers are imported.

No scientific acquisition/persistence result, multi-seed finding, parenting,
H1/H2, route-reasoning, general-G3, clean-ancestry, mechanism-freeze or full-mission
claim follows from this readout seam. Main retains integration and native/scientific
decisions. EDITSTOP on the two source/test hashes above.
