# R159 matched evaluator — parent-safe readiness

> Current gate/source: **runtime_generation3 witnessed-interval repair**. Execution generation1: learning COMPLETE56 calls atSeptember17 06:30UTC; frozen and unparented each DEVICE_BUSY before reservation, neither retried. Ledger1/12 reserved,56/672 charged; initial3 controls incomplete. NEW clear physical1 observation and unlaunched frozen readmission proposal await a NEW exact Main GO. See `execution_generation1/FINAL_RECEIPT.md` and `frozen_readmission_proposal1/MAIN_HANDOFF.md`. Original freeze/plan/source and UNKNOWN observations remain preserved.

## September 16, 2026 PDT / September 17 UTC

New helper and tests implemented; no old R130/R146/R158 controller, ledger, enrollment, cap, child, parent, or shared native module changed. Zero GPU dispatches/model calls and zero checkpoint enrollments. Actual successful cohort remains a Main-supplied binding; no readiness inferred from a COMMIT or an attempt number.

- **Instrument:** all28 existing reasoning_gym ledger items:4 within-family canaries,12 gate,12 exam. Paired LoRA ON/OFF, unchanged native greedy512 decoder, rank8, frozen Qwen2.5-7B-Instruct base. Fixed12 slots: three arms × initial/sleep1/2/4. Parented-frozen slots must retain unchanged step0 adapter and zero optimizer updates; these four slots implement the repeated-step0 schedule, not four extra jobs.
- **Separate budget:**56 nominal calls/checkpoint ×12 = **672 calls**, below720. Failed/ambiguous reservations charge all56 and never replay. Original4800-call/58-job limits and ledger remain untouched. Only node2 physical0/1 after original phase terminal; original physical locks and privileged vacancy scan, full3600s job window plus15s margin, separate node2 authority and six-hour lease margin. No child signals.
- **Actual sealed freeze:** September17 **04:52:56 UTC / September16 21:52:56 PDT**. Real installed reasoning-gym0.1.25 generated all28 items using actual `episode_from_id`. Final frozen-helper CPU smoke at05:00:40 UTC regenerated the fixed panel, exercised ACT parsing and invoked the native verifiers28 times on a synthetic smoke answer. PASS; CUDA hidden, no model calls/checkpoints, no items/keys/scores returned. Only `INSTALLED_GYM_CPU.json` metadata came back; all verifier outputs remain sealed on node2.
- **CPU:**317 tests pass:74 new R159 plus243 inherited native/scheduler/R158 continuation tests. Node2 lacks pytest; no dependency installed/copied. Full pytest runs locally using existing `/tmp/r136-pytest-support`; actual installed-gym smoke runs on the final receiving source.
- **Source:**1093 donor Python files unchanged; receiving tree adds only helper/test and two existing ledger/bootstrap data files (1097 pins). Exact runtime source/plan paths are in `RUNTIME_METADATA.json`. Generation1 freezer failure was missing ledger data in the Python-only donor, not a task/key/scoring failure. Preserve it; generation2 uses unchanged ledger/bootstrap resources in a separate tree.

## Compatibility and missing scope

R150 emits the supported R125 native COMMIT schema. Copies retain original COMMIT bytes/source paths; only adapter files are opened, never optimizer/RNG payloads or histories. Readiness requires actual INITIALIZED, copied hash-bound capacity RESULT with PASS/verified restoration/no updates, and clean initializer service exit.

Optional `initialization_source` is supported: cohort/INITIALIZED refs must agree; copied source/donor-COMMIT metadata and restored observations must prove identical original step0 adapter/AdamW/RNG hashes. Old paths remain provenance strings, never read/action targets. No attempt2/3/4 hardcoding. Freeze must predate the original initial COMMIT timestamp, including preserved recovery timestamps; no silent retrospective relaxation if this check fails.

Main still supplies actual cohort/initializer/capacity/lifecycle metadata, adapter-only copies and source-reader custody under the new campaign inputs, source-owner read authority, separate node2 budget, actual-provenance Builder gate, and exact execution/Main-GO files. CPU/source preparation is not GPU authorization. See `API.md` and `API_SCHEMA.json`.

## Claim limits

These28 fixed items are a narrow initial instrument, not a broad intelligence/capability test. Canary tests held seeds within train families; gate/exam test their specific held-family panels, not unrestricted general transfer. Pretraining contamination is not ruled out. One-shot ACT parsing and512-token censoring are declared constraints: parse failures, truncation, verifier failures and incomplete controls stay distinct. LoRA OFF is an adapter-activation diagnostic, not a replacement for frozen-parented and unparented-learning controls. Control completeness requires all12 COMPLETE slots; scores never select checkpoints. Language drift/repetition alone is not capability-loss evidence.

The original fixed capability/behavior battery remains a **separate unscheduled instrument**. Its unchanged30-item paired protocol adds720 calls across12 checkpoints; combining it with672 here exceeds the cap. No tasks, conditions, or scoring were altered to make it fit; no original-campaign results are relabeled as matched-cohort observations.

## Immutable hashes

- PLAN: `c2f32b5390f4d9a06ab30de1cd64eb91858055ca4944c6328edbad52125fed86`.
- FREEZE: `1515341fd0c8d1336cbea6728aa5ba3c27c638752964575affda2400002c81b6`.
- Tasks: `1fe62539536e5f74c956b40fe5e7cedeab750f8da209bc1c904fd245aab5bd47`.
- Prompts: `b5b7a17b2ead2e8aa5d0d6bbdc4a0ed7093da5dee464aec265358f915b1724a5`.
- Scoring: `b18dd017f550ee05e84b531f97de1c630f5bf012d6c72c0d3f6b987e4438ee56`.
- Helper: `86df360b1cd85d6d5b34e4962c5d0563ac0e1dd6b4228b5c1a3262037f1d515f`.
- Tests: `710977a38cbf97d2bd5178da7bb680f3280d4f0402120d14edad9c2387668d46`.
- Source manifest: `6ca1aca2c24e5063c79a92740a7d14c39b97064342ca5afa738f61e712de21cd`.

## [Builder] R159 CPU-only readiness — 2026-09-16 22:05:38 PDT / 2026-09-17 05:05:38 UTC

Implemented new matched evaluator and tests; API `freeze`, `gym-selftest`, `plan`, `validate`, `dispatch`, dispatcher-internal `evaluate`, metadata-only `status`. Separate immutable12-slot/672-call campaign; old4800/58 ledger/caps untouched. Actual installed reasoning-gym0.1.25 froze28 existing ledger tasks at04:52:56 UTC, then final receiving-helper CPU generation/parser/native-verifier smoke PASS at05:00:40 UTC; zero model calls/checkpoint enrollments. Local317 CPU tests PASS (74 new). No packages installed; node2 has no pytest, so receiving validation used the real installed-gym smoke rather than claiming remote pytest.

Runtime source `/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation/runtime_generation1/source`;1093 donor Python files unchanged. Helper SHA256 `86df360b1cd85d6d5b34e4962c5d0563ac0e1dd6b4228b5c1a3262037f1d515f`; tests `710977a38cbf97d2bd5178da7bb680f3280d4f0402120d14edad9c2387668d46`; SOURCE_MANIFEST `6ca1aca2c24e5063c79a92740a7d14c39b97064342ca5afa738f61e712de21cd`; immutable PLAN `c2f32b5390f4d9a06ab30de1cd64eb91858055ca4944c6328edbad52125fed86`.

Main's candidate4 remains unadmitted. Optional saved-initializer provenance supported; still require actual INITIALIZED, bound capacity PASS/verified restoration, clean service exit, adapter-only source custody/read authority, node2 budget and exact Main-GO. No inference from COMMIT alone or independent-review status. Preserved donor timestamp must satisfy prospective task-freeze gate. No GPU enrollment/launch. Prompts/answers/scores remain sealed;28 fixed items support only narrow panel claims, and original capability/behavior battery is separate/unscheduled to preserve the new cap. API, status, CPU and hashes: `research_loop/workers/r159_matched_evaluation_20260917/`.

## [Builder] R159 non-material timestamp-custody repair — 2026-09-16 22:19:32 PDT / 2026-09-17 05:19:32 UTC

Repaired only COMMIT-age custody: untouched older initialization is accepted only with exact saved-source recovery, unchanged original timestamp/adapter/AdamW/RNG hashes, zero saved-state generation/updates/exposure, actual INITIALIZED, bound capacity PASS and clean exit. New Main-bound source-owner timestamp receipt covers enrollment plus all3 arms' first birth/TRAIN/evaluation (or positively attested complete no-event history). Freeze must precede every observed exposure/enrollment; missing, ambiguous, post-exposure and refrozen evidence is refused. Actual candidate4 admission/custody and Main-GO still required; none synthesized.

350 CPU tests PASS (107 R159 +243 inherited). Actual receiving installed-gym28-task regeneration/parser/native-verifier smoke PASS; model_calls0/checkpoints_enrolled0. Runtime `/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation/runtime_generation2/source`; helper SHA23717c505fd077a65fabaf1b4a359b542a47879581a835a384387e5130c09806; tests SHA5f2b19eeaa71dfd8ac16d3b5440c71775b7bc962bd8284483ecb3647b7672293; manifest SHAa7f09b623ea9d270f9af70de38b299c2c80f516eae4bbafbab9ba0822f1d0200. Original PLAN SHA c2f32b5390f4d9a06ab30de1cd64eb91858055ca4944c6328edbad52125fed86 and04:52:56 UTC FREEZE SHA1515341fd0c8d1336cbea6728aa5ba3c27c638752964575affda2400002c81b6 unchanged, including sealed task bytes/selection/seed/prompts/scoring. Only two source files differ from preserved runtime1; old source/failure artifacts retained. No reseed, timestamp rewriting, old ledger/cap changes, enrollment, GPU launch, child signals, or sealed content disclosed. Parent-safe artifacts and revised API: `research_loop/workers/r159_matched_evaluation_20260917/runtime_generation2/` and `API.md`.

## [Builder] R159 candidate5 initial3 templates only — 2026-09-16 22:41:14 PDT / 2026-09-17 05:41:14 UTC

Verified local candidate5 INITIALIZED/common COMMIT/capacity/lifecycle hashes and exact recovered before/after; capacity PASS/VERIFIED, service exit0, zero initialization generation/updates. Cohort da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b; initialization05:31:49 UTC, saved state04:50:19 UTC. Original04:52:56 freeze unchanged. Archived candidate3 donor COMMIT hash f1fdb87d92e3e2efc401583faa02f2d6c5a8de07f5dcd20866215c8cb54a332c verified locally; no retired-root reads.

Prepared26 JSON metadata templates plus exact artifact/source-authority handoff and held copy/validate/dispatch commands in `research_loop/workers/r159_matched_evaluation_20260917/candidate5_initial3_templates/`. All JSON/three candidate shapes and four shell blocks' syntax checked locally; commands not run. Only three initial slots proposed (168 nominal calls if later admitted, within672/12), no new cap. Pending fields remain explicitly invalid/unknown: actual born-arm initial COMMIT hashes, trusted complete birth/TRAIN/eval histories and timestamp custody, source-reader authority/read ceiling, and Main node2 config/GO. Run GOs05:34:43 are not birth/copy/evaluator authority. No copies, input installation, enrollments, GPU launches, parent/child signals, or sealed data exposure. Runtime-generation2/helper/plan unchanged.
