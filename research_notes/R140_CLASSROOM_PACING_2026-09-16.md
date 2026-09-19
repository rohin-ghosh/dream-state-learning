# R140 prospective receiver-sleep classroom pacing

Owner: Sagan. Authorized September16,2026 within builder R134/R137 scope.
Only the relay changes. Children, parents, native PLANs, checkpoints, histories,
optimizer/RNG state, source snapshots and leases remain untouched. No behavioral
benefit is claimed. The existing R134 sender-sleep phase remains retained evidence.

## Exact prospective policy

- Bootstrap validates the journals and pins separate observed heads for A1005/6/7.
  These heads and the immutable PHASE timestamp define the new phase, not process
  spawn time. No peer message is published during bootstrap.
- Only a TRAIN child response whose REQUEST begins at or after its phase head
  can become eligible. It must be the last committed response included in a
  subsequent verified sender SLEEP_COMPLETE. No pre-phase/inflight source backfill.
- Each receiver gets at most one reserved incoming attempt per latest observed
  completed receiver sleep. Historical missed intervals never accumulate credits.
- Peer order is lexicographic, excluding self: receiver5 takes6 then7; receiver6
  takes5 then7; receiver7 takes5 then6. Rotation advances on reservation, including
  partial/uncertain attempts and explicit oversize skips, not on successful hearing.
  If the expected sender has no new eligible source, the relay waits; it does not
  substitute another sender or block the child.
- Select only that sender's latest eligible source. Persist supersession and
  skipped-interval receipts; never replay an old attempted sender/receiver pair.
- Allow only one outstanding attempt per receiver. The prior attempt must be
  verified in a rendered REQUEST, followed by a later receiver sleep, before a
  new attempt. Registration alone is insufficient. This also handles a receiver
  sleep racing a publication: there is no second queued message in that interval.
- Predecessor messages already queued drain naturally. Previously unobserved
  predecessor intents require exact REQUEST exposure and a later receiver sleep
  before new delivery. An unidentifiable predecessor partial intent fails closed
  for new dispatch. Unacknowledged delivery is never retried.
- Exact raw source text is still attributed as `Tool: Peer A100N:`. There is no
  summarizer, relay truncation or invented distillation for no-distillation7.
  Oversized envelopes consume a logged skipped slot without publishing.
- Keep max1000 reserved pairs across inherited and new attempts, not1000 anew.
  Keep the original16384-byte envelope cap. Polling is2seconds and never itself
  grants a delivery credit. The original hard end1790442300 remains enforced.

## Custody and restart

The new sidecar holds the old state directory's exclusive flock for its entire
lifetime, preventing the old relay from concurrently restarting. It never writes
that directory. CONFIG binds its complete file manifest and directory identity;
revalidate the predecessor before publication. The new state has its own lock.
All journals remain read-only to the sidecar except ordinary environment-INBOX
publication through the existing API; no journal writer lock is acquired.

Reservations encode receiver, sleep-record index and pair in their filenames.
Even an incomplete reservation consumes the interval and pair on restart. All
intent/partial/uncertain custody remains. Restart revalidates from genesis to
the observed live heads, then selects only the latest eligible state. It does
not replay intervening intervals. Incomplete PHASE custody is not reset.

Old visible peer text is not erased: pacing limits future arrivals, not retained
context size. The support no-distillation arm can therefore retain earlier peer
messages until its existing context eviction policy removes them naturally.

## CPU and immutable source gate

Local and exact node-local suites:103 tests PASS (35 new pacing,37 existing
relay,31 strict parent-exposure fixtures). Covers sender versus receiver cadence,
asymmetric sleeps, latest-only selection, delayed/registered-only exposure,
sleep/publication race, uncertain acknowledgement, partial slots, restart,
predecessor locking/integrity, no backfill, original budgets, exact attribution,
two-segment/no-summary source, source revalidation and wall expiry.

The first local29-test run had a fixture assertion sorting random inbox UUIDs as
chronology; the fixture now orders by the durable rotation index. No runtime
failure was hidden. Later combined97,101,103 and exact remote103 runs passed.

New source: `gpu/orch_r140_classroom_pacing.py`
SHA256 `02810952cb96c003f30cf68d11e63ac1df57286e8bc46a5db63398e5ae054b12`.
Tests: `tests/test_orch_r140_classroom_pacing.py`
SHA256 `33b0f2348dcf416e4f2f06736aa107aa580ee3c2dfc564c22cb33fc35be7b194`.
Node closure: `/localhome/local-rohing/orch_r140_classroom_pacing_20260916_attempt1/source`.
CPU_GATE SHA256 `94de1ef20749ff20ba3e2e8b475e35a749e573dcd72c44fed2e6c26ae30ade00`.
Python closure digest `87f420704bbbb7ee276e5ccb3faf9a248e8456cf4b8332aaeab3220d6b72567d`.
The old active relay snapshot is not edited; the new closure copies it and adds
the pacing module/tests plus the exact existing strict-exposure helper/tests.

## Deployment status

Deployed September16,2026. Old relay2087568 exited after exact-identity pidfd
pause at verified clock_nanosleep230 and complete custody archival. New
relay2670302 started12:33:22Z. The validated no-send bootstrap established
PHASE at12:34:05.513174Z, observed heads5=684,6=694,7=522. All eight native
identities were unchanged through handoff; all eight local parents remain live.
No child or parent was signalled, stopped or reset.56 inherited reserved pairs
remain old-phase evidence and count against the original1000 budget.

| Thread | Native PID | Programme / replay | Parent cadence / style | Peer phase |
|---|---:|---|---|---|
| A1005 | 2036898 | classroom brain / free_distillation | sparse3 / explanatory | R140 receiver-sleep alternating6,7 |
| A1006 | 2058507 | classroom creative / reread_select | sparse2 / workshop | R140 receiver-sleep alternating5,7 |
| A1007 | 2047929 | classroom support / no_distillation | sparse4 / validating-inquisitive | R140 receiver-sleep alternating5,6 |

Node operational root:
`/localhome/local-rohing/orch_r140_classroom_pacing_20260916_attempt1`.
Local receipts: `research_notes/analysis/orch_r140_classroom_pacing_20260916/deployed/`.
Launch SHA256 `4ca0bae690a8d13971c9ac81907fe642db67c81072bd650e0443f93340d87fb8`.
Predecessor preservation SHA256
`6b29c99a3bff05da3245aabd468d14b7f9f73d02a75698be4370551d511cb170`.
Full custody archive SHA256
`47c100bcaf5b943fb91c79aeb6fd7a1c4619c0355ec15811d902ac57908b8925`.

First new publication and strict rendered-REQUEST exposure remain pending at
12:35Z. Inherited drain receipts are not new R140 exposure. No behavioral benefit
is claimed. The first operator preflight failed on a lease key before any intent,
signal or copy; original FORKS uses `hard_deadline_unix`. The corrected operator
binds its exact original hash and wall, and the failure log is preserved.

## Lease verification and current exposure

At12:39:57Z independently verified all eight live native command lines on A100
host `a4u8g-0147`, their GUARD files and exact SHA256-bound PLAN/LEASE documents.
Every current child, including classroom5/6/7, has the same deadlines:

- Hard end1790442300 = **September26,2026,17:05:00 UTC**.
- Lease end1790463900 = **September26,2026,23:05:00 UTC**.
- Original safety margin21600seconds = six hours.
- Relay hard end equals the minimum current child hard end and the minimum
  child lease-minus-margin. It does **not** exceed these bound child walls.

The inheritance chain rehashes original A100 FORKS
`7a5df97210f78ac64041aed57e695bf387e2cf350bd64453d6d902d1a4392c91`
and its pinned original R108 lease-metadata PLAN. That donor experiment also
has an earlier, explicitly1.5-GPU-hour run budget (September15,10:37:03Z),
not an earlier lease expiry: its lease end is the same September26,23:05Z.
Do not conflate the donor run budget or other nodes' walls with these eight
current A100 plans. No lease/configuration change, extension or signal was made
for this audit; an earlier relay stop is not required by the verified bindings.
Receipt `deployed/LEASE_AUDIT2.json` SHA256
`15ad6dfe2b1196e6f03b637c2da6d23c166e8d40c8fa171ef2eee9f3b3a3f96d`.

Read-only full TRAIN-chain audit `deployed/EXPOSURE_AUDIT2.json` SHA256
`e3fbf0493437acddf6444839dc099300541e0d8be0cbb245deb2fa25a932cacb`
verifies all native identities and unchanged predecessor custody. Snapshot:
zero new reservations, publications or strict rendered-REQUEST exposures;
A1006 has reached post-phase sleep774, while5/7 latest sleeps683/521 still
precede their phase heads. First exposure awaits eligible sender/receiver sleeps
and the receiver's natural REQUEST, not a wall-clock deadline or induced turn.
No held readouts were opened. Deployment is complete; uptake remains unclaimed.
