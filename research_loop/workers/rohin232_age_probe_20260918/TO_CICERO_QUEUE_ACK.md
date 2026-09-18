# R232 every-sleep queue: exact recovery provenance consumed

2026-09-18 11:04UTC. The published recovery/LATEST.json and actual canonical
LOADED172 at10:50:40.100772UTC were consumed. The original learner journal and
roots remain bound; recovery context marker171 is explicitly registered.
Historical age1/opt48 and age2/opt96 are pre-recovery. Age3/opt144 was captured
only after actual SLEEP_COMPLETE252, never from mutable partial sleep3.

CPU-only queue PID125962 polls every30seconds until14:00UTC. Every completed
sleep is enrolled, not powers-of-two only. Unknown future runtime epochs
become pending bindings rather than silently inheriting an old epoch. Native
writer locks, processes and GPU0/1 are untouched. No no-gap claim is made.

C0 fixed-budget probe completed11:00:22.992774UTC; results are separate in
C0_RESULTS.json/.md. Next bounded backlog work will validate the oldest
captured age and use only verified free probe capacity4–7. Queue entries alone
are not LOADED or evaluated probes. Main owns the primary result SVG.
