# Canonical learner trajectory — request 05:48 UTC

Actual native observation: **2026-09-15T05:52:35.214990+00:00**. Labelled partials are right-censored, not completed cycles.
Only the existing GUIDED / UNPARENTED / NO_LORA baseline is included. Historical frozen-LoRA is a different control and is excluded.

## What has actually changed

- C1 GUIDED and OFF: 0/2 reflections admitted, zero updates, identical saved child. Both reflections reached the 512-token cap without termination (`complete_reflection_required`). This is an explicit no-op, not successful rehearsal.
- C2 GUIDED and OFF: each admitted 1/2 reflections and completed/saved 104 optimizer steps, with verified changed adapter state, unchanged frozen base, and adapter file SHA checks. Each fitted reflection was presented 16 times, with 192 legacy trajectory presentations; those are not total replay-row exposures.
- GUIDED C2 admitted a failed-outcome reflection. OFF C2 and C3 each admitted one successful-outcome reflection; the failed-outcome reflection was rejected by `reflection_not_answer_action_replay`, not by an outcome-success filter.
- OFF C3 completed another 104 saved steps. GUIDED and NO_LORA C3 experience are still partial at this observation; no C3 sleep/readout or matched-complete C3 claim for them.
- NO_LORA C1/C2: zero updates by architectural design (`NO_LORA`), even when a reflection is admissible. Native identity is frozen base, null adapter path and empty adapter file list, not historical frozen-LoRA.
- No learning-blocking implementation bug established: nonzero C2 fits and persisted lineage are verified. No learner code, targets, schedules, dose, allocation or gates changed.

## New reflection admissions and saved dose

| Arm | Cycle | Experience | New admitted / attempts (2 planned) | Failed-outcome admitted | Saved updates | New target presentations | Legacy trajectory presentations | Sleep disposition |
|---|---:|---|---:|---:|---:|---:|---:|---|
| GUIDED | 1 | COMPLETE | 0/2 | 0 | 0 | 0 | 0 | NO_VALID_REFLECTIONS |
| GUIDED | 2 | COMPLETE | 1/2 | 1 | 104 | 16 | 192 | COMPLETE |
| GUIDED | 3 | RUNNING_CENSORED | 0/0 | 0 | not saved | — | — | NOT_STARTED |
| UNPARENTED | 1 | COMPLETE | 0/2 | 0 | 0 | 0 | 0 | NO_VALID_REFLECTIONS |
| UNPARENTED | 2 | COMPLETE | 1/2 | 0 | 104 | 16 | 192 | COMPLETE |
| UNPARENTED | 3 | COMPLETE | 1/2 | 0 | 104 | 16 | 192 | COMPLETE |
| NO_LORA | 1 | COMPLETE | 1/2 | 1 | 0 | 0 | 0 | NO_LORA |
| NO_LORA | 2 | COMPLETE | 0/2 | 0 | 0 | 0 | 0 | NO_LORA |
| NO_LORA | 3 | RUNNING_CENSORED | 0/0 | 0 | not saved | — | — | NOT_STARTED |

C3 partial zero attempts means no reflection has finished yet, not 0/2 rejected. Failed and successful episodes remain preserved. The actual loss is ordinary positive-likelihood causal SFT on outcome-tagged learner reflections plus unchanged legacy replay; it is **not** unlikelihood/negative-gradient training of wrong actions. Teacher lesson bytes are excluded from targets.

## Thinking-first operational trajectory

Tokens include EOS. Rejected actions are execution errors, not rejected hypotheses. Route-sequence counts are observed executions, not independently verified alternative reasoning methods. Response completion is not semantic coherence.

| Arm | Cycle | Phase | Output tokens | Rejected / actions | Repeated actions | Distinct route sequences | Complete / response count | Ancillary success / episodes |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| GUIDED | 0 | readout | 88 | 1/8 | 0 | 2 | 8/8 | 1/2 |
| GUIDED | 1 | experience | 1152 | 1/11 | 1 | 2 | 11/13 | 1/2 |
| GUIDED | 1 | readout | 97 | 1/9 | 0 | 2 | 9/9 | 1/2 |
| GUIDED | 2 | experience | 1109 | 0/12 | 0 | 1 | 13/14 | 1/2 |
| GUIDED | 2 | readout | 91 | 1/8 | 0 | 2 | 8/8 | 1/2 |
| UNPARENTED | 0 | readout | 88 | 1/8 | 0 | 2 | 8/8 | 1/2 |
| UNPARENTED | 1 | experience | 1160 | 0/12 | 0 | 1 | 12/14 | 1/2 |
| UNPARENTED | 1 | readout | 97 | 1/9 | 0 | 2 | 9/9 | 1/2 |
| UNPARENTED | 2 | experience | 703 | 1/8 | 0 | 2 | 10/10 | 1/2 |
| UNPARENTED | 2 | readout | 91 | 1/8 | 0 | 2 | 8/8 | 1/2 |
| UNPARENTED | 3 | experience | 499 | 1/8 | 0 | 2 | 10/10 | 1/2 |
| UNPARENTED | 3 | readout | 133 | 0/12 | 0 | 2 | 12/12 | 2/2 |
| NO_LORA | 0 | readout | 42 | 0/4 | 0 | 1 | 4/4 | 1/2 |
| NO_LORA | 1 | experience | 1097 | 2/12 | 2 | 1 | 13/14 | 0/2 |
| NO_LORA | 1 | readout | 46 | 0/4 | 0 | 1 | 4/4 | 1/2 |
| NO_LORA | 2 | experience | 1164 | 2/12 | 2 | 1 | 12/14 | 0/2 |
| NO_LORA | 2 | readout | 40 | 0/4 | 0 | 1 | 4/4 | 1/2 |

## Parameter persistence versus behavioral retention

- GUIDED C2 → actual GUIDED C3 loads the changed saved adapter; OFF C2 → actual OFF C3 likewise. Full state hashes, file hashes, receipt hashes and native process identities are in `TRAJECTORY_0548_LINEAGE.json` and the verified native snapshot.
- Every completed post-sleep readout is a fresh process, loads the exact saved output identity and has no parent. All three arms share the same frozen readout tasks **at each corresponding checkpoint** C0/C1/C2 (hash-verified).
- Between adjacent checkpoints the held task hashes overlap **0/2**. TRAIN tasks also advance; GUIDED/NO_LORA experience includes state-conditional parent advice. Therefore these are exploratory transfer observations, not a same-task retention test or clean thinking/dose slope.
- GUIDED/OFF parent-free output-token trajectory C0→C1→C2 is 88→97→91 for both; NO_LORA is 42→46→40. Changed weights do not establish improved behavior. In particular, C1 changes cannot be attributed to sleep updates because C1 made none.
- No semantic learning, memory improvement, taught-skill retention or parent-content causal advantage is established here. No outcome-based tuning/deallocation; zero outcomes remain reported.
- Original `thinking.parent_visible=false` concerns visibility of counters, not presence of a parent in experience. Use native `LOADED.parent_present` (true in GUIDED/NO_LORA experience; false in all readouts).

## Measured phase and cycle times (seconds)

| Arm | Cycle | Experience envelope | Learner generation | Parent waits (calls) | Provider service | Wait minus service | Sleep | Readout | Readout generation | Interphase gaps | Total cycle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GUIDED | 1 | 542.490 | 50.083 | 413.080 (8) | 244.853 | 168.227 | 0.000 | 84.576 | 5.148 | 5.131 | 632.197 |
| GUIDED | 2 | 820.914 | 47.915 | 695.126 (8) | 264.043 | 431.083 | 381.243 | 82.065 | 4.786 | 8.217 | 1292.440 |
| GUIDED | 3 | 454.996 (partial) | 4.676 | 399.072 (4) | 134.302 | 264.769 | — | — | — | — | — |
| UNPARENTED | 1 | 126.514 | 45.886 | 0.000 (0) | 0.000 | 0.000 | 0.000 | 83.582 | 5.067 | 5.006 | 215.103 |
| UNPARENTED | 2 | 106.266 | 28.286 | 0.000 (0) | 0.000 | 0.000 | 380.666 | 82.610 | 4.732 | 8.416 | 577.958 |
| UNPARENTED | 3 | 99.583 | 20.727 | 0.000 (0) | 0.000 | 0.000 | 380.123 | 83.847 | 6.742 | 8.350 | 571.903 |
| NO_LORA | 1 | 717.205 | 36.000 | 551.106 (8) | 247.769 | 303.336 | 0.001 | 133.666 | 2.258 | 4.874 | 855.745 |
| NO_LORA | 2 | 845.473 | 38.173 | 677.106 (8) | 258.341 | 418.764 | 0.000 | 130.344 | 2.070 | 4.900 | 980.717 |
| NO_LORA | 3 | 323.434 (partial) | 2.528 | 205.036 (2) | 50.794 | 154.243 | — | — | — | — | — |

Parent wait includes queueing, provider service, delivery and polling; wait-minus-service is **not** a separately measured pure queue duration. Sleep includes model load, training and save: loss receipts lack per-update timestamps, so no invented training-only duration. Phase residual also includes model loading/environment work. Partial generation/waits cover completed calls only, with outstanding time inside the censored experience envelope. Sub-millisecond no-op sleeps round to 0.000 here; exact values remain in JSON.

## Actual phase boundaries (UTC, 2026-09-15)

| Arm | Cycle | Phase | Start | Finish | Status |
|---|---:|---|---|---|---|
| GUIDED | 1 | experience | 05:12:47.356Z | 05:21:49.846Z | COMPLETE |
| GUIDED | 1 | sleep | 05:21:54.011Z | 05:21:54.012Z | COMPLETE |
| GUIDED | 1 | readout | 05:21:54.977Z | 05:23:19.553Z | COMPLETE |
| GUIDED | 2 | experience | 05:23:23.621Z | 05:37:04.535Z | COMPLETE |
| GUIDED | 2 | sleep | 05:37:08.641Z | 05:43:29.884Z | COMPLETE |
| GUIDED | 2 | readout | 05:43:33.995Z | 05:44:56.061Z | COMPLETE |
| GUIDED | 3 | experience | 05:45:00.219Z | not finished | RUNNING_CENSORED |
| UNPARENTED | 1 | experience | 05:15:39.801Z | 05:17:46.315Z | COMPLETE |
| UNPARENTED | 1 | sleep | 05:17:50.373Z | 05:17:50.373Z | COMPLETE |
| UNPARENTED | 1 | readout | 05:17:51.322Z | 05:19:14.904Z | COMPLETE |
| UNPARENTED | 2 | experience | 05:19:19.046Z | 05:21:05.312Z | COMPLETE |
| UNPARENTED | 2 | sleep | 05:21:09.515Z | 05:27:30.181Z | COMPLETE |
| UNPARENTED | 2 | readout | 05:27:34.394Z | 05:28:57.004Z | COMPLETE |
| UNPARENTED | 3 | experience | 05:29:01.111Z | 05:30:40.695Z | COMPLETE |
| UNPARENTED | 3 | sleep | 05:30:44.886Z | 05:37:05.009Z | COMPLETE |
| UNPARENTED | 3 | readout | 05:37:09.168Z | 05:38:33.014Z | COMPLETE |
| NO_LORA | 1 | experience | 05:16:27.427Z | 05:28:24.632Z | COMPLETE |
| NO_LORA | 1 | sleep | 05:28:28.650Z | 05:28:28.650Z | COMPLETE |
| NO_LORA | 1 | readout | 05:28:29.507Z | 05:30:43.173Z | COMPLETE |
| NO_LORA | 2 | experience | 05:30:47.115Z | 05:44:52.587Z | COMPLETE |
| NO_LORA | 2 | sleep | 05:44:56.571Z | 05:44:56.572Z | COMPLETE |
| NO_LORA | 2 | readout | 05:44:57.488Z | 05:47:07.832Z | COMPLETE |
| NO_LORA | 3 | experience | 05:47:11.781Z | not finished | RUNNING_CENSORED |

## Evidence and preservation

- Read-only reducer and tests; no live GPU source changes or new baseline. Exact bounds and original deadlines remain unchanged.
- All raw parenting requests/responses remain node-local under `/tmp/orch_route_parent_campaign_20260915_canonical102/parent_raw`; only metadata and hash inventory were retrieved. Completed C1/C2 GUIDED and NO_LORA each have 8/8 parent receipt/wait joins per cycle, actual `openai/openai/gpt-6-astra`, no recorded provider errors.
- Snapshot filename refers to the 05:48 request; use the actual observation timestamp above, not the filename, as the data cutoff. No raw tasks, answers, teacher bytes or transcripts are published.
- Explicit source/test/compact handoff: `TRAJECTORY_0548_STAGE_MANIFEST.json`. Main retains Git ownership.
