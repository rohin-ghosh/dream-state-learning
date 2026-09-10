# v2 mandatory static fixture contract for P4–P14

This file freezes every scientifically material fixture dimension and mutation
class, expected decision, and failure behavior for proposal/intake review. It
authorizes no implementation or run and records no executed P1--P14 closure.
Exact incidental witness bytes that cannot enter a model input or scientific
assignment (for example a harmless regex witness used only by a schema unit
test) are implementation artifacts under
`research_loop/advisory/20260902_pcfl_v2_fixture_authority_adjudication.md`.
Only after separate exact human ratification, and before executing Stage 0,
must the implementation materialize every named case as a literal hash-bound
fixture catalog. Stage 0 then executes that catalog, emits each named receipt
as JCS, and binds source/contract hashes. T17 independently rehashes and
reviews the catalog and executed receipts before any pre-GPU decision. A
mismatch stops `NOT_RUN`; a future implementer may not choose a new scientific
value, weaken, omit, sample, or reinterpret a case. Any required scientific
choice returns to a new architecture intake.

## F01 — typed phase/state protocol

Generate one minimum and one maximum valid object for each of the 21 root
branches of `semantic_dsl.schema.json`; each must match exactly one `oneOf`
branch. Validate the corresponding phase/op transition in
`resolver_reducer.md`. Root instances `{}`, `null`, `[]`, `"x"`,
`{"op":"BOGUS"}`, an unknown member, and a private-field injection must fail.

Negative traces cover wrong-phase USE/PREDICT/COMMIT, candidate-REVISE,
missing/duplicate/reordered node references, stale/unread/future/other-session
capability, Dream-1 singular-capability field rather than ordered 1–2 pool,
Dream-2 COMMIT with zero/two capabilities, ABSTAIN with capability/payload,
and any PREDICT containing NOTE/AST payload bytes rather than a manifest.

`F01.01_D2_RETAIN_TRACE` is exact: Dream-1 authors nodes, PREDICTs C01/C02,
COMMITs their ordered capability pool; clone minting creates fixed Dream-2
candidate handles; fresh Dream-2 charges one candidate READ and raw-A READ;
PREDICT RETAIN has no new node list and includes nonempty
`decision_provenance_receipt_ids` containing the receipt ref of that sole
charged raw-A READ; its manifest provenance cites the matching raw-A handle.
The staged record freezes manifest decision RETAIN, the
issued capability, and the ordered provenance list. COMMIT repeats all three
values exactly and selects exactly the capability assigned for that RETAIN
manifest. The
materialized payload is byte-identical to the chosen Dream-1 candidate and no
harness-authored semantic bytes appear.

`F01.02_D2_RAW_A_PREDICT_POSITIVE` is the required positive wording: “Starting
with a fresh Dream-2 session, charge exactly one RAW_A_EVENT READ at zero-based
resolver ordinal `r_a`; its audit `operation_ordinal` and model-visible step
ordinal are `r_a+1`. At a later resolver ordinal `r_p`, accept exactly one
decisive RETAIN or REPLACE PREDICT whose ordered
`decision_provenance_receipt_ids` contains that sole raw-A `receipt_ref` and
whose manifest provenance contains the matching raw-A handle and whose B
predictions are exactly B1,B2. Store decision, issued object capability,
and provenance array with the staged manifest. Accept COMMIT only when all
three values are byte-for-byte equal to the stored staged values.” Expected:
accepted staged candidate and matching terminal COMMIT.

`F01.03_D2_RAW_A_PREDICT_NEGATIVES` is the required negative wording: “Reject
before mutation each trace with decisive Dream-2 PREDICT before any charged
RAW_A_EVENT READ; with zero or two charged raw-A reads; with missing, empty,
future, stale, other-session, non-raw-A-only, or sole-raw-A-omitting
`decision_provenance_receipt_ids`; with manifest provenance omitting the
matching raw-A handle; or with provenance introduced for the first
time at COMMIT. After a valid PREDICT, reject COMMIT if its decision, candidate
capability, receipt-ref order, receipt-ref membership, or receipt-ref bytes
differ from the staged manifest tuple.” Expected: first terminal failure, no
semantic mutation, no retry, and no corpus.

## F02 — receipt and delivery grammar

Generate one minimum/maximum valid value for each of the 17 root branches of
`event_catalog.schema.json`; each matches exactly one branch. Test event,
candidate, NOTE, AST, NOT_FOUND, target-menu, interactive audit, and one-shot
batch/audit forms. Empty/arbitrary roots, unknown members, wrong handle/result
kind or phase, unread handle, open payload, over-cap value, digest/byte count in
any model-visible read result, model-visible audit receipt, target menu before T3, and
target/source-event injection into a memory receipt all fail.

A candidate READ assigns its fixed-shape, ordinal-derived Dream-2-session capability, returns
the exact immutable Dream-1 candidate, and hides digest/address/path/length/
variant/cache/dedup. A one-shot batch's event order, JCS bytes, charged-read
count, receipt order, and total bytes equal the source ledger in the audit-only
comparison; model-visible `ONE_SHOT_EVENT_BATCH` has no `jcs_byte_count`, byte
length, or digest member. Missing, duplicate, reordered, or uncharged event
fails. The immutable one-shot Dream-1 candidate pool uses capability-free
`one_shot_provenance` containing only `public_handles`; inserting
`node_capabilities`, `candidate_capabilities`, or any node/object capability at
the candidate or nested NOTE level fails schema validation. Recurrent and
one-shot Think reject any source-event or extractor record.

`F02.01_MODEL_VISIBLE_IDENTIFIER_IDENTITY` checks direct public event/raw-A
handles against event kind plus one-based source ordinal. It separately covers
opaque public event/raw-A receipt refs, Dream-1 candidate handles and candidate-read capabilities,
target-memory handles and memory-read receipt refs, and session-local authored
node/object capabilities. Each value must match its fixed shape and the
`model_visible_identifier` namespace's deterministic ordinal vector. Clones
with corresponding topology/ordinals must have byte-identical values. Changing
content, h/q, condition/cut/intervention, model bytes, digest/address/path/
length, cache/dedup, timing/error, or score must not change a value; forced
collision, nondeterminism, or paired-value divergence fails.

`F02.02_ONE_SHOT_INPUT_CAPABILITY_CLOSURE` is mandatory evidence for T06 and
T07. Generate minimum and maximum valid `DREAM1_ONE_SHOT`,
`DREAM2_ONE_SHOT`, and `THINK_ONE_SHOT` envelopes. Each must use the closed
`one_shot_resolver_state`; Think must use `one_shot_ast_memory_packet` whose
records use `one_shot_ast_record` and `one_shot_provenance`. Recursively at
every object location, separately inject every capability-bearing property
name declared anywhere in either schema, including
`workspace_node_capabilities`, `staged_object_capabilities`,
`node_capabilities`, `candidate_capabilities`, `node_capability`,
`object_capability`, and `candidate_capability`. Separately replace each
one-shot public-handle provenance/citation value with a schema-valid recurrent
node or object capability, and replace each one-shot AST record/provenance with
the corresponding schema-valid recurrent form. Expected: every mutation fails
schema validation; no reducer or model invocation occurs. A recursive `$ref`
reachability check from all three one-shot input roots must reach none of
`resolver_state`, `ast_memory_packet`, `ast_record`, `provenance`,
`citation_ref`, `node_capability`, or `object_capability`.

## F03 — prompt/envelope and one-shot chronology

Every prompt contains exactly one `{{INPUT_ENVELOPE_JCS}}` marker and no other
marker. Missing, duplicate, unknown, unused, adjacent, or unescaped insertion
fails. Minimum/maximum recurrent Dream/Think and one-shot Dream/Think envelopes
validate with exact contract version, mode, lane, ordinal, budgets, state,
last-read result, and only mode-allowed packets; generic factor/null bytes are
identical outside named payload values.

One-shot Dream-1 COMMIT returns one or two complete candidates and selects
existing response-local C01/C02 slots; each candidate and nested NOTE has
capability-free provenance whose sole member is `public_handles`; ABSTAIN
returns empty arrays. One-shot
Dream-2 RETAIN selects one immutable input `source_dream1_slot`, carries exact
B1/B2 predictions and raw-A `decision_provenance_receipt_ids`, and contains no
candidate/capability/selected-candidate field. RETAIN with a candidate is a
required reject. REPLACE names its immutable D1 source, carries exactly one
response-local D2C01 candidate, selects D2C01, and cites raw A. Missing/wrong
raw-A provenance, post-response capability echo, absent source slot, two D2
candidates, capability-named provenance anywhere in the immutable D1 pool, or
ABSTAIN with content fails. ONE_SHOT_PLAN accepts exactly four
typed legal USE strings and terminal LOCK; short, fifth, missing-LOCK, wrong
target, feedback-adaptive, or opaque-memory plan fails. Its four USE values are
actor IPC; its terminal LOCK is consumed locally and any actor invocation or
actor input containing LOCK fails.

`F03.01_ONE_SHOT_OUTPUT_CAPABILITY_CLOSURE` is mandatory evidence for T06 and
T07. Generate minimum and maximum valid outputs for every atomic one-shot variant.
Dream candidates and every nested NOTE/record must use the dedicated one-shot
candidate/record/provenance definitions; every `ONE_SHOT_PLAN` citation must
use `one_shot_citation_ref` and therefore be a public handle. Recursively at
every output object location, inject each capability-bearing property name
listed in F02.02; replace every public-handle provenance/citation value with
each schema-valid recurrent node/object capability type; and substitute the
corresponding generic recurrent candidate, record, provenance, or citation
form. Expected: every mutation fails schema validation before staging,
materialization, actor dispatch, or state mutation. Recursive `$ref`
reachability from all five top-level one-shot output branches must reach none of
`dream1_candidate`, `dream2_candidate`, `ast_record`, `provenance`,
`citation_ref`, `node_capability`, or `object_capability`. This fixture defines
mutation classes, not incidental literal witness bytes.

## F06 — opaque identity and executable capacity

NOTE identity fixtures parse valid Unicode `text`, reject duplicate keys,
malformed UTF-8, isolated surrogates/non-I-JSON values, and hash the closed
schema-valid NOTE's JCS UTF-8 without Unicode normalization. Literal versus
escaped spellings of the same scalar produce identical identity; composed and
decomposed strings remain distinct. Raw response bytes remain audit-only. The
two exact domain-separator byte vectors in `semantic_contract.md` have golden
SHA-256 addresses.

Schema-generated cap-1/cap/cap+1 values cover NOTE/AST value 256 JCS bytes,
complete node 512, materialized payload 2,510, complete candidate 3,072, every
bounded string/array/container, and Dream-1 K=2/Dream-2 K=1 live state.
Maximum recurrent and atomic one-shot renderings must fit the exact token/
context envelope; any legal-schema object that exceeds a containing cap makes
the contract fixture fail rather than relying on runtime truncation.

## F04 — common randomness and runtime freeze

- `F04.01_HMAC_GOLDEN` uses the fixture root-secret, exact seed-key UTF-8
  string, digest, and uint32 in `rng_contract.json`; all four values must match.
- `F04.02_TREATMENT_INVARIANCE` clones that row and changes, one at a time,
  `h_or_q`, descriptive `lane`, `condition_id`, `memory_variant_or_cut`,
  `arm_id`, `cut_id`, and `scientific_or_diagnostic`. Expected: seed-key bytes, digest, backend seed,
  and sampler config remain identical.
- `F04.03_RETAINED_FIELD_REJECT` changes, one at a time, root, z side, sampling lane,
  phase role, target, goal twin, draw role, or resolver ordinal while retaining
  the same COMMON_SEED group. Expected: reject the whole group before calls.
- `F04.04_REQUIRED_PAIRS` materializes h0/h1 Dream-2 and selected-h
  SELF/EMPTY/CROSSED/SHAM pairs for every ordinal. Expected: identical
  seed-key JCS, digest, backend seed, topology, and literal sampler fields.
- `F04.05_ANALYSIS_ONLY` pairs each structured one-shot AST plan with its
  iterative AST comparator. Expected: `ANALYSIS_PAIR_ONLY`, distinct coupling
  groups and seed keys, and no stepwise-equality assertion.
- `F04.06_DOMAIN_RANGE_ENDIAN` changes only namespace/group and checks domain
  separation; digest octets `3e 1b 04 97` map to decimal `1041958039`, not a
  signed or little-endian value.
- `F04.07_RUNTIME_MUTATION` changes every leaf of `runtime_envelope.json` one
  at a time. Expected: executable-freeze rejection. Exact-stack build/import,
  tokenizer resolution, model load, or maximum-context failure is NOT_RUN and
  cannot select a replacement environment.
- `F04.08_MODEL_VISIBLE_IDENTIFIERS` recomputes every identifier golden vector
  in `rng_contract.json`; verifies the 16-byte digest prefix, base64url encoding
  with no padding, and exact per-kind fixed length; verifies clone invariance
  after changing each excluded content/treatment/audit field; rejects a forced
  collision for distinct namespace messages; and verifies that a
  branch-natural issuance-tuple change produces a distinct identifier. Apply
  this to public event/raw-A receipt refs, Dream-1 candidate handles
  and candidate-read capabilities, target-memory handles and memory-read
  receipt refs, and session-local authored node/object capabilities. Expected:
  byte-identical values across corresponding paired topology and ordinal; no
  content-derived or nondeterministic identifier.
- `F04.09_ORDINAL_OFFSET` enumerates every recurrent topology endpoint. For
  every zero-based `resolver_ordinal = r`, expected rendered
  `state.resolver_ordinal = r`, `INPUT_ENVELOPE.operation_ordinal = r+1`,
  model-authored `RESOLVER_STEP.ordinal = r+1`, and charged
  `AUDIT_READ_RECEIPT.operation_ordinal = r+1` when a read occurs. Any endpoint
  with `operation_ordinal != resolver_ordinal+1`, including the first and last
  opportunity of each topology, is rejected before invocation or mutation.
- `F04.10_FUTURE_EXECUTABLE_SNAPSHOT` asserts that these proposal bytes claim
  no implemented identifier/JCS source bytes, binary hash, or executed golden
  receipt before ratification. After exact human ratification and scoped
  implementation, the executable snapshot must be newly hashed, all vectors
  must be run, and T17 must independently rehash/review the snapshot before a
  pre-GPU decision. The snapshot may implement frozen semantics but may not
  introduce or select a new semantic choice.

## F05 — complete IPC inventory and actor firewall

For every field in `private_field_registry.json`, serialize a minimal valid
value and inject it separately at every non-consumer boundary. Expected:
pre-dispatch rejection. Inject one undeclared member named `x_extra`; expected:
rejection at every closed IPC object.

`F05.01_ACTOR_TRANSDUCER` freezes one valid public state, legal menu, USE, and
actor-transition object. It then mutates NOTE/AST/candidate/corpus/index,
query/result, memory handle/capability, digest/address/path/length/dedup/cache,
root/h/q/z/condition/cut/intervention, public goal, target ID/truth, seed, timing/error,
certificate, score, and report fields. Expected: serialized actor input and
actor output remain byte-identical. Direct injection of each field is rejected.
Replace USE with LOCK or inject LOCK beside USE. Expected: pre-dispatch
rejection and zero actor invocations; LOCK terminates Think locally.

`F05.02_HANDLE_IDENTITY` renders SELF, EMPTY, OBSERVED, CROSSED, and SHAM
clones before a permitted read result. Expected: byte-identical prompt/input,
memory-handle and topology-corresponding memory-read receipt-ref literal values,
count, order, and shape. The same equality applies to public event/raw-A refs,
Dream-1 candidate handles/read capabilities, and authored node/object
capabilities wherever paired topology corresponds. Changed value, count,
order, content-bearing or nondeterministic capability, forced collision,
paired-value divergence, path, address, digest, variant, dedup, cache, timing,
or length descendant is rejected.

`F05.03_DIGEST_OWNER` gives a corpus digest only to the noncognitive integrity
checker. Expected: Dream, Sleep cognition, target reader cognition, Think,
actor, primary reducer, and primary reporter inputs contain no digest or
descendant.

## F07 — resources and executable envelope

`F07.01_CPU_SUM` evaluates the eight Stage-0 maxima in
`resource_manifest.md`: `1344+16+15+25+40+30+55+15 = 1540 <= 1560` CPU minutes;
remaining containment margin is exactly 20. It separately checks 128 x 10.5 =
1,344 and the 26-hour CPU/wall stops. Adding any unledgered suite fails.

`F07.02_RESOURCE_BOUNDARIES` generates cap-1/cap/cap+1 cases for every input,
raw/accepted output, JCS byte, phase-token, live-tuple, read, action, call,
replay, storage, device, CPU, and wall cap. Expected: cap-1/cap accept if all
other invariants hold; cap+1 fails without truncation or row deletion.

`F07.03_PROSPECTIVE_DREAM` begins Dream-1 with remainder 8,192 and Dream-2 with
4,096. Before operation parse, requested maximum is `min(2048,remainder)`.
After parse, accepted node/read=512, PREDICT=2,048, and terminal/PASS=256.
Malformed output consumes its full raw count. Negative or increased remainder
is rejected.

`F07.04_MAX_CONTEXT` schema-generates every maximum input and tokenizes it with
the deterministically resolved tokenizer/chat template. The structured
one-shot case must fit exactly the declared `32768+15872=48640` upper bound in
the 65,536-token context. Any legal object exceeding its cap is NOT_RUN, not a
truncation or schema retry.

`F07.05_FORECAST` predicts the complete roster against one eligible >=96-GiB
TP=1 device, 18 device-hours, 24 scientific wall-hours, and 50 GiB storage.
Overrun returns whole-roster NOT_RUN. The fixture makes no lease-availability
or throughput claim.

`F07.06_THINK_REMAINDERS` checks the exact phase output budgets: iterative D1
is `10*512 = 5,120`, iterative D4 is `31*512 = 15,872`, and structured D4 is
`15,872`. Every preallocated call row, including `NOT_INVOKED`, carries
non-null integer `phase_tokens_remaining_before` and
`phase_tokens_remaining_after`; null is valid only for accepted/canonical output
when no output exists, never for phase counters. For an invoked accepted or
malformed opportunity, before/after values are continuous with adjacent
ordinals and the after value equals before minus the charged raw output tokens;
malformed output remains debited. For a preallocated `NOT_INVOKED` suffix,
before equals after at each unopened opportunity and the integer remainder is
carried forward unchanged. Any discontinuity, negative value, missing debit,
null counter, or NOT_INVOKED decrement fails.

`F07.07_AGGREGATE_WATCHDOGS` independently checks exact arithmetic:
scientific output maximum `1,709,056` plus diagnostic output maximum `31,744`
equals process output maximum `1,740,800`, leaving margin `9,200` under the
hard `1,750,000` stop; process input maximum `56,131,584` plus process output
maximum `1,740,800` equals process combined maximum `57,872,384`, leaving
margin `127,616` under the hard `58,000,000` stop. The margins are watchdog
containment only: allocating either margin to a call, retry, replay, larger
output, new cell, or adaptive work fails.

## F08 — exact Stage-1 gate and revision receipt

Let bits be ordered `G01..G11`. Evaluate all integers `n=0..2047`; bit `i` is
the corresponding Boolean conjunct. Expected `STAGE1_PASS=true` iff
`n=2047`. This is the complete 2^11 truth table, not a sampled table.

Starting from the all-true case, separately inject: missing/duplicate row;
each single false G01 through G11; missing/duplicate/wrong-kind/wrong-ID gate
receipt or evidence row; failed pair member; first-action or strict-contrast
tie; illegal/missing first action; equal SELF/EMPTY mean; equal SELF/CROSSED
mean; zero/two charged raw-A reads; zero/two charged candidate-parent reads;
either read uncharged; equal raw-A and candidate-read receipt IDs; either read
at or after PREDICT; absent/wrong raw-A receipt in
`decision_provenance_receipt_ids`; absent/wrong candidate-read receipt there;
raw-A handle absent/wrong in `public_handles`; candidate-read handle/hash not
identifying exactly one ordered pre-A pool member; PREDICT
`parent_candidate_capability` unequal to the capability minted by that read;
PREDICT decision RETAIN; terminal decision RETAIN; ABSTAIN; terminal COMMIT
selecting a capability other than the PREDICT-issued capability; COMMIT
decision-provenance unequal or reordered relative to PREDICT; selected
candidate hash equal to any pre-A pool candidate hash; false
`changed_from_every_pre_a_candidate`; unequal h-paired ordered pre-A pools;
mismatched Dream-1 clone or seed-key hash; equal h selected-candidate hashes;
false `branch_selected_bytes_differ`; and all previously registered actor,
sham, oracle, stage, and roster negatives. Every case must fail G04 or
invalidate the receipt as specified, terminate HUMAN_REQUIRED, and leave Stage
2 NOT_TRIGGERED.

`F08.01_REVISION_POSITIVE` has two z sides and h0/h1 COMMON_SEED Dream-2
branches. Each branch resolves against its complete fresh trace and ordered
one-or-two-candidate Dream-1 pool; has exactly one charged raw-A read and
exactly one charged candidate-parent read at distinct resolver ordinals before
the decisive PREDICT; includes both exact receipt refs exactly once in
`decision_provenance_receipt_ids` and the exact raw-A handle exactly once in
`public_handles`; binds the candidate-read handle/hash to exactly one pool
member and its minted capability to `parent_candidate_capability`; emits a
decisive `decision=REPLACE` PREDICT; and later COMMITs `decision=REPLACE`,
exactly that PREDICT capability, and byte-identical ordered provenance. The
selected JCS hash differs from every pre-A pool hash. Within each h pair,
ordered pre-A pools, Dream-1 clone hashes, and seed-key hashes match
byte-for-byte while selected hashes differ. Expected: G04 true. It establishes
a selected-object update only, never semantic appropriateness, content rewrite,
or action mediation.

## F09 — pre-target sham

`F09.01_SIGNATURE` freezes constructor/seed/input projection at T0, then after
authentic corpus freeze at T2 and before any T3 target/query rendering calls
the exact counter constructor in `experiment_spec.md` with its allowed
pre-target inputs. Expected: first
matching counter, or a total `SHAM_EXHAUSTED` receipt after counter 65535.
Repeated calls are byte-identical. A later/lower-priority match cannot replace
the first.

`F09.02_TARGET_MUTATION` holds constructor inputs fixed while mutating target,
goal, query trace, result, score, comparator, and report values. Expected:
identical constructor receipt and corpus bytes. Passing any such field directly
is rejected.

Every receipt records constructor ID/domain, source-footprint hash, root/z/h=0,
runtime/tokenizer/JCS IDs, counter or null, attempts 1..65536, every requested
and achieved note/token/byte/provenance/index bucket, status `MATCHED` or
`SHAM_EXHAUSTED`, and corpus audit hash only for MATCHED. Exhaustion keeps the
assignment and yields endpoint zero; no alternate sham is chosen. Report lint
rejects opaque `false`, `meaningless`, `random noise`, and solution/no-solution
classification.

## F10 — manifest, denominator, and replay totality

`F10.01_CARDINALITY` runs the canonical expansion twice and independently
recomputes:

```text
Stage 1 = 128 Dream + 782 recurrent Think = 910
Stage 2 = 356 Dream + 2144 recurrent Think + 4 one-shot Think = 2504
total   = 484 Dream + 2926 recurrent Think + 4 one-shot Think = 3414
process = 3414 + replay-001 + replay-002 = 3416 opportunities
```

Expected call IDs are exactly `s1-call-0001..0910` and
`s2-call-0001..2504`. Delete, duplicate, reorder, or add one call/assignment;
change stage, lane, selected h, target, topology, sampler, coupling kind/key,
denominator, or replay flag; add h=1 cut, opaque one-shot Think, unlisted
baseline, adaptive panel, or third replay. Each mutation is rejected.

`F10.02_STATUS_ORTHOGONALITY` verifies legal wrong =
`ASSIGNED/OPENED/RETURNED/ACCEPTED/0/LEGAL_WRONG`; timeout and malformed remain
assigned zeros; unopened Stage 2 =
`ASSIGNED/NOT_TRIGGERED/NOT_INVOKED/NOT_APPLICABLE/null/NOT_TRIGGERED`.
Summaries divide by assigned endpoint rows, never successes.

`F10.03_REPLAY` injects each of the four allowed pre-response infrastructure
classes in canonical call order. The first two distinct eligible calls bind
the two slots with exact source bytes/seed/runtime; a third remains unreplayed.
Timeout, malformed, wrong legal output, unavailable read, forecast failure,
and post-response fault consume no replay. Replay output never changes an
endpoint.

`F10.04_GATE_BINDING` supplies every literal G01–G11 receipt ID with its exact
schema kind and bound evidence row, including the decisive PREDICT raw-A handle
and receipt-ref fields. Expected: the all-true binding validates. Substitute an
arbitrary receipt ID, a valid ID of the wrong receipt kind, a duplicate ID, or
an evidence row not literally bound by the manifest. Expected: whole gate
binding rejection before reduction.

`F10.05_CALL_LEDGER_ORDINAL_AND_REMAINDER` gives an invoked Think-D4 row
`phase_tokens_remaining_before=15872`, raw debit `512`, and
`phase_tokens_remaining_after=15360`; expected: accept. Replace before with `15873`
or set either invoked counter to null; expected: reject. A preallocated
NOT_TRIGGERED/NOT_INVOKED row has integer before=after=`15872`; expected:
accept. Set either counter to null or decrement it; expected: reject. In every
case, display `operation_ordinal` must equal zero-based `resolver_ordinal+1`;
any other displayed ordinal is rejected.

## F11 — q fields and consequences

For each vector below, controls not shown are all zero and row order is the
manifest's `(z_side,goal_twin)` order.

| q0 SELF | q1 SELF | positive control contrasts | ANY | CONCERN |
|---|---|---|---:|---:|
| 0000 | 0000 | neither | 0 | 0 |
| 1000 | 0000 | neither | 1 | 0 |
| 1110 | 0000 | neither | 1 | 1 |
| 1100 | 1100 | q0 both only | 1 | 0 |
| 1100 | 1100 | both contrasts for both q | 1 | 1 |
| 0000 | 1000 | singleton q1 only | 1 | 0 |

Stage 0 additionally evaluates the complete 16 SELF x 16 EMPTY x 16 OBSERVED
vector product for each q and their joint product, plus every finite declared
target-blind policy/coupling class. `ANY` emits only
`independent_self_success_observed`; `CONCERN` emits only
`registered_specificity_concern`. Neither changes execution or the terminal
HUMAN_REQUIRED state. Any pooling, binomial/p-value/interval, identification,
prevalence, or population interpretation fails lint.

Named boundary expectations are exact: a singleton SELF success makes
`ANY_INDEPENDENT_SUCCESS=true` and `SPECIFICITY_CONCERN=false`; one q with
positive controls but fewer than three of four SELF successes leaves
`SPECIFICITY_CONCERN=false`; at least three of four SELF successes for the
declared q together with that q's required strict controls makes it true; and
the both-q case requires the strict controls independently for both q values.
The complete per-q vector product above is exhaustive, not sampled.

## F12 — opaque report access and claim lint

`F12.01_PROJECTION` attempts to pass every inventory field to primary reducer
and reporter. Only the allowlist in `visibility_contract.md` is accepted. Raw
NOTE/corpus/prompt/response bytes, lexical tokens, content summaries, and
inspection-selected examples are rejected. Any pre-freeze access invalidates
the report.

After report hash freeze, exploratory raw access must append an access receipt
and cannot mutate any row, gate, alarm, report, or state. Negative reports
claiming factor semantics, truth/falsity, solution content, mechanism,
h-mediated action, raw perception/discovery, recurrence, superiority,
efficiency, replication/generalization, persistence, lifetime, LoRA, A-MEM, or
paper efficacy fail. The exact positive descriptors in `analysis_contract.md`
pass.

## F13 — extractor delivery boundary

Enumerate all 720 S6 permutations and at least one arbitrary bijective global
relabeling per permutation. Expected extractor output is the literal position
map and is invariant to relabeling. Malformed/nonbijective trays, slot-based
action payloads, and any extra
history/root/h/q/z/target/goal/corpus/cache/score input or
inverse/closure/path/factor output are rejected.

Hold valid before/after arrays fixed and vary the valid typed
`USE(stem::suffix)` provenance action. Expected: identical permutation, proving
the action does not determine the extraction.

Interactive and sealed-batch modes use the same event bytes and extraction.
Batch count/order/bytes/total/K/R charges must equal the source-event ledger.
Bytes/total live only in the audit sibling; adding `jcs_byte_count`, any byte
length, or digest to the model-visible batch is rejected. An unread event has
no extraction. Injecting a source event/extractor record
into recurrent or one-shot Think is rejected. The rendered factor/q null is
rechecked after exact extraction and serialization. Only the “supplied local
permutation” descriptor passes claim lint.

## F14 — roster and conditional-scope preservation

Independently expand every cell in `assignment_generator_contract.md` and
compare row, assignment, call, coupling, stage, and replay summaries. Require
the exact four named sampled-z AST structured one-shot rows, h=0-only
crossed/sham cuts, absence of the 372-call h=1 cuts, and Stage 2 opening solely
through the G01–G11 gate. One extra/missing call, replacement of a failed row,
Stage-2-before-pass, result-triggered panel, new seed/prompt/root, or excluded
baseline fails.

The positive report is limited to an exact-root, selected-h, conditional
pre-context DEV using supplied local permutations. The registered next step is
only a new, separately deliberated and ratified powered-root confirmation plus
a separate genuine post-context/lifetime design; it is never part of or
automatically authorized by v2.
