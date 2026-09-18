# Stage 1 pixels/game contract — 2026-09-17

Authority: Rohin160's explicit parallel Stage 1 development instruction in this
thread, updated by Rohin161 below; governing handoff
`AGED_AGENT_CLONE_EVALUATION_AND_PARENTING_HANDOFF.md` revision 5 except where
Rohin161 overrides it. The judge/pixels revision 2 document is subordinate. This is scoped
implementation of that approved design, not a supervisor workflow, a new
architecture decision, scoring validation, or a final-run authorization.

## Rohin161 update and current API status

Both core modules and their CPU tests now exist. `CaptionGame` accepts generic
nonempty `lane` strings, including `PARENTED` and `UNPARENTED`; lane metadata is
never sent to scoring or vision. Main owns both learning/sleep lineages and
LOCAL Qwen visual transport, not a gateway. This worker does not implement FINAL.
Automatic/LLM similarity labels and small spotchecks are permitted in Stage 1;
missing new human panels are **not a Stage 1 blocker**. Automatic-only reports
remain provisional. Judge validation uses held-out human-rated dataset evidence
and automatic checks in Ampere's component, not a new human-panel gate here.

Current local governing rules are
`research_loop/workers/r177_caption_game_stage1_20260917/CURRENT_BUILD_RULES.md`
(the R161 current-build rules referenced by Main). Restart preserves each real
continuous lineage, not a new life or reset budget.

### Restart API — ready

`PixelArchive.from_snapshot(snapshot, agent_id, contest_id, scene, config, embed,
*, max_submissions=10000, same_joke_verifier=None)` and
`CaptionGame.from_snapshot(snapshot, agent_id, lane, manifest, config,
pixel_config, *, embed, judge, inspect_provider, count_tokens,
same_joke_verifier=None)` return restored instances. All constructor bindings
remain explicit and must match the snapshot; callers may pass them by keyword.
Alternatively construct a fresh instance and call `instance.restore(snapshot)`.
Restore on a nonempty instance is rejected rather than discarding live state.

Restoration invokes **none** of the supplied callables (including tokenizer and
optional verifier). It validates immutable representatives/vectors, chronological
membership closure, response/cache/trace agreement, agent/scene/config bindings,
and budget/counter invariants before committing state. Invalid state raises
`SnapshotError` (a `ValueError`) and leaves the instance unchanged. Main owns
atomic file persistence and external source/model/tokenizer/manifest hashes.
New game snapshots use schema 2 and include per-call counter deltas. Existing
schema-1 game snapshots are supported without provider replay: original
counters and events become an explicit accounting baseline, never reset or
fabricated per-call observations. Subsequent actions receive full delta records.
Archive snapshots retain schema 1, including legacy all-distance traces.

User update (line-wrapped): "Rohin161overridesrev5! Development2learninglineages
PARENTED/UNPARENTED (bothLoRAsleep), FINALno parentsbothsleeps;
frozenonlycontextbaselinepossiblylater. GamecorelaneIDs generic do not hardbind
FROZEN/LEARNER; supportPARENTED/UNPARENTED Mainintegration.
RequiredvisionLOCALQwen (Mainwiring), notgateway. SimilaritylabelsLLM+smallspotcheck;
nohumanpanelgateStage1; keepautomatic-onlyprovisional.
Acceptancejudgeheldouthumanrateddataset+automaticchecks, no newhumanpanelblock.
NeedAPIstatussoon; Mainwritinglocalvisionandrunnerbridge."

## Integration surface (published before implementation)

`gpu.ny_caption_pixels` exposes:

- `PixelConfig(embedding_model_id, embedding_revision, rho_coarse, rho_primary,
  rho_fine, resolution="primary", input_format="scene_caption_v1",
  calibration_status="provisional")`, a frozen dataclass. Thresholds are
  explicit; coarse <= primary <= fine. The embedding adapter must be a frozen
  pretrained encoder, not an arm-specific or trained-in-game model.
- `PixelArchive(agent_id, contest_id, scene, config, embed, *,
  max_submissions=10000, same_joke_verifier=None)`. `embed(text)` returns a vector;
  the core validates and normalizes it. Optional verifier receives only
  `(scene, candidate_caption, representative_caption)` and returns a bool.
- `archive.submit(caption, *, accepted, q)` returns immutable `SubmissionTrace`.
  Exact caption bytes are idempotent. Repeating the same caption with different
  acceptance/score is a conflict, not silent rescoring. `lookup(caption)`,
  `history`, `pixels`, `pixel_count`, and `snapshot()` expose local state only.
- `calibrate_pairs(pairs, config, embed, *, heldout_fraction=1/3, seed=177)` and
  `python3 -m gpu.ny_caption_pixels calibrate ...`: local evaluator-only labeled
  pair calibration, never arm outcomes or a reference-membership count.

`gpu.ny_caption_game` exposes:

- `Contest(contest_id, canonical_scene, image, split="agent_development")` and
  `DevelopmentManifest(contests, reserved_final_contest_ids=())` frozen
  dataclasses. Exactly three distinct development contests; no FINAL mode.
  `DevelopmentManifest.from_mapping` accepts the minimal projection documented
  below, not a historical-caption dataset. Main verifies image hashes and
  projects Ampere's data manifest; the game never opens image files itself.
- `GameConfig(tau, visual_call_limit=100, caption_word_limit=50,
  question_token_limit=128, visual_response_token_limit=256,
  transport_retries=2, max_submissions_per_contest=10000)` frozen dataclass.
  Tau is explicit; these ceilings cannot be increased past the specified caps.
- `JudgeResult(scene_fit, q)` and `VisualResult(observations, uncertainty)` are
  frozen dataclasses. Inject `judge(scene, caption) -> JudgeResult`,
  `inspect_provider(image, question) -> VisualResult`, and
  `count_tokens(text) -> int`. No reasoning, arm, history, references, or scores
  enter provider arguments. Main owns frozen provider instructions, models,
  tokenizers, image loading/hash verification and LOCAL Qwen transport adapters.
  No gateway transport belongs in this integration.
- `CaptionGame(agent_id, lane, manifest, config, pixel_config, *, embed, judge,
  inspect_provider, count_tokens, same_joke_verifier=None)`, any nonempty lane
  identifier (current Main lanes: `PARENTED`, `UNPARENTED`). Each instance owns
  separate archives, history, budgets and cache.
- `game.inspect_image(contest_id, question) -> dict` and
  `game.submit_caption(contest_id, text) -> dict` are the child tool endpoints.
  Errors are explicit structured results without invented observations.
  Submit success reports `accepted`, `q`, `scene_fit`, `status`
  (`new_pixel`/`repeat`/`rejected`), `pixel_id`, `pixel_count`,
  `matching_caption` (only this child's representative), and `replayed`.
  Exact submissions reuse the first result without scoring or counting again.
- `TransportError` is the adapter's explicit retryable exception. At most two
  retries (three attempts); exhaustion returns `transport_exhausted` with
  `pause_required=true`. Other exceptions never become visual observations or
  acceptance decisions. Cache hits still charge a logical visual call and
  question/context tokens. `snapshot()` is for Main's private persistence,
  never a parent-to-parent shared transcript.

Calibration inputs are `LabeledPair(pair_id, contest_id, scene, caption_a,
caption_b, labels, label_source="missing", group_id=None,
spotcheck_labels=None, labeler_id=None, labeler_revision=None)`. `labels` and
optional `spotcheck_labels` map `coarse`/`primary`/`fine` to booleans or null.
`label_source` is `llm`, `automatic`, `human`, `synthetic` or `missing`. Human
spotchecks override only non-null labels for their own pair/resolution; a small
spotcheck never discards the remaining automatic labels. All scoring reports
remain provisional. A missing human panel is informational, not a Stage 1 gate.
Pairs are held out by whole contest/declared scene group. Threshold selection
uses only the training labels and minimizes balanced FPmerge/FNsplit error,
jointly constrained to coarse <= primary <= fine. Both classes must exist in
training for each emitted resolution; absent evidence is never filled with an
invented threshold. Initial config thresholds are ignored by calibration.

`calibrate` consumes local JSON pairs, config and precomputed vectors only; it
does not load models or import adapter/plugin code. Vector keys are
`embedding_key(scene, caption)`. See `README.md` for complete commands and
limitations. Missing actual encoders/judges are Main/Ampere integration work,
not evidence that the synthetic fixtures validate scoring.

Minimal manifest projection:

```json
{
  "mode": "DEVELOPMENT",
  "development_contest_ids": ["dev-a", "dev-b", "dev-c"],
  "reserved_final_contest_ids": ["reserved-a", "reserved-b", "reserved-c"],
  "contests": [
    {"contest_id": "dev-a", "split": "agent_development", "canonical_scene": "Image-derived facts.", "image": "opaque-local-image-handle-a"},
    {"contest_id": "dev-b", "split": "agent_development", "canonical_scene": "Image-derived facts.", "image": "opaque-local-image-handle-b"},
    {"contest_id": "dev-c", "split": "agent_development", "canonical_scene": "Image-derived facts.", "image": "opaque-local-image-handle-c"}
  ]
}
```

This worker writes only its two core modules, their two CPU test files and this
directory. Main handles runner/parent/visual transport; Ampere handles
data/judge. No historical external caption reads, model/provider calls, GPU
jobs, final orchestration or scientific outcome claims are authorized here.
