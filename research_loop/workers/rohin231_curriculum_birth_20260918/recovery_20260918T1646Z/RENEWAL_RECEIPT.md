# Pair renewal: completed bounded receipt

September 18, 2026, UTC. This final summary uses the native observation at
18:26:13 and parent observations at 18:27:09–10 recorded in
`CURRENT_CONTINUATION.json`; it does not imply a later live poll. Detailed
evidence was published in `c209708385ce041db1c881f08fb4f79e5472c7e3`.
Finalization changes documentation only; all remote loops remain untouched.

## Actual restoration and post-load parenting

| Evidence | Frozen, ovx4 GPU1 | Learner, ovx4 GPU0 |
|---|---|---|
| Native PID / startticks | 471737 / 9987073 | 493500 / 10070880 |
| Same journal | 30fa18c869b34fd496a2758a4a28e197 | 038f85cbde5c4abfb749ea4d59da6897 |
| Restored latest COMPLETE | 1760; sleep53; optimizer0 | 2463; sleep31; optimizer1440 |
| Actual WALL_EXTENDED | 1762 | 2465 |
| Actual LOADED | 1763 at18:21:32.808444 | 2466 at18:17:04.970794 |
| Parent PID | 2946721 | 2946722 |
| Preserved parent publication | 4513316e31de48cbbc73170faa0ce30c | 0e928f4d77584d9bbcd5235e3c1836ae |
| Exact text rendered after LOAD | REQUEST1766 at18:21:37.538757, message6 | REQUEST2469 at18:17:06.548974, message6 |
| Following ACT request → response | 1775 →1776 at18:23:02.106606 | 2476 →2477 at18:17:27.984582 |
| Bound stage / ACT event | 1778 /1779 | 2479 /2480 |
| First completed new sleep | COMPLETE1796; sleep54; optimizer0 | COMPLETE2544; sleep32; optimizer1488 |

Exact inbox-text matching, request/response pending hashes and ACT source hashes
are verified in `CURRENT_CONTINUATION.json`. Parents continue following the same
canonical journals and existing ledgers: no parent restart, recreated input or
native-PID rebind was required. Both also produced fresh feedback after the new
ACTs; publication of that newer feedback is not counted as rendering.

## Actual per-component bounds

| Component | Frozen | Learner |
|---|---|---|
| Native, adopted in WALL and actual REQUEST | 2026-09-30 18:00:00; unix1790791200 | Same |
| Timeout wrapper, actual argument | 1036903s from2026-09-18 17:58:06.336903 | 1036065s from2026-09-18 18:12:04.399952 |
| Wrapper limit calculated from launch receipt | 2026-09-30 17:59:49.336903 | 2026-09-30 17:59:49.399952 |
| Actual systemd RuntimeMax / entered | 1w5d1m38s /2026-09-18 17:58:06 | 1w4d23h47m40s /2026-09-18 18:12:04 |
| Systemd nominal ceiling from those readings | 2026-09-30 17:59:44 | 2026-09-30 17:59:44 |
| CPU parent expiry | 2026-09-30 18:00:00; unix1790791200 | Same |

Wrapper absolute limits are computed from journaled launch observations, not
independent exact kernel timer readouts. Existing five-second stop/kill grace
remains inside the native safe ceiling. The allocation authority is the user's
October1 date, not a new provider lease verification: conservative October1
00:00UTC minus the mandatory six-hour margin gives September30 18:00UTC. No
lease was purchased or extended. The current pair no longer uses the superseded
18:00/23:30 short experiment bounds.

## Measured gaps and preserved state

| Observed interval, seconds | Frozen | Learner |
|---|---|---|
| Old exit → new LOAD | 1409.421803 | 848.288534 |
| Old exit → first new response | 1444.394876 | 856.491420 |
| Last old response → first new response | 1557.304797 | 1081.247902 |

These are observed intervals, not a claim of zero gap or exact internal idle
time. Learner downtime includes a preserved first receiving attempt that failed
before model construction because a required preservation sidecar was missing;
the sidecar was repaired and a distinct freshly admitted attempt succeeded.
Frozen replay was not restarted for latency.

Both WALL states match every non-deadline field of their bound completed states.
Adapter, optimizer, saved checkpoint RNG, journal identity and pending working
state were preserved; unsaved resident post-checkpoint sampling RNG continuity
is not claimed. Receiving memory probes passed with zero optimizer-step calls.
Thirteen scoped CPU tests passed. No SIGSTOP, operator hold, rollback, historical
target rewriting or signal to another owner's process occurred.

## Actual learning/control and notification evidence

- Frozen recipe1794 and eligibility1795: R227 all-authentic, three NEW rows,
  no semantic exclusions, raw targets unchanged, weight updates disabled.
  COMPLETE1796 retains optimizer0 and the identical adapter. Zero dose is the
  preserved frozen scientific control, not semantic filtering.
- Learner recipe2494 and eligibility2495: R227 all-authentic, three NEW rows ×16,
  zero old rows, no semantic exclusions, raw targets unchanged. COMPLETE2544
  advances1440→1488; cycle33 was already running at the finite observation.
- Actual sleep notices are1792/cycle54 and2492/cycle32. `TO_LEIBNIZ.md` supplies
  the restored epochs and completed ages; external every-sleep enrollment
  acknowledgment remains unverified and belongs to Leibniz.

No further pair renewal work or output polling is required for this receipt.
Both natives and both parents were active at the stated observations. Private
transcripts, full working states, host addresses and credentials are not included.
