# NODE1 first actual successor — 2026-09-17

**Lane4 / teach_parenting has actually loaded the exact saved successor.**
This is runtime journal/guard/containment evidence, not a CPU-pass inference.

- New native actor PID **1418920**, start ticks `38727122`.
- Actual source:
  `/localhome/local-rohing/orch_r179_node1_20260917_attempt2/lanes/lane4/source`.
- Actual guard:
  `/localhome/local-rohing/orch_r179_node1_20260917_attempt2/lanes/lane4/readmission1/GUARD.json`.
- Original life/inbox remains:
  `/localhome/local-rohing/orch_r136_a100_teach_parenting_20260916_attempt1/run1`.
- Saved sleep **41**, AdamW optimizer steps **4428**, adapter state
  `534c1e940b5d56631a6b038a9f523972e2cc4de31521b417d92f972bfa6fbdf0`.
- Saved full stream envelope
  `7432e7356f129dfcbe61a28b36361f4eb95177ff821982fa44c47841f734a308`
  restored exactly in the actual receiving CPU process before retirement.
- Native SHA: `1b6cb9622d5da9cfa54bb7ada1292e0de9b994cb9aea2f65474143bfe03a9a3b`.
- Main policy SHA: `b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b`.

## Actual proofs

Local complete metadata collection:
`EXECUTION_STATUS_1789666426320909115.json`, SHA
`7c8c9b807cd0fd510daade6aea5e6ff14b3de6c28aafc7ff6537bc86eab58889`.

Within that collection, the actual remote
`lanes/lane4/readmission1/LOADED_RECEIPT.json` SHA is
`1c8fa0737be20bacdd9bc1cb5927559a5616a07bcdf620b7eec18051b91a4e07`.
The underlying LOADED journal record SHA is
`a9c98ee0e3ca877926fb6c07cf6b796122be51dee909b0271d5a0a1df5220c97`;
observed load timestamp is Unix `1789666270.5483367`.

Privileged admission passed with no blockers, SHA
`e58709c968a1cd45063b1360c4e431a5a5354b78f69709af6ae1132008290f99`.
Seven-foreign-device confinement proof SHA:
`9e1affc3dfcf40f8f484bd1fb6d644cad3db25a4fb5db8e42156800aaf7e552c`.
Actual full-state receiving CPU proof SHA:
`92b3999d77e8dbbf61c0db3d81dc3102c4314457f4d46d2a72d9d9fb93de3c8a`.

The first attempt's dispatch-before-readout-child race and the first actual
privileged scanner identity-drift denial are preserved, not suppressed. See
`REPAIR_AND_READMISSION.md`. The repaired operator required a started readout
before pause. One explicit fresh readmission was allowed only after proving no
native had launched, the drift PID was gone, and the source/boundary/checkpoint
were unchanged. No scanner exception or guard bypass was introduced.

## Remaining live work

- Lanes **2, 3, 5, 6** have actual staged immutable sources, three receiving CPU
  checks each, and independent live attempt2 saved-boundary operators. Their
  operator PIDs at dispatch: 1366474, 1367396, 1368572, 1369540 respectively.
  They are not reported as handed off or loaded yet. Watch limits are 5400s;
  expiry leaves the original running. Their existing methods/walls remain fixed.
- Lane **7 / classroom_support** was actually verified as already compliant
  via its original no-distillation prepare branch; **no restart**. Original actor
  PID1997023 remains the observation bound by the no-op receipt.
- Frozen controls and all other nodes remain untouched.

`CONTEXT_CUSTODY_LANE4_1789666437197974996.json` currently establishes a verified
post-handoff journal prefix containing LOADED, INBOX and REQUEST, through index
5021. It does **not** yet establish a completed new generation, CONTEXT_RETAINED,
a subsequent completed sleep or post-sleep prompt custody. No such claim is made.
The read-only observer has five passing CPU checks and exports hashes/counts,
not child text. Later checks:

```sh
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B research_loop/workers/r179_context_survival_20260917/node1/collect_status.py
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B research_loop/workers/r179_context_survival_20260917/node1/observe_retained.py --physical 4
```

No sealed response/map/score data or credentials were opened; no parent message
or COORDINATION edit was made. Source-preservation copying did not open non-code
source assets. Original history/journal records were not rewritten or replayed.
