# Stage1 DATA/JUDGE integration

Owner: DATA + JUDGE sidecar. Rohin161 and `../CURRENT_BUILD_RULES.md` override Revision 5 of
`research_notes/forwarded/final_run_2026-09-17/AGED_AGENT_CLONE_EVALUATION_AND_PARENTING_HANDOFF.md`.
Earlier three-arm/six-condition launch plans are superseded. This is Stage1
development, not FINAL orchestration or a scientific outcome.

## Rohin161 override

Rohin161 supersedes the lane/final-scoring details of rev5: DEVELOPMENT has two
learning lineages, PARENTED versus UNPARENTED, with the same sleep recipe/task/
tools/nominal token budget and matched sleep counts. FINAL has parent-free
sleep-learning in both lanes; Main owns the carry-state decision. DATA/JUDGE
interfaces are unchanged. Visual inference must be local Qwen, never hosted.
Human panels are optional rather than a blocking requirement. Held-out real
ratings, automatic challenge tests and a second blinded local-model comparator
support PROVISIONAL development scoring, not human-validated claims.

## Implemented CPU interfaces

- `gpu.ny_caption_data`: bounded public retrieval; immutable revision/file pins;
  contest joins and rating checks; five disjoint whole-contest pools; private
  evaluator manifests and a separate caption-free DEVELOPMENT packet.
- `gpu.ny_caption_judge`: canonical scene/caption input, smoothed three-class
  targets, capped vote weights, pretrained-encoder training, held-contest
  calibration/validation, separate scene fit and error-audit interfaces.
- Only metadata counts, artifact paths/hashes and blockers are public handoff.
  Historical captions and FINAL identities/images/ratings stay evaluator-private.
  Contest 530 is evaluator-training-only due to Main's recorded preview exposure.

## Authority and current blockers

- Local code/tests and at most 2 GiB of public source/dataset downloads are
  authorized. No credentials are changed. No GPU/model/provider call is made.
- Training requires Main's exact slot, budget and capacity admission; the CLI
  must refuse without that binding. No saved trained checkpoint exists yet.
- Fresh image-only descriptions must be independently produced from pixels;
  dataset canny/uncanny text is not silently adopted as image-only provenance.
- Human acceptance/scene-fit labels are not yet supplied and are not a Stage1
  blocker under Rohin161. Automatic-only calibration is provisional, never
  human-validated. Tau has no automatic 0.5 fallback. FINAL release and final
  claims remain deferred.
- The children's frozen Qwen base/LoRA-only learning invariants are unchanged.
  A separate pretrained text encoder for the evaluator does not replace a child.

R172 B5/B6 code is frozen during Rawls's rereview and is not edited here.

## Earlier 105-test handoff (preserved evidence)

`API.md` documents exact Bacon producer-receipt and Main judge/scorer interfaces.
`TRAIN_CONFIG_TEMPLATE.json` proposes parameters but remains unready: the
successful preparation3 manifest has no attached image-only descriptions and
no local pretrained model manifest is supplied. It is not an admission.

`evidence/CPU_TESTS_20260917_v2.txt` records 105 passing synthetic CPU tests,
including privacy/pool restrictions, producer and row hashes, smoothed targets,
calibration without a tau fallback, scene-fit separation, challenge diagnostics,
checkpoint pin checks and refusal before model imports. This is not receiving
Torch/model proof or actual scoring validation. The comparator input/import
contract exists; separate admitted local Qwen inference is still outstanding.

## September17 11:21PDT continuation

Current source has122 passing local tests (10.48s) and122 passing actual node4
receiving tests (1.70s). The bounded receiving model proof passes in8.23s with
two CPU model loads, one synthetic optimizer step, no CUDA initialization and
no saved judge. Exact evidence is `evidence/NODE4_V1_RECEIVING_CPU_PROOF.json`.
The actual receiving model manifest and loaded-runtime hashes now exist; this
supersedes earlier missing-package/pretrained-dependency status, not earlier
receipts. GPU training has not run.

A source-hash/seed-selected48-image development judge plan uses only the frozen
train/dev pools:32 train and4 each for model selection, probability calibration,
thresholding and a disjoint untouched dev audit. Locked judge validation and
FINAL remain unused. The ordinary19-image agent-development packet is unchanged
and disjoint. `DESCRIPTIONS_REQUIRED_20260917_v1.md` gives the exact missing
local-Qwen bundle path and schema. Zero descriptions have been invented.

The original105-test WIP source is byte-preserved in
`private/PRESERVED_WIP_105_TESTS_20260917.tar`. No learner, R179, R176, shared
venv, credentials or coordination file was changed. The next real training run
requires the actual48 descriptions, lawful receiving data assembly and a fresh
physical2-only finite admission. No human panel or new review queue is added.
# Rohin167 actual development training — September17 2026

Classifier scene input now has an explicit, judge-only released-data policy:
`R167_RELEASED_CANNY_LOCATION_ENTITIES_JUDGE_ONLY_V1`. It consumes only the pinned
`gpt4o_description/train.jsonl` factual projection. The Qwen game/V-tool policy
is unchanged. Released-description provenance is not relabelled as new local
Qwen generation or independent pixel verification.

- Actual run: node4 physical2, strict systemd target kernel minor1 plus ctl/uvm,
  seven foreign minors denied. Receiving root ends `released_all_v4`.
- Actual model load/start: 2026-09-17 18:59:49.810698UTC; first optimizer updates:
  18:59:50.422559UTC. PID3941679/startticks23974474.
- Dataset eligible joins:180 fitting contests,1,041,036 available raw retained
  fitting rows. Sampling selects34,560 rows,64 per quality band per contest.
  Fitting performs at most2,000 sampled batches of16, not all-row epochs.
- Registered-dev whole-contest partitions:19 model selection,13 probability
  calibration,7 threshold selection,6 independent development audit. Sampled
  rows respectively1,216/832/448/384. Locked validation and FINAL not consumed.
- Missing joins:82 fitting/11 dev contests; no malformed selected descriptions.
  Neither released validation/test descriptions nor missing scene facts were
  substituted. Original48 candidate, all prior manifests and failed receiving
  attempts remain unchanged.
- Exact safe proof: `evidence/RECEIVING_V4_OBSERVATION_1789671611293554849.json`.
  Step100 results are selection-only, not independent calibration/audit.
- `SIMILARITY_TRAIN_HANDOFF.json` is ready:180 train-only contests partitioned
  into144 fitting/36 calibration, before caption or label reads by that worker.
  It does not require the trained judge; no public caption texts or IDs.

Receiving repair history: v1 omitted a historical test-harness dependency
(133pass/6 missing-file failures, no GPU). v2 proved strict confinement but
incorrectly assumed the host NVML index survived confinement (no model load).
v3 admitted correctly but rejected Torch's exact UUID without the NVML prefix
(CUDA property initialization, no models/optimizer steps). v4 fixes only these
verified runtime compatibility issues, preserves identity checks, and passes
148 local plus148 receiving CPU tests. There was no in-place attempt retry.

The earlier description-waiting notes below are historical. Rohin167 removed
that blocker for classifier training, not for the separate visual tool.
