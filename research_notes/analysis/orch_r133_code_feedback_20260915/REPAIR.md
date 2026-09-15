# R133 local read-only PEFT context repair

2026-09-15 22:05 UTC. **Non-material repair; no launch, retry, model/provider
call, optimizer, weight-data mutation, admission, Git or shared-ledger edit.**
Reduction is paused. Main owns the fresh R136 plan/guard/startup barrier.

## Verified failure and root cause

Node5 read-only checks used the existing `gpu/ovx3_ssh.sh` wrapper. At 22:01 UTC,
the immutable R133 `run1` showed LOADED with optimizer_count=0; 4 CALLs, 5 INTENTs,
1 FAILURE; native and episodes terminals `FAILED_NO_RETRY`; exit code 1.
The sanitized cell sequence was FULL draft/feedback/neutral (calls 1–3), BASE
draft (call 4), then BASE interpreter-feedback reserved as call 5 and failed with
`ValueError: all_weights_frozen`. No raw child text or task content was exported.
**Unchanged-weight completion proof is absent; no admission is supported.**
Main reports the failure archived in `FAILED_NATIVE_2200.json`.

Installed PEFT **0.20.0** was inspected as source text only, without importing
PEFT, loading a model or calling a model:

- `peft/peft_model.py:1046`: LoRA `disable_adapter()` exits by calling
  `enable_adapter_layers()` when adapters were enabled at entry.
- `peft/tuners/tuners_utils.py:508`, `:530`, `:1564`, `:1609`: enabling adapters
  calls `set_adapter(self.active_adapters)` with default `inference_mode=False`,
  setting active adapter parameters' `requires_grad=True`.
- The prior outer wrapper checked flags **inside** the PEFT context, before its
  exit restored enabled adapters and re-enabled gradients. BASE draft completed,
  but the next call rejected those flags. This matches the observed cell sequence.
- The old CPU double restored adapter enable state without mimicking this
  gradient side effect, so it missed the defect.

Installed source SHA256s:

```text
peft/peft_model.py
c07bf9545b3b17ea0363263b11fc25d0a2ebe814e3f8083da3fa08adaa824879
peft/tuners/tuners_utils.py
2f8f343737348014b71d775dda15a06dbe34df4190ed20afba8ad58ba471a5cf
```

## Exact local repair

`readonly_model` snapshots parameter references, their required-false gradient
flags, and LoRA module disable flags before entering the context. Entry and body
still fail on unexpected trainability; the requested FULL/BASE state is checked
inside. An **outer finally, after PEFT context exit**, restores only changed
gradient flags to their snapshotted false values and asserts both the complete
gradient-flag tuple and module enable-state tuple match entry.

Restoration also runs on body errors, context-entry/exit errors and adapter-state
assertions. Module-state drift is rejected, not silently repaired. No parameter
data, optimizer or active-adapter selection is written. API and 96-call quota
are unchanged: `collect(root, authorization, *, expected_gpu_uuid)`.

## CPU validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 tests/test_orch_r133_code_feedback_collection.py -v
```

**27 tests passed, 0 failures/errors, 3.376 seconds.** The default fake PEFT
context now realistically re-enables gradients on exit. Regression coverage:
bare-context reproduction; repeated FULL→BASE→FULL calls; all 96 mock native
calls; restoration after model/body and context-exit errors; rejection of body
trainability and adapter-enable-state drift; preservation of initially disabled
adapters; preexisting trainable weights still rejected. A storage-identity check
confirms the repair path changes flags rather than parameter data.
These are CPU tests, not a new native unchanged-weight receipt.

## Exact repair write allowlist and hashes

Only these three local files changed in this repair:

```text
gpu/orch_r133_code_feedback_collection.py
79b93767ed022c4aebb91f3d6aada480998effe2a07331e86ad59c5ad56dd4dd
tests/test_orch_r133_code_feedback_collection.py
139db9ad31f3ab387d72bcbeafd5fd07705d7f44dc75d93a302422176c58157b
research_notes/analysis/orch_r133_code_feedback_20260915/REPAIR.md
```

At 22:05 UTC, read-only remote hashing reconfirmed original R133 producer
`1b382863fe2c13addce6693e12b6f77d4ee70afaace79a945d0c57620ccb3085`,
GUARD `dbc98b80f132f1defd7e359114488bbcba68899da403d98851292137d60786a5`,
and PLAN `115cb43839ff11a6e004add01a56a1ccb661a7c8ec74517f3f32a09bf60b1659`.
The failed run/source, prior CPU manifests/previews and Main's guard/tests were
not edited or repinned. Their old source hashes are historical, not repair pins.

Main's subsequent R136 must use a completely fresh seed/task set, exclude all
16 R133 specification hashes, make 96 new calls without input/call replay, and
bind the repaired source/tests into a fresh CPU/native-tested plan and guard.
No R133 resumption, reinterpretation as success, or automatic admission follows.
