# Q0 custody test-only v2 and explicit-C bindings

**TEST-ONLY V2 EDITSTOP. Main acceptance is NOT claimed and remains pending.**
The runtime verifier is unchanged. Original tests, Main's failed test log,
original FAIL_CUSTODY receipts, earlier observations, and archive/seal inputs
are preserved. This is a non-material archival test-fixture repair, not a
research-system, native-runtime, scoring, or scientific-claim change.

## Main's failing test: reproduced and localized

Main's preserved log records 44 tests, one failure, 0.209 seconds:
`test_input_change_detection` expected FAIL_CUSTODY but observed PASS_CUSTODY.
The old test calls `Path.touch()` immediately after creating/scanning a tiny
fixture, without establishing that its content or recorded metadata changed.

In 200 isolated reproductions:

- **80 touches changed neither bytes nor the recorded stat fingerprint**;
  the unchanged-input guard correctly reported unchanged inputs and PASS_CUSTODY.
- **120 touches changed the fingerprint; all 120 were rejected.**
- No changed-fingerprint case passed; all touch-trial payload bytes remained
  identical. This reproduces the test's unconditional false expectation, not
  evidence of a changed real archive being accepted.
- Deterministic controls for an explicit mtime advance, appending payload bytes
  after the scan, and replacing the inode with identical bytes all rejected.
  A no-op control passed.

Diagnosis receipt:
`/tmp/astra_q0_tar_custody_race_diagnosis_20260913_attempt1.json`.

## Versioned test-only repair

New file: `/tmp/test_astra_q0_tar_custody_20260913_v2.py`.
It still imports the original, unchanged verifier. It replaces only the flaky
touch expectation with an explicit two-second mtime advance and asserts the
mtime really changed before requiring rejection. Five additional controls
cover post-scan archive append, same-bytes inode replacement, no-op behavior,
post-scan standalone-seal append, and same-size payload tampering before
verification with mtime restored.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_q0_tar_custody_20260913_v2.py -v
```

- Full v2 suite: **49/49 PASS**, zero failures/errors/skips, **0.204115s** in
  the structured CPU receipt (initial direct CLI run also passed in 0.224s).
- Repaired mutation regression: **200/200 fresh-fixture repetitions PASS**,
  zero failures/errors/skips, **0.203682s**.
- Verifier and v2 tests compile in memory without bytecode.
- Main has not independently accepted v2 through this sidecar's work.

CPU receipt: `/tmp/astra_q0_tar_custody_cpu_v2_20260913.json`.

No runtime detector patch is justified by a touch that changed neither bytes
nor the fingerprint. Existing stat/digest guards are still **not an atomic
snapshot guarantee** against arbitrary concurrent/subsequent writes. V2 does
not claim stronger locking or eliminate that limitation.

## R0/R2 sorting discrepancy: new observation, not rewritten failure

The original remote pipeline inherited `LANG=en_US.UTF-8` without an LC_ALL or
LC_COLLATE override. The frozen verifier documents bytewise pathname sorting.
The full-root checksum streams differ because the path order differs.

New read-only node2 observations explicitly set **LC_ALL=C** for the complete
pipeline and a second per-file SHA256 pass, exclusively through the authorized
SSH wrapper. No payload, archive, or remote file was written or transferred.
Both passes agree. Each root has **18,153 regular files**; direct local
dictionary comparison of every returned remote path/hash against the
archive-verified map yields **zero missing, extra, or changed entries**.
Stat inventories remain equal before/between/after both passes and to the
previous en_US observation. Terminal marker bytes are also unchanged.

New observation:
`/tmp/astra_q0_R0_R2_external_custody_C_20260913_attempt1.json`.

| Root | New explicit-C full-root stream SHA256 |
|---|---|
| R0 | `52c21a6e1ba5fa786a652998eacb91b348ab1da685a335e7b90494ca1383097d` |
| R2 | `350befebaa2a31768b05254c98443435c58d5d8610c6f1515e89218afd2a14dc` |

Using these **new expected digests**, the unchanged verifier streamed each
original local archive again. Both new receipts report PASS_CUSTODY, with
unchanged inputs: R0 **7.367614s**, R2 **7.470682s**. Original receipts remain
FAIL_CUSTODY against their original en_US expected streams; they are not edited
or relabeled.

- `/tmp/astra_q0_R0_tar_verification_C_20260913_attempt1.json`
- `/tmp/astra_q0_R2_tar_verification_C_20260913_attempt1.json`

R1 did not match because the two sorting methods happened to coincide. Its
17,567-file C stream equals Fable's supplied
`006c21d38b763953e5a59ef5641d3fe7683e3e32f71a84bb879c7de667a9db87`;
the same verified map sorted under en_US.UTF-8 gives
`c47b36a95d1da52291756974d2e700d16bdeead8d33af04a7b8b102d619f00b4`.
There are 2,324 differing order positions. Fable's actual runtime locale is
not available in its note; only C-order equivalence is established.

## Main-supplied controller output bindings

After new C custody passed, the sidecar verified both supplied controller
output envelopes' `EXACT_NATIVE_RAW_REPLAY` tags and canonical `report_sha256`.
Removing only `durable_completion`, and restoring the archived provisional
wrapper using the recorded scientific_claim, exactly reproduces the archived
`reduction.json` bytes. The canonical durable_completion exactly equals
the custody-bound `FINALIZED.json` bytes.

| Root | Verified controller report_sha256 |
|---|---|
| R0 | `7e3cd8644ba7643992a2331921ed2b1060593ade2860ff4536acb044e8a7e96b` |
| R2 | `e59900a2ea66f0b04f260a07b2b7e9540b258467893ceaf8e7bf8d6665b87694` |

Both supplied labels remain `Q0_V2_FULL_DOSE_ENDPOINT_FAIL` with
`BOTH_MAP_FIRST_STEP_MISS`. These are bindings to Main-supplied outputs, **not
native replay executed by this sidecar**, not Main approval, and not a science
upgrade or reclassification.

Combined provenance, prior-failure preservation, archive/C-observation bindings,
controller raw-file hashes, report hashes, exact-byte checks and unchanged raw
endpoints are in:
`/tmp/astra_q0_R0_R2_archive_custody_C_binding_20260913_attempt1.json`.

## Final SHA256 pins

```text
eaffff4a235986ac4ff1f43768ec7bee58a640dd3ec77c9db76057bdd6e4969b  /tmp/astra_q0_tar_custody_20260913.py
8a805d14f09a580c3a2434d94870f94d4370e717f0b7d9b6f38dd187ee248a6a  /tmp/test_astra_q0_tar_custody_20260913.py
4b9f4586f29e2aecfe7b2034742f58755a9efcbc6d7c9835b3f4f38ad22bcfd4  /tmp/test_astra_q0_tar_custody_20260913_v2.py
ead8de4cd1fbe1022d467baca611dc86f7197b5fe20378de09dea691c7090d0e  /tmp/astra_q0_tar_custody_main_cpu_20260913.log
f23a4881b04161c441ce4ab28bf3ccd174cb1d29959aad33a0d4c5f791319eb4  /tmp/astra_q0_tar_custody_race_diagnosis_20260913_attempt1.json
35e7a22e991ba2f26ce5fd37dd8506122eff00479dd7660959a7002fea39e3d9  /tmp/astra_q0_tar_custody_cpu_v2_20260913.json
0b97c718e2bd877b956b4e04371f8baf57f165c3455ea1a2b3703ec6f36f7461  /tmp/astra_q0_R0_R2_external_custody_C_20260913_attempt1.json
331dd96071f7b1ca2a8852c15c81a45a65262a856073f278957ed4c2a56ccaa2  /tmp/astra_q0_R0_tar_verification_C_20260913_attempt1.json
2c8346555d9ccfdfdc4cca9fae8f15c4bd9ebcb5dc88df29ec3a53e531eec052  /tmp/astra_q0_R2_tar_verification_C_20260913_attempt1.json
07d8b2b16da062bf00f2dc1f7a3e82db34b3a7695099ffa0ef593a872e0ef0de  /tmp/astra_q0_R0_R2_archive_custody_C_binding_20260913_attempt1.json
```

This handoff's hash is returned separately. Main may rerun the v2 test command
and review the binding receipt; **no Main acceptance has been inferred**.
