# PCFL v3 source repairs — adversarial cross-critique v1

Date: 2026-09-10

Status: **source-only adversarial advisory; rework required; not ratified and
not executable**. This document authorizes no implementation, preparation
source creation, materialization, fixture/root/data generation, CPU benchmark
run, model or tokenizer use, training, LoRA/adapter/checkpoint operation,
parenting, GPU use, resource acquisition, scientific execution, promotion,
claim, release, or submission.

Reviewed completely:

- `AGENTS.md`;
- `chg_20260910_pcfl_m0_mtext_bound_v2/consensus.json`;
- `20260910_pcfl_m0_exact_contract_repair_fresh_v1.md`;
- `20260910_pcfl_mtext_supplied_exact_contract_repair_fresh_v1.md`; and
- `20260910_pcfl_authority_durability_exact_repair_fresh_v1.md`.

## 0. Verdict

The three repairs contain most of the right ingredients, but they are **not a
single exact contract**. M-TEXT currently changes outcome-relevant M0
semantics after M0 is supposedly frozen; the durability repair defines a
different artifact identity and promotion mechanism from the M0 repair; and
several model-visible sizes, reader operations, conditions, and behavioral
counterfactuals are impossible or absent as written.

The successor should be an integrated v3 source proposal, not three documents
with amendment precedence left to an implementer. Select:

1. a fixed non-oracular action catalog with ordinary `NO_EFFECT` actions;
2. an eight-read, bundled graph reader followed by a hard first-action read
   cut;
3. checker-only semantic hashes and model-visible neutral capability handles;
4. `TRUTHFUL_NULL` links with **null endpoints**, not authentic endpoints;
5. `HandoffPublic` as the semantic payload and `MTextHandoff` as a private
   routing/binding envelope that names its digest;
6. separately named M0 conformance cells and M-TEXT scientific conditions;
7. the authority repair's per-file CAS and immutable reference receipts, not
   manifest-root-directory promotion;
8. a two-freeze preparation exception only after exact human ratification;
9. 64 M0 engineering roots, then the exact 16/32/16 M-TEXT
   DEV/CONFIRMATION/RESERVE split with presentation blocks as repeated finite
   cells, not a population sample; and
10. reset-sole-channel claims only for the carrier conditions, with raw/RAG/
    graph arms explicitly labeled alternative-memory baselines.

Until those choices are incorporated into one hash-bound proposal and the
blockers below are closed, the correct disposition is **REWORK**. No M0
implementation or M-TEXT execution is ready.

## 1. Exact reconciliation matrix

### 1.1 `legal_actions` versus `action_catalog` and `NO_EFFECT`

**Contradiction.** M0 exposes the exact currently legal relation actions and
treats a wrong relation as `ILLEGAL_ACTION`, invalidating a root. M-TEXT says
the model receives all sixteen relations and that a wrong relation is an
ordinary, charged `NO_EFFECT`. M-TEXT cannot change this after consuming an
immutable M0 handoff.

**Selected choice.** Amend M0 itself before materialization:

- replace `FiniteView.legal_actions` by `action_catalog`;
- in every path phase expose all `r00..r0f`, plus `finish` and `abstain`, in
  sorted order;
- in uncertainty expose all `e0..e3` plus `abstain`;
- in acquisition expose the already-M0-native IDs `c0`, `c1`, and `abstain`;
- use `c0/c1` everywhere; remove the unbound M-TEXT spelling
  `COMMIT_0/COMMIT_1`;
- a relation without an outgoing authentic STEP fact consumes one action,
  leaves state unchanged, closes the reader, and emits an evidence-false
  fixed-size `NO_EFFECT` ordinary event in the next registered action slot;
- a premature `FINISH` is an ordinary policy terminal named
  `WRONG_FINISH`, not a parser/controller error and not `ABSTAIN`; and
- `ILLEGAL_ACTION` is reserved for an action absent from the fixed catalog or
  a structurally invalid command.

`PublicEvent.outcome.kind`, `CommandResult.status`, branch terminal enums,
failure precedence, root receipts, expected vectors, and mutation fixtures
must all be amended consistently. As written, none contains the complete
`NO_EFFECT`/`WRONG_FINISH` surface.

### 1.2 Thirty-two reads versus eight reads and the first-action cut

**Contradiction.** M0 grants 32 reads and permits interleaved read/action
crawling. M-TEXT promises eight pre-action reads and closes the reader after
the first successful or unsuccessful world action. The call and token
arithmetic assumes the latter.

**Selected choice.** In M0, each path probe and delayed-goal phase begins with
exactly eight reads and four relation actions. Add `reader_open=true` and
`world_actions_taken=0`; the first relation action, including `NO_EFFECT`,
sets `reader_open=false`. Later READs return the ordinary padded `BLOCKED`
envelope without index dispatch. The cut resets only at the next isolated
probe fork or delayed reset.

The combined uncertainty/acquisition phase has at most four calls: at most
two optional pre-experiment READs, one experiment, and one commit. ACQUIRE
does not open a new reader. This makes the 4-call roster real rather than
granting a nominal 32-read budget that cannot be exercised.

### 1.3 Exact bundled-reader contract and the eight-read proof

**Blocker in both repairs.** M0's `MemoryReturn.item_kind` returns an atom
**or** a link. M-TEXT says a response contains one atom slot and one link slot
but still describes a one-record candidate list. With separate records and
semantic-hash ordering, eight reads do not guarantee discovery of a four-edge
AUTH path.

**Selected choice.** Replace `item_kind` with two independently typed slots:

```text
MemoryReturn := {
  status, fingerprint, anchor, cursor,
  atom_slot: AtomProjection | NULL_ATOM,
  link_slot: LinkProjection | NULL_LINK,
  repeat_count, pad
}
```

The pure candidate functions are:

- `NODE(a), cursor=i`: return the `i`th incident STEP atom in `atom_slot` and
  null link;
- `ATOM(x), cursor=i`: select the `i`th incident non-null readable link; return
  that link **and the unique opposite endpoint atom** as one bundle;
- `LINK(y), cursor=0|1`: return that link plus the selected endpoint atom;
- any absent position: fixed-size `NOT_FOUND`; and
- `REACHOUT_OFF` on `ATOM` or `LINK`: fixed-size `BLOCKED` without examining
  the carrier.

Candidate order is by frozen neutral slot handle, never semantic hash, goal,
or score. Returned atom/link handles enter the catalog. Node aliases merely
appearing inside a returned Atom do **not** become new READ capabilities.

This yields a constructive worst-case eight-read proof for either goal:

1. one `NODE(S)` read returns either `p0` or `p2`; both start a valid path;
2. its single incident forward link returns `p1` or `p3` in one bundled read;
3. at `p1/p3`, at most two incident-link reads find the forward `p4` bundle;
4. at `p4`, at most four incident-link reads inspect the two backward and two
   goal-terminal alternatives and find `p5` or `p6`.

The maximum is `1 + 1 + 2 + 4 = 8`. This proof must be exhaustively replayed
under every handle rotation and both goal orders. In `ATOMS`, the initial atom
may be returned, but its atom-anchor has no non-null link candidate and hence
cannot reveal the next atom; the first action closes reads. That is the exact
reason ATOMS cannot crawl. If the implementation grants capabilities for node
aliases inside the returned atom, this isolation fails.

M0's `SCRIPT_PATH_V3`, which presently says “exhaustive cursor traversal
within 32 reads,” must be rewritten to this exact eight-read bundled policy.
The reference must pass AUTH for every root and both goals and fail the
registered connection cuts without private path-table access.

### 1.4 Semantic identities versus neutral actor handles

**Contradiction.** M0 exposes content-derived `atom_id`, `link_id`, and
semantic-ID ordering. M-TEXT later replaces them with `a00..a19` and
`l00..l06`. This is not a renderer-only change: IDs are READ capabilities,
dependency values, catalog members, ordering keys, and model tokens.

**Selected choice.** Split identity at M0 source level:

- checker/provenance objects keep content-derived semantic hashes;
- actor-visible projections use only fixed-width capability handles:
  `a00..a19`, `l00..l06`, and, if primitive evidence must be exposed,
  a separately frozen `v00..` handle family;
- the per-root semantic-to-handle mapping is fixed before goal release,
  transformed only by the registered presentation rotation, and identical
  across all conditions for that root;
- handles do not change when a slot becomes NULL/EMPTY/cut/deranged;
- deps contain at most eight distinct earlier returned atom/link capability
  handles; and
- candidate order is public slot-handle order.

Semantic hashes, support-root hashes, root IDs, fixture roots, condition IDs,
and endpoint-oracle hashes remain checker/controller-only. Merely replacing
`Handle.id` while leaving content hashes inside model-visible Atom/Link rows
does not close the channel; the actor projection needs its own closed schema.

The exact constructive dependency rule should be modest and consistent:
first ACT cites its STEP atom; each later ACT cites its STEP atom and the AUTH
link connecting it to the preceding STEP. Across the full trace this yields
four atoms and three links. Delete M0's incompatible sentence requiring each
ACT to cite *all* path atoms and links.

### 1.5 `TRUTHFUL_NULL` currently discloses the answer it is meant to remove

**Critical flaw.** M0 preserves AUTH endpoints and content-derived link IDs
while changing only `status` to `EMPTY`. The system prompt says EMPTY does not
assert a connection, but the endpoint pair visibly states the same
connection. A capable policy can ignore the status word.

**Selected choice.** A `TRUTHFUL_NULL` carrier slot retains its padded outer
shape but has `status="EMPTY"`, `left=null`, `right=null`, and no semantic ID,
capability handle, evidence, or support fields. It must not expose either AUTH
endpoint or a content-derived AUTH ID. To preserve read exposure without
preserving the answer, an ATOM-anchor query may return one identical
non-capability EMPTY sentinel for each position up to that atom's frozen
AUTH degree; the sentinel and count reveal degree only, never the former
neighbor, pair, link handle, or opposite atom. It cannot enter deps or be used
as a LINK anchor. A hidden lookup from the queried atom to its former AUTH
neighbor is forbidden even if the returned endpoints are nulled.

AUTH, EMPTY, DERANGED, and NULL must have the same fixed outer bytes and the
same tokenizer length after the renderer. Fixed padding may achieve byte
equality but does not by itself guarantee tokenizer equality; the frozen
tokenizer checker must prove it. Failure blocks M-TEXT preparation rather than
triggering an identifier/padding search.

### 1.6 `HandoffPublic` versus `MTextHandoff`

**Apparent contradiction, resolvable by nesting.** M0 calls
`HandoffPublic` its only future-consumable output. M-TEXT defines a different
`MTextHandoff` containing private routing and oracle digests.

**Selected choice.** Preserve both with nonoverlapping meanings:

- `HandoffPublic` is the immutable model-free semantic payload produced under
  M0/H0. It contains only the condition-appropriate carrier and initial
  public state and is never allowed to contain root, condition, split, score,
  or oracle routing data.
- `MTextHandoff` is a private M-TEXT controller/checker envelope. It must name
  `handoff_public_sha256` and the exact M0 freeze ID. The renderer is given
  the verified `HandoffPublic` projection only, never the envelope.
- rename `root_public_alias` and `condition_public_alias` to private
  `root_route_id` and `condition_route_id`; “public” is false and invites an
  accidental render.
- the model-visible call is still only system bytes plus `ModelTurn`; the
  carrier is accessed through the frozen reader, not dumped into ordinary
  arms.

The current HandoffPublic fixed size and ModelTurn byte limit are incompatible
(section 2.4 below), so their numeric bounds remain a blocker.

### 1.7 M0's 19 cells versus M-TEXT's 19 conditions

**Semantic collision.** Both documents say “19,” but they enumerate different
objects. M0 has fourteen path conformance cells, two cue cells, and three
delayed conformance cells. M-TEXT has nineteen model-policy conditions,
including no-memory, target-only, passive signature, raw context, RAG, native
graph, two recurrence controls, and `NO_PERSIST_NEW`.

**Selected choice.** Give them disjoint type names and manifests:

- `M0ConformanceCell`: the CPU reference-script/intervention checks;
- `MTextCondition`: the model-execution roster; and
- `MTextCheckpoint`: the phase-specific frozen M0 checkpoint a condition
  consumes.

There is no 1:1 mapping and no authority transfer from a green M0 cell to an
M-TEXT condition. M0 must still conformance-test the `NO_PERSIST_NEW`
transform even if it is not promoted to a twentieth scored M0 cell. The M0
RootReceipt's current positional `public_handoff_digests:[x19]` is therefore
wrong for M-TEXT. Replace it with a separately typed, key-addressed H0
handoff-manifest receipt that covers every condition-required checkpoint and
transform, including `NO_PERSIST_NEW`.

The model roster may remain exactly nineteen after the corrections below.
Do not call those nineteen independent samples.

### 1.8 Manifest-root directory versus per-file CAS

**Contradiction.** M0 proposes atomically renaming
`pcfl_m0_frozen/<manifest_root>/`. The durability repair installs each file in
a per-file content-addressed store and promotes immutable reference objects
without moving the bytes. The manifest-root formulas also differ.

**Selected choice.** Use the durability repair's per-file CAS protocol:

- immutable payloads live under
  `materialized/objects/sha256/<2>/<62>`;
- a sorted manifest maps normalized logical path to byte length and object
  SHA-256;
- its semantic manifest root is the authority repair's domain-separated hash
  over raw length-prefixed sorted rows;
- the manifest JSON is installed immutably at that root-named path;
- checkers consume only that manifest and CAS objects;
- a human freeze is an immutable reference receipt naming exact upstream
  hashes; it moves no bytes; and
- no `current`, `latest`, mutable passed flag, directory rename, or symlink has
  authority.

The integrated successor must supply one exact manifest JSON schema and state
whether its root field is omitted or zeroed during encoding. The current
authority repair supplies the row hash algorithm but not the complete
manifest object schema; this remains a source blocker. Governance JSON may be
JCS plus one LF while payload bytes follow their frozen type encoding, but
the two classes must be explicitly enumerated. M0's blanket “no final
newline” rule cannot silently override the durability document's governance
encoding.

The proposed `preparation_input_root` also includes
`human_preparation_ratification_sha256`. If that ratification object is
expected to name the same input root, the definition is circular. Bind a
`pre_authority_root` over every source/spec/runtime/consensus field except the
human ratification; have the human object name that pre-authority root and
scope; then compute `preparation_input_root` from
`pre_authority_root || human_ratification_sha256`. No object may hash itself.

### 1.9 Materialization and freeze order

**Contradiction.** The v2 consensus requires actual exact bytes before
ratification/implementation. The M-TEXT repair repeats that literally. The
M0 and authority repairs propose ratifying deterministic preparation source,
then producing candidate bytes, then freezing those bytes.

**Selected choice.** Adopt the authority repair's two-freeze exception, but
only through a new exact human ruling that explicitly supersedes the literal
v2 `D-EXACT-BYTES` disposition for preparation alone:

1. source proposal contains the complete inert materializer/checker patch
   bytes, semantics, schemas, paths, runtime, output limits, and zero-choice
   operation;
2. human ratifies only creation/execution of that deterministic CPU
   preparation package;
3. one no-RNG/no-search/no-selection materialization produces candidate CAS
   bytes and terminal checker receipts;
4. fresh independent review examines source and output;
5. a second exact human decision freezes the candidate manifest; and
6. only then may a separate change request M0 runtime implementation.

The source-authoring step is itself scoped work. Under the current authority,
even materializer/checker code may not be created or run. A future proposal
can carry exact inert patch/file bytes inside its deliberation artifact so
Rohin can ratify what will be written; it may not infer permission from these
advisories.

M-TEXT's statement that “the successor ratification packet must contain the
actual materialized bytes” is retained for the **M0 implementation/M-TEXT
handoff** packet, not the earlier deterministic-preparation-source packet.
No generated byte becomes consumable before the second freeze.

### 1.10 V7 authority

The three repairs agree in substance: zero runtime reuse. Select the
authority repair's exhaustive primitive disposition and denylist. Delete any
`E-V7-TO-M0-REUSE` runtime edge. Governance citations to immutable V7 hashes
transfer no code, golden, oracle, result, permission, or scientific meaning.
The failed V7 audit remains `passed:false` and cannot become green through a
PCFL check.

### 1.11 Root count and splits

The root counts are consistent once their meanings are separated, but the
proposed contiguous `k` split is not a satisfactory answer to the v2 demand
for held-out factorial balance. It puts visibly different alias ranges in
DEV, CONFIRMATION, and RESERVE. Select this pre-model, explicitly stratified
roster instead:

```text
DEV k:          0, 6, 8, 14, 17, 23, 25, 31
CONFIRMATION k: 1, 3, 5, 7, 9, 11, 13, 15,
                16, 18, 20, 22, 24, 26, 28, 30
RESERVE k:      2, 4, 10, 12, 19, 21, 27, 29
```

This keeps every `(k,0)/(k,1)` twin together; balances low/high node-alias
halves, `z(k)`, `k mod 4`, and probe order within each split; gives
CONFIRMATION one representative of every `k mod 16` relation permutation;
and gives DEV and RESERVE eight different relation permutations each. The
choice is algebraic and must be frozen before model rendering. Reducers use
these explicit sets, not numeric `k` intervals.

Then:

- M0 deterministically materializes and checks all 64 `(k,h)` roots. This is
  an engineering census and Boolean conformance, not `N=64` science.
- M-TEXT uses the explicit eight/sixteen/eight `k` rosters above, yielding 16
  roots/eight twin blocks for DEV, 32 roots/sixteen blocks for CONFIRMATION,
  and 16 roots/eight blocks for RESERVE.
- both `h` twins are always kept together;
- goals, conditions, aliases, paths, phases, calls, turns, reruns, and cells
  are repeated finite-suite observations, never extra scientific units; and
- fixed topology permits only a one-model/one-suite conditional mechanism
  statement, not topology or population generalization.

No performance-based root generation, replacement, rescue, or reserve
opening is legal.

### 1.12 Model/runtime identity and claims

The proposed Qwen revision and runtime version strings are **not yet a frozen
model/runtime**. A future M-TEXT preparation packet must contain local file
inventory, hashes, sizes, tokenizer/chat-template bytes, wheels/interpreter/
image/CUDA/driver/controller/parser/renderer hashes, environment, and actual
hardware class. The source document's statement that the environment was
“already observed” is not a receipt.

Select Qwen2.5-7B-Instruct as the proposed primary only if a later human
decision binds those actual bytes. A 32B run is a separately named ceiling
and cannot replace a failed 7B condition. Neither model permits a LoRA,
parent, tokenizer substitution, provider fallback, or scientific claim under
the M-TEXT-SUPPLIED scope.

The one-shot output byte ceiling is missing: recurrent calls have 256 tokens
and 2,048 decoded bytes, while one-shot calls may generate 3,328 tokens but
have no corresponding decoded-byte/output-file limit. Bind a numeric
one-shot byte ceiling and include it in parser/resource receipts before any
execution.

### 1.13 Reset as the sole channel

The M-TEXT reset destruction list is the selected contract for the primary
AUTH and matched carrier conditions. After delayed reset, a new controller
and fresh two-message model request retain only the immutable root plus the
registered old/new carrier projection; no acquisition event, scratch,
history, command, return, KV/cache, session, filename, timing, or condition
metadata survives.

This claim cannot apply to `RAW_CONTEXT`, `RAG_RAW`, or `NATIVE_GRAPH`: those
arms deliberately retain alternative external memory. Label them
alternative-channel baselines, run their own reset projections, and never use
them as evidence that the carrier was the sole channel. `NO_PERSIST_NEW`
retains old carrier only. The main sole-channel conclusion is licensed only
if separately injecting each prohibited survivor fails preflight and each of
`OLD_CUT`, `NEW_CUT`, and `NO_PERSIST_NEW` destroys delayed integration.

An engine may stay resident only after proving prefix caching, response cache,
session handles, mutable adapters, and RNG state cannot carry cell content.
Forward/reverse ordering alone is a canary, not a proof of all hidden state.

### 1.14 Constructive dependence and the missing mask condition

M-TEXT defines `trace_dependence` using “all-path masking,” but its nineteen
condition roster has no all-atom-plus-link mask model condition. This would
silently add calls and invalidate the exact roster and resource arithmetic.

**Selected choice.** Use the already registered `BRIDGE_CUT_RECURRENT` as the
model-level all-path **connection** intervention: it removes every authentic
old connection incident to `p4`, which lies on every registered path, while
preserving atoms. Combine it with `TWIN_REDIRECT_RECURRENT` for binding
specificity. Rename the M-TEXT endpoint to
`connected_trace_dependence = bridge_cut_behavior_change AND
twin_redirect_correct_change`. Do not claim atom-level all-path-mask
dependence from this roster.

M0 may retain a private CPU all-path mask test for its fixed reference script,
but that is conformance only and must not be substituted for model behavior.
If the team wants the stronger atom-plus-link model counterfactual, it must
add a twentieth condition and recalculate every call/token/resource total.

## 2. Further blockers found by cross-critique

### 2.1 M0 fixed sizes make the M-TEXT input contract impossible

M0 fixes `FiniteView` at 131,072 UTF-8 bytes and `HandoffPublic` at 262,144
bytes. M-TEXT caps an input at 65,536 UTF-8 bytes and 8,192 tokens. A
`ModelTurn` containing the padded FiniteView already exceeds the byte cap
before the system prompt, chat template, or static context is added.

This is a hard pre-materialization blocker. The integrated source must bind
smaller numeric padding bounds and then prove, for every fully rendered
condition including RAW_CONTEXT and NATIVE_GRAPH:

```text
system + rendered user + generation allowance <= 16,384 tokens
rendered input bytes <= the registered byte ceiling
no truncation
```

The numeric bounds cannot be chosen later by a renderer. A deterministic
formula such as “smallest registered power-of-two bound exceeding the exact
finite-universe maximum” is acceptable only if the actual resulting numbers
and golden bytes are present before M0 implementation freeze.

### 2.2 Event anchors are not in the command schema

M-TEXT permits a `PublicEvent` anchor, but `Handle.kind` contains only NODE,
ATOM, and LINK. Select the simpler contract: there is no EVENT handle. When a
public event is released, its public node aliases may be installed as NODE
capabilities according to an exact catalog rule. Unknown reconstructed node
strings still reject unless present in the catalog.

### 2.3 Phase-specific endpoints need an explicit `NA`

Several M-TEXT conditions execute only 13, 17, 26, or 39 calls and therefore
do not observe every phase endpoint. The document nevertheless says every
endpoint is binary at every root/condition. Treating an unexecuted phase as
zero confounds an intervention with missing design; copying AUTH values
without declaring it launders results.

Add a closed `0|1|NA` endpoint schema and a phase-applicability matrix.
Reducers must reject `NA` in any registered gate rather than average it.
Inherited checkpoint prerequisites are checker facts, not model outcomes.

### 2.4 The uncertainty mechanism is not connected-memory causality

`FiniteView.uncertainty` exposes candidate outcome-anchor counts directly.
The policy can choose E0/E1 without reading a PREDICT atom or any Link. Thus
the experiment-choice endpoint can test prospective information use, but not
causal use of connected memory.

Keep it as a separate endpoint and narrow the headline wording: connected
rows identify path construction; public calibrated evidence identifies
experiment choice; the reset/cut interventions identify delayed old-plus-new
carrier use. Alternatively redesign uncertainty to require a separately
controlled memory read, which would change budgets, calls, and the roster.

### 2.5 Token equality is not implied by padded byte equality

The repairs correctly require tokenizer equality for matched carrier
conditions, but M0's underscore padding only guarantees byte length. Token
length and token identity can differ across AUTH/DERANGED/EMPTY content. Bind
which standard is required:

- equal **token count** is feasible and should remain mandatory;
- equal token IDs would erase the content intervention and is not desired;
- identical outer schema, record count, byte count, token count, calls, and
  budgets are the matched exposure vector.

The frozen tokenizer checker must enumerate every root, phase, and matched
condition. It may reject the design but may not search model performance for
an alternative encoding.

### 2.6 The practical-baseline contrast needs an exact formula

Define the conservative root-wise strongest textual baseline explicitly:

```text
b_best(k,e) = max(b_e(k,RAW_CONTEXT), b_e(k,RAG_RAW))
D_best(e) = sum_k [b_e(k,AUTH)-b_best(k,e)] / 16
```

Require `D_best >= 1/16` separately for two-goal traversal and delayed
integration. `NATIVE_GRAPH` remains a labeled ceiling, not part of this max.

### 2.7 The nominal `-0.05` adverse bound is exactly zero-loss here

With sixteen confirmation presentation blocks, every paired rate difference
is an integer multiple of `1/16=0.0625`. Therefore the literal condition
`D >= -0.05` permits **no net lost block**; its exact integer implementation
is `sum_k(b_AUTH-b_comparator) >= 0`. This is stricter than “allow a small
five-point loss.”

Retain that zero-net-loss interpretation if the `-0.05` bound is a governing
requirement. If one lost block should be permitted, the registered bound must
be changed prospectively to `-1/16`; it cannot be called `-0.05`. The
successor must state which scientific intent Rohin ratifies.

### 2.8 Resource arithmetic is numerically correct but not fully bound

The condition roster arithmetic checks:

```text
requests/root = 10*43 + 2*26 + 1*17 + 1*39 + 2*13 + 1*17 + 2*4 = 589
allowed generated tokens/root = 170,752
48 DEV+CONFIRMATION roots = 28,272 requests and 8,196,096 tokens
+ 24 sentinels = 28,296 requests and 8,202,240 tokens
max input tokens = 28,296 * 8,192 = 231,800,832
```

These totals remain valid only if the nineteen-condition roster and existing
phase call counts survive the repairs. No extra all-path-mask call, timing
probe, tokenizer test generation, retry, or ceiling model may be hidden in
them. If first-call timing is used to lower the resource ceiling, it must be
one of the 24 predeclared sentinels; otherwise it is an additional registered
call.

`A40-equivalent GPU-hours` is not exact without a frozen conversion rule.
Either require the registered physical A40 hardware class and report actual
GPU-hours, or prospectively bind a benchmark-independent conversion factor
for every permitted device. Actual GPU-seconds, input/output tokens, calls,
peak memory, wall time, and artifact bytes remain mandatory regardless.

The 192 GPU-hour, 48-hour wall, 500-GiB, and USD-zero ceilings are proposed
ceilings only until exact resource execution authority is ratified. Hitting
one yields INCOMPLETE and cannot prune cells.

### 2.9 Finite-census statistics are appropriate but the wording must stay
narrow

The twin-min reducer and exact finite rates are appropriate for this fixed
deterministic assay. No p-value, binomial interval, bootstrap interval,
standard error, or `N=16` population language is warranted. Exact numerators,
denominators, and paired differences are sufficient.

DEV is protocol selection and never evidence. Confirmation is one frozen
model/topology census. Failure consumes that confirmation split; reserve use
requires a new bound replication. This can support a conditional within-suite
mechanism statement only.

## 3. Exact remaining blockers and required tests

The integrated v3 source is not ratifiable until it closes all of these:

1. one amended closed M0 schema for `action_catalog`, `NO_EFFECT`,
   `WRONG_FINISH`, `reader_open`, `world_actions_taken`, neutral handles, and
   bundled MemoryReturn;
2. exact actor-projection schemas separating semantic hashes from all public
   capabilities and support labels;
3. exact eight-read reference traces for all 64 roots, both goals, both probe
   orders, all presentation rotations, and every matched carrier transform;
4. proof that ATOMS cannot gain a next-node capability and AUTH can complete
   within eight reads;
5. repaired `TRUTHFUL_NULL` with null endpoints/content IDs and exact byte/
   token exposure checks;
6. one normalized command vocabulary (`c0/c1`, `finish`, `abstain`) across M0,
   prompt, parser, actions, expected vectors, and receipts;
7. exact M0 record-size numbers compatible with every M-TEXT rendered input;
8. exact `HandoffPublic`/`MTextHandoff` nesting, hashes, projection allowlist,
   and private route-ID names;
9. a key-addressed H0 checkpoint/transform manifest, not an unexplained
   positional array of nineteen handoff digests;
10. disjoint schemas and applicability tables for `M0ConformanceCell` and
    `MTextCondition`, including `NO_PERSIST_NEW`;
11. the complete CAS manifest JSON schema, exact newline classes, manifest
    hash encoding, no-overwrite rules, and fault-injection cases;
12. a non-self-referential pre-authority/ratification/input-root identity
    chain;
13. exact preparation patch/file bytes and hashes before any preparation
    authoring/execution ratification;
14. exact checker source lineages and a mutation corpus covering every v2
    concern class, including the new oracle-action, read-cut, neutral-handle,
    EMPTY-endpoint, and size-overflow cases;
15. explicit human selection of the two-freeze exception and zero V7 runtime
    reuse;
16. the explicit balanced `k` split above in every reducer, roster, and
    golden, replacing contiguous range logic;
17. exact local model/tokenizer/runtime/hardware manifests before any M-TEXT
    execution approval;
18. a numeric one-shot decoded-byte/output limit;
19. exact phase applicability with `NA` handling;
20. reset mutation tests for every forbidden survivor and explicit exemption/
    labeling of external-memory baselines;
21. rename/define the model-level bridge-cut dependence endpoint or add a
    twentieth mask condition and recalculate resources;
22. narrow experiment-choice language unless uncertainty is redesigned to
    require memory;
23. exact strongest-baseline formula and literal integer implementation of
    every threshold, especially `-0.05`;
24. physical-device or A40-equivalence accounting and assurance that any
    timing call belongs to the roster;
25. closed request/call receipt schemas, maximum file sizes, failure
    precedence, ambiguous-call handling, and no-retry recovery tests;
26. pre-render paired-prefix tests over system bytes, user bytes, chat-template
    bytes, token IDs, settings, and tool returns; and
27. a fresh independent implementation review and separate author-side
    scientific-claim review after the relevant bytes actually exist.

Minimum newly explicit tests, beyond the already listed v3 registries:

```text
M0V3-ACTION-CATALOG-NOEFFECT-WRONGFINISH
M0V3-BUNDLED-READER-EIGHT-READ-COMPLETENESS
M0V3-ATOMS-NO-NEXT-NODE-CAPABILITY
M0V3-NEUTRAL-HANDLE-NONINTERFERENCE
M0V3-TRUTHFUL-NULL-ENDPOINT-DENIAL
M0V3-RECORD-SIZE-MTEXT-COMPATIBILITY
M0V3-HANDOFF-TYPE-AND-KEYED-ROSTER
M0V3-CONFORMANCE-VS-SCIENCE-NAMESPACE
M0V3-CAS-MANIFEST-SCHEMA-FAULT-INJECTION
M0V3-NONSELF-REFERENTIAL-AUTHORITY-ROOT
MTEXT-V3-BALANCED-EXPLICIT-SPLIT-ROSTER
MTEXT-V3-FULL-RENDER-BYTE-TOKEN-FIT
MTEXT-V3-PHASE-APPLICABILITY-NA
MTEXT-V3-BRIDGE-CUT-AND-TWIN-DEPENDENCE
MTEXT-V3-BASELINE-RESET-CHANNEL-LABELING
MTEXT-V3-ONE-SHOT-OUTPUT-BOUND
MTEXT-V3-RESOURCE-ROSTER-NO-HIDDEN-CALLS
```

## 4. Preparation scope, M0 implementation, and M-TEXT execution are distinct

The next governance chain must keep these scopes separate:

### A. Source-only integrated proposal

May contain prose, exact schemas/tables, an inert exact patch bundle, hashes,
test registry, and requested scopes. It may not write implementation paths,
materialize bytes, run CPU tests, load a tokenizer/model, or use GPUs. This is
the scope of the current work.

### B. Deterministic preparation-source realization

Requires a new exact human ratification naming the patch bytes and allowed
paths. It may write only the M0 semantic specification, materializer, two
independent checkers, schemas, mutation fixtures, and preparation runtime
manifest. It does not run them unless execution is separately included in the
exact ratified scope.

### C. Deterministic P0 materialization and F0 byte freeze

Requires explicit CPU preparation authority under the selected two-freeze
exception. It creates candidate CAS bytes/checker receipts with no RNG,
selection, model, tokenizer, benchmark inference, or science. A second human
decision over the actual manifest/review bytes is the only fixture freeze.

### D. M0 runtime implementation and CPU conformance

Requires a separate exact change bound to one frozen M0 freeze ID. It may
implement and test only the model-free CPU runtime. Passage is
`DEV_NONCLAIM`; it authorizes no model-facing handoff, M-TEXT, GPU, or claim.

### E. H0 and M-TEXT implementation/preparation

Requires separate architecture authority over the exact semantic handoff,
renderer, tokenizer/chat template, prompts, parser, controller, scorer,
session/reset protocol, conditions, resource ledger, runtime, and DEV split.
Tokenizer rendering/preparation is not silently covered by M0.

### F. M-TEXT DEV model execution

Requires fresh implementation and advocate reviews plus exact human approval
of model/tokenizer/runtime/GPU/resource manifests. DEV can select or reject a
future frozen protocol but is never paper evidence.

### G. M-TEXT confirmation and claim

After DEV, freeze exact bytes and an empty confirmation receipt registry;
obtain new independent review and exact human confirmation authority. Only a
complete confirmation may proceed to a separate evidence-to-claim review.
Even full passage supports supplied-memory causal use only.

None of A--G automatically authorizes the next. General permission to use
GPUs or agreement with the architecture does not replace an exact stage
approval.

## 5. Claim ceiling and final recommendation

After the selected repairs, the most M-TEXT could show is:

> In one fixed finite topology under one exact frozen 7B policy, grounded
> atom-plus-connection memory causally supported two goal-dependent path
> constructions; calibrated public evidence supported a separating action and
> revision; and a persistent old-plus-new carrier supported delayed
> integration after a sterile reset.

Even that sentence requires every noncompensatory confirmation gate and a
fresh evidence-to-claim review. It is not DREAM authorship, SLEEP, a learned
write, LoRA, continual learning, accumulation, compression, parenting,
lifetime improvement, or the PCFL flywheel.

The fastest defensible route is therefore not immediate implementation. It is
one short integrated v3 proposal incorporating the selected choices above,
followed by exact preparation-source ratification. The three current repairs
are valuable source material, but treating their precedence as an
implementation detail would reproduce the v2 failure in a more elaborate
form.
