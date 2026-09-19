# Node2 ENOSPC: independent read-only recovery handoff

2026-09-19. **Exact-tail fast resume is BLOCKED for both lives under the
currently installed, unchanged contracts.** Restored disk space alone does
not resolve an interrupted optimizer sleep, an incomplete journal transaction,
or the consumed one-shot admission. No native/service action is authorized by
this document.

## Scope and evidence

Only standard-library reads over `bash gpu/ovx_ssh.sh` were executed. No
research module was imported/executed, no StreamJournal was opened, no tensor
was loaded, and no process was signaled. No node files were created, removed,
renamed or repaired. Full journals remain on node2; local artifacts contain
bounded headers, metadata and selected checkpoint/state summaries, not history
or working-state bodies. The selected saved-state JSON was decoded/hashed on
node2, not replayed through the history/learning runtime.

- `NODE2_READ_ONLY_20260919.json`: SHA-256
  `0981c0861c60a35b492ba0ff717e9a109f2d0cc2e4051b96dd59417b4fd5b2ea`.
  Observed Unix 1789788267.5218635; inspection took 1.880 seconds. Both recorded
  native PIDs, C0 881309 and Astra7 886059, were absent. Boot was
  `8ff7b0dc-fbdf-4945-9044-3dffe94b5407`; about 3.69 GB was available on `/`.
  This is consistent with main's cache purge, not proof of sufficient future
  checkpoint/journal capacity. CUDA emptiness is main's observation, not an
  independently run GPU probe in this sidecar.
- `BOUNDARIES_VERIFIED_20260919.json`: SHA-256
  `ad85f45a7be0eaa1a372476b4c763ffad3f6ac6571caf53bf95540c7e360fd68`.
  Canonical record hashes verified for each selected COMPLETE, pending
  SLEEP_REQUEST and final UPDATE; COMPLETE/SLEEP_REQUEST saved-state hashes
  verified; each COMPLETE checkpoint document exactly equals its on-disk
  COMMIT. These are subset proofs, not a full journal/intent audit. Paired
  LEARN records were read and their metadata observed in the first receipt.
- Neither checkpoint binary files nor the full retained prefix/tail were
  rehashed; no restore/fast-resume timing or LOADED success is claimed.

## Exact committed boundaries and interrupted tails

| Item | C0 | Astra7 |
| --- | --- | --- |
| Latest COMPLETE / paired LEARN | 6631 / 6632 | 7750 / 7751 |
| Completed sleep / saved optimizer steps | 145 / 8412 | 146 / 9644 |
| COMPLETE saved rows / sleep frontier | 441 / 441 | 450 / 450 |
| Next SLEEP_REQUEST | 6660, cycle 146 | 7776, cycle 147 |
| Pending saved rows / sleep frontier | 444 / 441 | 453 / 450 |
| Final committed record | UPDATE 6710, step 8460 | UPDATE 7807, step 9673 |
| Committed UPDATE receipts after COMPLETE | 48 | 29 |
| Tail after COMPLETE, excluding intent bytes | 79 records / 280,375,032 bytes | 57 records / 200,755,465 bytes |

Exact COMPLETE pins:
- C0: `c9d2aa785f44f81f80aa50b2dbcc04e734bc1f37c1c5743e73a32e12c9ccb587`.
- Astra7: `a77e37494bf0c93ab640b67ef96f59cc520f2b4382a6b0f5651891a27d0ed485`.

Exact paired LEARN pins:
- C0: `bf945b51933ed768265ee632cf4378e109ddd22ffb069452a1e4c87fa3f4fda4`.
- Astra7: `a518531d486a69aed33e2777c3fbde0ba10db4bcd733b2de343c2399bd9218b3`.

Both pending SLEEP_REQUEST snapshots preserve three newer rows and history
including `working_state`, events, frontier and operations. Their pending
tokens are `sleep:...`, not completed sleeps. COMPLETE snapshots also retain
their original history/working state. Clearing pending or restoring only the
older COMPLETE is not exact current working-state continuity. UPDATE records
are execution receipts, not recoverable optimizer/RNG/tensor snapshots; steps
8460/9673 must not be described as durably checkpointed model states.

### C0 failed checkpoint

Actual root:
`/localhome/local-rohing/orch_r216_C0_20260918_attempt2/raw`.
Committed checkpoint: `checkpoints/sleep_000145/COMMIT.json`, optimizer/RNG file
161,853,949 bytes. Saved optimizer/RNG SHA:
`6e554cdf084ac3a9141f587e594361befb6bedae41ab50d0a9ce8e49a56f4ac4`.

Failed next directory `checkpoints/sleep_000146` exists with `adapter/` and an
86,966,272-byte `optimizer_rng.pt`, **no COMMIT.json**. The traceback reports
the torch serialization position mismatch. That incomplete next checkpoint
must not be promoted, overwritten, or mixed with the old optimizer/RNG.
No unexpected record-directory entries or missing intents for committed
records were observed; this does not make the interrupted sleep resumable.

Observed control correction: C0 `EXIT.json` is 80 bytes with `exit_code=1`,
`no_retry=true`; `OUTER_EXIT.json` is 57 bytes with `status=1`. They were not
zero-length at this inspection. These are explicit failure receipts.

### Astra7 failed publication

Actual root: `/localhome/local-rohing/orch_r229_Astra7_20260918/raw`.
Committed checkpoint: `checkpoints/sleep_000146/COMMIT.json`, optimizer/RNG file
161,853,949 bytes. Saved optimizer/RNG SHA:
`a52a7b1723650eff309216fe7e5dd67fcc08819e4f229d0e45841641035d3104`.

Pending artifact:
`stream/records/00000000000000007808.intent.json.partial`, zero bytes,
inode 55517074. The last committed record is UPDATE 7807; the attempted next
publication is not a committed UPDATE. The exact final resident optimizer
step at death is not established by that empty partial file.
`EXIT.json`, `OUTER_EXIT.json` and `FAILED.json` are zero-length and cannot
prove successful exit or supply a numeric exit status. Do not delete the
partial, fabricate its contents, or silently omit it from the reader.

## Original failure and restore contracts

All source references below are relative to each life-specific
`source_r233_lease_continuation`. Source hashes and their guard pins are in the
receipts. The two guards and plan hashes still matched their preserved pins;
only the named source modules, not the entire 2,292/2,295-file source closures,
were independently hashed in this sidecar.

1. `gpu/orch_r125_stream_journal.py:455`, `StreamJournal._scan()`, enumerates
   every retained index, parses each record and intent and applies every
   transition. At line 463, a `.partial` record-directory entry raises
   `incomplete_or_unexpected_journal_tail`. The unchanged contract provides no
   “empty means safe to ignore” exception. Astra7 is blocked before replay.
2. `gpu/orch_r125_continual_native.py:743` restores the latest saved state.
   Line 751 rejects unresolved pending generation/sleep; line 758 requires a
   saved RNG sleep boundary unless one of its explicit narrow exceptions
   applies. A faster scan alone cannot bypass either requirement.
3. `gpu/orch_r125_preupdate_recovery.py:137` is not a general crash recovery:
   it requires a latest exact SLEEP_REQUEST, specifically cycle 2 and three
   rows after sleep1, plus the original pre-update encoding-failure evidence.
   Both actual heads are UPDATE, at cycles 146/147. This exception does not
   apply, and neither current plan configures it.
4. `gpu/orch_r125_continual_native.py:684`, `finish_sleep()`, refuses an
   existing next checkpoint directory (`never_repeat_checkpointed_sleep`).
   C0's failed sleep_000146 is an additional block; do not remove it to evade
   the check. Checkpoint creation at line 439 writes adapter, optimizer/RNG,
   then COMMIT; absence of COMMIT is not a completed checkpoint.
5. `gpu/r213_recovery_runtime.py:43`, `RecoveryJournal._advance()`, recognizes
   an explicit `R213_SAVED_BOUNDARY_RECOVERY` event. It binds the exited tail
   and a receipt, requires old-native absence and nonzero outer status, and
   marks `exact_resident_continuity_claimed=False`. It replaces the latest
   state with a selected COMPLETE state and clears pending state. This is a
   declared saved-boundary rollback, **not exact-tail/working-state recovery**,
   not automatic, and not a fast reader. Astra7's empty outer-exit file cannot
   be presented as its required numeric failure evidence.
6. Native restore at line 429 rehashes adapter files and optimizer/RNG; at
   line 356 it restores optimizer state/count, parameter ordering, Python RNG,
   CPU RNG and CUDA RNG, then checks adapter state. Keep all these checks and
   the base/experiment/history hashes. Do not initialize a fresh optimizer,
   reset RNG, pair different checkpoint cycles, or alter row/visibility policy.

## Existing fast-resume support: not installed

Neither installed source contains `gpu/checkpoint_tail_runtime.py`; neither
plan selects `checkpoint_tail_recovery`. RecoveryJournal adds an event
transition, not a bounded `_scan` override. The v4 prefix reader previously
benchmarked for C2 is a separate candidate, not node2 admission evidence.
The preserved retention-only C0/Astra7 ports are not proof that a checkpoint-
tail resume route has been integrated and tested for these failure states.

For a future bounded route, main would need an exact-source receiving port,
its own source/epoch/guard pins and tests, a node-local verified prefix outside
the critical resume window, and full raw verification of the selected tail
and intents. It must preserve C0/Astra7-specific journal and inbox behavior,
all working-state/INBOX/sidecar semantics and failure checks. This sidecar did
not create a prefix proof or approve that port. Even after such a port exists,
the post-update sleep and Astra7 partial still need an independently bound,
explicitly authorized reconciliation contract; they are not cache problems.

## Original executable/confinement route, not a restart command

Executable used by the preserved native argv:
`/localhome/local-rohing/v2/venv/bin/python -B -m gpu.r233_node2_recovery`.
Its external entry is `dispatch --config <NEW_OPERATOR_APPROVED_GUARD>`.
Do **not** rerun it with either old guard: OUTER_STARTED and DISPATCH_ONCE
already exist, and admission/LAUNCH receipts are stale. Do not invoke `native`
or `child` directly to avoid the dispatch checks.

The intended original chain is:
`dispatch -> exact receiving CPU/source validation -> systemd probe -> fresh
privileged scan -> bounded systemd child -> one-shot supervisor -> stdin
LAUNCH_READY / exact-parent-bound native -> normal restore checks -> LOADED`.

`gpu/r205_runtime.py:301` uses `gpu/r184_node2_confinement.py:21` and preserves
DevicePolicy=strict, NoNewPrivileges=yes, empty capabilities, UID/GID 2524,
the actual GPU minor/UUID, source working directory, finite runtime and
environment isolation. `gpu/r233_node2_recovery.py:38` computes the remaining
runtime from the existing hard end/lease, not a fresh wall budget. Its original
pre-service admission must be privileged, clear, exact-guard-bound and no more
than 120 seconds old. `gpu/orch_r125_continual_guard.py:18` still requires full
Python source closure, node/plan/allocation/CPU/lease pins and reservation margin.

Both lives intentionally name the same *virtual* plan root:
`/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`.
The confinement BindPaths maps each distinct actual `copy_raw` root to that
virtual root. Do not confuse the shared virtual name with shared life state,
or run outside the life-specific original mount/admission route.

| Binding | C0 | Astra7 |
| --- | --- | --- |
| Physical slot | 4 | 1 |
| GPU UUID | GPU-d304a15c-516a-16a0-a926-a560304077cc | GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4 |
| Guard SHA | acf4d2d015874af1cc9585a25de63827e7d7ec36acd7a4509bce09671985f6c2 | fae6f4ede1e9c80be060aeca8dd494cbb24a6228b9225e33856b62ec3c0047f6 |
| Plan SHA | 87d5ed93cf9631cd101160f523eba550e590d8e1133f7c9c0a8329412243aa3a | 5e0eb5bfd150bb9ec7bcf8510c147d13f33b6bf529e7d1ad335e533c84dfda8d |

Unchanged for both: hard end **1789927200 = September 20, 2026, 18:00 UTC**;
lease end 1789980180 = September 21, 2026, 08:43 UTC; next-reserved bound
1789958580 = September 21, 2026, 02:43 UTC. No extension or new lease proposed.

## Bounded next decisions for main

1. Finish capacity recovery and budget safe checkpoint/journal headroom; this
   sidecar offers no deletion, archive transfer or weight-migration action.
2. Keep complete checkpoints, all tail/intent/partial artifacts, old controls,
   source epochs and working-state snapshots immutable. Verify checkpoint
   binaries against their exact COMMIT before any eventual model load.
3. Decide an explicit post-update reconciliation policy. **If preserving the
   latest working state and exact tail is mandatory, neither unchanged route
   is currently eligible.** Do not claim a COMPLETE-only rollback preserves
   the three newer rows or the resident optimizer/RNG state.
4. If a recovery implementation is authorized, stage a new source/attempt and
   exact source-bound CPU/receiving/admission evidence; retain original policy,
   namespace/GPU restrictions and deadlines. A fast reader and a failed-sleep
   reconciliation are separate requirements. No implicit full-prefix fallback,
   partial omission, duplicate send, or replay of unknown execution is approved.
5. Only main's separately approved execution may use the original confinement
   route. Require actual source-bound LOADED plus subsequent committed delivery
   evidence before reporting restoration. No automatic recovery is claimed here.
