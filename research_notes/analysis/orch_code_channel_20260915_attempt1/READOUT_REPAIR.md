# Non-material offline replay repair —2026-09-15 01:38UTC

First interim reduction stopped with `raw_replay_mismatch:feedback` before
producing any summary or admission. Exact mismatch: TERSE position13,
CALL_020 SOURCE has failed observed tuple(3,2,1,4), serialized by the native
JSON writer as list[3,2,1,4]. Fresh CPU replay correctly regenerates the tuple.
Both native and replay outcomes are false, expected[4,1,2,3] unchanged.

Repair only serializes replay feedback through the same JSON round trip
before comparing to serialized raw receipts. This does not relax oracle
comparison or action grammar: tuple-vs-list can still fail the native test.
Raw outcomes/targets/token IDs/neutral prefixes stay unchanged. New regression
test constructs exactly this tuple-valued failure and verifies failure remains.
Native source/archive is immutable; only separate offline reducer/verifier
files change. Failed interim_reviewed directory preserved, no native retry.
