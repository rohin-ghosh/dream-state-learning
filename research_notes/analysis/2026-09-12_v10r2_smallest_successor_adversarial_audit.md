# V10R2 smallest-successor adversarial audit

Date: 2026-09-12 UTC  
Status: docs-only, prospective scientific recommendation. No builder source,
run artifact, adapter, job, process, GPU reservation, or node was changed.

## Verdict

The smallest scientifically interpretable successor is **not** an oracle-only
patch and is **not** a replay or re-evaluation of attempt 2. It is a new,
prospectively sealed V10R2 with one calibrated response surface shared by
training, primary generation/scoring, oracle generation/scoring, and the
binary spill panels; a full clean-base OFF canary before fitting; fresh opaque
identifiers and held forms; then, only after that canary passes, four new
clean-base fits under the otherwise unchanged rank-8 recipe.

Candidate scoring should be retained and extended to the oracle, but it must
not replace unconstrained generation. The two measurements answer different
questions: forced two-candidate likelihood tests conditional action choice,
whereas strict free generation tests whether that choice reaches the declared
native action interface. A V10R2 pass needs both.

The already launched five-condition interface calibration is appropriately a
development calibration only. It may choose raw versus chat rendering for the
successor, but its old held oracle prompts cannot also be confirmation rows.
Once those outputs are inspected, use fresh identifier bytes and fresh held
template literals in V10R2. The calibration supplies no writer result and
cannot repair or promote W0 attempt 2.

## Why attempt 2 cannot be repaired into evidence

The exact attempt-2 root is
`/localhome/local-rohing/astra_diagnostics/astra_W0_v10r1_20260912_attempt2`
on node 3. The terminal report records four clean-base fits, 1,024 optimizer
steps, 1,504 requests, and 0.47178089486611147 A40-hours. Its report SHA-256 is
`407af1ff9ab3ca2865744e64155431cb00be8e21ab4025eb2fc4ac4d56bfb999`.

Two independent terminal defects remain:

1. All 256 explicit-table oracle generations consumed the complete 32-token
   allowance, emitted no terminal EOS, and were recorded `truncated:true`.
   Zero had complete stripped bytes equal to `ACT: a0` or `ACT: a1`; hence all
   four oracle cells have `oracle_BA=0.0` and the frozen label precedence gives
   `ASSAY_INVALID`.
2. `REAL_EXECUTION_SEAL.json` inventories 3,161 files and records
   `launcher.out` at the empty-file hash
   `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
   After the internal seal/replay, `main()` printed the returned 6,099-byte
   report into that in-root file. Its current hash is the report hash above.
   The exact frozen executor's read-only `replay-real` therefore exits 2 with
   `NONREPORTABLE_ABORT: sealed bytes changed`.

The seal fault is archival, but the oracle fault is not the only scientific
failure. The four fitted cells independently have only 4/16, 5/16, 7/16, and
8/16 keys at the required 0.50-nat NLL-gain threshold; generated BA is
0.3125--0.5000; own-minus-opposite BA is -0.15625--0.015625; maximum spill TV
is 0.26550--0.62228; and every root/map cell is 0/8 on exact unrelated native
outputs. Thus a prospective oracle-only repair could at best reveal the
already known downstream `OPTIMIZATION_INCONCLUSIVE` path. It cannot make the
old fits pass.

The defect also is not oracle-specific. In the exact OFF generation tree, all
464 records are truncated: 256 oracle, 128 primary, and 80 spill generations.
Every one therefore parses to no legal action under the frozen fail-closed
parser. Some adapters terminate earlier because supervised `ACT:` continuations
alter generation, but that does not make a raw-instruction base control a valid
common interface. The response surface must be repaired symmetrically.

Attempt 2 and its first aborted predecessor should remain byte-for-byte
terminal. Do not truncate or exclude `launcher.out`, rewrite the real seal,
soften the parser, accept an `ACT:` substring inside prose, reinterpret
truncation, or rerun the old reducer as if replay had passed.

## Disposition of the five proposed V10R2 choices

| Choice | Decision | Reason |
|---|---|---|
| Alter only the oracle | **No** | All 464 OFF generation outputs truncated, all unrelated native panels fail, and fitted likelihood/binding/spill gates fail independently. Oracle-only repair creates a cleaner label, not a writer result. |
| Alter all output prompts | **Yes, symmetrically** | Freeze one non-target-revealing binary response contract for train, primary, oracle, missing-mode, unsupported-mode, and neighbour contexts. Use a family-specific exact contract for the unrelated native output. Apply the selected raw/chat renderer identically to generation and candidate scoring. |
| Use candidate scoring | **Yes, alongside generation** | Existing primary/spill scoring is the right conditional-choice instrument. Add typed oracle scoring to separate supplied-table headroom from emission-format failure. Do not use closed-set scoring as a substitute for native free action. |
| Add a pre-fit clean-base oracle canary | **Yes** | Run all clean-base OFF controls first and stop automatically before any optimizer or adapter write if they fail. This prevents another four-fit run with a broken positive control. |
| Rerun fits from clean base | **Yes** | The response renderer changes the exact token stream and candidate boundary. Calibration/attempt-2 outcomes are known. A reportable V10R2 requires new fit-input hashes and four `OFF_CLEAN_BASE` loads; old adapters may appear only in a separately labelled development diagnostic. |

“All output prompts” includes the training contexts. If an explicit instruction
is added only at evaluation, V10R2 introduces a train/evaluation surface shift.
If it is added only to the oracle, oracle and fitted cells differ in more than
knowledge availability. The exact instruction must not reveal which candidate
is correct; for example, it may name the allowed complete outputs but not the
target. If chat rendering is selected, training and scoring must use the same
single user-message rendering plus assistant-generation boundary that free
generation uses. Do not template the answer into the user message or duplicate
special tokens.

The development calibration currently crosses
`raw_original_32`, `chat_original_32`, `raw_explicit_32`,
`chat_explicit_32`, and `raw_original_256` over 64 old held oracle prompts,
for 320 calls with the unchanged strict parser and no adapters. A parsimonious
successor rule is: explicit instruction is mandatory; prefer raw explicit at
32 tokens if all four calibration cells meet the old oracle threshold, else
use chat explicit at 32 if it does; if neither does, stop rather than fit.
`raw_original_256` diagnoses whether verbosity merely outlasted the old cap;
it should not by itself justify a verbose 256-token scientific interface.
If calibration results were inspected before this choice rule was frozen,
that is ordinary development selection, which makes fresh V10R2 confirmation
material mandatory rather than invalidating the calibration.

## Minimal prospective V10R2

Keep the abstract two-root orientation tables, complementary maps, per-key
multiplicities, rank/alpha/dropout, 128 rows and 256 updates per fit, context
masking, four root/map cells, fit seeds, thresholds, gate precedence, one-node
execution, and three-A40-hour cap unchanged. Change only what is needed to
make the response/evidence interface valid:

1. Materialize new opaque identifiers from a newly frozen identifier seed and
   four new held-template literals per root. They must be byte- and token-level
   disjoint from the 64 calibration prompt pairs. Retain the old abstract
   geometry and nuisance balance. Adding the common response contract to the
   eight training forms creates new exact fit inputs and is not a relabel of
   the attempt-2 corpora.
2. Freeze one renderer selected from the development calibration. Render the
   same non-target response contract on training, primary, oracle, and binary
   spill requests. Generation and scoring for a coordinate must have exactly
   the same prefix bytes/token IDs. Preserve exact continuations
   `ACT: a0\n` / `ACT: a1\n` plus EOS, the ASCII parser, no retry after model
   output, and fail-closed truncation.
3. Add `oracle_score` requests for both candidates. Oracle score choice is the
   finite argmax of the complete candidate-plus-EOS log likelihood, with a
   tie counted wrong. Keep strict `oracle_generate`. The explicit table is
   confined to these two typed oracle operations and never enters fitting,
   primary, spill, or caches for another operation kind.
4. Execute all OFF work before fitting in fresh clean-base processes. With the
   current panels plus oracle scoring, the prospective complete request count
   is 1,760: 384 primary generation, 384 primary score, 256 oracle generation,
   256 oracle score, 240 spill generation, and 240 spill score. The OFF-first
   block is 928 requests and can share two fresh clean-base loads by operation.
   It contains all 256 oracle generations/scores, 128 OFF primary
   generations/scores, and 80 OFF spill generations/scores.
5. Before any fit worker starts, require in each root/map both generated oracle
   BA and scored oracle choice BA at least 0.90. Also require the OFF response
   interface itself to be usable: no truncation/multiple `ACT` on the declared
   binary response canary beyond a prospectively frozen tolerance, and 8/8
   exact unrelated native outputs per root. The exact tolerance must be frozen
   before the new outputs exist; reusing the existing 0.95 validity convention
   is the smallest choice. A canary failure writes and seals a complete
   zero-fit `ASSAY_INVALID` terminal artifact and launches no optimizer.
6. Only after that automatic gate passes, run all four new fits from the
   frozen base. No attempt-2 adapter, optimizer state, cache, fit seed search,
   best rerun, or warm start is admissible. Evaluate once under the same
   renderer and unchanged downstream gates.
7. Keep stdout/stderr and worker logs outside the evidence root. Seal only
   after all in-root writers are quiescent; after controller exit, create a
   separate post-exit capsule binding the immutable root and external logs.
   A valid external log is custody evidence, not a reason to omit a mutable
   in-root file from replay.

Running the OFF block before the fits does not make it an outcome-adaptive
experiment if the controller's only possible transitions are prospectively
fixed: exact canary pass proceeds to the four declared fits; any failure seals
and stops. Humans must not inspect partial outputs and modify prompts,
thresholds, roots, or recipes inside that run.

## Minimal prospective CPU and tokenizer tests

No CPU fixture can show that Qwen follows an instruction, but the following
tests are sufficient before the staged GPU canary:

1. **Fresh-material/disjointness:** regenerate both V10R2 roots exactly;
   require new identifier and held-prompt hashes absent from the calibration
   manifest, no cross-root identifier/neighbour collision, unchanged target
   complements, equal counts, and exact 1/2 maxima for every registered
   shortcut family.
2. **One renderer everywhere:** for every train/held/binary-spill coordinate,
   assert the model-visible response contract is identical across OFF/W+/W-,
   target permutation cannot change its prompt, and oracle differs only by
   its typed explicit table. Mutate each renderer/template field and require
   manifest/request hashes to change.
3. **Real-tokenizer boundary:** on all four fits and all 1,760 requests, assert
   exact round trip, no prompt/target straddling, identical generation/scoring
   prefix IDs, equal candidate masks/counts, one EOS, no duplicate special
   tokens, and prompt plus 32 generated tokens within 2,048. Exercise both
   the chosen renderer and deliberately wrong raw/chat/double-template cases.
4. **Oracle anti-flow and score arithmetic:** `oracle_generate` and
   `oracle_score` must be OFF-only, typed, cache-disjoint, absent from fits and
   primary/spill projections, and scored over the exact full candidates.
   Golden fixtures cover finite score, non-finite abort, tie-as-wrong, exact
   0.90 boundary, and score-pass/generation-fail separation.
5. **Stage-order fail closure:** a canary-pass fixture launches exactly four
   fit workers afterward; each canary failure mode launches zero fit workers,
   creates no adapter/optimizer receipt, seals a zero-fit terminal report, and
   replays read-only. Partial human inspection has no dispatch API.
6. **Clean-base enforcement:** reject old adapter hashes, missing
   `OFF_CLEAN_BASE`, repeated initial-state mismatches, fewer/more than four
   fits, any warm start, changed seed, skipped update, or old fit-input hash.
7. **Request/reducer exactness:** assert the 1,760 cardinality and every panel
   denominator, both-root AND reduction, unchanged downstream thresholds and
   precedence, strict truncation/parser behavior, and a fixture where oracle
   generation/scoring pass while optimization, binding, interface, and spill
   each fail independently.
8. **Post-exit seal regression:** invoke the actual CLI return/print path in a
   subprocess with sibling stdout/stderr, close the descriptors, then require
   exact inventory equality and successful `replay-real`. Redirecting either
   descriptor directly, through a symlink/hard link, or through a tested
   logger/tee into the run must reject before GPU access. Mutating the external
   log must break the post-exit capsule without changing root replay.

The current FD-custody guard in commit `92a800bd` is a useful prevention
repair, but it does not by itself make attempt 2 replayable or establish the
full post-exit success path. V10R2 preparation must bind the changed source and
tests in a new root; an old prepared seal cannot authorize the repaired bytes.

## Honest claim boundary

A full V10R2 pass would support only this statement:

> Under one development-calibrated, explicitly scaffolded response interface,
> four newly clean-base-fitted rank-8 adapters over two engineered roots met
> the predeclared seen-key conditional-choice, exact generated-action,
> enumerated shortcut, spill, and unrelated-interface gates.

It would not show that attempt 2 passed; that the raw unscaffolded Qwen
interface works; that candidate scoring is native action; that the LoRA has a
particular internal representation; that a random future fit succeeds; or
that the recipe is generally reliable. It also would not establish unseen-key
generalization, authentic child authorship, lived outcome learning, memory,
retention, DREAM, parenting, connected knowledge, recurrence, continual
learning, H1/H2, or a whole organism.

If the pre-fit control fails, the result is an interface/assay failure and no
writer inference exists. If it passes but the all-key likelihood gate fails,
the registered conclusion remains recipe-local `OPTIMIZATION_INCONCLUSIVE`,
not substrate incapacity. Downstream non-pass labels retain their narrow
precedence-conditioned meanings. The five-condition calibration can support
only a development statement about strict action formatting and truncation on
old oracle prompts; it cannot be pooled with V10R2 or counted as a root.

## Evidence inspected

- `AGENTS.md`
- frozen attempt-2 source at commit `27743d0a`
- current custody/calibration source at commit `92a800bd`
- the exact node-3 attempt-2 terminal root, including report, seal, requests,
  OFF/oracle raw generations, resources, and frozen-source read-only replay
- `research_notes/analysis/2026-09-12_v10r1_w0_attempt2_terminal_assay_and_seal_failure_audit.md`
- `research_notes/analysis/2026-09-12_v10r1_w0_terminal_infrastructure_abort_audit.md`
- V9, V10, and V10R1 exact scopes and the V10R1 fit-variance decision
- the five-condition development-calibration and stdout/stderr-custody repair
  handoffs under `research_notes/astra_memos/receipts_20260912/`
