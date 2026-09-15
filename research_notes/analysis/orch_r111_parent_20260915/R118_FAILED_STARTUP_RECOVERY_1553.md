# Route failed-startup recovery — September 15, 2026

Status: **14 native CPU tests passed; both native CPU-only request verifications
passed; both actual privileged empty-CVD admission scans CLEAR. Not dispatched.**
System Python lacked pytest; native tests used the existing isolated
`orch_r111_f1_pytest_support` directory. No dependency installation or production
inference was performed. V1's13-test receipt remains preserved; V2 adds full
reference verification and rejection of new charges, with14 tests passing.

## Non-material repair and preserved failure

The previous CPU owner command inherited its allocated GPU UUID. Its CPU helper
therefore appeared as a UUID reservation to the strict scanner, even without
loading a model. The recovered owner's **exec environment** has
`CUDA_VISIBLE_DEVICES=''`; this is not a late environment change inside Python.
Only after an actual fresh privileged CLEAR scan does the launcher give the
unchanged frozen supervisor its original UUID. Tests exercise the existing
frozen launch function as well as the new recovery launcher. Native scans at
15:51:37–38 were CLEAR for both physical0 and4 with empty launcher visibility.
Those scans are evidence only: a future launch scans again, without waiver.

The existing c56 scientific closure and original actor/supervisor remain byte
unchanged. New disjoint code: `gpu/orch_r118_route_startup_recovery.py`.
It uses a new single-use `R118_STARTUP_RECOVERY_1552` attempt directory under
each original root. Original A1 `R118_PARALLEL_LAUNCH_ATTEMPT.json`, failed SCAN,
old session e834ff FAILED, and F1's pre-reparent broker binding are preserved.
It refuses any previous actor/supervisor/bootstrap/admission/terminal evidence,
changed charges, surviving old launcher, failed new dispatcher, reused attempt,
expired startup window or nonempty CPU launcher CVD. It never resets a ledger,
reuses an old dispatcher, or retries automatically.

## Prepared executable owners for Main's new campaign

Native base:
`/localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2`.

- Source: `source/gpu/orch_r118_route_startup_recovery.py`, SHA256 `c6e8e9b0aedc3a24903b1be0cbd20df8ba2751717921a4e2a9954a0b1a471e8f`.
- F1: `owners/F1/FRESH_OWNER_RECOVERY_PREPARED.json`, SHA256 `f59a2655fe83a938d29d4f3954a9ed1158726cf8944586f29ce2291b42e52973`.
- A1: `owners/A1/FRESH_OWNER_RECOVERY_PREPARED.json`, SHA256 `ec27ee04eb76a0e2d67e62363ffd8a8c690da4c310944d12f75b1d1b139e042b`.
- Compact export: `PREPARED_EXPORT.json`, SHA256 `19c1622a908cc912baadc7ae51018286194d3e0aa314a3690a5e6af41a37d7fb`.

Each owner contains the exact executable command, existing boundary and handoff,
cwd, environment and source-files union. The union adds only the new wrapper to
the unchanged frozen closure. Main can prepare its new all-eight campaign from
these source files. This worker does not create a competing campaign/session.

**Before dispatch:** bind the actual new Main campaign into root-local PLAN
control metadata, archiving prior bytes; bind corresponding broker metadata;
write fresh request references to the updated PLAN and final owner documents.
Prepared files are immutable historical evidence, not overwritten. They are
truthfully marked `runtime_staged:false` until this metadata step. The old
campaign is still bound at this observation; it must not be silently reused.
This is a data dependency, not another science approval requirement.

CPU-only verification of each prepared request is runnable exactly as its owner
command with `--verify-only` appended, and `CUDA_VISIBLE_DEVICES=''` from exec.
For example, on `gpu/ovx3_ssh.sh`:

```sh
CUDA_VISIBLE_DEVICES= /localhome/local-rohing/v2/venv/bin/python -B \
  /localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2/source/gpu/orch_r118_route_startup_recovery.py \
  --request /localhome/local-rohing/orch_r118_route_startup_recovery_20260915_v2/owners/F1/REQUEST_PREPARED.json \
  --request-sha256 c2ea7923fa662d204ec4d999cddf97d1f01703cabb25f2fa98a406fd26324652 \
  --verify-only
```

Do not remove `--verify-only` manually: actual startup additionally requires
Main's new live, source-bound dispatch session and branch environment. Main alone
dispatches all eight. Recovery requests expire16:10 UTC; inherited TRAIN16:55,
hard17:02, checkpoint/gen1 and original call caps are unchanged.

## Actual zero-new-call evidence

At native verification15:52:58:
- F1 N425/P68; ledger SHA256 `0b5a871529f354324b220b5482a8229698f19a1ca8493cfd7f8bccf4f8f020ce`.
- A1 N202/P36; ledger SHA256 `a67b4356a1963af964bb099b536e58a90cc9f95189c6269eb9adb72485a3de85`.

These match the pre-dispatch ledgers. Both original roots lack new route
actor/supervisor/bootstrap receipts; the old failure and scan hashes are bound
in prepared requests. This is route-only evidence, not a claim that no model
loaded in other families. No GPU signals, standalone launch, selector access,
optimizer operation, shared-state write, raw pull or Git mutation was performed.
