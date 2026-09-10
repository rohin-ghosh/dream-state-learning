# RML-G1 GPU deployment-path audit

**Date:** 2026-09-04  
**Scope:** read-only deployment audit for ratified
`chg_20260903_rml_g1_gold_action_fast_v1`. No GPU, network, model, or remote
job was launched while preparing this note.

## Authority and exact gate

`ratification.json` is `human_approved`, `implementation_authorized: true`,
and binds consensus SHA-256
`1c27cbe6ac3adda14078f2cdbfe62785ce7161b4ae35c2fb96b899b40da53cb9`.
Authorized scope is exactly:

```text
analysis:rml_g1_gold_action_fast_v1
gpu:rml_g1_gold_action_fast_v1_234_call_gate
implementation:rml_stage_b_gold_action_fast_v1
testing:rml_stage_b_cpu_preflight_v1
```

The gate is one frozen Qwen/Qwen2.5-32B-Instruct revision
`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, with 18 registered trajectories
(GOLD_REC 4, NONE_REC 4, P_ATOMS_REC 2, AUTH_REPLAY 2, SHAM_REC 2, CUT_REC 2,
TWIN_REC 2), 13 phase opportunities each = 234 registered opportunities, and
at most 234 scientific dispatches. Terminal suffixes are typed zero-attempt
cancelled records; slots cannot be transferred or retried. A pass is only the
single-fixture supplied-gold recurrent-interface statement in consensus, not
G2, DREAM/SLEEP, LoRA, scaling, or paper evidence.

## Reusable infrastructure and exact path

`rml_d0/run_cpu_gate.py` plus `rml_d0/tests/` are the deterministic world/target
baseline and must remain host-only. The new Stage-B reducer scores frozen
traces after cognition and never feeds score or hidden truth into prompts.
`freeze.py` creates/verifies repository-relative SHA locks;
`freeze_closure.py` checks reachable Python imports; `review_binding.py` verifies
fresh review receipts and reviewed-file hashes; `supervisor.py` binds material
workflows to authorized intake and pauses on drift.

The model/runtime primitives are `research_loop.runtime_preflight` (tokenizer,
transformers/vLLM versions, ninja, chat IDs) and
`research_loop.capture_environment` (Python/platform/package/GPU/CUDA/nvcc).
`remote_job.py` verifies approval, lock, spec, and inputs before/after each
stage, writes `started.json`/`progress.json`, then atomically writes either
`done.json` or `failed.json`; required artifacts must be fresh and are copied
to a run-specific snapshot.

The current checkout has no checked-in `rml_stage_b` runner/workflow, so the
following are exact command forms to use after those authorized files exist:

1. Run unchanged D0 and all new deterministic Stage-B tests with the pinned
   repository interpreter (`research_loop.plain_tests`, as documented); require
   T01--T03, selected-slice certificate, reducer mutation vectors, 234-ledger
   reconciliation, and zero model/GPU/network calls.
2. Create/verify a fresh lock:

```bash
python3 -m research_loop.freeze create --root . --out <lock> --file ...
python3 -m research_loop.freeze verify --root . --lock <lock>
```

   Then run `freeze_closure` against the final workflow; every reachable local
   Python import must be frozen.
3. Obtain independent-review and author-advocate approvals bound with
   `review_binding`; verify both immediately before dispatch. Rejection, hash
   drift, missing dependency, or CPU failure stops the path.
4. On the intended A40 host, run these reusable T04 stages before exposing a
   target:

```bash
/localhome/local-rohing/v2/venv/bin/python -m research_loop.runtime_preflight \
  --out research_loop/runtime/<run>.preflight.json \
  --model Qwen/Qwen2.5-32B-Instruct \
  --revision 5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd
/localhome/local-rohing/v2/venv/bin/python -m research_loop.capture_environment \
  --out research_loop/runtime/<run>.environment.json \
  --model Qwen/Qwen2.5-32B-Instruct \
  --revision 5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd
```

   These existing commands are necessary but insufficient: G1 T04 must also
   hash tokenizer/files, chat template, prompt/schema/parser/stop bytes,
   target order, source/builder/reducer/runner, backend/CUDA/driver/container,
   reset procedure, deterministic decoding, and all resource ceilings.
5. Only after T04 and both reviews pass, invoke a new G1-specific remote spec.
   Reuse `gpu/a40_ssh.sh` and the launch shape of
   `gpu/v2node_start_research_job.sh`, but never point it at
   `dream_ladder_v5.remote.json` (that launches DREAM/think stages outside G1).
   Pass the exact approval SHA and G1 lock/spec to `remote_job run`; poll only
   with `python -m research_loop.remote_job status --run-id <run> --job-root <root>`.
   Pull only after a terminal marker using `gpu/v2node_pull_research_job.sh <run>`.

## Host, cache, and artifacts

`gpu/a40_ssh.sh` names the leased 8xA40 host (`10.63.139.110`); v2 wrappers name
a 4xH100-NVL host and are not interchangeable. `gpu/v2_bootstrap.sh` creates
`$HOME/v2/venv`, sets `HF_HOME=$HOME/v2/hf`, and pulls only Qwen 7B/0.5B. It
therefore does **not** establish the required 32B cache. The pinned 32B model
and tokenizer must already be in the declared local HF cache, or be populated
by a separately approved non-scientific step; no network pull belongs inside
the gate. Keep cache/runtime/artifacts on local NVMe and hash cache/model files
in the frozen runtime closure.

Declared local outputs should be under `research_loop/runtime/<run>.*` and
`artifacts/rml_g1_gold_action_fast_v1/`; remote snapshots are
`<job-root>/<run>/artifacts/`, retrieved to
`gpu_artifacts_local/research_loop/<run>/job/`. Completion is `done.json` only:
`started.json` means running, `failed.json` means failed, and process existence
is not completion evidence.

## Ceilings and deployment hazards

Consensus R09 fixes 16,384 input tokens/131,072 bytes and 256 output tokens/
4,096 bytes per call; 16,640 context tokens; 1,024 row tokens/16,384 bytes and
128 scratch tokens/2,048 bytes; 212,992 input and 3,328 output tokens per
trajectory; 3,833,856 input and 59,904 output tokens for the gate; 24 aggregate
A40 GPU-hours, 3 hours wall time, 2 GiB artifacts, and USD 0 incremental spend.
Overflow, nondeterminism, load/hash/reset/provider failure, or undeclared import
is fail-closed and makes the run uninterpretable: no truncation, fallback,
prompt repair, retry, or replacement slot.

Main hazards are accidentally using the DREAM workflow; stale/missing 32B cache
or tokenizer revision; an incomplete freeze closure; treating 234 as completed
calls instead of registered-minus-cancelled accounting; scorer/cut/twin leakage
into cognition; and declaring success from process exit instead of fresh
artifacts, `done.json`, and post-run review.
