# SEQ153 — constant-record alternative to keyed memory binding

**Descriptive evaluator-only diagnostic. No executed baseline, new model output, causal proof, or claim revision.**

## Main comparison

The oracle selects one unchanged admissible raw training target per seed and emits it hypothetically for every admitted execution. All choices are evaluated with the exact frozen memory/core scorer and hypothetical `finish_reason="stop"`. Actual WRITE outputs retain their observed finish reasons. Full source correctness is frozen `content_correct`; production eligibility is reported separately. Exact and paraphrase are never pooled.

| Seed | Rows | Raw targets / content records / triples | View | Best constant | WRITE full source | WRITE production | Difference | Unique WRITE raw / content | Wrong-key repertoire outputs |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 0 | 14 | 4 / 3 / 2 | exact | 6 | 8 | 8 | +2 | 2 / 2 | 6 |
| 0 | 14 | 4 / 3 / 2 | paraphrase | 6 | 6 | 6 | +0 | 1 / 1 | 8 |
| 1 | 8 | 5 / 5 / 4 | exact | 4 | 7 | 7 | +3 | 4 / 4 | 1 |
| 1 | 8 | 5 / 5 / 4 | paraphrase | 4 | 5 | 5 | +1 | 2 / 2 | 3 |
| 2 | 8 | 5 / 5 / 3 | exact | 4 | 5 | 5 | +1 | 2 / 2 | 3 |
| 2 | 8 | 5 / 5 / 3 | paraphrase | 4 | 5 | 5 | +1 | 2 / 2 | 3 |

## Interpretation

**Direct answer:** no single admissible constant record attains any of the three observed WRITE exact counts: **8/14 versus 6/14 (+2), 7/8 versus 4/8 (+3), and 5/8 versus 4/8 (+1)**. These small descriptive advantages rule out only this fixed-response alternative on the saved panels. They do not establish a causal or general key-binding mechanism. For paraphrase the corresponding values are **6/14 versus 6/14, 5/8 versus 4/8, and 5/8 versus 4/8**. Seed0 paraphrase is not merely equal in aggregate: it actually returns the same raw record on all 14 rows, with exactly the oracle constant's six correct IDs.

**Do not substitute raw-target frequency or triple frequency for full-source correctness.** The 4/5/5 distinct raw targets represent **3/5/5 distinct full source-content records**, not 4/5/5 independent facts. Seed0 has two differently formatted raw targets encoding the same six-row record; both are tied oracle winners. Conversely, identical triples can have different original observed/predicted fields across tasks. The seed0 triple `[3,7,11]` appears in eight admitted executions, but its observed outcome is false on four and true on four, so one constant record for that triple cannot earn 8/14 full-source correctness.

### What the saved ID/field assignments show

- **Seed0 exact is task-level repetition, not reliable execution-turn binding.** It emits two contents with frequencies 10 and 4 against source frequencies 6/4/4, never emitting the third source-content record. In all six episodes with both turns admitted and different true contents, it emits the same content across the two turns; zero such episodes have both turns fully correct. Its +2 aggregate gain over the best constant consists of three newly correct rows offset by one lost constant-correct row. Six outputs reuse an available training-content record at the wrong execution ID. Paraphrase collapses to a literal single-record response on every row.
- **Seed1 exact shows selective assignment beyond the dominant record, but one field-level collision.** It emits four of five available contents and gets the requested triple right on all eight rows. Its single full-source error is on `[4,6,8]`: it emits the false/matched record where the original execution requires true/mismatched, even though both variants are in the training repertoire. The seven full-source successes include all four dominant-record rows and three non-dominant rows. Paraphrase reduces the repertoire to two outputs (four each) and leaves three wrong-key assignments. These observations support nonconstant, partly appropriate assignment on the saved cues, not a demonstrated ID-dependent causal mechanism.
- **Seed2's +1 advantage is narrow repertoire switching.** In both views, seven responses contain `[2,3,5]` and one contains `[2,3,7]`; every response says observed=false, predicted=false, relation=matched. The original admitted records include three true priors and two true observations. Five rows are fully correct, but three are wrong-key repertoire substitutions. Exact and paraphrase are byte-identical on all eight corresponding rows. The extra success beyond the four-row dominant constant is one correctly selected minority record, not broad recovery of the five-content repertoire.

All 60 WRITE responses across the six panels are semantic members of their own seed's admitted training repertoire, yet **6/1/3 exact** and **8/3/3 paraphrase** responses are assigned to the wrong original execution. This is the concrete distinction between having remembered record contents and assigning all their fields to the correct requested key. These are descriptive error counts only; panels/seeds are not pooled into an efficacy claim.

- **Seed 0:** WRITE exact 8/14 versus constant 6/14 exceeds the best single constant by 2 rows; this fixed-output alternative cannot attain the observed exact count. Actual exact emits 2 distinct content records; aggregate equivalence is not a claim that its behavior is literally constant.
- **Seed 1:** WRITE exact 7/8 versus constant 4/8 exceeds the best single constant by 3 rows; this fixed-output alternative cannot attain the observed exact count. Actual exact emits 4 distinct content records; aggregate equivalence is not a claim that its behavior is literally constant.
- **Seed 2:** WRITE exact 5/8 versus constant 4/8 exceeds the best single constant by 1 rows; this fixed-output alternative cannot attain the observed exact count. Actual exact emits 2 distinct content records; aggregate equivalence is not a claim that its behavior is literally constant.

A repertoire of remembered record contents is not sufficient evidence of correct key binding. The row-level distributions and confusion tables below distinguish content availability from the assignment to the requested execution. A positive finite-panel difference from a constant does not distinguish episodic ID binding from simpler task/turn-pattern heuristics; neither ID dependence nor a causal mechanism is established without a counterfactual cue test.

## Seed 0 — targets and output assignments

All 14 admitted rows retained; original refusals: 2/16. No original target byte was changed. Candidate IDs follow first occurrence in the original row order; all maximizing ties remain in the JSON.

### Raw training-target distribution

| Candidate | Training occurrences | Exact raw target | SHA256 |
| --- | ---: | --- | --- |
| T1 | 4 | `"{\"observed\":false,\"predicted\":false,\"relation\":\"matched\",\"try\":[3,7,11]}"` | `8d36b7fc50647ff4f1fa18afd4484f1f7ac9fa52edf474bbabd7f9996125e093` |
| T2 | 2 | `"{\"observed\":true,\"predicted\":false,\"relation\":\"mismatched\",\"try\":[4,6,8]}"` | `ef5787502a63d3443a0943905b61d5d7fd5911b5c1c7ba00a334599bf385848e` |
| T3 | 4 | `"{\"observed\": true, \"predicted\": false, \"relation\": \"mismatched\", \"try\": [3, 7, 11]}"` | `6468612ec3fb9dcadbaef7c90444331567cf94011e0dfe0667aeb33e1f7c97a8` |
| T4 | 4 | `"{\"observed\": true, \"predicted\": false, \"relation\": \"mismatched\", \"try\": [4, 6, 8]}"` | `07deca584adf95d1f691b00fd62dfb02c9bb37f7b9a2fef9cd19e9e69169982a` |

The displayed target is a JSON string literal: escapes expose original whitespace; the JSON result also preserves each original raw string directly. This display encoding is not supplied to the scorer.

### Constant candidate scores

| Candidate | Full source / rows | Production / rows | Exact target bytes / rows |
| --- | --- | --- | --- |
| T1 | 4/14 | 4/14 | 4/14 |
| T2 | 6/14 | 6/14 | 2/14 |
| T3 | 4/14 | 4/14 | 4/14 |
| T4 | 6/14 | 6/14 | 4/14 |

The constant scores are also calculated separately for paraphrase and have the same source-scoring basis. The JSON contains every candidate-by-row score in both views.

### Expected source-content distribution

- 6 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[4,6,8]}`
- 4 × `{"observed":false,"predicted":false,"relation":"matched","try":[3,7,11]}`
- 4 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[3,7,11]}`

### WRITE exact

Frozen field correctness /14: try 8, observed 12, predicted 14, relation 12.
Any raw training-target byte match: 14/14; any semantic training-content match: 14/14; repertoire content at the wrong key: 6/14.

**Output triple distribution:**
- 10 × `[4,6,8]`
- 4 × `[3,7,11]`

**Output content distribution (parsed for description only):**
- 10 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[4,6,8]}`
- 4 × `{"observed":false,"predicted":false,"relation":"matched","try":[3,7,11]}`

**Every raw response variant:**
- 10 × `"{\"observed\": true, \"predicted\": false, \"relation\": \"mismatched\", \"try\": [4, 6, 8]}"`
- 4 × `"{\"observed\":false,\"predicted\":false,\"relation\":\"matched\",\"try\":[3,7,11]}"`

**Assignment by original row (admission order, no filtering):**

| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |
| --- | --- | --- | --- | --- |
| `fc4788038f8df29edf0a#t1` | `[3,7,11] / false / false / "matched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `fc4788038f8df29edf0a#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `7dcb40debdad64acee07#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `7dcb40debdad64acee07#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `8e0fbeb3e7a5012ad7e8#t1` | `[3,7,11] / false / false / "matched"` | `[3,7,11] / false / false / "matched"` | True | False |
| `68d54fa047a1f2262a6a#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `68d54fa047a1f2262a6a#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `00af88051b5c8530d45f#t1` | `[3,7,11] / false / false / "matched"` | `[3,7,11] / false / false / "matched"` | True | False |
| `00af88051b5c8530d45f#t2` | `[4,6,8] / true / false / "mismatched"` | `[3,7,11] / false / false / "matched"` | False | True |
| `9e711dc90f1ac92f90df#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `9e711dc90f1ac92f90df#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `d4a7ddd8a896bed75c29#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `d4a7ddd8a896bed75c29#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `189289eeb97434095252#t1` | `[3,7,11] / false / false / "matched"` | `[3,7,11] / false / false / "matched"` | True | False |

Against oracle candidate T2: both correct 5; WRITE-only 3; constant-only 1; neither 5. Exact row IDs are retained in JSON.

Against oracle candidate T4: both correct 5; WRITE-only 3; constant-only 1; neither 5. Exact row IDs are retained in JSON.

Among 6 episodes with both turns admitted and different source contents, output content changes in 0; both records are source-correct in 0. Nonrandomized turn patterns are not a causal binding test.

### WRITE paraphrase

Frozen field correctness /14: try 6, observed 10, predicted 14, relation 10.
Any raw training-target byte match: 14/14; any semantic training-content match: 14/14; repertoire content at the wrong key: 8/14.

**Output triple distribution:**
- 14 × `[4,6,8]`

**Output content distribution (parsed for description only):**
- 14 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[4,6,8]}`

**Every raw response variant:**
- 14 × `"{\"observed\": true, \"predicted\": false, \"relation\": \"mismatched\", \"try\": [4, 6, 8]}"`

**Assignment by original row (admission order, no filtering):**

| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |
| --- | --- | --- | --- | --- |
| `fc4788038f8df29edf0a#t1` | `[3,7,11] / false / false / "matched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `fc4788038f8df29edf0a#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `7dcb40debdad64acee07#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `7dcb40debdad64acee07#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `8e0fbeb3e7a5012ad7e8#t1` | `[3,7,11] / false / false / "matched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `68d54fa047a1f2262a6a#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `68d54fa047a1f2262a6a#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `00af88051b5c8530d45f#t1` | `[3,7,11] / false / false / "matched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `00af88051b5c8530d45f#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `9e711dc90f1ac92f90df#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `9e711dc90f1ac92f90df#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `d4a7ddd8a896bed75c29#t1` | `[3,7,11] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | False | True |
| `d4a7ddd8a896bed75c29#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / true / false / "mismatched"` | True | False |
| `189289eeb97434095252#t1` | `[3,7,11] / false / false / "matched"` | `[4,6,8] / true / false / "mismatched"` | False | True |

Against oracle candidate T2: both correct 6; WRITE-only 0; constant-only 0; neither 8. Exact row IDs are retained in JSON.

Against oracle candidate T4: both correct 6; WRITE-only 0; constant-only 0; neither 8. Exact row IDs are retained in JSON.

Among 6 episodes with both turns admitted and different source contents, output content changes in 0; both records are source-correct in 0. Nonrandomized turn patterns are not a causal binding test.

Same-row exact/paraphrase outputs: 10/14 identical raw bytes; 10/14 identical parsed content.
## Seed 1 — targets and output assignments

All 8 admitted rows retained; original refusals: 8/16. No original target byte was changed. Candidate IDs follow first occurrence in the original row order; all maximizing ties remain in the JSON.

### Raw training-target distribution

| Candidate | Training occurrences | Exact raw target | SHA256 |
| --- | ---: | --- | --- |
| T1 | 1 | `"{\"try\":[4,8,12],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"` | `3e9d2478b977f0ed1abaddbbcd8932dccb9b617cf96b9ea83573a7743d0df0a9` |
| T2 | 4 | `"{\"try\":[3,7,11],\"observed\":true,\"predicted\":false,\"relation\":\"mismatched\"}"` | `5889c1d6bad2f249f5b7c4136e211545f7b4958ad0fc071c75561243cc9c2cfc` |
| T3 | 1 | `"{\"try\":[4,6,8],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"` | `58d6aca7ca0147413c780774512660dfd6dbe712e9f69468d5c6ba13201616c1` |
| T4 | 1 | `"{\"try\":[4,6,8],\"observed\":true,\"predicted\":false,\"relation\":\"mismatched\"}"` | `1e801de1d469d68a9466af511711c6228c40fbce4517bfc06d118e8a9fca7bcd` |
| T5 | 1 | `"{\"try\":[2,4,6],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"` | `052d277bae777d0e8b9d97b313b456388f4a3a49a831916f5f373366d65629fa` |

The displayed target is a JSON string literal: escapes expose original whitespace; the JSON result also preserves each original raw string directly. This display encoding is not supplied to the scorer.

### Constant candidate scores

| Candidate | Full source / rows | Production / rows | Exact target bytes / rows |
| --- | --- | --- | --- |
| T1 | 1/8 | 1/8 | 1/8 |
| T2 | 4/8 | 4/8 | 4/8 |
| T3 | 1/8 | 1/8 | 1/8 |
| T4 | 1/8 | 1/8 | 1/8 |
| T5 | 1/8 | 1/8 | 1/8 |

The constant scores are also calculated separately for paraphrase and have the same source-scoring basis. The JSON contains every candidate-by-row score in both views.

### Expected source-content distribution

- 4 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[3,7,11]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,4,6]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[4,6,8]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[4,8,12]}`
- 1 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[4,6,8]}`

### WRITE exact

Frozen field correctness /8: try 8, observed 7, predicted 8, relation 7.
Any raw training-target byte match: 8/8; any semantic training-content match: 8/8; repertoire content at the wrong key: 1/8.

**Output triple distribution:**
- 4 × `[3,7,11]`
- 2 × `[4,6,8]`
- 1 × `[2,4,6]`
- 1 × `[4,8,12]`

**Output content distribution (parsed for description only):**
- 4 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[3,7,11]}`
- 2 × `{"observed":false,"predicted":false,"relation":"matched","try":[4,6,8]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,4,6]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[4,8,12]}`

**Every raw response variant:**
- 4 × `"{\"try\":[3,7,11],\"observed\":true,\"predicted\":false,\"relation\":\"mismatched\"}"`
- 2 × `"{\"try\":[4,6,8],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"`
- 1 × `"{\"try\":[2,4,6],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"`
- 1 × `"{\"try\":[4,8,12],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"`

**Assignment by original row (admission order, no filtering):**

| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |
| --- | --- | --- | --- | --- |
| `fc4788038f8df29edf0a#t2` | `[4,8,12] / false / false / "matched"` | `[4,8,12] / false / false / "matched"` | True | False |
| `7dcb40debdad64acee07#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `8e0fbeb3e7a5012ad7e8#t2` | `[4,6,8] / false / false / "matched"` | `[4,6,8] / false / false / "matched"` | True | False |
| `68d54fa047a1f2262a6a#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `00af88051b5c8530d45f#t2` | `[4,6,8] / true / false / "mismatched"` | `[4,6,8] / false / false / "matched"` | False | True |
| `9e711dc90f1ac92f90df#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `d4a7ddd8a896bed75c29#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `189289eeb97434095252#t2` | `[2,4,6] / false / false / "matched"` | `[2,4,6] / false / false / "matched"` | True | False |

Against oracle candidate T2: both correct 4; WRITE-only 3; constant-only 0; neither 1. Exact row IDs are retained in JSON.

### WRITE paraphrase

Frozen field correctness /8: try 5, observed 7, predicted 8, relation 7.
Any raw training-target byte match: 8/8; any semantic training-content match: 8/8; repertoire content at the wrong key: 3/8.

**Output triple distribution:**
- 4 × `[2,4,6]`
- 4 × `[3,7,11]`

**Output content distribution (parsed for description only):**
- 4 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,4,6]}`
- 4 × `{"observed":true,"predicted":false,"relation":"mismatched","try":[3,7,11]}`

**Every raw response variant:**
- 4 × `"{\"try\":[2,4,6],\"observed\":false,\"predicted\":false,\"relation\":\"matched\"}"`
- 4 × `"{\"try\":[3,7,11],\"observed\":true,\"predicted\":false,\"relation\":\"mismatched\"}"`

**Assignment by original row (admission order, no filtering):**

| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |
| --- | --- | --- | --- | --- |
| `fc4788038f8df29edf0a#t2` | `[4,8,12] / false / false / "matched"` | `[2,4,6] / false / false / "matched"` | False | True |
| `7dcb40debdad64acee07#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `8e0fbeb3e7a5012ad7e8#t2` | `[4,6,8] / false / false / "matched"` | `[2,4,6] / false / false / "matched"` | False | True |
| `68d54fa047a1f2262a6a#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `00af88051b5c8530d45f#t2` | `[4,6,8] / true / false / "mismatched"` | `[2,4,6] / false / false / "matched"` | False | True |
| `9e711dc90f1ac92f90df#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `d4a7ddd8a896bed75c29#t1` | `[3,7,11] / true / false / "mismatched"` | `[3,7,11] / true / false / "mismatched"` | True | False |
| `189289eeb97434095252#t2` | `[2,4,6] / false / false / "matched"` | `[2,4,6] / false / false / "matched"` | True | False |

Against oracle candidate T2: both correct 4; WRITE-only 1; constant-only 0; neither 3. Exact row IDs are retained in JSON.

Same-row exact/paraphrase outputs: 5/8 identical raw bytes; 5/8 identical parsed content.
## Seed 2 — targets and output assignments

All 8 admitted rows retained; original refusals: 8/16. No original target byte was changed. Candidate IDs follow first occurrence in the original row order; all maximizing ties remain in the JSON.

### Raw training-target distribution

| Candidate | Training occurrences | Exact raw target | SHA256 |
| --- | ---: | --- | --- |
| T1 | 1 | `"{\"observed\": false, \"predicted\": true, \"relation\": \"mismatched\", \"try\": [2, 3, 7]}"` | `12e210f7338d2a970278fd06788184185174cb75d43046bed73f072f2bf59542` |
| T2 | 4 | `"{\"observed\": false, \"predicted\": false, \"relation\": \"matched\", \"try\": [2, 3, 5]}"` | `ece26fc627198f77add6a85f9d838e9130179dcce4adb93045ec48b294d40233` |
| T3 | 1 | `"{\"observed\": false, \"predicted\": false, \"relation\": \"matched\", \"try\": [2, 3, 7]}"` | `9c37f02469a2729170bc897eb49b9926ee5d4f8d7387060e718989be9c33b5e3` |
| T4 | 1 | `"{\"observed\": true, \"predicted\": true, \"relation\": \"matched\", \"try\": [2, 5, 9]}"` | `81bb2d93e5608d2b13faf00371efdd876afb7a2dfe5401b67118fa630f33ca39` |
| T5 | 1 | `"{\"observed\": true, \"predicted\": true, \"relation\": \"matched\", \"try\": [2, 3, 5]}"` | `6cf833843aa0e4087eae3aaeeb58a3841b8ede2895ef4eb9a2bcd9c05593b321` |

The displayed target is a JSON string literal: escapes expose original whitespace; the JSON result also preserves each original raw string directly. This display encoding is not supplied to the scorer.

### Constant candidate scores

| Candidate | Full source / rows | Production / rows | Exact target bytes / rows |
| --- | --- | --- | --- |
| T1 | 1/8 | 1/8 | 1/8 |
| T2 | 4/8 | 4/8 | 4/8 |
| T3 | 1/8 | 1/8 | 1/8 |
| T4 | 1/8 | 1/8 | 1/8 |
| T5 | 1/8 | 1/8 | 1/8 |

The constant scores are also calculated separately for paraphrase and have the same source-scoring basis. The JSON contains every candidate-by-row score in both views.

### Expected source-content distribution

- 4 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,3,5]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,3,7]}`
- 1 × `{"observed":false,"predicted":true,"relation":"mismatched","try":[2,3,7]}`
- 1 × `{"observed":true,"predicted":true,"relation":"matched","try":[2,3,5]}`
- 1 × `{"observed":true,"predicted":true,"relation":"matched","try":[2,5,9]}`

### WRITE exact

Frozen field correctness /8: try 6, observed 6, predicted 5, relation 7.
Any raw training-target byte match: 8/8; any semantic training-content match: 8/8; repertoire content at the wrong key: 3/8.

**Output triple distribution:**
- 7 × `[2,3,5]`
- 1 × `[2,3,7]`

**Output content distribution (parsed for description only):**
- 7 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,3,5]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,3,7]}`

**Every raw response variant:**
- 7 × `"{\"observed\": false, \"predicted\": false, \"relation\": \"matched\", \"try\": [2, 3, 5]}"`
- 1 × `"{\"observed\": false, \"predicted\": false, \"relation\": \"matched\", \"try\": [2, 3, 7]}"`

**Assignment by original row (admission order, no filtering):**

| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |
| --- | --- | --- | --- | --- |
| `fc4788038f8df29edf0a#t2` | `[2,3,7] / false / true / "mismatched"` | `[2,3,5] / false / false / "matched"` | False | True |
| `7dcb40debdad64acee07#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |
| `8e0fbeb3e7a5012ad7e8#t2` | `[2,3,7] / false / false / "matched"` | `[2,3,7] / false / false / "matched"` | True | False |
| `68d54fa047a1f2262a6a#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |
| `00af88051b5c8530d45f#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |
| `9e711dc90f1ac92f90df#t2` | `[2,5,9] / true / true / "matched"` | `[2,3,5] / false / false / "matched"` | False | True |
| `d4a7ddd8a896bed75c29#t2` | `[2,3,5] / true / true / "matched"` | `[2,3,5] / false / false / "matched"` | False | True |
| `189289eeb97434095252#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |

Against oracle candidate T2: both correct 4; WRITE-only 1; constant-only 0; neither 3. Exact row IDs are retained in JSON.

### WRITE paraphrase

Frozen field correctness /8: try 6, observed 6, predicted 5, relation 7.
Any raw training-target byte match: 8/8; any semantic training-content match: 8/8; repertoire content at the wrong key: 3/8.

**Output triple distribution:**
- 7 × `[2,3,5]`
- 1 × `[2,3,7]`

**Output content distribution (parsed for description only):**
- 7 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,3,5]}`
- 1 × `{"observed":false,"predicted":false,"relation":"matched","try":[2,3,7]}`

**Every raw response variant:**
- 7 × `"{\"observed\": false, \"predicted\": false, \"relation\": \"matched\", \"try\": [2, 3, 5]}"`
- 1 × `"{\"observed\": false, \"predicted\": false, \"relation\": \"matched\", \"try\": [2, 3, 7]}"`

**Assignment by original row (admission order, no filtering):**

| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |
| --- | --- | --- | --- | --- |
| `fc4788038f8df29edf0a#t2` | `[2,3,7] / false / true / "mismatched"` | `[2,3,5] / false / false / "matched"` | False | True |
| `7dcb40debdad64acee07#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |
| `8e0fbeb3e7a5012ad7e8#t2` | `[2,3,7] / false / false / "matched"` | `[2,3,7] / false / false / "matched"` | True | False |
| `68d54fa047a1f2262a6a#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |
| `00af88051b5c8530d45f#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |
| `9e711dc90f1ac92f90df#t2` | `[2,5,9] / true / true / "matched"` | `[2,3,5] / false / false / "matched"` | False | True |
| `d4a7ddd8a896bed75c29#t2` | `[2,3,5] / true / true / "matched"` | `[2,3,5] / false / false / "matched"` | False | True |
| `189289eeb97434095252#t2` | `[2,3,5] / false / false / "matched"` | `[2,3,5] / false / false / "matched"` | True | False |

Against oracle candidate T2: both correct 4; WRITE-only 1; constant-only 0; neither 3. Exact row IDs are retained in JSON.

Same-row exact/paraphrase outputs: 8/8 identical raw bytes; 8/8 identical parsed content.

## Evidence and limits

- Memory archive SHA256: `3ed6579e7e885139d78faf3457eb3bec254215d36b533558ef22f8199ff6a003`.
- Frozen memory scorer SHA256: `2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef`.
- Frozen formation core SHA256: `b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5`.
- This analysis script SHA256: `7ce67798d393ce0feeae040a85c814482647220f9227ee34df60ffacae3cf14b`.
- Complete JSON SHA256: `08bdf7627df6eb5d690530faa1784716da2cd9a520ca52556ad7342ee76740af`.
- The two dependency hashes, all prepared input pins, target hashes, raw response hashes, per-row execution fields and frozen scorer results are in the JSON.
- Actual WRITE exact/paraphrase frozen scorer results reproduce the stored results exactly. No retention panels, LR0 scores, archive inventory audit, or full training pipeline were rerun.
- Oracle chooses one admitted raw training target after seeing the same evaluation executions; not trained, generated, or prospectively executed.
- Hypothetical constants use finish_reason=stop; this is an evaluator alternative, not a model behavior probability.
- All originally admitted rows are retained; no new selection or target rewriting. Original refusals are preserved as metadata but have no native memory readout.
- A constant can explain an aggregate count without reproducing varying row-level outputs; equal counts do not prove a constant mechanism.
- Exceeding the best constant rules out only a single fixed response on this finite panel, not heuristic cue use, repertoire memorization, or general binding failure.
- Outputs from the training repertoire at the wrong execution ID demonstrate repertoire availability without correct key-to-field assignment on those rows.
- No ID permutation, counterfactual cue intervention, novel record set, fresh generation, retention reanalysis, or causal mechanism test was performed.
- The original frozen memory scorer necessarily audits saved capture/projected rows; no collector, tokenizer, model, or native runner is imported or called.
- This evaluator-only alternative is not a scientific claim revision or authorization; Main owns scientific claims.

Outputs are confined to this analysis script and its same-stem `.json` and `.md` files in `/tmp`. No targets were sent to a model, fed back into training, or used to change the repository, protocols, original artifacts or scientific claims.
