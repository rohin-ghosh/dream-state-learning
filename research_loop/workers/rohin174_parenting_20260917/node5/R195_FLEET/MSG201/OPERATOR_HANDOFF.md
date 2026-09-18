# MATH-B: source report and sole operator entrypoint

Authoritative arm specification:
`research_notes/analysis/R201_C2_CLONE_ARMS_2026-09-17.md`, plus Rohin's exact
instruction naming C3/node5/GPU3 and the conditional three-cycle withdrawal.
Uniform rollout is paused. No other learner is a retirement target.

## Entrypoint now available

From the repository root:

```sh
python3 -B research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201/math_b_operator.py status
```

After explicit Main READY **and actual receiving CPU/input readiness**, the
same transport entrypoint dispatches the source-bound existing-handoff adapter:

```sh
python3 -B research_loop/workers/rohin174_parenting_20260917/node5/R195_FLEET/MSG201/math_b_operator.py execute --ready <receiving-READY.json> --ready-sha256 <exact-SHA256>
```

This wrapper is not new custody machinery. It rechecks bound source/config/
CPU files and C3 identity, then calls the receiving R179/R181-derived
`rollout_operator.py execute --output <control> --seconds 1200`. The receiving
adapter must be completed/tested against Main's final bundle; **it is not yet
staged, and no receiving READY exists**. The wrapper refuses missing readiness
before opening an SSH dispatch. Historical C3/R181 READY is not accepted.

Reserved receiving control (not created):
`/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1`

New clone life root (not created):
`/localhome/local-rohing/orch_r201_math_b_node5_20260918_attempt1/life`

## Final receiving binding still required

Retain the existing READY fields `operator`, `plan`, `config`,
`source_manifest`, `cpu` as path/SHA256 references and status
`ACTUAL_SOURCE_CPU_READY_NOT_STOPPED`. Bind `main_ready` to Main's local exact
READY artifact. Add arm `MATH-B`, `retire_root` C3's original life,
`retire_pid=2668022`, `retire_start_ticks=22198740`, the canonical snapshot
manifest/console hashes in `SOURCE_SNAPSHOT_REPORT.md`,
`parent_style=B_OWN_OBJECT_WALKTHROUGH`, `guided_complete_cycles=3`,
`conditional_parent_withdrawn_complete_cycles=3`,
`live_inbox_replication=false`, `publish_new_Rohin_messages=false`.

The receiving CPU proof must retain status PASS/no CUDA initialization and
prove `optimizer_restored_exact`, `console_masking_preserved`, LR3e-5, tool
root equal to the new MATH-B life, and the exact snapshot/console hashes.
Its source manifest uses the existing `source_root`/`source_files` bindings.

The receiving handoff adapter must preserve **C3's next complete state**,
original journal and all inbox bytes, adapter/optimizer/RNG, and exact owners;
use existing pidfd/watchdog/readout-drain/containment primitives. Never use
the old C2-specific partial-sleep R188 stop script. No source root, saved
checkpoint, actor, inbox or journal of C3 may be overwritten or reset.

Only after replacement closure, clone restore, tool bridge, parent-B launch,
provenance and CPU tests pass may that adapter retire C3's exact actors and
launch the new named root. Original C2 receives no signal, parent turn or
hold release. Source weights come from complete51/4908, **not** prose5840.
Use console commit5846 identically for every arm; do not copy the live inbox.

First screen: three actual complete clone cycles, new16/old0, LR3e-5,
unchanged anchor and retained source optimizer/RNG. Parent B demonstrates
evidence-to-revised-attempt on the child's own object. If safe to continue,
follow the predeclared next three complete cycles with that parent withdrawn;
do not turn this into an automatic restart/reset or new dose. Observe actual
LOADED and first real R184 stage; neither staging nor LAUNCH alone is success.

## Current result

Source snapshot and masked-console provenance are complete and hash-verified.
C3 remains live. Missing: Main's final tested closure and the actual receiving
clone/parent/tool integration and CPU proof. No replacement source or clone
was deployed, and no retirement/parent/GPU action was taken.
