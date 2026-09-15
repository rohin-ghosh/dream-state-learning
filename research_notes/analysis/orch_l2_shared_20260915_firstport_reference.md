# First-current-port deterministic reference, separate from guided FROZEN

September15, 2026, 00:57UTC. Non-material reporting correction only.
No ongoing driver, source, cohort, policy, runtime archive or process changes.

| Existing split/stage | Deterministic first-port goals | Both-goal pairs |
|---|---:|---:|
| Held initial | 8/16 | 0/8 |
| Held C1 | 8/16 | 0/8 |
| Held C2 | 8/16 | 0/8 |
| Held C3 | 8/16 | 0/8 |
| TRAIN C1 | 8/16 | 0/8 |
| TRAIN C2 | 8/16 | 0/8 |
| TRAIN C3 | 8/16 | 0/8 |

These are derived counts, not an8/16 assumption. Load the unchanged saved
COHORT and SOURCE bytes, verify source replay and their exact hashes, then
run the existing shared episode/scoring transitions with a deterministic
callback that immediately chooses the FIRST port in the CURRENT public list.
It never reads memory, conditions on the goal, calls a model, trains, or
regenerates worlds. Each world has two fixed opposite-goal tasks, and pair
success requires both correct and different first committed ports.

Proof artifact:
`orch_l2_shared_20260914_attempt1/FIRSTPORT_FIXED_REFERENCE_20260915.json`,
SHA256 `5bbbbeeb19ea98046caf415268e5f6a642fe534417f50e832689aebfefc1685a`.
Contains per-world exact task, route, public receipt, endpoint and score;
source/cohort/code hashes; zero model/provider calls/fits. Operator-only:
do not send these held trajectories or global source to any parent.

The first CPU attempt using `orch_replication.first_port` failed transition
assertions: that helper recognizes only user messages STARTING `ROUTE TASK`,
whereas the shared episode emits a RECEIPT followed by an embedded updated
`ROUTE TASK`. It reused stale initial ports. No score from that attempt is
reported. Its failure/disposition is preserved inside the proof artifact.
The standalone reporting callback in `gpu/orch_l2_shared_reference.py` reads
the latest embedded public task and preserves actual listed order. Original
helper and every native driver remain untouched. Four CPU regressions pass:
initial unsorted list order, actual post-receipt CURRENT update, ignoring
child-simulated task text, and refusing empty ports rather than stale fallback.

Guided FROZEN is the matched GUIDED/no-consolidation CONTROL. It is not this
deterministic reference. C2 SHORT/FROZEN each11/16goals,4/8both-goal pairs;
their unchanged e226 traces are identical16/16, so exceeding this deterministic
reference is retained starting capability, not a learned gain in this run.
LONG2rows/28updates is the first actual GUIDED consolidation treatment; causal
interpretation awaits its own completed same-stage held/control evidence.
UNPARENTED1row/26updates is earlier actual unparented consolidation, not guided.
The separately allocated new pilot starts original37ec; no e226 recipient
or ongoing-route source/provenance substitution is requested here.

At00:57UTC original SHORT C3 experience7/16 and FROZEN11/16 were recorded.
Neither lane was terminal or released; original guardians continue unchanged.
