# Fable corpus-quality audit — MATH-SCALE rich rows (read-only, 2026-09-15 03:45Z)

Watcher read, not a blind re-label. Sources: native root `/localhome/local-rohing/orch_math_scale_20260914_attempt1` on node 2 (1,984 `shard*/CALL_*.json`, all still `semantic_status=UNREVIEWED` — labels live only in the repo-side reducer); repo snapshot `research_notes/analysis/orch_math_scale_20260914_attempt1/collection_terminal_20260915T004705Z/ROWS.json` (00:47Z, 740 rows reviewed) plus `fulltext_review/batch_*/ACCEPTED_REVIEW.json`; rubric `orch_math_scale_20260914_review_instructions.md`; earlier runs `orch_math_rich_20260914_attempt1` (96 calls) and `orch_math_record_20260914_attempt1` (190 calls). Reviewer = author-side Codex readers, six axes, PASS only if all six true; admission = outcome_pass AND 150–400 tokens AND PASS AND gold VALID (`orch_math_rich.py:111-115,157`).

## 1. Inventory (scale run)

- Tasks 1,024/1,024 attempted (256 × percentages, work_rates, fractional_quantities, group_accounting; 64 held tasks never mined). Learner calls 1,984/2,048 = 1,024 `rich` + 960 `new_record`; 64 records SKIPPED (`common_rich_failed_exact_oracle`).
- Oracle: rich 960/1,024, record 952/960. Token contract 1,558/1,984 (352 under 150, 74 over 400, 4 truncated). Mechanical candidates 1,508 = 616 rich + 892 record.
- Review at 00:47Z: 740 rows / 384 questions; PASS 503, FAIL 233, UNRESOLVED 4; **admitted 420** (143 rich + 277 record; 296 distinct tasks; all gold VALID). Gold 348 VALID / 32 AMBIGUOUS / 4 INVALID. Notebook 02:49Z snapshot (not local): 1,409 texts, 764 qualified. Admitted so far only from percentages (293) and work_rates (127); the other two families were unreviewed at 00:47Z.
- Rejection codes, all 1,984 rows, gate order: unreviewed candidate 925; admitted 420; tokens<150 338 (all rich); outcome fail 72; tokens>400 66 (60 record); semantic FAIL 155 (first_person only 93, grounded+neutral_prefix 25, no_padding 18, other mixes 19); PASS but gold AMBIGUOUS 6; UNRESOLVED 2.
- Across all 233 FAIL rows the false axes are first_person 160, grounded 71, neutral_prefix 70, no_padding 29, reusable 10; **139/233 fail on first_person alone**; 208/233 have the correct gold. 83 PASS rows are not admitted: 53 rich under 150 tokens, 20 over 400, 6 ambiguous gold, 4 oracle fails.

## 2–4. Samples and measures

Deterministic first 30 by shard/CALL order; "considerations" = sentences/lines opening a step or containing "="; "novel check" = a check sentence introducing an equation not already in the body; "branch" = any alternative/assumption/contrast wording (generous regex); meta = prompt/parent/checker wording.

| measure | admitted first 30 | FAIL first 30 | admitted all (420) | FAIL all (233) |
|---|---:|---:|---:|---:|
| median words / gen tokens | 195 / 293 | 120 / 204 | 187 / 278 | 114 / 205 |
| final = gold | 30/30 | 27/30 | 420/420 | 211/233 |
| median considerations | 11 | 10 | 10 | 10 |
| reuses ≥2 question numbers | 30/30 | 30/30 | 402/420 | 226/233 |
| has self-check sentence | 22/30 | 9/30 | 287/420 | 66/233 |
| self-check adds a new equation | 9/30 | 5/30 | 125/420 | 27/233 |
| branch / alternative wording | 0/30 | 4/30 | 23/420 | 21/233 |
| truncated (no FINAL) | 0/30 | 0/30 | 0/420 | 1/233 |
| meta / parent / checker wording | 0/30 | 0/30 | 0/420 | 2/233 |
| first-person markers present | 29/30 | 12/30 | 385/420 | 72/233 |

Within the `rich` kind the two classes are indistinguishable on content: admitted 143 vs FAIL 181 — median tokens 196 vs 184, considerations 10 vs 10, self-check 10/143 vs 14/181, novel check 6/143 vs 7/181, branch 4/143 vs 14/181; only voice differs (I/my present 108/143 vs 20/181; my count matches the reviewer on 677/740 rows, the rest mostly plural "we").

Earlier runs, same pattern. Rich run: 19 admitted; 36 FAIL, of which 33 first_person=False and 33 gold-correct; 32 terse rows excluded by the token floor (rich-vs-terse outcome 29/32 vs 5/32). Record run: 82/82 FAIL rows gold-correct, 80/82 first_person=False; the "autobiographical account" prompt moved admissions 9/63 → 55/63 while the rejected old records had *more* novel checks (46/54) than the admitted new ones (27/55).

Full reads (5 admitted, 5 FAIL, 4 FAILs with voice satisfied). Representative admitted, `shard0/CALL_0004` (task 4424, record, PASS): "First, I calculated the number of women and men: Number of women = 40% of 200 = 0.40 * 200 = 80; Number of men = 200 - 80 = 120 … To check the result, I verified that the calculations were correct and that the total … was indeed the sum of the women and men." — correct, grounded, linear; the check verifies nothing; label right by the rubric, no branching. Representative rejected, `shard0/CALL_0003` (same task, rich, FAIL first_person): "First, calculate the number of women and men: Women = 40% of 200 = 0.40 * 200 = 80; Men = 200 - 80 = 120 … Total = 64 (women) + 72 (men) = 136" — identical equations in imperative mood; the pair differs only in register. Labels I would dispute: `shard0/CALL_0019` (2178) FAIL for treating "about 25%" as 25% when the gold does the same; `CALL_0012` (1209) FAIL no_padding for re-stating 60−6=54, 54/2=27 while `CALL_0004`'s emptier check passes.

## 5. Verdict on the rubric

It is admitting correct, grounded, own-voice, non-padded **narration of one linear computation**, not branching reasoning. Concrete patterns:

1. **Register is the gate.** 139/233 FAILs fail only first_person; every content measure is flat between admitted and rejected rich rows; the record prompt's register flip alone lifted yield 9→55 of 63. The child is being selected for pronouns and mood.
2. **No branch anywhere, and the few branches are punished.** 23/420 admitted rows contain any alternative/assumption wording (0/30 in the sample); 20/892 candidate records state an assumption. Rows that did fork on an interpretation ("about 25%", "six small and medium apples", the growth "rumor") were rejected under grounded_operations or left UNRESOLVED. GSM8K is linear, so the rubric never asks "where could this go wrong, which reading did I drop".
3. **Checks re-narrate; records re-tell.** 287/420 admitted rows have a check sentence but only 125 add an equation; 60/274 admitted records contain no equation beyond the rich solution they were conditioned on; 124 admitted rows are second renditions of an already-admitted task (420 rows, 296 tasks); three opening templates cover 217/420.
4. **Length gate does the rest.** 338 rich rows (33%) drop on <150 tokens alone, 53 of them PASS on all six axes; admitted median 278 tokens vs FAIL 205. Short correct own-voice solutions are lost, longer templated ones kept.

Contamination and truncation are not a problem (0/420 each). What the corpus lacks is the property Rohin named: nothing in 420 admitted rows records a considered-and-rejected path, and the rubric has no axis that would reward one.
