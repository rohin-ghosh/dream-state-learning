# EDITSTOP — A100 OFF readiness attempt2

SEQ150 reserved for Main; completed infrastructure result only. No sequence register, Git, helper, launcher, or original-root edits performed by this inspection.

## Outcome and repair boundary

- Actual result: `OFF_NATIVE_READINESS_PASS`; started 2026-09-13 08:41:21.341497 UTC, finished 08:44:17.237225 UTC (175.895728 seconds).
- One OFF model load and one generation call; four-token cap, two returned tokens, finish reason `stop`. No semantic scoring or scientific pass.
- Short root `/tmp/astra_a100_off_v2` is an output-placement amendment to attempt1's socket-path failure, not a model/package/helper repair. Archived identity matches attempt1 exactly; request and actual prompt token IDs match.
- All 14 official model payloads passed before and after checks against the public binding. Binding SHA256: `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`.
- Unchanged helper SHA256: `1d971c12e27ca00c4f1dcfb6158267b48b7944a142e62e64b9b3eab83b5a171d`.
- Attempt2 launcher SHA256: `f393f4894f4e46392a037c3d4fbe628b1af487e8fde173bcebad6b32834a231f`.

## Exit and release

Bound UID1395 timeout PID/PGID40880, start ticks1003448; Main's external cap590 seconds. At 2026-09-13 08:45:03.761105 UTC, bound PID absent, same-user owned process group empty, and targeted all-process NVIDIA XML empty on GPU0 UUID `GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6`. GPU query SHA256: `e5661f8724ff3bd2d5625ae9726af45f373edc37d0ad491700a406983c8ff87e`.

Release is point-in-time, not a reservation or authorization for another workload. No OS wait/exit-code receipt exists. The result reports no available engine-shutdown method; independent process/GPU absence establishes observed release, not an inferred exit code.

## Archive and local verification

Fresh remote capsule `/tmp/astra_a100_native_readiness_archive_20260913_attempt2` transferred to this directory without overwrite. `evidence.tar` includes the new root, launcher claim directory, launcher script, unchanged helper, and custody metadata. Source inventories matched before/after packaging.

- Archive SHA256: `c2ba707c2bd0cda768665b38d240628d739417e7788f32176d31e857a3b64558`; 6,983,680 bytes.
- Local verification: exact 40 unique tar members; 24 source regular files plus two custody files; 14 directories. Every regular-file hash/size/mode and every directory type/mode matched. No extraction or native execution performed.
- Three leftover UNIX socket nodes are preserved as exact metadata only in `socket_metadata.json` and `custody/socket_metadata.json`; no socket objects are claimed archived, and originals remain untouched.
- `result.json` SHA256: `fba6a13c01ec398c56ce7a624588309e1576d8c7bc129141597ce9fd5e44241d`.
- `receipt.json` SHA256: `f54ecd2abc81d3781cf7a56c5f9e827df4c977fce5e5b5df886ca705c1eb7d8a`.
- `release.json` SHA256: `054aafea60e22059eff14c23c548c10d5b75087d9026b18941350621c78b0335`.
- `socket_metadata.json` SHA256: `ced54c9ab395210b3d10df242b8b822505ece94511517042231e0e62e3522ebb`.
- Native log preserved inside tar: 10,274 bytes, mode0600, SHA256 `fffa6c86017c5d5dc90364084c360670309e41b67f87e1e6b17579535820b88d`. Raw archive/logs are private evidence, not for publication or Git; no internal hostnames or credentials reproduced here.

`verification.json` records CPU-only archive assertions and release identity; this is not another helper test run. Previously accepted helper tests remain 21 CPU tests, not rerun here.

## Limits

PASS establishes this single OFF Qwen7B load and short generation with explicit local tool paths and short temporary-directory placement. LoRA loading/routing, HF training, long contexts, full Level1 panels, hardware parity, scientific efficacy, parenting/clean lineage, and general allocation readiness remain untested by this check. Main owns subsequent decisions and sequence registration; no launch, kill, retry, or original-root changes occurred.
