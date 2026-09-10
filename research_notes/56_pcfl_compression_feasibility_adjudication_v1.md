# 56 — PCFL compression feasibility adjudication v1

Date: 2026-09-07

Status: unbound, proposal-only adjudication. It authorizes no architecture
change, tokenizer/model call, implementation, benchmark generation, adapter
operation, external execution, GPU use, or claim.

## Verdict

The fresh rate--distortion design is scientifically much stronger than calling
fixed rank “compression,” but its proposed `0.5x/2x/4x/8x` context-length panel
is almost certainly incapable of passing its own byte-rate gate for the current
all-layer Qwen2.5-7B LoRA. Do not ratify or execute that load schedule as a
positive compression experiment until an exact model-free crossover receipt
shows that the expanded comparator is large enough.

This is not a reason to weaken accounting. It is a reason to separate three
claims:

1. DREAM may produce a shorter **semantic training code** than observation-
   expanded experience;
2. LoRA may **transport** that code into behavior; and
3. the complete life-specific parametric carrier is physically **compressed**
   only if its charged bytes beat the denotationally equivalent expanded
   carrier at bounded distortion.

The current ICLR parenting paper should claim at most (2), and only after its
own gates. The full project retains (1) and (3) as separately falsifiable E3
work rather than redefining a likely rate failure as success.

## Exact present adapter byte floor

The current trainer targets every attention and MLP projection in all 28
Qwen2.5-7B layers:

```text
q_proj, k_proj, v_proj, o_proj,
gate_proj, up_proj, down_proj
```

The cached pinned model config reports the architecture dimensions, and the
current `organism_v6/model_backend.py` fixes the serving context at 16,384:

```text
hidden_size        = 3584
intermediate_size  = 18944
kv projection size = 512
layers             = 28
runtime context    = 16384 tokens
```

For a LoRA linear map, trainable parameters are
`rank * (input_dim + output_dim)`. Therefore:

```text
parameters per rank per layer
 = (3584+3584)                         q
 + (3584+512) + (3584+512)            k,v
 + (3584+3584)                         o
 + 3*(3584+18944)                      gate,up,down
 = 90,112

parameters per rank over 28 layers = 2,523,136
```

At bf16 and before safetensors metadata or any life-specific auxiliary state,
the theoretical tensor floor is:

| rank | parameters | tensor bytes | expanded bytes needed merely for `R_exp < .50` |
|---:|---:|---:|---:|
| 1 | 2,523,136 | 5.05 MB | >10.09 MB |
| 4 | 10,092,544 | 20.19 MB | >40.37 MB |
| 8 | 20,185,088 | 40.37 MB | >80.74 MB |
| 16 | 40,370,176 | 80.74 MB | >161.48 MB |

The already-trained artifacts show that the current PEFT save path serializes
these adapters in fp32 rather than bf16:

| observed artifact | exact safetensors bytes | bytes/trainable parameter |
|---|---:|---:|
| rank 8, control adapter | 80,792,096 | approximately 4 |
| rank 16, B0 sleep-992 adapter | 161,533,192 | approximately 4 |

Under the actual present carrier bytes, rank 8 therefore needs an expanded
equivalent larger than 161.58 MB merely for `R_exp < .50`, and eligible raw
events larger than 230.83 MB for `R_raw < .35`; rank 16 needs more than 323.07
MB and 461.52 MB, respectively. These are still lower bounds: candidate tables,
indices, verbalizers, calibration state, prompts unique to the carrier, and any
retained optimizer/runtime state only increase `B_life`. A redesigned
serialization may approach the bf16 floor, but the current system may not
receive that hypothetical credit.

An `8 * 16,384 = 131,072` token expanded carrier is orders of magnitude below
the rank-8 crossover under ordinary UTF-8 token densities. At four bytes/token,
the actual current rank-8 `R_exp < .50` crossover is roughly 40.4 million
expanded tokens, or 2,466 runtime contexts; rank 16 needs roughly 80.8 million
tokens, or 4,930 contexts. The bf16 architectural floors are half those values.
These token conversions are planning approximations, not admissible evidence.
The exact pinned-tokenizer and canonical-serializer crossover must be computed
without loading a scientific model and frozen before any ratification.

## Consequences

### 1. Preserve the complete byte denominator

Do not count only nonzero singular values, an abstract rank, source corpus
tokens, or compressed checkpoint-on-disk bytes while the actor mounts dense
bf16 LoRA tensors. The relevant carrier rate is the complete life-specific
state required for acting. A separately compressed checkpoint supports a
storage/transport statement only if decompression machinery and the mounted
representation are charged under a prospectively defined boundary.

### 2. Do not spend GPU on a mathematically foreclosed positive cell

Before a rate--distortion run, execute a model-free `CROSSOVER_RECEIPT` that
prints, for every proposed rank/layout/precision and every generated load:

```text
adapter tensor bytes
+ all charged life-specific auxiliary bytes
expanded-equivalent bytes/tokens
canonical-text bytes/tokens
eligible raw-event bytes
R_exp and R_raw
minimum possible R_exp/R_raw before any task call
```

If the minimum possible rate cannot cross the registered threshold, either:

- run the cell explicitly as a cheap rate falsifier with no expectation of a
  positive compression claim; or
- change the scientific question through a new deliberation before spending
  writer/model/GPU compute.

### 3. Viable future routes are material choices, not accounting tricks

#### Route A — semantic-code compression plus separate LoRA transport

Compare a prospectively committed compact schema/connected code with its exact
observation-expanded equivalent through the common text interface. Require
denotational round-trip equality, shorter code, bounded functional loss,
prospective prediction on a fresh cohort, binding/twin interventions, and full
compiler/index accounting. Then separately show the same compact semantics are
transported through LoRA.

Allowed claim: the experience compiler formed a shorter useful semantic code,
and that code was behaviorally accessible through the adapter. Forbidden claim:
the LoRA or whole agent is physically smaller than expanded memory.

This route is the most feasible extension of the current architecture and
keeps the ICLR parenting experiment independent.

#### Route B — reach the honest all-layer LoRA crossover

Generate enough genuinely new PCFL-Stream semantics for the expanded carrier
to exceed the exact rank-8/16 byte crossover, with at least three loads beyond
it. This preserves the current all-layer adapter but likely demands tens of
millions of expanded tokens, enormous cumulative training, and a writer that
has not yet passed E0. It is scientifically clean and presently a later-scale
experiment, not a September critical-path item.

#### Route C — design a smaller experiential carrier

Use a much smaller targeted-layer/rank/precision/sparse adapter, learned code,
or dedicated parameter store whose mounted life-specific bytes can cross the
expanded comparator at feasible loads. This changes the architecture and its
possible effect on thinking. It requires a new source-bound deliberation and
cannot be introduced after seeing confirmation performance.

Even all-layer rank 1 is about 5.05 MB at the bf16 floor (about 10.09 MB under
the current fp32 serialization) and needs an expanded carrier over 10.09 MB
(about 20.19 MB current) for `R_exp < .50`, before auxiliary state. Merely
moving from rank 16 to rank 8 does not solve the scale mismatch.

#### Route D — explicit negative rate result

Run the exact rate panel and report that useful parametric transport costs more
bytes than an exact symbolic/text carrier at the studied lifetimes. This can be
a valuable systems result, especially alongside behavioral advantages, but the
word *compression* must be absent from the positive contribution.

## Repaired information-gain order

1. Finish the E0 native writer and E1 parenting tests; neither depends on a
   compression claim.
2. Run a zero-model crossover receipt for candidate E3 carriers and loads.
3. If no candidate crosses, perform only Route A semantic-code tests or state
   the expected rate falsifier; do not launch LoRA rate confirmation.
4. If a candidate crosses, require explicit/canonical text oracle success and
   the full causal connectedness/traversal controls from note 54.
5. Only then spend on the powered rate--distortion panel from the fresh design.

## Adopted and rejected parts of the fresh design

Adopt:

- exact canonical denotation and deterministic `EXPANDED_EQUIVALENT`;
- separate `B_common`, `B_life`, `B_actor_total`, and raw-audit bytes;
- complete candidate/index/codebook/prompt/runtime accounting;
- explicit-text oracle before LoRA;
- old/new/cross-era distortion vector and false-memory gates;
- authentic link, bridge, adapter-off, wrong-life, and twin controls;
- fixed-root, fixed-sequence, intersection--union statistics; and
- narrow one-fixed-child claim ceiling.

Reject until repaired:

- `8x` native context as an assumed sufficient compression horizon;
- provisional `N=48` power work before rate crossover feasibility;
- any suggestion that constant allocation implies sublinear useful code; and
- any GPU rate run before the model-free physical-byte floor is printed.

## Source receipts

- Fresh design:
  `research_loop/advisory/20260907_one_child_pcfl_rate_distortion_design_v1.md`
  (SHA-256
  `85a036c6f0244ca60652fe10e89ceb500e3bddd30bc69ef9b045abd8e0d3882e`).
- Current trainer target modules:
  `organism_v6/train_adapter.py` and `organism_v6/train_adapter_v21.py`.
- Cached model configuration read-only receipt:
  Qwen2.5-7B, 28 layers, hidden 3,584, intermediate 18,944, four KV heads.
- Existing-artifact read-only receipt: rank-8 safetensors `80,792,096` bytes;
  rank-16 safetensors `161,533,192` bytes.

This adjudication preserves the full project objective by exposing its real
scale requirement. It does not replace physical compression with a cheaper
semantic-code claim; it keeps both claims separately alive and measurable.
