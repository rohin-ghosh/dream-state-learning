# Experience Model v6 — common-prefix CompilerGym pilot v9 amendment

Status: proposed final ratification-candidate architecture bytes. The complete
v9 protocol is:

1. the exact v7 base protocol at SHA-256
   `6ddec2537cabcd4228a1d3144988f3483ba1e86ecc6be85fe5c82301449836b1`;
2. the exact v8 amendments at SHA-256
   `f4659794db70e2c31a8837148e241711c776c1a7cca86784d87fdc729964abd0`;
3. the acceptance-test amendment below.

The later clause supersedes only an earlier conflict. This revision changes no
experimental behavior, arm, model, writer, task, target, metric, visibility,
claim, or authority. It makes the already-normative lifecycle rule a literal
test obligation.

## A7. Lifecycle matrix must be tested, frozen, and audited

Replace the v8 acceptance-test namespace with:

* `V6S9_T01_STATE_ACTION_LIFECYCLE_GOLDENS`
* `V6S9_T02_SLEEP_SAMPLE_GOLDENS`
* `V6S9_T03_DOUBLE_SEAL`
* `V6S9_T04_PRE_GPU_REVIEW`
* `V6S9_T05_POSTRUN_AUDIT`

T01 must fault-inject an ordinary failure at every pre-panel phase represented
by the implementation: engineering canary; common-prefix reset/model/service/
slot commit/task commit; sleep-1 selection/tokenization/training/publication/
mount; either H/E continuation reset/model/service/slot commit/task commit;
sleep-2 selection/tokenization/training/publication/mount; and final snapshot/
panel construction. For every injection it must assert `RUN_INCOMPLETE` and an
empty forbidden execution suffix: no later model request, environment action,
training update, publication, mount, panel cell, or numeric report. It must
also inject an integrity failure at every lifecycle phase and assert immediate
`INTEGRITY_FAILURE` with no numeric release.

T01 separately injects an ordinary failure into each final-panel cell position.
It must assert that the failed cell is sealed missing, every remaining cell in
the already-frozen order runs once, no failed/prior result becomes model input,
no cell retries, both aggregate D values are absent, and the final status is
`PANEL_INCOMPLETE`. An integrity failure during the panel instead stops all
remaining cells and suppresses every numeric value.

T04 must bind one complete lifecycle transition table to the exact
implementation and run manifest. That table enumerates all phases above, the
single legal next phase for success and each failure class, and the exact H/E
branch and twelve-cell execution order. The pre-GPU reviewer must verify that
production control flow and T01 fixtures implement that table; an implicit or
code-derived-only table is a veto.

T05 must compare the actual ordered command/event/commit/status suffix with the
T04-bound lifecycle table. It verifies that the run stopped or continued at
the sole legal boundary, that no forbidden suffix exists, and that target-cell
continuation occurred only for ordinary post-entry cell failure. This lifecycle
check is in addition to v8's discrete update provenance, artifact/mount, packet,
target-feedback, and exact-rational recomputation requirements.

Independent fixture provenance from v8 A5 applies to every lifecycle golden.
No new retry, resume, salvage branch, test ID beyond the five listed above, or
science interpretation is introduced.
