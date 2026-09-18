# R224 parented-caption scorer adoption

[Builder] 2026-09-18 07:40 UTC. This non-material repair adopts free-form caption
extraction and feedback without changing the top-50, relevance or novelty
evaluation rules. Main owns this operator directory and scorer endpoint;
Leibniz owns the caption libraries; Turing owns the running learner/parent.

Nine focused CPU tests and two subtests pass for a complete legacy-state
export and bounded local socket handover. Export verifies every actual child
origin, exact raw text, serial attempt order, an unbroken BEFORE/AFTER chain and
all seen ACT hashes. It refuses incomplete dispatches. No old ACT is rescored.

The learner is not stopped or paused. A local bridge holds new requests during
the scorer replacement; it never retries a request after sending it. A handover
timeout reports an unknown outcome, not a fabricated judgment. The old scorer
is retained until a replacement load is verified. Existing state, novelty,
reference panel bindings, rank rule and endpoint access restrictions remain.

## Actual adoption

The replacement scorer loaded at **2026-09-18 07:45:56.620 UTC**; restoration
was verified and the waiting proxy released at **07:45:56.668 UTC**. New scorer
PID990782 and bridge PID990334 serve the original learner PID237705. Only the
old scorer PID224224 was retired, after the replacement was verified. No learner
signal or pause occurred. The original scorer deadline remains in force.

All 14 processed ACT hashes, including unparsed attempts, were retained. Measured
post-restore game and policy hashes match the exported state, not just aggregate
counters. `receipts/LOADED_VERIFIED.json` and `receipts/EXPORTED.json` bind those
facts; neither contains private reference panels. The tested library archive is
`75158d7ed87fb2c2165017a0d59bbe0592d9c7659235e57233e0e245c05e9b66`.

The first new actual ACT, RESPONSE1270, completed without killing the run and
returned clarification feedback with `next_stage=ACT`. It was **not scored**:
the scene was labelled in Chinese, which the current selector did not recognize.
This is not a judge rejection or a successful caption. A future-only selector
repair is assigned; this old result will not be resubmitted. Metadata-only
receipt: `receipts/FIRST_NEW_ACT.json`.

The old pinned learner client does not yet implement same-opportunity ACT
retries. The scorer returning the requested next stage does not establish that
the learner schedules it immediately. Nor does this service adoption establish
continuous unparented or frozen-base cohorts, or a matched learning result.
