# Executable C2 sampling diagnostic — Main handoff

**READY for Main's guarded CPU-staging repair and receiving review; NOT a
receiving-proof or GPU-launch receipt.** Source edits are held on Main's
request. Workstream 2 has not staged, reserved claims, submitted services,
loaded models, dispatched, committed, or pushed.

## Exact release and tests

- Current seal: `EXECUTABLE_SOURCE_FREEZE_REPAIR_V1.json`, SHA-256
  `b85c15d598010712af0fe32505285b79b63c8daf4a85565e300f0b940080e0ab`.
- **52 CPU tests pass**: `EXECUTION_CPU_TESTS_REPAIR_V1.log`.
  Run: `python3 -B -m unittest discover -s research_loop/workers/replication_sprint_20260919/replication -p 'test_*.py' -v`.
- `--plan` renders byte-identical `EXECUTION_REGISTRY.json`, SHA-256
  `1b4d9cb073ffa904c24cc7956a521d0b64be98138c12a4054dec456b40d8f1e1`.
- Main's preregistration bytes are bound by SHA-256
  `afb4de49f040c589ec416f7901c02b945776593ecf8670d4505aa417a30c5c63`
  in registry, source seal, preparation and role configs.

The original player/judge function code, contract, decoder, extraction,
feedback and reference-panel epoch are reused. The wrapper separately binds
the new seed epoch; it does not mutate the historic module or relabel the
new seeds as an old completed job. It checks tokenizer, template, libraries,
decoder and weights before generation. The completion validator also joins
the exact three scene IDs. `report_sampling.py` reports every source/seed,
deduplicates scene/caption identities, separates rankless outcomes by reason,
and reports missing cells as incomplete, never as a completed zero.

## Blocking repair and provenance

Main's first **CPU-only** stage failed on an obsolete hard-coded backbone
directory. The pinned scalar config instead references the existing base
manifest, whose **root** is the Hugging Face snapshot:

`/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`

Its old `files[].path` fields name the obsolete export; the original scalar
loader reads `root`. The repair verifies the manifest hash/model/revision and
root containment in the cache already bound read-only. No alternate model,
private data, or guessed filesystem root is introduced.

`RECEIVING_REPAIR_READ_ONLY_V1.json` records actual receiver execution of the
repaired **read-only helpers**: valid bound backbone, 26 inventoried staging
paths, no execution markers, no writes/models/GPU calls/services. It is not
the later role-confinement proof.

Failed source freeze:
`e717180b6caf7777dad84126a5cd30c503a908dc32c9f3f6fdde0a3a42f31ad0`.
Observed failed-tree digest:
`7cc0ef2de2a5d30431f7c1969176b184bc212805a2ee5ecf2bd3b74a161f12e6`.

The explicit repair checks those exact bytes, absence of PREPARED/launch/run
evidence, identical scientific registry, and absence of this diagnostic's
GPU claims under the original shared lock. It **archives the entire partial
directory**, writes a preservation receipt, and prepares the same diagnostic
root anew. No file is deleted; no consumed guard is reset. A platform-denied,
prepared, claimed, or executed diagnostic is ineligible for this repair.

## Exact next CPU command

From Main's **new immutable receiving directory** containing the repaired six
runtime files, candidate, original receipt, repair seal and preregistration
(`C2_SAMPLING_PREREGISTRATION.md`), run:

```bash
set -eu
PKG="$PWD"
python3 -B "$PKG/prepare_executable.py" \
  --candidate "$PKG/C2_SAMPLING_CANDIDATE_V2.json" \
  --candidate-sha256 83a897cf8a5054364a65b55918d5fde321aa552e9f5ab85a1ed5ee176e2eb51f \
  --receipt "$PKG/ORIGINALS_RECEIPT.json" \
  --receipt-sha256 7459c1b35c1f445add6da32cfa812103c5c3a6be76b8d2989003fc6d85c4efca \
  --seal "$PKG/EXECUTABLE_SOURCE_FREEZE_REPAIR_V1.json" \
  --seal-sha256 b85c15d598010712af0fe32505285b79b63c8daf4a85565e300f0b940080e0ab \
  --preregistration "$PKG/C2_SAMPLING_PREREGISTRATION.md" \
  --stage \
  --resume-staging-freeze-sha256 e717180b6caf7777dad84126a5cd30c503a908dc32c9f3f6fdde0a3a42f31ad0 \
  --resume-staging-tree-sha256 7cc0ef2de2a5d30431f7c1969176b184bc212805a2ee5ecf2bd3b74a161f12e6
```

For inspection only, replace `--stage` and the two resume options with
`--inspect-unlaunched`. If the tree differs, inspect the difference; do not
substitute a newly observed hash merely to suppress the mismatch. Do not
overwrite Main's original source package or the preserved failed directory.

## Main-only receiving proof and dispatch

After successful staging, inspect `PREPARED.json`, `MOUNTS.json` and all three
configs. Record Main's Builder/review entry and fresh receiving proof. Then:

```bash
ROOT=/localhome/local-rohing/post_sampling_replication_20260919/4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95
PREPARED_SHA=$(sha256sum "$ROOT/PREPARED.json" | cut -d ' ' -f1)
FREEZE_SHA=b85c15d598010712af0fe32505285b79b63c8daf4a85565e300f0b940080e0ab
python3 -B "$ROOT/runtime/dispatch_sampling.py" --root "$ROOT" \
  --prepared-sha256 "$PREPARED_SHA" --source-freeze-sha256 "$FREEZE_SHA" --check
```

`--check` is read-only and does not reserve GPUs. `--prove` instead of `--check`
is a **real service submission** through the original `sudo -n systemd-run`
route: it acquires the existing shared claims and runs six CPU-only role
proofs. It loads no models, but it consumes this diagnostic's one-shot launch
intent and starts the **single 2,400-second absolute block window**.

Main reviews the actual `PROOFS_COMPLETE.json` and its joined role proofs.
Only then use the same dispatcher arguments with `--run` and
`--proof-sha256 "$(sha256sum "$ROOT/PROOFS_COMPLETE.json" | cut -d ' ' -f1)"`.
At least 1,500 seconds must remain; no deadline is reset between proof, review
and the three sequential arms. A platform denial or failed role is terminal,
with no automatic retry, fallback, alternate GPUs, or signals to kept lives.

RootDirectory mounts/device denial and Python/CUDA compatibility must pass
on the actual receiving host. They are **not established by CPU mocks**. Any
new namespace/library/platform failure is a concrete blocker to report,
not permission to weaken custody or silently resubmit.

Read public accounting, including partial/missing cells, with:
`python3 -B "$ROOT/runtime/report_sampling.py" --root "$ROOT"`.
It outputs no caption strings, private panels or parent payloads.

## Identities, resources and limits

Scientific diagnostic epoch:
`4df129caf0a0377ba91feec83923bc972e00b10dab13b5b198594db567689d95`.
Block ID:
`65d113ba39d7a2ea0953dd290e64d1c4b9daeb607f2bc97029fd1e162a9114cf`.

| Arm | Fresh job ID |
| --- | --- |
| base | `37a1552b0ed1e3e7090cffe3bd74e5fefc1b54ef4416897066fcabfb4955fbf1` |
| C2 sleep51 | `d4dcc289b524c0d9d29a55ced3bdb15511ed465738cd09198c5f3edd7535cad1` |
| C2 sleep117 | `c3094680583eb0e18f5d13873912608e7d4fb5ba73aebeb2c89c58710f6003e3` |

- Seeds23301/23302, three original development scenes, 1,024 tokens/cell,
  6,144/source, **18,432 total**. Sampling replication, not new training
  lineages, unselected ages, or held-out transfer. All cells must be reported.
- ovx4 `ipp2-ovx-p3-02`, physical2/player and7/judge only. Original V4
  protected-process checks and shared UUID claims remain in force. Active V4
  queue, capsules, source-age history and original science bundles are untouched.
- Hard end **2026-09-30 00:00 UTC**, stricter than lane end17:59:30 UTC that
  day and lease boundaryOctober1 00:00 UTC. No lease extension. Block cap2,400s
  plus original30s teardown reservation.
- Historical arm elapsed times325.0/383.0/473.3s total19.7min, excluding
  preparation and separate scorer startup; roughly25–35min is a planning
  estimate, not a measured new-run ETA. No large VM transfers are required.
- Original dependencies and completed age24 comparisons remain documented
  in `REPORT.md` and `ORIGINALS_RECEIPT.json`; learner24 was already complete
  and must not be rerun as a missing arm. Do not mix judge epochs.
