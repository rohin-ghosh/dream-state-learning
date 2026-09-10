# PCFL-Compose v2 pre-intake systems/static-contract audit

**Date:** 2026-09-02  
**Audit type:** fresh exact-byte PRE-INTAKE review  
**Disposition:** **NOT READY FOR INTAKE**  
**Authority:** advisory only. This audit does not edit the proposal, initialize
or advance intake, authorize implementation/CPU/model/GPU/network work, ratify
the change, or approve a claim.

## Exact reviewed bundle

The reviewed `change.json` SHA-256 is exactly
`2fc2521d821efc2ff4852ef9decbb4c2bdf834a8f1b0ff438aec7e78d2a0f047`.
The directory contains 25 authored files: `change.json` plus 24 v2 artifacts
listed in its `context_files`. All 24 declared v2 artifact hashes match their
current bytes. All six JSON files parse as JSON. No intake validator or workflow
transition was invoked.

Every authored v2 file was read: change, experiment, scope, human directive,
semantic/schema/reducer, event catalog/extractor, RNG, private-field and
visibility contracts, analysis and assignment ledgers, resource manifest,
v1/premortem dispositions, and all eight prompts.

## Executive finding

The scientific roster and its arithmetic are substantially repaired, but the
runtime contract is not yet executable. There are seven intake-blocking defects:

1. `semantic_dsl.schema.json` validates no runtime object at its root and omits
   almost every operation payload variant.
2. `event_catalog.schema.json` has one event-only receipt shape, so candidate
   and memory reads cannot validate.
3. the RNG derivation includes the treatment fields that coupling is supposed
   to ignore, so declared coupled rows receive different seeds.
4. the registry explicitly gives the actor opaque memory, and the change-level
   visibility matrix merges reader, Think, and actor into one memory-visible
   stage.
5. opaque “bytes as received” cannot coexist with JSON/JCS string
   canonicalization as written, and the payload/candidate byte caps contradict
   one another.
6. one-shot Dream is instructed to emit a harness capability that cannot exist
   until after its single response; Dream-1 terminal decisions and one-shot
   Think LOCK also do not match the schema.
7. live-state/resource maxima are prose-only, per-operation generation limits
   cannot be selected before the model chooses an operation, and sampling/
   rendering parameters needed by the seed and token contracts are absent.

The 3,414-call design should remain unchanged while these bytes are repaired.
These are schema, information-flow, and determinism fixes, not reasons to add a
cell.

## What is already coherent

The following static properties survived review:

- Stage 1 is 128 Dream + 782 Think = 910 calls.
- Conditional Stage 2 is 356 Dream + 2,144 recurrent Think + four structured
  one-shot Think = 2,504 calls.
- The successful scientific path is 484 Dream + 2,926 recurrent Think + four
  one-shot Think = 3,414 calls; two replay opportunities give 3,416 process
  calls.
- Given the stated phase/input reservations, the output arithmetic recomputes
  to 1,709,056 scientific and 1,740,800 process tokens; the process combined
  ceiling recomputes to 57,872,384, leaving 9,200 output and 127,616 combined
  tokens under the rounded watchdogs.
- The assignment ledger contains exactly four named structured-only one-shot
  Think rows and no result-triggered model panel.
- `128 x 10.5` CPU-minutes is 1,344 minutes or 22.4 hours.
- The temporal claim correctly separates prospective commitments,
  raw-A-conditioned Dream-2 change, and selected-h corpus-to-later-action.
- Opaque semantic claims and opaque one-shot Think recurrence claims are
  explicitly withheld.

Those are necessary, not sufficient. The present schemas and process graph do
not enforce them.

## Blocking finding 1: the runtime schema is inert and incomplete

`semantic_dsl.schema.json` contains a top-level `definitions` object and prose
`invariants`, but no top-level `$ref`, `oneOf`, `type`, or
`additionalProperties:false`. Under Draft 2020-12, the prose strings are not
validation keywords. Consequently `{}`, `null`, a string, and an arbitrary
object all satisfy the root schema.

Even if a caller manually selects one definition, the definitions are not a
complete protocol:

- `resolver_step` contains only `op`, `ordinal`, and `phase`; it has no handle,
  query, node, candidate manifest, capability, action, citations, reason, or
  terminal payload.
- `ABSTAIN` is missing from the `op` enum although every contract and several
  prompts allow it.
- READ event-handle versus lexical/AST query variants are absent.
- NOTE and OPERATOR_AST nodes, public events, trays, actions, predictions,
  provenance, references, and byte-limited free strings are absent.
- NOTICE, CONNECT, and workspace-REVISE cardinality/ancestry variants are not
  represented.
- `staged_candidate.predictions` is an unconstrained object;
  `public_handles` is unbounded and unpatterned; node references need not be
  nonempty or unique; parents, uncertainty/confidence, audit fields, phase, and
  exact A1/A2 versus B1/B2 sets are missing.
- `commit` always requires one capability and uses only
  `RETAIN|REPLACE|ABSTAIN`. Dream-1 needs an ordered commitment of up to two
  candidates, while ABSTAIN must not require a candidate capability. A single
  capability also loses the declared `K=2` Dream-1 pool.
- no one-shot Dream-1 or Dream-2 output type exists.
- `one_shot_plan.actions` has neither item schema nor `minItems`; it has no
  decision, citations, target identity, or terminal LOCK field. It cannot
  enforce the prompt's four legal actions followed by LOCK.
- the `invariants` array cannot enforce phase-operation allowlists,
  cross-field nullity, staged-before-PREDICT, registered capability ownership,
  candidate byte limits, or opaque/AST isolation.

The normative prose also disagrees about the missing PREDICT branch:
`experiment_spec.md` says PREDICT emits a full candidate object, whereas the
semantic contract, resource manifest, reducer, and prompts say it emits a
manifest over already staged nodes. The latter is the only version compatible
with the 2,048-token recurrent PREDICT cap and should be selected explicitly.

### Exact repair

Replace the file with a real root instance schema using `$defs` and a top-level
`oneOf` whose branches are unambiguous by `artifact`, `phase`, and `op`.
Include, at minimum:

1. operation-specific `RESOLVER_STEP` branches for READ-handle, READ-LEXICAL,
   READ-AST, NOTICE, CONNECT, workspace-REVISE, PASS, Dream-1 PREDICT, Dream-2
   PREDICT, Dream-1 COMMIT, Dream-2 COMMIT, USE, LOCK, and ABSTAIN;
2. complete NOTE, AST term/statement/record, workspace-node, provenance,
   tray/prediction, query, action, staged-manifest, opaque capability, and
   one-shot object definitions;
3. `additionalProperties:false`, exact required fields, bounded strings and
   arrays, action patterns, `uniqueItems`, and phase-specific enums on every
   object;
4. separate Dream-1 COMMIT (`candidate_capabilities`, one or two, ordered),
   Dream-2 RETAIN/REPLACE COMMIT (exactly one appropriate capability), and
   capability-free ABSTAIN variants;
5. full one-shot Dream result types that carry their candidate bytes directly,
   and a one-shot Think plan with exactly four validated USE actions and
   terminal `LOCK`; and
6. executable reducer checks for ancestry, exact prediction ID sets, live
   object lookup, canonical-byte caps, and phase legality. These must be named
   runtime rules with positive/negative fixtures, not prose keywords inside a
   JSON Schema.

The v1 AST schema may be imported by exact `$ref` only if reference resolution,
base URI, and the imported hash are frozen. Copying its closed `$defs` into v2
is simpler and avoids implementation-dependent resolution.

## Blocking finding 2: the catalog cannot represent its declared reads

The pre-READ entry does provide the intended five-field allowlist. Its receipt
does not. `charged_read_receipt.payload` always requires
`before`, `action`, `after`, and `slot_permutation`, regardless of
`handle_kind`. Therefore:

- a `CANDIDATE` read cannot return an opaque or AST candidate package;
- an opaque NOTE or AST record read has no receipt type at all;
- `NOT_FOUND`, cursor, query, posting/audit count, and lane are absent;
- `TARGET_MENU` is accepted as a handle kind but cannot satisfy the event
  payload and conflicts with the direct post-freeze target marker;
- event payload members are unconstrained and allow arbitrary extra fields;
  the receipt therefore does not enforce six-slot trays, action syntax,
  permutation bijection, or the extractor boundary; and
- a single `payload_sha256`/`byte_count` rule makes candidate/memory content
  identity model-visible if this receipt is inserted into `STATE`, contrary to
  the harness-only candidate digest rule.

### Exact repair

Make `event_catalog.schema.json` a root schema with a discriminated union:

- `EVENT_READ_RECEIPT` for TREE_EVENT/RAW_A_EVENT, with a closed six-slot raw
  event and exact six-integer `slot_permutation`;
- `CANDIDATE_READ_RECEIPT` for a full typed candidate plus a separately issued
  fixed-shape session capability, with audit digest/length retained in an
  audit-only sibling object rather than the model-visible payload;
- `MEMORY_READ_RECEIPT` for LEXICAL NOTE, AST record, or explicit NOT_FOUND,
  including typed query/cursor and bounded returned value; and
- if target menus are direct prompt inputs, remove `TARGET_MENU` from the
  catalog. Otherwise give them a distinct, post-freeze receipt schema.

Separate `MODEL_READ_RESULT` from `AUDIT_READ_RECEIPT`. Only the former enters
the next prompt. Bind the handle-to-receipt-kind relation, phase allowlist,
byte caps, query caps, and no-extra-field rule. Add fixtures for every success,
NOT_FOUND, wrong-kind, unread, malformed, and cap boundary.

## Blocking finding 3: coupled rows currently have different seeds

`rng_contract.json` says the HMAC input contains
`fixed_row_fields_without_seed_digest` and `coupling_group`. The required row
fields include `h_or_q`, `condition_id`, and `memory_variant_or_cut`. Thus two
Dream-2 h branches with the same coupling group still serialize different
`h_or_q` values, and authentic versus EMPTY/crossed/sham Think rows still
serialize different treatment fields. HMAC outputs will differ. A common
`coupling_group` label does not cancel other bytes in the message.

The backend mapping is also incomplete: “truncated only by the declared
backend seed API” does not say byte order, bit width, signedness, range
reduction, or how renderer/reader/actor namespace seeds are derived. The
assignment ledger additionally calls one-shot and iterative AST plans
“paired by coupling group” even though their invocation topologies differ; it
does not say whether that is an analysis pair or a common-random-number claim.

### Exact repair

Keep full row metadata for audit, but derive from a separate `seed_key`:

```text
seed_key = JCS({
  domain, seed_derivation_version, coupling_group,
  root_id, z_side, lane, phase_role, target_id, goal_twin,
  draw_role, resolver_ordinal
})
```

`h_or_q`, `condition_id`, `memory_variant_or_cut`, arm/cut identity, and
scientific/diagnostic labels must be excluded for a declared coupled
treatment contrast. A unique coupling group already separates rows that must
not share a draw. If a retained field differs within an intended coupling
group, Stage 0 must fail rather than derive different seeds.

Add a `coupling_kind` enum. `COMMON_SEED` is allowed only for rows with matching
invocation topology; `ANALYSIS_PAIR_ONLY` labels structured one-shot versus
iterative comparisons and does not promise stepwise identical randomness.
Freeze the HMAC message bytes and golden digest, exact backend integer mapping,
temperature, top-p, sampling/stop parameters, vLLM revision, and deterministic
renderer/reader/actor seed projections. The complete manifest must assert both:
all `COMMON_SEED` members have byte-identical seed keys/seeds, and all distinct
groups have their intended domain separation.

## Blocking finding 4: the actor is granted memory

`private_field_registry.json` lists `actor` among the consumers of
`opaque_note_bytes`. The change-level visibility matrix compounds this by
combining `TARGET_THINK_ACTOR` into one stage and marking
`STAGED_OPAQUE_BYTES` visible there. It also marks `PRIVATE_FIELDS` merely
“hidden” in that combined stage because actor transition bytes are internal,
which cannot prove they are forbidden to reader/Think.

This violates the proposed causal boundary. The corpus is supposed to affect
the actor only through Think's emitted legal action. Giving actor code a memory
object, digest, capability, receipt, lane, intervention, root, or score creates
an unmeasured direct path from treatment to physical outcome.

### Exact repair

Split the graph and visibility matrix into `TARGET_READER`, `TARGET_THINK`, and
`ACTOR`. Bind an explicit IPC schema:

- reader receives only its assigned corpus/index and a Think query, and returns
  a typed bounded NOTE/AST/NOT_FOUND result to Think;
- Think receives the public target state/goal/menu, its workspace, and reader
  results, and emits only USE/LOCK;
- actor receives only current public state, public legal menu, the emitted
  action, and its sealed transition implementation; and
- actor returns only the public next tray/action-validity result, never target
  correctness, path truth, memory identity, or score.

Remove `actor` from `opaque_note_bytes.consumers`; add `target_reader` and
`target_think` only where content actually flows. Actor must be forbidden from
candidate/corpus bytes, content addresses, session capabilities, corpus
variant/cut IDs, reader queries/receipts, root/family/h/q/z, target truth,
certificates, comparator bits, scorer labels, and analysis. Keep
`actor_transition_bytes` actor-only and immutable.

The registry claims exhaustive classification but currently omits public/raw-A
events, extracted permutation, candidates, indexes, queries/receipts, prompt
inputs, target/public state, action requests/results, B outcomes, RNG seeds,
errors/timing/cache, intervention IDs, and terminal scores. Add them or narrow
the “exhaustive” claim and provide a separate complete process-input allowlist.
Static taint fixtures must reject every forbidden field at each IPC boundary.

## Blocking finding 5: JCS and opaque-byte identity conflict

The semantic contract says both that all structured JSON is JCS and that
`NOTE.text_bytes` is “hashed as received” and remains unnormalized. No NOTE
schema or encoding is defined. A JSON string is Unicode scalar data, not an
arbitrary byte field. Raw spellings such as literal `é`, `\u00e9`, member order,
and insignificant whitespace can parse to the same value and produce the same
JCS bytes, so the raw response bytes cannot simultaneously be the JCS identity.

The content-address domain separator is written as `"...\\0"` in prose, which
does not unambiguously distinguish a NUL byte from the two ASCII bytes
backslash-plus-zero. The JCS version/implementation and Unicode-data version
are required in fixtures but not identified by version/hash in the authored
bundle.

There is also a literal capacity contradiction: `semantic_contract.md` allows
a notes/records payload of 4,096 bytes but caps the **complete** candidate at
3,072 bytes. `resource_manifest.md` instead describes a 2,510-byte payload and
3,072-byte candidate. A complete envelope cannot be smaller than its payload.

### Exact repair

Choose one coherent opaque representation. The least disruptive choice is:

1. NOTE has a valid-Unicode `text` string, not undefined `text_bytes`;
2. retain the exact raw model response separately for audit;
3. define authored/stored NOTE identity as the JCS UTF-8 bytes after one
   parse/schema/JCS boundary;
4. perform no Unicode normalization before hashing those JCS bytes; and
5. derive NFC/casefold lexical keys under one pinned Unicode version without
   replacing or rehashing the stored NOTE.

If arbitrary octets are actually required, use an explicitly canonical
base64url field, validate/decode it separately, require decoded valid UTF-8 for
the lexical reader, and state which encoded or decoded bytes are addressed.
Do not mix raw JSON bytes with JCS identity.

Specify domain-separator bytes in hexadecimal or a normative byte vector and
include one golden address fixture. Bind the JCS implementation/source hash,
RFC version, Unicode version, duplicate-key parser, invalid-scalar policy, and
raw-versus-canonical retention rule.

Use one capacity table everywhere. If the current resource choice is retained,
change the aggregate payload cap to 2,510 JCS bytes and prove that the entire
candidate—including predictions, handles, provenance, confidence, parents,
and audit field—fits 3,072 bytes. Enforce both the per-item 256/512 limits and
aggregate limit in runtime code. If the maximum envelope does not fit, raise
the complete candidate cap and re-run the one-shot/token arithmetic before
intake.

## Blocking finding 6: prompt/state transitions cannot execute as written

The prompt set is hash-bound, but its exact markers do not define an executable
conversation:

- generic Dream-1 says COMMIT uses `RETAIN`, `REPLACE`, or `ABSTAIN`; RETAIN and
  REPLACE are Dream-2 decisions, while Dream-1 must commit an ordered candidate
  pool;
- both one-shot Dream prompts ask the model to emit candidate bytes and then
  reference a harness-created session capability in the same single response.
  The capability cannot exist until the harness accepts and stages that
  response;
- one-shot Dream-2's sole `{{EVENTS}}` marker does not identify the Dream-1
  candidate pool/capabilities separately from tree and raw-A events;
- one-shot Think requires four USE actions “followed by LOCK,” but its schema
  has only an untyped, possibly empty `actions` array and no LOCK;
- AST prompts promise a “closed JCS AST schema,” but v2 defines no AST grammar;
- recurrent prompts name a schema but include no schema/version marker or
  operation budget. `{{STATE}}` is not defined as carrying these values;
- iterative Think's `{{CATALOG}}` has no compatible memory catalog/read receipt
  schema and no explicit last reader-result field; and
- adjacent free-form markers such as `{{CATALOG}} {{STATE}}` and
  `{{TARGET}} {{AST_PACKET}}` are not a normative length-delimited input
  envelope. The promised opaque `note_value` data channel is absent from every
  prompt and renderer schema.

### Exact repair

Create closed input schemas for recurrent Dream-1, recurrent Dream-2,
recurrent Think, one-shot Dream-1, one-shot Dream-2, and structured one-shot
Think. Render one marker such as `{{INPUT_ENVELOPE_JCS}}`, containing explicit
`contract_version`, mode/lane, ordinal, remaining operation/read/output
budgets, typed catalog, typed state, last model-visible read result, target when
allowed, and one-shot candidate/event/AST packets when allowed. The renderer
must insert untrusted opaque text only as a JCS string value inside this
envelope and bind its canonical byte length.

Make each prompt require exactly one named output artifact and no other bytes.
Fix Dream-1 COMMIT to an ordered one/two-capability selection. For one-shot
Dream, remove capability echo entirely: the single returned DREAM1/DREAM2
artifact is itself the terminal model commitment, and the harness may address
it only afterward. Alternatively make staging and COMMIT separate calls and
recompute the four-call roster; the former is smaller and preserves the ledger.
Define one-shot Dream-2 input as tree events + raw A + the immutable one-shot
Dream-1 candidate pool, with no target.

Make ONE_SHOT_PLAN contain exactly four validated actions and
`terminal:"LOCK"`. Incorporate the closed AST grammar. Add a marker inventory
fixture that fails on missing, duplicate, unused, unknown, or unescaped marker
values and compares factor/null generic prompt bytes outside their legitimate
payload differences.

## Blocking finding 7: resource limits are not yet enforceable contracts

The numerical ledger is correct conditional on its assumptions, but those
assumptions are not encoded:

- none of the 256/512/2,510/3,072/live-tuple byte limits appears in a validating
  schema;
- Dream phase cumulative caps of 8,192/4,096 are used in arithmetic but are not
  stated as a complete reducer transition with `remaining_tokens`;
- the model chooses its operation inside a response, so the server cannot know
  whether to request 512, 2,048, or 256 tokens before generation. A malformed
  response has no parsed operation class;
- maximum rendered prompt byte numbers are asserted without a normative input
  schema or renderer, so no maximum legal fixture can yet be constructed;
- temperature, top-p, stop strings/token IDs, guided-decoding mode, timeout,
  backend seed mapping, vLLM revision, chat template, tokenizer hashes, and
  Unicode/JCS implementation identifiers are absent;
- Stage-0 root certification alone reserves 22.4 of 24 CPU-hours, but exact
  programs and all parser/JCS/tokenizer/schema/reader/reset fixtures are also
  charged to Stage 0 without an allocation of the remaining 1.6 hours; and
- 18 device-hours is a competing stop, not a proof that the full maximum-token
  roster can complete. This is disclosed, but the pre-GPU completion rule must
  say whether a predicted overrun is NOT_RUN rather than partial execution.

### Exact repair

Add a machine-readable resource schema/manifest and reducer fields for raw
input/output tokens, JCS bytes, operation/read/action counts, phase cumulative
tokens, global scientific/process calls, replay slots, device/wall time, and
artifact bytes. Make all maxima schema- or runtime-enforced and cover
`cap-1/cap/cap+1`.

Set recurrent Dream's prospective server limit to
`min(2,048, phase_tokens_remaining)` because PREDICT is the largest possible
operation; after parse, enforce the 512/2,048/256 accepted-operation limits.
Malformed Dream output may consume up to that server limit and remains charged
to the 8,192/4,096 phase total. Set recurrent Think prospectively to 512. Use
the one-shot phase/trajectory cap directly. This preserves the current
aggregate output arithmetic.

Freeze every sampling/rendering/runtime byte and produce maximum fixtures from
the completed schemas with truncation disabled. The configured context must
fit the stated 48,640-token maximum. Allocate CPU explicitly—for example 22.4
hours root certification plus at most 1.6 hours for all other Stage-0 work—or
raise the global CPU cap before intake. Require a pre-GPU resource forecast to
fit the device/wall stop with margin or return NOT_RUN; no cell may be dropped.

## Material analysis-contract gap

`analysis_contract.md` defines pairing well, but the Stage-1 gate is not a
literal Boolean reducer. “Authentic memory above EMPTY and crossed corpus” and
“no comparable sham redirection” do not define strictness, tie handling,
required row completeness, or whether action success, first-action
redirection, and failure-effect endpoints are conjuncts or alternatives.

Add a machine-readable gate expression naming every receipt and exact
comparison. For example, state whether `mean(SELF-EMPTY) > 0` and
`mean(SELF-CROSSED) > 0` are required, whether sham requires redirection exactly
zero, and how any unavailable/failed pair maps to gate false. The gate must
operate only on the selected-h rows registered in the assignment ledger and
must not pool Stage 2. Freeze a complete truth-table fixture.

## Exact file-level repair checklist

Before authoring a new SHA:

1. **`semantic_dsl.schema.json`:** replace inert definitions with complete
   root schemas and all operation, representation, terminal, and one-shot
   variants; add executable runtime invariants.
2. **`event_catalog.schema.json`:** add closed event/candidate/memory/NOT_FOUND
   unions and split model-visible read results from audit-only digests.
3. **`rng_contract.json`:** derive from a treatment-invariant seed projection;
   define common-seed versus analysis-only pairing and exact backend mapping.
4. **`private_field_registry.json`:** remove actor from opaque memory; enumerate
   every IPC-relevant information class and consumer.
5. **`visibility_contract.md` and `change.json`:** split reader, Think, and actor
   stages and bind actor's minimal input/output schema.
6. **`semantic_contract.md`:** choose JCS Unicode-string or canonical encoded
   octet identity, specify domain bytes, and reconcile payload/candidate caps.
7. **`resolver_reducer.md`:** define phase-specific COMMIT/ABSTAIN, K=2
   Dream-1 selection, capability issuance/lookup, token-remaining transitions,
   and receipt variants.
8. **all eight prompts:** use typed single-envelope markers; fix Dream-1 and
   one-shot capability chronology, one-shot LOCK, schema/version, budgets, and
   untrusted-data rendering.
9. **`resource_manifest.md`:** encode caps, prospective generation policy,
   frozen sampling/runtime identifiers, maximum fixture derivation, and the
   complete CPU allocation while retaining the verified call/token sums.
10. **`analysis_contract.md`:** make the Stage-1 conjunction executable and
    exhaustive.
11. **`experiment_spec.md`, `assignment_ledger.md`, `v1_disposition.md`,
    `premortem_disposition.md`, and acceptance-test text:** reconcile every
    statement that currently says the missing schemas/capability flow/seed
    coupling are already complete.
12. Recompute all v2 hashes and `change.json`, then repeat this static audit
    before any intake initialization.

## Final disposition

Do not initialize intake at the reviewed SHA. The causal roster, negative,
lane separation intent, and resource sums are worth preserving, but the exact
runtime surface presently permits arbitrary schema-valid values, fails to type
two of its three read classes, does not deliver common seeds to declared
couples, and exposes memory to the actor by contract.

A repaired proposal can remain exactly 3,414 scientific/3,416 process calls.
It needs new bytes, a new SHA, and another pre-intake static audit. This document
does not perform or authorize that repair.
