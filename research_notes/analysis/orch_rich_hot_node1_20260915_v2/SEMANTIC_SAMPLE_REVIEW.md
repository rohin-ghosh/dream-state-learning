# V2 deterministic semantic sample — author-side, not admission

Selection fixed before review: first three source responses on physical0 and
physical2, and first three completed own-second-pass responses on physical4
and physical6. This is 12 final outputs across four conditions, with six
additional first-pass captures retained for auditing the two-stage histories.
The snapshot is `snapshot_0424`; exact measurement timestamps are in its
manifest. It is a small, nonrandom, repeated-task sample, not 12 independent
questions or an estimate of population quality. Hubble owns 64-raw/12-sample
publishing/admission; this author-side review does not replace that process.

All twelve complete task/response texts and the supplied first-pass histories
were read semantically. No keyword count was used as a positive label.

| Physical / call | Assessment |
| --- | --- |
| 0 / 00001 | Cats: computes 26 combined lions/tigers, 13 cougars, 39 total. No alternative considered or rejected. |
| 0 / 00002 | Multiplayer groups: computes 36 slots minus three repeats, 33. No alternative; the wording about prior grouping is not independently resolved. |
| 0 / 00003 | Bottle caps: computes 75 green out of 125, 60%. No consequential alternative. |
| 2 / 00001 | Cats: same valid calculation, shorter expression. No alternative. |
| 2 / 00002 | Groups: same slot/repetition arithmetic. No alternative. |
| 2 / 00003 | Caps: same valid percentage. No alternative. |
| 4 / 00002 | Jellybeans: checks 3×14 + 2×14 = 70 against the first pass. Useful consistency check, not branching. |
| 4 / 00004 | Fruit dozens: repeats 2.5×12 + 5×12 = 90 and says no alternatives are needed. Not a positive branch. |
| 4 / 00006 | Mountain: checks 60/15 + 72/36 = 6 and again rules alternatives unnecessary. Not a positive branch. |
| 6 / 00002 | Chickens: verifies feed cost/profit arithmetic. Asking whether supplied prices are realistic is outside this word problem; rejecting that digression is not a meaningful search branch. |
| 6 / 00004 | Dance lessons: **fabricates consequential ambiguity** about which two lessons are free and changes a correct first-pass 80 to incorrect 100. Order cannot remove the two free lessons from the ten specified. Preserve this harmful self-evaluation. |
| 6 / 00006 | Snacks: correct 18/6 = 3; imagines damaged pouches/contingencies then dismisses them because not specified. This unnecessary hypothetical is not counted as meaningful branching. |

Measured sample results:
- **0/12 meaningful task-relevant supported search branches.**
- **1/12 fabricated consequential branch**, producing a correct-to-wrong revision.
- **11/12 numeric-oracle correct**; numerical correctness is not semantic admission.
- **11/12 without a counted meaningful branch**; lack of a relevant alternative
  is not itself a content failure or reason to add padding.

The birdseed counterfactual in `branch_candidate/REVIEW.md` is a separately
selected illustration. Its operational counterfactual interpretation and
stricter search-branch interpretation are explicitly separated. It is not
added to this sample's numerator or denominator.

Raw output labels, numeric FINAL oracle, source bytes, failures and token
captures remain untouched. Every output remains unadmitted here. No qualified
rows/hour is established by this review; report native output rates separately.
