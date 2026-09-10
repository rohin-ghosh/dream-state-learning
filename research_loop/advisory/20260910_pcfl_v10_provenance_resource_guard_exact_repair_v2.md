# PCFL V10 exact source repair v2: provenance, resources, and the V7 guard

Date: 2026-09-10

Status: **source-only successor advisory under the human-ratified V9 rework
scope**. This document preserves
`20260910_pcfl_v10_provenance_resource_guard_exact_repair_v1.md` byte for
byte. It authorizes no source-bundle authoring, import, syntax check,
preparation, implementation, materialization, fixture/root/data generation,
checker execution, benchmark, model/tokenizer call, training,
LoRA/adapter/checkpoint work, parenting, GPU use, resource acquisition,
scientific claim, release, or submission.

## 0. Controlling sources and scoped succession

| source | SHA-256 |
|---|---|
| V9 critique | `e92e461fe8e37ed22353ffdefe0929afb98e1d59bb62643d138093a95ffbd4a5` |
| V9 consensus | `9e2066e1782a627e3fab15e179f1e15c33dc829b51076dbdd52556c5053176cf` |
| V9 source-authoring plan | `00914dfd94ae5a6a8e9ed031e2f349fbc21711ed6bb5891fcd44699093260132` |
| V10 registry/render/claim repair v1 | `a6c9944f6b410f75a7ac4afa152e922fd30857f5ecd4d5f32ce9b111e80317b2` |
| V10 authority/delayed-baseline repair v1 | `b381e5079b7ac15306533da7f9425646d103fcfcd4220937605c55396a46704c` |
| provenance/resource/guard repair v1 | `cf634bf4040b9dc945cd5140c943d8718043244d1e1e717053f4436ab1b28371` |

The change identity is exactly:

```text
C10 = "chg_20260910_pcfl_m0_mtext_bound_v10"
PLAN_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source_authoring_plan.json"
MANIFEST_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/normative_source_manifest.json"
BOUNDARY_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/v7_boundary_v4.json"
DENIAL_CORPUS_PATH =
  "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/governance/v10_normative_denial_corpus.json"
```

This v2 is the successor selection for `D-V9-PROVENANCE-POSITIVES`,
`D-V9-RESOURCE-FACTORIAL`, and `D-V9-V7-GUARD-EXCEPTION`. It incorporates the
v1 finite-order, contradiction, revocation, CAS, nonomission, and nonexposure
laws. It supersedes v1 only in these identified places:

1. every V9 boundary/plan path in v1 is replaced by the exact C10 path above;
2. governance-private writer/hasher and independent exact-byte-review access
   are distinguished from candidate/preparation/runtime consumption;
3. the guard projection contains the literal 22-path allowlist in section 6;
4. source-provenance rows are external manifest sidecars, never embedded in
   the bytes whose digest they state;
5. the boundary has the exact, noncircular governance provenance in section
   5, sourced from the bound V10 normative denial corpus; and
6. the colliding name `ChargedResourceV5` is replaced, for C10 only, by the
   closed `ChargedResourceV10` in section 4.

No other inherited scientific, visibility, roster, endpoint, test, or claim
rule is weakened. In particular, an umbrella receipt cannot replace any of
the seven individually registered tests below.

## 1. Immutable 18-condition roster and budget

The complete per-root roster remains:

| # | condition | mode | P | U | D | slots | generated allowance | input allowance | READ opportunities | world-action opportunities | terminal opportunities |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `AUTH_RECURRENT` | R | 2 | 1 | 1 | 43 | 11,008 | 352,256 | 24 | 14 | 3 |
| 2 | `AUTH_SCRATCH_OFF` | R | 2 | 1 | 1 | 43 | 11,008 | 352,256 | 24 | 14 | 3 |
| 3 | `ATOMS_RECURRENT` | R | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 4 | `DERANGED_RECURRENT` | R | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 5 | `REACHOUT_OFF_RECURRENT` | R | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 6 | `NO_MEMORY_RECURRENT` | R | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 7 | `PASSIVE_SIGNATURE_RECURRENT` | R | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 8 | `RAW_CONTEXT_RECURRENT` | B | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 0 | 12 | 3 |
| 9 | `RAG_RAW_RECURRENT` | B | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 24 | 12 | 3 |
| 10 | `NATIVE_GRAPH_RECURRENT` | B | 2 | 0 | 1 | 39 | 9,984 | 319,488 | 0 | 12 | 3 |
| 11 | `BRIDGE_CUT_RECURRENT` | R | 2 | 0 | 0 | 26 | 6,656 | 212,992 | 16 | 8 | 2 |
| 12 | `TWIN_REDIRECT_RECURRENT` | R | 2 | 0 | 0 | 26 | 6,656 | 212,992 | 16 | 8 | 2 |
| 13 | `UNCERTAINTY_SHAM_RECURRENT` | R | 0 | 1 | 0 | 4 | 1,024 | 32,768 | 0 | 2 | 0 |
| 14 | `OLD_CUT_RECURRENT` | R | 0 | 0 | 1 | 13 | 3,328 | 106,496 | 8 | 4 | 1 |
| 15 | `NEW_CUT_RECURRENT` | R | 0 | 0 | 1 | 13 | 3,328 | 106,496 | 8 | 4 | 1 |
| 16 | `NO_PERSIST_NEW_RECURRENT` | R | 0 | 0 | 1 | 13 | 3,328 | 106,496 | 8 | 4 | 1 |
| 17 | `TARGET_ONLY_ANSWER_PRIOR_TAPE` | T | 2 | 1 | 1 | 4 | 11,008 | 32,768 | 24 | 14 | 3 |
| 18 | `AUTH_NO_FEEDBACK_TAPE` | T | 2 | 1 | 1 | 4 | 11,008 | 32,768 | 24 | 14 | 3 |

Here `P` is the two path phases `PROBE_A` and `PROBE_B`, `U` is
`UNCERTAINTY_ACQUIRE`, and `D` is `DELAYED_GOAL`. A recurrent path phase has
13 registered slots, 3,328 generated-token allowance, 106,496 input-token
allowance, eight READ opportunities, four world-action opportunities, and one
terminal opportunity. The U phase has four slots, 1,024 generated tokens,
32,768 input tokens, zero READ, two world actions, and zero terminals. A tape
uses one call in each applicable phase while retaining that phase's full
generated allowance and executor-side opportunities.

```text
slots/root
  = 2*43 + 8*39 + 2*26 + 1*4 + 3*13 + 2*4
  = 501

allowed generated tokens/root
  = 2*11,008 + 8*9,984 + 2*6,656 + 1*1,024
    + 3*3,328 + 2*11,008
  = 148,224

maximum input-token allowance/root = 501*8,192 = 4,104,192

DEV, 16 roots          = 8,016 slots; 2,371,584 generated; 65,667,072 input
confirmation, 32 roots = 16,032 slots; 4,743,168 generated; 131,334,144 input
DEV + confirmation     = 24,048 slots; 7,114,752 generated; 197,001,216 input
sentinels               = 24 slots; 6,144 generated; 196,608 input
active grand maximum   = 24,072 slots; 7,120,896 generated; 197,197,824 input
reserve only, 16 roots  = 8,016 slots; 2,371,584 generated; 65,667,072 input
```

Reserve is dormant and cannot replace DEV, confirmation, or sentinel work.
The arithmetical product `64*148,224=9,486,336` includes dormant reserve and
is not the active generated-token maximum. `REQUEST_EMITTED` and
`NOT_REACHED` partition every registered slot. A `NOT_REACHED` slot retains
its registered ceiling but contributes zero offered or actual tokens and zero
model call.

### 1.1 Test 23 fixture meanings

- `RESOURCEV10-POS-ROSTER-18` is exactly the 18 ordered rows in the table and
  no nineteenth, missing, renamed, or reordered row.
- `RESOURCEV10-POS-PHASE-PROJECTION` expands every P into `PROBE_A` and
  `PROBE_B`, every U into `UNCERTAINTY_ACQUIRE`, every D into `DELAYED_GOAL`,
  and reproduces every row's applicable phase count and opportunities.
- `RESOURCEV10-POS-ROOT-SPLIT-ACTIVE` reproduces the 16/32/16 split and every
  active, sentinel, and separate-reserve total above.
- `RESOURCEV10-POS-NOT-REACHED-PARTITION` independently seals issued and
  unissued suffixes and satisfies the exact slot and token partition.
- `RESOURCEV10-REJ-ROSTER-ROW-DRIFT` independently adds, drops, renames,
  reorders, or changes the mode of one condition; each case rejects.
- `RESOURCEV10-REJ-PHASE-PROJECTION-DRIFT` independently adds, drops, or moves
  one P/U/D applicability or opportunity; each case rejects.
- `RESOURCEV10-REJ-SLOT-OR-ALLOWANCE-DRIFT` changes exactly one slot, 256-token
  generation cap, or 8,192-token input cap; each case rejects.
- `RESOURCEV10-REJ-EARLY-TERMINAL-DELETES-SLOT` removes rather than seals one
  post-terminal `NOT_REACHED` slot; reject.
- `RESOURCEV10-REJ-RESERVE-SUBSTITUTION` uses any reserve root to rescue,
  replace, or augment DEV/confirmation; reject.
- `RESOURCEV10-REJ-SENTINEL-AS-ENDPOINT` counts any sentinel as a condition,
  root, endpoint observation, or reserve; reject.

## 2. Verbatim nine-field acceptance registry records

The following is a valid JSON array. Each object has exactly the nine fields
required by `AcceptanceTestSpec`; a C10 registry v2 must copy the objects
byte-for-byte after JSON parsing/canonical serialization. It may not merge,
rename, omit, alias, or add fields to them.

```json
[
  {
    "test_id": "M0V4-ZERO-V7-RUNTIME-REUSE-01",
    "kind": "invariant",
    "required_before": "materialization",
    "acceptance": "Every non-boundary C10 member, provenance row, capability, import surface, runtime surface, and actor/model projection satisfies all seven V7/V5 denial predicates; independently derived ordinary coincident scalars remain permitted; the boundary exception is owned only by test 34.",
    "positive_fixture_ids": ["V7V10-POS-CLEAN-PCFL", "V7V10-POS-COINCIDENT-SCALAR"],
    "reject_or_mutation_fixture_ids": ["V7V10-REJ-RESOLVED-PATH", "V7V10-REJ-MODULE", "V7V10-REJ-WHOLE-ARTIFACT", "V7V10-REJ-DECLARED-PROVENANCE", "V7V10-REJ-DISTINCTIVE-INTERFACE", "V7V10-REJ-CAPABILITY", "V7V10-REJ-ACTOR-MODEL"],
    "evidence_artifact": "ZeroV7RuntimeReuseReceiptV1",
    "failure_disposition": "INVALID before materialization; emit no prepared output.",
    "claim_withdrawal": "Withdraw clean-room status and every scientific clause."
  },
  {
    "test_id": "MTEXTV4-ROSTER-SLOT-ENVELOPE-23",
    "kind": "invariant",
    "required_before": "model_execution",
    "acceptance": "The exact 18 rows, phase projections, 501 slots/root, 148224 generated tokens/root, 4104192 input tokens/root, 16/32/16 root split, 24 sentinels, active totals, reserve separation, and REQUEST_EMITTED/NOT_REACHED partition equal section 1.",
    "positive_fixture_ids": ["RESOURCEV10-POS-ROSTER-18", "RESOURCEV10-POS-PHASE-PROJECTION", "RESOURCEV10-POS-ROOT-SPLIT-ACTIVE", "RESOURCEV10-POS-NOT-REACHED-PARTITION"],
    "reject_or_mutation_fixture_ids": ["RESOURCEV10-REJ-ROSTER-ROW-DRIFT", "RESOURCEV10-REJ-PHASE-PROJECTION-DRIFT", "RESOURCEV10-REJ-SLOT-OR-ALLOWANCE-DRIFT", "RESOURCEV10-REJ-EARLY-TERMINAL-DELETES-SLOT", "RESOURCEV10-REJ-RESERVE-SUBSTITUTION", "RESOURCEV10-REJ-SENTINEL-AS-ENDPOINT"],
    "evidence_artifact": "RosterSlotEnvelopeReceiptV1",
    "failure_disposition": "INVALID for arithmetic/roster drift; INCOMPLETE for a missing slot receipt.",
    "claim_withdrawal": "Withdraw all scientific and resource-comparability clauses."
  },
  {
    "test_id": "MTEXTV4-PER-ARM-CHARGED-RESOURCE-VECTOR-24",
    "kind": "invariant",
    "required_before": "model_execution",
    "acceptance": "Every applicable root-condition-phase emits exactly one closed ChargedResourceV10; every common and reduction receipt reconciles; standalone CAS is the complete per-arm closure, physical CAS is the digest union, and every positive fixture in section 4 has its exact golden.",
    "positive_fixture_ids": ["RESOURCEV10-POS-CLOSED-SCHEMA", "RESOURCEV10-POS-FULL-VECTOR-ZERO-NA", "RESOURCEV10-POS-STATIC-REPEATED", "RESOURCEV10-POS-RAG-WORK", "RESOURCEV10-POS-BLOCKED-READER", "RESOURCEV10-POS-NOT-REACHED", "RESOURCEV10-POS-CAS-STANDALONE-PHYSICAL", "RESOURCEV10-POS-COMPONENT-REDUCTION", "RESOURCEV10-POS-POST-ORIGIN-DESCENDANT"],
    "reject_or_mutation_fixture_ids": ["RESOURCEV10-REJ-V5-SCHEMA-NAME", "RESOURCEV10-REJ-MISSING-FIELD", "RESOURCEV10-REJ-EXTRA-FIELD", "RESOURCEV10-REJ-WRONG-TYPE", "RESOURCEV10-REJ-ZERO-NA-MISSING", "RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE", "RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL", "RESOURCEV10-REJ-CAUSAL-REALLOCATION"],
    "evidence_artifact": "PerArmChargedResourceVectorReceiptV1",
    "failure_disposition": "INVALID affected arm and resource factorial; no scalar imputation is allowed.",
    "claim_withdrawal": "Withdraw the affected arm and every practical, componentwise-resource, or efficiency comparison."
  },
  {
    "test_id": "MTEXTV4-RESOURCE-METER-NONOMISSION-25",
    "kind": "invariant",
    "required_before": "model_execution",
    "acceptance": "The closed capability manifest and ResourceMeterEventV10 ledger attribute every allowed work, storage, device, call, reader, network, and artifact event exactly once; raw events reconcile every ChargedResourceV10 leaf and no omitted, duplicated, unowned, negative, or unattributable event exists.",
    "positive_fixture_ids": ["RESOURCEV10-POS-METER-CAPABILITY-CLOSURE", "RESOURCEV10-POS-METER-LEAF-RECONCILIATION", "RESOURCEV10-POS-CAUSAL-SCOPE-RECONCILIATION"],
    "reject_or_mutation_fixture_ids": ["RESOURCEV10-REJ-STATIC-ONCE-ONLY", "RESOURCEV10-REJ-RAG-BUILD-OR-POSTINGS-FREE", "RESOURCEV10-REJ-COMMON-READER-FREE", "RESOURCEV10-REJ-HIDDEN-THINKER-CALL", "RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE", "RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL", "RESOURCEV10-REJ-CAS-DIGEST-ALIAS", "RESOURCEV10-REJ-DELETED-TEMP-FREE", "RESOURCEV10-REJ-CPU-WARMUP-FREE", "RESOURCEV10-REJ-GPU-UNATTRIBUTABLE", "RESOURCEV10-REJ-MEMORY-UNATTRIBUTABLE", "RESOURCEV10-REJ-ZERO-NA-MISSING", "RESOURCEV10-REJ-SEGMENT-SUM", "RESOURCEV10-REJ-REGISTERED-ACTUAL-CONFLATION", "RESOURCEV10-REJ-NETWORK-OR-COST", "RESOURCEV10-REJ-CAUSAL-REALLOCATION"],
    "evidence_artifact": "ResourceMeterNonomissionReceiptV1",
    "failure_disposition": "INVALID affected arm and resource factorial; a global ceiling or test 19 cannot compensate.",
    "claim_withdrawal": "Withdraw the affected assay and every practical, componentwise-resource, or efficiency clause."
  },
  {
    "test_id": "M0V4-PROVENANCE-FINITE-ORDER-26",
    "kind": "invariant",
    "required_before": "implementation",
    "acceptance": "The finite position table, seven-pair order, canonical alias collapse, complete primitive roots, later independent support, legal shared-root diamonds, and SYNTH/re-expression non-evidence rules reproduce every section 3 positive fixture exactly.",
    "positive_fixture_ids": ["PROVV10-POS-OLD-SIX-ORDER", "PROVV10-POS-NEW-H0", "PROVV10-POS-NEW-H1", "PROVV10-POS-FAILED-COMMIT-ABSENCE", "PROVV10-POS-ALIAS-CANONICAL", "PROVV10-POS-SHARED-ROOT-DIAMOND", "PROVV10-POS-SYNTH-NON-EVIDENCE"],
    "reject_or_mutation_fixture_ids": ["PROVV10-REJ-PAIR-ORDER-DRIFT", "PROVV10-REJ-POSITION-DRIFT", "PROVV10-REJ-DIAMOND-FALSE-CYCLE", "PROVV10-REJ-DUPLICATE-ROOT-INFLATION", "PROVV10-REJ-REEXPRESSION-EVIDENCE"],
    "evidence_artifact": "ProvenanceFiniteOrderReceiptV1",
    "failure_disposition": "INVALID provenance construction; false diamond rejection is also failure.",
    "claim_withdrawal": "Withdraw grounded-carrier, connected-memory, and connection-specificity clauses."
  },
  {
    "test_id": "M0V4-PROVENANCE-REVOCATION-CYCLE-27",
    "kind": "invariant",
    "required_before": "implementation",
    "acceptance": "Whole-batch structural validation, exact support, contradiction precedence, permanent transitive revocation, transform nonadmission, cycle rejection, corroboration, and atomic commit reproduce every section 3 fixture and rejected batches leave the store byte-identical.",
    "positive_fixture_ids": ["PROVV10-POS-CORROBORATION", "PROVV10-POS-REVOCATION-STATE", "PROVV10-POS-ATOMIC-COMMIT"],
    "reject_or_mutation_fixture_ids": ["PROVV10-REJ-ALIAS-UNKNOWN", "PROVV10-REJ-ALIAS-DUPLICATE-SOURCE", "PROVV10-REJ-ALIAS-SELF-OR-CYCLE", "PROVV10-REJ-PARENT-UNKNOWN", "PROVV10-REJ-PARENT-SELF-SAME-FORWARD", "PROVV10-REJ-COLLAPSED-DAG-CYCLE", "PROVV10-REJ-NONCANONICAL-PARENTS", "PROVV10-REJ-NONCOMPOSABLE-PAIR", "PROVV10-REJ-INCOMPLETE-PRIMITIVE-PARENTS", "PROVV10-REJ-PREMATURE-VALIDATION", "PROVV10-REJ-REUSED-DISCOVERY-ROOT", "PROVV10-REJ-SYNTH-AS-PRIMITIVE", "PROVV10-REJ-SYNTHETIC-ONLY-VALIDATION", "PROVV10-REJ-UNREVOKE", "PROVV10-REJ-TRANSFORM-EVIDENCE", "PROVV10-REJ-BATCH-ATOMICITY"],
    "evidence_artifact": "ProvenanceRevocationCycleReceiptV1",
    "failure_disposition": "INVALID provenance state; an invalid batch must leave the pre-batch store byte-identical.",
    "claim_withdrawal": "Withdraw every carrier-derived and connection-evidence clause."
  },
  {
    "test_id": "M0V4-V7-GUARD-EXCEPTION-NONEXPOSURE-34",
    "kind": "invariant",
    "required_before": "materialization",
    "acceptance": "The exact C10 boundary has only the governance-private custody accesses in section 5 and one candidate/preparation/runtime semantic consumer, V7_BOUNDARY_GUARD; its only downstream output is the exact four-field pass projection with the literal sorted 22-path allowlist; boundary metadata never crosses that projection.",
    "positive_fixture_ids": ["V7V10-POS-BOUNDARY-C10-BINDING", "V7V10-POS-GOVERNANCE-CUSTODY", "V7V10-POS-SOLE-GUARD-CONSUMER", "V7V10-POS-BOUNDARY-PROVENANCE", "V7V10-POS-NONEXPOSURE-TWIN", "V7V10-POS-FAIL-CLOSED"],
    "reject_or_mutation_fixture_ids": ["V7V10-REJ-SECOND-SEMANTIC-CONSUMER", "V7V10-REJ-GOVERNANCE-ACCESS-PROJECTION", "V7V10-REJ-GUARD-OPENS-DENIED", "V7V10-REJ-PROJECTION-PATHSET", "V7V10-REJ-PROJECTION-EXTRA-FIELD", "V7V10-REJ-FAILURE-PROJECTION", "V7V10-REJ-INDIRECT-CHANNEL", "V7V10-REJ-BOUNDARY-COPY", "V7V10-REJ-EMBEDDED-SELF-HASH", "V7V10-REJ-BOUNDARY-PROVENANCE-SOURCE"],
    "evidence_artifact": "V7GuardExceptionNonexposureReceiptV1",
    "failure_disposition": "INVALID before materialization; emit no projection or prepared output.",
    "claim_withdrawal": "Withdraw clean-room status and every scientific clause."
  }
]
```

## 3. Exact provenance semantics and fixture corpus

### 3.1 Finite order, pair order, roots, and support

The unsigned lexicographic coordinate is exactly
`Position=(major:u8,lane:u8,ordinal:u16)`. Lane 0 is the ordinary event at a
major position; lane 1 is its post-event synthesis. Reserved absent positions
never renumber. The authoritative pair registry is exactly:

| ordinal | position | pair |
|---:|---|---|
| 0 | `(24,1,0)` | `(p0,p1)` |
| 1 | `(24,1,1)` | `(p2,p3)` |
| 2 | `(24,1,2)` | `(p1,p4)` |
| 3 | `(24,1,3)` | `(p3,p4)` |
| 4 | `(24,1,4)` | `(p4,p5)` |
| 5 | `(24,1,5)` | `(p4,p6)` |
| 6 | `(41,1,6)` | `(p4,nh)` iff `nh` was admitted |

`FactKey=(src_ordinal,relation_ordinal,dst_ordinal)` and
`PairKey=(FactKey(left),FactKey(right))` use unsigned numeric tuple order.
Public aliases, semantic hashes, paths, goal, score, condition, filesystem
order, and wall time never order evidence. Alias edges must be strictly
decreasing by raw digest and are resolved transitively before node identity,
parent sorting, root calculation, support, contradiction, cycle, or render.

```text
roots(ROOT r)  = {canonical_id(r)}
roots(SYNTH s) = set_union(roots(parent) for parent in parents(s))
roots(ALIAS a) = roots(resolve(a))
```

Root sets contain only canonical primitive ROOT IDs. SYNTH and REEXPRESSION
IDs never become evidence; aliases and sinks never count twice. A shared-root
diamond is legal and root-deduplicated. A `PAIR_PROPOSAL` cites the complete
canonical primitive ROOT set for both endpoint FactKeys at the proposal cut.
Support requires strictly later independent primitive ROOT evidence disjoint
from discovery roots. A REEXPRESSION adds no root and cannot validate or
render a pair. Only SUPPORTED, non-REVOKED PAIR_PROPOSAL nodes render.

### 3.2 Test 26 fixture definitions

| fixture ID | exact required result |
|---|---|
| `PROVV10-POS-OLD-SIX-ORDER` | Old-cut evidence produces exactly ordinals 0--5 at `(24,1,0..5)` and exactly six supported links after positions 25--31 validate their endpoints. |
| `PROVV10-POS-NEW-H0` | Admitted `nh=C-R07->D` produces only ordinal 6 at `(41,1,6)` and renders only after independent p4/nh validations at 42/43. |
| `PROVV10-POS-NEW-H1` | Admitted `nh=C-R08->D` has the same ordinal/position and the same later-support law. |
| `PROVV10-POS-FAILED-COMMIT-ABSENCE` | With no admitted nh ROOT, `(41,1,6)` and validation 43 are reserved but absent and no seventh link exists. |
| `PROVV10-POS-ALIAS-CANONICAL` | Direct and strictly decreasing alias citations collapse to one sorted parent ID and yield identical SYNTH ID, roots, status, and rendering. |
| `PROVV10-POS-SHARED-ROOT-DIAMOND` | For `s0=[r0,r1]`, `s1=[r0,r2]`, and `s2=[s0,s1]`, accept and require `roots(s2)={r0,r1,r2}`; shared `r0` is neither doubled nor a cycle. |
| `PROVV10-POS-SYNTH-NON-EVIDENCE` | REEXPRESSION `x1=[x0]` is accepted structurally, `roots(x1)=roots(x0)`, neither synthetic ID is a root, and x1 alone supports and renders nothing. |
| `PROVV10-REJ-PAIR-ORDER-DRIFT` | Reject any swap, omission, duplicate, or eighth authoritative pair. |
| `PROVV10-REJ-POSITION-DRIFT` | Reject changed major/lane/ordinal, wall-time ordering, renumbering after absence, or nondeterministic tie. |
| `PROVV10-REJ-DIAMOND-FALSE-CYCLE` | The exact legal shared-root diamond must not be rejected as cyclic. |
| `PROVV10-REJ-DUPLICATE-ROOT-INFLATION` | Reject root multisets, alias/sink double count, or repeated shared-root support. |
| `PROVV10-REJ-REEXPRESSION-EVIDENCE` | Reject any support, Link, or TransitionRow obtained from synthetic-only evidence. |

### 3.3 Test 27 fixture definitions and precedence

Whole-batch alias, schema, canonical-ID, parent, position, and cycle checks
complete before support, contradiction, revocation, rendering, or write.
Rejected batches leave the pre-batch store byte-identical. For a structurally
valid batch the exact precedence is:

```text
BATCH_REJECT > REVOKED > SUPPORTED > PENDING/SUPPORT_REJECT
```

A later identical FactKey ROOT is corroboration. A later ROOT with the same
`(src,rel)` and different `dst` permanently revokes every dependent proposal
and transitive SYNTH descendant. Later matching evidence, aliasing,
rerendering, or reproposal cannot un-revoke it.

| fixture ID | exact disposition |
|---|---|
| `PROVV10-POS-CORROBORATION` | Valid commit; later identical FactKey ROOT supplies applicable independent support and creates no conflict. |
| `PROVV10-POS-REVOCATION-STATE` | Valid commit; contradiction makes the pair and all transitive dependents permanently REVOKED and removes rendered rows. |
| `PROVV10-POS-ATOMIC-COMMIT` | A wholly valid multi-object batch commits every canonical object exactly once. |
| `PROVV10-REJ-ALIAS-UNKNOWN` | `BATCH_REJECT`: unknown target. |
| `PROVV10-REJ-ALIAS-DUPLICATE-SOURCE` | `BATCH_REJECT`: one source has two targets. |
| `PROVV10-REJ-ALIAS-SELF-OR-CYCLE` | `BATCH_REJECT`: self, nondecreasing, or cyclic alias edge. |
| `PROVV10-REJ-PARENT-UNKNOWN` | `BATCH_REJECT`: collapsed parent absent. |
| `PROVV10-REJ-PARENT-SELF-SAME-FORWARD` | `BATCH_REJECT`: self, same-position, or later parent. |
| `PROVV10-REJ-COLLAPSED-DAG-CYCLE` | `BATCH_REJECT`: alias collapse exposes a dependency cycle. |
| `PROVV10-REJ-NONCANONICAL-PARENTS` | `BATCH_REJECT`: unresolved, duplicated, unsorted, or ID-mismatched parent array. |
| `PROVV10-REJ-NONCOMPOSABLE-PAIR` | `SUPPORT_REJECT`: `left==right` or `left.dst!=right.src`. |
| `PROVV10-REJ-INCOMPLETE-PRIMITIVE-PARENTS` | `SUPPORT_REJECT`: missing endpoint ROOT, foreign FactKey, or SYNTH substitution. |
| `PROVV10-REJ-PREMATURE-VALIDATION` | `SUPPORT_REJECT`: validation is not strictly later. |
| `PROVV10-REJ-REUSED-DISCOVERY-ROOT` | `SUPPORT_REJECT`: proposal and validation root sets intersect. |
| `PROVV10-REJ-SYNTH-AS-PRIMITIVE` | `BATCH_REJECT`: synthetic node declared primitive. |
| `PROVV10-REJ-SYNTHETIC-ONLY-VALIDATION` | `SUPPORT_REJECT`: no later primitive evidence. |
| `PROVV10-REJ-UNREVOKE` | `VALID_REVOKED`: all attempted restoration leaves the item REVOKED. |
| `PROVV10-REJ-TRANSFORM-EVIDENCE` | `BATCH_REJECT`: transform adds evidence, support, contradiction, revocation, or position. |
| `PROVV10-REJ-BATCH-ATOMICITY` | `BATCH_REJECT`: malformed final object causes zero persistent mutation. |

## 4. Closed C10 resource contract

### 4.1 Types and scoped supersession

In this section:

- `u64` is a JSON integer in `[0,18446744073709551615]`;
- `measure` is `u64` or the literal JSON string `"NA"`;
- `hex64` is a lowercase 64-character hexadecimal JSON string;
- `nfc_string` is a nonempty NFC UTF-8 JSON string without control bytes;
- `condition` is exactly one of the 18 condition strings in section 1;
- `phase` is exactly `PROBE_A`, `PROBE_B`, `UNCERTAINTY_ACQUIRE`, or
  `DELAYED_GOAL`; `mode` is exactly `R`, `B`, or `T`; and
- `split` is exactly `DEV`, `CONFIRMATION`, `RESERVE`, or `SENTINEL`.

For an `ARM` record every identity value is non-`NA` and matches the C10
roster. For the sole `COMMON` record, `root_receipt_id`, `condition`, `phase`,
`mode`, and `split` are each the literal `"__COMMON__"`; every digest remains
`hex64`. All numeric leaves are `measure` unless explicitly typed `u64`.
`0` means applicable and unused. `"NA"` is legal only where the closed
applicability matrix in C10 `resource_roster_v4.json` says the resource class
does not exist; missing is never zero or NA. Arrays are ordered as stated.
Every object is closed recursively: a missing or extra key, duplicate key,
wrong type, unsorted array, duplicate array identity, negative number,
floating point number, exponent notation, or integer outside `u64` rejects.

`ChargedResourceV10` supersedes `ChargedResourceV5` only for the C10 candidate,
C10 tests 24/25, and future receipts derived from those C10 bytes. It does not
rename, modify, reinterpret, validate, or invalidate any V5--V9 artifact. A C10
registry or receipt naming `ChargedResourceV5`, accepting both versions, or
coercing one into the other rejects.

### 4.2 Exact `ChargedResourceV10`

```text
ChargedResourceV10 := {
  schema_version: 10,
  artifact_type: "pcfl_charged_resource_v10",
  identity: {
    record_kind: "ARM" | "COMMON",
    scope_id: hex64,
    root_receipt_id: nfc_string,
    condition: condition | "__COMMON__",
    phase: phase | "__COMMON__",
    mode: mode | "__COMMON__",
    split: split | "__COMMON__",
    model_sha256: hex64,
    tokenizer_sha256: hex64,
    chat_template_sha256: hex64,
    renderer_sha256: hex64,
    parser_sha256: hex64,
    controller_sha256: hex64,
    scorer_sha256: hex64,
    runtime_sha256: hex64,
    device_manifest_sha256: hex64,
    meter_manifest_sha256: hex64,
    cas_object_ledger_sha256: hex64
  },
  opportunity: {
    registered_slots: u64,
    slots_request_emitted: u64,
    slots_not_reached: u64,
    maximum_input_tokens: u64,
    registered_generation_allowance: u64,
    offered_generation_allowance: u64,
    read_opportunities: u64,
    world_action_opportunities: u64,
    terminal_opportunities: u64
  },
  stored: {
    raw_event_bytes: measure,
    atom_bytes: measure,
    link_bytes: measure,
    common_index_bytes: measure,
    rag_index_bytes: measure,
    native_graph_bytes: measure,
    static_context_bytes: measure,
    prompt_source_bytes: measure,
    raw_event_tokens: measure,
    atom_tokens: measure,
    link_tokens: measure,
    static_context_tokens: measure
  },
  build: {
    common_fixture_cpu_ns: measure,
    graph_build_cpu_ns: measure,
    index_build_cpu_ns: measure,
    cache_warmup_cpu_ns: measure,
    render_cpu_ns: measure,
    controller_cpu_ns: measure,
    scorer_cpu_ns: measure,
    common_fixture_peak_rss_bytes: measure,
    graph_build_peak_rss_bytes: measure,
    index_build_peak_rss_bytes: measure,
    cache_warmup_peak_rss_bytes: measure
  },
  reader: {
    invocations: measure,
    found_returns: measure,
    not_found_returns: measure,
    blocked_returns: measure,
    candidate_rows_examined: measure,
    postings_touched: measure,
    documents_returned: measure,
    atom_records_returned: measure,
    link_records_returned: measure,
    return_utf8_bytes: measure,
    return_tokens: measure,
    reader_cpu_ns: measure
  },
  thinker: {
    calls_attempted: u64,
    calls_completed: u64,
    calls_failed: u64,
    input_tokens: u64,
    input_system_tokens: u64,
    input_protocol_tokens: u64,
    input_state_tokens: u64,
    input_static_context_tokens: u64,
    input_reader_return_tokens: u64,
    input_prior_scratch_tokens: u64,
    input_other_tokens: u64,
    generated_tokens: u64,
    decoded_utf8_bytes: u64,
    service_latency_ns: u64,
    arm_wall_span_ns: u64,
    gpu_device_charges: [{
      physical_device_uuid: nfc_string,
      active_ns: u64,
      peak_memory_bytes: u64
    }, ...],
    peak_worker_rss_bytes: u64
  },
  behavior_work: {
    successful_world_actions: u64,
    no_effect_world_actions: u64,
    other_unsuccessful_world_actions: u64,
    total_world_actions: u64,
    terminal_commands: u64,
    controller_tool_operations: u64
  },
  artifacts: {
    request_bytes: u64,
    response_bytes: u64,
    tool_return_bytes: u64,
    trace_bytes: u64,
    receipt_bytes: u64,
    log_bytes: u64,
    other_installed_bytes: u64,
    temporary_bytes_written: u64,
    temporary_bytes_deleted: u64,
    standalone_cas_object_count: u64,
    standalone_cas_bytes: u64
  },
  external: {
    network_requests: u64,
    network_rx_bytes: u64,
    network_tx_bytes: u64,
    external_cost_microusd: u64
  }
}
```

`scope_id` is the SHA-256 identity of the canonical tuple
`(record_kind,root_receipt_id,condition,phase,mode,split)` encoded by the C10
schema. `gpu_device_charges` is bytewise sorted by UUID and has at most one
entry per physical device. In the frozen local assay all three network fields
and `external_cost_microusd` are exactly zero; any nonzero value invalidates
the proposal rather than recording an allowed resource.

### 4.3 Exact component laws

The following equalities are noncompensatory:

```text
slots_request_emitted + slots_not_reached = registered_slots

calls_completed + calls_failed = calls_attempted

found_returns + not_found_returns + blocked_returns = invocations

input_tokens = input_system_tokens + input_protocol_tokens
             + input_state_tokens + input_static_context_tokens
             + input_reader_return_tokens + input_prior_scratch_tokens
             + input_other_tokens

total_world_actions = successful_world_actions
                    + no_effect_world_actions
                    + other_unsuccessful_world_actions
```

Registered allowance includes sealed `NOT_REACHED`; offered and actual
counters do not. Static content is charged once as resident storage and again
in `input_static_context_tokens` on every emitted request containing it. RAG
charges raw documents, index bytes, index build, cache warmup, query CPU,
candidate rows, postings, returned documents/envelopes/tokens, and every later
request that contains a return. Common readers charge found/null/blocked
invocations, fixed envelopes, serialization, hashing, returned records, and
reader CPU. Every attempted, failed, tape, retry, and sentinel thinker call is
metered; no retry is thereby authorized.

Actual counts, bytes, CPU, latency, GPU, memory, and artifacts remain measured
outcomes. Sums reduce by sum, peaks by `max`, wall span by
`max(end)-min(start)`, and physical GPU hours by
`sum(active_ns)/3,600,000,000,000`. No A40-equivalent conversion, imputation,
or scalar efficiency score exists.

### 4.4 Standalone and physical CAS

`CasObjectChargeV10` is a closed ledger row:

```text
{
  sha256: hex64,
  nbytes: u64,
  category: "RAW_EVENT" | "ATOM" | "LINK" | "COMMON_INDEX" |
            "RAG_INDEX" | "NATIVE_GRAPH" | "STATIC_CONTEXT" |
            "PROMPT_SOURCE" | "REQUEST" | "RESPONSE" | "TOOL_RETURN" |
            "TRACE" | "RECEIPT" | "LOG" | "OTHER_INSTALLED" | "TEMPORARY",
  owner_scope_id: hex64,
  reachable_scope_ids: [hex64, ...]
}
```

Rows are sorted by `(sha256,category,owner_scope_id)` and
`reachable_scope_ids` is bytewise sorted and duplicate-free. Same bytes under
two digests or different bytes under one digest reject.

For arm scope `a` and a reduction scope `S`:

```text
Closure(a) = distinct ledger digests whose reachable_scope_ids contains a
standalone_cas_bytes(a) = sum(nbytes(o) for o in Closure(a))
physical_cas_bytes(S) = sum(nbytes(o) for o in union(Closure(a) for a in S))
```

An object counts fully for every standalone arm that needs it, never a
fraction. Physical storage counts its digest once. Common preparation is
recorded once in `COMMON`; each standalone arm reports `COMMON + arm-specific`
work, while a suite-physical reduction reports `COMMON once + arm-specific`
work. Reduction receipts are distinct artifacts, state scope membership
explicitly, and report `physical_cas_object_count` and `physical_cas_bytes`;
they are not per-arm `ChargedResourceV10` records.

`RESOURCEV10-POS-CAS-STANDALONE-PHYSICAL` has common objects of 10 and 20
bytes, A-only 7 bytes, and B-only 11 bytes. It requires:

```text
standalone(A) = 37
standalone(B) = 41
physical(A union B) = 48
```

`78`, `22`, fractional sharing, or omission is invalid.

### 4.5 Raw meter events and post-origin causal descendants

Every measured contribution has exactly one closed raw row:

```text
ResourceMeterEventV10 := {
  schema_version: 10,
  artifact_type: "pcfl_resource_meter_event_v10",
  event_id: hex64,
  event_kind: "BUILD" | "STORE" | "READ" | "RENDER" | "THINKER" |
              "WORLD_ACTION" | "ARTIFACT_WRITE" | "ARTIFACT_DELETE" |
              "NETWORK" | "EXTERNAL_COST",
  charge_scope_id: hex64,
  originating_scope_id: hex64,
  slot_id: nfc_string | "NA",
  causal_parent_event_ids: [hex64, ...],
  metric_json_pointer: nfc_string,
  amount: u64,
  unit: "COUNT" | "BYTE" | "TOKEN" | "NANOSECOND" | "MICROUSD",
  source_receipt_sha256: hex64
}
```

Objects are closed; parent IDs are bytewise sorted and duplicate-free;
`metric_json_pointer` names exactly one numeric leaf in the applicable
`ChargedResourceV10` or common receipt. `event_id` hashes the canonical row
with `event_id` omitted. A row maps to exactly one leaf and one charge scope.
Every leaf equals the exact reduction of all and only its mapped rows.

Resource and evidence provenance are not interchangeable. A datum may descend
from an earlier O41/O42/O43 evidence event, but each later build, storage,
reader, render, request-token, model, action, or artifact operation is a new
meter event charged where that operation executes. Thus every D baseline use
of an outcome descendant charges its D arm's static/index/reader/render/input
work; it is not back-charged to AUTH U, hidden in `COMMON`, or assigned to the
content's provenance root. Conversely, actual common construction remains
owned once by `COMMON`; standalone closure includes it fully and physical
reduction includes it once. A descendant never erases, moves, or substitutes
for its origin event, and a causal edge never supplies a free charge.

`RESOURCEV10-POS-POST-ORIGIN-DESCENDANT` fixes one common 100-byte descendant,
one D-arm 20-ns retrieval, one 40-byte return, and two later requests each
containing 12 return tokens. Require common stored bytes 100; D reader CPU 20;
D return bytes 40; D reader-return input tokens 24; and no corresponding
charge in the originating U arm. `RESOURCEV10-REJ-CAUSAL-REALLOCATION`
independently moves each contribution to origin, COMMON, another arm, or no
arm and must reject.

### 4.6 Remaining resource fixtures

- `RESOURCEV10-POS-CLOSED-SCHEMA`: all exact keys/types and no extras pass.
- `RESOURCEV10-POS-FULL-VECTOR-ZERO-NA`: legitimate zero and matrix-authorized
  NA remain distinct from missing.
- `RESOURCEV10-POS-STATIC-REPEATED`: 100 stored static tokens in three emitted
  requests gives 100 stored and 300 input-static tokens.
- `RESOURCEV10-POS-RAG-WORK`: nonzero build, warmup, query, candidates,
  postings, four-document return, return-token, later-input, and artifact
  leaves reconcile.
- `RESOURCEV10-POS-BLOCKED-READER`: one blocked call has one invocation, fixed
  return bytes/tokens, and zero candidate rows/postings.
- `RESOURCEV10-POS-NOT-REACHED`: registered ceilings include an unissued
  suffix; offered and actual counters exclude it.
- `RESOURCEV10-POS-COMPONENT-REDUCTION`: sums, maxima, wall interval, CAS
  union, and physical-device GPU conversion reproduce their goldens.
- `RESOURCEV10-POS-METER-CAPABILITY-CLOSURE`: the capability manifest names
  every process, thread, subprocess, file/CAS, index/cache, reader, model,
  device, network, and artifact-write path and no other path is reachable.
- `RESOURCEV10-POS-METER-LEAF-RECONCILIATION`: every vector numeric leaf
  equals its raw rows exactly once.
- `RESOURCEV10-POS-CAUSAL-SCOPE-RECONCILIATION`: every post-origin descendant
  retains its causal parents and charges its actual execution scope.

The negative fixtures are individual and noncompensatory:

- `RESOURCEV10-REJ-V5-SCHEMA-NAME` substitutes `ChargedResourceV5`, a dual
  version, or a compatibility coercion; reject.
- `RESOURCEV10-REJ-MISSING-FIELD`, `RESOURCEV10-REJ-EXTRA-FIELD`, and
  `RESOURCEV10-REJ-WRONG-TYPE` independently delete, add, or mistype one leaf
  at every object depth; every case rejects.
- `RESOURCEV10-REJ-ZERO-NA-MISSING` independently substitutes each member of
  the three-way distinction for another; reject.
- `RESOURCEV10-REJ-STATIC-ONCE-ONLY` charges resident static storage but omits
  one or more emitted-request static token segments; reject.
- `RESOURCEV10-REJ-RAG-BUILD-OR-POSTINGS-FREE` independently omits document
  storage, index build, warmup, query, candidates, postings, return, or
  downstream return-token input; reject each case.
- `RESOURCEV10-REJ-COMMON-READER-FREE` omits a found/null/blocked invocation,
  fixed envelope, serialization, record, hashing, or CPU contribution; reject.
- `RESOURCEV10-REJ-HIDDEN-THINKER-CALL` omits a background, retry, sentinel,
  failed, tape, or ordinary attempt; reject.
- `RESOURCEV10-REJ-CAS-DIVIDED-STANDALONE` fractionally allocates or omits a
  shared object from an arm closure; reject.
- `RESOURCEV10-REJ-CAS-SUMMED-PHYSICAL` sums standalone closures instead of
  taking the digest union; reject.
- `RESOURCEV10-REJ-CAS-DIGEST-ALIAS` admits identical bytes under two digests
  or different bytes under one digest; reject.
- `RESOURCEV10-REJ-DELETED-TEMP-FREE` deletes a written request, response,
  index, cache, trace, log, or other temporary object without both counters;
  reject.
- `RESOURCEV10-REJ-CPU-WARMUP-FREE` omits common preparation, graph/index
  construction, tokenizer/model warmup, or cache priming; reject.
- `RESOURCEV10-REJ-GPU-UNATTRIBUTABLE` lacks a unique physical-device UUID,
  active-ns owner, or separable concurrency boundary; reject.
- `RESOURCEV10-REJ-MEMORY-UNATTRIBUTABLE` lacks a resettable per-arm host or
  device peak boundary; reject.
- `RESOURCEV10-REJ-SEGMENT-SUM` changes any input segment or total so the exact
  equality fails; reject.
- `RESOURCEV10-REJ-REGISTERED-ACTUAL-CONFLATION` substitutes registered,
  offered, emitted, or actual call/token counters for one another; reject.
- `RESOURCEV10-REJ-NETWORK-OR-COST` admits a provider/network edge, network
  byte/request, or nonzero external cost; reject.
- `RESOURCEV10-REJ-CAUSAL-REALLOCATION` performs any post-origin move described
  in section 4.5; reject.

Unattributable concurrency invalidates resource evidence; it is never imputed.

## 5. Exact C10 boundary, governance custody, and noncircular provenance

### 5.1 Plan binding

The future C10 plan at `PLAN_PATH` must contain exactly one nonmember manifest
output at `MANIFEST_PATH` and exactly 23 `manifest_member:true` source rows.
Their basenames, roles, media types, and byte ceilings equal the ratified V9
plan after changing only the change-directory component from `_v9` to `_v10`.
Exactly one member has `role:"V7_BOUNDARY"`, schema `V7BoundaryV1`, maximum
65,536 bytes, and `logical_path=BOUNDARY_PATH`. No second boundary, alias,
symlink-equivalent path, wildcard, directory grant, or unlisted output exists.

The C10 plan has the additional closed field below. Its array has exactly one
row and no extra row or row field:

```text
governance_inputs: [{
  role: "V10_NORMATIVE_DENIAL_CORPUS",
  logical_path: DENIAL_CORPUS_PATH,
  media_type: "application/json",
  sha256: hex64,
  access: "GOVERNANCE_ONLY"
}]
```

The valid C10 `SourceAuthoringGrantV1` and later
`PreparationExecutionGrantV1` each bind the complete C10 plan hash, thereby
binding this singleton path and digest; the human-required state binds the
same plan and corpus digest. The governance input is not an authored source
entry, manifest member, runtime input, or output. The corpus bytes must be
separately human-ratified under the
V10 human-required state before Authority S. It is a closed canonical JSON
object whose seven arrays are the exact denial classes: resolved paths;
module/package/reflection/subprocess identities; whole-artifact digests;
forbidden declared-provenance identities; distinctive interfaces; reachable
capabilities; and actor/model exposure identities. Values are bytewise sorted
and duplicate-free. It contains no positive PCFL semantic value, answer,
score, expected output, carrier content, or model-visible field.

### 5.2 Access classes and ordering

There are exactly three relevant machine principals:

1. `AUTHORITY_S_SOURCE_WRITER_HASHER` is governance-private and exists only
   under the valid C10 source-authoring grant. It may read the grant, plan,
   bound V10 normative sources, and denial corpus; create or edit exactly the
   23 source paths; compute their SHA-256 and byte lengths; and write the
   nonauthoritative external manifest. It may not import, execute, syntax
   check, prepare, materialize, run a checker, generate fixtures/data/roots,
   open any denied external path, or emit any preparation/runtime projection.
2. `INDEPENDENT_EXACT_BYTE_REVIEWER` is read-only, governance-private, and
   independent of the writer and guard. After Authority S closes, it may read
   and rehash the grant, plan, corpus, all 23 exact member bytes, every
   external provenance row, and the manifest for exact-byte human review. It
   may produce only a governance-private review artifact. It may not edit,
   import, execute, prepare, derive expected scientific values, or emit a
   candidate/preparation/runtime projection.
3. `V7_BOUNDARY_GUARD` is, after exact-byte ratification and only under a
   later exact human `PreparationExecutionGrantV1`, its first validation
   substage and the sole **candidate/preparation/runtime semantic consumer**
   permitted to parse `BOUNDARY_PATH`. It may read the
   ratified denial corpus, external manifest/provenance rows, the other 22
   candidate members as inert bytes, and proposed PCFL
   read/import/capability manifests. It compares registered metadata only. It
   never resolves, opens, imports, hashes, or executes a denied target and
   never learns a PCFL expected value from the boundary or corpus.

Writer/hasher and independent reviewer access are byte-custody acts in the
governance/source-authoring plane, not candidate semantic consumers and not
exceptions available to preparation, checker, materializer, runtime, model,
or science. The guard remains the only semantic boundary consumer in those
planes. Any other access or any downstream influence from the first two
principals rejects.

The exact order is: ratified corpus and C10 source-authoring grant; Authority-S
write/hash; external manifest close; independent exact-byte review; human
ratification of the exact candidate bytes and manifest; a separate exact human
`PreparationExecutionGrantV1`; guard as the grant's first validation substage;
pass projection if and only if the guard passes; then and only then the later
substages of that same preparation grant. Guard passage does not issue,
expand, or replace the grant that authorized it. No step implies or creates
the authority of the next. The guard is substage zero of the one exact
preparation attempt. Failure consumes that attempt, yields no projection, and
permits no retry or reserve substitution; this governance failure adds no
scientific call, slot, or token allowance.

### 5.3 External provenance and boundary-only governance source

No member embeds a provenance row containing its own digest. After a member's
bytes are closed and hashed, `MANIFEST_PATH` stores exactly one external
`SourceProvenanceRowV1[C10]` for it. The manifest is not a member and its own hash
is bound later by review/state artifacts, so the graph is noncircular.

Every one of the 23 external rows has nonempty, duplicate-free, bytewise tuple
sorted `derivation_sources` and at least one entry whose
`kind="PCFL_V10_NORMATIVE"`. Language-standard or standard-library sources
may be additional entries but never replace that minimum. All
`PCFL_V10_NORMATIVE` paths and hashes are non-null, rehash exact V10 normative
bytes bound by the human-required state, and carry a stable clause identifier.
All rows state `v7_runtime_derivation:false` and
`v7_oracle_derivation:false`.

The boundary is the only row to which the following closed boundary-specific
cross-field rule applies. It remains a `SourceProvenanceRowV1[C10]` and is
exactly:

```text
{
  schema_version: 1,
  artifact_type: "pcfl_m0_source_provenance",
  logical_path: BOUNDARY_PATH,
  source_sha256: hex64,
  authored_for_change_id: C10,
  source_authoring_grant_sha256: hex64,
  derivation_sources: [{
    kind: "PCFL_V10_NORMATIVE",
    identifier: "V10-NORMATIVE-DENIAL-CORPUS",
    path: DENIAL_CORPUS_PATH,
    sha256: hex64
  }],
  v7_runtime_derivation: false,
  v7_oracle_derivation: false,
  author_attestation: "authored only from the listed V10 normative/language sources under SourceAuthoringGrantV1 sha256=<G>; no V7 runtime/oracle derivation and no import, checking, or execution occurred"
}
```

The `derivation_sources` array has exactly that one entry; its digest equals
the plan-bound and grant-bound corpus digest. `source_sha256` hashes the
already closed boundary bytes, not a container holding this row. The corpus
is classified `PCFL_V10_NORMATIVE` because it is the newly human-ratified V10
negative governance specification; this does not declare any V7 runtime or
oracle as a derivation source. In the attestation, `<G>` is replaced by the
lowercase `source_authoring_grant_sha256`, exactly as for every other V1 row.
Copying from, opening, hashing, importing, or
executing a denied path/artifact instead of authoring from the corpus rejects.

Actual denied values may occur only in the governance-private corpus,
`BOUNDARY_PATH`, and governance-private review/guard evidence. Other source
members may use generic vocabulary such as `V7_BOUNDARY`, test IDs, schema
field names, array indices, and `passed`, but cannot repeat an actual denied
value. External ordinary provenance rows contain V10 normative references,
not copied V7 identities.

## 6. Exact guard projection and nonexposure

The guard's successful projection is the closed object:

```text
V7GuardProjectionV1 := {
  schema_version: 1,
  artifact_type: "pcfl_v7_guard_projection",
  passed: true,
  pcfl_read_allowlist: [
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/acceptance_tests.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/cas_freeze_contract_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/check_axiomatic_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/check_constructive_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/claim_disposition_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/delayed_twin_entitlement_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/endpoint_gate_registry_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/failure_precedence_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/handoff_consumer_graph_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/handoff_projection_allowlist_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/handoff_public_v4.schema.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/integrated_contract.md",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/materialize_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/mtext_handoff_v4.schema.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/mutation_fixtures.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/object_schemas_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/prepare_v4.py",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/provenance_contract_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/resource_roster_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/runtime_manifest_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/semantic_table_v4.json",
    "research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v10/source/transition_table_v4.json"
  ]
}
```

The array is the bytewise UTF-8 sort of exactly the 22 non-boundary
`manifest_member:true` C10 plan paths. Equality is literal: no missing,
additional, reordered, normalized, relative-to-cwd, alias, symlink, URI,
directory, or glob entry is accepted. `BOUNDARY_PATH`, `MANIFEST_PATH`,
`DENIAL_CORPUS_PATH`, `PLAN_PATH`, and every directory are excluded. The
manifest, plan, provenance, corpus, and detailed guard receipt remain
governance-private prerequisites; their omission from the projection does not
make them preparation-readable.

The projection has exactly four fields and no boundary path/digest, denied
value, V7/V5 identifier, module/interface name, violation detail, provenance
row, manifest hash, corpus hash, expected value, timing, or error. Failure
produces no projection. A governance-only result may say
`SOURCE_BOUNDARY_REJECTED`, but neither that string nor its details enters a
preparation/runtime/public artifact.

For two clean boundary/corpus governance inputs whose metadata differs but
whose guard decision and exact 22-path allowlist are equal, the pass
projection and every possible downstream semantic, actor, model, cache,
index, filename, error, length, ordering, padding, timing, receipt, and claim
byte are identical. If a mutation changes pass to fail, the sole allowed
downstream effect is absence of the projection.

## 7. Exact V7 fixture semantics

- `V7V10-POS-CLEAN-PCFL`: all 22 projected members pass the seven predicates
  and each external provenance row has at least one bound
  `PCFL_V10_NORMATIVE` source.
- `V7V10-POS-COINCIDENT-SCALAR`: independently derive `0,1,4,8,16` from
  bound V10 normative/language rules without a denial predicate; pass.
- `V7V10-POS-BOUNDARY-C10-BINDING`: exactly one C10 boundary plan row exists
  at `BOUNDARY_PATH` with the exact role/schema/ceiling.
- `V7V10-POS-GOVERNANCE-CUSTODY`: only the writer/hasher and independent
  reviewer perform their ordered, governance-private byte accesses; neither
  creates a downstream semantic projection.
- `V7V10-POS-SOLE-GUARD-CONSUMER`: after custody/review, the boundary has
  exactly one candidate/preparation/runtime semantic edge, to the guard.
- `V7V10-POS-BOUNDARY-PROVENANCE`: the external boundary row and bound corpus
  reproduce section 5 exactly without self-reference.
- `V7V10-POS-NONEXPOSURE-TWIN`: private metadata twins with equal pass and
  pathset yield identical projection and synthetic downstream bytes.
- `V7V10-POS-FAIL-CLOSED`: one denied edge changes pass to fail and yields no
  projection or preparation-visible object.

The seven test-01 rejection fixtures use boundary-array indices rather than
copying actual values. They separately cover resolved path/symlink escape;
module/package/reflection/plugin/subprocess access; whole artifact or embedded
whole copy; declared denied provenance; distinctive interface as dependency,
oracle, fixture, or answer source; reachable file/environment/argv/cwd/
deserialization/network capability; and any actor/model/cache/error/timing/
scientific-receipt exposure.

The test-34 mutations have these exact results:

- `V7V10-REJ-SECOND-SEMANTIC-CONSUMER`: any preparation, materializer,
  checker, fixture bank, runtime, renderer, parser, scorer, reducer, model,
  session, cache, or scientific receipt reads the boundary or corpus; reject.
- `V7V10-REJ-GOVERNANCE-ACCESS-PROJECTION`: writer/reviewer emits or changes
  any candidate/preparation/runtime/public byte; reject.
- `V7V10-REJ-GUARD-OPENS-DENIED`: guard resolves, opens, hashes, imports, or
  executes a denied target rather than comparing metadata; reject.
- `V7V10-REJ-PROJECTION-PATHSET`: omit/add/reorder a path; admit boundary,
  manifest, plan, corpus, directory, glob, alias, or symlink; reject.
- `V7V10-REJ-PROJECTION-EXTRA-FIELD`: any fifth field or forbidden metadata;
  reject.
- `V7V10-REJ-FAILURE-PROJECTION`: failed guard emits any object or partial
  allowlist; reject.
- `V7V10-REJ-INDIRECT-CHANNEL`: private metadata changes any semantic/public/
  rendered/cache/index/error/timing/claim byte at equal pass/pathset; reject.
- `V7V10-REJ-BOUNDARY-COPY`: another member repeats an actual denied value;
  reject.
- `V7V10-REJ-EMBEDDED-SELF-HASH`: a member embeds the provenance row carrying
  its own digest or the manifest/member graph is cyclic; reject.
- `V7V10-REJ-BOUNDARY-PROVENANCE-SOURCE`: missing normative source, extra
  derivation entry, wrong corpus path/hash, V7 runtime/oracle derivation, or
  denied target used instead of the corpus; reject.

Tests 01 and 34 both must pass. Test 01 owns universal denial outside the
boundary; test 34 alone owns the exact guard exception, custody, pathset, and
nonexposure. Neither receipt substitutes for the other.

## 8. Resolution and claim boundary

| V9 item | exact v2 closure |
|---|---|
| `D-V9-PROVENANCE-POSITIVES` | exact positions/seven pairs; post-alias canonical roots; legal shared-root diamond; SYNTH/re-expression non-evidence; explicit positive/reject fixtures; contradiction, permanent revocation, cycle, transform, and batch atomicity |
| `D-V9-RESOURCE-FACTORIAL` | exact 18/501 roster and 16/32/16 split; active totals; closed versioned vector/types; extra-field rejection; standalone/physical CAS; raw meter and causal-descendant attribution; separate tests 23/24/25 |
| `D-V9-V7-GUARD-EXCEPTION` | exact C10 plan/boundary; governance custody distinct from semantic consumption; noncircular external provenance; mandatory V10 normative derivation; literal 22-path projection; fail-with-no-projection; direct and indirect nonexposure; separate tests 01/34 |

These are source, conformance, and governance selections only. They add no
condition, phase, root, model call, token, endpoint, mechanism, or claim. Even
future passage would not support DREAM authorship, SLEEP, LoRA transport,
learning, retention, self-written memory, parenting, compression,
generalization, lifetime improvement, scalar efficiency, or the complete
organism.
