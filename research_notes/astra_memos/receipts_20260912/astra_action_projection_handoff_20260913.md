# Exploratory action-projection formation — CPU complete, EDITSTOP

Implementation follows `research_notes/analysis/2026-09-13_formation_interface_rootcause.md`.
No fit, launch, native tokenizer/model/GPU, Git, network, runtime/collector changes or
formal C11 framework. No Q0/clean-Level-2 integration. Carver's files were not edited.

## Exact changed paths

1. `organism_v6/rulegame_action_projection.py` — NEW171-line explicit task/formation
   interface, public tentative history, shared five-slot projection, descriptive metrics.
2. `tests/test_rulegame_action_projection.py` — NEW13 focused CPU tests and six exact
   archived invalid raw strings as parser-regression fixtures.
3. `organism_v6/born_rulegame_formation.py` — versioned opt-in binding, AUTH/OFF routing,
   same capture/replay APIs; original default binding/behavior preserved.
4. `tests/test_born_rulegame_formation.py` — original21 tests retained plus9 new binding,
   role, replay, visibility and mocked-native tests; native fixture also supports OFF.
5. `/tmp/astra_action_projection_handoff_20260913.md` — this handoff only.

`organism_v6/rulegame_parenting_diagnostic.py` was NEVER edited. No task_runner injection.
Its SHA256 remains `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
Original process selector SHA256 remains
`a060f11165e68baa9baaf50433e157e2b3d348a3577e4fbc8ba540d269c24168`;
birth corpus remains `43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b`.
These unchanged original dependencies preserve the cross-snapshot birth custody check.

## Main integration: explicit opt-in, no new launcher

Use the genuine normalized completed/released AUTH pin already validated by Main
(e.g. from the accepted formation plan); this module does not revalidate the birth
runner's terminal/release artifacts. Continue the existing original-pin/base/source
verification before constructing a binding. No fabricated OFF birth adapter/pin.

```python
from organism_v6 import born_rulegame_formation as role
from organism_v6 import rulegame_action_projection as projection
from organism_v6 import rulegame_parenting_diagnostic as diagnostic

auth_binding = role.make_binding(
    normalized['pin'], expected_birth_pin_sha256=normalized['pin_sha256'],
    interface=projection.INTERFACE, child_mode='AUTH')
off_binding = role.make_binding(
    normalized['pin'], expected_birth_pin_sha256=normalized['pin_sha256'],
    interface=projection.INTERFACE, child_mode='OFF')
binding_sha256 = diagnostic.value_hash(auth_binding)  # separately hash OFF binding
```

`interface='rulegame_action_projection_v1'` AND `child_mode='AUTH'|'OFF'` are required
for the new `born_rulegame_formation_action_projection_v1` schema. Both bindings
retain the actual completed-AUTH reference for matched base custody; OFF's served
role identities have adapter_input=None/adapter_files={} for EVERY role. AUTH serves
its genuine adapter to wake/record/restate; parent remains OFF. No mutable engine
switch, synthetic LoRA, newly trained adapter, or new generation role is introduced.

Existing `make_binding(pin, expected_birth_pin_sha256=...)` with no new arguments
still emits EXACT original schema/fields/role identities and runs the original
`diagnostic.run_formation`. A child_mode without the interface is rejected.

Existing APIs continue:

```python
# backend creation/allow_gpu remains exclusively Main's native integration.
capture = role.capture_formation(
    backend, binding, expected_binding_sha256=diagnostic.value_hash(binding),
    cutoff=monotonic_cutoff)
checked = role.replay_formation(
    capture, binding, expected_binding_sha256=diagnostic.value_hash(binding),
    cutoff=monotonic_cutoff)
```

`NativeRoleBackend(binding, expected_binding_sha256=..., allow_gpu=True)` loads ONE
engine for that immutable binding. OFF constructs NativeBackend(model,None), never
constructs _LoRARequest, and uses lora_request=None on every generation. AUTH uses
the existing born_child/id1/path request except parent=None. Missing AUTH LoRA and
synthetic OFF handles fail closed. Role identities/routes are checked per raw call
and during replay. No native constructor was invoked outside mocks in this work.

Main must version its driver/role-hash/schema/inventory handling separately; frozen
old drivers and captures remain immutable. Include the new projection module in the
new source snapshot. New opt-in bindings hash that source explicitly; old default
bindings do not silently acquire a new interface. Old source-bound captures cannot
be resealed/reinterpreted as this variant. There is no new CLI or runtime in this patch.

## Fresh task and budget contract

`projection.schedule()` declares four development IDs, each used once in P and A:
`rule{0|1}/astra-action-projection-v1-20260913/lesson{0|1}/{pre|apply}`.
The existing two-rule/two-lesson P/A task topology and RuleGame evaluator/quiz grading
are reused, but the explicit NEW namespace produces fresh quiz instances and derived
seeds. Evaluation schedule is empty; no Q0/current-formation tasks are overwritten.
AUTH/OFF use identical declared schedules and existing role seed derivation/settings;
adaptive prompts/call counts may differ when the actual children respond differently.
Tests prove identical requests under identical scripted outputs, not equal live traces.

Projection is still role='wake', with the ordinary wake seed for its actual tick and
400-token cap. No separate projection allowance. An invalid at tick n dispatches
nothing; its single projection uses tick n+1 from the SAME5slots. A second invalid
is terminal; invalid at tick5 has no projection. A later independent invalid after
a successful projection can use its own next slot, still never exceeding5 total.
Maximum per binding stays40wake/12record/4parent/4restate=60calls, with unchanged
caps400/100/200/120 (18480output-token ceiling). These are ceilings, not observed cost.
Main retains actual controller/worker600s/cleanup140s/deadline/reservation/release
ownership. The monotonic cutoff cannot itself interrupt a blocked model call.

## Parser, public visibility and causal records

No first-marker salvage, output filtering, appended restatement, target rewriting,
new world/scorer, or source-slot substitution. BOTH original and projected outputs
use the UNCHANGED `parse_action(...,'interaction_v3')` and existing TRY/reveal state
checks. Accordingly registered aliases remain legal, DONE ends without world action,
and missing PREDICT may still be a valid world action but not valid process-v2 write
material. The projection prompt requests canonical ACT and preceding PREDICT; it does
not weaken OR secretly strengthen the registered parser. DONE is not recovery.

Invalid raw text is retained verbatim in the raw call and a protocol_invalid event,
with tentative=True/executed=False. Public history wraps it in explicit
UNEXECUTED_PROPOSAL/NO ACTION OR WORLD RESULT markers. Projection receives that exact
current public history, exact invalid text and one-action instructions only; no
hidden rule/panel, later response, birth score or fabricated result is supplied.
If the invalid text itself contains a fabricated OUTCOME string, it stays inside
the explicitly unexecuted block; only execution events represent actual world effects.

The valid projection is a separate raw call, with an execution event joined by
projection_of=<original invalid call_id>; record_prompt uses ONLY that actual executed
response/outcome. Records never become wake history. Parent/restatement content is
unchanged, including a raw birth-dialect restatement; no quoting/filtering amendment
is slipped in. Parent helpers, neutral-control prompt and4000-character transcript
tail remain original. Tentative end markers also state no execution; markers are not
semantic certification or an injection-proof interpretation of arbitrary raw text.

Both raw generations, role identities/routes, request/response hashes, times, native
tokens and actual execution/record joins remain captured. Replay reproduces every
request/world/event/result. Forged execution for a tentative response, edited invalid
raw text, changed projection tick, wrong child route or wrong source fails replay.
Backend failure raises existing FormationFailure with preserved partial raw calls;
ordinary protocol-invalid tasks remain present rather than replaced.

## Metrics, audit and limits

New result.interface_metrics[P|A] reports numerator/denominator pairs for:
- original_valid: original responses passing unchanged parser AND state checks
  (includes DONE as valid termination), divided by original wake attempts;
- projection_recovery: projections producing an ACT world execution, divided by
  projection attempts; DONE and invalid projections do not recover;
- final_quiz_valid: valid scored quizzes divided by all four tasks in that arm;
- record_fidelity: eligible records divided by actual record requests.
It also reports original/projected invalids, last-slot invalids without opportunity,
wake/world/TRY counts. Zero denominators remain zero, not automatic success.

Parent semantic audit remains required. Invented recaps/false process diagnoses are
NOT auto-approved or repaired: result.parent_recaps_verified=False and
semantic_no_answer_certification=False regardless of syntax/replay success. Existing
main_audit_contract is retained. Main must reject inaccurate recaps scientifically.

New source namespace/schema are intentionally NOT drop-in legacy process material.
Prescribed old selectors remain untouched; do not relabel IDs or synthesize slots to
make them accept these traces. No write/readout/fit chain is implemented or authorized.
Capture/replay correctness is not efficacy, policy validity, useful selection,
parenting, retention, learning, Q0, clean Level2, H1/H2 or clean-lineage evidence.

## CPU validation and exact commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_rulegame_action_projection test_born_rulegame_formation \
  test_rulegame_parenting_diagnostic test_rulegame_process_material \
  test_rulegame_record_material -q
```

164 tests PASS in97.032s. After the final documentation-only role docstring update,
the43 focused/default role tests also PASS in2.108s:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_rulegame_action_projection test_born_rulegame_formation -q
```

Includes all21 original role tests, golden equality against original interaction_v3,
six exact invalid-parser regressions, no-world-before-projection spies, strict invalid
and state-budget cases, raw public visibility goldens, five-slot/no-third-retry tests,
record truth, P/A visibility/no recap certification, AUTH/OFF request/route fixtures,
source/schedule rejection and raw/execution replay tampering. Native route tests use
mock engines/tokenizers only; no installed/native model evidence is claimed.

## Frozen SHA256

- projection module: `47564a630b166cadda546ac5ae65c79bd9ca223a8574b0cfc693d6bc0177ad19`
- projection tests: `a4edcf6e19b2283f2cb4b91a23593b3a2437618b87a8ee54211af69c6694e2a9`
- born role module: `2cb24cf0447d3e5a7d8e61c9a0a65658e033f2c0bfc01b4b60ae15bce437a945`
- born role tests: `d3987ce3a24554b7cce8be76822dcb00579603acf0d0c647f2f0f1ef99ee4753`

EDITSTOP. Main owns reviewed source snapshot, new driver/launcher binding, native
tests and any scheduling. Original pinned diagnostic/source inventory is preserved.
