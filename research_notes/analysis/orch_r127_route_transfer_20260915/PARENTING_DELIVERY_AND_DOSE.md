# Canonical TRAIN parenting delivery and dose through C4

Read-only reduction, September 15, 2026. Native node3 root: `/tmp/orch_route_parent_campaign_20260915_canonical102`. This audit reads **GUIDED/UNPARENTED TRAIN C1–C4 only** and their training/source provenance. It does not read the new transfer assay, historical readout outputs, sealed FINAL, or parent evaluation data; it makes no model/provider/GPU/broker changes and does not gate evaluation.

## Bottom line

The historical contrast has verified parenting delivery—not just charged requests—and matched initial child, training tasks/order, available observations, update counts and row presentations through C4. **It is not token-exposure matched.** GUIDED receives more supervised child-target tokens, and its realized action trajectories differ. This supports describing the arms as parented versus unparented training trajectories, not isolating a specific feedback-learning mechanism or establishing transfer improvement.

## Initial identity, tasks and available observations

- Both first TRAIN stages and the shared initial source generator bind state `d13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f`, adapter file SHA256 `6f7546d334a6dd65c5a22dddeff2ee6eb42292373d79552df52a272f3aeab76f`, and recorded base state `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`. Initial adapter files were independently hashed; the complete base weights were not rehashed in this sidecar.
- The same **eight TRAIN tasks in the same order**, two per cycle, have identical initial public-message prefixes in both arms. Every cycle's input child matches its preceding saved sleep output; these are continuing weight lineages, not fresh seed restarts.
- Four exact TRAIN source collections, native `TRAIN-C0-W0` through `TRAIN-C3-W0`, each contain four accepted initial-child-written event records. Both arms use the same available store. All **32 GUIDED and 26 UNPARENTED actual READ feedback returns** checked equal the corresponding shared source bytes. Different numbers of reads mean *available* observations are matched, not realized experience trajectories.
- All 222 legacy encoded replay rows are byte-identical across the six actual fits. Source-file hashes match the original PREPARE manifest. No new evaluation task or observation was used to establish these checks.

## Parent delivery, not billing

| C1–C4 TRAIN quantity | GUIDED | UNPARENTED |
|---|---:|---:|
| Completed request→response bindings | 32 | 0 |
| `speak=true` responses / silent responses | 32 / 0 | 0 / 0 |
| Action-coach interventions present in subsequent actual generation input | 24 | 0 |
| Reflection-coach interventions present in actual reflection generation input | 8 | 0 |
| Action responses with private parent guidance in generation messages | 46 / 46 | 0 / 40 |
| Reflection generations with private parent guidance | 8 / 8 | 0 / 8 |

For each intervention, the completed queue response joins to the episode or SLEEP_COACH record. Actual captured generation messages equal the public prefix plus the recorded guidance; reflection inputs equal the neutral episode reconstruction plus the recorded private coach inventory. Repeated guidance in later turns is not counted as another intervention. These are input-delivery checks, **not evidence that the child understood, used, or benefited from each intervention**. Provider RAW_RESPONSE/model identity was not separately audited here.

UNPARENTED's LOADED receipts declare parent absence; its actual action and reflection messages contain no added parent segment, and its parent request inventory is empty. The historical `experience/COMPLETE.json` field `parent_free=false` appears in both arms because the frozen writer sets it from `phase == 'readout'`. It is not the authoritative parent-visibility measurement for TRAIN. That historical metadata is preserved, not relabeled.

## Actual masks and realized training dose

| Cycle | Updates G / U | Admitted new targets G / U | Presentations per admitted target | New supervised token presentations G / U |
|---|---:|---:|---:|---:|
| C1 | 0 / 0 | 0 / 0 | None; planned 4, no fit | 0 / 0 |
| C2 | 104 / 104 | 1 / 1 | 16 | 7,376 / 6,384 |
| C3 | 104 / 104 | 1 / 1 | 16 | 6,672 / 6,448 |
| C4 | 112 / 112 | 2 / 2 | 16 | 15,792 / 13,312 |
| **Cumulative through C4** | **320 / 320** | **4 / 4** | **64 new-target presentations each** | **29,840 / 26,144** |

Actual LOSSES row indexes and active-token counts agree with saved MASKS and DOSE_EXPOSURE, not merely planned recipe values. Each arm has **1,216 legacy-row presentations**, including 576 old-trajectory presentations, and **25,654 legacy supervised token presentations**. Total supervised token presentations, including legacy and target end-of-turn tokens, are **55,494 GUIDED versus 51,798 UNPARENTED**. GUIDED therefore has **14.1% more new-target exposure** and **7.1% more total supervised-token exposure**, despite equal updates and row-presentation counts. These counts describe label exposures, not unique knowledge, effective gradient magnitude, or wall time.

The eight admitted reflection rows across both arms satisfy:

1. Exact original reflection response/capture/episode bindings; neutral public prefix excludes the recorded private guidance.
2. All prefix and suffix labels are `-100`; the single supervised interval is exactly the child's re-encoded reflection plus end-of-turn token.
3. Native tokenizer-only checks verify the actual encoded prefix and supervised text. Full recorded private guidance strings and eight-word private spans are absent from admitted targets. No teacher answer text was substituted.

Two UNPARENTED C4 targets have different generated-versus-re-encoded token segmentation but decode to **identical original child bytes**. Their saved targets match canonical tokenizer re-encoding; this is lossless serialization, not altered supervision. No model was loaded to check this. The checks cannot rule out semantic paraphrases or influence from private guidance; that influence is part of the parented-child condition.

All eight rejected reflections remain rejected: GUIDED four `complete_reflection_required`; UNPARENTED two `complete_reflection_required` and two `reflection_not_answer_action_replay`. Equal admitted counts conceal different selection mechanisms and different generated content. C1 offers no new weight updates in either arm.

## Causal and measurement limits

- This is one continuing trajectory per arm, without independent training replicas. Same tasks/order and initial weights do not make trajectories exchangeable after parenting changes their actions, context and reflections.
- Different target lengths and realized experiences can mediate a total parenting effect. They prevent interpreting this as a **token-dose-controlled** test or isolating feedback responsiveness from generation length, exposure, attention, and content selection.
- The frozen training code constructs a **fresh AdamW optimizer each sleep** while carrying adapter weights. Do not call this persistent optimizer-state learning across sleeps.
- Scope ends at C4. Main's separate C6 accounting, GUIDED424/UNPARENTED536, is not re-audited or pooled into this matched-update window.
- Presence of guidance in actual messages verifies treatment delivery, not retained behavioral change. New parent-free transfer outcomes must be reported separately; this sidecar makes no outcome or improvement claim.

## Coverage, execution and publication

Complete TRAIN coverage: **16 episode records, all 86 action-capture message records, 16 reflection records, eight experience/sleep pairs, all six fits' saved masks and 640 update-log entries**, plus the four TRAIN source collections. Independently opened parent/CALL files are bounded at **96/100**: all 32 parent request/response pairs (64 files), plus the first action and reflection CALL for each of 16 episodes (32 files). These CALL checks sample **32 of 102 available CALL files**; the exact selection and hashes are in JSON. Episode-embedded action captures are checked exhaustively, but are not represented as 102 independently checked CALL files.

**9 local + 9 native CPU tests PASS.** Native execution uses only the existing tokenizer and standard CPU metadata reduction; no weights loaded, parent calls, GPUs, broker mutations, or new evaluation reads. Intermediate audit assertions were corrected to recognize lossless retokenization; no historical artifact or training verdict changed.

Exact publication allowlist (Main owns Git):

- `gpu/orch_r127_parenting_audit.py`
- `tests/test_orch_r127_parenting_audit.py`
- `research_notes/analysis/orch_r127_route_transfer_20260915/PARENTING_DELIVERY_AND_DOSE.json`
- `research_notes/analysis/orch_r127_route_transfer_20260915/PARENTING_DELIVERY_AND_DOSE.md`

JSON binds helper/test hashes, tokenizer hash, source manifest matches, per-cycle task/prefix hashes, initial and continuing state identities, and native evidence references. Raw TRAIN transcripts, token-ID arrays, masks and event-store text remain on node3. No other files are part of this sidecar.
