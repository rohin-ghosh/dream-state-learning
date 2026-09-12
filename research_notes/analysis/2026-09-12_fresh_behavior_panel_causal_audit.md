# Fresh solution-disjoint behavioral reread: independent causal audit

Date: 2026-09-12  
Audited source: `bd74905c` plus canonical-metadata repair `e67539d2`  
Scope: design, helper, reducer, tests, and committed evidence only. No builder
source was edited; no model, GPU, fit, or remote job was invoked.

## Verdict

**REWORK BEFORE GPU.** The comparison is structurally capable of measuring a
narrow and useful effect: whether six already-fitted adapters change immediate
mini-Sudoku actions on exact output grids absent from their fit material, with
a wrong-binding adapter controlling target tokens and generic answer-format
learning. It is not ready under the current default preparation, because six
IDs at the front of the frozen candidate range have already been evaluated by
Qwen in committed prior work. Two smaller claim/custody gaps also need to be
closed before model output is generated.

After the minimum repairs below, this is a valid **exploratory same-family,
exact-output-disjoint behavioral generalization diagnostic**. It is not a
Dream/Think/Sleep, parenting, lived-experience, recurrence, or H1/H2 test.

While this audit was in progress, Main launched attempt 2 under the standing
builder authorization. Its frozen panel includes four of the six known-exposed
IDs: `1900071`, `1900072`, `1900073`, and `1900075`. Attempt 2 therefore must
be preserved as contaminated development evidence and cannot support the
fresh-panel claim regardless of its result. The launch gate below applies to a
new root; this watcher did not launch or stop the live job.

## What is sound

1. The useful and corrupt fits use the same 32 prompt contexts and the same
   multiset of answer text/token targets. The difference is whether each full
   solution is paired with its own puzzle or the next puzzle. Thus a useful
   advantage over corrupt is more diagnostic than an ordinary adapter ON/OFF:
   generic `ACT:`/Sudoku-output learning and answer-token marginals are matched.
2. The selector deterministically takes the first eligible candidates, validates
   native entries and unique solvability, rejects exact historical/within-panel
   puzzle and solution duplicates, stops after 16, and fails rather than widening
   the range. No model score is used by `select_panel`.
3. All six existing adapter inventories, all historical material bytes, the
   base inventory, runner source snapshot, generator digest, and package version
   are checked. The metadata tuple-to-list repair in `e67539d2` is correct: it
   canonicalizes only at the JSON evidence boundary and does not mutate native
   generator objects.
4. Each adapter retains a separately executed OFF/ON pair, exact prompts and
   wake seeds are checked, failed/missing workers are not silently scored zero,
   and later actions cannot rescue the preregistered first-ACT endpoint.
5. The implementation explicitly labels optimizer seeds as repeated fits on
   the same corpus and the shared 16-puzzle panel as exploratory rather than
   independent replications.

## Blocking issue 1: six candidate IDs are already model-exposed

The protocol says it was selected before candidate model output and begins at
`rg/mini_sudoku/1900070`. But committed artifact
`research_notes/astra_memos/receipts_20260912/astra_correction_utility_analysis_20260912_main.json`
(commit `e4013594`, 07:05 local, before the 09:48 protocol and 09:55 helper)
contains actual Qwen OFF/ON wake outputs and scores for all six IDs
`1900070` through `1900075`, across multiple earlier adapter cells. The same six
IDs already occur in the committed prior-exposure registries, including
`astra_constraint_prior_ids_20260912.json` (SHA-256
`a93b5d4a1d1ad365f116ec688979c38b1c1481bbcc21f18df09d2832df481097`).

Attempt 2 selected four of those six: `1900071`, `1900072`, `1900073`, and
`1900075`. The helper can exclude additional IDs, but `--prior-exposure-json` is optional
and defaults to an empty list. Its CLI expects a bare JSON list, while the
existing registries are objects with an `episode_ids` member, so those registry
files cannot be passed directly. No end-to-end test asserts that the known six
are excluded by `prepare`.

Minimum repair:

- Freeze a bare JSON list that includes at least `1900070`--`1900075`, after a
  final union/audit of committed and remote prior model-exposure ledgers.
- Make that file mandatory for this run, record its path/hash/provenance, and
  assert its candidate-range intersection in preflight.
- Prepare a new root with the list supplied. Preserve and decline any panel
  prepared without it. Skipping the six still leaves 24 frozen candidates;
  shortage must continue to fail rather than widen the range.
- Add an end-to-end preparation test proving exposed IDs are neither generated
  nor selected and are present in every spec's `selection_used_episode_ids`.

This is a selection/prospectivity defect, not evidence against the adapters.

## Blocking issue 2: a positive difference-in-differences is not by itself
## useful transport

The reducer's highlighted `solved_count_gain` is only

`(useful_ON - useful_OFF) - (corrupt_ON - corrupt_OFF)`.

That number can be positive when the useful adapter is flat and the corrupt
adapter merely causes harm. Such an outcome establishes content-sensitive
adapter damage, not successful transfer of useful behavior. The report exposes
the component cells, but its sole `all_three_positive` convenience flag checks
only this difference-in-differences.

Minimum repair: freeze a claim hierarchy before launch.

- **Useful exact-solution transport** requires a positive useful ON-minus-OFF
  first-ACT solve effect, a useful-ON advantage over corrupt-ON, and a positive
  difference-in-differences. Report each optimizer seed separately; do not make
  the third condition rescue failure of the first.
- If only the difference-in-differences is positive, the maximum claim is that
  correct versus wrong bindings differentially alter exact-output-disjoint
  behavior.
- Continuous first-ACT native score, native-best, action counts, and formatting
  remain diagnostics/secondary endpoints and cannot rescue a failed exact-solve
  claim after results are visible.

The exact numerical threshold (all three fits versus a descriptive mean) must
also be stated prospectively. With one shared 16-item panel and three optimizer
seeds, neither choice supplies independent-data significance.

## Blocking issue 3: prospective reducer and common-random validity are not
## enforced

Preparation records `helper_sha256`, but `reduce` never requires the executing
helper/reducer digest to equal it. It only writes the reducer's current digest
into the finished report. Therefore the endpoint implementation can change
after model outputs exist without failing reduction. Minimum repair: at the
start of `reduce`, require the current helper digest to equal the preflight
digest, and add a regression test that a post-preparation helper mismatch
fails.

The six OFF conditions have the same base, prompts, explicit seeds, and primary
endpoint, so their first-action/score vectors should be identical. The reducer
currently reports `all_off_action_score_vectors_equal` but does not make a
mismatch change evidential status. A mismatch means the intended common-random
comparison was not realized and, with only one draw per puzzle, stochastic or
runtime variation can mimic an adapter contrast. Minimum repair: preregister an
invalid/noncausal status when the OFF primary vectors disagree (preferably also
hash/compare raw first wake outputs), rather than merely emitting `false` next
to an otherwise positive headline.

Fixed useful-before-corrupt and OFF-before-ON order remains a time/device
confound. Counterbalancing before spec freeze would be cleaner, but for this
explicitly exploratory diagnostic it can remain a disclosed limitation if the
OFF equality gate passes and source/runtime custody remains exact.

## Endpoint and leakage boundaries

- First-ACT exact native solve is a valid immediate behavioral endpoint and is
  appropriately zero for missing/invalid/unmeasured ACTs. It is sparse but was
  selected before these readouts; partial credit is correctly secondary.
- The CPU oracle answers are stored beside the specs, not put in the model
  prompt, scratchpad, history, or fit corpus. The evaluator has no tools or
  retrieval, so this is not prompt leakage.
- Exact puzzle and labeled solution disjointness rules out verbatim full-grid
  target replay. It does **not** rule out Sudoku automorphisms, shared rows or
  substructures, generator-family overlap, or pretraining knowledge. Nearly all
  4x4 solution grids are highly symmetric. The existing limitation is necessary.
- The training targets are externally supplied oracle `ACT:` lines and omit the
  bootstrap's required `PREDICT:`-before-ACT behavior. This probe can measure
  answer-action behavior, but not prospective thought, calibrated prediction,
  self-authored experience, or compliant continual-agent cognition.
- The three optimizer seeds share identical training data and the evaluation
  panel. They estimate fit instability only; the 192 condition-cells must never
  be treated as 192 independent observations.

## Exact maximum claim if repaired and positive

The strongest defensible sentence is:

> On one prospectively fixed 16-puzzle mini-Sudoku panel whose exact puzzle and
> solution arrays were absent from the 32 fit examples and the previous
> 16-puzzle development panel, rank-8 adapters trained on correctly paired
> puzzle-to-solution actions produced a descriptive first-action exact-solve
> gain over the frozen base, and that gain exceeded the gain from equally dosed,
> target-token-marginal-matched wrong-pairing adapters, across [report the three
> optimizer-seed results individually].

This supports limited transport/generalization of a supervised conditional
action mapping to new exact outputs. It does not establish a newly learned
Sudoku algorithm, nonisomorphic generalization, untouched confirmation,
independent replication, statistical reliability, learned thinking, LoRA
memory extraction in general, parenting, or the Dream--LoRA--Think flywheel.

If useful ON does not itself beat useful OFF, replace "produced a gain" with
the weaker material-sensitivity statement above.

## Tests reviewed

Archived target-host receipts report 96/96 CPU tests passing after the JSON
canonicalization repair. The tests cover deterministic selection, exact
overlap and shortage, metadata/generator drift, pin checks, prompt/seed
checking, complete 12-condition reduction, first-ACT-not-best semantics,
custody, and failure preservation.

The same 96-test command is not portable to this macOS checkout: 48 tests fail
because `/var/folders/...` resolves to `/private/var/folders/...`, while
fixtures persist pre-resolution paths and custody intentionally rejects a
symlink in any ancestor. This does not contradict the recorded Linux target
pass or reveal a GPU-path scientific failure, but it means I could not
independently reproduce the claimed aggregate green suite on this host. Rerun
the target-native suite after the three repairs; add the exposure, reducer-hash,
and OFF-mismatch tests that are currently absent.

## Launch gate

No GPU until all of the following are true in a fresh preparation root:

1. known candidate exposures are mandatory, frozen, hashed, and excluded;
2. the useful-transport claim hierarchy/threshold is frozen;
3. reducer bytes are bound to preflight and OFF mismatch has a noncausal status;
4. the repaired target-native CPU suite passes;
5. 16 eligible items remain and all six immutable specs/manifests are frozen.

No new fit is needed. If these checks pass, the bounded six-pair reread is worth
its estimated GPU cost as an exploratory writer/behavior diagnostic, while the
main paper must continue to rely on separate own-experience and lifetime tests.
