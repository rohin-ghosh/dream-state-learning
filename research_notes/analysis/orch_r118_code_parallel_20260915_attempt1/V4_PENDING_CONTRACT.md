# V4 CODE pending-consolidation recovery contract

Nonmaterial Main-scoped recovery; CPU-ready candidate, not release/dispatch.
V1/V2/V3 and original live sources, calls, submissions and reservations remain
unchanged. This candidate removes the impossible requirement for another old
serial sleep, not the requirement for two fully settled scheduled episodes.

## Actual source custody, 2026-09-15 15:10:07 UTC

Native-only in-memory validator inspection succeeded on both CODE roots using
actual replay validation. No remote source file was installed, no raw returned,
no process signalled. Full machine receipt: V4_NATIVE_PENDING_INSPECTION.json.

| Branch | Pending cycle | Complete native calls | Parent COMPLETE / MISSING | Lifetime native / parent charges | Next cycle after catch-up |
|---|---:|---:|---:|---:|---:|
| F3 | 22 | 8 | 3 / 2 | 735 / 100 | 23 |
| A3 | 8 | 9 | 3 / 2 | 274 / 40 | 9 |

Both actors alive, no live children, previous CODE DEV settled. Both pending
cycles have no SHARED_SLEEP/cycle COMPLETE. Generation1 checkpoint:
43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d.
Carried reflection cap3072 unchanged. Common submissions:

- F3 generation_000001/F3.json SHA03c213d4aa63578aca73ac0646d662ba26e4c3388941b457d245af29360f069b.
- A3 generation_000001/A3.json SHA3ef8ac0f02a734aaefde15f909c062e9f0d3959b8719129c0be43bff40dc0480.

These are COMMON submission-file hashes. Earlier observation hashes label the
local SHARED_SUBMISSION.json wrapper and must not be substituted for them.
This is current pending-cycle accounting, not completed sleeps or all8 DEV.

## Exact Main/Herschel handoff

Use a fresh service/release subtree within each existing CODE root, never reuse
an earlier attempt. Existing INTEGRATION.md commands remain; both Main DRAIN
and LAUNCH branch entries additionally require
`boundary_mode: SETTLED_PENDING_CONSOLIDATION`. DRAIN still pins exact native /
guardian identities, root, PLAN hash and common root. LAUNCH still pins frozen
source manifest, checkpoint, campaign, anchor order and original FINAL custody.

After an actually authorized release, HANDOFF.json and OWNER_RELEASE.json retain
original bounds, all charges, previous DEV, carry, all original reservations,
parents, environment and triples. New node-local artifacts are PENDING_ROWS.json,
EPISODE_0_SETTLED.json, EPISODE_1_SETTLED.json, PENDING.json and PENDING_CURSOR.json.
They are derived custody metadata; no original file is rewritten. Episode
COMPLETE means all scheduled actions terminal, not successful task outcome.

Owner request's boundary is the actual Herschel third mode, exclusively:

```json
{
  "committed_checkpoint_sha256": "<canonical generation1 checkpoint SHA>",
  "mounted_checkpoint_sha256": null,
  "canonical_reload_required": true,
  "settled_pending_consolidation": {"path": "<PENDING.json>", "sha256": "<SHA>"},
  "settled_cursor": {"path": "<PENDING_CURSOR.json>", "sha256": "<SHA>"}
}
```

Pending schema R118_SETTLED_PENDING_CONSOLIDATION_V1; cursor schema
R118_PENDING_CONSOLIDATION_CURSOR_V1. Original SILENT parent reservations remain
SILENT; the central terminal-only envelope normalizes that enum to MISSING with
explicit disclosure because its accepted terminal enum excludes SILENT. This is
not a change to consumed-parent metrics. Both observed pending cycles have0SILENT.

Startup uses bootstrap_fresh_actor -> wait_fresh_collection_go. Pending CODE
must receive action RESUME_PENDING_PARALLEL_BOUNDARY_BEFORE_NEW_CALLS and exact
pending reference. Then resume_pending_consolidation must return
existing_submission_reused=true, exact rows/submission/cycle, zero native calls
and optimizer updates. CODE never calls submit in this path. It constructs a
fresh-identity SAFE certificate and calls await_campaign_activation then
launch_at_boundary. No per-owner collective initialization or serial fallback.

Only actual all8 commit permits pending cycle COMPLETE, its first fresh DEV,
settled cursor and next-cycle collection. Other owners without pending rows
collect their two scheduled episodes after bootstrap GO. Thus GO waits for8
bootstrap actors, not8already-submitted branches. Failed helper/collective remains
a charged single attempt; no duplicate submit, retry, old TRAIN replay, or
retroactive capture-generation metadata.

Original guard, broker terminal-only handoff and same8-call FINAL rebind remain
required before SAFE publication; Hubble owns F3 broker and CODE owns A3 overlay.
Main alone releases/dispatches and supplies all8 common authorization. No current
actor, timer, broker, CONFIG, source, ledger, or budget was changed by preparation.
