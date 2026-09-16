# Child-experiment isolation: read-only feasibility probe

## Scope and verdict

- Observed on **2026-09-16, approximately 06:13–06:15 UTC** (2026-09-15, approximately 23:13–23:15 America/Los_Angeles). Compact host receipts were timestamped `06:14:02.486151Z` for `ovx3` and `06:14:03.370218Z` for `a40r`.
- Assigned candidates only: **ovx3physical6**, **a40r0**, **a40r2**. Reserved **ovx3physical7 was not queried, statted, opened, allocated, or otherwise touched**. No other per-GPU device paths were inspected.
- Access used only `bash gpu/ovx3_ssh.sh 'python3 -B -'` and `bash gpu/a40r_ssh.sh 'python3 -B -'`. Local source inspection was read-only. No Git or ledger commands/mutations; this report is the only authored file. No resident coordination, pause, restart, or admission decision.
- No GPU management queries, device opens/ioctls, allocations, model imports/loads, sandbox launches, package installs, signals, privilege escalation, or credential-content inspection. Tool executions were version queries, read-only `systemctl show`, and read-only cgroup-BPF inspection. No raw hostnames, connection targets, environment values, or credential material are included. Wrapper stderr was withheld.
- **Verdict: partial ingredients exist, but child isolation is NOT demonstrated or ready to claim.** Resource delegation is available through each user's systemd service. An unprivileged namespace-based launcher is a conditional implementation candidate, with a live AppArmor permission question. No usable unprivileged device-controller enforcement path was established. The inspected R125 launcher itself does not establish these isolation boundaries.

This is an observational sidecar, not an architecture change, implemented sandbox, scientific claim, or launch authorization. Main's separate resident work is outside this sidecar. Remaining tests below are proposals, not commands executed or permission to touch reserved resources.

## Direct observations

### Executable paths and versions

Both aliases returned the same inventory under the wrapper account's PATH:

| Tool | Resolved PATH entry | Version / result |
| --- | --- | --- |
| bwrap | `/usr/bin/bwrap` | `bubblewrap 0.9.0` |
| unshare | `/usr/bin/unshare` | `unshare from util-linux 2.39.3` |
| docker | Not found in PATH | No executable/version established |
| podman | Not found in PATH | No executable/version established |
| systemd-run | `/usr/bin/systemd-run` | `systemd 255 (255.4-1ubuntu8.17)` |
| systemctl | `/usr/bin/systemctl` | Same systemd version; user-manager query succeeded |
| newuidmap / newgidmap | Neither found in PATH | No subordinate-ID helper execution path established |
| bpftool | `/usr/sbin/bpftool` | Present; effective attached-program query failed with EPERM |

The inspected bwrap, unshare, systemd-run and bpftool entries were root-owned `0755`, not setuid/setgid, and not writable by the wrapper user. Their `security.capability` xattr reads returned errno 61 (no attribute). Presence is not an executable sandbox test; PATH absence is not an exhaustive disk search. No container daemon was contacted. Default Docker and system/user Podman socket locations were absent on both aliases. Other runtime endpoints were not searched.

### Account and namespace permission envelope

| Observation | ovx3 | a40r |
| --- | --- | --- |
| Kernel release | `7.0.0-31-generic` | Same |
| Effective UID / GID | `2524 / 2524` | Same |
| Supplementary groups | `1002, 2524` | Same |
| Effective / permitted / ambient capabilities | All zero | Same |
| Capability bounding set | `000001ffffffffff` | Same |
| `NoNewPrivs` / `Seccomp` in probe | `0 / 0` | Same |
| `kernel.unprivileged_userns_clone` | `1` | `1` |
| `user.max_user_namespaces` | `3860576` | `3860473` |
| `user.max_net_namespaces` / `user.max_pid_namespaces` | Each `3860576` | Each `3860473` |
| AppArmor enabled / probe profile | `Y / unconfined` | Same |
| `kernel.apparmor_restrict_unprivileged_userns` | `1` | `1` |
| `kernel.yama.ptrace_scope` | `1` | `1` |
| `kernel.unprivileged_bpf_disabled` | `2` | `2` |

The namespace-count sysctls and userns toggle are permissive ingredients, **not proof of permission to create usable namespaces**. AppArmor's unprivileged-userns restriction is enabled. The three checked profile files (`/etc/apparmor.d/bwrap`, `bubblewrap`, `unshare`) were absent, and the loaded-profile listing was unreadable. This does not prove that no alternative profile exists, nor that bwrap will fail; actual creation and mount/net/PID operations remain untested. Each subordinate-ID mapping file had one matching account entry, but the helper programs were absent. Mapping values and other accounts were not retained. A single-ID mapping may suffice for a particular design; a multi-ID/rootless-container setup has not been established.

The `/proc/self/ns/*` versus `/proc/1/ns/*` comparison was **inconclusive**: the PID-1 link strings did not match the expected namespace-link format, while the self links did. Do not interpret the unequal strings as existing PID/network/user isolation. The observed proc mount had no `hidepid` option. No other job's command line, environment, descriptors, memory, or status was inspected.

These observations bind to the wrapper account and its probe processes. They do not establish the actual resident/broker process credentials, inherited descriptors, namespace membership, or cgroup placement. No live resident PID was located or inspected.

### Cgroup enforcement and delegation

Both aliases expose a writable-mounted **cgroup v2** hierarchy. Its root advertises `cpuset cpu io memory hugetlb pids rdma misc dmem`. The wrapper SSH-session cgroup and inspected ancestors were root-owned and not writable by UID 2524. In particular, its current `cgroup.procs` and `cgroup.subtree_control` were not writable. Directly placing a child under that session is not an established resource-control mechanism.

Separately, `/sys/fs/cgroup/user.slice/user-2524.slice/user@2524.service` and its `cgroup.procs` / `cgroup.subtree_control` were UID/GID 2524-owned and writable. That service's available and enabled subtree controllers were **`cpu memory pids`**. Read-only systemd queries returned:

```text
ActiveState=active
Delegate=yes
DevicePolicy=auto
NoNewPrivileges=no
RestrictNamespaces=no
```

The user manager answered `Version=255.4-1ubuntu8.17` on both aliases. Thus a user-service-based CPU/memory/PID containment path is plausible, unlike direct modification of the current SSH-session cgroup. No transient unit was created, no process was moved, and no limit was installed or exercised. The service properties are configuration observations, not measured child constraints.

The checked `devices.allow`, `devices.deny`, and `devices.list` files were absent in the v2 hierarchy. **Their absence does not show that devices are unrestricted**: v2 device restrictions require considering attached cgroup BPF programs rather than the v1 files. Read-only `bpftool -j cgroup show <current-cgroup> effective` returned exit **255**, with **Operation not permitted** in its JSON output on both aliases. Consequently, inherited device filters could not be established or ruled out. No program was loaded or attached.

Zero effective capabilities, disabled unprivileged BPF, CPU/memory/PID-only observed delegation, and the failed BPF query provide **no demonstrated route for this account to install a GPU device allowlist**. `Delegate=yes`, the systemd executable, and `DevicePolicy=auto` are not evidence of such a route. A trusted host-side device-policy service or administrator-provisioned cgroup remains a potential dependency, not an available/approved capability. No sudo policy or privileged service was exercised to bypass this gap.

### Assigned-device metadata only

All listed device nodes were root:root, mode `0666`, and passed `os.access(R_OK/W_OK)` for the probe account. These are filesystem/DAC observations, **not successful driver opens, BPF-policy checks, allocation checks, or proof of GPU identity**.

| Alias / candidate | Node | Character major:minor |
| --- | --- | --- |
| ovx3 / ovx3physical6 | `/dev/nvidia6` | `195:6` |
| a40r / a40r0 | `/dev/nvidia0` | `195:0` |
| a40r / a40r2 | `/dev/nvidia2` | `195:2` |
| ovx3 / shared driver metadata | `/dev/nvidiactl`, `/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools` | `195:255`, `504:0`, `504:1` |
| a40r / shared driver metadata | Same three shared paths | `195:255`, `508:0`, `508:1` |

No `/dev` enumeration occurred. No other GPU's node was inspected. The assigned physical-index-to-device/UUID binding must come from main's approved provenance; this probe did not validate it with a driver query. Shared control/UVM nodes also mean that showing only one numbered device path is insufficient evidence of complete GPU-driver isolation.

### Filesystem exposure and inspected launcher

On both aliases the account home directory was UID/GID 2524-owned `0750`, readable/writable/searchable by this same account; `/tmp` was root-owned `1777` and readable/writable/searchable. `/data` was absent. Only directory metadata was inspected: **no credentials, held corpus, sealed scores, home contents, or live child artifacts were read**. Actual held-data paths, permissions, ACLs, mounts, and their relationship to broker-owned paths remain unknown.

Local source inspection provides a separate, limited finding:

- `gpu/orch_r125_continual_guard.py:83` copies `os.environ` before adding runtime variables. Its `Popen` at line 102 selects a working directory, pipes/logs, GPU environment, and a new session. That launch site does not supply a sanitized allowlist environment, dedicated UID, namespace launcher, syscall filter, or device-policy mechanism. The privileged scan is an admission step, not child confinement. This sidecar did not invoke it.
- `gpu/orch_r125_continual_native.py:132` starts the fresh readout with ordinary `Popen`, with no explicit replacement environment or sandbox in that call. Line 160 checks `CUDA_VISIBLE_DEVICES`. This is a selection/contract check, not an OS access-denial test.

These are source-level observations only: deployed source hashes and any external parent confinement were not inspected. Starting a new session, setting offline-library variables, or copying source into another directory does not itself show denial of sockets, held files, credentials, or other processes. An empty effective capability set is not equivalent to `NoNewPrivileges=1`.

## Feasibility by requested boundary

| Boundary | Current assessment | Remaining implementation control |
| --- | --- | --- |
| Network denial | Not demonstrated. No network syscall, connection, or network-namespace creation was attempted. | Usable separate network namespace and/or reviewed syscall policy; no inherited network FDs, proxy/agent sockets, host network handles, or unrestricted broker relay. Test loopback and IPv4/IPv6 as well as external routes. |
| Credential and held-filesystem denial | Not demonstrated. Same-account ambient access and inherited environment remain concerns. | Default-empty mount view; explicit read-only code/model/runtime allowlist; child-only writable scratch/output; sanitized HOME/environment; descriptor allowlist; no host home, repository secrets/held trees, host `/proc`, `/run`, or parent-root escape. Read-only exposure is still readable exposure. |
| Other GPU/device denial | No usable device enforcement path established. DAC on the assigned nodes is broad; inherited cgroup BPF is unknown. | Explicit minimal `/dev`, no inherited device FDs, no device-node creation/privilege escalation, and an independently enforced major/minor allowlist where required. Resolve shared NVIDIA driver-node/ioctl exposure and actual assigned-device identity. CPU-only broker and GPU worker may require different profiles. |
| Other-process isolation | Not demonstrated. Probe has no seccomp/no-new-privileges baseline; Yama alone does not establish this boundary. | PID namespace with fresh procfs, no host proc handles, reviewed ptrace/process-vm/pidfd/namespace restrictions, no escalation, and broker/child privilege separation. A different numeric UID inside a user namespace is not necessarily a different host UID. |
| CPU/memory/PID containment | Plausible via writable user-service delegation; not installed or tested. | A broker-owned child cgroup/unit with explicit limits. Child must not receive writable cgroup files or user-manager D-Bus/socket access that permits moving itself or editing limits. |
| Broker-mediated jobs | Broker ownership alone is not a security boundary. No implementation inspected here proves enforcement on every dispatch. | Trusted broker outside child reach; structured requests rather than arbitrary shell/host paths; enforced slot/resource policy; narrow artifact channel; no credential, network, process-control, or filesystem confused-deputy operations. Fail closed before child execution when required controls cannot be installed. |

## Concrete remaining controls and tests — NOT EXECUTED

1. **Bind the actual launcher identity and threat model.** Main should identify the intended broker/child launcher, source hashes, host aliases, candidate binding, host UID/GID/groups, capability sets, inherited-FD policy, and intended protection from parent/sibling processes. This receipt must not be substituted for a live-child confinement receipt. Keep ovx3physical7 excluded from all later probe targets.
2. **Resolve the AppArmor/userns prerequisite.** First obtain a read-only authoritative profile/policy explanation for the exact installed bwrap executable. In a separately authorized CPU-only test, create the required user/mount/PID/network namespaces and exercise their actual setup operations under the intended unprivileged identity. Record errno/profile failures and namespace identities; positive sysctls or `--version` are not acceptance evidence. Do not silently fall back to unsandboxed execution.
3. **Specify the filesystem/environment/FD boundary before execution.** Build an explicit allowed mount/path list and synthetic secret/held canaries outside it. Verify allowed reads and denied reads/writes, including symlinks, traversal, `/proc/*/root`, `/proc/*/fd`, inherited working-directory handles, and environment variables. Use dummy values only, never production credentials or sealed data. A clean environment must also exclude authentication-agent sockets and user-manager/control sockets.
4. **Verify network denial without real destinations or credentials.** An approved disposable CPU-only harness should test socket creation/connection policy using synthetic endpoints, IPv4/IPv6, loopback, inherited FDs, filesystem/abstract Unix sockets, and broker relay requests. Define allowed IPC explicitly. Offline model flags alone must fail this acceptance criterion.
5. **Obtain authoritative device-policy evidence.** Have the authorized host-side owner identify effective ancestor/child cgroup device BPF and how the broker can bind a non-escapable assigned-device allowlist. Record the allowed major/minor set and NVIDIA shared-node rationale. Begin with synthetic device-policy tests in an approved disposable harness. Any later real-device open/allocation/ioctl test requires separate scoped authorization and must never target the reserved device. The current sidecar's no-device-open rule remains in force.
6. **Exercise process protection using disposable peers only.** Under separate authorization, prove that a CPU-only child cannot inspect sensitive peer/broker proc entries, ptrace/process-vm access, obtain host namespace handles, or use process-control APIs outside its allowed descendants. Signal tests, if desired, need separate approval and dummy peer processes; none may target main, a resident, or a reserved experiment. Verify dropped capabilities, no-new-privileges, procfs contents, and exact host-ID mapping.
7. **Prove delegated resource limits and prevent escape.** Separately create a bounded disposable user unit/cgroup, check real membership and `cpu.max`, `memory.max`, `pids.max`, and test a low-impact PID/memory boundary. Ensure the untrusted child cannot reach the user bus or writable cgroup control paths to reconfigure/migrate. Do not run saturation tests alongside residents or infer enforcement from property acceptance alone.
8. **Test broker admission and every alternate execution path.** Reject arbitrary shell, unapproved paths/devices, credential requests, network relays, and requests crossing the candidate assignment. Cover the resident, experiment child, fresh readout, subprocess descendants, retries, and error cleanup. A correctly isolated primary command does not secure a later ordinary `Popen` path. Preserve evidence without changing shared ledgers from this sidecar.
9. **Bind evidence to exact deployed bytes and profile.** Record positive allow tests and negative deny tests, kernel/runtime/profile versions, mount/FD/environment policy, actual namespace and cgroup membership, and authorized device mapping. Claim only the boundaries exercised. Namespace creation failure, unknown device policy, broker bypass, or ambient held/credential visibility means the relevant isolation gate remains unproven.

**Handoff:** both aliases have the same relevant toolchain and resource-delegation opportunity. Their principal unresolved issues are AppArmor-mediated namespace usability, unprivileged device-policy authority/evidence, and the absence of demonstrated filesystem/network/process confinement in the inspected launch sites. No isolation claim or modification to main's ongoing resident work follows from this report.

## Main follow-up: actual CPU-only namespace attempt

At September16 06:35:53–54 UTC, Main tested the unprivileged bwrap launch on
both wrappers: unshare-all, private proc/dev/tmp, read-only runtime libraries,
empty environment, and only `id -u` as the intended payload. No GPU devices,
model code, credentials, held files or network destination were supplied.
Both returned exit1 before the payload, with:

```
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

Thus this tested unprivileged path cannot currently establish its network
namespace. No host policy was disabled or changed. This is not a claim that
all possible sandbox designs are unavailable; a trusted executor design and
the device/filesystem/process/network negative tests remain necessary. Child
experiment execution stays disabled rather than falling back to host execution.

## Trusted bootstrap feasibility — September 16, 07:26 UTC

Main's CPU-only probe on `ovx3` and `a40r` successfully ran the same
unshare-all/private-proc/private-dev/private-tmp/empty-environment bwrap
configuration through `sudo -n timeout 10`, with only `/usr/bin/id -u` as
payload. Both printed `0` and exited successfully. No GPU devices, model code,
held data or credentials were mounted; no host security settings were changed.

This establishes that a trusted privileged bootstrap can create those
namespaces, not that an untrusted child sandbox is ready. The payload identity
was namespace-root. Unprivileged payload identity, filesystem/process/network
negative tests, hard resource quotas and enforced assigned-device access remain
unproven. Experiment tools stay disabled; there is no host-shell fallback.
