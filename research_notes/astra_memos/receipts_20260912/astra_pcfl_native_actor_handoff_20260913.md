# PCFL C0 native actor — early API, 2026-09-13

Implementation/testing in progress. No native/model/tokenizer/network execution
has occurred. Current PCFL runtime remains frozen and native-blocked.

`gpu.astra_pcfl_native_actor.NativeActor(config, loader=None,
environment_reader=environment_identity, clock=time.monotonic)` is lazy:
construction/import has no file writes or model/tokenizer imports. Explicit
`start()`, `generate(request, limits)` or `count_tokens(text)` starts execution.
Injected loader/environment/clock support CPU tests without installed native
libraries. `scripted=False` always: this adapter cannot sneak through the
frozen runtime's scripted-only entry.

Config fields are closed: `schema`, `model_path`, `model_binding`,
`source_files`, `tokenizer_files`, `chat_template_sha256`, `tokenizer_probe`,
`environment`, `gpu_uuid`, `engine`, `output_dir`, `deadline`,
`device_seconds_cap`, `max_input_tokens`, `max_output_tokens`, `max_calls`.
Schema is `pcfl.c0_native_actor.v1`. Main supplies the actual local official
public model receipt `{path,sha256}` and source-file SHA map including the
actually imported actor file. Environment pins python/version and six package
versions. Model files are streamed/hash-checked once on explicit startup;
subsequent calls check recorded path/stat identities, not another 14GB hash.
No model hash was performed by this worker.

Public `request` has exactly `{id,messages,seed,mount:'C0'}`. Messages have
only role/content, one initial system and alternating user/assistant history
ending in user. Runtime `limits` are the current five fields plus optional
`input_tokens`; result retains its current five-field response schema.
Raw request, render/input tokens, sampling, output tokens/text and response
receipts are separate write-once files in a fresh caller-owned output root.

`close()` reports engine shutdown only. It returns `owned_group_released=None`,
`gpu_vacant=None`, `outer_release_required=True`: Main's outer controller must
enforce hard timeout and verify actual process/GPU release. The actor never
claims a production-D/scientific/native-ready gate or implements formal C11.

Frozen pattern read: `/tmp/astra_birth_skill_probe_run_20260913.py`
SHA256 `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`,
especially `render`, `public_model_files`, and `Native`. No import of that
runner, its scientific targets, old fixed token cap, or shared trainer is used.

---

## Final author handoff — EDITSTOP

Only these assigned files were written:

| Path | SHA256 |
|---|---|
| `gpu/astra_pcfl_native_actor.py` | `f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26` |
| `tests/test_astra_pcfl_native_actor.py` | `cee367063f524a6d23d1d51259431fa7dd267ac60162d4beececa07fcf5ed354` |
| this `/tmp` handoff | reported separately, not self-hashed |

### Caller bindings and execution

- `model_path` is the absolute local official snapshot path. `model_binding`
  names the existing public model receipt and its exact SHA; repository,
  revision, 14-file inventory, public-match tags, sizes and actual file hashes
  must match. No remote-name fallback or adapter files are accepted. Model
  hashes are read once per actor startup; later operations check recorded
  path/device/inode/size/mtime/ctime identities. Main can reuse one loaded
  actor across the roster. Hashing is real startup work, not a free cache claim.
- `source_files` maps absolute source paths to SHA256 and must include the
  actually imported actor file. `tokenizer_files` maps the four names
  `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt` to the
  matching public manifest hashes. `tokenizer_probe={text,token_ids}` and
  `chat_template_sha256` bind loaded tokenizer behavior and exact template.
- `environment={python,version,packages}` pins the resolved interpreter path,
  `sys.version` and versions of vLLM, Torch, Transformers, tokenizers,
  safetensors and huggingface-hub. The native loader requires
  `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`,
  `HF_HUB_DISABLE_TELEMETRY=1`, `VLLM_NO_USAGE_STATS=1`, and exactly the bound
  `gpu_uuid` in `CUDA_VISIBLE_DEVICES`. It neither sets these nor logs other
  environment values. Main/outer controller verifies actual device ownership.
- Supply `engine` equal to exported `ENGINE`: bf16, TP1, eager, 16,384 context,
  memory fraction .85, prefix caching off, `enable_lora=False`, remote code
  disabled. Sampling is greedy single-output with penalties inherited from
  the frozen public runner; only request seed and remaining output cap vary.
  Every call uses `lora_request=None`. No stop-line trimming or repair is added.
- `max_input_tokens` is caller-bound up to 16,384; `max_output_tokens` up to
  2,048; `max_calls` up to the zero-fit maximum 1,952. `deadline` is in the
  same monotonic-clock domain as the actor; `device_seconds_cap` is positive
  and at most 36,000. The actor does not invent a roster or derive these caps
  from responses. Return/read cumulative accounting remains the runtime's job.
- `output_dir` must not exist, including as an empty directory or symlink.
  Its parent must already exist without symlink aliases and be disjoint from
  the model tree. Explicit execution creates it once. Every artifact uses
  exclusive creation plus flush/fsync; there is no resume, overwrite, retry,
  collector or automatic archive operation.

Typical Main-owned lifecycle is explicit construction, optional `start()`,
the planned `generate`/`count_tokens` calls, then `close()` in a `finally`
block. `count_tokens` on an unstarted actor also starts its model-backed
session; use the separate tokenizer qualifier for tokenizer-only preparation.
Construction and unused `close()` do not create a directory or load anything.

### Receipt and failure semantics

Artifacts are `config.json`, `identity.json`, `load.json`, indexed
`call_NNNN.request.json`, `.render.json`, `.raw.json`, `.response.json`,
`count_NNNN.json`, and `close.json`. Failed work keeps `.error.json` or
`load_error.json`. Native bad-cardinality captures are retained before
rejection. A caller/reducer must honor error/close status, not select an
isolated raw output as a successful call. Partial files after a hard kill
remain incomplete evidence; there is no automatic recollection.

Template-generated token IDs must equal explicit encoding of the rendered
prompt, the actual Qwen system segment must equal the supplied public system
message, and returned engine prompt IDs must match. Output IDs are counted
exactly, including whatever the engine returns; decoded text must equal raw
output text, with no stripping or Unicode normalization. UTF-8 SHA/hex and
raw output tokens are preserved. Receipt dictionaries are detached from
caller inputs and returned response mutations cannot change recorded bytes.

Once an execution fails, the actor refuses further generation. IDs cannot be
reused; concurrent calls and exhausted call budgets fail without retry.
Invalid public API schemas fail before model load. Request/message keys are
closed, rejecting oracle/scorer/private/cell/adapter metadata. This is a
structural public interface, not a semantic classifier for arbitrary prose;
Main's sealed scheduler remains responsible for the origin of message text.

Timing separates preparation-inclusive `operation_started`,
`model_load_started`/`ready_at`, and `generation_started`/`generation_ended`.
Returned `device_seconds` is the actor operation's measured wall interval,
including lazy startup when applicable; it is **not GPU active time**.
`close.elapsed_actor_seconds` includes all completed actor operations,
standalone token counts, and shutdown. The outer controller must account for
reservation, between-call gaps and remaining process-release work without
double counting these intervals. No profile/throughput result is asserted.

### Hard boundaries retained

The actor performs finite local source/model/tokenizer checks. It is not a
production-D definition, full prepared-plan validator, scientific gate,
parenting/amortization result or formal C11 guard. No model was trained.

An in-flight LLM constructor/generation/tokenizer call cannot be interrupted
by the actor's post-return clock checks. **The outer controller must enforce
hard process timeout, lease margin and cleanup**, including partial loader
failure. Call `close()` even on validation/generation exceptions; an absent
or failing engine shutdown method does not certify vacancy. The close receipt
deliberately leaves `owned_group_released` and `gpu_vacant` null, so Main must
combine actual outer release evidence rather than replace these with True.

The existing runtime was not edited and still rejects a native adapter at
its scripted-only entry. Its hashes remain:

- runtime: `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1`
- runtime tests: `5a5e81688d2c9598d6cbc9d1e285b10d7258589e9d358ea509475b19fbf12af5`

### Validation actually performed

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_astra_pcfl_native_actor -q
Ran 32 tests in 0.593s — OK
```

All model/tokenizer objects and package identities are injected CPU fakes;
model-named files are tiny synthetic test payloads. The native loader function
itself is also exercised with fake vLLM/Torch modules to check exact arguments,
C0/LoRA=None, sampler caps and shutdown—not with actual native libraries.
Coverage includes lazy startup, closed public API, immutable files, context/
token/time limits, no retry, identity drift before/after load, full raw failed
outputs, distinct load/generation timing and honest outer-release status.
AST parsing and direct trailing-whitespace checks pass on both owned files.
No other worker's tests were rerun.

Local status/HEAD and applicable instructions were read before writing; no
pull was attempted because network was forbidden. Main advanced HEAD from
`b4911b62` to `e8f5095b` during this task. All unrelated code, manuscripts,
rules and evidence were preserved. No Git mutation, external send, real
model/tokenizer execution, model download, native/GPU call or process launch
was performed by this worker. Main retains assembly and native execution.
