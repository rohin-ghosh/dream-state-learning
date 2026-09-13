# PCFL CPU preparation sidecar — EDITSTOP, 2026-09-13

**Owned source/tests frozen. This is a reusable CPU bridge, NOT full execution
closure, model readiness, a qualified writer, or a scientific result.**

Main's resumed instruction prompted one final fail-closed amendment before
this refreeze: `production_bindings.distractor` is a required closed
`UNRESOLVED` object, with unresolved topology, D0/D1 result bytes, receipt
schema and terminal public response. Public probe-result bytes remain
unresolved too. Core fixture/provisional D descriptions are NOT production
authority. No X→Z/Z→Y/q_D choice, result text or new receipt semantics was
invented here. `static_contract_complete=False`,
`execution_contract_valid=False` and `ready_for_model_calls=False` remain
explicit even when every implemented bridge invariant passes.

Read the latest production-binding extraction:
`research_notes/analysis/2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md`,
SHA256 `bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`.
Future concrete D binding requires an explicit scoped update, not an evidence
receipt or a changed status Boolean. Formal C11 was not added.

Only these paths were authored by this sidecar:

- `organism_v6/pcfl_vertical_prepare.py`
- `tests/test_pcfl_vertical_prepare.py`
- `/tmp/astra_pcfl_vertical_prepare_handoff_20260913.md`

AGENTS and local Git status/upstream configuration were inspected before
writes. Initial HEAD/cached origin/main divergence was `0 0`; no network pull
was attempted because network was expressly forbidden. No commit/push,
tokenizer/model/native/GPU/network call, live-script edit, backend/trainer edit,
or scientific artifact was made. Other agents' additions and the existing
`gpu/codex/dream_state.rules` modification were preserved. Main's intervening
commits `0042139f` and `84ae9890` were observed, not authored here. Additive
collection repair has no bearing on this schema. Formal C11 remains deferred.

## Frozen pins and validation

SHA-256:

| Path | SHA-256 |
|---|---|
| `organism_v6/pcfl_vertical_prepare.py` | `e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4` |
| `tests/test_pcfl_vertical_prepare.py` | `e66832d1891e9f83b7591ee454c5d7d93a3d6007e1df2da4607d9d5d23038862` |
| Read-only core dependency at validation: `organism_v6/pcfl_vertical_dev.py` | `03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f` |

Commands actually run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_pcfl_vertical_prepare.py -q
# final scoped run: 26 tests PASS, 12.954 seconds
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_pcfl_vertical_dev.py -q
# read-only integration dependency: 39 tests PASS, 0.938 seconds
git diff --check -- organism_v6/pcfl_vertical_prepare.py tests/test_pcfl_vertical_prepare.py
sha256sum organism_v6/pcfl_vertical_prepare.py tests/test_pcfl_vertical_prepare.py organism_v6/pcfl_vertical_dev.py
```

The final scoped run additionally compared the core source SHA256 before and
after the run: identical at the dependency hash above. That dependency is not
owned/frozen by this sidecar and may subsequently change.

Also ran `ast.parse`, in-memory `compile`, and trailing-whitespace checks on
both owned Python files: PASS. The preparer imports only `hashlib`,
`itertools`, `json`, `math`, `re`, and `collections`. No optional runtime or
model import is hidden in a helper. Earlier development runs passed 18, 23,
and 24 tests; one intermediate fixture-refresh regression failed and was
repaired in the owned test helper. Later runs passed 25 tests, then 26 after
the explicit D-unresolved amendment. The final 26-test run is authoritative.

All six authority hashes from the closure memo were verified against local
files. The core's additional seventh pin for the closure memo is accepted
only at its exact frozen value. These matches do not prove world/readiness.

## Public API

`build_execution_contract(bindings, tokenizer_receipt) -> dict`

- Detaches inputs, computes hashes, inserts fixed v2.2 recipe, prospective
  W0–W8/parser literals and the finite CAL table, then validates.
- Does not select a world, render, bank, schedule, replay, tokenizer,
  measurement, GPU, profile, cut, or work row on the caller's behalf.

`validate_execution_contract(contract, profile_receipts=None) -> dict`

- Malformed, unknown, duplicate, drifted, or inconsistent bridge fields raise
  `ExecutionContractError`. No input is modified.
- Returns `bridge_invariants_valid=True` only after its concrete checks.
  Returns **`execution_contract_valid=False`**, with `missing_interfaces`;
  the unresolved external certificates below cannot be waived by inserting
  booleans or relabeling test measurements. This sidecar has no native release.
- `static_contract_complete=False` distinguishes checked static invariants
  from a complete static assay; `ready_for_model_calls=False` is separate.
- Reports both LOW_ONLY/HIGH_USED expansions: 15/16 fits, 3000/3200 updates,
  960/1024 added retention generations and summed device-time caps.

`validate_formation_binding(contract, corpus_id, queries, rows) -> dict`

- Accepts the exact objects returned by core admission and
  `core.materialize_queries(rows)`. Returns only contract/corpus and immutable
  slot→target/source hash bindings, including replay slots.
- A missing bank, different chronological handle/field/order, extra query,
  modified raw target, incorrect taint, or CEILING_FIXTURE fit source raises
  `VS_FORMATION_BANK_MISMATCH`. It does NOT remap structural slots, rewrite
  rows, recompile a favorable corpus, or substitute ideal rows.
- `formation_binding_valid` proves this CPU byte/structural check only;
  `native_custody_verified=False` is intentional. The runtime/writer must
  verify original admitted generation/receipt custody separately.

`root_skeleton_digest(bindings) -> hex SHA-256`

- Prospective hashing helper, not a validity verdict or release. Allows replay
  placeholders with non-null source before replay selection; excludes their
  source/request/support/bank values. First-block banks, corpus/root/arm/slot
  identities, roots, core root/world registries, cuts, addresses and counterpart
  maps are frozen. Full build subsequently requires resolved valid replays.
- Do not inject post-formation targets, losses, scores, child spans or hashes
  into a skeleton. They are not structural fields.

`canonical(value) -> bytes`, `digest(value) -> hex SHA-256`, and
`load_contract(payload_bytes, expected_sha256) -> dict` provide canonical
UTF-8 JSON and sidecar checking. Encoding is sorted keys, compact separators,
`ensure_ascii=False`, no nonfinite values or implicit type coercion. Duplicate
JSON keys and noncanonical payloads fail. The core's own canonical function
returns ASCII-escaped text; use **prepare.digest**, not blindly core.digest,
for these envelopes/contract hashes, especially with non-ASCII payloads.

`calibration_transition(state, gates) -> terminal/next-state label` consumes
strict Booleans for `custody, masks, schedule, finite_200_updates,
zero_truncation, complete_readout, checkpoint, locality_refusal,
zero_false_rows, generic_canary, pcfl_retention, event_semantic, event_strict,
link_semantic, link_strict`. The tests enumerate all 32,768 Boolean assignments
at LOW and HIGH. HIGH can run only after valid/safe LOW misses acquisition;
native route, W8, NLL, margins and confusion are not inputs.

## Exact caller binding maps

The closed `bindings` keys are:

```text
source_pins implementation_pins environment core_registry root_registry
slot_registry counterpart_registry replay_registry batch_registry
diagnostic_registry intervention_registry locality_registry work_registry
profile_registry
```

### Core, roots, source pins

- `core_registry = core.registries()` **verbatim detached return**, including
  `schema, source_pins, root_schema, render_registry, parser_registry,
  world_registry, intervention_registry`. No competing core renderer/world
  implementation is introduced here. `core_registry.intervention_registry`
  is the generic core rule set, NOT the concrete cut roster below.
- `source_pins` is either the exact six-pin `prepare.SOURCE_PINS` dictionary or
  all seven entries returned by core. No arbitrary extra pin is accepted.
- `implementation_pins = {preparer, validator, core}` contains exact source
  SHA-256 strings. The pure module checks shapes/relationships, not filesystem
  bytes. Main must independently compare loaded source files to these pins.
- `environment = {base, model_revision, model_files, tokenizer_revision,
  chat_template_sha256, environment_sha256, product, gpu_uuids, cal_seeds}`.
  `base=Qwen2.5-7B-Instruct`, `product=A40`; file maps are filename→SHA256.
  `cal_seeds` has exactly `cal/init, cal/dropout, cal/readout, cal/batch`.
  LOW/HIGH share these, clean C0, corpus and schedule; only LR changes.
- Each `root_registry` entry has exactly `id, role, seed, old_bit,
  canonical_r, primary_reachout, wire, topology, cube`.
  `wire=core.to_data(root)` unchanged; `seed=core.seed('root/'+id)`.
  `topology` contains pre-output `[source, port, destination]` triples from
  that root's inventory; it is NOT generated formation text. `cube` is the
  ordered eight O/R/D bit triples. Root order is excluded/0–3,
  disposable/0, dev/0–1; DEV O/R and RA/RB assignments are fixed by index.

### Writer banks, replay, batches

- `slot_registry`: 15 corpus records `{id, root, arm, slots}`: seven DEV arms
  per root plus one disposable `S1_AUTH` corpus shared by LOW/HIGH.
- Each slot: `{id, source, row_type, phase, support, bank, taint, request}`.
  `source=null` means first occurrence; replay source names a first slot.
  `row_type=EVENT|LINK`; `phase=OLD|NEW` means query bearing that material;
  `taint=AUTHENTIC|CONTROL`. Every replay copies source request/support/bank/
  phase/type/taint exactly and never adds an address or target.
- `support` is an ordered list of **presealed chronological EVENT/LINK
  handles** (same identity space as core query `support`), not a hash of the
  enclosing block. `bank` maps each support to its pre-output expected fields:
  EVENT `{event, source, port, destination, receipt}`; LINK
  `{link, first, second, via, receipt_first, receipt_second}`.
  These banks are planner/admission-only; never send them as extra child
  prompt material. Free choice may fail a bank; that must fail formation.
- `counterpart_registry`: `{left, right, pairs, replaced}` per comparison.
  `pairs` and `replaced` contain `[left_slot_id, right_slot_id]`; their union
  is a total bijection of the twenty slots. Required anchor maps: S1_AUTH→
  ATOMS/TWIN/PERMUTE and S2_FULL_R0→FULL_R1/OLD_REPLAY, on both DEV roots.
  Unchanged pairs and common replay sources/positions are checked jointly.
- `replay_registry` rows: `{corpus, row_type, suffix, eligible, prior,
  selected, slots, domain_hash, support_counts}`. `slots` are destination replay
  slot IDs. Base suffix `replay`: three S1 EVENTs or one S2 OLD EVENT.
  ATOMS adds `atoms_extra` (three EVENTs, common selections counted as prior).
  OLD_REPLAY adds `old_event_extra` (one EVENT, common prior) and
  `old_link_extra` (one LINK, no EVENT prior). Common eligibility is the
  unchanged OLD source intersection across the family; extra eligibility is
  the arm-local full eligible type set. A NEW-bearing grouped query in one
  mate cannot sneak into the common OLD replay pool.
- Replay hash domain is canonical JSON
  `[root_skeleton_digest, stage, family, row_type, suffix]`, with `stage=S1|S2`
  and `family=S1_four_arm|S2_three_arm`. This explicit wire spelling is a
  prospective implementation binding, not a past measured fact. Rotation,
  distinct subsets, range/variance/rotated-rank tie break and appearance
  counts are recomputed. No bytes/losses/scores influence selection.
- `batch_registry`: `{corpus, epochs}`, exactly five lists of forty batches
  of four `[slot_id, view_id]` pairs. Views are integers 0–7, not W8. Every
  pair occurs once/epoch. Underlying support overlap (including singleton vs
  grouped reads and replays) fails. At most one LINK and one NEW item per
  batch; S1 non-ATOMS has 24 LINK batches, ATOMS zero, S2 32. Unchanged mates
  share exact indexed positions. First-joint-backtracker-solution provenance
  remains missing; validity of a submitted assignment is not that proof.

### Diagnostics, cuts, locality, work

- `diagnostic_registry = {producer_sha256, payload, payload_sha256}`;
  `producer_sha256=implementation_pins.core`,
  `payload=core.diagnostic_registry(queries,candidate_blocks)` unchanged,
  `payload_sha256=prepare.digest(payload)`. Its role must be scorer-only;
  each wrong-block target hash is checked. Complete eligible-universe and
  all-address certification remain core/Main evidence, not invented here.
- Concrete `intervention_registry` rows:
  `{id, corpus, kind, slots, support, replacement, endpoint, view, seed,
  unaffected_mate, task_ids, denominator, minimum_drop}`.
  Kinds are `S1_LINK, REACHOUT_OLD, S2_OLD, S2_NEW`; replacement is `MISS`,
  endpoint `service`. Support/slot references, unaffected-mate disjointness
  and attainable arithmetic are checked. Full graph/service oracle coverage
  and exact every-root/state critical-cut materialization are still required.
- `locality_registry`: `{corpus, other_corpus, unseen, wrong_root, seed}`;
  each address list has eight `{request, view}` records with W0–W7. Unseen
  requests are absent from all supported/replay targets; wrong-root requests
  exist in the explicitly named distinct-root corpus but not the local one.
- Each `work_registry` row has exactly:

```text
id kind purpose root state corpus endpoint prompt_sha256 mount seed
input_cap output_cap returned_cap ancestry denominator gpu_uuid branch
device_seconds_cap budget profile reuses
```

  `kind=task|generation|lookup|forward|fit|cold_load`;
  `branch=BOTH|HIGH_USED`; `budget=training|dev_inference|cal_low_readout|
  cal_high_readout`. Each row is one work item, not an aggregated `count`.
  `reuses` is null or an existing row ID. Core purposes have totals
  `single_actor=1106, service_task=576, direct_read=324, formation=76,
  canary=280`. `pcfl_retention` must have 64 generation rows per executed fit
  state. Fit states are globally distinct, including literal CAL_LOW/HIGH.
  Fit corpus/root/mount and shared CAL fields are checked. Per-fit 1800s,
  DEV inference 36000s and CAL readout 3600s/state caps are separate sums of
  device-seconds, never parallel wall time. Exact adaptive service turns,
  W8/forward/confusion/load/item reuse expansions are still missing.

### Tokenizer and profiles

- `tokenizer_receipt = {kind, decisions_hash, revision, files,
  chat_template_sha256, measurements}`; `kind=offline_measurement` for actual
  external measurements or explicitly `synthetic_test` in tests;
  `decisions_hash=prepare.digest(bindings)` after ALL decisions are selected.
- Each measurement: `{id, text, token_ids, offsets, attention_mask, labels,
  eos_index, opaque_spans, categories}`. Offsets/spans are UTF-8 byte pairs;
  categories are `masked|content|grammar`. Overlap with any opaque byte span
  is content; EOS is grammar. EOS is supervised, only post-EOS padding has
  mask 0/label -100, lengths ≤512. Same-shape alternate pad IDs are allowed.
  Complete inventory coverage, every corpus/view measurement and actual
  response-only mask provenance are NOT inferred from one measured row.
- `profile_registry`: four `{id, path, shape, cap_device_seconds, gpu_uuid,
  accounting}` declarations. Shape is a positive integer list;
  `accounting=summed_device_seconds`. Work references these IDs.
- Optional later `profile_receipts` list entries:
  `{id, kind, contract_sha256, path, shape, gpu_uuid, product, device_seconds,
  accounting, evidence_sha256}`. `kind=measurement|synthetic_test`.
  Contract/path/shape/GPU/product/accounting must match and time must fit the
  bound cap. Receipts are external immutable evidence; they cannot fill or
  alter decisions. There is no profile or model call in this module.

## Runtime/writer hookup and remaining interfaces

The current read-only runtime and writer already reference these concrete
fields: roots via `entry['wire']`; exact shared `core_registry`; corpus slots
and epoch arrays; `environment.cal_seeds`; `validate_formation_binding`.
Runtime remains explicitly scripted-only and writer custody is independently
checked. No file outside the three owned paths was changed for alignment.

Order for Main's future concrete preparation:

1. Supply complete core-derived roots, banks, counterparts, cuts, addresses
   and profile/work declarations. Compute prospective skeleton hash before
   replay assignment; materialize replay and joint schedules without outputs.
2. Complete every binding and obtain actual offline tokenizer evidence against
   `prepare.digest(bindings)`. Then build and seal canonical contract bytes
   and their `prepare.digest(contract)` sidecar. Persist write-once in Main's
   artifact owner; this pure module performs no file writes.
3. Obtain the four immutable measured profile receipts against that exact
   contract hash. Rerun validation without changing any decision.
4. Independently close all named missing interfaces, including native loaded
   source/contract enforcement. A successful **bridge** check is not release.
5. For formation, pass admitted core rows/queries unchanged. If authorized
   free-choice chronology does not realize a required predeclared bank,
   preserve the failure and stop that formation; never rebind the contract.

Unresolved interfaces reported by the code remain:

- authoritative production D topology/outcome/receipt/terminal bytes and
  exact R/D public probe-result render bindings (not inferred from core);
- complete core render/parser/diagnostic/critical-cut oracle certification;
- first-joint-solver-solution and semantic counterpart proof;
- full real-tokenizer inventory/view/mask coverage;
- complete diagnostic/service/cold-load/denominator expansion;
- actual loaded source pins and native contract-hash enforcement;
- missing measured profiles; synthetic test evidence never upgrades these.

The test corpus intentionally has invented structural banks, work rows,
token IDs, device identities and durations. It uses real core registry objects
and public CPU parser interfaces for integration checks but is **not** a valid
scientific world or native contract. No mock assertion claims real closure.

**EDITSTOP: owned source/tests frozen at the hashes above.**
