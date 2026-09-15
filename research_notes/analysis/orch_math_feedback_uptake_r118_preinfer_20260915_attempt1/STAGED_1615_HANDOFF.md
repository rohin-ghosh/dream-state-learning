# Actual campaign-bound CPU stage and broker custody

Campaign `/localhome/local-rohing/orch_r118_main_startup_recovery_20260915_1610/CAMPAIGN.json`, SHA256 `7ea22b7fe4637ac344df140c7b56d49304091d067ec32d2558975ea1759e6610` is bound in both actual runtimes. Source map remains the exact186-entry v4 map, SHA256 `b8d9f1b0b1933280b46f326d90b7a2ccb0996ae8c131d2f22a562b18ba77f20d`. No GPU code/source closure was changed during staging.

Service prefix: `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4`.

| Branch | Final owner under prefix | SHA256 |
|---|---|---|
| F2 | `lane1/FRESH_OWNER.json` | `e7ba4f22bf35c0d9d09a5e1616a67b29b6eb5c6b0b855349461360e2a6ad3a25` |
| A2 | `lane5/FRESH_OWNER.json` | `044160376c8715911e7acc3bcc6083aaf3c27c022b5b566875d020336f5b4516` |

Both have runtime_staged=true and exactly the campaign's math source_files. New guards/LAUNCH remain absent at the completed preflight; Main alone dispatches all-eight GPUs.

## Actual broker readiness

- F2 node broker PID2722783, Hubble-owned, actual original queue lock. `lane1/BROKER_READY.json` SHA256 `7f0af2d894b1e6540530ea3120d795f44e89fb912a15a6dd45197ff6bcda3386`, binding runtime `122b4eccd7888d53d6de11213c995d3be7a931021b6968a781b4ddea29d578aa` and new lane1/GUARD_TERMINAL.json.
- A2 VM broker PID2690776 alive, actual original queue lock. `lane5/BROKER_READY.json` SHA256 `3cef41dd20330ebb08c28f0dde5502705b638f410cedeaa71695e979f6d85aa5`, binding runtime `ccc1e81c63a0462043c49468a986eb8f76d5f04ecb7e5a50e8ac55bf04425a20` and new lane5/GUARD_TERMINAL.json.
- A2 immutable runtime `/tmp/orch_math_feedback_uptake_r118_preinfer_broker_source_20260915_attempt4` preserves active CONFIG1a4caaa9..., original GO, HTTP slots/claims/budgets/deadline. Only new service mapping changes. Eight local and eight immutable-runtime CPU tests passed; native runtime/release/config hashes and original GO were verified before start. Source manifest `b6f76cad61db82448e4796d9d5f37e33b2a14078bbc09cbf0c8d148b872081c6`; CPU receipt `2111d224e9ac4d1c8b06a1fbe7d1e1b3124b0a9e2613b33920051c2ddc87eb4d`.

## Actual timer retirement

Only F2 cutoff2610049/schedule2610050 and A2 cutoff2610042/schedule2610043 were retired. Historical PPIDs pointed to the failed guards and had authentically changed to1. A separate CPU-only helper validated **all boot/PID/start/UID/command/executable/cwd fields unchanged**, preserving both historical and fresh identities, then used the actual fresh identity for CPU-FD/CVD checks and pidfd signaling. Only mutable PPID is disregarded; no executable or command identity is synthesized. Four local and four native regressions passed, including reuse/exec/command changes and explicit selector rejection.

The helper is separately pinned in the stage authorization and receipts at `/localhome/local-rohing/orch_math_feedback_uptake_r118_stage_cpu_20260915_1612`; it is not injected into the immutable GPU source. `STAGED.json` there, SHA256 `6fa2e1adfa55ed08b84155710517ed1b9d625e573dbd21d26037d591a6e1e761`, includes both final owner/runtime/retirement references. Main selector1519259 was checked unchanged/live before and after stage and during final preflight, never signaled.

## Exact read-only preflight command — already passed

On node5:

```sh
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_source_20260915_v4 \
  python3 -B /localhome/local-rohing/orch_math_feedback_uptake_r118_stage_cpu_20260915_1612/PREFLIGHT.py
```

This checks actual staged authorization, preserved ledgers/carry, broker/runtime/terminal and original queue-lock bindings, campaign source closure and selector identity. It performs no admission scan, inference, provider request, model load or mutation. A2 VM process liveness was additionally checked locally because its PID is not a node5 PID.

Stage is already complete; do not rerun it. Both actual authorization windows end16:25UTC. F2 N274/P60 next11 and A2 N170/P36 next7 remain unchanged; canonicalgen1, TRAIN16:55/native16:59/hard17:02 and original43-cycle/FINAL ceilings remain. No old readout retried, failed session reused, standalone GPU dispatched or Git mutated.
