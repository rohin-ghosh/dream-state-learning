# Main/Turing P3 receiving contract — no empty novelty restart

State schema is `R223_CAPTION_SESSION_STATE_V1`. Exact native wrapper fields:

```text
{
  schema: "R223_CAPTION_SESSION_STATE_V1",
  life_root: original absolute resolved native life root,
  scene_ids: [{contest_id, canonical_scene}, ...],
  phase: "COMPLETE",
  game: exact last complete AFTER.json.game,
  policy: exact last complete AFTER.json.policy,
  seen: sorted list of EVERY already-processed ACT record_sha256,
  format_policy: "R223_FREEFORM_CAPTION_QA_V1",
  source_mode: "NATIVE_JOURNAL",
  session_binding: null
}
```

`scene_ids` is now the descriptor list from the unchanged approved game manifest,
in original scene order, not just strings. Both fields in each descriptor must
match the new service loader; no renaming, scene reorder or guessed identifiers.
`game` preserves all novelty archives, cached submissions and accounting.
`policy` preserves previous counts/directions and outcome-allocation state.
Freeform service chunking respects the legacy internal allowance without dropping
validated captions. The legacy direct-submit policy remains unchanged.

For old services without SESSION_STATE.private.json: at Main's scorer-boundary
cutover, retain/hash original LOADED and EVERY attempts/{ACT_SHA}/REQUEST,
BEFORE, RESULT, AFTER file. Include all completed processed ACT hashes in `seen`,
even old unparsed/zero-caption outcomes. Verify sequential BEFORE/AFTER continuity
and that the selected latest AFTER closes the last attempted request. If any
request is pending/unknown, do not call the export COMPLETE or replay it. Preserve
the old output/root; write a NEW bound wrapper file and NEW receiving output.
Never reconstruct novelty merely from aggregate counters or accepted captions.

Native invocation adds `--resume-state WRAPPER --resume-state-sha256 SHA256`.
Keep the same game/data/image/judge/encoder/pixel/relevance, agent_id, top_k50,
life root and manifest bindings. `game.restore` validates the old state's bindings;
the session validates scene descriptors/root/source mode and restores `seen`.
A new output directory does NOT mean a new game or reset candidate history.

Before releasing the waiting proxy, verify the new scorer `LOADED.json` fields:
`resume_state_input_sha256` equals the exported wrapper SHA;
`resumed_complete_state` is true; `restored_seen_count` equals ALL exported ACT
hashes; `restored_game_snapshot_sha256` equals `ny_caption_data.digest(wrapper.game)`;
`restored_policy_snapshot_sha256` similarly binds `wrapper.policy`. Hashes use
sorted ASCII-escaped compact JSON (`data.canonical`), not file formatting bytes.
These are measured AFTER restore, not copied from the input or aggregate guesses.
They include no private caption payload. `resume_state_input` also binds the
input path/hash, and `source` binds the loaded service file. LISTENING remains
separate readiness evidence. No need to stop the old service to perform a load.

Main owns `rohin224_caption_adoption` and the actual service switch. This worker
has not touched the live scorer or P3. Do not replay ACT701/765. The server's wire
contract is backward compatible; the old pinned native client does not gain
same-opportunity retries until its separately coordinated safe source adoption.

Standalone sessions additionally set `source_mode="STANDALONE_GENERATION"` and
`session_binding={controller: exact_binding, backend: exact_identity}`. Their
`life_root` field names the confined generation receipt root, NOT a native life;
`seen` contains actual generation request hashes. They are independent conditions
and never import P3's novelty or pretend a frozen base has an optimizer.
