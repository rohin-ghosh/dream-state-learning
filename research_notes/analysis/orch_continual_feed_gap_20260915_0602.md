# Continual feed gap and replacement segment — 2026-09-15 06:02 UTC

## Observed cause, not an inference from a healthy watcher

Main inspected native publisher PID3443504 and its frozen source adapter.
`gpu/orch_continual_batch_snapshot_node2.py` pins SOURCE to
`/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1` and requires
the original37ec identity. That original generation source stopped producing
while the fleet moved to newer exhaustion roots. The receiver watcher being
alive does not establish that current generation is being fed to training.

The last inspected publisher snapshot095 contains42 remaining candidates,
not the64 required for review. Its4633 captured calls end at
04:48:31.549811UTC. Snapshot timestamp is05:59:18.635773UTC. Repeated scans
of this retired source cannot fill the batch. The original publisher exited
at05:59:51.885861UTC under its11-minute dispatch margin before the unchanged
06:10:32.518UTC deadline, with96/128 review slots reserved.

Its last successful status snapshot was05:28:06.459553UTC, not a live
06:00 throughput observation:692 batch-admitted distinct targets,120 sampled
PASS within accepted batches,572 individually unreviewed there;284 sampled
PASS across all adjudicated batches. Its571.6 batch-admitted rows/hour was
a publisher-window statistic at that earlier cutoff, not current raw-generation
or qualified fleet throughput. The latest375 of these were ingested at L1
update2020, but still had zero presentations at the05:53:50 exposure audit.

No source was silently added to the existing frozen registry. No failed batch
was salvaged. No existing deadline or counter was reset. Old raw sources,
partial42 candidates, review failures, and publisher terminal remain preserved.

## Prospectively allocated replacement publisher segment

This is CPU/provider work; all existing GPU lanes keep running.

- Scope: current node2 BASE/37ec exhaustion **math TRAIN** generation only.
  Source identity/protocol and complete call provenance must be bound before
  first review. No teacher, checkpoint-derived, parenting or held outputs.
- Cicero owns the new native read-only source snapshot/registry adapter and
  tests under the new `orch_continual_exhaustion_feed` prefix.
- Hubble owns the disjoint new publisher integration/tests and compact run
  receipts under `orch_continual_exhaustion_publish`; teacher-fit preparation
  is paused, not declared launched.
- Additional ceiling:128 single-attempt review calls, at most2 concurrent;
  at most64 batches of2 calls. Per-call output cap no greater than8192 or
  the existing lower transport limit. New hard deadline08:00UTC, with the
  existing11-minute new-dispatch margin. No automatic extensions or retries.
- Aggregate ceilings remain separately visible: original128 plus new128
  equals256; original actual reserved96 is retained, not reset to zero in
  cumulative reporting. New calls have not started at this publication.
- Carry all prior seen hashes and held exclusions; preserve exact encoder
  checks and admission tags. Tag register/length and measure worked-method
  branching separately from counterfactual checks. Do not silently relabel
  old reviewer verdicts or mix source families to fill a batch.
- Keep raw calls, targets and archives on node disks. Repo gets source,
  tests, bounded manifests/hashes, counters and result reductions only.
- After CPU/provenance validation, record exact ready root/source hashes in
  COORDINATION and BOARD before first dispatch. Bind the receiver explicitly
  to this new segment; do not mutate the old pinned controller or registry.

This allocation is not a claim that the replacement publisher has launched,
that a row has been admitted, or that the continually fitted child has learned
from current exhaustion generation. Those require distinct receipts.
