# PCFL physical-carrier crossover receipt attack v1

Date: 2026-09-07

Status: **fresh-context, independent, model-free adversarial audit**. This
review changed no frozen source, receipt, model, tokenizer, benchmark, adapter,
or external state; used no network or GPU; and authorizes no scientific run or
claim. The only execution beyond reading and hashing the named files was a
CPU-only synthetic parser check with temporary, fabricated bytes.

## Verdict

**REVISE.** The LoRA parameter arithmetic, reported file/payload differences,
sidecar additions, strict crossover integers, and 8x byte-density values in
`20260907_pcfl_physical_crossover_receipt_v1.md` are arithmetically correct.
The receipt is useful as a fail-closed warning that the proposed positive 8x
cell has not earned spend.

It is not, however, the complete pre-spend `CROSSOVER_RECEIPT` required by
note 56. It supplies numerator intercepts and denominator requirements, not
the actual generated-load denominators or rates; it has no mechanism to charge
the enumerated life-specific auxiliaries; and its parser does not enforce a
non-overlapping, gap-free safetensors data partition. The final assertion that
the document "implements the pre-spend requirement" is therefore too strong.
It satisfies the gate only in the operational sense that the absence of a
qualifying cell must stop spend, not in the evidentiary sense of completing
the prescribed receipt.

## 1. Bound inputs and hash audit

The locally inspected bytes hash as follows:

| input | SHA-256 | disposition |
|---|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` | operating contract read |
| `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md` | `95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd` | matches the re-audit's binding |
| `research_loop/advisory/20260907_pcfl_compression_feasibility_reaudit_v1.md` | `d3c5e7513c18bceec46359ceca5223404f83438a734fe869eacbec0de69a55c2` | independently hashed here |
| `research_loop/advisory/pcfl_crossover_receipt.py` | `71c0b36596d9ff3cce0a2bf9217cbba8b7053902698f9acc40582e118bb9f77b` | matches the receipt's script hash |
| `research_loop/advisory/20260907_pcfl_physical_crossover_receipt_v1.md` | `ac1c4d48d5ad2b9de14c103852b8550fd385f7c9e8c9ca3be09b6db54a3f60f0` | independently hashed here |

The three adapter hashes, three config hashes, and three tensor-manifest hashes
cannot be independently recomputed from the frozen local evidence named for
this review. The receipt records an execution command on another host, but no
machine-readable command output or full tensor manifest is preserved beside
the Markdown. Consequently those hashes bind claimed remote artifacts if the
artifacts are later produced, but the present packet does not let an
independent reader verify that the table and prose were transcribed from that
output. This is a provenance limitation, not evidence that the stated hashes
are wrong.

## 2. Independent arithmetic and strict-inequality audit

For 28 layers and seven LoRA-targeted projections, the declared dimensions
give `90,112` parameters per rank per layer and `2,523,136` per rank overall.
Thus ranks 8, 16, and 64 contain respectively `20,185,088`, `40,370,176`, and
`161,480,704` elements. Multiplication by four exactly reproduces the reported
fp32 payloads:

```text
rank 8:   80,740,352 B
rank 16: 161,480,704 B
rank 64: 645,922,816 B
```

Subtracting these from the reported files gives the stated overheads `51,744`,
`52,488`, and `52,888` bytes. Adding sidecars of `1,259`, `1,260`, and `1,261`
bytes gives the stated actor totals `80,793,355`, `161,534,452`, and
`645,976,965` bytes. The tensor count `392` and per-module count `56` are also
structurally consistent with `28 layers * 7 modules * 2 (A/B)`.

For integer byte denominator `D`, the strict gates are:

```text
B/D < 1/2  => D_min = 2B + 1
B/D < 7/20 => D_min = floor(20B/7) + 1
```

Independent exact-integer evaluation reproduces every crossover value in the
receipt, including equality-boundary cases. Dividing the three life-specific
expanded minima by `131,072` reproduces `1,232.7896`, `2,464.8009`, and
`9,856.8070` bytes/token after four-decimal rounding.

One implementation qualification remains: `strict_denominator_min` accepts a
binary floating-point rate and calls `floor(numerator / rate)`. It happens to
return the correct integers for all published sizes and for `.50`/`.35`, but
it is not an exact general implementation of the function its name and output
notes promise. A revision should take a rational threshold (for example,
numerator/denominator integers or `Fraction`) and perform integer arithmetic.

## 3. Safetensors parsing attack

The parser checks each tensor's `end-start` against its shape/dtype byte count
and checks only that `data_start + max(end) == file_bytes`. It does **not**
establish that offsets form the unique, complete data-buffer partition required
for physical accounting:

- it does not reject two tensors whose byte intervals overlap;
- it does not reject a leading or internal unindexed gap;
- it does not require the first offset to be zero or each next start to equal
  the previous end;
- it does not explicitly reject negative offsets, reversed intervals, or
  duplicate JSON object keys; and
- it sums interval lengths even when intervals overlap, so
  `tensor_payload_bytes`, `total_numel`, and the apparent dtype floor can count
  the same physical bytes more than once.

A CPU-only synthetic check demonstrated the first two defects. A fabricated
file with two one-element F32 tensors both pointing at `[0,4]` was accepted and
reported `8` tensor-payload bytes although its data buffer contained `4`.
Another fabricated file with its sole F32 tensor at `[4,8]` was accepted with
four leading unindexed bytes. No real adapter was opened or executed in this
test.

For the claimed trusted files, the reported payload/file arithmetic is
internally plausible and gives no affirmative sign of overlap. But without
the artifacts or preserved full output, this review cannot establish that
their actual interval sets were valid. The parser should validate header
schema, reject duplicate keys, sort intervals by start, require a nonnegative
contiguous partition from zero through the exact data-buffer length, and then
assert that the sum of unique interval lengths equals that buffer length. It
should also assert the expected tensor namespace, A/B pairing, layers, target
modules, shapes, consistent rank, and absence of unexpected tensors before
the prose calls the files the declared all-layer LoRA carriers.

## 4. Accounting-boundary attack

The script's `B_life_serialized_bytes` is the safetensors file by definition,
not a demonstrated census of the complete life-specific carrier required for
acting. Its only discovered sidecar is a sibling `adapter_config.json`, and it
has no input manifest or CLI fields for candidate tables, indices, codebooks,
verbalizers, calibration state, carrier-unique prompts, decompression state,
or other life-specific runtime state enumerated by note 56. It also supplies
no auxiliary growth law as load increases. Calling the numerator complete is
therefore unsupported unless a prospectively bound exclusion/inclusion
manifest proves that all such objects are absent, shared, or charged.

The receipt separately reports serialized file bytes and tensor payload bytes,
which is good. It nevertheless computes rate crossovers only for serialized
`B_life` and serialized `B_actor_total`; it does not bind whether the scientific
claim concerns transport/storage bytes, mounted resident bytes, or both
simultaneously retained representations. "Mounted resident ... actual dtype"
is inferred from serialized dtype, but the parser cannot establish allocator
overhead, load-time casting, runtime buffers, or whether the serialized
checkpoint remains required while acting. Excluding allocator overhead may be
acceptable for a conservative feasibility lower bound, but not for a final
complete-carrier accounting claim without a frozen coordinate and rationale.

The config sidecar is described as potentially common even though its contents
are not printed and the files differ by rank and byte size. `B_actor_total`
does include it, so the published actor arithmetic is safe on that narrow
point. A final receipt must prospectively justify which fields are shared
architecture code versus life-specific state instead of inferring commonness
from the filename.

## 5. Earlier pre-spend requirement is still open

Note 56 required, **for every proposed rank/layout/precision and every
generated load**:

```text
adapter tensor bytes
+ all charged life-specific auxiliary bytes
expanded-equivalent bytes/tokens
canonical-text bytes/tokens
eligible raw-event bytes
R_exp and R_raw
minimum possible R_exp/R_raw before any task call
```

The current receipt provides adapter files, one automatically found sidecar,
strict denominator minima, and a hypothetical required bytes/token density.
It provides no generated load rows, no SHA-bound raw/canonical/expanded
artifacts, no actual byte or token denominators, no actual `R_exp`/`R_raw`, no
minimum possible rates at a load, no complete auxiliary census, and no
evaluation of every proposed serialization precision/layout. A required
denominator is not an observed denominator, and a required density is not an
exact serializer bound.

Accordingly, the receipt does not prove mathematical impossibility at 8x by
itself: an actual expanded byte maximum was not generated or bounded. It does
correctly show how implausibly large the 8x denominator would need to be and,
combined with the anti-inflation/minimal-normal-form premise, strongly supports
the conservative decision not to launch a positive rate experiment. The
correct status is: **numerator/crossover intercept audited; positive cell not
demonstrated; spend remains blocked.**

## 6. Required repair before any positive E3 spend

1. Harden the safetensors parser with exact header and interval-partition
   validation, expected-carrier schema assertions, and rational threshold
   arithmetic; add overlap, gap, duplicate-key, negative-offset, unexpected-
   tensor, and equality-boundary regression fixtures.
2. Preserve a SHA-bound machine-readable receipt output, including the complete
   tensor manifest, beside the human-readable adjudication.
3. Add a prospectively sealed accounting manifest for every life-specific and
   common object, its bytes at every load, its growth law, and the chosen
   serialized/resident/simultaneously-retained resource coordinate.
4. Generate and hash the exact raw-event, canonical-text, and deterministic
   `EXPANDED_EQUIVALENT` artifacts for each proposed load; record exact bytes,
   exact pinned-tokenizer token counts under a separately authorized model-free
   procedure, and the denotational-equivalence check.
5. Print actual `R_exp` and `R_raw` and their strict pass/fail results for every
   rank/layout/precision/load, with at least three prospectively selected loads
   beyond the larger honest crossover before power or GPU work is considered.
6. Revise the present receipt's last paragraph to call it a partial physical-
   numerator/intercept receipt, not completion of note 56's pre-spend receipt.

Until those repairs exist and receive the required independent gate, the
current artifact supports **no positive physical-compression execution or
claim**. It remains a valid and useful reason to stop the proposed 8x spend.

## Advisory digest convention

The SHA-256 of the final bytes of this advisory is reported in the handoff
that accompanies the file, rather than embedded here, because embedding a
whole-file digest would change the bytes being hashed.
