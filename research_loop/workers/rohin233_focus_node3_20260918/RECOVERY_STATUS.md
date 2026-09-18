# Node3 kept-life recovery — 2026-09-18

Initial diagnosis cut16:50:11UTC. The eight kept lives exited with code124,
5–20 seconds before their own configured operator hard walls. The guarded
launcher runs `timeout` with a ten-second margin; its subsequent
`native_failed_preserve_no_retry` error is the wrapper's refusal to retry.
The inspected native logs contain no child exception or OOM evidence. Node3
uptime starts September13,10:02:17UTC; no reboot occurred in this interval.
At16:46:09 all eight devices had1MiB used and no compute processes; available
host RAM was987GiB. GPU activity is not lease evidence.

The existing user-confirmed/Fable-reported, host-bound lease receipt specifies
September26,03:03UTC. No lease extension or purchase is performed. New recovery
budgets are finite twelve-hour horizons from each preparation, additionally
capped by the existing reservation and six-hour physical-lease margin.
The former six-hour experiment budgets are not reused.

Scope is the five exact `r213_r226_caption_*_fork` lives on0/3/5/6/7 and
`r213_math_a`, `r213_math_b_fork`, `r213_math_c` on1/2/4. No obsolete/siege root
can enter the recovery allowlist. All original journal records remain; each
failure's stream/checkpoint/control is copied privately with SHA manifests.
Recovery appends the already-established saved-boundary reconciliation event,
restoring coherent adapter/optimizer/RNG plus saved working state in the SAME
journal. Post-boundary updates, outputs and inputs are inventoried as gaps,
not advertised as exact resident continuity. No raw targets/binaries are public.

Six focused recovery CPU tests and the37-test owned suite pass. Receiving
six-test checks pass. Per-life archive replay, checkpoint integrity and
resident-runtime tests are required before one-at-a-time dispatch. GPU0's
first CPU preflight rejected an offline inbox namespace mismatch before any
live journal mutation or launch; that attempt was retained, and replay now
uses the existing confined namespace rather than rewriting historical inputs.

This initial cut is NOT a LOADED claim. Actual subsequent LOADED/REQUEST/ACT
and renewed service receipts will be recorded separately. Existing learning
recipes/filter mismatches are retained, not silently upgraded. Parent workers
resume recorded turns, not epoch openers: normal response/checkpoint cadence,
changed parent intervention after three completed cycles, genuine human
priority. Main owns P3/scoring; node3 restores only its own feedback relay.
