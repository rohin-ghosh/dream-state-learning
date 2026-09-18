# R167 / R152 sidecar — live replay inventory and session proposal

## Result (September 17, 2026, 07:54–07:55 UTC)

**21 previously identified native learners freshly confirmed in this bounded inventory: free 14; reread/select 4; parent-guided 2; none 1.** These are live native PID/start-tick/argv plus hash-bound active-plan observations, not parent-process counts or a complete fleet census. “Reread” and “select” are labels for the same implemented `reread_select` variant, not two independently implemented replay algorithms.

| Variant | Confirmed live threads |
| --- | --- |
| `free_distillation` (14) | C1, C2, C3, C4, C5, R158 parented_learning, brain_free, classroom_brain, creative_free, pilot, repo_reader, run1, support_free, teach_replay |
| `reread_select` (4) | classroom_creative, creative_reread, creative_select, teach_perception |
| `parent_guided_distillation` (2) | brain_guided, teach_parenting |
| `no_distillation` (1) | classroom_support |

All selected plans have two ordinary segments per sleep. Free, reread/select and parent-guided use an additional native pre-sleep child generation; no-distillation omits that extra generation, **not ordinary sleep/training**. No-distillation is not a frozen/no-learning control. Reread/select is a prompt asking for verbatim selection, not parser-enforced extraction. Parent-guided changes the invitation to consult parent guidance; it does not make parent messages direct targets.

### Per-thread process/plan pins

Pins below are 12-character abbreviations; metadata receipts retain exact full hashes and paths. Source pin is the process-located experiment-binding stream source, or legacy native source when the old stream has no variant registry. Legacy untagged plans are classified from the actual fixed native invitation and its plan validation, not inferred from thread names or current checkout defaults.

| Thread | Node / live native PID | Effective replay | PLAN / source pin |
| --- | --- | --- | --- |
| C1 | ovx3 / 2578597 | free_distillation (default) | `078df2c0239e` / `617e3ecd0bb4` |
| C2 | ovx3 / 2610332 | free_distillation (default) | `0059733c7986` / `617e3ecd0bb4` |
| C3 | ovx3 / 2525436 | free_distillation (default) | `9ee3949087ce` / `617e3ecd0bb4` |
| C4 | ovx3 / 2619696 | free_distillation (default) | `0303de16d68a` / `617e3ecd0bb4` |
| C5 | ovx3 / 2578735 | free_distillation (default) | `486fafdc7958` / `617e3ecd0bb4` |
| R158 parented_learning | a40r / 530635 | free_distillation | `0e857b2c39e0` / `617e3ecd0bb4` |
| brain_free | ovx2 / 1172314 | free_distillation (legacy fixed) | `3ed70172ee87` / `106be5bd8bde` |
| brain_guided | ovx2 / 1029925 | parent_guided_distillation | `ba3b4cc2dada` / `617e3ecd0bb4` |
| classroom_brain | a100 / 1072657 | free_distillation | `9357f2c195d3` / `617e3ecd0bb4` |
| classroom_creative | a100 / 1316795 | reread_select | `77a236b7b660` / `617e3ecd0bb4` |
| classroom_support | a100 / 1997023 | no_distillation | `afdbddbe2fbe` / `617e3ecd0bb4` |
| creative_free | ovx2 / 1098298 | free_distillation | `5c7f4a952dbc` / `617e3ecd0bb4` |
| creative_reread | ovx2 / 1266769 | reread_select | `cde51871c4eb` / `617e3ecd0bb4` |
| creative_select | ovx2 / 1202149 | reread_select | `797e8dc0ac54` / `617e3ecd0bb4` |
| pilot | ovx3 / 2736739 | free_distillation (legacy fixed) | `565efd26002b` / `d3cbd3b0053f` |
| repo_reader | ovx3 / 2611440 | free_distillation (legacy fixed) | `cfef30fca289` / `7626d13974a7` |
| run1 | ovx3 / 2803009 | free_distillation (legacy fixed) | `283468db6a48` / `d3cbd3b0053f` |
| support_free | ovx2 / 1347090 | free_distillation (legacy fixed) | `7307bafb8779` / `106be5bd8bde` |
| teach_parenting | a100 / 1025183 | parent_guided_distillation | `22ca67b931ca` / `617e3ecd0bb4` |
| teach_perception | a100 / 2409681 | reread_select | `8c6654d6d882` / `9ac05f14009f` |
| teach_replay | a100 / 2197976 | free_distillation | `827829405ae6` / `617e3ecd0bb4` |

## Do not confuse parents, storage roots and learners

- Reused R166 process inventory; only its known native PIDs plus R157's known repo_reader PID were queried. No full journal reread or new process census. The first pass preserved errors for a per-node byte cutoff and legacy sources lacking the newer variant registry; a narrow follow-up resolved classification against the actual old native source. These were observer limitations, not learner failures.
- R166's old `support_none`, `creative_none`, frozen-control and pending-frozen parent controllers are **not** evidence those corresponding native learners are live. They are excluded from this confirmed-live variant inventory. An old parent output/config is neither a live learner nor proof of retirement; this sidecar does not certify any process retired or dead. In particular, classroom_support is the positively confirmed live no-distillation learner; similarly named stale support_none is not substituted for it.
- Repo_reader **is now positively confirmed** at native PID2611440. Its hash-bound PLAN retains original root `/localhome/local-rohing/orch_r136_repo_reader_20260916_attempt1/run1`, while the prior R157/R166 storage/parent binding points at `recovery_r154_saved30_20260916_attempt2/run1`. Preserve both provenance fields; do not infer a new root, rewrite the plan, or use the PLAN's original root alone as a checkpoint locator.
- Frozen R165 boundary handling, unparented arms and kernel threads are outside this refreshed set. No GPU query, model load, source/training edit, parent dispatch, process control or checkpoint payload read occurred.

## Proposed one-off “good-behaviour replay session” — NOT executed

Use **one existing scheduled pre-sleep opportunity**, initially on a free or parent-guided live arm after Main's policy/intake decision. Do not modify its frozen invitation, add a generation, force a sleep, duplicate a training row, replace recorded child text, or increase its presentation count. For the no-distillation arm, do not silently bolt on the extra session: that would change its control; any comparison must explicitly retain the control or receive separate scope.

1. Select one concrete **already observed child behavior**, supported by that child's own TRAIN record and the actual feedback it saw: e.g. checking a claim against a real tool receipt and correcting the claim. Credit the action, not fluent self-report or a held score. Record the original child/feedback references and hashes. If the old attempt is outside current visible context, defer rather than injecting raw history or fabricating recall.
2. Proposed single ordinary attributed TRAIN-parent turn, within the existing parent cadence/object budget: **“Earlier, you checked your claim against the actual result and changed it. Revisit your own attempt: what did you expect, what did you observe, and what would you keep or change next time? Use your own experience and words, not mine; leave uncertain parts uncertain.”** Substitute only the first sentence's action when justified by actual evidence. This is an optional one-off invitation, not a recurring answer template or a demand for agreement.
3. Let the existing runtime generate the child's response and native pre-sleep segment normally. Train only the runtime's eligible **own-generated child target tokens**, with their exact recorded conditioning prefix/token IDs/masks. Parent cue, environment invitation, tool feedback and surrounding context remain masked as direct targets. No parent-written “corrected retelling” is inserted as child output. Own-generation provenance alone does not guarantee substantive reflection or prevent copying: if the child merely quotes the parent, record that limitation and do not count it as successful behavior replay or silently rewrite/filter its targets.
4. For `reread_select`, preserve its original verbatim-selection invitation and evaluate whether the child actually selected its **own behavior/evidence**; do not relabel parent quotation as the child's successful action or claim enforced own-only extraction. A guarantee excluding such copied text would require a separately reviewed mechanism, not this metadata sidecar. Do not turn selection into free rewriting by changing the native invitation.
5. Observe only ordinary TRAIN evidence across the next **three completed sleeps**, without forcing completion: did the child independently repeat the concrete action on a new relevant object? Mark missing opportunity, uncertainty or relapse explicitly. Corrected-retelling provenance and next-sleep survival are separate claims; none is established here.

### Exposure accounting required if Main later runs it

Actual changes in this sidecar: **zero parent turns, zero extra generation calls, zero optimizer updates, zero replay presentations.** The proposal is not an exposure-neutral claim: changing the parent's visible cue changes the child's conditioning and likely generated content, even if schedule and update counts stay fixed. Re-generating or selecting the same own passage creates additional semantic exposure through new child targets; document that rather than saying “no change” because no optimizer knob moved.

For any later attempt record: thread/native/config/plan/source pins; credited child and observed-feedback references; cue hash and verified rendered-parent reference; native variant/invitation; target segment hashes and token counts; planned versus actual generation/update/presentation counts from existing receipts; NEW versus rehearsal exposure for each affected own segment; unchanged anchor mixture and optimizer settings; old own passages repeated/selected when identifiable; exact completed sleep/checkpoint references; and survival outcomes/opportunity limitations for the next three sleeps. Never infer exposure counts from thread names, use held scores to select examples, or overwrite the ordinary schedule/failures. Any extra session, row replay, multiplicity or masking change is an explicit experimental exposure delta requiring Main's separate decision.

## Raw-unparented siege/war-plan era locator

**Not located in the reused R166 metadata.** The retained files contain no `raw_unparented`, `siege`, `war-plan`, `sleep_000008` or `sleep_000025` references. No guessed root or sleep8–25 checkpoint path is offered. Main's direct root inventory remains authoritative; no duplicate root scan, journal archaeology or held/eval read was performed here.

## Metadata receipts

`LIVE_REPLAY_METADATA.json` preserves the first refresh, including observer errors; `VARIANT_CLARIFICATION.json` preserves the narrow resolution and legacy-source lines; `BINDINGS.json` pins them and the reused R166 input. Counted remote reads are 6,708,863 bytes (about 6.40 MiB); the sum of declared per-pass read budgets is 20 MiB. Only this inventory and bounded metadata receipts were created, under `research_loop/workers/r167_object_survival/`. No changes were made to R166 evidence or another worker's scope.

## Actual observed TRAIN carry — September 17, 2026 append

This supplements, not replaces, the 07:54–07:55 live inventory. One bounded completed-checkpoint sample per selected thread is **not** a causal survival comparison or a new fleet census. No held/eval results were read.

| Variant / thread / sleep | What actually appears in saved TRAIN carry | What is NOT established |
| --- | --- | --- |
| Free / pilot / 38 | Compaction retains a Python-object discussion, including a claim that code/syntax is correct; malformed nested quotes, `data/get`, `resultl` and indentation remain. | **Object retention only; NOT verified good behavior or correct code. Do not boost it as a positive target.** |
| Free / C1 / 31 | Latest compaction is exactly `{}`. Ordinary rows90/91 retain the Elara/map/treasure narrative inside write-workspace JSON. | Empty summary is not substantive object carry. Generated write syntax is not actual successful file creation; some JSON is malformed. |
| Reread/select / creative_reread / 38 | Chinese narrative retains a woman, career worries and chrysanthemum petal; repeated paraphrases and mixed-language/corrupted words appear. | Neither verified verbatim extraction nor improved attention/control. |
| Parent-guided / brain_guided / 35 | Epoch/batch/update-frequency concepts and formulas survive; text claims actual updates7/4 and correctness, then proposes implementation. | Those are child claims, not separately observed execution. No verified strategy success. |
| None / classroom_support / 38 | 122 eviction operations and no compaction operation; latest ordinary rows repeat multiplication/manual-check requests with role/tool-looking text. | No new distilled summary; apparent peer/tool prose is not real communication or tool success. |

Pilot receipt `OBSERVED_TRAIN_CARRY.json` SHA `5437d8ea858884f9fac9c30bac9593b0cb134bfa1c279cbe1476a23fb9b13700`: 2,230,884 bytes read. Its `compaction_summary_count=0` was an initial observer search of raw events; the actual summary is retained under `last_operation[0].summary`. Do not interpret the observer field as no compaction. Sleep receipt reports159 updates/49,351 own-token exposures; this is the ordinary historical sleep, not R168 activity.

Variant receipt `VARIANT_TRAIN_CARRY.json` SHA `9abd8f77387f3b0c5a3661fc9921444e496d666332fd43ea6f6c1eeb54bc9bf4`: 13,937,307 bytes read. Exact COMMIT/record/source paths and hashes are retained there. These two carry passes add16,168,191 bytes to the earlier inventory reads, totaling22,877,054 bytes for this R167 inventory/carry series (excluding separate R166 work). All original observer errors/receipts remain preserved.

The earlier good-behavior-session proposal remains **conditional**: this sample has not established a qualifying good attention action. R168's later one-row×four object-dose proposal is separately labeled experimental exposure, not the earlier exposure-neutral schedule. See `research_loop/workers/r168_targeted_replay/PLAN.md`: the C1 whole-row selection is currently blocked rather than silently boosting wrappers/scaffolding or calling malformed code correct. Parenting/retelling rollout must not wait for this sidecar.

## C1-only refresh — September 17, 2026, 08:26 UTC

The fleet table remains an **07:54–07:55 snapshot**, not a re-certified current21-thread census. This refresh checks only C1 and does not infer the other threads' current liveness or new carry.

| Evidence | Actual observation | Claim boundary |
| --- | --- | --- |
| C1 parent, 08:26:23 | Newest observed successor-parent attempt96 is SILENT; no spoken message. SOURCE's96-response/31-sleep counts describe its earlier capture. | Parent rollout/STARTED is not rendered delivery. Copied attempt93 is predecessor history. No fresh good retelling attributed to parenting here. |
| C1 native, 08:26:48 | Original PID2578597/start14835459 and R157 source cwd still match. Head3483 is UPDATE, optimizer_step2927. | Live native continues; this one-record read does not establish a newer completed compaction, full chain validity or adoption of a new invitation. |
| Invitation activation2 | Preserved Main execution notebook/status reports pre-handoff missing-test-file failure; no successor LOADED/adoption in that attempt. | Separate from parent delivery. No R168 source hook or extra dose was smuggled into activation2. |
| R168 target | Historical17/33/43/80 and empty/sleep-only rows not admitted; wait for fresh exact own evidence after actual Main/Mendel delivery. | Zero selected rows, extra live presentations or extra live updates; one-row×four remains prospective only. |

Bound receipts and next eligibility checks are in `research_loop/workers/r168_targeted_replay/WAITING_AFTER_MAIN_0824Z.md`. This refresh reads one959-byte remote journal payload, no child targets, checkpoint tensors or sealed/eval data. Old carry samples and rejected/failed receipts remain intact; no background monitoring or parent-rollout hold was started.
