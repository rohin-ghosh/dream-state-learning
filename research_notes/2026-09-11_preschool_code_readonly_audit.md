# Preschool implementation: read-only audit

Date: 2026-09-11

Status: independent read-only audit. No file was imported or executed and no
test, model, tokenizer, training, parenting, or GPU action was performed. The
reviewed files are unratified material loop changes and must remain inert.

## Verdict

Do not sync or launch the current implementation. It is not yet a trustworthy
disposable affordance scout, and no part of the preschool feature is a
non-material repair: it changes the interaction loop, generated tokens,
information visibility, corpus eligibility, promotion behavior, and scientific
estimand.

## Fatal correctness blockers

1. **Execution IDs repeat across visits.** The ID contains only program ID,
   tick, and within-episode action count. Repeated visits to a program recreate
   the same ID. See `organism_v6/preschool.py:145`.
2. **Generation randomness repeats across visits.** Ordinary wake seeds and
   `NOTE_AFTER` seeds omit occurrence/visit index. See
   `organism_v6/batch_loop.py:132` and `organism_v6/preschool.py:181`.
3. **Resume is not transactional.** Ledger rows are appended before the wake
   marker; a crash can rerun and duplicate a batch. Pending post-outcome rows
   are cleared before generation. Neutral probes have the same
   ledger-before-marker problem. See `organism_v6/run_life_v2.py:824`,
   `organism_v6/preschool.py:170`, and `organism_v6/preschool.py:476`.
4. **The resume test does not exercise resume.** It merely verifies that
   events exist. See `tests/test_preschool_flags.py:334`.
5. **A sleep report can be committed before `COMPILED`.** A crash in that gap
   causes the rerun to overwrite the report using an empty delta. See
   `organism_v6/run_life_v2.py:882` and `organism_v6/preschool.py:414`.
6. **The gate counts the wrong quantity.** Enforcement compares the cumulative
   admitted set with 64, while q14 requires 64 distinct new records in the
   current block. See `organism_v6/preschool.py:369` and `:401`.
7. **Clone mode silently omits the gate.** The flag is accepted, but the gate
   is executed only in the non-clone branch. See
   `organism_v6/run_life_v2.py:879`.
8. **The feature claims generic gym support but is compiler-specific.** Outcome
   parsing, examples, and the default neutral panel encode CompilerGym. A
   task-disjoint nursery will be misparsed or contaminated. See
   `organism_v6/preschool.py:82`, `:106`, and `:114`.
9. **Invalid configurations are accepted.** Examples include enforcement
   without `NOTE_AFTER`, a lesson without its slot, clone plus enforcement,
   and simultaneous dynamic parent plus fixed lesson.

## Major design and claim blockers

1. **The nominal single lesson is repeated in every tick prompt for a whole
   block.** The delivery log says once while effective exposure is dozens or
   hundreds of times. See `organism_v6/run_life_v2.py:538` and
   `organism_v6/batch_loop.py:41`.
2. **The new record cannot yet influence later cognition or sleep.**
   `NOTE_AFTER` is not inserted into subsequent context, and shadow mode does
   not add it to compilation. The current code therefore measures prompted
   transcription. See `organism_v6/preschool.py:190` and
   `organism_v6/sleep_compile.py:269`.
3. **The lesson uses real compiler passes.** It can directly affect actions and
   makes these children CompilerGym-exposed, so they cannot become clean final
   deployment ancestors.
4. **There is no causal parenting contrast.** The implementation lacks an
   active sham, adapter ON/OFF mediation, a later-choice endpoint, and complete
   parent/context removal.
5. **The gate does not require first-person articulation.** It may train
   grounded third-person text even though the proposed endpoint is a
   first-person record. See `organism_v6/preschool.py:347`.
6. **Required receipts are missing.** The report omits episode coverage,
   optimization-success strata, the manual 98% audit, model/adapter identities,
   corpus hashes, unmatched-number census, and source/age survival. See
   `organism_v6/preschool.py:376`.
7. **“ACT executed” is not authoritative execution.** It records the model's
   requested string rather than a backend-returned canonical sequence of
   passes that actually executed. See `organism_v6/batch_loop.py:77`.

## Flags-off claim

The ordinary single-life, non-clone path appears behavior-preserving by code
inspection. Global byte identity is not proven: the test covers one compiler
scenario, while clone manifests gain new fields and changed runtime hashes.
See `tests/test_preschool_flags.py:138` and
`organism_v6/run_life_v2.py:457`.

One test also assumes that every valid execution improves the program, which
is false: a valid pass sequence can do nothing or regress. See
`tests/test_preschool_flags.py:176`.

## Required disposition

Keep the files local and inert. First ratify the scientific design. Then repair
the experiment in a scoped implementation with occurrence-indexed identities
and seeds, transactional writes, task-disjoint material, a truthful artifact
path into later context and/or sleep, an active sham, complete removal probes,
and exact receipts. No GPU run should be authorized until fresh independent
review confirms those properties.
