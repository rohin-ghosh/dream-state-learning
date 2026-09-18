# Node2 capacity reservation — 2026-09-17 16:41 PDT

Latest Main direction supersedes the earlier Chandra-first reservation in
R186_CHANDRA_PROBE_HANDOFF.md. Reserve GPU7 and completed/free comparison slots
for Tesla's six original-life exact handoffs before node3's 16:50 operational
stop / 17:00 real ceiling. Optional R187 node4 launches are deferred.

- GPU7: reserved for Tesla; a fresh device/process census is still required.
- GPU0/P4: saved44 observed at 16:37:05.523895 PDT; this alone is NOT a GPU
  release. Verify readout/native/service completion and actual capacity first.
- GPU5/LR.3, GPU6/LR3, GPU1/P32: incomplete windows remain running. Do not stop
  them or shorten the fixed42–44 comparison window for this reservation.
- GPU3/explicit1 and GPU4/brief1: uncapped baselines; release only after verifying
  complete42–44 checkpoints and preserving exact state. No stop has occurred.
- Chandra: a bounded probe may use a completed/free slot only if it fits the
  evacuation schedule and does not contend with Tesla. The earlier probe-first
  queue is no longer controlling.
- Repo GPU2/node2 and judge GPU2/node4 remain untouched.

This is a reservation, not an admission, transport, termination, or live-handoff
receipt. Tesla owns original-life transport/signals. Current source/checkpoints
are not changed. Actual terminal/exit/capacity evidence follows separately.
