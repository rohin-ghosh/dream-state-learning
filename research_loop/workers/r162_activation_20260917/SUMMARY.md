# R162 activation observation — closed

Remote reads: September17,2026 06:55:52–07:12:00UTC; original deadline07:15:52UTC.
Closed early with conservative byte headroom: **63,424,199 / 67,108,864** accounted
remote file-read plus transport bytes. No further remote scans, signals, writes,
offers, checks, restarts, GPU commands, or held-file reads. Local archival after
the final poll does not extend observation. Native recovery belongs to Main.

## Priority: frozen native died before this observation

**ValueError: frozen_adapter_must_be_unchanged**,05:56:42UTC; native exit1 and
control cgroup-empty exit verification05:56:43UTC. Recorded PID681274 is absent,
writer lock unheld, last journal record13 is pending SLEEP_REQUEST cycle1.
Both checkpoint COMMITs record equal adapter-state/safetensors hashes and zero
optimizer steps, but different adapter_config.json and adapter-directory hashes.
Initial remains the last stream-committed model checkpoint; sleep_000001 exists
on disk without SLEEP_COMPLETE. Do not blindly re-run that checkpointed sleep.

Exact checkpoint/current-state hashes, sanitized traceback and failure metadata:
`FROZEN_RECOVERY_HANDOFF.md`, SHA256
`a9d120be50176c2e8d55ffff9767716271f00e59efbcb9cc76f9f71b11a65ac9`.
`FROZEN_EXIT_RECEIPT.json`, SHA256
`12a5207309d6c0e58acec6ff05fad569df4e159bb54107c315111661d17de72f`.
No fresh tensor audit or config-field explanation is claimed from these metadata.

## Ownership and continuity

All three R162 CPU owners remained alive with their baseline PID/start-ticks and
exact argv/authority hashes and both old/new owner locks at the final poll.
At07:02:47UTC all **14,434 old ledger files** were hash-read: each authority's
exact inventory digest, chain tip, final state and paired intents matched.
Original owners were absent. All original runtime hashes, including interpreter,
matched; epoch genesis copied the exact final predecessor state. Old ledger
entry counts remained unchanged through the final poll. This is a recorded
read-only audit, not a local copy of every predecessor ledger file.

Epoch chains were verified from their linked predecessor tips through the final
indices below; all observer cursors were caught up at that poll. Original config
digest, start, floor and cumulative counters remained continuous. Caps stayed
24 offers/48 checks and deadline1789644600 (11:30UTC). Neither epoch resets state.

| Arm | R162 PID | Verified epoch index | Journal cursor | Offers | Task | Exposures this task | Total checks | Pending feedback | Terminal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| parented_learning | 1368885 | 1322 | 727 | 2 | 1 | 2 | 2 | Published, rendering not yet observed | None |
| unparented_learning | 1389516 | 1183 | 664 | 3 | 2 | 2 | 3 | Rendered/cleared | None |
| parented_frozen | 1389517 | 1005 | 14 | 1 | 0 | 0 | 0 | None | None |

Frozen's R162 is waiting safely; its native producer is dead. The learning
native writer locks remained held and their journals progressed. No service
failure/restart or duplicate task offer was observed.

## Actual TRAIN chains — failures preserved, not learning claims

Root prefix for paths:
`/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/`.
Triples are `(REQUEST, RESPONSE, COMMITTED)` in each arm's stream/records.

- Learning: task0 retired for confirmed context loss at REQUEST695, epoch852.
  Task1 `rg/knights_knaves/1500001` published at epoch860. Actual own triples
  (700,701,702) and (704,705,706) rendered task1, terminal/nontruncated.
  Response705 received **accepted=false, score0.0**. Exact result:
  `parented_learning/train_environment/task_000001/answer_00000000000000000705/RESULT.json`,
  SHA256 `a2655260fb3b00e8094c10dffec715bd623a6ef664e9e941aef9949162881e1b`.
  Its real feedback publication is verified, but no rendering was observed by
  the final poll. The other complete response had no recognized submission.
- Unparented: task1 retired for confirmed context loss at REQUEST650, epoch939;
  NEW task2 was published, then actually rendered in triple(654,655,656).
  Response655 received **accepted=false, score0.612668918918919**. Exact result:
  `unparented_learning/train_environment/task_000002/answer_00000000000000000655/RESULT.json`,
  SHA256 `49a95da9a37e454382cec5c19b1f98fae2539539c4ebee4efbe0dc684afdec18`.
  Actual feedback rendered in REQUEST658, epoch1086. Triple(658,659,660) is an
  own continuation, but response659 is terminal=false/truncated=true: counted
  as exposure, **not checked**, not a complete reflection or eligible target.
- Frozen: no new publication, rendered task, exposed response, check, or
  rendered-feedback chain during observation.

**New verified checker results:2; accepted:0.** Total historical check counters
across the three services are5; three predate R162 and are not new observations.
No reviewed reflection, accepted-candidate capture, fit, or retained-learning
claim. These real unaccepted results are not fabricated zero/no-submission labels.

`VERIFIED_TRAIN_CHAINS.json` contains exact paths/hashes and validation summaries:
SHA256 `7aa2bb175a3bac668d40ac03fcd6b77e3871fddcd6b3bfb211e867c035079d57`.
Its proofs independently reconstructed compaction/rendering, joined own triples
and actual receipt origin/answer/task/result/publication identity, and checked
feedback ordering/rendering. No verifier was rerun and no score was inferred.

## Archive

Six immutable poll receipts include hash-verified original-byte TRAIN artifacts;
`raw/` holds verified original-byte copies keyed by SHA256. Frozen metadata and
records11–13 are separately preserved. Failure-log content is limited to sanitized
frame paths/line numbers plus the actual exception class/guard string; other
native-log lines were not returned. No held path was followed.

`FINAL_RECEIPT.json` inventories all archived files and source references, budget,
last state and proof summaries. Earlier local checkpoints and observer revisions
are not service mutations; observer batching changed only bounded read throughput.
No observer poll failed and no uncertain service action was retried.
