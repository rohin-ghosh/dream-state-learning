# M-core v2: minimal crossed two-cycle THINK--DREAM--SLEEP relay

Date: 2026-09-12 UTC

Status: **superseded by**
`2026-09-12_m_core_minimal_exact_two_cycle_design_v3.md`. This v2 note is kept
only as design history and must not be implemented or used to authorize an M
fit. It changes no builder source, benchmark, child, model, adapter, job, GPU
state, coordination, claim, or release.

## Verdict

The fresh audit was right about all five identification failures. A clean
minimum still needs only **six fixed-seed fits per successful root**, but they
must be allocated differently and staged:

```text
SLEEP-1 (run first)
  1. FULL_OLD
  2. SOURCE_DERANGED_OLD
  3. DREAM_DERANGED_OLD

SLEEP-2 (run only after every S1 kill gate passes)
  4. FULL_NEW_h0
  5. FULL_NEW_h1
  6. FULL_OLD_PLUS_PAD
```

The root is the presealed `h=0/h=1` outcome-twin pair. It shares the same
public childhood, DREAM, and S1 adapters. The two truthful public outcomes
produce different new rows and therefore require two distinct S2 adapters.
`FULL_OLD_PLUS_PAD` is a matched clean-base S2 rebuild, not the old S1 adapter,
and isolates training the new row from merely training again.

The repair also makes the two upstream interventions orthogonal:

- `SOURCE_DERANGED_OLD` changes only a crossed, repeated, within-situation
  child-action/public-outcome contingency. It retains the exact authentic
  DREAM links.
- `DREAM_DERANGED_OLD` retains every authentic source row but binding-swaps
  the child's selected links into schema-, slot-, hit-, and dose-matched false
  links.

Source is identified at Phase C; DREAM is identified at Phase B; the second
write is identified at Phase D. The corrupt S1 arms are not rebuilt at S2.
That avoids spending fits on a structurally doomed total chain and avoids
claiming their D failures as separate evidence.

## 1. Exact root object and independent unit

One root is an immutable potential-outcome object containing:

```text
root nuisance nonce                 k
eight symmetric path lanes         i = 0..7
two presealed useful lanes          u_A, u_B
one presealed delayed lane          u_D in {u_A,u_B}, independent of h
source-contingency orientation      b in {0,1}
nuisance outcome bit                z in {0,1}
truthful outcome twins              h in {0,1}
all aliases, presentation rotations, event schedules, future goals,
interventions, fit/data/inference order, and RNG counters
```

`h=0` and `h=1` are repeated counterfactual branches inside one root, never two
independent observations. Goals, calls, paths, renders, checkpoints, and
surface rotations are also repeated measures. Independent `N` is the number
of source-disjoint root objects.

Every actor-visible node, action, relation, event, link, candidate, and row ID
is derived from `(k, object_class, slot, derivation_kind)` and independently
permuted. An ID names one immutable canonical object. A shuffle or twin with
different bytes receives a different derived ID and cites its unchanged source
objects; “same ID with changed payload” is always invalid.

## 2. Symmetric path geometry and non-syntactic DREAM

### 2.1 Path graph

The hidden graph has eight symmetric lanes:

```text
a_i: S -> U_i                  for i=0..7
b_i: U_i -> B                  for i=0..7
c:   B -> C
t_A: C -> T_A
t_B: C -> T_B
```

All `U_i` have the same public type, degree, source frequency, age stratum,
record schema, byte length, and alias distribution. Every candidate pair
`(b_i,c)` is endpoint-composable and has the same exposed endpoint syntax.
Endpoint joining therefore returns an eight-way tie; it cannot reveal
`u_A/u_B`.

Phase-B goals start from the same public state `S`. Goal A's ordinary public
constraint makes lane `u_A` the only valid route to `T_A`; goal B analogously
uses `u_B` and `T_B`. Those goals and route blueprints are presealed but absent
from every Phase-A and DREAM capability. A later Phase-D goal starts at the
same presealed `U_(u_D)` in both outcome twins and targets `D`; `u_D` is chosen
independently of `h`. Its unique minimum proof is:

```text
old link (b_u + c) -> new row n_h: C -R(7+h)-> D
```

The old link and `n_h` are each separately necessary.

### 2.2 Public evidence available to DREAM

Before DREAM, the child actually executes a matched evidence block for every
lane. Each lane has the same number and order class of joint, left-only, and
right-only public tests. All eight joint actions succeed equally often, so raw
co-use frequency and reward count tie. For the two useful lanes only, matched
single-component ablations show that both `b_i` and `c` were necessary. For
the other six, the joint success is fully explained by a single component or
a registered nuisance route. The left/right explanation is balanced across
decoys.

These are ordinary child actions followed by causally later public outcomes.
No theorem label, necessity bit, link, goal, future support action, score, or
answer appears. The exact evidence schedule is fixed before the child acts;
missing child actions remain adverse and are never executed by the harness.

At the DREAM cut the child sees the public evidence and an order-permuted
roster of the eight pair IDs. All eight candidates are indistinguishable by
endpoint composability, type, degree, slot count, byte length, age, frequency,
and joint-success count. It emits exactly two pair IDs in one
`ORGANIZE_SET`. The bytes are sealed before visibility of:

- support-action handles, arguments, menus, or expected results;
- Phase-B/C/D goals, actions, hypotheses, or outcomes;
- the root theorem, compiler, scorer, hidden roles, or expected trace.

After sealing, the child executes fresh public support tests. The link compiler
admits a proposed pair only if new joint and matched single-component outcomes
independently verify both-atom necessity. It cannot propose, rank, replace, or
repair a pair.

### 2.3 Mechanical and chance baselines

Every root reports, before any memory fit:

1. `ENDPOINT_JOIN`: all eight pairs tie; a frozen semantic-independent tie
   rule selects two;
2. `FREQUENCY_RECENCY`: the frozen joint-count/recency policy selects two;
3. `CHANCE_2_OF_8`: exact probability of selecting both useful lanes is
   `1 / C(8,2) = 1/28`;
4. `NECESSITY_ORACLE_CPU`: a declared mechanical ceiling applies the exact
   joint-minus-single ablation rule to public evidence; it is never available
   to the child, compiler, reader, or actor.

The child selection must be compared with all four. Beating endpoint/frequency
and chance supports non-syntactic child organization. Matching the explicit
necessity ceiling does not show an algorithm unavailable to a compiler; it
shows that the child emitted the correct organization from its experience.
Use **child-specific DREAM intelligence** only if the child exceeds the frozen
non-oracle mechanical policies over roots. Otherwise say only **child-emitted
pre-blueprint organization**.

### 2.4 Matched DREAM derangement

`DREAM_DERANGED_OLD` begins from the exact child `ORGANIZE_SET`, then applies a
presealed fixed-point-free lane permutation to its two link bindings. It keeps
the query anchors, `FOUND` envelopes, link schema, slots, occurrence count,
citations count, padding, target length, render count, and optimizer work
fixed, while the action-bearing endpoints/payloads point to two wrong lanes.
The derived false rows have new IDs and explicit derivation receipts; no public
event is rewritten.

This is deliberately a corrupted-binding control, not a truthful memory. All
generic interface/non-harm gates must still pass, and FULL-versus-DERANGED is
not credited if the deranged adapter merely damages unrelated behavior.
`NULL` is removed: it changed hit geometry and made failure automatic.

## 3. Authentic crossed action--outcome source

### 3.1 Source event block

One opaque Phase-A source situation `s` permits two child actions `L` and `R`.
The child must execute each exactly four times within a presealed eight-slot
opportunity block. Order is free; missing coverage is an adverse root failure.
Outcomes are root-randomized opaque public aliases denoted `T` and `O` only in
this specification:

```text
b=0:  L -> [T,T,T,O]       R -> [T,O,O,O]
b=1:  L -> [T,O,O,O]       R -> [T,T,T,O]
```

Occurrence order within each action is presealed and presentation-balanced.
Thus the authentic contingency has
`P(T | preferred action)=.75` and `P(T | other action)=.25`. SLEEP renders the
eight actual events in the qualified writer's forward and inverse views:

```text
situation + executed action -> public outcome
situation + desired outcome -> action propensity
```

It does not invent a deterministic action label from a stochastic event.

### 3.2 Within-situation derangement

`SOURCE_DERANGED_OLD` uses a presealed within-`s` outcome-donor permutation
that preserves:

- the same eight immutable child action events;
- four L and four R occurrences;
- four T and four O outcomes overall;
- every source surface, occurrence, row/view count, padding class, render
  multiplicity, loss mask, and optimizer step;

but produces:

```text
L -> [T,T,O,O]             R -> [T,T,O,O].
```

The derived rows get new IDs and cite both the unchanged action event and the
unchanged donor event plus the frozen permutation. Conditional on the public
situation, action and outcome are now independent. This is a real contingency
intervention, not an opposite deterministic label map.

All path/DREAM/support rows are byte-identical between `FULL_OLD` and
`SOURCE_DERANGED_OLD`. All source rows are byte-identical between `FULL_OLD`
and `DREAM_DERANGED_OLD`.

### 3.3 Later inverse-action endpoint

Phase C asks for an information action under a desired public source outcome.
`L` maps to experiment family `{E0,E1}` and `R` maps to `{E2,E3}`. Four
destroyed probe forks counterbalance action labels, outcome request (`T` or
`O`), family presentation, and catalog order. They share the S1 adapter but
write nothing and cannot affect the acquisition trunk.

For FULL, requesting `T` versus `O` must reverse the higher-probability source
action and therefore redirect the experiment family. These destroyed probes
score correctness for the requested **source outcome**, not target-information
gain: the `O` probe intentionally redirects to the family that is nuisance in
the acquisition trunk. The real acquisition trunk always requests `T`, for
which the preferred source action maps to the target-informative family. Under
SOURCE_DERANGED, both actions have `.5` propensity. Its choices are allowed to
be lucky; the control is **not required to fail D** and receives no S2 build.
The source estimand is the paired root-level inverse-action accuracy across the
four counterbalanced C probes, not a structurally forced null-arm terminal
zero.

## 4. Complete Phase-C and admission truth table

The source orientation `b` determines which experiment family is informative.
The target bit is `h`; `z` is a balanced nuisance bit independent of `(b,h)`:

```text
b=0: E0=h, E1=1-h, E2=z, E3=1-z
b=1: E2=h, E3=1-h, E0=z, E1=1-z
```

Before acting, the child must cite its inverse source read and publish two live
hypotheses, predicted outcomes, the complete outcome-to-row map, and one
experiment. The only prospective maps are:

```text
E0 or E2:  outcome 0 -> n0; outcome 1 -> n1
E1 or E3:  outcome 0 -> n1; outcome 1 -> n0
```

The exact admission law, exhaustively instantiated for all
`b,h,z,experiment,outcome` combinations, is:

| chosen experiment | public outcome | posterior over `h` | declaration faithful | world-true row | admission |
|---|---|---|---|---|---|
| target-family direct (`E0` if b0; `E2` if b1) | `y=h` | `{h}` | mapped `n_h` | yes | admit `n_h` |
| target-family inverse (`E1` if b0; `E3` if b1) | `y=1-h` | `{h}` | mapped `n_h` | yes | admit `n_h` |
| non-target direct | `y=z` | `{0,1}` | branch may be syntactically followed | not identifiable | `NO_ADMISSION` |
| non-target inverse | `y=1-z` | `{0,1}` | branch may be syntactically followed | not identifiable | `NO_ADMISSION` |

Numeric coincidence `z==h` never authorizes a row: a nuisance experiment
leaves the public posterior over `h` non-singleton. `DECLARATION_FAITHFUL` and
`WORLD_TRUE` are separate receipt bits. The target-blind compiler sees only
the public source/calibration rows, declaration, action, and outcome. It emits
the declared row only when the public posterior is singleton and the row is
supported; otherwise the reserved slot receives canonical `NO_ADMISSION`.

For FULL, the two `h` twins share every byte through experiment dispatch, then
the public outcome, admitted row, and correct delayed action redirect. Each
twin requires its own S2 adapter. Source/DREAM controls stop at S1/C/B, so
there is no chance-based demand that a nuisance branch fail a later goal.

## 5. Closed reader observability

### 5.1 Actor-visible API

The actor never sees or selects a candidate ID. It sees exactly:

```text
MemoryCatalog {
  schema_version,
  legal_query_types,
  currently_public_anchor_ids,
  reads_remaining
}

READ {query_type, anchor_id}

MemoryReturn {
  status: FOUND | MISS | BLOCKED,
  query_fingerprint,
  row_or_fixed_pad,
  reads_remaining
}
```

Legal anchors are only current public state/goal/source handles or endpoints
returned in an earlier row. The catalog is constant across arms/twins except
for already public goal/state bytes. It contains no slot IDs, candidate
metadata, hit hints, row counts, truth, role, answer, rank, score, or future
handle.

For each READ the backend constructs the complete fixed 32-slot candidate bank
and performs one frozen recognition-scoring call with the mounted carrier.
Candidate order is semantic-independent and permuted in an invariance cell;
the reader returns the unique maximum above the frozen threshold or `MISS`.
It cannot substitute, repair, or semantically interpret a row. Candidate scan
cost, tokens, and latency are charged even though candidates are not actor-
visible.

LoRA is mounted only inside this READ transaction. The clean base plans and
acts. This endpoint is `typed functional traversal`, not learned internal
search.

### 5.2 Exact read budgets and ceilings

Phase B permits three READs: entrance atom `a_u`, old link `(b_u+c)`, and
terminal atom `t_A/t_B`. The normal atoms-only carrier needs four READs
(`a_u,b_u,c,t`) and cannot produce a complete trace under three. A required
**four-read atoms-only exact-text ceiling** must solve both goals. This makes
the DREAM effect explicitly a bounded read-budget/connected-row advantage,
not inability of atoms to contain the answer.

Phase C permits one inverse source READ plus one experiment. Phase D permits
two READs: the old link and `n_h`.

Before model work, exhaustive CPU receipts must show:

- `I(catalog/order/status/length; correct row | public query) = 0` under the
  root generator;
- bank size `32` is greater than every read budget;
- goal-only, catalog-only, fixed-first, ID, length, hit-pattern, and exhaustive-
  suffix proxies are at or below `.25`;
- internal candidate permutation preserves positive semantics/actions;
- a returned-row semantic twin redirects the next query/action;
- exact text passes at normal FULL budgets and atoms-only passes only at four;
- actor/reader processes cannot open/import generator, theorem, compiler
  receipt, hidden truth, scorer, oracle, or expected trace.

Publish the exact serialized catalog, READ, and return bytes plus the complete
proxy/mutual-information table. If opaque addressing makes positive retrieval
impossible, the assay is invalid; if metadata makes it possible without the
carrier, it is leaked.

## 6. Two-cycle chronology and trained conditions

```text
A0   seal root and h twins, all future objects and execution order
A1   child path/evidence/source ACTs -> public outcomes -> immutable ledger
A2   child ORGANIZE_SET sealed before blueprint/goals
A3   child support ACTs -> public outcomes -> two admitted FULL links
S1   fit FULL_OLD, SOURCE_DERANGED_OLD, DREAM_DERANGED_OLD
B    same-start goal twins; source-control B equivalence; DREAM contrast
C-p  four destroyed inverse-action probe forks; no outcome enters training
C    FULL only: declaration -> experiment ACT -> public outcome -> G_new
S2   fit FULL_NEW_h0, FULL_NEW_h1, FULL_OLD_PLUS_PAD
D    fresh processes/resets; run delayed goal and cuts for both h twins
```

Every build starts from immutable birth with the exact writer recipe that
actually passes W0 and its old/new coexistence canary. If canonical Q0 passes,
M uses Q0; if a prospectively registered representation/preservation repair
qualifies, M uses exactly that. M adds no cross-view, paraphrase, loss,
plasticity, rank, seed, or dose choice.

### 6.1 S1 decks

| build | source block | DREAM block | role |
|---|---|---|---|
| `FULL_OLD` | authentic crossed events | child's two supported links | positive old carrier |
| `SOURCE_DERANGED_OLD` | within-situation independent derived rows | byte-identical authentic child links | action/outcome contingency |
| `DREAM_DERANGED_OLD` | byte-identical authentic source | two hit-matched binding-swapped links | DREAM binding/content |

Exact deck-diff receipts must prove that only the named rows/derived IDs differ.
`SOURCE_DERANGED_OLD` must match FULL on B traversal; `DREAM_DERANGED_OLD`
must match FULL on C source inversion. A generic interface or unrelated-action
drop beyond the W0 bound invalidates the contrast rather than helping it.

### 6.2 S2 decks

All three use the identical FULL old deck, initialization, data order,
renderer, row count, dose, optimizer schedule, and reserved slot:

| build | reserved S2 slot | role |
|---|---|---|
| `FULL_NEW_h0` | truthful `n0` selected after the h0 public outcome | outcome-0 delayed carrier |
| `FULL_NEW_h1` | truthful `n1` selected after the h1 public outcome | outcome-1 delayed carrier/redirection |
| `FULL_OLD_PLUS_PAD` | matched canonical pad; no new target | equal-work second-write baseline |

If FULL does not select a target-informative experiment or `G_new` does not
admit the truthful row, that root is an adverse zero and its S2 fits are
prospectively skipped. Skipping after an upstream noncompensatory failure is a
futility rule, not complete-case filtering; the root remains in every
denominator.

S2 is a clean-base cumulative reconstruction, not an in-place update of S1.

## 7. Inference-only controls

The six builds above support every other required cell:

| control | construction | interpretation |
|---|---|---|
| `SLEEP1_OFF` | unmount S1 during B/C under identical visible history | first-write dependence before S2 |
| `NO_SLEEP2` | mount FULL_OLD at D | new information absent without another write opportunity; diagnostic only |
| `S2_OLD_PLUS_PAD` | matched S2 baseline build | causal effect of training the new row |
| `WRONG_ROOT` | next root's same build under frozen slot mapping | life-specific carriage |
| `LINK_CUT` | suppress required old link in raw return | DREAM-link necessity |
| `OLD_CUT` | suppress old link at D | delayed old necessity |
| `NEW_CUT` | suppress `n_h` at D | delayed new necessity |
| `GOAL_TWIN` | same start/non-goal bytes, A/B goal change | query/path/action redirection |
| `DESIRED_OUTCOME_TWIN` | source query requests T versus O | inverse source-content redirection |
| `OUTCOME_TWIN` | separate h0/h1 S2 builds | public outcome/new-row/delayed-action redirection |
| `CATALOG_PERMUTE` | internal semantics-preserving bank order | no order/slot policy |
| `READ_BINDING_SWAP` | same build, named returned payload derangement | semantic content rather than carrier presence |
| `GOAL_ONLY/CATALOG_ONLY` | carrier absent, fixed-size MISS | prompt/menu shortcut ceiling |
| `TEXT_SAME_SEMANTICS` | exact FULL rows, same reader/API, no LoRA | assay ceiling, not lifetime text baseline |
| `ATOMS_TEXT_READ4` | exact atoms, four reads, no links/LoRA | atoms contain the solution; links save a bounded read |

Every positive return must have a byte-exact receipt:

```text
child ACT -> public outcome -> canonical admitted row -> exact target bytes
-> adapter manifest -> raw recognition output -> actor-visible return
-> action dependency
```

No positive cell may substitute a semantic return.

## 8. Noncompensatory root endpoint

Set `R_r=1` only when all of the following are true for the same presealed root:

1. CPU theorem, prefix, immutable-ID, reader observability, proxy, transform,
   reset, unique-proof, and oracle-air-gap receipts pass.
2. Every critical source/evidence row follows an actual child ACT and causally
   later public outcome; no draft/harness/oracle action is admitted.
3. The child DREAM seal precedes blueprint visibility and selects both
   supported useful lanes; later support validates both links. Mechanical and
   chance comparison is a separate cohort-level release gate, never a field
   inside `R_r`.
4. All three S1 carriers pass row extraction, canonical interface, unrelated-
   action non-harm, carrier-origin, and wrong-root gates.
5. FULL solves both B goals with valid three-read dependency traces;
   GOAL_TWIN redirects query/path/action; LINK_CUT and DREAM_DERANGED fail the
   link-dependent trace; SOURCE_DERANGED matches FULL on B.
6. Across four counterbalanced C probes, FULL's inverse-action accuracy for
   the requested source outcome is `1.0` and exceeds SOURCE_DERANGED by at
   least `.25`; requesting T versus O redirects the source action/experiment
   family; DREAM_DERANGED matches FULL on this source endpoint.
7. In both h twins, FULL declares a valid map, selects a target-family
   experiment, receives the public outcome, and G_new admits exactly `n_h`.
8. `FULL_NEW_h0` and `FULL_NEW_h1` retain all registered critical old rows and
   add only their truthful new row; their B retention probes still pass.
9. Both FULL_NEW twins solve D from the same `U_(u_D)` with valid old+new
   traces and different correct
   final actions. FULL_OLD_PLUS_PAD, OLD_CUT, NEW_CUT, LINK_CUT, and WRONG_ROOT
   fail D. FULL_NEW beats FULL_OLD_PLUS_PAD; `NO_SLEEP2` is
   reported but does not replace this matched contrast.
10. Exact text completes the full chain, ATOMS_TEXT_READ4 solves B, and every
    positive byte has carrier origin.

Later success never rescues an earlier zero. Source deranged is **not**
required to fail D because it has no S2 arm. DREAM deranged is **not** required
to fail D for the same reason. Their isolated S1 endpoints plus the exact
unique-proof/cut tests identify the intended upstream seams without a
chance-contradictory terminal requirement.

Root-level diagnostics, all intention-to-treat and adverse-filled, are:

```text
S_r = inverse_source_action_accuracy_C(FULL_OLD)
      - inverse_source_action_accuracy_C(SOURCE_DERANGED_OLD)

M_r = valid_link_trace_B(FULL_OLD)
      - valid_link_trace_B(DREAM_DERANGED_OLD)

W_r = delayed_value_D(FULL_NEW_h)
      - delayed_value_D(FULL_OLD_PLUS_PAD)

F_r = min_h [ delayed_value_D(FULL_NEW_h)
              - max(delayed_value_D(OLD_CUT_h),
                    delayed_value_D(NEW_CUT_h)) ]
```

`R_r` is a reliability conjunction. It is not a substitute for reporting the
paired source, DREAM, first-write, and new-write contrasts over all roots.

## 9. Fatal shortcuts

Any structural occurrence invalidates the instrument; a root-local occurrence
adverse-fills that root:

1. roots/goals/useful lanes selected or regenerated after child behavior;
2. endpoint/type/degree/ID/order/frequency syntax distinguishes DREAM candidates;
3. support blueprint or future goal/action/outcome visible before DREAM seal;
4. compiler proposes, ranks, repairs, or replaces child links;
5. NULL/absence changes hit/read geometry instead of matched derangement;
6. source control lacks both child actions, repeated within-situation outcomes,
   or an independence-producing donor permutation;
7. source derangement changes path/DREAM rows or Phase-C world/compiler;
8. DREAM derangement changes source rows, slot/hit geometry, or generic dose;
9. outcome-twin adapter simulated by read substitution or both new rows trained
   into one carrier;
10. nuisance coincidence admitted as knowledge without a singleton public
    posterior;
11. no matched S2 old-plus-pad fit while claiming the new-row write caused D;
12. actor-visible candidate IDs/metadata or an opaque address puzzle supplies
    the selected row;
13. candidate enumeration fits inside the read budget;
14. goal/menu/catalog/fixed-position proxy exceeds its ceiling;
15. same semantic ID names different bytes;
16. oracle/hidden truth/score/future goal enters training, actor, reader, or
    compiler capability;
17. outcome precedes action, an unexecuted draft is admitted, or the harness
    acts for the child;
18. positive READ performs semantic substitution/repair;
19. raw event/DREAM/C text, cache, workspace, or query state crosses reset;
20. LoRA is mounted during planning/action but effect is called memory carriage;
21. fit seed/rank/LR/renderer/dose/threshold is selected on M outcomes;
22. failed roots are retried, dropped, permissively reparsed, or replaced;
23. twins/goals/calls/checkpoints counted as independent roots;
24. generic corrupt-adapter damage counted as semantic specificity;
25. clean-base cumulative reconstruction called in-place expansion;
26. typed recognition traversal called native learned search; or
27. parenting/final-gym/other-root artifacts return into the fixed child/root.

## 10. Staged roots, stopping, and inference

All stages are source-disjoint. No DEV root becomes confirmation evidence.

### Stage 0 — CPU, zero fits

Exhaust at least 64 alias/root/twin fixtures over every `(b,h,z)`, lane and
presentation cell. Require:

- all `2*2*2*4` Phase-C experiment cases match the admission table;
- both source contingency orientations and the exact eight-event derangement;
- all DREAM candidate equivalences, lane permutations, derangements, and
  mechanical/chance scores;
- exact reader catalog bytes, 32-slot bank, mutual-information/proxy table,
  read ceilings, prefix laws, roots/cuts, sterile resets, and air gap;
- scripted exact-text FULL success, read-4 atoms success, and every negative
  mutation.

Any structural failure stops M.

### Stage 1 — exact-text child DEV, 4 then at most 8 roots

Run four fixed roots through authentic child source actions, pre-blueprint
DREAM, exact text, both h twins, both source desired-outcome probes, all cuts,
and read-4 atoms. Stop on any leakage/receipt failure or fewer than `2/4`
complete roots. If `2/4` or `3/4`, extend to eight; require at least `6/8`.
If `4/4`, proceed. Report child selection against all mechanical baselines.

### Stage 2a — two-root S1 LoRA kill

Fit only the three S1 builds on two presealed DEV roots: **six fits total**.
Run every B/C/source/DREAM/reader/interface gate. Both roots must have positive
`S_r`, positive `M_r`, FULL B success, orthogonal-control equivalence, and no
fatal defect. On failure, adverse-fill the roots and stop before S2.

### Stage 2b — two-root S2 kill

Only after 2a passes, fit the two truthful h adapters plus old+pad on each
root: **six more fits**. Require both outcome twins, retention, matched S2
effect, cuts, and D conjunction in both roots. Failure stops widening.

### Stage 3 — eight-root DEV

Add six disjoint DEV roots. Always run S1 first; run S2 only for roots passing
the frozen upstream gate, while adverse-filling failures. Require at least
`6/8` joint `R_r=1`, zero structural defects, and measured resource bounds.
This is the last mechanics-changing stage.

### Stage 4 — sixteen-root confirmation

Run sixteen fresh iid roots in presealed condition/device/inference order.
There is no replacement, extension, or early success stop. The upstream S1
futility rule may skip S2 compute but never removes a root. Require at least
`12/16` `R_r=1`; this is the smallest cohort allowing 25% root failure while
rejecting the registered practical null `Pr(R=1)<=.5` by the exact one-sided
binomial test (`.0384064`). Separately report all root-level paired contrasts,
exact sign/randomization intervals, mechanical-selection results, and failure
reasons. A child-specific DREAM release additionally requires the child's
exact-selection rate to exceed each frozen non-oracle endpoint/frequency
policy under the registered paired exact test; `NECESSITY_ORACLE_CPU` remains
a ceiling, not an opponent the child must beat. Compare the child's count to
the exact `Binomial(16,1/28)` chance law as a descriptive construct check.
`12/16` is a bounded reliability claim, not by itself an exact causal test or
open-world population estimate.

## 11. Corrected fit count and rough GPU cost

Maximum fit count is unchanged, but failed-design cost is halved upstream:

```text
per root S1 maximum:      3 fits
per S1-surviving root S2: 3 fits
per successful root max:  6 fits

2-root S1 kill:                          6 fits
2-root full kill after S1 passes:        12 fits total
8-root DEV maximum:                      48 fits total
16-root confirmation maximum:            96 fits
DEV + confirmation worst case:           144 fits
```

Let `t_fit` be measured on this exact deck using the actually W0-qualified
writer. At the prior provisional `7.5--15 A40-minutes/fit`, worst-case training
is `18--36 A40-hours`. The larger source/evidence action blocks, two outcome
twins, exact-text controls, and read interventions plausibly add `10--24`
A40-hours, so the conservative all-in range is **28--60 A40-hours** after CPU
closure. Eight well-packed A40s imply roughly 3.5--7.5 ideal device-hours,
with serial chronology/process startup increasing wall time.

The S1-only two-root kill costs `.75--1.5 A40-hours` of training and should
hold failed-design all-in spend below roughly three A40-hours. If a root fails
upstream in DEV/confirmation, its three S2 fits are saved without changing its
zero. If measured `t_fit` differs, replace the estimate algebraically; do not
remove controls.

## 12. Claim boundary

If every gate passes, the strongest sentence is:

> In a finite typed benchmark, LoRAs carried records compiled from a crossed
> contingency in the child's own public actions and outcomes and from a
> child-emitted pre-blueprint organization of its evidence. A clean actor used
> typed reads differently under different goals, selected a content-dependent
> information action, and after either truthful public outcome a matched
> cumulative write enabled a delayed action requiring one old link and the
> newly grounded row.

Use `crossed experiential binding`, `child-emitted pre-blueprint
organization`, `typed functional traversal`, and `two-cycle compiler-mediated
cumulative reconstruction` only when their named gates pass. Use `child DREAM
intelligence` only when selection beats the frozen non-oracle mechanical
policies. Do not use `native graph learning`, `learned search`, `open-world
expansion`, `in-place adapter growth`, `compression`, or `lifetime flywheel`.

M-core remains the mechanism study; it does not replace the separately raised-
child L-core lifetime experiment.

## Source lineage

- `research_notes/analysis/2026-09-12_m_core_revised_three_condition_adversarial_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_minimal_exact_two_cycle_design.md`;
- `research_notes/analysis/2026-09-12_think_dream_sleep_minimum_decisive_program_audit.md`;
- `research_notes/analysis/2026-09-12_connected_relay_scaffolding_adversarial_review.md`;
- `research_notes/2026-09-12_end_to_end_goal_closure_synthesis.md`;
- `research_notes/2026-09-11_pcfl_relay_readiness_rework.md`;
- `research_loop/advisory/20260910_pcfl_v2_minimal_exact_semantics_fresh_v1.md`.
