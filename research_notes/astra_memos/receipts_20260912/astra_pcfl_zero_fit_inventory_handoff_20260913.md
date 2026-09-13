# Scoped C0 fixed-L8 inventory — EDITSTOP, September 13, 2026

## Owned artifacts and qualification

Only `gpu/astra_pcfl_zero_fit_inventory.py`,
`tests/test_astra_pcfl_zero_fit_inventory.py`, and this handoff were written.
No Git, network, native/remote/model/GPU or actual-tokenizer execution by this
worker. Original qualifier, driver, wrapper, profiler and all other files were
left untouched. Tests use synthetic tokenizers/receipts, never model weights.

Label: `SCOPED_C0_FIXED_L8_NOT_FULL_ALLOCATOR`. This implements Main's separate
C0 inventory choice, not smallest-L/full-pool/DFS qualification or full-v2.2
release. Production requires the exact Main policy hash below, including its
explicit37 reserved literals. No canary IDs or excluded namespace substrings.

## Stable invocation for Main only — not executed here

```sh
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_HUB_DISABLE_TELEMETRY=1 timeout 180 "$PYTHON" \
  gpu/astra_pcfl_zero_fit_inventory.py \
  --model "$EXACT_LOCAL_MODEL" \
  --policy "$COPIED_MAIN_POLICY" \
  --policy-sha256 afdcf27496bdaccb7188760959d3c38f7000d00ae96e428167c052b08644b1bb \
  --tokenizer-pins "$EXPECTED_TOKENIZER_PINS_JSON" \
  --tokenizer-pins-sha256 "$EXPECTED_PINS_FILE_SHA256" \
  --public-receipt "$PUBLIC_MODEL_RECEIPT" \
  --public-receipt-sha256 a7481b25da06b3358abbaa0934c9e2d4983bc667d97cfbeac8bc3eef7ca3e3e2 \
  --output "$FRESH_OUTPUT"
```

All paths absolute; output parent exists without symlink aliases, output
does not exist and is disjoint from the model. Main chooses the exact cached
interpreter and preserves the outer timeout/log. No retry/resume CLI exists.

Expected tokenizer pins JSON is exactly `{files, chat_template_sha256}`:
extract the `pins` object of the archived profiler's `tokenizer.json`, write
it fresh, and pass its exact file hash. Do not pass the entire profiler receipt
or merely the driver's four-file subset. `files` must match the profiler's
complete local tokenizer-relevant inventory, including config.json and any
present optional tokenizer/template files. Every such file must match the
explicitly hash-bound public14-file model receipt. Additional unbound files
are not silently accepted. Actual loaded chat-template and local tokenizer
path must match. AutoTokenizer is loaded with `local_files_only=True` and
`trust_remote_code=False`; no model/vLLM loader is invoked.

Public receipt inspected locally as metadata only:
`/tmp/astra_qwen_node2_binding_20260913_attempt1.json`, SHA shown in command.
Its repository/revision are Qwen/Qwen2.5-7B-Instruct /
`a09a35458c702b33eeacc393d103063234e8bc28`. Model path must resolve to that receipt's
exact local model. The code validates all14 receipt entries as metadata, and
reads/hashes only tokenizer-related files, not weights. It is not a fresh
14-weight-file revalidation or model-ready certificate.

## API and deterministic order

```python
run_inventory(model_path, policy_path, policy_sha256,
              tokenizer_pins_path, tokenizer_pins_sha256,
              public_receipt_path, public_receipt_sha256, output_dir,
              *, tokenizer_loader=None)
```

Injected tokenizer_loader always marks outputs SYNTHETIC_CPU_FIXTURE and passes
`synthetic=True` into used-surface measurement. Production CLI has no injection.
Pure CPU seam: `allocate(tokenizer, candidate_sink, choice_sink, choices,
deadline=None)`, requiring an initially empty choices list. It is not a native
certificate API. Production uses a180-second deadline in addition to Main's
mandatory outer cap; synchronous tokenizer code still needs outer timeout.

Fixed root order excluded/0..3, then core.SLOTS insertion namespace/slot order:
N,P,E,L,Q,R,G. Exactly53 slots/root,212 choices. For every slot salts0..999999
are examined in increasing order using the unchanged opaque_candidate formula.
First candidate with8 strict integer token IDs, unique raw bytes/token vector
among already chosen IDs and no reserved substring collision wins. Reserved
check reuses the unchanged qualifier helper with the policy's exact literal
list; structural namespace prefixes remain allowed. No alternate L, pool,
backtracking, whole-root redraw, equalization, padding or model-output access.

Every completed candidate attempt includes root/namespace/index/slot/salt,
text/hash, actual token IDs/hash/count, acceptance Boolean and rejection list.
Chosen rows include candidate and choice-object hashes. Encoder errors are
recorded with traceback and stop immediately rather than skipping a salt.
Salts/roots/candidate bytes are deterministic; environment/exception paths
are provenance, not part of a claim of cross-host identical metadata.

## Files and failure custody

- `inputs.json`: policy/input hashes, source map, slot/root order, exact reserved
  set, tokenizer pins and offline flags.
- `tokenizer.json`: actual class/template/pins and package/interpreter identity;
  synthetic fixtures are explicitly marked instead of inventing package proof.
- `candidates.jsonl`, `choices.jsonl`: flushed streaming append receipts.
- `roots.json`: ordered four concrete core root wires, saved before measurement.
- `choices.json`: complete chosen records/hashes, saved before measurement.
- `plan.json`: unchanged800-task/1952-conditional-slot expansion.
- `measurements.json`: exactly one call to driver's all-used-surface measurement.
- `receipt.json`: only after used-surface, context-budget, end-source/file/offline
  checks pass. Includes output file hashes/choice hash; model_calls/fits/updates0.
- On ordinary failure: `failure.json` with complete exception/traceback/phase
  and hashes of retained artifacts, plus `unqualified_choices.json`.

All files use exclusive creation. Used-surface failure retains all212 chosen
IDs/four roots and exits nonzero: no choice repair/reselection or second
measurement. Encoder/exhaustion failures retain the partial journal/choices.
An external hard timeout may interrupt exception handling; preserve the fresh
directory and completed journal lines as incomplete, never infer qualification
from roots or measurements alone. Missing receipt.json is not a success.

Initial rendered context is also capped at14336 tokens and with2048 reserved
output must fit the16384 engine cap. Conditional future READ transcripts remain
bounded by the driver's per-call checks, not enumerated using invented output.
Standalone L8 does not waive any used-surface group matching, private-byte,
template or collision check. RA/RB keep their separate within-render groups.

Main's existing wrapper can prepare from the successful output directory's
plan.json/measurements.json; it must still validate actual measurement readback,
source/model/native environment, resource/lease/UUID/deadline and fresh outputs.
This utility never constructs a NativeActor, launches or grants readiness.
`ready_for_model_calls`, `full_allocator_qualified`, `full_v22_release` remain
false even when status is USED_SURFACES_PASSED: the scoped tokenizer stage is
complete but those separate gates have not been run here.

## CPU verification

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 -m unittest discover -s tests -p test_astra_pcfl_zero_fit_inventory.py -v
```

Final run: **19 tests PASS,3.345s**. Coverage includes212-slot ordering and
first-eligible receipts/hash replay; repeatable roots/candidates/choices;
unchanged core candidate formula; one800-task/1952-slot measurement; raw/token/
length/reserved rejection; exact policy list; encoding errors/exhaustion;
failure roots retained without retry; input/public/tokenizer/template drift;
typed tokens; context limit; CUDA/offline/deadline checks; explicit CLI bindings.
Tiny salt-domain and damaged-measurement cases are test-only mocks. No claim
that actual Qwen used-surface qualification passed; Main runs it once offline.

## Exact SHA256 pins

```text
83ef1f64b3b4130dc5521547d4f8165baac613ced7ecdcf7d12c982668227737  gpu/astra_pcfl_zero_fit_inventory.py
1351906f97f18cf5cf536fa7308d1c13196a19a668d080f558d91fd38bd81a45  tests/test_astra_pcfl_zero_fit_inventory.py
afdcf27496bdaccb7188760959d3c38f7000d00ae96e428167c052b08644b1bb  ASTRA_PCFL_C0_INVENTORY_POLICY_2026-09-13.md
b0100efe123604dde2900127663a3eda299bc60cc8fe1d40f10c045e48d73638  gpu/astra_pcfl_zero_fit_dev.py (unchanged)
bc35b66f17dd391c396c2fd08158bf969dd0b99991cddd957141a2ff2857f679  gpu/astra_pcfl_tokenizer_profile.py (unchanged)
da30eb90a8655ec0707dd8c83c22ed08f1032dadb7a663edd7102774e0e84d3a  organism_v6/pcfl_tokenizer_qualification.py (unchanged)
```

Handoff hash returned separately. No learning/full allocator/full construct/
C11/parenting/H1/H2 evidence is produced, and no future child may inherit these
authored ceiling rows as authentic material.
