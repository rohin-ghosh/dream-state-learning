# SEQ153 retention repair — decision brief

September 13, 2026. **Recommendation: one 3e-5, eight-pass fork across all three
original learners, importing their completed LR0 endpoints.** Do not combine
LR and replay changes. Main owns selection, implementation and launch; this is
design only, not a promotion or launch approval.

## 1. What needs repair

Stored summaries, not a new cell reduction (WRITE versus LR0):

| Seed | Exact-cue source-faithful /n | Paraphrase /n | Held content /48 | Canary /12 |
| --- | --- | --- | --- | --- |
| 0 | 8/14 vs0 | 6/14 vs0 | 44 vs47 | 12 vs12 |
| 1 | 7/8 vs0 | 5/8 vs0 | 37 vs48 | 12 vs12 |
| 2 | 5/8 vs0 | 5/8 vs0 | 17 vs48 | 12 vs12 |

“Exact-cue” is not exact-byte recall: WRITE exact bytes are7/14,7/8,5/8.
The3/11/31 held losses matter despite perfect narrow canaries. Native finite
updates and cold carriage work; selective retention does not. Repeated records
are not independent samples. Lovelace retains detailed cell/replay reduction.

## 2. Smallest informative experiment

Fork each **original perception adapter**, never its damaging WRITE descendant.
Change only WRITE LR1e-4→3e-5; keep all14/8/8 admitted raw child targets,
eight passes, batch1, fresh same-seed optimizer, rank8, masks/EOS, deterministic
epoch orders and exact/paraphrase/held/canary calls unchanged. Preserve originals;
no dose ladder, checkpoint selection, row filtering or automatic extra trial.

Incremental cost: **3fits,112/64/64 updates (240 total),240presentations;
88/76/76 readbacks (240 total)**. Existing training encodings imply41,608 input/
padded tokens and6,776 supervised tokens across these fits; lower LR does not
reduce token work. Keep the conservative3600s controller cap per learner
including verification/cleanup (≤3GPU-hours), plus≤180s collection per new root;
this is a ceiling, not a runtime estimate. No old LR0 fit or readback is rerun.

**Proposed exploratory screen, frozen before the fork:** retain at least the
observed8/14,7/8,5/8 source-faithful exact-cue counts while restoring every
LR0-correct held item and all canaries, for each learner—not just the mean.
Report paraphrase, raw bytes, canonical format and itemwise losses separately.
If this fails, report the recall/retention tradeoff; do not call reduced damage
a stable substrate or quietly relax the screen. One tested lower LR, then Main
decides whether further evidence warrants replay.

## 3. Reuse interface: explicit historical control, not fake completed stages

The frozen runner has hardcoded LR in `config_for`, closed `validate_spec`,
four `STAGES`, and `collect`/`validate_completed` requiring both fits/readouts.
**It has no existing single-arm/imported-control mode.** Do not patch its old
plans, call its collector again, or forge current LR0 stage receipts.

Small versioned extension: a candidate-only fit/readout controller plus a
read-only `reuse_control` manifest pointing to existing **scores, collection,
completion and plan hashes**, seed, parent/tensor inventory, dataset/training/
calls hashes, scorer/source pins and inference configuration. Reuse
`build_calls`, `score_calls` and `summarize` semantics; pair new candidate rows
with stored `scores.cells.LR0` by row ID in a separate comparison artifact.
Label old1e-4 and LR0 observations **reused, noncontemporaneous**, never as new
cost or additional replications. No duplicate reducer is needed.

Before reuse, bind identical original adapter and LR0 initialized/final tensor
identity after recorded dtype conversion; identical source facts, tokenized
prompts, output caps, engine/model/scorer versions and deterministic settings.
Reject mismatches rather than silently substitute another baseline. New-root
custody proves only its own stages; imported evidence keeps its original custody.
Main must add CPU regression coverage for import mismatch, duplicate/missing row,
one-shot collection and unchanged original files, then normal native provenance/
vacancy/lease checks. Failure to establish comparability requires explicit new
control planning, not an automatic rerun.

## 4. Why not start with replay—and its legitimate source

SEQ113/116 show useful distinct-source interleaving, but FOUR's advantage varies
by seed. SEQ118 retains M0/B1 at16/16 with replay while NEW_ONLY2 reaches8/16 M0
exact and4/16 B1, with arithmetic intact; replay halves new-fact dose and changes
allocation. These authored-memory results motivate replay, not causal proof or
permission to put teacher-authored Level1 targets into child SLEEP.

An available **own-source** fallback is each seed's same admitted v2 records:
archived `capture.json` → `episodes[].turns[].record.request.input_messages`
(original source-present task), paired with that record's exact raw child answer.
Use `dataset.json.rows[].source` execution/request/event hashes to join and keep
only the original admission set; no rewriting, held answers, OFF/other-seed
outputs or authored96row targets. This is a new source-present replay view of
existing experience, not more source-withdrawn repetition or invented targets.

If separately chosen: interleave one such replay presentation per memory
presentation, rotating distinct episode sources where possible, all records
equally exposed. Eight memory passes remain: **480candidate updates total** at
batch1,3fits,240readbacks; source-present token cost needs a new encoding audit.
This changes compiler/context mix and doubles presentations, so old1e-4 alone
does not isolate replay at matched compute. Imported LR0 remains a no-update
endpoint, not a newly executed replay-dose-matched control. These records span
only2/4/3 admitted triples and all have explicit priors: they do not cover broad
Level1 abstention/source families. Truly diverse replay requires prospectively
collected, source-verified **own** experience—not retrospective test copying.

## 5. Confirmation and evidence bindings

The original48held cases are now **exploratory repair panels**. After freezing
a candidate, a separately sealed source-disjoint48case skill panel plus12new
canaries per learner needs both candidate and unchanged-control readbacks:
360new calls, no fits, separately budgeted—not reusable old outputs on new cues.
This confirms that panel, not learner replication. Broader retention claims
also require fresh learner/formation seeds, own-record writes and new memory
access cues, with the recipe and selection rule fixed before inspection.
Keep the already-planned fresh-interaction diagnostic separate. No H1/H2,
general G3, learned closed-loop or mission-completion claim follows.

Read-only sources: `ASTRA_ACTUAL_RECORD_MEMORY_PROTOCOL_2026-09-13.md`;
`ASTRA_INTERLEAVED_MEMORY_READOUT_2026-09-12.md`; `ASTRA_SEQUENTIAL_MEMORY_2026-09-13.md`
(all under `research_notes/astra_memos/`). Frozen runner under `receipts_20260912/`:
`astra_real_record_memory_run_20260913.py`, SHA256
`7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`.
Score members are `real_record_memory_seed{0,1,2}_20260913_attempt1_collected/scores.json`
inside `gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar`.
Their locally checked SHA256 values, seed order:
`b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf`;
`5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979`;
`a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef`.
Only stored summaries/interfaces were inspected: no rescoring, code/targets,
native work or manuscript edits. **EDITSTOP — design delivered to Main.**
