# SEQ-252: trajectory-label ablation fails both contextual two-hop panels

September14,2026. One native TRAJECTORY_LOSS_OFF fit and fresh AFTER are COMPLETE.
Source4f1d7b689e7892d989cb97e6406d5c80d9bfb6a8. Independent bounded review pending.

| Endpoint | Full trajectory sleep (SEQ250/251) | Matched trajectory-loss-off |
|---|---:|---:|
| Original graph OWN_TEXT goals | 3/4 | 0/4 |
| Fresh graph OWN_TEXT goals | 3/4 | 0/4 |
| Original graph parametric / unavailable / OFF goals | 0/4 each | 0/4 each |
| Fresh graph unavailable goals | 0/4 | 0/4 |
| Old16facts W0 / W8 | 16/16 each | 11/16 each |
| Held audit | 16/16 | 15/16 |

The control starts at the exact207ad parent and uses the same222 saved rows,
input tokens,100batch-index tuples, freshAdamW3e-5, seed0 and rank8 as SEQ250.
Only trajectory-row labels210–221 are masked. All old memory/cue/audit labels
are unchanged. Each batch multiplies its mean loss by active-control labels /
full-reference labels, preserving the full-reference denominator:5977 active
control labels against8245 reference labels; zero supervised trajectory labels.
This is a label-gradient ablation, not an equal-active-token treatment and not
a whole-life unparented control. No FULL refit or new teaching occurred.

All four control OWN_TEXT episodes on each graph terminate with a goal NODE
used as the ROUTE argument, rather than a port; none commits a route. This is
the pre-lesson failure pattern. The full-target child instead performs legal
two-step actions on3/4 cases in each graph. On this one lineage and recipe,
the trajectory targets add useful action behavior beyond the matched rehearsal.
The observed gain cannot be ascribed simply to another rehearsal-only sleep.

However achieved retention is NOT matched: the ablated run also loses five
old facts and one audit case. Removing targets changes the entire optimizer
trajectory, not just a separable skill component. Do not claim that supervision
affects only routing, that the control is equivalently competent otherwise,
or that one run estimates population parenting efficacy. The saved no-write
parent provides a second contextual0/4 comparison without this new forgetting.
Three-seed replication and complete developmental/control lives remain pending.

## Native record and cost

Root `/tmp/astra_event_two_hop_lesson_control_20260914_attempt1`, node2GPU0,
guardian398565,15:56:24–16:04:47UTC. Train260.051s; AFTER240.338s; total500.389
native-phase seconds (~0.1390dedicatedA40h), not kernel-only time. AFTER173calls;
all measured failures retained. Native frozen-base, saved-state and unchanged
source-file checks PASS. Initial207ad43ef65f1f6ba7c50d37f5d5dfa8c2253d1cb301e585d7b6b7a78bb93990;
saved/reloaded1f3d2614dfa66a6648f83fbcd96579b99464a59a7711a595b221200e9ad6383b.

Complete source/adapter/calls capsule:
`gpu_artifacts_local/astra_event_two_hop_lesson_control_terminal_20260914_attempt1/extracted`.
Local/remote archive SHA256:
`602454f836ed759648711af80f6a54cf254aa4b7a13af1529caa0853b305e35c`.
Main8focusedCPUtests and actual-source preparation passed before launch. No
controller remains live for this run and no process was killed.

The separate fresh-memory write already completed100updates on node2GPU1;
its AFTER is still running. Do not import its pending outcome into this result.
