# Node3 historical R174 mapping: observed, not switched

Current Rohin175 baseline-first proposal and refreshed inventory: `R175_HANDOFF.md`.
The unchanged-R166 staging language in this historical snapshot is superseded;
all baseline recipients are prospective, including hands-off contrasts.

Observed: 2026-09-17T13:22:16-07:00 (PDT).
Children: `[REDACTED_HOST]`. Parents: `nvl-ai`.

| GPU | Life | Child PID | Parent PID | Current parent clock/cadence |
| --- | --- | --- | --- | --- |
| 0 | support_free | 978750 | 3790951 | request/1 |
| 1 | creative_reread | 985544 | 3844172 | response/2 |
| 2 | brain_free | 989340 | 3860905 | request/1 |
| 3 | brain_guided | 979678 | 3800858 | response/2 |
| 4 | creative_free | 980283 | 3813748 | response/2 |
| 7 | creative_select | 982471 | 3824946 | response/3 |

All twelve identities verified by start ticks and argv; all six child PIDs matched their physical GPU. All parent loaded/bound config and source/provider hashes match.

Child root template: `/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2/control{GPU}/run1`.
Child config template: `/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2/control{GPU}/GUARD.json`.
Parent config template: `research_loop/workers/r179_context_survival_20260917/node3/parents/physical{GPU}/CONFIG.json`.

Full paths, exact hashes, process start ticks, source bindings, parent-call counters, pending-publication inbox IDs and recovery offsets: `INVENTORY_20260917T132216-0700.json`.

Main binding/helper/assignments have not been received. A/B/C/D and unchanged R166 control are unassigned; no switch or new-policy delivery is claimed.
All existing lives continue. No child was restarted, no parent was signalled, and no remote write/provider call occurred.
Preserve the request-clock distinction for support_free and brain_free; their current cadence 1 is not response-clock cadence 1.
Preserve pending publications; local registration alone does not prove rendered REQUEST exposure.
Internal stop September 17, 2026, 16:50 PDT; machine ceiling 17:00 PDT. No extension.
Initial 30-minute window: 13:18–13:48 PDT. A completed rollout requires both actual new-policy turn and rendered REQUEST proof after Main binding.
