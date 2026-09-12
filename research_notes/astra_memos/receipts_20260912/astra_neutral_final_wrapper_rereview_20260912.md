# Final neutral wrapper read-only re-review

2026-09-12, 08:21–08:23 UTC. Helper/source tests remain frozen. No repository edits, Git/network/GPU actions, or W0/B0 actions. W0 ASSAY_INVALID/launcher seal diagnosis is outside this review.

## Disposition

The agreed source/probe-custody integration is correct in the inspected wrapper. The prior concrete timeout/constructor and empty-query defects are repaired along the normal controller path. No new operational cleanup blocker was demonstrated in this quick CPU review. One P2 lifecycle-audit custody gap remains, described below; it does not invalidate the live cleanup checks themselves.

## P2 — Newly added lifecycle receipts are outside final custody

Locations: `organism_v6/run_reasoning_neutral.py:116`, `:124`, `:239`–`:252`.

`run_worker` writes `<condition>.process.json` and `<condition>.cleanup.json`, checks the live cleanup booleans, and returns the actual worker PID. The controller correctly compares that PID to WORKER_DONE. However, neither these process/cleanup files nor their original digests are retained/revalidated in PAIR_DONE. The custody helper intentionally covers WORKER_DONE and the probe directory, not controller lifecycle metadata. Consequently the earlier arm's cleanup evidence can change or its process evidence disappear during the later arm and the pair still finalizes.

Concrete CPU reproduction used the updated real-`run_probe` fixture with mocked worker/lifecycle transport. The synthetic second worker changed `off.cleanup.json` to `{"reservation_release_verified": false, "changed": true}` and deleted `off.process.json`. `run_pair` still wrote PAIR_DONE. This tests historical evidence preservation, not real GPU execution or whether the live cleanup actually failed.

Smallest wrapper-only fix: retain original process/cleanup receipt contents or digests at successful worker completion, validate their PID/PGID/device and successful-release fields, and revalidate both arms' original lifecycle artifacts immediately before PAIR_DONE. Include those digests in the final seal. Capture the original PAIR_STARTED digest too if the final seal is intended to protect that human-readable prospective record. Keep this separate from the frozen helper API; main owns the wrapper. Add a mutation/deletion regression based on the real-helper parent fixture.

Operational distinction: successful `run_worker` already requires its live `group_empty and gpu_empty` result; changing a JSON file later does not bypass that in-memory test. The issue is that a successful pair can retain contradictory/incomplete historical release evidence, not that this reproduction ran an uncleared GPU.

## Integration checks that pass inspection

- Prospective `source_snapshot` is captured before workers and persisted in PAIR_STARTED.
- Workers check the recorded spec/device and verify that historical source snapshot before construction and after model work/cleanup.
- `verify_condition` runs on each completed worker, then the controller compares the receipt PID with the real `Popen` PID and checks device/spawn fields.
- Original receipt dictionaries are retained, passed to `validate_pair`, and included in PAIR_DONE with the returned condition-keyed receipt-file digests and the original source snapshot. No refreshed replacement receipt or new final-time snapshot bypass was found.
- Final spec/model/families validation remains in place. Actual probe manifests/configuration/ledger artifacts now back the parent positive fixture, including pinned bootstrap text.
- Worker launch uses a dedicated session, trusted cwd/PYTHONPATH, explicit CUDA selector and spawn/offline settings. Cleanup executes in `finally` on wait success/failure/timeout/interrupt and signals only the owned group; the controller records failures via `except BaseException`.
- Constructor failure now reaches `close_backend(None)` and controller group cleanup. Shared `wait_gpu_free` no longer treats failed/empty query output as zero.
- The wrapper's all-process XML query rejects failed/missing/malformed responses and graphics/process entries; successful worker return requires both owned-group absence and GPU-process-table absence.

Limits: real vLLM process topology, CUDA device enumeration, and actual GPU release were not exercised. Source binding is local on-disk custody, not an attestation of loaded code/weights or source origin. The helper's documented same-UID filesystem/atomicity limits remain unchanged.

## Commands/results

Read-only `nl`, `sed`, `rg`, `sha256sum`, `date -u` inspection.

```text
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' PYTHONPATH=tests:. python3 -B -m unittest test_run_reasoning_neutral -v
21 tests passed in 2.032s
log: /tmp/astra_neutral_final_wrapper_rereview_tests.log
```

This includes the real CPU descendant timeout/failure/interrupt tests with GPU queries mocked. Did not rerun all 138 tests.

One additional CPU-only `python3 -B -` heredoc reproduction, using the same environment and existing fixtures, produced:

```text
Synthetic CPU actual run_probe outputs; mocked worker/lifecycle transport, NOT GPU evidence.
PAIR_DONE with earlier cleanup changed and process evidence deleted: True
Stored cleanup now: {"reservation_release_verified": false, "changed": true}
```

Log: `/tmp/astra_neutral_final_wrapper_rereview_repro.log`.

## Stable reviewed snapshots

```text
71971046f17468794a13c4367c0e8164d964747989c06849ce129086e6689069  organism_v6/run_reasoning_neutral.py
49ae8d5f9a215fb42abe51dee60f0084218973fcc81f43d161ecfef7abaeda6b  organism_v6/neutral_pair_custody.py
84bc39aa1922d748ac640573d28e751bbdfe3a47e7f65b2bafc9c72d3473af12  tests/test_neutral_pair_custody.py
```

Wrapper hash matched at review start/end. Helper/test hashes still match the frozen handoff. Repository files changed by re-review: none. Main retains all patch ownership.
