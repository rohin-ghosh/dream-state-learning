# PCFL physical-carrier intercept receipt v4

Date: 2026-09-07

Status: **partial serialized-adapter intercept only; positive E3 spend remains
blocked.** Supersedes v3 after adopting the independent v3 re-audit at
`research_loop/advisory/20260907_pcfl_physical_intercept_receipt_reaudit_v3.md`
(SHA-256
`57742e6e6ae106945bf5cbd5a4218004cc129164b0a233e83f60405b0049ac07`).

## Final parser/profile repairs

The exact namespace now accepts only canonical decimal layer spellings
`0,1,...,27`; aliases such as `00` are rejected. The raw emitted receipt has
schema `pcfl_physical_carrier_intercept_receipt_v4` and includes the entire
validation profile: namespace template, layer count, Qwen dimensions,
module/branch map, and path-specific expected ranks/dtypes. Thus raw output
states which configurable profile performed acceptance rather than leaving it
to surrounding prose.

Script:
`research_loop/advisory/pcfl_crossover_receipt.py`

SHA-256:
`418ccb837891f9b6cad91b877ec7052af1fab0ce2c9525a10be610cb0455ad20`

Tests:
`research_loop/advisory/test_pcfl_crossover_receipt.py`

SHA-256:
`9ff6252c1cd0d7fa925be442d5560395215e209e3c355bc25a0f5d677aeb580e`

All 13 checked-in CPU tests pass, including the new `layers.00` attack. The
prior fresh reviewer additionally mutated all 14 module/side dimensions and
found every mutation rejected. The exact-profile validator was rerun read-only
against the reported rank-8/rank-16/rank-64 artifacts. It emitted the v4 schema
and pinned profile and reproduced file hashes and element totals. The external
bytes and complete raw stdout remain outside the local packet, so this is an
author-observed result rather than independently replayable local provenance.

Machine-readable transcribed summary:
`research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v4.json`.
It explicitly records that provenance limitation and does not masquerade as raw
stdout.

## Exact conditional intercepts

| rank | reported serialized adapter file | exact-profile element count | expanded bytes required for adapter-file ratio `<.50` | required bytes/token at 8x16k |
|---:|---:|---:|---:|---:|
| 8 | 80,792,096 B | 20,185,088 | 161,584,193 | 1,232.7896 |
| 16 | 161,533,192 B | 40,370,176 | 323,066,385 | 2,464.8009 |
| 64 | 645,975,704 B | 161,480,704 | 1,291,951,409 | 9,856.8070 |

These are conditional serialized-adapter-file numerator intercepts. They are
not complete life/actor state, runtime residency, actual denominators, actual
rates, a mathematical impossibility proof, or a measured compression failure.
They and the absence of a qualifying generated-load receipt support one action:
do not spend on the proposed 8x positive physical-compression panel.

## Unchanged complete E3 gate

Positive E3 execution still requires prospectively sealed and SHA-bound raw,
canonical, and deterministic expanded artifacts at every load; exact bytes and
authorized pinned-tokenizer counts; complete life/common auxiliary census and
growth laws; serialized/resident/simultaneously-retained coordinates; actual
rates; denotational equivalence; and at least three useful loads beyond the
honest crossover. Until that packet exists and passes independent review,
physical all-layer-LoRA compression is a later-scale objective. Semantic-code
compression and LoRA transport remain distinct nearer claims.
