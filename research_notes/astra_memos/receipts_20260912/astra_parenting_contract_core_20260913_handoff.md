# Explicit-contract core — CPU implementation EDITSTOP

September 13, 2026. Canonical CPU-only protocol now bound:
`research_notes/astra_memos/ASTRA_PARENTING_CONTRACT_DEV_2026-09-13.md`, SHA256
`74b62e8ca4ba79e796f8fc666e065613758297fbd4610fd5bf3788d4da772572`.
Core-only implementation; no native allocation, launch, fitting, training export
or changes to frozen sources. This supersedes the pre-protocol core/test pins
`1ecc9701...` / `ced8ff2...`: only canonical pin/defaults, literal instruction and
typed-template alignment, declared budget metadata and their CPU fixtures were
added. No scientific gate or dispatch relaxation. Main reassesses direct-PCFL
priority; this source freeze is not execution authorization.

## Frozen paths, hashes and tests

- `/tmp/astra_parenting_contract_core_20260913.py` SHA256
  `a4790182668a93264118e4780aa759e9c7f672e0ba2fab2d906a34cfad0957e4`.
- `/tmp/test_astra_parenting_contract_core_20260913.py` SHA256
  `119403a395cfe3b2664f779a55ef8752037314eed4be87aabdb54fe0cd253da7`.
- This handoff is the third and only other owned file. Frozen alignment core
  `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`
  and parented core
  `68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688`
  were checked unchanged after implementation.

**23 CPU fixture tests PASS,0.733s.** Actual frozen CPU RuleGame/parser with
scripted responses; no model/tokenizer/native lifecycle. Tests include all9
states/180calls and raw replay; public-world and factor balance; exact neutral
contacts/current-restatement-only contexts; noncanonical JSON; metadata
content/schema separation; missing fields; no alias/nested extraction;
duplicate keys, NaN and exponent-overflow nonfinite JSON; receipt splicing;
null fresh prediction; all-invalid/empty/partial denominators; backend failures;
wrong routes/producers and re-signed request/world/score tampering. Tests use an
exact byte copy of Main's canonical protocol and reject unrelated self-pinned
protocols. All20 assembled seed0 ALIGNED fixture requests are pinned together
as `f111e6c22b14179ff4fa19268c73eab3609b383bf3d81b6ab730fd26ddf9e53f`.
Canonical protocol instruction literals and typed templates are in the manifest.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp python3 -m unittest -v test_astra_parenting_contract_core_20260913
```

## Implemented API

- `load_dependencies(source_root=SOURCE_ROOT, *, protocol_path,
  protocol_sha256, parented_path=PARENTED_PATH,
  alignment_path=ALIGNMENT_PATH)` verifies exact supplied protocol bytes and
  pinned frozen helper modules, returning `game_class, interface, parented,
  manifest`. Protocol arguments now default to Main's canonical repository
  path and fixed SHA. An alternate deployment path must contain the same exact
  bytes; any noncanonical SHA is rejected, even if it matches that file.
  Runner may continue passing both protocol fields from its bound spec.
- `build_manifest(dependencies, *, prior_task_ids=(), prior_ids=None,
  prior_task_fingerprints=())`: shared8-task schedule under keys `0/1/2`;
  task/world/public receipt IDs shared across seeds, child receipt IDs distinct
  by state. New schema/namespace; original three parent plan/weight pins.
- `tasks_for_seed(seed, deps)` returns identical task content/order for0/1/2:
  P-P-C-C-C-C-P-P, block sizes2, four P prior/outcome combinations, four C
  latest-display-position/outcome combinations. All public outcomes use the
  frozen CPU world. Prior IDs/fingerprints checked where supplied.
- `run_phase(state, backend, deps, *, binding=None)` and
  `run_state(state, backend, *, dependencies, binding=None)` retain the old
  callback form. States `perception_seedN_ALIGNED`, `_SWAPPED`,
  `_ACTIVE_NEUTRAL`; backend(request)->{request_id,state,raw,finish_reason,...}.
  Four contact/restatement calls in EVERY arm; eight wakes, at most eight
  records, maximum20calls/arm,60/seed,180total. No lexical restatement gate.
- `replay_validate(capture,deps)` / `audit_capture(capture,*,dependencies)`
  reconstruct exact requests, raw responses, world events and scores. This is
  CPU replay, not native route/model verification.
- `score_note(note,task)`, `score_wake(raw,finish_reason,task,errors=())`,
  `score_record(raw,finish_reason,task,execution,deps,errors=())` expose exact
  required-field presence/type/content separately from schema. Extras cannot
  block correct known-path content; no alias/recursive extraction; duplicate
  keys reject. Strict action dispatch remains closed-schema.
- `readout(records,contacts,events)` retains `PROCESS_USE`, `EXECUTED`,
  `RECORD_FAITHFUL`, `FULL_MATERIAL`, with the last two meaning required-path
  CONTENT in this NEW version. Adds schema-compliant endpoints and record-source,
  own-event/address fields; all8 slots/4per family retained. `RESTATE=None`,
  `restate_mask=None`; completion is separately reported, never lexical success.
- `summarize(captures,deps)` / `threshold_vector(cells)` report complete/missing
  cells and per-root A−S/A−ACTIVE_NEUTRAL contrasts, NO adopted feasibility
  thresholds or scientific pass. `automatic_pass=False`, `fit_authorized=False`.

## Native runner integration differences

Retain original producer binding and frozen-world/helper checks. Change arm
inventory to ACTIVE_NEUTRAL, all arm caps20, tasks8, blocks4×2, calls60/180.
Do not keep old16-task denominators, NO_PARENT special-cases or lexical gate.
Prepare must tokenize all P/C/NEUTRAL restatement prompts plus explicit family
task instructions and retain actual costs. Existing output caps restate160,
wake256, record384; temperature0, generation seed0. Dynamic assembled-context
token checks remain runner-owned; no truncation or output repair.

Keep `PARENTED_PATH/PARENTED_SHA256`, `root_binding`, existing request metadata,
capture `events/contacts/records/readout/summary`, and root/state identities as
before. Add frozen `ALIGNMENT_PATH=/tmp/astra_parenting_alignment_core_20260913.py`
SHA `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`
to deployment and source snapshots. It is reused for pure utilities/world
dispatch only, without edits/global monkeypatching or its old protocol loader.
The parented core still imports its frozen V2 and memory dependencies at their
declared `/tmp` paths; the existing source root supplies pinned repository
Python modules. Preserve that dependency layout; no new external package.

Exact neutral string:
`Continue with the next scheduled tasks using their instructions. Briefly acknowledge this message before proceeding.`

## Capture/readout semantics and integration cautions

Schema `astra_parenting_contract_dev_20260913_v1`. `manifest_sha256` hashes the
canonical manifest without that self-hash field; captures use the same rule for
`capture_sha256`. Runtime capture builds the core's inventory-free manifest,
as the old core did; runner's saved manifest also binds its supplied prior
inventory and must be checked independently. Do not equate file-byte SHA with
the canonical internal manifest hash.

Each record row keeps exact `wake/request/response`, `wake_score`, real
`execution`, optional `record/request/response`, `record_score`, and endpoint
Booleans. Public-event probes and actual child receipt retain independent
source joins and hash-chain events. No answer rewriting or training export.

Readout endpoints: PROCESS_USE, EXECUTED, RECORD_SOURCE, OWN_EVENT, ADDRESS,
RECORD_FAITHFUL, FULL_MATERIAL, WAKE_SCHEMA, RECORD_SCHEMA,
SCHEMA_FULL_MATERIAL. CONTENT endpoints require normal completion and no call
errors. Schema columns describe structure independently of finish. FULL_MATERIAL
is public-content plus full record-content; SCHEMA_FULL_MATERIAL additionally
requires wake/record schema. Neither requires a successful lexical restatement.
Canonical serialization is a separate raw-string flag, not a content gate.

`per_field` contains eight ordered slots for public_note/record_source/own_event/
address, with present/type_valid/correct/status at each declared field.
Uncalled/unattempted slots have null fields and explicit status; undecodable
outputs have unassessable field statuses, not inferred factual errors.
`by_family_delivery` denominator2, `by_family` denominator4 and total8 never
shrink. Missing/incomplete states appear in descriptive `threshold_vector`;
`feasibility_pass=None`, `thresholds_adopted=False`, no inherited SEQ160 floors.

The frozen event judge is additionally exposed on a declared required-field
projection as a diagnostic, not repair of raw output or an alternate source
scorer. Source content only uses exact note/source paths; wrong source and
correct new event are separately visible. Unknown keys—including nested
metadata—cannot mask correct required-path content, but fail schema. Strict
dispatch still rejects unknown wake-outer/action keys and null predictions.

Native preflight must change its lesson-key assertion to P/C/NEUTRAL and must
not calculate a matched arm's contact tokens as twice the sum of all3 lessons:
ALIGNED/SWAPPED each receive2P+2C; ACTIVE_NEUTRAL receives4NEUTRAL. All4 child
restatements count. Actual tokens/elapsed times are runner-owned; the core
reports UTF8 bytes only. Its explicit prompts are longer: check static and
every dynamic context with the original tokenizer/model limit before calls.

Protocol binding call for the runner (values from Main's already pinned spec):

```python
dependencies = core.load_dependencies(
    spec["source_root"],
    protocol_path=spec["protocol"]["path"],
    protocol_sha256=spec["protocol"]["sha256"],
)
manifest = core.build_manifest(dependencies, prior_ids=prior_inventory)
capture = core.run_phase(state, backend, dependencies, binding=identity)
audit = core.replay_validate(capture, dependencies)
```

Declared optional-execution ceilings in `manifest.limits`:1800 controller
seconds +180 collection seconds/root,180 maximum calls,2 aggregate A40-hours
including preparation. These are metadata, not an implemented controller or
runtime guarantee; `native_execution_authorized=False`. No old feasibility
thresholds are halved or adopted. No controller/ancestry framework was added.

Source layout: new core, frozen alignment, parented, V2 and memory core modules
at their declared `/tmp` paths, plus the existing pinned source_root tree.
No additional package or special new PYTHONPATH is required by this core;
`PYTHONPATH=/tmp` in the unittest command discovers the owned test module.
Pin/snapshot the new core plus frozen alignment module in the new runner,
alongside its existing transitive source inventory. Do not alter the old runner.

Shared source tasks are8 distinct source instances, not72 independent units. Four-factor
balance is across the whole family: P prior and C display direction differ
between first/second family blocks, so block comparisons do NOT identify
improvement. Explicit ordinary prompts teach the requested operations; this
assay only describes incremental fixed guidance under that contract, not
parenting qualification, adaptation, mediation or persistence.

No write-material API: current lesson/restatement bytes and raw records are
diagnostic evidence only. Main owns protocol, runner, native preparation and
outcomes. Only these three new files were edited.

EDITSTOP
