# PCFL-Compose v2 exact-byte pre-intake adversarial audit

**Date:** 2026-09-02  
**Verdict:** **REWORK BEFORE INTAKE**  
**Status:** read-only, pre-intake scientific/design audit. This artifact does
not edit or initialize v2 intake, authorize implementation or CPU/model/GPU
work, ratify any bytes, or license a scientific or paper claim.

## Exact object audited

The authored proposal is:

- `change_id`: `chg_20260902_pcfl_compose_self_revision_text_dev_v2`
- recomputed `change.json` SHA-256:
  `2fc2521d821efc2ff4852ef9decbb4c2bdf834a8f1b0ff438aec7e78d2a0f047`
- declared context entries: 77
- missing context files: 0
- context hash mismatches: 0
- duplicate context paths: 0
- authored files in the v2 change directory: 25, all 24 files other than
  `change.json` present in its context array
- acceptance-test IDs: 19

The repository's read-only `validate_change` path accepts the architecture
artifact and all context bindings. That is necessary provenance evidence, not
evidence that the experiment-specific JSON files validate the objects their
names claim to validate.

I read every authored v2 file, the v2 token/state advisory, the twenty-item
premortem and its disposition, and the v1 critique/consensus disposition.
No v2 file was edited and no intake transition, implementation, construct run,
model call, or GPU call was performed.

## Strongest case

The authored bundle incorporates much of the intended repair. It names only
three DEV roots; separates prediction, raw-A response, and selected-h
corpus-to-action language; removes optional model panels; fixes the successful-
branch arithmetic at 3,414; confines one-shot Think to four selected AST rows;
specifies a pure event-local extractor; explicitly declines h-to-action
mediation; makes opaque evaluation nonsemantic; narrows sham claims; reduces
candidate size; and introduces typed catalogs, field/RNG contracts,
content-addressed staging, q-specific controls, executable-environment locks,
and report restrictions. The proposal and all 77 references are byte-clean.

The remaining failures are nevertheless architectural, not editorial. Several
normative files cannot jointly describe a runnable trace. In particular, the
schemas accept arbitrary objects, the stated common-random-number derivation
gives different seeds to the rows it says are coupled, one-shot Dream requests
a capability that cannot yet exist, and the actor is explicitly allowed to
consume opaque note bytes. Those defects defeat the ownership and causal
claims even if future code happens to implement the intended design.

## Blocking defects

### `V2_PRE_B01`: Both JSON “schemas” validate no root object

`event_catalog.schema.json` declares custom top-level members
`pre_read_catalog_entry` and `charged_read_receipt`, but contains no root
`type`, `properties`, `$defs`, `$ref`, `oneOf`, or other assertion connecting
an instance to either object. Under Draft 2020-12, unrecognized/custom keywords
do not constrain the instance. An empty object or an object containing private
truth is therefore valid against the root document.

`semantic_dsl.schema.json` has the same fatal shape. Its `definitions` are not
referenced by the root and the root has no instance assertion. Even treating
`definitions` as a legacy container, `{}`, `{"op":"BOGUS"}`, or an arbitrary
private-field packet satisfies the root. The prompts' instruction to use “the
JCS RESOLVER_STEP schema” therefore refers to no validating root schema.

The nested definitions are also too weak if manually selected:

- `resolver_step` contains only `op`, `ordinal`, and `phase`; it cannot encode
  a READ handle/query, a model-authored NOTICE/CONNECT/REVISE node, PREDICT
  manifest/predictions, USE action, LOCK, or citations;
- `staged_candidate.predictions` is an unconstrained object and can omit A/B
  commitments or carry forbidden fields;
- no OPAQUE_NOTE node, AST record, candidate manifest, Dream-1 commitment,
  Dream-2 commitment, candidate-read receipt, lexical-read receipt, or
  one-shot Dream object is defined;
- `one_shot_plan.actions` has no item schema or minimum cardinality and the
  object has no terminal LOCK field; and
- `additionalProperties:false` on the outer charged receipt does not constrain
  its `payload`, which can carry arbitrary extra/private members.

**Exact fix.** Replace the documents with real Draft 2020-12 root schemas.
Use `$defs` plus a root `oneOf`/discriminator over every phase- and operation-
specific response. Recursively set required fields and
`additionalProperties:false`; define exact A1/A2 and B1/B2 shapes, public
handles, node contents/references, NOTE and AST objects, READ/USE/LOCK, each
one-shot object, and phase-specific terminal variants. Define separate catalog
and receipt unions for TREE_EVENT, RAW_A_EVENT, CANDIDATE, memory NOTE/AST, and
TARGET_MENU. Add negative fixtures showing that `{}`, unknown operations,
private fields, missing predictions, wrong-phase operations, arbitrary action
types, and event fields inside a candidate receipt all fail under the actual
root validator. Until this is fixed, T05/T06/T07/T09/T11/T14 cannot be an
implementation contract.

### `V2_PRE_B02`: The charged-receipt schema cannot represent its declared handle kinds

The catalog permits `TREE_EVENT`, `RAW_A_EVENT`, `CANDIDATE`, and
`TARGET_MENU`. Its single charged receipt requires a payload with
`before`, `action`, `after`, and `slot_permutation`. That shape is appropriate
only for a public tray event. A Dream-2 candidate-package read and a target or
memory read cannot conform. Conversely, because the payload object has no
property assertions, a tray receipt can legally include `family`, `h_or_q`, a
target, a closure, comparator fields, or arbitrary content despite the
top-level prose allowlist.

**Exact fix.** Split handles and receipts into discriminated closed schemas.
A public-event receipt alone contains the raw tray and extracted permutation.
A candidate receipt resolves a fixed opaque candidate handle to the exact
permitted candidate bytes/manifest only after charge. A target-menu receipt
contains only public target/action fields after T3. Lexical and AST readers
have their own closed return types. Add cross-kind negative tests and a
field-level taint test over the serialized bytes, not a prose array named
`forbidden_before_read`.

### `V2_PRE_B03`: The common-random-number derivation mathematically breaks every intended pair

`rng_contract.json` says the seed is HMAC over
`fixed_row_fields_without_seed_digest` plus `coupling_group`. The required row
fields include `h_or_q`, `condition_id`, `memory_variant_or_cut`, `phase`, and
other treatment-varying values. Therefore two h Dream-2 rows with the same
coupling group still hash different `h_or_q` values. Authentic versus EMPTY,
OBSERVED, crossed, or sham rows still hash different condition/variant values.
Iterative versus one-shot rows still hash different phase/condition values.
Sharing a `coupling_group` does not make their HMAC messages equal and cannot
produce the promised same seed.

The derivation is additionally incomplete: it does not freeze the HMAC message
schema as actual JCS JSON, which exact fields are excluded for each contrast,
backend seed bit width, byte order, signed/range mapping, collision handling,
or the sealed-secret creation/binding receipt. The bundle also drops v1's
sampling parameters—no temperature, top-p, repetition penalty, stop sequence,
or decoding configuration appears—so an exact seed does not define an exact
model treatment.

**Exact fix.** Separate descriptive `invocation_row` fields from a canonical
`seed_key`. For each declared comparison, define a `coupling_key` consisting
only of fields common to the pair plus output-step ordinal; explicitly exclude
the treatment fields meant to differ. Bind a machine-readable table of paired
row IDs to identical complete HMAC messages and assert exact seed equality.
Define independent groups by domain-separated unequal keys. Specify the exact
secret-generation/freeze event, JCS object, HMAC bytes, full digest, backend
integer conversion, collision rule, and all decoding/sampler parameters. A
golden fixture must demonstrate seed equality for h0/h1 Dream-2,
authentic/control target Think, and the selected iterative/one-shot pairs, and
inequality for every intentionally independent pair. This is required before
the raw-A or corpus-action causal language is coherent.

### `V2_PRE_B04`: One-shot Dream asks for a capability that cannot exist in that call

The semantic contract correctly says one-shot Dream has no prior node registry
and the harness addresses its complete object only after accepting the single
response. Yet `one_shot_dream1.txt` tells the model to return candidates “then
reference one staged session capability in COMMIT.” The capability is generated
by the harness after the response is accepted, so it cannot be known inside
that same one-call response. The same problem occurs for a one-shot Dream-2
`REPLACE`: a newly authored replacement cannot have a harness capability before
the response that contains it has been parsed and accepted.

**Exact fix.** Define atomic one-shot response schemas that carry complete
candidate object(s) and select them by response-local candidate slot/ID. After
the single response validates, the harness may materialize the selected object
and issue its private content address; no capability round trip occurs. The
alternative is a second model COMMIT call per phase, which changes the
one-shot call counts, matching contract, 3,414 ledger, tokens, and proposal
hash. Add a causality fixture proving every model-visible selection value
exists before generation begins.

### `V2_PRE_B05`: “Session-local” capabilities cannot cross the fresh Dream-2 boundary as specified

Dream-2 is a fresh context/session that must inspect and RETAIN or REPLACE a
Dream-1 candidate. The only modeled reference is a `session_opaque_capability`
whose consumer is `same_session_dream`. A Dream-1 capability cannot therefore
be valid in Dream-2, but no deterministic clone-time rule mints Dream-2-local
candidate handles/capabilities. The event catalog admits `CANDIDATE`, while its
receipt schema cannot return one. The prompt does not distinguish a charged
candidate handle from a terminal capability.

Dream-1 also has up to two active candidates, while the COMMIT schema has one
singular `candidate_capability`. It is unclear whether Dream-1 commits one
candidate, an ordered one-or-two-candidate set, or whichever capability was
issued most recently. An `ABSTAIN` terminal still requires a capability in the
schema. Finally, all three decisions `RETAIN|REPLACE|ABSTAIN` are permitted in
every phase even though the reducer calls REPLACE Dream-2-only.

**Exact fix.** Define distinct noninterchangeable types:

1. fixed pre-READ candidate handle;
2. charged candidate read receipt;
3. session-local staged-object capability; and
4. terminal commitment-set capability.

At the Dream-1 clone boundary, mechanically mint fixed-shape Dream-2-local
handles in the same order and with h-invariant metadata. Define a Dream-1
terminal schema that explicitly commits an ordered one-or-two candidate set,
a Dream-2 RETAIN schema that names one read Dream-1 candidate, a REPLACE schema
that names a newly staged Dream-2 object, and an ABSTAIN schema with no
capability. Reject stale, unread, other-session, wrong-phase, reordered, or
ambiguous references. Bind collision-free capability generation; the current
`cap-` plus sixteen-character pattern is a shape, not a derivation or uniqueness
contract.

### `V2_PRE_B06`: PREDICT has mutually incompatible ownership/capacity semantics

The experiment says “A PREDICT emits a full candidate object to append-only
staging.” The reducer, semantic contract, resource manifest, change graph, and
generic prompt instead say NOTICE/CONNECT/REVISE author nodes first and PREDICT
selects a compact ordered manifest of their references without repeating node
or candidate payload bytes. These are different protocols with different
authorship, operation schemas, token maxima, and commitment boundaries.

The distinction is not cosmetic. The premortem capacity repair depends on the
manifest interpretation. If PREDICT emits a full 3,072-byte candidate under
2,048 output tokens, adverse tokenization can still fail. If it emits only
references, the schema must define how each prior operation authored a node,
how two candidate manifests share/reuse nodes, and exactly what the harness may
materialize without inventing semantic content.

**Exact fix.** Select one protocol everywhere. The coherent 3,414 design is:
each accepted cognitive operation emits one complete, bounded model-authored
node; PREDICT emits only a closed manifest and predictions; the pure reducer
resolves referenced nodes and constructs no new text/AST content. Amend the
experiment sentence and create the missing op-specific node/manifest schemas.
The max-token fixture must cover the complete operation response including
envelope and reason, not merely the node value.

### `V2_PRE_B07`: The actor is explicitly allowed to consume opaque memory

`private_field_registry.json` lists `opaque_note_bytes` consumers as
`sleep`, `surface_reader`, and **`actor`**. The proposal's visibility matrix
then merges `TARGET_THINK_ACTOR` and marks staged opaque bytes visible. The
graph even draws `FROZEN_LANE_CORPUS -> TARGET_TIME_ACTOR`. This permits a
direct corpus/digest-to-actor path that bypasses the reader and model Think,
while the scientific interpretation assumes the actor consumes only a legal
action and sealed private transition bytes.

Combining reader, Think, and actor also makes the public target and private
transition boundary unauditable: the Think model may see target/menu bytes but
not private transitions; the actor may use private transitions but must not see
the memory corpus, model workspace, capability, digest, or alternate action
plan.

**Exact fix.** Split the visibility stages into `TARGET_READER`,
`TARGET_THINK`, and `PUBLIC_ACTOR`. Make opaque/AST bytes visible only through
the lane reader to Think; remove actor from the opaque-note consumer list.
Actor input is exactly the current public tray/menu plus one schema-valid USE
action and its own sealed transition implementation. Replace the graph with
`CORPUS -> READER -> THINK -> PUBLIC_ACTION -> ACTOR`. Add a process-boundary
test that mutates corpus bytes/digests while holding the emitted action fixed
and proves actor input/output is identical. Without this repair, later action
differences need not demonstrate model reading or using memory.

### `V2_PRE_B08`: One-shot exposure contradicts the charged-read/extractor contract

Experiment Section 2 says every learned lane—including one-shot Dream,
iterative Think, and structured one-shot Think—receives public event payloads
only after a charged READ. The one-shot prompts instead receive all eligible
events in their single input and cannot perform an interactive read. Iterative
Think receives a frozen corpus, not public source events; structured one-shot
Think receives an AST packet. The event-extractor contract says it runs only
after “the selected raw event” is released by the charged reader, which does
not describe batch one-shot exposure.

This ambiguity can give one-shot Dream uncounted preprocessed events, or worse,
can leak original public experience into target-time Think despite the
visibility matrix forbidding it.

**Exact fix.** Scope the common extractor to public-event-consuming Dream and
OBSERVED/EXACT interfaces. Define two explicit delivery modes: interactive
charged receipt for recurrent Dream and a mechanically charged, complete
eligible batch built event-by-event for one-shot Dream. Record all batch
events/bytes against K/R and input budgets. State that iterative and one-shot
Think never receive source events or extracted event records unless the named
memory representation itself contains them. Update prompts, chronology, and
visibility tests accordingly.

### `V2_PRE_B09`: Candidate/payload byte maxima are internally impossible or undefined

The semantic contract permits a notes/records payload of 4,096 JCS bytes but a
“complete candidate” of only 3,072 JCS bytes, even though the complete
candidate is also said to bind/include every payload byte, prediction, parent,
citation, and audit field. Either the payload can exceed its container, or
“complete candidate” means only a manifest—contradicting other uses of that
term. The resource manifest separately says the payload is 2,510 bytes, which
is the single AST fixture's observed value, not a general opaque/AST schema
maximum.

`NOTE.text_bytes` is also not representable by any authored schema. JSON has
strings, not raw byte values; “hashed as received” could mean raw model response
spelling, decoded Unicode scalar content, JCS-escaped string bytes, or a base64
payload. Those choices yield different identities and byte/token limits.

Even the reduced node cap is not proved by the accepted-output cap: a 512-JCS-
byte node plus the resolver envelope can exceed a 512-token accepted response
under adverse byte fallback. The current root schema supplies no maximum legal
fixture from which T06/T07/T16 could be generated.

**Exact fix.** Name separately and consistently: `node_value`, full
`node_envelope`, `candidate_manifest`, `materialized_payload`, and
`materialized_candidate_envelope`. Every container maximum must be at least the
sum/overhead of its permitted contents, or the contents must be external
references explicitly excluded from that byte count. Specify NOTE encoding
(for example, a Unicode JSON string whose identity is its JCS string/member
bytes, or explicit base64 of bytes) and use it everywhere. Generate boundary
fixtures mechanically from the real schemas and pinned tokenizer. If any legal
operation response does not fit, lower byte limits or raise/recompute token
limits before intake; a future test that may return `NOT_RUN` does not make
contradictory maxima an exact design.

### `V2_PRE_B10`: The Stage-1 gate is still not an executable Boolean function

`analysis_contract.md` defines several row aggregates, but Experiment Section
4 describes the gate in prose: “an exact Dream-1 A candidate,” “both h Dream-2
B commitments,” “complementary registered actions,” “authentic memory above
EMPTY and crossed,” and “no comparable sham redirection.” It does not enumerate
which h/z/goal rows each conjunct consumes, whether every SELF action must be
exact, the strict numerical threshold for “above,” or the Boolean definition
of “comparable” sham redirection. The acceptance test says the conjunction is
fixed without supplying the formula.

There is also no exact endpoint for “branch-appropriate revision.” Correct B
predictions can change while both h branches select identical corpus bytes;
different corpus hashes can occur without either difference affecting action.
The proposal correctly rejects h-mediated-action language, but its permitted
descriptor still says fresh Dream-2 made “registered branch-appropriate
revisions” without specifying what registered observable makes that true.

**Exact fix.** Add a machine-readable gate expression over literal row IDs and
named receipt fields. Define A/B correctness cardinality for every z/h pair,
the action and goal-twin conjunction, exact authentic-minus-EMPTY/crossed
inequalities, sham criterion, failure behavior, and tie handling. Add a
separate revision endpoint: e.g. exact B change plus an explicit terminal
RETAIN/REPLACE/candidate-set decision under both branches. If corpus content
difference is required, say so mechanically; do not call it semantically
appropriate. Exhaust the Boolean truth table and make the report descriptor a
pure function of it.

### `V2_PRE_B11`: Content-address visibility is contradictory at Sleep and underspecified by consumer

T05 expects that no “content-identity descendant reaches cognition or Sleep.”
The semantic contract says opaque Sleep checks the digest, and the private
field registry permits `opaque_note_bytes` digest and length-bucket exposure
without specifying which consumer receives it. The resource manifest says
COMMIT carries “capability/address/length references,” while the reducer,
prompts, and semantic contract say the model sees capability only and never
address/digest/storage identity. These statements cannot all hold.

The visibility matrix does not list content address, capability, store path,
length bucket, dedup status, or candidate handle as information items, so it
cannot establish the promised nonvisibility. A capability's fixed shape alone
does not make its value invariant across authentic/crossed/sham interventions;
exposing different opaque tokens at target time is itself an identity channel.

**Exact fix.** Separate a noncognitive harness integrity checker from the
Sleep transformation and state exactly which one receives the digest. Remove
“address/length” from every model COMMIT description if capability-only is the
choice. Add each identity/capability field to the visibility matrix with
per-consumer permissions. At target time, render fixed handle values as well
as fixed shapes/count/order across intervention clones, and keep all content
addresses and corpus variant IDs outside reader/Think/actor input. Test exact
rendered bytes before authorized read returns.

### `V2_PRE_B12`: Stage 0's 24-hour CPU maximum is not jointly allocated

The root certificates alone may consume `128 x 10.5 = 22.4` CPU-hours. Stage 0
also includes 28 exact solver evaluations, 60 actor applications, full q-policy
alarm enumeration, schemas/JCS/Unicode tests, tokenizer/chat-template maximum
fixtures, reader/extractor tests, assignment generation, resets, taint, and
resource checks. None has a CPU allowance. The remaining implicit 1.6 hours is
not proven sufficient. Thus the v1 competing-limit defect survives in a new
form: root work fits, but the complete mandatory Stage 0 maximum does not have
a joint bound under 24 hours.

**Exact fix.** Add a literal CPU ledger for every non-root Stage-0 suite and
sum its worst case with the 1,344 root minutes. Either reduce the per-root cap
so all mandatory work fits or raise the aggregate cap before intake. Define
whether tokenizer/model-file reads count as CPU/wall and make root, auxiliary,
aggregate, and wall stops jointly testable. T01/T16 must not claim the whole
suite fits based only on root multiplication.

### `V2_PRE_B13`: No target-independent sham constructor is frozen

The semantic contract lists mechanical properties that a “presealed arbitrary
byte corpus” should match, but supplies neither exact bytes nor a deterministic
constructor/seed/input domain. It therefore cannot prove target independence,
pre-result sealing, tokenizer-bucket matching, or provenance/index-shape
matching. An implementer retains discretion to choose a weak/easy sham while
remaining consistent with the prose.

**Exact fix.** Bind either each exact sham corpus for the three roots/sides or
a total deterministic constructor with its seed derivation, source corpus
access, token alphabet, rejection rule, maximum attempts, and failure status.
It must run before targets/query traces are visible and emit a receipt for
every claimed match/nonmatch. If exact matching cannot be achieved within its
predeclared search bound, the affected row is a retained failure; no alternate
sham is selected. Keep the admitted nonmatches in every report.

### `V2_PRE_B14`: The “sealed assignment ledger” is an aggregate formula, not a complete manifest

`assignment_ledger.md` verifies the 484/2,926/4 sums and names the four
one-shot lives, but it does not enumerate 3,414 call IDs, all target IDs,
sampled z values, candidate/condition rows, coupling groups, sampler settings,
or `replay_eligible` flags. `rng_contract.json` requires a future golden
manifest, while the replay rule dynamically selects the first and second
eligible infrastructure failures. No schema or deterministic construction
algorithm for that manifest is bound.

Concrete z/seed values may legitimately be sealed during authorized Stage 0,
but the selection algorithm, source randomness commitment, row-expansion
schema, target selection, and exact eligibility rules must already be frozen
before intake can authorize building them. Otherwise T0 retains architectural
discretion.

**Exact fix.** Add an assignment-manifest schema and total generator contract
mapping the three named roots, selected h/q, z draw/antipode, targets, twins,
conditions, operations, coupling keys, and sampler configuration to every
possible call ID and terminal row. Define `replay_eligible` in that schema and
the exact failure classes that may consume each replay slot. Hash the generated
manifest before the first model call and prove its group sums. Do not call the
current formula table an exhaustive row ledger.

## Material defects

### `V2_PRE_M01`: Model/runtime identity is incomplete before the executable-freeze gate

The model revision and bf16/vLLM mode are named, but vLLM version, engine
flags, tensor parallelism, quantization absence, chat template bytes, tokenizer
revision/files, JCS implementation, Unicode-data version, stop strings, and
sampler settings are not. T14/T17 promise to hash a later executable bundle,
which is appropriate evidence, but the architectural allowed-value contract
must be frozen first; otherwise the implementation team chooses scientific
treatment details after ratification.

**Exact fix.** Add exact allowed values or a deterministic source-resolution
rule for every treatment-affecting runtime field. Make any deviation a new
architecture hash, not merely a failed pre-GPU fixture.

### `V2_PRE_M02`: Process success and scientific correctness share one ambiguous status vocabulary

The long-form table uses `RUN_SUCCESS` and `RUN_FAILURE`, while wrong but legal
actions, correct parsing with incorrect predictions, infrastructure errors,
and exact scientific success are not cleanly separated. If `RUN_SUCCESS` means
task success, valid wrong executions disappear into “failure”; if it means a
valid run, its endpoint need not be one. The resource manifest similarly risks
calling the 3,414 assignment ceiling “calls” without separate valid/invalid
response counts, although the prose partially acknowledges charged failures.

**Exact fix.** Use orthogonal fields: assignment status, invocation/process
status, parse/reducer status, scientific endpoint value, and terminal reason.
Every legal wrong action is a completed process row with endpoint zero, not an
infrastructure failure. Bind report denominators to assigned rows, never
`RUN_SUCCESS` count.

### `V2_PRE_M03`: “Any independent gain” conflicts with the registered specificity alarm

The analysis contract flags only either q with at least three of four SELF
successes, or both q values having both positive control contrasts. Experiment
Section 5 then says “Any independent gain is an alarm.” A single independent
success or a positive contrast for only one q is an independent gain but does
not satisfy the stated alarm. This changes terminal interpretation.

**Exact fix.** Choose one literal rule and use it everywhere. Prefer separate
fields for `ANY_INDEPENDENT_SUCCESS`, the calibrated compound
`SPECIFICITY_CONCERN`, and their exact report consequences. The Stage-0 joint
policy enumeration must define the finite legal plan set and sampler coupling;
“each declared stochastic coupling” is not itself an enumerable policy class.

### `V2_PRE_M04`: The structured one-shot plan is not executable from its schema

The prose correctly restricts four calls to one selected factor life and one
selected independent life with two goal twins, but `one_shot_plan` accepts zero
actions and arbitrary JSON elements and cannot encode the promised final LOCK.
The prompt says “at most four legal USE actions followed by LOCK,” while the
assignment ledger says it “must emit four legal USE actions then LOCK.”

**Exact fix.** Require exactly four typed legal action strings for D4 plus an
explicit terminal `LOCK`, or define the exact shorter-plan failure schema.
Bind the target IDs, action feedback policy, and open-loop executor. Keep the
result limited to those four AST rows.

### `V2_PRE_M05`: Maximum-input fixtures are conditional rather than an executable bound

The resource manifest permits complete rendered inputs of 49,152--81,920
bytes under 16,384/32,768 token caps and relies on a future pinned-tokenizer
fixture. That is acceptable only if the legal free-text/schema space is finite
and mechanically generatable. The current schemas do not impose the prose byte
caps, and no specific tokenizer/chat-template/JCS implementation is bound, so
there is no well-defined “maximum legal fixture.” The 48,640-token
input-plus-output requirement for structured one-shot Think also needs an
exact runtime context limit, not only a future check.

**Exact fix.** After B01/B09, derive maximum fixtures from schema/runtime byte
bounds, bind tokenizer/chat template and configured model context, and record
input plus output jointly. If the maximum cannot be proven under every legal
string/operation, lower the legal space or raise/recompute caps before intake.

### `V2_PRE_M06`: Report language still overstates the undefined revision endpoint

The bundle carefully disclaims mediation, raw-perception induction,
recurrence, semantics, replication, and paper efficacy. Its allowed descriptor
nonetheless says Dream-2 made “registered branch-appropriate revisions.” Until
B10 defines an observable revision event, this can mean merely a correct B
prediction, a different opaque hash, or a RETAIN/REPLACE enum. Strict opacity
prevents a semantic judgement that a note was appropriately revised.

**Exact fix.** Replace “branch-appropriate revision” with the exact mechanical
facts that pass: the registered Dream-2 terminal decision/candidate identity
and B commitments changed under the raw-A fork. Reserve “self-revised” for a
predeclared nonsemantic decision predicate and never imply useful content or
action mediation.

### `V2_PRE_M07`: Opaque retention and later human visibility need a policy boundary

The resource manifest retains all prompt/output bytes append-only, while the
analysis contract forbids opaque semantic inspection. Artifact retention is
necessary, but a report author can still inspect successful notes and select
examples or mechanistic language outside the automated scorer.

**Exact fix.** Define role-based access/report generation: causal gates and
the primary report consume only allowed hashes/provenance/behavior; raw opaque
bytes remain sealed audit artifacts until the primary report is frozen. Any
later human/model qualitative reading is labeled exploratory, cannot change a
gate, and cannot establish factor semantics, no-solution content, or mechanism.

## Coverage against the twenty premortem obligations

| Premortem obligation | Exact-byte finding |
|---|---|
| `PM_T01_STAGE_CONDITIONALITY` | **Partial.** Separate summaries and conditional wording are present, but the all-pass predicate is not a literal Boolean function (`B10`). |
| `PM_T02_EXECUTABLE_FREEZE` | **Specified, not self-sealing.** Freeze/failure language is good; allowed runtime/sampler values remain incomplete (`M01`). |
| `PM_T03_UNTOUCHED_ACCESS` | **Partial.** Cache/access canaries are promised, but merged actor visibility and missing capability fields defeat an exact process boundary (`B07`, `B11`). |
| `PM_T04_SELECTED_H_SUPPORT` | **Pass at design level.** h=0 and the absent 372 calls are explicit. Gate row use still needs B10's formula. |
| `PM_T05_NO_H_MEDIATION_CLAIM` | **Mostly pass.** Mediation is explicitly untested; “branch-appropriate revision” remains undefined (`B10`, `M06`). |
| `PM_T06_EXTRACTOR_PURITY` | **Pass at prose level.** The event-local algorithm and exclusions are strong. The executable source remains a later freeze item. |
| `PM_T07_EXTRACTOR_READ_GATE` | **Fail.** Recurrent intent is clear, but one-shot/batch and target-Think exposure contradict the universal charged-READ statement (`B08`). |
| `PM_T08_RENDERED_NULL_THEOREM` | **Specified.** It is a mandatory Stage-0 receipt; its exact row/manifest generator remains missing (`B14`). |
| `PM_T09_COMMIT_INTEGRITY` | **Fail.** Root schema, capability lifetime, multi-candidate commit, one-shot chronology, and PREDICT semantics are unresolved (`B01`, `B04`--`B06`). |
| `PM_T10_HASH_INVISIBILITY` | **Fail.** Digest/capability/address/length permissions conflict and the actor can consume notes (`B07`, `B11`). |
| `PM_T11_MAX_STAGEABLE_OBJECT` | **Fail.** Payload/container and NOTE encoding are contradictory; no operative schema defines the fixture (`B01`, `B06`, `B09`, `M05`). |
| `PM_T12_OPAQUE_RENDER_SAFETY` | **Partial.** Strong prose exists, but no NOTE/read/root schema can enforce the channel (`B01`, `B02`, `B09`). |
| `PM_T13_SHAM_CONTRACT` | **Fail.** Match/nonmatch claims exist, but no exact bytes or target-independent constructor is bound (`B13`). |
| `PM_T14_STRUCTURED_ONESHOT_ROWS` | **Partial.** Four root-life/twin rows are named; one-shot action and Dream capability schemas are not executable (`B04`, `M04`). |
| `PM_T15_EXACT_3414_LEDGER` | **Partial.** Aggregate arithmetic is correct and panels are excluded; the purported exhaustive row/call manifest and replay eligibility contract do not exist (`B14`). |
| `PM_T16_LITERAL_TOKEN_ENVELOPE` | **Fail.** Arithmetic upper sums are correct, but legal-object definitions, node/PREDICT fit, tokenizer identity, and non-root CPU work are not jointly bounded (`B09`, `B12`, `M05`). |
| `PM_T17_SPECIFICITY_CALIBRATION` | **Partial.** Calibration is required, but policy enumeration and “any gain” semantics conflict (`M03`). |
| `PM_T18_REDIRECTION_TRUTH_TABLE` | **Partial.** Redirection semantics are improved; the exact Stage-1 gate formula remains absent (`B10`). |
| `PM_T19_CAUSAL_DIFF_ALLOWLIST` | **Fail.** The intent is present, but CRN derivation differs across paired rows and identity/actor channels remain (`B03`, `B07`, `B11`). |
| `PM_T20_REPORT_BOUNDARY` | **Partial.** Most forbidden claims are explicit; the revision predicate and post-hoc opaque-access boundary remain (`M06`, `M07`). |

## Residual v1-critique status

The v1 disposition ledger says no concern is deferred, but the exact bytes do
not yet support that statement:

- `CRIT_PCFL_003` remains blocking because the catalog schema is nonoperative
  and its payload is open (`B01`, `B02`).
- `CRIT_PCFL_004` remains blocking because the Stage-1 gate is prose, not an
  executable estimand (`B10`).
- `CRIT_PCFL_006` remains material because mandatory non-root CPU work is not
  included in the joint 24-hour maximum (`B12`).
- `CRIT_PCFL_008` remains blocking because treatment-varying fields enter the
  supposedly common seed key and sampler settings are absent (`B03`).
- `CRIT_PCFL_014` remains blocking in a new form: terminal byte repetition is
  gone, but capabilities cannot support one-shot, cross-session, two-candidate,
  and abstain semantics (`B04`, `B05`).
- `CRIT_PCFL_015` is reconciled in prose, but the nonoperative DSL cannot reject
  candidate REVISE or wrong-phase REPLACE (`B01`).
- `CRIT_PCFL_017` remains material/blocking at the model boundary because
  NOTE bytes and JCS/container byte identities are not schema-defined (`B09`).
- `CRIT_PCFL_018` remains blocking because stageable object/input and total CPU
  maxima are not yet jointly executable (`B09`, `B12`, `M05`).

The other v1 repairs are substantially preserved: selected-h qualification,
opaque semantic restraint, q-specific controls, exact-program zero-model-call
accounting, structured-only one-shot scope, excluded baseline claims, and the
DEV/paper boundary are materially stronger than v1.

## Required rework order

The least wasteful repair sequence is:

1. replace both root schemas and split all actor/reader/candidate receipt types;
2. choose one staged-node/PREDICT protocol and repair recurrent plus one-shot
   capability lifetimes and phase-specific COMMIT forms;
3. correct the seed key and bind all decoding/runtime parameters;
4. split reader/Think/actor visibility and make every address/capability field
   explicit;
5. make byte containers, NOTE encoding, and maximum fixtures coherent;
6. freeze the exact Stage-1 Boolean gate, revision endpoint, sham constructor,
   assignment generator, and specificity terminology;
7. add the missing non-root CPU budget and recompute joint resource maxima;
8. update disposition ledgers, tests, prompts, claims, hashes, and the proposal
   SHA; then repeat fresh deliberation on the new bytes.

None of these should be delegated to implementation discretion. They change
which messages are legal, which model sees which information, which rows share
randomness, what counts as a causal pass, and whether the declared maxima can
run. Initializing intake on the current bytes would merely bind known
contradictions into the authoritative chain.

## Final disposition

Do not initialize v2 intake at SHA
`2fc2521d821efc2ff4852ef9decbb4c2bdf834a8f1b0ff438aec7e78d2a0f047`.
The exact context graph is intact, but the current proposal is not a complete
executable scientific architecture. Re-author, rehash, and only then begin a
fresh intake/deliberation chain. No implementation, CPU construct execution,
model call, GPU run, or claim is warranted by this audit.
