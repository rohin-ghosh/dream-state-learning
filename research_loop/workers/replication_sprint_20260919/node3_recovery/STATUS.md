# Node 3 preserved-state recovery — September 19, 2026

## Current cut: 13:17:53 UTC

**All eight kept lives remain DOWN. None has been restarted.** The first blocker
is persistent disk capacity, not a liveness/credential/lease gate. All eight
native logs explicitly report `OSError: [Errno 28] No space left on device`.
The common outage began September19 05:56:19–05:56:42 UTC; at this cut, downtime
is approximately **7 hours 21 minutes and continuing**. Seven final EXIT files
are zero bytes because failure logging also ran out of writable space.

- Host: `ipp2-ovx-p6-09`, uptime 6 days 3 hours; no reboot.
- `/dev/nvme1n1p2`: 880G total, 845G used, **0 available** to the life owner.
  Approximately 37.45GB remains in filesystem-reserved blocks; this is **not**
  usable recovery headroom and no reservation was changed or bypassed.
- All eight original GPUs: 1MiB used, no compute applications. No kept native,
  classroom or caption runtime process found in the fresh original-route check.
- Original execution ceiling remains **September24 18:00UTC**, with original
  physical lease evidence recording September26 03:03UTC. No lease was extended
  and no fresh provider-side lease query is claimed.
- Guard→plan bytes and **all 196–201 pinned source files per life match**.
  Each last COMPLETE matches a committed adapter/optimizer/RNG file set by hash.
  Tensor deserialization and fresh confined admission have **not** run.

## Per-life boundary table

All rows are DOWN / parent unattached to a new receiver / unchanged deadline.
“Old updates” are **recorded uncheckpointed work**, not recoverable optimizer
state. The full sleep would need a declared new recovery epoch; running only
the remaining updates would be false continuity.

| Life | Original GPU | Last COMPLETE / sleep | Pending operation | Old updates | Full new sleep work | Additional block |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `r213_math_a` | 1 | 9445 / 183 | generation REQUEST9466 | 0 | not applicable | missing RESPONSE; zero-byte 9467 intent partial |
| `r213_math_b_fork` | 2 | 9476 / 192 | SLEEP_REQUEST9505, cycle193 | 48 | 48 | partial sleep193 checkpoint; no COMMIT |
| `r213_math_c` | 4 | 8937 / 194 | SLEEP_REQUEST8966, cycle195 | 8 | 48 | zero-byte 8977 intent partial |
| `r213_r226_caption_observation_fork` | 0 | 10269 / 143 | SLEEP_REQUEST10317, cycle144 | 77 | 80 | zero-byte 10398 intent partial |
| `r213_r226_caption_perspective_fork` | 3 | 10789 / 139 | SLEEP_REQUEST10833, cycle140 | 20 | 80 | zero-byte 10857 intent partial |
| `r213_r226_caption_revision_fork` | 5 | 9991 / 137 | SLEEP_REQUEST10040, cycle138 | 42 | 80 | zero-byte 10086 intent partial |
| `r213_r226_caption_selfderive_fork` | 6 | 9292 / 132 | SLEEP_REQUEST9340, cycle133 | 68 | 80 | zero-byte 9412 intent partial |
| `r213_r226_caption_unparented_fork` | 7 | 10102 / 142 | SLEEP_REQUEST10148, cycle143 | 5 | 80 | zero-byte 10157 intent partial |

Math B is the **first integration candidate**, not launch-ready: its journal
has no partial-intent artifact, its durable sleep192 checkpoint hashes match,
and every pending row and all 48 UPDATE receipts are available. Its attempted
sleep193 optimizer/RNG file is only 93MiB versus the committed file's 155MiB,
and its `torch.save` failed. Never adopt that partial checkpoint or equate its
last logged scalar step9788 with serialized optimizer/RNG state.

## Why the existing fast path cannot simply restart these

1. There is nowhere for the owner to append a journal record or save a new
   checkpoint. No data was deleted, compressed in place, moved, or overwritten.
2. The existing caption checkpoint+tail wrapper requires an exact resolved
   COMPLETE plus paired LEARN, with no intervening work or pending request.
   None of these eight is at that boundary. Trimming the tail would discard
   authentic rows/history and contradict the recovery instruction.
3. Seven journals contain a zero-byte `.intent.json.partial`. The original
   scanner correctly rejects it. Reconciliation must preserve the artifact
   and record what is known; it cannot silently erase the failed transaction.
4. The existing C0/Astra7 pending-sleep candidate is not a drop-in node3
   launcher: it restricts life IDs, a different deadline, three pending rows,
   and a different suffix. Caption lives here have five rows and an actual
   `R227_TARGET_METRICS` record before the recipe. Original pending-sleep
   startup plus paired-LEARN integration is still missing.
5. Math A has no durable RESPONSE for its final generation request. Neither
   a made-up response nor an automatic regeneration is authorized by these
   receipts. It needs a specific loss-accounted interrupted-generation path.

## Prepared repair and CPU evidence

`pending_sleep_contract.py` is an **offline validation patch**, not a runtime
kernel, launcher, admission substitute, or journal repair. It binds each of
the seven real SLEEP_REQUEST tails, original plan/GPU/deadline, all rows,
history and working state, recorded all-authentic-row recipe, target hashes,
and exact old head. It preserves caption diagnostic records rather than
stripping them to mimic the node2 input layout. It requires restarting the
entire pending sleep from durable adapter/optimizer/RNG state and separately
accounting for lost work and newly executed compute. It never executes that
work, clears pending, retries a provider, or claims unsaved RNG exists.

**27 CPU regression tests pass**: 23 contract tests and 4 tests against the
unchanged original fast-startup gates. The latter explicitly confirm that
pending generation, pending sleep and zero-byte partial intents remain
rejected, while a resolved COMPLETE+LEARN fixture is accepted. All seven
contracts also validate against bounded read-only original-node records;
full history replay and tensor loads were not performed.

## Next operational sequence

1. Main must arrange persistent headroom while preserving old artifacts.
   Altering root reserves, using tmpfs for durable checkpoints, or deleting
   historical journals is not a solution within this scope.
2. Complete the original pending-sleep startup/paired-LEARN integration for
   math B; preserve its failed checkpoint and immutable source-bound contract.
   Integrate partial-intent reconciliation before the other six sleep lives.
   Do not invoke a multi-hour full-body historical JSON replay.
3. Before any launch, recheck physical lease, exact PID/start identities and
   original GPU occupancy; obtain fresh original confinement/admission. Old
   guards are evidence, not consumable launch authority. Keep original caps.
4. Record the scoped CPU/provenance Builder receipt in the main coordination
   log at actual deployment. No GPU launch is authorized by this status file.
5. Require actual `LOADED → REQUEST → ACT` and downtime receipts before any
   successful-recovery claim. Then source-bound rebind parents using preserved
   ledgers. Do not duplicate publishers or retry old HTTP401 requests.
6. Preserve the seven-protected-native parent prerequisite. Until all required
   receivers are restored, the current parent snapshot failure is expected;
   it must not be relaxed to make a service look healthy.

## Receipts

- `NODE3_DIAGNOSIS_20260919.json`: bounded tails, checkpoint/source hashes,
  original control/lease bindings, partial artifacts and observed downtime.
- `PENDING_SLEEP_CONTRACTS.json`: seven verified offline contract summaries;
  no child context or full historical bodies copied to the VM.
- `FRESH_LIVENESS_20260919.txt`: original-route final disk/process/GPU read.
- `CPU_TESTS.txt`: 27 passing CPU tests; not a full-repository test claim.
- `COORDINATION.md`: scoped Builder record; Main owns project-level updates.

No original plans/guards, journals, checkpoints, mailboxes, provider ledgers,
parent policies, lease limits or external services were modified. No native
was signalled. No Git commit or push occurred. No restart or parent-delivery
receipt is fabricated; both remain absent.
