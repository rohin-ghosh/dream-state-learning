# Fresh statistics, visibility, and exact-execution audit of M-core v3

Date: 2026-09-12 UTC

Scope: independent fresh-context audit of only
`research_notes/analysis/2026-09-12_m_core_minimal_exact_two_cycle_design_v3.md`.
I treated statements about future Stage-0 receipts as requirements, not as
evidence that those receipts already exist. I did not inspect or change builder
code, jobs, GPU state, coordination, or the v3 source memo.

## Verdict: REWORK before text/model work or any fit

The inferential skeleton is substantially sound: the independent unit is the
root; DEV, TEXT, and confirmation are separated; the five ordered sign-count
tests are legitimate under the stated iid-root target; the binomial arithmetic
is correct; and the maximum fit counts are correct. The design is nevertheless
not yet an executable exact contract. Several objects that determine bytes,
legal transitions, stochastic coupling, and visibility remain prose-level or
internally inconsistent. Consequently a deterministic CPU materializer and an
independent checker cannot be written from v3 alone.

These are specification blockers, not requests for another trained condition.
Every repair below is zero-fit.

## Checklist disposition

| Area | Disposition | Reason |
|---|---|---|
| JCS and public/audit visibility | **REWORK** | No closed schemas or field ACL; raw bytes have no JCS representation; audit labels occur in the trace-shaped object. |
| Side-channel noninterference | **REWORK** | The visible alphabet, clock access, padding deadline, and overrun transition are not executable. |
| Exhaustive adaptive READ theorem | **REWORK** | The stated model state omits returned payload/citation state, the success predicate and budgets are not fully encoded, and several transitions/controls are undefined. |
| PAD token/loss/mask/visit/position/batch/step equality | **REWORK** | The required equality is directionally right but its allowed-difference mask and full tensor/batch fixtures are absent; RNG is condition-specific. |
| Root/randomization/Latin schedule | **REWORK** | The generator and schedule are not instantiated, and independent rotations do not guarantee the claimed exact balance. |
| DEV/TEXT/confirmation separation | **PASS** | Separate presealed manifests, nested DEV prefixes, adverse filling, and no confirmation extension are explicit. |
| `S/M/U/W/F/R` estimands | **PASS WITH BINDING FIX** | The scalar algebra and noncompensation are coherent, but some referenced intervention cells are not defined exactly. |
| Source labels | **PASS WITH FIXTURE FIX** | Authentic counterfactual labels remain frozen for the derangement; public aliases and nuisance fixtures still need byte realization. |
| Fixed-sequence tests | **PASS** | `S -> M -> U -> W -> R` at one-sided `.05`, stopping confirmatory rejection at the first non-rejection, strongly controls FWER if each root indicator is iid. |
| Binomial/Clopper--Pearson arithmetic | **PASS** | `P[Bin(16,.5)>=12]=2517/65536=.0384063720703125`; 11 successes do not reject. |
| Fit counts | **PASS** | 3 S1 plus 3 S2 per survivor; maxima 12 for the two-root kill, 48 for all DEV, 96 for confirmation, and 144 combined. |
| Measured-only cost | **REWORK** | A single `N_fit*t_fit` is not valid for heterogeneous exact decks/devices, and staged stops reduce work for reasons besides per-root S1 futility. |

## Blocking findings and minimal zero-fit repairs

### B1. There is no closed deterministic generator or canonical-byte package

The root law names a “registered generator version,” `H`, alias pool, event
strata, finite rotation set, catalog-permutation cell, and rejection procedure,
but supplies none of their byte-level definitions. In particular:

- `k` has no sampling/assignment law; the root seed, PRNG algorithm/version,
  draw order, domain separators, rejection order, and `H` input framing are
  absent;
- the three-versus-three decoy-class assignment is not a root draw, and the
  allegedly complete ablation table gives no binary outcome for the nuisance
  trial;
- foundation actions/outcomes, support fixtures, event-order strata, the alias
  pool bytes, and the reserved candidate fillers are not enumerated;
- immutable ID derivation lacks an encoding/hash/opacity rule, so including
  `derivation_kind` in the derivation tuple may make an audit-only label visible
  through a row or citation ID;
- the candidate-order permutation set and its query-cell assignment are not
  defined; “every catalog order” could mean the registered subset or all
  `32!` permutations;
- the qualified tokenizer, reader prefix, token IDs, row renderer, threshold,
  and `W*` are deliberately deferred, so no current artifact binds the lengths
  and tensor equalities on which root admission depends.

The displayed objects are pseudostructures, not JSON Schemas or canonical
instances. JCS also has no byte-string type, so a JCS `Trace` cannot contain
`exact_request_bytes` or `exact_return_bytes` without a specified encoding.
The statements about `o_goal` and `o_outcome` are plausible requirements, but
their values and even the first differing row subfield cannot be checked until
real canonical row IDs/citations/payloads exist.

Minimal repair: before Stage 0, commit one versioned, content-addressed
**materialization package** containing:

1. RFC 8785 JSON Schemas and canonical example bytes for every public,
   training, compiler, scorer, and audit object; encode embedded bytes as a
   specified base64url or hex string, or store their SHA-256 plus a separate
   blob;
2. an explicit counter-based PRNG/hash construction, seed and domain framing,
   draw/rejection order, ID encoding, alias bytes, decoy allocation, all binary
   outcomes, order strata, rotation/permutation tables, and candidate fillers;
3. the exact qualified `W*`/tokenizer/renderer/reader artifact digests and
   parameters once they exist; and
4. a deterministic CPU command that emits the complete fixture corpus and a
   second implementation that verifies its digest, schemas, offsets, truth
   tables, and zero-diff receipts.

This does not require a fit. Until `W*` is qualified, the materializer should
exit with a named unmet prerequisite rather than silently choosing a recipe.

### B2. Public, scorer-visible, compiler-visible, and audit-only bytes are not separated exactly

The prose declares many fields audit-only, but there is no field-by-field
capability matrix or distinct schemas enforcing that declaration. The proposed
`Trace` includes `condition` and `h_or_null` in the same JCS object described as
the canonical scorer input. Those are audit labels and are unnecessary for
validating a public execution; allowing the scorer to consume them permits a
condition- or truth-aware implementation. `root_id` may be needed to select a
graph, but that lookup also needs an explicit non-branching interface.

Visible row and citation IDs are another unresolved channel: they necessarily
change under derangement and h, while their construction includes
`derivation_kind`. “Opaque” and “role-independent distribution” are not exact
noninterference properties unless the visible allocation table is fixed before
roles and its audit mapping is inaccessible.

There is also no complete Phase-C public trace. `SOURCE_INVERSE` returns an L/R
propensity row, while the general rule says every executed action must be cited
by a FOUND row. The next committed action is an experiment `E0...E3`, which is
not a payload allowed by that row. Declaration, predictions, outcome-to-row
map, experiment dispatch, public observation, posterior calculation, and
admission have no canonical schemas or exact transition sequence. Thus R item
9 cannot be scored by the declared trace scorer, and the “same bytes through
dispatch” h-twin claim is not checkable.

Finally, `d_pad` must be extracted in audit validation even though P/Q are
forbidden actor anchors and the complete public query language has no PAD
validation phase. That operation is either an undeclared query or an
audit-only extractor; v3 does not say which.

Minimal repair:

- split `PublicExecutionTrace` from an `AuditEnvelope`. The pure scorer accepts
  only the former plus a read-only public graph handle. Put condition, hidden
  `h/b/z`, donor maps, derivation kinds, expected answers, device/order labels,
  and root-truth lookup in the latter and add forbidden-field tests;
- allocate visible row/citation handles from a pre-role, token-isomorphic table
  and keep the handle-to-provenance map exclusively in the audit envelope;
- publish the exact C state machine and objects. Either authorize `E` through a
  public menu edge cited by the returned L/R row, or add a separate canonical
  `DISPATCH_EXPERIMENT` event with a frozen authorization rule. Bind the public
  posterior algorithm to public bytes only and test all 32 cases by capability
  denial, not merely by expected table output; and
- define PAD extraction as a separate audit-only interface unavailable to the
  actor, with its own schema and receipt. Do not add a hidden seventh public
  query type.

### B3. The side-channel theorem lacks an observable machine

“Padded to the frozen duration bucket” does not define a proof. The bucket
value/source, actor clock and scheduling capabilities, release instant,
charged-call path for absent carriers, and overrun/timeout transition are
missing. If the actor can observe a clock, callback order, exception, or early
root termination, backend score time can remain visible even when a pad object
has fixed length. Declaring timeout a root failure is not enough unless the
actor never resumes and cannot branch on that failure.

Minimal repair: define the actor-observable alphabet and an explicit padded-RPC
transducer. All calls, including MISS/cuts/carrier-free controls, must enter the
same 32-score path and release exactly at a registered boundary. Remove actor
clock/process/cache/network access; make overrun an audit-envelope terminal
event before actor resumption. Exhaustively compare public transcripts after
alpha-renaming and add a delayed-backend fake-clock test. Hardware timing can
remain a later validation, but the zero-fit interface theorem must have these
exact semantics.

### B4. The adaptive READ theorem is not yet the theorem stated

The proposed state contains status history and “returned anchors,” but not the
actual returned row ID/payload, cited action sequence, row lifetime, or which
part of a two-action link remains executable. Enumerating FOUND/MISS/BLOCKED
classes therefore cannot prove all payload-dependent adaptive policies. Initial
budgets for each production/control phase are implicit rather than table data.

The canonical scorer says that a trace passes when it follows graph transitions
and reaches the target, but the public transition graph allows every entrance
`a_j` to reach `T_A` or `T_B`. It does not encode the additional goal predicate
that the first entrance must equal `route(required_route_cue)`. Without that
predicate, a wrong-cue route followed by its own valid link and terminal reaches
the nominal target, contradicting the claimed unique B traces.

Other machine holes are material:

- the seven `ATOM_SUCCESSOR(B)` shared-action alternatives and reserved fillers
  are absent from the graph that is called complete;
- it is unspecified which FULL hit `READ_BINDING_SWAP` changes, and the sole
  public action `c` at B has no legal wrong shared-action counterpart;
- R refers to an undefined `GOAL_TWIN` result;
- `OLD_CUT_D_h`, `NEW_CUT_D_h`, `READ_BINDING_SWAP_D_h`, and `WRONG_ROOT_h` in
  `F_r` are not exact condition IDs from the control table; and
- the D binding swap does not say whether it corrupts the old link, the new row,
  or both. One combined failure would not establish both contents separately.

Minimal repair: publish one machine-readable finite transition system with
explicit initial states/budgets, full row payload in state, citation
consumption/lifetime, malformed-action absorbing failure, exact goal-validity
predicate, carrier-specific return relation, and every candidate action's
syntax/transition. Run an independent BFS/model checker over histories; policy
enumeration can then be represented by exhaustive action/query branching.
Publish witness traces for the 3/4/2 upper bounds and shortest-path/unreachability
certificates for every lower bound and cut.

Bind every control to an exact transition. Define `GOAL_TWIN` as either the
ordinary registered A/B alpha-renamed pair (preferred, no extra control) or a
real intervention. Restrict each binding swap to a named hit having a legal
wrong action. At D, use separately named old-link and new-row swaps and include
both in `F_r`/`R_r`; these are inference-only additions and require no fit.

### B5. Condition-specific RNG defeats the claimed matched isolation

The fit seed is `H(protocol,root_id,build_id)`. Since `build_id` is the
condition, FULL, source-deranged, DREAM-deranged, new-h0, new-h1, and PAD receive
different minibatch/dropout/random streams. Equality “in law” does not make a
realized within-root contrast content-only. `S_r`, `M_r`, and `W_r` can change
because of fit RNG, even if row counts, masks, positions, batches, and step
counts are nominally equal. That contradicts the repeated claim that only the
named binding/row differs.

Actor/child decoding and inference seeds are not specified at all. In
particular the two h worlds must make the same C declaration and dispatch under
identical public history; independent sampling could make them diverge before
the outcome.

Minimal repair: use common random numbers within each matched family. Derive
training RNG from `(protocol,root_id,stage,stream,step_or_slot)`, excluding
condition/build ID, and verify identical initialization, deck-slot order,
batch membership, dropout masks, and deterministic-kernel settings outside the
allowed payload-token positions. Bind actor/child decoding parameters and RNG
similarly, with the h twins cloned from one pre-dispatch process/RNG snapshot.
If common RNG is intentionally rejected, the claim boundary must instead say
the estimands include independent optimization/inference noise; the current
content-isolation language would then be false.

### B6. The PAD equality gate has no exact allowed-difference object

The intended tensor/work matching is strong, but “every diff outside payload
token IDs is zero” is undefined. `n0`, `n1`, and `d_pad` differ not only in an
action alias: C versus P, D versus Q, row IDs, and authentic citation/event IDs
may occupy earlier token positions. A token-isomorphic alias triple for the
named row/action does not prove equality of the entire rendered example.
Likewise “batch exposure” and “optimizer work” cannot be derived merely from
row-level length equality, especially while RNG differs.

Minimal repair: materialize, before fitting, the exact per-example
`input_ids`, `attention_mask`, labels, loss mask, view/visit IDs, deck slot,
batch index, optimizer step, and RNG-stream indices for all three S2 builds.
Publish a same-shape allowed-difference bitmap naming every semantic payload
position (including endpoint/action/opaque handle/citation positions), require
bitwise equality everywhere else, and require equal supervised-token counts
and mask coordinates. Do the analogous S1 paired receipts. Root rejection on a
failed match is appropriate and needs no extra PAD fit.

### B7. The Latin/device/order law is not an instantiated randomization

One independently drawn Latin “rotation” per root cannot by itself make every
arm/control/device position balanced within that root when each trained arm is
fit once. Independent per-root rotations also provide balance only in
expectation across 16 roots, not the exact balance claimed in the prose. The
number of positions/devices, schedule matrix, behavior when S2 is skipped,
inference repetition count, and mapping of controls to positions are absent.
If instead rotations are dealt without replacement to force cohort balance,
the complete root objects are no longer iid as currently asserted.

Minimal repair: publish the actual schedule matrix and rotation set, separately
for fit order, device assignment, and inference/control order. The least
disruptive statistical choice is independent uniform rotation/permutation per
root, explicitly claiming balance in expectation and targeting probability
over that iid schedule. Report realized positions. Treat shared-state/order
departures as global instrument failures so the root indicator remains a
deterministic function of its iid complete root object. If exact blocked cohort
balance is preferred, replace the simple iid-binomial justification with a
test valid for that blocked assignment.

### B8. The cost equation is not measured-only as written

`N_fit*t_fit` assumes one common fit duration, but S1 and S2 decks differ and
the schedule permits device heterogeneity. A duration measured for one “exact
`W*` deck” cannot be multiplied across other exact deck/device classes without
an equality receipt. Moreover, work may stop because Stage 0 or TEXT fails,
the two-root S1/S2 kill fires, widening fails, or confirmation is never opened;
S1 futility is not the only reduction from the 144-fit maximum.

Minimal repair: define actual measured training device-time as

```text
C_train_actual = sum over completed fits f of measured_device_seconds(f)
```

and report it only from job receipts, stratified by exact deck class and device.
A prospective maximum may be computed only after timing every registered
deck/device class, as the sum of its measured bound times its maximum count.
Keep action, inference, reset, validation, serialization, queuing, and process
startup as separately measured quantities. The numerical fit-count maxima in
v3 need no change.

## Statistical verification

The five scalars have the intended noncompensatory sign semantics:

- `S_r>0` requires authentic source performance to exceed the frozen-label
  source derangement;
- `M_r>0` requires FULL to beat DREAM derangement for both B goals;
- `U_r>0` requires positive FULL-versus-OFF differences at both B goals and C;
- `W_r>0` requires the matching new carrier to beat equal-work PAD in both h
  worlds; and
- once its intervention IDs are bound, `F_r>0` requires every named D
  necessity/specificity contrast in both h worlds.

Missing/skipped/process-failed cells set to zero cannot manufacture a positive
contrast. `R_r` correctly makes the controls, chronology, orthogonal
preservation, and all earlier gates noncompensatory. The frozen authentic
source label for SOURCE_DERANGED avoids post-treatment relabeling.

For a tested component let `K=sum_r 1[delta_r>0]`. Under the registered iid
root null `Pr(delta_r>0)<=.5`, the exact one-sided p-value is
`sum_{j=K}^{16} C(16,j)/2^16`. At `K=12` this is exactly
`2517/65536=.0384063720703125`; at `K=11` it is `6885/65536`, so 12 is the
correct cutoff. The one-sided 95% Clopper--Pearson lower endpoint should be
bound as `Beta^{-1}(.05;K,17-K)` for `K>0` (zero when `K=0`); for `K=12` it is
approximately `.5156035789`. These are componentwise intervals. P-values and
intervals after the first fixed-sequence non-rejection may be tabulated, but
must be labeled descriptive rather than confirmatory rejections.

This exact binomial claim still depends on B7's repair: complete confirmation
root objects, including all random streams and schedule assignment, must truly
be iid, with shared execution departures treated as global invalidation rather
than correlated root-local noise.

## Release gate

Do not begin TEXT, reader-model acceptance, or any M fit until B1--B7 have a
content-addressed zero-fit fixture/receipt bundle and an independent checker
passes it. B8 must be repaired before any resource estimate is published. No
additional trained arm is needed; the only suggested new cells are inference-
only D content swaps.
