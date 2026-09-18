# R205 external-dispatch audit — September 18, 2026 UTC

Read-only observation at **03:54:46.218 UTC** (Unix1789703686.218068). No service/native/parent signals, broker writes, human-inbox writes, runtime edits, or duplicate insurance copy. This is an operator receipt, not an R205 deployment receipt.

## Immediate finding for Main

**Yes: the legacy community service independently consumes committed C2 responses, without a communication-stage exclusion.** Runtime omission of ordinary executor dispatch is necessary but does not exclude this second consumer. Its current C2 cursor is stalled historically, so there is no evidence that it is presently dispatching the current R204 responses; the stall is not a safety filter.

- Live VM process **769286**, start ticks178833457, cwd `/data/home/rohing/dream-state-orch`, command `/usr/bin/python3 -B -m gpu.orch_r153_community_service --config /data/home/rohing/dream-state-orch/research_loop/workers/r157_community_service_keepalive_20260917/bundle/SERVICE.json --run`.
- Source: `gpu/orch_r153_community_service.py:177` pulls committed snapshots; lines198–200 create `TRAIN_CHILD_RESPONSE` origins; **line318 classifies raw response, line326 submits CPU work, line334 applies exchange actions**, independently of the native R184 dispatcher. Lines374–383 poll all five actors. No R205/stage exclusion is present in this inspected source.
- Current on-disk service SHA256 `afcc59a2fa317d0242389198e526079a401649e161e5b80b205198e796fdfbc7`. This pins the inspected source, not a new introspection claim about loaded Python bytecode.
- Config SHA256 `401489f42fb3fba8dea7046e40401c053eceb9d5132de2df98e794d7455cf5ef`; C2 binds host `ovx3`, original root `/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`, journal `260be8b8710a42559b291797c6e14983`.
- Actual remote transport: `/localhome/local-rohing/orch_r153_service_source_v4_20260917/gpu/orch_r153_community_transport.py:126`. Lines126–152 collect REQUEST/RESPONSE/COMMITTED triples without stage exclusion; configured transport SHA256 `b798199a10508164de724631fc8a81bf28fb3500db5bc0048ec486cb7707905a`.
- This external service still binds the older CPU gate `/localhome/local-rohing/orch_r153_cpu_smoke_20260916t2245z/gate`, SHA256 `8b4579d9c99c2f4d54fbd738ff965bc9472ed9f08ff6fae5f4dbfeadceaf1150`. It is not the native math bridge's newer gate. No claim of R194 policy equivalence for the legacy service is made.

## Actual persisted C2 dispatch state

Read in one SQLite read transaction using `mode=ro` and `PRAGMA query_only=ON`, without constructing the mutating service/broker classes:

`/data/home/rohing/courier/r153_community_20260916/broker/state.sqlite3`

```json
{
  "actor": "C2",
  "next_index": 3434,
  "head": "fd4ab120e25ad5fe6628ed9b68dc7dcdf18268b4d98aaf2fe8841895ac9c9caf",
  "error": "OperationalError",
  "job_counts": {"CPU_DONE": 6, "REJECTED": 87},
  "latest_stored_response_indices": [3429, 3425, 3275, 3271],
  "pending_or_cpu_intent_or_cpu_unknown_jobs": 0
}
```

The same cursor/error was observed at03:51:48.433UTC. The error's underlying cause has not been established. Do not repair/restart this shared service opportunistically and unleash historical backlog. Other C1–C5 bindings must be preserved.

## Math bridge is request-driven

Node5 process **3179422** remains live; remotely checked03:54:06UTC. Source `/localhome/local-rohing/orch_r204_C2_20260918_resume1/math_bridge.py`, SHA256 `63100f72a00fedc20c609a250b399eec4874b5380a9638157a63e4fe50531a3c`.

- Lines25–33 send an explicit native request to the UNIX socket; `serve()` lines36–86 waits on `accept()` at55, validates peer/native/guard bindings, and invokes `cpu_once()` at75.
- It does not independently tail the journal or execute every response. Bypassing `_cpu` for the R205 direct console ACT prevents this caller path.
- It does not currently reject an explicitly submitted communication-stage response itself. No R205-specific defensive filter has been deployed.

## Required narrow integration before R205 serving

Main owns the stage module/tests. Bind the actual direct-console marker and genuine source-inbox IDs in the committed request/response provenance, available **before any external classification or CPU/exchange submission**. A later post-COMMITTED stage marker alone can race this independent consumer. Match that exact contract in the community consumer/transport, skipping communication replies regardless of whether their prose includes executable fences or JSON. Keep other actors' behavior, source history, and cursor evidence intact. The current stall is not an acceptable substitute for this exclusion.

No shared runtime/service/test/COORDINATION modification or new review framework was introduced by this audit. The R205 bundle/marker is not yet supplied; this report identifies the concrete external dispatch path to account for, not a new conceptual-approval gate.

## Concurrent operator state

- C2 current-incarnation read03:53:54.010UTC: native3179563/start23773135, R204 LOADED6057 at03:31:00.309UTC; finite head6261 UPDATE. Latest complete55/record6202 at03:48:04.194UTC, AdamW5116. Detailed source/hash evidence: `CURRENT_INCARNATION/OBSERVED_20260918T0354Z.json`.
- Actual R204 COMPACTION6207 at03:50:07.241UTC reduced13066 to5842 tokens using prior child compaction; REQUEST6208 started03:50:07.259UTC at5842 masked tokens. Nine R204 requests through6261: maximum12084, zero at/above12288, maximum observed THINK-stage streak1.
- Same Astra2600320/start180884873 and Main insurance process2738165/start181034852 are live at the audit time. No recovery/restart performed; backup progress beyond process liveness is Main's receipt to report.
- All four tracked parent publications now have actual rendered-request receipts; fourth `4e733c7e32c34bfe9a918c5fb90b5714` first appears in THINK REQUEST6208. RESPONSE6063 did not answer Rohin retry637c5468. No R205 answer/retry-ready claim.
- No clone/retirement actor was launched by this operator. The six slots remain relinquished for explicit handoff as documented in `COPERNICUS_NODE5_FROZEN_HANDOFF.md`; original GPU1 remains owned here, repo_reader7 protected.
- Emergency evacuation cancelled; no04:00 stop or purchase. User-confirmed lease end September22 04:04UTC; native's existing wall was not silently extended.
- Saved completed learning remains preserved, including prior corrupt exposure. Historical R202 resume preserved model/AdamW/SAVED-checkpoint RNG/current history, not proven exact resident post-console sampling RNG. No rollback/unlearning or exact full-live RNG-continuation claim.
