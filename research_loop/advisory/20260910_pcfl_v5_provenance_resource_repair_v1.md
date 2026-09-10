# PCFL V5 source repair: charged resources and closed provenance

Date: 2026-09-10

Status: **source-only advisory for a newly bound successor proposal**. This
document is not a ratification and authorizes no preparation-source authoring,
implementation, materialization, fixture/root/data generation, CPU benchmark,
model or tokenizer execution, training, LoRA/adapter/checkpoint work,
parenting, GPU use, resource acquisition, scientific claim, release, or
submission.

## 0. Inputs and ruling

This repair was derived from the following complete inputs:

| Input | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| V4 `change.json` | `a6332cfeab3bc2281404a568e2c04eaf8ffa28db96d3c33265140f9fe7c3408f` |
| V4 `critique.json` | `6caa938022d9e6b2e47a3d3997b8d06c44a67568550fd86716d6123e2c1e2fad` |
| V4 `consensus.json` | `7cad92d5563f0b0be69d6dd72fca7419573d93fbb19021e5b614e0bac0798720` |
| integrated V4 candidate | `32d73b800971a61a20fa68694dc9cbed9203c65d59d3c01c5baffe2c3a6e53cc` |
| predecessor M0 exact-contract advisory | `b7329f6c89253a5d627751c0135a0f1aab6caff89d5d1d12dc2eba9ef08c3297` |
| predecessor M-TEXT exact-contract advisory | `73866889087937617ad3341ea409ccf1cc9207aaded8c416e704debbe0430947` |

The exact repairs below are sufficient source selections for
`D-V4-RESOURCE-FACTORIAL` and `D-V4-PROVENANCE-TOTAL-ORDER`. They must be
copied into a newly hash-bound architecture change and reviewed; this advisory
does not amend or ratify the rejected V4 packet by itself.

## 1. Exact 18-arm opportunity roster

Let a recurrent path phase (`PROBE_A`, `PROBE_B`, or `DELAYED_GOAL`) have:

```text
model-call slots = 13
allowed generated tokens = 13 * 256 = 3,328
maximum input-token allowance = 13 * 8,192 = 106,496
READ opportunities = 8
relation-action opportunities = 4
terminal opportunities = 1
```

Let the combined `UNCERTAINTY/ACQUIRE` phase have:

```text
model-call slots = 4
allowed generated tokens = 4 * 256 = 1,024
maximum input-token allowance = 4 * 8,192 = 32,768
READ opportunities = 0
world-action opportunities = 2
terminal opportunities = 0
```

A tape uses one model call per registered phase. Its call receives the entire
corresponding recurrent generated-token allowance: 3,328 for each path phase
and 1,024 for uncertainty/acquisition. The tape retains the same executor-side
READ, world-action, and terminal opportunity maxima as the corresponding
recurrent phase. It does not thereby receive future handles or feedback.

The following table is the complete per-root registry. `P` counts path probes
A and B, `U` the combined uncertainty/acquisition phase, and `D` delayed goal.
`R`, `B`, and `T` mean recurrent, alternative/bypass channel, and one-shot
tape. A disabled reader call still counts as a reader invocation and returns
the registered fixed-size `BLOCKED` envelope; `none` means there is no reader
interface in that arm.

| # | condition | mode | P | U | D | reader/channel in applicable path phases | call slots | generated allowance | input allowance | READ opp. | world-action opp. | terminal opp. |
|---:|---|:---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `AUTH_RECURRENT` | R | 2 | 1 | 1 | authentic common reader | 43 | 11,008 | 352,256 | 24 | 14 | 3 |
| 2 | `AUTH_SCRATCH_OFF` | R | 2 | 1 | 1 | authentic common reader | 43 | 11,008 | 352,256 | 24 | 14 | 3 |
| 3 | `ATOMS_RECURRENT` | R | 2 | 0 | 1 | atom-only common reader | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 4 | `DERANGED_RECURRENT` | R | 2 | 0 | 1 | deranged common reader | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 5 | `REACHOUT_OFF_RECURRENT` | R | 2 | 0 | 1 | fixed-size `BLOCKED`, no lookup | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 6 | `NO_MEMORY_RECURRENT` | R | 2 | 0 | 1 | fixed-size `BLOCKED`, no carrier | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 7 | `PASSIVE_SIGNATURE_RECURRENT` | R | 2 | 0 | 1 | condition-independent null envelope | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 8 | `RAW_CONTEXT_RECURRENT` | B | 2 | 0 | 1 | raw rows in static context; none | 39 | 9,984 | 319,488 | 0 | 12 | 3 |
| 9 | `RAG_RAW_RECURRENT` | B | 2 | 0 | 1 | deterministic BM25 retrieval | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 10 | `NATIVE_GRAPH_RECURRENT` | B | 2 | 0 | 1 | native graph in static context; none | 39 | 9,984 | 319,488 | 0 | 12 | 3 |
| 11 | `BRIDGE_CUT_RECURRENT` | R | 2 | 0 | 0 | bridge-cut common reader | 26 | 6,656 | 212,992 | 16 | 8 | 2 |
| 12 | `TWIN_REDIRECT_RECURRENT` | R | 2 | 0 | 0 | twin-redirect common reader | 26 | 6,656 | 212,992 | 16 | 8 | 2 |
| 13 | `UNCERTAINTY_SHAM_RECURRENT` | R | 0 | 1 | 0 | no path reader | 4 | 1,024 | 32,768 | 0 | 2 | 0 |
| 14 | `OLD_CUT_RECURRENT` | R | 0 | 0 | 1 | old-cut common reader | 13 | 3,328 | 106,496 | 8 | 4 | 1 |
| 15 | `NEW_CUT_RECURRENT` | R | 0 | 0 | 1 | new-cut common reader | 13 | 3,328 | 106,496 | 8 | 4 | 1 |
| 16 | `NO_PERSIST_NEW_RECURRENT` | R | 0 | 0 | 1 | no-persist-new common reader | 13 | 3,328 | 106,496 | 8 | 4 | 1 |
| 17 | `TARGET_ONLY_ANSWER_PRIOR_TAPE` | T | 2 | 1 | 1 | no memory; READ commands are blocked | 4 | 11,008 | 32,768 | 24 | 14 | 3 |
| 18 | `AUTH_NO_FEEDBACK_TAPE` | T | 2 | 1 | 1 | authentic common reader | 4 | 11,008 | 32,768 | 24 | 14 | 3 |

The closed arithmetic is:

```text
slots/root = 2*43 + 8*39 + 2*26 + 1*4 + 3*13 + 2*4 = 501

generated allowance/root
  = 2*11,008 + 8*9,984 + 2*6,656 + 1*1,024
    + 3*3,328 + 2*11,008
  = 148,224

input allowance/root = 501 * 8,192 = 4,104,192

DEV, 16 roots          = 8,016 slots; 2,371,584 generated; 65,667,072 input
confirmation, 32 roots = 16,032 slots; 4,743,168 generated; 131,334,144 input
DEV + confirmation     = 24,048 slots; 7,114,752 generated; 197,001,216 input
sentinels               = 24 slots; 6,144 generated; 196,608 input
grand maximum           = 24,072 slots; 7,120,896 generated; 197,197,824 input
reserve only, 16 roots  = 8,016 slots; 2,371,584 generated; 65,667,072 input
```

These are registered opportunities, not a claim that all requests are
emitted. Every unissued suffix is a separately sealed `NOT_REACHED` slot.

## 2. Complete charged resource vector

For every root `r`, condition `c`, and registered phase `p`, the future exact
M-TEXT package must emit one `ChargedResourceV5(c,r,p)` record. Every field is
an integer except an explicitly enumerated identity or `NA`. `0` means the
resource type applies and none was consumed. `NA` is legal only when the arm
has no such resource type (for example, BM25 postings in `RAW_CONTEXT`); a
missing field is always invalid.

```text
ChargedResourceV5 := {
  identity: {
    root_receipt_id, condition, phase, mode,
    model_sha256, tokenizer_sha256, chat_template_sha256,
    renderer_sha256, parser_sha256, controller_sha256,
    scorer_sha256, runtime_sha256, device_manifest_sha256
  },
  opportunity: {
    registered_slots, slots_request_emitted, slots_not_reached,
    max_input_tokens, registered_generation_allowance,
    offered_generation_allowance, read_opportunities,
    world_action_opportunities, terminal_opportunities
  },
  stored: {
    raw_event_bytes, atom_bytes, link_bytes, common_index_bytes,
    rag_index_bytes, native_graph_bytes, static_context_bytes,
    prompt_source_bytes,
    raw_event_tokens, atom_tokens, link_tokens, static_context_tokens
  },
  build: {
    common_fixture_cpu_ns, graph_build_cpu_ns, index_build_cpu_ns,
    render_cpu_ns, controller_cpu_ns, scorer_cpu_ns,
    common_fixture_peak_rss_bytes, graph_build_peak_rss_bytes,
    index_build_peak_rss_bytes
  },
  reader: {
    invocations, blocked_returns, not_found_returns, found_returns,
    candidate_rows_examined, postings_touched, documents_returned,
    atom_records_returned, link_records_returned,
    return_utf8_bytes, return_tokens, reader_cpu_ns
  },
  thinker: {
    calls_attempted, calls_completed, calls_failed,
    input_tokens, generated_tokens, decoded_utf8_bytes,
    service_latency_ns, arm_wall_span_ns,
    gpu_active_ns_by_physical_device, peak_device_memory_bytes,
    peak_worker_rss_bytes
  },
  behavior_work: {
    successful_world_actions, no_effect_world_actions,
    other_unsuccessful_world_actions, total_world_actions,
    terminal_commands, controller_tool_operations
  },
  artifacts: {
    request_bytes, response_bytes, tool_return_bytes, trace_bytes,
    receipt_bytes, log_bytes, other_bytes, unique_cas_bytes
  },
  external_cost_microusd
}
```

### 2.1 Counting laws

1. **Slots and tokens.** For the ordered slot registry `J(c,r,p)`,
   `registered_slots=|J|` and
   `slots_request_emitted + slots_not_reached = registered_slots`.
   `registered_generation_allowance` sums the frozen cap of every slot,
   including `NOT_REACHED`; `offered_generation_allowance` sums caps only for
   `REQUEST_EMITTED`; `generated_tokens` sums tokenizer-emitted tokens from
   completed calls. `input_tokens` is the sum of the exact chat-template token
   arrays sent. No estimate, character/token conversion, or maximum may be
   substituted for an actual count.
2. **Stored bytes.** For category `x`, let `Closure_x(c,r,p)` be the set of
   distinct SHA-256 CAS objects of that category reachable by the arm's frozen
   manifest. Then `stored.x_bytes = sum(nbytes(o) for o in Closure_x)`; a
   content-identical object counts once within an arm. It counts in every
   arm whose standalone closure needs it, so sharing never makes one arm look
   free. The separate suite-physical total is the byte sum over the union of
   all closures and therefore does not double-count CAS sharing.
3. **Stored tokenizer tokens.** Token counts use the exact frozen tokenizer
   with `add_special_tokens=false` over the canonical model-accessible UTF-8
   bytes of each distinct object, then sum once within the arm. Binary-only
   index objects have bytes but token value `NA`, not zero. Rendered request
   tokens are counted only in `thinker.input_tokens`, preventing double count.
4. **Common and incremental work.** Common fixture construction is recorded
   once in a `__COMMON__` receipt and copied as the named
   `common_fixture_cpu_ns` component of each arm's standalone vector. Arm-
   specific graph or index construction is charged to that arm. Suite physical
   CPU is `COMMON once + sum(arm-specific components)`; standalone comparison
   is `COMMON + arm-specific components`. No fractional allocation by 18,
   roots, calls, or observed performance is permitted.
5. **CPU work.** Each named component is the sum of thread CPU nanoseconds in
   its isolated, resettable worker accounting boundary. Reader CPU includes
   anchor resolution, candidate enumeration, lookup/ranking, serialization,
   and return hashing. RAG additionally records postings touched and documents
   returned. `BLOCKED` without lookup must have zero candidate rows/postings
   but still records one invocation and one fixed-size return.
6. **Calls and returns.** A thinker call is attempted only after the durable
   `REQUEST_EMITTED` marker. Completed and failed partition attempts. Reader
   return counters partition invocations. Atom/link/document counters count
   non-null records, while `return_utf8_bytes` and `return_tokens` count the
   complete rendered tool-return envelopes, including typed null padding.
7. **GPU and latency.** GPU charge is the sum of metered active nanoseconds for
   the request on each exact physical device UUID; actual GPU-hours are
   `sum(active_ns)/3,600,000,000,000`. No `A40-equivalent` conversion exists.
   `service_latency_ns` is the sum of request end minus request start;
   `arm_wall_span_ns` is `max(end)-min(start)` and is not additive. Peak RSS
   and device memory are maxima from a resettable per-arm worker/device meter.
   If the runtime cannot attribute a value under concurrency, resource-factor
   evidence fails rather than imputing it.
8. **Artifacts.** Category byte counts are exact installed file sizes.
   `unique_cas_bytes` sums distinct arm-reachable artifact digests once. The
   suite-physical artifact total is again the union, not the sum of standalone
   vectors. Temporary files that are created and deleted still count in their
   category's written-byte counter and may not escape charging.
9. **Money and hidden paths.** The frozen local proposal requires
   `external_cost_microusd=0`. Network/provider access, an unregistered model
   call, background retrieval, cache warmup, preprocessing subprocess, or
   artifact outside the manifest is a hard receipt failure, not uncharged
   overhead.

Root, condition, split, phase, and suite vectors reduce componentwise by sum,
except peaks use `max` and wall spans use their stated interval formula. `NA`
may combine only with `NA`; an applicable comparison containing `NA` rejects.

### 2.2 What may be called matched

Matching is phase-projected. `AUTH` path phases may be compared with the path
projection of `ATOMS`, `DERANGED`, `BRIDGE_CUT`, `TWIN_REDIRECT`, and
`REACHOUT_OFF`; its uncertainty phase with `UNCERTAINTY_SHAM`; and its delayed
phase with `OLD_CUT`, `NEW_CUT`, and `NO_PERSIST_NEW`. These contrasts must
match outer schema, slot handles and counts, fixed record/envelope bytes,
frozen-tokenizer token counts, read/action/terminal opportunities, recurrent
call slots, generation allowance, model, decoding, and session boundary for
the projected phase. Actual calls, reader CPU, input tokens, latency, GPU
time, and artifacts remain measured outcomes and need not match.

`AUTH_SCRATCH_OFF` matches all ex-ante full-sequence opportunities.
`AUTH_NO_FEEDBACK_TAPE` matches generated-token, READ, action, and terminal
opportunities but deliberately does not match call count, input tokens,
latency, or compute. `NO_MEMORY` and `PASSIVE_SIGNATURE` are shortcut controls,
not storage-matched carrier arms. `RAW_CONTEXT`, `RAG_RAW`, and
`NATIVE_GRAPH` are deliberately unequal alternative channels; they can support
a separately named behavioral advantage, but not an equal-resource or
efficiency claim.

No scalar efficiency score is defined here. Any later scalar weighting of
time, tokens, memory, storage, or money requires a new prospective formula and
ratification. A behavioral win plus the complete vector supports only the
componentwise facts actually observed. It never supports text-versus-LoRA,
compression, training, or transport efficiency.

## 3. Closed V4 provenance order

### 3.1 Canonical positions and node identities

Wall time and filesystem order are forbidden. Every evidence node has the
lexicographically ordered coordinate:

```text
Position = (major:u8, lane:u8, ordinal:u16)
lane 0 = one ordinary event at that major position
lane 1 = post-event synthetic proposal
```

Tuple comparison is unsigned numeric. Thus `(24,0,0) < (24,1,0) <
(25,0,0)`. A reserved position may be absent; positions never renumber.
Aliases are preprocessing references, not evidence nodes, and have no
position or evidential root.

Canonical ROOT and SYNTH IDs are lower-hex SHA-256 over the stated domain tag
followed by JCS UTF-8 of every field except `node_id`, with no BOM or trailing
LF:

```text
ROOT  domain = "PCFL-M0-PROV-ROOT-v4\0"
SYNTH domain = "PCFL-M0-PROV-SYNTH-v4\0"
```

SYNTH parent IDs are alias-collapsed, duplicate-eliminated, and sorted by raw
32-byte digest before hashing. A declared ID that differs from this
post-collapse canonical hash rejects the batch.

The exhaustive authoritative schedule is:

| position(s) | content |
|---|---|
| `(00..06,0,0)` | discovery ROOTs `p0..p6`, respectively |
| `(07..22,0,0)` | 16 calibration ROOTs in role order `H0,H1,Z0,Z1`, then experiment order `E0,E1,E2,E3`; position is `7 + 4*role_index + experiment_index` |
| `(23,0,0)`, `(24,0,0)` | `q0`, `q1` ROOTs |
| `(24,1,0..5)` | the six old pair proposals in section 3.2 |
| `(25..31,0,0)` | independent validation ROOTs for `p0..p6`, respectively |
| `(32..35,0,0)` | isolated goal-A ordinary event slots in execution order |
| `(36..39,0,0)` | isolated goal-B ordinary event slots in execution order |
| `(40,0,0)` | experiment outcome ROOT when `evidence=true` |
| `(41,0,0)` | commit outcome; exact `nh` ROOT only after correct commit |
| `(41,1,6)` | the new pair proposal `(p4,nh)`, present iff `nh` was admitted |
| `(42,0,0)` | independent new validation ROOT for `p4` |
| `(43,0,0)` | independent validation ROOT for `nh`, iff `nh` was admitted |
| `(44..47,0,0)` | delayed-goal ordinary event slots in execution order |

An event slot produces a provenance ROOT only when its canonical public event
has `evidence=true`; a `NO_EFFECT`, terminal, empty, private, synthetic, or
checker-only record does not. The canonical reference-success trajectory has
the rank-6 new proposal. Failure microfixtures reserve but omit it. Main V4
authoritative material contains no `REEXPRESSION` node. A conformance-only
REEXPRESSION fixture, if retained, sorts after all PAIR_PROPOSAL candidates by
`(payload_digest,parent_ids)` and remains synthetic non-evidence.

### 3.2 Pair enumeration and exact ordinals

For a STEP fact define:

```text
FactKey = (src_node_ordinal, relation_ordinal, dst_node_ordinal)
PairKey(a,b) = (FactKey(a), FactKey(b))
eligible(a,b) iff a != b and a.dst == b.src
```

Numeric internal ordinals `N00..N1f` and `R00..R0f`, never public aliases or
hash rank, determine ordering. At a compiler cut, enumerate every eligible
distinct FactKey pair available at the cut, sort by `PairKey`, and omit only a
PairKey already proposed or permanently revoked. Actor goal, route, score,
`k`, `h`, split, transform, presentation slot, and semantic-hash order are not
inputs.

The finite pair registry and global ordinals are exactly:

| global ordinal | cut/position | pair | composition |
|---:|---|---|---|
| 0 | `(24,1,0)` | `(p0,p1)` | `S -> X -> B` |
| 1 | `(24,1,1)` | `(p2,p3)` | `S -> Y -> B` |
| 2 | `(24,1,2)` | `(p1,p4)` | `X -> B -> C` |
| 3 | `(24,1,3)` | `(p3,p4)` | `Y -> B -> C` |
| 4 | `(24,1,4)` | `(p4,p5)` | `B -> C -> TA` |
| 5 | `(24,1,5)` | `(p4,p6)` | `B -> C -> TB` |
| 6 | `(41,1,6)` | `(p4,nh)` | `B -> C -> D` |

`q0` and `q1` compose with no admitted STEP and generate no pair. For ordinal
6, `nh` uses `R07` when `h=0` and `R08` when `h=1`; its global ordinal remains
6. No other pair exists in the authoritative finite registry.

The proposal parent list is the complete sorted set of primitive ROOT IDs at
or before the proposal cut whose exact FactKey equals either endpoint. It is
not a chosen minimum, does not contain SYNTH, and deduplicates an identical
root reached through more than one alias or branch. Omitting one available
root, adding another FactKey, or substituting a synthetic ancestor is
`SUPPORT_REJECT`.

### 3.3 Alias collapse

Alias rows are checker-input references only:

```text
AliasRow = {source_id:hex64,target_id:hex64}
```

`source_id` must be unique and must not collide with a canonical ROOT or SYNTH
ID. `target_id` must name either a canonical node or another declared alias.
Require raw-byte `target_id < source_id`. Process sources in ascending raw-byte
order and follow targets until a canonical non-alias node is reached. Reject a
self target, unknown target, duplicate source, canonical-node/source
collision, nondecreasing edge, or alias cycle. The strict-decrease rule makes
termination finite; cycle detection remains mandatory defense in depth.

Before any hash, chronology, root-set, support, or cycle check, replace every
parent/support citation by its resolved sink, remove duplicate citations, and
sort raw digest bytes. Aliases never merge different payloads, change a
position, create evidence, or survive into a carrier/handoff. Direct and
aliased encodings of the same citations must yield the same canonical SYNTH
ID, root set, support status, and rendered bytes.

### 3.4 Parent DAG, support, contradiction, and revocation

Only SYNTH nodes have parents. After alias collapse, every parent must exist
and have strictly smaller `Position`; unknown, self, same-position, or forward
parents reject the whole batch. Run an explicit depth-first cycle check over
the complete collapsed graph before semantic processing; any directed cycle
rejects the whole batch. A shared-root diamond is valid. A node's evidential
roots are the set union of primitive ROOT ancestors, so a shared root counts
once. A SYNTH can never be supplied as a primitive evidential root.

For proposal `s=(a,b)` at position `q`, let `P(s)` be its complete proposal
root set. At evaluation cut `t`, define `V_f(s,t)` as the set of admitted ROOTs
with exact endpoint FactKey `f`, position strictly greater than `q` and at or
before `t`, and ID not in `P(s)`. The proposal is `SUPPORTED` iff:

```text
eligible(a,b)
and canonical parents are complete
and V_a(s,t) is nonempty
and V_b(s,t) is nonempty
and neither endpoint relation key is conflicted
and no ancestor is REVOKED
```

Synthetic descendants, a repeated citation to an old root, a root at the
proposal position, a root before the proposal, or validation of only one
endpoint cannot satisfy support. The rendered evidence list is the sorted set
union `P(s) union V_a(s,t) union V_b(s,t)`. Rendering serializes only
SUPPORTED proposals and cannot propose, support, repair, or un-revoke.

An admitted STEP ROOT conflicts when its `(src,rel)` already has a different
admitted `dst`. Processing valid roots in increasing `Position`, then node ID,
marks that `(src,rel)` relation key permanently conflicted at the first such
event. An identical FactKey repeat is corroboration, not contradiction. At the
conflict event, every proposal depending on any FactKey with that relation key
and every transitive SYNTH descendant becomes permanently `REVOKED`; the
PairKeys enter the permanent-revocation set. Future matching evidence cannot
clear the conflict or status, and the compiler cannot re-propose that PairKey.

Status precedence at every cut is:

```text
structural BATCH_REJECT
  > REVOKED
  > SUPPORTED
  > PENDING / SUPPORT_REJECT
```

Thus a contradiction admitted at the same cut at which support would
otherwise complete revokes first. Revoked links/rows are absent from every
later carrier and handoff; primitive public ROOT events remain in the audit
log. Carrier transforms execute only after authentic render, have no
provenance position, cannot add ROOT/SYNTH/support, and cannot repair or cause
revocation.

The checker performs two passes atomically: validate schema, canonical IDs,
aliases, positions, parents, hashes, and cycles for the entire candidate; only
then apply facts, support, conflicts, and revocation in total order. Any first-
pass failure leaves the pre-batch store unchanged.

## 4. Mandatory positive and reject fixtures

The successor source manifest must enumerate and hash at least these distinct
fixtures; prose-only coverage is insufficient.

### Positive / expected-state fixtures

| fixture ID | required result |
|---|---|
| `PROVV5-POS-OLD-SIX-ORDER` | Exact positions `(24,1,0..5)`, exact pair order above, and exactly six supported old links only after events 25..31. |
| `PROVV5-POS-NEW-H0-H1` | For each `h`, correct commit emits exactly ordinal 6 at `(41,1,6)`; support occurs only after both events 42 and 43; failed commit omits proposal and validation. |
| `PROVV5-POS-ALIAS-CHAIN-CANONICAL` | A two-hop strictly decreasing alias chain plus duplicate citations collapses to the direct canonical parent list, ID, root set, status, and rendering. |
| `PROVV5-POS-SHARED-ROOT-DIAMOND` | Two SYNTH parents share one ROOT and a child cites both; DAG is legal and the shared root appears once. |
| `PROVV5-POS-CORROBORATION` | A later identical FactKey repeat completes support and never creates conflict. |
| `PROVV5-POS-REVOCATION-PROPAGATES` | A valid later contradictory ROOT leaves the batch valid but marks the direct proposal and every SYNTH descendant REVOKED and removes their rendered link/row. |

### Expected rejection / non-admission fixtures

| fixture ID | required result |
|---|---|
| `PROVV5-REJ-ALIAS-MALFORMED` | Individually reject unknown target, duplicate source, source/node collision, self target, nondecreasing target, and alias cycle. |
| `PROVV5-REJ-PARENT-TIME` | Individually reject unknown, self, same-position, and forward parent after alias collapse. |
| `PROVV5-REJ-COLLAPSED-CYCLE` | Alias collapse exposes a SYNTH dependency cycle; whole batch rejects atomically. |
| `PROVV5-REJ-NONCANONICAL-ID-PARENTS` | Reject unsorted/duplicate unresolved parents, wrong post-collapse ID, omitted available discovery root, or foreign FactKey root. |
| `PROVV5-REJ-SYNTHETIC-SUPPORT` | Synthetic-only, pre-proposal, same-position, reused discovery-root, or one-endpoint-only validation yields no support/link/row. |
| `PROVV5-REJ-NONCOMPOSABLE-PAIR` | Pair with `a==b` or `a.dst!=b.src` is not admitted. |
| `PROVV5-REJ-UNREVOKE` | After conflict, later identical evidence, rerender, aliasing, or re-proposal cannot restore support; any claimed restoration rejects the expected receipt. |
| `PROVV5-REJ-TRANSFORM-EVIDENCE` | Any carrier transform that adds provenance, support, a proposal, or a primitive root rejects. |
| `PROVV5-REJ-BATCH-ATOMICITY` | One malformed final object in an otherwise valid batch causes zero persisted mutation. |

Resource fixtures must likewise include the exact 18-row table as a positive
golden and one independent mutation for every numeric cell, vector field,
`0`/`NA` distinction, CAS closure member, actual-versus-registered counter,
counter reduction law, meter identity, and unregistered/background work path.

## 5. Acceptance-test completeness and distinct IDs

The V4 umbrella tests `M0V4-PROVENANCE-TRANSFORM-DAG-06` and
`MTEXTV4-ROSTER-ENDPOINT-RESOURCE-10` should remain, but neither is an
adequate uniquely failing acceptance unit. The critique's draft
`MTEXTV4-RESOURCE-FACTORIAL-19` should not be reused as a second umbrella.
Register these noncolliding tests after the existing `-00..-22` namespace:

1. `MTEXTV4-ROSTER-SLOT-ENVELOPE-23`: verifies all 18 rows, phase
   projections, per-arm maxima, 501/148,224/4,104,192 root totals, split and
   sentinel totals, and `NOT_REACHED` partitioning; rejects any added/removed
   slot or allowance.
2. `MTEXTV4-PER-ARM-CHARGED-RESOURCE-VECTOR-24`: requires every vector field
   and counting law for every root-condition-phase receipt, the exact match
   masks, standalone-versus-physical CAS accounting, and absence of an
   unregistered scalar-efficiency or text-versus-LoRA conclusion.
3. `MTEXTV4-RESOURCE-METER-NONOMISSION-25`: injects uncharged cache warmup,
   preprocessing, index/graph work, reader return, model call, deleted
   temporary artifact, concurrent unattributable memory/GPU work, and network
   access; every mutation must fail closed.
4. `M0V4-PROVENANCE-FINITE-ORDER-26`: verifies the full position table,
   exact seven-pair registry and order, canonical post-alias identities,
   complete roots, later independent support, and legal root-deduplicated
   diamonds using all positive fixtures.
5. `M0V4-PROVENANCE-REVOCATION-CYCLE-27`: verifies contradiction precedence,
   permanent descendant revocation, no re-proposal/un-revoke, collapsed cycle
   rejection, transform non-admission, and batch atomicity using every reject
   fixture.

Tests 23--25 are required before any practical-baseline or resource statement.
Tests 26--27 are required before the source-ratifiability and preparation
gates may call provenance closed. Their receipts must be separate even if one
checker executable evaluates both.

This closes only the two assigned V4 dispositions. Overall successor
acceptance remains incomplete until the independently identified authority,
handoff projection, delayed-entry entitlement, algebra shortcut,
producer/scorer neutrality, bridge/twin endpoint, endpoint applicability,
claim-clause disposition, rendered model boundary, and zero-V7 provenance
tests are also exact and hash-bound. No pass here may compensate for those
open gates.

## 6. Claim boundary

The resource repair permits exact statements about registered opportunity and
observed componentwise cost. It does not itself establish efficiency. The
provenance repair permits a checker to establish deterministic chronology,
support, and revocation behavior in this finite instrument. It does not prove
scientific construct validity, DREAM authorship, learning, retention, LoRA
transport, generalization, or organism-level behavior.
