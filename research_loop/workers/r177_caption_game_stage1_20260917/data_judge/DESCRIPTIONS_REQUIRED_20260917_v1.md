# Exact remaining vision input — R177 development judge

**Missing actual file:**
`research_loop/workers/r177_caption_game_stage1_20260917/data_judge/incoming/LOCAL_QWEN_JUDGE_DESCRIPTIONS_V1.json`.
This file has deliberately not been fabricated or populated with placeholders.
No local-Qwen description execution is claimed.

## Fixed image-only work packet

`IMAGE_TASKS_DEVELOPMENT_JUDGE_20260917_v1.private.json`, SHA
`d9cb98a6df0d3e9739fb547604603b0ca4d0ce0122f6dc15de7f7ca9771752c0`:
48 tasks, chosen before reading any real caption or rating rows in this
continuation. Each contains only a contest key, pinned image reference and
factual image-only policy. Do not print contents or IDs to Main/parents.

The private plan is `private/DEVELOPMENT_JUDGE_PLAN_20260917_v1.json`, SHA
`b46eeac4499b0908eb680750c42b7cb9ae1aaa1533e2140ff3d4c1c4d3e85659`.
It selects 32 judge-training contests and four each for model selection,
probability calibration, threshold selection and an untouched development audit.
All four held subsets belong to the already frozen judge-dev pool. The audit
is predeclared, disjoint from threshold selection and never selects checkpoints,
temperature or tau. Whole near-duplicate scene groups stay together. No frozen
pool is reassigned; original locked judge-validation and FINAL are unused.

The original 19-task agent-development packet is still a separate unchanged
image-only packet for the game. Those 19 contests are **not** evaluator training
inputs. Producing their descriptions does not supply the 48 judge descriptions.

## Required bundle schema

```text
{
  "schema": "NY_LOCAL_QWEN_DESCRIPTION_BUNDLE_V1",
  "source_manifest_sha256": "4d17031bae93bb83e3f89109e4acb5fc28dfa79706bb47b27c6b0e5fe96bb45d",
  "task_packet_sha256": "d9cb98a6df0d3e9739fb547604603b0ca4d0ce0122f6dc15de7f7ca9771752c0",
  "descriptions": [
    {"contest_id": "copied from the private task", "scene": "actual local-Qwen factual output",
     "producer_receipt": {"path": "actual accessible producer receipt", "sha256": "actual SHA256"}}
  ]
}
```

Exactly one entry for every requested task; no missing, duplicated or additional
contest. Each producer receipt binds the exact task image, policy, output text
hash and actual local frozen-Qwen model manifest. The complete producer schema
is in `API.md` under Immediate handoff to Bacon. Scene text is factual only,
40–8,000 characters, with no historical-caption, uncanny or parent-history input.
The requested image is the sole factual source; no hosted visual fallback.

Receipts and their model manifests must be accessible to the assembly process at
the supplied paths and match their hashes. Preserve original execution receipts
and explicitly bind transported references; do not invent a receipt or silently
claim that metadata alone proves inference, blindness or image accuracy.

Use `gpu.ny_caption_data.attach_description_bundle(source_ref, packet_ref,
bundle_ref, NEW_MANIFEST_PATH)` to produce the new description-attached manifest.
It leaves preparation3 and all previous attempts untouched. Then write a new
config replacing only the proposed config's unready `data_manifest` reference.
`development_source_manifest` and `development_plan` remain the exact original
bindings. Receiving asset-path assembly must preserve the selected source bytes
and producer links; this CPU stage has not copied real caption data or images.

## What does and does not need vision

- No vision needed: pinned source/model acquisition, split/group/identity checks,
  rating validation and soft-target plumbing, synthetic CPU model loading,
  forward/backward checks, package proof, finite config/source staging. Done.
- Vision required: canonical factual scene input for every selected real training,
  calibration and audit example; scene swaps and the independent scene-fit head.
  Zero of the 48 actual descriptions is attached here yet.
- Existing human rating counts are lawful evaluator labels for the selected
  train/dev contests; they are not image descriptions. Existing dataset-generated
  descriptions have not established the required local-Qwen image-only custody.
  Neither caption-only fitting nor invented scene text is substituted.

Once those inputs arrive, the proposed initial run is bounded to400 optimizer
steps,1,800seconds maximum, node4 physical2 only. It still needs exact receiving
data/source/config pins and fresh physical2 capacity/lease admission. The Builder
CPU gate exists; no human panel or new review queue is added. No actual judge
metrics or trained checkpoint exist yet. Future metrics are exposed only through
`NY_SAFE_PUBLIC_SCORING_ERROR_REPORT_V1`, without captions or contest IDs.
