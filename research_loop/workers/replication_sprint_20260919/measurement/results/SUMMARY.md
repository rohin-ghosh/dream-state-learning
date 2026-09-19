# Think→Act measurement — bounded offline review

Descriptive bounded observations only. No pooled causal, fleet-wide, independence, retention or transfer claim.

YES/NO are explicit evidence or reviewer annotations; missing evidence is UNKNOWN, not failure.
All omissions below are exclusions from analysis only. No authentic training rows are removed.

## reviewed_correction_chain

Sampled units: **5**. Units are not independent training replications.

| Measure | YES | NO | UNKNOWN | Assessed denominator |
|---|---:|---:|---:|---:|
| feedback_delivered | 5 | 0 | 0 | 5 |
| exact_visibility_at_recognition | 1 | 0 | 4 | 1 |
| exact_visibility_at_act | 4 | 1 | 0 | 5 |
| specific_recognition | 1 | 4 | 0 | 5 |
| next_act_observed | 5 | 0 | 0 | 5 |
| next_act_committed | 5 | 0 | 0 | 5 |
| next_act_correct | 0 | 5 | 0 | 5 |
| external_check_performed | 0 | 0 | 5 | 0 |
| external_check_passed | 0 | 0 | 5 | 0 |
| no_reminder_reuse | 0 | 0 | 5 | 0 |
| post_sleep_retention | 0 | 0 | 5 | 0 |
| fresh_context_transfer | 0 | 0 | 5 | 0 |
| artifact_plan_established | 0 | 0 | 5 | 0 |
| planned_artifact_emitted | 0 | 0 | 5 | 0 |

Source-reported levels (not inferred): `{"0":4,"1":1}`.

- next_act_correct_given_specific_recognition: 0 YES / 1 assessed; 0 UNKNOWN of 1 eligible observations.
- next_act_correct_given_exact_visibility: 0 YES / 4 assessed; 0 UNKNOWN of 4 eligible observations.
- emitted_given_established_plan: 0 YES / 0 assessed; 0 UNKNOWN of 0 eligible observations.

## reviewed_withdrawal_cycle

Sampled units: **1**. Units are not independent training replications.

| Measure | YES | NO | UNKNOWN | Assessed denominator |
|---|---:|---:|---:|---:|
| feedback_delivered | 0 | 0 | 1 | 0 |
| exact_visibility_at_recognition | 0 | 0 | 1 | 0 |
| exact_visibility_at_act | 0 | 0 | 1 | 0 |
| specific_recognition | 0 | 1 | 0 | 1 |
| next_act_observed | 1 | 0 | 0 | 1 |
| next_act_committed | 0 | 0 | 1 | 0 |
| next_act_correct | 0 | 0 | 1 | 0 |
| external_check_performed | 0 | 0 | 1 | 0 |
| external_check_passed | 0 | 0 | 1 | 0 |
| no_reminder_reuse | 0 | 0 | 1 | 0 |
| post_sleep_retention | 0 | 0 | 1 | 0 |
| fresh_context_transfer | 0 | 0 | 1 | 0 |
| artifact_plan_established | 0 | 0 | 1 | 0 |
| planned_artifact_emitted | 0 | 0 | 1 | 0 |

Source-reported levels (not inferred): `{"UNKNOWN":1}`.

- next_act_correct_given_specific_recognition: 0 YES / 0 assessed; 0 UNKNOWN of 0 eligible observations.
- next_act_correct_given_exact_visibility: 0 YES / 0 assessed; 0 UNKNOWN of 0 eligible observations.
- emitted_given_established_plan: 0 YES / 0 assessed; 0 UNKNOWN of 0 eligible observations.

## unreviewed_ACT

Sampled units: **11**. Units are not independent training replications.

| Measure | YES | NO | UNKNOWN | Assessed denominator |
|---|---:|---:|---:|---:|
| feedback_delivered | 0 | 0 | 11 | 0 |
| exact_visibility_at_recognition | 0 | 0 | 11 | 0 |
| exact_visibility_at_act | 4 | 7 | 0 | 11 |
| specific_recognition | 0 | 0 | 11 | 0 |
| next_act_observed | 11 | 0 | 0 | 11 |
| next_act_committed | 11 | 0 | 0 | 11 |
| next_act_correct | 0 | 0 | 11 | 0 |
| external_check_performed | 0 | 0 | 11 | 0 |
| external_check_passed | 0 | 0 | 11 | 0 |
| no_reminder_reuse | 0 | 0 | 11 | 0 |
| post_sleep_retention | 0 | 0 | 11 | 0 |
| fresh_context_transfer | 0 | 0 | 11 | 0 |
| artifact_plan_established | 0 | 0 | 11 | 0 |
| planned_artifact_emitted | 0 | 0 | 11 | 0 |

Source-reported levels (not inferred): `{"UNKNOWN":11}`.

- next_act_correct_given_specific_recognition: 0 YES / 0 assessed; 0 UNKNOWN of 0 eligible observations.
- next_act_correct_given_exact_visibility: 0 YES / 0 assessed; 4 UNKNOWN of 4 eligible observations.
- emitted_given_established_plan: 0 YES / 0 assessed; 0 UNKNOWN of 0 eligible observations.

## Assistance / visibility / epoch strata

Full epoch hashes and all metric denominators are in SUMMARY.json; truncated hashes below are display-only.

| Unit / life | Epoch | Assistance | Visibility scope / result | N | Recognition YES/assessed | Next correct YES/assessed |
|---|---|---|---|---:|---:|---:|
| reviewed_correction_chain / C2 | da33de6e018d | PARENT_CORRECTION_PRESENT_IN_SAMPLED_HISTORY | selected_correction / YES | 1 | 0/1 | 0/1 |
| reviewed_correction_chain / P3 | be37a7ca216d | PARENT_CORRECTION_PRESENT_IN_SAMPLED_HISTORY | selected_correction / YES | 1 | 0/1 | 0/1 |
| reviewed_correction_chain / P7 | 5e4f31faf76a | PARENT_CORRECTION_PRESENT_IN_SAMPLED_HISTORY | selected_correction / YES | 1 | 0/1 | 0/1 |
| reviewed_correction_chain / frozen | 8f6b6368e26b | PARENT_CORRECTION_PRESENT_IN_SAMPLED_HISTORY | selected_correction / NO | 1 | 1/1 | 0/1 |
| reviewed_correction_chain / learner | 4ff6c68dcee5 | PARENT_CORRECTION_PRESENT_IN_SAMPLED_HISTORY | selected_correction / YES | 1 | 0/1 | 0/1 |
| reviewed_withdrawal_cycle / r213_r226_caption_observation_fork | UNKNOWN | NO_NEW_PARENT_HUMAN_PEER_INPUT_PRIOR_CONTEXT_VISIBLE | prior_parent_context_not_selected_correction / UNKNOWN | 1 | 0/1 | UNKNOWN (0 assessed) |
| unreviewed_ACT / C2 | 6c240459cff2 | PARENT_TEXT_VISIBLE | any_parent_in_bounded_TRAIN_reader_NOT_selected_correction / YES | 2 | UNKNOWN (0 assessed) | UNKNOWN (0 assessed) |
| unreviewed_ACT / FRESH_R231 | 8766c303cec6 | ASSISTANCE_UNKNOWN_NOT_PROVEN_ABSENT | any_parent_in_bounded_TRAIN_reader_NOT_selected_correction / NO | 3 | UNKNOWN (0 assessed) | UNKNOWN (0 assessed) |
| unreviewed_ACT / GAME1_P3 | 7c4a61fd8eb5 | PARENT_TEXT_VISIBLE | any_parent_in_bounded_TRAIN_reader_NOT_selected_correction / YES | 2 | UNKNOWN (0 assessed) | UNKNOWN (0 assessed) |
| unreviewed_ACT / R232_SIBLING_FROZEN | fed58dada3a7 | ASSISTANCE_UNKNOWN_NOT_PROVEN_ABSENT | any_parent_in_bounded_TRAIN_reader_NOT_selected_correction / NO | 4 | UNKNOWN (0 assessed) | UNKNOWN (0 assessed) |

## Analysis omissions and limitations

- Input rows: 17; unique retained observations: 17.
- Analysis omission entries: 14; training exclusions: **0**.
- Missing/unresolved fleet registrations are not failed children or zero-scoring ACTs.
- Review windows select one chain each; their other ACTs are not independent adjudicated trials.
- Correctness is imported from explicit review, never from intention words, parent delivery, or judge acceptance.
- The manual review has no independent second-reviewer signoff. Task histories and guidance differ.
- Post-sleep retention, fresh-context transfer and plan→artifact fidelity require additional explicit annotations.
- File hashes bind these small projections; original remote journals are not replayed or re-attested.

## Analysis omission reasons

- `CURRENT_BINDING_UNRESOLVED_NOT_COLLECTED`: 14 ledger entries.

## Input provenance

- `research_loop/workers/post_recovery_correction_hourly_20260918/public/cuts/20260919T120025.942165Z.json` — `ceb492b80c9cf549e633203be39fd81c3b1a572ad364f2c6407184506796f6c7` (217044 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/REVIEW.json` — `d0c967101703f0a1e88eb1ba012dcb16219e4f92c990fdec6806da64e5a1c2cb` (44974 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/evidence/C2.json` — `a31ea69dac9c419f520bbd70c938b1dcc442c1e5a77d33eb34309e5df956656b` (350664 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/evidence/P3.json` — `d3e8446a9ac6560b6bbb21c1b0e5df878302f1831856888f813acaa2d0e9320c` (144765 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/evidence/P7.json` — `b8d29d0aaf08e5ee02b69a7e21da16437ddde9ae6b21d22095377ee3e76c2840` (214337 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/evidence/frozen.json` — `fd69f9c19b3c812e0b3ca891e8eec348f8b478e9023b26e288b5332cb21ad2ce` (148322 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/evidence/frozen_PREDECESSOR.json` — `1d139e80453a030d67392f6f992af3591c0f220d81884e8071bc66d6bb185a3c` (3157 bytes).
- `research_loop/workers/post_recovery_correction_review_20260919_0139/evidence/learner.json` — `509f56c517599924b113466413563f89cdb590e16f7e611ac72eae77a05bcd0c` (159419 bytes).
- `research_loop/workers/replication_sprint_20260919/measurement/inputs.json` — `24f12a81a992979e9a74c9dc6ce5c5ec6ccd0db8033f6e28cb9841b67fd6c901` (739 bytes).
- `research_loop/workers/rohin205_node3_20260918/R232_OBSERVATION_COMPLETED_TRACE.json` — `afae60add2c9552b1a7e094d1cc27752877c32c13514d851e07dc901cfc12c01` (7245 bytes).
