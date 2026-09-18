# R158 benchmark continuation — parent-safe operational receipts

## Scope and frozen contract

September17, 2026 UTC / September16 PDT. Explicit user execution task: implement and actually launch a bounded append-only controller/copier after the prior03:54UTC wall. Own new `gpu/orch_r158_benchmark_continuation.py`, its tests and this worker directory; append only to COORDINATION. No scoring, corpus, decoder, base, enrollment, aggregate-call or phase-job cap changes. No child/generator/community-parent actions. Source reads only the three originally admitted checkpoint roots.

## Terminal custody and quotas before launch

- Old R146 phase normal COMPLETE:62 completed checkpoints,65 charged checkpoint keys, three historical explicit timeout failures preserved. Old copier normal COMPLETE after16 cycles. All66 audited old controller/scheduler/job identities are gone; old local copier3861062 is gone.
- Shared predecessor/R146 job accounting is53/58; **five phase-job slots** remain. Aggregate accounting is65×60/4800; **900 nominal calls** remain. Failed/ambiguous reservations remain charged. New/unknown reservation configs are refused, not treated as free quota; original seed keys and original pre-phase claims stay charged.
- Original node2 FORKS and benchmark reservation preserve the original lease-budget ceiling September21 08:43UTC and six-hour-margin inference cutoff September21 02:43UTC. No node5 authorization is substituted for node2, no booking or lease extension performed.
- Same run1/pilot roots verified against current owner R157 applied receipts, remote PLAN/LEASE hashes and live PID/start identities. Native COMMIT discovery verified unchanged initial hashes. Kernel uses its original root and already-pinned source-read ceiling September18 00:00UTC; no recovery-root inference or enrollment. Custody and source-selected checkpoint metadata are in `SOURCE_CUSTODY.json`; no optimizer/RNG/TRAIN content was opened by the copier.

## Implementation and validation

- The existing R146 scheduler and original benchmark/runner remain unchanged. New controller binds exact old terminal/config provenance, owns the existing successor lock, requires old identities gone, and launches the existing scheduler with its existing physical0/1 locks and privileged empty-device admission. Its new two-hour-or-shorter config keeps all non-wall/non-provenance scheduler fields equal to the exact prior segment.
- Both4800-call and58-job caps are checked against the shared ledger and the complete predecessor configuration inventory. New job claims remain in that ledger. No failed-key retry, budget reset, implicit phase-cap reset or competing controller is allowed.
- New local copier uses the established read-only native COMMIT/adapter exporter. Source-root and initial-COMMIT custody are exact; archives are content/hash validated and only adapter, COMMIT, manifest and copy proof can reach node2. READY publication uses the existing enrollment verifier. Known reserved/failed keys return `ALREADY_RESERVED_NO_REPLAY` without copying or dispatching.
- **433 CPU tests pass:**29 new continuation tests plus404 existing R146/original benchmark suites. Tests include full inherited scheduler validation, unchanged donor dependencies, source-root/archive integrity, failed-key no-replay, shared budget accounting, predecessor ownership, custody expiry, remote binding and local-only copier import isolation. No dependencies installed; existing `/tmp/r136-pytest-support` used. Source whitespace checks pass.
- Generation1 was **never launched**: remote preflight refused importing the local-only copier, which is absent from the frozen donor. Its source/configs remain preserved. Generation2 lazy-loads that backend only for local copy actions; a regression explicitly denies it during node import. Every1091 donor Python file remains byte-identical; only the owned helper and test are added (1093 total). No native dependency was replaced to match workspace drift.
- Generation2 real node preflight and local copy validation both PASS. Full config/source/CPU/Builder provenance is bound. Dated pre-launch Builder gate is appended to shared COORDINATION at04:17UTC.

## Actual launch, not just preparation

At **04:17:39 UTC / September16 21:17:39 PDT**, actual controller **1688939/start84709817**, inherited scheduler **1688949/start84709839**, and local copier **3142862/start172567713** launched. Identity/command/boot bindings subsequently matched. The125 pinned historical metadata files still hash unchanged. Receipts: `generation2/CONTROLLER_LAUNCH.json`, `COPIER_LAUNCH.json`, `ALIVE_METADATA.json`.

- New source: `/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1/source_r158_20260917t0416z`.
- Phase: `/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1/CONTINUATION_R158_20260917T0416Z.json`, SHA256 `657c8b797c59b2cee21927cd8d010f87237ec8626b16e32b053ff9d6f9c66127`.
- Scheduler config SHA256 `fb9281e6a0c90f26b2ef30c1a4ba2215e419b0029e87b0cfa794e97b96bc8a0e`; local actual `generation2/COPY_CONFIG_OWNED_LOCK.json` SHA256 `3509392a3054104d1aa70ab9e0b288c2ccb8e2d99c55eeff3d015cbdf5a05c74`.
- Fixed first copy04:27UTC, first dispatch04:30UTC; unchanged proposed hardwall05:54UTC. The04:00 slot was already past when this execution task resumed. The05:00 slot cannot fit the existing >3615s job-window requirement, so this generation can admit at most two jobs at its single eligible tick even though five shared phase slots remain. Earlier completion/idle exit is permitted by the existing scheduler.
- The latest startup observation still has62 completed, zero new admissions and no active GPU jobs. This section does **not** claim the future copy/dispatch or a new completion; metadata verification follows.

## APIs and visibility

Remote `validate`, `node`, `status`, `known`, `stage` require `R158_ADMISSION_SHA256` bound to the exact phase JSON. Local `copy-validate`, `copy` require `R158_COPY_ADMISSION_SHA256` bound to the exact copier JSON. Both use `--config`; known/stage accept bounded item-free `--payload`. All failures return only an error type and bounded identifier, never private exception bodies. No existing module was monkeypatched or gate bypassed.

Parent-facing evidence is counts, identities, paths, hashes and terminal status only. Inference outputs stay under the original private benchmark architecture. No private report, scores, held prompts/keys or model responses were exposed. New launch/copy records and historical staging failures are preserved; no commit/push.

## [Builder] R158 actual copy/dispatch/completion receipt — 2026-09-16 21:37:57 PDT (2026-09-17 04:37:57 UTC)

Metadata-only terminal verification, not startup-only: the 04:27:23 UTC copier cycle completed with all three original lineages (legacy, pilot, kernel) COPIED_AND_READY_VERIFIED. At 04:30:28/29 UTC the inherited scheduler admitted kernel on node2 GPU0 and legacy on GPU1. Both actually completed with exit0: kernel 04:35:06 UTC, legacy 04:35:41 UTC. Each ledger COMPLETE matches its claim/native-completion hashes; each has60 RAW filenames counted without reading contents. Scheduler BOUNDED_SCHEDULER_FINISHED at04:35:46 UTC; controller BOUNDED_PHASE_FINISHED at04:36:13 UTC. Fresh boot/start-tick checks show both job identities and controller1688939/scheduler1688949 gone. Terminal scheduler metadata has no active physical GPUs; the older phase polling row is stale.

Totals: **64 completed checkpoints (62+2, includes six seeds);67 charged checkpoint keys;55/58 shared phase jobs charged,3 remaining;4020/4800 nominal aggregate calls charged,780 remaining.** Exactly two new admissions, zero new failed attempts. Three historical failed reservations remain charged and unreplayed;125 pinned historical metadata files rehashed unchanged. Pilot remains one READY pending checkpoint. No next dispatch:05:00 cannot meet the unchanged >3615-second full-job-window requirement before this generation's05:54 UTC hardwall. Remaining quota is not authority for another launch.

Evidence: `research_loop/workers/r158_benchmark_continuation_20260917/generation2/ACTUAL_COMPLETIONS_METADATA.json`, `TERMINAL_METADATA.json`, and `copy_output/COMPLETE.json`. Remote phase COMPLETE SHA256 `41b6edb4f1aed1b338251489d8844935a54d34185fca471bdeec474337ca84bf`; scheduler COMPLETE SHA256 `ec8389f42b541df8aed2c96c041db39d5d130ecf34eb3a375259a5ed43031146`. Existing CPU receipt confirms433 passing tests; helper/test hashes remain frozen. No benchmark/scoring, enrolled source, cap, ledger ownership or child changes. No sealed prompts, keys, scores, responses or private report contents read/exposed. These are operational completion counts, not capability claims. Node4 matched-triplet candidate2 is a separate provenance source/campaign: no enrollment or implementation authorized or performed here.
