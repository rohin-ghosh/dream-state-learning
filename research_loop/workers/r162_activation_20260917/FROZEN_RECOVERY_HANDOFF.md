# Frozen candidate5 native failure — read-only recovery handoff

Observed September17,2026 under the original R162 observer deadline07:15:52UTC.
No remote writes, signals, restarts, held-file reads, or source changes.

Root: `/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/parented_frozen`.
Attempt: sibling `attempts/run-parented_frozen-attempt2`.

## Concrete failure

`NATIVE_FAILED.json`: **ValueError: frozen_adapter_must_be_unchanged** at
05:56:42.151412UTC. `NATIVE_EXIT.json`: exit_code1 at05:56:43.625066UTC.
`LIFECYCLE.json`: SERVICE_EXIT_VERIFIED, service_returncode1,
cgroup_empty_verified=true, terminal unit failed/exit-code. Recorded native
PID681274 is absent; frozen stream WRITER.lock has no owner in the observed
`/proc/locks` snapshot. R162 CPU PID1389517 is alive with both service locks and
waits at cursor14; it was not killed or restarted.

Sanitized traceback: `gpu/orch_r150_matched_native.py:517 run` ->
`gpu/orch_r125_continual_native.py:502 finish_sleep` ->
`organism_v6/orch_r150_matched_stream.py:139 commit_sleep` ->
`:122 _validate_frozen_receipt` -> `orch_r125_continual_stream.py:34 require`.
The latter guard requires both equal adapter-state hashes AND equal adapter
directory hashes. Recorded checkpoint metadata identifies the unequal conjunct:

- Initial and sleep1 adapter-state SHA256 both
  `95966e71c3ec81487d05e02d6b770c422febfc433fe367d856a6e4817f8dbe14`.
- Both adapter_model.safetensors file hashes are
  `2beaa09d4930b1eafa6a1a07a67f3d062b35336d5e5ac58778a00ad518cf9dfe`;
  README hashes also match. These are recorded metadata, not a fresh tensor audit.
- adapter_config.json differs: initial
  `defb66b9d5bfdeff0a65f5624c661420b59219091a525401e23fa491824fe997`, sleep1
  `f2272102e22e6b7b16484ce1569de9b961d38cd36ae41fd9bcfc5fe153f24a78`.
- Consequently adapter-directory hashes differ: initial
  `6332eb67771f71fe5eb8fa546791eb502ce3af1754a6ad6bae0f5d665959153f`, sleep1
  `8e07a2bb7733558e65aa341d97a5869f62b4b37ffd9df4d9fc26f0cff35bcf4c`.
- Both COMMITs report optimizer_steps0. This observation does not establish which
  config field changed or authorize relaxing the guard; Main's recovery worker owns that.

## Exact checkpoint/current state

Last completed journal own response: record11 COMMITTED. Record12 COMPACTION.
Last journal record: `stream/records/00000000000000000013.json`, SLEEP_REQUEST
cycle1, file SHA256
`0a8711cb081396df3ac12f1ccd6ab1fb5005f62fddab6b589f1561fac6408f08`;
record-envelope SHA256
`29102c71db4f59c251baab77d3523ab8856d03019c0ccab5600122b7fd23a416`.
Resume-state SHA256
`e8e04d4c7529b4aff6b12ee65ee56bc46aa37efec5e10cfb724281e02c5ac31c`.
Rows3, sleep_frontier0, sleep_receipts0, segments_per_sleep2,
pending=`sleep:1c66b1314805d4779a3ecc10ddd0db0dd46f61b55acebf3bf6428dc2413357e2`.
Model-state SHA256 remains
`4f7c384733ed4e145e67329af794c0237b2b93126c6e172baf26487229313070`.

Last stream-committed model checkpoint: `checkpoints/initial/COMMIT.json`, file
SHA256 `68580b9e6f4db25d0bc8b5a2107eec7507863d617065ff8b3f6d7c352a97417c`.
An additional disk checkpoint exists at `checkpoints/sleep_000001/COMMIT.json`,
file SHA256 `1aa0ab173c105e880c5b8da7ce697d57113c49d6c6536255b15cd4a3d443b977`.
It was written before commit_sleep rejected the receipt: **no SLEEP_COMPLETE**.
Do not equate this disk checkpoint with a completed journal boundary or blindly
rerun sleep1; the native implementation rejects an existing checkpoint directory.
No adapters/optimizer binaries were opened for this diagnostic.

## Local receipts

`FROZEN_EXIT_RECEIPT.json` contains exact-byte metadata copies and sanitized native
trace frames/class/guard string; other log lines and source expressions are omitted.
SHA256 `12a5207309d6c0e58acec6ff05fad569df4e159bb54107c315111661d17de72f`.
`FROZEN_BOUNDARY.json` preserves exact records11/12/13 (all TRAIN state); record,
adjacency and state hashes verified locally. SHA256
`368d3120463767f735ce59b194afefb91181ad56253a58c3dd52473c26aaa448`.
Full remote metadata paths/hashes and both COMMIT bodies are in the exit receipt.
No held readouts or their logs were opened. Recovery belongs to Main's separate
worker; R162 is waiting safely for a future actual TRAIN request.
