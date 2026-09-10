# v2 visibility, IPC, taint, reset, and report-access contract

`private_field_registry.json` is the exhaustive information inventory. The
rule at every boundary is deny-by-default: a process receives only the fields
in its literal input allowlist below, and any undeclared field, descendant,
metadata, header, filename, environment variable, log fragment, exception,
timing value, or cache behavior is a Stage-0 failure.

## Split target-time processes

The former combined `TARGET_THINK_ACTOR` stage is invalid and is replaced by
three separate processes and two typed IPC edges:

```text
FROZEN CORPUS/INDEX -> TARGET_READER -> NOTE|AST|NOT_FOUND -> TARGET_THINK
TARGET_THINK -> USE -> PUBLIC_ACTOR -> PUBLIC NEXT STATE + ACTION VALIDITY
TARGET_THINK -> LOCK -> LOCAL THINK TERMINAL (no actor IPC)
```

| process | exact allowed inputs | exact allowed outputs |
|---|---|---|
| `TARGET_READER` | assigned corpus/index through an orchestrator-private object reference; fixed target-memory handle; one typed Think query/cursor naming that handle | one bounded NOTE, one bounded AST record, or NOT_FOUND to Think; audit-only sibling to integrity/resource processes |
| `TARGET_THINK` | public target state, public goal/legal menu, own workspace, fixed target-memory handle, and charged reader result | one schema-valid USE to actor, or LOCK to the local Think terminal controller; no actor-private transition or score |
| `PUBLIC_ACTOR` | current public state, public legal menu, exactly one schema-valid USE, and its sealed immutable transition bytes | public next state and action-validity only |

`LOCK` is never serialized or dispatched on the Think-to-actor edge, and it
causes no actor invocation. The actor never receives or can derive
NOTE/AST/candidate/corpus/index bytes,
memory handles, capabilities, queries, reader results, addresses, digests,
paths, byte/token lengths, corpus variant/cut, root/family/h/q/z, target ID or
truth, goal-twin ID, seed/sampler data, cache/timing/error data, certificate,
comparator, score, analysis, or report state. Mutating corpus, index, digest,
address, path, or intervention identity while holding the emitted action and
public actor inputs fixed must give byte-identical actor input and output.

## Dream and event exposure

Recurrent Dream sees public events only through an interactive charged event
receipt. One-shot Dream sees the same eligible events only through the
mechanically charged event-by-event sealed batch defined in
`event_extractor_contract.md`. Think—recurrent or structured one-shot—never
receives a source event or extractor record; it receives only its permitted
memory representation and post-freeze public task packet.

A recurrent pre-READ catalog exposes exactly `handle_id`, `handle_kind`,
`phase`, `ordinal`, and `readable`. It exposes no payload, digest, length,
timing, parse/error state, family, h/q/z, result-derived shape, target,
comparator, closure, address, path, cache, or dedup field. Model-visible event,
candidate, and memory results and `ONE_SHOT_EVENT_BATCH` never contain an audit
digest or byte count; those fields live in a non-model audit sibling.

All one-shot envelopes use a dedicated closed empty state with no workspace or
staged-object capability arrays; the recurrent state schema is unreachable.
Structured one-shot Think uses only the closed one-shot AST packet/record and
public-handle-only provenance, never the recurrent capability-bearing record.
All `ONE_SHOT_PLAN` citations are public event/raw-A handles; node/object
capabilities are neither visible inputs nor valid output citations. The same
closed public-handle-only provenance applies to every one-shot Dream candidate,
nested NOTE/record, and immutable Dream-1 pool item. Any capability field or
value at any one-shot input/output depth is rejected before invocation or
mutation.

Dream-1 staged bytes are cloned before the h/q fork. Candidate-handle values,
candidate-read-capability values, receipt-ref values, count, order, and shape
are identical across paired fresh Dream-2 sessions wherever their topology and
ordinals correspond. At target time the rendered memory-handle values and
memory-read receipt refs, count, order, shape, prompt envelope, and all bytes
before an authorized reader result are identical across SELF, EMPTY, OBSERVED,
CROSSED, and SHAM intervention clones wherever topology corresponds.
Content address, store path, digest, dedup/cache state, variant/cut ID, and
length are never model-visible. A separate noncognitive integrity checker may
verify them; Dream, Sleep cognition, reader cognition, Think, and actor may not.

Public event/raw-A handles are direct fixed labels of event kind plus one-based
source ordinal. Every opaque model-visible identifier named by these edges is
fixed-shape, non-content, and a deterministic function only of declared
topology and zero-based issuance/source/resolver ordinal under the dedicated
`model_visible_identifier` namespace supplied by `rng_contract.json`: public
event/raw-A receipt refs, Dream-1
candidate handles and candidate-read capabilities, target-memory handles and
memory-read receipt refs, and session-local authored node/object capabilities.
This contract does not specify the namespace's HMAC. Content, treatment,
condition/cut/intervention, model output, digest/address/path/length,
cache/dedup, timing/error, and score are forbidden derivation inputs. A
collision, topology-corresponding paired-value mismatch, or content-bearing
identifier is a Stage-0 failure.

## Chronology, taint, mutation, and reset

At T0 assignments, source-randomness commitment, target-blind constructors,
handles, seeds, and contracts freeze. Dream-1 has no raw A or target. At T1
fresh Dream-2 can receive raw A only after a charge and can receive a Dream-1
candidate only through its fixed-shape, ordinal-determined Dream-2-session
reference.
At T2 Sleep receives selected model-authored bytes and permitted public
provenance, but no target, score, identity descendant, or offline label. Only
after corpus freeze at T3 may target state/goal/menu enter Think and actor.
B/evaluation never returns upstream.

The only permitted paired h Dream-2 pre-invocation differences after the
shared clone are raw A, its event-local extraction, the charged model-visible
receipt, and deterministic renderer/state descendants of those public bytes.
Seed, sampler, topology-corresponding identifier values, cache policy, runtime,
and all pre-A bytes must match.

The manifest's `resolver_ordinal` and rendered pre-operation
`state.resolver_ordinal` are zero-based `r`. The input envelope's `operation_ordinal`, model-authored step
`ordinal`, and audit read receipt's `operation_ordinal` are all one-based
`r+1`. Every field named `operation_ordinal` is therefore one-based. Any
alternative offset or mismatch is rejected before a consumer runs.

Offline-comparator mutation first freezes model outputs, corpus, index, reader
results, and action inputs, mutates every `offline_mutable` inventory field,
and replays deterministic projections only. Frozen causal bytes must remain
identical; this is not a claim that a stochastic rerun is identical. The
separate `target_test_only` mutation proves every pre-target Dream/Sleep/index
byte is target-independent. Every branch/life/target begins a clean process
under the namespaces in `rng_contract.json`; context, KV cache, filesystem or
object-store identity, timing/error state, prior target, B outcome, and
evaluator state cannot cross the reset boundary.

## Opaque access and report boundary

Opaque bytes are retained append-only but are sealed from `PRIMARY_REDUCER`
and `PRIMARY_REPORTER`. Before the primary report freezes, those roles may
consume only: assignment and allowed row metadata; process/parse statuses;
endpoint values; public predictions/actions/outcomes; revision-receipt
booleans and permitted receipt IDs; corpus and executable hashes; provenance
counts/types; resource totals; and access-log receipts. They may not consume
raw prompts/responses, NOTE text, corpus excerpts, lexical tokens, human/model
summaries of opaque content, or examples chosen by inspecting opaque bytes.

The primary report is rendered only from that fixed projection, linted, then
JCS-hashed with its complete access log. Any raw opaque access by a report or
analysis role before that receipt invalidates the report and gates. Only after
freeze may the named `POST_REPORT_EXPLORATORY_REVIEWER` request separately
logged raw access. Such inspection is labeled exploratory, cannot alter a row,
gate, alarm, report, or run state, and cannot establish factor semantics,
truth/falsity, solution/no-solution content, mechanism, h-mediated action,
recurrence, superiority, replication/generalization, persistence, lifetime,
LoRA, A-MEM, or paper efficacy. AST-only semantic inspection remains a
separate non-rescuing diagnostic and never feeds an opaque gate.

## Static enforcement

Stage 0 serializes each process input against an exact allowlist and injects
every forbidden inventory item one at a time; every injection must fail before
the consumer runs. It also tests content-bearing capabilities, changed handle
values/order/count, changed receipt refs, nondeterministic/colliding identifiers,
LOCK on actor IPC, path/address/variant descendants, target-time source-event
injection, undeclared consumers, and cache/timing/error channels. The change-
level visibility matrix and graph must be regenerated to name
`TARGET_READER`, `TARGET_THINK`, and `PUBLIC_ACTOR` and the edges above; until
that non-overlapping artifact is repaired, this contract records an explicit
cross-file dependency rather than treating the stale merged matrix as valid.
