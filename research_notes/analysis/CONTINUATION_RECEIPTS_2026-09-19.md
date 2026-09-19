# Experiment continuation — September 19, 2026

## Repository publication

The useful repository snapshot was pushed as
`9eaa23db2f47b11ed60f0b997210fb7399c47c28`. The live working checkout and
ordinary index were deliberately not reset. An old local HEAD or dirty working
tree is not evidence that this publication failed. The broad test suite is not
green; its failures remain recorded in `REPOSITORY_SNAPSHOT_2026-09-19.md`.

## Completed frozen-sibling probe

The original queue actually dispatched and completed frozen-sibling sleep24.
It did not merely enroll an age or record a proposed launch. Six cells used
exactly 6,144 generated tokens, with no parent tokens or parameter updates.

| Seed | Generated tokens | ACT attempts | Distinct scored | Distinct accepted | New pixels |
| --- | ---: | ---: | ---: | ---: | ---: |
| 23201 | 3,072 | 11 | 53 | 28 | 14 |
| 23202 | 3,072 | 11 | 38 | 17 | 14 |

Counts deduplicate `(contest_id, caption_sha256)` separately for each seed;
replayed old `new_pixel` statuses are not counted again. These are descriptive
judge outcomes, not certified humor or evidence of retained improvement. This
one completed probe does not establish whole-fleet every-sleep coverage.

Receipt:
`research_loop/workers/post_reboot_probe_queue_20260919/SLEEP24_COMPLETION_20260919.json`.
It binds the remote COMPLETE, LOADED, judge and source manifests, launch record,
and the existing reducer by SHA256. The source adapter SHA is
`04341ab86f5f98718bc53218166537ecc20fc7d5053f3ed47cc0fcdda918f5d0`.

## Extra node2 caption player: parent delivery

The native remained alive at PID1800978/start101994417, on its original
checkpoint-tail incarnation. No learner restart or signal was needed.

- The earlier 04:58:49 UTC parent was consumed in INBOX8943, rendered in
  REQUEST8958, and followed by ACT8959 at 05:05:15 UTC. The parent was visible,
  but the child repeated its previous line. This is delivery, not uptake.
- The restored xhigh parent published at **07:20:26 UTC**. Its chain is
  **INBOX10273 → REQUEST10288 → ACT10289**, ending at **07:21:28 UTC**.
  The parent was visible in the ACT request; the child again repeated
  “Continue previous thinking: Judgement of previous Captions.”
- The parent published its next source-bound turn at **07:21:58 UTC**.
  Its chain is **INBOX10375 → REQUEST10390 → ACT10391** at **07:32:46 UTC**;
  the parent was visible and the child still repeated. Cadence continues after
  an actual subsequent ACT, even if compaction removed
  the parent message. Visibility is recorded separately; neither visibility nor
  a subsequent ACT is automatically scored as uptake.

This is a non-material delivery/cadence repair. The original xhigh policy,
90-word parent limit, metadata-only Tool visibility, cumulative 640-call ceiling,
35 prior provider attempts, all-authentic-child-row policy, and original lease
remain unchanged. Failed or ambiguous provider/publication attempts are not
silently repeated. The three original parent locks remain in force.

Code, 12 focused regression tests, and exact REQUEST/ACT hashes:
`research_loop/workers/post_recovery_node2_caption_20260919/parent_restore/`.

## Extra node2 caption player: scoring route

An existing socket pathname did **not** mean that the route worked. Five recent
R184_ACT records, through ACT record10190, contained
`ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY / ConnectionRefusedError`. They were not
failed caption-quality judgments and must not be counted as rejected captions.

The existing adopted rank8/step15625 scorer499905 and its two bridges448322 and
502012 were still alive. A bounded CPU-only repair restored the original private
SSH → authenticated journal proxy → SSH route at **07:24:20 UTC**. It preserves
the exact original registry, journal, frontier3303, scorer epoch, novelty ledger,
and September20 17:59:20 UTC transport deadline. No historical ACT or synthetic
caption was submitted; no native, scorer, or GPU process was restarted.

The new route has fresh private socket endpoints; the former stale socket is
preserved. Transport readiness alone is **not** a successful judgment receipt.
The first future natural ACT10391 reached the CPU proxy at **07:32:52 UTC**,
but was **not dispatched to the scorer**: the source exporter rejected its
88,290,372-byte THINK-to-ACT journal window against the existing 67,108,864-byte
total limit. The largest individual record is 22,102,730 bytes, below its own
33,554,432-byte limit. Thus connection refusal is repaired, but **scoring remains
blocked by the total-window limit**, not caption quality.

The operator's diagnostic reread authenticated the real source records and
discarded exported stdout; it did not score or replay the historical attempt.
Exact sizes and origin hashes are in `TRANSPORT_OVERSIZE_DIAGNOSIS.json`.
No byte/ancestry checks or memory limits were relaxed. The already prepared
node3 projected-wire candidate addresses the same failure class but still needs
safe custody/receiver integration; it was not silently injected into the live
scorer. This is an implementation blocker, not a new permission request.

There are 18 passing focused parent/route tests, five passing tests of the
reused original transport implementation, and seven passing authenticated
journal/scorer transport tests in the existing cached test environment. The
system Python lacks pytest; that failed invocation is preserved separately.
Both CPU controllers are registered
with the existing foreground supervisor. Boot installation remains
`BLOCKED_UNINSTALLED`; this is not a claim of reboot-safe operation.

## Still open

- The C0/Astra7 interrupted-sleep runtime candidate is now implemented offline.
  Main independently reran all **79 CPU tests** (39 candidate, 18 contract,
  22 strict-replay tests); all passed. It remains **uninstalled and not
  launch-ready**: Astra7's partial intent needs explicit reconciliation, the
  original startup/paired-LEARN integration is unfinished, and fresh full-source
  admission has not run. The candidate restarts all 48 updates from the durable
  saved checkpoint and counts discarded/recovery compute separately. It does
  not claim exact unsaved optimizer/RNG continuity or an actual GPU restore.
  See `research_loop/workers/post_recovery_node2_sleep_20260919/runtime_candidate/README.md`
  and Main's `TEST_RECEIPT_1789803093607468737.json` in that directory.
- The node3 parent service reports restart backoff in the current supervisor
  cut. A process inventory is not proof that every child is parented.
- No live retention-fix adoption or new level2/level3 correction chain is
  established by these repairs. No H1/H2 success claim follows from this probe.

The reconciled C2 same-block results remain in
`research_loop/workers/post_recovery_c2_age_eval_20260918/RESULTS.md`;
raw event sums and distinct per-seed results must not be mixed.
