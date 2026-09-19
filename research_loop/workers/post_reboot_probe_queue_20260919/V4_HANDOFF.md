# V4 repair handoff — September 19, 2026, 04:01:29 UTC

**OFFLINE. NO ACTIVATION OR GPU LAUNCH.** V3 remains byte-identical locally and
on the receiving host. This repair is entirely within this worker. No native
or scorer signal, original journal mutation, collector/enrollment duplication,
service-management attempt, commit or push occurred.

## Release and changed paths

New local release directory: `version_v4/`.
Receiving copy: `/localhome/local-rohing/post_reboot_probe_queue_20260919/candidate_v4`.
Seal: `version_v4/SOURCE_FREEZE_V4.json`, SHA256
`40d71c6f25aef03a649520f09bcf92748de2501002b1dd48e9c9e777a29dbd56`.
All25 source files bound by the original V3 seal are unchanged. Both seals were
verified independently on the receiving host after final staging.

- `epoch_cache.py`: bounded canonical verification, per-process shared proof,
  fresh metadata of all cached records, rapid-write content fence, sticky faults.
- `probe_runtime.py`: shared epoch validation and bounded fresh-identity warmup.
- `host.py`: both-source incremental progress, fresh protected/lease checks even
  when pending, bounded420-second one-shot transport ceiling.
- `daemon.py`: pending proof cannot create an intent or launch; no blanket pause
  for incomplete validation; fast bounded warmup cycles; real failures still pause.
- `bind_bundle.py`, `dispatch_once.py`: bind the new cache module and bounded
  source preparation before execution. No existing runtime/config is rewritten.
- `source_preflight.py`: CPU-only cost/proof diagnostic; no dispatcher invocation.
- `test_epoch_cache.py`, `test_queue.py`: new integrity, budget, cache and
  no-admission-on-pending regressions; inherited reconciliation tests retained.
- `CACHE_REPAIR.md`, `README.md`, `seal.py`, `ACTIVATE_FOREGROUND.sh`: repair
  contract, version closure and an explicitly blocked activation script.

## Tests and measured cost

**88 CPU tests PASS locally and remotely** (58 inherited +30 added).
Final local1.678 seconds; receiving0.583 seconds. No GPU smoke test or actual
dispatcher call. Receipts: `offline_receipts/REGRESSION_TESTS_V4.log` and
`offline_receipts/V4_FINAL_CHECK.json`.

One CPU-only receiving-host source preflight ran03:56:26–03:59:25 UTC.
It authenticated7,685 required records /17,287,249,487 bytes across both source
epochs, with190 bounded calls:

- Cold: **178.562857 seconds**. Cold work was NOT skipped or replaced by a
  persisted, unauthenticated cursor. It still exceeds the old120-second wrapper.
- Immediate warm recheck: **0.098567 seconds**, zero record decodes, zero journal
  payload bytes read. Every retained cached file's metadata was checked again.
- Source heads: FRESH_R2317710 and R232_SIBLING_FROZEN4200. Exact hashes are in
  `offline_receipts/SOURCE_PREFLIGHT_V4_20260919_0356.json`.
- Configured host/boot/UID, protected PID/start/argv identities and original
  lease passed fresh checks on every bounded call, including the warm recheck.
  This is historical proof at that receipt time, NOT a current GPU-free claim.

The cache is process-local. Later calls within the same observer/capsule verifier
reuse proof; a new process must cold-validate again. Do not repeatedly spawn
short preflights expecting persisted progress. A bounded call limits256 records,
64 MiB or2 seconds, allowing one atomic record up to32 MiB and metadata overhead.
Pending is never admission. The two-second rapid-write fence uses raw hashes,
not repeated JSON decoding, until local timestamp granularity is safely past.

## Timeout and survivors

The original120-second timeout is recorded at **approximately03:47 UTC** from
Main's report; exact original tool log/exit status is unavailable. The first
remote action was a read-only process inspection, not another observer launch.
No matching observer/binder remained at03:50:08; activation was absent. No
survivor remained at the final04:01:29 process check either. Exit cause unknown.
Receipt: `offline_receipts/PREFLIGHT_TIMEOUT_20260919_0347.json`.

## Exact blockers before executable activation

1. The concrete sleep24 source capsule remains intact, but its runtime/config
   binds V3. V4 adds/changes scheduling runtime files and MUST reject the V3
   runtime manifest. An explicit reviewed, immutable runtime/config/registry
   rebind preserving the SAME source/job/no-retry identity is still needed;
   that rebind is not implemented/performed in this task. Do not rebuild capture,
   change job ID, overwrite old sealed files or erase an attempted-source marker.
2. Main's activation must bind the new seal after that rebind. No activation
   record exists. The V4 activation shell script intentionally exits2.
3. A fresh cold observer still needs about3 minutes for this existing17.3 GB
   suffix. Allow a bounded300-second CPU preflight or let the reviewed foreground
   observer warm its own cache in small cycles. No cold-under120s claim is made.
4. Fresh actual GPU2/7 UUID occupancy, original claims/attempt reconciliation,
   full bundle checks and current protected/source/lease checks are still needed
   immediately before any durable dispatch intent. This diagnostic did not
   inspect GPU occupancy or assert full capsule admission.

Exact CPU-only command (already run once; **not an activation command**):

```sh
/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate_v4/source_preflight.py --policy /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/policy.json --max-seconds 300
```

At final check, existing config SHA remains
`c43eccadff2b9b1a5f0de5af45a3333e7f480f8b921d0a6c2f6e50368d3cbc4f`;
both activation.json and that job's runtime/LAUNCH.json are absent. Completed
465ded… was not touched or rerun. Scientific evaluator and shortfall policy
remain unchanged. Boot installation is **BLOCKED_UNINSTALLED**; credential
bootstrap is **UNVERIFIED**. No future reboot-safe guarantee.
