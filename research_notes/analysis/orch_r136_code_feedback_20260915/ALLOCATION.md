# R136 fresh-cohort allocation

[Builder / Main] 2026-09-15T22:10:46Z

Only `gpu/ovx3_ssh.sh` physical7 / `GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b`.
R133 failed after4 calls and5 reserved intents; its entire run and source remain
immutable. Do not replay its failed or completed inputs. R136 uses a new random
seed and16 new PUBLIC TRAIN tasks, excluding all16 R133 planned specs/IDs and its
seed in addition to the original declared inventories:70 spec hashes,96 ID
hashes,1 used-seed hash. Coverage is bounded, not global semantic disjointness.

PLAN `4e6c6093b50d0ec3b79be50134a60cb9f5796da8034bf85b2b65bdc50e987195`;
TASKS `9269106abce2d0ddef31efa3b7e49303d1657fe89c97959dfe144fd88d4d3cef`;
EXCLUSIONS `66b4acf82d440fa45e938afbd36af728f0fa3c7866fac50db9707bdcdca0f357`.

Same declared R133 comparison: fixed FULL18404 versus its frozen Qwen2.5-7B
base with LoRA actually disabled, one original draft shared into real interpreter
feedback and neutral-review forks. **96 new calls maximum**,2048 tokens/call;
zero optimizer updates, external parents, automatic row admissions or retries.
Expected15–60minutes; hard wall **September15 23:30UTC**, before the existing A4
September16 06:00UTC timer and more than six hours before the lease wall.
Fresh privileged GPU/process admission is mandatory; no existing life is stopped.

The producer repair restores inference-only gradient flags after PEFT context
exit and rejects adapter-enable drift; it does not change parameter data, the
optimizer, the tasks' public interface or feedback visibility. Future launcher
source publishes its receipt atomically and signals the child only afterwards.
Neither change is applied to the failed R133 source. Main and node5 pass73 CPU
tests:27 producer,13 launcher,33 unchanged public-helper tests. CPU success is
not a model-load or completion receipt.

Read-only adapter COMMIT remains
`7eb8c8416cb540fb871ac2d9c89be576973d56f8453af3018aa62c083b0c5d83`,
state `d8397e0ae0f4ab8ee4c242e6b0d7dc5ca90fd97d14b5ed6af061383b4e3e2ffe`.
Original weights remain in the verified node-local R133 weights directory;
R136 has its own frozen source, fresh plan and output directory at
`/localhome/local-rohing/orch_r136_code_feedback_20260915_attempt1/run1`.

Launch from that root using its source PYTHONPATH and empty CUDA visibility:
`python -B -m gpu.orch_r133_code_feedback_guard supervise --config GUARD.json`.
Only the guarded native child receives the UUID. No safeguard/model fallback is
part of this work. A positive result would show immediate correction under
feedback, not retained learning, metacognition or a parenting-specific benefit.
Any subsequent training must separately declare source targets, masking,
rehearsal, anchors, controls, dose and fresh parent-free evaluation.
