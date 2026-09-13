# Level1 operational inventory — requested 2026-09-13T0746Z

Read-only snapshot through existing `gpu/a40_ssh.sh` (node1) and `gpu/ovx_ssh.sh` (node2). No GPU/NVML queries, launches, kills, native collection, model/corpus reads, runtime edits, or repository changes. No response bodies or scientific outcomes inspected.

**12/12 controller PIDs alive; 12/12 launch identities and roster/plan/root bindings match; 0/12 cells with recorded failure markers or recognized error signatures in bounded worker-log tails.**
Controller identities compare PID, /proc start_ticks, UID and command-line SHA256 to `launched.json`; PPID changes to1 are expected after batch launcher exit, not identity drift. Worker checks compare stage/root arguments, launch/start receipts and current process state; worker start_ticks are observed, not independently birth-pinned in stage receipts.

Roster: `/tmp/astra_level1_roster_20260913_attempt1/roster.json`; SHA256 `ad1c8d522d295e3c1b33c7e6ed93fbf89c467d3206d61e449d6844905fa19423`. Both remote roster and pinned precheck-file hashes verified.
- node1: observed 2026-09-13 07:48:21 UTC; boot-ID match=True, UID match=True; batch submission finished=True (submission is not experiment completion).
- node2: observed 2026-09-13 07:48:22 UTC; boot-ID match=True, UID match=True; batch submission finished=True (submission is not experiment completion).

| Node / GPU | Cell | Controller PID / state | Controller start_ticks | Current stage / worker PID | OFF evidence | Failures | Next check |
|---|---|---|---|---|---|---|---|
| node1 / 0 | prediction_seed0 | 2874439 alive/S | 106617247 | fit started / 2882784 alive | 60/60; closed=True; released=True | none observed | F |
| node1 / 1 | prediction_seed1 | 2874893 alive/S | 106619760 | fit started / 2882706 alive | 60/60; closed=True; released=True | none observed | F |
| node1 / 2 | prediction_seed2 | 2875352 alive/S | 106621922 | fit started / 2882707 alive | 60/60; closed=True; released=True | none observed | F |
| node1 / 3 | goal_completion_seed0 | 2876101 alive/S | 106623667 | fit started / 2882487 alive | 60/60; closed=True; released=True | none observed | F |
| node1 / 4 | goal_completion_seed1 | 2877696 alive/S | 106625480 | fit started / 2882490 alive | 60/60; closed=True; released=True | none observed | F |
| node1 / 5 | goal_completion_seed2 | 2878855 alive/S | 106627269 | fit started / 2882491 alive | 60/60; closed=True; released=True | none observed | F |
| node2 / 1 | contradiction_seed0 | 4168522 alive/S | 51363231 | post launched/preflight / 4179267 alive | 60/60; closed=True; released=True | none observed | R |
| node2 / 2 | contradiction_seed1 | 4169406 alive/S | 51365100 | fit started / 4175431 exited (logged step 320) | 60/60; closed=True; released=True | none observed | F |
| node2 / 3 | contradiction_seed2 | 4169805 alive/S | 51366938 | fit started / 4176344 alive | 60/60; closed=True; released=True | none observed | F |
| node2 / 4 | update_judgement_seed0 | 4170978 alive/S | 51368810 | fit started / 4177072 alive | 60/60; closed=True; released=True | none observed | F |
| node2 / 5 | update_judgement_seed1 | 4172582 alive/S | 51370666 | fit started / 4177325 alive | 60/60; closed=True; released=True | none observed | F |
| node2 / 6 | update_judgement_seed2 | 4173845 alive/S | 51372544 | fit started / 4177845 alive | 60/60; closed=True; released=True | none observed | F |

## Exact next check
Recheck at **2026-09-13 07:50:22 UTC** using the same node wrapper and receipt-derived PIDs; no action is scheduled by this note.
- Root for each cell: `/localhome/local-rohing/astra_diagnostics/level1_<CELL>_20260913_attempt1`, where `<CELL>` is the exact table cell name.
- Launch receipt: `/tmp/astra_level1_roster_20260913_attempt1/batch_node1_parentfix/<CELL>/launched.json` for node1; `/tmp/astra_level1_roster_20260913_attempt1/batch_node2/<CELL>/launched.json` for node2. Do not substitute original pre-parentfix submission receipts.
- **F:** recheck the exact controller identity and fit worker `/proc/<PID>/stat` + cmdline; inspect `run/fit/fit.json`, `run/fit/adapter/DONE`, `run/fit/adapter/train_manifest.json` (completion accounting:320 steps), `run/fit/released.json`, then `run/post/launch.json` and `run/post/started.json`. Missing fit receipt/step log does not itself show a stall; training stdout may be buffered.
- **R:** recheck current worker, `run/<STATE>/closed.json` and `released.json`; after post, inspect `capture_complete.json`. Count response filenames only; do not read answer bodies or invoke collection.
- **C:** reconcile controller receipt and `controller_failure.json` versus `capture_complete.json`; an exited PID without a completion marker is not success.
- Every check also inspects `controller_failure.json`, `run/*/failure.json`, `run/*/cleanup_failure.json`, and only sanitized error classes from bounded stderr tails. On error/exited identity mismatch, report Main; no retry, kill, helper edit or collection here.

## Completion and limits
At this snapshot: 0/12 capture-complete markers; 0/12 collection claims. No native collection performed.
Observed process existence is not a GPU utilization/health claim. OFF release is based on existing release receipts, not a fresh NVML query. Files/processes were sampled sequentially; this is not an atomic distributed snapshot. No recorded failure is not a guarantee of eventual completion.

| Cell | Launch UTC | Nominal launch +5400s outer-cap reference |
|---|---|---|
| prediction_seed0 | 2026-09-13 07:41:32 UTC | 2026-09-13 09:11:32 UTC |
| prediction_seed1 | 2026-09-13 07:41:57 UTC | 2026-09-13 09:11:57 UTC |
| prediction_seed2 | 2026-09-13 07:42:19 UTC | 2026-09-13 09:12:19 UTC |
| goal_completion_seed0 | 2026-09-13 07:42:37 UTC | 2026-09-13 09:12:37 UTC |
| goal_completion_seed1 | 2026-09-13 07:42:55 UTC | 2026-09-13 09:12:55 UTC |
| goal_completion_seed2 | 2026-09-13 07:43:13 UTC | 2026-09-13 09:13:13 UTC |
| contradiction_seed0 | 2026-09-13 07:39:53 UTC | 2026-09-13 09:09:53 UTC |
| contradiction_seed1 | 2026-09-13 07:40:11 UTC | 2026-09-13 09:10:11 UTC |
| contradiction_seed2 | 2026-09-13 07:40:30 UTC | 2026-09-13 09:10:30 UTC |
| update_judgement_seed0 | 2026-09-13 07:40:48 UTC | 2026-09-13 09:10:48 UTC |
| update_judgement_seed1 | 2026-09-13 07:41:07 UTC | 2026-09-13 09:11:07 UTC |
| update_judgement_seed2 | 2026-09-13 07:41:26 UTC | 2026-09-13 09:11:26 UTC |

The cap references are operational estimates from submission time; the runtime starts its own monotonic deadline shortly after process creation. They do not authorize extending a timeout or intervening in other work.
