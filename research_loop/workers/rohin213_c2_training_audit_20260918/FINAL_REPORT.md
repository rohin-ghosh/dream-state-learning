# Original C2: independently audited content of actual training

Fixed observation cut: 2026-09-18T06:16:22.860734+00:00; completed sleeps40–65.
Manual full-row review; source stage, eligibility and executed UPDATE counts are independently joined.
No C2 control changes, no signals, no causal or quality claim. No heuristic gate used to label rows.

Completed: 87 NEW candidates, 82 NEW trained, 5 excluded; 199 distinct trained sources including rehearsal.
Actual presentations: 1549 = 1312 NEW + 237 REHEARSAL. Every completed sleep agrees with UPDATE events.

| Manual class | All trained distinct | All presentations | NEW trained | NEW presentations |
|---|---:|---:|---:|---:|
| META_INTENT_COMPLIANCE | 107 | 802 | 42 | 672 |
| SUBSTANTIVE_CONTENT | 64 | 452 | 23 | 368 |
| MIXED | 27 | 279 | 16 | 256 |
| UNCERTAIN | 1 | 16 | 1 | 16 |

## Per-sleep actual NEW training

M=meta-intent/compliance; S=substantive content; X=mixed; U=uncertain.
M/S/X/U are trained row counts, not candidates. P columns are actual presentations.

| Sleep | Candidates | Excluded | M | S | X | U | M-P | S-P | X-P | U-P | Rehearsal-P | All-P | COMPLETE |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 40 | 3 | 0 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 117 | 165 | 4943 |
| 41 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 48 | 0 | 0 | 120 | 168 | 5128 |
| 42 | 3 | 0 | 2 | 0 | 1 | 0 | 32 | 0 | 16 | 0 | 0 | 48 | 5199 |
| 43 | 3 | 0 | 2 | 0 | 1 | 0 | 32 | 0 | 16 | 0 | 0 | 48 | 5268 |
| 44 | 3 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 0 | 48 | 5337 |
| 45 | 3 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 0 | 48 | 5406 |
| 46 | 3 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 0 | 48 | 5476 |
| 47 | 3 | 0 | 1 | 1 | 1 | 0 | 16 | 16 | 16 | 0 | 0 | 48 | 5545 |
| 48 | 3 | 0 | 1 | 1 | 1 | 0 | 16 | 16 | 16 | 0 | 0 | 48 | 5615 |
| 49 | 3 | 0 | 1 | 2 | 0 | 0 | 16 | 32 | 0 | 0 | 0 | 48 | 5684 |
| 50 | 3 | 0 | 1 | 2 | 0 | 0 | 16 | 32 | 0 | 0 | 0 | 48 | 5753 |
| 51 | 3 | 0 | 1 | 1 | 1 | 0 | 16 | 16 | 16 | 0 | 0 | 48 | 5823 |
| 52 | 5 | 0 | 1 | 0 | 4 | 0 | 16 | 0 | 64 | 0 | 0 | 80 | 5975 |
| 53 | 3 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 0 | 48 | 6055 |
| 54 | 3 | 1 | 1 | 1 | 0 | 0 | 16 | 16 | 0 | 0 | 0 | 32 | 6122 |
| 55 | 3 | 0 | 1 | 1 | 1 | 0 | 16 | 16 | 16 | 0 | 0 | 48 | 6202 |
| 56 | 3 | 0 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 48 | 6283 |
| 57 | 3 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 0 | 48 | 6365 |
| 58 | 3 | 1 | 2 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 32 | 6432 |
| 59 | 4 | 0 | 2 | 0 | 2 | 0 | 32 | 0 | 32 | 0 | 0 | 64 | 6543 |
| 60 | 4 | 0 | 3 | 0 | 0 | 1 | 48 | 0 | 0 | 16 | 0 | 64 | 6647 |
| 61 | 3 | 1 | 2 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 | 32 | 6714 |
| 62 | 4 | 1 | 1 | 0 | 2 | 0 | 16 | 0 | 32 | 0 | 0 | 48 | 6807 |
| 63 | 3 | 0 | 2 | 1 | 0 | 0 | 32 | 16 | 0 | 0 | 0 | 48 | 6892 |
| 64 | 4 | 0 | 4 | 0 | 0 | 0 | 64 | 0 | 0 | 0 | 0 | 64 | 6997 |
| 65 | 6 | 1 | 4 | 1 | 0 | 0 | 64 | 16 | 0 | 0 | 0 | 80 | 7142 |

Sleep40/41 include117/120 distinct older rehearsal rows at one presentation each;
their NEW targets still receive16 presentations each. Later completed sleeps contain no rehearsal.

## The reported last40/all-meta comparison

Samples below are explicitly bound by source IDs/hashes in FINAL_COUNTS.json; different cuts are not interchangeable.
- last40_completed_trained_new: 40 rows; {"META_INTENT_COMPLIANCE": 25, "MIXED": 6, "SUBSTANTIVE_CONTENT": 8, "UNCERTAIN": 1}.
- last40_completed_new_candidates: 40 rows; {"META_INTENT_COMPLIANCE": 24, "MIXED": 6, "SUBSTANTIVE_CONTENT": 9, "UNCERTAIN": 1}.
- last40_latest_observed_candidates_including_pending: 40 rows; {"META_INTENT_COMPLIANCE": 25, "MIXED": 6, "SUBSTANTIVE_CONTENT": 8, "UNCERTAIN": 1}.

Sleeps62–65: 17 candidates; 15 actually trained.
In the completed-trained last40 sample, pure META25 plus MIXED6 equals31 rows containing meta.
That may explain a binary31/40 description, but MIXED is not relabeled as pure meta here.
Under this manual rubric, THINK6731 is a substantive conceptual answer but excluded;
6738/6749 are trained MIXED;6820 is a trained actual narrative;7036 is trained calculation code.
Thus an all-pure-meta claim is not reproduced on this stated sample/rubric. This is not a causal rebuttal.

## Boundaries and limitations

Sleep means SLEEP_COMPLETE.document.cycle, not runtime-local R189 outcome counter, which resets.
FINAL_COUNTS.json includes an explicit counter-to-next-sleep mapping. Journal indices are neither counter.
Sleep52 trained after02:53:07.145 compaction, but all five of its targets were generated before it.
The latest pending sleep is not included in completed counts; its actual update count is not established
by this collector cut and must not be called zero. Pending target labels describe content only.
Each UPDATE also co-trains fixed ANCHOR material (weight0.25); child/anchor token exposures are recorded
separately in FINAL_COUNTS.json. These content counts do not classify all loss or all training tokens.
Full-target manual review is single-auditor, with explicit rationales and uncertain cases retained.
Substantive does not mean correct, useful, executed or new; MIXED remains a separate category.
Public target previews are exact first150 Unicode characters, escaped only for display; full rows are private.
Collection validates each full canonical journal record before projecting it. Stored SLEEP projections omit
resume_state; their record SHA binds the original full record, not the smaller projection.

Detailed original52–63 sources/stages/hashes/eligibility/UPDATE indices: AUDIT.json and ROWS.csv.
All40–65 rows and stage counts: EXTENDED_AUDIT.json and FINAL_COUNTS.json.
No original C2 runtime, parent, inbox, checkpoint or lease was changed.
