# Bounded continuation status

**Finished and released at21:04:53.561 UTC**,16m02.561s into the shared window.
Exactly two additional attempts used. Attempt3 preserved6 measured timing cases;
attempt4 preserved11, with warmups excluded. GPU6 is empty and both owned units
are stopped. No additional launch is permitted under this authority.

Actual warm HF-call rates from attempt4: **23.189 tok/s** at2k input/256 output;
**5.026 tok/s** at12k/256; batch2 at2k/256 is**19.633 per life /39.266 aggregate**.
No measured case reached40 per life. At12k,39.385 of50.935 HF seconds lie outside
the instrumented model-forward intervals; the specific operation is unproven.

See `../attempt4/PROFILE_REPORT.md`, `../attempt4/RESULTS.json` and
`../attempt4/GPU6_RELEASE.json`. Full matrix/sleep are explicitly incomplete:
the owned runner was stopped after valid trials for the requested GPU handoff.

## Historical window and dispatch

User authorizes at most two additional attempts (attempt3 and, only if needed,
attempt4), within one total window **2026-09-17 20:48:51–21:08:51 UTC**. Preparation
and any bookkeeping recovery consume the same window; no budget reset per attempt.
No model, measurement, benchmark or lease change; no installs or live child writes.

The repaired receipt signature and its CPU regression are retained. Only the
runtime admission/deadline controls are tightened to the shared absolute end.
Every attempt requires fresh source pins, CPU/provenance gate and strict UUID/minor
plus FD/capacity/lease admission. Prior attempts remain preserved.

Status: attempt3 persisted8 timing receipts (6 measured cases plus2 excluded
warmups), then stopped on a false rejection of a sampled pad-token ID. Those
receipts include warm singleton256-token HF-call throughput of23.239 tok/s.
That is actual synchronized timing, unlike attempt2's post-load timestamp window.

The accounting-only repair passed22 CPU regressions and fresh provenance checks.
Attempt4 launched at20:58:23 UTC after fresh privileged FD/capacity/lease admission
and actual strict device/UUID validation. Its systemd maximum is617 seconds,
bounded by the same21:08:51 UTC deadline. Initial real timing receipts are saved.
Both additional attempt slots are consumed; there is no further GPU attempt under
this authority. The19.96 tok/s window from attempt2 remains explicitly caveated and
is not used to support a40 tok/s claim.
