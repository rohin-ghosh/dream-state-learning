# R159 interval repair — September17 06:15 UTC / September16 23:15 PDT

Non-material custody repair authorized by Main. `OBSERVED_INTERVAL` keeps the existing event schema/common cohort, arm, kind, complete-coverage and common-observation bindings, and substitutes `first_earliest_unix`, `first_latest_unix`, `source_evidence` for `first_unix`. Bounds must be finite non-boolean numbers and satisfy **original freeze < earliest <= latest <= observed**. Evidence is1–16 unique exact SHA256/path refs to regular non-symlink metadata files under campaign inputs, checked at validation and throughout evaluation. Existing exact OBSERVED/NOT_OCCURRED rules are unchanged; every arm still needs birth/TRAIN/evaluation. Missing/changed witnesses, equal/crossing freeze, inverted/future/nonfinite bounds, mixed schemas and incomplete coverage fail closed.

**Tests:**383 local CPU tests PASS (140 R159 +243 inherited); seven receiving stdlib synthetic interval tests PASS, including all9 arm/kind intervals. Actual receiving installed-gym28-task regeneration/parser/native-verifier smoke PASS, zero model calls/enrollments; private verifier outputs remain sealed. No dependencies installed. Separate observation/copy utilities pass10/5 tests. Actual copied candidate CPU checks pass3/3; concrete config fields/hashes pass3/3. Full `validate --go` deliberately not run without Main's exact GPU execution GO.

| Artifact | SHA256 |
| --- | --- |
| helper | `100e952409e9e76eb143db2d8f5a504ea8120593e52f85b56f19b07fd7d0bafc` |
| tests | `0efecc73582389a8c5eb5de32a69efa9aadd7420e499f6d1d6ea79113cc6fec9` |
| runtime3 SOURCE_MANIFEST | `9a85e4cda65a517c779baea2dc393390936b90f199fe31947dab65c16fe45fa3` |
| runtime3 CPU_GATE | `7028f84e33e91dbe6fcda183e858ea728a3e9b290220687b1b00439b9813a9a9` |
| original PLAN unchanged | `c2f32b5390f4d9a06ab30de1cd64eb91858055ca4944c6328edbad52125fed86` |
| original04:52:56.060556 UTC FREEZE unchanged | `1515341fd0c8d1336cbea6728aa5ba3c27c638752964575affda2400002c81b6` |

Receiving source `/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation/runtime_generation3/source`. Only evaluator/helper test files differ from preserved runtime2; every old source-manifest entry and original plan/freeze reverified unchanged before/after staging. No task selection, seed, prompt, scoring, model, claim, visibility,12-slot/672-call or old4800-call/58-job cap change.

## Node2 point-in-time readiness

At06:04:36 UTC exact host `[REDACTED_HOST]`, physical0/1 privileged scans clear, no blocking reasons; existing lock-file inode entries absent from `/proc/locks`, no locks acquired/changed. Refreshed privileged scans at06:14:04 UTC both still clear. Old R158 controller identity PID1688939/start84709817/boot8ff7b0dc-fbdf-4945-9044-3dffe94b5407 is gone; terminal SHA41b6edb4f1aed1b338251489d8844935a54d34185fca471bdeec474337ca84bf is BOUNDED_PHASE_FINISHED. Terminal metadata retains64 completed/67 reserved,55 phase jobs charged,3 jobs/780 calls remaining; no old ledger writes or retries.

Existing scheduler-bound lease ends **September21 08:43 UTC**, not a new lease purchase or extension. Proposed September17 **08:00 UTC** hardwall/read ceiling satisfies its six-hour margin. Every dispatch must start strictly before **06:59:45 UTC**, preserving3600+15 seconds. Initial learning0/frozen1 may run concurrently only after GO; unparented0 waits for learning0's verified release and still needs a full remaining window. Three worst-case windows are not guaranteed now: if release is too late, the third stays unreserved; do not extend wall, drop controls by score, or increase budget.

Interpreter `/localhome/local-rohing/v2/venv/bin/python` SHAa92f0f95e883390c7256b2e441484aac06b1002dbe1d924141a77c8d82f96223; existing service identity SHA26b16432e913ea03e6c2ae41977c60885d00ad601a6bf8d097b8a6e57734cbcc verified current. Model directory is the existing Qwen2.5-7B-Instruct cache snapshot, no model loaded. Fresh locks/admission remain mandatory at actual execution.

## Current disposition

Main's separate source/copy authority now permits the witnessed metadata and exact adapter-only copies; these completed with hash joins in `../initial3_generation1/MAIN_HANDOFF.md`. That authority explicitly does **not** grant node2 GPU execution. Ledger remains0/12 reserved,0/672 charged; no evaluation launch, parent/child/service action, optimizer/RNG payload read, held readout content or scientific gain claim.
