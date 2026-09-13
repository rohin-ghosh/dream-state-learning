# PCFL actual-tokenizer profiling plan — September 13, 2026

Read-only API/source review; no tokenizer/model loading, remote commands,
network, qualification search, tests or native execution performed. Only this
plan was written. Main chooses whether/where to execute. No allocator change.

## Recommendation and current API distinction

**For the separate zero-fit diagnostic, first profile its existing used-surface
measurement API against Main's already-frozen four-root inventory.** This is
CPU-only and needs neither a vLLM engine nor model-weight loading/hashing.
It does NOT qualify an allocator. If the question is the cost/feasibility of
the registered allocator itself, profile the unchanged public qualifier with
a complete registry and streaming receipts, as described below. These are
different questions; do not substitute a cheaper search for the registered one.

Neither module has a CLI/main entry point. `python -m` on either is not a
profiling command. The actual APIs inspected are:

```python
# organism_v6.pcfl_tokenizer_qualification
qualify_opaque_ids(bindings, encode, tokenizer_pins, *, receipt_sink=None)
verify_qualification(result, bindings, tokenizer_pins, receipts=None)

# gpu.astra_pcfl_zero_fit_dev
build_tasks(root_wires)
measure_tokenizer(plan, tokenizer, binding, *, synthetic=False)
tokenizer_binding(actor_config)
build_manifest(plan, measurements, actor_config, *, wall_seconds,
               device_seconds, output_dir, test_only=False)
validate_manifest(manifest, tokenizer=None)
```

The zero-fit handoff still says “implementation in progress” and gives a
provisional signature. This plan follows the CURRENT SOURCE instead.

### Zero-fit scope, not a full v2.2 release

`ASTRA_PCFL_ZERO_FIT_SCOPE_2026-09-13.md` explicitly separates C0 calibration
from unexecuted training schedules. Four excluded roots produce 640 delayed
plus 160 reachout tasks: **800 fixed tasks, at most 1,952 actor calls, zero
fits/updates/adapters**. The tokenizer profile makes ZERO actor calls. Future
native use retains all controls, fixed denominators, at most12 READs/task,
cumulative2,048 actor-output and4,096 returned tokens/task, source/model
custody, and actual release evidence. No full-assay, clean ancestry,
persistence, parenting or H1/H2 qualification follows from a token check.

`measure_tokenizer` checks these surfaces using the supplied inventory:
- Every opaque ID from all four roots, including private goal IDs measured
  separately but prohibited from public prompts/service blocks. Current
  structural schema has 53 slots/root, hence212 opaque measurements.
- All800 exact initial system/user chat-template renders. It checks that
  template rendering then encoding equals `apply_chat_template(tokenize=True)`.
- Every manifested READ request and exact service block, plus `MISS`.
- Equal token lengths in its actual grouped substitution classes; one common
  opaque length4..12, unique opaque token vectors, exact text hashes and
  private-ID exclusion. It does not inspect allocator search history, unused
  EVENT_TWIN/LINK_PERMUTE classes or training schedules.

If Q is the sum of task query counts, this receipt has212+800+2Q+1 entries;
keep repeated task-specific entries, not a deduplicated sample. Continuation
assistant outputs cannot be pre-invented: the native driver checks actual
continuation rendering/token budgets as they occur. Initial context ceilings
are checked by `validate_manifest`, not by `measure_tokenizer` alone.

## Required input inventory — no substitute fixtures

For the cheapest zero-fit profile Main must supply:
1. Exact frozen four-root wire JSON list in order `excluded/0` through
   `excluded/3`, including all53 structural slots/root, and its external file
   SHA256. Do not call default `build_root(label)` to manufacture salt-zero
   IDs or treat synthetic CPU receipts as actual tokenizer evidence. No
   allocator is run or changed by the measurement API.
2. Exact tokenizer binding JSON and external file SHA256. Its CLOSED fields
   are `model_path`, `tokenizer_files`, `chat_template_sha256`; the files are
   exactly `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt`.
   Use the already-local official Qwen2.5-7B-Instruct revision
   `a09a35458c702b33eeacc393d103063234e8bc28`, linked to Main's existing model
   receipt. No copying arbitrary tokenizer files or fetching missing ones.
3. Pinned source snapshot for the seven files returned by
   `driver.source_snapshot()` (listed in the final section), its external
   JSON-file SHA256, and import root containing those same modules/docs.
4. Existing offline native interpreter/environment identity: executable/hash,
   Python version, transformers/tokenizers/huggingface-hub versions, actual
   tokenizer class and chat-template bytes/hash. The profile records these;
   it is not a replacement for later native actor environment/model checks.
5. Fresh absolute output directory, CPU wall cap and sufficient disk. No GPU
   lease is needed for this tokenizer-only action. Do not invoke
   `NativeActor`, its `_native_loader`, `Diagnostic.run`, or any writer.

No authoritative root/binding/source-receipt paths were supplied with this
request. The variables below therefore denote MAIN-SUPPLIED PINNED INPUTS,
not files I created or verified. Existing synthetic inventories cannot fill
that provenance gap merely by relabeling their receipt.

## Cheapest faithful command: used zero-fit surfaces

Prospective only. Set absolute `SOURCE_ROOT`, `NATIVE_PYTHON`, `ROOT_WIRES`,
`ROOT_WIRES_SHA256`, `TOKENIZER_BINDING`, `TOKENIZER_BINDING_SHA256`,
`SOURCE_PINS`, `SOURCE_PINS_SHA256`, and new `OUT`; export these variables.
Run from the selected source root. The proposed120-second CPU cap is a
profiling budget, NOT a measured completion-time promise.

```sh
mkdir -- "$OUT" || exit 1
set -C
env PYTHONPATH="$SOURCE_ROOT" PYTHONDONTWRITEBYTECODE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
  CUDA_VISIBLE_DEVICES='' \
  /usr/bin/time -v -o "$OUT/resource.txt" \
  timeout --signal=TERM --kill-after=5s 120s "$NATIVE_PYTHON" -B - \
  > "$OUT/stdout.json" 2> "$OUT/stderr.log" <<'PY'
import hashlib, importlib.metadata, json, os, sys, time
from pathlib import Path

def supplied(name):
    raw = Path(os.environ[name]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == os.environ[name + "_SHA256"]
    return json.loads(raw)

def save(name, value):
    with (Path(os.environ["OUT"]) / name).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
        stream.write("\n")

started = time.monotonic()
roots = supplied("ROOT_WIRES")
binding = supplied("TOKENIZER_BINDING")
source_pins = supplied("SOURCE_PINS")
for path, expected in source_pins.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
for name, expected in binding["tokenizer_files"].items():
    assert hashlib.sha256((Path(binding["model_path"]) / name).read_bytes()).hexdigest() == expected
from gpu import astra_pcfl_zero_fit_dev as driver
assert driver.source_snapshot() == source_pins
plan = driver.build_tasks(roots)
save("tasks.json", plan)
from transformers import AutoTokenizer
load_started = time.monotonic()
tokenizer = AutoTokenizer.from_pretrained(binding["model_path"],
    local_files_only=True, trust_remote_code=False)
loaded = time.monotonic()
save("environment.json", {"python": sys.executable,
    "python_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
    "version": sys.version,
    "packages": {name: importlib.metadata.version(name) for name in
        ("transformers", "tokenizers", "huggingface-hub")},
    "tokenizer_class": type(tokenizer).__module__ + "." + type(tokenizer).__name__,
    "is_fast": tokenizer.is_fast,
    "chat_template_sha256": hashlib.sha256(tokenizer.chat_template.encode()).hexdigest(),
    "load_seconds": loaded-load_started})
receipt = driver.measure_tokenizer(plan, tokenizer, binding, synthetic=False)
measured = time.monotonic()
save("measurements.json", receipt)
print(json.dumps({"status": "USED_SURFACES_MEASURED_NOT_NATIVE_RELEASE",
    "tokenizer_load_seconds": loaded-load_started,
    "measure_seconds": measured-loaded,
    "total_seconds": time.monotonic()-started,
    "tasks": len(plan["tasks"]), "measurements": len(receipt["measurements"]),
    "receipt_sha256": receipt["sha256"], "model_calls": 0, "fits": 0}))
PY
status=$?
printf '%s\n' "$status" > "$OUT/exit_status.txt"
```

Use a shell without `errexit` around the timed command so failure status is
retained. Pin the exact command and input receipts, then hash all completed
output files. `receipt_sha256` above is the module's object seal, NOT the
outer `measurements.json` byte hash. A successful tokenizer measurement is
not an executable native manifest. An exception preserves stderr/resources;
`measure_tokenizer` has NO receipt_sink and does not return a partial receipt
when validation fails. An external timeout is an incomplete profile, not a
failed scientific assay or a license to select different IDs.

## If Main specifically profiles the allocator

Use `qualification.qualify_opaque_ids` unchanged, NOT private `_qualify`
with weakened limits, synthetic mode, a sampled slot list, a larger L,
length-first seed search, alternate namespace bytes, caching/deduplication
that drops receipts, or preselected candidates. Production limits are fixed:
L=4..12 ascending; salts0..999999; first4096 admissible candidates PER SLOT
PER L; then deterministic first-solution joint traversal.

The actual public API REQUIRES all seven roots in prescribed order, every
namespace, complete named substitution classes for `grammar_row`, `query`,
`event_twin`, `link_permute`, `collision_render`, `reachout_order`, slot
coverage, and a nonempty ordered complete training-sequence registry. Each
class has at least two mates. Full training text already contains exact
chat-template/assistant/EOS bytes and must be STRICTLY `<512` tokens. The
zero-fit scope does not magically make this full-search API accept four
roots or empty training inventories. Missing full registry is an input/API
limitation; do not fabricate training strings just to run the search.

Closed bindings fields: `schema`, `source_pins`, `tokenizer_pins`,
`root_slots`, `reserved_literals`, `substitutions`, `training_sequences`,
`required_training_ids`, `render_registry_sha256`.
Tokenizer pin fields: `revision`, `files`, `chat_template_sha256`,
`encoding_policy`; policy MUST be
`preformatted_text_no_added_special_tokens_no_truncation`.
Reserved literal categories: `prompt_keywords`, `canary_ids`,
`parser_prefixes`, `other`. Freeze exact structural slot order and literal/
slot parts, required-class membership, source authorities and renderer hash
BEFORE starting. Loaded tokenizer file/template provenance is caller-owned;
the qualifier checks pin objects but does not authenticate the files itself.

Once those inputs exist, use the SAME offline load/file-pin/resource wrapper
as above, replacing task measurement with this exact public call; use a
separate fresh output directory and the same explicit120-second profile cap:

```python
from organism_v6 import pcfl_tokenizer_qualification as qualification
# Main supplies and byte-verifies complete bindings and tokenizer_pins;
# caller has already checked loaded tokenizer files and exact template.
with (Path(os.environ["OUT"]) / "candidate_receipts.jsonl").open("x", buffering=1) as stream:
    def sink(record):
        stream.write(qualification.canonical(record).decode("utf-8") + "\n")
    result = qualification.qualify_opaque_ids(
        bindings,
        lambda text: tokenizer.encode(text, add_special_tokens=False, truncation=False),
        tokenizer_pins,
        receipt_sink=sink)
save("qualification.json", result)
```

A complete pool pass for the current371 slots requires at least1,519,616
candidate measurements for ONE L, before any rejected candidates or joint
render checks. Earlier infeasible L values can each exhaust a million salts
on an early slot. This is why no honest full-search elapsed estimate follows
from mocked tests. Streaming avoids retaining every receipt in RAM; it does
not remove pool storage, search work or disk cost. Timings include receipt
serialization/I/O and cold loading. Capture resource wall/user/sys/max-RSS,
receipt bytes/count and last COMPLETE receipt context (L/root/slot/salt), and
whether the search actually returned. Do not project joint-search cost from
candidate throughput alone.

An outer timeout retains the receipt prefix and means PROFILE_INCOMPLETE,
not `VS_ASSAY_INVALID`; do not fabricate a result or inject an encoder
exception as a fake scientific failure. Preserve the prefix, not resume it
through an invented checkpoint API. A complete result still says
`full_production_qualified=False` and `ready_for_model_calls=False`.
`verify_qualification` later replays the search from recorded token IDs,
requires the full transcript as a list, and does NOT re-tokenize or certify
loaded-encoder provenance. It is unnecessary duplicate work for the initial
timing profile and must not be presented as actual-tokenizer measurement.

## Source snapshot inspected

Paths relative to the selected source root; hashes identify this read, not
permission to overwrite concurrent changes. Reconfirm pins before use.

| File | SHA256 |
| --- | --- |
| `organism_v6/pcfl_tokenizer_qualification.py` | `da30eb90a8655ec0707dd8c83c22ed08f1032dadb7a663edd7102774e0e84d3a` |
| `gpu/astra_pcfl_zero_fit_dev.py` | `0319856d22c7566c9f837f130b8e252d953e8400a304b4ae42384329017b8697` |
| `organism_v6/pcfl_vertical_dev.py` | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |
| `gpu/astra_pcfl_vertical_dev.py` | `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1` |
| `gpu/astra_pcfl_native_actor.py` | `f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26` |
| `research_notes/astra_memos/ASTRA_PCFL_ZERO_FIT_SCOPE_2026-09-13.md` | `c674b152b6147f6f8a698af065c33648eaeea7a309bbb531e2b59d022c19f29c` |
| `research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md` | `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91` |
| `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md` | `599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b` |

Qualifier authority files under `research_notes/analysis/` also byte-checked:
`2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md`
(`bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`),
`2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md`
(`5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd`),
`2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
(`683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca`).

No actual-tokenizer cost or qualification outcome is claimed. EDITSTOP.
