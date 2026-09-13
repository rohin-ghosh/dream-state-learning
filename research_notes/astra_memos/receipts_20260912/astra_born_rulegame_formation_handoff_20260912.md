# Born RuleGame level2 participation — EDITSTOP

September 12, 2026 local date. **CPU implementation complete; no native run or launch.**
Only `organism_v6/born_rulegame_formation.py`, `tests/test_born_rulegame_formation.py`
and this handoff were written. Read the assigned level2 advisory; did not edit
birth corpus/runner, historical diagnostic/backend, or any other worker's files.
This implements the authorized role-routing bridge, not a new task, scientific
criterion, C11 gate, curriculum, fit, native preparation or launch coordinator.
Main chooses whether to use it **after the birth component result**.

## Frozen interface

- `make_binding(birth_pin, *, expected_birth_pin_sha256) -> binding` (`:73`).
  Hash is `diagnostic.value_hash` over the normalized pin, **not** an assertion
  that this hash equals the raw birth result file's SHA. Sources, interaction_v3
  and all four per-role identities become externally hash-bindable in `binding`.
- `capture_formation(role_backend, binding, *, expected_binding_sha256, cutoff,
  clock=time.monotonic) -> capture` (`:195`). No file writes. Calls the existing
  `diagnostic.run_formation` unchanged, then replays its entire result before
  returning. Success status is `AWAITING_MAIN_AUDIT`, never scientific PASS.
- `replay_formation(capture, binding, *, expected_binding_sha256, cutoff)`
  (`:222`) reconstructs every exact request, public world event and record join,
  settings, seeds, call ordering, role identity/routing and result. No model or
  backend calls. Caller supplies the original monotonic cutoff as well as the
  external binding hash; capture cannot silently enlarge it.
- `RoleCalls` / `RoleReplay` (`:119`, `:159`) expose the versioned in-memory
  call layer, with `protocol="interaction_v3"`, `ask`, `count`, `counts`.
  Ordinary capture errors raise `FormationFailure` with `.partial`: retained
  requests, any returned raw responses, events and `result=None`; no replacement
  calls/retries. Invalid task/record outputs are retained normally, not rejected
  merely for poor performance. A failed RoleCalls object cannot continue.
- Injected role backend has `verify()`, `identity(role) -> exact identity`, and
  `generate(request) -> {response, loader_identity, loader_identity_sha256,
  lora_request}`. `response` retains existing native text/rendered prompt/token
  IDs/finish/stop fields. The route is **None** for parent, otherwise
  `{name: "born_child", id: 1, path: <exact pinned child adapter>}`.
- `NativeRoleBackend(binding, *, expected_binding_sha256, allow_gpu=False)`
  (`:240`) is the opt-in integration backend, **not a CLI**. Reuses the actual
  `diagnostic.NativeBackend` / `model_backend.VLLMBackend` constructors once,
  with child LoRA enabled. One immutable child LoRARequest is reused. Every
  parent generation explicitly passes `lora_request=None`; wake/restate/record
  pass that exact child request. There is no adapter-path/global switching,
  second teacher engine, teacher training, stacking, or online update.

## Completion pin: caller/runner integration obligation

The birth runner's evolving terminal layout is deliberately **not guessed or
parsed**. Its checked completed-fit integration must produce this exact minimal
normalized summary, bind it into its prospective immutable plan, and supply its
value hash. This is an interface, **not a second completion/science gate**:

```python
birth_pin = {
    "schema": "completed_birth_adapter_pin_v1",
    "status": "COMPLETE",
    "birth_arm": "AUTH",  # or DERANGED
    "birth_plan_sha256": "<real immutable birth plan SHA256>",
    "completion_receipt_sha256": "<real checked terminal receipt SHA256>",
    "child_identity": checked_completed_child_generation_identity,
    "model_files": checked_base_file_hashes,
    "origin": "SOURCE_AUTHORED_BIRTH_NOT_CLEAN",
    "model_origin": "UNRESOLVED_LOCAL_HASHES_ONLY",
}
binding = make_binding(birth_pin, expected_birth_pin_sha256=externally_bound_pin_hash)
```

`child_identity` is the exact existing `configured_generation_identity` shape:
local absolute model/adapter loader spellings, configuration and one weight-file
hash, and existing loader defaults/scope. Its adapter must be the one verified
against the completed birth fit, **not an arbitrary directory relabelled COMPLETE**.
The module rejects unknown/extra pin fields (including scores), invalid status,
missing custody hashes and adapter pins. It checks disk base/adapter hashes at
native construction and verification; child adapter hashes and engine loader
identity are also checked around requests. Parent derives from the same base
identity with adapter=None/files={}, identically across AUTH/DERANGED.

**Honest limit:** this module cannot establish that caller-supplied completion
hashes identify genuinely completed/released birth work. Main/birth runner must
verify that upstream link, recipe/source/model/adapter custody and full release.
Hash-bound normalized assertions are not model authentication or clean lineage.
No birth scores, material or terminal payloads are generation inputs.

## Unchanged behavior and visibility

One selected born child runs two lesson positions in each of P/A, fixed existing
pre/apply tasks: at most **60 calls** (wake40, record12, parent4, restate4), output
ceiling18,480 tokens. Requests keep original temperature, seed salts, token caps,
stop strings and full-JSON relation definition. Both teacher arms use OFF base:
P process guidance, A the existing interaction_v3 neutral/optional accurate-recap
contract; child restatement unrestricted in both. No favorable reselection or
synthetic targets. No write/export/sleep operation exists in this module.

The equivalence regression compares **every request, result and event** to the
original single-identity interaction_v3 execution with scripted output. Real
role-aware replay enforces parent/pre-task and wake/record/world joins, rejects
rehashed prompt/seed/protocol/identity/routing tampering, and requires exact call
cardinality. Raw generated text, including whitespace and invalid material, is
not stripped, repaired, reserialized or replaced.

**Visibility clarification surfaced during implementation:** original
`play_task` appends public `quiz score: ...` feedback to the pre-task transcript;
original `run_formation` gives that transcript to the parent. The test explicitly
preserves this. No birth/dev/sealed/later-evaluation score or score metadata is
added to the teacher. Thus “no score to teacher” is satisfied for those excluded
scores, **not** interpreted as removing already-public pre-task world feedback.
If Main intends to exclude even that public feedback, that would conflict with
the requested unchanged formation behavior; no silent change was made here.

Role identities/routing in receipts describe actual configured generation calls,
not semantic nonleakage certification. The nested diagnostic result intentionally
remains byte-equivalent to its original result (including its inherited generic
claim-boundary string); the capture's outer boundary explicitly limits this
component to **participation/in-context interaction only, zero writes**.
Source-authored birth is NOT CLEAN; model origin remains UNRESOLVED. No P1/G3,
retained learning, parenting efficacy, G5/H1/H2 or format-proof promotion.

## CPU validation and remaining native integration

Final new suite: **21/21 PASS in1.639s**. Unchanged diagnostic suite:
**46/46 PASS in16.139s**, including strict_v1/v2 historical request hashes,
interaction_v3 and legacy single-identity flows. Both new files AST-parse.
Initial19-test run had one test-string capitalization mismatch; corrected only
that assertion, reran19green, then added two stronger constructor/partial-failure
regressions for the final21. No source behavior was changed to satisfy a failure.

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
  python3 -B -m unittest discover -s tests -p test_born_rulegame_formation.py -v
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
  python3 -B -m unittest discover -s tests -p test_rulegame_parenting_diagnostic.py -v
```

Tests exercise actual original constructor chains with **mocked** vLLM LLM,
SamplingParams and LoRARequest, proving one engine configured enable_lora=True
and parent None versus exact child object for all roles. Native token/rendering/
stop/cardinality checks run against a CPU character-tokenizer fixture. Other
cases cover AUTH/DERANGED teacher identity equality, changed base/adapter/route,
all role caps, cutoff before/after generation, partial exceptions, changed loader
after generation, missing/extra calls, wrong provenance and invalid records/tasks.

**Not executed:** real vLLM loading/generation/tokenization, a completed-birth
artifact check, native process/session cleanup, or participation outcomes.
Main's eventual supervised integration still needs to verify real one-engine
OFF/child routing and token receipts, consume actual checked completion pins,
and own external deadlines/lease/device/process cleanup. The monotonic cutoff
checks cannot interrupt a blocked native call. In-memory partials are not durable
crash artifacts; the integrating runner owns persistence/sealing and hard-stop
custody. Replay by itself checks token shapes/caps, not independent tokenizer
re-encoding; NativeRoleBackend checks exact rendered/input/output token alignment
at generation. Native postcapture audit/external capture hashes remain runner
responsibilities. This version is **not** drop-in input to legacy single-identity
`check_capture`, `audit_native_calls`, exporters or runners; no such integration
is claimed or implemented.

## Exact hashes

- New module: `918b9d46bdb68423d8fe28c6ae92bde27aa4b47d183b72727f88767c36c6376e`
- New tests: `af01f91f39e3ef0a7363106af1d0bbd2c53453a46fa6e37fcdf99ac0813d3abe`
- Read-only diagnostic, unchanged from inspection:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`
- Read-only model_backend, unchanged from inspection:
  `93feee1cb30720b565aac8f570d368cad8e137789b39f228fbd8ed264123a3f5`

No Git, SSH/network, GPU/native/model execution or other implementation edits.
**EDITSTOP. Main retains integration and launch authority; no launch implied.**
