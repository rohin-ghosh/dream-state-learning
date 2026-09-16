# R137 A2 activation and first fresh Astra response

[Builder / Main] September 16, 2026, 02:27 UTC. This updates the historical
CPU-ready handoff without overwriting its pre-launch evidence.

## Actual activation

The exact old A2 broker3796147/start160688270 retired between calls at
02:22:44 UTC, after an earlier busy observation safely resumed it. Zero child
signals were sent. Replacement broker2017450/start163239415 started at
02:22:56 UTC, from published commit `a7926383`; it remained alive at02:25:25.
Provider, policy, effort, budgets, consumer, checkpoints and optimizer unchanged.

Stage: `/data/home/rohing/courier/runtime/r137_a2_request_repair_v3`.
Manifest: `bb3ab4b49faf867c6c936922a6b5e0bcdd009bd5a697d70309db1ddd619cf713`.
Actual post-lock boundary02:22:58.216 UTC excludes all101 existing requests and
reservations at/before Unix1789525378.2163372. No historical request was replayed.

| Receipt relative to stage | SHA256 |
| --- | --- |
| RETIREMENT.json | 0175202eb9dde4ff9e647830963bd39612e14644e080e331a73e37781f22b48a |
| runtime/START_BOUNDARY.json | 01db16ca4d19d136cdae15db9bcfd3bedaac51ad676e1eac5e4505b8b1ae31de |
| runtime/STARTED.json | 0fe8034bded39a5bb6b1ec69160a2a921a0da19aa1b09cea59a2ed5d05fdbaba |

## First new request: COMPLETE publication, injection pending

`R121_C000039_E1_experience` reserved parent slot102 at02:23:03.871 UTC,
strictly after activation. The native request SHA is
`f999367e301223953fea385147e4ebdcb96153621f4d7bce36916729f7f02a80`.
Provider RESULT records **COMPLETE**, actual model
`openai/openai/gpt-6-astra`, finished02:23:20.958 UTC. PUBLISHED records
COMPLETE at02:24:00.240 UTC. No native `parent_delivered` file existed at the
02:26 inspection: **publication is not yet verified child consumption**.
The child had already entered C39 sleep; do not interrupt it or replay guidance.

Native queue base:
`/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane5`.

| Receipt relative to queue base | SHA256 |
| --- | --- |
| parent_transcripts/R121_C000039_E1_experience/RESULT.json | aa3f50eaf6408d38f8ee1ad3e8db613329714d4099a2fafa594ac4f9a48277c1 |
| parent_claude/R121_C000039_E1_experience.claim/PUBLISHED.json | 5298e57989c71d56d70ecba1d0c9163e6b02380060c9b6f30f57bde7a063fb31 |
| parent_queue/R121_C000039_E1_experience.response.json | e33f34495a1f1ee1473b558faf96d50d8843446a13abc5208c035bc9a48242d7 |

## Child is advancing, not stalled

Native root:
`/localhome/local-rohing/orch_math_feedback_uptake_r124_readout_20260915_attempt1/A2`.
At02:26:52 UTC: native908,parent102, committed optimizer14625,
child-token exposures2275423, anchor-token exposures273305. C39's live
`sleep/UPDATES.jsonl` contained186 updates, most recent02:26:49.494 UTC,
with26720 child-token and3355 anchor-token exposures in the ongoing sleep.
Keep live-sleep counts separate from committed COUNTERS; do not double count.

Native dispositions written during01:26:52–02:26:52 UTC were **0 COMPLETE,
8 MISSING,0 SILENT**, all from pre-activation requests C35–C38. Fresh epoch:
one COMPLETE publication, zero verified native injections at inspection.
This distinguishes a repaired dispatch path from parenting uptake or learning.

## Other lanes and remaining scope

Independent A1 read-only audit at02:24 UTC found its renderer already accepts
NEXT_GUIDANCE with BOUND_REQUESTED_SETTINGS; no A2-style backport needed.
Its latest10 native receipts were0 COMPLETE,5 SILENT,5 MISSING (not an hourly
cohort). No A1 mutation or new provider call was made by the audit.

F1/F2/F4 remain explicitly unparented: startup-loaded consumer model bindings
reject honest Astra replies. Prospective Astra is an accepted model choice,
not a prohibited fallback. Resolving the incompatible resident bindings needs
the previously requested saved-state process handoff while preserving the
logical child, adapter, optimizer/RNG, context, ledgers and old dispositions.
No permission response or supported no-restart switch has been obtained.
No new F1/F2/F4 broker, spoofed identity, or child restart is claimed.
