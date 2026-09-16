# Astra transition status — 2026-09-16 03:25 UTC

## What is actually running

- **F1:** saved-state actor2664733 and Astra broker2281435 are live. C56 starts
  from C55 adapter/AdamW/RNG/history, without replaying charged calls. Fresh
  parent000119_F1_C0056 is Astra SILENT, not substantive guidance.
- **F2:** saved-state actor2627464 and Astra broker2229344 are live. C46 sleep
  finished at16460 cumulative optimizer steps; DEV readout was observed running.
  Fresh C46E0/E1 both returned Astra COMPLETE. Native injection is still a
  separate verification; publication alone is not uptake.
- **F4:** the consumer successfully resumed C111 and completed that cycle,
  then **crashed at03:21:00 UTC** on `ValueError: uncropped_native_context`
  inside the subsequent episode. Actor2638280 is absent. It is **not running**.
  This is a separate context-capacity failure, not parent transport failure.
  The optional NEXT_GUIDANCE broker repair is installed: broker2314779 is live
  and owns the existing ledger lock, with repair high-water324. It will never
  replay P0323 or any slot<=324. No new request>324 has yet been generated.
  Therefore no successful repaired F4 parent delivery is claimed.
- **A2:** confirmed current actor **4156720**, not the obsolete4007301 listed
  in earlier inherited notes. Its R125 recovery wrapper is already in use;
  Main did not restart or alter it. At03:25:03Z it is running on physical5:
  native986,parent108,committed optimizer16029, with480 separately logged
  updates in the current C42 sleep. This is evidence of ongoing training.

## Preservation and remaining work

F4's state, failed-call evidence, C111 carry, frozen-gen1 adapter and original
FINAL/wall controller2615040 are preserved. The controller is alive; this does
not establish that FINAL can run with its native actor absent. A safe
context-capacity continuation is unresolved. No silent context cropping,
logical-child reset, fabricated model output or replay was performed to hide
the failure. F4 remains frozen-adapter elicitation, not optimizer learning.

F4 failure log (node-local):
`/localhome/local-rohing/orch_r139_F4_timer_source_v1/INITIAL_RESUME.log`
SHA256 `8d6e81427c19631f9c8a06df612daf1e613745e179843a03288af4476b58f098`.

F4 new broker publication SHA256:
`aff2fda6abd21b4d340a09ff52b8a4451029cdee0d38b9c977c9dce49ea1fdc7`.
Repair-boundary SHA256:
`79313811c9553a3959cf4f1ef6232a632ab36b183576dc7f25fcca462ac8ab2e`.

A2 actual command SHA256:
`910d612c4493b2ad86784ede50dfd98a78e9d2103dcc5810f41b67a747c89a39`,
PID4156720/start3661474. Earlier `A2/native.log` is an obsolete failed launch
log, not the live runtime-recovery log.

## Validation and counts

All11 R139 test modules pass when run in fresh processes: **136 tests PASS**.
Single-process aggregate discovery reports3 errors from conflicting pinned
runtime imports (`isolated_A4_import`); that mode is not claimed green. The
runtime isolation checks were not weakened. `git diff --check` passed on the
changed source/ledger/receipt paths.

The03:20:23Z eight-lane rolling-hour publication table is in STATUS_0320.md.
It is not a native-injection count or proof of retained learning. Historical
Fable/MISSING dispositions stay unchanged. The R121 paper scope and unresolved
four-way benchmark work remain as described in R121_LEVEL1_SCOPE_20260916.md.
