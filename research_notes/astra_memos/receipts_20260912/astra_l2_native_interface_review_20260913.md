# Bounded L2 native-interface source review

Reviewed 2026-09-13, closed 05:48 UTC. Read-only sidecar; only this memo written.
Root instructions apply; no nested AGENTS.md found under gpu/organism_v6/tests.

## Disposition

**No concrete launch-blocking integration bug found in wrapper 213c2a2 / tests
d2ebe1 against the inspected core, unchanged trainer and local public/reflection
helpers.** No source repair requested. This is not native acceptance, a final-C11
review, or a new launch gate. Main retains staging/launch authority. Scope remains
PROMOTE/SHADOW, three actual fits maximum, not a five-fit/MISBOUND live comparison.

One provenance clarification for Main: the current local protocol file hashes
to `638936cf…`, not the earlier message's `ae304738` prefix. I did not receive a
staged specification with which to resolve that difference. The current source
protocol and wrapper agree on seeds 2026091301/2026091302/0 and maxima
128 calls / 3 fits / 100 updates. This is not evidence of a wrapper defect; use
the actually accepted protocol pin when staging, rather than assuming the old
shorthand identifies the bytes reviewed here.

## Concrete interface checks

1. **Core and public/helper calls match.** Wrapper `load_apis` (line 210) loads
   the explicit four-file snapshot and two pinned helper paths. Core wire decode,
   captured-block reconstruction, `close_block`, `complete_sleep`, `check_pair`
   and routing calls (332–380) match actual core signatures and data types.
   `public_model_files(receipt, model)`, `native_tokenizer(model)` and
   `render(tokenizer, messages)` exist with the consumed return fields in
   `/tmp/astra_birth_skill_probe_run_20260913.py:171,192,213`.
   Reflection `environment(probe)`, `load_native_model(model)` returning
   `(tokenizer, base)`, and `check_adapter(adapter, config)` match at lines
   153, 421 and 454. Public `gpu_state(plan)` expects exactly the used GPU
   identity fields; `cleanup(process)` accepts the passed process object.
   No stale reflection-corpus or old-core signature was found in these calls.

2. **Actual trainer masks and manifest keys match.** Wrapper `encode_training`
   (390) checks the exact core-exported child action, explicitly renders the
   same generic system/user prefix as inference, adds the native assistant EOS,
   and masks prompt and template-only tail. Its `chat_template=False` and
   `add_eos=False` are deliberate: supplied spans are already templated and
   contain one supervised EOS, not raw untemplated actions. The actual v3
   `normalize_items`, `encode_item_segments`, `pack_by_group`, `epoch_order` and
   `collate` functions are called, not a replacement encoder. Prefix/full-token
   equality, no truncation/splitting, per-row labels and padded batch masks are
   checked before fitting. Wrapper `validate_manifest` (460) uses keys actually
   emitted by trainer `run_training` (657; manifest at 711, packing at 779,
   completion at 852): corpus counts/hash, truncation, token categories/views,
   `train_tokens_seen`, steps/micro-batches/epochs and loss arrays. The explicit
   `child_action` plus `assistant_end` categories and 20× token exposure align.
   Returned and durable manifests are compared. No manifest-key mismatch found.

3. **Publication versus SHADOW is connected correctly.** `route_for` (366)
   returns None for base/SHADOW, with a base-identity assertion; PROMOTE resolves
   the matching completed first or second candidate inventory. `Native` (527)
   supplies either None or `LoRARequest(name, id, path)` to `LLM.generate`.
   Each inference stage creates its own engine; request ID reuse across separate
   workers is not an adapter-cache collision. Shared SLEEP1 is performed once;
   both states reference the same candidate bytes. Each SLEEP2 uses its own
   reconstructed cumulative corpus. SHADOW's fitted candidates are retained but
   not mounted. Captures/readouts are replayed against routes and source receipts.

4. **No unintended warm-start/shared mutable-base path found.** Each fit worker
   calls reflection's fresh `from_pretrained(... local_files_only=True)` loader,
   rejects an existing PEFT configuration and invokes the unchanged trainer
   without warm-start arguments. The trainer locally wraps the supplied base
   with `get_peft_model` (737), constructs a fresh optimizer and saves adapter
   artifacts, not base files. Inspecting the supplied model's trainable names
   afterward is also the established reflection-helper pattern (482); the fact
   `run_training` returns a manifest rather than a model is not itself a call
   mismatch. Fresh process-per-stage ownership prevents an in-memory fitted
   base from becoming SHADOW's or the next fit's base. Actual native PEFT behavior
   and frozen-weight immutability were not exercised by this source review.

## Validation and limits

Ran `python3 -B -m unittest tests.test_l2_public_record_dev
tests.test_astra_l2_public_record_dev -q`: **89 passed in 10.437s**. Initial run
exceeded the shell's 10-second allowance; rerun with 60 seconds completed cleanly.
Fixtures use the real pure core/v3 encoder with synthetic tokenizer/model/process
objects; model fits, backend loads and process/GPU operations are mocked. Helper
definitions were read as source; no native tokenizer/model, GPU, network or Git
operation was performed. No source files were edited.

Remaining unexercised integration surfaces are the real tokenizer boundaries,
vLLM/PEFT loading and output behavior, actual parameter/mask execution and staged
helper/model/spec identity. The wrapper already checks relevant native values
at execution; green synthetic fixtures do not prove them. No extra guard,
threshold or optional framework is proposed. This review supports proceeding
with Main's existing native prep, not a scientific-success assertion.

## Reviewed SHA256 pins

- `gpu/astra_l2_public_record_dev.py`:
  `213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e`
- `tests/test_astra_l2_public_record_dev.py`:
  `d2ebe1e3a37c7ad7ee42e07aab583494d86819be7dfa7fd7cac25b392baed3f2`
- `organism_v6/l2_public_record_dev.py`:
  `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`
- `tests/test_l2_public_record_dev.py`:
  `9691e1c2b97d25a8a5bc0747bb5937ecd9281b0c52a041efbdfc9cc63499a4aa`
- `organism_v6/train_adapter_v3.py`:
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- `organism_v6/__init__.py` (empty):
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `/tmp/astra_birth_skill_probe_run_20260913.py`:
  `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`
- `/tmp/astra_reflection_fit_run_20260913.py`:
  `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`
- `research_notes/astra_memos/ASTRA_L2_PUBLIC_RECORD_PROTOCOL_2026-09-13.md`:
  `638936cfd54a791c7f517b5c93ea944002a697a1b78c6a672f04398dc3486f51`

Wrapper/test/protocol hashes were unchanged at the closing check. EDITSTOP.
