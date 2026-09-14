# SEQ264 — rich action-first V3: header compatibility, no fit

2026-09-14, Builder/Schrodinger. All four TEACH-only processes are terminal.
**372 actual native calls; 64 attempted episodes; 56 action-complete episodes;
336 UNREVIEWED candidate turns in each of three matched views. No fit and no
content promotion.** Eight episode failures remain in the evidence. All four
native stages report COMPLETE; this is not an all-episodes or content pass.

## Prospective change and fixed controls

Executed source: `80368f94b3b97bb5ef92476a0885f26282d9e6a4`.
Protocol: `2026-09-14_rich_action_first_v3_collection_protocol.md`, SHA256
`a45be0236103a759de40473a81029b1568a035220c544aa96bbc18a3cbc81aef`.
CPU/actual prepare packet was published as `7434b4a4` before launch; the
launch path checked successful publication before invoking guards. Live PID
handover was published as `f07866f5`. All four actual prepares used zero
model calls. The 50 focused CPU tests passed in35.723s; shell syntax passed.
All four original V1 and four V2 actual teaching documents replay unchanged.

Only explicit `ACTION_FIRST_V3` accepts the additional exact prefix
`RATIONALE: `, alongside `RATIONALE\n`, with one exact `\nACTION\n` delimiter.
Raw text, command grammar, character/UTF-8 action spans, message validation,
terminal/token bounds and real environment execution remain intact. No command
scan, missing-character repair or prose-to-action substitution was introduced.
V1/V2 defaults, outputs and replay remain unchanged.

The four original shard EXPOSE collections are reused through the unchanged
V2 loader. Each shard requires all five source worlds ready; only its four
TRAIN worlds feed teaching. No PROBE teacher inputs or targets, new EXPOSE,
critique, baseline, retention panel, fit or retry. V2's ACTION_FIRST_PROTOCOL,
generation configuration/seed and same parent state are reused:
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
All four readonly state and frozen-base checks pass.

## Failure-inclusive execution

|Shard|Native calls /96|Action-complete /16|Rows per view|Phase wall seconds|Finished UTC|
|---|---:|---:|---:|---:|---|
|0|93|14|84|639.099|20:02:46.493|
|1|96|16|96|634.472|20:02:41.906|
|2|92|12|72|608.634|20:02:16.062|
|3|91|14|84|656.132|20:03:03.545|
|All|372 /384|56 /64|336|2538.337 summed|All terminal|

Action-complete still means all six planned commands in order, four actual
READs, two committed ROUTEs, and arrival at the final goal. Actual goal
arrivals are58/64: two five-command/three-read arrivals are **not** complete
curriculum episodes and contribute no candidate rows. Do not substitute the
looser goal-arrival count for the declared six-command gate.

All16TRAINworlds contribute at least two complete episodes. Nine worlds have
all four tasks complete. Using matched display-order goal pairs (tasks0&2,
tasks1&3), strict action completion covers24/32 pairs across15/16 worlds.
These are coached execution coverage counts, not teacher-free probe scores
or content-qualified coverage.

|Shard/world/task|Native calls in failed episode|Preserved failure|
|---|---:|---|
|0/A/2|5|Three reads, a committed route, then repeated port invalid at new CURRENT.|
|0/D/0|4|Malformed address in actual action: `E_WPTDWZJQM`; no repair.|
|2/A/0|5|Three reads, a committed route, then an invalid subsequent route.|
|2/A/3|5|Three reads, a committed route, then an invalid subsequent route.|
|2/B/1|5|Goal reached with only three reads; fails six-command plan.|
|2/D/0|5|Goal reached with only three reads; fails six-command plan.|
|3/B/1|3|Plain `READ EVENT E_Q7W3G372HJ` lacks required rich envelope; rejected.|
|3/D/1|4|After three reads and an off-plan route, next coaching failed `routing_source_must_already_be_public` before generation.|

The final case has a preserved fifth actor-callback attempt but no fifth
native response. Thus the traces contain373 actor invocations and372 actual
native calls. The unsourced next instruction was not sent to the model.
All raw failed outputs, execution errors and partial public histories remain
in the capsule. There are zero native generation errors, nonterminal native
responses or truncations. Two captures have parser validation errors; the
other failures arise from actual transitions, the strict plan or source gate.

## What the compatibility comparison does and does not show

All64 first-turn student prefixes, coached prompts, source hashes **and raw
native responses** exactly match their V2 counterparts. V3 newly permits the
62 exact colon-prefixed first responses that V2 rejected. Later histories now
continue from real executed actions. Across all372 V3 outputs the prefix
counts are62colon,309newline,1other. The malformed address and plain-command
failure above remain failures: this was not a general output-repair parser.

V2 remains closed at74calls,2/64action-complete,12candidate turns, and zero
content-qualified episodes. Main's8PASS/3FAIL/1UNRESOLVED and independent
6PASS/3FAIL/3UNRESOLVED turn reviews both exclude its two episodes; preserve
their marginal disagreements. No retrospective V2 passes or12-row fit.

V3 yields an executable candidate corpus after removing that particular
header incompatibility. It does **not** establish richer reasoning, rationale
truth, learning benefit, independent planning, transfer, clean ancestry or
H1/H2. V3 spent more calls because episodes continued; no equal-compute claim.
The 370 projected captures carry368missing-prediction-label and2unseen-public-
identifier diagnostics. These diagnostics are not semantic verdicts, and
optional label absence is not automatic content failure. Every candidate
remains UNREVIEWED, reviewed=False, fit_ready=False, rationale_truth_verified=False.

## Content review is unblocked, not completed

`gpu_artifacts_local/astra_rich_action_first_v3_terminal_20260914_attempt1/CONTENT_REVIEW_INPUTS.json`
contains **all56action-complete episodes and all336turns**, ordered by
shard/world/task/call. It follows the V2 packet layout: public student_prefix,
actual raw response, exact projection, call/source IDs and hashes; it also
includes relative native CALL file paths and file hashes. No coached messages,
source plans, PROBE cases or future observations are added. A scan against
all fixed PROBE identifiers finds none. Captured public history is unchanged.

Packet SHA256:
`b7e19b81e347ee0c0e89f97e669f32fd9bef8513067233ab1355962eb76bc92b`.
Shared content contract:
`3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b`.
Ramanujan owns substantive review of all turns; Main audits disagreements
and accepted samples. The primary makes no acceptance prediction and applies
no additional selector. No fit until that corpus/content decision is made.

## Evidence, compute and handover

Remote root `/tmp/astra_rich_action_first_v3_20260914_attempt1` on A100.
Launch requested19:52:06UTC; all four first scanner admissions clear and
native stages started19:52:07UTC. Guardian/native PID pairs by shard:
0:143147/143198; 1:143148/143214; 2:143149/143212; 3:143150/143206.
Each used its allocated physical GPU0–3 and exact UUID in the prelaunch
packet; live CVD values were checked. All four guards completed. A post-run
physical check finds GPUs0–3 at0MiB/0percent. GPUs4/5 were not touched.

Actual totals:209,921 prompt tokens,47,082 generated tokens including terminal
tokens,20,996 whitespace words. No missing token counts. Maximum prompt820
tokens and generation302tokens are within2048/512bounds. Summed phase wall
2538.337s is0.705094 A100-hours of phase-wall accounting (includes loading and
checks, not metered kernel time or a billing/equal-token assertion).

Local terminal archive:
`gpu_artifacts_local/astra_rich_action_first_v3_terminal_20260914_attempt1/terminal.tar.gz`
SHA256 `b8b9d7e1eb1b2bda37b602d6c6ea7f26e4b6362371803ce8c3e7edac8d3ca633`.
Extracted root:
`gpu_artifacts_local/astra_rich_action_first_v3_terminal_20260914_attempt1/extracted/astra_rich_action_first_v3_20260914_attempt1`.
Remote archive `/tmp/astra_rich_action_first_v3_20260914_attempt1_terminal.tar.gz`
matches the downloaded archive hash. Both contain all prepare/native/guard
files, CPU_REPLAY_CHECK.json and the review packet; the separately preserved
source archive/source directory are excluded from the terminal tar.

Source archive:
`gpu_artifacts_local/astra_rich_action_first_v3_20260914_attempt1/source_80368f94.tar.gz`
SHA256 `8671cda547e311be8d5a8fd4005b35aa5d3273cec99c06c988af1c182d18bb4b`.
CPU_REPLAY_CHECK.json SHA256:
`b09238260a5ea5600aa60c0ba4d37606186a257966955b3611968c63b4008e63`.
Frozen-source replay verifies every projected command, all matched candidate
rows, actual CALL messages/response/error joins, output inventories, state
receipts and metrics. Downloaded file hashes were checked again locally.
This is author-side internal replay, not independent tensor or content
authentication. The branch's next action is substantive review, not a rerun
or automatic fit. SEQ264 is published irrespective of review yield.
