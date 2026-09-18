# Node5 fleet: seven live; awaiting Main tested READY

Observed September 18, 2026, 02:09:59 UTC / September 17, 19:09:59 PDT.
Receipt: `INVENTORY_20260918T021000Z.json` (the embedded observation time is
authoritative). **No rollout, stage, signal, hold, parent action or background
waiter was started. Original C2 was excluded.**

| Life | GPU | Native PID | Latest complete | Optimizer total | Inbox files |
| --- | ---: | ---: | ---: | ---: | ---: |
| run1 | 2 | 2495635 | 74 | 6490 | 62 |
| pilot | 6 | 2757295 | 62 | 5911 | 112 |
| repo_reader | 7 | 2761360 | 60 | 5589 | 93 |
| C1 | 0 | 2707975 | 62 | 5543 | 144 |
| C3 | 3 | 2668022 | 59 | 4975 | 132 |
| C4 | 4 | 2606742 | 59 | 4925 | 109 |
| C5 | 5 | 2761060 | 64 | 5165 | 62 |

All seven have an actual LOADED record for their current native PID, matching
plan/lease pins and checked source-file pins. These are **existing R181
learners**, not R195 rollout evidence. Each current recipe is new16/old0;
none has `think_act_learn` in its plan or the R184 module in its source.
All adapter/optimizer/RNG checkpoint references and inbox file hashes are in
the receipt; no saved-state restoration was attempted. New inbox arrivals
remain allowed; existing bytes must remain unchanged.

## Lease and exact-path constraints

- Every plan and its hash-bound LEASE_BUDGET agree: hard wall1789776000 =
  **September 18, 2026, 17:00 PDT / September 19, 00:00 UTC**; lease cutoff
  1789776600 = **September 18, 17:10 PDT / September 19, 00:10 UTC**.
  Preserve the600-second margin. This is verification of existing bindings,
  not a lease extension or external rental-system revalidation.
- Source/control/native PID/start/argv bindings for all seven are retained in
  the inventory. C1/C3/C4 share a native-source hash; C5, run1/pilot and
  repo_reader have distinct inherited overlays. Do not wholesale replace
  them with a C2 source or assume one native text applies to all variants.
- repo_reader logical root is
  `/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/run1`;
  actual backing root is
  `/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/recovery_r154_saved30_20260916_attempt2/run1`.
  Reuse its existing mount namespace and confinement capsule.
- Existing outer execute/readmission processes and contained supervisors were
  identified separately from native timeout wrappers. They are not an excuse
  for a second competing waiter or broad process-group termination. Rebind
  current identities and verify the existing handoff lock before launch.

## Fastest safe reuse (no new custody system)

Use the current per-life R181 `rollout_operator.py` lineage with the R179
primitives: `old_inputs`, `owner_pair`, `namespace_command`, `cpu_proof`,
`validate_successor`, `execute`, `supervise`, and existing strict containment.
Do not invoke its historical selector or mutate its consumed current attempt.
Bind a fresh sole attempt to Main's final bytes and the seven-life allowlist.

The existing `cpu_actual.py:prove` already roundtrips full saved history,
adapter binding, AdamW tensors/groups/steps, Python/CPU RNG, and saved CUDA RNG
without GPU initialization or a wall-extension call. Rebind its old R179/R181
source-policy checks to Main's final approved closure; keep those exact-state
checks. This avoids the unrelated historical `saved_primitives.boundary_cpu`
path, which unconditionally calls `prepare_wall_extension` and fails when the
unchanged-wall plan has no extension authorization. No new wall authority or
runtime repair is needed merely to choose the right existing proof path.

The existing finite transition already provides pidfds, watchdog-backed exact
pause, saved-boundary recheck, readout draining, recorded retirement and strict
admission. Keep it. Do not read readout results. Future R184 metadata-tail
support must prove the exact same SLEEP_COMPLETE/checkpoint, never accept a
REQUEST/INBOX/new-work suffix or a previous checkpoint rollback.

## Main integration blockers

1. **Main tested READY and final receiving source/config/dependency bindings
   have not been supplied.** Shared source files changing on disk are not
   READY. Need R184/R193/R198/R195/R194 together and preserved new-only16x.
2. Need final per-life CPU gate and tool-route bindings. R184 requires a
   `cpu_gate_root` and hash. The bounded remote census found no separate
   persistent bridge/broker/service process outside C2; this is not proof
   that tools are absent (routes may be local or transient).
3. Initial inspection found incomplete NFKC propagation in the kernel bridge
   and community remote schema. A later finite check at approximately02:12Z
   now sees Main's shared-tree changes: `child_request` accepts NFKC and passes
   it to extraction; `remote_dispatch` accepts optional `code_policy` and
   `root_policy`. This removes those static source findings, **not** the need
   for tested READY and matching actual receiving bridge bindings. The seven
   running sources remain unchanged. This operator edits neither module.
4. Receiving-source import/CPU checks and real saved-boundary proofs remain
   required after READY. Historical passed tests are not approval of the new
   closure. No training rows, model state, visibility or claims are changed
   by this metadata-only preparation.

After READY: receive/bind, run actual-source CPU and preservation checks,
reuse the finite same-life boundary handoff, then verify successor
**LOADED + first actual R184 stage**, each against its PID/source/config and
saved-state binding. Staging/arming/LAUNCH alone is not success.

The initial observer receipt is retained: it double-counted timeout wrappers
and reported seven `count=2` rows, not seven failed learners. Exact native
argv-prefix matching corrected this observer-only issue. Later receipts
locate inboxes at `stream/inbox` and scan far enough to identify every current
LOADED record. No runtime or test file was modified.

Follow-up inventory `INVENTORY_20260918T021156Z.json` at02:11:56Z confirms
all seven identities remain live, with C1 complete63 and run1 complete75.
It adds hashes of each existing operator/helper and consumed-attempt receipt.
Every current lane has OWNER_RETIRED and historical READY artifacts; those
are the old R181 handoff, **not Main READY for this rollout**. The existing
same `cpu_actual.py` hash is shared by all seven; repo_reader retains its
exact `reader_capsule.py` hash29e2d77dfe21a6c1b37861f52c00d2eeb858c67b60f054ab6e2d2238cc135c95.
