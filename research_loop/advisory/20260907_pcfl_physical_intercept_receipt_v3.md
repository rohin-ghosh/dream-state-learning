# PCFL physical-carrier intercept receipt v3

Date: 2026-09-07

Status: **partial serialized-adapter intercept only; positive E3 spend remains
blocked.** Supersedes v2 after adopting the independent re-audit at
`research_loop/advisory/20260907_pcfl_physical_intercept_receipt_reaudit_v2.md`
(SHA-256
`f88c709f0eff9beac55cb28170adebc04ae7cdfe0b3d9ff6804c4229e62b9cf9`).

## Repairs adopted

The validator is now pinned to the exact declared Qwen2.5-7B PEFT layout:

- namespace `base_model.model.model.layers.{0..27}`;
- `self_attn` for q/k/v/o and `mlp` for gate/up/down;
- hidden size 3,584, KV output 512, intermediate size 18,944;
- exact module-specific LoRA A/B shapes;
- explicit expected rank and fp32 serialized dtype;
- complete 28-layer, seven-module, A/B pairing;
- expected total element count and exact contiguous data partition.

The checker rejects invented prefixes/branches and dimensionally tiny fake
carriers. Machine-readable fields no longer claim to observe mounted runtime
residency, simultaneous checkpoint retention, a common sidecar, or a complete
actor/life numerator. They report only header-derived serialized tensor
payload, the adapter file, the discovered config sidecar, and their known-file
subtotal. Actual runtime and complete auxiliary coordinates remain absent.

Script:
`research_loop/advisory/pcfl_crossover_receipt.py`

SHA-256:
`2313990bf08996038b18d70ae01b447c939dc5463917f0be708f18168029c1a9`

Tests:
`research_loop/advisory/test_pcfl_crossover_receipt.py`

SHA-256:
`6e63d73326e0de8eaad652ae70aa51d6a6b95fa4ea1019e89517d6278e91265f`

All 12 CPU-only tests pass. New attacks cover a 392-name but dimensionally
tiny fake carrier, an invented near-miss namespace, and a one-element wrong
projection dimension in addition to the v2 partition/schema/rate tests.

## Read-only real-artifact result

The exact-layout validator was rerun read-only on the three reported remote
rank-8/rank-16/rank-64 artifacts with explicit expected ranks and fp32 dtype.
It accepted all three and reproduced their prior SHA-256, file-byte, element,
and tensor-manifest fields. This is author-observed external command output,
not independently replayable local provenance: the external adapter bytes and
complete stdout were not copied into this repository.

A transcribed, SHA-bindable machine-readable summary is stored at
`research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v3.json`.
That JSON labels this provenance limitation explicitly and must not be treated
as a substitute for the remote bytes or raw stdout.

The three serialized-adapter-file intercepts remain:

| rank | reported adapter file | header-validated elements | expanded bytes required for adapter-file ratio `<.50` | bytes/token required at 8x16k |
|---:|---:|---:|---:|---:|
| 8 | 80,792,096 B | 20,185,088 | 161,584,193 | 1,232.7896 |
| 16 | 161,533,192 B | 40,370,176 | 323,066,385 | 2,464.8009 |
| 64 | 645,975,704 B | 161,480,704 | 1,291,951,409 | 9,856.8070 |

These demanding intercepts and, more fundamentally, the absence of any
qualifying generated-load receipt justify **not spending** on the proposed 8x
positive panel. They do not prove mathematical impossibility or a measured
rate failure.

## Remaining complete-receipt gate

No positive physical-compression cell may run until a prospectively sealed
packet supplies actual SHA-bound raw, canonical, and deterministic expanded
artifacts at every proposed load; exact bytes and authorized pinned-tokenizer
counts; a complete life/common auxiliary census; serialized/resident/
simultaneously-retained coordinates; actual rates; and at least three useful
loads beyond an honest crossover. Until then, physical all-layer-LoRA
compression remains a later-scale objective, while semantic-code compression
and LoRA transport are separate nearer claims.
