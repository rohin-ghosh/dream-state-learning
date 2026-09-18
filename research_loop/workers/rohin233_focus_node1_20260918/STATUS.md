# R233 node1 retirement receipts

Scope is node1 only. The five selected lives were **already ended**, not live
retirements performed in response to R233. Their active R210/R213 controls had
successful `EXIT.json` receipts and complete sleep/working-state/terminal tails.

| Authorized life | GPU | Final active control | Existing normal exit (UTC, September 18) | Final sleep | Optimizer steps |
|---|---:|---|---|---:|---:|
| creative_b1 | 7 | creative_b1_r210/control | 06:32:01.709854 | 69 | 5,500 |
| r203_creative_structured_a4 | 4 | r203_creative_structured_a4_r213/control | 08:01:30.275760 | 81 | 5,564 |
| r203_math_comm_b2 | 2 | r203_math_comm_b2_r213/control | 08:06:22.524714 | 81 | 5,164 |
| r203_math_self_derive_c5 | 5 | r203_math_self_derive_c5_r213/control | 08:13:10.731101 | 81 | 5,660 |
| r203_repo_evidence_c3 | 3 | r203_repo_evidence_c3_r213/control | 08:19:48.261895 | 81 | 5,868 |

The common original root is
`/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/`.
For each row its untouched raw root is `<common-root>/<life>/life`.
Original cohort-root `RETIRED.json` files refer to predecessor replacements;
they were not used to claim descendant termination.

Independent state copies are under logical node1:
`/localhome/local-rohing/rohin233_focus_node1_20260918/<life>/snapshot`.
Every training checkpoint and complete stream file is copied, together with
active source/control. Original records, working state, inboxes, checkpoints,
earlier phases, service artifacts and readouts remain in place. No bytes deleted.

Nine focused CPU tests pass. All five copied adapter/optimizer/RNG hashes, CPU
payload checks and complete saved-journal validations pass. The canonical
aggregate is `receipts/VERIFIED_ALL_FIVE.json` (SHA-256
`a0819b5e9a1eb230e485975602dcbf3c4bd117cd534cad3050beb13fedc2cd89`).
The earlier four-life receipt is retained, not overwritten. Total preservation:
90,037 files, 49,155,836,203 bytes, and 37,080 fully validated journal records.
No GPU model load/resume is claimed. Every archival verifier has exited.
Twenty-one historical local-parent PID checks found no remaining process
(`LOCAL_HELPERS_FIVE.json`). No native, timer,
parent or watcher was signalled; no kept life was paused; no GPU was refilled.

The `VERIFIED_RETIREMENT.json` receipts carry launcher PID/start ticks,
the exact state/checkpoint hashes, full manifest pointers and journal audits.
The launcher is the timeout wrapper, not the native child. Native PID/start
ticks are unavailable after these existing exits and are not fabricated.

`REPO_C3_SCOPE.json` binds the user-authorized extension to the exact `talk.sh`
prefix/mapping and the actual R213 control. Final ACT7792 has the attributed
PROCESS_FAILED receipt7795; the subsequent LEARN proposal is not a checked
success. This bounded evidence does not justify retaining the already-ended arm.

## Historical process identity

| Life | Timeout-wrapper PID | Wrapper start ticks | Final native PID/ticks |
|---|---:|---|---|
| creative_b1 | 3504372 | 42941176 | Unavailable after existing exit |
| r203_creative_structured_a4 | 303021 | 43585259 | Unavailable after existing exit |
| r203_math_comm_b2 | 302762 | 43585122 | Unavailable after existing exit |
| r203_math_self_derive_c5 | 303118 | 43585324 | Unavailable after existing exit |
| r203_repo_evidence_c3 | 302896 | 43585191 | Unavailable after existing exit |

Actual active pointer, guard, launch and exit file hashes are bound in the
canonical receipts. The `full_archive_manifest` field provides each exhaustive
node-local inventory's exact path/hash; `saved_artifacts` binds its final adapter,
optimizer/RNG and COMMIT bytes. `resume_state_record`, `working_state_record`
and `terminal_record` bind exact resumable context/working state and clean end.
Checkpoint virtual paths remain unchanged and require the recorded receiver
namespace mapping when restored. All process absence checks precede archival
finalization. No native start ticks or successful GPU restore are invented.
