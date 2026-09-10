# PCFL V10 exact source repair: provenance positives, resource factorial, and V7 guard

Date: 2026-09-10

Status: **source-only advisory under the human-ratified V9 rework scope**.
This document authorizes no source-bundle authoring, import, syntax check,
preparation, implementation, materialization, fixture/root/data generation,
CPU benchmark, model/tokenizer call, training, LoRA/adapter/checkpoint work,
parenting, GPU use, resource acquisition, scientific claim, release, or
submission.

## 0. Controlling bytes and ruling

This repair reads the complete V9 critique and consensus and the directly
cited inherited repair sources:

| input | SHA-256 |
|---|---|
| V9 change | `bada525623c094914e41c60048a2e4714e1912c1202e5e889b2bf28f9992a0fc` |
| V9 critique | `e92e461fe8e37ed22353ffdefe0929afb98e1d59bb62643d138093a95ffbd4a5` |
| V9 consensus | `9e2066e1782a627e3fab15e179f1e15c33dc829b51076dbdd52556c5053176cf` |
| V9 candidate | `8a47d30909e0e171fe6dc1d6f92640fb7ed6d2bdab6642cabe57f91a5d549f59` |
| V9 source plan | `00914dfd94ae5a6a8e9ed031e2f349fbc21711ed6bb5891fcd44699093260132` |
| inherited provenance/resource repair | `96b3dcd1b60f484ae1983a91f00fd5abfe60fadf297876d837cfd32eb830b504` |
| inherited authority/V7 repair | `ae74fae9516fba5a699514674fd2299ec3130eca7814be723ccc5717258fcb2a` |

The selections below resolve exactly:

- `D-V9-PROVENANCE-POSITIVES`;
- `D-V9-RESOURCE-FACTORIAL`; and
- `D-V9-V7-GUARD-EXCEPTION`.

They do not resolve or weaken any other V9 disposition. The successor must
register each test below individually. An umbrella test may depend on them but
cannot replace, merge, compensate for, or rename them.

## 1. Immutable assay roster and budget

No experiment condition, phase, root, request slot, token allowance, endpoint,
gate, interface, or claim changes. The exact per-root scientific roster stays:

| conditions | count | phases | slots each | generated-token allowance each |
|---|---:|---|---:|---:|
| `AUTH_RECURRENT`, `AUTH_SCRATCH_OFF` | 2 | P+U+D | 43 | 11,008 |
| `ATOMS_RECURRENT`, `DERANGED_RECURRENT`, `REACHOUT_OFF_RECURRENT`, `NO_MEMORY_RECURRENT`, `PASSIVE_SIGNATURE_RECURRENT`, `RAW_CONTEXT_RECURRENT`, `RAG_RAW_RECURRENT`, `NATIVE_GRAPH_RECURRENT` | 8 | P+D | 39 | 9,984 |
| `BRIDGE_CUT_RECURRENT`, `TWIN_REDIRECT_RECURRENT` | 2 | P | 26 | 6,656 |
| `UNCERTAINTY_SHAM_RECURRENT` | 1 | U | 4 | 1,024 |
| `OLD_CUT_RECURRENT`, `NEW_CUT_RECURRENT`, `NO_PERSIST_NEW_RECURRENT` | 3 | D | 13 | 3,328 |
| `TARGET_ONLY_ANSWER_PRIOR_TAPE`, `AUTH_NO_FEEDBACK_TAPE` | 2 | four phase-level calls | 4 | 11,008 |

```text
slots/root
  = 2*43 + 8*39 + 2*26 + 1*4 + 3*13 + 2*4
  = 501

allowed generated tokens/root
  = 2*11,008 + 8*9,984 + 2*6,656 + 1*1,024
    + 3*3,328 + 2*11,008
  = 148,224

maximum input-token allowance/root = 501*8,192 = 4,104,192

DEV, 16 roots          = 8,016 slots; 2,371,584 generated tokens
confirmation, 32 roots = 16,032 slots; 4,743,168 generated tokens
DEV + confirmation     = 24,048 slots; 7,114,752 generated tokens
sentinels               = 24 slots; 6,144 generated tokens
grand maximum           = 24,072 slots; 7,120,896 generated tokens
maximum input allowance = 24,072*8,192 = 197,197,824 tokens
reserve only, 16 roots  = 8,016 slots; 2,371,584 generated tokens
```

Tests in this advisory are source/conformance requirements. They add zero
scientific model-call slots and zero generated-token allowance.

## 2. `M0V4-PROVENANCE-FINITE-ORDER-26`

Register this test individually with:

```text
kind: invariant
required_before: implementation
evidence_artifact:
  finite-order, canonical-pair, alias-collapse, legal-diamond, and
  synthetic-non-evidence receipt
expected:
  every exact positive fixture in 2.2 is accepted with its registered
  canonical output, including legal shared-root diamonds and SYNTH root-set
  deduplication; no SYNTH or re-expression becomes primitive evidence
falsifies:
  false cycle rejection, hash/order ambiguity, duplicate-root inflation,
  synthetic evidence laundering, or omission of the seventh pair
```

### 2.1 Frozen finite order and pair registry

Retain the inherited unsigned tuple order
`Position=(major:u8,lane:u8,ordinal:u16)`, where lane 0 is the ordinary event
and lane 1 is its post-event synthesis. The seven authoritative pairs remain:

| ordinal | position | pair |
|---:|---|---|
| 0 | `(24,1,0)` | `(p0,p1)` |
| 1 | `(24,1,1)` | `(p2,p3)` |
| 2 | `(24,1,2)` | `(p1,p4)` |
| 3 | `(24,1,3)` | `(p3,p4)` |
| 4 | `(24,1,4)` | `(p4,p5)` |
| 5 | `(24,1,5)` | `(p4,p6)` |
| 6 | `(41,1,6)` | `(p4,nh)` iff `nh` was admitted |

Numeric internal `FactKey=(src_ordinal,relation_ordinal,dst_ordinal)` and
`PairKey=(FactKey(left),FactKey(right))`, never public alias, goal, path rank,
semantic-hash rank, condition, score, or transform, determine pair order.
SYNTH parent citations are alias-collapsed, duplicate-eliminated, and sorted
by raw digest before identity, time, cycle, and support checks.

For any node `x`, define its evidential roots recursively:

```text
roots(ROOT r)  = {r}
roots(SYNTH s) = set_union(roots(parent) for parent in parents(s))
roots(ALIAS a) = roots(resolve(a))
```

The union is a mathematical set of canonical ROOT IDs. A SYNTH ID is never a
member. An alias and its sink cannot count twice. A valid diamond may share
one or more primitive roots and must not be classified as a cycle solely
because its branches reconverge.

PAIR_PROPOSAL parents remain the complete canonical primitive ROOT set for its
two endpoint FactKeys available at the proposal cut. A conformance-only
REEXPRESSION may have earlier SYNTH parents, but it adds no root and never
appears in authoritative V9 material. Rendering can consume only SUPPORTED
PAIR_PROPOSAL nodes; it cannot consume a REEXPRESSION as evidence.

### 2.2 Exact positive fixtures

Each fixture is a separately named entry in `source/mutation_fixtures.json`
and a separately asserted case under test 26:

1. `PROVV10-POS-OLD-SIX-ORDER`: the old-cut roots produce exactly ordinals
   0--5 at `(24,1,0..5)` in the table order; none is SUPPORTED before its
   endpoint validations at positions 25--31; exactly six links render after
   complete validation.
2. `PROVV10-POS-NEW-H0`: admitted `nh=C-R07->D` produces only ordinal 6 at
   `(41,1,6)` and renders only after later independent p4 and nh validations
   at 42 and 43.
3. `PROVV10-POS-NEW-H1`: identical to the preceding fixture except
   `nh=C-R08->D`; the ordinal and position remain 6 and `(41,1,6)`.
4. `PROVV10-POS-FAILED-COMMIT-ABSENCE`: without an admitted nh ROOT, position
   `(41,1,6)` and validation 43 are reserved but absent and no seventh link
   exists.
5. `PROVV10-POS-ALIAS-CANONICAL`: two strictly decreasing aliases resolve to
   one canonical ROOT; a direct citation and the two alias citations collapse
   to one sorted parent ID and yield the same SYNTH ID, root set, status, and
   rendering as the direct-only encoding.
6. `PROVV10-POS-SHARED-ROOT-DIAMOND`: with distinct ROOTs `r0,r1,r2`, earlier
   `s0.parents=[r0,r1]`, `s1.parents=[r0,r2]`, and later
   `s2.parents=[s0,s1]`, accept the acyclic graph and require
   `roots(s2)={r0,r1,r2}` exactly. `r0` counts once, not twice, and the two
   paths to it are not a cycle.
7. `PROVV10-POS-SYNTH-NON-EVIDENCE`: accept a conformance-only
   REEXPRESSION `x1.parents=[x0]` over primitive ROOTs and require
   `roots(x1)=roots(x0)` with neither `x0` nor `x1` in the root set. Offering
   the re-expression alone as later validation does not support a proposal
   and admits no Link or TransitionRow.
8. `PROVV10-POS-CORROBORATION`: a strictly later identical FactKey ROOT is
   corroboration, completes the applicable independent support, and never
   marks `(src,rel)` conflicted.
9. `PROVV10-POS-REVOCATION-STATE`: a structurally valid later ROOT with the
   same `(src,rel)` and different `dst` keeps the audit batch valid while
   changing every dependent proposal and transitive SYNTH descendant to
   permanent REVOKED and removing their rendered rows.

## 3. `M0V4-PROVENANCE-REVOCATION-CYCLE-27`

Register test 27 separately from test 26. It owns the fail-closed mutation
surface and cannot stand in for positive acceptance:

```text
kind: invariant
required_before: implementation
evidence_artifact:
  provenance structural-rejection, support-rejection, contradiction,
  permanent-revocation, transform-nonadmission, and atomicity receipt
expected:
  every case in 3.1 returns its exact registered disposition and an invalid
  batch makes zero persistent mutation
falsifies:
  cycle acceptance, premature/synthetic support, contradiction masking,
  un-revocation, transform-created evidence, or partial batch application
```

### 3.1 Exact negative fixtures

The outcome enum is exactly `BATCH_REJECT`, `SUPPORT_REJECT`, or
`VALID_REVOKED` as stated:

| fixture | required outcome |
|---|---|
| `PROVV10-REJ-ALIAS-UNKNOWN` | `BATCH_REJECT`: alias target is unknown. |
| `PROVV10-REJ-ALIAS-DUPLICATE-SOURCE` | `BATCH_REJECT`: one source has two targets. |
| `PROVV10-REJ-ALIAS-SELF-OR-CYCLE` | `BATCH_REJECT`: independently exercise self, nondecreasing edge, and multi-row alias cycle. |
| `PROVV10-REJ-PARENT-UNKNOWN` | `BATCH_REJECT`: collapsed parent ID is absent. |
| `PROVV10-REJ-PARENT-SELF-SAME-FORWARD` | `BATCH_REJECT`: independently exercise self, same-position, and later-position parent. |
| `PROVV10-REJ-COLLAPSED-DAG-CYCLE` | `BATCH_REJECT`: aliases expose a SYNTH dependency cycle. |
| `PROVV10-REJ-NONCANONICAL-PARENTS` | `BATCH_REJECT`: unsorted, duplicated, unresolved, or post-collapse-ID-mismatched parent array. |
| `PROVV10-REJ-NONCOMPOSABLE-PAIR` | `SUPPORT_REJECT`: `left==right` or `left.dst!=right.src`. |
| `PROVV10-REJ-INCOMPLETE-PRIMITIVE-PARENTS` | `SUPPORT_REJECT`: omit one available endpoint ROOT, add a foreign FactKey ROOT, or substitute a SYNTH parent for the required primitive set. |
| `PROVV10-REJ-PREMATURE-VALIDATION` | `SUPPORT_REJECT`: validation is before or at proposal position. |
| `PROVV10-REJ-REUSED-DISCOVERY-ROOT` | `SUPPORT_REJECT`: proposal and validation root sets are not disjoint. |
| `PROVV10-REJ-SYNTH-AS-PRIMITIVE` | `BATCH_REJECT`: a SYNTH or REEXPRESSION is declared as a primitive evidential ROOT. |
| `PROVV10-REJ-SYNTHETIC-ONLY-VALIDATION` | `SUPPORT_REJECT`: only synthetic descendants repeat the endpoint. |
| `PROVV10-REJ-UNREVOKE` | `VALID_REVOKED`: after contradiction, later matching evidence, aliasing, rerender, or re-proposal leaves the PairKey and all descendants REVOKED; any claimed restored link makes the expected receipt fail. |
| `PROVV10-REJ-TRANSFORM-EVIDENCE` | `BATCH_REJECT`: a carrier transform adds ROOT, SYNTH, support, contradiction, revocation, or a provenance position. |
| `PROVV10-REJ-BATCH-ATOMICITY` | `BATCH_REJECT`: one malformed final object in an otherwise valid batch leaves the pre-batch store byte-identical. |

All schema, canonical-ID, alias, parent, position, and cycle checks complete
over the whole batch before support, contradiction, revocation, rendering, or
write. For a structurally valid batch the status precedence remains:

```text
BATCH_REJECT > REVOKED > SUPPORTED > PENDING/SUPPORT_REJECT
```

## 4. `MTEXTV4-ROSTER-SLOT-ENVELOPE-23`

Register test 23 individually:

```text
kind: invariant
required_before: model_execution
evidence_artifact: exact roster/slot/token/NOT_REACHED arithmetic receipt
expected:
  the immutable table and every total in section 1 reproduce exactly;
  REQUEST_EMITTED plus NOT_REACHED partitions every registered slot
falsifies:
  a hidden call, missing condition/phase, altered token allowance, early-
  terminal slot deletion, reserve substitution, or resource-ledger drift
```

Positive fixture `RESOURCEV10-POS-ROSTER-GOLDEN` contains all 18 rows and the
root/split/sentinel totals from section 1. Negative fixtures independently
mutate every row's condition, phase bit, slot count, generation allowance,
8,192 input ceiling, split multiplier, sentinel count, `REQUEST_EMITTED`, and
`NOT_REACHED`; every single mutation rejects. Sealed NOT_REACHED slots count
in registered maxima but never in actual calls, offered generation allowance,
actual input, or generated tokens.

## 5. `MTEXTV4-PER-ARM-CHARGED-RESOURCE-VECTOR-24`

Register test 24 individually with one `ChargedResourceV5` for every
root-condition-phase and separate `__COMMON__`, root, condition, split, and
suite reductions.

### 5.1 Closed vector

Every numeric field is a nonnegative integer. `0` means applicable but unused.
`NA` is valid only for an inapplicable resource class and may never replace a
missing counter.

```text
ChargedResourceV5 := {
  identity: {
    root_receipt_id, condition, phase, mode,
    model_sha256, tokenizer_sha256, chat_template_sha256,
    renderer_sha256, parser_sha256, controller_sha256,
    scorer_sha256, runtime_sha256, device_manifest_sha256,
    meter_manifest_sha256
  },
  opportunity: {
    registered_slots, slots_request_emitted, slots_not_reached,
    maximum_input_tokens, registered_generation_allowance,
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
    cache_warmup_cpu_ns, render_cpu_ns, controller_cpu_ns, scorer_cpu_ns,
    common_fixture_peak_rss_bytes, graph_build_peak_rss_bytes,
    index_build_peak_rss_bytes, cache_warmup_peak_rss_bytes
  },
  reader: {
    invocations, found_returns, not_found_returns, blocked_returns,
    candidate_rows_examined, postings_touched, documents_returned,
    atom_records_returned, link_records_returned,
    return_utf8_bytes, return_tokens, reader_cpu_ns
  },
  thinker: {
    calls_attempted, calls_completed, calls_failed,
    input_tokens,
    input_system_tokens, input_protocol_tokens, input_state_tokens,
    input_static_context_tokens, input_reader_return_tokens,
    input_prior_scratch_tokens, input_other_tokens,
    generated_tokens, decoded_utf8_bytes,
    service_latency_ns, arm_wall_span_ns,
    gpu_active_ns_by_physical_device,
    peak_device_memory_bytes, peak_worker_rss_bytes
  },
  behavior_work: {
    successful_world_actions, no_effect_world_actions,
    other_unsuccessful_world_actions, total_world_actions,
    terminal_commands, controller_tool_operations
  },
  artifacts: {
    request_bytes, response_bytes, tool_return_bytes, trace_bytes,
    receipt_bytes, log_bytes, other_installed_bytes,
    unique_cas_bytes, temporary_bytes_written, temporary_bytes_deleted
  },
  external_cost_microusd
}
```

The seven input segment counts partition every exact rendered request:

```text
input_tokens = input_system_tokens + input_protocol_tokens
             + input_state_tokens + input_static_context_tokens
             + input_reader_return_tokens + input_prior_scratch_tokens
             + input_other_tokens
```

RAW_CONTEXT and NATIVE_GRAPH static-context tokens are charged once in
`stored.static_context_tokens` and again as input work on **every emitted
request containing them** in `thinker.input_static_context_tokens`. That is
intentional, not double counting: one is resident representation and the
other is repeated thinker input. RAG charges raw documents and index storage,
index-build/cache-warmup CPU, each query, candidate rows and postings touched,
returned documents/bytes/tokens, and the returned-token segment of every
subsequent model request. Common-reader arms charge invocations, lookup work,
typed null/blocked envelopes, records, serialization, and reader-return input
tokens. Thinker calls and GPU work are charged for every arm, including
one-shot tapes and failed attempts.

### 5.2 Exact standalone versus physical CAS law

For category `x`, root `r`, condition `c`, and phase `p`, define
`Closure_x(r,c,p)` as the set of distinct SHA-256 CAS objects of category `x`
reachable from that arm's frozen manifest.

```text
standalone_bytes_x(r,c,p)
  = sum(nbytes(o) for o in Closure_x(r,c,p))

physical_bytes_x(scope)
  = sum(nbytes(o) for o in union(Closure_x(r,c,p)
                                  for (r,c,p) in scope))
```

A content-identical object counts once inside one closure but counts fully in
every standalone arm that needs it. It is never divided by the number of
arms, roots, links, or calls. Suite physical storage counts the union once and
must not be computed by summing standalone values.

The exact positive microfixture is `RESOURCEV10-POS-CAS-STANDALONE-PHYSICAL`:
two common objects have 10 and 20 bytes, arm A has a unique 7-byte object, and
arm B a unique 11-byte object. Require:

```text
standalone(A) = 10+20+7  = 37
standalone(B) = 10+20+11 = 41
physical(A union B)      = 10+20+7+11 = 48
```

`78` is explicitly invalid as physical storage; `22` or any fractional share
is invalid as either standalone charge. The same closure/union law applies to
`unique_cas_bytes` and each stored/artifact byte category.

Common preparation work is recorded once in `__COMMON__`. A standalone arm
reports `common + arm-specific` work; suite-physical work is `common once +
sum arm-specific`. No observed-performance or equal-share allocation is
allowed. Actual time/token/byte counters sum; peaks reduce by `max`; wall span
is `max(end)-min(start)`; physical GPU-hours are
`sum(gpu_active_ns_by_physical_device)/3,600,000,000,000`. No
`A40-equivalent` conversion is permitted.

### 5.3 Required positive fixtures

- `RESOURCEV10-POS-FULL-VECTOR-ZERO-NA`: complete vector with legitimate zeros
  and legitimate `NA`, proving they are distinct from missing.
- `RESOURCEV10-POS-STATIC-REPEATED`: one 100-token static context stored once
  and included in three emitted requests yields stored static tokens 100 and
  request static-context tokens 300.
- `RESOURCEV10-POS-RAG-WORK`: nonzero index build, warmup, query, candidate,
  postings, four-document return, return-token, model-input, and artifact
  counters reconcile to their source receipts.
- `RESOURCEV10-POS-BLOCKED-READER`: one blocked invocation has one fixed-size
  return and zero candidate rows/postings, never zero invocation/return bytes.
- `RESOURCEV10-POS-NOT-REACHED`: registered allowance includes the unissued
  suffix while offered allowance and actual counters exclude it.
- `RESOURCEV10-POS-CAS-STANDALONE-PHYSICAL`: exact 37/41/48 result above.
- `RESOURCEV10-POS-COMPONENT-REDUCTION`: sums, maxima, interval wall span, CAS
  union, and physical-device GPU conversion each reproduce an independent
  golden.

Test 24 passes only when every root-condition-phase vector and every reduction
reproduces all positive goldens. It permits componentwise resource reporting;
it defines no scalar efficiency score and no text-versus-LoRA comparison.

## 6. `MTEXTV4-RESOURCE-METER-NONOMISSION-25`

Register test 25 individually:

```text
kind: invariant
required_before: model_execution
evidence_artifact: resource meter capability-closure and nonomission receipt
expected:
  every allowed work/storage/device path maps to exactly one raw counter and
  the registered reduction; all injected omissions or double charges reject
falsifies:
  free preprocessing, hidden retrieval/model work, CAS allocation bias,
  deleted-artifact erasure, unattributable concurrency, or NA laundering
```

The future meter manifest must enumerate the only process, thread, subprocess,
file/CAS, reader, index, cache, network, model-call, host-memory, physical-
device, and artifact-write capabilities. Unregistered capability is failure.
Per-arm workers and device streams must be attributable and resettable; if
concurrency prevents attribution, resource-factor evidence is invalid rather
than imputed.

The negative corpus is individually registered:

| fixture | required rejection |
|---|---|
| `RESOURCEV10-REJ-STATIC-ONCE-ONLY` | static context is charged for storage but omitted from one or more request-token segments. |
| `RESOURCEV10-REJ-RAG-BUILD-OR-POSTINGS-FREE` | index build, cache warmup, query, candidate row, postings, document return, or return tokens are omitted. |
| `RESOURCEV10-REJ-COMMON-READER-FREE` | blocked/null/found reader invocation, serialization, fixed envelope, record, or CPU is omitted. |
| `RESOURCEV10-REJ-HIDDEN-THINKER-CALL` | background, retry, sentinel, failed, or one-shot model attempt lacks a call/token/latency/device receipt. |
| `RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE` | common CAS bytes are fractionally allocated or omitted from standalone closure. |
| `RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL` | suite physical bytes sum standalone arms instead of taking the digest union. |
| `RESOURCEV10-REJ-CAS-DIGEST-ALIAS` | same bytes under two digests, or different bytes under one digest, evade unique-object accounting. |
| `RESOURCEV10-REJ-DELETED-TEMP-FREE` | a temporary request, response, index, cache, or log is deleted without written/deleted byte charge. |
| `RESOURCEV10-REJ-CPU-WARMUP-FREE` | preprocessing, graph build, tokenizer warmup, model warmup, or cache priming occurs outside a named CPU component. |
| `RESOURCEV10-REJ-GPU-UNATTRIBUTABLE` | GPU work has no physical device UUID/active-nanosecond owner or shared concurrency cannot be separated. |
| `RESOURCEV10-REJ-MEMORY-UNATTRIBUTABLE` | host/device peak has no resettable per-arm accounting boundary. |
| `RESOURCEV10-REJ-ZERO-NA-MISSING` | missing is encoded as zero or NA, or an applicable comparison contains NA. |
| `RESOURCEV10-REJ-SEGMENT-SUM` | input segments do not sum exactly to tokenizer-counted request input. |
| `RESOURCEV10-REJ-REGISTERED-ACTUAL-CONFLATION` | registered, offered, and actual slot/token counters are substituted for one another. |
| `RESOURCEV10-REJ-NETWORK-OR-COST` | any provider/network edge or nonzero external cost appears in the local USD 0.00 proposal. |

Test 25 is noncompensatory. Passing a global resource ceiling, test 19, or the
performance gates cannot rescue one failed nonomission fixture.

## 7. Sole V7 governance-guard exception

The only planned source member permitted to contain the registered FeltCraft
V7/V5 denied paths, hashes, change/protocol IDs, whole-artifact identities,
and distinctive interface names is exactly:

```text
research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v9/
  source/v7_boundary_v4.json
role: V7_BOUNDARY
schema: V7BoundaryV1
maximum_nbytes: 65,536
manifest_member: true
```

Governance deliberation/review artifacts may quote these identities as
negative authority evidence. That does not create a candidate, preparation,
runtime, model, or scientific exception. Generic control vocabulary such as
`V7_BOUNDARY`, `V7BoundaryV1`, the two registered test IDs, array field names,
and `passed` may appear in test/consumer specifications; actual denied values
must occur only in the boundary member and governance records.

`V7_BOUNDARY_GUARD` is the sole pre-preparation consumer role allowed to read
the boundary member. It is a validation stage over the existing 23-member
source plan, not a new source-plan row, experiment condition, or scientific
call. Its read closure is exactly:

1. `source/v7_boundary_v4.json`;
2. the normative source manifest and the other 22 planned member bytes;
3. their SourceProvenanceRow records; and
4. the proposed PCFL read/import/capability manifests.

It may normalize and resolve candidate paths, parse/hash candidate bytes, and
compare declarations with the boundary arrays. It may not open, import,
execute, deserialize from, or hash a file at a denied V7/V5 path; invoke a
denied module; use network access; execute any candidate source; or learn
expected PCFL values from the boundary.

The guard checks the inherited seven denial classes exactly: resolved path,
module/package/reflection/subprocess, whole artifact or embedded whole
artifact, declared V7-derived provenance, distinctive V7 interface used as a
dependency/answer source, reachable capability, and actor/model exposure.
Independently derived ordinary coincident scalars pass only when a provenance
row points to PCFL normative bytes or a named language/standard-library rule
and none of the seven predicates is true. There is no heuristic copied-scalar
test.

### 7.1 One-way output and nonexposure law

The guard's detailed receipt is governance-private. On success, its only
projection into a later preparation authority is:

```text
V7GuardProjectionV1 := {
  schema_version:1,
  artifact_type:"pcfl_v7_guard_projection",
  passed:true,
  pcfl_read_allowlist:[sorted repo-relative PCFL paths]
}
```

It contains no boundary path, boundary/denied digest, V7/V5 path or hash,
change/protocol ID, module/interface name, primitive/golden/output/audit
identity, violation detail, or boundary-derived expected value. On failure,
no projection exists and no preparation input is created. A generic private
governance result may say `SOURCE_BOUNDARY_REJECTED`; its details never enter
a public error, timing channel, receipt consumed by science, or later prompt.

Only the boolean pass and exact PCFL allowlist may affect whether preparation
is admitted and what PCFL files it can read. Materializer, constructive and
axiomatic checkers, fixtures, mutation bank, runtime, handoffs, readers,
renderer, parser, scorer, reducer, model/session/cache, public errors, and
scientific receipts receive neither the boundary object nor its metadata.

For two clean conformance inputs whose boundary metadata differs but whose
guard decision and PCFL allowlist are equal, every preparation-visible
projection and every potential semantic/actor/model-visible byte must be
identical. Governance/source-manifest/approval identities may differ and
remain private. If a boundary mutation changes pass to fail, the only allowed
effect is absence of the preparation projection. No V7 metadata is ever
rendered, serialized downstream, used as cache/index key, or exposed through
error text, length, ordering, padding, timing, or artifact name.

## 8. Individual V7 acceptance tests and fixtures

### 8.1 `M0V4-ZERO-V7-RUNTIME-REUSE-01`

Retain and register test 01 individually. It checks that all non-boundary
source/provenance/capability/runtime surfaces satisfy the seven denial
predicates and that ordinary coincident values are not falsely rejected. It
does not own or silently broaden the boundary exception.

Positive fixtures:

- `V7V10-POS-CLEAN-PCFL`: all 22 non-boundary members derive only from bound
  PCFL normative bytes or named language/standard-library rules; guard passes.
- `V7V10-POS-COINCIDENT-SCALAR`: independently derive each ordinary scalar
  `0,1,4,8,16` from an allowed source; guard passes with no V7 provenance.
- `V7V10-POS-BOUNDARY-SELF`: the exact planned boundary member contains its
  registered denial values and is accepted only as input to the sole guard.

Negative fixtures use boundary-array indices so actual denied values are not
copied into `mutation_fixtures.json`:

- `V7V10-REJ-RESOLVED-PATH`: direct, `..`, absolute, and symlink-resolved
  denied path.
- `V7V10-REJ-MODULE`: direct/dynamic import, package resource, reflection,
  plugin/entry point, serialized callback, and subprocess module.
- `V7V10-REJ-WHOLE-ARTIFACT`: exact hash, whole-file copy, and embedded
  byte-for-byte member.
- `V7V10-REJ-DECLARED-PROVENANCE`: denied source, golden, receipt, audit,
  primitive, or derived translation supplies semantics/tests/expected values.
- `V7V10-REJ-DISTINCTIVE-INTERFACE`: denied interface supplies a dependency,
  fixture field, oracle, or expected result.
- `V7V10-REJ-CAPABILITY`: file descriptor, environment, configuration, argv,
  cwd, package data, deserialization, subprocess, or network closure can reach
  a denied target.
- `V7V10-REJ-ACTOR-MODEL`: denied identity appears in carrier, view, return,
  tool envelope, rendered/tokenizer bytes, cache/session, public error,
  timing surface, or scientific receipt.

Every negative rejects before preparation and creates no downstream
projection.

### 8.2 `M0V4-V7-GUARD-EXCEPTION-NONEXPOSURE-34`

Register test 34 as a separate invariant required before preparation:

```text
evidence_artifact:
  sole-consumer capability graph, guard pass/fail projection, and
  downstream byte-nonexposure receipt
expected:
  only V7_BOUNDARY_GUARD reads the one boundary member; only the exact pass
  projection crosses the guard; equal pass/allowlist yields identical
  downstream bytes; failure yields no projection
falsifies:
  guard self-rejection, a second exception, denied-file read, boundary
  metadata laundering, or a direct/derived actor/model channel
```

Fixtures:

1. `V7V10-POS-SOLE-GUARD-CONSUMER`: consumer graph has exactly one incoming
   read edge from the boundary member to `V7_BOUNDARY_GUARD` and no other
   outgoing boundary edge; exact projection validates.
2. `V7V10-POS-NONEXPOSURE-TWIN`: two conformance-only boundary objects differ
   in an unused denied digest, both pass the same clean PCFL corpus and produce
   the same PCFL allowlist; the preparation projections and all synthetic
   downstream semantic/public/rendered bytes are byte-identical. Only private
   governance/source-manifest identities may differ.
3. `V7V10-POS-FAIL-CLOSED`: one denied-edge mutation changes pass to fail;
   projection is absent and no preparation-visible object exists.
4. `V7V10-REJ-SECOND-CONSUMER`: any materializer, checker, fixture, mutation,
   runtime, handoff, reader, renderer, parser, scorer, reducer, model/session,
   cache, or scientific receipt reads the boundary or an actual denied value.
5. `V7V10-REJ-GUARD-OPENS-DENIED`: guard resolves or opens the external denied
   path instead of matching only the registered metadata.
6. `V7V10-REJ-PROJECTION-EXTRA-FIELD`: pass projection contains a boundary
   digest/path, denied value, violation, V7 identifier, expected value, timing,
   or any field beyond the four-field closed schema.
7. `V7V10-REJ-FAILURE-PROJECTION`: failed guard emits any preparation
   projection, partial allowlist, candidate source, or consumable receipt.
8. `V7V10-REJ-INDIRECT-CHANNEL`: boundary metadata changes a semantic ID,
   carrier/handoff byte, ordering, pad length, error, filename, cache/index
   key, timing field, tokenizer input, result, or claim while pass/allowlist
   remain equal.
9. `V7V10-REJ-BOUNDARY-COPY`: any of the other 22 source members repeats an
   actual denied path/hash/interface value rather than referring generically
   to a boundary-array index.

Tests 01 and 34 both must pass. Test 01 proves denial; test 34 proves that the
mechanism needed to enforce denial neither rejects itself nor becomes a data
channel.

## 9. Resolution and claim boundary

| V9 consensus item | exact closure |
|---|---|
| `D-V9-PROVENANCE-POSITIVES` | individually registered tests 26 and 27; exact seven-pair order; shared-root diamond acceptance; SYNTH/re-expression non-evidence; alias, support, cycle, contradiction, revocation, transform, and atomicity fixtures |
| `D-V9-RESOURCE-FACTORIAL` | individually registered tests 23, 24, and 25; immutable roster; complete charged vector; repeated static-input, RAG, reader, thinker, GPU, memory, artifact, zero/NA, standalone-CAS, suite-physical-CAS, and nonomission laws |
| `D-V9-V7-GUARD-EXCEPTION` | retained test 01 plus distinct test 34; exactly one boundary member and guard consumer; closed pass projection; fail-with-no-projection; direct and indirect nonexposure corpus |

These are deterministic software/governance requirements. They do not prove
scientific construct validity or authorize execution. Even future passage
would not support DREAM authorship, SLEEP, LoRA transport, learning,
retention, self-written memory, parenting, compression, generalization,
lifetime improvement, efficiency, or the complete organism.
