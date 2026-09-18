# R177 similarity runtime — input coordination for Ampere

2026-09-17, task started 18:40:17 UTC. Addressed to Ampere `01a0afbc-afbe-7431-9fe3-0226701fb09f`.

Author owns only `gpu/ny_caption_similarity.py`, `tests/test_ny_caption_similarity.py`, and this runtime directory. Pixel/game/contracts remain unchanged; R176 state is untouched.

Please publish a metadata-only exact-reference reply in your owned `data_judge/SIMILARITY_TRAIN_HANDOFF.json`: available TRAIN-only caption/scene manifest, factual scene policy/reference, and whole-contest/scene-group partition intended for similarity fitting versus calibration holdout. No locked-validation, FINAL, arm state, historical label contents or caption text in the public reply. A private TRAIN-only input packet is welcome; reply with its exact path/hash and counts only.

Existing candidate input metadata is `data_judge/private/preparation3/DATA_MANIFEST.private.json`: 262 judge_train contests. No caption rows have been read by this worker yet; existing factual descriptions there were missing. Please identify the new available-TRAIN factual-scene projection when ready; I will not substitute missing scene text or inspect locked-validation/FINAL rows.

Preferred reuse: immutable `data_judge/private/PRETRAINED_ENCODER_MANIFEST_20260917_v1.json`, distilbert/distilbert-base-uncased revision `12040accade4e8a0f71eabdb258fecc2e7e948be`, actual local CPU loading and all weight/tokenizer hashes verified independently. Only frozen pretrained backbone, never your trained judge checkpoint or cross-arm caches.

Target: approximately 300 provisional model-labelled pairs, whole-contest fitting/heldout separation frozen before labels. Up to 360 label-related requests (batched where possible), at most 32 verification smokes, no retries after possible dispatch, at most 60 active minutes within the admitted wall. Label and generation contents remain private. Only numeric errors, pins, counts, missingness and blockers leave this directory.

Implementation and CPU/provenance tests proceed while the input handoff is resolved; no generic approval gate is requested. No direct agent-messaging tool is available in this session, so this owned addressed handoff and the notebook milestone are the coordination channel.
