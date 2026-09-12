# SEQ-088 — bounded public-check production

Native paired production completes from immutable5d4c5608 on node3GPU1.
Eight constructed observed board exercises per arm, frozen local Qwen base,
no adapters, no fits. Same generation seed and caps; cards differ in content
and length (process47tokens, format44), so compute equivalence is not claimed.

| Endpoint | Process coaching | Active format control |
|---|---:|---:|
| Strict-schema cases with grounded citation |0/8|1/8|
| Schema-valid records |0/8|8/8|
| Invalid citations inside schema-valid records |0|7|
| Structurally clean grounded records, excluding lesson truth |0/8|1/8|
| Actual generated token IDs |392|313|
| Actual prompt token IDs |2104|2080|

All16 generations stop normally with raw native token/stop metadata; no
length truncation. The zero process invalid-citation count is NOT evidence
of no factual errors: all its records fail schema validation first because
coordinates are numeric strings, while the checker requires integers.
The common task states one-based coordinates but does not explicitly specify
integer coordinate types. Do not infer inability to find duplicates from
that strict-schema result. Independent public-content diagnosis is pending;
any numeric-string normalization must be explicitly post hoc and cannot
replace these original primary counts or approve lesson text for training.

The16 records are one small prompt-conditioned production comparison, not
three learner seeds, weight persistence, P1 internalization, H1/H2, or a
developmental campaign result. No output has been trained or promoted.
Free-text next-check reminders remain separate from machine-checked citations.

## Verification and cost

Native source/model/preparation validation and semantic report replay pass.
The reported controller elapsed276.672446s is retained and range-checked,
not recomputed by the reducer; cold-start/verification outside it is extra.
Both worker cleanup receipts pass; controller118954 is absent and Main's
fullGPU1 XML/CUDA/queue check passes. The native close routine stops owned
EngineCore119213 (process) and120162 (format); no unrelated process or manual
kill is involved. A leaked-semaphore warning is recorded, not hidden.

Main's first external capture assertion compared the replay without the
controller-added elapsed field to the full report. That capture check failed,
not the experiment. The corrected capture explicitly preserves and validates
the runtime field, then confirms exact semantic equality and release.
The initial raw capsule is retained separately, not overwritten.

Verified terminal capsule SHA256
`7935c254ac16cfbf33c8cbf9386e9a947ec9b02e50d28e9f03987efb3bbbda89`;
initial pre-audit capture SHA256
`aa1d516ebdc3a87673fc65a0a5def1f2598521272d8101b4729e0e263af12ce2`.
Both capture script versions and final capsule accompany this memo under
`receipts_20260912/`. Preserve actual run/preparation roots on node3.
