# Actual route recovery final owners — 2026-09-15 16:14 UTC

Both branches are CPU-staged against Main's actual new campaign:
`/localhome/local-rohing/orch_r118_main_startup_recovery_20260915_1610/CAMPAIGN.json`,
SHA256 `7ea22b7fe4637ac344df140c7b56d49304091d067ec32d2558975ea1759e6610`.
Both final broker identities passed the unchanged native validator. Both explicit
`--verify-only` commands and final-owner exports passed. **No GPU dispatch.**

## Final owner references

- F1 `/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v2/stage_1609/F1/FRESH_OWNER_FINAL.json`, SHA256 `7af096a51057e343a5e88d735e8e8c0dfc0d7287aa1d1c8aeaae9eaf5d3882e1`.
- A1 `/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v2/stage_1609/A1/FRESH_OWNER_FINAL.json`, SHA256 `de533ae3610cbed7a82b2c85477484e0d1a09353dcd316c4514541f4fa9ee016`.

Main uses these exact final documents, not the previous prepared owner documents,
for its new all-eight session. Source files remain the same prepared union:
unchanged scientific c56 plus recovery wrapper c6e8e9b0. CPU launcher CVD is empty;
only the supervisor receives its original UUID after a new strict CLEAR scan.
No collection before actual all-eight GO. No reused e834ff dispatch.

## Checked CPU-only preflight commands

These exact commands succeeded and are recorded in native
`/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v2/stage_1609/PREFLIGHT_CHECKED_1614.json`,
SHA256 `11a09abf438e802f98abcedee4b0ac79f9fcb78f3f4fcce2ff49b997eebbf313`.
The byte-identical local compact is `FINAL_RECOVERY_PREFLIGHT_1614.json`.

```sh
bash gpu/ovx3_ssh.sh 'set -eu
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1
PY=/localhome/local-rohing/v2/venv/bin/python
RUN=/localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2/source/gpu/orch_r118_route_startup_recovery.py
OUT=/localhome/local-rohing/orch_r118_route_recovery_binder_20260915_v2/stage_1609
"$PY" -B "$RUN" --request "$OUT/F1/REQUEST_FINAL.json" --request-sha256 166a00c3f7bb8c71973afd4e6a772694cd1627ac26167da9499f88d1ee2880d6 --verify-only
"$PY" -B "$RUN" --request "$OUT/A1/REQUEST_FINAL.json" --request-sha256 e26356f8f1e82f5233d04099e1c2b85ff681d273531124fb95d3b7639b09c0ae --verify-only
'
```

Do not remove `--verify-only` for a manual launch. Only Main's coordinated new
session may dispatch the exact owner commands. Request expiry is16:25 UTC;
TRAIN16:55, hard17:02, original call caps and FINAL allocation remain unchanged.
The new single-use recovery namespace remains `R118_STARTUP_RECOVERY_1552` in
each original root. Old attempts, scans, PLANs, prepared requests and failures
are preserved; missing old DEV/OPEN are not relabeled successful or replayed.

## Actual broker custody

F1: Hubble-owned broker2594802, binding SHA256
`a65e8c515ada6716d17c1b713d422c3de35653af903b06cefe9a7c8600ba44ad`,
new PLAN SHA256 `c59f5037ec3f660a9aa54a21c0cc06ebc056aa574269c59470e35c4dcd846ae3`.

A1: new native custodian2713164 starts only after parent reparenting settles to1;
actual VM HTTP worker2681535 retains the original provider/config/four HTTP
slots/queue/wait120. This is explicitly VM provider + node custodian, not a
claim of provider inference on the node. Binding SHA256
`ff8b6d0e4aa2c8ffbeda9d0f902652b24866bcf812095967b5f251e79406180e`,
new PLAN SHA256 `1088e1c86202c2c5305167b9378d73bd8f4fa4c43aa8bb72f0afa650f43322d0`.
Custody root `/localhome/local-rohing/orch_r118_route_astra_custody_20260915_1611`;
`READY_VALIDATED.json` SHA256 `e16c9a37e53f395e2301a161d30e2e510e805f24b9011b12961b0dc5b7e835c4`.

A1 prior worker2488913 had exited with `custody_heartbeat_failed_no_new_dispatch`;
prior custodian2563918 exited with `PLAN_unchanged` after authorized new PLAN
binding. Both failures remain preserved. No process signal or claim retry was
needed. The old empty queue lock was already absent; no live lock was removed.
Inventory-only preparation errors (claim directory treated as file, then absent
old lock) were preserved before corrected read-only inventory; no provider call
or raw deletion occurred. All36 old requests/responses/PUBLISHED claim records
retain their hashes:23 COMPLETE,3 SILENT,10 MISSING. No new request was fabricated.

Native wrapper source remains unchanged e1eda0d8; prior12 local/12 native tests
remain its source-bound tests. New binder11 and recovery14 native tests passed.
No selector1519259 access, CONFIG/shared-state/optimizer changes, raw VM pulls
or Git mutations. Final actor-dependent cutoff/FINAL bindings still require
actual identities after Main's dispatch; these are not invented at CPU stage.
