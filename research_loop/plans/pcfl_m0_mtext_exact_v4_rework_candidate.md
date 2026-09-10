# PCFL M0 + M-TEXT-SUPPLIED V4 — integrated rework candidate

Date: 2026-09-10

Status: **source-only proposal for fresh deliberation**. This file is not a
ratification and authorizes no implementation, deterministic materialization,
fixture/root/data generation, CPU benchmark execution, model or tokenizer
execution, training, LoRA/adapter/checkpoint work, parenting, GPU use,
resource acquisition, scientific claim, release, or submission.

## 0. Plain-language decision

Build a small ruler before testing the learning organism.

The ruler asks one narrow question: can one frozen text model use a supplied
connected memory to plan two different routes, use a public uncertainty signal
to choose an informative action, and later combine old and newly admitted
memory after a sterile reset?

This is not yet DREAM, SLEEP, LoRA, parenting, continual learning, or a
lifetime curve. It validates the task and read/use boundary those later tests
will rely on. The learning system remains simply THINK, DREAM, and SLEEP; the
detail below is experimental hygiene, not extra cognition.

The previous V2 five-role deliberation returned `rework`. This candidate
integrates the three source repairs and three independent audits into one set
of choices. It intentionally removes optional machinery when a smaller
control answers the same question.

## 1. Decisions selected in this candidate

1. The model-free instrument is version-bumped to
   `PCFL_M0_THIN_V4`; V3 artifacts fail to load under V4.
2. PCFL has **zero FeltCraft V7 runtime reuse**. V7 is governance/design
   evidence only. Its failed scope audit remains failed.
3. Use the explicit deterministic 64-root algebra already reviewed, with the
   balanced noncontiguous DEV/confirmation/reserve split in section 10.
4. The actor sees neutral fixed-width handles; semantic hashes remain private
   checker/provenance identities.
5. The action catalog is fixed and non-oracular. A wrong catalogued relation
   is a charged `NO_EFFECT`; premature `finish` is ordinary `WRONG_FINISH`.
6. Each path has eight pre-action reads. A bundled link read returns the link
   and its opposite endpoint atom. The first world-action attempt closes the
   reader, including a `NO_EFFECT` attempt.
7. Drop `TRUTHFUL_NULL_RECURRENT` from the scientific roster. Endpoint-free
   empty returns remain an M0 conformance case, not a model condition.
8. Separate substrate-neutral task success from connected-memory constructive
   use. Raw/RAG/no-memory controls can therefore succeed or fail behaviorally,
   rather than losing automatically because they lack carrier citations.
9. Every delayed phase uses one immutable, model-independent supplied
   delayed-entry fixture. It never borrows an AUTH model output. Acquisition
   and delayed use are separate factorial assays; this stage makes no
   acquisition-to-retention or continuous-life claim.
10. Use registered bridge-cut plus binding-twin behavior for model-level
    dependence. Do not add an unregistered twentieth all-path-mask run.
11. Treat `AUTH_SCRATCH_OFF` as the carried-scratch ablation. Rename the
    one-shot cell `AUTH_NO_FEEDBACK_TAPE`; it is a closed-loop-feedback lower
    bound, not a pure recurrence comparator.
12. Treat public uncertainty counts as a separate prospective-evidence
    mechanism. They do not establish connected-memory causality.
13. Use per-file content-addressed storage and immutable reference receipts.
    There is no mutable `current`, `latest`, or passed pointer.
14. Adopt an explicit two-freeze preparation exception: first approve exact
    deterministic preparation source; then separately freeze the actual
    candidate fixture bytes after two checks and fresh review.
15. M0 engineering conformance, M-TEXT DEV, M-TEXT confirmation, and every
    later learning package remain separate human-authorized stages.

## 2. Closed M0 V4 finite universe

### 2.1 Roots and aliases

Internal nodes are exactly `N00..N1f`; relations are exactly `R00..R0f`;
experiments are exactly `E0..E3`; outcomes are bits `0|1`.

The internal roles are:

```text
N00=S   N01=X   N02=Y   N03=B   N04=C   N05=TA  N06=TB  N07=D
N08=H0  N09=H1  N0a=Z0  N0b=Z1 N0c=Q0  N0d=Q1  N0e..N1f=DECOY
```

The complete engineering universe is `(k,h)` for `k in 0..31` and
`h in {0,1}`: exactly 64 roots. There is no RNG, seed search, ranking,
selection, retry, favorable-root rejection, or replacement.

```text
z(k) = popcount(k) mod 2
node_alias(N_i) = "n" + lower_hex2(i XOR k)
rel_alias(R_j)  = "r" + lower_hex2(j XOR (k mod 16))
exp_alias(E_j)  = "e" + lower_hex1(j XOR (k mod 4))
```

Both `h` twins for a fixed `k` are actor-byte-identical until the ordinary
outcome of an informative experiment. Private root/split/condition/score
identities never enter actor-visible bytes.

### 2.2 Paths and acquired fact

Old transition atoms are exactly:

```text
p0: S  -R00-> X       p1: X -R01-> B
p2: S  -R02-> Y       p3: Y -R03-> B
p4: B  -R04-> C       p5: C -R05-> TA
                      p6: C -R06-> TB
q0: Q0 -R0e-> N10     q1: Q1 -R0f-> N11
```

Registered minimum path classes are exactly:

```text
A, S->TA: p0,p1,p4,p5 | p2,p3,p4,p5
B, S->TB: p0,p1,p4,p6 | p2,p3,p4,p6
D, S->D : p0,p1,p4,nh | p2,p3,p4,nh
```

The acquired atom is `nh: C -R(07+h)-> D`, admitted only after a correct
commit. Every registered path needs bridge atom `p4`; the delayed goal needs
old path structure plus `nh`.

### 2.3 Public uncertainty evidence

The frozen public calibration counts are:

```text
       E0     E1     E2     E3
H0    [1,0]  [0,1]  [1,1]  [1,1]
H1    [0,1]  [1,0]  [1,1]  [1,1]
Z0    [1,1]  [1,1]  [1,0]  [0,1]
Z1    [1,1]  [1,1]  [0,1]  [1,0]
```

Actual outcomes are `E0=h`, `E1=1-h`, `E2=z(k)`, and `E3=1-z(k)`.
`E0/E1` separate the target bit; `E2/E3` only separate the nuisance bit.
Because these counts are directly public, experiment choice tests use of
prospective evidence, not use of graph links.

### 2.4 Event chronology and provenance cuts

Logical positions are total coordinates, not wall-clock times:

```text
00..06  old discovery p0..p6
07..22  calibration rows
23..24  q0,q1
24.POST_EVENT_SYNTH.*  old proposals
25..31  independent old validation p0..p6
32..35  isolated goal-A event slots
36..39  isolated goal-B event slots
40      experiment outcome
41      commit outcome
41.POST_EVENT_SYNTH.*  new proposals
42      independent new validation p4
43      independent validation nh iff acquisition succeeded
44..47  delayed-goal event slots
```

Every proposal parent is strictly earlier in this order; validation is
strictly later and disjoint. Support parents are the complete deduplicated set
of primitive evidence available at the proposal cut. Transformed carriers
never create support evidence. Contradiction/revocation removes descendants
before any later handoff.

## 3. Actor-visible identity and action contract

Checker objects retain content-derived semantic IDs. The actor sees only:

```text
atom capabilities: a00..a19
link capabilities: l00..l06
node handles:       public node aliases
```

The root-specific semantic-to-slot map is private, frozen before goal
release, and invariant across conditions. Carrier transformations change
slot contents/status, never handles or ordering. Semantic hashes, evidence
roots, root IDs, conditions, splits, scores, oracle values, filenames, and
private maps are denied from all actor projections.

Path-phase `action_catalog` is all sixteen relation aliases plus `finish` and
`abstain`, regardless of current state. Uncertainty exposes four experiment
aliases plus `abstain`; acquisition exposes `c0,c1,abstain`.

- authentic outgoing relation: consume one action, move state, emit `NODE`;
- other catalogued relation: consume one action, keep state, emit
  evidence-false `NO_EFFECT`;
- `finish` at target: ordinary success;
- premature `finish`: ordinary zero-valued `WRONG_FINISH`;
- out-of-catalog ID or structurally invalid command: instrument-level
  `ILLEGAL_ACTION`.

The first relation attempt closes the reader whether it moves or yields
`NO_EFFECT`. Four relation attempts and one uncharged terminal opportunity
are available per path phase.

## 4. Bundled reader and constructive bound

`MemoryReturnV4` has independently typed atom and link slots plus an explicit
`grants` list. Only handles in `grants` become future READ/dependency
capabilities. Merely mentioning a node alias inside an atom or link grants
nothing.

```text
MemoryReturnV4 := {
  v:4,
  status: FOUND | NOT_FOUND | BLOCKED,
  fingerprint,
  anchor,
  cursor,
  atom: PublicAtom | NULL_ATOM,
  link: PublicAuthLink | PublicEmptyLink | NULL_LINK,
  grants: [public-capability-handle],
  repeat_count: 1 | 2 | 3,
  pad
}
```

Candidate order is public slot-handle order only.

- `NODE(n),i`: return the `i`th incident STEP atom; grant that atom only.
- `ATOM(a),i`: return the `i`th forward readable AUTH link and its right
  endpoint atom together; grant both returned handles.
- `LINK(l),0|1`: return that link and the selected endpoint atom.
- absent cursor: fixed-size `NOT_FOUND`.
- reader closed or `REACHOUT_OFF`: fixed-size `BLOCKED` without index lookup.

One AUTH route is constructively available in at most five of eight reads:

1. `NODE(S)` returns either first atom `p0|p2`;
2. the first atom returns `p1|p3` plus its link;
3. that atom returns `p4` plus its link;
4. `p4` cursor 0 returns one terminal atom plus link;
5. only if it is the other goal, `p4` cursor 1 returns the desired terminal.

The public goal identifies which terminal atom is desired. The actor then has
four path atoms and three authentic adjacent links; three reads remain for a
benign retrieval error. Exhaustive CPU goldens cover both
paths, goals, probe orders, roots, rotations, and transforms.

ATOMS cannot crawl: initial node reads may expose start/terminal atoms, but
atom fields grant no node capability, no AUTH link returns an intermediate
atom, and the first attempted action closes the reader. Exhaustive capability
closure must exclude `p1,p3,p4` and every link before action.

## 5. Carrier transforms and checkpoint DAG

`M0ConformanceCell` and `MTextCondition` are disjoint enums and manifests.
There is no numeric or positional 1:1 mapping.

M0 must materialize and conformance-test AUTH, ATOMS, endpoint-null EMPTY,
DERANGED, BRIDGE_CUT, TWIN_REDIRECT, UNCERTAINTY_SHAM, REACHOUT_OFF, OLD_CUT,
NEW_CUT, and NO_PERSIST_NEW transforms. Endpoint-null EMPTY returns are
query-local, identity-null, grant nothing, expose no neighbor, and are not a
scientific M-TEXT condition.

The exact checkpoint DAG is:

```text
OLD(root)
  -> isolated PATH_A(condition)
  -> isolated PATH_B(condition)
  -> condition-local UNCERTAINTY/ACQUIRE when registered
  -> condition-local DELAYED after sterile reset when registered
```

Path-A and path-B traces never become inputs to each other. Their joined
receipt has a closed allowlist and contains no branch scratch, abandoned
thought, reader transcript, workspace, dependency, correctness, failure,
timing, sibling handle, or padding residue.

`DELAYED_ENTRY(k,h)` is a model-independent fixture containing the authentic
old carrier plus the canonical admitted new atom/link for the ordinary correct
acquisition outcome, and no scratch, transcript, capability workspace, cache,
or session state. Every D phase is an isolated fork of that same supplied
entry. `OLD_CUT`, `NEW_CUT`, and `NO_PERSIST_NEW` apply only at that fork.
All delayed conditions have acquisition and retention endpoints `NA`; no
result joins a U-phase model output to a D-phase model input.

Static phase starts plus transition/reader functions are frozen inputs.
Model-dependent views/results are dynamic content-addressed execution
receipts, not pre-materialized checkpoints.

## 6. M0/M-TEXT handoff and reset

`HandoffPublic` is the immutable model-free semantic payload. It contains
only the condition-appropriate carrier and phase-start public state.
`MTextHandoff` is a private routing/binding envelope naming
`handoff_public_sha256`, M0 freeze ID, renderer/parser hashes, and private
route IDs. The model receives neither this envelope nor a dumped carrier.

The common reader consumes verified `HandoffPublic`; the renderer receives
only its allowlisted public projection.

For AUTH and matched carrier conditions, delayed reset destroys all model
messages, generated scratch, commands, tool returns, reader transcripts,
workspaces, raw history, acquisition transcripts, caches, KV state, session
handles, RNG state, filenames, timing, and mutable process state. A fresh
controller and stateless request retain only immutable root public state and
the registered old/new carrier projection.

`RAW_CONTEXT`, `RAG_RAW`, and `NATIVE_GRAPH` deliberately retain separately
declared external memory. They are alternative-channel baselines and never
support a claim that the carrier was the sole surviving channel.

## 7. Size and rendering boundary

Preparation uses a no-choice size derivation: for each closed M0 type, choose
the smallest 256-byte multiple that contains the exhaustive V4 maximum
canonical unpadded encoding. The preparation source contains hard
upper caps; overflow fails the full candidate rather than enlarging a type:

```text
one row      <= 2,048 bytes
MemoryReturn <= 4,096 bytes
GoalsComplete <= 12,288 bytes
FiniteView   <= 16,384 bytes
Carrier      <= 32,768 bytes
HandoffPublic <= 65,536 bytes (never directly rendered)
one raw object <= 1,048,576 bytes
```

The resulting exact per-type bounds and golden bytes must exist in the P0
candidate and be separately human-frozen before M0 implementation. This
source proposal does not pretend those absent bytes already exist.

For every M-TEXT request, including RAW_CONTEXT and NATIVE_GRAPH:

```text
system + chat-template + rendered user <= 65,536 UTF-8 bytes
input <= 8,192 tokenizer tokens
input + generation allowance <= 16,384 tokenizer tokens
no truncation
```

Recurrent responses allow at most 256 generated tokens and 2,048 decoded
bytes. A 3,328-token path tape allows at most 26,624 decoded bytes; the
1,024-token uncertainty/acquisition tape allows 8,192 decoded bytes. Overflow
is a behavioral zero with a sealed receipt; it never triggers retry or
truncation.

Matched carrier conditions require equal outer schema, records, byte count,
token count, read/action opportunity, calls, and generation allowance. They
do not require identical token IDs, which would erase the content treatment.
Tokenizer-equality certificates are produced only after an exact tokenizer
is separately frozen; no performance-guided padding/remapping is permitted.

## 8. Exact M-TEXT roster

The scientific roster has 18 conditions:

```text
Full P+U+D labels, 43 slots (2; phases remain independent):
  AUTH_RECURRENT
  AUTH_SCRATCH_OFF

Path A+B plus supplied delayed entry, 39 slots (8):
  ATOMS_RECURRENT
  DERANGED_RECURRENT
  REACHOUT_OFF_RECURRENT
  NO_MEMORY_RECURRENT
  PASSIVE_SIGNATURE_RECURRENT
  RAW_CONTEXT_RECURRENT
  RAG_RAW_RECURRENT
  NATIVE_GRAPH_RECURRENT

A+B only, 26 slots (2):
  BRIDGE_CUT_RECURRENT
  TWIN_REDIRECT_RECURRENT

Uncertainty/acquisition only, 4 slots (1):
  UNCERTAINTY_SHAM_RECURRENT

Supplied delayed entry only, 13 slots (3):
  OLD_CUT_RECURRENT
  NEW_CUT_RECURRENT
  NO_PERSIST_NEW_RECURRENT

Four phase-level one-shot calls (2):
  TARGET_ONLY_ANSWER_PRIOR_TAPE
  AUTH_NO_FEEDBACK_TAPE
```

The one-shot tape may name the closed union of future public action classes,
but execution still applies phase-local semantics. It cannot name future
reader-return handles and has no constructive-citation endpoint. A wrong
catalogued relation remains `NO_EFFECT`; a post-action READ remains
`BLOCKED`. It tests the value of outcome-conditioned closed-loop execution,
not scratch alone.

Every maximum request opportunity is preregistered. An unissued suffix after
terminal behavior is sealed `NOT_REACHED`; actual emitted calls are reported
separately.

## 9. Endpoints and causal meanings

Each phase-specific endpoint is `0|1|NA`. A reducer rejects `NA` wherever a
registered gate requires that endpoint.

Substrate-neutral behavioral endpoints:

- `two_goal_task_success`: reaches and correctly finishes isolated A and B;
- `delayed_task_success`: reaches and correctly finishes at D after reset;
- `plan_valid`, `first_action_correct`, and `plan_execution_consistent`,
  defined without carrier-specific citations.

Carrier-mechanism diagnostics, applicable only where the common connected
reader makes them meaningful:

- `relevant_atom_returned`, `relevant_link_returned`, `public_handle_reused`;
- `connected_constructive_use`: every executed transition cites its returned
  atom and each adjacency cites an earlier returned authentic link;
- `delayed_connected_integration`: the delayed constructive trace uses an
  admitted old atom/link and the condition-local new atom/link;
- `connected_trace_dependence`: derived across AUTH, BRIDGE_CUT, and
  TWIN_REDIRECT; bridge cut changes/destroys the construction and the twin
  changes the goal-specific terminal action correctly.

Prospective-evidence endpoints, explicitly separate from connection claims:

- `separating_choice`;
- `realized_information`;
- `belief_revision` from `UNKNOWN` to the observed target bit;
- `acquisition_success` after correct `c0|c1`.

Static-context identifiers may be cited only under a separately typed
baseline provenance rule. They never masquerade as common-reader handles.
Cross-substrate comparisons use behavioral endpoints only.

## 10. Split, reducers, and gates

The balanced fixed split is:

```text
DEV k:          0,6,8,14,17,23,25,31
CONFIRMATION k: 1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30
RESERVE k:      2,4,10,12,19,21,27,29
```

Both `h` twins stay together. M0 checks all 64 roots as an engineering census.
M-TEXT uses 16 DEV roots, 32 confirmation roots, and leaves 16 reserve roots
dormant. Roots, calls, goals, conditions, aliases, and twins are not
independent samples. This is one fixed-model, fixed-topology finite assay;
there are no p-values or population-generalization claims.

For endpoint `e` and condition `c`:

```text
b_e(k,c) = min(e(k,0,c), e(k,1,c))
R_DEV_e(c) = sum_{k in DEV} b_e(k,c) / 8
R_CONF_e(c) = sum_{k in CONFIRMATION} b_e(k,c) / 16
D_e(c1,c0) = sum_{k in CONFIRMATION}(b_e(k,c1)-b_e(k,c0)) / 16
b_best(k,e) = max(b_e(k,RAW_CONTEXT), b_e(k,RAG_RAW))
D_best(e) = sum_k(b_e(k,AUTH)-b_best(k,e)) / 16
```

The source-authoring deliberation must encode gates as exact integer counts.
The intended confirmation gates are:

1. AUTH task: at least 12/16 blocks for two-goal and delayed task success.
2. Connection necessity: AUTH exceeds ATOMS, DERANGED, BRIDGE_CUT, and
   REACHOUT_OFF by at least 4/16 on two-goal task success; AUTH connected
   constructive use is at least 12/16; paired bridge/twin dependence is at
   least 12/16.
3. Prospective evidence: AUTH separating choice, realized information,
   belief revision, and acquisition are each at least 12/16;
   UNCERTAINTY_SHAM is at most 4/16 on target information/revision/acquisition,
   and AUTH exceeds it by at least 8/16 on acquisition.
4. Delayed necessity: AUTH delayed connected integration is at least 12/16;
   OLD_CUT, NEW_CUT, and NO_PERSIST_NEW are at most 4/16 on delayed task
   success; AUTH exceeds each by at least 8/16.
5. Shortcut bounds: NO_MEMORY, TARGET_ONLY, and PASSIVE_SIGNATURE are each at
   most 5/16 on substrate-neutral traversal/delayed task endpoints where
   applicable.
6. Zero-net-adverse rule: on comparable substrate-neutral task and plan
   endpoints, AUTH loses no net confirmation block to ATOMS. This is the exact integer meaning
   of the inherited `-0.05` bound because one block is 1/16=0.0625.
7. Practical textual-memory advantage is separate: AUTH exceeds the root-wise
   strongest of RAW_CONTEXT and RAG_RAW by at least 1/16 on both substrate-
   neutral two-goal and delayed task success. NATIVE_GRAPH is a ceiling only.
8. Carried-scratch value is separate: AUTH exceeds AUTH_SCRATCH_OFF by at
   least 4/16 on prospectively named behavioral endpoints with zero net
   adverse block.
9. Closed-loop-feedback value is separate: AUTH_SCRATCH_OFF exceeds
   AUTH_NO_FEEDBACK_TAPE by at least 4/16 on prospectively named acquisition
   and delayed-task endpoints. This is not labeled scratch or recurrence
   necessity, and U-to-D retention is not inferred.

No stronger claim is rescued by averaging gates. DEV may tune/fork the
protocol but is never evidence. Confirmation failure consumes the split.
Reserve is only a post-confirmation robustness follow-up under new authority,
never a replacement confirmation.

## 11. Exact resource envelope

With the 18-condition roster:

```text
maximum request slots/root
  = 2*43 + 8*39 + 2*26 + 1*4 + 3*13 + 2*4
  = 501

allowed generated tokens/root
  = 2*11,008 + 8*9,984 + 2*6,656 + 1*1,024
    + 3*3,328 + 2*11,008
  = 148,224

DEV (16 roots):          8,016 slots; 2,371,584 output tokens
confirmation (32 roots): 16,032 slots; 4,743,168 output tokens
DEV + confirmation:      24,048 slots; 7,114,752 output tokens
sentinels:               24 slots; 6,144 output tokens
grand maximum:           24,072 slots; 7,120,896 output tokens
maximum input allowance: 24,072 * 8,192 = 197,197,824 tokens
reserve only:            8,016 slots; 2,371,584 output tokens
```

These are maxima, not guaranteed emitted calls. Every condition also reports
actual calls, input/output tokens, reader work, CPU/GPU seconds, wall time,
memory, artifact bytes, actions, and failures.

Execution scope, if later requested, is restricted to exact physical hardware
named in that request. No undefined `A40-equivalent` conversion is used.
Proposed hard ceilings remain 192 actual A40 GPU-hours, 500 GiB artifacts,
and USD 0.00 external spend. DEV and confirmation have separate active-run
clocks; review/approval waiting is outside compute time. A pre-authorized
sentinel must establish throughput feasibility before DEV.

## 12. Content-addressed preparation and two freezes

The selected durability layout is per-file CAS:

```text
materialized/objects/sha256/<first-2>/<remaining-62>
materialized/manifests/<semantic-manifest-root>.json
materialized/receipts/<run-id>.json
frozen/<freeze-id>.json
```

The canonical manifest object is JCS UTF-8 plus one LF:

```text
{
  "artifact_type":"pcfl_m0_candidate_manifest",
  "entries":[{"encoding":...,"logical_path":...,"nbytes":...,"sha256":...}],
  "preparation_input_root":hex64,
  "schema_version":1
}
```

The semantic manifest root is omitted from the manifest object itself and is
carried by its path and the freeze receipt. It is:

```text
SHA256("PCFL-M0-MANIFEST-v1\0" || concat(sorted rows))
row = uint32be(path_len) || path_utf8 || uint64be(nbytes) || digest_raw32
```

The manifest JSON itself has a separate object SHA-256. A freeze receipt names
both.

To avoid self-reference:

```text
pre_authority_root = H(all exact source/spec/schema/materializer/checker/
                       runtime/scope/consensus hashes except human approval)
human preparation approval names pre_authority_root and allowed scope
preparation_input_root = H(domain || pre_authority_root || approval_sha256)
```

`run-id` hashes `preparation_input_root`. `freeze-id` hashes
`preparation_input_root`, semantic manifest root, manifest-object hash, and
both checker receipt hashes. Timestamps, hostnames, process IDs, usernames,
attempt numbers, and filesystem order affect neither identity nor science.

Objects/manifests/receipts install no-replace after write, close, fsync,
rehash, and directory fsync. Existing identical objects are reused; any
identity collision fails. Crashes leave nonauthoritative staging. One terminal
receipt exists per input root; a failed receipt requires changed bound source
and a new input root. No candidate promotes itself.

The two preparation checkers have frozen, disjoint authorship/source lineage:
one independently reconstructs every root; the other checks axioms,
cardinalities, noninterference, mutation fixtures, reducers, and transforms.
They share only the frozen spec/schemas and standard library. Agreement proves
reproduction plus checked invariants, not semantic truth; fresh human review
still follows.

## 13. Authority sequence

1. Fresh five-role deliberation of this integrated source decision.
2. Human ratification of the exact selected design and **only** the scope to
   author deterministic semantic/materializer/checker source bytes.
3. Fresh deliberation and exact human approval of those actual source bytes
   for deterministic CPU preparation execution.
4. One no-RNG/no-selection materialization, two checks, postflight, and fresh
   independent source/output review.
5. Second human freeze of the actual candidate manifest and receipts.
6. Separate M0 runtime implementation approval bound to one freeze ID.
7. CPU conformance, fresh implementation review, and human nonclaim
   acceptance.
8. Separate M-TEXT renderer/model/runtime/DEV approval after local model,
   tokenizer, chat-template, hardware, prompt, parser, and resource bytes are
   exactly inventoried.
9. DEV only; then fork/freeze, fresh reviews, and a new human confirmation
   approval.
10. Separate evidence-to-claim review. Later E0, M-LORA, lifetime, and
    parenting packages remain independent.

No stage implicitly authorizes the next.

## 14. Required source and test closure

The future exact preparation-source packet must contain the complete V4
semantic JSON, transition/failure tables, closed schemas, materializer, two
checkers, mutation fixtures, runtime manifest, CAS rules, and tests. At
minimum it must close:

- V3/V4 domain separation and zero V7 runtime/import/oracle access;
- actor semantic-hash denial and neutral-handle noninterference;
- fixed non-oracular catalog, `NO_EFFECT`, and `WRONG_FINISH`;
- bundled-reader completeness within eight reads and ATOMS non-crawl;
- first-action reader close, including `NO_EFFECT`;
- endpoint/identity-null EMPTY behavior;
- public cursor order and exhaustive agenda mutation denial;
- total provenance order, independent validation, legal diamonds/cycles,
  contradiction, revocation, and transform non-admission;
- checkpoint DAG, join allowlist, repeat/retry/lost-response/reset isolation;
- `NO_PERSIST_NEW` and every delayed-cut ordering;
- M0 conformance versus M-TEXT science namespace separation;
- exact per-type size derivation and full-render byte/token fit;
- HandoffPublic/MTextHandoff projection and static/dynamic receipt separation;
- phase endpoint `NA` applicability and probe-to-root reducers;
- bridge/twin dependence, baseline reset-channel labeling, and ceiling labels;
- request-slot/NOT_REACHED arithmetic with no hidden calls;
- CAS schema, non-self-referential roots, no-overwrite/fault injection,
  duplicate run, crash recovery, and malformed-receipt precedence; and
- fresh independent implementation and scientific-advocate review.

## 15. Claim ceiling

Even complete confirmation could support only:

> In one fixed finite topology under one exact frozen text policy, supplied
> grounded atom-plus-connection memory causally supported two goal-dependent
> route constructions; separately supplied calibrated evidence supported an
> informative action and revision; and a persistent old-plus-new carrier
> supported delayed task completion and connected integration after sterile
> reset.

It cannot support DREAM authorship, SLEEP, LoRA storage, learning,
compression, parenting, accumulation, lifetime improvement, general memory
intelligence, or the PCFL flywheel. Those require later packages and their own
controls.

## 16. Human-only decisions requested after deliberation

If fresh consensus recommends proceeding, Rohin will be asked to ratify only:

1. zero V7 runtime reuse;
2. the explicit two-freeze preparation exception;
3. the integrated V4 semantic direction above; and
4. authority to author, but not execute, the exact deterministic preparation
   source packet.

No model, tokenizer, fixture materialization, benchmark run, training, LoRA,
parenting, GPU, claim, release, or submission authority is requested here.
