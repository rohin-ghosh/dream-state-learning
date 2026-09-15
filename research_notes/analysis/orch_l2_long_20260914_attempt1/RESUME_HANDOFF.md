# Exact LONG continuation evidence — 2026-09-15T00:13Z

`RESUME_ORIGINAL_001.tar.gz` is a read-only archive of the actual remote
LONG/cycle1/experience directory, all three LONG queue request/response pairs,
LONG learner/parent call ledgers, and original shared deadline. It contains no
global SOURCE or readout. SHA256:
`cb57a948f9e95e9fc7e3e05f39bfa2db4801ab6084e82ea61ff03ecf0272a7fb`.

`RESUME_STATE_001.json` is derived operator recovery evidence, NOT parent input
or a replacement run receipt. SHA256:
`daf92dd20bff3b425a6f8c42e49d9f7cd9261680de22838c502d2321a1908423`.
Every archive member is hashed there. Original raw provider result strings,
model usage and six provider reservation records are also retained with hashes.

## State at interruption

- Cycle1 experience; next episode index4 (fifth episode), turn0.
- Four completed episodes,16 child calls,2 task successes, zero sleeps/updates/readouts.
- Two coaching decisions consumed, two remaining. Three parent queue requests
  include one semantic review, not three coaching decisions.
- One delivered message,108 native tokens; one actual exposure,108 tokens.
- Own full history contains episodes0–3. Its bounded projection equals the
  actual0002 request's history exactly; sleep history is empty.
- Question offsets: episode0→0,1→4,2→4,3→2,4→0. Historical attempted turns,
  spoken world(1,0), decision records and failed request are saved.
- Original deadline remains1789472611.845884; no new12h clock or cap.
- Existing six actual provider reservations remain consumed (utility+main
  for each0000/0001/0002). No model retry, parent dispatch or new charge occurred.

## Resume boundary for Main to relay to SHORT

Original0002 request is already reserved and generated, but not delivered.
Its long_request SHA is
`536b52354f68c11e93274bea14fea7c6a350efaa0e2974572cd078a4ceff7949`.
It records remaining_decisions=3 BEFORE that reservation; current remaining
quota is2. Do not regenerate a new request with quota2 and call it the same
request. Recovery needs the original bound request and saved generated result,
then ordinary message validation/token counting and a separately logged
delivery. Do not invoke a fresh before_turn that consumes a third decision.

SHORT owns shared parser import, response recovery/provenance and partial-stage
resume. LONG owns restoration of its counters/history at that boundary. The
present JSON is evidence ready for that integration, not a claim that the
current hook/guardian already supports resuming. No new generic driver exists.
Completed episodes/calls/reviews and original failures must stay byte-identical;
no replay or retrospective rescore of the first four episodes. Do not reset
ledgers, discard failed requests, or silently overwrite queue error receipts.

The first parent advice and fabricated child observations remain untouched.
PUBLIC SYSTEM omission is disproved; no exposure repair is authorized here.
No causal gain, acceleration, cohesion, retention, reflection or compiler result
exists. Runtime remains stopped on the separately recorded transport failure.
