# Oracle lookup diagnostic — frozen handoff, September 12, 2026

Implemented only new organism_v6/oracle_lookup_diagnostic.py and
tests/test_oracle_lookup_diagnostic.py. Formation, W0, calibration and their
tests remain untouched/frozen. No GPU/network/Git/remote actions were taken.
One CPU original-producer replay subprocess was exercised by the relocation test.
This handoff now covers the final grounded_copy amendment. The old lookup run
and retained source35ba8f2c983d9baa99ece979183dceffd3e4e344 remain untouched.
Replay that old run using its original frozen producer, not this amended module.

## Exact contrast

Source: the completed, sealed calibration, with an explicit caller-supplied
CALIBRATION_SEAL.json SHA256. Full original calibration replay is required;
the failed W0 source remains failed and read-only. The 64 chat_explicit_32
inputs/outputs are reused as a paired full-table baseline with **zero new
baseline inference calls**. Their original order must equal the first held
row for each tool/mode key, for both roots/maps.

The default instruction_variant=format_only preserves the prior single-row
model-facing inputs exactly. New instruction metadata is hash-bound, so new
request IDs differ from old artifacts. Single-row selection still uses only
the held row's tool/mode key from w0.oracle_prompt, never generated outcomes.

The ONE final prospective variant is instruction_variant=grounded_copy. It
prepends exactly the following literal and one newline before cal.INSTRUCTION:

> Use the action table as the source of truth. For the exact tool and mode in the task, copy the ACT value after -> from its matching row.

Nothing else changes in row selection, question context, expected action,
chat rendering, greedy seed0, 32-token cap or strict parser. Naturally the
rendered prompt and token IDs reflect the added instruction. Variant and full
literal instruction_text are recorded in manifest, requests and report, with
condition=single_row_grounded_copy_chat_explicit_32 and a distinct result cell
label single_row_grounded_copy. Maximum64 new inference requests / one A40-hour.
No further prompt variants or format search are planned after this diagnostic.

Primary contrast is the previous SINGLE_ROW format_only result, reported by
main as 32/64 correct and 58/64 valid. The report labels these historical counts
caller-reported, not independently replay-verified by this module. The retained
full-table baseline is a historical TWO-FACTOR comparison (table extent plus
instruction), not an isolated instruction effect. No new baseline generation
or automatic selection based on prior output is performed.

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
GPU UUID and bounded diagnostic deadline may differ in the inherited runtime
config. The instruction variant is prospective experiment metadata. No separate
config JSON is required. OUT and LOGS must be fresh, disjoint directories with existing
parents, outside calibration/W0/model/protected roots.

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
CAL=/absolute/original/completed-calibration
CAL_SEAL_SHA256=caller_supplied_actual_completed_calibration_seal_sha256
OUT=/absolute/existing/parent/oracle-lookup-grounded-copy
LOGS=/absolute/existing/parent/oracle-lookup-grounded-copy-logs
GPU_UUID=GPU-actual-reserved-a40-uuid
DEADLINE_UNIX=$(( $(date +%s) + 3300 ))

python3 -B -m organism_v6.oracle_lookup_diagnostic prepare \
  --out "$OUT" --calibration "$CAL" \
  --calibration-seal-sha256 "$CAL_SEAL_SHA256" \
  --log-dir "$LOGS" --gpu-uuid "$GPU_UUID" \
  --deadline-unix "$DEADLINE_UNIX" \
  --instruction-variant grounded_copy

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

Latest focused rerun: **8 tests passed in 25.224s** after main's 09:05 UTC resume.
Source bytes were unchanged during this rerun. The earlier 17-test combined
result (6 lookup + 11 calibration, 29.798s) predates this amendment.
Coverage includes authentic row/context/target identity; deterministic64;
unchanged parent bytes; wrong seal/overlap/no-overwrite/opt-in; real helper
prepare/replay with fake model/process boundaries; 64 new calls and unchanged
fake parameter data; strict counts; incomplete and failed generations; and
equal-byte relocated helper replay in the actual original producer checkout.
The amendment adds a pre-amendment fixture hash regression proving default
request payloads are identical after removing the new instruction metadata,
and checks all64 grounded requests differ only in prefix/rendering/token IDs,
variant/condition metadata and request hash. It also exercises grounded-copy
prepare/worker/replay and verifies the report's historical comparison labels.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -m unittest \
  test_oracle_lookup_diagnostic -q
```

Frozen source hashes:

```
6300ec9b64aecacfc941550d948a78908ebe0345c84a2527df7287ed34bec8bf  organism_v6/oracle_lookup_diagnostic.py
f0137108eac64221692281a053a713d255deb7d8afb1f43ecf81c7337ea8ac24  tests/test_oracle_lookup_diagnostic.py
```

Last source edits: module09:00:24 UTC, tests09:00:43 UTC, September 12, 2026.
No ongoing source edits. Exact CLI help was checked on CPU. Only this /tmp
handoff was updated after the latest rerun; main owns Git and the one GPU test.
