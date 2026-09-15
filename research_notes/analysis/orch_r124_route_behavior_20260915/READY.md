# R124 route behavior assay — 2026-09-15 19:09 UTC

Status: **CPU/native READY; waiting for the current generation owner's safe handover.** No assay GPU input is claimed by this receipt.

## Question and limits

Does one actual LoRA sleep change a child's response to the **same public prompts in an empty context**? Route's existing readouts already retain full `response.raw` and token IDs; their bare commands are actual minimal-prompt behavior, not truncated logging. This new diagnostic preserves the minimal policy and adds a separately labelled brief-explanation policy. It is not a retrospective repair of historical readouts.

For each of eight existing DEV tasks, prompts contain either the initial public observation or that observation plus the actual record at the first listed address. No hidden world answer, parent text, prior child carry, training episode or FINAL task is supplied. Each condition receives identical prompt bytes. There are 32 prompts per condition, 512 output-token cap, greedy decoding, batches of at most four, and a fresh process for each condition.

Conditions: `BEFORE`, `AFTER`, and `AFTER_LORA_OFF`. The latter is a capability/suppression reference, **not an unparented-learning twin**. Changes in responses or length do not establish retained improvement or a causal parenting effect. Those remain unproven.

## Bound inputs

| Branch | Consecutive saved cycles | Export manifest SHA256 |
|---|---|---|
| F1 | 13 → 14 | `d970808e89a5726c628d29e5d7ed299cc6b88b5a258e1eb9606b983572af48e7` |
| A1 | 12 → 13 | `ee63aedd1a74b1d2aec39427d268ce65a340ebda040762b5322f8d1a9418d080` |

Both prompt files have SHA256 `e42cef46848b020718f246ebdd56f6198eb5a3fc0c69f67b467f112981a85f5d`.

All checkpoint/adapter files were copied and hash-verified directly between nodes; no optimizer was copied, no raw archive was written on the VM. Source branches continue unchanged on node 5. Inputs and new raw outputs stay under `/localhome/local-rohing/orch_r124_route_behavior_20260915` on `ovx`.

## Readiness and allocation

- Physical `ovx` 7 prospectively replaces one generation-only lane; other 13 level-1 slots and parenting lanes are unchanged. Generation remains active until its owner verifies a completed-task handover.
- Scope: 192 new diagnostic calls, zero parent/provider calls, zero optimizer steps; two-hour assay bound within the existing lease minus six hours.
- Local and native focused tests: 10 + 10 PASS. Four native adapter relocation/identity bindings PASS. Full import closure PASS after a pre-GPU missing-scanner packaging repair. No admission waiver.
- Native `READY.json`: SHA256 `7bf4694f3b7ef8fea593100743c5b1d886a2c70e56479c62de8107d6f3184a36`.
- Native `PLAN.json`: SHA256 `83933ffcd185a3721f0fb3b6b62d4845a64f47072a7b092ae436bd3eb0203654`.
- Frozen evaluator module: SHA256 `6b9008cd41618c81035d98f568c5859a25d23f9e272efd7fed4a2c65698579ff`.

Launch after the owner release receipt and a fresh privileged exact-UUID scan:

```sh
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r124_route_behavior_20260915/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r124_route_behavior_probe supervise --plan /localhome/local-rohing/orch_r124_route_behavior_20260915/PLAN.json'
```

The launcher must be detached with its PID/log receipt when dispatched. Existing failures are preserved, never retried under old keys. Output metrics describe exact text changes, rationale tokens before the action, terminal/truncation status and repeated four-grams; semantic coherence and retained improvement remain `UNJUDGED`/`UNPROVEN` until supported separately.
