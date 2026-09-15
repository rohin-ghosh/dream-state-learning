# Actual attempt5 stage and CPU preflight PASS — 2026-09-15 16:33 UTC

Campaign `/localhome/local-rohing/orch_r118_main_final_startup_20260915_1630/CAMPAIGN.json` SHA256 `fb9bd9419d7621684ea41f93778ebb5c83de6076e46993a68d2a83189f62cab0`.

Service prefix `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt5`:

| Branch | Final owner | SHA256 |
|---|---|---|
| F2 | lane1/FRESH_OWNER.json | 128b1e0e477630d9f532f468377ea3a9292e9f238e957a692f53bd80bde1d52c |
| A2 | lane5/FRESH_OWNER.json | 3ff5a92739cc0272961cba549c1eb8975e6f38dd76bb9a457d6fd0d38c79a4e6 |

Actual F2 broker2843647 (Hubble/node5), BROKER_READY SHA256 `4be31879889de2037ce143de392eccf496192ea1c3c0cc5cedf74326c0229b55`. Actual A2 broker2808906 (VM), BROKER_READY SHA256 `d5098124c421145eeb31f04bb85d7f6f39ed3959a925f46389235e0f526addcd`. Both actual original queue locks acquired and receipts bound to attempt5 RUNTIME and GUARD_TERMINAL. A2 eight CPU broker regression tests PASS in copied immutable legacy runtime; only prospective service mapping changes. Existing config/GO/HTTP slots/claims/budgets/prompt root unchanged. New A2 wrapper SHA256 `19ee5f59b98948a1fd4e8533c5dcc4711c626a2b54a9fc51057213dfdb697938`, binding SHA256 `d467725074dcafcadfa4f11db9d40a374a40cc1d223cdbdc04f2df46f49853ed`; files and launch metadata under `/tmp/orch_math_feedback_uptake_r118_preinfer_broker_source_20260915_attempt5/ATTEMPT5_*`. Historical cloned metadata retains old names and is not the new launch record.

CPU stage receipt `/localhome/local-rohing/orch_math_feedback_uptake_r118_stage_cpu_20260915_1631/STAGED.json` SHA256 `cc186c1c8ff8e0d658920b38b4d124599816823c6c41cdc0429d1f2c56e25afe`. Four authentic old cutoff/FINAL timers retired only under actual new scoped authorization using existing tested exact-identity/reparent helper. Selector1519259 preserved unchanged. No GPU source map mutation;188 math source pins remain frozen.

Exact CPU preflight **already PASS**, no admission scans or model/provider calls:

```sh
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B /localhome/local-rohing/orch_math_feedback_uptake_r118_stage_cpu_20260915_1631/PREFLIGHT.py
```

Verified staged owners/campaign closure, release/preserved files, counters274/60 and170/36, next11/7, actual broker/runtime/terminal/queue locks, selector unchanged. Guards not started at preflight. Main alone dispatches; do not rerun stage. CPU startup authorization expires16:35; original TRAIN16:55/native16:59/hard17:02 and FINAL unchanged.

Publication additions: this file, STAGED_1632.json, F2_BROKER_READY_1633.json, A2_BROKER_READY_1633.json in this directory, and scoped journal/COORD entries. No raw VM evidence or Git mutation.
