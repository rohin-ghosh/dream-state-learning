# Bacon: exact successful explicit1 interface — 2026-09-17

Read-only handoff. Bacon owns all node5 rollback/execution. Ampere makes no node5
mutation and does not replay or publish the pending Rohin intervention.

## Successful frozen source

- Local payload `R184_EXPLICIT.tar.gz`; local source `r184_explicit_source/`;
  local pin file `R184_EXPLICIT_SOURCE.json` SHA256
  `720833444e7b045c3e3b059d89dac469764c24106725f2f8ba5040d92120b773`.
- Node2 `/localhome/local-rohing/orch_r153_r184_node2_20260917/explicit1/source`;
  sibling `SOURCE.json`, `control/PLAN.json`, `control/GUARD.json`, `BRIDGE.json`.
- Plan SHA256 `3887bb900ea1c8f27325fcd8537a080eaff7d5e591407c9b2aef647583907448`;
  guard SHA256 `81b2fc8a5e27a335f38176ac8946dc355ea96af6945f8e17e0ce3bd078de0beb`.
- All134 Python hashes still identical at16:06PDT. `r184_build.py` documents the
  narrow early-dispatch and external-CPU adapters; DO NOT rerun its build over
  existing sources. `r184_receive.py` documents exact saved41 initialization,
  but is node2-specific and AUTO-DISPATCHES; do not run it unmodified on node5.

## Saved state / initialization

Packet `/localhome/local-rohing/orch_r184_C2_sleep41_1789684294308387719` originated
on node5 and is already staged on node2 beneath
`/localhome/local-rohing/orch_r153_r184_staging_20260917/`.
Preservation receipt SHA256
`cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e`.
Exactly records0..5128, saved41, optimizer4428, completed frontier and no pending
operation; adapter `9203c472ed7ff1c1609fe2be0a619c7190cf90e73b4a80826aeaf0ae5414fd59`,
optimizer/RNG `6ea6fa9ffdfe806308293f1e08749b6cfea08f1bf1cae07f6a86608af1db80df`.
Never substitute current live explicit1/raw (now beyond41) for the frozen packet.

Each copy adds empty `stream/WRITER.lock` and `stream/inbox`, copying ONLY the
historical inbox files already registered in the saved prefix with recorded
hashes. New pending human input must be handled separately by Bacon, once.
Original logical root must remain
`/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life` to keep
raw-prefix absolute INBOX path bindings valid. Node2 uses private systemd
`BindPaths=<copy>/raw:<logical-root>`. On original node5, Bacon must preserve
the superseded42 artifacts first and manage the original-root mapping himself.

## Stage and CPU bridge

Plan `think_act_learn` keys: schema `R184_THINK_ACT_LEARN_V1`, unique `trial_id`,
`reflection_policy=explicit`, `think_segments=1`, actual node-local `cpu_gate_root`
and matching `cpu_gate_sha256`; `rehearsal_presentations=0`, `new_presentations=16`.
Frozen native dispatches R184 before historical readout catchup. LR remains3e-5;
no R186 treatment is implied for the original life. No complete-episode encoder.

Frozen `gpu/r184_cpu_bridge.py` command:
`PYTHONPATH=<source> <venv-python> -B -m gpu.r184_cpu_bridge --config <base>/BRIDGE.json`.
Launch this CPU-only outside the strict GPU service. JSON keys:
`raw_root`, `journal_id`, unique0600 UNIX `socket`, `gate_root`, `gate_sha256`,
`stop_unix`. Native `_cpu` reads `<source-parent>/BRIDGE.json` and sends only
`{kind: TRAIN_CHILD_RESPONSE, record_index, record_sha256}` with index>=5129.
It performs origin-bound `cpu_once(...,start=True)`, strips result text and returns
publication/status metadata, with no automatic retries.

Node2's gate is `/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2242z/gate`,
SHA256 `5241727deccc099cdf93d6bde213d44df2ae52ba4b6b73103d10abbb5bfc0a89`.
It is node/boot-bound: NOT a portable approval for node5. Retain Bacon's actually
valid node5 gate/profile. Likewise frozen `gpu/r184_node2_confinement.py` is
hard-bound to node2GPU3 and cannot be used unchanged for node5GPU identity.

Successful dispatch has separate external bridge + strict supervisor, then
`LOADED`, new THINK/ACT/LEARN records. Explicit1 actual ACT COMPLETE is record5139,
followed by LEARN revision1 and actual sleep updates. No replay of old CPU calls.
Do not duplicate an external parent: existing inherited parent TRAIN history and
actual new human message handling are distinct from spawning another parent.
