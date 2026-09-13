# L2 public-record diagnostic: external terminal custody

**Date:** 2026-09-13 UTC  
**Status:** custody sealed before score inspection  
**Run root:** `/localhome/local-rohing/astra_diagnostics/l2_public_record_20260913_attempt1`

## Terminality check

A read-only external check selected only processes whose executable name began
with `python` and whose full command contained either
`astra_l2_public_record_20260913` or `l2_public_record`. It returned no matching
process and exit status zero. This corrected an earlier unusable `pgrep -af`
check whose search expression appeared in the checking shell's own command
line.

No scientific score or arm-result field was read before the custody values
below were recorded.

## Whole-root custody

- File count: **529**
- Whole-root digest: **`e93f957419bcb546c37291df4783cc8593fc27a8f37a82fa3fcde0cdf822c87e`**
- Digest construction: locale-C path sort over every regular file beneath the
  run root, followed by `sha256sum` of each file and then `sha256sum` of that
  ordered stream.
- `FINALIZED.json` SHA-256:
  **`a4f9ebfd99679ec01e5330ae87d17e522bcc5b698c10fbcc62a46b24ef957e62`**

The queried generic keys `schema`, `status`, `finalized_at`,
`scientific_claim`, and `root` were absent (`null`) in `FINALIZED.json`; no
other field was inspected at custody time.

## Interpretation boundary

This is an exploratory base-start, two-SLEEP public-record diagnostic. Custody
does not make it the authentic child-authored vertical experiment and does not
authorize claims about self-learning, parenting, recurrence, lifetime
improvement, or parametric mediation. Independent reduction must first match
the whole-root digest above.
