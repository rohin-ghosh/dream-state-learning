# Recovery broker readiness — 2026-09-15 16:14:17.120062 UTC

Actual validation receipt (node-local):
`/localhome/local-rohing/orch_r118_claude_recovery_custody_20260915_1612_v1/READY_ALL_VALIDATED.json`
SHA256 `ffa2dbb3ae3c2bb9a1be1f0cc11e18fceaea6fb080ffbdbc812ec010cca73dcf`.

Campaign: `/localhome/local-rohing/orch_r118_main_startup_recovery_20260915_1610/CAMPAIGN.json`, SHA256 `7ea22b7fe4637ac344df140c7b56d49304091d067ec32d2558975ea1759e6610`.

| Branch | Actual PID | Ready SHA256 | Claims / publications |
|---|---:|---|---|
| F1 | 2594802 | a65e8c515ada6716d17c1b713d422c3de35653af903b06cefe9a7c8600ba44ad | 68 / 68 |
| F2 | 2722783 | 7f0af2d894b1e6540530ea3120d795f44e89fb912a15a6dd45197ff6bcda3386 | 60 / 60 |
| F3 | 2714738 | 00b9f4d5021a1c5fb82a2f23f367ee8f9b177bfa600f3c1ce1fed6c9c9bd78de | 100 / 100 |
| F4 | 2717390 | 773238b5afc434d1ccfb161fe64d4709f39042737a5fc80d07f451bf782035cd | 40 / 40 |

All live identities compared exactly with native `/proc` identity and PPID 1; original exclusive queue locks held. F1 actual frozen `validate_broker_binding` passes against new PLAN `c59f5037ec3f660a9aa54a21c0cc06ebc056aa574269c59470e35c4dcd846ae3`. F1 was not restarted: its old ready bytes were preserved and only PLAN/runtime/campaign/observed identity metadata was updated.

F2 ready path: `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4/lane1/BROKER_READY.json`.
F3 ready path: `/localhome/local-rohing/orch_r108_code_parent_r115_node5_2_20260915_attempt1/parallel_v4/service_3/BROKER_READY.json`.
F4 ready path: `/localhome/local-rohing/orch_r115_grid_pair_20260915/F4/parallel_recovery_1548/BROKER_READY.json`.
F1 retains its original-root `R118_PARALLEL_BROKER_BINDING.json` path.

Terminal-only wrapper retains pinned original broker/provider/config/prompt/claims/caps/deadlines. New F4 terminal is `R118_GRID_PARALLEL_RECOVERY_V1_TERMINAL.json`; F2/F3 use their new service-local `GUARD_TERMINAL.json`; F1 unchanged real writer. Historical terminal files and failed attempts remain untouched. No charged requests retried; publication counts are not COMPLETE or native-consumption counts. No new provider calls at validation observation. No GPU/judge activity or Git mutation.

Non-material regression repair: readiness publication waits for actual reparenting to PPID 1 and two equal identity reads. It fails without publishing ready if identity cannot settle. 8 local + 8 native focused tests passed; all successor actual configuration checks passed before launch. Native sources remain outside Git worktree.

Publication allowlist:
- `gpu/orch_r118_claude_recovery_rebind.py` SHA256 `105f9a607608e4880c8b5e76ef4988785407f853ec631b5921de7f9130de5eb5`
- `tests/test_orch_r118_claude_recovery_rebind.py` SHA256 `dbc1eb5aa781767bf90c053e9b6a655e403e824509a7d8b326e6e1ef037104f4`
- This compact receipt.

Unchanged dependency: `gpu/orch_r118_claude_terminal_rebind.py` SHA256 `985111d9e1c49ecdcf18deb82b6b19bdcdb6e5a05695b3372b79b5615a066635` and its existing focused tests. Main owns session/GPU dispatch and publication.
