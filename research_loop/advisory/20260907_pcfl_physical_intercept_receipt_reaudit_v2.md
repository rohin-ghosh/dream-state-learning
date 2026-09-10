# PCFL physical-carrier intercept receipt re-audit v2

Date: 2026-09-07

Status: **fresh-context, independent, model-free and tokenizer-free re-audit**.
This review changed none of the six bound inputs, used no network, model,
tokenizer, benchmark, adapter execution, or GPU, and authorizes no scientific
run or claim. Execution was limited to the existing CPU unit suite and two
temporary fabricated safetensors containers.

## Verdict

**REVISE.** The hardened parser closes the concrete interval-partition,
duplicate-key, negative/reversed/empty-range, and floating-point threshold
defects identified by the v1 attack. The nine checked-in CPU tests pass, and
the published rank-8/rank-16/rank-64 serialized-file crossover arithmetic is
correct conditional on the reported remote file sizes.

The repair does not yet establish the stronger statement that accepted files
are the declared Qwen2.5-7B all-layer LoRA carriers. It checks the presence of
392 plausible A/B names and a common rank, but not the module-specific input
and output dimensions or an exact canonical tensor namespace. A fabricated
28-layer rank-8 file with only 3,136 elements and 12,544 payload bytes passes;
the declared architecture requires 20,185,088 elements. The test fixture
itself treats dimension-free one-by-one projections as valid, so the missing
invariant is neither implemented nor tested.

The v2 note is substantially and correctly narrowed to an **intercept
receipt**, not a complete E3 `CROSSOVER_RECEIPT`. Two claims remain too strong:
the unattached remote rerun is an attestation rather than independently
replayable evidence, and “structurally complete all-layer carriers” exceeds
what the validator proves. Positive E3 spend remains blocked.

## 1. Bound inputs and hashes

The exact local bytes inspected for this re-audit were:

| input | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md` | `95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd` |
| `research_loop/advisory/20260907_pcfl_physical_crossover_receipt_attack_v1.md` | `e383a80dff908dfb19ba887dfc802047fe5c3c24206df1ee87def1792451e052` |
| `research_loop/advisory/pcfl_crossover_receipt.py` | `74098e6f6e3aa26ce7271cb9a25fc17afc79affe6fe4a3c6567b8c00646b5081` |
| `research_loop/advisory/test_pcfl_crossover_receipt.py` | `6085a8083547f60dc82fa27793a2433dcc43fdfa0b7753388480306b4221af30` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v2.md` | `59ee6bef3776c51e80429cc3a67ede0fe7ad0ba55106f857feb9c5461183ef20` |

These match the script, test, and attack hashes printed in v2. No remote
adapter, config, full tensor manifest, or machine-readable rerun output was
available in the six-file packet, so the remote artifact hashes and acceptance
result were not independently recomputed here.

## 2. Disposition of the concrete v1 parser defects

### Closed

- Intervals are sorted and required to start exactly where the preceding
  interval ended, beginning at zero. This rejects overlap and leading or
  internal gaps.
- The final interval endpoint and summed interval lengths must equal the exact
  data-buffer length. This rejects trailing unindexed bytes and prevents
  double-counted overlap from masquerading as tensor payload.
- Negative, reversed, and empty intervals are rejected before accounting.
- `object_pairs_hook` rejects duplicate keys recursively while decoding JSON.
- Tensor records require exactly `dtype`, `shape`, and `data_offsets`, with a
  supported dtype, positive two-dimensional integer shape, integer offsets,
  and shape/dtype bytes equal to interval bytes.
- The exact gates now use integer rational arithmetic:

  ```text
  D_min = floor(B * rate_denominator / rate_numerator) + 1
  ```

  This is the correct smallest positive integer denominator for the strict
  inequality at the registered `.50 = 1/2` and `.35 = 7/20` thresholds.
- The parser requires every declared layer/module key, both A and B sides, one
  global rank, and an optional explicit expected rank.

### Still incomplete

The final item is only name/rank completeness, not architectural completeness.
For a declared rank `r`, the pinned dimensions require at least:

| module | LoRA A shape | LoRA B shape |
|---|---|---|
| `q_proj`, `o_proj` | `[r, 3584]` | `[3584, r]` |
| `k_proj`, `v_proj` | `[r, 3584]` | `[512, r]` |
| `gate_proj`, `up_proj` | `[r, 3584]` | `[18944, r]` |
| `down_proj` | `[r, 18944]` | `[3584, r]` |

The code checks only `A.shape[0] == B.shape[1]`. It never checks `A.shape[1]`,
`B.shape[0]`, the expected per-module shape, the expected per-rank total
parameter count, or an artifact-specific expected dtype/precision.

A CPU-only fabricated file containing all `28 * 7 * 2 = 392` expected leaf
names, contiguous F32 data, and rank 8 was accepted with:

```text
accepted tensor_count = 392
accepted total_numel  = 3,136
accepted payload      = 12,544 bytes
declared total_numel  = 20,185,088
```

Thus an accepted file can be smaller than the declared rank-8 carrier by a
factor of approximately 6,436.6 in element count. This does not invalidate the
arithmetic for the reported real file sizes, but it defeats using parser
acceptance as proof that a file realizes the declared architecture.

The tensor-name regular expression is also permissive on both sides of the
layer and module names. A second fabricated container whose first name was

```text
alien.layers.0.invented.down_proj.lora_A.weight
```

and whose other names used the analogous invented path passed. The parser
therefore rejects names outside its broad pattern, but does not validate the
exact current PEFT/Qwen namespace. Finally, `__metadata__` is excluded from
tensor validation without validating its type or contents, so “header schema”
should be read as tensor-record schema, not complete-header schema.

## 3. Test-coverage audit

The command

```text
python3 -m unittest research_loop/advisory/test_pcfl_crossover_receipt.py -v
```

ran nine tests in 0.013 seconds; all passed. The v2 sentence that nine CPU
tests pass is exact. The checked cases are the two published strict-rate
boundaries, one contiguous container, overlap, a leading gap, a negative
interval, one obviously unexpected name, wrong explicit rank, and duplicate
JSON keys.

The suite does not cover the full set of implementation claims. In particular,
it has no regression case for reversed or empty ranges, internal or trailing
gaps, invalid header length/top-level type, malformed tensor schema, unsupported
dtype, invalid shape/offset types, missing A/B side, missing layer/module,
out-of-range layer, inconsistent A/B rank, inconsistent global rank,
`--include-tensors`, or the CLI rank/path cardinality check. Several share code
paths with covered cases, so this is a coverage gap rather than evidence those
checks fail.

More materially, there is no test for the declared projection dimensions,
total parameter formula, exact namespace, or expected dtype. The suite's
`valid_header` deliberately uses A shape `[rank, 1]` and B shape `[1, rank]`;
that makes a useful interval fixture but cannot certify a Qwen carrier. A
28-layer architecture-valid fixture or per-module synthetic shape table, plus
one wrong-input-dimension and one wrong-output-dimension attack for every
projection family, is required before claiming architectural completeness.

## 4. Arithmetic audit

Given the reported serialized file sizes, v2's table is exact:

```text
rank 8:  2 *  80,792,096 + 1 =   161,584,193
rank 16: 2 * 161,533,192 + 1 =   323,066,385
rank 64: 2 * 645,975,704 + 1 = 1,291,951,409
```

The bf16 floors follow from the declared element counts at two bytes each:
`40,370,176`, `80,740,352`, and `322,961,408` bytes. Dividing each strict
rank-specific expanded minimum by `8 * 16,384 = 131,072` tokens reproduces
`1,232.7896`, `2,464.8009`, and `9,856.8070` after four-decimal rounding.
These are serialized-`B_life` intercepts, not observed rates, complete-actor
intercepts, or evidence that an 8x expanded artifact cannot attain the required
denominator.

No arithmetic error was found in the narrowed v2 table. The qualification is
provenance: this packet permits recomputing arithmetic from the three stated
file sizes, but not recomputing those sizes from the referenced remote bytes.

## 5. Provenance and accounting overclaim

### Remote rerun

V2 says the hardened parser was rerun against three remote artifacts and that
all passed while reproducing the v1 rows. It does not preserve or hash the JSON
stdout, the `--include-tensors` manifest, an exact invocation, or the three
input artifacts beside the note. `--include-tensors` capability is not evidence
that such output was emitted and retained. On the local packet, “the new
validator confirms” is therefore too strong; the independently supportable
wording is “the authors report that the hash-bound validator accepted the
remote files.” A SHA-bound machine-readable output remains required.

### Structural identity

Even if the reported rerun is accepted as true, passing the current validator
establishes a contiguous data partition, plausible layer/module/A/B name
coverage, and consistent rank. It does not establish module dimensions, exact
model namespace, expected dtype, or equality to the analytically declared
parameter layout. “Structurally complete all-layer carriers” must be narrowed
accordingly until those invariants are checked.

### Resource-coordinate labels

The script computes useful serialized quantities, but some output names imply
facts unavailable to a header-only parser:

- `mounted_resident_tensor_bytes_actual_dtype` is the serialized tensor
  payload calculated at the header dtype. No mount was performed, so runtime
  casting, allocator overhead, buffers, and resident bytes were not observed.
- `simultaneously_retained_checkpoint_bytes_for_acting` is set to the
  safetensors file size alone. The parser neither observes checkpoint retention
  during acting nor adds a separately resident tensor copy, so this is not a
  simultaneously-retained coordinate.
- `B_actor_total_serialized_bytes` includes only the adapter file and an
  automatically discovered sibling `adapter_config.json`. It is a known-file
  subtotal, not a complete actor total absent the auxiliary census required by
  note 56.
- The sibling config is named `common_sidecars` and charged as `B_common`
  without a sealed proof that its rank-dependent fields are common across the
  comparison rather than carrier-specific loading state.

V2 correctly lists complete auxiliary and serialized/resident/simultaneously-
retained accounting as **unestablished**, which prevents these script labels
from supporting a final compression claim. The labels should nevertheless be
made conditional or renamed so the machine-readable receipt cannot be read as
having observed runtime facts that it intentionally did not execute.

## 6. Exact assessment of v2's narrowed language

The following v2 boundaries are accurate and should be preserved:

- it is a partial, model-free, tokenizer-free intercept receipt;
- it supplies no generated-load raw/canonical/expanded denominators, token
  counts, actual `R_exp`/`R_raw`, auxiliary census, or complete resource
  coordinates;
- it does not implement note 56's complete pre-spend evidentiary receipt; and
- the scientific action remains fail-closed, with semantic-code compression
  and LoRA transport kept separate from physical LoRA compression.

The following phrases require revision:

1. Replace “the new validator confirms that their tensor layouts are ...
   structurally complete all-layer carriers” with the narrower attested result:
   the reported files passed contiguous-partition, declared leaf-name coverage,
   and rank checks; architecture dimensions and exact namespace remain open.
2. Qualify “exact current numerator/intercept evidence” and “current real
   carriers” as reported **serialized adapter-file** intercepts. Exactness is
   conditional on remote sizes not independently available in this packet and
   does not extend to the complete life-specific or actor numerator.
3. Ground the rejection of the positive 8x panel in the fail-closed absence of
   a qualifying generated-load receipt. The intercepts set demanding targets;
   without a generated denominator or upper bound they do not by themselves
   prove an 8x rate failure.

## 7. Required repair

1. Add an exact allowed tensor namespace and module-specific A/B shapes for the
   pinned architecture; assert expected dtype, per-module counts, per-rank
   total elements, and payload bytes.
2. Add regression attacks for wrong input/output dimensions and near-miss
   namespaces, plus direct coverage of missing pairs/modules/layers,
   inconsistent ranks, reversed/empty intervals, internal/trailing gaps, and
   malformed header/tensor schemas.
3. Preserve a SHA-bound `--include-tensors` JSON output for each remote file,
   with exact command, script hash, artifact/config hashes, and acceptance
   result. Until then, label the rerun as author-reported.
4. Rename serialized-payload estimates and known-file subtotals so they do not
   assert mounted, retained, common, or complete-actor facts; obtain those facts
   only through the prospective accounting manifest and runtime-coordinate
   procedure.
5. Apply the three language qualifications above while retaining v2's explicit
   intercept-only status and spend block.

These repairs are model-free and do not relax the governing result. No
positive physical-compression run or claim is warranted by the present packet.

## Advisory digest convention

The SHA-256 of the final bytes of this advisory is reported in the handoff
accompanying the file rather than embedded here, because embedding a whole-file
digest would change the bytes being hashed.
