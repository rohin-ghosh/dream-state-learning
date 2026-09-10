# MJP-D0 target-host isolation observation

Observed read-only on 2026-09-02 before any MJP-D0 implementation:

- host: `a4u8g-0105`
- lease role: already-held 8xA40 worker; no new lease was acquired
- OS: Ubuntu 24.04.4 LTS
- kernel: `6.17.0-35-generic`, x86_64
- CPU: AMD EPYC 7742 64-Core Processor; `nproc=256`
- absent from `PATH`: Docker, Podman, nerdctl, ctr, runc, crun, enroot,
  Singularity, and Apptainer
- available: `/usr/bin/bwrap`, version `0.9.0`, SHA-256
  `52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712`
- passwordless noninteractive sudo is available on this owned lease
- unified cgroup v2 is present with `cpu io memory pids` controllers;
  transient `systemd-run` units with `MemoryMax` and `TasksMax` succeeded

The following containment properties were exercised successfully with no
science code or data present:

- a fresh Bubblewrap namespace used `--unshare-all --die-with-parent
  --new-session --cap-drop ALL`;
- its root was a fresh tmpfs containing only a read-only `/usr`, `/bin`,
  `/lib`, and `/lib64` symlinks, fresh `/proc` and `/dev`, and private tmpfs
  `/tmp` and `/work`;
- the payload ran as UID/GID 65534 with an empty allowlisted environment;
- wrapping the payload with `setpriv --no-new-privs` yielded `NoNewPrivs: 1`
  and zero `CapInh`, `CapPrm`, `CapEff`, `CapBnd`, and `CapAmb`;
- neither `/home` nor `/localhome` existed in the sandbox;
- an IPv4 connect attempt returned `ENETUNREACH`;
- the read-only root rejected writes and remounting it writable;
- a transient cgroup-v2 accounting canary completed successfully.

This evidence does **not** establish OCI conformance. Bubblewrap is a Linux
namespace sandbox, not an OCI runtime or image. It supports a replacement
backend proposal only. The production canary must additionally prove exact
input immutability, a single empty output mount, IPv6 and Unix-socket
isolation, closed inherited file descriptors, dependency-closure hashes,
pre/post roots, fresh run/skip namespaces, and externally observed
`memory.peak`/`pids.peak`.
