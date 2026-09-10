# PCFL compression feasibility re-audit v1

Date: 2026-09-07

Status: **independent, proposal-only, read-only re-audit**. This review is
bound to `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md`,
SHA-256
`95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd`.
It changes no source, design, model, tokenizer, adapter, benchmark, workflow,
or execution state and authorizes no implementation, fit, model/tokenizer
call, external execution, GPU use, or scientific claim.

## Verdict

**PASS AS A REJECTION OF THE CURRENT `0.5x/2x/4x/8x` POSITIVE RATE
EXPERIMENT; NOT A PASS FOR ANY REPLACEMENT E3 DESIGN.** The all-projection
LoRA parameter arithmetic is exact conditional on the declared Qwen2.5-7B
dimensions. Both the bf16 architectural floor and the reported current fp32
safetensors sizes make the proposed `8x` endpoint physically incapable of
approaching the registered rate thresholds under any honest ordinary PCFL
serialization. The model-free crossover receipt must precede power work or
model/GPU spend.

The route map mostly preserves claim discipline, but Routes A--D are not four
ways to earn the same claim. Route B alone preserves the current all-layer
LoRA physical-compression estimand. Route A is an honest narrower semantic-code
claim; Route C can preserve only a generic parametric-carrier claim after a
material rearchitecture and new fixed-child binding; Route D is a valid
negative result and releases no positive compression clause. These distinctions
must remain explicit in any successor deliberation.

## 1. Independent arithmetic check

The inspected trainers target, with `bias="none"`, all seven projections in
each transformer block:

```text
q_proj, k_proj, v_proj, o_proj,
gate_proj, up_proj, down_proj
```

For hidden width `h=3,584`, KV width `k=512`, MLP width `m=18,944`, and
`L=28` layers, rank-`r` LoRA contributes `r*(din+dout)` parameters per linear
map. Thus:

```text
per rank per layer
 = 2*(h+h) + 2*(h+k) + 3*(h+m)
 = 2*7,168 + 2*4,096 + 3*22,528
 = 90,112

per rank over 28 layers = 90,112*28 = 2,523,136
```

The resulting values are:

| rank | parameters | bf16 tensor floor | fp32 tensor floor |
|---:|---:|---:|---:|
| 1 | 2,523,136 | 5,046,272 B | 10,092,544 B |
| 4 | 10,092,544 | 20,185,088 B | 40,370,176 B |
| 8 | 20,185,088 | 40,370,176 B | 80,740,352 B |
| 16 | 40,370,176 | 80,740,352 B | 161,480,704 B |

Note 56's decimal-MB table is correct. Its reported rank-8 file size
`80,792,096 B` is `51,744 B` above the fp32 tensor floor, and its rank-16 file
size `161,533,192 B` is `52,488 B` above the fp32 tensor floor. Those sizes are
internally consistent with fp32 tensors plus safetensors metadata. The derived
strict denominator requirements are also correct:

| present file | required for `R_exp<.50` | required for `R_raw<.35` |
|---:|---:|---:|
| rank 8: 80,792,096 B | `>161,584,192 B` | `>230,834,560 B` |
| rank 16: 161,533,192 B | `>323,066,384 B` | `>461,523,405.7 B` |

Two receipt qualifications remain. First, note 56 does not give the observed
artifact paths or hashes, so this review verifies their internal arithmetic,
not their independent provenance. A ratifiable `CROSSOVER_RECEIPT` must bind
the exact files and inspect tensor names, shapes, dtypes, file bytes, and
metadata. Second, serialized code length, mounted resident bytes, and any
simultaneously retained checkpoint are different resource coordinates. The
successor accounting must say which copies are required for a fresh actor and
report storage and resident memory separately; it may neither credit a
hypothetical bf16 rewrite to the current fp32 carrier nor double-count one
representation merely because it is loaded.

The serving cap is independently visible in
`organism_v6/model_backend.py` as default `max_model_len=16,384`. The actual
`L_native` in the rate design is strictly smaller after fixed prompt/state and
output reserve, so using `8*16,384=131,072` tokens is generous to feasibility.

## 2. The registered load schedule cannot honestly cross

At the generous 131,072-token upper endpoint, the rank-8 bf16 floor alone
would require the expanded form to average more than

```text
80,740,352 / 131,072 = 616 UTF-8 bytes per expanded token
```

to pass `R_exp<.50`. The present rank-8 file requires

```text
161,584,192 / 131,072 = 1,232.79 bytes per expanded token.
```

At the planning density of four bytes/token, `R_exp` is about `77.0` at the
bf16 floor and `154.1` for the present file, versus the required value below
`.50`. Equivalently, the present rank-8 crossover is approximately 40.4
million expanded tokens or 2,466 full 16k contexts. Auxiliary prompts,
candidate tables, codebooks, indices, and runtime state only move the
crossover farther away.

The raw gate independently requires more than 115.34 MB at the bf16 floor or
230.83 MB for the reported current rank-8 file. Raw-event bytes are not
mathematically determined by the expanded-token cut, so an exact generator
bound is still required. Artificially huge raw prose, padding, repeated
exposures, or long labels cannot count as new semantic load or rescue the
claim. In any case the joint gate already fails on `R_exp` for a minimal
ordinary PCFL rendering.

Strict mathematical impossibility should be asserted only after the frozen
serializer/tokenizer-free byte receipt supplies an exact maximum, because a
token count alone is not a byte bound. Note 56 appropriately says “almost
certainly” and requires the receipt. Scientifically, however, there is no
credible honest positive cell at `8x`: a representation bloated enough to
reach 1,233 bytes per token would violate the minimal observation-normal-form
and expanded-baseline anti-inflation gate.

The crossover receipt must evaluate the full functions, not only the tensor
intercept:

```text
B_lora(n) = adapter_file_or_minimal_bound_carrier + every charged auxiliary(n)
R_exp(n)  = B_lora(n) / B_expanded(n)
R_raw(n)  = B_lora(n) / B_raw(n).
```

If a candidate catalog, index, label map, or other auxiliary grows at least
`.50` as fast as `B_expanded`, an `R_exp<.50` crossover may never exist. A
tensor-only crossover is therefore necessary, not sufficient. Likewise, a
constant tensor allocation supplies a zero byte-growth slope even when useful
information has collapsed; all non-loss and authenticity gates remain
conjunctive.

## 3. Route-by-route claim audit

### Route A — valid narrowing, not physical LoRA compression

This route can support that a target-independent experience compiler produced
a shorter useful connected **textual semantic code**, followed separately by
same-semantics LoRA transport. It does not establish that the adapter or
complete life-specific parametric carrier is shorter than expanded memory.
The separation in note 56 is correct and must not later be recombined into
“LoRA compressed experience.”

The proposed prospective fresh-cohort prediction is a PCFL-Schema abstraction
test, not necessary merely to show deterministic denotational code reduction.
It may strengthen Route A, but it changes the scientific object and adds its
own prediction-before-observation controls. It cannot be used post hoc to
inflate compressibility or substitute schema generalization for the physical
rate gate.

**Disposition: preserves honesty and part of the full objective, but narrows
the E3 physical-carrier claim.**

### Route B — preserves the current physical-compression estimand

This is the only route that leaves the current rank-8/16 all-projection carrier
unchanged. It remains valid only if the successor schedule is defined around
the larger of the exact `R_exp` and `R_raw` crossover loads and contains at
least three prospectively sealed loads beyond that crossover, not merely three
points beyond native context. Each load must add genuinely new supported
mappings; padding, replay, exposure, or repeated provenance does not count.

The complete auxiliary slope, unamortized compiler/training cost, writer
fidelity, old/new/cross-era non-loss, false-memory, linked/deranged/bridge,
adapter-off, wrong/twin-life, and common-read gates all survive unchanged.
There is no power calculation until the model-free byte surface has a feasible
cell.

**Disposition: preserves the original claim, but is presently a later-scale
program with no demonstrated feasible or affordable cell.**

### Route C — preserves only a newly bound carrier claim

A targeted-layer, quantized, sparse, learned-code, or dedicated parameter
store may make a feasible crossover. It is a material architecture change,
not a cheaper cell of the current experiment. Sparse masks, indices, scales,
codebooks, dequantization/decompression state, candidate machinery, serialized
bytes, and mounted representation all remain charged. Functional non-loss may
not be borrowed from the all-projection child.

To retain the one-child topology, the new carrier architecture and fixed-child
selection/requalification must be bound before outcomes; adding it to an
already selected terminal child does not preserve the original “current
all-layer LoRA” estimand. If the dedicated store is not LoRA, the released
claim must say “parametric carrier,” not “per-life LoRA.”

**Disposition: can preserve a generic compressed-experiential-carrier claim
after new deliberation; it changes, and cannot retroactively rescue, the
current LoRA claim.**

### Route D — preserves falsifiability, not a positive clause

Running the original panel as an explicitly negative rate result is valid if
resource-proportionate and prospectively labeled. Useful transport at
`R_exp>>1` may still be informative, but neither behavioral advantage nor a
flat allocation curve releases “compression.”

**Disposition: preserves the scientific boundary and yields a negative E3
result; it does not support the full objective's positive compressed-
experiential-knowledge clause.**

## 4. Required disposition

Adopt note 56's immediate no-go: do not ratify `0.5x/2x/4x/8x`, spend on
`N=48` power, or launch a model/GPU rate run as a positive compression test.
First produce a source-bound, model-free crossover receipt with exact
serializer outputs, artifact/tensor provenance, both byte denominators, every
auxiliary-state growth law, and a feasible three-post-crossover schedule.

If no honest cell exists, choose Route A with its narrower textual-code plus
transport wording or Route D as a negative result. Route B alone retains the
present physical all-layer-LoRA claim. Route C requires a new architecture,
new fixed-child binding, and claim wording matched to the actual carrier. None
of these choices changes the one-parent/one-child topology, but only a newly
ratified Route B or qualifying Route C can release a positive physical
rate--distortion clause.

## Read receipts

- `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md`, SHA-256
  `95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd`
- `research_loop/advisory/20260907_one_child_pcfl_rate_distortion_design_v1.md`,
  SHA-256
  `85a036c6f0244ca60652fe10e89ceb500e3bddd30bc69ef9b045abd8e0d3882e`
- `organism_v6/train_adapter.py`
- `organism_v6/train_adapter_v21.py`
- `organism_v6/model_backend.py`
- `research_loop/plans/one_parent_child_headline_v1.md`
