# Retry1 follow-through, September 18, 2026

Scope: retain exclusive CPU-side ownership through actual retry LOAD and genuine
parent REQUEST-to-committed-ACT evidence. Preserve waiter3671383/start186769383
and Main's controller658049/start32833295. No native restart, source change,
signals, second replay or duplicate publication.

Actual 20:10:31 UTC check: the same controller remains runnable in CPU replay;
no dispatch or exit receipt. The existing waiter is waiting for an actual retry
LOAD. No new parent, rendered Tool notice or R227 sleep receipt is claimed.

[Builder] 2026-09-18 20:11 UTC — Added read-only `p3_retry_receipts.py` and
eight focused regressions. Combined retry suite: 37 tests PASS. The observer
reuses the existing verified rendering reader and committed-ACT correlator,
follows the exact LOAD hash, and advances a local private cursor through at
most 40 new records per invocation. It does not repeatedly reread full journal
history. Raw text remains in a local private evidence cache, not public output.

Future evidence will separately show:

- Exact current native incarnation and parent process identity, not only LOAD.
- Original-ledger model request/response hashes and actual publication receipt.
- Exact parent source bound to rendered REQUEST and later committed ACT;
  publication alone is not delivery and ACT is not proof of improvement.
- Retained Tool notice `04a8952f5a84794f257f24e1765489d7` and its exact source hash.
- Actual SLEEP_RECIPE, TARGET_ELIGIBILITY and COMPLETE records if naturally
  observed; no inference of R227 adoption from source bytes or plan alone.
- Any technical row exclusions, without relabeling them semantic filters.

Command after the existing waiter writes its actual retry binding:

```sh
python3 -B research_loop/workers/rohin233_recovery_20260918/p3_retry_receipts.py
```

Public output is `P3_RETRY_ACTUAL.json`; private cursor/evidence is
`P3_RETRY_EVIDENCE.private.json`. These files are not fabricated in advance.
An attachment failure permits only tested CPU helper repair. A native failure
is reported to Main immediately, not independently retried.
