# LONG lossless envelope helper — 2026-09-15 UTC

Non-material transport repair only. Main relay to SHORT; no shared files edited.

```python
from gpu.orch_l2_long_envelope import parse_json_envelope
parsed = parse_json_envelope(provider_response['result'])
```

Signature: `parse_json_envelope(text: str) -> dict`.
Helper SHA256: `82b0867480d50c2073d4149c7139ae3a9ecda64397e0629a5f37bb69f37f3ec3`.

Accepts an ordinary JSON object or one complete lowercase `json` Markdown fence,
with JSON whitespace outside. The only field normalization is top-level
`distillation_for_rohin` to `distillation` when the canonical key is absent.
Both keys present (even equal), duplicate keys at any depth, extra prose,
multiple envelopes, malformed/non-object JSON and non-JSON constants raise
`ValueError`. No substring salvage, teacher rewriting, rubric/gate changes,
model invocation, filesystem write, dispatch, or budget charge occurs.
Caller must retain provider raw bytes/status/usage and validate its existing
task schema and provider success. This helper does not grant acceptance.

Six CPU tests pass with `python3 -B -m unittest tests.test_orch_l2_long_envelope -v`.
They read the actual preserved 0001/0002 provider envelopes, check unchanged
raw-file hashes, equal entire parsed semantics after the sole key rename, and
identical UTF-8 message/reason/distillation bytes. Actual 0001 review decisions,
hashes and rationale stay intact.

SHORT owns broker import and provenance-bound recovery of saved provider
results, not a new dispatch. Original queue error responses must be retained,
not silently overwritten. Do not rescore/replay the first four episodes.
This helper does not retrospectively admit rows or alter gates. Resume must
distinguish already delivered 0000 from generated-but-undelivered 0002,
preserve both reserved coaching decisions, and consume 0002 without charging
it again. LONG is preserving its exact stage/history/quota receipts separately.

No exposure repair: actual first parent observation includes neutral PUBLIC
SYSTEM verbatim, including opaque identifiers and no simulated turns. Original
opaque-label advice remains a protocol-quality counterexample, not an
omitted-SYSTEM explanation or single-episode causal result. Missing full RICH
GUIDANCE is a separate possible limitation, outside this repair.
