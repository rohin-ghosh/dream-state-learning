# Independent bounded normalizer review

Reviewed 2026-09-16, read-only except this audit directory. Verdict: **PASS for the lossless JSON representation helper; runtime input recording is not established by these helper tests or the supplied CPU proof.** No concrete loss-of-content defect found in the reviewed implementation. This is not a launch gate or a review of Hilbert's unfinished recovery integration.

## Exact scope and validation

- `gpu/orch_r140_grid_json.py` SHA256 `7a9d95d996fc6854b1a8cf19819850fc7d36d836cc857c9bdf3286245bb251e6`.
- `tests/test_orch_r140_grid_json.py` SHA256 `f61ab29b3526e10bc742110f7d1c00762139c9bca9dcdc83cf55f96771256534`.
- Supplied `EXACT_FAILED_CALL_PROOF.json` SHA256 `3d2ffa71f569608b094a705ae6be6802164bdc72f022fa0ccc592bc7e5f096d6`.
- Independently ran `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_orch_r140_grid_json -v`: **14 PASS**.
- Wrapper-only node hash check of historical `F4/calls/N04456.json` matches proof: `d4a7f4885084c8ca56d3770a45d0c67d80c8f4a94ad1168260a5ec6e7ade00dd`. No replay, tokenizer/model load or provider call performed by this review.

## Findings

1. **Lossless at decoded JSON/message-content level.** Lines 37–50 accept only exact canonical ASCII-escaped dict/list JSON; ambiguous duplicate keys, nonfinite values, scalars, noncanonical spelling and unpaired surrogates are not transformed. Unicode is re-encoded, not summarized or clipped. Lines 83 and 89–102 demand exact recovery of original message objects, including canonical content strings. System/assistant messages and all non-content message fields are preserved; caller input is deep-copied. This does not assert identical tokenization/model behavior or preservation of arbitrary outer receipt-file serialization bytes.
2. **Bounded overflow behavior.** Already-fitting prompts remain unchanged; only overflow prompts are considered. Remaining overflow raises rather than truncating or reducing the generation cap. Flat token-list validation avoids treating a tokenizer mapping as a tiny token count. Supplied CPU proof reports 16020 + 384 = 16404 (20 over 16384), changed to 8338 + 384 = 8722 (7662 spare). Proof source pin matches reviewed source. Actual tokenizer computation was not independently rerun here; the 14 tests use a synthetic character-count tokenizer.
3. **Runtime recording is an integration obligation, not a helper capability.** The helper returns `actual` messages plus hashes/indices; it does not dispatch or persist a CALL record. The supplied proof is expressly CPU-only, not an executed runtime-input witness. At review, the bounded GPU source search found no normalizer call site beyond this helper. Concrete integration requirement: generate from the returned messages, record those same actual messages and normalization metadata in the new call receipt, and retain/recover the originals without overwriting the failed receipt. A recording-only stub regression should join recorded messages to the tokenizer/generate input and assert the hashes/recovery match. Do not label an unmodified original prompt as the input actually sent.
4. **Metadata claim boundaries.** `historical_model_calls_replayed=False` is a fixed helper field, not independent proof of orchestration behavior. Likewise lossless JSON values do not mean exact-context continuation. Report this as reversible serialization/representation change with changed tokens, not identical model context; preserve historical charge/disposition records in the separate recovery seam. No safeguard/provider rerouting is implemented by this helper.

No source changes, signals, launches, model/provider calls or shared-ledger edits. No raw held content, thinking or transcripts exported.
