# Math second-session exit observation — 2026-09-15 16:20–16:21 UTC

Read-only observation; no scan rerun, launch, restage, signal, provider request or model call performed by this audit.

Session `/localhome/local-rohing/orch_r118_main_startup_recovery_20260915_1610/SESSION.json`, SHA256 `2987f2cba47868934fd6d465f0001c94e7d754d3b7972bb56c328ed6f081e641`, has dispatcher FAILED at 16:17:13.628 UTC (`fresh_owner_command_failed_A3`, retry_allowed=false). GO absent. Code owner diagnoses A3; no math root-cause attribution to A3 scanner details is inferred here.

Math service prefix `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4`:

| Branch | Guard PID | Actual resident subprocess PID | Terminal UTC | Preserved native/parent charges | Preserved files verified |
|---|---:|---:|---|---|---:|
| F2 / lane1 | 2752421 | 2752992 | 16:17:14.590 | 274 / 60 | 276 |
| A2 / lane5 | 2752425 | 2752990 | 16:17:14.559 | 170 / 36 | 181 |

All four PIDs absent at observation. Both GUARD_TERMINAL receipts are FAILED, native_alive=false, no_retry=true. Both actual ADMISSION receipts have clear=true/blocking_reasons=[]; original drift reasons remain in the unreconciled_blocking_reasons history field. Both LAUNCH receipts exist: CPU subprocess creation must not be confused with model residency. Both NATIVE.log files end `ValueError: failed_or_expired_session_must_not_start`, thrown at session_open before resident work. MODEL_LOADED, NEW_GRADIENT_RNG, and original-root R118_PARALLEL_BOOTSTRAP are absent.

All 457 original-root files bound by the prior PREINFERENCE_EXIT preserved_files maps still match their hashes, including counters and charged reservations. PREINFERENCE_EXIT itself describes the earlier failed session, NOT this second-session exit. Actual current reservation-file counts are F2 native101/parent60 and A2 native61/parent36; these file counts are not cumulative native totals. Incremental charged native/provider requests: **0 / 0** each. No model/bootstrap or optimizer execution observed; common STATE remains generation1, optimizer_steps3009/shared_optimizer_steps1884, checkpoint `43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d`. No claim of provider-side billing reconciliation beyond the unchanged local charge ledger.

Exact node evidence under the service prefix:

| Evidence | F2 SHA256 | A2 SHA256 |
|---|---|---|
| laneN/ADMISSION.json | 08e5db04c3965e8c528c32713ca91d855f1a8fd58aa77e50e8e2fb7ed32ab714 | 50008b348383cf84273a78753bd314ba6a4721942871df5c5d24da29d331d713 |
| laneN/GUARD_TERMINAL.json | cf37ca71c973c62c6e785daa377c8c13132ad7215420e3228056df95241500ea | 85e0c56d82c5ef47d5cb6047681034dba9f74dee15c67a30d21ba4fa96643925 |
| laneN/LAUNCH.json | b1b92d968057e5c8055d033a243d50ff207a2101adcaf9caa7f73093b7274f0e | c750cb1661a48143a1438d6ff1589b06a493e3773f76f3082a99a6bf6b7b038c |

F2 broker2722783 and A2 VM broker2690776 are also absent at observation; neither was restarted. Main selector1519259 remains live and untouched. Existing timers were not signaled or rebound. Original TRAIN16:55/native16:59/hard17:02 and separate FINAL allocation remain unchanged. Raw evidence remains node-local. This failed session will not be replayed or restaged.
