# Q0 executor gap map for Astra

**Date:** 2026-09-13 UTC  
**Scope:** independent implementation-readiness audit only. I changed no
builder source, Q0 material, objective, threshold, model/tokenizer state,
adapter, job, or GPU process. I did not run a model, tokenizer, benchmark, or
test suite.

## Verdict

The closed pair-balanced natural-common-prefix Q0 is **ready to implement but
not implemented**. The scientific bytes are already sufficiently specified
for the first root. The two required files do not exist:

```text
gpu/astra_pairwise_q0.py
tests/test_astra_pairwise_q0.py
```

Astra does not need another objective/threshold/design round. It needs one new
executor, its focused tests, a fresh native preparation, and one bounded run.
The work is substantial but localized. The hardest parts are the FP64
first-update canary, exact dynamic lifecycle, and failure-proof reducer—not
the task material or ordinary PEFT plumbing.

The first root can be built without any dependency on SEQ-120 or the born
RuleGame formation. The historical Q0 root is still present on node 3 and its
four critical hashes still match the committed evidence. This is later-run
contamination-free, but it is intentionally a **researcher-supplied synthetic
writer test**, not clean child experience or a learning-agent result.

One separate paper-level gap remains: the minimum manuscript path requires two
unchanged confirmation roots after the first terminal, but the exact opaque-ID
and optimizer-seed allocation bytes for those two roots are not yet pinned in
an implementation artifact. That does not block the registered first root. It
does need an output-blind confirmation-root manifest before anyone can choose
or replace confirmation roots.

## Binding protocol, in precedence order

1. `2026-09-12_pairwise_binding_falsifier_adjudication.md`
2. `2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md` (binding
   amendments where prose differs)
3. `2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md`
4. `2026-09-12_q0_claim_bearing_implementation_preflight.md`
5. `2026-09-12_iclr2027_minimum_empirical_claim_path.md` and
   `2026-09-13_seq120_q0_priority_decision.md` for units, deadline, and claim
   use—not for changing root-1 scientific bytes.

Frozen first-root facts include root-1 orientation
`[0,1,1,0,1,0,0,1]`, actions `-mem2reg/-gvn`, rank 8, alpha 16, dropout `.05`,
all seven projection families, seed 1, AdamW `3e-5`, and 128 quartet updates
per completed fit. Mandatory maps are `P_AUTH` and exact-complement
`P_DERANGED`; there are at most three attempted fits.

## What exists now

### Sealed source material

The committed capsule exists at
`research_notes/astra_memos/receipts_20260912/astra_semantic_writer_terminal_20260912.tgz`:

| object | SHA-256 |
|---|---|
| terminal capsule | `422b27e55f794cd14670f049ad09fd31b95887aa615c4d59bc0a03687e83dcf0` |
| archived `manifest.json` | `f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830` |
| archived `material.json` | `769ee38ab444c9e56b6ce7dbf93be95f49e113ca7a60e02322349a53c3ef4336` |
| archived `fits.json` | `8946700f4b94078bc6d15ffd24cfe29c364783f672e90ff36a69a5b077b78aec` |
| archived `SEAL.json` | `71f164765d1cdfeef96b881da6eac68de05f1921989f1b167f7dff7b6f088d71` |

Root 1 contains exactly 128 training rows per old map, 64 held rows, locality
families of `8 missing + 8 unsupported + 16 neighbouring`, eight native-copy
items, and the other root's 64 held rows for wrong-root evaluation. Its eight
opaque tools, eight neighbours, prompt templates, and ordering are already
materialized.

A read-only node-3 check at this audit found the original directory
`~/astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1`, the original
source snapshot `~/astra_sources/d160e0b...`, and the original carrier proof
in `/tmp` all still present. The four hashes above match in place. Thus the
current hard-coded `verify_original` route is operational now; Q0 does not
need a reconstruction from later experimental data.

### Reusable implementation surfaces

Use these as hash-pinned helpers, not as scientific logic to inherit blindly:

- `semantic_writer_diagnostic.build_material` and `render`: frozen task
  topology and native Qwen chat rendering.
- `astra_semantic_objective_probe.verify_original`: original
  manifest/seal/material verification. It currently relies on the live node-3
  original and its pinned absolute dependencies; the new preparation must
  preserve this check or explicitly validate the committed capsule projection.
- `multikey_writer_gateway_simple`: canonical JSON/digests, file/tree hashing,
  checked paths, write-once artifacts, snapshot/environment pins, local-only
  tokenizer loading, deterministic Torch configuration, model loading,
  LoRA tensor/inventory hashes, GPU identity/idle checks, and output-FD
  custody.
- `semantic_writer_diagnostic.fit_model`: only the exact clean-base rank-8
  LoRA/AdamW construction. Re-audit every field immediately.
- `semantic_writer_diagnostic.load_eval_model`: fresh base plus a fixed saved
  snapshot, after adapting its old directory assumption in the new executor.
- `writer_interface_calibration._generate` and
  `semantic_carrier_diagnostic.strict_output`: unprefilled greedy generation
  and strict output parsing.
- `run_reasoning_neutral.run_worker` or the existing carrier bounded-worker
  pattern: owned process-group termination and per-stage GPU-release evidence.
  Select one custody path and bind it; do not combine two subtly different
  cleanup contracts.
- `gpu/astra_semantic_objective_probe.py`: a useful five-stage controller and
  source/input/worker receipt skeleton. It is not the Q0 trainer or reducer.

The helper source hashes named in the earlier implementation preflight remain
unchanged at this audit: objective probe `98a90f33...d41`, semantic writer
`d6ea45ac...db0`, gateway `b9fd33c7...10c8`, and interface generator
`9ab582eb...6c7`.

### Existing tests

The reusable regression surface has 105 existing test methods:

```text
tests/test_semantic_objective_probe.py       20
tests/test_semantic_writer_diagnostic.py     17
tests/test_multikey_writer_gateway_simple.py 68
```

If the new executor imports the interface and supervisor helpers directly,
also run their 11 and 22 tests respectively. Prior Linux receipts establish
these components separately, but there is no focused Q0 suite and no combined
Linux receipt for the not-yet-written executor.

## What must not be reused

- `train_adapter_v3`, `semantic_writer_diagnostic.train_rows`, and
  `multikey_writer_gateway_simple.finite_train_step`: they implement ordinary
  full-response, one-row training rather than the explicit quartet P/V loss.
- Old candidate scoring, `score_sums`, `cell_gates`, reducers, or terminal
  classifiers: they contain the obsolete unequal-shape/BF16 and normalized-TV
  surfaces.
- Any complete target-shaped labels/masks after the decision point.
- Any fitted Q0, SEQ-089, SEQ-120, birth, or born-formation adapter.
- Any Level-1 corpus, target, template, failure location, threshold, or
  outcome.

## Minimum executor decomposition

One module can contain all of this; separate modules are not scientifically
required.

### 1. CPU/native preparation and seal

- Read only the archived root-1 material and clean-base identity.
- Independently encode both complete legal continuations for all 128 exact,
  64 held, 96 locality prompts.
- Derive the maximal common token prefix and prove it ends at natural
  `ACT: -`; discover branch IDs rather than trusting literals `10536/21404`.
- Store assistant/user boundaries and prove the forwarded assistant suffix has
  no branch, LF, EOS, padding, label, or target-shaped tensor.
- Prove target flips leave decision-input IDs and hashes identical.
- Build 32 target-free quartets from the registered pair/schedule digest
  domains, serialize once, and repeat the same order four times.
- Require exact topology, 64/64 action balance in both maps, quartet 2/2
  balance, exact/held template disjointness, panel-prefix disjointness, and
  complete locality/copy inventory before model load.
- Bind the Qwen public repository/revision
  `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`
  plus the local model/tokenizer file inventory. Historical Q0 remains
  unresolved; the new claim-bearing run need not.

### 2. Zero-update objective audit

- Fresh seed-1 zero-B rank-8 initialization, matching every later fit by
  ordered trainable inventory, initial tensor digest, and step-zero logits.
- Natural-prefix BF16 forward logits cast to FP32 as `z_train32`.
- Explicit `L_P=softplus(-s*d)` and
  `L_V=logsumexp(z)-z[target]`; never native `output.loss`.
- Record all 128 legal-token masses `M` and `-log(M)`.
- For all 32 quartets record ordered P/V gradient digests, norms,
  `norm(V-P)`, `R`, and cosine. A present finite near-zero P gradient takes the
  registered scientific `ZERO_XOR_TANGENT_AT_INIT` branch; a missing,
  disconnected, nonfinite, or wrong-inventory gradient is an integrity abort.
- Seal the objective-degeneracy decision before any fit.

### 3. Contemporary OFF

- Fresh exact model load and the same final readout implementation used by ON.
- Require native copy `8/8` before a fit is launched.
- Preserve every exact, held, locality, copy, prefix-logit, and strict
  generation record. There is no historical-OFF substitution.

### 4. Dynamic fit lifecycle

- `P_AUTH`: the first scheduled quartet is update 1. If its four analytic
  projections and four observed margins pass, continue in the same
  model/optimizer/RNG process through update 128; otherwise seal after one.
- After an AUTH canary miss, run exactly one DERANGED canary update, then stop
  it and optionally run unary under the frozen release table.
- After an AUTH pass, run `P_DERANGED` normally. Optional `V_AUTH` or unary is
  chosen only by the sealed precheck/canary/exact-acquisition table.
- Every update performs four separate natural-length forwards in the fixed
  order, averages the four explicit losses, then one backward and one AdamW
  step. No batching/padding shortcut.
- Hash pre-forward CPU/CUDA RNG state for every actual row forward and require
  cross-arm identity where causally compared.
- Save immutable LoRA-only snapshots at updates 32, 64, 128 without changing
  model, optimizer, or RNG state. No pause/resume, checkpoint selection,
  alternate seed/rate/rank/order, or retry.

### 5. Analytic first-update canary

- In a state-neutral dropout-off block, compute each signed
  `d_canary64` gradient from FP64 hidden-state/output-head products.
- Prove diagnostics leave tensors, buffers, `.grad`, RNG, mode, and empty
  optimizer state unchanged.
- Preserve the actual dropout-active FP32 parameter delta from update 1.
- For all four prompts require both signed `<grad(d),delta>` and signed
  observed-margin improvement above prospectively coded FP64 accumulation
  error bounds. Store dot, absolute product sum, error bound, ratio, and the
  signed 4-by-4 Gram matrix.
- A miss describes this exact sampled seed/quartet/dropout path. It is not a
  universal LoRA-gradient claim.

### 6. Fresh snapshot readout

- For updates 32 and 64: all `128 exact + 64 held` natural-prefix margins.
- For update 128: the same margin panel plus strict generation on all 192
  exact/held prompts, q/M and strict generation on all 96 locality prompts,
  and eight native-copy prompts.
- Fresh base load for every snapshot, bound to adapter directory and LoRA
  tensor digest.
- Preserve raw generated IDs/text, EOS/truncation/multiple-ACT state, closed
  action enum, request/load/adapter/source hashes, attempts=`1`, and every
  denominator.

### 7. Pure reducer, terminal, replay

- Reconstruct material, token projection, schedule, requests, release path,
  and fixed denominators before scoring.
- Enforce every inclusive acquisition/complement/interface/locality threshold
  and adjacent failure literally. OFF and both P maps alone determine the
  primary Q0 label; optional arms receive suffixes and cannot veto it.
- Apply integrity-before-science terminal precedence exactly as closed.
- Seal raw files, adapters, logs, stage receipts, resource accounting, source
  and input pins, then run CPU/read-only reducer replay and demand exact report
  bytes.
- Prove the owned process group and selected GPU are empty before terminal
  release.

## Minimum focused test matrix

`tests/test_astra_pairwise_q0.py` must cover, before any real launch:

1. Material counts, maps, balance, target-free schedule golden bytes, map-flip
   input invariance, exact one-row-per-sweep coverage, and every leakage/panel
   collision mutation.
2. Native Qwen chat/token boundary on every pairwise item, candidate-order
   reversal, branch-ID discovery/check values, no truncation/padding/fallback.
3. Real CPU Torch P/V equations, target reversal, outside-pair V gradient,
   zero/near-zero P branches, and every degeneracy boundary at equality and
   one adjacent failure.
4. Real-autograd/AdamW canary toys: true XOR passes; constant, mode-only,
   tool-only, and unary cheap policies take their registered paths.
5. FP64 error-bound equality/adjacent failure, multiplication-before-sum,
   signed Gram definition/tolerance, and held even-median convention.
6. State/RNG/initialization/optimizer invariance and deliberate mutation of
   RNG, buffers, `.grad`, mode, parameter ordering, or optimizer fields.
7. Exact update/forward/snapshot counts, dynamic release table, every early
   stop, V non-veto, no retry/resume, deadline/lease stop, worker failure,
   cleanup, and GPU-release proof.
8. Closed strict-action enum and every reducer gate at its inclusive boundary
   and adjacent failure: class recall, key coverage, complements, q/M mean and
   tail, A/I integer limits, transitions, copy, wrong-root opposites, optional
   qualifiers, and integrity precedence.
9. Complete synthetic pass/failure raw fixtures, immutable seal, exact replay,
   missing/duplicate/extra/retried/nonfinite/tampered record rejection.
10. A dependency-allowlist test and preparation receipt that excludes all
    SEQ-120/birth/born-formation files, adapters, outputs, and source hashes.

Then run the new suite plus the untouched 105-test objective/writer/gateway
regression suite in the bound Linux execution environment. If interface and
supervisor helpers are imported, run those additional 33 tests as well. The
earlier macOS 105-test attempt is not admissible because repository path and
GNU-timeout assumptions failed there.

## Exact minimum receipts

The terminal should contain at least:

- prepared manifest; contract/source/dependency allowlist; archived source
  pins; public+local base/tokenizer pins; rendered/tokenized material;
  decision-prefix inventory; schedule; panel/request inventory; CPU/native
  test receipt;
- objective-audit raw rows/quartets and sealed arm-selection receipt;
- one OFF load plus complete raw prefix/generation/copy records;
- per attempted fit: job/start/load, ordered initialization and optimizer
  receipts, every step/RNG record, canary before/delta/after artifacts,
  snapshots and adapter/tensor hashes;
- per snapshot: fresh-load receipt and complete raw readout records;
- per worker/controller: command, PID/start time, deadline, stdout/stderr hash,
  finish status, exact work counts, owned-group/GPU cleanup;
- pure reducer output with all numerators/denominators and terminal subtype;
  full immutable inventory/seal; exact replay receipt; final resource and GPU
  release receipt.

An integrity abort must preserve its partial raw evidence but cannot become a
scientific failure label. A valid early canary stop is a scientific terminal.

## Work and cost arithmetic

For two completed mandatory P maps, excluding small repeated canary forwards:

| operation | count |
|---|---:|
| training updates/backwards | 256 |
| training row forwards | 1,024 |
| zero-update audit prefix forwards | 128 |
| snapshot/OFF prefix readout forwards | 1,632 |
| strict generation requests | 888 |
| maximum generated tokens at 32/request | 28,416 |
| fresh workers/model-load stages if every snapshot is isolated | 10 |

The optional completed third fit raises these to 384 updates, 1,536 training
row forwards, 2,304 readout-prefix forwards, 1,184 generations, at most 37,888
generated tokens, and 14 fresh worker/load stages. Early stops reduce all of
these.

Measured anchors: SEQ-089 used two old 256-row-step fits plus 384 generations
and 384 margin forwards in `576.104` seconds. The older four-fit semantic Q0
with 14 stages and 1,712 requests used `1,414.695` seconds. This executor uses
fewer backward steps but more exact prefix/locality readout and more expensive
gradient auditing. A defensible unprofiled expectation is roughly **15--35
minutes for a two-fit root**, potentially approaching the registered
**2,700-second / 0.75 A40-hour ceiling** with the optional third fit. The cap,
not that forecast, is binding.

Three paper roots cost at most **2.25 A40-hours**. After the first valid root
freezes the executor, two confirmations can run on two isolated A40s in
parallel for at most another 45 minutes of wall time. Implementation and raw
audit, not GPU capacity, dominate the calendar. Based on the existing helper
coverage, the implementation is plausibly a focused **6--12 builder-hour**
task; the numerical/state tests are the uncertainty.

## Isolation from SEQ-120 and born formation

The dependency closure is clean if enforced as above:

- the archived Q0 capsule/material/source all predate SEQ-120 and are already
  content-hashed;
- current reusable Q0 helper hashes match the pre-SEQ-120 implementation
  preflight;
- no Q0 executor exists that could already have absorbed later bytes;
- the only shared object is the frozen public base model, which is an intended
  common starting point, not a learned adapter;
- SEQ-120 and born formation are not needed for material, target maps,
  schedules, thresholds, model construction, or readout.

The new source manifest should be an allowlist and fail if it sees
`birth_conditional*`, born-formation modules, their capsules, their adapters,
or their roots. Do not copy a useful lifecycle pattern from those files into
Q0 now; use the already predeclared Q0/gateway/objective helpers instead.

## Astra's shortest safe path

1. Create only the new executor and focused test file; leave all archived
   modules byte-identical.
2. Implement material/objective/reducer as pure helpers first, then the
   dynamic worker/controller.
3. Run focused plus archived regressions on Linux; seal the result.
4. Native-prepare root 1 from the still-live archived source; bind current
   public/local model provenance; inspect only preparation receipts.
5. Run one serial A40 terminal under the 2,700-second cap; preserve either pass
   or valid failure and replay it from raw records.
6. Independently raw-audit it. Freeze source/recipe bytes. Before confirmation,
   bind exactly two output-blind fresh-root/optimizer-seed allocations, then
   run both without replacement or outcome-conditioned change.

No SEQ-120 repair, parenting run, rank/LR sweep, or further governance round is
on this critical path.
