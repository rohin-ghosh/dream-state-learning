# Every-sleep serialized execution candidate — inactive

Non-material resource-scheduling repair under standing builder scope. This worker
implements an executable receiving-host foreground queue, not an enrollment
daemon and not a metadata-only dispatcher. **Nothing here has been activated,
copied to a GPU host, or used to launch a probe.** All execution-path tests mock
the launcher and host. Main reviews the frozen source, actual source bindings,
device/lease checks and original route before deployment. No extra human,
per-device or per-experiment ratification is introduced.

Only this new worker is modified. Original scientific sources, the previous
465ded… run, native lives, scorers, collectors and enrollment remain untouched.
The old run and four other known attempts are durable no-retry history, including
its one unknown provider error. There is no replay to clear backlog.

## Scope and invariants

- Only `FRESH_R231` and `R232_SIBLING_FROZEN` checkpoint families; their explicit
  journal IDs, source roots, initial/current LOADED anchors and prospective
  frontiers are in `policy.json`. Every old epoch/age remains in the queue.
- Standalone frozen base remains a flat-weight reference with no native sleep
  counter. No synthetic base ages or unvalidated family conversions.
- Unsupported v1 roots: C2, P7, GAME1_P3, C0, Astra7, MATH_A, MATH_B_FORK,
  MATH_C, GAME_N3_0/3/5/6/7, GAME_UNPARENTED_N2. Their ages receive explicit
  `PENDING_UNSUPPORTED_ROOT`, not deletion or implicit evaluation.
- Unchanged 103-file scientific closure; frozen Qwen base and captured adapter;
  same three development scenes, seeds23201/23202, 1024 actual generated tokens
  per cell, 6144 per source, same judge/rules/panels/controls. Parent tokens and
  model updates are zero. No source transcript/optimizer state enters evaluation.
- Exactly one job, two processes, UUID-bound player2 / judge7. All six other
  physical GPUs and their exact protected PID/start/argv handles are protected.
  No arbitrary device fallback, native signal or displacement.
- Current occupancy must be zero MiB/no compute processes on both assigned
  devices. Complete fresh inventory, original UUID claims and prior attempts
  must all permit admission. Every role independently proves its one physical
  device opens and all seven others are denied before model load.
- At most2400 seconds per job, original lease end1790791170. A durable queue
  deadline is passed to the one-shot; preflight latency cannot extend it.
  Claims retain the original deadline plus30-second teardown hold.

## Actual integration and durable behavior

`daemon.py --run` calls `LocalHost.verify_capsule`, records a SQLite FULL-sync
INTENT, then invokes the staged `runtime/dispatch_once.py --launch` **once**.
That one-shot uses the validated original GPU-host transient cgroup route
(`sudo -n systemd-run`, closed device policy, exact UUID, bounded runtime).
`probe_runtime.py` verifies bindings/confinement and delegates to the
byte-identical original `probe.main`. There is no alternative executor.

Singleton `flock`, SQLite serialization and the original shared
`post_reboot_probe_dispatch_20260919/dispatch_locks` protect the lane. Success,
failure, partial dispatch, transport ambiguity and known previous attempts are
durable source-key/job-ID tombstones; source IDs use the original algorithm.
No daemon restart resubmits INTENT. An ambiguous intent is reconciled read-only
until its deadline/hold, then becomes UNKNOWN_NO_RETRY, never retried.

Reconciliation precedes new admission, including while paused. Matching running
handles are observed, not relaunched. PID reuse is rejected; GPU-host boot changes
produce INTERRUPTED_NO_RETRY and a persistent rebind pause. A live job after its
deadline keeps the slot occupied; the observer does not kill it or native work.
Claims are never released early just because COMPLETE exists. Unknown legacy
attempts in the pinned original namespace block admission pending reconciliation.
The original multi-condition R232 battery is inventoried separately, not parsed
as a one-shot source. All its loaded conditions and judge must have completion
markers; matching enrolled cut hashes become no-retry history without inventing
a journal identity. This receiving-host case is covered by two regression tests.

The state retains every enrollment entry, de-duplicates exact keys, rejects
conflicting journal/index/epoch changes and shrinking snapshots, and schedules
the oldest *available eligible* prospective cut from the least-recently attempted
life. Missing capture/exposure/binding stays pending, even when a later captured
cut is available; this is not silently “latest only.” Snapshot files are read
only; refreshing them uses the existing observer/owner, not another enrollment
daemon. Capsule registration is append-only and unattempted files are reverified
on the receiving host, not trusted because metadata says ready.

**The frozen evaluator itself still has its original behavior**: this observer
does not rewrite feedback or stop its token loop. Its one active job holds the
lane while shortfalls await terminal classification. A cleanly terminated,
authenticated six-cell6144-token run with exclusively verified model-free
512-limit input-length guard failures becomes COMPLETED_WITH_SCORING_SHORTFALL:
unknown remains unscored, not zero/rejected, and that source never retries.
Later independent ages may run after original claims/handles clear. Generic or
unverifiable provider faults, incomplete/failed execution, platform, identity,
source and provenance ambiguity still persistently pause. See
`POLICY_ADJUDICATION.md`; the old blanket shortfall pause was assistant-added,
not inherited. Completion audits actual token IDs, original THINK/ACT limits,
request/result/event joins, device/LOAD evidence and unchanged weights.
There is no parent publication path; stdout contains only operational summaries.

## Safe VM check (no host calls or launches)

From the repository root:

```bash
python3 -B -m unittest discover -s research_loop/workers/post_reboot_probe_queue_20260919 -p 'test_*.py' -v
python3 -B research_loop/workers/post_reboot_probe_queue_20260919/daemon.py \
  --check \
  --enrollment research_loop/workers/rohin233_kept_age_probe_20260918/enrollment/private/STATE.json \
  --enrollment research_loop/workers/rohin233_kept_age_probe_20260918/extra_enrollment/private/STATE.json \
  --state research_loop/workers/post_reboot_probe_queue_20260919/offline_receipts/queue.sqlite \
  --report research_loop/workers/post_reboot_probe_queue_20260919/offline_receipts/DISPOSITIONS.json
```

The empty default `capsules.json` is intentional: no old execution root is
relabelled as an unattempted source. The offline receipt gives each retained age
its pending reason. CPU tests are synthetic; they are not current host occupancy,
source freshness, protected-identity or platform-permission receipts.

## CPU preparation and receiving-host activation (Main only; not performed)

**Current seal is `SOURCE_FREEZE_V3.json`; earlier seals/receipts are superseded.**
`NEXT_ENTRY.json` preserves the exact sibling sleep24 enrollment epoch. The
read-only receiving-host `NEXT_SOURCE_RECEIPT.json` verifies its four captured
files, original103-file source and fresh exposure:124 records,72 requests, one
inherited source state, no identifier/scene matches. It is not prepared, not
admitted, and not a claim that GPU2/7 or protected identities remain unchanged.
The health portion of that combined read timed out after the exposure receipt.

After staging/review, this exact command constructs and registers that one
capsule using the unchanged original preparer and the scoped binder; **it never
dispatches**. It fails closed if reviewed host/source/protected bindings changed.
Do not interpret an empty registry or a construction failure as ready for work.

```bash
REVIEWED_FREEZE_SHA256='<reviewed SOURCE_FREEZE_V3.json file SHA256>' \
  bash /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate/CONSTRUCT_NEXT_CAPSULE.sh
```

1. Review/stage this frozen candidate at
   `/localhome/local-rohing/post_reboot_probe_queue_20260919/candidate`.
   Stage/update two read-only enrollment snapshots under the sibling `inputs/`.
   Re-run CPU tests there and verify `SOURCE_FREEZE_V3.json` file hash. Review
   `policy.json` against actual `/proc`, journal epochs, UUID inventory and lease.
   These template identities are not a claim they remain live after retention.
   Main records the dated `[Builder]` tests/provenance line before any GPU run;
   this offline worker does not edit the global coordination document.
2. Use an existing coherent captured checkpoint. Run the unchanged
   `prepare_probe.py` from the validated103-file source closure, with
   `--source-root /localhome/local-rohing/orch_r233_recovery_s24_probe_20260918`,
   `--original /localhome/local-rohing/orch_r232_age_probe_20260918`,
   `--queued <captured checkpoint>`, `--life <reviewed source root>`, and a NEW
   `--root /localhome/local-rohing/post_reboot_probe_queue_20260919/jobs/<job_id>`.
   Supply the original enrolled row without changing its epoch. Preparation
   must independently pass original captured/inherited exposure eligibility.
   A missing checkpoint or failed audit stays pending; no automatic recapture
   or new scientific battery is invented here.
3. Bind that prepared root with `bind_bundle.py --root <root> --entry <entry.json>
   --policy <reviewed policy.json> --lease-authority <original LEASE_AUTHORITY.json>`.
   This CPU-only command never calls the dispatcher. It freezes the runtime,
   original scientific assets, policy, source age/epoch and config, and writes
   `runtime/CAPSULE.json`. Append its object to a separate `inputs/capsules.json`
   registry. Config/source hashes are verified again at admission and each role.
4. Create a separate `inputs/activation.json` from `activation.example.json`:
   after Main's operational review set reviewed/runtime_enabled true, bind the
   actual freeze file SHA and canonical reviewed policy SHA, and a finite expiry
   no later than the lease. The checked-in example is deliberately not usable.
   This is one deployment decision, not per-job/per-GPU authorization.

Exact future foreground argv on the receiving GPU host (NOT executed here):

```bash
/localhome/local-rohing/v2/venv/bin/python -B \
  /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate/daemon.py \
  --run \
  --policy /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/policy.json \
  --freeze /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate/SOURCE_FREEZE_V3.json \
  --activation /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/activation.json \
  --enrollment /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/enrollment.json \
  --enrollment /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/extra_enrollment.json \
  --capsules /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/capsules.json \
  --state /localhome/local-rohing/post_reboot_probe_queue_20260919/state/queue.sqlite
```

Run this on the original allowed GPU-host route, not on the VM as a workaround
for service-management enforcement. Any actual tool/platform denial is terminal;
do not try another command, route, service manager or escalation method. The
foreground loop emits only changes and polls every10 seconds; no growing full
observation log. No daemon wrapper, supervisor registry or boot unit was enabled.
The exact argv is also in `ACTIVATE_FOREGROUND.sh`, which is not executed here.

## Explicit source/protected-identity rebind

Legitimate retention adoption can change PIDs, journals, roots or LOADED epochs.
The candidate never follows such changes automatically. Stop the *candidate
foreground loop* after read-only reconciliation of its active job; leave native
processes untouched. Keep the frozen release and old policy; create a reviewed
new policy file and a separate receipt from `rebind.example.json`. Run
`rebind.py --state <same queue.sqlite> --policy <new policy.json> --review <review.json>
--freeze <SOURCE_FREEZE_V3.json>`, then review a new activation record.

Rebind requires exact old/new policy hashes, unchanged lease/lane/battery, and no
unreconciled job. It preserves all entries, audit events and attempt tombstones.
Old prepared capsules retain their bytes and become explicit
PENDING_POLICY_REBIND_NEW_BUNDLE_REQUIRED; old-journal ages stay pending rather
than relabelled into the successor. V1 does not rewrite a previously bound job
directory for the same source cut. New, unattempted successor cuts may be bound
normally after review. Do not erase state or alter config to evade no-retry.

**Boot installation: BLOCKED_UNINSTALLED. Credential bootstrap: UNVERIFIED.**
No `systemctl`/`loginctl` probes or installation attempts. No credentials are
written or printed. The local fixed evaluator needs no provider key, but neither
templates nor credentials inherited from a current shell prove secure automatic
boot provisioning or future reboot safety. Enrollment recovery is not automatic
GPU execution recovery; this remains an inactive implementation candidate.
# V4 notice

The runtime-only rebind is implemented; see `RUNTIME_REBIND.md`. The original
V3 and initial V4 descriptions below are historical. Main must use the final
V4_REBIND seal and the separate immutable capsules_v4 registry, not the V3 paths.

This is the separate bounded-cache repair release. Read `CACHE_REPAIR.md` first.
The inherited V3 documentation below is historical, not an activation assertion.
The existing frozen sleep24 capsule is not rebound; V4 remains offline.
