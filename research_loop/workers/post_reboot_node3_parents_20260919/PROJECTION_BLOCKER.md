# Main / endpoint owner / Averroes: bounded projection contract blocker

September19 2026, 02:09UTC. **Oversized-window scoring is NOT repaired.**
This task made no live changes. Non-material, offline diagnostic/regression work
only; no native, scorer, parent, bound, epoch, ledger, parser, or training-row
change; no synthetic live request, historical ACT replay, signal, commit or push.

## Root cause and actual existing route

The same source ACT/THINK can be authenticated on node3 without shipping its
checkpoint state elsewhere. That state is not caption content, but its original
bytes are currently required to recompute complete journal hashes and ancestry
on the receiver. Raw strings plus hashes alone are not authenticated evidence.

The deployed path is `transport_large_proxy.export_via_ssh` ->
`journal_transport.export_chunks` -> original `--import-chunk` over authenticated
SSH -> `Hub.native` -> `LifeSession.process` -> `process_verified`.

- `research_loop/workers/rohin221_continuous_caption_20260918/journal_transport.py:22`
  exports the whole contiguous latest-THINK-to-ACT-stage window. Line44 retains
  the original **67,108,864-byte aggregate**, including COMMITTED state,
  CONTEXT_INPUT and REQUEST resume/checkpoint state. Individual bound remains32MiB.
- `research_loop/workers/rohin233_ovx4_recovery_20260918/transport_large_proxy.py:33`
  already imports unchanged chunks and sends only the last stage record to the
  scorer socket. Thus the existing socket envelope is already small: the
  failure happens earlier, before any export envelope or scorer dispatch.
- `research_loop/workers/rohin221_continuous_caption_20260918/journal_bundle.py:50`
  accepts only `{index,file_sha256,raw}` original-byte records, validates both
  hashes and contiguous linkage, and rejects mirror rewrites.
- `research_loop/workers/rohin221_continuous_caption_20260918/shared_scorer.py:41`
  accepts exactly `{session_id,request,records}`; request is exactly
  `{origin,metrics}`. At line73, the server exposes `native.sock` and `base.sock`,
  not a native projection/import-attestation endpoint.
- `gpu/ny_caption_life_service.py:74` is an internal callback **only after source
  validation**, not a raw-text network endpoint. The standalone base route has
  incompatible source/session bindings and cannot legitimately relabel natives.

Splitting an oversized origin across unaccounted imports would evade the
aggregate guard, not repair it. Stripping state breaks original record hashes;
rehashing descendants breaks the original ACT origin. Omitting intermediate
records breaks THINK attribution/salvage. None was attempted live.

## Minimal unsupported-contract blocker / action needed

No supported current route accepts node-side full validation plus a bounded
authenticated source projection. There is no exposed live receiver-reload hook
in this deployment. Editing its immutable disk source or launching a second
scorer would not be a valid scoped repair.

**Endpoint owner coordination is required:** add/deploy an owner-authenticated
native projection receiver in the existing serialized scorer service, feeding
its existing `process_verified` only after validating a pinned node-side
authentication receipt. Preserve exact raw ACT **and latest own THINK**, original
source/record/COMMITTED-stage identities, contiguous-chain and real-boundary
checks, session/native binding, parser byte offsets, salvage attribution, dedupe,
seen ledger, original epoch, deadlines, and all existing wire bounds. Do not
transport only pre-extracted captions or treat hashes as signatures. The
deployment mechanism must be explicitly coordinated because this scope forbids
scorer restart and no supported hot activation is exposed.

This is an **unsupported provenance wire contract**, not proof that authenticated
projection inherently changes the judge or scientific thesis. A source verifier,
receiver and end-to-end authenticity/parity tests are needed before claiming
equivalence. No deployment approval or independent acknowledgment is inferred.

## Fresh natural operational-error receipts

Read-only audit02:07:50.415723UTC. All five source responses below were generated after
Main's01:48 resume; none was replayed. Exact Tool text appears in the listed
REQUEST with `all_history_tokens_masked=true`. These are explicit **no judgment,
scorer not contacted** notices, not scorer receipts or training success.

| Fork | RESPONSE -> ACT -> Tool INBOX -> REQUEST | Failure UTC | Tool publication UTC | Original bytes |
|---|---|---|---|---|
| observation | 8065 -> 8068 -> 8079 -> 8081 | 02:00:20.319113 | 02:00:38.942122 | 72,824,491 |
| perspective | 8447 -> 8450 -> 8459 -> 8461 | 02:02:02.022120 | 02:02:15.720126 | 72,878,356 |
| revision | 7781 -> 7784 -> 7793 -> 7795 | 02:07:15.729012 | 02:07:24.110403 | 109,537,088 |
| selfderive | 7211 -> 7214 -> 7223 -> 7225 | 01:59:52.344198 | 01:59:59.265870 | 72,801,400 |
| historical unparented; R233 parented | 7766 -> 7769 -> 7778 -> 7780 | 01:56:18.737147 | 01:56:31.996769 | 104,984,803 |

## Smaller windows are reaching the scorer, without caption judgments

At02:08:49UTC,48 post-restoration transport attempts comprise16 explicit
pre-dispatch failures and32 scorer-service receipts. Those32 contain **zero
caption feedback results**, returning scene-identification/no-caption errors.
This is not complete transport silence, successful caption ranking, or repaired
THINK-salvage transport. Current shorter windows preserve the original policy;
no ancestry omission was introduced by this worker.

The original Tool relay's first new natural scorer -> native INBOX chains are
authenticated for all five: observation7812 -> 7815 -> 7827 at01:32:28.586727;
perspective8192 -> 8195 -> 8207 at01:33:30.069267;
revision7397 -> 7400 -> 7412 at01:28:56.999471;
selfderive6958 -> 6961 -> 6973 at01:30:10.057938;
historical-unparented7511 -> 7514 -> 7526 at01:27:56.130309UTC.
These are earlier first receipts reverified read-only, not new scoring or replays.

## Identity, tests and evidence

Real-host02:07:53UTC: model330973, controller425470, error reporter459421,
supervisor399392 unchanged; VM boot80d71f45-6f0c-4479-b0e5-77a9611c793e.
Scorer499900/start10094999 reverified02:09:33UTC, boot
7c130f24-3105-4909-abfb-b669929e0b96; bridges448173/502015, five epochs,
native incarnations and node-local publishers unchanged. No service registration
change is needed for this offline-only task; existing restart commands/locks stand.

**43 CPU unittest tests pass**, including14 new deployed-contract tests: exact
ACT/THINK callback-input parity for full originals and the supported preimported
short envelope; rejection of missing ancestry, foreign wire fields, byte tamper,
stripped/rehashed state, descendant rewrites and standalone relabeling. The
callback is a CPU test stub, not a judge or an implemented projection verifier.

Evidence: `PROJECTION_READINESS.json`, `PROJECTION_READONLY_PREFLIGHT.json`,
`DEPLOYED_PROJECTION_CONTRACT.json`, `DEPLOYED_RECEIVER_ENTRYPOINT.json`,
`PROJECTION_CONTRACT_TESTS.txt`, `FRESH_OPERATIONAL_CHAINS_LATEST.json` plus its
immutable cut, and `JUDGMENT_RECEIPTS_LATEST.json` plus its immutable cut.
Actual deployed main SHA256:
`c5ea88e80e520fe35dc3df9c5b442060bd86ced4453e779c5cfe585cc552ef0c`.
Shared scorer, importer and LifeSession full-source hashes match deployed;
native source-authentication function ASTs match. Local judge main differs, so
the handoff uses the separately read deployed entrypoint, not local-main inference.
