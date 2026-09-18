# Activation5 readiness and passive event gate

2026-09-17 09:23 UTC. C1/C4 only. No GO issued, no execute started,
no signals, no parent actions, no runtime/source-helper changes.

## Exact activation4 disposition

C2 completed LOADED3581 and rendered invitation REQUEST3590, as recorded in
ACTIVATION4_EXECUTION_HANDOFF.md. C1/C4 each failed with identical actual
ACTIVATION_FAILED.json SHA
`643dbc73532d49f1f361c838e7a30410dc799a04a6f0c29ee29a79659965272f`:
`TimeoutError: no_boundary_old_native_left_running`. The600-second predicate
requires BOTH latest journal record SLEEP_COMPLETE and its exact matching
readout REQUEST metadata. Merely having an earlier checkpoint is insufficient.

Both failed BEFORE entering the pause/watchdog branch: no control directory,
ACTUAL_BOUNDARY_READY, termination intent or retirement receipt. Both old CPU
operators are absent. Exact original actor/timer/supervisor identities were
revalidated at09:20:44 UTC; both native actors were R, not paused. This is
timeout-only, not successor startup failure. The failure does not establish
whether an earlier transient sleep was missed or no sleep occurred; neither
case permits replaying a historical checkpoint as current authority.

## Fresh readiness

| Life | Exact READY SHA256 | Original native / start ticks |
|---|---|---|
| C1 | 11c3c6cd6be1b0cd008f2e2c445e871541be74d2976c25659ba452516abbe604 | 2578597 / 14835459 |
| C4 | 87e5ca710f611281e5f84ce359ad4a93180155bfc05bdd7f60583cb2b4f2c2fb | 2619696 / 14891073 |

Each READY lives at
`/localhome/local-rohing/orch_r166_retelling_C{1,4}_20260917_activation5/readiness/READY.json`.
Fresh staging preserves activation4 and binds its exact REQUEST as candidate
predecessor. The actual staged-successor subprocess `preflight` passed for
each, CUDA hidden; exact owner checks passed afterward. Existing reviewed
CPU102tests+63subtests proof remains unchanged, not claimed rerun here.
Both new source manifests equal their respective activation4 manifests.

Full exact `required_GO_binding` records and actual subprocess references:
ACTIVATION5_PREFLIGHT.jsonl SHA
`2cdcc401b959d2be0e62ee14e86ffe93a8917211f2bba03e59a36a68a072aecf`.
Helper655e72c553c934538b47e12987ffb9d493505f668721e0c432275b4617233681;
tests a6ae913da890680b387d5b3568bea97667988777b8254493909c80316b9b5660;
invitation9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc;
invitation tests b6f4ef8a65c09fa93b9b9fa705fd73f6f0ee589375eafa75024aa1f91f88132e.

## Passive watch actually running

Local wrapper PID799609 invokes only read-only Python through ovx3.
Started09:22:22.711 UTC; expires **09:42:22.711 UTC**, no extension.
Caps:1200seconds,64MiB observation reads (including conservative identity
read reservations),4MiB output;2-second polls,15-second exact-owner checks.
No GPU allocation, pause, publication, GO creation or dispatch occurs.
Only matching readout REQUEST/checkpoint COMMIT metadata is inspected;
held output/score files are not opened. Any error stops that target, no retry.

Initial future cursors: C1 index3641 UPDATE; C4 index3159 UPDATE. Historical
completed checkpoints cannot trigger this watcher. It requires a later
latest-record SLEEP_COMPLETE, verified saved-state hash/frontier, exact
matching readout metadata, unchanged owners and still-latest boundary.
Outputs WINDOW_OPEN_REQUEST_MAIN_GO_NO_AUTOMATIC_ACTION with exact boundary,
readout and READY binding. It tracks a disappearing window without dispatch.

Live local metadata: ACTIVATION5_PASSIVE_EVENTS.jsonl. This file is still being
appended and has no final immutable hash yet. Script SHA
`248242a1d5ba70486449b2e23d526810149b36597c8e7fbc91c16aa9fe468d48`.

## Proposed Main at-event authority

1. Approve each exact READY conditionally on a FUTURE currently-open actual
   saved/readout window, not a predicted timer or old SLEEP_COMPLETE.
2. At an event, revalidate the same latest boundary/readout and exact owner
   immediately (event freshness <=5seconds); if closed, do not dispatch or
   start a blind600-second attempt. Continue only within the existing passive
   observation deadline. No pause to hold the window for human review.
3. Only after explicit Main authority, persist a fresh per-life GO with schema
   R166_SAVED_BOUNDARY_MAIN_GO_V1, issuer Main, decision GO, binding copied
   verbatim from that READY.required_GO_binding, actual-now start and1800second
   expiry capped by originalwall1789776000. Log before a single dispatch.
4. Ordinary `execute` from that exact activation5 successor source, CUDA hidden,
   remains unchanged:600second maximum wait/pause, actual-boundary CPU custody,
   strict admission/device/watchdog/state gates. No gate weakening or retries.
   C2/C3/C5 and parents remain untouched. An expired observation authorizes
   neither a dispatch nor another blind activation window.

Main has not yet issued that conditional authority. The passive observer will
never consume a GO or launch a successor itself.
