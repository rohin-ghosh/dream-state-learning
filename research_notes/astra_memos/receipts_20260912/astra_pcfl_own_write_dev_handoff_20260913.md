# OLD own-write formation interface — September 13, 2026

Formation implemented; final pins/test receipt below. No native launch or numerical writer.
Coordination for Main/Meitner: the new training module should consume the
following explicit seam rather than infer payloads from the older runtime.

## Implemented API

`build_config(cell, actions, link_choices, *, actor_config, seed, limits)`
returns a detached sealed config (`sha256`). Choices have no defaults and use
the existing planner's actual OLD chronology. `actor_config` is the existing
NativeActor closed config, with max_calls exactly 20 and C0 only. `limits` is
one fixed existing NativeActor request-limits dict used at every opportunity.
No replay/schedule selection is implemented in formation; training owns the
17 first blocks + three deterministic authentic EVENT replay selection.

Hash seam: driver `canonical(value)` is the existing NativeActor UTF-8 sorted
compact JSON encoding (`ensure_ascii=False`, finite floats allowed);
`digest(value)` SHA-256s those bytes. Config/report internal seals and capture
hashes use this encoding. The nested planner keeps its original core seal;
raw generation SHA-256 is always the actual UTF-8 raw response bytes. Do not
use the pure world's no-floats canonicalizer on native timing/config receipts.

Read Meitner's `/tmp/astra_pcfl_own_write_train_handoff_20260913.md`: the
proposed `build_fit(config, config_sha256, report, report_sha256, schedule,
schedule_sha256, binding, native_receipts)` seam is compatible. Formation does
not close the actor; Main supplies independent native config/identity/load/
close receipts after its lifecycle closes. Schedule must be sealed before
generation by Main; formation neither selects nor owns its three replay rows.

`run_formation(config, expected_sha256, actor, out, *, receipt_reader=None)`
calls only `actor.generate(request, limits)`. It does not start/close/launch an
actor, fit, reload, or release a GPU. It creates a fresh archive before the
first call. Default receipt reader reads the existing actor output sidecars;
an injected reader is available for CPU tests. The returned summary alone is
not sufficient because NativeActor returns no finish reason or token IDs.

`replay_validate(config, expected_sha256, report)` independently reconstructs
public prompts, chronology, world outcomes, admission and payload joins from
the archived captures, without model calls or a full execution contract.

## Successful report seam for scoped training

Report contains `status`, `config_sha256`, 20 fixed `slots` (attempted, failed,
or uncalled), actual `world_receipts`, `admissions`, `formation_binding`, and
`writer_payload`, plus an internal `sha256` seal. A failed formation has no
writer payload. No missing rows or targets are invented.

`writer_payload` has:

```text
rows                 exact core CHILD_SUBMISSION rows
queries              exact core.materialize_queries(rows)
generations          [{raw, sha256, origin, capture_sha256}] for 12 EVENT/LINK outputs
controls             []
first_block_slots    unchanged planner.first_block_slots (17; no replay slots)
```

`capture_sha256` binds the complete archived native per-call capture and its
original sidecar bytes, not a synthetic placeholder. Whole response UTF-8
span only. Native generation origin is `CHILD_NATIVE`; injected CPU receipts
use `CHILD_INJECTED_CPU_TEST` and cannot be presented as native evidence.
Keep the report and sealed config alongside payloads so training can invoke
`replay_validate` and bind model/source/capture receipts independently.

`native_custody_verified=False` always: this module proves local byte joins,
not remote process identity or GPU release. Reported native-vs-injected kind
is receipt evidence, not a grant of native write authorization. Main's native
adapter must independently bind the actor's config/identity/files and release.

Prompt policy is fixed public session history: formation system; each real
explore prompt; child's exact action; actual public receipt plus EVENT prompt;
child's exact EVENT; subsequent prompts; four LINK prompts and exact outputs.
No private planner banks, expected rows, parent text or oracle text are sent.
Stop-only admission; any malformed output, source/receipt mismatch or differing
predeclared action/link choice ends formation with remaining slots uncalled.
All failures remain archived. No actor generation retry or corpus reselection.

## Integration note for Meitner/Main: cold start

The new writer's inspected `_native_binding` currently compares every raw
`operation_started >= load.ready_at`. That rejects a real first cold call:
NativeActor starts its operation clock before loading. Check
`generation_started >= load.ready_at` instead, retaining
`operation_started <= generation_started <= generation_ended`. Formation now
has a regression using the real injected NativeActor with a two-second cold
load and proves this distinction. No writer/actor source was edited here.

The driver's `device_seconds` sums returned actor operation intervals, including
first cold load, not total outer/release time or measured GPU active time.
Main still owns absolute deadline/outer timeout/cleanup/close receipts. Do not
pre-start this dedicated actor: `run_formation` requires its output directory
to be absent and it lazily starts on the first generate. `out` must be a fresh
sibling/disjoint directory with an existing parent, not inside the actor/model.

## Concrete archive and replay contract

- `config.json` is written before the first request. It seals source files,
  planner choices/bank, seed, actor config and fixed limits. The actor config
  must include every absolute path/hash returned by `source_pins()` in its
  `source_files`; Main builds these after copying the source snapshot. No
  config/action/link choices are inferred from a response.
- `call_00.request.json` through at most `call_19.request.json` precede their
  one-shot calls. Each corresponding `call_XX.attempt.json` retains request,
  limits, returned summary, sidecar capture and any backend/reader error.
- `formation.json` is the sealed complete or failed report. All 20 slots remain
  present. Fail-fast leaves later slots `UNCALLED`; possible EVENT/LINK counts
  remain 8/4. No failed report has a writer payload. A valid but different
  EXPLORE creates its actual public receipt then fails the sealed-choice check;
  an invalid EXPLORE has no receipt; a non-stop EXPLORE is never executed.
- Capture schema: `{schema, index, files}`. Each file value is
  `{utf8, sha256}`, preserving its exact original JSON file bytes, including
  whitespace. Successful captures contain `config.json`, `identity.json`, and
  that call's `request/render/raw/response.json`; failure captures may be
  partial and retain `error.json`. Each file is bounded to 4 MiB when read.
- `_capture_data(capture,index)` is the explicitly reusable validated parsed
  sidecar seam used by Meitner's native lifecycle binding and tokenizer checks.
  Successful formation crosschecks exact request/limits, source/model/route
  declarations, one unchanged identity receipt, sampling, raw/summary/decoded
  bytes, prompt/output token IDs/counts and finite ordered timings. No missing
  finish record is interpreted as stop. Parsing the metadata never parses or
  rewrites the child's EVENT/LINK text before the real core admission.
- The report's `formation_binding` is the exact result of
  `planner.bind_child(...)`, without a full contract. It includes real core
  formation/admission/query checks but `preparer_binding=None`. The scoped
  writer separately validates its own schedule/bank; there is no synthetic
  full-preparer success receipt. `replay_validate` accepts an honestly failed
  archive as replay-valid, not as write-eligible.
- Source changes detected at the final config check leave existing attempts
  intact and create `formation_failure.json`, then raise. Caller still closes
  the actor. Interrupted/native sidecars remain in the bound actor directory.

This helper does not independently decode model tokens or re-render the actual
tokenizer. It verifies the existing actor's archived token joins; scoped writer
`encode_fit` additionally re-renders/re-decodes with the bound actual tokenizer.
Likewise `NATIVE` is the receipt's declared origin, not a signed process proof.
CPU tests produce `CHILD_INJECTED_CPU_TEST`, never native supervision. Main
must preserve independent lifecycle/source/model receipts before native use.

## EDITSTOP — owned bytes and CPU validation

| File | SHA-256 |
|---|---|
| `gpu/astra_pcfl_own_write_dev.py` | `caba37d1fb8696c16f22e5bf714648fd3446be85a89c48e7eaa4abcfe94a24d2` |
| `tests/test_astra_pcfl_own_write_dev.py` | `cc3be61058efe5d1c8fcf65c0eda0c9a9897b9754ab493ca70c926f97632fbd8` |

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 -m unittest discover -s tests -p test_astra_pcfl_own_write_dev.py -q
```

Final focused result: **27 tests PASS, 7.576 s**. Additional unchanged dependency
suites: **32 native-actor CPU tests PASS, .567 s** and **13 formation-planner
tests PASS, 3.953 s**. No native model loads: tests inject a synthetic session
into the real lazy NativeActor, with synthetic model/tokenizer files.

Coverage includes e5=Z/Y and e7=B remaining port, alternate sealed choices,
valid action mismatch and invalid action, length action/EVENT failures, fenced
and missing-LF output rejection, wrong receipts and LINK pairs, exact public
history/no parent or oracle fields, pre-output archive seal, no actor reuse,
byte/hash/token/identity/route/timing drift, missing finish sidecars, no target
or taint substitution, fixed failure denominators, cold-load timing, and no
full writer gate/numerical-fit invocation. Initial development runs exposed
and fixed native float-receipt canonicalization and deterministic failure
message ordering; no native or scientific attempt occurred.

No other source, protocol, old capture, old scorer or result was modified.
No C0 outcome, final gym, network, model, native process, launch, or commit was
accessed/executed. Main integrates allocation and the independently owned
schedule/writer/cold-readout later; this is formation-only EDITSTOP.
