# Fresh Paper-1 canary science audit: smallest causal-chain closure

**Date:** 2026-09-02  
**Status:** bounded, nonauthoritative advisory. This document does not change
the frozen Paper-1 goalposts, ratify bytes, authorize implementation, authorize
model/GPU/network/LoRA work, or promote a scientific claim.

## Verdict

The smallest worthwhile immediate experiment is a **single precommitted
held-out v03r collision pair**, run text-first and followed by exactly two
per-life MEMORY-LoRA trainings only if the text mechanism passes:

```text
fixed public action/outcome life
  -> target-absent recurrent prompted writes M0
  -> non-answer THINK0 / one non-evidentiary agenda coordinate
  -> {no return, own-coordinate return, matched-distractor return}
  -> frozen M1
  -> identical semantic corpus as text or per-life LoRA
  -> fresh adaptive THINK1 after final-goal reveal
  -> paired counterfactual state-token decision
```

Use fixed prompted policies. Do **not** train a LOOP adapter, compare learned
operation policies, sweep a rank pyramid, or add on-policy exploration. Those
are Paper 2/later. Do not build RML, PCFL-lite, a new action world, or a v03r
active-action projection before this canary. They add claims and failure modes
without answering the immediate question: can the already intended organs
actually pass information end to end?

This is a conditional recommendation, not a recommendation to run the current
files unchanged. v03r is the best existing *world geometry* for the canary, but
the present export and thinker contracts have launch-blocking mismatches listed
below. After those are repaired through the required architecture-deliberation
and exact human-ratification path, one pair is enough for an existence/failure
localization canary. It is not enough for a paper result.

## Is v03r actually suitable?

### What makes it the right minimum

v03r already supplies unusually useful causal controls:

- its two latent members have the same final-goal bytes and different correct
  answers;
- exactly one primary action-outcome record differs across the twins;
- route, effect, animal-role, target-baseline, source-calibration, and workshop
  information are all necessary to the exact public oracle;
- no local working window contains the full proof;
- the final goal is revealed after a pre-goal checkpoint;
- the pair, rather than two correlated members, is the scoring unit;
- a public-only oracle succeeds while registered edge-removal ablations fail;
- passive-signature splitting gives a genuine untouched split, and seed 5 is
  the first 46-episode held-out pair, so it matches the existing 46/22/16
  scheduler without padding or schedule surgery.

That is enough to test a fixed-deck chain from consequences of actions to a
later counterfactual decision. It is substantially closer to Paper 1 than the
unchanged Action World v0 and much cheaper than finishing proposal-only v2e.

### Why v03r is not launch-ready unchanged

1. **The structured precheckpoint export exceeds the intended public text.**
   `CounterfactualConfluenceV03R.precheckpoint_export()` iterates over
   `self.episodes` and copies `dict(episode.payload)`. For source/animal color
   rows, that includes the internal pigment `ratio`; `public_episodes()`
   deliberately removes that ratio because the rendered episode exposes only
   an opaque label. The comment that `public_record` contains no unavailable
   field is therefore false. The model boundary must use the skin-correct
   public projection, not the internal episode payload, and a mutation test
   must prove that every stripped ratio/latent field is unreachable.

2. **The final thinker is not implemented for this task.** The current v2e
   contract ends at THINK0 and explicitly omits RELEASE/final-goal scoring. The
   hardened `goal_conditioned_thinker` releases only when cited supported edges
   form a directed path from a declared anchor to an output entity. v03r's
   answer requires conditional subtraction/retention plus recipe mapping; it is
   not licensed by that path rule. A correct-looking state token cannot be
   called a valid hardened release until a public, goal-bound terminal contract
   exists that permits the model to commit the token while leaving correctness
   to the sealed offline scorer. Do not insert an exact arithmetic solver into
   THINK1 to close this gap.

3. **The existing no-feedback arm is not a no-return arm.** In
   `run_recurrent_text_experiment`, `no_feedback` still receives sixteen
   intrinsic RETURN_SLEEP calls. The causal recurrence contrast needs an actual
   M0 freeze with zero post-THINK0 dream calls, plus a compute-matched wrong
   coordinate arm.

4. **The model writer/self-check path is incomplete.** The generic scheduler
   can represent provisional/support/reinforce/supersede operations, but v2e
   deliberately keeps every cognition row provisional and performs only
   post-seal closure scoring. Offline relation normalization or the hidden
   expected polarity must never become admission, support, ranking, or training
   input. A support transition must be model-authored from visible independent
   evidence, with its false supported rows retained.

5. **The shortcut gate is incomplete.** The population test gates the passive
   predictor, but reports rather than gates the other public-feature
   combinations. The source file itself still declares the rendered-text/order
   shortcut audit and public final thinker/paired scorer as P1 blockers. These
   must fail closed before a scientific call.

6. **THINK0 is strongly scaffolded.** The operational probe gives the exact
   source endpoint, target endpoint, relation type, and instruction to request
   the join. It does not reveal the answer or twin bit, but it supplies most of
   the missing-dependency coordinate. Therefore a pass demonstrates
   *prompted agenda routing and recurrent use*, not autonomous dependency
   discovery or a generic dream policy. This is acceptable for a canary and
   nowhere else.

### Claim limits imposed by the world

The 46-event life is only about 1.1k rendered tokens and fits native context.
Its experience-producing actions are fixed, and the terminal is a one-token
prediction rather than an environment action. Thus even a perfect result does
not establish beyond-context value, superiority to RAG/long context, LoRA
necessity, policy-selected information gathering, better future experience,
lifetime growth, or a flywheel. It establishes only that a prompted fixed-deck
organism can construct, transport, and use life-bound connected memory in this
small paired synthetic family.

## Exact canary

### Frozen instance and models

- World: `lands-v0.3r-counterfactual-confluence`, aligned renderer, seed 5,
  latent bits 0 and 1; score them only as one pair.
- Split: held out by the existing passive-key split. No prompt, parser,
  realization, read, or stopping choice may be tuned after either seed-5 member
  is exposed to a model.
- Prompt-development domain: existing aligned development seeds 0--2 only.
  CPU gold fixtures may validate syntax and state transitions, but their
  scripted paths remain labeled ceilings.
- DREAM and THINK controller: pinned
  `Qwen/Qwen2.5-32B-Instruct` revision
  `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, bf16; DREAM one sample at
  temperature 0.2/top-p 0.95/max 256 tokens, THINK deterministic/max 128
  tokens per operation.
- MEMORY substrate: pinned Qwen2.5-7B revision already used by the transport
  harness, bf16, one fresh rank-64 LoRA per twin, alpha 128, dropout .05,
  q/k/v/o projections, learning rate `2e-4`, batch 32, maximum line length 96.
  Rank 64 is the existing measured transport setting; there is no rank sweep.
  One predeclared `1e-4` sanity fallback is permissible only if the post-train
  output is malformed/gibberish before any scientific read, and both the failed
  and fallback artifacts count in the ledger.

The two-model split must be disclosed: 32B supplies prompted cognition; 7B
supplies per-life parametric association reads. It is not evidence for a
single-backbone system.

### Common target-absent prefix

For each twin independently:

1. Run 46 WAKE calls, each seeing exactly the current public-projected action /
   observation / outcome and at most six current local semantic neighbors.
2. Interleave the existing 22 deterministic REACTIVATE calls. Each receives
   one earlier public record plus at most six local semantic neighbors.
3. Run 16 TARGET_BLIND_SLEEP calls under the same bounded visibility.
4. Freeze `M0` and its semantic/corpus hashes.
5. Reveal only the non-answer operational probe to a fresh THINK0. THINK0 may
   perform at most 12 typed operations over M0 and must either emit exactly one
   registered `REQUEST_DREAM` coordinate or defer. It never sees raw history,
   the final question, answer, twin bit, hidden oracle, scorer, or distractor
   coordinate.

The prefix is generated once per logical life and byte-cloned across return
conditions. There is no arm label in any model prompt.

### Return and substrate arms

| ID | Post-THINK0 write | Final memory/read condition | Purpose |
|---|---|---|---|
| `T-M0` | none | M0 as structured text | zero-return recurrence control |
| `T-OWN` | 16 calls selected by THINK0's coordinate | M1-own as structured text | complete text organism |
| `T-DIST` | 16 calls selected by the frozen matched distractor | M1-distractor as structured text | compute/type-matched selection control |
| `T-TWIN` | no new calls | the other twin's frozen M1-own as text | life-binding/path-use intervention |
| `L-OWN` | reuse frozen M1-own | own per-life LoRA, then clean 32B thinker | same-corpus parametric transport |
| `L-TWIN` | no new training | the other twin's M1-own LoRA | parametric life-binding intervention |

Only `T-M0`, `T-OWN`, `T-DIST`, and `T-TWIN` are run initially. Train the two
LoRAs and run `L-OWN`/`L-TWIN` only if the text gate below passes. The swapped
conditions reuse artifacts; they do not train extra adapters.

There is intentionally no separate no-memory arm in this existence canary.
`T-M0` isolates the return edge, `T-DIST` matches return compute, and the twin
swap isolates life-bound content. A no-memory model baseline becomes mandatory
in replication, but it does not localize the remaining recurrent/transport
failure better than these three controls.

### Target visibility and chronology

| Phase | DREAM/THINK may see | Must not see |
|---|---|---|
| WAKE / REACTIVATE / initial SLEEP | current/selected public-projected records; up to six local semantic rows; fixed process prompt | operational probe; final goal/answer; latent bit; internal ratios; oracle/scorer; future rows |
| THINK0 | operational-probe text and endpoints; frozen M0 through the reader; generic operation grammar | raw lifetime; distractor coordinate; final goal/answer; hidden polarity; proof path |
| RETURN_SLEEP | one selected public record; up to six recipient-local semantic rows; the coordinate as **selection only** | final goal/answer; donor memory; hidden score/polarity; coordinate as a citable premise |
| SLEEP/compile/LoRA train | exact frozen M1 semantic rows, statuses, provenance, and registered views | final goal/answer; THINK hypotheses/claims; offline normalization; oracle/scorer descendants |
| THINK1 | final public question; generic public entity/relation ontology; fresh empty workspace; one chosen reader backend | raw lifetime; M0/THINK0 scratch; agenda/arm label; answer; proof path; other backend |
| offline evaluation | committed artifacts, hidden expected answer, exact oracle/path | no output or feedback back into cognition/training |

The M1 semantic hash and complete text/LoRA training-corpus hash must be sealed
before the final goal is rendered to any model process. Run/skip evaluation
must leave all cognition and later bytes identical.

## Write semantics

Use exactly one generic `SELF_CHECK_DRIFT` writer condition. The no-gate versus
self-check precision trade-off and the v5 poisoned-corpus failure are already
known; repeating perfect-gate, no-gate, prompt ladders, or game-informed writer
ceilings would not answer this canary.

- One DREAM call may `PASS`, create one concept/edge, reinforce one existing
  row, or supersede one row. It cannot emit a batch or a final answer.
- Every created row starts `provisional` and cites only the public/memory
  handles visible in that call. Depth is computed from cited prior-memory
  parents, never declared by the model.
- A later `REINFORCE` may make a row `supported` only when it cites at least one
  independently visible public or semantic premise not used by the creation
  derivation. Rewording/repetition alone is not support.
- `SUPERSEDE` is append-only. The old row and all false model-supported rows
  remain in the artifact and in false-memory accounting. No hidden-truth
  filter, expected polarity, FactorSolver, relation allowlist, or scorer may
  create, delete, rewrite, support, reject, rank, or resample a row.
- The deterministic compiler may deduplicate exact semantic identities and
  render the registered canonical/QA/reverse/partial-cue views. It may not
  invent an edge, normalize an unrecognized relation into `causal_join`, or
  materialize the held-out answer.
- Text and LoRA conditions consume the same sealed active semantic rows,
  statuses, provenance, and four view strings. Repetition is training dose, not
  new evidence. Use the current exposed budget: 24 total touches per concept
  and 96 per relation. Train once over that exposure-expanded corpus.

Normalization-only scorer matches may be reported diagnostically but do not
count as closure and do not enter the transport corpus.

## Read and final-decision semantics

THINK1 is a fresh prompted controller, not a one-shot answer prompt and not an
answer-aware scripted read plan.

- It has at most 12 model operations and may form a subgoal, issue one typed
  atomic query, update/revise a cited workspace, backtrack, commit one state
  token, or defer.
- The query vocabulary exposes only public entity handles and generic relation
  kinds. It must not enumerate the oracle path, the correct object, a parent
  set, or a per-target sequence of query keys.
- The text reader returns at most one immutable exact row plus provenance and
  epistemic status, or `NOT_FOUND`/`CONFLICT`.
- The LoRA reader receives the identical typed cue, mounts only the recipient's
  adapter, generates one strict atomic memory line or `NOT_FOUND`, then
  unmounts. The clean 32B thinker performs all workspace composition. No
  hidden corpus scan or answer-candidate enumeration is credited to LoRA.
- Every commit cites the returned rows it actually used. The terminal contract
  checks syntax, scope, and citation existence only. The sealed evaluator—not
  an in-loop arithmetic verifier—scores the state token and reconstructs the
  cited path afterward.

Measure fixed read fidelity on every cited decisive row plus an equal number of
precommitted matched distractor rows under the four registered cue forms. This
is a path-local canary, not an estimate of whole-corpus recall.

## Conjunctive pass gate

Count every malformed output, exhausted budget, missing adapter read, defer,
or unscored member as wrong. There is no seed replacement or repair-and-rerun.
The canary passes only if all of the following hold:

1. **Visibility/integrity:** all forbidden-field mutation tests pass; no final
   goal/answer/proof/scorer descendant occurs before M1/corpus seal; both twin
   adapters start from the same clean base and no cache/index/workspace crosses
   lives or arms.
2. **Recurrent connection:** THINK0 emits the registered own coordinate on both
   twins. `M1-own - M0` contains at least one verbatim correct `causal_join`
   row absent from M0, with route/effect-bound public provenance and at least
   one prior semantic parent (computed depth at least 2). The corresponding
   own closure is absent from `M1-distractor`.
3. **Text behavior:** `T-OWN` gets both twins correct. `T-M0` and `T-DIST` each
   fail paired-both-correct. `T-TWIN` fails paired-both-correct and changes or
   defers at least one member relative to `T-OWN`.
4. **Actual path use:** both credited `T-OWN` commits cite the decisive returned
   atoms. Masking the new join or substituting the matched twin atom removes
   paired success. A final correct token without this path does not count.
5. **Transport:** fixed path-local varied-cue LoRA read fidelity is at least
   0.90; `L-OWN` gets both twins correct with the same operation budget as
   `T-OWN`; `L-TWIN` fails paired-both-correct and changes or defers at least
   one member. For a one-pair canary, text/LoRA noninferiority means exact
   equality of paired success, not a confidence interval.

This deliberately harsh one-pair rule is a kill gate, not a statistical test.
It is designed so a green result warrants replication and a red result names
the broken organ.

## Failure interpretation

| Observation | Interpretation and next action |
|---|---|
| THINK0 fails to emit the already scaffolded coordinate | Controller/interface failure. Stop; more dream sampling or LoRA cannot repair it. |
| Own depth-2 closure does not appear | Prompted recurrent connection formation failed under the bounded view. Stop before LoRA. |
| Own closure appears but `T-OWN` is not paired-correct | Text construction exists but adaptive reconstruction/use fails. Repair only the read/think organ under a new reviewed scope. |
| `T-M0` or `T-DIST` is also paired-correct | The return edge or own agenda is not causally identified. Report plumbing success at most; do not claim recurrent benefit. |
| `T-TWIN` remains paired-correct or masking has no effect | Life-memory attribution fails; prior, target shortcut, or controller leakage explains the answer. |
| Text gate passes but LoRA fidelity is below .90 | Parametric installation/read failure. Preserve a text-only mechanism result; do not tune ranks on the held-out pair. |
| LoRA fidelity passes but `L-OWN` fails | Stored atoms are readable, but the adapter-reader/clean-thinker handoff fails. |
| `L-OWN` passes and `L-TWIN` also passes | No causal per-life LoRA credit. |
| Every conjunct passes | One bounded existence result: prompted recurrence constructed, same-corpus text/LoRA transported, and a fresh thinker used life-bound memory for paired held-out prediction. Replication is still required. |

No outcome here authorizes language about on-policy learning, learned
exploration, a learned controller, compression advantage, LoRA superiority,
post-context persistence, saturation, continued improvement, or a flywheel.

## Approximate cost

For the seed-5 pair and the existing 46/22/16 schedule:

| Work | Maximum calls/jobs |
|---|---:|
| Common target-absent DREAM prefix | `2 * (46 + 22 + 16) = 168` 32B calls |
| OWN and DIST return DREAM branches | `2 twins * 2 branches * 16 = 64` 32B calls |
| Common THINK0 | `2 * 12 = 24` 32B calls |
| Four text final conditions | `2 * 4 * 12 = 96` 32B calls |
| Conditional two LoRA final conditions | `2 * 2 * 12 = 48` 32B calls, plus at most 48 online 7B reads |
| MEMORY-LoRA training | 2 rank-64 adapter jobs; twin swap reuses them |

The text kill gate is therefore at most **352 32B calls**. The full conditional
canary is at most **400 32B calls**, plus 7B memory reads and fixed probes. At
the registered output caps this is at most about **59.4k DREAM output tokens**
and **21.5k THINK output tokens**; tokenizer-exact input totals must be measured
before authorization and will plausibly be on the order of (10^6), not
assumed from call count.

Each own M1 has at most 100 created semantic rows because there is at most one
creation per 84 prefix plus 16 return calls. Under the current four-view touch
plan, the worst case is about **9,600 training lines per adapter** if every row
is relational (usually far fewer). The repository's measured upper anchor is
53 minutes for 94k lines x four epochs on Qwen2.5-7B; this canary should budget
roughly **0.5--1 GPU-hour per adapter including startup/sanity**, not claim a
linear speedup before measuring it. Two existing rank-64 adapters occupy about
**308 MB** total, excluding logs.

Using the measured 32B H100 timing anchors, reserve approximately **2--4 H100
GPU-hours for inference** and **1--2 7B GPU-hours for both adapter jobs and
reads**, or roughly **3--6 GPU-hours total** plus artifact verification. Parallel
adapter training can reduce wall time but not scientific cost. These are
planning bounds, not authorization.

## Relationship to `chg_20260901_rml_pilot_v1`

The proposed v03r canary and RML are **not duplicate experiments**. They overlap
in the eventual causal story, but sit at different rungs of evidence:

| | Repaired v03r canary proposed here | `chg_20260901_rml_pilot_v1` |
|---|---|---|
| Immediate question | Can all frozen Paper-1 organs transmit one causally necessary, life-specific connection end to end? | Can a paper-facing rendered lifetime benchmark support construct validation, scale/horizon studies, attribution, strong baselines, and eventually fixed-deck/on-policy comparisons? |
| Current substrate | Existing paired v03r world and scheduler, with a bounded blocker list | Proposed fluid/thermal reference world followed by multiple non-isomorphic packs and staged model experiments |
| Experience | One fixed 46-event action/outcome life per twin | Intended 0.5x/2x/4x/8x native-context horizons; fixed deck first and randomized on-policy work later |
| Endpoint | One paired counterfactual state-token decision whose answer flips under a one-record collision | Broader R/N/O/J/P/X diagnostics and multi-step behavioral/action endpoints |
| Experimental width | One held-out pair; four text arms; two conditional LoRA arms | CPU construct gate, gold/text/LoRA stages, three-pack confirmation, large baseline matrix, then possible flywheel work |
| Decision value | Kill or advance the concrete organism in at most 352 text-gate calls / 400 full 32B calls plus two small adapters | Establish generality and paper-grade operating regimes after the organism and benchmark construction separately survive |

RML is therefore a **later benchmark/confirmation line**, not a replacement
for the immediate v03r organ-closure test. A future, fully validated RML program
could supersede v03r as the paper-facing evidence base; it does not supersede
this canary as the cheapest way to learn whether the currently intended
organism works at all.

That distinction is also forced by the actual change state. The RML v1
consensus is `human_required` with recommendation `rework`, says v1 releases
nothing, sets `implementation_forbidden: true`, and calls for a newly
hash-bound **CPU-only RML-D0 v2** before any model, GPU, LoRA, or downstream
benchmark work. A green RML-D0 would validate only the reference construct and
model-independent causal-unit cuts; it would not demonstrate the prompted
recurrent writer, text/LoRA transport, adaptive thinker, or paired model
behavior. Conversely, a green v03r canary would not validate RML's horizons,
packs, action tasks, or generality. Building RML first would postpone, rather
than answer, the unresolved Paper-1 organ question.

Accordingly:

- **v03r as currently executable: NO-GO.** Its private-field export, missing
  public final thinker, nonzero purported no-return arm, and incomplete
  shortcut gates invalidate a launch.
- **the minimal v03r repair: REWORK, then GO only after exact ratification.**
  The minimum decisive immediate Paper-1 experiment is precisely the seed-5
  paired text gate above, followed conditionally by the two own/twin LoRA
  reads. It is decisive for end-to-end causal-chain existence or organ-level
  failure localization, not for statistical generalization.
- **RML v1 as currently proposed: NO-GO / REWORK by its own consensus.** Keep
  it as the later benchmark roadmap; do not treat its unratified CPU D0 or its
  much larger future matrix as a prerequisite for this canary.

## Work that should be rejected now

- Do not execute the full six-life v2e proposal-closure package first. Its
  514 shared DREAM calls plus D-scaled branch/exploratory work still omit the
  final goal, final thinker, LoRA, and behavior endpoint.
- Do not add a learned LOOP arm, behavior cloning, rejection SFT, a policy
  baseline ladder, or the rank/data-timescale pyramid. Prompted control is the
  frozen Paper-1 condition.
- Do not add an active intervention menu or restore Action World v0. Fixed
  v03r action-outcome records are sufficient for this fixed-deck Paper-1
  canary; active evidence acquisition is the later flywheel claim.
- Do not sweep seeds, skins, prompt ladders, hypothesis budgets, ranks, or
  model sizes before this pair passes. Replication is downstream of organ
  closure.
- Do not run perfect-gate/no-gate writer arms. Existing results already show
  the self-check precision trade-off and v5's poisoned-corpus failure.
- Do not run raw long context or RAG as if v03r could decide their saturation.
  The complete life fits context, so those conditions are predictable small-
  world ceilings, not tests of the frozen beyond-context clause. Strong native
  context, iterative RAG, linked memory, exact graph, raw/direct-QA LoRA, and
  same-lifetime batch SFT remain mandatory for later paper-scale evidence.
- Do not treat relation normalization, exact public oracle, scripted gold
  reads, or game-informed prompts as headline cognition. They are offline
  diagnostics/ceilings only.

## Advisory decision

**Current state: NO-GO to launch; GO to a narrowly scoped repair and exact
ratification of this one-pair canary.** The repair surface is only the public
export, actual zero-return branch, model-authored support semantics, final
public thinker/commit contract, paired scorer, and shortcut/visibility tests.
If that surface expands into a learned controller, new world, on-policy action,
rank study, or benchmark program, reject it and return to the bounded canary.

A green result earns one next step: freeze the exact organism and replicate
across the registered seeds/skins with the full strong-baseline matrix. It does
not itself close the paper's beyond-context or continuing-improvement claims.
