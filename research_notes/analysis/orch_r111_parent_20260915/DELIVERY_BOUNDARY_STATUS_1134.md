# Route delivery / boundary status — 2026-09-15 11:34 UTC

For Main and Hubble. `send_input` is not exposed in this session; this file and
the worker/COORD notification are the actual communication, not a claimed send.

Fresh wrapper observation at 11:34:39 UTC: F1 actor356208 exists, cycle4 started,
3 cycles complete; 1 COMPLETE, 34 MISSING, 0 SILENT. A1 actor459948 exists,
cycle2 started, 1 cycle complete; 7 COMPLETE, 6 MISSING, 2 SILENT.
Both immutable live plans still use 120-second parent waits.

Hubble's 11:32–11:34 diagnostic identifies nine F1 provider exits as safeguard
refusals, not demonstrated latency. No request replay, rephrasing, safeguard
bypass, or effort reduction is authorized as a remedy for those refusals.
The prospective 600-second consumer / 570-second provider budget is preparation
for transport latency, not a claim to repair refusals. Parent effort remains max;
head effort remains max. Distinct wait eras invalidate a parent-model-only match.

Live v3 does not poll STOP_AFTER_CYCLE. Actor SIGTERM alone causes supervisor
recovery. No controller is armed, neither actor has been signaled, neither plan
has been edited, and the shared coordinator has not been initialized.

Preparing a reservation-lock boundary: after a final post-sleep readout completes,
hold the existing ledger lock, let original cycle completion bookkeeping finish,
then bind the latest checkpoint/optimizer/carry and verify zero next-cycle
reservations before an identity-checked supervisor+actor release. Race losers
release the lock and leave the life running. Any empty successor START must be
explicitly preserved/resumed rather than skipping task IDs or resetting quotas.
