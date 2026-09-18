# VM/orchestration handover inventory — 2026-09-18

Preparation only. No destination has been selected, no credential is copied,
no lease is changed and no transfer outside the repository is authorized by
this checklist. Rohin says his leases and API access outlast his internship;
verify each provider's actual expiry and account ownership at handover.

## What must move or be reproducible

| Item | Capture / validation | Handling |
| --- | --- | --- |
| Repository and dirty source | Branch/commit/worktree map; explicit local patch inventory; pinned dependencies; submodules if any | Push reviewed source and small receipts, not `git add -A`; retain dirty checkout until verified |
| Life registry and topology | Logical names, node aliases, GPU allocations, roots, active native/controller/parent/relay PIDs, peer and console routes | Private operational registry; public version uses aliases, no host addresses |
| Complete per-life state | Adapter, optimizer, RNG, working state, cycle/frontier and immutable manifest with SHA256 | State-consistent snapshot at an existing safe boundary; preserve active life, never claim manifest-only files are bytes |
| Journals and learning provenance | REQUEST/RESPONSE/STAGE, tool results, inboxes, row texts, sleep recipes, eligibility and update receipts | Preserve source hashes and cross-record links; authenticated parent/child identities and target masking must survive |
| Dataset and game state | Local data manifests, panel/version mappings, assets, scoring adapters, novelty index, attempts, cache identity and decisions | Preserve teaching/evaluation separation; sealed material and answer keys stay outside child visibility |
| Judge jobs | Checkpoints, optimizer/scheduler/RNG, datasets, shard order, training steps, selection and contrast-test outputs | Capture both running arms and exact resume commands; retain bytes on nodes until copied and hash-verified |
| Stateful CPU services | Scorers, polling frontiers, publication outboxes, dedup ledgers, leases/locks, expiry timers, logs | One writer per route; copying a process list does not restart a service |
| Parent programmes | Briefs, curriculum phase, last seen child record, pending messages, reading/memory schedule, factual sources | Preserve deliberate unparented controls and P7-only Astra7 parent relationship |
| Console and research record | Rohin transcript/pinning, inbox acknowledgement state, names, COORDINATION, worker receipts, thesis/notebook and unresolved orders | Replay only undelivered source-bound messages, not all history as new input |
| Secrets and private endpoints | SSH identities, host map, provider credentials, API tokens, permission scopes, renewal/revocation owners | Inventory names/purposes only; encrypted authorized channel later, never Git, logs or child context |
| Environment | OS/runtime versions, model/tokenizer cache checksums, Python environments, CUDA/driver compatibility, storage layout and free space | Rebuild/test on destination before any controller takeover |
| Monitoring and backups | Hourly reports, publication worktree, error alerts, service expiry/restart policy, manifest/backups | Verify first report on destination; preserve immutable previous snapshots |

## Cutover checks, not an instruction to cut over now

1. Rohin names the destination and authorizes private transfer/access. Measure
   total bytes and transfer time; exclude large artifacts from repository commits.
2. Build a node-by-node manifest with byte size, checksum, ownership and latest
   verified checkpoint. Verify both source and destination before deleting nothing.
3. Bring up destination readers first. Validate console/Tool rendering against
   exact source receipts without replaying actions or creating duplicate parents.
4. Transfer each stateful CPU writer with an explicit frontier and mutually
   exclusive writer lease; keep GPU learner lives running on their leased nodes.
5. Verify uninterrupted record timestamps, one parent per intended route,
   actual judgments in context, no control contamination, live learning recipes,
   secret access, and the next hourly report. Record any real gap in seconds.
6. Keep the old orchestrator and recovery manifests available until Rohin
   accepts the handover. Retire old CPU writers only after counterpart verification.

## Time-bound services already requiring attention

- P3's source-authenticated judgment relay currently expires at **11:07:09 UTC
  on September 18, 2026**. Renew or replace before that time without duplicate
  delivery; do not let scorer results become silent again.
- The current hourly collector expires at **14:09:07 UTC on September 18, 2026**.
  Its publication companion and allowlisted worktree are part of the handover.
- Absolute source paths in receipts may be inherited logical paths, not physical
  directories. Preserve the logical-to-physical mapping rather than rewriting
  historical hashes or paths.
