# Second shared startup failed before bootstrap

[Builder Main] September 15, 2026, 16:18:56 UTC verification.

The checked launcher passed its five bounded CPU preflights and actually
started dispatcher **2752325 at 16:17:10 UTC**. All eight owner commands
spawned. At **16:17:13 UTC**, A3's launch-time GPU admission was rejected:
`ValueError: fresh_privileged_full_admission`, from the unchanged CODE guard.
The dispatcher recorded `fresh_owner_command_failed_A3` and
`retry_allowed=false`.

At 16:18:56 UTC there are **zero BOOTSTRAP_START receipts and no GO**.
No new shared learning or successful restart is claimed. CPU preflight
success did not establish launch-time GPU admission. The code owner is
investigating the actual rejected admission snapshot; no blanket waiver or
retry of this failed session is authorized. Each family is checking its
own successor exit and preserving charged work, timers and failure evidence.
Model loading in individual processes is not a successful shared bootstrap.

Wrapper: `gpu/ovx3_ssh.sh`. Root:
`/localhome/local-rohing/orch_r118_main_startup_recovery_20260915_1610`.

| Receipt | SHA256 |
| --- | --- |
| `SESSION.json` | `2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641` |
| `SESSION.dispatch/START.json` | `74a811802ff62b73ce92518a016cda34fdca4483e5c7ae171c2ea15d85aa3973` |
| `SESSION.dispatch/FAILED.json` | `3750fc1a74861d2f871be586d017d7d1edff0ba519f1a7ed72e0c7a99d4f4fa8` |

Owner CPU PIDs: F1 2752420, F2 2752421, F3 2752422, F4 2752423,
A1 2752424, A2 2752425, A3 2752426, A4 2752427.

The original request draft used an incorrect dispatcher CLI subcommand;
this was caught by inspecting the parser **before execution**. That draft
remains `CHECKED_DISPATCH_REQUEST.json`; the corrected, actually executed
request is `CHECKED_DISPATCH_REQUEST_V2.json`. It did not retry any model
input or consume a failed session. The earlier 15:43 failure is also preserved.

Original TRAIN ends 16:55 UTC; canonical FINAL selection stays 17:00 UTC,
selector 1519259. No quota, training deadline, sealed visibility or scientific
claim changes. Frozen-seed reference completed separately; its protocol-only
outputs are not evidence of retained-thinking or parenting gains.
