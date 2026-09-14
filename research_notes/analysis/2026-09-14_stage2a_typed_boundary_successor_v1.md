# Advisory Stage2A typed-boundary exactness cross-check v1

**Date:** 2026-09-14 PT
**Status:** `ADVISORY_NONAUTHORITY`. Astra v6 at commit `b74cbc64` is the
adopted authority. This memo neither supersedes it nor opens a gate.
**Scope:** prospective CPU source/test exactness only; no materialization,
tokenizer/model call, fit, GPU use, capacity change, or scientific result.

## 1. Precedence and one replacement

Stage2A v5 remains the inherited contract and Astra v6 is its adopted typed-
boundary successor. The only intended replacement is v3 section 8's twelve-
root exhaustive semantic-alias ledger as a promotion/admission gate, including
that ledger's vector requirement in v3 section 10 row 7 and P0.5. Complete
source custody, v2 sections 8.1--8.2, the future-ID producer, namespace
certificate, typed graph aliases/core/signatures, finite route basis/matcher,
actor/parser bytes, paired design, targets, seeds, scoring, training, costs,
and claims remain. `source_semantic_occurrences` may remain a non-promoting
diagnostic; it cannot clear, fail, or exempt a boundary. This paragraph records
the narrow reading; this advisory does not itself perform the replacement.

The binding inputs at this checkout are:

| object | current file SHA-256 |
|---|---|
| adopted Astra v6 at `b74cbc64` | `119b97eb418e7b9586c1425c091b846f7eb7f100ab337ca03cc8b92df2b7b0b6` |
| Stage2A v5 | `6ebefdba31de6f14416105c9509dbba06319f306bdd3472259a8d072ba9877e7` |
| reduced critical path | `bc17448f0106909970b4550e9b806b74854d781c4b97b189c536c768fa30b14d` |
| Builder core bindings v1 | `04b214f3ade98bc9f1464a869791def711beaf3b143af4ca51d70f43e82250ff` |
| finite route language v1 | `12a7d849a6c2a2c6ead1d6b3acb2279e2e725a929a1b0a0638346fad5a7d4b4b` |
| metadata-complexity fresh audit | `f99705ae022da90f4060a893c2b7824b3e6ee9c4b848893c6abfeb8beaf4ef69` |

The metadata audit's evidence paragraph calls `34a29185...` its own hash; at
this checkout that hash is instead the prior v5 source-readiness audit. The
last row above is the hash of the actual committed metadata-audit bytes and is
the evidence used here.

## Adversarial comparison verdict

**`V6_NEEDS_NARROW_BINDINGS`.** Only the following v6 ambiguities could produce
two conforming-looking implementations or weaken a gate:

1. “Once per case/pair” does not choose 32 pair objects or 64 case objects, nor
   define their bytes/content IDs. It can therefore duplicate or omit a member,
   mutation, off-trace source, or route basis while retaining matching hashes.
2. The decision boundary names content but no schema, projection encoding,
   canonical ID-list form, nullable fields, or native-receipt state. Two binders
   can hash different public bytes or treat a hash-only list as custody.
3. “Full private categorical values and keys” has no finite field/type rule.
   Producers can disagree about `family`, phase/mutation enums, compound case
   keys, or slash fragments; “unhandled category” cannot be tested without that
   closed basis.
4. Original-offset ownership is required but the exact field authorization and
   route-receipt records are unnamed. Endpoint, owner, shared-GOT, boundary-
   crossing, and complete-causal-prefix implementations can therefore diverge.
5. Gate 5's “in each phase/both arms” does not define four decision classes
   versus five source phases, deterministic record choice, or require the named
   leak detector to fire. A guard could receive credit solely from boundary-
   equality rejection without testing a leak class.
6. `STOP admission` and “native preparation open” are prose states. They do not
   say which existing GO flags remain false or whether a reviewer can open a
   tokenizer/model path by setting an adjacent flag.
7. V6 says thresholds are unchanged while inheriting v5's full-panel thresholds
   and also selecting the later reduced 560 slots. Without binding the reduced
   minima, pair subset, chain reservation, and BASE-gain rule, either threshold
   family can be implemented.

Sections below are advisory narrow bindings for those seven points; they add no
new gate, scientific content, or capacity.

## 2. Exact custody objects

Use v3 CJSON and SHA-256. `HEX` is lowercase hex. For exact bytes `b`, define

```text
BLOB(name,b)={"bytes_hex":HEX(b),"name":name,
              "sha256":HEX(SHA256(b)),"size_bytes":len(b)}
```

`bytes_hex` is mandatory: a digest is never a substitute for retained bytes.
For custody only, encode typed source values recursively as follows: a dataclass
is `{"dataclass":fully-qualified-class-name,"fields":[[declared-name,ENC(value)],...]}`
in declared field order; a mapping is `{"mapping":[[ENC(key),ENC(value)],...]}`
sorted by encoded key; a tuple is `{"tuple":[ENC(value),...]}`; bytes are
`{"bytes_hex":HEX(value)}`; and string, integer, boolean, and null are unchanged.
An object blob's `b` is `CJSON(ENC(object))`; the display-master blob's `b` is
the raw master bytes. Blob names are unique and raw-ASCII sorted.

There are exactly 32 `STAGE2A_PAIR_SOURCE_CUSTODY_V1` payloads, one for each
`p00..p31`. Each payload has exactly keys
`blobs,contract_hashes,pair_index,schema,world`. `contract_hashes` has exactly
`core_v1,route_v1,stage2a_v5,typed_boundary_v1`; the first three equal their
correspondingly named rows in section 1 and the last equals this file's SHA-256
at the adopting commit.
Each payload has the following complete blobs:

```text
source_contract_pins
display_master
allocation_master_receipt
role_bindings
paired_construction
paired_mutation_receipt
m0/case_descriptor       m1/case_descriptor
m0/task                  m1/task
m0/registry_services     m1/registry_services
m0/effective_world_edges m1/effective_world_edges
m0/trace                 m1/trace
m0/facts                 m1/facts
m0/targets               m1/targets
m0/route_basis           m1/route_basis
```

`registry_services` includes every directory, ordinary/recovery service block,
raw registry row, owner, and off-trace contingency. `targets` contains all four
targets with exact bytes/hash, command/operand, ordinal/phase, trace boundary,
selection index, and before/after CURRENT. `paired_mutation_receipt` contains
the exact v5 member allowlist and both values at every allowed pointer.
`route_basis` contains every registered EVENT transition once with its owning
query, EVENT, port, predicted GOT, effective WORLD destination, RECOVER,
receipt, and source path; successor state is the effective destination.

The payload also retains, as deterministically named blobs, every per-decision
canonical disclosed-ID list, future-ID list, public graph, and core required by
section 3. Their names are exactly
`mM/uU/ARM/{disclosed_ids,future_ids,public_graph,core,typed_leak_basis}` for `M=0,1`,
`U=0..3`, and `ARM=CLOSED,ATOM_LOCAL`. Each ID-list item has exactly
`source_path,type,value`; sort unique items by individual CJSON bytes and store
the list as a CJSON array. Graph/core bytes remain their adopted canonical
bytes. Define

```text
pair_source_id = HEX(SHA256(CJSON(payload)))
```

and address the retained payload by that ID. The independent checker rebuilds
each pair from the adopted constructor, allocation/master pins, and role map;
requires byte equality for every blob; and independently reproduces the pair,
member cases, mutation, routes, targets, all hashes, and all counts. No caller
object, digest, cache, success flag, span, exemption, or inventory is trusted.

## 3. Exact per-decision public boundary

There are exactly `64 cases * 4 targets * 2 arms = 512` receipts. A
`STAGE2A_PUBLIC_BOUNDARY_V1` receipt has exactly:

```text
schema, pair_source_id, world, member, unit_id, arm,
decision_class, source_phase, decision_index, retained_source_turn_indices,
projection_kind, projection_bytes_hex, projection_sha256,
message_receipts, field_receipts, route_receipts,
target_bytes_hex, target_sha256, target_command, target_operand,
task_start, task_goal, latest_public_current,
implicated_query, implicated_event, contradiction_status,
disclosed_ids_ref, disclosed_ids_sha256,
future_ids_ref, future_ids_sha256,
core_ref, core_sha256, public_graph_ref, public_graph_sha256,
route_basis_ref, route_basis_sha256,
typed_leak_basis_ref, typed_leak_basis_sha256,
native_prefix_receipt
```

`decision_class` is `SEEK`, `PROSPECT`, `CHECK`, or `CONTINUE`; `CHECK` maps
exactly from source phase `READ_CHECK` or `STEP_CHECK`, and the other three map
identically. Nullable implicated/operand/contradiction values preserve their
existing typed null rules. Every `*_ref` is the exact blob name in the bound
pair source; its digest must match that blob.

`projection_kind` is exactly `PUBLIC_CONTENT_LF_PROJECTION_V1` and its bytes are
the exact ASCII contents of the original allowed prefix messages joined by one
LF with no added terminal LF. `message_receipts` bind, for every message, role,
projection `[start,end)`, original message index, original source-turn index or
null, observation index, content hash, world/member/arm, and pair source ID.
The checker independently renders the allowed CLOSED or ATOM prefix and
requires equality of messages, projection, ordering, offsets, and bytes before
scanning. ATOM never inherits CLOSED history.

Each `message_receipts` item has exactly `content_sha256,end,message_index,
observed_at,role,source_trace_index,start,world,member,arm,pair_source_id`.

`field_receipts` bind each public occurrence by exact value bytes,
`[start,end)`, message receipt, parsed field path/type, original owner and
source path, observation index, and authorization kind. Authorization kinds
are only:

```text
PROTOCOL_STOP_GRAMMAR  TASK_START  TASK_GOAL  LATEST_CURRENT
RETURNED_ROUTE_QUERY   RETURNED_EVENT_DID
ISSUED_QUERY           SELECTED_EVENT
IMPLICATED_EVENT_RECOVER  RETURNED_EVENT_GOT_CURRENT
```

They retain the adopted phase and chronology rules: SEEK operand only in an
already returned ROUTE QUERY; PROSPECT only in returned EVENT DID; CHECK only
as the issued query or selected EVENT already in the transcript; CONTINUE only
as latest CURRENT. `RETURNED_EVENT_GOT_CURRENT` requires an authentic returned
EVENT owner and equality to latest CURRENT, but not selection of that EVENT.
The protocol exception covers only the system's standalone `STOP` line.

Each `field_receipts` item has exactly `authorization_kind,end,
evidence_sha256,message_index,observed_at,owner_id_hex,owner_type,parsed_path,
source_path,source_trace_index,start,value_hex`; nullable owner/source-turn
values are explicit null. Each `route_receipts` item has exactly
`causal_prefix_end,causal_prefix_sha256,causal_prefix_start,end,
first_endpoint_end,first_endpoint_start,message_indices,roles,second_endpoint_end,
second_endpoint_start,source_paths,start`.

Before native preparation, `native_prefix_receipt` is exactly null. At native
preparation it becomes an exact receipt for pinned tokenizer/template file
hashes, rendered context bytes/hash, context token IDs/hash/count, message
boundaries, generation suffix, and round-trip bytes; the independently
rendered context must equal the context actually supplied to the actor. This
memo performs and authorizes none of that native work.

An occurrence is authorized only at its receipted original offsets. Copying,
moving, appending, truncating, crossing a field/message boundary, changing any
intervening byte, or changing case/member/arm/master/role map invalidates it.
For route history, the receipt binds the complete original causal prefix
through the second endpoint, including intervening actor, WORLD, and service
bytes and roles. Endpoint equality is insufficient; bare ordered-ID prose and
unknown route prose have no exemption.

## 4. Finite typed leak basis and decision

For each boundary, independently derive one
`STAGE2A_TYPED_LEAK_BASIS_V1`, bind its CJSON SHA-256 in the receipt, and scan
only these six typed classes. The basis object has exactly
`entries,route_basis_ref,route_basis_sha256,schema`. Every `entries` item has
exactly `kind,source_path,value_hex,value_type`; sort unique items by their
individual CJSON bytes. Classes 1--5 are entries and class 6 is the bound route
basis/reference:

1. `NEXT_ACTION`: the exact full target bytes.
2. `TARGET_OPERAND`: the exact non-null operand, under section 3's phase rules.
3. `UNDISCLOSED_ID`: every exact undisclosed QUERY, EVENT, PORT, and non-task
   destination ID in the complete future list, retaining identifier type and
   source path.
4. `PRIVATE_VALUE`: the complete `world/member` case key, causal-pair key,
   unit ID, every complete role key, and complete string values of the existing
   descriptor/core/mutation enum fields `domain,pair_type,family,family_motif,
   flow,recovery_subtype,terminal_class,goal_side,phase,mutation_kind`; retain
   type and source path, deduplicate by `(type,value)`, and never split a value.
5. `FORBIDDEN_LABEL`: exactly `PCFL_EVENT_LINK`, `PCFL_OLD_NEW`,
   `PCFL_ROUTE_PREFIX`, `GOAL_BRAID_CROSS_ROUTE`,
   `GOAL_BRAID_DELAYED_BRANCH`, `GOAL_BRAID_OLD_PREFIX`, plus edge labels
   `LINK`, `OLD`, and `NEW`.
6. `ROUTE_LANGUAGE`: the complete section-2 effective-transition basis through
   the adopted finite route recognizer, including action/service/mixed forms
   and ordered port/event/query list forms.

V2 raw, uppercase/space-collapsed, and compact normalization remains. It is
applied to each complete typed value, never to create sub-needles. IDs and
keys match only as complete structured tokens; private categorical values
match only a complete parsed field/token, never characters inside another
identifier or string. Full actions and supported routes are also checked
across parsed field/message boundaries. Invalid public syntax fails closed.

No needle may be derived from a JSON pointer, structural key name, array index,
boolean, null, standalone integer, tagged pointer/value, or substring/lexer
atom of an opaque identifier or other typed value. A clean decision requires:

```text
candidate projection == independently rendered allowed projection
AND every typed-basis match is absent or has the one applicable exact
    section-3 occurrence/route receipt
AND no receipt authorizes NEXT_ACTION (except PROTOCOL_STOP_GRAMMAR),
    UNDISCLOSED_ID, PRIVATE_VALUE, or FORBIDDEN_LABEL
AND unknown route prose is reported UNCERTIFIED and fails the boundary
```

## 5. Eight CPU gates and control names

All gates run on the complete 32-pair/64-case/256-unit/512-boundary source.

1. `G1_SOURCE_TOTALITY`: independently reproduce all pair payloads and blobs,
   v5 placements, role/master/allocation pins, both members/arms, 256 targets,
   and READ/STEP/THINK/STOP totals `96/64/64/32`.
2. `G2_BOUNDARY_EQUALITY`: all 512 projections match independent rendering;
   every extra, missing, moved, reordered, or changed byte fails.
3. `G3_INVENTORY_EQUALITY`: every disclosed/future list and every complete
   effective-transition basis matches independent values, hashes, counts,
   source paths, effective destinations, and recovery ownership.
4. `G4_CLEAN_SOURCE_PASS`: all 512 authentic CLOSED/ATOM boundaries pass with
   custody for every allowed occurrence; ATOM has no inherited history.
5. `G5_LEAK_MUTATION_MATRIX`: in each of the eight
   `(SEEK|PROSPECT|CHECK|CONTINUE) * (CLOSED|ATOM_LOCAL)` strata, use the
   raw-ASCII-smallest eligible boundary and a fresh unauthorized span to inject
   the full target, operand, one future ID of every type available in that
   stratum, a full private category and role key, each of the nine forbidden
   labels, and every supported two-transition route rendering family. Each
   injection must produce its named typed finding; equality failure alone is
   not credit.
6. `G6_RECEIPT_ADVERSARIES`: copied text, moved/truncated prefix, changed
   intervening WORLD/service bytes, same endpoints with changed middle,
   foreign arm/case/master/role map, cross-boundary match, and caller-created
   span/inventory/receipt each fail.
7. `G7_PAIR_SCORING_INTEGRITY`: intervention twins have only predeclared
   differences; target tape, decode seeds, BASE/D1 identity, strict scoring,
   canaries, training, and cost arithmetic reproduce exactly.
8. `G8_RESOURCE_RECEIPT`: report canonical bytes/items, peak RSS, and wall time
   for every one of 512 checks and totals. No truncation, sampling, skipped
   record, or resource-error clearance is allowed. Runtime is bounded by the
   public projection, exact lists, and finite transition basis, never by
   traversing the complete custody tree per arm.

The advisory narrow bindings use these exact control names:

```text
GO_CPU_SOURCE            = TRUE_AFTER_ROOT_ADOPTION
GO_CPU_TEST              = TRUE_AFTER_ROOT_ADOPTION
STOP_TYPED_BOUNDARY      = TRUE_ON_ANY_G1_TO_G8_OR_REVIEW_FAILURE
GO_NATIVE_PREPARATION    = FALSE_PENDING_G1_TO_G8_AND_FRESH_REVIEW
GO_WRITE_ROOT            = FALSE
GO_MATERIALIZE           = FALSE
GO_MODEL_TOKENIZER       = FALSE
GO_FIT_OR_GPU            = FALSE
GO_CLAIM                 = FALSE
```

`STOP_TYPED_BOUNDARY` also fires if any complete source byte/object is absent,
any inventory lacks independent derivation, any injected leak lacks its named
finding, any copied/foreign occurrence inherits custody, or any invariant below
changes. Under these advisory bindings, only after all eight gates pass on
exact committed bytes and a fresh reviewer binds the exact source/test/receipt
hashes may that reviewer set
`STOP_TYPED_BOUNDARY=FALSE` and `GO_NATIVE_PREPARATION=TRUE`. That transition
does not set any other GO true and is not model/GPU authority.

## 6. Preserved reduced-screen boundary

The selected next model experiment remains exactly the reduced 560-call rung:
BASE `280` plus D1 `ATOM_LOCAL` `280`, one fit, 256 updates/four presentations,
zero reader calls, with intervention pairs `0,2,4,6` per decision class, eight
chains reserving 29 calls each, and 16 canaries. Its minima remain pair-correct
`>=3/4` per SEEK/PROSPECT/CHECK/CONTINUE, typed interventions `>=30/32`, whole
chains `>=6/8`, useful pre-STEP READs `>=7/8`, typed STEPs `>=7/8`, canaries
`>=15/16`, and chain gain over paired BASE `>=2/8`. Targets, target tape,
adapter rank/heat/mask/template, decode seeds, strict parser/scoring, controls,
claims, and all later continuation/STOP rules remain unchanged. This memo
removes a metadata bottleneck only; it adds no science, fit, call, token, actor,
context, or GPU capacity.
