# Full audit — good results, interesting results, measurable behaviour (Fable, 2026-09-18)

Six dimension reports and six adversarial verdicts were received (game, judge, audits, c2c0, pair, players); the players verdict was truncated in the input and no seventh verdict arrived. Corrected statements are used where a verdict adjusted a claim. Times are UTC as written in the receipts; PDT is UTC minus 7.

## The five things worth saying today

1. Novelty per token falls with age, and the frozen base out-explores every trained child at a matched budget. Parent-free probe, 3 scenes x 2 seeds x 1024 generated tokens, same decoder and scorer, zero updates: new-pixel events per 1000 tokens are base 9.44 (58 events), C2 sleep51 6.51 (40), C2 sleep87 4.07 (25), C0 sleep84 3.09 (19), fresh sleep1 4.72 (29), fresh sleep2 2.44 (15). Inside both lineages with two ages the fall holds at both seeds (C2 24 to 14 and 16 to 11; fresh 19 to 10 and 10 to 5). The older C2 also fragments: 108 responses vs 58 at sleep 51, 57 vs 106 tokens per response, 2.11x prompt tokens (verified; mostly the response-count effect). Matched on generated tokens only; two ages per lineage; new pixels are embedding-novelty events, not certified jokes. Source: research_loop/workers/rohin233_focus_20260918/public/MOVEMENT_CURVES.json; rohin233_kept_age_probe_20260918/R233_FRESH_R231_s2_STATUS.json; rohin232_age_probe_20260918/RESULTS.md.

2. The live game judge is scene-blind and its "accepted" is mostly not humour. Widegap step 6250 prefers a contest's own top caption over another cartoon's top caption in 51/100 pairs (chance) while rejecting shuffled 100/100, scene descriptions 100/100, nonsense 99/100, truncated 94/100 and beating mid-tier 74/100. Acceptance is rank <= 50 of 65 against a random human panel. On manual review 2 of 47 distinct accepted base strings are joke-like; 16 of P3's 26 accepts are plan sentences and its best rank ever (14/65) went to "We will monitor the judges' feedback and adjust as necessary." Source: rohin207_contrast_20260918/WIDEGAP_REPORT.json; rohin221_continuous_caption_20260918/R230_SEED_SELECTION_AUDIT_v1.json; node 4 SCALE_physical3 INBOX records.

3. Two scene-aware judges exist and nothing uses them. Both R210 1M-pair runs finished on ovx5 at 14:19 UTC (07:19 PDT): other-contest accuracy 90.0% (rank8) and 89.0% (rank16) at step 15625 vs 52.5% / 48.5% at the warm start, at a Spearman cost of 0.01 to 0.07. The pre-declared Spearman-only rule selected step 146/145, which is the scene-blind warm start. ovx5 shows 0 MiB on all 8 GPUs, no notebook entry, and every game receipt still binds widegap-6250. Source: ovx5 orch_r210_ovx5_mixed1m_rank{8,16}_*/training/checkpoint_diagnostics/step_*/CONTRAST.private.json, SPEARMAN.private.json, COMPLETED.json.

4. The controlled pair is clean; stage 0 is a shared null with one large drift difference. Same birth prompt (sha 7362d19a), same initial adapter hash (04341ab8), frozen arm 48 sleeps at 0 steps, learner 23 sleeps x 48 = 1104 updates, 0 shared parent texts. Both arms produce content ACTs from cycle 1 (learner 21/23, frozen 39/48) and neither reached stage 1 (max streak 2 in both). The learner drifted: CJK in 30/69 responses vs 3/144, fullwidth 53/69 vs 2/144, state-JSON dumps 69/69 vs 97/144; on 17+8-6 the learner wrote 17 correct vs 18 wrong final values, the frozen 51 vs 7. One life per arm; the frozen arm ran 2.1x the cycles in the same wall time, so compare per cycle. Source: ovx4 orch_r231_curriculum_birth_20260918 and orch_r232_curriculum_frozen_20260918 raw/stream/records; rohin231_curriculum_birth_20260918/r232_pair/README.md.

5. Sleep installs habits, not content, and corrections do not travel. C2's meta opener: 0/153 responses in the first 51 sleeps, 122/237 after the first R191 training row (02:50 UTC), 61/61 THINK responses from 09:00 UTC. Training receipts for sleeps 40-65 reconcile end to end (1549 presentations) and 802 (52%) are pure meta rows. After Astra flagged "I will assume" at 07:29 UTC the phrase went from 5/238 responses to 51/158. Across 21 reviewed correction traces on 18 lives: level 0:14, 1:5, 2:2, 3:0. C0 recall after sleep: 0 true recalls in 16 probes, 1 confabulation. Source: ovx3 orch_r153_community_C2 stream/records; rohin213_c2_training_audit_20260918/FINAL_COUNTS.json; rohin232_correction_audit_20260918/public/CURRENT.json; ovx orch_r216_C0_20260918_attempt2/raw.

## Good results

Mechanism / level 0-1
- Training receipts reconcile: C2 sleeps 40-65, 87 NEW candidates, 82 trained, 199 sources, 1549 presentations = 1312 NEW + 237 rehearsal, every NEW target at exactly 16 (rohin213_c2_training_audit_20260918/FINAL_REPORT.md).
- First ON-not-OFF survival, medium confidence: raw unparented child's birth sentence returns at empty context with adapter ON at 11/18 checkpoints, OFF 0/18; war-plan vocabulary 0/36 (research_notes/analysis/OBJECT_SURVIVAL_FIRST_READ_2026-09-17.md). Lexical read, one life.
- C2 derived V=3 by hand once (adjusted): RESPONSE 5840 at 01:58 UTC, answering Rohin's request for the exact n=3 equation, algebra exact, after 9 PROCESS_FAILED runs. 5840 itself was never trained, but its restatement (5863, a THINK, not an ACT) was trained x16 at sleep 52; every later V=3 had the answer in its prompt; no context-free recall (rohin232_correction_audit_20260918/public/HISTORICAL_C2_DERIVATION.json; node-5 records).
- Checkable-correct arithmetic: C0 ACT 2554/2588 (6+6+3=15, 5*6/2=15) and frozen sibling ACT648 are the only observer-verified checks in the 16-life cut; regex-extracted binary claims C0 65/67, C2 5/5, medium confidence (rohin233_semantic_movement_20260918/REPORT.md; c2c0 node scan).
- Coached level-2 correction: fresh learner ACT346 works the inverse check 19+6=25, 25-8=17; frozen sibling ACT47 does the same with 0 updates (rohin232 POSTCUT_SEMANTIC_REVIEW_1122.md; FROZEN_FOLLOWUP.json).
- Language correction lands immediately, 4/4 (C0 #993 to #998, #1471 to #1474; C2 #6546 to #6550, #9372 to #9375); C0 relapsed 8 min later (node records).
- Filters do what they say: C0 8/47 sleeps trained 0 steps because all 3 rows were meta_only, 68/141 NEW rows excluded; V2 content filter would reject 5/6 rows V1 trained in sleeps 72-74 (80 presentations), not deployed (rohin225_content_repair_20260918/PROSPECTIVE_AUDIT.json).

Judge
- Garbage rejection and humour separation (adjusted): widegap 518/600 = 86.3%; BT8k step-300 judge (2,400 comparisons, not 8,000) 69.75% tie-half. Widegap is a warm-start continuation of that same adapter plus 100k wide-gap pairs (~42x exposure, objective and batch changed), so the gain cannot be attributed to pair count alone (rohin207_contrast_20260918/WIDEGAP_REPORT.json, BT8K_REPORT.json; node-4 judge_config and warm-start receipt).
- Crossed-scene negatives fix scene-blindness: 52.5% to 85.0% by step 1000, 84-92% for all 18 later checkpoints; rank 8 vs 16 no material difference (ovx5 R210 checkpoint diagnostics).
- Throughput: 1M comparisons in 32,281 s at 30.69 pairs/s on 4 GPUs vs 8.42 pairs/s on one A40 for the 100k run (UPDATE_015625.json; CAPTION_GAME_AUDIT_2026-09-17.md).

Game
- Selfderive fork (adjusted): 26 accepted / 19 new_pixel of 174 ranked, best rank 30, all 26 texts present in its own responses. But 22 of 26 came in the first two hours (09h 11, 10h 11, 11h 3, 12h 1, none after 12:01 UTC), the first 3 including the best were written at 09:02 UTC before any judge feedback reached it, all on one scene, and 9/26 carry a literal "Captcha:" prefix (ovx2 r213_r226_caption_selfderive_fork/raw INBOX and RESPONSE records).
- P3 window receipts re-derived: 14 ACTs, 60 scored, 55 rejected, 5 accepted, 3 new pixels; 12/12 cycles match Leibniz's cut (rohin228_decision_audit_20260918/P3_RECEIPT_CUT.json).
- First matched datum, n=1: C2 snapshot51 one caption rank 25/65 accepted with a new pixel; base ranks 60 and 56 rejected (research_notes/analysis/R213_FIRST_MATCHED_CAPTION_DATUM_2026-09-18.md).

Parenting / curriculum
- Pair design verified (item 4); parent turns disjoint across arms (0 exact, max 8-gram Jaccard 0.211 on birth greetings).
- Content from cycle 1: state-only responses 2/69 and 2/144, 0 exact duplicates in both arms; parent's first "correct calculation, not just a plan" at 7.0 min (learner) and 0.5 min (frozen) after LOADED (ovx4 records).
- Rohin's turns to C2 got direct answers before the habit installed: first 8 turns 8/8 content and 1/8 meta head; last 10 turns 6/10 content and 8/10 meta head; strict read 7 direct, 3 meta-framed, 8 intention (medium; ovx3 records).
- Honesty improved where one parent pressed one point (09-17 lineage, medium): unreceipted-claim rate C4 11/18 to 3/18 to 1/18, support_free 6/18 to 2/18 to 1/18 (FLEET_BEHAVIOUR_IMPROVEMENTS_AND_MVP_GAPS_2026-09-17.md).

## Interesting results

- Late-cell exploration (medium): the base finds 72% of its pixels in the second half of each 1024-token cell (42/58), C2-87 24% (6/25), fresh2 20% (3/15) (MOVEMENT_CURVES.json seed_curves).
- The frozen base leads the continuous game: 99 new pixels vs 12 for P3, acceptance 67% vs 5-15% for every LoRA child; but 450/549 (82%) of base accepts are semantic repeats. Unmatched budgets and start times (R227_HOURLY_20260918T140005Z.json).
- Recall invented: C0 #1538 confabulated a "driver stapler story" repeated in 6 consecutive responses; 0 true recall, 2 honest no-memory, 11 subject changes in 16 probes. P7 named the cab driver "Asta" ("Iona" 0/319); its one apparent recall had the themes quoted in the parent's question. P3 reported "mixed feedback" it never received; C2 asserted V=29 from empty stdout (ovx C0 records; SCALE_physical7 records; ROHIN_CLONES_CONVERSATIONS_2026-09-17.md; C2_PILOT_LOG line 80).
- No level-3 correction anywhere: 0 of 21 traces, and every reviewed interval contained a fresh reminder; 2323 of 2344 feedback candidates unreviewed. C2 cycles 42-44 named the sympy fix in LEARN and re-imported sympy in 3/3 next ACTs (rohin232 CURRENT.json; C2_PILOT_LOG lines 44-69).
- Flagging a phrase made it 16x more frequent; Astra then wrote "set aside" in 29/153 C2 turns (ovx3 INBOX #7647 onward).
- P3 stopped on silence: 16 caption-bearing responses 05:51-07:00 UTC, 0 caption lines 07:10-08:30 UTC with no judgment in context. Content ACTs then collapsed: 07h 8/8, 08h 7/7, 09h 4/9, 10h-16h 5/59; fuzzy repeats 59% of responses in 14h; parentless 140 min after 14:45 UTC; the xhigh Astra turn rendered but the next ACT was intention-only, mixed English/Chinese, 0 captions; 0 scored strings 12-14 UTC (SCALE_physical3 records; rohin233_focus_20260918/P3_RENDER_AND_UPTAKE.json).
- Language collapse in isolated lives: P7 switched mid-sentence at 05:56:27 UTC, 11 s after Rohin's loneliness prompt; CJK share 06h 46.5%, 08h 8.1% after "answer in English", 16h 78.4%; Astra7 went 4.5% to 60.2% within an hour of P7's first Chinese message; the frozen no-adapter control drifted to 164/194 CJK with 0 sleeps. C2's decline (17% to 7%) is mostly a birth-hour burst (12/33 in the first hour; adjusted) and C0 ran 22% CJK under the English quarantine all life, so the quarantine does not explain C2 (SCALE_physical7 records; ovx Astra7 records; CHILDREN_DISTILLED_2026-09-17.md; verdict c2c0).
- P7 cast Astra as its trainee unprompted at 08:43:34 UTC; after being made Astra7's parent it sent 34 messages, 0 addressed to the child, 93 about a confabulated monitoring config (SCALE_physical7 records).
- Math trio (medium): A and C reached the correct 12 but the parent logged UNRESOLVED; problem 2 went 0/3, C wrote 60 in 198 places (ovx2 r213_math_* records).
- Equal wall time gave the frozen arm 2.1x the cycles (4.1 vs 9.1 min per cycle); its ACT content rate fell 15/15 to 7/13 in 13h with 0 weight change at mean prompt 4062 tokens near the 4608 trigger (ovx4 records).
- Pilot-log "16/16 meta rows in cycles 62-65" not reproduced: 11/15 pure meta, 2 mixed, 2 substantive (rohin213 FINAL_COUNTS.json).
- Hourly collector inconsistency: the 14:00 cut sets fork ACT_attempts to 0 for 08h/09h while earlier cuts reported 4-13 and ACTs_reaching_scorer stays 3-13 (R227_HOURLY_*.json cross-cut).
- Age testing is enrollment: 590 ages enrolled, 5 evaluated, 9.68 sources/hour, ~60 h backlog; frozen sibling 0 evaluated (rohin233_kept_age_probe_20260918/PROSPECTIVE_STATUS.md, QUEUE_COVERAGE.md).
- Base's scripted-parent epoch shows 19% pixels per scored vs 10.4% before, but a restart, 0 format faults and frozen weights confound it (medium; PARENT_RENDER_LATEST.json).
- Parent turns uneven: C2 13/14 opportunities in an hour, C1/C3/C4/C5 0 (rohin204_maintenance_20260917/STATUS.md).
- Node-3 forks lost judging at 12:34-13:07 UTC, parents at 14:01-14:45, natives reloaded 17:08-17:20; 30 transport failures in 13h (R227 hourly; rohin233_focus_node3_20260918/STATUS_LATEST.md).
- The "82 accepted in the first hour" base claim is not receipted in the audited files; the hourly collector gives 192/267 for 08-09 UTC under its own definitions (DEVELOPMENTAL_CURRICULUM_2026-09-18.md; R227_HOURLY_20260918T140005Z.json).

## Measurable behaviour

| behaviour | how measured | value(s) | life | source |
|---|---|---|---|---|
| Novelty per token | new-pixel events / 6.144k generated tokens | base 9.44; C2 s51 6.51; C2 s87 4.07; C0 s84 3.09; fresh s1 4.72; fresh s2 2.44 | probe conditions | MOVEMENT_CURVES.json; R233_FRESH_R231_s*_STATUS.json |
| Accepted per token | accepted / 6.144k | base 12.86; s51 11.56; fresh2 8.63; fresh1 8.30; C2-87 8.14; C0 3.91 | same | same |
| Late-cell exploration | pixels at cell tokens 512-1024 / total | base 0.72; C0 0.68; fresh1 0.52; s51 0.42; C2-87 0.24; fresh2 0.20 | same | MOVEMENT_CURVES seed_curves |
| Response fragmentation | tokens/response; prompt tokens | base 131, 61,931; s51 106, 92,306; C2-87 57, 194,560; C0 88, 95,982; fresh1 108; fresh2 104 | same | MOVEMENT_CURVES.json |
| Repetition among accepts | semantic repeats / accepted | base 450/549; P3 14/26; selfderive 7/26; probe fresh1 22/51, fresh2 38/53, s51 31/71, C2-87 25/50, base 21/79, C0 5/24 | game players; probe | R227_HOURLY_20260918T140005Z.json; MOVEMENT_CURVES |
| Acceptance rate | accepted / newly scored, 04:55-14:00 UTC | base 549/820; P3 26/212; selfderive 26/174; observation 10/118; unparented 2/40; revision 0/9; perspective 2/7 | continuous players | R227 hourly cumulative |
| Accepted per hour | accepted per UTC window | base 08h 192, 09h 117, 11h 36, 12h 114, 13h 90; P3 05h-11h 1, 4, 0, 3, 5, 6, 7; selfderive 09h 11, 10h 11, 11h 3, 12h 1 | base, P3, selfderive | R227 hourly; ovx2 INBOX |
| New pixels per ACT | new_pixels / ACT_attempts per window | base 08h 0.44, 09h 0.14, 11h 0.67, 12h 1.00, 13h 1.06; P3 05h-11h 1.00 to 0.00, none 12h-13h | base, P3 | R227 hourly |
| Accepts that are jokes | manual review of accepted texts | base 2/47 (24 descriptions, 18 weak, 3 variants); P3 5 captions / 16 plan sentences / 5 no text of 26; top rank 14/65 to a process sentence | base, P3 | R230_SEED_SELECTION_AUDIT_v1.json; node-4 INBOX |
| Judge scene-blindness | own-contest top beats other-contest top / 100 | widegap 51; BT8k 46; R210 step 15625 90 / 89; R210 selected 52.5 / 48.5 | judge | rohin207 reports; ovx5 CONTRAST.private.json |
| Judge garbage rejection | wins / 100 | widegap shuffled 100, description 100, nonsense 99, truncated 94; BT8k 100, 100, 67.5, 48.5 | judge | rohin207 reports |
| Judge mid-tier discrimination | wins / 100 | widegap 74; BT8k 56.5; R210 rank8 step 15625 77 | judge | same; ovx5 |
| Judge vs human rating | macro Spearman | rank8 0.2739 start, 0.2511 final; rank16 0.2772, 0.2453; best = first checkpoint | judge | ovx5 SPEARMAN.private.json |
| Relevance gate leniency | mismatched rejected / 100; matched preferred | 25/100; 71/100 | gate | RELEVANCE_PROBE.json |
| Format faults | fault attempts / ACT attempts | base 114/207; P3 41/48; selfderive 42/38; observation 39/41; unparented 30/38; revision 48/40; perspective 52/35 | continuous players | R227 hourly |
| Transport failures | 13:00-14:00 UTC | 6 per fork, 30 total, 0 reaching scorer | five forks | R227 hourly |
| Intention-only vs content ACTs | quoted string >= 15 chars, or arithmetic '=', or R227 heuristic | P3 31 content / 65 plan of 98 (10h-16h 5/59); C2 7 = 1 I + 5 W + 1 U; P7 10 = 4 I + 0 W + 6 U; learner 21/23; frozen 39/48; 32-ACT cut 26 concrete, 2 intent, 2 plan, 2 meta | P3, C2, P7, pair, 16 lives | node-4 records; rohin227 snapshots; ovx4 records; rohin233 REPORT.json |
| Excerpt replies | paragraph promised vs written | 4 promised / 0 written; 76-99 chars, 88-92% CJK | P7 | SCALE_physical7 INBOX 1663-1935 |
| Correction uptake level | reviewed traces, levels 0/1/2/3 | 21 traces: 14 / 5 / 2 / 0; unreviewed 2323/2344 | 18 lives | rohin232 CURRENT.json |
| Movement after feedback | status per life | lexical_change_only 4; no_checked_resolution 3; artifact_absent 2; partial_uptake 2; not_applied 1; task_switch 1; unverified 1; artifact_emerges 1; emerges_runtime_rejects 1; checked-correct 2 lives | 16 lives | rohin233 REPORT.json |
| Correction named, not applied | LEARN names fix, next ACT ignores | 3/3 cycles 42-44 | C2 | C2_PILOT_LOG lines 44-69 |
| Flagged phrase frequency | "I will assume" before/after 07:29:48 UTC | 5/238 to 51/158 | C2 | ovx3 records |
| Parent abandoning corrections | Astra turns with "set aside" / "repeat" | 29/153 and 39/153 | C2 | ovx3 records |
| Meta-head opener | regex on first 120 chars | 0/153 first 51 sleeps; 122/237 after first R191 row; late THINK 61/61, ACT 0/31, LEARN 2/31; C0 0/148 | C2, C0 | ovx3, ovx records |
| Heading template | Line judgment / Next artifact heads | C0 89/148, late THINK 34/37, LEARN 27/30; C2 48/392 | C0, C2 | same |
| Meta rows trained | manual class of trained rows | sleeps 62-65: 15 trained = 11 META, 2 MIXED, 2 SUBST; sleeps 59-65: 25 = 18 META, 4 MIXED, 2 SUBST, 1 UNC; sleeps 40-65 presentations META 802, SUBST 452, MIXED 279, UNC 16 | C2 original | rohin213 FINAL_COUNTS.json |
| Zero-step sleeps / excluded rows | SLEEP_COMPLETE, R195 | C0 8/47 zero-step, 68/141 NEW excluded; C2 0 zero-step, 68 excluded of 234 rows | C0, C2 | ovx, ovx3 records |
| Training dose | rows x presentations; steps | C2 7532 steps / 110 sleeps; C0 1248 / 47 (6156 incl. inherited 4908); learner 1104 = 23 x 48; frozen 0 | C2, C0, pair | SLEEP_COMPLETE records |
| Recall after sleep | probe response class | C0 16 probes: 0 recall, 2 honest no-memory, 2 echo, 1 confabulation (6-response run), 11 subject change; P7 6 prompts, "Iona" 0/319, 1 Chinese partial naming "Asta"; C2 0/1/4 (report claim) | C0, P7, C2 | ovx records; SCALE_physical7; R233_STATUS.md |
| Arithmetic correctness | regex a op b = c checked | C0 65/67; C2 5/5 | C0, C2 | c2c0 scan (medium) |
| Checked math on shared object | correct vs wrong final values on 17+8-6 | learner 17 vs 18; frozen 51 vs 7; 23+9-7 learner 10 vs 1; 34-15+7 frozen 15 vs 7; 42-18+9 4 vs 0; 43-16+8 0 attempts | pair | ovx4 records |
| Simplest task completion | 6+3=9 written / mentions / reminders | 0 / 13 / 8 over 64 min | learner | ovx4 records |
| Stage-0 streak | parent "I count" statements; max streak | learner one x1, two x2, max 2; frozen first x1, one x9, two x3, max 2; 0 advances | pair | ovx4 INBOX |
| Math-trio answers | stated counts (correct 12; 25) | A 11 to 12; C 26 responses state 12; B never settled; div-4 0/3, C 60 in 198 places | math a, b, c | ovx2 records (medium) |
| Astra7 arithmetic | responses with arithmetic; V stated | 4/125, all broken code; 0 V values | Astra7 | ovx orch_r229 records |
| CJK drift | responses containing CJK, by thirds or hour | C2 23/132, 13/132, 9/132; C0 9/49, 16/49, 8/50, max run 6; learner 30/69; frozen 3/144; P7 hourly 0.4% to 78.4%; Astra7 4.5% to 60.2%; frozen no-adapter control 164/194; forks 2.4-13.9%; ranked CJK captions 63/180 all rank 63-65 | fleet | node records; CHILDREN_DISTILLED |
| Fullwidth drift | responses with fullwidth chars | learner 53/69; frozen 2/144; C2 bins 4/15 (s0-4), 11/15 (s35-39), 10/15 (s45-49) | pair, C2 | ovx4; C2_PILOT_LOG |
| Language-correction uptake | next response CJK-free; relapse | 4/4 immediate; C0 relapse 8 min; P7 07h 65.8% to 08h 8.1% to 09h 45.3% | C0, C2, P7 | node records |
| Repetition | exact dups; fuzzy Jaccard > 0.6; templates | C2 8/392; C0 0/148; pair 0/69, 0/144; P3 exact 0/292, fuzzy 14h 59%; P7 template 145/319, 100% 10h-17h, 6 identical rows trained, 12 repeats after ban; node-1 templates 79/120, 41/123, 34/117 | fleet | node records; FLEET_BEHAVIOUR 3.3 |
| Novelty per token (text) | unseen 5-gram fraction by thirds | C2 0.59 / 0.87 / 0.77; C0 0.74 / 0.69 / 0.65 | C2, C0 | c2c0 scan |
| State-JSON in responses | THINK_ACT_STATE present | learner 69/69; frozen 97/144 | pair | ovx4 records |
| Working-state only, no arithmetic | responses | 2/69; 2/144 | pair | ovx4 records |
| Parent-turn counts | INBOX by speaker | C2 Astra 153, Rohin 18; C0 Astra 77, Rohin 0; learner 24 (7.1/h); frozen 49 (14.9/h); P3 Astra 40, Rohin 2; P7 Astra 77, Rohin 7; forks 25/26/24/25/12; math 68/66/73; Astra7 P7 34, Astra 0; 05:54 UTC hour C2 13/14, C1/C3/C4/C5 0 | fleet | node records; rohin204 STATUS.md |
| Parent flags | turns naming language / copying / wrong object | learner 17/24, 18/24, 9/24; frozen 3/49, 23/49, 16/49 | pair | ovx4 INBOX |
| Response latency | INBOX to next RESPONSE | C2 Rohin median 0.4 min; Astra 0.6 (p90 11.0); C0 Astra 3.3 (p90 8.7) | C2, C0 | c2c0 scan |
| Parent/judge gaps | last turn to scan | P3 parent 140 min (last 14:45 UTC), last ranked judgment 11:29; forks judge end 12:34-13:07, parent 14:01-14:04; math 14:12-14:14 | P3, forks, math | node records |
| Cycle cadence | median sleep-to-sleep | learner 9.1 min; frozen 4.1 min; C2 10.1 responses/h; C0 21.1/h | pair, C2, C0 | node records |
| Cycle decision declared | explicit continue/branch/stop | UNKNOWN 14/14; inferred CONTINUE 6, BRANCH 1 | P3 cycles 69-82 | rohin228 P3_RECEIPT_CUT.json |
| Role inversion | responses treating Astra as trainee; direct addresses to child | 39/319 from 08:43:34 UTC; 0 addresses; 3/144 mention child | P7 | SCALE_physical7 records |
| Unreceipted claims | claims without execution receipt per 18 | C4 11, 3, 1; support_free 6, 2, 1; C5 invented MSEs 6/6 | 09-17 lineage | FLEET_BEHAVIOUR 2.2, 3.2 |
| Execution receipts | census | node 1: 0 in 8 journals; node 3: 0 in 6; node 4: 1 rejection; C2 25 COMPLETE of 69 ACTs; C0 0/47 (no executor) | fleet | FLEET_BEHAVIOUR 3.2; ovx3, ovx records |
| Taught-behaviour uptake | 19 taught behaviours by evidence | expressed 3 + convention 1; partial 5; restated 2; none 8; all in-context | C2 | C2_TAUGHT_BEHAVIOURS_2026-09-18.md (medium) |
| Object survival in weights | P0 empty-context probe ON vs OFF | knight ON 11/18, OFF 0/18; war plan 0/36 | raw_unparented | OBJECT_SURVIVAL_FIRST_READ (medium) |
| Guidance delivered to base | envelopes / texts / tokens | 9 / 6 / 1028, 0 bridge errors | frozen base R233 epoch | PARENT_RENDER_LATEST.json |
| Age-probe coverage | evaluated / enrolled; throughput | 5 / 590; 9.68 sources/h; frozen sibling 0 | 16 journals | PROSPECTIVE_STATUS.md |
| Judge throughput | pairs/s | 8.42 (1 A40) vs 30.69 / 30.54 (4 GPUs) | judge | CAPTION_GAME_AUDIT; ovx5 UPDATE_015625.json |

## What is claimable for the abstract today, and what is not

Claimable (matched or receipted):
- At a fixed 6144-token parent-free budget with identical scenes, seeds, decoder and scorer, embedding-novelty per token falls with age inside both lineages that have two ages, and every trained child sits below the frozen base (2 seeds x 3 scenes; novelty, not humour).
- The live judge is scene-blind (51/100) but rejects garbage (94-100/100) and separates top from mid-tier (74/100) on development contests; a crossed-scene loss raises scene awareness to 88-90% at a Spearman cost of 0.01-0.07.
- In a matched birth pair, neither the learning nor the frozen arm reached stage 1 in ~200 live minutes; the learner alone drifted to CJK (43% vs 2%) and state-JSON dumps (100% vs 67%). One life per arm: report as an observation, not a result.
- Sleep on own outputs installs form: the meta opener appears only after training rows begin and 52% of C2's presentations in sleeps 40-65 were meta rows; language drift also occurs in a never-trained control, so drift alone is not a training effect.
- Training receipts reconcile end to end (1549 presentations).

Not claimable:
- H1 (weight-level retention of taught content): no ON-not-OFF result on any parented or retelling life; the one raw-child birth-sentence result is lexical and medium confidence; adapter_improvement is unknown for all 16 lives; recall after sleep is 0 true recalls.
- H2 (parented or learning child beats frozen or unparented at a matched comparison): every continuous-game comparison is unmatched in budget, start time, parenting and attempt unit; the one matched datum is n=1; the frozen sibling was never age-probed.
- "Accepted captions" as jokes or distinct ideas: 2/47 base accepts joke-like, 16/26 P3 accepts are plan sentences, judge is text-only.
- Any level-3 (unreminded) correction: 0 observed, no test window has existed.
- Selfderive fork improvement from parenting or sleep: acceptances front-loaded, best predates feedback, 0 after 12:01 UTC.
- Base novelty rise under the scripted parent: confounded by restart and zero faults.

## Verification notes

- game: confirmed. Fragmentation numbers reproduce exactly; the 2.11x prompt-token figure is mostly the 1.86x response-count effect (prompt per response 1591 to 1801).
- judge: adjusted. Contrast counts reproduce exactly; "12.5x more pairs" is wrong, widegap is a warm start of the BT8k step-300 adapter (2,400 comparisons) plus 100k wide-gap pairs with a changed objective; development contests were reused for selection.
- audits: adjusted. V=3 derivation reproduces; 5863 is a THINK not an ACT; its restatement was trained x16 at sleep 52; "~15 h" is at most ~12.2 h; every later V=3 had the answer in prompt.
- c2c0: adjusted. CJK counts reproduce; C2's decline is chiefly a birth-hour burst; "73/77 Use English" is 73/77 turns mentioning English (49 literal); C0 ran 22% CJK under the same quarantine.
- pair: confirmed. Identical prompt and adapter hashes, frozen 48 no-op sleeps, learner 1104 updates, parent texts disjoint; caveat that the frozen arm ran 2x cycles per wall hour.
- players: adjusted (verdict truncated in input). Selfderive 26/19 reproduce; acceptances front-loaded and collapse after 12:01 UTC; best caption predates judge feedback; all on one scene; "genuine scene captions" overstates a text-only judge.
- Seventh verdict: not present in the input.

## Gaps

- No matched learner-vs-frozen or parented-vs-unparented game comparison exists; the continuous game differs in budget, start time, scene roster and attempt unit per player, and the frozen sibling has 0 evaluated ages.
- Age curves rest on six 6144-token probes; 585 enrolled ages await capture at ~10 sources/hour on one lane.
- No unreminded-transfer window has been observed, so level 3 cannot be measured; 99% of feedback candidates are unreviewed.
- Humour is not measured: 9 of 200 probe accepts and 47 base strings have been read by a human; the judge is text-only and scene-blind, so scene fit is unmeasurable with the bound judge.
- Recall probes lack a context-free design; the one apparent P7 success had the answer quoted in the question.
- Execution receipts are absent on nodes 1 and 3 and C0 has no executor, so correctness of most claimed work cannot be checked.
- Token counts are not in the life records, so novelty per token is only available from the probe, not from continuous lives.
- The hourly collector's ACT_attempts field is inconsistent across cuts for node-3 forks, and the 33/41/8 literal audit and the 82-accepted first-hour figure have no receipt in the checkout.

---
Provenance: produced 2026-09-18 17:00–17:49Z by a 15-agent read-only workflow launched by Fable (7 dimension readers over repo files and node records, 6 adversarial verifiers re-deriving each reader's top claim, 1 writer; 279 tool uses). Every number is to be read against the cited file or record range; nothing here is a paper claim until Rohin says so.
