# Fundamental teaching readout handoff — 2026-09-12

Main is the sole Git operator. No Git, network, GPU, fitting, parent, live-world,
dataset, coordination-notebook, or other contributor file changes were made.

## Owned implementation

- `/data/home/rohing/dream-state/organism_v6/fundamental_teaching_readout.py`
- `/data/home/rohing/dream-state/tests/test_fundamental_teaching_readout.py`
- This requested handoff: `/tmp/astra_fundamental_readout_handoff_20260912.md`

## Python API and plan schema

Import `organism_v6.fundamental_teaching_readout`.

`prepare(out, model, adapter, device, lease_end) -> plan` is CPU-only. `adapter`
is a local path or `None`; `device` is one explicit numeric device string or GPU
UUID; `lease_end` is Unix seconds, stored as a finite float. Preparation requires
over 750 seconds remaining (600 worker + 140 cleanup reserve + 10 lease margin).
Output must be fresh, outside the repository, and not overlapping model/adapter.
Failed preparation roots are not reused. No GPU allocation is performed here.

`plan.json` has these fields:

```text
schema: 1
model: resolved local model path string
adapter: resolved local adapter path string | null
device: selected physical device string
lease_end: Unix float
model_files: base.model_hashes(model), relative filename -> SHA256
adapter_files: base.tree_hashes(adapter), relative filename -> SHA256; {} when OFF
cases: 48 exact selected build_candidate()["eval"] rows, unchanged
requests: 48 {call_id, case_id, role, arm, prompt, temperature, seed, max_tokens}
source_hashes: base.sources() plus readout, corpus, reasoning_neutral_probe.py
native_inputs: 48 {call_id, rendered_prompt, prompt_token_ids}
identity: base.expected_identity(plan, adapter)
worker_seconds: 600
output_token_ceiling: 3072
claim_limits: explicit dev-only behavioral/formatting/byte-origin limitations
```

`requests` are fixed in addition-ID order 000..031, then memory-ID order
000-0..015-0. `call_id` runs 0000..0047. `role` and `arm` are both `readout`:
these are receipt/usage metadata, never extra text sent to the model. The exact
candidate `context` is the entire prompt. Every request is temperature 0.0,
seed 20260912, max_tokens 64, with no added stop rule, retries, examples,
reminders, or expected answer. Requests/rendering are identical across roots for
OFF/teach/control; only adapter identity changes. Confirmation has no request:
the other 32 additions, 16 memory paraphrases, and 16 unknown probes are excluded.

Native preparation uses the actual local tokenizer's single-user
`apply_chat_template(..., tokenize=False, add_generation_prompt=True)` and its
`encode(rendered)` result, exactly as `base.NativeBackend` does. Any system text
provided by the native template is retained unchanged; no manual wrapper is used.
Actual model-file hashes and all adapter-file hashes are recorded. Byte pins do
not authenticate model origin. Freeze Main's corpus/dependency edits before
preparation: run/reduce reject source or model/adapter hash drift.

`run(root, allow_gpu=False) -> supervision_receipt` refuses without explicit
opt-in and delegates once to `base.supervise`, using one 600-second-bounded worker.
The supervisor may shorten its bound for remaining lease/cleanup time. The fresh
`run/` directory prevents retries, including after failure. The worker checks its
supervisor-owned process group/device and watches parent loss, lease expiry, and
its own deadline; it signals only its owned process group. Backend closure runs
in `finally`, preserving failure receipts and requiring verified cleanup.

`reduce(root) -> reduction` is CPU-only and writes a fresh `reduction.json`.
It requires successful supervision/owned-group/GPU-release receipts, backend
cleanup, exact 48 raw request/response pairs, capture-manifest integrity, pinned
source/model/adapter identities, request/response hashes, ordered timestamps,
`base.validate_response`, actual rendering/input/output-token audits through
`base.audit_native_calls`, and matching `base.usage` evidence. Missing artifacts
raise rather than returning a zero, partial summary, or scientific failure score.
Existing reduction output is never overwritten.

## Scoring and output

- `score_addition(text, expected)` is pure. Anchored ACT/PREDICT label lines are
  counted including malformed declarations; integer payloads must consume the
  complete line. It retains `first_act`, `act_count`, `first_predict`,
  `predict_count`, `action_valid`, `prediction_valid`, `predict_before_act`,
  `correct_action`, `adherence`, `expected`, and `raw_text`. Missing/multiple ACT
  is invalid even if one answer matches. Correct action is independent of
  prediction format. Adherence requires one valid prediction before one valid
  action, both matching the expected sum; there is no best-answer rescue.
- `score_memory(text, expected)` is pure: strip, lowercase, remove at most one
  terminal period, then require exactly blue/green/red/yellow. No second strip,
  punctuation cleanup, quoted-answer extraction, prose interpretation, or unknown
  rescue. It retains `raw_text`, `normalized`, `answer` (null when invalid),
  `valid`, `correct`, and `expected`.
- Reduction `counts` is `{total:48, addition:{total:32, correct_action,
  invalid_action, adherence}, memory:{total:16, correct, invalid}}`.
- `rows` retains every case's raw text and scoring fields, with call/case/kind IDs.
- `cost.readout` and `cost.readout.by_arm.readout` hold request counts, actual
  native input/output token counts, token ceiling, and generation seconds.
  `reserved_seconds` comes from supervision, including its owned cleanup window.
  `monetary_cost` is null because no billing-rate evidence is available.
- Full native responses include text, actual input/output token IDs, actual
  rendered prompt, finish reason, and stop reason. They are preserved under
  `run/data/calls/NNNN.{request,response}.json`; scoring never rewrites them.
- Other artifacts: `plan.sha256.json`, `run/worker/{process,supervision}.json`,
  `run/worker/stdout.log`, `run/data/{identity,backend.ready,backend.cleanup,
  usage,manifest}.json`, and `run/data/failure.json` on capture failure.

## CLI (Main only for GPU execution)

From `/data/home/rohing/dream-state`, use separate fresh roots for each arm:

```bash
python3 -B -m organism_v6.fundamental_teaching_readout prepare \
  --out /tmp/fundamental-OFF-FRESH --model /absolute/local/model \
  --device 0 --lease-end "$LEASE_END_UNIX"

python3 -B -m organism_v6.fundamental_teaching_readout prepare \
  --out /tmp/fundamental-teach-FRESH --model /absolute/local/model \
  --adapter /absolute/local/teach-adapter --device 0 --lease-end "$LEASE_END_UNIX"

python3 -B -m organism_v6.fundamental_teaching_readout run \
  --root /tmp/fundamental-OFF-FRESH --allow-gpu
python3 -B -m organism_v6.fundamental_teaching_readout reduce \
  --root /tmp/fundamental-OFF-FRESH
```

Repeat preparation with the control adapter and a distinct fresh control root;
Main allocates each device and sequences the readouts. `_worker` is internal to
the supervisor and must not be invoked directly. Nothing trains or promotes an
adapter; Main's separate fit/material harness owns those decisions and artifacts.

## Validation performed

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p test_fundamental_teaching_readout.py
python3 -B -m organism_v6.fundamental_teaching_readout --help
```

22 owned CPU tests pass. Scoring tests were written before implementation and
initially failed because the implementation did not yet exist. Tests cover fixed
selection, exact prompt-only invocation, equal arm settings, actual small-fixture
file hashing, native-token fixture audits, complete/invalid/missing outputs,
source/adapter/request/token tampering, no retries, cleanup/load failures,
supervisor delegation, unowned-worker rejection, and parent-loss cleanup.
Tokenizer/backend responses in tests are explicitly CPU fixtures, not actual
Qwen generation evidence. No real model tokenizer preparation or GPU run was
performed by this contributor. `python3` is available; bare `python` is not.
