# Fixed-coaching record core — native lifecycle handoff, 2026-09-13

**EDITSTOP. Core only; native lifecycle/writer belong to Main/Beauvoir.** No fit, tokenizer/model load, GPU/native operation, network, collection, Git or repository edit. Original proposal and all frozen helpers remain unchanged. Tests use synthetic DEV backend replies only; no confirmation response/world execution was generated.

## Frozen files

- `/tmp/astra_parented_record_core_20260913.py` SHA256 `68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688`.
- `/tmp/test_astra_parented_record_core_20260913.py` SHA256 `82ff272a7eb084156092b0a8fcf86b943dee28688bfeda7a83acd082cb3aa1da`.
- Protocol `research_notes/astra_memos/ASTRA_PARENTED_RECORD_DEV_2026-09-13.md` SHA256 `bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964`. This supersedes the generative-parent proposal. Contact literals are the exact single-line strings from Main, not Markdown line wrapping.
- Schedule SHA256 `b251dec197f94d35960367f723f833f5ef0689396da36a8bff6e1d5400cb08c2`: 36 disjoint DEV/CONF pre/apply/held IDs, as previously proposed. Confirmation execution requires explicit `split="confirm"`; default is DEV.

## Stable API

```python
load_dependencies(source_root=SOURCE_ROOT, *, core_path=V2_PATH,
                  memory_path=MEMORY_PATH, protocol_path=None)
contract(dependencies) -> dict
build_manifest(dependencies=None, *, prior_episode_ids=()) -> dict
schedule() -> {"dev": {"pre": list, "apply": [list, list], "held": list},
               "confirm": {"pre": list, "apply": [list, list], "held": list}}
episode_ids(split="dev", phase="formation") -> tuple[str, ...]
check_disjointness(prior_episode_ids=()) -> dict
run_state(state, backend, *, phase="formation", split="dev",
          dependencies=None, binding=None) -> capture
run_formation(state, backend, *, split="dev", dependencies=None, binding=None)
run_held(state, backend, *, split="dev", dependencies=None, binding=None)
audit_capture(capture, *, dependencies=None) -> audit
project_capture(capture, *, dependencies=None) -> dataset
compare_states(captures, *, dependencies=None) -> descriptive_comparison
```

`phase` is exactly `formation` or `held`. State names are `perception_seed{0,1,2}_{P,N,INITIAL}`; INITIAL is held-only. `build_manifest` returns `{contract,disjointness}`. `contract` binds exact prompts, contacts, schema, source/dependency hashes, protocol hash, schedule, caps and visibility. Manifest does not certify allocation/model identity or complete cohort custody. Supply actual historical IDs to `check_disjointness`; no hidden exposure certification.

Capture schema: `astra_fixed_guidance_record_20260913_v1`. Export schema: `astra_fixed_guidance_source_withdrawn_20260913_v1`. `PROTOCOL="interaction_v3"` identifies the unchanged production parser/scorer, distinct from the pinned campaign document.

## Backend callback and capture layout

Backend takes **one request dict**, never positional prompt parameters:

```python
def backend(request):
    return {"request_id": request["request_id"], "state": request["state"],
            "raw": exact_decoded_text, "finish_reason": "stop", ...}
```

Optional additional response fields (e.g. `native_response`) remain in exact replayed evidence. Request fields: `state,split,phase,episode_id,stage,lesson,episode_index,tick,kind,input_messages,max_output_tokens,temperature,seed,source_execution_sha256,contact_sha256,request_id`. `stage` is pre/apply/held/restate; `kind` is wake/record/restate. Restatement tick is0 and its episode ID is that lesson's pre ID. No parent callback exists. Use `input_messages` verbatim, explicit native LoRA routing, native output caps and all request/response byte/token checks in the lifecycle.

Caps: wake96/record192 at temperature0; restate120 at temperature.5; generation seed0 across matched opportunities. Fixed contacts are logged as chained `kind="fixed_contact"` events, not model calls. Restatement raw text is retained even for length completion; absent nonstring raw yields empty restatement context, with original failure recorded. Neither case requests retry or suppresses scheduled apply work. Native hardware/backend errors remain the lifecycle's stopping responsibility.

Capture top-level: `schema,state,arm,phase,split,binding,contract,episodes,contacts,events,summary,qualification,native_identity_verified,automatic_pass,capture_sha256`.

- `episodes`: source order pre0, apply0×4, pre1, apply1×4 (or held×8). Each includes `episode_id,stage,lesson,episode_index,turns`. Each turn has `tick,wake,execution,record,score,status,errors`; uncalled records/scores are null, never fabricated zero-accuracy records.
- `contacts`: `{lesson,contact,restatement,apply_context_sha256}`; full generated child restatements and exact author messages preserved in audit capture only.
- `events`: frozen-v2 chained call/execution events plus fixed-contact events; record requests join current execution hashes. Replay reconstructs every request, actual world outcome, score and failure before exact whole-capture comparison.
- `summary`: actual calls/contacts, zero parent-model calls, reached executions, strict/content/production counts, fields, pre/apply/held and turn strata, input/output UTF-8 byte counts. **Bytes are not tokens**; lifecycle must report actual rendered/tokenized contact/prompt costs and unequal realized compute.

**Important protocol repair in this NEW core only:** legacy v2 earlier history includes derived `status` values such as `PRODUCTION_RECORD`/`RECORD_REJECTED`. They violate this protocol's no-eligibility-feedback rule. This core's `_history` retains raw wake, outcome, raw child record, finish reasons and attempt, but omits scorer/status fields. Original helpers are unchanged. Record construction/scoring otherwise reuses the original source-bound production interfaces. Apply prompts receive current contact/restatement; pre and held receive none. Held begins with a fresh episode-local history, and no formation capture is an input to `run_held`.

## Dataset/writer seam

`project_capture` reaudits formation, rejects any held capture, and examines exactly16 apply opportunities in fixed order. All source-faithful stop records are admitted, without selection by gains, canonicality, pre performance, target uniqueness or episode success. Fences/wrong fields/source mismatches do not qualify. Output preserves exact raw UTF-8 bytes and no target rewriting.

Dataset: `{schema,status,state,split,reason,rows,refused,counts,source_proof,qualification}`. `status` is `WRITE_AVAILABLE` or explicit `NO_WRITE`. Counts include all16 possible slots, n admitted,16−n refused, distinct targets/triples, episodes with admissions and excluded4pre slots/2restatements. No additional episodes on shortage. NO_WRITE is for the lifecycle to route to unchanged original tensors without fabricating a fit stage.

Each row: `{row_id,input_messages,paraphrase_input_messages,raw_target,target_sha256,encoding_contract,source}`. Source includes state/split/task/lesson/tick, public execution ID, full execution ID/hash, wake/record request IDs, record event hash and capture hash. Dataset-level provenance holds hashes, not parent/context prose. `input_messages` is the original source-withdrawn public-ID/schema cue; no case action/prior/outcome or coaching text. Only cue+raw target enters the encoder, not serialized provenance. `paraphrase_input_messages` is interface compatibility only: **this campaign does not schedule memory readback calls**.

Existing memory runner `encode_training(rows,tokenizer,trainer,helper,probe,fit_seed)` accepts this row shape, n≤16. It invokes the original TrainingItem/mask code and deterministic eight-pass ordering. Native worker must validate target+EOS/no truncation and warm-start tensors itself; this core does no encoding/fit. Never pass these new captures to the old hard-pinned projector, old root verifier or collector.

## Native source layout and limits

Import-time paths must exist with exact frozen bytes:

- `/tmp/astra_level1_real_record_core_20260913_v2.py`: `b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5`.
- `/tmp/astra_real_record_memory_core_20260913.py`: `2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef`.
- Under supplied `source_root`: `organism_v6/rulegame.py` (`88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3`) and `organism_v6/rulegame_parenting_diagnostic.py` (`e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`). Their pinned CPU definitions are loaded without importing native trainer dependencies.
- Protocol defaults to `source_root / PROTOCOL_RELATIVE`; `protocol_path` may name a separately deployed copy with the same SHA. Its actual location does not change the manifest.

Use the new module by explicit file import, or PYTHONPATH=/tmp for its module name. **Core dependency loading itself needs no PYTHONPATH change.** A native lifecycle importing organism_v6 trainer/probe packages must add its complete pinned source snapshot to PYTHONPATH separately; the two source files above suffice only for core CPU execution. The writer has additional dependencies and is not delivered here.

Formation maximum42calls/arm,84/pair; held32/state,96/seed; retention120/seed for the two descendants, historical original baseline imported. Total300/seed,900 across three seeds; zero parent-model calls. Native lifecycle enforces LR3e-5/eight passes, maximum128updates/arm and768total,7200s/seed including ≤180s collection, continuous consumed-budget accounting, owned finite cleanup and one-shot custody. No such native work occurs here.

## Validation

`PYTHONDONTWRITEBYTECODE=1 python3 /tmp/test_astra_parented_record_core_20260913.py -v`

**17 tests PASS in0.489s.** Covers exact contacts, all six formation identities, fixed namespaces without executing CONF, zero parent callbacks,42call ceilings, score-free history, temporary context and held/sleep isolation, variable admission, byte-preserved noncanonical records, wrong-prior/fenced/extra-field refusals, NO_WRITE with no replacement, source/order/contact/Boolean-count tampering, wrong joins, failed restatement handling, protocol pin and unchanged frozen globals. These are CPU fixtures, not native prefix/mask verification or evidence of learning.
