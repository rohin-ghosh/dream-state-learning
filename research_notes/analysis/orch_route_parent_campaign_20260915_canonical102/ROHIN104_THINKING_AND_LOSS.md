# Rohin104: thinking-first and actual loss semantics

Reduced 2026-09-15T05:19:28.166898+00:00. Historical segment2 is complete; its FROZEN arm remains frozen LoRA, never NO_LORA. All C1→C2 joins verify the same saved child. Eight TRAIN episodes per historical cycle; the new canonical schedule is exactly two sequential episodes per sleep.

| Historical arm | Output tokens C1→C2 (includes EOS) | Rejected actions C1→C2 | Within-episode repeats C1→C2 | Complete responses C1→C2 | Admitted reflections C1→C2 |
|---|---:|---:|---:|---:|---:|
| GUIDED | 3750 → 2471 | 7/46 → 8/44 | 6/46 → 8/44 | 51/54 → 52/52 | 5/8 → 7/8 |
| UNPARENTED | 4036 → 4054 | 2/39 → 2/43 | 0/39 → 0/43 | 45/47 → 49/51 | 6/8 → 6/8 |
| FROZEN | 3339 → 3342 | 7/46 → 7/44 | 7/46 → 7/44 | 54/54 → 52/52 | 8/8 → 8/8 |

These are operational proxies, NOT verified thinking quality. Rejected actions count execution/capture errors, not deliberate rejected hypotheses. Distinct route-sequence counts confound different task identifiers and do not establish multiple approaches per task. Complete responses/admitted reflections are syntax and provenance hygiene, not semantic coherence. Semantic reasoning quality remains unreviewed on node-local transcripts. Changes across different TRAIN task groups are descriptive, not a clean causal learning slope; no outcome-based scheduling or deallocation.

## Actual negative-example training

Every successful and failed experience is offered to reflection. Failures are marked FAILURE_NOT_CORRECT_ANSWER and attempted_actions_are_not_gold. Eligibility filters enforce complete self-generated reflections and provenance/teacher-span exclusions; they do not filter on task correctness. Raw failed actions are not promoted as correct answer targets.

| Historical learning arm/cycle | Failed episodes offered | Failed-reflection targets actually trained | Successful-reflection targets trained | Actual updates |
|---|---:|---:|---:|---:|
| GUIDED C1 | 7/8 | 4 | 1 | 136 |
| GUIDED C2 | 8/8 | 7 | 0 | 152 |
| UNPARENTED C1 | 2/8 | 2 | 4 | 144 |
| UNPARENTED C2 | 2/8 | 2 | 4 | 144 |

Loss is ordinary causal next-token cross-entropy on the admitted learner reflection plus the unchanged legacy replay mix, with positive active/original token normalization. It INCREASES likelihood of the reflection conditional on outcome-tagged evidence. This is NOT negative gradient on failed actions, NOT unlikelihood/DPO/RL, and NOT proof that all failed episodes were trained. Prefix tokens have labels -100; teacher lesson bytes are excluded from supervised targets. NO_LORA and historical FROZEN have zero fits/updates.

Current legacy mix remains unchanged. Age-decay plus train-use refresh, and later zero-replay plasticity, are FUTURE separate-arm designs only; neither is enabled in this life.

## Reader provenance

READER_STAGE_HASHES.json contains exact paths and SHA256 for each historical phase and currently complete canonical phase. SEGMENT2_COMPLETE_REDUCTION.json includes input identities, timestamps, thinking counters, saved-child/fresh-process joins, ancillary outcomes, and the original FROZEN C1 failure/repair envelope. NEGATIVE_EXAMPLE_LOSS_RECEIPTS.json binds actual trained outcome strata to experience/sleep receipts. LATEST_METRICS.json is a live compact snapshot, not immutable evidence. Raw prompts and replies remain on node3.
