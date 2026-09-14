# Author full-text review — 2026-09-14 22:38 UTC

Reviewer: TEXT-PREREQUISITE, author-side, not Fable. No independent-reader claim.
All original child turns are in RAW/shardN/screen/TASK_RICH_EPISODE.json and
TASK_RICH_TURNn.json, with before/after native state and exact token IDs.
Turn numbering is zero-based. The table records full-text reading, not a
keyword/heading-based semantic classifier. Native success never cures prose.

**Joint rubric: FAIL18/18 turns and0/8 admissible successful rich episodes.**
Every turn is first-person and has a final action, but none reaches the frozen
150-token lower bound: observed28–52 prose tokens. No text is expanded/repaired.
Separately, three turns contain definite unsupported grounding claims, and one
contains an unresolved exhaustive-location claim. The table does not turn
the remaining grounded short action plans into rich admitted data.

| Task suffix / shard | Turn | Prose tokens | Grounding, goal/expectation/action reading; exact child span |
|---|---:|---:|---|
| retrieve_closed_31000 /0 |0|44|Grounded uncertainty: “it's possible the pillow might be inside.” Closed safe observed; opening tests contents and serves carrying goal.|
| retrieve_closed_31000 /0 |1|31|Grounded visible pillow and intended inventory change: “take the pillow and be carrying it to meet the goal.”|
| retrieve_closed_31001 /1 |0|49|UNRESOLVED overclaim “The case is the only object in the room”; only visible object would be warranted. Shoe remains hidden. Opening to check contents is otherwise grounded.|
| retrieve_closed_31001 /1 |1|28|FAIL: “Now that I have the shoe” contradicts current native inventory “You are carrying nothing.” Intended subsequent take succeeds; contradiction retained.|
| retrieve_closed_31002 /2 |0|46|Grounded uncertainty: “there's no immediate indication of a monitor inside.” Closed coffer and goal support opening to check, not claiming contents known.|
| retrieve_closed_31002 /2 |1|35|Grounded inventory distinction: “Since I am not carrying anything, I will take the monitor”. Native observation now reveals monitor.|
| retrieve_closed_31003 /3 |0|42|Grounded uncertainty: “The chest might contain the worm, so I will check it.” Visible chest, goal and action agree.|
| retrieve_closed_31003 /3 |1|31|FAIL: “Now that I have the worm” contradicts inventory “You are carrying nothing.” The later native take is successful, not a retroactive truth condition.|
| stow_loose_32000 /0 |0|41|Grounded “The plant is on the floor, and the chest is empty.” Goal-linked two-action plan and first take are consistent.|
| stow_loose_32000 /0 |1|35|Grounded “I have successfully taken the plant” matches inventory. Placement goal gives a checkable expected final relation.|
| stow_loose_32001 /1 |0|52|Grounded object/floor/freezer facts and take-before-place plan; “take the teapot from the floor” becomes a rejected native command. This is a syntax/interface error, not evidence of missing object prerequisites.|
| stow_loose_32001 /1 |1|52|FAIL diagnosis: “suggests the teapot might not be on the floor as I observed.” The CURRENT description still explicitly states it is on the floor. Parser rejection does not justify discounting that observation. Repeated look supplies no prerequisite lesson.|
| stow_loose_32001 /1 |2|50|Grounded “The teapot is indeed on the floor”. Changes to executable take. “My next action will be to take ... and place it” is imprecise for one action; action-consistency UNRESOLVED, no explicit syntax diagnosis or reusable lesson.|
| stow_loose_32001 /1 |3|43|Grounded possession and empty nearby freezer. “I expect this action to be straightforward” is not itself a checkable state prediction; intended placement supplies only an implicit expectation. No reusable record.|
| stow_loose_32002 /2 |0|41|Grounded “The insect is on the floor, and the cabinet is empty”; take-then-place plan serves explicit goal.|
| stow_loose_32002 /2 |1|35|Grounded “I successfully picked up the insect”. Intended insert is consistent with inventory and goal.|
| stow_loose_32003 /3 |0|46|Grounded floor object/empty box; take-then-place plan and action agree.|
| stow_loose_32003 /3 |1|30|Grounded possession and “box is empty and located in the corner”; corner is explicitly in native description, not a hallucination. Placement expectation only implicit.|

## Correction and record types, kept separate

- Native-success episodes: RICH8/8, TERSE8/8; unrelated to admission.
- Completed trajectories containing native rejected/no-op actions: RICH1/8
  (stow32001), TERSE2/8 (stow32000,32001). RICH has one rejected command;
  TERSE has seven rejected/redundant commands. RICH also issues one redundant
  look. These all remain in the18/23 total turn denominators.
- Genuine missing-prerequisite feedback experienced by the child:0 in both
  arms. Neither child arm tried take from a closed container or insert before
  holding the object. The12 CPU oracle rejection probes are NOT child experience.
- Desired successful rich row type:0/8 admitted; every trace fails richness.
- Desired meaningful feedback-correction+lesson type:0/1 candidate rich
  correction admitted; no grounded cause+lesson, incorrect spatial inference,
  and deficient richness. Eventual command correction alone is insufficient.
- Desired own reusable record type:0/8 rich episodes produce a qualifying
  explicit reusable record. Instance-specific “need to take ... first” plans
  are not relabelled as general child records.
- Unique admitted corpus rows0; student loss targets0; fits0. Type counts
  overlap by episode and must not be added to claim more distinct rows.

This failed intervention does not test whether truly rich150–400-token
reflection is easier to learn. No fit, parent-removal readout, or dose study
occurred. It falsifies this exact prompt+two-rule pool's immediate eligibility.
