# Route coordinated stage scope — September 15, 2026

Status: requirements prepared; no authorization issued by this worker, no stage,
retirement, new GPU actor, broker launch or FINAL waiter launch performed.
Selector **1519259 is excluded from every retirement scope and was not inspected**.
The existing Main-owned selector and canonical selection bytes remain untouched.

Exact per-branch values and fresh read-only CPU identities are in
`STAGE_AUTH_REQUIREMENTS_1527.json`; its top-level `authorized:false` makes it
requirements evidence, not a usable authorization. Native reference:
`/localhome/local-rohing/orch_r118_route_parallel_candidate_20260915_v4/STAGE_REQUIREMENTS_1526.json`,
SHA `0877a96be42067140af62850fcf30508fd153019d88ec5c4a88f2c932adbcda2`.

## Main-issued stage authorization

Issue one immutable authorization per branch with these actual required fields:

- `authorized:true`, `all_eight_released:true`, `common_handoff_coordinated:true`,
  `lifecycle_rebinding_authorized:true`.
- `readiness_sha256`, `release_sha256`: exact F1/A1 values in the requirements file.
- `checkpoint_sha256:43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`.
- `old_CPU_lifecycle_retirement:{path,sha256}`: the actual immutable retirement
  receipt, required before strict dispatch and FINAL rebinding. It must report
  `status:RETIRED_FOR_COORDINATED_SUCCESSOR` and an `identities` object with exactly
  `cutoff_monitor`, `cutoff_fuse`, `F1_FINAL`, `A1_FINAL`; all must actually be exited.

The scope is F1 physical0 and A1 physical4 only, staging and their lifecycle/broker/
FINAL CPU binding, preserving old PLAN/raw/counters. Standalone GPU startup is not
authorized: only Main's coordinated all-eight dispatcher may use the exported
owner commands. Never broaden the retirement receipt to the selector or peers.

Controls must provide the actual Main campaign reference, matching its absolute
activation directory and source-file union; exact candidate-local c56 backend ref;
the original shared anchor root; TRAIN end1789491300 (16:55 UTC), and an activation
wait end no later than that. The stage CLI validates these fields; command lines
are already frozen in `R118_FINAL_C56_PRESTAGE_COMMANDS.md`.

## Actual lifecycle order, no fabricated IDs

1. Main supplies actual campaign/control and coordinated stage/retirement refs.
   Verify hashes, canonical state, original charges and dead predecessor receipts.
2. Stage each `R118_PARALLEL_PLAN.json`, preserving original `PLAN.json`. Export
   the final owner to a **new** output directory. Keep the campaign-pinned prepared
   owner files unchanged; command/cwd/env/source files and handoff bounds must agree.
3. Bind each actual broker to the new PLAN hash and
   `R118_PARALLEL_TERMINAL.json` real writer. Publish only after an actual matching
   broker identity is available; keep provider and parent wait120 unchanged.
4. Main dispatches the owners with actual fresh-session environment and strict
   privileged UUID/minor/process admission. This worker does not call standalone
   GPU launch. New actor/guard IDs come from real runtime receipts.
5. Using those real actor/guard IDs and all-eight actual era bindings, prepare the
   new route cutoff control, then FINAL configs/waiters and supervision evidence.
   `rebind-cutoff` reads `R118_PARALLEL_ACTOR_READY.json`; `rebind-final` requires
   that exact control. Those final identity bindings cannot truthfully be completed
   before Main dispatch. This dependency is not another science approval gate.

The built-in successor guard remains responsible for its inherited hard window
while external cutoff/FINAL identity binding is completed. Its successful launch
does not claim that an external FINAL timer already exists. Missing readouts stay
missing, gen0 is never replayed, and native canonical restoration precedes collection.

## Read-only observation at 15:27 UTC

- Old cutoff monitor1271059 and fuse1271060: recorded identities absent.
- F1 FINAL1496784 and A1 FINAL1496788: exact old CPU waiter script/config identities
  present, empty CUDA visibility; no signals sent. These are not selector1519259.
- No new route sidecar PLAN exists. F1 N425/P68 nextC8, A1 N202/P36 nextC5 unchanged.
- Existing final source SHA `dbe2cf05b614ab374964249324c02d5e19f8b8bc29684fe5da398be505d9c618`
  matches the frozen candidate copy and existing final CPU receipt
  `31844080634a415301999a2695e84064d65d1ea6baf9c520aca32398ae730bdc`.
  Final evaluation remains separately bounded to48 native calls/branch at
  17:00–17:20 UTC, no parents/optimizer/train buffer and no early FINAL reads.
