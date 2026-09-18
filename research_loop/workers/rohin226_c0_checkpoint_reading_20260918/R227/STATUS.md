# R227 C0 — read-only current recipe and publication receipts

Historical 08:39 cut. See `FOLLOWUP.md` and `LATEST.public.json` for the subsequent publication/status read.

Observed **2026-09-18 08:38:55–08:39:42 UTC**. R227 requires all own-child rows to train, retaining provenance, external-token masking, and technical validity. **That exclusion-OFF state is not yet effective in this C0 native.** No pause, restart, signal, deployment, parent publication, model/GPU call, or remote write was performed by this audit. No V2 was adopted. Shared native code was not edited.

## Actual current life

- Same native PID **2561156**, start ticks **94173182**, node2 GPU4. Same original parent **2561001 / 94172764** and existing additive reading publisher **2729920 / 94773801**. All identities matched and were alive, not stopped.
- Exact-command discovery found one original-parent process and one reading-publisher process, not duplicates. This is an exact-identity check, not a fleet-wide claim.
- Latest captured completed sleep: **cycle66, record942, total optimizer5356**, 32 updates in this sleep. The final UPDATE941 finished **08:37:28.040171 UTC**; completion-file mtime is **08:38:21.086841 UTC**. SLEEP_COMPLETE has no embedded wall timestamp, so mtime is explicitly not an embedded completion time.
- First reading is now in the **completed cycle65 ledger**: REQUEST849, ACT-response857, SLEEP_COMPLETE877. Cycle66 records ACT890 and no new reading render. Math and gradual reading continue with the same original parent.
- Reading state at this cut: one publication, next reading after completed67, spacing3, English retry pending, memory_after_cycle=null. No second delivery or memory probe is claimed. Parent language guidance is distinct from a training-row exclusion.

## Loaded recipe, corroborated by actual sleep receipts

All eight inspected deployed source hashes occur in the unchanged guard's source pins; hashes are in `CURRENT.public.json`. Guard SHA remains `46b88748175a5750ec1de9f6e9b1e30fa1d49f38b4a4f8f7395de1275d137016`. Same LOADED1 SHA: `bfd5c0cce84abe72354adbe87de1916906be968db9c75ce108e7383c3834f1f9`.

| Loaded component | Actual policy / behavior |
|---|---|
| Code quality exclusion | `R194_FULLWIDTH_CODE_TARGET_EXCLUSION_V1` |
| Review/receipt exclusions | `R195_CHILD_ROW_REVIEW_V1` |
| Prose/script exclusion | `R209_ENGLISH_PROSE_TARGET_QUARANTINE_V1` |
| Content/meta exclusion | `R213_CONTENT_BEARING_TARGETS_V1` |
| Plain-context target exclusion | `eligible_rows` rejects `journal_scaffolding_target` unconditionally when presentation is enabled |
| Technical target validation | `R144_SPECIAL_TOKEN_TARGET_EXCLUSION_V1`; separate from quality policy |
| Training recipe | 16 new presentations, zero rehearsal, `MASKED_CAUSAL_CE_V1` |

**TARGET_ELIGIBILITY909**, file mtime **08:32:43.280913 UTC**, SHA `811161e361a87d492230dbcbbea81b49973698f3a3e6aa144e53fc0269d46711`: **3 new candidates → 2 retained, 1 excluded** for `provisional_english_target_script_quarantine`. Completed sleep942 repeats this exclusion. This is actual execution, not merely an old configured flag. Code/content policies were enabled but made no additional exclusions in this batch.

## Supported way off: no complete live switch found

- Subsequent Main handoff reports the prospective implementation and regressions ready: new `organism_v6/orch_r227_learning_policy.py`, with `learn_row_policy='R227_ALL_AUTHENTIC_CHILD_ROWS_V1'` in both plan and think configuration, explicit empty/false semantic-exclusion logging, and no history alteration. This is Main-reported prospective readiness, not a C0 deployment receipt. This worker has not adopted, deployed, or independently retested that shared change.
- Deployed `gpu/orch_r125_continual_native.py:717` loads the validated plan at entry; `NativeChild` keeps it in memory (`:317`). Sleep consults that in-memory plan (`:492`). No supported live filter-control/reload path was found in the inspected deployed entrypoints, native, driver, and filters. Editing a plan or source file does not establish a live change.
- Existing optional-policy validation accepts absent code/review keys at startup, not an `OFF` policy value (`organism_v6/orch_r194_code_target_filter.py:44`). Driver/trainer review settings must agree (`gpu/orch_r184_think_act_learn.py:841`), and driver prose/content options depend on review (`:135`). These are prospective configuration seams, **not a supported hot toggle**.
- Omitting those optional keys alone is also **not complete R227 compliance**: plain-context target rejection remains (`organism_v6/orch_r125_plain_context.py:84`). Do not disable presentation or external masking as a workaround.
- The concrete old loaded call sites are native sleep's review/code calls (`:526–530`) and plain-context target rejection (`:536–537`). Main's reported prospective common-path repair does not replace these in the existing process. No patch, control file, unsupported injection, pause, or restart was attempted here. Keep this life running while Main establishes the supported no-gap path; do not report exclusions OFF before an actual new recipe/eligibility receipt proves it.

## Read-only intention/artifact metric

Existing record909 R213 annotations across 3 candidates contain **1 meta/intention unit, 23 content units, 27 unknown units**. This is a sum of pre-existing heuristic labels, not a new assessment of truth, artifact quality, degradation, or learning. Unknowns are retained as unknown; prose can be content. The audit does not invoke a classifier, supply a learning gate, or change eligibility. The old live filter's separate effect is disclosed above.

## Publication and exact receipt paths

- Baseline manifest already pushed: **`51440f045749e8263d5c8dd7848b0b4de03448d8`**. Existing `C0_BASE_20260918T081045Z` manifest SHA remains `c46295bad37f0848b4e63204940afa56e4c700f074e91db6fb55ba0c174c8972`; no new capture or binary transfer.
- Reading schedule/helpers/tests and sanitized first-render receipts already pushed: **`21e4c1fe82f2e79a74b9e06a833127e443f0ce96`**, 11 paths, historical publication receipt records 14 passing CPU tests. Both commits were rechecked as ancestors of fetched `origin/main`; this audit did not fetch or create another commit.
- Existing public receipt: `research_loop/workers/rohin226_c0_checkpoint_reading_20260918/FIRST_READING.public.json`. REQUEST849 started **08:27:36.072316 UTC**, 9515 prompt tokens, all history masked; ACT-response857 finished **08:28:02.588876 UTC**.
- Raw REQUEST: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw/stream/records/00000000000000000849.json`.
- Raw ACT response: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw/stream/records/00000000000000000857.json`.
- Raw eligibility: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw/stream/records/00000000000000000909.json`.
- Raw completed sleep: `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw/stream/records/00000000000000000942.json`, SHA `3f09a24d0856ef36692d5795cfb0dda4b98d37644657f5b08efb39403868f223`.
- Reading ledger: `/localhome/local-rohing/orch_r226_c0_operator_20260918/reading/CYCLE_000065.json`; turn receipt: `/localhome/local-rohing/orch_r226_c0_operator_20260918/reading/TURN_0000.json`.
- New **local, not yet pushed** metadata-only receipts: `R227/CURRENT.public.json` and `R227/PARENT_AND_LEDGER.public.json` beside this report. They contain paths, hashes, aggregate counts and identities, never child text, host addresses, keys, private panels, or checkpoint bytes. The bounded live read is explicitly non-atomic; all 192 selected journal records passed canonical hash checks.
