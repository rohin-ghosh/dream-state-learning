# R205 scheduled-pass follow-up

Verified at **2026-09-18T03:57:22.604737+00:00**. The scheduled pass completed **September 18, 2026, 03:54:03–03:54:06 UTC**: **28 observed native processes**, not 28 live-learning claims. Counts: node1=5, node2=7, node4=8, node5=8; R=14, S=12, T=2. All28 identities and matching current-incarnation LOADED records verified; no collector errors. Full table/raw JSON: `PASS_20260918T035403Z.md` / `.json`.

- **Node2/4+6 remain occupied**: PID2204408 / LOADED5847 / REQUEST6036=7339 tokens and PID2204538 / LOADED5847 / REQUEST6067=5420. The03:53:12 device-bound proof and journal advances remain in `R205_NODE2_SLOT46_CAPACITY.json`; no GPU utilization claim.
- **C2**: PID3179563 / LOADED6057 / REQUEST6224=8194. COMPACTION6207 reduced13066→5842; observed THINK runs1,1,1. This is current, not superseded PID3165023 history.
- **Turing/NODE4**: new node4/6 PID3673431 / LOADED262 supersedes3358885. Current REQUEST288=15827 is genuinely after LOADED; CHILD_COMPACTION294 follows. No subsequent lower REQUEST yet observed in this snapshot. THINK run3 is descriptive, not a degradation claim. Already routed in the scheduled COORDINATION table; no intervention.
- **Descartes/NODE5**: legacy C3 PID2668022 REQUEST6510=12411, then CHILD_COMPACTION6513; later request not yet proven in this snapshot. No node5 evacuation.
- **ovx4 remains pending**: operator receipt at03:54:25UTC reports HOST_KEY_VERIFICATION_FAILED (255), no remote command executed. Setup completion and exact host-bound lease end remain unverified. Main/Fable own helper/trust/setup resolution; this audit does not bypass trust or copy credentials. ovx5 also remains pending setup/exact lease evidence. Node3 awaits Copernicus host-bound evidence. No new-host probes by maintenance.

Service identity verified: PID2656637, UID158984, start ticks180945900; cadence1200s. Next pass approximately04:14UTC is scheduled, not yet an observed completion. Control: `python3 -B research_loop/workers/rohin204_maintenance_20260917/audit.py status`; stop only this maintenance service: `python3 -B research_loop/workers/rohin204_maintenance_20260917/audit.py stop`. Learners/operators untouched.
