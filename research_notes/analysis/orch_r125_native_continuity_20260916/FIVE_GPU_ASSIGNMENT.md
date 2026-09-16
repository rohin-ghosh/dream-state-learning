# Continual child: one resident plus four experiment GPUs

Rohin's correction to Message 126 supersedes the interpretation that his GPU
question concerned the four-condition skill-acquisition study. No GPUs are
reserved for that study by this assignment.

| Role | Wrapper / physical GPU | Assignment timing |
|---|---|---|
| Continual child's resident inference + LoRA sleep | `ovx3` / 2 | Stage and run after current ownership/provenance checks and native CPU integration tests; first engineering run targeted within 30 minutes of this posting, not yet a launch receipt. |
| Child experiment slot 1 | `ovx3` / 6 | Earmark now; enable only after device/filesystem/process isolation is tested. |
| Child experiment slot 2 | `ovx3` / 7 | **Not available to the child at the R142 wall.** R142 ended at 05:22 UTC, but the prior 06:00 UTC FINAL reservation remains. Assign only after its readout has actually completed and released ownership, no earlier than the recorded 06:20 evaluation boundary. |
| Child experiment slot 3 | `a40r` / 0 | Earmark now; enable after current ownership, lease and sandbox checks. |
| Child experiment slot 4 | `a40r` / 2 | Same as slot 3. |

All dates above are September 16, 2026, UTC. These are **five assigned roles,
not five currently running or child-accessible GPUs**. Fresh occupancy and
CUDA-visible process checks are still required; no resident is preempted.
If the 06:00 readout lasts longer, slot 2 waits for actual release rather than
using a scheduled time as proof. The child's text stream and inbox can run
before its experiment tools are enabled.

## Isolation required before child-selected experiments

- Enforced GPU device access for the assigned slot, not merely
  `CUDA_VISIBLE_DEVICES`; no access to the resident's or another lane's GPU.
- A separate unprivileged process/container with a private writable job
  directory, read-only approved model/input mounts, and no access to research
  ledgers, held data, live checkpoints, host SSH config or credentials.
- No network and no host SSH or provider credentials inside the child job.
  A builder-owned broker submits restricted job requests to the assigned node;
  the model does not receive host shell access or node credentials.
- Hard time, CPU/RAM, process-count and output limits; bounded concurrency and
  GPU-memory scheduling; kill only broker-owned jobs at their bound walls.
- No arbitrary deletion, package installation, resource leasing or commands
  affecting other lives. Job specifications, actual invocations, results and
  source hashes are recorded on the nodes, with compact repo receipts.
- Negative tests must show denied reads/writes outside the job mount, denied
  access to other GPUs/processes and denied network access. Tool responses must
  reflect actual executed results, never narrated experiments.

Until these checks pass, the birth context truthfully says the child has a
text stream and inbox, **not a shell or GPU-experiment tools**. This does not
block the resident continuity/sleep proof. No hardware isolation is claimed
from a prompt or command allowlist alone.
