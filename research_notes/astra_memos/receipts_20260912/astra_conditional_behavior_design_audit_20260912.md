# L1 mathematical preimplementation audit — September 12, 2026

**Actionable specification clarifications, not an implementation verdict,
launch veto, or formal C11 gate. EDIT-STOP.** Only this note was written.
Read the two dated protocol documents; did not inspect Bernoulli's incomplete
corpus/tests, duplicate their implementation, or use GPU/network/Git.

Sources:

- `research_notes/analysis/2026-09-12_behavior_memory_bridge_and_level1_intertwining_protocol.md`, especially lines118–148 and171–225.
- `research_notes/analysis/2026-09-12_l0_to_h1_smallest_decisive_gate_sequence.md`, Gate1, especially lines70–123.

## 1. Replace literal “every shortcut scores exactly .50”

**The literal requirement is impossible.** Define action/outcome labels by
bits0/1. In PROSPECT let belief orientation be `b`, goal be `g`; the correct
action is `a=b XOR g`, and the predicted outcome is exactly `g`. Its full
decision is `J_P=(predicted action, predicted outcome, ACT)=(a,g,a)`.

On a balanced crossed square:

| Restricted information | Scored target | Best possible row accuracy |
| --- | --- | ---: |
| goal only | predicted outcome alone | **1.00**, by copying GOAL |
| goal only | full joint decision `J_P` | .50 |
| constant full output | `J_P` | **.25**, four equiprobable decisions |
| unique row index / unrestricted lookup | `J_P` | **1.00**, one label per index |

For REVISE write prior action `a`, predicted outcome `p`, observed outcome
`o=p XOR m`, where `m=0` means MATCH/KEEP and `m=1` MISMATCH/SWITCH. Then
`NEXT=a XOR m`; full decision `J_R=(m,m,a XOR m)` has four possible values.
Constant full-output accuracy is .25. Prior-action-only full-joint accuracy
is .50. Observed-token-only full-joint accuracy is .25 when `p` is also
balanced independently; on a square with fixed `p`, observed token alone
already determines COMPARE/POLICY perfectly, but not NEXT.

**Smallest interpretation:** enumerate the **best restricted-policy ceiling**
on the full joint decision, require **at most .50**, and report its exact
value—not equality to .50 and not each component's ceiling. For feature
projection `h`, the finite-table lookup ceiling is
`C(h)=sum_z max_y count(h(x)=z,J(x)=y) / N`.
This is a feature-class ceiling, not a requirement that every individual
policy, including deliberately wrong ones, score .50. Keep component scores
diagnostic; goal→predicted-outcome copying is expected, not a corpus failure.

Twin-pair pass rates need separate baselines: a constant decision passes
**zero** pairs whose correct decisions differ. Do not require pairwise .50
either. A shortcut can pass one twin family and fail the other; this is why
the two registered family gates remain separate.

## 2. Exactly32 held cases can supply16 pairs in EACH family

Use **eight crossed2×2 squares per operation**, not two disjoint32-case panels:

- PROSPECT vertices `(square,b,g)`: goal edges change only `g`; belief edges
  change only `b`. Each square contributes two edges to each family.
- REVISE vertices `(square,a,m)`, fixing `p` within a square and balancing it
  across squares: outcome edges change only OBSERVED; prior-action edges
  change the prior action in both PREDICT and ACT while holding `p,o,m` fixed.
  COMPARE/POLICY stay fixed on prior-action edges; NEXT exchanges.

Thus32 vertices,16 edges/family, with each vertex used exactly once in each
family. Every family edge must preserve all non-intervention prompt bytes.
The visible CASE identifier, wording and card-order nuisance settings must
be **shared across the square**; unique condition IDs belong in metadata,
not the prompt. Swapping belief bindings does **not** merely reorder the
same two card entries. Balance nuisance settings across complete squares.

The earlier “16 unseen cards × two unseen forms” cannot simultaneously mean
two different forms on each card's only two rows **and** a goal twin differing
only in GOAL. Minimal Gate1-compatible interpretation:32 crossed vertices,
with held forms balanced **across squares**, fixed within a square. Do not
quietly expand to64 held cases. With two actions/outcomes there are only two
bijective maps; “unseen cards” means held instances/wording, not16 new logical
truth tables or16 independent functions.

REVISE must have both legal action names available in a shared public
interface/card. If only the previous action is exposed and the other opaque
label is not otherwise defined, SWITCH is underdetermined. Do not recover
the other action from a private answer key or silently assume new labels.

## 3. Preserve128 training rows with literal target permutations

One concrete count-preserving interpretation of the earlier ambiguous
“semantic cards”:

- PROSPECT: four crossed squares × four condition vertices × four forms
  =64 rows. This means16 **card-plus-goal instances**, not16 distinct mappings.
- REVISE: eight crossed squares × four vertices × two forms =64 rows,
  equivalently16 outcome-twin pairs × two forms.

PROSPECT atomic instances receive16 presentations over four epochs; REVISE
atomic conditions receive8. A REVISE **pair** receives16 aggregate
presentations. The memo's “each semantic case16” needs this unit distinction;
do not invent extra rows to equalize these different counting units.
Total remains512 row presentations and128 updates at batch4/gradaccum1.

Register a coherent complementary map before scoring. A minimal literal
permutation is:

- PROSPECT: give `(b,g)` the complete AUTH target of `(b,1-g)` within its
  card-matched square. It chooses/predicts the non-goal consequence coherently.
- REVISE: give `(a,m)` the complete AUTH target of `(a,1-m)`.

This preserves complete target strings and marginals exactly; do not flip
only a tag and leave a contradictory action. DERANGED gold must come from
that declared rule, not be inferred from whatever it generates.

**Per-batch parity is stronger than global token balance.** There are32
closed target-swap pairs per operation in this construction. One P pair plus
one R pair per batch gives32 batches/epoch and permits deterministic row
interleaving. Keep the identical schedule in both arms; balance pair
orientation/template/position strata. An unrestricted row shuffle can split
swap pairs and break per-batch parity despite a perfect global multiset.
Audit the *actual* registered encoder/collator/epoch schedule, not an ideal
pre-shuffle order.

Require equality of the multiset of **complete supervised token-ID sequences
including EOS**, not just token totals or a bag of token IDs. Within each
swapped pair, verify equal native context length; then swapping whole targets
preserves total-length/EOS-position multisets in that batch. Check native
context/target/total lengths jointly, EOS offsets, masks, truncation and
loss-bearing padding. MATCH/MISMATCH or KEEP/SWITCH need not have equal native
lengths; a closed permutation handles that. Equal isolated nonce-token lengths
alone do not prove equal lengths in the actual rendered/masked positions.

## 4. Freeze baseline visibility; exclude tautological features

Allowed shortcut projections must be named exactly before enumeration:
constant output, first listed action, literal GOAL token, literal OBSERVED
token, prior action name, fixed surface-template ID, and a specified repeated
position feature such as batch slot—not an unrestricted absolute row index.
Report each applicable projection's joint ceiling, with unavailable features
marked N/A. A first-listed-action policy is not the same as a constant full
output: if it also reads that action's binding, its joint ceiling can be .50.

Do **not** call these restricted shortcuts:

- goal plus its matching belief-card row/index: already supplies the action;
- parsed prediction-versus-observation equality: already supplies COMPARE and
  POLICY; with the prior action and action alphabet it solves all of REVISE;
- selected/correct action, target length/EOS metadata, expected-branch flag,
  DERANGED target, or pair-coordinate ID derived by the generator;
- case-ID/absolute-row lookup with one target per key, or feature combinations
  containing the complete sufficient input to the intended procedure.

Their ceilings may legitimately be1.00; that tests an oracle/full-input
procedure or metadata leakage, not failure of nonce-label balancing.

**Teacher-forcing leakage also matters:** gold `PREDICT: a -> o` already
reveals the subsequent ACT; gold COMPARE already determines POLICY. Computing
action/KEEP log odds after those answer-bearing gold fields does not isolate
input use. Smallest clean interpretation: score the two complete registered
candidate continuations from the **same input-only prefix**, or a common
answer-independent stub, and difference their log odds across twins. Never
append different gold reasoning fields to the two scoring contexts. Register
which contrast supplies the1-nat operation gate (naturally belief twins for
PROSPECT, outcome twins for REVISE); report other contrasts without choosing
the most favorable one afterward.

## 5. Keep syntax, joint semantics and pair correctness distinct

Emit separate fields for surface/strict validity, each semantic component,
full joint semantic correctness, and strict-and-joint correctness. Missing,
duplicate or ambiguous semantic fields fail that endpoint; do not use best
occurrence, synonyms, or prose interpretation to rescue them. Benign surface
deviations should not be silently equated with wrong cognition. Denominators
stay32/operation; invalid outputs are not discarded.

A twin pass needs both endpoints correct under the assigned joint rule and
the required relation between them—not merely two different outputs.
Explicitly register whether strict surface validity is additionally required
for a pair; report both if ambiguous. For belief twins, the predicted outcome
stays the goal while the selected action changes; do not require every field
to flip. For prior-action twins, COMPARE/POLICY remain fixed.

Threshold arithmetic must be literal: `.95` of32 means31, not30; `.90` of128
means116; `.05` spill on16 controls permits **zero**, not1/16. The older final
surface `.95` and Gate1's30/32 are different cutoffs. Use Gate1 as the named
operational gate, record its separate strict-validity denominator/predicate,
and do not disguise30/32 as95%. If surface and strict validity are identical
predicates on32 cases, the strict gate makes the effective requirement31/32.

**Immediate handoff:** implement the8-square edge checks, joint restricted
ceiling `<=.50` with exact values, frozen feature projections, literal closed
target swaps and actual native batch parity, and explicit scoring/rounding
denominators. Main should record these operational interpretations; this
audit neither chooses an LR nor alters launch authority or scientific claims.

**EDIT-STOP.**
