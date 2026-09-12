# Fresh causal/mechanism audit of M-core v5

Date: 2026-09-12 UTC

Scope: independent zero-fit review of the complete
`2026-09-12_m_core_exact_two_cycle_design_v5.md`, using only its two linked v4
audit memos where lineage was needed. I treated the package, checker, receipts,
TEXT results, model acceptance, and fits as unimplemented requirements, not
evidence. I did not inspect or edit builder code, coordination, models, jobs,
or GPU state, and ran no model or scientific job.

## Verdict: REWORK before materialization, TEXT, reader acceptance, or M fits

The six-fit/root allocation is sufficient. Conditional on exact realization,
v5 has the right high-level causal structure: authentic FULL source rows versus
a hit/work-matched derived tie; selected authentic links versus wrong-payload
links; a clean actor whose only LoRA-mediated channel is typed READ; a
FULL-mounted goal-field intervention; clean-base S2 old+new versus old+PAD;
and separate old/new cuts and content swaps. The phase-lifted graph and action
authorization make public observations consequences of a row-guided action,
not a substitute route around the row.

Four zero-fit contract defects still prevent that structure from identifying
the released mechanism. They are not reasons to add a seventh trained arm.

## Claim blockers

### 1. The NEW compiler cannot perform its stated public-source check

Sections 3.4, 5.3, and 8 require `NEW_ROW_ADMISSION` to reconstruct the
authentic source-preferred family and reject the nuisance-family branches.
But the normative semantic rule says a NEW `CompilerInput` contains only
declaration, dispatch, outcome, and `public_task_law`; `source_evidence` must
be null. The same rule makes `public_task_law` root-independent and forbids
`b`. The declaration records the actor's choice, not the authentic 3:1/1:3
source contingency. Therefore a pure conforming compiler cannot know whether
the chosen family is authentic. It must either use forbidden hidden/ambient
state or omit the required check. This defeats both the live
`SOURCE_READ_SWAP_C` interpretation and the no-hidden-answer claim.

The closed input also lacks enough public root-local construction data for
several outputs. A selected opaque pair handle plus eight TEST event pairs
does not specify its `U_i`, `[b_i,c_0]`, destinations, or canonical row handle;
the NEW declaration supplies two opaque row handles but no complete `n0/n1`
row templates or action handles. A root-independent blob cannot supply these
root-specific aliases. Similar canonical output-template ambiguity remains
for source rows. The prose package tables may audit an output, but the stated
compiler capability is a pure function of the closed `CompilerInput`.

Finally, `CompilerDecision` has no event handle, input hash, or logical tick.
It cannot itself prove that link admission followed selection/support or that
NEW admission followed the authentic dispatch observation. A trace array
position is not the promised action/observation/compiler causal receipt.

Minimum repair: give each compiler a closed, public, root-local template input
containing every complete alternative row it may emit, with no role, expected
answer, condition, `b`, `z`, or `h`. Reveal the link blueprint only after the
child selection is sealed; expose both NEW alternatives before the outcome.
Permit NEW additionally to receive the original authentic `SourceEvidenceView`
and require it to recompute the preferred family from those events. Add a
compiler invocation/decision handle, exact input hash, and tick later than all
cited prerequisites. The checker must reject any output not derivable from
those bytes alone.

### 2. “Child-selected” and “fresh support” are not provenance-closed

Authentic source actions are well represented by
`ChildCommittedActionEvent -> PublicObservation`. Pair selection is not.
`PublicPairSelection` has only two handles and a tick: no event handle,
`CHILD_COMMIT` authorization, actor-input hash, model/decode/RNG receipt, or
link to the 32 public ablation observations. It is therefore consistent with
the schema for the materializer, which knows the hidden selected pair, to emit
the correct pair. Requiring the correct pair in `T_r`/`R_r` does not prove the
child chose it from visible evidence.

`AblationEvidenceView` then carries only eight generic authentic pairs. The
normative rules do not require their actions to occur after the selection,
under a newly revealed support fixture disjoint from the original ablation
fixture. Thus the same pre-selection observations can satisfy the literal
LINK input even though the claim says fresh support. There is also a literal
cardinality typo: the lane profile lists one useful plus three left and three
right decoys (seven), while the generator selects two useful lanes plus six
decoys (eight).

Minimum repair: replace/extend `PublicPairSelection` with an addressable
child-authenticated decision event bound to its complete public input and
actor draw ledger. Require its two handles to be chosen from the visible
eight-pair roster solely after all 32 ablation action/observation pairs.
Represent a separately committed support-fixture reveal, require all eight
support actions and observations to have ticks after selection, and require
fixture/event disjointness. Make LINK cite the selection and those support
events. State explicitly that both members of the selected pair have
`1/0/0/0` evidence.

### 3. The source live swap changes an extra actor-visible cause

`SOURCE_READ_SWAP_C` is described as the causal count-to-action intervention,
but section 5.4 changes the row handle as well as the two count bindings. The
row handle is actor-visible and is later cited by the action event. Therefore
redirection cannot literally be attributed to the count binding alone. The
common RNG, fixed RPC size, and required opposite action remove timing and
malformed-control explanations, but not this simultaneous identity change.

Minimum repair: keep the FULL row handle, query, citations, ordering, actions,
totals, envelope, and all non-count bytes identical in the swap; record the
intervention identity only in audit. If immutable row identity is required to
change with content, add a zero-fit handle-only sham and require authentic
choice/admission under it. The trained SOURCE_DERANGED contrast may retain a
distinct derived-control handle because it estimates the whole fitted-row
intervention, not the count-only live swap.

### 4. The goal intervention and ATOMS gate are not closed by the schemas

The actor input byte cut is a good repair: the ordinary A/B pair differs only
under `/goal/`, and the FULL-mounted cue swap changes one goal field while
holding the target fixed. But `RecognitionRequest` has only a generic vector
of one or two `public_anchor_handles`; no normative type-specific mapping says
which element is the route cue, terminal target, desired source outcome, or D
key. In the cue swap the goal handle and catalog anchors are deliberately held
fixed, yet the required first ROUTE request/return must change to `q_uB`.
Without a closed request construction rule, one conforming implementation can
ignore the changed cue while another can place it in an anchor. The downstream
allowed-difference mask must also allow exactly the request fingerprint, pad,
row, action, and observation differences caused by that one input byte field;
the separately named `rpc_observable_allowed_diff.json` is not a listed member
unless it is explicitly made a section of `allowed_difference_maps.json`.

There is a second literal gate conflict: normative `BGoal.read_budget` is
`CONST[3]`, while `TEXT_ATOMS_READ4`, the ATOMS theorem, and `R_r` require a B
episode with four reads. Both cannot be schema-valid as written.

Minimum repair: make `RecognitionRequest` a closed union of query-specific
payloads and bind the deterministic ActorEpisodeInput-to-request projection.
For `ROUTE_BY_CUE`, the request must carry the actual route-cue handle; for the
other query types it must carry their displayed arguments. Bind a complete
causal-descendant difference mask for `FULL_GOAL_CUE_SWAP_B`. Add a registered
ATOMS B-goal/input variant with read budget four and an exact allowed-difference
map; ordinary FULL remains three.

## Intervention and gate disposition

| Intervention/gate | Disposition |
|---|---|
| `SOURCE_DERANGED_OLD`; `G_S` | Sound conditional on compiler repair. The 2/4--2/4 row is a truthful derived view, has no privileged action, preserves authentic donors/marginals/work, and invalid cells cannot score favorably. |
| `SOURCE_READ_SWAP_C` | REWORK for missing authentic source input to NEW and the extra row-handle change. Declaration-before-dispatch/outcome otherwise avoids a post-treatment target. |
| `DREAM_DERANGED_OLD`; `G_M` | Sound conditional on child/support provenance. Exact wrong links, exact legal wrong actions, orthogonal-row preservation, common work/RNG, and the FULL payload swap close a carrier-global explanation. Require the payload-swap receipt to include its presealed `VALID_SWAP_ENDPOINT`, not merely `applied=1`. |
| `S1_OFF_B/C`; `G_U` | Sound. Charged matched MISS envelopes plus unavailable-return rejection distinguish absence from a broken RPC. |
| A/B pair, `FULL_GOAL_CUE_SWAP_B`, catalog permutations/no-carrier cells | Ordinary byte isolation is sound; cue-swap execution needs blocker 4 repaired. `CATALOG_NO_GOAL_NO_CARRIER` is correctly descriptive and is not used as goal isolation. |
| B link cut/payload swap | Sound availability/content controls once the control registry binds one exact expected terminal/failure code. Post-action observation differences are descendants of the row intervention, not baseline observation confounds. |
| `FULL_NEW_h0/h1`, `OLD_PLUS_PAD`, `NO_SLEEP2`; `G_W` | Sound conditional on blocker 1. Clean-base equal-work old+new versus old+grounded-PAD identifies outcome-specific public row addition, while exact old extraction and B behavior establish coexistence. It does not identify online/in-place updating. |
| D old/new cuts and separate payload swaps; `G_F` | Sound and noncompensatory. The sequence cursor, action authorization, two-read budget, BFS proof, exact wrong actions, and separate cuts make each old link and new row necessary for this typed D path. They establish access/content necessity, not global representational minimality. |
| Interface canary and non-harm | Appropriate validity gates, not mechanism outcomes. They help exclude a generally broken carrier but cannot repair a missing causal receipt. |
| `G_R` | Fails until all four blockers are closed. Replace “every named R control” with the literal manifest-bound control-registry set and bind one expected endpoint code/trace per control so validity is never assigned after outcomes. |

## Resulting claim boundary

After these zero-fit repairs and actual package/checker realization, no extra
trained condition is needed. The design can then identify the narrow stated
claim: compiler-mediated carriage of an authentic crossed source contingency,
utility of child-evidence-selected links, goal-cue-conditioned typed traversal,
and clean-base second-cycle coexistence/use of one old link and one
outcome-specific new row, with separate within-carrier necessity interventions.
It still must not be described as DREAM intelligence, native search, online
growth, general retention, or global row minimality.
