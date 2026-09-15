# R118 shared-era parent delivery — 13:00 hourly entry

As-of: **2026-09-15 13:00:05.656651 UTC**. Cumulative SHARED era after actual common initialization (12:23:54 UTC), not a full-hour rate. Selection: original branch-root queued requests with payload cycle at/after released next cycle; only publications/receipts observed by cutoff. No provider calls, retries, queue writes, changes to cadence, taxonomy, or old verdicts.

Counts below are **COMPLETE / MISSING / SILENT / pending**. Native MISSING means recorded absence/failure disposition, not consumed guidance. COMPLETE means receipt-bound guidance, not usefulness, semantic change, or learning.

| Branch | Shared cycle start | Published C/M/S/P | Native C/M/S/P | First–last publication UTC |
|---|---:|---|---|---|
| F1 | 7 | 1/7/0/0 | 1/7/0/0 | 12:27:46–12:36:35 |
| F2 | 10 | 4/2/0/0 | 4/2/0/0 | 12:35:59–12:44:34 |
| F3 | 21 | 3/2/0/0 | 3/2/0/0 | 12:30:56–12:39:38 |
| F4 | 8 | 2/3/0/0 | 2/3/0/0 | 12:29:32–12:59:51 |
| **Total** | — | **10/14/0/0** | **10/14/0/0** | **24 requests** |

## Recorded COMPLETE intervention classes

Published and native COMPLETE class distributions match. Each exact recorded string below occurs once; these are parent metadata, not new semantic judgments.

- F1: `record_vs_current_observation` × 1.
- F2: `check_consequence` × 1, `evidence_reading_and_check_purpose` × 1, `expectation_before_computing` × 1, `verbatim_repetition_generic_reflection` × 1.
- F3: `reflection_grounding_ran_vs_reasoned` × 1, `run_vs_reason_verification` × 1, `verify_read_vs_run` × 1.
- F4: `premise_verification_before_planning` × 1, `template_plan_over_fabricated_observation` × 1.

## Provenance and boundaries

- F4 includes recovered P0036: the repair reconstructed its receipt at 12:36:48 UTC without redispatch; its old observation clock is explicitly an upper bound from the recorded failure, not a contemporaneous acceptance timestamp. Actual N00521 at 12:38:52.438871 UTC contains the exact guidance; SHA-256 `33b7dc56cb56dc36aba7b5ba9fda758a7763d93acc1002517cdc7d5de896065b`. Therefore totals include nine ordinary COMPLETE receipts and one explicitly reconstructed/applied receipt.
- F1 MISSING receipts bind request ID/hash but omit response hashes. Linked single-attempt publications are verified separately; no native response-hash certificate is invented.
- All ten COMPLETE publication archives rehashed on node; request/response/native joins checked at the available binding strength. Full row references, immutable activation/release/common hashes and configuration eras are in the JSON receipt.
- Broker source SHA-256 by era:
  - F1: `46f4118be681920c97f18bdb1c1c5b6231d1ce75873246f2f6a1dea36f86bdf7`, `d7ab85e550994ba3bced3e54277fd184eec0d73f678f2ef653dd55152f0c8d86`
  - F2: `46f4118be681920c97f18bdb1c1c5b6231d1ce75873246f2f6a1dea36f86bdf7`
  - F3: `46f4118be681920c97f18bdb1c1c5b6231d1ce75873246f2f6a1dea36f86bdf7`
  - F4: `46f4118be681920c97f18bdb1c1c5b6231d1ce75873246f2f6a1dea36f86bdf7`, `9bca74e82d5549eacd6d16e763fcf43e5b237f56c07298a24d07bc3f0bc552b5`

## Published MISSING codes

- F1: `provider_error_or_turn_limit` × 7.
- F2: `parent_tag_class` × 1, `provider_timeout` × 1.
- F3: `provider_error_or_turn_limit` × 1, `provider_timeout` × 1.
- F4: `provider_exit_failure` × 3.

These are existing transport/validation codes, not newly diagnosed safeguard categories. No old failure was rescored. Raw provider/child text stays on node.
