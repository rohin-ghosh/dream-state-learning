# Fresh-context causal/graph/mechanism audit of M-core v3

Date: 2026-09-12 UTC

Scope: independent adversarial review of
`2026-09-12_m_core_minimal_exact_two_cycle_design_v3.md` only. I did not edit
the design, builder source, jobs, GPU state, or coordination records.

## Verdict: REWORK

V3 has the right finite graph and the right broad six-build decomposition, but
the literal contract does **not yet** justify its exact-isolation language.
There are four claim-blocking defects: matched fits deliberately use different
fit RNGs; the exhaustive-reader theorem is inconsistent with its own return
quantifier; the public/private graph and initial episode-byte boundaries are
not closed; and `WRONG_ROOT` is neither a defined hit-matched intervention nor
guaranteed to fail. Two further closure defects concern S2 PAD identity bytes
and the un-intervened source-to-experiment bridge at C.

These are specification defects, not requests for another trained carrier.
All repairs below can be made before fitting and preserve the maximum of six
trained builds per attempted complete root.

## What the literal graph does establish

Conditional on the actor not receiving the adjacency/transition table and on
`FOUND` being restricted to rows actually available from the mounted carrier,
the graph is sound:

- For either B goal, `ROUTE_BY_CUE` supplies the entrance action, a stored
  `LINK_SUCCESSOR` supplies the two ordered middle actions, and
  `TERMINAL_TO_TARGET` supplies the target-specific final action. That is a
  valid three-READ construction. Replacing the link by its two atoms gives a
  valid four-READ construction.
- At D, starting at `U_(u_D)` makes the old selected link necessary to reach C,
  and the h-specific new row necessary to choose the sole successful final
  action. With the citation rule, two READs suffice and removing either row
  blocks the trace.
- Because `u_D` is chosen from `{u_A,u_B}`, the delayed trace really reuses one
  of the child-selected links; it is not a disconnected second-cycle task.
- The source event table is a genuine within-root action--outcome crossing.
  The 2:2/2:2 source derangement preserves action counts and total outcome
  counts while destroying the informative action--outcome contingency. C is
  scored against the authentic orientation rather than a relabelled corrupt
  truth.
- The `(b,h,z,E)` table correctly prevents `z==h` from turning a nuisance
  observation into knowledge. The two h twins cross the same source
  orientation with opposite outcome-specific admissions.
- The DREAM arm starts from the child's exact sealed two-ID output, retains two
  link-shaped records, and changes the link binding. The public necessity
  table makes selection mechanically recoverable, and v3 correctly limits the
  claim to a child-selected, evidence-indicated set rather than child-specific
  intelligence.
- A disconnected, gradient-bearing PAD is the correct *kind* of equal-work S2
  baseline. `NO_SLEEP2` is correctly labelled diagnostic rather than
  equal-work.
- Clean-base reconstruction and the D old/new cuts support cumulative
  reconstruction and final joint use, not in-place adapter growth. The stated
  claim boundary gets this right.

Those conclusions become unconditional only after the blockers below are
repaired.

## Claim-blocking defects and minimal zero-fit repairs

### 1. FULL and controls differ in fit randomness (and may differ in device)

Section 1.1 defines `fit RNG = H(protocol, root_id, build_id)`. Because
`build_id` distinguishes FULL, SOURCE-deranged, DREAM-deranged, h0, h1, and
PAD, every causal contrast changes both semantic training content and the
complete stochastic optimization trajectory. Matching a *seed law* is not
matching the realized nuisance. With one fit per condition per root, an
observed FULL/control difference can therefore be caused by dropout,
minibatch, or other fit randomness. The same problem applies to `S_r`, `M_r`,
`W_r`, and all D contrasts. A one-rotation-per-root device schedule also does
not make each condition device-balanced within that root.

Minimal repair: define a common-random-number seed keyed by
`(protocol, root_id, fit_family)` and explicitly excluding condition/build
identity. Use the same ordered deck slots, minibatches, dropout draws,
deterministic-kernel settings, and physical device/software image for all
three S1 members, and separately for all three S2 members. Artifact IDs may
still contain `build_id`; optimization RNG may not. Rotate the whole matched
triplet across devices between roots rather than placing its members on
different devices. Publish pairwise optimizer-input and realized-RNG receipts.
This adds zero fits.

### 2. The stated exhaustive READ theorem does not entail the minima

Section 4.4 says the transition system explores every possible
`FOUND/MISS/BLOCKED` return. Under that quantifier, an atoms-only actor can
receive a correct `LINK_SUCCESSOR` FOUND and use the same three-READ route as
FULL. Likewise, a carrier with a removed row can receive a spurious FOUND.
The 32-slot scorer always presents all semantic alternatives, so syntax alone
does not prevent such a return. Stage 0 cannot prove facts about false-positive
behavior of a later fitted neural reader.

Minimal repair: publish two explicitly separate results.

1. A formal graph theorem parameterized by an availability relation, with
   `FOUND(row)` legal only when that canonical row is a member of the specified
   ideal carrier. This proves the 3/4/2 minima and cut unreachability for the
   ideal FULL, ATOMS, and row-deleted carriers.
2. Model-level acceptance tests that reject a root if the qualified reader
   returns any unavailable bypass row, including an atoms-only link or a row
   suppressed by a cut.

Do not describe (1) as enumerating unrestricted possible FOUND payloads, and
do not describe (2) as a zero-fit theorem. No added trained M arm is needed;
the existing exact-text and inference-cut cells suffice.

### 3. Graph visibility and episode-level noninterference are not exact

Section 2 calls node/action types and deterministic transition semantics
public, while Sections 4.1 and 7.1 give the backend/scorer the root graph. If
the actor or neural candidate scorer is also given the adjacency table, the
correct `U_i -> b_i`, terminal, and h-world successor relations can be read
from the public graph rather than recovered from the carrier. Opaque aliases
help only if the serialization exposed to the actor/reader does not reveal the
slot relation. The current text does not provide that byte-level visibility
table.

Also, the claimed first A/B-dependent actor-visible byte cannot be inside
request 1: the actor has already received different complete goals `G_A` and
`G_B`. The request-prefix check therefore omits earlier actor-visible input.
For C, the root law does not bind actor decoding RNG, so “same bytes through
dispatch” does not by itself force the same pre-outcome declaration and
experiment in both h twins.

Minimal repair:

- Define one canonical `ActorEpisodeInput` containing every initial goal,
  state, legal-action surface, catalog/API object, system prompt, model ID, and
  decode configuration. State that only current-state observations and
  post-action transitions are public; adjacency, slot indices, route
  bijections, h, expected traces, and the scorer's truth graph are confined to
  the environment/scorer process. Give the candidate scorer the request and
  candidate bytes only.
- Prove the visible node/action/row-ID aliases are token-isomorphic and jointly
  independent across semantic roles, not merely marginally permuted.
- Bind `o_goal` over the complete episode-input byte stream, where the intended
  A/B difference actually first occurs. Retain the D prefix claim only after
  hashing every process input before return 2.
- Make actor/reader decoding deterministic or use common inference draws keyed
  without condition and h. Publish a byte-identical C twin transcript through
  the committed experiment action, before the public outcome diverges.

### 4. `WRONG_ROOT` is undefined as a matched causal control

“Source-disjoint carrier with fixed slot mapping” does not say how donor node,
action, row, goal, and citation IDs enter the recipient namespace. A raw donor
will usually MISS for root-identity and vocabulary reasons, so it differs from
FULL in availability, all old/new content, fit RNG, and possibly device. If a
role-preserving isomorphism is intended, an independently drawn donor can
coincide with the recipient on source orientation, selected links, or final
action. Thus “every root-specific trace fails” is not entailed by the root law.
Nevertheless `WRONG_ROOT` is included inside `F_r` and mandatory carrier-origin
gates.

Minimal repair: choose one of two honest contracts.

- Treat raw `WRONG_ROOT` as an explicitly unmatched specificity diagnostic,
  permit MISS, remove it from `F_r`, and let the already hit-matched B/D
  binding swaps plus old/new cuts carry the causal claim; or
- Preseal a source-disjoint donor and a role-blind isomorphism into the
  recipient public namespace, require hit/status/length/query/work parity, and
  construct fixed-point-free mismatches for every tested critical payload.
  Put this donor/mapping law in A0 and acknowledge that the resulting control
  is a mapped wrong-content intervention, not an unconstrained random wrong
  root.

Either repair adds zero per-root fits if already trained source-disjoint donor
carriers are reused under the presealed law.

### 5. Literal S2 PAD byte equality conflicts with immutable provenance

Section 5.3 requires every diff outside payload token IDs to be zero. But n0,
n1, and PAD arise from different authentic events, require different immutable
row/event IDs, and carry different endpoint/action identities. Earlier
sections require an immutable ID to name exactly one byte string. Therefore
raw token equality outside an undefined “payload” cannot simultaneously hold
with truthful distinct provenance. If only length, masks, counts, and positions
are meant to match, the current zero-diff sentence overclaims.

Minimal repair: define the exact field projection called `payload`; publish
both raw and registered-alpha-normalized diffs; require raw identities to stay
distinct; and require equality only of schema, token-position classes,
lengths, loss masks, visits, deck/batch positions, optimizer draws, and reader
envelopes after role-independent alpha-renaming. Keep true provenance
audit-only. If IDs/citations enter gradient or scorer bytes, they must use
presealed token-isomorphic opaque aliases and be included among the declared
intended semantic differences. This preserves PAD's equal-work purpose
without pretending the three truthful rows are byte-identical.

### 6. The actual source-to-experiment crossing lacks a C intervention

SOURCE-deranged and S1-OFF are tested on destroyed inverse probes, but only
FULL enters the live `declaration -> experiment -> public outcome ->
admission` branch. The global binding-swap description is instantiated in the
acceptance list at B and D, not at live C. Consequently v3 jointly observes a
correct source probe and a correct live experiment, but does not directly show
that changing the returned source action changes the live family and prevents
admission.

Minimal repair: add an inference-only destroyed `SOURCE_READ_SWAP_C` twin. On
the live C request, replace the FULL inverse return by the opposite L/R row
with identical hit/status/length/query envelope, require the cited action to
open the nuisance family, and require `NO_ADMISSION` for every h/z case. Add
this cell to `R_r`. It needs no fit and makes the source -> action -> public
outcome -> S2 admission crossing explicit.

## Controls after repair

`S1_OFF`, `GOAL_ONLY`, link/old/new cuts, and carrier-free cases are deliberate
availability interventions and necessarily expose MISS instead of FOUND. V3
already says they are not hit-matched content controls; they remain valid for
necessity if that limitation is preserved in every claim. DREAM and source
derangements, READ binding swaps, and the S2 PAD comparison are the content or
equal-work controls and therefore require common realized nuisance, not just
the same distributions. `CATALOG_PERMUTE` is a sound order-leak check if the
candidate scorer is deterministic and never receives the permutation index.

## Maximum and ceiling statements

The fit-count arithmetic follows from the declared no-rerun/futility rules:
three S1 builds plus three S2 builds give at most six M fits per root, eight
DEV roots give at most 48, sixteen confirmation roots give at most 96, and the
combined fitted M program gives at most 144. This excludes writer
qualification and the untrained text stage, as the memo should state at each
use of the maximum.

Two nearby claims do not follow:

- “Smallest defensible” is a global minimality statement; v3 constructs a
  six-build design but does not enumerate or rule out all lower-build designs.
  Replace it with “this proposed defensible design uses at most six.”
- `N_fit * t_fit` is not an exact cost maximum unless every S1 and S2 deck has
  the same measured duration or `t_fit` is explicitly the maximum over all
  build types. Use the sum of build-specific measured durations (or
  `3*t_S1 + 3*t_S2` per complete root) instead.

The mechanical DREAM policy reaches 100% only conditional on a complete valid
registered evidence table. Child omissions are already adverse root failures,
so the wording should retain that conditioning. The `1/28` uniform exact-two
chance construct and the 12/16 binomial threshold are otherwise correct.

## Promotion condition

After the six zero-fit repairs above, v3 would support the narrow claim it
states: compiler-mediated source and selected-link carriage, typed functional
READ use, a causally later public outcome followed by clean-base cumulative
S2 reconstruction, and final old+new use. Until then, the exact causal claims,
finite-reader theorem, and GPU/scientific-claim gate should remain closed.
