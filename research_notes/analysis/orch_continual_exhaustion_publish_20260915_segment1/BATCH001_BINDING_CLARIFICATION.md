# Batch001 group1: response validation failure, not HTTP transport

Offline native inspection on 2026-09-15 at 06:26 UTC found six review records.
All six target hashes join the immutable packet; all six raw-call hashes match.
Only response ordinal 0 has a mismatched `student_prefix_sha256`.
Response ordinals 1–5 have all three bindings correct. No response body is copied here.

Native scope: `/localhome/local-rohing/orch_continual_exhaustion_publish_20260915_segment1/orch_continual_exhaustion_feed_batch_001`;
compare `REVIEW_PACKET_1.json` with `PROVIDER_UPLOAD/batch_001_1/reader/result.json`.
Main independently replayed pinned validation: `ValueError: review_hash_mismatch`.
The controller's generic transport/subprocess failure label is not a diagnosis.
Preserve FAILED/raw/charged reservations; no retry, salvage or relabeling.

Prospective CPU-only proposal: immutable dispatch registry assigns integer row keys;
model returns keys and semantic/evidence judgments, never opaque hashes. Host code
requires exact unique key coverage and the original registry digest, binds hashes,
then runs the unchanged full-text, literal evidence, gold and branch validation.
This prevents SHA transcription errors; it cannot guarantee that a reviewer reasons
about the intended row. Existing evidence and semantic checks remain necessary.
New unused source: `gpu/orch_continual_exhaustion_publish_keyed.py`.
No hotpatch, new provider call, ledger reset, new budget or failed-review rehydration.
