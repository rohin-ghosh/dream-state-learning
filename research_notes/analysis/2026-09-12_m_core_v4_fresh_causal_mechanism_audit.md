# Fresh causal/mechanism audit of M-core v4

Date: 2026-09-12 UTC

Scope: independent read-only review of the complete
`2026-09-12_m_core_exact_two_cycle_design_v4.md` against both complete v3
audits. I treated every future materializer, checker, theorem receipt, reader
qualification, and fit as an unexecuted requirement, not as evidence. I did
not inspect or edit builder code, coordination, jobs, model state, or GPU
state, and I ran no model or scientific job.

## Verdict: REWORK before TEXT, reader acceptance, or any M fit

V4 repairs the broad six-build causal layout and most of the specifically
named v3 defects. In particular, the connected B and D constructions are
sound under the intended availability relation, the h-specific D row is
delayed until after a public outcome, and the source, DREAM, and S2 controls
can all be implemented without a seventh trained carrier.

The literal contract is not yet exact or causally safe, however. There are
four claim blockers:

1. invalid or failed control cells are assigned endpoint zero and can thereby
   create positive confirmatory contrasts;
2. the public-event and compiler schemas cannot represent several authentic
   child events or compile the source and PAD records that the claim requires;
3. the claimed goal-only byte cut conflicts with episode identity, while the
   named no-goal control also removes the carrier; and
4. the supposedly complete transition/schema/generator package is still
   under-specified in ways that prevent the named exhaustive theorem and
   provenance checks from being implemented from v4.

These are zero-fit specification repairs. The six-trained-carrier maximum can
remain unchanged.

## What v4 does establish, conditional on exact materialization

### The connected traversal has no graph-level `U -> C` shortcut

For B, the canonical trace is
`S -> U_u -> B -> C -> T`, and for D it is
`U_uD -> B -> C -> D`. The only successful transition out of `U_i` is the
correct `b_i` into B; the only successful transition out of B is `c_0` into
C. A live link citation authorizes exactly those two ordered actions and
survives across the intervening public observation. Direct uncited actions,
wrong actions, a READ between the two actions, and out-of-order use all fail.
Thus the intended machine makes B live mediation rather than a decorative
waypoint.

The B link cut and hit-matched wrong-link swap separately test availability
and content. At D, the old-link cut/swap and new-row cut/swap are separately
named; no combined failure substitutes for either. Because `u_D` is one of
the two selected lanes, a valid D trace really reuses an old selected link.
The new `n_h` row is compiled only after the C declaration, dispatch, and
causally later public outcome, and a sterile reset excludes the raw C history.
Subject to the schema/provenance repairs below, these facts support delayed
old-memory use plus outcome-specific new-memory use.

### The important v3 intervention repairs are present

- S1 triplets and S2 triplets use condition-blind common realized training
  randomness and one physical device/image per triplet.
- The formal READ relation restricts `FOUND` to carrier availability, while
  neural unavailable-row returns are separately rejected.
- `SOURCE_READ_SWAP_C` is a live, hit-matched inference intervention that must
  redirect dispatch into the nuisance family and prevent admission.
- `RAW_WRONG_ROOT` is honestly demoted and removed from `F_r` and `R_r`.
- S2 uses a grounded gradient-bearing PAD, an allowed-difference bitmap, and
  tensor/batch/RNG/work equality rather than pretending raw provenance IDs are
  identical.
- The A/B goal pair replaces `GOAL_TWIN`; D has separate old and new content
  swaps; device/order balance is claimed only in expectation; cost is the sum
  of measured fit receipts; and global minimality is no longer claimed.

The fit arithmetic is therefore coherent: three S1 fits plus three S2 fits
give at most six M fits for a complete root. Every new intervention named by
v4 is inference-only or a zero-fit fixture/check.

## Claim blocker 1: failed controls can manufacture every favorable contrast

Section 9.1 says that missing, skipped, timed-out, malformed, and failed cells
receive endpoint zero. That is adverse for a positive arm, but favorable for
a subtracted control. For example:

```text
FULL B completes = 1
DREAM_DERANGED fit crashes or its intended wrong row is not extractable = 0
M_r = 1 - 0 = positive
```

The same problem applies when SOURCE_DERANGED, S1_OFF RPC, OLD_PLUS_PAD, or a
D cut/swap is missing or structurally invalid. More subtly, a completed
control carrier that fails to carry its intended control row also creates the
desired endpoint failure without demonstrating a content intervention.
Although `R_r` later rejects such a root, `S`, `M`, `U`, and `W` are tested as
earlier co-primary hypotheses. A later failure of `R` cannot undo an earlier
confirmatory rejection. Consequently the present fixed sequence can reject a
mechanism null because its controls malfunctioned.

Minimal zero-fit repair: separate a **valid completed scientific endpoint
failure** from an invalid/missing cell. Define a prerequisite gate for each
component before taking its sign. At minimum:

```text
I_S(r) = 1[G_S(r) and S_r > 0]
I_M(r) = 1[G_M(r) and M_r > 0]
I_U(r) = 1[G_U(r) and U_r > 0]
I_W(r) = 1[G_W(r) and W_r > 0]
I_R(r) = R_r
```

Each `G` must require every constituent episode to complete, matched nuisance
receipts to pass, positive/control carriers to extract their exact intended
rows, orthogonal rows and interfaces to be preserved, injected cuts/swaps to
be applied exactly, and the expected FOUND/MISS envelope to be observed. A
valid completed control trace that reaches the wrong endpoint remains
endpoint zero; a crash, timeout, missing fit, failed extraction, or malformed
intervention makes the component indicator zero, not the control endpoint
zero. Test these gated indicators in the registered sequence. Raw contrast
magnitudes may still be reported descriptively.

## Claim blocker 2: schemas cannot express the authentic compilation chain

V4 says its displayed objects are exact closed schemas, but several required
objects have no complete definition: `PublicReadEvent`, `PublicDeclaration`,
`PublicPairSelection`, `PublicMenu`, and `DecodeConfig`. The trace union names
`PublicCompilerDecision`, whereas the only displayed type is
`CompilerDecision`. Exact handle length/encoding, array cardinalities, enum
sets, and phase-specific nullability are also deferred.

There are two causal inconsistencies inside the fields that are displayed.

First, every `PublicActionEvent` must have authorization
`MEMORY_ROW|PUBLIC_DISPATCH`, and v4 calls `PUBLIC_DISPATCH` a Phase-C-only
exception. The authentic foundation, source, ablation, support, and P/PAD
actions happen before a carrier READ and are not experiment dispatches. They
therefore cannot be serialized as `PublicActionEvent`s, even though the
compiler and the released claim require committed child action followed by a
causally later public observation.

Second, `CompilerInput.compiler_phase` has only
`LINK_ADMISSION|NEW_ROW_ADMISSION`. No phase or separate canonical compiler
constructs the inverse source rows from the eight source events, and no phase
constructs/adopts `d_pad` from `P --p_0--> Q`. Nevertheless the S1 availability
sets contain source rows, the S2 deck contains `d_pad`, and `R_r` requires
source and PAD admission provenance. The text also never fixes which complete
source evidence/citation set maps a 3:1/1:3 contingency to the two inverse
rows. A `MemoryRow` has exactly two visible citation handles, so this cannot be
left to an implementation convention.

The provenance conjunction is additionally too broad for the corrupted
controls. A crossed SOURCE row and a DREAM payload-swapped link deliberately
do not state the authentic action--outcome/link binding. Requiring every such
fitted control row itself to be an authentic action followed by its own later
outcome is impossible. What can be authentic is the positive row and every
donor event, plus a presealed, audit-only derivation from them.

Minimal zero-fit repair:

1. Add a child-commit authorization/event type, with exact action-then-
   observation linkage and logical ordering, or define a separate closed
   `ChildCommittedActionEvent` used by the compilers.
2. Add exact `SOURCE_ROW_COMPILATION` and `PAD_ROW_COMPILATION` phases (or
   separately named pure compilers), including all input events, tie/reject
   behavior, output rows, visible citation-bundle semantics, and receipts.
3. Define every omitted public type and make the trace union use the actual
   compiler-decision type.
4. Split `R_r` provenance: FULL/source/support/PAD positive records must cite
   their authentic committed action and later outcome; corrupt fitted rows
   must instead cite an immutable presealed derivation whose donors each have
   authentic provenance. Donor identity and derivation remain audit-only.
5. Change A0's “seal ... PAD control event” to sealing PAD potential-outcome,
   handle, and schedule bytes. The authentic event itself must be appended
   only after the A1 child action.

This repair is necessary to show that the LoRA target was compiled from the
claimed public experience rather than inserted by a privileged materializer.

## Claim blocker 3: the goal byte cut and named goal control are not coherent

V4 says the first A/B actor-visible difference lies inside
`ActorEpisodeInput.goal`. Under JCS key order, `episode_handle` precedes
`goal`. If the two repeated-measure episodes have distinct episode handles,
the claim is false. If they reuse one episode handle, the contract must say
that it is a matched-pair handle rather than a unique episode identity;
otherwise two different inputs/traces reuse one immutable episode identifier.
This matters because an episode-specific opaque token is an alternative cue
for the route, defeating the assertion that the goal is the first cause of
redirection.

The named `CATALOG_ONLY_NO_GOAL` cell does not isolate goal dependence because
it also removes the carrier. It also invokes a “goal-neutral input” even
though `ActorEpisodeInput.goal` is non-null and no neutral `PublicGoal` form is
defined. The ordinary G_A/G_B pair is a useful goal-redirection assay only
after all non-goal actor bytes, including decode commitment and episode
identity, are proven equal.

Minimal zero-fit repair: put unique episode identity only in the audit
envelope and expose one explicitly defined matched-pair handle in both A/B
inputs, or otherwise define a non-goal public prefix whose equality is
unambiguous. Bind `o_goal` on the complete stored JCS bytes and require all
pre-offset bytes equal. Then either relabel `CATALOG_ONLY_NO_GOAL` as a mere
carrier-free conjunction negative, or define a legal goal-neutral schema and
run it with FULL mounted. A FULL-mounted goal-null or registered goal-field
intervention is inference-only and adds no fit.

With that repair, the two ordinary goals, exact route/query/action
redirection, route-validity predicate, B link cut, and link payload swap are
sufficient for the narrow goal-conditioned traversal claim. Without it,
episode identity and simultaneous carrier removal remain open explanations.

## Claim blocker 4: the “exact” generator and theorem lack a complete machine

The content-addressed package and independent-checker requirement are good
gates, but v4 does not yet specify enough bytes to build them independently.
Examples that affect the claimed theorem or visibility boundary include:

- `FRAME` accepts byte parts, but the root-nonce and training-RNG calls pass
  unencoded strings/integers/handles; byte order and widths are not given.
  The CLI seed is not explicitly required to equal the seed bound by the
  protocol.
- A path named by `protocol_sha256` is not itself a content address for the
  other package files unless `protocol.json` commits to the digest and role of
  every schema, roster, table, binding, fixture, and manifest. Receipts that
  are generated later also cannot be silently added inside an immutable
  digest domain.
- The “complete action/state geometry” omits X from its state list and does
  not give repeat transitions for the eight L/R source acts, the ablation and
  support arenas, experiment dispatch/outcomes, or their dead states. These
  omissions prevent canonical public traces and provenance checking.
- `PublicGoal` requires both read and action budgets, but G_A/G_B/G_D and the
  formal machine fix only READ budgets. Exact action budgets and the C initial
  budget/state are absent.
- The availability sets are prose sets rather than a complete
  request-to-canonical-row relation, and canonical `R*_K` is not enumerated.
  Exact candidate row bytes/citations for available and reserved rows are
  deferred. Therefore the independent BFS cannot yet reproduce every legal
  FOUND payload, citation cursor, action, success predicate, and cut.
- A root draws one z and materializes only the two h branches, while the live
  `SOURCE_READ_SWAP_C` requirement says “every h/z case.” V4 must say whether
  all-z is a Stage-0 compiler fixture or a live per-root repeated measure. It
  must not silently count unmaterialized z worlds in `R_r`.

Minimal zero-fit repair: publish a protocol appendix or the actual immutable
package that closes those definitions, then run the already-required
independent checker. The package root must commit to every immutable member;
derived receipts should live in a separately content-addressed result bundle.
Give exact encodings to every hash invocation, exact phase/action budgets and
transition rows, exact candidate/citation bytes and `A_K(request)` tables, and
an explicit scope for the 32-case C fixture versus live root branches. Only
then can the availability theorem, offsets, ACL/forbidden-field checks, and
immutable provenance receipts be evidence rather than promises.

## Mechanism disposition after the minimal repairs

| Mechanism question | V4 disposition |
|---|---|
| No graph-level `U -> C` shortcut | **PASS conditional on the complete transition fixture** |
| Live B mediation | **PASS**: ordered live link cursor forces `b_i` then `c_0` |
| Child-selected link admission | **PASS in concept; REWORK schema/provenance** |
| Delayed use of old A memory at D | **PASS conditional on valid old cut/swap and gated cells** |
| Outcome-specific new memory at D | **PASS conditional on exact compiler/PAD provenance** |
| Connected old+new traversal | **PASS** under availability and endpoint validity |
| Goal expansion/conditioning | **REWORK** episode byte cut and FULL-mounted goal control |
| Source read -> live dispatch -> outcome -> admission | **PASS in concept** via `SOURCE_READ_SWAP_C`; exact source compilation still missing |
| Six-fit maximum | **PASS**; no seventh trained carrier is required |
| Visibility/provenance closure | **REWORK** until schemas, compilers, transitions, and package digest close |
| Confirmatory causal components | **REWORK** because invalid controls currently score favorably |

## Promotion condition

V4 should not be promoted on the statement that it already “closes the two v3
audits.” It closes their architectural direction and preserves the desired
six-fit bound, but the four blockers above must be repaired and materialized
before TEXT, reader-model acceptance, or fitting. No additional M fit is
needed. After those zero-fit repairs, the contract would support the narrow
claim it states: compiler-mediated crossed source and selected-link carriage,
goal-conditioned typed traversal through a live B, and clean-base second-cycle
reconstruction that jointly uses the required old link and a causally later
outcome-specific new row.
