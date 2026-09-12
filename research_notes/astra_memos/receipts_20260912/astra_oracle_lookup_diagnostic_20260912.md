# Oracle lookup diagnostic — frozen handoff, September 12, 2026

Implemented only new organism_v6/oracle_lookup_diagnostic.py and
tests/test_oracle_lookup_diagnostic.py. Formation, W0, calibration and their
tests remain untouched/frozen. No GPU/network/Git/remote actions were taken.
One CPU original-producer replay subprocess was exercised by the relocation test.

## Exact contrast

Source: the completed, sealed calibration, with an explicit caller-supplied
CALIBRATION_SEAL.json SHA256. Full original calibration replay is required;
the failed W0 source remains failed and read-only. The 64 chat_explicit_32
inputs/outputs are reused as a paired full-table baseline with **zero new
baseline inference calls**. Their original order must equal the first held
row for each tool/mode key, for both roots/maps.

The only new condition replaces the full table with one authentic line from
w0.oracle_prompt. Selection uses only the held row's tool/mode key, never
generated outputs or correctness. The task context, expected action, explicit
instruction, chat template, greedy seed0, 32-token cap and strict W0 parser
are unchanged. Original row bytes, context, pair/baseline IDs, rendered prompts,
input IDs and raw generated output/IDs are preserved. Maximum64 new requests.

Outputs are DEVELOPMENT_ORACLE_LOOKUP_DIAGNOSTIC / EVALUATION_ONLY with
clean_lineage=false and UNRESOLVED_LOCAL_HASHES_ONLY authentication. This is
development material, not W0 rescue, oracle qualification, new gates, training,
clean admission, persistent learning or parenting evidence. Replayed prior
full-table observations are not an independently rerun concurrent baseline.

## Relocation handling

The original calibration spec.sources absolute paths are never rewritten.
All three expected producer files (calibration module, W0 module, calibration
test file) must still exist at their original paths, match original bound
hashes, and match the bytes of the currently imported helpers by known suffix.
The strict parser hash must also match. If paths differ, the helper runs the
original retained checkout's actual calibration replay CLI in a CPU subprocess,
with cwd/PYTHONPATH set to that verified original source root; it compares the
returned report to the pinned original report. Missing/changed originals or
different imported bytes fail closed. It does not spoof module paths or patch
calibration._sources at runtime. Identical source paths use the direct replay.

Keep original calibration/W0 paths, producer checkout, and calibration external
worker log accessible and unchanged. An archive copy may be made elsewhere,
but moving/removing the original artifacts or logs is unsupported. Existing
true original replay success is preserved, not replaced with a fabricated PASS.

## Exact CLI (main only)

Run from the new checkout; use the Python environment matching the calibrated
config. This helper inherits actual model/tokenizer/environment/node/driver and
lease pins from calibration, not official authentication. Only the prospective
GPU UUID and bounded diagnostic deadline may differ. No separate config JSON
is required. OUT and LOGS must be fresh, disjoint directories with existing
parents, outside calibration/W0/model/protected roots.

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
CAL=/absolute/original/completed-calibration
CAL_SEAL_SHA256=caller_supplied_actual_completed_calibration_seal_sha256
OUT=/absolute/existing/parent/oracle-lookup
LOGS=/absolute/existing/parent/oracle-lookup-logs
GPU_UUID=GPU-actual-reserved-a40-uuid
DEADLINE_UNIX=$(( $(date +%s) + 3300 ))

python3 -B -m organism_v6.oracle_lookup_diagnostic prepare \
  --out "$OUT" --calibration "$CAL" \
  --calibration-seal-sha256 "$CAL_SEAL_SHA256" \
  --log-dir "$LOGS" --gpu-uuid "$GPU_UUID" \
  --deadline-unix "$DEADLINE_UNIX"

(
  set -C
  exec timeout --signal=TERM --kill-after=5s 3595s \
    python3 -B -m organism_v6.oracle_lookup_diagnostic execute \
      --run "$OUT" --allow-gpu \
    > "${OUT}.external.log" 2>&1
)

python3 -B -m organism_v6.oracle_lookup_diagnostic replay --run "$OUT"
```

prepare is CPU/tokenizer-only and reads/hashes local model files without loading
a model. execute alone opts into GPU use; it creates one fresh subprocess with
the explicit selected UUID, offline flags, deterministic torch configuration,
one eager HF local base, eval(), requires_grad_(False), and the existing
calibration inference_mode generation helper. Child worker stdout/stderr goes
to an exclusive LOGS/worker.log outside OUT. Parent outer log also stays outside.
Main owns reservation checks including /proc (existing compute table idle
check alone is insufficient), coexistence with formation GPUs, and outer cleanup.

The subprocess deadline is at most one hour from execute entry and before the
caller deadline/inherited lease cutoff. Requests check the deadline; parent
timeout stops its owned process group. Wrong hardware, changed input/source
pins and prior output artifacts reject. Generation failures preserve partial
raw outputs and FAILED.json, issue no complete report/seal, and cannot retry
the same directory. Normal process exit releases the model; GPU execution has
not been tested by this author. No adapter/optimizer/parameter persistence API
is used. Raw resource metadata and immutable artifacts are retained.

## Results and CPU validation

report.json has eight root/map/condition cells, each total16, with correct,
valid, truncated and multiple counts, plus 64 paired prompt IDs. Missing or
duplicate outputs reject; truncation/multiple ACT rules use exact w0.parse_output.
Baseline records are copied verbatim and rechecked against the sealed source.

Passed **17 tests in 29.798s**: 6 new lookup tests + 11 unchanged calibration tests.
Coverage includes authentic row/context/target identity; deterministic64;
unchanged parent bytes; wrong seal/overlap/no-overwrite/opt-in; real helper
prepare/replay with fake model/process boundaries; 64 new calls and unchanged
fake parameter data; strict counts; incomplete and failed generations; and
equal-byte relocated helper replay in the actual original producer checkout.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -m unittest \
  test_oracle_lookup_diagnostic test_writer_interface_calibration -q
```

Frozen source hashes:

```
d1f7dd559cbae7b0fd67421147b555711f09d24f0e90b4e520f5a83eb482d990  organism_v6/oracle_lookup_diagnostic.py
b45f09019c3811c9e659868607130acd6bc09552deedd7cebed249fccc42c91e  tests/test_oracle_lookup_diagnostic.py
```

Last source edits: module08:51:15 UTC, tests08:51:37 UTC, September 12, 2026.
No ongoing source edits. Exact CLI help was checked on CPU.
