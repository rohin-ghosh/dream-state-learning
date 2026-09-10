# PCFL physical-carrier intercept receipt re-audit v3

Date: 2026-09-07

Status: **fresh-context, independent, model-free and tokenizer-free re-audit**.
This review changed none of the bound inputs, used no network, model,
tokenizer, benchmark, adapter, or GPU execution, and authorizes no scientific
run or claim. Execution was limited to the checked-in CPU unit suite,
arithmetic/consistency checks, and temporary fabricated safetensors
containers.

## Verdict

**REVISE.** V3 correctly repairs the Qwen projection-dimension and total-
element checks, uses appropriately narrowed serialized accounting names, and
keeps the complete E3 receipt gate unpassed. All 12 checked-in CPU tests pass.
Every published rank-8/rank-16/rank-64 element, payload, subtotal, strict-
crossover, and 8x16k bytes/token value is internally exact conditional on the
author-reported external file sizes.

V3 is not yet claim-safe for its stronger statements that the validator is
"pinned to the exact" Qwen namespace and that an "exact-layout validator"
accepted the remote files. The layer-name regular expression accepts
non-canonical zero-padded spellings. A fabricated, otherwise fully valid
28-layer carrier in which the 14 layer-0 leaves use `layers.00` instead of
`layers.0` is accepted with all 392 leaves and the exact expected element
count. In addition, the architecture parameters remain CLI-configurable and
the emitted validator record does not bind the validation profile. The local
v3 JSON manually states that profile, but it is explicitly a transcription,
not preserved raw stdout or a cryptographic binding between the command,
profile, and external bytes.

These defects do not invalidate the conditional serialized-adapter
intercepts, and they do not justify a **REJECT**. They require a small parser,
receipt-binding, test, and wording repair before the exact-layout claim can
pass. Positive E3 spend remains correctly blocked and the complete E3 gate
remains open.

## 1. Bound inputs and SHA-256

The exact local bytes inspected were:

| input | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_reaudit_v2.md` | `f88c709f0eff9beac55cb28170adebc04ae7cdfe0b3d9ff6804c4229e62b9cf9` |
| `research_loop/advisory/pcfl_crossover_receipt.py` | `2313990bf08996038b18d70ae01b447c939dc5463917f0be708f18168029c1a9` |
| `research_loop/advisory/test_pcfl_crossover_receipt.py` | `6e63d73326e0de8eaad652ae70aa51d6a6b95fa4ea1019e89517d6278e91265f` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v3.json` | `c0dc37908ed4abf8ad09579d99ca3b34ae986ebc2fce7fed0e2cb179138b224a` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v3.md` | `ebb817924c19a0c3908963ea40487f9ef1f9558565064ff64b9621ef6344f0d2` |

The script, test, and adopted v2 re-audit hashes printed in the v3 Markdown
match these local bytes. The v3 JSON is accurately called "SHA-bindable," not
already SHA-bound by the v3 Markdown; its digest is recorded above for this
review. The three external adapters, their sidecars, raw validator stdout, and
exact invocation are absent, so their stated hashes and acceptance results
were not independently recomputed.

## 2. Exact namespace: one remaining acceptance bypass

The fixed prefix, branch, module, side, and suffix components are enforced.
Invented prefixes and wrong branch/module combinations are rejected. The
layer component is not an exact canonical string, however:

```python
r"(?P<layer>[0-9]+)"
layer = int(match.group("layer"))
```

Converting the captured string to an integer normalizes aliases such as `00`
to layer 0 before the expected-pair comparison. The CPU attack used:

- the exact 28 layers, seven modules, and A/B sides;
- the declared module-specific shapes, rank 1, F32, exact metadata, and a
  contiguous complete data partition; and
- only one namespace mutation: all layer-0 leaf names changed from
  `layers.0` to `layers.00`.

The validator accepted it with:

```text
tensor_count = 392
total_numel  = 2,523,136
payload      = 10,092,544 bytes
```

Thus acceptance proves membership in a normalized namespace, not the exact
canonical PEFT/Qwen name set claimed by v3. Because the remote tensor names
are not locally retained and their manifest digest cannot be inverted, this
review also cannot separately show that the three reported remote manifests
used only canonical layer spellings.

The robust repair is to construct the exact expected string-name set for
every layer/module/side and require equality with the header tensor keys.
Alternatively, reject any layer capture unequal to `str(int(capture))` in
addition to the existing range check. Add a regression attack for `layers.00`
and rerun the external artifacts after the repair.

## 3. Dimensions, rank, dtype, and total elements

The module-specific dimension logic is correct:

| module | expected A | expected B |
|---|---|---|
| `q_proj`, `o_proj` | `[r, 3584]` | `[3584, r]` |
| `k_proj`, `v_proj` | `[r, 3584]` | `[512, r]` |
| `gate_proj`, `up_proj` | `[r, 3584]` | `[18944, r]` |
| `down_proj` | `[r, 18944]` | `[3584, r]` |

The per-layer coefficient is 90,112 elements, so the exact 28-layer total is

```text
expected_numel = 28 * 90,112 * r = 2,523,136 * r.
```

This yields exactly 20,185,088, 40,370,176, and 161,480,704 elements at ranks
8, 16, and 64. The reported F32 payloads are exactly four times those totals,
and the hypothetical bf16 floors are exactly twice those totals. Pair
completeness plus the exact expected layer/module key set implies 392 tensor
leaves. Expected dtype, common rank, A/B rank agreement, exact shape-derived
bytes, and exact interval partition are all checked before acceptance.

A CPU-only attack changed each input/output dimension in turn across all 14
module/side combinations while rebuilding otherwise coherent offsets. All 14
were rejected with the projection-shape error. No dimension or total-element
bypass was found.

The remaining qualification is profile binding. `expected_layers`,
`hidden_size`, `kv_size`, `intermediate_size`, dtype, and rank are arguments;
the CLI exposes all of them as options or defaults, and expected ranks may be
omitted. A one-layer profile was accepted when requested, as a generic
validator reasonably may do, but the result contained none of the expected-
profile fields. Consequently, raw output alone would not prove which profile
was applied. Emit a `validation_profile` containing every expected parameter
and the canonical namespace identifier, preserve the exact invocation, and
bind both into the raw receipt. Until then, describe the claimed 28-layer run
as author-attested rather than saying the validator itself is pinned.

## 4. Tests and schema/version audit

The command

```text
python3 -m unittest research_loop/advisory/test_pcfl_crossover_receipt.py -v
```

ran 12 tests in 0.034 seconds; all passed. The v3 count is correct. The three
new checked-in attacks cover the dimensionally tiny carrier, an invented
prefix, and one wrong `q_proj` A dimension. The implementation is stronger
than that narrow dimension coverage, as the 14 additional temporary attacks
confirmed, but the zero-padded layer alias is neither tested nor rejected.

The current script still emits top-level schema
`pcfl_physical_carrier_intercept_receipt_v2`, while the transcribed summary
uses `pcfl_physical_carrier_intercept_receipt_v3_transcribed_summary` and the
Markdown calls the repaired receipt v3. The latter is clearly labeled as a
summary, so this does not change the arithmetic, but the validator schema
should be versioned consistently when its validation contract and accounting
fields change.

## 5. Accounting-coordinate and cross-format audit

The emitted accounting names close the v2 overclaim:

- `serialized_tensor_payload_bytes_from_header` describes a header-derived
  serialized payload, not observed runtime residency;
- `adapter_safetensors_file_bytes` describes the adapter file alone;
- `discovered_config_sidecar_bytes` does not assert that the sidecar is common
  state; and
- `known_serialized_file_subtotal_bytes` is explicitly a known-file subtotal,
  not a complete actor or life-state numerator.

The old mounted-resident, simultaneously-retained, `B_actor_total`, and
`B_common` coordinates are absent. Runtime residency, simultaneous retention,
and complete auxiliary accounting remain explicitly unestablished. The
script's introductory docstring and internal variable `common_sidecars` retain
older wording, but no emitted coordinate relies on it; cleaning those names
would reduce ambiguity without changing this verdict.

The JSON and Markdown agree on status, architecture values, ranks, adapter
file sizes, element counts, strict half-rate expanded minima, and rounded
8x16k bytes/token values. For every JSON row, the following identities hold:

```text
F32 payload       = 4 * total_numel
bf16 floor        = 2 * total_numel
known subtotal    = adapter file + discovered config sidecar
strict <.50 D_min = 2 * adapter file + 1
strict <.35 D_min = floor(adapter file * 20 / 7) + 1
8x16k bytes/token = strict <.50 D_min / 131,072
```

The Markdown table is therefore an exact conditional transcription of the
JSON rows. The external artifact, config, and tensor-manifest digests remain
author-reported, which both formats now state plainly.

## 6. Scientific-claim boundary and complete E3 gate

The narrowed serialized-adapter intercept is otherwise claim-safe:

- it reports strict denominator targets, not observed rates;
- it conditions provenance through an adjacent author-observed/external-
  bytes limitation;
- it does not infer impossibility or measured failure from the intercepts;
- it keeps semantic-code compression and LoRA transport separate from
  physical LoRA compression; and
- it lists raw, canonical, expanded, runtime, retained, auxiliary, and actual-
  rate evidence as absent.

The final paragraph correctly leaves the complete E3 gate open and blocks all
positive physical-compression cells until a prospective, SHA-bound receipt
supplies the missing denominators, tokenizer-authorized counts, complete
state census, resource coordinates, actual rates, and useful post-crossover
loads. Nothing in this re-audit relaxes that gate.

V3 can become a **PASS** after the canonical layer-name repair, a bound emitted
validation profile and consistently versioned raw receipt, a regression test,
an external rerun, and replacement or qualification of "pinned exact layout"
language. No GPU or scientific run is needed for those repairs.

## Advisory digest convention

The SHA-256 of the final bytes of this advisory is reported in the handoff
accompanying the file rather than embedded here, because embedding a whole-
file digest would change the bytes being hashed.
