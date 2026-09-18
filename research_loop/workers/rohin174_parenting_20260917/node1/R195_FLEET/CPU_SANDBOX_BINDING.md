# Node1 actual CPU sandbox binding — 2026-09-17 19:13 PDT

**CPU sandbox verified. Final runtime/root-policy tests still pending. No
native handoff, learner call, GPU call or learner/control mutation.**

## Binding for Main

Use the two actual values in `CPU_GATE_READY.json`:

```json
{
  "cpu_gate_root": "/localhome/local-rohing/orch_r153_cpu_smoke_20260918t0212z/gate",
  "cpu_gate_sha256": "ca755cbd60be96fa310bff0c8149ed8777159e0e09dbd437c076190f7577356d"
}
```

The hash is **cpu.digest(cpu.verify_gate(actual_remote_gate_root))**, not a
hash of this note, an archive, a local copied receipt or another host's gate.
Reverification binds node1's current boot and the exact profile/capture source.
All final per-life roots stay unchanged R136 roots. Main's versioned same-life
`cpu_once` root policy must retain canonical path/journal identity checks and
leave the R153 default unchanged; that final runtime work is not asserted done.

## What ran and what passed

At 2026-09-18 **02:11:55.518–02:12:11.697 UTC** (September17
19:11:55.518–19:12:11.697 PDT), the unchanged existing module
`gpu.orch_r153_sandbox_smoke` ran on actual node1, `[REDACTED_HOST]`, UID1395:

- Existing R125 confinement probe: **basic, output, timeout, memory, files —
  all PASS**. Basic has23 checks, files2; actual memory OOM, output bound and
  timeout behavior are separately verified by the existing gate validator.
- Existing fixed BUILDER_TEST smoke: plain arithmetic printed42, punctuation
  case printednormalized, malformed syntax failed with nonzero exit as expected.
  These are trusted fixtures, not live child actions or an NFKC learning claim.
- Bounds: memory128MiB/swap0, pids8, CPU25%; strict device BPF, private network,
  no-new-privileges, filesystem restrictions, nonroot dynamic identities and
  read-only inputs. No GPU device opens are attempted by the standard probe.
- Existing runtime limits and teardown remained unchanged. All five probe
  cgroups are absent after stop; a second inspection found all eight created
  transient units nonrunning. The deliberate syntax-failure unit retains a
  failed status (expected evidence), not a live process; its cgroup was removed.

Fresh `cpu.verify_gate` plus current unit/cgroup recheck completed
**02:12:37.792 UTC / 19:12:37.792 PDT**. Five downloaded gate receipts match
their exact remote hashes, and their original remote-reference digest matches
the binding above. No automatic retry or background process was left running.

## Search, source and evidence custody

The authorized legacy search found no accepted R153 smoke-gate root, no
candidate basic/output/timeout/memory/confinement JSON within the bounded
maxdepth4 node1 search (excluding source, stream, checkpoints, readouts,
sealed/final areas), and no owned top-level R125/probe/gate directory in /tmp.
That is a bounded search, not a claim about every file on the host. Existing
live node1 sources contained the older probe SHA3fd355e3…, not the current
profile's files-mode observation fix; none of those sources were modified.

Eight existing source files were copied byte-for-byte to a new immutable
operator-only source directory. Local/receiving manifests match. No new
framework, probe logic, sandbox policy, runtime patch or test was authored.

- Frozen source root:
  `/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/cpu_source_20260918t0212z`.
- Profile SHA:
  `9117c4d72cdbb700e351f4625e763f96cf94341a3cf6d2a2cf3445687bfae48b`.
- Capture SHA:
  `b45825aad250ad0305b1f2d2c1b475690a4c6dda89045f97d5ee63da1294119d`.
- Actual full verification: `CPU_GATE_VERIFIED_20260918T0213Z.json`, SHA
  `1790a346d49177f390a437dd1b07cdf127dfa09097838c7ecb9964caa700e2bd`.
- Original-byte evidence archive: `CPU_GATE_EVIDENCE_20260918T0212Z.tar`, SHA
  `08879b5a6038e9d2ea0a8738d5f17e1761f1fc6965f48254ae2e53f276795509`;
  extracted into the same-named directory for Main's inspection.
- Full source manifests, source archive, builder stdout and stderr remain in
  this worker directory. No credential values were printed or copied.

Gate validity is source-and-boot-bound. Reverify it using the final receiving
runtime before deployment; a host reboot or changed profile/capture requires
new actual evidence, not reuse of this hash. Work hard stop remains
2026-09-26 17:05 UTC; physical lease end remains23:05 UTC. Main alone posts
COORDINATION. This CPU preparation is not the pending code-test READY.
