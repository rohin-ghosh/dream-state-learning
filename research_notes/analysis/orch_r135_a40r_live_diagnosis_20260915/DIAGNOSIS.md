# R135: a40r physical0/2 bounded live diagnosis

2026-09-15 UTC. Read-only node inspection through `gpu/a40r_ssh.sh`; final liveness sample **21:48:01 UTC**. Only this directory is owned. No launch, model call, restart, kill, reservation, credential change, source/live-plan edit, ledger edit, or Git mutation was performed. Raw reflection and checkpoint bodies remain node-local. `RECEIPT.json` contains selected metadata and evidence hashes, not those bodies.

## Terminal and current cursor

| Physical | Exact existing lane | Terminal UTC | Actual cursor / next unreserved call |
| --- | --- | --- | --- |
| 0 | `/localhome/local-rohing/orch_r109_route_20260915_node1_7_attempt2/overflow_r129_v1/campaign_node1_7` | FAILED, 21:32:28.185865 | C53 reflection turn 2; native 2047 COMPLETE; next **2048**; P112 COMPLETE, next parent 113 |
| 2 | `/localhome/local-rohing/orch_r109_route_20260915_r120_C39_fork_a40r2_attempt1/lease_r120_v2/campaign_node1_7` | FAILED, 21:27:58.909450 | C60 reflection turn 2; native 2328 COMPLETE; next **2329**; P127 MISSING, next parent 128 |

Both devices read **0 MiB / 0% utilization**, twice. Neither is currently waiting for its parent or performing native inference. The historical guard/native PIDs 2809466/2809711 and 776453/777378 are absent; current process-metadata discovery also found no matching lane process. The physical2 binding comes from its existing root and `GUARD_LAUNCH.json` physical=2/source metadata, corroborated by launch/actor identity, not an assumed PID.

Both native failures are `ValueError: uncropped_context_fit`: physical0 at 21:32:25.809572; physical2 at 21:27:57.040392. Both guardians subsequently report `native_failure_no_replay`, write FAILED terminal receipts with automatic refill false, and publish clear release scans (physical0 21:32:29.426058; physical2 21:28:00.423721). Their `STATUS.json` parent phases are stale and must not override terminal evidence.

## Root cause and provenance distinction

The node's pinned runtime checks the uncropped prompt against the 32,768-token context limit in `organism_v6/orch_r109_route.py:139`. Both native tracebacks end there. In `gpu/orch_r109_route_run.py:198`, this check precedes reservation on line 199. The next call files are absent and native ledgers end at 2047/2328: the pending second reflection was **not reserved or executed**. The evidence supports context-fit rejection, not OOM, lease exhaustion, or an inference exception after dispatch. Exact failed prompt token counts were not computed; no tokenizer/model execution was needed.

Physical0 already completed its R129 C52 changed-context carry, then overflowed again at C53 turn 2. Its latest checkpoint is C52/native 2006, **41 completed calls behind** the terminal cursor. Physical2's latest checkpoint is C59/native 2302, **26 completed calls behind**. Restarting either checkpoint conventionally would replay completed work. Native counts and reservation sequence agree; parent completed/missing counters are inherited run counters and must not be conflated with parent reservation numbering. Preserve both separately.

**Physical2's P127 is not an already-consumed COMPLETE parent.** It reserved at 21:24:56.838448, exhausted the runtime's 180-second parent wait, and wrote MISSING at 21:27:56.944019. The response file now says COMPLETE, but its mtime is **21:28:10.816575**, after both the missing receipt and native/guardian failures. The exact runtime (`gpu/orch_r111_route_recovery.py:95`) returns empty advice when that wait expires. Do not retroactively consume the late response, change P127's disposition, reset its charge, or reissue it. Physical0 P112, by contrast, has a COMPLETE consumption receipt and matching response/request join.

## Residual timers and bounds

No lane-attributable `sleep`/`timeout` process was found by selected stdio/root metadata and timer-parent references to the receipt PIDs. A subsequent cwd/stdio/command-metadata scan also found no lane process. No command-line reads were permission-denied in that final scan. This is a bounded process census, **not an exhaustive scheduler registry audit**; no timer was canceled or replayed.

Both READY files still carry native deadline **September 18, 2026 17:58 UTC**, hard deadline **18:00 UTC**, and lease end **September 19, 2026 00:00 UTC**. Near 21:47:43 UTC September 15, the remaining configured intervals were 245,417 / 245,537 / 267,137 seconds respectively. These are unused future bounds, not evidence of a live watchdog, reservation, or restart permission. The physical2 parent wait is already exhausted, not residual.

## Smallest prospective non-material recovery — Main only, not executed

Use a **new, explicitly declared changed-context continuation artifact at each exact unreserved turn**, reusing the existing R129 context-fork approach rather than restarting an old guard or modifying its one-shot evidence. This is an experiment implementation choice under the supplied standing authorization only while retaining its frozen-base, visibility, provenance, controls, and claim invariants; it is not an identical-context continuation or a new scientific claim.

1. Bind the failed-state counters, complete reservation ledger prefix, last completed native reflection, actual parent consumption receipt, pinned source/base, and existing deadlines. Preserve all old evidence and counters, zero optimizer updates, and no adapter. Do not reuse the hard-coded R129 C52/2006 recipe or its `GUARD_ONCE` directory.
2. Retain the latest full child-authored reflection verbatim node-local; archive rather than silently crop the earlier prefix. Use an explicit changed-context notice and pending instruction, without a compiler-authored summary. For physical0 carry **actual P112 advice** into C53 turn 2 / native **2048**. For physical2 preserve the actual **P127 MISSING / empty-advice** outcome into C60 turn 2 / native **2329**; the late response is archival only. No parent re-call for either pending turn.
3. CPU/provenance preflight the exact rebuilt prompt below 32,768 tokens, native numbering, parent dispositions, prefix hashes, and absence of next-call artifacts. Include regressions for repeated turn-2 overflow and late-response non-consumption. A fresh compact carry is not guaranteed to fit; if it cannot preserve the full selected child reflection within the frozen limit, stop rather than crop it, replay calls, or change the base/context invariant. The physical2 MISSING branch requires its own tested handling; the existing R129 helper requires COMPLETE and cannot be applied verbatim.
4. Do not claim that the lagging checkpoint includes intervening work or rerun those cycles. Preserve the partial-cycle task/evidence state and completed-call charges from node-local artifacts, or explicitly document what state cannot be restored before proposing any launch. Physical0's repeated overflow also warrants this preflight before every future unreserved reflection dispatch, not an assumption that one compaction solves the run permanently.

Main owns implementation, any required CPU/provenance publication, live-plan decisions, and Git. This task changes none of them and launches nothing.
