# Parent material diagnostic — frozen handoff, 2026-09-12

## Prelaunch clock repair — supersedes original source freeze below

New source freeze: **08:43:20 UTC, September 12, 2026**. No ongoing edits.
Diagnostic-local DiagnosticState overrides only clock_line; DiagnosticDriver
subclasses NoEndTokenDriver and preserves all State fields, including born_at.
Rendered clock retains chunk, budget and chunks-since-progress, omitting only
wall-clock alive seconds. SCHEDULE now records
clock_policy="deterministic_tick_only_no_alive_seconds". Global State,
batch_loop, time functions and actual ledger timing metadata are unchanged.
CLI/config fields remain unchanged. Use these new bytes for launch:

```
bbda9f086f3070cee5f708ad71772a99a7a65715dfb08ff32d97927d7f5b2d5d  organism_v6/parent_material_diagnostic.py
75da14687e4ae19ae44e034106d0a3317106f2c2e40694088c821ce781ad33f7  tests/test_parent_material_diagnostic.py
```

Focused rerun: **9 tests passed in 28.236s**, including both full fixture arms
and a regression that changes born_at, allows actual wall time to advance,
and verifies identical rendered prompts at the same tick. No monkeypatching.
Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -W ignore::ResourceWarning -m unittest test_parent_material_diagnostic -q`.
The original results and hashes below document the prior freeze only.

Source frozen at 08:41:07 UTC; no further source edits in progress.
Only the two new owned Python files and this report were changed. No Git,
network, remote commands, model loading, or GPU launch was performed.

## Scope and interpretation

Inference-only static lesson versus active sham, one arm per fresh process.
Outputs explicitly say EXPLORATORY_LOCAL_BASE, clean_lineage=false,
official_base_authentication=UNRESOLVED, evaluation=NONE. Local hashes are
actual byte pins, not official origin authentication. There are no adapters,
training calls, lineage manifests, clean gates, admission certificates or
training targets. These descriptive records establish neither persistence,
learning, parenting efficacy nor H1/H2. No sealed/final task is scheduled or
sent to a teacher. Teacher here is a fixed artifact, not a dynamic parent model.

Both arms use the same 64 unique training IDs (seed6101), generation seed7101,
budget16, wake batch8, wake cap400, note cap100, temperature0.7. The phase-zero
lesson/sham is delivered through the real receipt API once; the same text is
present in each subsequent wake/note context. This is not a refresher schedule.
Main measured lesson203 versus sham158 raw teacher tokens on node3: **not exact
dose matched**. Runtime records actual counts for both texts and per-request
presentations. Chat token accounting uses tokenize=False, then encode with
add_special_tokens=False; it never counts a BatchEncoding with len().

## Exact configuration and CPU pin creation

The JSON accepts exactly four Config fields: out, mode, model_path,
expected_files. mode is lesson or sham. model_path must be the resolved actual
local directory. expected_files maps every local relative file path to SHA256.
out must not exist; its parent must exist. Do not place it within a training
life/lineage, or the model directory. All other protocol values are fixed.

From the repository root, main can create fresh paired configs without models:

```bash
export LOCAL_BASE=/actual/local/base/directory
export PAIR_PARENT=/absolute/existing/diagnostic-parent
python3 -B - <<'PY'
import json, os
from pathlib import Path
from organism_v6.parent_material_diagnostic import local_files
model = Path(os.environ['LOCAL_BASE']).resolve(strict=True)
parent = Path(os.environ['PAIR_PARENT']).resolve(strict=True)
pins = local_files(model)
for mode in ('lesson', 'sham'):
    config = dict(out=str(parent / mode), mode=mode,
                  model_path=str(model), expected_files=pins)
    with (parent / (mode + '_config.json')).open('x') as target:
        json.dump(config, target, indent=2, sort_keys=True)
PY
```

Use the same resolved path inherited from W0, not a model repository ID.
Copy/configure actual pins prospectively; do not use synthetic test pins.

## Exact launch (main only; not executed by author)

Launch separately for mode=lesson and mode=sham, each with its own GPU UUID and
external fresh log. Main currently plans node3 GPU0/GPU2; calibration on GPU1
must remain untouched. Main checks /proc reservations and process groups.

```bash
MODE=lesson
MODEL=/actual/resolved/local/base/directory
PAIR_PARENT=/absolute/existing/diagnostic-parent
GPU_UUID=GPU-actual-reserved-uuid
(
  set -C
  exec env V6_MODEL="$MODEL" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    CUDA_VISIBLE_DEVICES="$GPU_UUID" \
    timeout --signal=TERM --kill-after=5s 7195s \
    python3 -B -m organism_v6.parent_material_diagnostic \
      --config "$PAIR_PARENT/${MODE}_config.json" --execute \
    > "$PAIR_PARENT/${MODE}.external.log" 2>&1
)
```

Repeat with MODE=sham and its distinct reserved GPU_UUID. Logs are siblings of
the arm directory, never descendants. set -C refuses log overwrite. Environment
must be established before Python imports model_backend. Without --execute the
CLI exits before reading configuration or loading a model. Main owns the hard
two-hour process-group deadline and post-run GPU inventory.

## Artifacts, joins and limitations

Config, local pins, source hashes, schedule, teacher receipts/doses, actual
prompts/rendered prompts/outputs, seeds, source identities, raw ledger and
results are preserved. Successful/error finalization hashes files and removes
write bits. Existing output directories are refused; no resume/reseal path.
Base bytes and configured model identity are checked before/after execution.
Partial results are attempted on catchable errors; hard process termination
cannot guarantee finalization. Constructor failure occurs before the backend
context manager's try/finally and may leave workers: main's external process
group cleanup and fresh inventory remain required. Normal exits use the
existing close_backend helper. GPU execution remains untested by author.

summarize(out) reuses the actual source/content judge descriptively. It joins
ACT and note records to actual raw generation outputs, verifies their hashes,
rejects missing sources/outputs, echoes and invalid records, and reports raw
counts plus unique normalized records, rejection reasons and null ratios for
zero measured actions. Zero qualified material is a useful descriptive result.
Judgments use zero-based physical record_line/source_line offsets. No minimum
64 threshold, training corpus or eligibility is issued by this module. A
separate write-prep consumer must retain these exploratory labels and may not
treat unique_grounded=true as clean admission or ancestry authentication.

## Validation and frozen bytes

Passed: **61 unittest tests in 30.076s**: diagnostic8 + preschool_reasoning53.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -W ignore::ResourceWarning \
  -m unittest test_parent_material_diagnostic test_preschool_reasoning test_reasoning_gym_gym -q
```

test_reasoning_gym_gym contains no unittest-discoverable tests (zero counted).
An additional pytest invocation for it could not run: /usr/bin/python3 has no
pytest installed. No dependency installation attempted. The real strict gym
helpers are exercised by the diagnostic's CPU fixture tests. The --execute
negative test intentionally prints argparse's refusal. The initial focused
run had two startup failures (output-directory check order), repaired before
the final passing run; all failure output was preserved in the conversation.

Final source hashes (both last edited 08:41:07 UTC):

```
da0c738c55f8e22d3da3c2524346fa20928572fae6b43c501548d7340f8ee664  organism_v6/parent_material_diagnostic.py
6fcedba893b6cd89449ba7d87c6501a6f9d4828d0fbcdf1ad71fb868d59d4dcd  tests/test_parent_material_diagnostic.py
```

Final runner is 324 lines. Since main's 316-line review, the last change adds
independent raw note-output joining/hash checks and a negative control; no
computational recipe, teaching schedule, cap or seed changed. Files are frozen.
