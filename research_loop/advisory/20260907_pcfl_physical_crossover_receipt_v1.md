# PCFL physical-carrier crossover receipt v1

Date: 2026-09-07

Status: completed model-free, tokenizer-free, read-only accounting receipt.
This is not an E3 experiment, architecture change, implementation approval,
model execution, benchmark execution, adapter training/mount, or GPU run.

## Question

Can the proposed `0.5x/2x/4x/8x` expanded-text panel plausibly cross the
registered physical compression thresholds for the current all-layer
Qwen2.5-7B LoRA carrier?

## Instrument

Script:
`research_loop/advisory/pcfl_crossover_receipt.py`

Script SHA-256:
`71c0b36596d9ff3cce0a2bf9217cbba8b7053902698f9acc40582e118bb9f77b`

The script imports no model, tokenizer, PyTorch, PEFT, or safetensors library.
It reads the safetensors eight-byte header length and JSON header, checks every
tensor's shape/dtype against its byte offsets, hashes the complete files, and
reports serialized, mounted-payload, common-sidecar, and strict rate-crossover
quantities separately. A canonical JSON manifest over every tensor name,
shape, dtype, offset, element count, and byte count is itself SHA-bound below.
Run with `--include-tensors` to print that full manifest.

Receipt command executed read-only on the existing A40 host:

```text
python3 pcfl_crossover_receipt.py --native-context-tokens 16384 \
  /localhome/local-rohing/v6_out/controls/adapter_r8/adapter_model.safetensors \
  /localhome/local-rohing/v6_out/L_B_seed0/sleep_0992/adapter/adapter_model.safetensors \
  /localhome/local-rohing/v6_out/controls/adapter_r64/adapter_model.safetensors
```

No scientific process or GPU state was changed.

## Exact artifacts

| field | rank 8 | rank 16 | rank 64 |
|---|---:|---:|---:|
| adapter SHA-256 | `ccbb00754c0001524447ddfc0eb4cd8d3380cc0bafc1b69c4ff62856b0145a89` | `92b9855be72b8cc552c0cee840d5a2cdb8667104f243dcac3c946b97b3fa19e8` | `2384a6fae5fe249ad358e54feddafa6b4353f4ae2b9ff179f32062df60f1fea5` |
| serialized `B_life` | 80,792,096 B | 161,533,192 B | 645,975,704 B |
| common config sidecar | 1,259 B | 1,260 B | 1,261 B |
| serialized `B_actor_total` | 80,793,355 B | 161,534,452 B | 645,976,965 B |
| tensor payload at actual dtype | 80,740,352 B | 161,480,704 B | 645,922,816 B |
| bf16 tensor floor | 40,370,176 B | 80,740,352 B | 322,961,408 B |
| trainable elements | 20,185,088 | 40,370,176 | 161,480,704 |
| tensor count | 392 | 392 | 392 |
| serialized dtype | fp32 | fp32 | fp32 |
| safetensors overhead | 51,744 B | 52,488 B | 52,888 B |
| tensor-manifest SHA-256 | `44296f5937a40292ff712c46b16d59f6f02af243de768f7148475b3b9c893767` | `b59cf115f049b160560678192a536070f0d96edb054c819d82d585e4c9b2c43e` | `efedb0c3dd8fe668ff8190f155cbdf2ffea5563cb9738f196f5c9e1fca34667e` |

Every adapter has 56 tensors for each of `q_proj`, `k_proj`, `v_proj`,
`o_proj`, `gate_proj`, `up_proj`, and `down_proj`: LoRA A and B in each of 28
layers. Metadata is exactly `{"format":"pt"}`.

Config sidecar SHA-256 values are, respectively:

- rank 8: `1abbd8c8db41d4f58bedf3ad3e638f6f45b4f2128ea38aaa830391dc7635f838`;
- rank 16: `e047936bba34f1496377a89bd7bb247402cbcb70121bb8be60a9922d03866f79`;
- rank 64: `c47702f743141abea5a8d081cbed98398aba482d016b2df5b94407d6908ee435`.

The sidecars are reported separately because they may be common code rather
than life-specific state. The base model is shared `B_common` and excluded
from the numerator. Historical sleep checkpoints and optimizer state are not
needed for acting and are also excluded; only the currently mounted checkpoint
is counted. Runtime allocator overhead is not included in mounted tensor
bytes, so the receipt favors the positive compression hypothesis.

## Strict crossover requirements

The integer denominator is one byte above the equality boundary.

| requirement | rank 8 | rank 16 | rank 64 |
|---|---:|---:|---:|
| expanded bytes for `B_life/B_expanded < .50` | 161,584,193 | 323,066,385 | 1,291,951,409 |
| raw bytes for `B_life/B_raw < .35` | 230,834,561 | 461,523,406 | 1,845,644,869 |
| expanded bytes for `B_actor_total/B_expanded < .50` | 161,586,711 | 323,068,905 | 1,291,953,931 |
| raw bytes for `B_actor_total/B_raw < .35` | 230,838,158 | 461,527,006 | 1,845,648,472 |

At `8 * 16,384 = 131,072` tokens, the expanded artifact would need at least:

- rank 8: `1,232.7896` bytes per token;
- rank 16: `2,464.8009` bytes per token;
- rank 64: `9,856.8070` bytes per token.

These are not assumptions about tokenizer density. They state the exact
average serialized byte density an actually generated 8x artifact would have
to exhibit to cross the registered life-specific rate threshold.

## Adjudication

The prior decision is strengthened:

1. Reject the proposed `0.5x/2x/4x/8x` panel as a positive physical-LoRA
   compression experiment before any GPU or power spend.
2. Do not call fixed rank, useful LoRA transport, semantic distillation, or
   deletion of detail physical compression.
3. Preserve the full E3 objective. Route B—a genuinely large accepted-semantic
   load that crosses the complete all-layer-LoRA byte boundary—is the only
   route that retains the present physical-LoRA compression claim.
4. Semantic-code compression may be tested sooner only as a separately named
   code-length result, with LoRA transport separately measured.
5. Before any replacement E3 run, generate and SHA-bind the actual raw and
   deterministic `EXPANDED_EQUIVALENT` byte artifacts, then rerun this receipt.
   Only their counted bytes can turn the present scientific infeasibility into
   a mathematical crossover or falsifier.

This receipt implements the pre-spend requirement in
`research_notes/56_pcfl_compression_feasibility_adjudication_v1.md` and the
accounting caveats in
`research_loop/advisory/20260907_pcfl_compression_feasibility_reaudit_v1.md`.
