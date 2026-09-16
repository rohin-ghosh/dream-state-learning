# Child-selected experiment confinement — independent review

September 16, 2026, 07:39 UTC. **Verdict: not yet demonstrated; CPU-only
confinement testing may proceed separately from the running child.** This is
a review, not implementation, launch authorization, or a resident/scheduler
change. Only this file is owned by this reviewer. No exploits, remote calls,
sandbox executions, device opens, or live-process tests were performed.

## Evidence and immediate blocker

Read `FIVE_GPU_ASSIGNMENT.md`, `ISOLATION_PROBE.md` (including Main's 06:35
and 07:26 UTC follow-ups), and
`../orch_r124_continuity_20260916/BUILD_SCOPE.md`. Those records show failed
unprivileged network-namespace setup, successful privileged namespace setup
with an `id -u` payload returning zero, and no complete negative-test receipt.
Root inside a namespace does not identify the host UID; neither successful
setup nor an empty effective capability set proves safe execution.

**Unverified advisory lead supplied by the requester:** upstream bubblewrap
advisory **GHSA-pxhw-h44j-8pfx** reports setup symlink traversal in
attacker-controlled mounts affecting versions **<0.12.0**. The probe records
local **0.9.0**. The advisory was not independently fetched because remote
calls were prohibited for that review. The builder's later retrieval also failed;
the advisory/version attribution is not independently verified and is not a
launch-gate premise. Do not test the exploit.
The successful privileged probe is not evidence against this setup-time risk.

## Minimum contract and alternatives

Python/shell **payload bytes may be child-chosen; privileged launch parameters
must not be**. A broker accepts bounded source and approved input identifiers,
not host commands, unit properties, mount paths, device lists, executable
overrides, environment overrides, or cleanup paths. It runs outside child
reach. All retries and subprocesses retain confinement; no host-shell fallback.

| Candidate | Minimum acceptable conditions | Assessment |
| --- | --- | --- |
| System-manager transient **service** with `RootDirectory=`, `DynamicUser=yes`, `PrivateNetwork=yes`, `PrivateDevices=yes`, `DevicePolicy=strict` | Trusted minimal root tree and runtime; explicit read-only approved inputs; private bounded scratch; no host home, repository, `/run`, credentials, held data, or inherited sockets. Add `NoNewPrivileges=yes`, empty capability bounding/ambient sets, resource limits and whole-cgroup termination. Establish process visibility/isolation separately; these named settings do not themselves prove a private PID namespace. Verify effective device BPF and actual payload credentials. | Preferred CPU-only candidate to investigate: avoids the affected bwrap setup path **if it does not invoke bwrap**. Requires trusted system-manager authority, not merely a delegated user service. `RootDirectory` alone is not confinement; `PrivateNetwork` does not remove inherited sockets or filesystem Unix sockets. `DynamicUser` identity recycling makes output ownership/cleanup important. Installed systemd 255 support and effective enforcement still need receipts. |
| Privileged bwrap with fixed trusted mount configuration | Root-owned launcher/runtime/configuration and every setup path ancestor; no child-controlled mount source/destination tree, symlink, writable ancestor, or race during setup. Stage bounded regular-file payload bytes through trusted code, not attacker-supplied archives/directories. Drop to a dedicated non-root **host** identity before payload execution; prove mappings, groups and capabilities. Separate trusted cgroup/device enforcement is required. | A genuinely trusted mount topology narrows the advisory's stated precondition, but a read-only bind of a child-owned tree does not make setup trustworthy. For this first trial, reject 0.9.0 unless a verified fix/backport is established; prefer a verified fixed build at least 0.12.0. An older-build exception would require separate evidence of complete precondition exclusion, not a successful smoke test. Fixed bwrap still needs every contract test below. |

For either path: no host UID 0 payload and no broker/resident/wrapper-account
identity reuse. Record host-observed UID/GID/groups and `uid_map`/`gid_map`, not
just `id` inside the sandbox. Require private process view/fresh procfs or a
demonstrably equivalent restricted view plus cross-process denial; no host
namespace handles, writable cgroups, manager sockets, or child BPF authority.
Mounts are deny-by-default: a read-only secret or held dataset is still a leak.
Runtime libraries, Python startup paths and shell initialization must also be
trusted; no child-selected dependency installation or privileged import hooks.

## Risk-ranked acceptance tests — proposed, not executed

Use synthetic canaries, disposable peers and tiny limits only. These tests
are not permission to read actual secrets/held data, touch reserved GPUs, run
exploits, or saturate shared nodes. Each row requires expected and observed
results bound to the exact launch profile; configuration acceptance alone fails.

| Priority / risk | Concrete acceptance evidence |
| --- | --- |
| **P0 — privileged setup / fail-open** | Record executable/package hashes and fix provenance, trusted root/mount manifest and parent ownership. Reject child-supplied unit/mount/device options and symlink-bearing setup inputs **before privileged setup**. Inject missing runtime, denied namespace creation, rejected unit property and absent required device policy: a dummy payload marker must never appear; no ordinary `Popen`/shell retry executes it. This is failure-path testing, not advisory exploitation. |
| **P0 — secrets / held-data exposure** | Place dummy secret, held-score and live-checkpoint canaries outside approved mounts. Allowed input read and scratch write succeed; outside reads/writes, traversal, payload-level symlink access, proc root/FD paths and inherited-directory-FD access fail. Enumerate the payload's own environment/FDs: only approved nonsecret variables and bounded I/O channels exist. No host HOME, SSH/agent sockets, manager sockets, live trees or held-derived input enters the manifest. |
| **P0 — host identity / peer control** | Trusted observer records host credentials, mappings, zero payload capability sets, no-new-privileges, namespace IDs and cgroup membership. A disposable broker-like peer remains inaccessible through proc inspection, ptrace/process-memory/pidfd access and signaling. Payload cannot acquire host namespace handles, elevate identity, load BPF, migrate cgroups or change its limits. Never target a resident or scheduler. |
| **P0 — device escape** | CPU profile has only approved pseudo-devices, no NVIDIA nodes/FDs and no device-node creation permission. Authorized observer records effective ancestor/leaf cgroup device BPF, not just `DevicePolicy` text or missing v1 files. Use a harmless disposable test device to distinguish permitted from denied opens without GPUs. Unknown BPF authority/enforcement fails this gate. |
| **P0 — network / broker bypass** | Against disposable harness endpoints only, verify no host/external IPv4/IPv6, host loopback, abstract or filesystem socket reachability; no inherited network FD or broker relay. Declare whether sandbox-private loopback/IPC is allowed. If claiming no sockets at all, verify syscall denial too; `PrivateNetwork` alone does not establish that claim. |
| **P1 — resource / descendant escape** | Verify actual `cpu.max`, `memory.max`, `memory.swap.max`, `pids.max` and mount/storage limits. Small disposable child trees hit deliberately low task/memory limits without affecting a dummy peer; scratch exhaustion and output excess terminate or reject the job. Exercise timeout, forked descendants, parent exit and broker failure: all job tasks are killed within the stated bound and cannot restart or escape the cgroup. No host saturation tests. |
| **P1 — output / cleanup authority** | Bound stdout/stderr while streaming, before buffering or journaling; cap artifact count, per-file size and total bytes. Reject symlink/special-file/traversal artifacts and terminal-control rendering; never execute/import extracted results. After whole-cgroup termination, trusted collection copies only validated regular files to broker-owned receipts. Cleanup uses broker-created job identity/directory handles, never child paths or broad UID/process-name kills. Test malicious filenames, stale IDs and repeated cleanup against dummy neighboring jobs: their files/tasks survive; no recycled DynamicUser UID inherits leftovers. |
| **P1 — evidence integrity** | Capture source/input/runtime/profile digests, admission identity, actual invocation, allow/deny outcomes, start/end times, exit/timeout/limit reasons, output truncation and cleanup result outside child-writable storage. A positive trivial Python and shell run succeeds through the same dispatcher as negative tests. Results are labeled untrusted observations, not child claims accepted as facts. |

## What permits a limited first experiment

After all applicable P0/P1 rows pass on the actual selected node/profile,
Main could admit **one offline CPU-only standard-library Python or shell job**,
separate from the resident. Proposed initial ceilings: one concurrent job,
one CPU equivalent, 512 MiB RAM, zero swap, 16 tasks, 30-second runtime plus
at most 5 seconds for whole-cgroup teardown, 32 MiB total writable storage
including temporary files, 64 KiB submitted source and 1 MiB combined returned
output/artifacts. Verify host headroom and use lower limits if necessary.
No GPU, model, live checkpoint, network, credentials or held data is needed.
Hold limits through collection/cleanup, not just the immediate shell process.

Evidence must include the effective service or bwrap configuration, trusted
setup/fix evidence, host identity and namespace receipt, device-BPF/resource
receipt, synthetic allow/deny matrix and bounded cleanup receipt. A missing
control disables the job; it does not authorize a weaker fallback. This
limited acceptance is not permission to change the running child's tools.

**GPU access remains a separate unmet gate.** `FIVE_GPU_ASSIGNMENT.md` reports
a40r physical0→minor3 and physical2→minor1, whereas the probe merely stats
`/dev/nvidia0` and `/dev/nvidia2`; it does not resolve that mapping. Obtain fresh
custody/lease and UUID→major:minor binding before any GPU admission. Exclude
ovx3 physical7 without explicit release; do not probe it for negative tests.
Later enforcement needs an exact assigned-device allowlist and justification
of shared NVIDIA control/UVM nodes and ioctl reach, tested using authorized
disposable resources only. `CUDA_VISIBLE_DEVICES` and visible device filenames
are not security controls. CPU cgroups do not establish hard GPU-memory/compute
quotas or freedom from shared-driver interference.

## What remains impossible to assert from this review

No current child confinement, safe GPU execution, absence of all kernel/driver
escapes or side channels, general held-data noninterference, resource fairness,
scientific validity, learning benefit or continuity is established. A passing
CPU matrix supports only the tested policy/build/node and bounded workload;
it does not prove arbitrary hostile-code safety on a shared kernel. Changes
to setup bytes, inputs/mounts, identity, device exposure or policy require new
bound evidence. Nothing here pauses, restarts, or modifies the resident.
