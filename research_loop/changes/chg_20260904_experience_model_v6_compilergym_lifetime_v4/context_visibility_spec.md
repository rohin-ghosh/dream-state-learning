# Experience Model v6 CompilerGym lifetime v4: context, state, and visibility contract

Status: normative design specification only. This file authorizes no
installation, import, execution, model call, training, target opening, or
claim. A later ratified run manifest MUST bind the bytes of this contract,
the pinned model/tokenizer, and the local CompilerGym/POJ104 fit receipts
before any executable stage.

This contract resolves the v3 context, prose, lifecycle, fork-memory, and
reader/writer findings. It describes one recurrent model. `ORIENT` and
`THINK_ACT` are invocation phases of that model; `SLEEP` is a deterministic,
model-free compiler and is not a learned router, sleeper, or second model.

## 1. Normative terms and identities

The words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, and MAY have
their usual RFC-2119 meanings. A *principal* is a process boundary with an
allowlisted input and output capability. A *field* is visible only when its
principal appears in the field's reader list; an artifact being derivable
from a receipt does not make its source bytes visible to a model.

There are exactly two on-policy identities:

* `HARNESS` uses the pinned base model, bootstrap, packet assembler, parser,
  deterministic retriever, public ledger/notebook, tools, budgets, order, and
  reset schedule. It mounts the null adapter at every wake.
* `EXPERIENTIAL` is byte-matched to `HARNESS` and mounts one cumulative,
  life-local authentic LoRA below prompt assembly. Its own ledger/notebook is
  common nonparametric source evidence, not learned parameter state.

No arm, condition, checkpoint, adapter origin, training receipt, row count,
latency, cache state, or fork identity may be encoded in a model-visible
field. `HARNESS` MUST NOT receive sham or useful adapter bytes. `ORIENT` and
`THINK_ACT` MUST use the same pinned model, tokenizer, bootstrap, sampling
family, and below-prompt adapter assignment within a system.

## 2. Canonical state and serialization

### 2.1 Authoritative state

The controller owns exactly this state (key order is normative):

```json
{"schema":"v4.state","life_nonce":"opaque","task_nonce":"opaque",
 "task_index":0,"tasks_completed":0,"sleep_index":0,"decision_index":0,
 "pair_index":0,"orient_calls":0,"think_act_calls":0,
 "model_output_tokens":0,"environment_action_attempts":0,
 "retrieval_queries":0,"notebook_writes":0,"public_best_score":0.0,
 "focus":{"mode":"KEEP","public_question":null,
          "public_strategy":null,"uncertainty":"HIGH","focus_seq":0},
 "environment":{"observation":[0],"instruction_features":[0],
                 "current_cost":null,"best_cost":null,"legal_passes":[],
                 "terminal":false,"last_action_status":"RESET",
                 "public_summary":null},
 "workspace":{"manifest_id":"opaque","file_ids":[]},
 "ledger_seq":0,"notebook_seq":0}
```

The illustrative zero values above are type examples; a run manifest binds
the actual immutable `ANCHOR`, vector lengths (56 and 70), and opaque nonce
construction. `life_nonce`, `task_nonce`, `manifest_id`, and `file_ids` are
opaque stable identifiers, never arm or target labels. The controller MUST
reject unknown state keys, duplicate keys, non-finite numbers, or vector
lengths other than `Autophase[56]` and `InstCount[70]`.

The state block is a shape declaration rather than a runnable fixture: the
`[0]` vectors in the abbreviated example stand for exactly 56 and 70 integer
slots. A canonical state instance MUST contain all slots and no ellipsis or
placeholder.

State is serialized as UTF-8 NFC JSON with no insignificant whitespace,
decimal integers, lowercase JSON literals, and the declared key order shown
here (not lexicographic key sorting). This v4 contract owns that choice;
`experiment_spec.md` delegates canonical ordering to this contract, so the
declared schema key order is the single normative rule.
Arrays retain their declared order. Strings escape control characters and
MUST NOT contain a raw delimiter. Hashes are lowercase SHA-256 hex. This
serialization rule applies to packet fields, events, notebook records, and
row inputs; a generic unordered JSON serializer is not conforming.

### 2.2 Canonical model packet

Every model call reconstructs a new packet from authoritative state. A
provider conversation, hidden chat prefix, KV cache, scheduler state, shell
history, or prior raw output MUST NOT be reused. The packet's top-level field
order is fixed and MUST be exactly:

```text
PACKET_HEADER, ANCHOR, CLOCK_BUDGET, LIFE, FOCUS, ENVIRONMENT,
RECALLED_EXPERIENCE, RECENT_TAIL, PACKET_END
```

Each section is one canonical JSON object rendered between literal section
delimiters. `PACKET_HEADER` contains only `{"schema":"v4.packet","phase":
"ORIENT"|"THINK_ACT"}`. The model input is the concatenation in that order;
there are no omitted empty sections. Within each section the key orders are:

```text
ANCHOR:
 schema, anchor_hash, objective, rules, operation_grammar, public_field_rules
CLOCK_BUDGET:
 schema, decision_index, pair_index, tasks_completed, sleep_index,
 remaining_decisions, remaining_model_output_tokens, remaining_env_actions,
 remaining_recall_queries, remaining_notebook_writes
LIFE:
 schema, life_nonce, task_nonce, task_index, public_best_score
FOCUS:
 schema, mode, public_question, public_strategy, uncertainty, focus_seq
ENVIRONMENT:
 schema, observation, instruction_features, current_cost, best_cost,
 legal_passes, terminal, last_action_status, public_summary, workspace
RECALLED_EXPERIENCE:
 schema, records
RECENT_TAIL:
 schema, events
```

`ANCHOR` is immutable within a run and contains no target roles, target
outcomes, arm names, adapter status, or infrastructure telemetry. `legal_passes`
is a canonical ordered array of public pass identifiers. A pass identifier is
an integer index and its canonical public name; filesystem paths and raw IR
are absent. `workspace` contains only the current task's public manifest ID
and sorted opaque file IDs; it contains no source path, shell history, or
cross-task file bytes.

### 2.3 Exact token caps and collision order

Counts use the pinned tokenizer, counting delimiters, JSON punctuation, field
names, and values. These are hard caps:

| Item | Cap |
|---|---:|
| complete model packet | 4,096 input tokens |
| `ANCHOR` section | 640 tokens |
| `CLOCK_BUDGET` section | 256 tokens |
| `LIFE` section | 192 tokens |
| `FOCUS` section | 384 tokens |
| `ENVIRONMENT` section | 1,280 tokens |
| `RECALLED_EXPERIENCE` section | 512 tokens |
| `RECENT_TAIL` section | 512 tokens |
| packet framing and delimiters | 32 tokens |
| one model output (either phase) | 256 generated tokens |
| complete task output across six pairs | 3,072 generated tokens |
| one event in the ledger | 256 tokens |
| recent-tail event suffix | 512 tokens, complete events only |
| one retrieved record | 192 tokens |
| rendered training row | 768 tokens |
| compiled corpus | 192 rows, at most 64 per view |
| notebook text | 64 tokens per record |
| notebook records | 16 records per life |
| life snapshot ledger | 64 complete events (the pilot's checkpoint prefixes are <=48) |
| recall queries per `ORIENT` | 2 |
| wake pairs per task | 6 `ORIENT`/`THINK_ACT` pairs |
| public environment actions per task | 6 attempts |

The section caps are maxima, not permission to increase the 4,096-token
packet. The assembler applies this exact loss order when optional text or
evidence would collide with a cap:

1. Normalize prose to NFC and truncate each optional prose field to its
   declared field cap using a token-prefix plus the literal `TRUNCATED`
   marker. Required enum, integer, vector, ID, and status fields are never
   truncated.
2. Phase-output prose is bounded before parsing: if an optional output prose
   value exceeds its field cap, the parser returns a syntax/semantic failure;
   it does not silently shorten the value. For an already parsed packet
   `FOCUS`, truncate `public_strategy` and then
   `public_question`, retaining `mode` and `uncertainty`.
3. In each recalled record, truncate public prose, then drop the record's
   optional note body; retain IDs, operation, status, and score. Drop the
   second recalled record before the first.
4. In `RECENT_TAIL`, remove the oldest complete event until the section fits;
   an event is never cut in half. The tail therefore contains a suffix of
   complete events, possibly empty.
5. If the packet still exceeds 4,096 tokens, fail closed with
   `PACKET_OVERFLOW`; do not drop `ANCHOR`, counters, public observations,
   legal actions, finite focus fields, or current workspace identifiers, and
   do not retry with a larger cap.

An overlong required field, vector, legal-pass list, event, or anchor is a
manifest/fit failure, not a truncation opportunity. `PACKET_OVERFLOW` emits
no model call, consumes the current pair as a failed decision, appends a
minimal failure event if it fits, and terminates the task; it never silently
changes the experiment.

The provider output limit is a hard stop at 256 generated tokens. A stop that
cuts a JSON value, closing brace, or required key makes that phase malformed;
the parser does not request continuation. An output at or below the limit is
still rejected if it is not the exact canonical JSON grammar below. The
controller records the token count and parse disposition, never the discarded
raw string.

## 3. ORIENT and THINK_ACT grammar

### 3.1 ORIENT JSON schema

The raw output MUST be exactly one JSON object with this key order and no
fence, commentary, duplicate key, or unknown key:

```json
{"schema":"v4.orient","focus_mode":"KEEP","recall":[],
 "public_question":null,"public_strategy":null,"uncertainty":"HIGH"}
```

The normative finite enums are:

```text
focus_mode = KEEP | EXPLORE | IMPROVE | RECOVER | VERIFY | STOP
uncertainty = LOW | MEDIUM | HIGH
recall.source = LEDGER | NOTEBOOK
recall.kind = BEST | FAILURE | SUCCESS | NOTE
```

`recall` has zero, one, or two entries. Each entry has key order
`source, kind, ordinal`; `ordinal` is a nonnegative integer less than the
current source count and refers only to the calling system's own life
snapshot. `public_question` and `public_strategy` are nullable strings of at
most 48 tokens each. The optional public strings are parsed public prose and
may condition the immediately following `THINK_ACT` call and event as
zero-mask provenance.

There are deliberately no `private_rationale` or `private_hypothesis` fields
in this schema. If a model emits either term, or any other private prose,
outside the declared object, the bytes are unparsed output: they are rejected,
discarded, and mask-zero, with no ledger/notebook/compiler path.

Semantic validation is strict: `STOP` requires an empty recall and null
public strings; every recall ordinal must resolve; and all strings must be
valid UTF-8 NFC without delimiters. A semantic failure is `ORIENT_INVALID`.
On either syntax or semantic failure, the controller charges one ORIENT
call/output-token count, discards all returned text, uses the deterministic
fallback `focus_mode=KEEP`, zero recalls, null public strings,
`uncertainty=HIGH`, and still performs the mandatory `THINK_ACT` call. There
is no hidden retry and ORIENT can never execute an operation.

### 3.2 THINK_ACT JSON schema

The raw output MUST be exactly one JSON object with this key order:

```json
{"schema":"v4.think_act","operation":{"type":"INSPECT","args":{"scope":"CURRENT"}},
 "public_note":null,"expected_effect":null,"uncertainty":"HIGH"}
```

Finite operation grammar and canonical argument key order are:

```text
operation.type = INSPECT | APPLY_PASS | NOTE_APPEND | FOCUS_REVISE | STOP

INSPECT      args = {"scope":"CURRENT"|"BEST"|"LEGAL_ACTIONS"|"SUMMARY"}
APPLY_PASS   args = {"pass_index": integer in [0, len(legal_passes))}
NOTE_APPEND  args = {"kind":"OBSERVATION"|"PLAN"|"RECOVERY"|"GENERAL",
                      "text": string of at most 64 tokens}
FOCUS_REVISE args = {"focus_mode":"KEEP"|"EXPLORE"|"IMPROVE"|"RECOVER"|"VERIFY",
                      "public_question": nullable string <=48 tokens,
                      "public_strategy": nullable string <=48 tokens}
STOP         args = {"reason_code":"DONE"|"NO_PROGRESS"|"INVALID_STATE"|"BUDGET"}
```

`public_note` and `expected_effect` are nullable parsed strings with caps 64
and 48 tokens respectively. Public note text, expected effect, and public
focus prose are declared public provenance and may be retained in the next
state/event as zero-mask conditioning. There are deliberately no
`private_rationale` or `private_hypothesis` fields in this schema: if either
is emitted outside the declared object it is unparsed output, rejected,
discarded, and mask-zero; it is never a notebook entry or compiler input.
`uncertainty` uses `LOW|MEDIUM|HIGH` and is provenance only.

The parser rejects wrong key order, duplicate/unknown keys, missing keys,
wrong types, non-finite numbers, unknown enum values, illegal pass indices,
noncanonical strings, and operation/argument mismatches. A malformed or
semantically invalid output consumes exactly one THINK_ACT call and one
decision budget unit, discards the output, performs no public operation, and
appends a `MALFORMED` event. There is no retry. A valid `APPLY_PASS` always
consumes one environment-action attempt even when the service later reports
invalid, timeout, or environment error. `INSPECT`, `NOTE_APPEND`, and
`FOCUS_REVISE` do not consume environment-action budget. `STOP` ends the task
after its event. At most one operation can be dispatched per pair.

### 3.3 Loss mask and row projection

Loss is computed only on assistant output tokens in a rendered training row.
The mask is one exactly on these finite parsed fields: `focus_mode`, each
`recall.source`, each `recall.kind`, `operation.type`, and the finite
operation arguments (`scope`, `pass_index`, `kind`, `focus_mode`, and
`reason_code`). It is zero on every input token and on JSON punctuation,
field names, delimiters, IDs, observations, legal-pass names, scores,
retrieved records, event text, `public_question`, `public_strategy`,
`public_note`, `uncertainty`, `expected_effect`, any private rationale or
hypothesis bytes, all other prose, and all unparsed output.

Parsed public prose MAY remain as zero-mask row input/provenance. This is
intentional conditioning, not a hidden target. Private prose is not even a
row input. Unparsed output is discarded, not hashed into a row, notebook, or
retrieval record. No rationale, hypothesis, self-report, or human-theory
similarity may be an endpoint, correctness label, selection criterion, or
positive training target. The v4 writer contains no anchor, preservation, KL,
or other auxiliary rows.

## 4. Public events, notebook, and retrieval

### 4.1 Complete event schema

The ledger is append-only and each decision, including malformed/failing
decisions, appends one complete event with this key order:

```json
{"schema":"v4.event","life_seq":0,"task_index":0,"decision_index":0,
 "pair_index":0,"pre_state_hash":"sha256","focus":{"mode":"KEEP",
 "public_question":null,"public_strategy":null,"uncertainty":"HIGH"},
 "recall_ids":[],"operation":{"type":"INSPECT","args":{"scope":"CURRENT"}},
 "public_outcome":{"status":"INSPECTED","observation":[0],
 "instruction_features":[0],"current_cost":null,"best_cost":null,
 "reward":0.0,"terminal":false},"resource":{"orient_tokens":0,
 "think_act_tokens":0,"environment_action_attempted":false},
 "post_state_hash":"sha256","public_provenance":null}
```

The actual observation and instruction vectors MUST be exactly lengths 56 and
70. `status` is one of `RESET`, `INSPECTED`, `PASS_APPLIED`, `NOTE_WRITTEN`,
`FOCUS_CHANGED`, `STOPPED`, `MALFORMED`, `INVALID`, `TIMEOUT`,
`ENV_ERROR`, `PACKET_OVERFLOW`, or `NOTEBOOK_FULL`. A failed service action
retains the previous valid best state and score, is counted separately, and
never receives positive action credit. `public_provenance` may contain only
the object `{"public_question":string|null,"public_strategy":string|null,
"public_note":string|null}` in that key order, with the prose caps above,
and is always mask-zero. Private fields and raw/unparsed output are absent.
For a `MALFORMED` or `PACKET_OVERFLOW` event, `operation` is `null` and
`public_outcome` contains no fabricated service result; otherwise operation
is the validated typed object. The `[0]` vectors in this shape example stand
for exactly 56 and 70 integer slots. An event over 256 tokens is an atomic
lifecycle failure; it is not truncated.

The ledger record is the source for future within-life retrieval and sleep
compilation. It is not a model parameter and is not evidence specific to the
LoRA unless a later analysis explicitly says so.

### 4.2 Notebook schema

`NOTE_APPEND` is the only notebook writer. A successful append has this key
order and consumes one life slot:

```json
{"schema":"v4.notebook_record","notebook_seq":0,"origin_event_seq":0,
 "kind":"OBSERVATION","text":"public text","public_only":true}
```

`kind` is `OBSERVATION|PLAN|RECOVERY|GENERAL`; text is normalized public
prose of at most 64 tokens. There are at most 16 records, no overwrite and
no deletion. At capacity, `NOTE_APPEND` produces `NOTEBOOK_FULL`, no record,
and no retry. Notebook records are bounded source evidence; they cannot
carry private thought, hidden target data, condition labels, paths, or
unbounded scratch state.

The deterministic retriever accepts only the parsed finite query tuple
`(source, kind, ordinal)` and returns records from the caller's own snapshot
in ledger sequence order. It materializes at most two records, each at most
192 tokens. Its canonical record key order is
`schema, source, ordinal, event_seq, kind, operation_type, operation_args,
status, current_cost, best_cost, reward, terminal, public_provenance`; the
record contains no private prose, raw IR, path, target role, or condition
label. A missing record is a parser-invalid query, not a search over other
sources. Retrieval is identical in schema, cap, ordering, and budget for both
systems and all forks.

### 4.3 State projection versus sleep projection

The next packet carries only current finite focus and parsed public prose.
Private prose is same-call-only. The sleep compiler reads a sealed
`public_source_projection` consisting of event finite fields, public
observations/outcomes, public notebook records, public prose provenance,
resource counters, and hashes. It MUST NOT read private prose, unparsed
output, target/evaluator data, or evaluation artifacts. Public prose may
condition a rendered row but has mask zero and can never be selected as a
target. This explicit projection resolves the apparent contradiction between
parsed public provenance and the private-thought boundary.

## 5. Principals and directional access

The following is an allowlist, not a descriptive visibility label. Every
read/write not listed is forbidden. The `MODEL` reads only the packet and
causally receives the assigned adapter weights below prompt assembly; it
cannot inspect adapter bytes or any receipt.

| Principal | Reads | Writes |
|---|---|---|
| `STATIC_CONSTRUCTOR` | already-local public catalog, source/IR hashes, public structural metadata | candidate/group manifest only |
| `TARGET_SEALER` | sealed candidate manifest, public predeclared roles, authorized runtime headroom receipts | immutable target/spare role seal |
| `LIFE_CONTROLLER` | current state, own sealed ledger/notebook, public service result | counters, task/life state, checkpoint snapshot seal |
| `PACKET_ASSEMBLER` | anchor, controller projection, current public environment/workspace, own retrieval result, recent events | one canonical packet; no external artifact |
| `MODEL` | canonical packet; assigned weights below prompt assembly | raw phase output to its parser only |
| `ORIENT_PARSER` | one ORIENT output | finite plan or `ORIENT_INVALID` receipt |
| `RETRIEVER` | caller's own sealed ledger/notebook and finite query | at-most-two rendered records |
| `THINK_ACT_PARSER` | one THINK_ACT output | one typed operation or `MALFORMED` receipt |
| `OPERATION_DISPATCHER` | typed operation, current public legal projection | one dispatch request |
| `LLVM_SERVICE` | current task public bitcode handle and legal pass request | public observations, status, cost, terminal result |
| `NOTEBOOK_WRITER` | validated `NOTE_APPEND`, controller sequence | one notebook record or `NOTEBOOK_FULL` |
| `LEDGER_WRITER` | pre/post public state, parsed finite fields, retriever IDs, service result | one complete event |
| `SLEEP_COMPILER` | sealed EXPERIENTIAL public projection, frozen compiler/mask/recipe bytes, clean base hash | candidate rows, selection/rejection manifest, trainer request |
| `TRAINER` | selected rows and clean pinned base | one candidate authentic LoRA and receipt; trainer state is ephemeral |
| `ADAPTER_PUBLISHER` | candidate authentic LoRA and successful trainer receipt | one atomically published EXPERIENTIAL adapter |
| `ADAPTER_LOADER` | pinned base and assigned serialized adapter | in-memory assigned weights only |
| `FORK_LAUNCHER` | sealed target public packet, assigned adapter, system snapshot | fresh fork mount and quarantine handle |
| `EVAL_QUARANTINE` | fork public outcomes, resource receipts, teardown evidence | quarantined evaluation artifact only |
| `OFFLINE_AUDITOR` | sealed manifests, ledgers, snapshots, adapters, receipts, quarantined outcomes | audit report; never a model packet |

`SLEEP_COMPILER` has no reader capability for target roles/outcomes,
evaluator/reference data, raw private output, live workspace, process/cache/
RNG state, or any HARNESS adapter. It writes only EXPERIENTIAL's candidate
adapter; HARNESS receives a scheduling receipt and remains null. `TRAINER`
cannot write ledger/notebook/state. `LEDGER_WRITER` cannot write adapter.
`EVAL_QUARANTINE` cannot write either life ledger/notebook, compiler corpus,
adapter, later target, or split. The auditor receives serialized artifacts
after the fact and cannot feed any bytes back into a model call.

## 6. Persistence, sleep, and reset

### 6.1 Within-life persistence

Across ordinary wake pairs, the controller retains task/life counters,
public best score, current focus, append-only public ledger, capped notebook,
and deterministic retrieval definition. At acquisition task boundaries it
retains only the life ledger/notebook and cumulative public progress; it
resets focus to `KEEP`, clears the recent tail, resets the public environment,
workspace, tool processes, task files, compiler process/cache, and task RNG.
The opaque life nonce and life sequence remain stable.

At acquisition boundaries 4 and 8 only, the controller seals the
EXPERIENTIAL public projection. `SLEEP_COMPILER` deterministically selects
outcome-filtered ORIENT/ACT/REVISE rows under the bound 192/64/view and
50:50 retained-old/new capacities, renders 768-token rows, and rebuilds one
cumulative rank-16, alpha-16, dropout-0 `q_proj`/`v_proj` LoRA from the clean
pinned base with reset AdamW. The fixed target-token-touch receipt is 24
touches per retained row. There is no preservation/anchor/KL/auxiliary
objective, early stop, tuning, or target input. On receipt success it
atomically publishes the new authentic adapter. On any schema, provenance,
mask, budget, numerical, or integrity failure it publishes nothing and
terminates this recipe.

Only the published authentic LoRA crosses sleep. The sealed ledger,
notebook, source projection, manifests, and receipts persist as
nonparametric within-life source/audit evidence. Optimizer moments, gradients,
trainer process, packed batches, temporary corpus/cache, inference process,
provider session, KV/prefix cache, and RNG state are destroyed. `HARNESS`
performs the same sleep boundary accounting but mounts no adapter and gains
no learned bytes.

### 6.2 Life reset and sterile-fork reset

At an independent life reset, the adapter, ledger, notebook, retrieval index,
all counters/progress, focus, workspace, task/environment process, compiler
cache, files, RNG lineage, trainer state, and receipts tied to the prior life
are reset or discarded. No life evidence crosses lives.

Every target fork is cold-started in a fresh process from the pinned base,
its assigned adapter (or null), a fresh target-local workspace, fixed target
packet, fixed seed stream, and one immutable read-only life snapshot as
specified below. It receives no parent process, KV, cache, RNG, shell,
trainer, or live workspace state. At teardown the process, snapshot mount,
workspace, adapter mapping, and all temporary state are destroyed or placed
in quarantine. Its outcomes and receipts never write back to a life,
notebook, ledger, compiler, trainer, later target, or split.

## 7. Matched checkpoint target forks

The public target panel is sealed before any target model call. For each
checkpoint `c in {0,4,8}`, the fork launcher creates one HARNESS fork and one
EXPERIENTIAL-authentic fork for each of the four targets. It also creates an
EXPERIENTIAL adapter-off fork at each checkpoint and an EXPERIENTIAL
binding-shuffled fork only at checkpoint 8 if the predeclared semantic
derangement succeeds.

The exact mounts are:

| Fork | Base/adapter mount | Read-only life snapshot |
|---|---|---|
| `HARNESS@c` | clean base + null adapter | capped `HARNESS` ledger/notebook snapshot through `c` |
| `EXPERIENTIAL-authentic@c` | clean base + authentic checkpoint adapter | capped `EXPERIENTIAL` snapshot through `c` |
| `EXPERIENTIAL-off@c` | clean base + null adapter | the exact same `EXPERIENTIAL` snapshot used by authentic at `c` |
| `EXPERIENTIAL-shuffled@8` | clean base + semantically binding-shuffled adapter | the exact same `EXPERIENTIAL` snapshot used by authentic at `8` |

The checkpoint-0 snapshot is a canonical empty snapshot. The checkpoint-4
snapshot contains exactly the sealed public ledger/notebook prefix after
acquisition task 4; checkpoint 8 contains the prefix after task 8. A snapshot
is capped at 64 complete ledger events and 16 notebook records, with the same
event schema, 192-token-record, two-query, and packet caps used by the life.
The pilot prefixes (24 events at checkpoint 4 and 48 at checkpoint 8) retain
every event through that checkpoint; outside that bound, oldest events are
excluded before sealing. The snapshot's bytes and hash
are identical across all forks that name it. It is mounted read-only. A fork
`NOTE_APPEND` writes only to a fork-local ephemeral overlay, which is
retrievable later inside that same target fork under the ordinary notebook
caps but is never added to the mounted life snapshot, visible to another
fork, or returned to either on-policy life. The overlay is destroyed at fork
teardown after its quarantined audit receipt is written.

Thus `HARNESS` target forks retain HARNESS's own common nonparametric life
evidence, and all three EXPERIENTIAL fork variants retain the same
EXPERIENTIAL evidence. Adapter-off and shuffled differ only in assigned
weights and operation-target binding, respectively; they do not lose the
common retrieval channel. No target fork receives its role label, checkpoint
label, condition label, evaluator/reference data, future target, training
receipt, or life identity beyond the opaque nonce.

Every fork uses the same target order, public packet schema, six wake pairs,
at-most-six environment-action attempts, score construction, parser charges,
reset policy, and quarantine protocol. The fork model cannot distinguish the
forks from a marker. `D_HE,c` is consequently a descriptive contrast of
matched whole-harness checkpoint forks with their respective read-only life
snapshots; one common acquisition order and one paired life still do not
identify an arm effect, causal credit, or lifetime mechanism.

### 7.1 Experiment-contract boundary

Score definitions, CompilerGym edge cases, outcome-filtered compiler,
deduplication, row packing, optimizer/touch accounting, binding-shuffle
construction, split/headroom authority, seed derivation, determinism tiers,
and Stage-C dispositions are owned normatively by
[`experiment_spec.md`](experiment_spec.md), Sections 3--8. This file does
not restate or override those rules. The packet parser's operation-charge
rules above and the experiment contract's score-cell rules are jointly
required; a parser, lifecycle, or snapshot failure is handled as specified
here, while score and disposition classification follows the experiment
contract exactly.

The experiment contract delegates canonical JSON ordering to this file; the
normative rule is the declared schema key order above. No implementation may
replace it with generic sorted-key serialization.

## 8. Visibility prohibitions and failure boundary

The following are never model-visible in any phase or fork: raw source/IR,
filesystem paths, hidden target/reference/solution bytes, target roles,
future candidates, evaluator data, arm/condition/checkpoint labels, adapter
hash/origin, sleep duration, row or token counts, latency, cache warmth,
retry/training telemetry, private raw output, unparsed output, provider
conversation, hidden chain-of-thought, KV/prefix state, and cross-boundary
workspace/process/RNG state. Public observation vectors, legal pass names,
public outcomes, finite operation labels, bounded parsed public prose, and
the caller's capped read-only source snapshot are allowed exactly where the
packet order specifies them.

Any hash drift, local-artifact mismatch, unauthorized reader/writer,
packet/row overflow, parser contract drift, unexpected key, target leakage,
snapshot write, evaluation writeback, adapter mount mismatch, or reset
failure is terminal for the current recipe. The system MUST emit a failure
receipt and stop; it MUST NOT repair, substitute, tune, retry, increase a
cap, reveal a target, or reinterpret the failure as a result. A scientific,
causal, lifetime, superiority, or paper claim requires a separately ratified
change with fresh independent lives and controls.
