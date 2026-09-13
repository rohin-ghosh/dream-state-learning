# PCFL offline tokenizer profile — author EDITSTOP

Date: 2026-09-13. Implementation and synthetic CPU checks complete. No actual cached tokenizer/model was loaded; no native, GPU, network, download, staging, commit, or push operation was performed. This is an allocator-cost observation tool, not qualification or release.

## Owned files and exact freeze hashes

Read-only HEAD observed: `fe3225274c72b37136961ec9c96a04921f20a3f4`.

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_tokenizer_profile.py` | `bc35b66f17dd391c396c2fd08158bf969dd0b99991cddd957141a2ff2857f679` |
| `tests/test_astra_pcfl_tokenizer_profile.py` | `301d2f7920c4abe7fea5158a565e6043f6e4cf249b661f92e476f5ff71aa21ba` |

Read-only dependency pins at validation:

| Dependency | SHA256 |
| --- | --- |
| `organism_v6/pcfl_tokenizer_qualification.py` | `da30eb90a8655ec0707dd8c83c22ed08f1032dadb7a663edd7102774e0e84d3a` |
| `organism_v6/pcfl_vertical_dev.py` (optional roots only) | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |

Other workers' dirty manuscript, rules, zero-fit source/test files were left untouched. Only the two owned source/test files and this handoff were authored.

## Main's execution interface (NOT run here)

Substitute actual interpreter/cache/output paths; output must not already exist and its parent must exist without symlink aliases:

```sh
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
  /absolute/native/python -B gpu/astra_pcfl_tokenizer_profile.py \
  --model /absolute/existing/cached/model \
  --output /absolute/existing/parent/fresh-profile
```

Optional `--include-provisional-roots` adds raw `build_root('excluded/0')` through `build_root('excluded/3')` inventories. Optional `--expected-pins /absolute/pins.json` requires exactly `{"files": {"relative_file": "sha256", ...}, "chat_template_sha256": "sha256"}`. Without expected pins the tool observes and records current bytes, not certification against an independently approved tokenizer.

`run_profile(model_path, output_dir, *, include_provisional_roots=False, expected_pins=None, tokenizer_loader=None, environment_reader=environment_identity, clock_ns=time.perf_counter_ns)` is the Python interface. Loader injection is exclusively a synthetic-test interface and labels results `SYNTHETIC_CPU_FIXTURE`. The normal path lazily imports AutoTokenizer and passes `local_files_only=True, trust_remote_code=False`. All four environment flags are required before loading, checked after load and after encoding; no full environment or credentials are captured.

## Exact operation and receipts

- Exactly 4096 candidate encode attempts on success: actual qualifier API `opaque_candidate('excluded/0', 'node', 0, salt)` for salts 0 through 4095, in order. No warmup, salt-count override, selection, filtering, redraw, retry, qualification, or allocator mutation. No full registry/manifest construction dependency for the default path.
- Encoding is `encode(text, add_special_tokens=False, truncation=False)`. Each candidate JSONL row preserves salt/domain, raw text and UTF-8 SHA256, actual integer token IDs, canonical-JSON token-ID SHA256, count, and measured encode nanoseconds. Duplicate strings/ID sequences are counted, never removed.
- Summary contains observed token-length histogram, distinct candidate/sequence counts, total tokens and encode time sum/min/max. Tokenizer load time, candidate-loop time (including receipt/hash overhead), and observation time are separately named; no GPU-active-time claim.
- `identity.json`: Python executable/version, transformers/tokenizers/huggingface-hub versions, safe flags, cache path, candidate domain, and profile/qualifier source hashes; optional core source hash. Scientific records remain separate from imported APIs.
- `tokenizer.json`: exact loaded chat template string/hash, loader class, tokenizer-file pins, and load time. Required files are `tokenizer_config.json` and `tokenizer.json`; named config/vocabulary/special-token files and discovered Jinja templates are also pinned. These are tokenizer/config hashes, not model-weight provenance; no weight rehash. Loaded cache path, template, source and file drift are checked.
- `profile.json`: successful `PROFILE_COMPLETE_UNQUALIFIED`, hashes of candidate/identity/tokenizer receipts, pins and summaries. Qualification, selection, allocator-change and model-call-readiness flags are false.
- Optional `provisional_roots.json` and `provisional_tokens.jsonl`: unqualified raw inventories and per-ID receipts, with per-namespace and per-root/namespace distributions. Current pinned core has 212 inventory entries across four roots, encoded separately from the 4096 candidate pool. These are identifier lengths, not full rendered grammar/query/training lengths or joint qualification.
- A fresh directory and exclusive-create files prevent this tool from overwriting/reusing prior outputs. Failures after directory creation preserve `failure.json`, phase, planned denominator, attempted candidate encodes and completed rows, then stop without success or retries. Partial receipts must not be read as a complete profile. This is write-once application behavior, not filesystem tamper protection.

## Checks and limitations

Command executed:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_astra_pcfl_tokenizer_profile -q
```

**20 tests PASS, 1.072s.** Synthetic fixtures only: exact real generator ordering/count, raw ID/hash receipts, no filtering, mixed lengths, actual provisional core inventories, write-once paths, offline rejection, fake-transformers local-only loader kwargs, expected pins, model-weight hash exclusion, partial failure/no retry, invalid IDs, file drift, wrong cache path, CLI dispatch/help and package identity. AST parsing and trailing-whitespace checks PASS for both owned files. Direct CLI `--help` PASS without tokenizer load. No other workers' tests were duplicated.

Main still needs to run the tool on the actual cached tokenizer and archive its measured receipts. One finite sequential timing observation cannot establish throughput across hosts/cache states or approve the production allocator. No full manifest, tokenizer qualification, model execution, native readiness, experiment release, parenting, amortization, H1/H2 or mission-completion claim follows from these CPU tests.

EDITSTOP: source/test hashes above are frozen for Main review and integration.
