# PCFL vertical CPU core — reconciled EDITSTOP, 2026-09-13

## CURRENT: production D remains unresolved (supersedes prior release below)

Reconciled Main's latest instruction and
`research_notes/analysis/2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md`,
exact byte SHA256 `bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`.
The earlier permitted prospective Z->Y/q_D realization is now retained ONLY
as an explicitly requested CPU demonstration fixture, not production science.
The prior handoff/source/registry pins below are historical, NOT current pins.

Current exact file-byte hashes:

- `organism_v6/pcfl_vertical_dev.py`:
  `03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f`
- `tests/test_pcfl_vertical_dev.py`:
  `9d145421d41a2526d3e55ab7b0f9a67f3760f692c3f6ec33e2dbb0c84d1a00f2`
- Current `registries()` canonical-data SHA256:
  `caceddbaab84390196b8d1b219062440a4e7b49e640665b463f1bf83a43e8f03`
- Current `audit_construct(excluded/0..3)` canonical-data SHA256:
  `23da507cd2cec6fc9a09515ee48b2f174e96dfdfc4fd508ece92b6e8b78f795a`

Validation actually run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover
-s tests -p 'test_pcfl_vertical_dev.py' -q`; **39 tests PASS, 0.916s**. Three added
regressions cover unresolved production schema, default-path rejection, and
fixture isolation. Existing chronology/bank-failure and exact-row tests remain.
The binding memo's bytes are now also tested. Handoff hash reported separately.

### Changed API/schema for Main and Kierkegaard

`production_binding_status()` returns a fresh closed object:

```text
status = VS_ASSAY_INVALID
execution_contract_valid = false
source / source_sha256 = the binding memo above
distractor = {
  endpoints: null, port_semantics: null, public_outcomes: null,
  receipt_schema: null, post_commit_transition: null
}
relevant_public_result = null
production_inventory_complete = false
pending = [explicit missing semantics, namespace typing, tokenizer, timing]
```

`require_production_bindings()` always raises `VS_ASSAY_INVALID` while this
object is unresolved. Production defaults now reject before emitting any
invented probe/result or enabling NEW:

- `WorldSession(cell,'NEW',...)`
- `render_reachout(cell,goal,...)`
- `render_task(...,'RAW_EPISODIC',...)` (and therefore default `render_views`)
- a non-fixture session's `probe(...)`.

The narrow CPU-demo opt-in is keyword-only `fixture_only=True` on those APIs
and `render_views`; it is NOT a production binding, scientific authorization,
or native bypass. NEW fixture receipts and admitted-span provenance explicitly
retain `fixture_only=True`. `ceiling_fixture` internally opts in and retains
its harness-scripted/non-child origin. It remains usable for local regression
algebra, but not as native D evidence. No new production D was invented.

`registries()['world_registry']` keeps the same key set but now contains:

```text
probe_endpoints = [['H','S_R'], null]
probe_result = null
probe_receipt_slots = null
distractor = production_binding_status()
```

The existing r9/r10 handles in the unqualified **fixture candidate** inventory
are not a resolved production probe-receipt allocation. G_ inventory slots
likewise do not decide model-visible goal typing. Production inventory remains
incomplete until these choices and real tokenizer constraints are bound.
Typed base32/seed algorithms and known OLD/relevant route algebra are unchanged.

Kierkegaard/Main: consume this updated core registry, preserve these nulls,
and require the production-binding gate rather than sealing dummy semantics.
The preparer is another worker's file; I have NOT edited it or claimed its
current validation path enforces this new gate. An old implementation/source
pin or fixture test success cannot authorize preparation or inference.

`audit_construct` now labels its scope
`CPU_FIXTURE_ONLY_NOT_PRODUCTION_D_CERTIFICATE`, embeds the unresolved binding
status, and keeps both `full_construct_passed` and `ready_for_model_calls`
false. Its 192 route/cut, 48 old projection and symbolic quartet calculations
remain useful CPU regression evidence but do NOT establish real public-D
entropy/neutrality or all five production closure seams. Actual tokenizer,
inventory, measured device-time, native custody and scientific ceilings remain
separate gates. PCFL still cannot substitute for parented/matched/parent-removal
claims.

EDITSTOP after reconciliation. Only the assigned core, test, and this handoff
were changed. No model/tokenizer/native/GPU/network/Git operation or launch.

---

## HISTORICAL RELEASE (superseded where noted above)

Implementation frozen after 36 pure-CPU tests. Owned: `organism_v6/pcfl_vertical_dev.py`,
`tests/test_pcfl_vertical_dev.py`, this handoff only. No native/model/tokenizer,
network, Git, training, or launch. Not execution readiness or scientific pass.

## Shared API for Kierkegaard/Main

Import `organism_v6.pcfl_vertical_dev`. Public JSON registries are returned as
fresh detached objects by `registries()` (schema `pcfl_vertical_cpu_v1`):
`source_pins`, `root_schema`, `render_registry`, `parser_registry`,
`world_registry`, `intervention_registry`. `canonical(data)` and `digest(data)`
hash closed JSON. `seed(label)` and `opaque_candidate(label,namespace,index,salt)`
implement the binding-register algorithm; CPU candidates are NOT tokenizer
qualified. `SLOTS` and `PREFIXES` enumerate inventory slots and namespaces.

`build_root(label, inventory=None)` returns an immutable Root; supplied complete
inventory is namespace -> structural slot -> opaque identifier. Labels are
`excluded/0..3`, `disposable/0`, `dev/0..1`. `to_data(root_or_cell)` /
`from_data(data)` are explicit closed-schema roundtrips. `expand_cube(root)`
returns eight private WorldCells. No private cell is a model-visible wire.

`render_task(cell,goal,render_id='NATIVE_CONTEXT',projection=None,rows=(),
wrong_rows=())` returns only public prompt data. `render_reachout(cell,goal,
render_id)` implements RA/RB. `ideal_rows(cell)` is explicitly tainted
`CEILING_FIXTURE`, never authentic child data. `oracle_route_v1` and
`oracle_routes_v2` are independent closed-form/search oracles; `score_route`
executes a complete strict command, optionally with OLD/NEW edge cut.

`WorldSession(cell,stage)` issues actual deterministic CPU EXPLORE/PROBE
receipts, preserves failed attempts, and exposes only registered public fields.
`parse_event_line`, `parse_link_line`, `parse_read`, `parse_route` are strict.
`admit_event(raw, receipt, session, fresh_id)` / `admit_link(raw, receipts,
session, fresh_id, events)` return admission dicts including original UTF-8
bytes/hash/span (no normalization/repair); private cross-stage verification
does NOT render OLD context. `formation_report(admissions,expected_events,
expected_links,required_bank=None)` retains all attempted denominators. `materialize_queries(rows)`
returns address -> block records (`request`, `target`, `support`, `taint`).
`score_memory_response(raw, expected)` separates strict/semantic/refusal/false-row.

`make_event_twin(rows,root)` / `make_link_permute(rows,root)` return CONTROL
rows, never eligible authentic ancestors. `cut_queries(queries,root,cut)` cuts
every address carrying the selected event/link carrier, not only singleton
READ EVENT. `diagnostic_registry(queries,candidate_blocks)` enumerates finite
same-type/same-count incorrect blocks without exposing candidates to prompts.
`classify_offsets(target,offsets)` binds opaque-overlap content vs grammar.
`audit_construct(roots)` reports executable CPU checks and remaining gates.

## Prospective literal decisions

Main's W8, exact-row/bare-or-text-fence envelope, MISS-only refusal and false-row
rule are literal registry entries. EXPLORE/PROBE/READ/ROUTE accept no terminal
LF; EVENT/LINK require exactly one LF. Ports are displayed in inventory
structural order (never opaque spelling or outcome); reachout RA/RB reverses
option order exactly as prescribed. Distractor probe tests isolated Z -> Y,
reports q_D as an available port; execution stays isolated Z -> Y. The OLD
Z --u--> Y edge remains unchanged. Relevant probe reports H -> S_R and q_R.
Probe outputs do not carry hash-chain/private metadata into visible text.

All in-context projections use one literal MEMORY header, exact rows/receipt
lines joined without blank rows, then a single blank line and the exact ROUTE
TASK. ACTIVE_LINKED_TEXT mounts no rows: exact query blocks are external CPU
service data. NONE_OFF mounts no memory. NEW_ONLY uses only the new EVENT,
not NEW LINKs exposing OLD handles. Full exact fixture rows are declared
researcher-authored ceiling data. No compiled fixture row can pass the
authentic-child admission API by provenance alone.

Important formation seam: live event handles are chronologically presealed,
not picked after seeing a port/outcome. Structural e0..e8 in the ideal ceiling
world denote edges, whereas free-choice OLD formation can assign a different
chronological handle to that edge. The core must report this distinction;
the preparer/runtime must not silently substitute ideal fixture rows or an
output-derived schedule for actual admitted child spans.

No CAL/SLEEP scheduler, writer, future accounting framework, C11, or operational
authority is implemented here. Full native gates and tokenizer qualification
remain pending even if the core CPU suite passes.

## Final pins and validation

Exact SHA256 of file bytes:

- `organism_v6/pcfl_vertical_dev.py`:
  `db41a9c1a1412774ac1e1d3a088cc7499b09d366ac12bbe43db21b6ae2de730a`
- `tests/test_pcfl_vertical_dev.py`:
  `9cbe4d10215e0da8d668bd75b85257aa8dc2c79c56661bcd71d2fed94a503161`

The handoff's hash is reported separately, not embedded recursively here.
The seven controlling source files are byte-checked by `test_source_pins`.
The frozen partial core was reused by porting its distinct closed-form and
graph-search route algorithms and fixed topology; no old file was changed and
the new module has no runtime dependency on `/tmp`.

Command actually run locally (stdlib only, no pycache writes):

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_pcfl_vertical_dev.py' -v
Ran 36 tests in 0.959s — OK
```

Pure-data hashes using core `digest` (canonical compact sorted ASCII JSON;
these are NOT file-byte hashes):

- `registries()`: `dac7d94c21c7b2536470d28ab87d6d0d046b3aaeb7abe5196bbb439bdae35892`
- `to_data(build_root('excluded/0'))`:
  `823754da5823bbcef0d00852d3c1160d5e012b6e8c236eb7555acdd906d6d186`
- Ten-render snapshot, excluded/0 O1/R1/D0 goal0 with excluded/1 O0/R0/D0
  wrong-root fixture: `ca87f40f3c78ac9885a071297408d08b40b1401a31454a1c6d5af1b16b02b5bc`
- `audit_construct` over excluded/0..3:
  `c120607314c8f8a6cf31f3cac06d942c100fca7b0ac013fbc472829a68e0ffe2`

No test receipt file was written elsewhere. Full test output is in the tool
transcript. CPU tests and deterministic constructor reports are replayable.

## Final integration details (supersede draft shorthand)

Kierkegaard's current preparer handoff consumes the entire detached
`registries()` as `bindings['core_registry']`. This agrees with the core.
`validate_registries(value)` checks literal/schema identity; no runtime world
logic needs duplicating. The per-address diagnostic payload remains separate.
`canonical` returns text (encode ASCII to persist); `digest` returns hex.
The core's public registry is ASCII, so its digest agrees with compact UTF-8
canonicalization in the preparer. Do not equate this with an arbitrary JSON
file's byte hash.

`WorldSession.public_affordances()` exposes only `{source,ports}`; runner need
not inspect private `_cell`. `event_prompt` and `link_prompt` supply only the
chronologically presealed empty fresh handle. `RouteSession.commit` is one-shot
even on malformed output and returns only `{terminal,arrived}`. Low-quality
EXPLORE/PROBE output consumes its opportunity and remains in attempts.

`ceiling_fixture(cell)` executes real deterministic CPU world transitions using
the fixed first-listed OLD-port policy, then the relevant probe and revealed
NEW port. Its origin is `HARNESS_SCRIPTED_CPU_CEILING_NOT_CHILD`. RAW_EPISODIC
is the action/result chronology from those transitions, not a hand-authored
outcome list. `ideal_rows` copies those witnessed fields into **researcher**
ceiling rows with taint `CEILING_FIXTURE`. This is deliberately separate from
`admit_event`/`admit_link`, which never author or repair semantic raw targets.

All admissions retain full caller-supplied raw generation bytes, their UTF-8
hash and `[0,len(bytes))` span. No prefix/suffix is stripped to rescue formation.
They expressly say `native_generation_verified=False`; CPU-issued receipts
and matching caller text are NOT proof of native authorship. Native request,
raw generation, source state and span custody must be bound by the runner.
NEW session parent receipts/events are private verification material only;
they are never substituted into NEW prompts. A NEW LINK must touch its own
NEW event; stale old-only pairs, cross-root evidence, receipt splices, controls,
and ideal fixture rows are rejected as authentic ancestors.

`render_task` canonicalizes only **whole-row order**, never row contents,
using registered structural/chronological handles. Incomplete context
conditions fail rather than silently becoming NONE_OFF. WRONG_ROOT requires
one complete other-root sequence; its exact order/counterpart must be presealed
by preparation, not inferred from current task answers. `render_views` exposes
all ten; `read_query` implements deterministic ceiling service only, validates
the address/content/source-hash binding, and never invokes a memory model.
Absent service MISS is not inserted into training queries.

`paired_cuts`/`cut_queries` affect the complete grouped result at every address
containing the carrier or incident LINK, including EVENTS_AT and LINKS_FROM.
Uncut counterpart blocks remain identical. Replaced blocks retain an explicit
uncut target hash and evaluation-intervention label; returned MISS has no
claimed returned-row citations. These are modular read interventions, not
parameter-level mediation or proof that LINK information is necessary.

## Required bank and chronology are separate gates

`formation_report(..., required_bank=bank)` accepts a **presealed** map:

```text
opaque EVENT/LINK handle -> exact typed fields (the parser's fields dict)
```

The caller must obtain it from the frozen contract, not construct/reseal it
from post-output admissions. The function does not mutate the bank and reports
its hash, missing/different/extra handles. No bank returns
`REQUIRED_BANK_UNBOUND`, even with 8 EVENT + 4 LINK accepted. Missing or changed
bank content returns `VS_FORMATION_BANK_MISMATCH`. `formation_complete` requires
all scheduled accepted calls **and** exact bank match; this still does not
verify native source custody or pre-output timing of the supplied bank.
Kierkegaard's `validate_formation_binding` binds that bank to the contract.

Concrete regression: under O1, first listed a0 reaches X. The live first event
is chronological e0 describing X, while ideal structural e0 is the a1->A edge
witnessed later with r6. The tests preserve both descriptions unchanged.
Supplying the pre-existing ideal structural bank to a complete live formation
fails; dropping a required last LINK also fails. No oracle row is inserted,
no fresh handle is remapped, and no slot is resealed. `LINK_PERMUTE` additionally
rejects a bank not matching its registered structural l0..l3 topology instead
of guessing a new derangement after outputs. Preparer/runtime must treat a
required-bank mismatch as failed formation, not permission to repair it.

Relevant code: `organism_v6/pcfl_vertical_dev.py:348`,
`organism_v6/pcfl_vertical_dev.py:444`, `organism_v6/pcfl_vertical_dev.py:625`.
Regression tests: `tests/test_pcfl_vertical_dev.py:117`,
`tests/test_pcfl_vertical_dev.py:295`.

## Achieved versus explicitly pending

Implemented/exercised: seven fixed root labels, opaque candidate algorithm,
full O/R/D cubes; two independent route oracles; actual CPU EXPLORE/PROBE;
strict EVENT/LINK/READ/ROUTE; public projection byte snapshots and collision
equalities; source/span admission; copy-only multi-row query compiler;
CONTROL-tainted coherent event twin and fixed LINK derangement; grouped
OLD/NEW/LINK read cuts; exact semantic/refusal/false-row truth table; finite
caller-declared wrong-block enumeration and content/grammar offset classifier.

`audit_construct` reports 32 worlds, 64 delayed tasks, 192 route/cut decisions,
48 receipt/EVENT/EVENT+LINK old-route decisions, 32 LINK successor-support
instances (K is 1 or 2; K>1 is not silently called uniquely derivable), and
16 pre-outcome quartets with exact balanced information vector `[1,1,1,0]`.
OLD_ONLY and NEW_ONLY rendered Bayes-best counts are 32/64; NONE_OFF is 16/64.
These are evaluator CPU construct facts, not model performance.

Pending separately: real tokenizer-qualified joint inventory and template
measurements; complete rendered shortcut-feature/pair certificate; concrete
retention/canary and campaign panels; exhaustive prepared diagnostic universes;
actual profiles/device-time budgets; sealed schedule/contract; native runtime
and raw-generation provenance; model zero-fit ceilings and actual formation.
The helper report deliberately leaves `full_construct_passed=False` and
`ready_for_model_calls=False`. It does not claim all five closure seams solved.
None of this implements CAL/SLEEP or authorizes inference/training.

PCFL is a direct substrate/closed-loop diagnostic. It does **not** replace the
still-required parented, matched-control, or parent-removal claims, and makes
no parenting-improvement, native/HF parity, H1/H2 promotion or later-outcome
claim. Main retains integration, operational decisions and scientific claims.

EDITSTOP: only the three owned paths were changed; no commit or other worker's
file edit. No native, model, tokenizer, GPU, network, or launch operation.
