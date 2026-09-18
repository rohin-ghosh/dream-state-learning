# C0 reading: additive, source-bound secondary object

The existing C0 math life and original onboarding parent remain unchanged.
The named pre-reading baseline is `C0_BASE_20260918T081045Z`, completed08:10:59UTC,
sleep62/optimizer5244; its manifest-only commit is
`51440f045749e8263d5c8dd7848b0b4de03448d8`. No further snapshots are created here.

The reading publisher started08:14:58.951649UTC, PID2729920/start94773801.
C0 is PID2561156/start94173182; its original math parent is
PID2561001/start94172764. The service is finite, identity-bound, CPU-only and
operator-authored. It cannot signal, restart or reconfigure a learner.

## Schedule

- First reading after completed sleep64: the verbatim cab-driver excerpt and
  "Read this. Then tell me, in English, how it makes you feel."
- After that question is actually rendered and answered by a source-bound ACT,
  wait for its subsequent completed sleep. Ask how the child feels about the
  story now and what it remembers; permit "I do not remember," supply no story
  facts or answers in this memory prompt.
- Every three completed cycles, advance through retelling feelings, noticing
  the previous feeling report, thinking about the child's own situation, then
  reflecting on self. Math remains active between these secondary turns.
- Protocol step6 applies throughout: observed non-English script or exactly
  repeated wording gets one plain English correction; a second occurrence
  moves to the next excerpt. No answer/feeling receives a score.
- Publication, REQUEST render, ACT source, and completed-cycle ledger are
  distinct receipts. A subsequent ACT is not proof of following the prompt.
- The parent does not remove or pin context. Memory observations record whether
  the full story remains visible and make **no adapter-retention claim**.

`PROTOCOL.md` is an exact copy of the published P7 protocol, SHA256
`79af72fea1847a249a0c200b872be8f259cd0db357c36089e81ff3e0d2a9bac0`.
`reading_parent.py` and bundled `c0_receipt.py` are the exact deployed source
bytes. The latter is the existing C0 identity/record helper; its historical
R225 `publish` CLI is not part of this schedule and must not be rerun.

## Observation and publication boundary

`FIRST_READING.public.json` reports the actual captured observation time,
publication and render state. It deliberately omits child raw text, original
private observation paths, and live process environment. It does not promote
pending publication to delivery or scheduled objects to actual compliance.
`reading_receipts.py` is a read-only projection of existing receipts, not a
process controller. The original private observation stays local and untracked.

Published code/receipts do not replace the running service. The original math
parent remains the same process. The named checkpoint bytes and all other bulk
archives are excluded from this publication.

## CPU tests

Run from this directory:

```sh
python3 -B -m unittest -q test_reading_parent test_c0_receipt test_reading_receipts
```

These tests need only the standard library and create no GPU/model process or
live publication. They check protocol bytes, cycle spacing, post-sleep recall,
retry/advance behavior, actual-record hashes and public-receipt data minimization.
