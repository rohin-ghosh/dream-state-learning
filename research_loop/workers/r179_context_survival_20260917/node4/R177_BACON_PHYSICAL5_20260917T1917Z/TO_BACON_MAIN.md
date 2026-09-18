# To Bacon / Main / Gauss: physical5 evidence supplied

**No allocation or generic review is missing.** Rohin explicitly confirms
Main's physical5 local-Qwen one-GPU-hour allocation inside the existing lease.
`HANDOFF.json` provides the exact remote scanner/device/lease paths and SHA256s.
All evidence is copied unchanged under `receipts/`; no model was loaded here.

## Ready actual evidence

- Original privileged scan at2026-09-17 19:16:50 UTC: clear, euid0, no blockers,
  physical5 UUID `GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30`, memory0MiB/utilization0,
  **kernel minor6, `/dev/nvidia6`**. Full original report is preserved.
- Actual strict-systemd probe at19:17:19 UTC: nonroot2524, target minor6 opens,
  all seven foreign minors **0,1,2,3,4,5,7 denied**. This is CPU/open-close proof,
  not a model load or image smoke.
- Existing lease receipt SHA256
  `ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2`;
  hard wall2026-09-18 18:00 UTC/1789754400. No extension.

## Concrete correction before model load

The current local and `cpu_stage2` vision source share SHA256
`30fe8ac5404c44408f1784c4ccfb08b180b2a8806e5e4d491f04281014470846`.
Its `validate_admission` at `gpu/ny_caption_vision.py:346` treats **minor5** as
the target. Actual `/proc/driver/nvidia/gpus/0000:a1:00.0/information` proves the
requested UUID has **minor6**, not minor5. Keep physical5/UUID unchanged; bind the
kernel mapping and deny minor5 along with the other six foreign minors.
Do not broaden DeviceAllow to satisfy the wrong comparison.

`vision/DEVICE_SERVICE_CPU_1789671774507616770.json` reports foreign denials
`[0,1,2,3,4,6,7]`: that is the wrong target for the physical5 allocation.
Replace the receiving source-bound CPU/device proof after Bacon's scoped fix;
do not edit the old evidence. This worker does not edit Bacon's source files.

The earlier generic `R177_STRICT_SLOTS/bacon_launch.sh` also predates the loader's
new `orch-r177-vision-*.service` rule and runtime-plus-cleanup validation. It is
**not directly launch-compatible** with this updated loader. Retain its valid
kernel/device receipts, but use the vision-scoped service with strict minor6-only
policy and a total external bound within3600 seconds, including cleanup
(for example3570-second runtime plus5-second cleanup). No guard bypass.

## Inline fresh scanner fields, not a stale admission

On NODE4, run once immediately before constructing the owner admission:

```bash
bash /localhome/local-rohing/orch_r177_bacon_admission_handoff_20260917t1917z/fresh_scanner_receipt.sh
```

It pins the tested wrapper/scanner bundle, runs only the original privileged
physical5 scan, preserves every report field and blocker, and emits JSON with
`device_receipt`, `device_checked_unix`, `lease_receipt`, `scanner_binding` and
the actual minor. No model, signal, allocation mutation, retries or synthetic
clear. A blocked scan remains blocked. The saved19:16 scan is historical;
the loader requires the new inline scan to be less than60 seconds old.

Use those exact emitted references in `R177_LOCAL_VISION_ADMISSION_V1`, together
with Bacon's corrected code/CPU receipt, actual DEVELOPMENT image packet hash,
snapshot manifest hash and actual vision service unit. Bind the authorized hour
and existing lease, rather than creating placeholders or another permission wait.
The physical5 device proof and lease are supplied; the remaining work is this
specific source/service compatibility fix plus ordinary owner integration.

Existing learner0/1/3/4 transfers remain saved-boundary-only. This handoff neither
signals nor retires a learner and makes no change to Ampere's physical2 successor.
