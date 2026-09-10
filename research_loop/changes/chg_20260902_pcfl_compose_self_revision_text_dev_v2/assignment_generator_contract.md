# v2 total assignment-manifest generator contract

This contract is proposal-only. It freezes every scientific algorithm and
semantic choice of the deterministic generator that a separately ratified
implementation and Stage 0 must realize; it does not assert that implementation
or executable bytes exist, generate roots, consume CPU, or authorize a call
now. After implementation, a newly rehashed and independently reviewed pre-GPU
executable snapshot must bind the generator/JCS source and binary hashes without
changing any choice below. Output is one RFC8785-JCS
`PCFL_V2_ASSIGNMENT_MANIFEST` validated by
`assignment_manifest.schema.json`, hashed before any model call, and immutable
thereafter.

## Source commitment and deterministic choices

The future hash-bound generator receives exactly: the 32-octet sealed root secret and commitment
defined in `rng_contract.json`; the hash-bound 64 factor and 64 independent
candidate certificates; hashes of this contract, the schema, RNG contract,
runtime envelope, prompts, typed protocol contracts, and accepted pre-GPU
executable snapshot; and no model output, target result, timing, cache, or
reviewer choice. This input list freezes semantics now but is not evidence that
any future hash or executable receipt already exists.

Candidate certificates are sorted by `(family, certificate_id)` using UTF-8
byte order. For each certificate compute
`HMAC-SHA256(root_secret, JCS({domain:"pcfl-compose-v2/root-rank/v1",
family,certificate_id}))`; sort by the 32 digest octets, breaking an impossible
digest tie by `certificate_id`. The first two factor certificates become
`pcfl-open-factor-0000` and `pcfl-untouched-factor-0000` in that order; the
first independent certificate becomes `pcfl-independent-0000`. A duplicate
certificate, digest tie without a unique certificate-ID tie-break, missing
certificate, or rejected certificate returns `GENERATOR_NOT_RUN`; selection
is never retried.

For each registered root, derive sampled `z` as the low four bits of the
unsigned big-endian first eight octets of
`HMAC-SHA256(root_secret, JCS({domain:"pcfl-compose-v2/z/v1",root_id}))`.
Render it as a four-character MSB-first binary string. `ANTIPODE` is bitwise
XOR with `1111`. The ordinary continuation is literally `h=0` for factor and
`q=0` for independent. Target candidates are the finite set certified by the
bound construct. Rank them with the same method under domain
`pcfl-compose-v2/target-rank/v1` and fields `(root_id,z_side,h_or_q,
target_kind,candidate_id)`; choose the lowest digest once. Goal twins are the
two exact goal renderings emitted by the bound goal-twin constructor, ordered
by twin bit 0 then 1. Target IDs and packets freeze in the private manifest at
T0 and do not render to Dream/Sleep before T3.

At T0 the arbitrary opaque sham assignments, constructor bytes, seed rule,
allowed future input projection, and failure consequence freeze into the
manifest; exact sham bytes cannot yet exist. After the selected authentic
corpus freezes at T2, and before any T3 target packet or query is rendered, the
constructor in `experiment_spec.md` consumes only its permitted pre-target
footprint and emits an append-only receipt bound to those preassigned rows.
`SHAM_EXHAUSTED` retains every affected assignment with endpoint zero and
permits no alternate sham.

## Canonical expansion order

Within every loop, enum order is literal: stage; table row below; root order as
listed above; `z_side=[SAMPLED,ANTIPODE]`; continuation bit `[0,1]`;
condition in table order; `goal_twin=[0,1]`; phase order; resolver ordinal
ascending. Null-valued factors remain explicit JSON nulls. Stage-1 call IDs are
`s1-call-0001` through `s1-call-0910`; Stage-2 IDs are
`s2-call-0001` through `s2-call-2504`. `call_index` is 1..3414 across those two
ranges. No output-dependent branch can change the arrays.

Session topologies are exact call-opportunity arrays:

| topology | expansion |
|---|---|
| `DREAM1_32` | resolver ordinals 0..31 |
| `DREAM2_16` | resolver ordinals 0..15 |
| `THINK_D1_10` | resolver ordinals 0..9 for one goal twin |
| `THINK_D4_31` | resolver ordinals 0..30 for one goal twin |
| `ONE_SHOT_DREAM1_1` | ordinal 0 |
| `ONE_SHOT_DREAM2_1` | ordinal 0 |
| `ONE_SHOT_THINK_D4_1` | ordinal 0 |

`resolver_ordinal` is always zero-based assignment/RNG topology. The
model-visible `operation_ordinal` is always one-based and is exactly
`resolver_ordinal + 1`; thus the ranges above render respectively as 1..32,
1..16, 1..10, 1..31, and 1 for every one-shot topology. Resolver state before
the first response may carry completed-operation count 0, but no input envelope
or model output may call that value the first `operation_ordinal`. Any offset,
phase-global ordinal, 0-valued model operation, or 1-valued first resolver
ordinal is a generator/pre-render failure.

An ordinary recurrent Dream life is `32+16=48`; a shared Dream-1 two-
continuation fork is `32+16+16=64`; an iterative D1+D4 two-goal-twin life is
`2*(10+31)=82`; D4 twins are `2*31=62`; a one-shot Dream phase pair is 2; and
a structured one-shot plan is 1. Each opportunity remains present even when
its runtime outcome becomes not invoked or failed; outcome fields are stored
orthogonally and never delete a manifest row.

## Complete cell expansion

| order | sealed cell | exact expansion | Dream | recurrent Think | one-shot Think |
|---:|---|---|---:|---:|---:|
| 1 | S1 open opaque SELF fork | 2 z x `(DREAM1_32 + 2 h x DREAM2_16 + 2 h x 2 twins x (THINK_D1_10+THINK_D4_31))` | 128 | 328 | 0 |
| 2 | S1 oracle | open root, h=0, sampled z, 2 twins x `(THINK_D1_10+THINK_D4_31)` | 0 | 82 | 0 |
| 3 | S1 selected-h EMPTY | open root, h=0, 2 z x 2 twins x `THINK_D4_31` | 0 | 124 | 0 |
| 4 | S1 selected-h CROSSED | same keys as row 3 | 0 | 124 | 0 |
| 5 | S1 selected-h SHAM | same keys as row 3 | 0 | 124 | 0 |
| 6 | S2 untouched factor opaque SELF fork | same expansion as row 1 on untouched root | 128 | 328 | 0 |
| 7 | S2 independent opaque SELF q fork | same expansion as row 1 with q on independent root | 128 | 328 | 0 |
| 8 | S2 factor EMPTY then OBSERVED | untouched root, 2 conditions x 2 h x 2 z x 2 twins x `THINK_D4_31` | 0 | 496 | 0 |
| 9 | S2 independent EMPTY then OBSERVED | independent root, 2 conditions x 2 q x 2 z x 2 twins x `THINK_D4_31` | 0 | 496 | 0 |
| 10 | S2 AST diagnostic | factor h=0 sampled life then independent q=0 sampled life; each `DREAM1_32+DREAM2_16+2 twins x THINK_D4_31` | 96 | 124 | 0 |
| 11 | S2 one-shot Dream diagnostic | same two selected lives; each `ONE_SHOT_DREAM1_1+ONE_SHOT_DREAM2_1+2 twins x THINK_D4_31` | 4 | 124 | 0 |
| 12 | S2 structured one-shot Think | factor h=0 sampled then independent q=0 sampled; 2 twins x `ONE_SHOT_THINK_D4_1` | 0 | 0 | 4 |
| 13 | S2 selected-h CROSSED then SHAM | untouched factor root, 2 conditions x h=0 x 2 z x 2 twins x `THINK_D4_31` | 0 | 248 | 0 |
|  | **total** |  | **484** | **2,926** | **4** |

Rows 1–5 are exactly `128 Dream + 782 recurrent Think = 910`. Rows 6–13 are
exactly `356 Dream + 2,144 recurrent Think + 4 structured-only one-shot Think
= 2,504`. The complete scientific opportunity array is exactly 3,414.

The only structured one-shot assignments are, literally, the sampled-z AST
D4 packet for: untouched factor `h=0`, twin 0; the same twin 1; independent
`q=0`, twin 0; and the same twin 1. Each is
`ANALYSIS_PAIR_ONLY` with its iterative AST row and therefore has a distinct
random coupling group. No antipode, other continuation, or opaque one-shot
Think row can be generated.

## Coupling, IDs, gate bindings, and endpoints

Every assignment ID is the ASCII join of the prefix `asgn`, stage, cell order,
root ID, z side, continuation name/value or `none`, lane, condition, target
kind/ID or `none`, and goal twin or `none`, separated by `:`. Row ID replaces
the prefix by `row`. Session ID replaces it by `session` and adds topology.
Before serialization every component must match the schema ID grammar; a
collision is fatal.

The dedicated `rng_contract.json` namespace `model_visible_identifier` is the
sole constructor for every model-visible receipt reference, D1-candidate
handle, candidate-read capability, target-memory handle, target-reader
receipt, and recurrent authored-node/staged-object capability. Its closed
`session_scope` is constructed directly from the row/session values
`{goal_twin,operation_topology,phase_role,root_id,sampling_lane,target_id,z_side}`
with all seven members present and semantic absence represented by JSON null.
The generator and renderer must never substitute descriptive `lane`,
condition, h/q, variant/cut, assignment/call ID, payload identity, digest,
path, or length. It assigns `source_ordinal`, `issue_ordinal`,
`resolver_ordinal`, and `issuance_role` exactly as that namespace specifies.

Candidate handles are derived lazily at the fresh D2 boundary from committed
D1 pool positions 0 then 1; the D1 bytes were cloned, so corresponding h/q D2
sessions receive byte-identical handle count/order/value. The target-memory
handle is source/issue ordinal 0 and is byte-identical across corresponding
SELF/EMPTY/OBSERVED/CROSSED/SHAM sessions. Public-event, raw-A, candidate, and
reader receipt references and read-minted capabilities follow their charged
read/source/resolver tuple. Authored node/object capabilities follow accepted
mint order and the exact NOTICE/CONNECT/REVISE/PREDICT issuance role. Therefore
a common topology prefix is byte-identical across treatment clones, while a
later difference in operation role, resolver position, source slot, or number
of prior mints follows each branch's natural zero-based tuple. Payload or query
content alone cannot change an identifier. A distinct-message collision is
fatal and is never redrawn.

For `COMMON_SEED`, coupling-group ID replaces treatment-varying descriptive
lane/condition/cut components with the literal `COMMON` and retains exactly
the seed-key fields in `rng_contract.json`. Each call separately records
`sampling_lane`: all opaque recurrent target-time SELF/EMPTY/OBSERVED/CROSSED/
SHAM rows use `OPAQUE_TARGET_THINK`, while descriptive `lane` remains treatment
metadata outside the seed key. All treatment fields stay in the call row for
audit but never enter `seed_key`. Topology-mismatched diagnostics are
`ANALYSIS_PAIR_ONLY` and receive distinct group IDs. Every generated model
call has `replay_eligible=true`, but a slot can be used only for the exact four
pre-response infrastructure classes in the schema.

Endpoint assignments are generated for every registered A/B commitment and
every D1/D4 target/goal row, plus session-only provenance receipts. Every row
has denominator weight 1 and literal call IDs. At T0 each literal Stage-1 gate
key `G01`--`G11` is bound to exactly one closed object containing the exact
`receipt_id` and `receipt_kind` required by `assignment_manifest.schema.json`.
After Stage 1, `gate_receipt.schema.json` requires the corresponding typed
receipt object at that ID and kind; the gate reducer rejects a missing,
duplicate, wrong-kind, or Stage-2 binding. It never discovers evidence through
a dynamic query or substitutes an unbound row.

At T0 Stage-2 rows are `ASSIGNED` with a sealed-conditional stage status. If
the fixed Stage-1 predicate fails, their outcome records are
`NOT_TRIGGERED/NOT_INVOKED/NOT_APPLICABLE/null/NOT_TRIGGERED`. A legal wrong
execution is `ASSIGNED/OPENED/RETURNED/ACCEPTED/0/LEGAL_WRONG`. Infrastructure,
timeout, malformed, illegal, early-lock, unavailable-read, abstain, NOT_RUN,
and NOT_APPLICABLE cases follow the total mapping in `analysis_contract.md`.

## Totality and replay allocation

The generator returns exactly one of: a valid manifest plus SHA-256 receipt,
or `GENERATOR_NOT_RUN` with a closed reason from missing/rejected input,
duplicate ID, invalid schema, cardinality mismatch, coupling violation, or
target-construction failure. It never emits a partial manifest. A later valid
`SHAM_EXHAUSTED` receipt is not a manifest-generator failure: the affected
preassigned rows remain and receive endpoint zero without another constructor
attempt.

The manifest contains two replay-slot records in the fixed order
`replay-001`, `replay-002`, initially with null source IDs. During execution,
scan failed eligible scientific calls in canonical call-index order.
`replay-001` binds the first eligible call and `replay-002` the next distinct
eligible call. Eligible means exactly `ENGINE_START_FAILURE`,
`ENGINE_PROCESS_CRASH_BEFORE_RESPONSE`,
`TRANSPORT_EOF_BEFORE_RESPONSE`, or
`DEVICE_RUNTIME_FAULT_BEFORE_RESPONSE`; timeout, parse failure, illegal/wrong
output, unavailable read, OOM forecast, and any response-byte-bearing failure
are ineligible. Replay bytes/config/seed equal the source exactly, run in a
fresh process, never replace it, and never enter an endpoint. There is no third
slot.

Stage 0 must reject any missing/extra/duplicate row, wrong stage/order/count,
invalid target or selected-h cut, mismatched common seed, reused analysis-only
seed group, missing denominator, invalid replay class, third replay, adaptive
cell, or unlisted lane. It recomputes the table independently and hashes the
validated JCS manifest before scientific execution.

## Total resource-counter projection

Each Think session deterministically selects exactly one runtime profile from
its topology: `THINK_D1_10 -> THINK_D1_RECURRENT`, `THINK_D4_31 ->
THINK_D4_RECURRENT`, and `ONE_SHOT_THINK_D4_1 ->
THINK_D4_STRUCTURED_ONE_SHOT`. Their initial/cumulative raw-output maxima are
respectively 5,120, 15,872, and 15,872 tokens. Every one of the 3,414 call
resource rows carries required integer `phase_tokens_remaining_before` and
`phase_tokens_remaining_after`; JSON null is invalid, including for unopened,
NOT_TRIGGERED, NOT_RUN, and post-terminal NOT_INVOKED rows.

For the first row of a Think phase, `before` equals its profile initial value.
For each later canonical resolver ordinal, `before` equals the preceding row's
`after`. An invoked recurrent row requests `min(512,before)`; the structured
one-shot requests `min(15872,before)`. After charging raw generated tokens and
before parsing, `after = before - raw_output_tokens`. A retained uninvoked row
has raw output zero and `after = before`. Accepted-token nullability never
affects this raw-token equation. Consequently the final remainder plus the
sum of raw output over all rows equals the initial value exactly, including
failure and noninvocation suffixes. Replays charge only process aggregates and
cannot alter the source phase counter.
