# Writer interface/truncation calibration — September 12, 2026

## Scope and status

Implemented only NEW `organism_v6/writer_interface_calibration.py` and NEW
`tests/test_writer_interface_calibration.py`, plus this handoff. No existing W0
source or actual run was edited. No GPU, network, Git, model loading or real
inference execution was performed in this task. CPU tests use synthetic parent
custody, tokenizer/model boundaries and mocked worker processes.

This is **DEVELOPMENT_CALIBRATION / EVALUATION_ONLY**, not a W0 replacement,
rescue, writing assay, memory/behavior/parenting result or clean ancestry.
W0 remains the original failed source. Old held-out items are calibration
material now and cannot be reused as uncontaminated test evidence. The module
does not train, load adapters, call any admission/lineage writer, or authenticate
official model origin. W0's local hashes remain byte pins, not authentication.

## Fixed diagnostic

For each of two W0 roots, traverse its original held rows in their existing
order and select the first occurrence of each `(tool, mode)`: 8 tools × 2 modes.
Repeat these same selections for both maps. This gives **64 paired oracle
prompts**, without inspecting per-prompt outputs or correctness to select rows.
The original W0 `oracle_prompt` table is reused verbatim.

| Condition | Rendering | Instruction | Maximum new tokens |
| --- | --- | --- | --- |
| `raw_original_32` | raw | original | 32 |
| `chat_original_32` | tokenizer chat template | original | 32 |
| `raw_explicit_32` | raw | fixed instruction | 32 |
| `chat_explicit_32` | tokenizer chat template | fixed instruction | 32 |
| `raw_original_256` | raw | original | 256 |

All 320 requests are greedy (`do_sample=False`), seed 0, with no retries.
The exact fixed instruction is prepended to the oracle table, followed by one
newline, uniformly in both explicit conditions:

```text
Reply with exactly one line: ACT: a0 or ACT: a1. Do not include explanations.
```

Chat rendering is exactly the pinned tokenizer's `apply_chat_template` with
one user message, `tokenize=False`, and `add_generation_prompt=True`, followed
by tokenization with `add_special_tokens=False`. Raw conditions tokenize their
raw prompt with the same setting. Prompt-plus-generation length is bounded by
W0's 2048-token context limit. Raw/original 32 and 256 share identical input
token IDs; only the generation cap changes. No answer-only postprocessing,
regex extraction, stripped explanations, softened parser, or extra correction
prompt is introduced.

The reducer calls W0's unchanged **`parse_output(text, truncated)`**. It reports
20 cells (2 roots × 2 maps × 5 conditions), each with total=16 and integer
**correct / valid / truncated / multiple** counts. It also reports 64 pair IDs
with all five request IDs, parent oracle request IDs and paired flags. A
truncated otherwise-canonical ACT remains invalid, exactly as in W0.

## Failed-parent custody, not rescue

`prepare` requires main's pin of the **original** `REAL_EXECUTION_SEAL.json`.
It uses W0's prepared-artifact validation with `check_source=False`: this
validates the original manifest, configuration, prepared receipts, material
and request blueprint even if the current W0 source has since received fixes.
Current W0 code and the exact parser source are separately frozen as calibration
dependencies; historical W0 source hashes are retained, not overwritten.

All current parent files must match the original seal inventory with exactly
one exception: `launcher.out`, whose sealed SHA256 must be that of empty bytes
and whose current content must be nonempty. Added/deleted files, any other
changed bytes, a different seal, an unfailed/resealed parent, or further logger
drift after calibration preparation fail closed. The receipt records the
original seal contents/hash, complete current inventory, and old/current
logger hashes and current size. No parent bytes are changed.

The source checks also validate material deterministically from W0 seeds,
validate/rebuild all 1504 original requests against the bound identities,
adapter hashes and tokenizer preflight, verify the report hash and its declared
ASSAY_INVALID/four zero-oracle cells, and check the declared fourteen-stage
inventory. This is **not** a replacement full scientific replay or assertion
that W0 passed. The permitted failed-parent status is explicitly
`FAILED_LOGGER_DRIFT`, with `parent_passed=false` throughout.

## Preparation and execution safety

- `prepare` loads the local pinned tokenizer only, **never the model or CUDA**.
  The same W0 model/tokenizer inventory and package/Python environment are
  required, using W0's `pin_local_inputs` / `load_local_tokenizer` APIs. These
  are local-only reads; CPU preparation must use a compatible environment.
- Preparation freezes the 320 actual raw/user prompts, rendered prompts, input
  token IDs, exact condition/pair/parent IDs and targets. It checks source/input
  hashes again before finishing. Missing chat-template support fails closed.
- Calibration and log directories must both be new, with existing parents,
  disjoint from each other, W0, protected roots and model/tokenizer paths. No
  symlink output paths. Operator stdout/stderr must also stay outside W0 and
  the calibration root. This uses the existing W0 output-descriptor guard.
- Only `execute --allow-gpu` schedules the worker. It revalidates prepared
  bytes/source/input hashes and W0's A40 hardware/UUID/node/driver/idle checks.
  One fresh worker inherits exactly that GPU UUID, offline flags and W0's
  deterministic environment. There is no arbitrary alternate GPU/config flag.
- The worker reuses W0's `configure_torch` and `load_hf_model`, calls `eval()` and
  `requires_grad_(False)`, and generates inside `torch.inference_mode()`. It
  never imports/loads a PEFT adapter or creates an optimizer. The small generator
  wrapper is necessary because W0's generator hardcodes raw prompts and 32
  tokens; changing W0 itself would violate ownership and assay immutability.
- **Hard cap: one GPU, 3600 seconds / one A40-hour**, or earlier caller deadline
  or pinned lease cutoff. The supervisor waits only for the remaining budget,
  reserves five seconds for termination, and stops only its own worker process
  group on timeout/failure. The worker checks deadlines before loading and
  between requests. No unbounded retry, second worker or continuation is used.
- The worker's stdout/stderr goes to an exclusive external `worker.log` in the
  separate log directory. Failure artifacts and partial request files are
  preserved; the same run cannot restart. Full completion rechecks model,
  tokenizer, parent, config and source hashes, recomputes counts, records the
  external worker-log hash and seals the new calibration output only.
- `replay` is CPU/read-only: verify this new calibration's seal, counts,
  resource arithmetic, source/parent bindings and external worker-log hash.
  It never calls a repair/reseal path for W0. Changing external launcher logs
  does not change calibration's sealed file inventory; worker-log drift is
  still detected separately.

Raw generation artifacts contain continuation token IDs, exact decoded text,
terminal-EOS decode, EOS status and truncation status. Full input prompts/token
IDs are retained in `requests.json`, joined by request ID. Reported evidence is
conditional on these instrumented outputs, not independent model authentication.

## Exact commands for main — no launch performed here

Main supplies absolute canonical paths, the externally selected original seal
hash, and a future deadline in Unix seconds no later than W0's pinned lease
cutoff. Both `CAL_RUN` and `CAL_LOG_DIR` must not exist; their parents must exist.
Do not put either under `W0_RUN`. Do not point a shell log into either sealed
evidence root.

```sh
# Set externally selected values first; do not fabricate or reseal the W0 pin.
: "${W0_RUN:?absolute failed W0 run directory}"
: "${W0_ORIGINAL_SEAL_SHA256:?pin of original failed REAL_EXECUTION_SEAL.json}"
: "${CAL_RUN:?new absolute calibration directory}"
: "${CAL_LOG_DIR:?new separate absolute log directory}"
: "${CAL_DEADLINE_UNIX:?prospective deadline not later than pinned lease cutoff}"

# CPU/tokenizer preparation only, no model/GPU load:
PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.writer_interface_calibration prepare \
  --parent "$W0_RUN" \
  --parent-seal-sha256 "$W0_ORIGINAL_SEAL_SHA256" \
  --out "$CAL_RUN" \
  --log-dir "$CAL_LOG_DIR" \
  --deadline-unix "$CAL_DEADLINE_UNIX"

# FUTURE main-reviewed local GPU command; NOT executed in this task.
# Exclusive launcher log is external to both sealed evidence roots.
(
  set -C
  PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.writer_interface_calibration execute \
    --run "$CAL_RUN" --allow-gpu > "$CAL_LOG_DIR/launcher.out" 2>&1
)

# CPU/read-only replay after completed calibration:
PYTHONDONTWRITEBYTECODE=1 python3 -m organism_v6.writer_interface_calibration replay \
  --run "$CAL_RUN"
```

The `_worker` subcommand is internal to the bounded supervisor; main should not
invoke it directly. A prepared run is not approval to launch. Existing lease,
shared-node and builder preflight rules remain main's responsibility.

## Validation and remaining boundaries

CPU regression command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p test_writer_interface_calibration.py -v
```

Final verification on September 12, 2026: **11 calibration tests passed plus
68 existing W0 tests passed, 79 total**. CLI `--help` was also checked without
model loading. The focused tests cover prospective
row selection, all five conditions and token pairing, strict parse/counts,
failed-parent read-only handling, unexpected mutation/seal rejection, fresh
roots/external logs, model-free prepare and opt-in guards, GPU identity failure,
supervised timeout cleanup, complete mocked worker/model-only flow and replay,
plus tokenizer/template drift before model loading. No actual W0 run was
available/used for an end-to-end prepare here; main must run the CPU/tokenizer
prepare on the actual pinned local artifacts. GPU dependencies, timings and
actual diagnostic outputs remain untested until main explicitly schedules them.

Ready for main's CPU prepare and local launch; no further governance workflow
is added by this handoff. The calibration source/tests are finished for review.
There is no separate caller-authored calibration config JSON: `prepare` inherits
the failed W0 run's pinned model/tokenizer/environment/GPU configuration and
freezes it together with the five conditions, supplied parent-seal pin, output
paths and deadline in the new calibration `manifest.json`.

Final source SHA256 values:

```text
9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7  organism_v6/writer_interface_calibration.py
7408c757784724af3cd9c1addfc120d82d624d8f828802e6b1393cf0d47cb21b  tests/test_writer_interface_calibration.py
```
