# Canonical FINAL selector armed

Observed September 15, 2026, 13:25:51 UTC through `gpu/ovx3_ssh.sh`.

- Native source: `/localhome/local-rohing/orch_r118_final_selector_source_20260915_v2`.
- Source SHA256: `64ccee2884b1dddafde70da8ccc2795127c8a4553fb6eb1a301484da369334ed`, verified before dispatch.
- Launch receipt: `/localhome/local-rohing/orch_r118_final_selector_20260915_attempt1/LAUNCH.json`; exclusive intent and log in the same directory.
- Timeout PID 1519258; Python PID 1519259; both observed after launch. Timeout process start ticks 1431188.
- CPU only (`CUDA_VISIBLE_DEVICES` empty), no sealed task reads, no model or provider calls, no actor signals.
- Runs `python3 -B -m gpu.orch_r118_final_selection wait` with the three lineage pins in CONTRACT.md and the source hash above. Outer timeout 15000 seconds.
- Main is the sole writer of the common `FINAL_SELECTION.json`. Selection is scheduled for 17:00 UTC, with evaluation bounded to 17:20 UTC or an earlier applicable lease margin. Arming is not completed selection or completed evaluation.
- Each family must independently establish predecessor release and absence of a partial/completed morning FINAL before evaluation. The route cutoff does not release math, code, or grid actors.

## Training and visibility snapshot

At 13:26:30 UTC, the first pooled sleep had 484 recorded updates, 84,779 child-token exposures and 8,988 anchor-token exposures. COMPLETE was absent; shared STATE remained generation 0. These are uncommitted updates, not a released shared checkpoint or retained learning.

At approximately 13:27 UTC, six representative route/math/code artifacts were rehashed on-node and matched the published visibility audit. OPEN turns live in `OPEN_TRAIN_*.json` and `open_readouts/readout_*/OPEN.json`, not files named `open_turn*`. Full generated continuations are retained. See `research_notes/analysis/R118_ROUTE_VISIBILITY_20260915_1136.md` for the historical checkpoint distribution and limits; do not relabel all route readouts as rich or all as protocol-only.

The CPU-only blind DEV judge had 12 finished dispositions: 10 COMPLETE and 2 UNRESOLVED. These are annotation completion statuses, not evidence of behavioural improvement. No FINAL data was read.

## Publication validation

Main reran the 16 selector and 12 CPU-judge standard-library tests successfully. The L1 feed/status standard-library suites contributed 13 passing tests. A combined attempt to import four other worker suites failed because this VM's system Python lacks pytest; those are not counted as local passes. Their independently recorded native CPU receipts remain the cited validation, with no package installation or live process change.

The L1 checkpoint-12260 receipt separately records ten new-target presentations (1,798 supervised tokens) in FULL and none in CONTROL; both restored optimizers advanced 128 steps from checkpoint 12132. This establishes actual feed consumption, not capability preservation or metacognitive improvement.
