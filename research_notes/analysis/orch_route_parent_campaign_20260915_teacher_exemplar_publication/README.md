# Teacher exemplar publication — separately labelled collection

- Arm: **TEACHER_DISTILLATION**, 8 math + 8 route prospectively frozen TRAIN tasks, one single-attempt provider.
- Actual response identity: `openai/openai/gpt-6-astra`; 16/16 completed. Final-answer checks 16/16; method/proof correctness is not independently verified.
- This is collection only: no learner fit, no mainline or ongoing-L1 ingestion, no child performance claim. Teacher prompts remain excluded from targets.
- Raw prompts/responses/errors and private checks remain on node3 under the native root recorded in `LINEAGE.json`. `NODE_RAW_INVENTORY.json` contains only filenames, sizes and SHA-256 values.
- `RESULTS.json` contains bounded call metadata, usage and reductions, never task text, answers or teacher response bytes.
- `VERIFICATION.json` records fresh remote and local snapshot checks plus five CPU unit tests. Source hashes match the original pre-provider receipt.
- Publish only paths explicitly listed by `MAIN_STAGE_MANIFEST.json`; never recursively stage the old `orch_route_parent_campaign_20260915_teacher_exemplar/` tree.
- The old local untracked buffer has not been pruned. Historical collection location is not misrepresented as native generation. No canonical route life or provider broker was changed.
