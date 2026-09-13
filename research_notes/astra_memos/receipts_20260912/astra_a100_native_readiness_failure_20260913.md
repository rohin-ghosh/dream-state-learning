# SEQ148 reserved — A100 OFF readiness attempt1 inspection

**FAIL: infrastructure initialization; not a scientific result. EDITSTOP.**
Main reserves SEQ148; this sidecar does not update the sequence log or Git.

## Actual outcome

- Started September13,2026 at **08:32:29.917720 UTC**; failure finalized
  **08:33:33.926516 UTC**, elapsed **64.008796 seconds**, below the590s cap.
- `result.json` and launcher stdout agree: `OFF_NATIVE_READINESS_FAILED`,
  phase `OFF_engine_load`, error class `ZMQError`. The bound timeout PID/PGID38533,
  UID1395, startticks950305 was absent by08:33:41 UTC; its owned group was empty.
- The archived pre-load receipt consistently matches **all14 official file
  hashes/sizes**, including stability flags and the pinned public binding.
  Tool lookups passed. No `request.json`, `response.json`, or `model_after.json`
  exists: **zero completed readouts**, not a zero score. A completed model load
  was not established; no training or adapter loading was requested.

## Exact failure diagnosis

The preserved log shows vLLM resolving Qwen architecture/configuration, then
failing while constructing its engine-core client IPC socket:
`LLM.__init__ → EngineCoreClient → make_zmq_socket → socket.bind`.
The exception reports an IPC path longer than the **107-character limit**.

The actual absolute ASCII filesystem address under this attempt's
`tmp/<36-character UUID>` is **122 bytes**, excluding the `ipc://` transport
prefix. The helper's process-local TMPDIR is derived from the fresh output root;
the long descriptive root makes that derived socket path too long. Tilde-redacted
diagnostic text is shorter than the actual address and should not be counted.
This is a **scratch-path configuration failure**, not another missing-ninja
failure, model-payload mismatch, evidence of hardware incapability, or efficacy
failure. The earlier SEQ147 sampling/JIT PASS is not invalidated.

**Smallest future remedy, not applied:** use a fresh, short real output root
(for example a unique `/tmp/anr2_<id>`), so the inherited `<root>/tmp` plus slash
and UUID remains within the IPC limit. A symlink alias to the long root is not
sufficient because the readiness helper resolves the output path. Alternatively
Main may separately authorize a versioned short-scratch repair. No script was
edited and no rerun, kill, installation or global configuration change occurred.

## Release

At **08:34:22.042988 UTC**, the targeted GPU0 query matched
`GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6` and its all-process XML was empty.
PID38533 was absent and same-user PGID38533 had no members; group absence was
reconfirmed before archival. Exact receipt: `release.json`.
This is a point-in-time release observation, not a reservation for a retry.
No foreign-process inventory was taken.

## Archive and custody

Fresh on-node capsule:
`/tmp/astra_a100_native_readiness_archive_20260913_attempt1/`.
This VM directory contains `evidence.tar`, `receipt.json`, `verification.json`,
`release.json`, and this sanitized inspection.

Archive: **184320 bytes, 22 members, 18 files**. It includes the entire fresh
run root, launcher claim directory, exact launcher/readiness/helper/runtime
scripts, and pinned public-binding/precheck receipts. The CPU test script was
not present on A100 and is not falsely represented as node-side evidence.
It remains at its existing VM `/tmp/test_astra_a100_native_readiness_20260913.py`
path with the prior frozen pin.

Source inventories matched before/after archiving. VM tar SHA256 and all member
names, types, sizes, modes and file payload hashes verified without extracting
or collecting/scoring. Original roots/scripts and previous archives are intact.
The4153-byte native.log survives at mode0600 in the archive; its recorded hash
matches. Archive mode0600; destination directory mode0700. Keep raw evidence
private and uncommitted; never report internal hostnames or raw logs publicly.

| Evidence | SHA256 |
|---|---|
| evidence.tar | `3c4434f0875343e4d5114ce1a3e8bd375c4d2ea0aa2e5a0e79e8810ae80bca89` |
| result.json within archive | `871e0c9edd103f895860644cf120fe760026844f70c3daea93a69ce235c42174` |
| native.log within archive | `d85500b7b300f26e93d88deda39b77d4671094b7da20726ff9e6be31de030c82` |
| receipt.json | `abd63b37ba0aad7249201ecb387cf5e96eeb3a79a8fbfea3d2db704990875e75` |

Launcher SHA256 verified against Main:
`558ca770c0d37f277a9f6a878ec09b896dc1dd894cdf16cf39c9447889922c72`.
Readiness SHA256:
`1d971c12e27ca00c4f1dcfb6158267b48b7944a142e62e64b9b3eab83b5a171d`.

## Remaining limits

No OS wait/exit-code receipt was persisted by the detached launcher; failure
is established by the matching result/stdout, retained traceback and observed
exit/release, not an invented exit status. Full vLLM loading/generation remains
unvalidated. Adapter routing, HF training, long contexts, other GPU/kernel
paths, hardware parity and all scientific outcomes remain untested here.

EDITSTOP.
