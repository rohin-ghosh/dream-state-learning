# M-core v6 fresh causal-identification and visibility audit

Date: 2026-09-12 UTC

Scope: fresh, independent, read-only scientific audit of
`2026-09-12_m_core_exact_two_cycle_design_v6.md`. I read `AGENTS.md` first and
used only local text/search checks. I did not use a GPU or model, run builder
code, inspect an earlier review as authority, or change builder source,
coordination, jobs, or evidence. This memo is the only intended change.

## Verdict

**REWORK before materialization.** Do not freeze the v6 bytes as the immutable
package contract. The six-fit topology itself does not need to change: every
repair below is a schema, compiler projection, runtime-control, receipt, or
claim-boundary repair. The design has no present scientific result; even a
repaired contract would still require its actual package/checker,
qualification, TEXT, DEV, and CONF evidence.

I found the following exact blockers. I do not list nonblocking preferences.

## 1. No closed receipt proves that the child or clean actor produced a public action

V6 calls `ChildCommittedActionEvent` authentic, but its closed object contains
only an authorization constant, instruction/action/pre-state handles, and a
tick (`v6:382-400`, `1833-1847`). `MemoryAuthorizedActionEvent` and
`ExperimentDispatchEvent` likewise contain parsed action assertions but no
model-turn reference. `ChildPairSelectionEvent` adds input/binding/draw hashes,
but still omits the exact continuation and parser result (`1854-1863`).
`PublicDeclaration` has still less custody (`1871-1877`). The generic
`ExecutionAttemptReceipt` binds only an optional artifact digest
(`2263-2270`), and no gate consumes a closed actor-generation object. The
untyped `raw_evidence` blob cannot repair this because v6 expressly forbids a
gate from relying on it.

Concrete counterexample: a harness can synthesize the registered expected
`ChildCommittedActionEvent`, selection, source choice, declaration, and
dispatch directly from the hidden expected trace, attach a valid-looking draw
ledger, and never use the child's or actor's continuation. Every current
event/root/result schema can still be satisfied. The same construction can
assert an empty reset while actually reusing a process, because
`ResetReceipt` contains only three claimed bits and no model-turn/process
edge (`2147-2151`). Thus neither “child's authentic public actions” nor “a
reset clean actor used typed reads” follows from an `R_r=1` bundle as typed.

Minimum zero-fit repair: add one closed `ModelTurnReceipt` (or equivalent) for
every child and deployment decision. It must bind the exact pre-turn public
transcript/input, actor and tokenizer/runtime/decode binding, birth-state and
process instance, exact continuation bytes and token IDs, inference-draw
ledger, parser digest, and the single parsed READ/action/selection/declaration
object. Every corresponding public event must cite that turn. Make reset bind
the first turn of each episode to a fresh process, immutable birth checkpoint,
and empty-context digest. Gates and the independent checker must consume these
typed receipts, not a raw blob. This changes no fit.

## 2. The pair-selection event cannot represent the selection action it claims, and LINK lacks a typed support map

The action machine exposes 28 surfaces, one for each unordered pair
(`504-507`), and `ChildPairSelectionTask` carries eight lane handles plus 28
pair handles (`1732-1738`). The event instead has
`visible_pair_roster:VEC[8,...]` and two `selected_pair_handles`
(`1854-1863`); the prose and semantic rules repeat an “eight-pair roster”
(`395-400`, `2487-2490`). It has no selected action-surface handle. Eight lanes,
28 unordered-pair candidates, one chosen pair candidate, and the two member
lanes are therefore conflated. Membership in the event's eight-element vector
does not prove that the child emitted any of the 28 legal selection actions.

The next edge is also under-typed. `AblationEvidenceView` supplies an unlabelled
array of eight authentic pairs (`1901-1905`), while the reveal supplies an
unlabelled array of eight action handles (`1864-1870`). The compiler has no
graph capability (`367-375`). Array cardinality plus the global trial-order
constant does not bind each action/observation to one selected lane and one of
`JOINT/LEFT/RIGHT/NUISANCE`. Permuting the same eight observations across
trial roles can change whether each lane is `1/0/0/0` without violating a
closed field type available to the compiler.

Minimum zero-fit repair: give the event distinct fields
`visible_lane_handles[8]`, `visible_pair_candidate_handles[28]`,
`selected_pair_action_handle`, and `selected_lane_handles[2]`; bind the action
handle to the canonical unordered pair and to the model-turn receipt from
blocker 1. Replace the unlabelled support array with eight closed bindings
`{lane_handle, trial_kind, action_event, observation}` and require a bijection
over two selected lanes times four trial kinds, exact reveal action handles,
and later ticks. Then LINK can verify the two profiles from its own bytes.

## 3. SOURCE gives the compiler the forbidden control/provenance label

The capability table says donor map, derivation, and condition are unavailable
to the compiler (`367-375`), and the prose says donor identity and derivation
kind remain audit-only (`411-418`). The actual `SourceEvidenceView` is a
`ONEOF` whose positive member says `AUTHENTIC_EVENT_PAIR`, while its control
member says `DERIVED_CONTROL_PAIR` and exposes the donor action, donor
observation, and derivation-receipt handle (`1879-1899`). The compiler is also
said to verify that receipt (`637-643`), although the receipt object is not in
its input and dereferencing it would cross the declared ACL.

Concrete counterexample: a pure compiler can branch on `binding_class` before
looking at counts. It is then a condition-aware compiler despite using only
canonical input bytes. This defeats the stated condition-blind source edge
and makes the capability matrix false.

Minimum zero-fit repair: make both arms project to one identical
compiler-facing `PresentedSourcePair` shape containing only the presented
action, presented public outcome, and condition-neutral citation material
needed for counting. The audit/checker, not the compiler, must validate the
authentic or presealed-derived provenance projection and retain donor maps and
derivation receipts exclusively in `AuditEnvelope`. Remove all provenance
class/donor/receipt fields from compiler capability. The compiled FULL and
truthful 2/2 rows and all three S1 fits remain unchanged.

## 4. NEW cannot determine an outcome-specific row from its declared public bytes

`NEW_ROW_ADMISSION` is supposed to compute a posterior using only the input at
`455-469`. But `PublicObservation` exposes an opaque observation handle and
surface, not a typed bit or public handle-to-bit codebook (`1849-1853`);
`PublicTaskLaw` contains no experiment-to-`h` outcome formula
(`1923-1931`); and `CompilerRowTemplate` contains no `h` selector
(`1910-1921`). The only explicit mappings are the declaration's
`predicted_outcomes` and `outcome_row_handles`, and that declaration is not
bound to an actor turn (`1871-1877`). The assertion that the compiler “can
recompute” the posterior (`2504-2518`) is therefore stronger than the closed
inputs.

Concrete counterexample: hold authentic source evidence, source choice,
menu, dispatch, observation, and the two unlabeled templates fixed. One
schema-valid declaration can use predictions `[0,1]` and row order `[n0,n1]`;
another can use `[1,0]` and `[n1,n0]`. With no pre-outcome typed law or outcome
codec, the compiler cannot identify which is faithful. The same observed
surface can consequently admit either row. An environment/materializer can
also write the declaration from hidden `h` without a detectable actor leak.

Minimum zero-fit repair: include a pre-outcome public `ExperimentLaw` that
binds each menu position to `H`, `ONE_MINUS_H`, or `NUISANCE`; include a
public outcome-handle-to-bit codebook (or a typed public bit in the observation);
and use a NEW-template subtype with an explicit public hypothesis selector
`0|1`. Bind the declaration to a model-turn receipt, make dispatch cite that
declaration, and check its prediction/map against the pre-outcome law. The
compiler can then derive preferred family from authentic counts, reject
nuisance, compute the singleton from dispatch plus observed bit, and copy the
uniquely labeled template without seeing `b`, `z`, or actual `h`. No new fit is
needed.

## 5. The registered cut traces are impossible under the closed reader input

For a READ, v6 scores all 32 candidate rows with deterministic inputs and says
the unique passing candidate returns FOUND (`790-801`). A cut only deletes the
correct SHA from availability (`771-788`). `RecognitionScorerInput` contains
just prompt, request, and candidate row (`1988-1995`); it contains neither the
mounted availability state nor a control-local candidate projection. The
static `AvailabilityEntry` is keyed only by base carrier and request
(`1535-1542`), although the semantic rule claims it covers controls
(`2528-2530`). `ControlMutation` has no defined scorer-input transition
(`1562-1566`).

Concrete counterexample/impossibility: ordinary FULL and `B_LINK_CUT` mount
the same FULL adapter, issue the same LINK request, and score the same 32
candidate rows. Determinism therefore gives identical scores. Because the
ordinary row must pass, the cut also yields that FOUND; after availability is
deleted it becomes `ROOT_UNAVAILABLE_FOUND`, not the required charged MISS and
`VALID_CUT_ENDPOINT`. The same contradiction holds for both D cuts. If an
implementation secretly lets the scorer see cut availability, that is an
untyped intervention/reader side channel instead.

Minimum zero-fit repair: define a manifest-bound mounted-candidate projection
for every base/control instance. A cut must remove the target before scoring
and fill its slot with a presealed schema/length/work-matched nonmatching row,
so 32 scorer calls remain and a filler false positive is still invalid rather
than silently filtered. Key availability/canonical returns by an audit-only
`mount_instance_handle` (or an equally closed applied-mutation state), and
bind every scorer input to that projection. The actor must see only the
resulting fixed-size MISS, never the mount/control identity. This makes the
specified cut transitions possible without adding a fit.

## 6. The B/D “payload swaps” permit a public intervention-label change

`SOURCE_READ_SWAP_C` correctly keeps the row handle and every non-count byte
fixed (`708-722`). In contrast, the general hit-matched bitmap explicitly
allows row-handle changes (`849-855`), and B/D swaps are only specified as a
replacement `MemoryRow` (`1005-1008`, `1562-1566`). A clean actor may therefore
route on the unique replacement handle rather than on the changed sequence or
new action. The resulting failure establishes that a distinguishable wrong-row
instance was consumed, not the advertised payload specificity used in `F_r`.

Minimum zero-fit repair: apply the same isolation rule as the source swap.
For B and D old-link swaps, preserve row handle, query/key, action mode,
citations, status, length, timing, and all unrelated bytes; change only the
ordered action payload and mechanically forced destination/hash/frame
descendants. For the D new-row swap, preserve the same nonpayload fields and
change only `n_h` to `n_(1-h)` plus forced descendants. Intervention identity
remains audit-only. This is inference-only.

## 7. Writer/reader qualification is both circular and too weak to establish the required capability

The immutable package includes `wstar_binding.json` and `reader_binding.json`.
Each binding contains `qualification_receipt_sha256` (`1638-1648`), while the
closed `QualificationReceipt` contains `binding_sha256` (`2395-2399`). Taken
literally, the writer binding must hash the receipt that must hash the writer
binding; the reader has the same cryptographic fixed-point cycle. The receipt's
arbitrary list of generic named checks also does not require carriage/extraction
of ATOM, SEQUENCE, CHOICE_TABLE, NEW, PAD, or cumulative old+new rows.

This is not a merely missing implementation. The current local writer gateway
has exactly two binary `ACT: a0/a1` candidates and binary targets
(`organism_v6/multikey_writer_gateway_simple.py:44-55,157-160,267-298`), and
the terminal independent audit says its generation cells missed the selective
binding thresholds and “This is not a selective writer”
(`2026-09-12_semantic_w0_writer_terminal_independent_audit.md:31-50,
193-214`). Nothing reviewed supplies evidence that those bytes are a qualified
typed-row `W*`. V6's own warning at `959-962` is correct, but its closed
qualification objects cannot enforce it or be materialized as written.

Minimum zero-fit repair: remove result-receipt hashes from both immutable
bindings. Bind instead a closed qualification specification, fixture set,
renderer/parser, model, recipe, and thresholds. Later typed writer and reader
qualification receipts must bind the already-hashed package and binding. The
writer specification must mandatorily test exact render/extract custody for
all four row uses (including 2/2 CHOICE_TABLE, two-action links, `n0/n1`,
private PAD, and old+new coexistence); the reader specification must test the
same mounted-candidate semantics used by positive, cut, swap, and no-carrier
cells. Until those receipts pass, label the package unqualified and bar TEXT/M,
rather than inserting the current gateway or a generic accepted receipt.

## 8. “Pre-blueprint” and causal child selection overstate the actual timing

The root generator draws the useful unordered lane pair, assigns A/B within
it, and chooses `u_D` before childhood (`312-325`). The immutable transition,
availability, fixture, and template-generating assets are also package-bound.
The child can authentically recover the uniquely indicated preassigned pair
before support/template *reveal*; it does not causally create a pair before a
blueprint exists. V6 partly acknowledges this by limiting the DREAM statement
to provenance/agreement (`608-614`), but the releasable claim still says
“child-selected pre-blueprint pair set” (`27-39`).

Minimum zero-fit repair: keep the generator and all fits, but narrow the claim
to **child-authenticated recovery, before support and link-template reveal, of
the preassigned pair uniquely indicated by the registered public ablation
evidence**. “Child-selected evidence-indicated pair” is acceptable only as
descriptive provenance/agreement, not as an identified causal effect of child
selection, learned search, or blueprint creation.

## Minimum claim after repair

Conditional on the repaired typed receipts and all noncompensatory `R` gates,
the result could support:

> In a finite typed benchmark, a qualified writer carried rows compiled from
> authenticated child action/outcome turns and from a child-authenticated
> recovery, before support and template reveal, of the preassigned pair
> uniquely indicated by public ablation evidence. A reset clean actor used
> typed reads to complete two goal-conditioned old-memory traces. Following an
> authenticated public experimental outcome, a second clean-base cumulative
> write preserved the required old link and added the uniquely public-law-
> identified new row required for a delayed action.

That wording still does not identify DREAM intelligence, native learned
search, online/in-place growth, general retention, recurrence, a whole-organism
effect, or a causal effect of the child's pair-selection policy. All repairs
preserve exactly the S1 triplet plus conditional S2 triplet: at most six M
fits per complete root.
