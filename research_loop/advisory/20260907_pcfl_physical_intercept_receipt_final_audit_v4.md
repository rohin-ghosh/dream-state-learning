# PCFL physical-carrier intercept receipt final audit v4

Date: 2026-09-07

Status: **fresh-context, independent, model-free and tokenizer-free final
audit**. No network, model, tokenizer, benchmark, adapter, or GPU was used.
Execution was limited to the checked-in CPU unit suite, exact arithmetic and
format checks, and a temporary synthetic safetensors invocation. No reviewed
source was changed.

## Verdict

**PASS — for the deliberately partial serialized-adapter intercept only.**

The v3 zero-padding, validation-profile, and raw-schema defects are closed.
All locally verifiable digests, counts, arithmetic, schema names, and Markdown
transcriptions agree. V4 is claim-safe because it treats the three external
adapter observations and their digests as author-reported, does not turn the
conditional numerator crossovers into observed rates or a compression-failure
claim, and expressly keeps positive E3 spend blocked pending a complete
prospective receipt.

This is not a pass of complete E3 evidence. The external adapter bytes,
sidecars, exact external invocation, and complete raw stdout are absent from
the local packet and were not independently replayed. Complete state census,
runtime and retention coordinates, authorized denominators, actual rates,
equivalence, and useful post-crossover loads remain open.

## Bound local inputs and SHA-256

| input | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_reaudit_v3.md` | `57742e6e6ae106945bf5cbd5a4218004cc129164b0a233e83f60405b0049ac07` |
| `research_loop/advisory/pcfl_crossover_receipt.py` | `418ccb837891f9b6cad91b877ec7052af1fab0ce2c9525a10be610cb0455ad20` |
| `research_loop/advisory/test_pcfl_crossover_receipt.py` | `9ff6252c1cd0d7fa925be442d5560395215e209e3c355bc25a0f5d677aeb580e` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v4.json` | `71df2509e42057c10c5ba734df6f9682cbd462d2573190a1984a3a26239aaaf4` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v4.md` | `7c7b4d5c78d03ed6fd79583cab0bc95b8b745bab75eff7896e790bbd7fe625e4` |

The v4 Markdown's adopted v3 re-audit, script, and test digests match these
local bytes. The v4 JSON repeats the script and test digests exactly. Every
declared digest in the JSON is well-formed lowercase 64-hex; the three
adapter, sidecar, and tensor-manifest digest values cannot be recomputed
without their disclosed-absent external inputs.

## Defect closure

The tensor-name expression now permits only `0` or a nonzero digit followed by
decimal digits. Consequently `layers.00` cannot be normalized to layer 0
before comparison. The checked-in regression mutates the otherwise valid
layer-0 namespace to `layers.00` and observes the expected namespace
rejection. The exact branch/module, A/B pair, rank, dtype, projection-shape,
element-total, and contiguous-partition checks remain intact.

The raw emitter now identifies schema
`pcfl_physical_carrier_intercept_receipt_v4` and emits a
`validation_profile` containing the namespace template, expected layer count,
all three Qwen dimensions, the complete module/branch map, and path-specific
expected ranks and dtypes. A temporary one-layer synthetic CLI invocation
confirmed those fields are emitted with the values actually supplied. The
local JSON correctly uses the distinct summary schema
`pcfl_physical_carrier_intercept_receipt_v4_transcribed_summary` and names the
raw emitted schema separately; it does not present itself as preserved raw
stdout.

All 13 checked-in CPU tests pass, including duplicate-key, interval,
namespace, rank, tiny-carrier, projection-dimension, and zero-padding attacks.
This independently confirms the claimed test count. The earlier 14-way
dimension attack is accurately attributed to the prior reviewer rather than
claimed as a new v4 execution.

## Numeric and cross-format consistency

For the declared 28-layer Qwen profile, the exact LoRA coefficient is 90,112
elements per layer per rank, hence 2,523,136 elements per rank. Each JSON row
satisfies exactly:

```text
total_numel       = 2,523,136 * rank
F32 payload       = 4 * total_numel
bf16 floor        = 2 * total_numel
known subtotal    = adapter file + discovered config sidecar
strict <.50 D_min = 2 * adapter file + 1
strict <.35 D_min = floor(adapter file * 20 / 7) + 1
8x16k bytes/token = strict <.50 D_min / 131,072
tensor count      = 28 * 7 * 2 = 392
```

The ranks 8, 16, and 64 therefore yield exactly 20,185,088, 40,370,176,
and 161,480,704 elements. Their adapter-file strict half-rate denominators are
161,584,193, 323,066,385, and 1,291,951,409 bytes. The Markdown's displayed
bytes/token values 1,232.7896, 2,464.8009, and 9,856.8070 are the correct
four-decimal renderings of the JSON values. File sizes, element totals,
thresholds, ranks, status, and partial-evidence qualifications agree across
the JSON and Markdown.

## Claim boundary

V4 consistently calls these values conditional serialized-adapter-file
numerator intercepts. It denies complete-life-state, residency, simultaneous
retention, actual-denominator, actual-rate, impossibility, and measured-failure
interpretations. Its no-spend result is therefore a procedural gate in the
absence of a qualifying receipt, not a positive scientific conclusion.

The complete E3 gate remains open exactly where required: prospective
SHA-bound raw, canonical, and expanded artifacts; authorized pinned-tokenizer
counts; complete life/common auxiliary accounting and growth laws; resource
coordinates; actual rates; equivalence; and at least three useful
post-crossover loads. This audit authorizes no model, adapter, benchmark, or
GPU execution and does not promote any positive physical-compression claim.

## Advisory digest convention

The SHA-256 of the final bytes of this audit is reported in the accompanying
handoff rather than embedded here, because embedding a whole-file digest would
change the bytes being hashed.
