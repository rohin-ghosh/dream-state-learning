# Chandra: probe queue and one-shot plumbing — 2026-09-17 16:27 PDT

No node2 slot is released to probes by this note. Do not compete with a native
or its synchronous generic32 readout. Ampere will reserve each eligible freed
slot for Chandra after native EXIT plus a fresh clear/device census.

| GPU | current copy | release condition |
| --- | --- | --- |
| 0 | R186 P4, `.../orch_r153_r186_c2_plasticity_20260917/p42` | max_sleeps44 terminal + native/service exit + target clear |
| 1 | R186 P32, same base `/p322` | same; still training |
| 5 | R186 LR.3, same base `/lr032` | same; still training |
| 6 | R186 LR3, same base `/lr33` | same; newly dispatched |
| 3 | R184 explicit1 | STILL LIVE; max_sleeps is null, outer7200s; not released at saved44 |
| 4 | R184 brief1 | STILL LIVE; max_sleeps is null, outer7200s; not released at saved44 |

GPU2 repo learner and GPU7 reserve are excluded. Do not assume current baseline
3/4 end merely because saved42/43/44 exists. Source/native changes or early stops
of these frozen baselines have not been authorized by this handoff.

## Safe reuse interface

Frozen generic32 module is unchanged in every source:
`gpu/orch_r125_continual_readout.py`, `run(plan_path, checkpoint_path, output_path)`;
CLI `python -B -m gpu.orch_r125_continual_readout --plan PLAN --checkpoint COMMIT --output OUT`.
This module is NOT your new object/procedure/attention probe; retain it unchanged
and stage your own new evaluator module/source/output with its23-test receipt.

Existing containment plumbing is frozen `gpu/r184_node2_confinement.py` in the
selected copy's source. `command(config_path,mode)` builds root-owned systemd
service with nonroot2524, empty capabilities, NoNewPrivileges, strict single
GPU device allowlist, CPU target-open/seven-foreign-denial proof, fresh privileged
scan, bounded RuntimeMaxSec and private raw-to-logical-root bind mount.
Its current `child` branch launches TRAINING: do NOT invoke it unmodified for
a probe. In your NEW source bind a dedicated one-shot probe entrypoint after
the same `verify(unit)`, keeping device and lease policy unchanged. Never reuse
consumed DISPATCH_ONCE/OUTER_STARTED latches or modify existing source/control.

Readout input must bind exact source/PLAN SHA and completed COMMIT (adapter and
optimizer/RNG file hashes), admitted UUID, `R125_ADMISSION_PLAN_SHA256`, and
source-read-only before/after identity. A new output must not preexist. The
existing wrapper intentionally refuses implicit readout replay. Do not call
`fresh_readout(child,...)` in an already running parent/learner.

Host-visible saved artifacts are under `<copy>/raw/checkpoints/sleep_000042`,
`sleep_000043`, `sleep_000044`; use only actually COMPLETE snapshots. COMMIT
paths remain the original logical C2root. A private bind of `<copy>/raw` to
`/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life` is needed
inside the new probe service; do not rewrite raw prefixes/COMMIT paths or bind
one copy over another globally. Standalone output is evaluator-owned, not
parent/learner feedback. No probe labels, answers or outcomes to Main.

The older roots without `r153` are stopped tool-blocked attempts; do not select
their checkpoints as successful R186 treatments. LR3 `/lr32` was pre-native
admission failure and has no newly trained checkpoint. Use current paths above.
