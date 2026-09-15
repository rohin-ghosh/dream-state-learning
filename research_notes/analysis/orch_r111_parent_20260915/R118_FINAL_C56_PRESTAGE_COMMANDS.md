# Route final-c56 pre-stage owner handoff

September 15, 2026. Main owns campaign, coordinated CPU retirement/stage authority,
all-eight dispatch and Git. **No route stage or dispatch has occurred.** No extra
science gate is introduced. The frozen-initial-adapter wrapper remains Main's work.

## Exact prepared references

Wrapper: `gpu/ovx3_ssh.sh`. Candidate prefix:
`/localhome/local-rohing/orch_r118_route_parallel_candidate_20260915_v4`.
Actual imported coordinator is `source/gpu/orch_r118_parallel_consolidation.py`, SHA
`c56bb57b69405877a65124b623316f9b8bd769aa8f51db6f2481ff65325c5cdb`, verified identical
to Main's `/localhome/local-rohing/orch_r118_fresh_exec_cpu_20260915_v4/source/gpu/orch_r118_parallel_consolidation.py`.

| Reference under candidate | SHA256 |
|---|---|
| `source/SOURCE_HASHES.json` (168 files) | `921a7bcb7bf90017f05c7279dd18901eebbf11597e262b26e39e3e897bc86fb8` |
| `owners/F1/FRESH_OWNER_PREPARED.json` | `242fea3e81e011437cc2e60662cbb5a0f1464b7469e1e3521f944442f04ba857` |
| `owners/A1/FRESH_OWNER_PREPARED.json` | `efdd472c506a1051539dbe45a8a607355265fa37d1a22aca01ac87a7b423abb0` |
| `ROUTE_PARALLEL_READY_F1.json` | `72690064e3b6288e9e36c63afaa51580a68d5f6e25344ff8eb6ce271b91b5ae4` |
| `ROUTE_PARALLEL_READY_A1.json` | `fcbda883eff0c446d908515cdcb8183a9581d83f3fc91b987682253b324fa60f` |
| `CPU_RERUN.json` | `d7d9ea15fcb49ad3dca5b57d28ead5f98c9983949b6fc574b9d97aa49e3262a4` |

Native closure **215 passed +28 subtests in 59.59 seconds**. An initial legacy
pidfd fixture identity-test failure remains in `CPU.json`/`CPU.log`; unchanged
source passed the full rerun. No production GPU/provider inference in these tests.

Actual CLI `prepare-fresh-owner` produced both owners BEFORE stage. Their `command`,
`cwd`, `env`, `source_files`, inherited bounds and handoff refs can be read now by
Main's campaign/session preparation. Both owner contracts were checked by the
actual c56 validator; see `owners/{F1,A1}/VALIDATION.json`. Metadata explicitly says
`runtime_staged:false`; the command itself refuses launch until the real sidecar
PLAN, retirement receipts, broker bindings and coordinated session are present.
Do not mutate these pinned prepared owners after preparing a campaign/session.

Actual crash releases remain unchanged under the ORIGINAL roots:

| Branch | Root | `R118_POSTCOMMIT_CRASH_BOUNDARY_V1/RELEASED.json` SHA256 |
|---|---|---|
| F1 | `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1` | `3d9ecf85756cad3e89afb18dbaf358fd4c032ab10641f6c27bed368e8abfd805` |
| A1 | `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1` | `9209ca3207933a926759af8cb21ed3e1b485ca3f12dc44cdfb5312b1325e442b` |

F1 native425/parent68 → next new C8; A1 native202/parent36 → next new C5.
Missing DEV/OPEN is not retried or counted complete. Gen0 is already trained;
canonical gen1 remains `43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`.
Actual native bootstrap still must restore canonical LoRA/F1 AdamW/RNG before GO;
A1 has no optimizer and its new rank RNG is labelled new, not old-peer continuity.

## Main campaign inputs and exact stage commands

Build campaign `source_files` as the union of all eight prepared owners' **absolute**
`source_files`, plus the actual central c56 coordinator closure. Do not use the
relative keys from `SOURCE_HASHES.json` as absolute runtime pins. Main's final c56
`prepare_campaign` output reference must be included in route controls as:

```json
{"campaign":{"path":"ACTUAL_MAIN_CAMPAIGN_PATH","sha256":"ACTUAL_MAIN_CAMPAIGN_SHA256"}}
```

Those strings are placeholders, not claimed existing paths. Keep the other original
control fields: `anchor_root`, exact candidate-local `backend_source`,
`train_end_unix:1789491300`, `activation_wait_end_unix<=1789491300`, absolute
`activation_directory`. Campaign root/inbox/deadline/route source pins are verified
at stage and in the resident client. `stage` sets `requires_campaign:true`.

Within the remote shell reached through `gpu/ovx3_ssh.sh`, assign actual Main-issued
`MAIN_STAGE_F1_AUTH`, `MAIN_STAGE_A1_AUTH` and `PARALLEL_CONTROLS` paths first, then:

```sh
PY=/localhome/local-rohing/v2/venv/bin/python
CANDIDATE=/localhome/local-rohing/orch_r118_route_parallel_candidate_20260915_v4
F1=/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1
A1=/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$CANDIDATE/source"
"$PY" -B -m gpu.orch_r118_route_parallel_lifecycle stage --root "$F1" --release "$F1/R118_POSTCOMMIT_CRASH_BOUNDARY_V1/RELEASED.json" --readiness "$CANDIDATE/ROUTE_PARALLEL_READY_F1.json" --authorization "$MAIN_STAGE_F1_AUTH" --controls "$PARALLEL_CONTROLS"
"$PY" -B -m gpu.orch_r118_route_parallel_lifecycle stage --root "$A1" --release "$A1/R118_POSTCOMMIT_CRASH_BOUNDARY_V1/RELEASED.json" --readiness "$CANDIDATE/ROUTE_PARALLEL_READY_A1.json" --authorization "$MAIN_STAGE_A1_AUTH" --controls "$PARALLEL_CONTROLS"
```

Stage authority requires exact readiness/release/checkpoint hashes and true
`authorized`, `all_eight_released`, `common_handoff_coordinated`,
`lifecycle_rebinding_authorized`. For strict launch also bind the actual
`old_CPU_lifecycle_retirement` receipt; the roles are `cutoff_monitor`, `cutoff_fuse`,
`F1_FINAL`, `A1_FINAL`. Main's selector is not retired. Old PLAN and raw stay intact.

Main's dispatcher then uses each prepared owner's already-exported strict command:

```sh
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r118_route_parallel_run launch --root /localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r118_route_parallel_run launch --root /localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1
```

These are **dispatcher argv documentation**, not standalone activation authority.
Use owner cwd/env and Main-issued fresh-session environment. The launch performs
fresh privileged UUID/minor/process admission, starts new identities and checks the
actual broker binding to `R118_PARALLEL_PLAN.json`/`R118_PARALLEL_TERMINAL.json`.
Hubble F1 and A1 broker must bind those actual paths and retain parent wait120.
FINAL/cutoff/new-guard binding commands remain in `R118_ROUTE_PARALLEL_RUNTIME_V1.md`,
but use V4 source, actual new identities and the unchanged canonical selector.

## Actual resident callbacks and preservation

`Session.bootstrap` invokes final c56 `bootstrap_fresh_actor`, then
`wait_fresh_collection_go` before new TRAIN. Route branches have no pending gen1
submission to replay. At each actual two-episode boundary, route now calls c56
`await_campaign_activation` with its actual certificate: this publishes SAFE and
waits for Main's bounded campaign autoarm, then invokes c56 `launch_at_boundary`.
It does not merely poll an activation inbox without publishing readiness.

V3 and its unused ffdbe closure are retained as historical evidence, not patched.
`SOURCE_UPGRADE.json` binds old and new hashes. Original counters/caps, common
TRAIN16:55, hard17:02, lease margin, separate FINAL17:00–17:20 and parentwait120
are unchanged. No release/retirement/CONFIG/selector/Git mutation was done here.
