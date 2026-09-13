# P-CHAIN-2: fresh preimplementation audit

**Date:** 2026-09-13 PT  
**Audited proposal:**
`research_notes/analysis/2026-09-13_smallest_parametric_two_hop_composition_ceiling.md`
at original author commit `8469715d` (current synchronized equivalent
`06b562a6`)  
**Scope:** documentation-only review. I did not author source, materialize a
root, invoke a tokenizer or model, fit an adapter, use a GPU, or make a
scientific claim.

## Verdict

**REWORK BEFORE IMPLEMENTATION; CONDITIONAL GO after the seven repairs below.**

The experiment's central control is good: AUTH and DERANGED use the same
identifiers, keep the first hop fixed, change only the assigned second hop,
and must both acquire their assigned facts and redirect the endpoint on the
same questions. That is much stronger than adapter-on versus adapter-off and
would rule out generic tuning damage, an answer prior, and an identifier-only
answer rule.

The current text nevertheless leaves three primary inferences ambiguous:

1. candidate-assisted one-hop scoring does not show that an opaque atom can be
   freely generated in the mode the two-hop trace requires;
2. a model trained only on explicit trace targets cannot support a causal
   `CoT versus direct` claim when the direct format received no matched
   training; and
3. the D2 rule can continue past and then displace a successful D1 primary
   checkpoint merely because the diagnostic LOCAL arm underfit.

These are specification defects, not reasons to abandon the screen. The
repairs do not require a new scientific arm, rank, dose, or material scale.

## What is already sound

- `EVAL-MEM`, `PROMPT-ONLY`, and `JUNCTION-TRAIN` are concretely disjoint.
  PROMPT-ONLY facts are visible only on independent evaluation calls and do
  not enter the parametric training corpus.
- AUTH/DERANGED have matched identifier and output marginals; DERANGED is a
  valid alternate world rather than a deliberately broken corpus.
- Requiring DERANGED to preserve the unchanged first hop, acquire its own
  second hops, retain generic canaries, and redirect the answer prevents
  generic damage from masquerading as content causality.
- The exact parser, no repair/canonicalization, target-disjoint skill
  examples, and prohibition on any scored A--C row are appropriate.
- The fit arithmetic in the proposal is internally correct: D1 is four
  invocations / 1,536 total updates; the terminal D2 path is seven
  invocations / 3,072 total updates. The published call and generated-token
  sums (`448` / `83,968` at D1; `736` / `139,264` terminal) also recompute
  correctly under the currently listed panels.
- One DEV material root and learner seed are correctly bounded as an
  engineering ceiling, not population evidence.

## Required repair 1: qualify free atom extraction, not candidate recognition

The proposal says each one-hop question exposes eight endpoint candidates.
That can prove selection of a stored binding, but it cannot distinguish a
freely generatable memory completion from recognition among prompt-visible
strings. The scored two-hop trace must generate the intermediate `B_i`
without such a list. Consequently, if candidate-assisted one-hop passes and
the trace fails, `PARAMETRIC_CHAIN_NOT_SHOWN` conflates composition failure
with a simpler free-recall/spelling failure.

Replace the existing `32` one-hop calls per state with no-candidate, strict
canonical completion calls:

```text
MEMORY NEXT <source> => <target>
```

Sixteen score first hops and sixteen score second hops. Keep the existing
`15/16` per-stratum and `30/32` strict-terminal gates. Because the answer is
then an opaque target absent from the prompt, BASE and LR0 should be required
to score at most `1/16` per stratum, not `4/16`. An optional candidate panel
may be reported as a separate recognition diagnostic, but it cannot qualify
Gate 1 or repair a free-generation miss.

This is an in-place replacement, so the current call/token arithmetic remains
unchanged.

The endpoint candidates on the full two-hop panel may remain if the intended
claim is explicitly `free intermediate generation plus endpoint selection`.
If the maximum wording says that both bindings were *freely reproduced*,
remove those candidates too. Do not slide between those two claims.

## Required repair 2: demote direct versus trace to format transfer

Every JUNCTION skill target has the explicit three-line trace, whereas no
arm receives dose-matched direct-answer targets. A lower direct score can
therefore be caused entirely by supervised output-format matching; it does
not show that explicit CoT enabled a latent computation.

For the smallest screen, keep the 16 direct calls but rename question 3 and
Gate 4 to **canonical-trace versus alternate direct-output transfer**. Report
the scores descriptively. Delete `CoT-enabled`, `CoT necessary`, and any
mechanistic inference from their difference.

A causal trace-versus-direct experiment would require an additional
target-disjoint `DIRECT-JUNCTION` training state matched in exposure and
target-token work. That is unnecessary for this ceiling and should not be
added now.

Also soften `let generated B become the cue for B -> C`: the primary output
shows a trace in which `B` precedes the second completion, but a printed CoT
can be post-hoc. Same-ID redirection proves binding-sensitive composition,
not causal dependence on the printed token. A later prefix intervention can
test token-level mediation if it becomes important.

## Required repair 3: make D1/D2 selection primary-arm safe

The current rule opens D2 if *either* learned arm misses one-hop acquisition.
Thus ATOM-JUNCTION could pass every D1 primary gate while an underfit
ATOM-LOCAL arm forces both adapters to continue, potentially degrading the
already successful primary checkpoint.

Freeze this branch instead:

- If ATOM-JUNCTION passes free one-hop extraction, prompt-fact qualification,
  and authentic two-hop composition at D1, select D1 and train DERANGED at
  D1. A failed LOCAL arm makes only the curriculum contrast uninterpretable.
- Otherwise open D2 only under the proposal's already declared underfit or
  composition-miss conditions, continue all three coupled tapes, and select
  D2 terminally.
- Preserve D1 raw outputs and checkpoints regardless. Never choose whichever
  of D1/D2 later looks better.

If the authors instead consider the LOCAL contrast co-primary, that must be
said explicitly; it would be a different stopping objective from the current
`parametric composition first, curriculum diagnostic second` hierarchy.

## Required repair 4: bind the atomic writer bytes and custody

`source record` and `supervised memory row` are not exact enough for a
preimplementation contract. Bind the literal system/user/assistant roles,
newlines, response-loss mask, and which side contains the observed mapping.
Each atomic training unit may expose exactly one relation and supervise
exactly one canonical memory line. It must contain:

- no chain ID, shared episode ID, A/B/C role label, endpoint candidate,
  scored query wording, or second relation;
- no correlated source identifier joining the two rows beyond the legitimate
  shared middle token `B_i`; and
- no adjacent/pair-specific schedule marker. Paired-row lag and batch
  placement should be generated independently subject to the existing
  never-same-minibatch rule.

Run every evaluation request in a fresh context/KV state. Complete all fits
before making any evaluation root readable by a trainer. In particular,
DERANGED is trained after AUTH dose selection, so its process must still be
unable to traverse prior PROMPT-ONLY/EVAL raw-output directories. Existing
prose states this intended visibility; the successor must turn it into exact
path/manifest custody.

## Required repair 5: close the LOCAL positional convention

The current LOCAL example is under-specified. JUNCTION always answers with
the target of the second printed memory line. If LOCAL sometimes answers the
first line, a JUNCTION advantage may be an answer-position convention rather
than help from a joining curriculum.

For every LOCAL target, place the queried one-hop fact in the second memory
line and answer that line's target. The first line is a genuinely nonjoining
fact. Match line order, relevant-line position, answer position, wrapper
length, and batch target-token totals to JUNCTION. The question semantics
must still differ (one-hop local versus two-hop junction), so the permitted
wording remains only **the target-disjoint junction curriculum package
helped**. It cannot isolate a unique neural chaining mechanism.

## Required repair 6: make shortcut nulls executable and stricter

`single-feature nulls` and `all pairwise combinations` do not name an
algorithm. A classifier fitted and scored on the same 16 answers could
memorize identities; a hand-selected heuristic after seeing labels would be
equally invalid. Predeclare the exact label-free functions and their tie
breaking before materialization. They may inspect only the stated surface
fields and train-domain mappings, never EVAL labels.

The current pairwise allowance `<=8/16` permits a nominal shortcut to solve
half the panel. Tighten every fixed single/pairwise null to `<=4/16`, or bind
a separate multiplicity-aware threshold prospectively and explain why it
cannot supply a material fraction of the `14/16` primary gate. Never resample
a valid fixed root because a null happens to perform well; repair/version the
generator as already required.

The same-prompt AUTH/DERANGED redirection remains the decisive defense; these
surface nulls are supporting closure, not proof that every heuristic has been
enumerated.

## Required repair 7: define LR0 as an effective zero delta

Ordinary LoRA initialization can contain a nonzero random `A` tensor and a
zero `B` tensor while the effective product `delta_W = scale * B @ A` is
exactly zero. Therefore `adapter delta byte-zero` must mean every effective
per-layer delta is bitwise zero, not that every serialized adapter tensor is
zero. Bind the optimizer/no-weight-update receipt, effective-delta hash, and
BASE/LR0 identical raw response bytes on common deterministic calls.

This preserves LR0 as a strong training-path/pipeline twin without requiring
an impossible all-zero standard initialization.

## Should P-CHAIN-2 precede M-COMBINE-4?

**It should precede any combined interpretation or Stage-3 coupling, but it
does not need to serially precede M-COMBINE-4 Stage 2A.**

The experiments answer orthogonal upstream questions:

- P-CHAIN-2: can the writer expose two opaque parametric bindings through one
  canonical composed output?
- M-COMBINE-4 Stage 2A: can a supervised controller coordinate autonomous
  READ/STEP/CHECK/STOP over an exact external text service?

M-COMBINE-4 does not consume a parametric memory and therefore does not depend
on a positive P-CHAIN-2 result. With multiple GPUs, source work and eventual
fits may proceed in parallel after their own gates. Both must be green before
designing the later same-adapter memory-plus-controller junction. If only one
passes, the failed primitive—not the combined organism—is localized.

EVENT-retention-v2 acquisition remains a real prerequisite for P-CHAIN-2's
writer recipe. A retention-v2 miss should stop P-CHAIN-2 rather than invite a
post-result heat/rank rescue.

## Allowed outcome after repair

If free one-hop extraction, prompt-fact qualification, AUTH composition,
DERANGED assigned composition, paired same-ID redirection, LR0 identity, and
canaries all pass, the maximum defensible statement is:

> In a single-seed development ceiling, a rank-8 adapter exactly generated
> two separately supervised opaque NEXT atoms and returned the assigned
> endpoint on held two-hop queries. A same-identifier counterfactual adapter
> preserved the first atom and redirected the second atom and endpoint under
> its alternate learned binding.

If endpoint candidates remain on the primary query, replace `generated the
second atom` with `selected the assigned second-hop endpoint`. Do not claim
that the printed intermediate causally mediated the answer, that explicit CoT
was necessary, that the facts were independently acquired, or that this is
own-life/retained/autonomous memory.

## Promotion checklist

P-CHAIN-2 is implementation-ready only after a successor document resolves,
without changing the frozen material scale or dose:

1. no-candidate one-hop extraction;
2. descriptive-only direct-output scoring;
3. D1/D2 primary-safe stopping;
4. exact atomic serialization and trainer/evaluator custody;
5. second-line LOCAL positional matching;
6. executable predeclared nulls; and
7. effective-delta LR0 semantics.

Until then: **no source/material/model/GPU GO from this audit.**
