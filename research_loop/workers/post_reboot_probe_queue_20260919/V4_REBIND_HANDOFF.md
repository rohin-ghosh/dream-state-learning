# Immutable rebind handoff — September19,2026, 04:13:06 UTC

**CPU REBIND VERIFIED; READY FOR MAIN REVIEW; NOT ACTIVATED OR LAUNCHED.**
This supersedes V4_HANDOFF.md's missing-runtime-rebind blocker and the historical
CACHE_REPAIR.md deployment section. Main owns the Builder log and actual launch.

## Concrete job and immutable pins

- Same sleep24 source: R232_SIBLING_FROZEN, optimizer0, captured LOADED74 epoch.
- SAME job/no-retry identity:
  `4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f`.
- Same source key:
  `30fa18c869b34fd496a2758a4a28e197:7dfa305c4c2d689bd72a6ff343448c36246a2398190291d46688852ca1b565cd`.
- Final candidate: `/localhome/local-rohing/post_reboot_probe_queue_20260919/candidate_v4`.
- Final seal: `SOURCE_FREEZE_V4_REBIND.json`, SHA256
  `d77089e8d7eb3ff06e709fb8f16c9555a2c620a614fe9c335a516c54475061e0`.
- Sibling runtime:
  `/localhome/local-rohing/post_reboot_probe_queue_20260919/jobs/4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f/runtime_v4`.
- New `JOB_CONFIG.json` SHA256:
  `604549b5e3a994465939b71fd753bebccb48f83a5c2111d6f6e7c25fc8252b38`.
- New `CAPSULE.json` SHA256:
  `8ca4923a8e8c9673a06e619f53320c2dab0fc0b0ee806a5722cb7dc7a7395527`.
- New registry: `/localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/capsules_v4.json`, SHA256
  `2e04590f6265e4759222283c1d9843c13d81eb3ded6878c6e7eaf086136f2b37`.
- Policy SHA unchanged:
  `605c43ba2c87ead62f49c3efcc80a0f80689a1bc9ff20466478839497dfebd1b`.

Only config fields `runtime_directory`, `runtime_files`, `runtime_rebind` differ.
All103 scientific files and original input hashes, capture/exposure/epoch,
adapter, source root, scenes/seeds, six-cell6144-token budget, judge/control,
parent-free/frozen evaluation, fixed player2/judge7 UUIDs and horizons are unchanged.
No capture reconstruction or source-epoch scan ran during rebind or verification.

## Exact Main command — activation, not another staging command

After reviewing the exact seal/config/registry and recording Main's dated Builder
tests/provenance line, execute this ONCE from the VM repo through the original
GPU-host route. This worker has NOT run it:

```sh
bash gpu/ovx4_ssh.sh '/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate_v4/activate_reviewed.py --reviewed-seal d77089e8d7eb3ff06e709fb8f16c9555a2c620a614fe9c335a516c54475061e0 --reviewed-registry 2e04590f6265e4759222283c1d9843c13d81eb3ded6878c6e7eaf086136f2b37'
```

The helper verifies the reviewed source/registry and concrete binding pins,
creates `inputs/activation_v4.json` once and execs ACTIVATE_FOREGROUND.sh. The
shell now contains a real foreground daemon argv, not the old blocked stub.
An identical existing review can be reused for recovery without rewriting it;
a conflicting review is rejected. The daemon retains the original state path
`state/queue.sqlite`, singleton lock, audit/no-retry history and original claims.
Any actual platform denial remains terminal; there is no alternate route.

**Do not rerun `rebind_runtime.py --stage` or rebuild the existing capture.**
Optional CPU-only verification (already independently passed; no epoch warmup):

```sh
bash gpu/ovx4_ssh.sh '/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate_v4/rebind_runtime.py --verify --root /localhome/local-rohing/post_reboot_probe_queue_20260919/jobs/4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f'
```

## Tests, warmup and bounds

- **107 CPU tests PASS locally and receiving-host**; final local1.771s, remote0.702s.
  Shell syntax also passes. Source seals and actual runtime-module equality were
  independently verified on the node. No actual dispatcher was invoked.
- Regressions reject source/battery/input/epoch/deadline changes, predecessor
  mutation, arbitrary/symlink runtime paths, prior source attempts of ANY status,
  old/new runtime START/LAUNCH ambiguity, expired same-job claims, existing state
  during staging and partial/duplicate rebinds. Other registry entries are preserved.
- The fresh daemon warms its OWN process-local source cache in bounded cycles;
  no standalone source observer should be launched first. It cannot create an
  intent while proof is pending. Fresh GPU occupancy, claims, protected handles,
  source epoch and lease admission remain mandatory before actual execution.
- Role validation runs independently, at most300 seconds each, within the
  existing absolute intent/job deadline. Submission requires more than360s
  remaining. Actual PID/start/argv/confinement START_INTENT is durable BEFORE
  cold validation, so reconciliation sees the pending CPU role. Both concurrent
  roles and the original transient units remain bounded by the same2400-second
  job deadline and1790791170 lease. No deadline reset or extension occurs.
- Full six-cell completion is not guaranteed by the minimum remaining window.
  An overrun, unknown outcome or failure stays no-retry/pause; no zero score is
  invented. The original shortfall classification/evaluator remain unchanged.

## Preservation and final observed state

V3 source seal, predecessor config/capsule/registry, all scientific inputs and
receipts are preserved. Previous V4 and staging release copies are preserved in
`candidate_v4/epoch_release_archive` and `candidate_v4/staging_release_archive`;
all three predecessor seals verified. Their hashes identify historical files,
not the current candidate's source. Local new code is in `version_v4_rebind/`.

At04:13:06 UTC: both activation records ABSENT; original queue state ABSENT;
all job runtime LAUNCH and role START markers ABSENT. Rebind verification also
passed current configured protected identity checks at that time. No GPU-free
claim is made: actual occupancy and full fresh admission belong to daemon startup.

Receipts: `offline_receipts/V4_REBIND_FINAL_CHECK.json` and
`offline_receipts/REGRESSION_TESTS_V4_REBIND.log`. No native/scorer signal, new GPU
work, old465ded… rerun, collector/enrollment duplication, parent publication,
service-management command, commit or push. Boot: BLOCKED_UNINSTALLED.
Secure automatic credential bootstrap: UNVERIFIED. No reboot-safe guarantee.
