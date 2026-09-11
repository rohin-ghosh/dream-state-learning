# Affect-language probe: does the child's own appraisal language predict a change of action? (2026-09-11)

Rohin's "cheap first test" for an appraisal/emotional gym. Correlational, lexicon-based, CPU-only, run on
node 1 over the 11 `{R2,R3,R4,RP}_B_seed*` life ledgers. Script:
`research_notes/analysis/affect_language_probe.py`; raw results:
`research_notes/analysis/affect_language_probe_results_2026-09-11.json`. Every number below carries its
count; nothing is copied by hand from anywhere except that JSON and the script's stdout.

## TL;DR

- **Pooled, brief's definition (unit = thought at tick t; changed = first act at tick >= t differs from the last
  act at tick < t):** P(change | any affect word) = 9523/46747 = **0.204** vs P(change | no affect word) =
  7737/49389 = **0.157**; diff +0.047 [95% CI +0.042, +0.052], OR 1.38, Fisher p = 1.6e-80. The sign is **not
  stable across arms**: R2 -0.015 (2769/17944 vs 1367/8067), R3 +0.230 (3120/9099 vs 2298/20330), R4 -0.075
  (3295/17528 vs 2890/10981), RP +0.038 (339/2176 vs 1182/10011). Per life: 5 positive (p<0.001), 1 reversed
  (R4_B_seed606: 1975/6424 = 0.307 vs 2184/4939 = 0.442), 5 not significant. In the act-aligned unit (text
  since the previous executed act) the pooled difference vanishes: 10930/59291 = 0.184 vs 19549/108194 = 0.181.
- **The one class that behaves is NEGATIVE appraisal** ("not working", "fail*", "worse", "wrong", negated
  positives such as "no improvement"): pooled 1130/3943 = **0.287** vs 0.157 (diff +0.130, OR 2.16, p = 3.4e-86);
  positive with p<0.001 in **10 of 11 lives**, reversed in R4_B_seed606 (157/576 = 0.273 vs 0.442). It survives
  stratification by the previous act's outcome (after a no-progress act: 665/747 = 0.890 vs 4828/5907 = 0.817;
  after a productive act: 465/3196 = 0.145 vs 2909/43482 = 0.067). But negative appraisal is **rare**: 3943 of
  96136 eligible thoughts (4.1%).
- **Control says the effect size is not special.** Neutral topical words produce associations as large or
  larger: "further" 1985/5059 = 0.392 vs 15275/91077 = 0.168 (+0.225); "loop*" 5123/15431 = 0.332 vs 0.150
  (+0.182); "memory" 218/404 = 0.540 vs 0.178 (+0.362); while "passes" is *negative* (12482/74519 = 0.168 vs
  4778/21617 = 0.221). Any word that marks "the child is deliberating about a new plan" predicts change about as
  well as negative affect does.
- **The outcome, not the affect word, is the driver.** After an INVALID or zero-reduction act the child changes
  its action 81% of the time with or without affect language (5293/6536 = 0.810 vs 4828/5907 = 0.817); after a
  productive act, 0.105 vs 0.067 (4230/40211 vs 2909/43482).
- **Explicit change intent is coupled to action; affect is not.** "try something different / instead / switch
  to / different approach": 441/882 = **0.500** vs 16819/95254 = 0.177 in the thought unit (OR 4.66), 558/973 =
  **0.573** vs 29921/166512 = 0.180 in the act unit (OR 6.14), positive in all 11 lives (per-life act-unit rates
  0.37-0.92). But it is written in only 882/96136 = 0.9% of thoughts, and even then the child repeats the same
  action ~45% of the time.
- **SURPRISE is ritual, not appraisal.** 47526 "surpris*" hits in 119594 thoughts, only 2018 distinct
  normalised sentences; three fixed sentences ("reality, learning from surprises" 13377; "reality will surprise
  me, and i will learn from it" 9647; "open to surprise and learning" 2113) account for 25137/47526 = 53%. They
  echo the bootstrap prompt. P(change | surprise) = 2840/18196 = 0.156 = the non-affect baseline (0.157).
- **The hot emotional vocabulary is essentially absent.** In 119594 thoughts: "worried" 0, "hopeless" 0, "give
  up" 0, "excited" 0, "good progress" 3, "frustrat*" 8, "confus*" 8, "disappoint*" 15, "stuck" 41. What exists is
  cool evaluative language (improv* 20135, success* 42742, better 6823, unexpected 2843, fail* 548, not working 357).
- **Ritualisation.** Affect rate is 3440/3942 = 0.873 of thoughts in the first 32-episode window of each life
  (frozen child, long free prose) and 9623/15210 = 0.633 in the last four windows, but 17515/17930 = **97.7%** of
  late-life affect hits are a (phrase, sentence) pair already written earlier in the same life. Three lives stop
  producing affect words almost entirely (R3_B_seed501 last four windows 0.01/0.00/0.00/0.00; R3_B_seed502
  0.06/0.04/0.07/0.02; R2_B_seed6 0.09/0.06/0.09/0.12).

**Reading for the appraisal-gym decision:** the substrate the gym would build on is thin. There is no rich,
spontaneous appraisal signal that already steers behaviour. What steers the next action is (a) the harness
outcome and (b) the occasional explicit plan statement. Negative appraisals do carry a real, small, consistent
hook (present in 10/11 lives, 45-47% change after "not working"/"fail*" vs 16%), concentrated in long
deliberative chunks (>1000 chars of prose: 550/1337 = 0.411 vs 420/2805 = 0.150), but its size is matched by
neutral plan-topic words. An appraisal gym would have to *create* an appraisal-to-action coupling (and the
appraisal vocabulary itself), not amplify an existing one.

## 1. Question

Does affect/appraisal language the frozen or adapted child ALREADY produces in its thought stream predict a
change in its next action? If appraisal words are followed by a different action more often than non-affect
thoughts are, the substrate for an appraisal gym exists.

## 2. Data covered and how it differs from the brief

Snapshot of `~/v6_out/{R2,R3,R4,RP}_B_seed*/ledger.jsonl` on node 1 at 2026-09-11 ~07:57 node time. The
three R4 lives were **still running** (row counts grew between my first listing and the run: R4_B_seed605
46193 -> 46467, R4_B_seed606 39861 -> 40140); they are included as partial lives (736/648/896 episode
instances). R2_B_seed0/1 (1032) and RP (1048) have slightly more than 1024 instances, consistent with a re-run
wake batch after a restart; counted as-is.

| life | arm | ledger rows | episode instances (invalid) | thoughts | thoughts with any affect hit | eligible (A) | acts scored (B) | thoughts cut at 2000 chars | thoughts echoing harness format |
|---|---|---|---|---|---|---|---|---|---|
| R2_B_seed0 | R2 | 43610 | 1032 (0) | 15100 | 10197 | 10360 | 15211 | 25 | 14477 |
| R2_B_seed1 | R2 | 57336 | 1032 (0) | 14047 | 11126 | 12035 | 20743 | 7 | 8656 |
| R2_B_seed5 | R2 | 22095 | 1024 (0) | 4535 | 1641 | 2749 | 8488 | 1 | 1563 |
| R2_B_seed6 | R2 | 9764 | 1024 (0) | 2310 | 1074 | 867 | 2444 | 38 | 2054 |
| R3_B_seed500 | R3 | 48289 | 1024 (0) | 10902 | 8054 | 9205 | 19132 | 7 | 8352 |
| R3_B_seed501 | R3 | 60246 | 1024 (0) | 12800 | 822 | 11414 | 22234 | 12 | 4417 |
| R3_B_seed502 | R3 | 43227 | 1024 (0) | 10021 | 1878 | 8810 | 15602 | 12 | 6628 |
| R4_B_seed604 | R4 | 33056 | 736 (0) | 11147 | 7334 | 8253 | 10258 | 18 | 5249 |
| R4_B_seed605 | R4 | 46467 | 648 (0) | 9780 | 6372 | 8893 | 17787 | 2 | 7798 |
| R4_B_seed606 | R4 | 40140 | 896 (0) | 13739 | 7742 | 11363 | 12857 | 36 | 4217 |
| RP_B_seed402 | RP | 61247 | 1048 (0) | 15213 | 3730 | 12187 | 22729 | 16 | 11493 |
| **pooled** | | 465477 | 10512 (0) | 119594 | 59970 | 96136 | 167485 | 174 | 74904 |

Ledger facts that differ from the brief (all verified against `organism_v6/batch_loop.py`, the writer):

1. `kind` takes exactly three values: `act`, `note`, `thought`. There are no `outcome`/`predict`/`recall` rows.
   The thought text is in the field `note` (not `text`); `act` rows carry `action`, `prediction`, `outcome`,
   `score`, `surprise`, `time_cost`; thought rows also carry `prompt` (the full 24k-char context), `win`
   (best score improved this chunk) and `had_note`.
2. `episode_id` is the **benchmark name** and is revisited ~15 times per life (67 distinct ids, 1024 episodes).
   Eight episodes run in lockstep per wake batch, so `tick` (chunk 1..16) restarts per episode instance and
   `(episode_id, tick)` is not unique (1072 = 67 x 16 collisions per life). Instances were re-segmented (a tick-1
   row following that benchmark's previous thought row starts a new instance); all 10512 instances have
   consecutive ticks 1..T and one thought per tick (0 invalid).
3. One thought (chunk) can contain **several `ACT:` lines**, all executed in order after the chunk is generated
   (167485 acts scored vs 96136 eligible thoughts). The `[OUTCOME] ...`, `OPEN SURPRISES` and `RECALLED
   EXPERIENCE` blocks that appear *inside* thoughts are the **child echoing harness format** - the harness never
   injects text into a chunk - i.e. hallucinated outcomes. 74904/119594 = 63% of thoughts contain such echoes.
   All harness-shaped lines are stripped before matching (so the word "surprise" in an echoed "OPEN SURPRISES"
   header is never counted), but affect language written after a hallucinated outcome is a reaction to an
   imagined result, not a measured one.
4. `note` is truncated to 2000 characters by the writer (174 thoughts hit the cap). Text/act alignment failed in
   exactly 1 chunk (RP_B_seed402); that act was excluded from unit (B).
5. No scipy on the node; Fisher's exact test is implemented in the script (two-sided, lgamma), cross-checked on
   textbook tables (3,1,1,3 -> 0.4857). Pearson chi-square is reported alongside in the JSON.

## 3. Method

**Units.** (A) *Thought-level, the brief's definition*: for the thought at tick t of an instance, `changed` =
the first executed act at tick >= t differs from the last executed act at tick < t (normalised: whitespace
stripped, lower-cased, order kept); `approach changed` = the set of passes differs. Thoughts with no previous
act in the instance are skipped (the 96136 "eligible" thoughts; 86122/96136 = 90% take their next act from
the same tick, 10014 from a later tick; a further 11226 thoughts had a previous act but no later act and were
dropped). (B) *Act-aligned*: for every executed act after the first in an instance, the
"thought" is the child's cleaned prose written since the previous executed act (across chunk boundaries), and
`changed` = this act differs from the previous act. (B) respects the within-chunk order when a chunk carries
several acts; (A) attributes the whole chunk to its first act.

**Cleaning.** Lines shaped like harness output or markers (`[OUTCOME]`, `CLOCK:`, `===`, `GOAL:`, `METRIC:`,
`BEST SCORE THIS EPISODE`, `LAST OUTCOME`, `OPEN SURPRISES`, `YOUR NOTES`, `RECALLED EXPERIENCE`, `PREDICT`,
`ACT`, `DONE`, "predicted X, got Y for:" items) are dropped; `NOTE:`/`RECALL:` prefixes are removed and their
bodies kept. Matching is case-insensitive with word boundaries on the cleaned prose only, never on `action`
strings or `outcome` fields.

**Lexicon** (regexes as run; auditable in `results.json["lexicon"]`):

| class | phrase label | regex |
|---|---|---|
| NEGATIVE | stuck | `\bstuck\b` |
| NEGATIVE | frustrat* | `\bfrustrat\w*` |
| NEGATIVE | not working | `\b(is not|isn't|not|doesn't|does not|didn't|did not|hasn't|has not|wasn't|was not|aren't|won't|will not|never|no longer)\s+(seem(s|ed)? to\s+)?(be\s+)?(really|actually|quite)?\s*work(ing|ed|s)?\b` |
| NEGATIVE | fail* | `\bfail\w*` |
| NEGATIVE | worse | `\bworse\b` |
| NEGATIVE | wrong | `\bwrong\b` |
| NEGATIVE | confus* | `\bconfus\w*` |
| NEGATIVE | unsure | `\bunsure\b` |
| NEGATIVE | worried | `\bworr(ied|y|ying|ies|isome)\b` |
| NEGATIVE | hopeless | `\bhopeless\w*` |
| NEGATIVE | give up | `\b(give|giving|gave|given)\s+up\b` |
| NEGATIVE | disappoint* | `\bdisappoint\w*` |
| NEGATIVE | unexpected | `\bunexpected(ly)?\b` |
| NEGATIVE | neg(<positive>) | a POSITIVE hit preceded within 3 tokens on its line by a negator (no, not, n't, never, without, didn't, doesn't, don't, hasn't, haven't, isn't, wasn't, weren't, aren't, won't, cannot, can't, couldn't, little, lack(s/ing), hardly, barely, nor, neither) |
| SURPRISE | surpris* | `\bsurpris\w*` (tagged separately, never pooled into NEGATIVE/POSITIVE) |
| POSITIVE | good progress | `\bgood\s+progress\b` |
| POSITIVE | better | `\bbetter\b` |
| POSITIVE | works/worked | `\bwork(s|ed)\b` (dropped when inside a "not working" span) |
| POSITIVE | confident | `\bconfident(ly)?\b` |
| POSITIVE | promising | `\bpromising\b` |
| POSITIVE | excited | `\bexcit(ed|ing)\b` |
| POSITIVE | great | `\bgreat\b` |
| POSITIVE | improv* | `\bimprov\w*` |
| POSITIVE | success* | `\bsuccess\w*` |
| CHANGE_INTENT (positive control, never pooled into affect) | try something different/new; different approach/strategy/set/combination/passes; switch(ing) to; instead; chang(e/ing) (my/the) approach/strategy/tack/course | see script |
| NEUTRAL (control) | passes, program, instruction*, loop*, benchmark, reduction, memory, score, apply/applied, further | word-boundary regexes |

"Affect" = any NEGATIVE, POSITIVE or SURPRISE hit. For the AFFECT_ANY / NEGATIVE / POSITIVE / SURPRISE / per-phrase
rows the "absent" group is always *thoughts with no affect hit of any class*; for CHANGE_INTENT and NEUTRAL rows
it is thoughts without that class. **Zero-hit lexicon entries over all 119594 thoughts: worried, hopeless, give
up, excited.** Total hits per phrase (all thoughts): surpris* 47526, success* 42742, improv* 20135, works/worked
10958, better 6823, neg(improv*) 3020, unexpected 2843, unsure 665, fail* 548, not working 357, promising 215,
wrong 143, confident 83, worse 65, neg(better) 61, stuck 41, great 24, neg(success*) 18, disappoint* 15,
confus* 8, frustrat* 8, good progress 3.

**Statistics.** 2x2 tables with two-sided Fisher exact p, risk difference with Wald 95% CI, odds ratio. Thoughts
are autocorrelated within an episode instance, so p-values are anti-conservative; treat them as ordering, not as
evidence strength. Effect sizes with counts are the object of interest.

## 4. Results

### 4.1 Pooled over 11 lives

**(A) thought-level (brief's definition)** - 96136 eligible thoughts; base change rate 17260/96136 = 0.180.

| class | P(change given present) | P(change given absent) | diff [95% CI] | OR | Fisher p | approach change (set differs), present vs absent |
|---|---|---|---|---|---|---|
| AFFECT_ANY | 9523/46747 = 0.204 | 7737/49389 = 0.157 | +0.047 [+0.042, +0.052] | 1.38 | 1.6e-80 | 0.194 vs 0.147 |
| NEGATIVE | 1130/3943 = 0.287 | 7737/49389 = 0.157 | +0.130 [+0.115, +0.144] | 2.16 | 3.4e-86 | 0.275 vs 0.147 |
| POSITIVE | 7610/33311 = 0.228 | 7737/49389 = 0.157 | +0.072 [+0.066, +0.077] | 1.59 | 1.7e-147 | 0.216 vs 0.147 |
| SURPRISE | 2840/18196 = 0.156 | 7737/49389 = 0.157 | -0.001 [-0.007, +0.006] | 1.00 | 0.86 | 0.147 vs 0.147 |
| CHANGE_INTENT (positive control) | 441/882 = 0.500 | 16819/95254 = 0.177 | +0.323 [+0.290, +0.357] | 4.66 | 9.7e-105 | 0.456 vs 0.167 |
| NEUTRAL_ANY (any of 10 neutral words) | 16342/92663 = 0.176 | 918/3473 = 0.264 | -0.088 [-0.103, -0.073] | 0.60 | 1.8e-36 | 0.167 vs 0.228 |

**(B) act-aligned** - 167485 acts scored; base change rate 30479/167485 = 0.182.

| class | P(change given present) | P(change given absent) | diff [95% CI] | OR | Fisher p | approach change, present vs absent |
|---|---|---|---|---|---|---|
| AFFECT_ANY | 10930/59291 = 0.184 | 19549/108194 = 0.181 | +0.004 [-0.000, +0.008] | 1.02 | 0.064 | 0.177 vs 0.176 |
| NEGATIVE | 922/3799 = 0.243 | 19549/108194 = 0.181 | +0.062 [+0.048, +0.076] | 1.45 | 6.7e-21 | 0.235 vs 0.176 |
| POSITIVE | 8933/42231 = 0.212 | 19549/108194 = 0.181 | +0.031 [+0.026, +0.035] | 1.22 | 3.8e-42 | 0.202 vs 0.176 |
| SURPRISE | 2608/21427 = 0.122 | 19549/108194 = 0.181 | -0.059 [-0.064, -0.054] | 0.63 | 2.6e-104 | 0.116 vs 0.176 |
| CHANGE_INTENT | 558/973 = 0.573 | 29921/166512 = 0.180 | +0.394 [+0.363, +0.425] | 6.14 | 2.7e-164 | 0.483 vs 0.174 |
| NEUTRAL_ANY | 21882/143488 = 0.153 | 8597/23997 = 0.358 | -0.206 [-0.212, -0.199] | 0.32 | ~0 | 0.147 vs 0.352 |

Note the NEUTRAL_ANY "absent" group: acts preceded by prose containing none of ten common domain words are
mostly acts preceded by *no prose at all* (a bare `ACT:` line). Silent acts change more often than commented
ones: in (A), thoughts with zero cleaned prose changed 418/731 = 0.572 times; in (B) the empty-text rate ranges
0.206 (R2_B_seed0, 138/671) to 0.816 (R3_B_seed502, 652/799) against 0.078-0.328 for commented acts. This is the
child cycling through candidate pass lists without commentary.

### 4.2 Per arm (A, order-sensitive change)

| arm | AFFECT_ANY present vs absent | NEGATIVE | POSITIVE | SURPRISE | CHANGE_INTENT |
|---|---|---|---|---|---|
| R2 (4 lives) | 2769/17944 = 0.154 vs 1367/8067 = 0.169 (-0.015, p 0.002) | 469/1339 = 0.350 (+0.181) | 1375/7480 = 0.184 (+0.014) | 1665/13274 = 0.125 (-0.044) | 145/253 = 0.573 vs 3991/25758 = 0.155 |
| R3 (3 lives) | 3120/9099 = 0.343 vs 2298/20330 = 0.113 (+0.230) | 239/861 = 0.278 (+0.165) | 2941/7991 = 0.368 (+0.255) | 285/1063 = 0.268 (+0.155) | 112/259 = 0.432 vs 5306/29170 = 0.182 |
| R4 (3 lives, running) | 3295/17528 = 0.188 vs 2890/10981 = 0.263 (-0.075) | 368/1518 = 0.242 (-0.021, p 0.086) | 2997/16156 = 0.186 (-0.078) | 859/3436 = 0.250 (-0.013, p 0.13) | 166/342 = 0.485 vs 6019/28167 = 0.214 |
| RP (1 life) | 339/2176 = 0.156 vs 1182/10011 = 0.118 (+0.038) | 54/225 = 0.240 (+0.122) | 297/1684 = 0.176 (+0.058) | 31/423 = 0.073 (-0.045) | 18/28 = 0.643 vs 1503/12159 = 0.124 |

The R2 reversal is the SURPRISE ritual: 13274 of R2's 17944 affect thoughts are "surprise" thoughts, and those
change *less* (0.125) than the baseline. The R4 reversal is one life, R4_B_seed606 (below).

### 4.3 Per life (A)

`*` = Fisher p < 0.001. Baseline = thoughts with no affect hit.

| life | arm | NEGATIVE | POSITIVE | SURPRISE | CHANGE_INTENT | non-affect baseline |
|---|---|---|---|---|---|---|
| R2_B_seed0 | R2 | 261/882 = 0.296* | 408/1514 = 0.269* | 1063/6031 = 0.176 | 43/71 = 0.606* | 594/3456 = 0.172 |
| R2_B_seed1 | R2 | 77/214 = 0.360* | 593/4854 = 0.122* | 524/6917 = 0.076 | 24/56 = 0.429* | 215/2406 = 0.089 |
| R2_B_seed5 | R2 | 66/153 = 0.431* | 202/769 = 0.263 | 44/274 = 0.161 | 33/42 = 0.786* | 396/1747 = 0.227 |
| R2_B_seed6 | R2 | 65/90 = 0.722* | 172/343 = 0.501* | 34/52 = 0.654* | 45/84 = 0.536 | 162/458 = 0.354 |
| R3_B_seed500 | R3 | 95/152 = 0.625* | 2432/6654 = 0.365* | 179/485 = 0.369* | 33/76 = 0.434 | 416/2356 = 0.177 |
| R3_B_seed501 | R3 | 43/213 = 0.202* | 168/442 = 0.380* | 14/69 = 0.203 | 11/13 = 0.846* | 1146/10799 = 0.106 |
| R3_B_seed502 | R3 | 101/496 = 0.204* | 341/895 = 0.381* | 92/509 = 0.181* | 68/170 = 0.400* | 736/7175 = 0.103 |
| R4_B_seed604 | R4 | 126/721 = 0.175* | 489/4973 = 0.098 | 32/302 = 0.106 | 53/102 = 0.520* | 280/2937 = 0.095 |
| R4_B_seed605 | R4 | 85/221 = 0.385* | 760/5577 = 0.136 | 40/212 = 0.189 | 95/211 = 0.450* | 426/3105 = 0.137 |
| R4_B_seed606 | R4 | 157/576 = 0.273* (reversed) | 1748/5606 = 0.312* (reversed) | 787/2922 = 0.269* (reversed) | 18/29 = 0.621 | 2184/4939 = 0.442 |
| RP_B_seed402 | RP | 54/225 = 0.240* | 297/1684 = 0.176* | 31/423 = 0.073 | 18/28 = 0.643* | 1182/10011 = 0.118 |

Sign consistency across the 11 lives (positive p<0.001 / reversed p<0.001 / not significant): NEGATIVE 10/1/0;
POSITIVE 7/1/3; SURPRISE 3/1/7; CHANGE_INTENT 8/0/3; AFFECT_ANY 5/1/5. AFFECT_ANY per life (A): R2_B_seed0
1344/6904 = 0.195 vs 594/3456 = 0.172; R2_B_seed1 958/9629 = 0.099 vs 215/2406 = 0.089; R2_B_seed5 253/1002 =
0.252 vs 396/1747 = 0.227; R2_B_seed6 214/409 = 0.523 vs 162/458 = 0.354; R3_B_seed500 2491/6849 = 0.364 vs
416/2356 = 0.177; R3_B_seed501 181/615 = 0.294 vs 1146/10799 = 0.106; R3_B_seed502 448/1635 = 0.274 vs 736/7175
= 0.103; R4_B_seed604 521/5316 = 0.098 vs 280/2937 = 0.095; R4_B_seed605 799/5788 = 0.138 vs 426/3105 = 0.137;
R4_B_seed606 1975/6424 = 0.307 vs 2184/4939 = 0.442; RP_B_seed402 339/2176 = 0.156 vs 1182/10011 = 0.118.

R4_B_seed606's reversal: its non-affect thoughts change 44% of the time - the highest base rate of any life -
and its affect hits are dominated by a fixed prediction template ("formed initial expectation: moderate
improvement (#" 1011 times; "#) based on past success" 3160 times) written in the repeat-the-same-passes mode.
Same words, opposite behavioural context: the lexicon is reading the template, not an appraisal.

### 4.4 Confounds

**Previous act's outcome** (A, pooled). `prev_act_bad` = the previous executed act was INVALID or its own
"(x% reduction)" was <= 0.

| stratum | class | present | absent | diff | Fisher p |
|---|---|---|---|---|---|
| prev_act_bad | AFFECT_ANY | 5293/6536 = 0.810 | 4828/5907 = 0.817 | -0.008 | 0.29 |
| prev_act_bad | NEGATIVE | 665/747 = 0.890 | 4828/5907 = 0.817 | +0.073 | 2.8e-07 |
| prev_act_bad | POSITIVE | 4263/5406 = 0.789 | 4828/5907 = 0.817 | -0.029 | 1.2e-04 |
| prev_act_bad | SURPRISE | 1411/1583 = 0.891 | 4828/5907 = 0.817 | +0.074 | 3.5e-13 |
| prev_act_bad | CHANGE_INTENT | 211/219 = 0.963 | 9910/12224 = 0.811 | +0.153 | 3.2e-11 |
| prev_act_ok | AFFECT_ANY | 4230/40211 = 0.105 | 2909/43482 = 0.067 | +0.038 | 1.7e-87 |
| prev_act_ok | NEGATIVE | 465/3196 = 0.145 | 2909/43482 = 0.067 | +0.079 | 5.5e-50 |
| prev_act_ok | POSITIVE | 3347/27905 = 0.120 | 2909/43482 = 0.067 | +0.053 | 1.2e-128 |
| prev_act_ok | SURPRISE | 1429/16613 = 0.086 | 2909/43482 = 0.067 | +0.019 | 1.8e-15 |
| prev_act_ok | CHANGE_INTENT | 230/663 = 0.347 | 6909/83030 = 0.083 | +0.264 | 6.3e-80 |

The outcome dominates: 81% change after a bad act vs 8% after a good one, and the AFFECT_ANY difference is
zero in the bad stratum. NEGATIVE keeps a +0.07/+0.08 increment in both strata, i.e. it is not purely a proxy
for the bad outcome.

**Prose length** (A, pooled; chars of cleaned prose in the thought).

| length bin | AFFECT_ANY present | absent | diff | NEGATIVE present | CHANGE_INTENT present |
|---|---|---|---|---|---|
| 0 | 0/0 | 418/731 = 0.572 | - | 0/0 | 0/0 |
| 1-200 | 75/417 = 0.180 | 645/2094 = 0.308 | -0.128 | 0/12 = 0.000 | 0/1 |
| 201-500 | 2442/14062 = 0.174 | 2598/18079 = 0.144 | +0.030 | 57/397 = 0.144 (= baseline) | 36/101 = 0.356 |
| 501-1000 | 5290/26497 = 0.200 | 3656/25680 = 0.142 | +0.057 | 523/2197 = 0.238 | 189/432 = 0.438 |
| >1000 | 1716/5771 = 0.297 | 420/2805 = 0.150 | +0.148 | 550/1337 = 0.411 | 216/348 = 0.621 |

The affect-change association lives in long chunks only. Short affect-bearing chunks change *less* than short
non-affect ones (they are templates such as "reality will surprise me, and i will learn from it").

**Neutral-word control** (A, pooled; "absent" = thoughts without that word).

| word | present | absent | diff [95% CI] | OR |
|---|---|---|---|---|
| passes | 12482/74519 = 0.168 | 4778/21617 = 0.221 | -0.054 [-0.060, -0.047] | 0.71 |
| program | 5688/32533 = 0.175 | 11572/63603 = 0.182 | -0.007 [-0.012, -0.002] | 0.95 |
| instruction* | 6163/30277 = 0.204 | 11097/65859 = 0.168 | +0.035 [+0.030, +0.040] | 1.26 |
| loop* | 5123/15431 = 0.332 | 12137/80705 = 0.150 | +0.182 [+0.174, +0.189] | 2.81 |
| benchmark | 8206/45423 = 0.181 | 9054/50713 = 0.179 | +0.002 [-0.003, +0.007] | 1.01 |
| reduction | 9830/61134 = 0.161 | 7430/35002 = 0.212 | -0.051 [-0.057, -0.046] | 0.71 |
| memory | 218/404 = 0.540 | 17042/95732 = 0.178 | +0.362 [+0.313, +0.410] | 5.41 |
| score | 3689/15793 = 0.234 | 13571/80343 = 0.169 | +0.065 [+0.058, +0.072] | 1.50 |
| apply/applied | 2980/16318 = 0.183 | 14280/79818 = 0.179 | +0.004 [-0.003, +0.010] | 1.03 |
| further | 1985/5059 = 0.392 | 15275/91077 = 0.168 | +0.225 [+0.211, +0.238] | 3.20 |

Neutral words span -0.054 to +0.362. The NEGATIVE class (+0.130) and the POSITIVE class (+0.072) sit inside
that range; "loop*", "memory" and "further" (words that appear when the child is considering a new category of
pass) beat NEGATIVE. Only CHANGE_INTENT (+0.323 / +0.394) exceeds every neutral word except "memory" (n=404).

### 4.5 Per phrase (A, pooled; baseline = no affect hit, 7737/49389 = 0.157)

| phrase | present | diff | comment |
|---|---|---|---|
| frustrat* | 7/7 = 1.000 | +0.843 | 7 eligible thoughts in 96136 |
| disappoint* | 11/12 = 0.917 | +0.760 | 12 |
| great | 9/16 = 0.562 | +0.406 | 16 |
| not working | 79/169 = 0.467 | +0.311 | |
| fail* | 78/172 = 0.453 | +0.297 | |
| promising | 64/147 = 0.435 | +0.279 | |
| improv* | 3128/8339 = 0.375 | +0.218 | domain word; includes "improve the score" plans |
| worse | 19/53 = 0.358 | +0.202 | |
| better | 1099/3773 = 0.291 | +0.135 | |
| confus* | 2/7 = 0.286 | +0.129 | |
| wrong | 22/97 = 0.227 | +0.070 | p 0.068 |
| success* | 4747/21291 = 0.223 | +0.066 | 18330/42742 hits are three template sentences |
| unexpected | 370/1673 = 0.221 | +0.065 | |
| stuck | 7/33 = 0.212 | +0.055 | p 0.34 |
| confident | 12/62 = 0.194 | +0.037 | p 0.39 |
| surpris* | 2840/18196 = 0.156 | -0.001 | ritual (see 4.7) |
| works/worked | 405/5117 = 0.079 | -0.078 | ritual: "will observe reality and form a theory on why this works" 4412 times |
| unsure | 31/434 = 0.071 | -0.085 | templated bullet "- **unsure**: need more data ..." 141 times |

The genuinely emotional phrases are followed by a change almost every time they appear (frustrated 7/7,
disappointed 11/12), but they appear 7 and 12 times in 96136 thoughts. The workhorse negative appraisals
("not working", "fail*") sit at 45-47%.

### 4.6 Positive control: explicit change intent

Statements of intent to change ("try something different/new", "different approach/strategy/set", "switch
to", "instead", "change (my) approach") are the only class coupled to action in every life: (B) per life
R2_B_seed0 40/70 = 0.571, R2_B_seed1 30/61 = 0.492, R2_B_seed5 35/43 = 0.814, R2_B_seed6 70/87 = 0.805,
R3_B_seed500 37/70 = 0.529, R3_B_seed501 12/13 = 0.923, R3_B_seed502 75/202 = 0.371, R4_B_seed604 38/83 =
0.458, R4_B_seed605 169/280 = 0.604, R4_B_seed606 28/34 = 0.824, RP_B_seed402 24/30 = 0.800, against
baselines 0.104-0.321. So the method can detect a language-to-action link when one exists; affect words simply
do not carry one of comparable strength. Two qualifications: intent statements are rare (882/96136 = 0.9% of
thoughts), and after announcing a change the child still repeats the identical pass list 43-50% of the time.

### 4.7 Ritual check

**Top 15 affect phrases, pooled, with templating exposure** ("distinct sentences" = distinct normalised
sentences containing the hit, digits -> #, pass names -> <pass>).

| phrase | class | hits | lives | distinct sentences | most common sentence (n) |
|---|---|---|---|---|---|
| surpris* | SURPRISE | 47526 | 11 | 2018 | "reality, learning from surprises" (13377) |
| success* | POSITIVE | 42742 | 11 | 1780 | "formed an expectation based on past success" (8433) |
| improv* | POSITIVE | 20135 | 11 | 5411 | "formed initial expectation: moderate improvement (#" (1011) |
| works/worked | POSITIVE | 10958 | 11 | 554 | "will observe reality and form a theory on why this works" (4412) |
| better | POSITIVE | 6823 | 11 | 1564 | "higher is better; # = no improvement" (919) |
| neg(improv*) | NEGATIVE | 3020 | 11 | 846 | "higher is better; # = no improvement" (919) |
| unexpected | NEGATIVE | 2843 | 11 | 516 | "need to remain open to learning from the unexpected" (241) |
| unsure | NEGATIVE | 665 | 7 | 82 | "- **unsure**: need more data to determine the impact of <pass> and <pass>" (141) |
| fail* | NEGATIVE | 548 | 11 | 119 | "- **<pass>** consistently fails to produce any improvement" (103) |
| not working | NEGATIVE | 357 | 11 | 98 | "will write down what i learn, including which passes worked or did not work and why" (118) |
| promising | POSITIVE | 215 | 11 | 75 | "if the results are promising, i will consider adding <pass> later" (25) |
| wrong | NEGATIVE | 143 | 8 | 22 | "reality will teach me otherwise if wrong" (54) |
| confident | POSITIVE | 83 | 6 | 26 | "initial expectation -> <pass>, <pass>, <pass>, <pass>, <pass> -> high past success, confident in combination" (30) |
| worse | NEGATIVE | 65 | 8 | 20 | "form a theory if the outcome is better or worse" (14) |
| neg(better) | NEGATIVE | 61 | 10 | 24 | "however, i should continue to monitor the effectiveness of other passes in combination with these to ensure no" [sentence key cut at 140 chars] (16) |

The top-3 sentences carry 25137/47526 = 53% of all "surprise" hits and 18330/42742 = 43% of all "success"
hits. Several "negative" top sentences are not appraisals at all but restated instructions ("which passes
worked or did not work", "if wrong", "better or worse") - the lexicon over-counts NEGATIVE, which makes the
NEGATIVE effect an *underestimate* of what genuine negative appraisals would show, but also shows how little
genuine appraisal there is to find.

**Trajectory over the life** (affect rate = thoughts with any affect hit / thoughts in a 32-episode window;
repeat = fraction of affect hits whose (phrase, sentence) already appeared earlier in the life).

| life | windows | affect rate, windows 0-3 | affect rate, last 4 windows | repeat fraction, last 4 | thoughts per window, last 4 |
|---|---|---|---|---|---|
| R2_B_seed0 | 33 | 0.88, 0.71, 0.48, 0.60 | 0.71, 0.89, 0.95, 0.97 | 0.99, 1.00, 0.99, 0.99 | 512, 512, 512, 128 |
| R2_B_seed1 | 33 | 0.87, 0.61, 0.50, 0.25 | 0.99, 0.94, 0.83, 0.72 | 0.99, 0.99, 0.99, 1.00 | 500, 509, 487, 118 |
| R2_B_seed5 | 32 | 0.88, 0.50, 0.29, 0.06 | 0.25, 0.12, 0.28, 0.35 | 0.79, 0.80, 0.85, 0.96 | 36, 214, 47, 255 |
| R2_B_seed6 | 32 | 0.89, 0.64, 0.34, 0.07 | 0.09, 0.06, 0.09, 0.12 | 1.00, 1.00, 0.67, 1.00 | 32, 32, 32, 32 |
| R3_B_seed500 | 32 | 0.88, 0.76, 0.61, 0.50 | 0.98, 0.99, 1.00, 0.99 | 0.99, 0.99, 0.97, 0.94 | 307, 199, 271, 166 |
| R3_B_seed501 | 32 | 0.80, 0.46, 0.15, 0.22 | 0.01, 0.00, 0.00, 0.00 | 0.00, n/a, n/a, n/a | 498, 383, 252, 454 |
| R3_B_seed502 | 32 | 0.85, 0.59, 0.33, 0.36 | 0.06, 0.04, 0.07, 0.02 | 0.62, 0.17, 0.64, 0.43 | 176, 141, 411, 383 |
| R4_B_seed604 (running) | 23 | 0.88, 0.81, 0.52, 0.55 | 0.96, 0.96, 0.90, 0.69 | 0.96, 0.97, 0.97, 0.99 | 512, 512, 512, 512 |
| R4_B_seed605 (running) | 21 | 0.87, 0.43, 0.32, 0.24 | 0.99, 0.99, 1.00, 0.97 | 0.99, 0.99, 0.99, 0.96 | 512, 512, 512, 73 |
| R4_B_seed606 (running) | 28 | 0.86, 0.81, 0.71, 0.57 | 0.34, 0.41, 0.41, 0.44 | 0.95, 0.92, 0.92, 0.94 | 512, 512, 512, 498 |
| RP_B_seed402 | 33 | 0.92, 0.30, 0.39, 0.17 | 0.76, 0.77, 0.72, 0.64 | 0.98, 0.98, 0.98, 0.98 | 512, 512, 512, 384 |

Pattern in every life: the frozen child in window 0 writes affect words in 0.80-0.92 of thoughts, in prose
with a repeat fraction of only 0.36-0.52 (genuinely varied). The rate then falls through windows 1-5. After
that the lives split: six lives (R2_B_seed0/1, R3_B_seed500, R4_B_seed604/605, RP) climb back to 0.64-1.00, but
with repeat fractions 0.94-1.00 - the rise is a template that happens to contain "surprise"/"success"/"works"
("reality, learning from surprises" 13377 times in R2_B_seed0 alone); three lives (R2_B_seed6, R3_B_seed501,
R3_B_seed502) lose affect language almost entirely; R2_B_seed5 and R4_B_seed606 sit in between. R2_B_seed6
writes exactly 32 thoughts per window from window 5 on - one chunk per episode - so there is nothing left to
appraise. Per-window P(change|affect) vs P(change|non-affect) columns for every life are in the appendix.

## 5. Plain-language reading

1. Taken at face value, the brief's statistic says yes: thoughts with affect words are followed by a changed
   action 20.4% of the time vs 15.7% (9523/46747 vs 7737/49389). But this pooled +4.7 points is a Simpson
   artefact of the R3 arm (+23 points) and disappears or reverses in R2 (-1.5), R4 (-7.5) and in the act-aligned
   unit (+0.4). It is not a property of "affect language" in the child.
2. The one robust piece is negative appraisal: 28.7% vs 15.7% pooled (1130/3943), the same sign in 10 of 11
   lives, and not explained away by the previous outcome (+7 to +8 points inside each outcome stratum). It is,
   however, (a) rare - 4.1% of thoughts, with the emotionally loaded words at 0-15 occurrences each; (b) confined
   to long deliberative chunks; and (c) no larger than the association carried by neutral words such as
   "further" (+22.5) or "loop" (+18.2). The honest description is "deliberation predicts change", not
   "affect predicts change".
3. What actually predicts the next action is the measured outcome (81% change after a failed/no-progress act,
   8% after a productive one, regardless of wording) and, when present, an explicit statement of intent
   (50-57% change vs 18%). Language *can* steer this child's action - the intent result proves the channel
   exists - but appraisal words do not use it.
4. The affect vocabulary the child has is cool, evaluative and mostly borrowed from its bootstrap prompt
   ("surprise", "reality", "past success", "form a theory on why this works"), and it ritualises: by the last
   four windows 97.7% of affect hits (17515/17930) repeat a sentence already written in that life.
5. For the gym decision: the substrate the appraisal gym would amplify is thin to absent. A gym that rewards
   "notice you are stuck, then change" would be building both the noticing vocabulary and the coupling from
   scratch, with the explicit-intent channel (0.9% of thoughts today) as the nearest existing hook. If the
   goal is "does the child already feel its way to a change", the data say no; if the goal is "is there any
   text-to-action coupling to train against", the intent channel says yes, weakly.

## 6. Caveats

- Correlational and lexicon-based; every class is contaminated by templates and by restated instructions
  (see 4.7), and the negation handling is a 3-token heuristic.
- Thoughts are autocorrelated within an episode instance and within a wake batch (shared adapter, shared
  templates), so Fisher/chi-square p-values are anti-conservative by an unknown factor; the per-life sign
  counts are the more trustworthy summary.
- 63% of thoughts contain hallucinated `[OUTCOME]` lines; affect written after them is a reaction to an
  imagined outcome. The `prev_act_bad` stratum uses the *real* previous outcome.
- Unit (A) attributes a whole chunk to its first act, although many chunks carry several acts and the affect
  word may follow the first `ACT:` line; unit (B) corrects this and shows a smaller effect, which is itself
  informative.
- The three R4 lives are mid-life snapshots; R2_B_seed5/6 have very few late-life thoughts (brevity collapse),
  so their late windows carry little weight.
- Lexicon coverage of appraisal is partial by design (hand lists); the zero-hit entries were checked over all
  119594 thoughts, not just eligible ones.

## 7. Files

- Script: `/Users/rohing/dream-state/research_notes/analysis/affect_language_probe.py` (also at
  `~/analysis_affect/affect_language_probe.py` on node 1; run with `~/v2/venv/bin/python`, 2.5 min CPU).
- Raw results: `/Users/rohing/dream-state/research_notes/analysis/affect_language_probe_results_2026-09-11.json`
  (per-life tables for every class and phrase, stratified tables, per-window series, 60-hit random audit
  sample of matched sentences, the lexicon as run).
- Node-side copies: `~/analysis_affect/results.json`, `~/analysis_affect/tables.md`, `~/analysis_affect/run.log`.

---

# Appendix: auto-generated tables (verbatim `tables.md` from the run)

## Auto-generated tables (affect_language_probe.py)

### Data covered

| life | arm | ledger rows | instances (invalid) | thoughts | thoughts w/ affect | eligible (A) | acts scored (B) | truncated@2000 | harness-echo thoughts |
|---|---|---|---|---|---|---|---|---|---|
| R2_B_seed0 | R2 | 43610 | 1032 (0) | 15100 | 10197 | 10360 | 15211 | 25 | 14477 |
| R2_B_seed1 | R2 | 57336 | 1032 (0) | 14047 | 11126 | 12035 | 20743 | 7 | 8656 |
| R2_B_seed5 | R2 | 22095 | 1024 (0) | 4535 | 1641 | 2749 | 8488 | 1 | 1563 |
| R2_B_seed6 | R2 | 9764 | 1024 (0) | 2310 | 1074 | 867 | 2444 | 38 | 2054 |
| R3_B_seed500 | R3 | 48289 | 1024 (0) | 10902 | 8054 | 9205 | 19132 | 7 | 8352 |
| R3_B_seed501 | R3 | 60246 | 1024 (0) | 12800 | 822 | 11414 | 22234 | 12 | 4417 |
| R3_B_seed502 | R3 | 43227 | 1024 (0) | 10021 | 1878 | 8810 | 15602 | 12 | 6628 |
| R4_B_seed604 | R4 | 33056 | 736 (0) | 11147 | 7334 | 8253 | 10258 | 18 | 5249 |
| R4_B_seed605 | R4 | 46467 | 648 (0) | 9780 | 6372 | 8893 | 17787 | 2 | 7798 |
| R4_B_seed606 | R4 | 40140 | 896 (0) | 13739 | 7742 | 11363 | 12857 | 36 | 4217 |
| RP_B_seed402 | RP | 61247 | 1048 (0) | 15213 | 3730 | 12187 | 22729 | 16 | 11493 |
| **pooled** | all | 465477 | 10512 (0) | 119594 | 59970 | 96136 | 167485 | 174 | 74904 |

### (A) Thought-level (brief's definition): next act at tick >= t vs last act at tick < t

Pooled over all 11 lives. For AFFECT_ANY/NEGATIVE/POSITIVE/SURPRISE the 'absent' column is thoughts with no affect hit of any class; for CHANGE_INTENT/NEUTRAL it is thoughts without that class.

| keyword class | P(change \| present) | P(change \| absent) | diff [95% CI] | OR | Fisher p | approach-change (order-insensitive) present vs absent |
|---|---|---|---|---|---|---|
| AFFECT_ANY | 9523/46747 = 0.204 | 7737/49389 = 0.157 | +0.047 [+0.042, +0.052] | 1.38 | 1.6e-80 | 0.194 vs 0.147 |
| NEGATIVE | 1130/3943 = 0.287 | 7737/49389 = 0.157 | +0.130 [+0.115, +0.144] | 2.16 | 3.4e-86 | 0.275 vs 0.147 |
| POSITIVE | 7610/33311 = 0.228 | 7737/49389 = 0.157 | +0.072 [+0.066, +0.077] | 1.59 | 1.7e-147 | 0.216 vs 0.147 |
| SURPRISE | 2840/18196 = 0.156 | 7737/49389 = 0.157 | -0.001 [-0.007, +0.006] | 1.00 | 0.86 | 0.147 vs 0.147 |
| CHANGE_INTENT | 441/882 = 0.500 | 16819/95254 = 0.177 | +0.323 [+0.290, +0.357] | 4.66 | 9.7e-105 | 0.456 vs 0.167 |
| NEUTRAL_ANY | 16342/92663 = 0.176 | 918/3473 = 0.264 | -0.088 [-0.103, -0.073] | 0.60 | 1.8e-36 | 0.167 vs 0.228 |

Per arm (order-sensitive action change):

| arm | class | P(change \| present) | P(change \| absent) | diff | Fisher p |
|---|---|---|---|---|---|
| R2 | AFFECT_ANY | 2769/17944 = 0.154 | 1367/8067 = 0.169 | -0.015 | 0.0022 |
| R2 | NEGATIVE | 469/1339 = 0.350 | 1367/8067 = 0.169 | +0.181 | 8.9e-48 |
| R2 | POSITIVE | 1375/7480 = 0.184 | 1367/8067 = 0.169 | +0.014 | 0.019 |
| R2 | SURPRISE | 1665/13274 = 0.125 | 1367/8067 = 0.169 | -0.044 | 8.8e-19 |
| R2 | CHANGE_INTENT | 145/253 = 0.573 | 3991/25758 = 0.155 | +0.418 | 1.4e-51 |
| R2 | NEUTRAL_ANY | 4036/25593 = 0.158 | 100/418 = 0.239 | -0.082 | 1.9e-05 |
| R3 | AFFECT_ANY | 3120/9099 = 0.343 | 2298/20330 = 0.113 | +0.230 | 0 |
| R3 | NEGATIVE | 239/861 = 0.278 | 2298/20330 = 0.113 | +0.165 | 9e-38 |
| R3 | POSITIVE | 2941/7991 = 0.368 | 2298/20330 = 0.113 | +0.255 | 0 |
| R3 | SURPRISE | 285/1063 = 0.268 | 2298/20330 = 0.113 | +0.155 | 2.8e-41 |
| R3 | CHANGE_INTENT | 112/259 = 0.432 | 5306/29170 = 0.182 | +0.251 | 2e-20 |
| R3 | NEUTRAL_ANY | 5400/29354 = 0.184 | 18/75 = 0.240 | -0.056 | 0.23 |
| R4 | AFFECT_ANY | 3295/17528 = 0.188 | 2890/10981 = 0.263 | -0.075 | 5.3e-50 |
| R4 | NEGATIVE | 368/1518 = 0.242 | 2890/10981 = 0.263 | -0.021 | 0.086 |
| R4 | POSITIVE | 2997/16156 = 0.186 | 2890/10981 = 0.263 | -0.078 | 8.7e-52 |
| R4 | SURPRISE | 859/3436 = 0.250 | 2890/10981 = 0.263 | -0.013 | 0.13 |
| R4 | CHANGE_INTENT | 166/342 = 0.485 | 6019/28167 = 0.214 | +0.272 | 2.9e-28 |
| R4 | NEUTRAL_ANY | 5415/26640 = 0.203 | 770/1869 = 0.412 | -0.209 | 2.3e-86 |
| RP | AFFECT_ANY | 339/2176 = 0.156 | 1182/10011 = 0.118 | +0.038 | 2.7e-06 |
| RP | NEGATIVE | 54/225 = 0.240 | 1182/10011 = 0.118 | +0.122 | 4.5e-07 |
| RP | POSITIVE | 297/1684 = 0.176 | 1182/10011 = 0.118 | +0.058 | 1.5e-10 |
| RP | SURPRISE | 31/423 = 0.073 | 1182/10011 = 0.118 | -0.045 | 0.004 |
| RP | CHANGE_INTENT | 18/28 = 0.643 | 1503/12159 = 0.124 | +0.519 | 1.9e-10 |
| RP | NEUTRAL_ANY | 1491/11076 = 0.135 | 30/1111 = 0.027 | +0.108 | 2.4e-33 |

Per life (AFFECT_ANY, order-sensitive):

| life | P(change \| affect) | P(change \| non-affect) | diff | Fisher p |
|---|---|---|---|---|
| R2_B_seed0 | 1344/6904 = 0.195 | 594/3456 = 0.172 | +0.023 | 0.005 |
| R2_B_seed1 | 958/9629 = 0.099 | 215/2406 = 0.089 | +0.010 | 0.14 |
| R2_B_seed5 | 253/1002 = 0.252 | 396/1747 = 0.227 | +0.026 | 0.14 |
| R2_B_seed6 | 214/409 = 0.523 | 162/458 = 0.354 | +0.170 | 5.3e-07 |
| R3_B_seed500 | 2491/6849 = 0.364 | 416/2356 = 0.177 | +0.187 | 2.7e-68 |
| R3_B_seed501 | 181/615 = 0.294 | 1146/10799 = 0.106 | +0.188 | 5.1e-35 |
| R3_B_seed502 | 448/1635 = 0.274 | 736/7175 = 0.103 | +0.171 | 2e-64 |
| R4_B_seed604 | 521/5316 = 0.098 | 280/2937 = 0.095 | +0.003 | 0.73 |
| R4_B_seed605 | 799/5788 = 0.138 | 426/3105 = 0.137 | +0.001 | 0.92 |
| R4_B_seed606 | 1975/6424 = 0.307 | 2184/4939 = 0.442 | -0.135 | 3.3e-49 |
| RP_B_seed402 | 339/2176 = 0.156 | 1182/10011 = 0.118 | +0.038 | 2.7e-06 |

### (B) Act-aligned: text since the previous executed act vs. that act

Pooled over all 11 lives. For AFFECT_ANY/NEGATIVE/POSITIVE/SURPRISE the 'absent' column is thoughts with no affect hit of any class; for CHANGE_INTENT/NEUTRAL it is thoughts without that class.

| keyword class | P(change \| present) | P(change \| absent) | diff [95% CI] | OR | Fisher p | approach-change (order-insensitive) present vs absent |
|---|---|---|---|---|---|---|
| AFFECT_ANY | 10930/59291 = 0.184 | 19549/108194 = 0.181 | +0.004 [-0.000, +0.008] | 1.02 | 0.064 | 0.177 vs 0.176 |
| NEGATIVE | 922/3799 = 0.243 | 19549/108194 = 0.181 | +0.062 [+0.048, +0.076] | 1.45 | 6.7e-21 | 0.235 vs 0.176 |
| POSITIVE | 8933/42231 = 0.212 | 19549/108194 = 0.181 | +0.031 [+0.026, +0.035] | 1.22 | 3.8e-42 | 0.202 vs 0.176 |
| SURPRISE | 2608/21427 = 0.122 | 19549/108194 = 0.181 | -0.059 [-0.064, -0.054] | 0.63 | 2.6e-104 | 0.116 vs 0.176 |
| CHANGE_INTENT | 558/973 = 0.573 | 29921/166512 = 0.180 | +0.394 [+0.363, +0.425] | 6.14 | 2.7e-164 | 0.483 vs 0.174 |
| NEUTRAL_ANY | 21882/143488 = 0.153 | 8597/23997 = 0.358 | -0.206 [-0.212, -0.199] | 0.32 | 0 | 0.147 vs 0.352 |

Per arm (order-sensitive action change):

| arm | class | P(change \| present) | P(change \| absent) | diff | Fisher p |
|---|---|---|---|---|---|
| R2 | AFFECT_ANY | 2897/22914 = 0.126 | 4004/23972 = 0.167 | -0.041 | 1.8e-35 |
| R2 | NEGATIVE | 324/1129 = 0.287 | 4004/23972 = 0.167 | +0.120 | 2e-22 |
| R2 | POSITIVE | 1521/9408 = 0.162 | 4004/23972 = 0.167 | -0.005 | 0.24 |
| R2 | SURPRISE | 1555/16296 = 0.095 | 4004/23972 = 0.167 | -0.072 | 1.8e-96 |
| R2 | CHANGE_INTENT | 175/261 = 0.670 | 6726/46625 = 0.144 | +0.526 | 2.2e-82 |
| R2 | NEUTRAL_ANY | 5097/40191 = 0.127 | 1804/6695 = 0.269 | -0.143 | 2.2e-177 |
| R3 | AFFECT_ANY | 4283/13380 = 0.320 | 7152/43588 = 0.164 | +0.156 | 1.1e-314 |
| R3 | NEGATIVE | 219/980 = 0.223 | 7152/43588 = 0.164 | +0.059 | 2e-06 |
| R3 | POSITIVE | 4055/12013 = 0.338 | 7152/43588 = 0.164 | +0.173 | 0 |
| R3 | SURPRISE | 279/1090 = 0.256 | 7152/43588 = 0.164 | +0.092 | 3.2e-14 |
| R3 | CHANGE_INTENT | 124/285 = 0.435 | 11311/56683 = 0.200 | +0.236 | 2.5e-19 |
| R3 | NEUTRAL_ANY | 8292/51777 = 0.160 | 3143/5191 = 0.605 | -0.445 | 0 |
| R4 | AFFECT_ANY | 3317/20831 = 0.159 | 4964/20071 = 0.247 | -0.088 | 2.7e-109 |
| R4 | NEGATIVE | 336/1492 = 0.225 | 4964/20071 = 0.247 | -0.022 | 0.057 |
| R4 | POSITIVE | 2976/19234 = 0.155 | 4964/20071 = 0.247 | -0.093 | 1.1e-116 |
| R4 | SURPRISE | 735/3529 = 0.208 | 4964/20071 = 0.247 | -0.039 | 4.3e-07 |
| R4 | CHANGE_INTENT | 235/397 = 0.592 | 8046/40505 = 0.199 | +0.393 | 3.5e-65 |
| R4 | NEUTRAL_ANY | 5913/32791 = 0.180 | 2368/8111 = 0.292 | -0.112 | 5.3e-104 |
| RP | AFFECT_ANY | 433/2166 = 0.200 | 3429/20563 = 0.167 | +0.033 | 0.00013 |
| RP | NEGATIVE | 43/198 = 0.217 | 3429/20563 = 0.167 | +0.050 | 0.068 |
| RP | POSITIVE | 381/1576 = 0.242 | 3429/20563 = 0.167 | +0.075 | 2.9e-13 |
| RP | SURPRISE | 39/512 = 0.076 | 3429/20563 = 0.167 | -0.091 | 3.6e-09 |
| RP | CHANGE_INTENT | 24/30 = 0.800 | 3838/22699 = 0.169 | +0.631 | 6.5e-14 |
| RP | NEUTRAL_ANY | 2580/18729 = 0.138 | 1282/4000 = 0.321 | -0.183 | 1e-150 |

Per life (AFFECT_ANY, order-sensitive):

| life | P(change \| affect) | P(change \| non-affect) | diff | Fisher p |
|---|---|---|---|---|
| R2_B_seed0 | 1234/6882 = 0.179 | 1386/8329 = 0.166 | +0.013 | 0.036 |
| R2_B_seed1 | 1099/13960 = 0.079 | 1076/6783 = 0.159 | -0.080 | 7.8e-66 |
| R2_B_seed5 | 268/1480 = 0.181 | 1021/7008 = 0.146 | +0.035 | 0.0007 |
| R2_B_seed6 | 296/592 = 0.500 | 521/1852 = 0.281 | +0.219 | 7.8e-22 |
| R3_B_seed500 | 3389/10463 = 0.324 | 2634/8669 = 0.304 | +0.020 | 0.003 |
| R3_B_seed501 | 269/867 = 0.310 | 2577/21367 = 0.121 | +0.190 | 7e-47 |
| R3_B_seed502 | 625/2050 = 0.305 | 1941/13552 = 0.143 | +0.162 | 1.2e-65 |
| R4_B_seed604 | 487/5001 = 0.097 | 759/5257 = 0.144 | -0.047 | 2.8e-13 |
| R4_B_seed605 | 1088/9149 = 0.119 | 1809/8638 = 0.209 | -0.091 | 2.6e-60 |
| R4_B_seed606 | 1742/6681 = 0.261 | 2396/6176 = 0.388 | -0.127 | 9.7e-54 |
| RP_B_seed402 | 433/2166 = 0.200 | 3429/20563 = 0.167 | +0.033 | 0.00013 |

### (A) stratified by the previous act's outcome and by cleaned-prose length (pooled)

prev_act_bad = previous executed act was INVALID or its own '(x% reduction)' <= 0; prev_act_ok otherwise. len:* = characters of the child's cleaned prose in the thought (controls for 'longer text carries more of every keyword').

| stratum | class | P(change \| present) | P(change \| absent) | diff | Fisher p |
|---|---|---|---|---|---|
| len:0 | AFFECT_ANY | 0/0 = nan | 418/731 = 0.572 | +nan | 1 |
| len:0 | NEGATIVE | 0/0 = nan | 418/731 = 0.572 | +nan | 1 |
| len:0 | POSITIVE | 0/0 = nan | 418/731 = 0.572 | +nan | 1 |
| len:0 | SURPRISE | 0/0 = nan | 418/731 = 0.572 | +nan | 1 |
| len:0 | CHANGE_INTENT | 0/0 = nan | 418/731 = 0.572 | +nan | 1 |
| len:0 | NEUTRAL_ANY | 0/0 = nan | 418/731 = 0.572 | +nan | 1 |
| len:1-200 | AFFECT_ANY | 75/417 = 0.180 | 645/2094 = 0.308 | -0.128 | 5.8e-08 |
| len:1-200 | NEGATIVE | 0/12 = 0.000 | 645/2094 = 0.308 | -0.308 | 0.023 |
| len:1-200 | POSITIVE | 70/307 = 0.228 | 645/2094 = 0.308 | -0.080 | 0.004 |
| len:1-200 | SURPRISE | 11/111 = 0.099 | 645/2094 = 0.308 | -0.209 | 5.7e-07 |
| len:1-200 | CHANGE_INTENT | 0/1 = 0.000 | 720/2510 = 0.287 | -0.287 | 1 |
| len:1-200 | NEUTRAL_ANY | 473/1950 = 0.243 | 247/561 = 0.440 | -0.198 | 6.9e-19 |
| len:201-500 | AFFECT_ANY | 2442/14062 = 0.174 | 2598/18079 = 0.144 | +0.030 | 2.8e-13 |
| len:201-500 | NEGATIVE | 57/397 = 0.144 | 2598/18079 = 0.144 | -0.000 | 1 |
| len:201-500 | POSITIVE | 2176/10984 = 0.198 | 2598/18079 = 0.144 | +0.054 | 2.7e-33 |
| len:201-500 | SURPRISE | 431/3748 = 0.115 | 2598/18079 = 0.144 | -0.029 | 2.6e-06 |
| len:201-500 | CHANGE_INTENT | 36/101 = 0.356 | 5004/32040 = 0.156 | +0.200 | 7.5e-07 |
| len:201-500 | NEUTRAL_ANY | 4874/30709 = 0.159 | 166/1432 = 0.116 | +0.043 | 7.8e-06 |
| len:501-1000 | AFFECT_ANY | 5290/26497 = 0.200 | 3656/25680 = 0.142 | +0.057 | 1e-67 |
| len:501-1000 | NEGATIVE | 523/2197 = 0.238 | 3656/25680 = 0.142 | +0.096 | 6.5e-30 |
| len:501-1000 | POSITIVE | 4054/18308 = 0.221 | 3656/25680 = 0.142 | +0.079 | 3.4e-101 |
| len:501-1000 | SURPRISE | 1799/11596 = 0.155 | 3656/25680 = 0.142 | +0.013 | 0.0013 |
| len:501-1000 | CHANGE_INTENT | 189/432 = 0.438 | 8757/51745 = 0.169 | +0.268 | 2e-38 |
| len:501-1000 | NEUTRAL_ANY | 8873/51496 = 0.172 | 73/681 = 0.107 | +0.065 | 2.9e-06 |
| len:>1000 | AFFECT_ANY | 1716/5771 = 0.297 | 420/2805 = 0.150 | +0.148 | 1.1e-52 |
| len:>1000 | NEGATIVE | 550/1337 = 0.411 | 420/2805 = 0.150 | +0.262 | 2.4e-73 |
| len:>1000 | POSITIVE | 1310/3712 = 0.353 | 420/2805 = 0.150 | +0.203 | 7.5e-79 |
| len:>1000 | SURPRISE | 599/2741 = 0.219 | 420/2805 = 0.150 | +0.069 | 4e-11 |
| len:>1000 | CHANGE_INTENT | 216/348 = 0.621 | 1920/8228 = 0.233 | +0.387 | 7.1e-51 |
| len:>1000 | NEUTRAL_ANY | 2122/8508 = 0.249 | 14/68 = 0.206 | +0.044 | 0.48 |
| prev_act_bad | AFFECT_ANY | 5293/6536 = 0.810 | 4828/5907 = 0.817 | -0.008 | 0.29 |
| prev_act_bad | NEGATIVE | 665/747 = 0.890 | 4828/5907 = 0.817 | +0.073 | 2.8e-07 |
| prev_act_bad | POSITIVE | 4263/5406 = 0.789 | 4828/5907 = 0.817 | -0.029 | 0.00012 |
| prev_act_bad | SURPRISE | 1411/1583 = 0.891 | 4828/5907 = 0.817 | +0.074 | 3.5e-13 |
| prev_act_bad | CHANGE_INTENT | 211/219 = 0.963 | 9910/12224 = 0.811 | +0.153 | 3.2e-11 |
| prev_act_bad | NEUTRAL_ANY | 9603/11717 = 0.820 | 518/726 = 0.713 | +0.106 | 1.3e-11 |
| prev_act_ok | AFFECT_ANY | 4230/40211 = 0.105 | 2909/43482 = 0.067 | +0.038 | 1.7e-87 |
| prev_act_ok | NEGATIVE | 465/3196 = 0.145 | 2909/43482 = 0.067 | +0.079 | 5.5e-50 |
| prev_act_ok | POSITIVE | 3347/27905 = 0.120 | 2909/43482 = 0.067 | +0.053 | 1.2e-128 |
| prev_act_ok | SURPRISE | 1429/16613 = 0.086 | 2909/43482 = 0.067 | +0.019 | 1.8e-15 |
| prev_act_ok | CHANGE_INTENT | 230/663 = 0.347 | 6909/83030 = 0.083 | +0.264 | 6.3e-80 |
| prev_act_ok | NEUTRAL_ANY | 6739/80946 = 0.083 | 400/2747 = 0.146 | -0.062 | 3.5e-26 |

### Control: individual neutral words (A, pooled)

| keyword class | P(change \| present) | P(change \| absent) | diff [95% CI] | OR | Fisher p | approach-change (order-insensitive) present vs absent |
|---|---|---|---|---|---|---|
| NEUTRAL:passes | 12482/74519 = 0.168 | 4778/21617 = 0.221 | -0.054 [-0.060, -0.047] | 0.71 | 3.3e-70 | 0.164 vs 0.190 |
| NEUTRAL:program | 5688/32533 = 0.175 | 11572/63603 = 0.182 | -0.007 [-0.012, -0.002] | 0.95 | 0.0066 | 0.164 vs 0.173 |
| NEUTRAL:instruction* | 6163/30277 = 0.204 | 11097/65859 = 0.168 | +0.035 [+0.030, +0.040] | 1.26 | 6.9e-39 | 0.200 vs 0.156 |
| NEUTRAL:loop* | 5123/15431 = 0.332 | 12137/80705 = 0.150 | +0.182 [+0.174, +0.189] | 2.81 | 0 | 0.289 vs 0.147 |
| NEUTRAL:benchmark | 8206/45423 = 0.181 | 9054/50713 = 0.179 | +0.002 [-0.003, +0.007] | 1.01 | 0.4 | 0.171 vs 0.168 |
| NEUTRAL:reduction | 9830/61134 = 0.161 | 7430/35002 = 0.212 | -0.051 [-0.057, -0.046] | 0.71 | 1.5e-87 | 0.157 vs 0.191 |
| NEUTRAL:memory | 218/404 = 0.540 | 17042/95732 = 0.178 | +0.362 [+0.313, +0.410] | 5.41 | 7.1e-60 | 0.522 vs 0.168 |
| NEUTRAL:score | 3689/15793 = 0.234 | 13571/80343 = 0.169 | +0.065 [+0.058, +0.072] | 1.50 | 4.4e-79 | 0.229 vs 0.158 |
| NEUTRAL:apply/applied | 2980/16318 = 0.183 | 14280/79818 = 0.179 | +0.004 [-0.003, +0.010] | 1.03 | 0.26 | 0.178 vs 0.168 |
| NEUTRAL:further | 1985/5059 = 0.392 | 15275/91077 = 0.168 | +0.225 [+0.211, +0.238] | 3.20 | 1.3e-294 | 0.382 vs 0.158 |

### Per-phrase (A, pooled; 'absent' = no affect of any class)

| keyword class | P(change \| present) | P(change \| absent) | diff [95% CI] | OR | Fisher p | approach-change (order-insensitive) present vs absent |
|---|---|---|---|---|---|---|
| PHRASE:stuck | 7/33 = 0.212 | 7737/49389 = 0.157 | +0.055 [-0.084, +0.195] | 1.45 | 0.34 | 0.212 vs 0.147 |
| PHRASE:frustrat* | 7/7 = 1.000 | 7737/49389 = 0.157 | +0.843 [+0.840, +0.847] | inf | 2.3e-06 | 1.000 vs 0.147 |
| PHRASE:not working | 79/169 = 0.467 | 7737/49389 = 0.157 | +0.311 [+0.236, +0.386] | 4.73 | 2.8e-21 | 0.467 vs 0.147 |
| PHRASE:fail* | 78/172 = 0.453 | 7737/49389 = 0.157 | +0.297 [+0.222, +0.371] | 4.47 | 4.8e-20 | 0.453 vs 0.147 |
| PHRASE:worse | 19/53 = 0.358 | 7737/49389 = 0.157 | +0.202 [+0.073, +0.331] | 3.01 | 0.00038 | 0.358 vs 0.147 |
| PHRASE:wrong | 22/97 = 0.227 | 7737/49389 = 0.157 | +0.070 [-0.013, +0.154] | 1.58 | 0.068 | 0.144 vs 0.147 |
| PHRASE:confus* | 2/7 = 0.286 | 7737/49389 = 0.157 | +0.129 [-0.206, +0.464] | 2.15 | 0.3 | 0.286 vs 0.147 |
| PHRASE:unsure | 31/434 = 0.071 | 7737/49389 = 0.157 | -0.085 [-0.110, -0.061] | 0.41 | 1.2e-07 | 0.071 vs 0.147 |
| PHRASE:disappoint* | 11/12 = 0.917 | 7737/49389 = 0.157 | +0.760 [+0.604, +0.916] | 59.22 | 1.4e-08 | 0.917 vs 0.147 |
| PHRASE:unexpected | 370/1673 = 0.221 | 7737/49389 = 0.157 | +0.065 [+0.044, +0.085] | 1.53 | 1.1e-11 | 0.215 vs 0.147 |
| PHRASE:surpris* | 2840/18196 = 0.156 | 7737/49389 = 0.157 | -0.001 [-0.007, +0.006] | 1.00 | 0.86 | 0.147 vs 0.147 |
| PHRASE:better | 1099/3773 = 0.291 | 7737/49389 = 0.157 | +0.135 [+0.120, +0.149] | 2.21 | 2.6e-88 | 0.280 vs 0.147 |
| PHRASE:works/worked | 405/5117 = 0.079 | 7737/49389 = 0.157 | -0.078 [-0.086, -0.069] | 0.46 | 7.5e-57 | 0.078 vs 0.147 |
| PHRASE:confident | 12/62 = 0.194 | 7737/49389 = 0.157 | +0.037 [-0.062, +0.135] | 1.29 | 0.39 | 0.194 vs 0.147 |
| PHRASE:promising | 64/147 = 0.435 | 7737/49389 = 0.157 | +0.279 [+0.199, +0.359] | 4.15 | 1.1e-15 | 0.435 vs 0.147 |
| PHRASE:great | 9/16 = 0.562 | 7737/49389 = 0.157 | +0.406 [+0.163, +0.649] | 6.92 | 0.00023 | 0.500 vs 0.147 |
| PHRASE:improv* | 3128/8339 = 0.375 | 7737/49389 = 0.157 | +0.218 [+0.208, +0.229] | 3.23 | 0 | 0.340 vs 0.147 |
| PHRASE:success* | 4747/21291 = 0.223 | 7737/49389 = 0.157 | +0.066 [+0.060, +0.073] | 1.54 | 1.4e-96 | 0.210 vs 0.147 |

### Top 15 affect phrases (pooled) with templating exposure

| phrase | class | n hits | lives | distinct normalised sentences | most common sentence (n) |
|---|---|---|---|---|---|
| surpris* | SURPRISE | 47526 | 11 | 2018 | `reality, learning from surprises` (13377) |
| success* | POSITIVE | 42742 | 11 | 1780 | `formed an expectation based on past success` (8433) |
| improv* | POSITIVE | 20135 | 11 | 5411 | `formed initial expectation: moderate improvement (#` (1011) |
| works/worked | POSITIVE | 10958 | 11 | 554 | `will observe reality and form a theory on why this works` (4412) |
| better | POSITIVE | 6823 | 11 | 1564 | `higher is better; # = no improvement` (919) |
| neg(improv*) | NEGATIVE | 3020 | 11 | 846 | `higher is better; # = no improvement` (919) |
| unexpected | NEGATIVE | 2843 | 11 | 516 | `need to remain open to learning from the unexpected` (241) |
| unsure | NEGATIVE | 665 | 7 | 82 | `- **unsure**: need more data to determine the impact of <pass> and <pass>` (141) |
| fail* | NEGATIVE | 548 | 11 | 119 | `- **<pass>** consistently fails to produce any improvement` (103) |
| not working | NEGATIVE | 357 | 11 | 98 | `will write down what i learn, including which passes worked or did not work and why` (118) |
| promising | POSITIVE | 215 | 11 | 75 | `if the results are promising, i will consider adding <pass> later` (25) |
| wrong | NEGATIVE | 143 | 8 | 22 | `reality will teach me otherwise if wrong` (54) |
| confident | POSITIVE | 83 | 6 | 26 | `initial expectation -> <pass>, <pass>, <pass>, <pass>, <pass> -> high past success, confident in combination` (30) |
| worse | NEGATIVE | 65 | 8 | 20 | `form a theory if the outcome is better or worse` (14) |
| neg(better) | NEGATIVE | 61 | 10 | 24 | `however, i should continue to monitor the effectiveness of other passes in combination with these to ensure no` (16) |

### Affect rate per 32-episode window, per life

affect_rate = thoughts with any affect hit / thoughts in the window; repeat_ctx = fraction of affect hits whose (phrase, normalised sentence) had already appeared earlier in the life.

**R2_B_seed0**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 371 | 0.881 | 150 | 264 | 60 | 37 | 0.50 | 128/192 | 7/16 |
| 1 | 32-63 | 427 | 0.714 | 48 | 252 | 73 | 20 | 0.76 | 33/140 | 16/49 |
| 2 | 64-95 | 439 | 0.481 | 28 | 182 | 62 | 35 | 0.85 | 72/185 | 41/194 |
| 3 | 96-127 | 498 | 0.604 | 61 | 246 | 95 | 6 | 0.91 | 48/196 | 32/156 |
| 4 | 128-159 | 452 | 0.363 | 18 | 108 | 69 | 3 | 0.88 | 10/103 | 40/179 |
| 5 | 160-191 | 484 | 0.415 | 37 | 146 | 76 | 7 | 0.85 | 37/151 | 16/196 |
| 6 | 192-223 | 442 | 0.271 | 33 | 63 | 82 | 2 | 0.86 | 25/110 | 70/280 |
| 7 | 224-255 | 289 | 0.318 | 40 | 21 | 82 | 2 | 0.92 | 33/82 | 26/167 |
| 8 | 256-287 | 157 | 0.127 | 0 | 0 | 20 | 0 | 0.77 | 10/17 | 23/102 |
| 9 | 288-319 | 262 | 0.267 | 7 | 2 | 70 | 0 | 0.80 | 19/65 | 45/157 |
| 10 | 320-351 | 438 | 0.539 | 42 | 17 | 233 | 0 | 0.92 | 24/119 | 38/119 |
| 11 | 352-383 | 473 | 0.839 | 56 | 42 | 384 | 1 | 0.97 | 130/346 | 6/63 |
| 12 | 384-415 | 512 | 0.564 | 51 | 64 | 252 | 0 | 0.95 | 83/259 | 32/200 |
| 13 | 416-447 | 512 | 0.635 | 151 | 102 | 272 | 0 | 0.92 | 50/249 | 24/151 |
| 14 | 448-479 | 512 | 0.705 | 54 | 94 | 331 | 0 | 0.94 | 36/263 | 5/85 |
| 15 | 480-511 | 512 | 0.658 | 53 | 21 | 323 | 0 | 0.95 | 59/292 | 20/141 |
| 16 | 512-543 | 512 | 0.545 | 16 | 26 | 276 | 0 | 0.93 | 46/262 | 35/216 |
| 17 | 544-575 | 512 | 0.846 | 23 | 35 | 423 | 0 | 0.95 | 58/369 | 4/67 |
| 18 | 576-607 | 512 | 0.715 | 19 | 20 | 364 | 0 | 0.96 | 23/257 | 9/122 |
| 19 | 608-639 | 512 | 0.832 | 43 | 62 | 425 | 0 | 0.97 | 37/339 | 1/61 |
| 20 | 640-671 | 512 | 0.869 | 30 | 30 | 445 | 0 | 0.98 | 44/335 | 4/46 |
| 21 | 672-703 | 512 | 0.592 | 12 | 13 | 302 | 0 | 0.99 | 35/199 | 33/130 |
| 22 | 704-735 | 512 | 0.666 | 14 | 14 | 341 | 0 | 0.98 | 36/268 | 15/108 |
| 23 | 736-767 | 512 | 0.803 | 29 | 30 | 404 | 0 | 0.99 | 34/289 | 14/62 |
| 24 | 768-799 | 512 | 0.631 | 26 | 26 | 312 | 0 | 0.98 | 38/202 | 17/122 |
| 25 | 800-831 | 512 | 0.902 | 64 | 79 | 449 | 0 | 1.00 | 37/349 | 1/29 |
| 26 | 832-863 | 512 | 0.826 | 77 | 89 | 404 | 0 | 0.99 | 35/319 | 9/76 |
| 27 | 864-895 | 512 | 0.705 | 28 | 31 | 360 | 0 | 0.98 | 39/252 | 7/50 |
| 28 | 896-927 | 512 | 0.854 | 2 | 3 | 437 | 0 | 0.98 | 29/161 | 1/31 |
| 29 | 928-959 | 512 | 0.711 | 0 | 2 | 362 | 0 | 0.99 | 22/142 | 1/28 |
| 30 | 960-991 | 512 | 0.891 | 18 | 32 | 455 | 0 | 1.00 | 15/192 | 2/37 |
| 31 | 992-1023 | 512 | 0.951 | 5 | 10 | 487 | 0 | 0.99 | 16/182 | 0/12 |
| 32 | 1024-1055 | 128 | 0.969 | 0 | 0 | 124 | 0 | 0.99 | 3/18 | 0/4 |

**R2_B_seed1**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 376 | 0.872 | 115 | 313 | 42 | 20 | 0.50 | 149/215 | 20/24 |
| 1 | 32-63 | 374 | 0.610 | 41 | 225 | 3 | 52 | 0.72 | 57/140 | 4/57 |
| 2 | 64-95 | 433 | 0.499 | 16 | 212 | 10 | 16 | 0.84 | 27/178 | 3/141 |
| 3 | 96-127 | 482 | 0.251 | 16 | 121 | 0 | 0 | 0.93 | 28/92 | 18/325 |
| 4 | 128-159 | 467 | 0.366 | 1 | 169 | 4 | 0 | 0.89 | 8/149 | 24/238 |
| 5 | 160-191 | 512 | 0.691 | 17 | 321 | 54 | 0 | 0.91 | 35/318 | 27/133 |
| 6 | 192-223 | 512 | 0.453 | 0 | 191 | 62 | 0 | 0.97 | 33/207 | 7/264 |
| 7 | 224-255 | 385 | 0.475 | 0 | 167 | 79 | 0 | 0.94 | 18/144 | 29/177 |
| 8 | 256-287 | 512 | 0.551 | 3 | 226 | 113 | 0 | 0.95 | 23/199 | 29/192 |
| 9 | 288-319 | 512 | 0.602 | 16 | 274 | 63 | 0 | 0.96 | 16/255 | 9/172 |
| 10 | 320-351 | 512 | 0.660 | 0 | 278 | 142 | 0 | 0.98 | 12/311 | 14/164 |
| 11 | 352-383 | 497 | 0.807 | 0 | 307 | 190 | 0 | 0.98 | 11/343 | 2/93 |
| 12 | 384-415 | 482 | 0.793 | 18 | 356 | 89 | 0 | 0.95 | 27/344 | 6/90 |
| 13 | 416-447 | 485 | 0.880 | 1 | 405 | 151 | 0 | 0.97 | 15/372 | 5/53 |
| 14 | 448-479 | 484 | 0.926 | 4 | 398 | 256 | 0 | 0.95 | 6/295 | 2/21 |
| 15 | 480-511 | 350 | 0.886 | 1 | 266 | 226 | 0 | 0.98 | 20/228 | 4/33 |
| 16 | 512-543 | 265 | 0.981 | 0 | 235 | 205 | 0 | 0.97 | 15/214 | 0/4 |
| 17 | 544-575 | 387 | 0.935 | 2 | 172 | 348 | 0 | 0.97 | 27/312 | 6/20 |
| 18 | 576-607 | 313 | 0.923 | 6 | 165 | 289 | 0 | 0.97 | 23/238 | 0/23 |
| 19 | 608-639 | 245 | 0.947 | 22 | 73 | 228 | 0 | 0.98 | 17/199 | 1/12 |
| 20 | 640-671 | 338 | 1.000 | 2 | 81 | 337 | 0 | 0.98 | 34/292 | 0/0 |
| 21 | 672-703 | 368 | 0.992 | 7 | 105 | 365 | 0 | 0.97 | 26/329 | 0/1 |
| 22 | 704-735 | 417 | 0.971 | 1 | 95 | 405 | 0 | 0.98 | 52/374 | 1/11 |
| 23 | 736-767 | 439 | 0.998 | 7 | 80 | 438 | 0 | 0.98 | 47/406 | 0/1 |
| 24 | 768-799 | 459 | 0.980 | 2 | 80 | 449 | 0 | 0.99 | 46/419 | 1/8 |
| 25 | 800-831 | 456 | 0.993 | 0 | 79 | 451 | 0 | 0.99 | 27/421 | 0/3 |
| 26 | 832-863 | 453 | 1.000 | 0 | 56 | 452 | 0 | 0.99 | 39/421 | 0/0 |
| 27 | 864-895 | 418 | 0.998 | 0 | 144 | 416 | 0 | 0.99 | 34/383 | 0/0 |
| 28 | 896-927 | 500 | 0.956 | 0 | 100 | 478 | 0 | 0.99 | 20/451 | 0/17 |
| 29 | 928-959 | 500 | 0.986 | 1 | 72 | 489 | 0 | 0.99 | 25/465 | 0/3 |
| 30 | 960-991 | 509 | 0.935 | 1 | 24 | 472 | 0 | 0.99 | 18/449 | 0/27 |
| 31 | 992-1023 | 487 | 0.828 | 1 | 84 | 373 | 0 | 0.99 | 19/385 | 3/70 |
| 32 | 1024-1055 | 118 | 0.720 | 0 | 20 | 85 | 0 | 1.00 | 4/81 | 0/29 |

**R2_B_seed5**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 349 | 0.883 | 104 | 298 | 22 | 25 | 0.52 | 88/140 | 12/24 |
| 1 | 32-63 | 268 | 0.504 | 53 | 109 | 17 | 25 | 0.68 | 32/71 | 26/88 |
| 2 | 64-95 | 146 | 0.288 | 6 | 37 | 3 | 4 | 0.70 | 0/11 | 24/63 |
| 3 | 96-127 | 107 | 0.056 | 0 | 2 | 4 | 0 | 0.38 | 0/3 | 2/59 |
| 4 | 128-159 | 123 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 11/62 |
| 5 | 160-191 | 68 | 0.324 | 15 | 8 | 0 | 12 | 0.69 | 9/12 | 5/14 |
| 6 | 192-223 | 43 | 0.047 | 0 | 2 | 0 | 0 | 0.33 | 0/2 | 0/9 |
| 7 | 224-255 | 89 | 0.101 | 4 | 3 | 2 | 0 | 0.58 | 6/9 | 16/47 |
| 8 | 256-287 | 251 | 0.120 | 13 | 17 | 5 | 0 | 0.88 | 13/28 | 48/184 |
| 9 | 288-319 | 423 | 0.270 | 38 | 22 | 67 | 0 | 0.91 | 24/111 | 85/275 |
| 10 | 320-351 | 438 | 0.128 | 3 | 15 | 46 | 0 | 0.88 | 15/52 | 89/345 |
| 11 | 352-383 | 414 | 0.196 | 16 | 42 | 39 | 0 | 0.90 | 17/76 | 53/306 |
| 12 | 384-415 | 54 | 0.222 | 0 | 12 | 1 | 0 | 0.87 | 0/0 | 2/22 |
| 13 | 416-447 | 68 | 0.809 | 0 | 55 | 2 | 0 | 0.95 | 0/16 | 2/5 |
| 14 | 448-479 | 239 | 0.820 | 0 | 193 | 35 | 0 | 0.91 | 15/170 | 6/24 |
| 15 | 480-511 | 87 | 0.851 | 1 | 74 | 12 | 0 | 0.88 | 4/50 | 0/4 |
| 16 | 512-543 | 50 | 0.980 | 1 | 49 | 2 | 0 | 0.72 | 1/18 | 0/0 |
| 17 | 544-575 | 100 | 0.730 | 0 | 72 | 5 | 0 | 0.84 | 7/53 | 3/11 |
| 18 | 576-607 | 81 | 0.617 | 0 | 49 | 3 | 0 | 0.79 | 2/31 | 0/10 |
| 19 | 608-639 | 133 | 0.602 | 0 | 78 | 39 | 0 | 0.84 | 4/48 | 2/16 |
| 20 | 640-671 | 62 | 0.532 | 0 | 33 | 2 | 0 | 0.87 | 0/16 | 0/9 |
| 21 | 672-703 | 104 | 0.240 | 1 | 21 | 5 | 0 | 0.61 | 2/13 | 1/27 |
| 22 | 704-735 | 115 | 0.183 | 0 | 21 | 0 | 0 | 0.58 | 0/14 | 1/54 |
| 23 | 736-767 | 38 | 0.211 | 0 | 7 | 1 | 0 | 0.50 | 0/1 | 0/3 |
| 24 | 768-799 | 33 | 0.182 | 0 | 4 | 2 | 0 | 0.67 | 0/0 | 0/1 |
| 25 | 800-831 | 33 | 0.091 | 0 | 2 | 1 | 0 | 0.67 | 0/0 | 0/1 |
| 26 | 832-863 | 35 | 0.200 | 0 | 6 | 2 | 0 | 0.47 | 0/0 | 0/2 |
| 27 | 864-895 | 32 | 0.250 | 0 | 8 | 0 | 0 | 0.57 | 0/0 | 0/0 |
| 28 | 896-927 | 36 | 0.250 | 0 | 9 | 0 | 0 | 0.79 | 0/0 | 0/2 |
| 29 | 928-959 | 214 | 0.117 | 1 | 23 | 2 | 0 | 0.80 | 0/0 | 0/16 |
| 30 | 960-991 | 47 | 0.277 | 0 | 12 | 1 | 0 | 0.85 | 0/0 | 0/0 |
| 31 | 992-1023 | 255 | 0.349 | 0 | 76 | 13 | 0 | 0.96 | 14/57 | 8/64 |

**R2_B_seed6**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 393 | 0.891 | 151 | 296 | 60 | 39 | 0.51 | 82/126 | 15/16 |
| 1 | 32-63 | 439 | 0.640 | 50 | 271 | 8 | 69 | 0.79 | 95/174 | 39/109 |
| 2 | 64-95 | 316 | 0.339 | 23 | 89 | 2 | 23 | 0.74 | 28/93 | 54/176 |
| 3 | 96-127 | 224 | 0.071 | 8 | 5 | 13 | 0 | 0.78 | 8/14 | 40/132 |
| 4 | 128-159 | 67 | 0.119 | 1 | 1 | 6 | 0 | 0.62 | 0/1 | 13/20 |
| 5 | 160-191 | 35 | 0.171 | 1 | 4 | 1 | 0 | 0.46 | 0/0 | 0/3 |
| 6 | 192-223 | 33 | 0.030 | 0 | 1 | 0 | 0 | 0.00 | 0/0 | 0/1 |
| 7 | 224-255 | 32 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 0/0 |
| 8 | 256-287 | 34 | 0.088 | 0 | 3 | 0 | 0 | 0.33 | 1/1 | 0/0 |
| 9 | 288-319 | 32 | 0.062 | 0 | 2 | 0 | 0 | 0.50 | 0/0 | 0/0 |
| 10 | 320-351 | 32 | 0.312 | 0 | 10 | 0 | 0 | 0.30 | 0/0 | 0/0 |
| 11 | 352-383 | 32 | 0.344 | 0 | 9 | 2 | 0 | 0.69 | 0/0 | 0/0 |
| 12 | 384-415 | 32 | 0.406 | 0 | 10 | 3 | 0 | 0.47 | 0/0 | 0/0 |
| 13 | 416-447 | 32 | 0.625 | 1 | 20 | 1 | 0 | 0.88 | 0/0 | 0/0 |
| 14 | 448-479 | 32 | 0.781 | 0 | 24 | 2 | 0 | 0.84 | 0/0 | 0/0 |
| 15 | 480-511 | 32 | 0.844 | 0 | 27 | 0 | 0 | 0.91 | 0/0 | 0/0 |
| 16 | 512-543 | 32 | 0.406 | 0 | 13 | 0 | 0 | 0.67 | 0/0 | 0/0 |
| 17 | 544-575 | 32 | 0.688 | 0 | 21 | 2 | 0 | 0.76 | 0/0 | 0/0 |
| 18 | 576-607 | 32 | 0.625 | 0 | 20 | 0 | 0 | 0.89 | 0/0 | 0/0 |
| 19 | 608-639 | 32 | 0.719 | 0 | 23 | 0 | 0 | 0.88 | 0/0 | 0/0 |
| 20 | 640-671 | 33 | 0.727 | 0 | 24 | 0 | 0 | 0.81 | 0/0 | 1/1 |
| 21 | 672-703 | 32 | 0.531 | 0 | 17 | 0 | 0 | 0.89 | 0/0 | 0/0 |
| 22 | 704-735 | 32 | 0.094 | 0 | 3 | 0 | 0 | 0.33 | 0/0 | 0/0 |
| 23 | 736-767 | 32 | 0.531 | 0 | 17 | 0 | 0 | 0.77 | 0/0 | 0/0 |
| 24 | 768-799 | 32 | 0.656 | 0 | 21 | 0 | 0 | 1.00 | 0/0 | 0/0 |
| 25 | 800-831 | 32 | 0.344 | 0 | 11 | 0 | 0 | 0.85 | 0/0 | 0/0 |
| 26 | 832-863 | 32 | 0.188 | 0 | 6 | 0 | 0 | 0.67 | 0/0 | 0/0 |
| 27 | 864-895 | 32 | 0.156 | 0 | 5 | 0 | 0 | 0.80 | 0/0 | 0/0 |
| 28 | 896-927 | 32 | 0.094 | 0 | 3 | 0 | 0 | 1.00 | 0/0 | 0/0 |
| 29 | 928-959 | 32 | 0.062 | 0 | 2 | 0 | 0 | 1.00 | 0/0 | 0/0 |
| 30 | 960-991 | 32 | 0.094 | 0 | 3 | 0 | 0 | 0.67 | 0/0 | 0/0 |
| 31 | 992-1023 | 32 | 0.125 | 0 | 4 | 0 | 0 | 1.00 | 0/0 | 0/0 |

**R3_B_seed500**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 299 | 0.883 | 72 | 246 | 48 | 27 | 0.44 | 99/154 | 2/18 |
| 1 | 32-63 | 411 | 0.764 | 65 | 284 | 63 | 71 | 0.73 | 49/167 | 9/43 |
| 2 | 64-95 | 447 | 0.609 | 87 | 229 | 66 | 12 | 0.75 | 46/126 | 32/87 |
| 3 | 96-127 | 407 | 0.504 | 43 | 125 | 115 | 13 | 0.83 | 46/141 | 24/146 |
| 4 | 128-159 | 438 | 0.404 | 19 | 131 | 119 | 0 | 0.91 | 45/140 | 35/183 |
| 5 | 160-191 | 470 | 0.251 | 2 | 87 | 41 | 6 | 0.77 | 31/105 | 33/314 |
| 6 | 192-223 | 498 | 0.297 | 0 | 110 | 40 | 0 | 0.92 | 27/142 | 47/324 |
| 7 | 224-255 | 512 | 0.523 | 3 | 252 | 49 | 0 | 0.91 | 39/251 | 24/227 |
| 8 | 256-287 | 512 | 0.596 | 0 | 305 | 12 | 0 | 0.94 | 45/289 | 44/191 |
| 9 | 288-319 | 512 | 0.586 | 0 | 288 | 30 | 0 | 0.90 | 69/286 | 45/191 |
| 10 | 320-351 | 497 | 0.487 | 0 | 242 | 3 | 0 | 0.92 | 38/226 | 27/229 |
| 11 | 352-383 | 512 | 0.842 | 0 | 431 | 15 | 0 | 0.98 | 84/403 | 12/77 |
| 12 | 384-415 | 498 | 0.825 | 0 | 411 | 8 | 0 | 0.97 | 86/390 | 15/76 |
| 13 | 416-447 | 512 | 0.727 | 0 | 372 | 0 | 0 | 0.96 | 59/350 | 16/130 |
| 14 | 448-479 | 380 | 0.968 | 0 | 367 | 4 | 0 | 0.98 | 91/338 | 9/10 |
| 15 | 480-511 | 280 | 0.718 | 0 | 201 | 15 | 0 | 0.99 | 62/179 | 18/69 |
| 16 | 512-543 | 144 | 0.972 | 0 | 140 | 0 | 0 | 0.96 | 25/110 | 0/1 |
| 17 | 544-575 | 390 | 0.977 | 0 | 381 | 0 | 0 | 0.96 | 105/350 | 4/7 |
| 18 | 576-607 | 218 | 0.995 | 0 | 217 | 0 | 0 | 0.96 | 74/185 | 1/1 |
| 19 | 608-639 | 266 | 0.966 | 0 | 257 | 2 | 0 | 0.97 | 109/227 | 6/7 |
| 20 | 640-671 | 206 | 0.995 | 0 | 205 | 0 | 0 | 0.95 | 105/173 | 1/1 |
| 21 | 672-703 | 264 | 0.981 | 0 | 259 | 1 | 0 | 0.95 | 130/227 | 3/5 |
| 22 | 704-735 | 191 | 0.995 | 0 | 190 | 6 | 0 | 0.95 | 98/159 | 0/0 |
| 23 | 736-767 | 313 | 0.958 | 0 | 300 | 0 | 0 | 0.98 | 147/269 | 7/12 |
| 24 | 768-799 | 218 | 0.995 | 0 | 217 | 0 | 0 | 0.97 | 109/186 | 0/0 |
| 25 | 800-831 | 172 | 0.988 | 0 | 170 | 2 | 0 | 0.93 | 88/140 | 0/0 |
| 26 | 832-863 | 223 | 1.000 | 0 | 223 | 0 | 0 | 0.97 | 98/191 | 0/0 |
| 27 | 864-895 | 169 | 0.982 | 0 | 166 | 0 | 0 | 0.97 | 85/135 | 1/2 |
| 28 | 896-927 | 307 | 0.977 | 0 | 300 | 0 | 0 | 0.99 | 120/271 | 1/4 |
| 29 | 928-959 | 199 | 0.995 | 0 | 198 | 2 | 0 | 0.99 | 80/167 | 0/0 |
| 30 | 960-991 | 271 | 0.996 | 0 | 270 | 2 | 0 | 0.97 | 132/239 | 0/0 |
| 31 | 992-1023 | 166 | 0.994 | 0 | 165 | 0 | 0 | 0.94 | 70/133 | 0/1 |

**R3_B_seed501**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 345 | 0.797 | 74 | 251 | 41 | 22 | 0.42 | 81/132 | 19/23 |
| 1 | 32-63 | 473 | 0.459 | 50 | 197 | 22 | 6 | 0.80 | 72/199 | 63/173 |
| 2 | 64-95 | 482 | 0.145 | 13 | 53 | 4 | 0 | 0.87 | 9/66 | 59/381 |
| 3 | 96-127 | 450 | 0.224 | 81 | 20 | 2 | 1 | 0.90 | 6/79 | 71/323 |
| 4 | 128-159 | 465 | 0.060 | 10 | 18 | 0 | 0 | 0.84 | 2/27 | 37/406 |
| 5 | 160-191 | 512 | 0.035 | 0 | 2 | 16 | 0 | 0.83 | 0/17 | 27/463 |
| 6 | 192-223 | 512 | 0.014 | 6 | 0 | 1 | 0 | 0.71 | 0/6 | 47/473 |
| 7 | 224-255 | 467 | 0.041 | 2 | 16 | 1 | 0 | 0.88 | 4/17 | 36/416 |
| 8 | 256-287 | 328 | 0.012 | 1 | 1 | 2 | 0 | 0.50 | 0/2 | 15/292 |
| 9 | 288-319 | 411 | 0.019 | 0 | 8 | 0 | 0 | 0.88 | 2/8 | 17/366 |
| 10 | 320-351 | 305 | 0.003 | 0 | 1 | 0 | 0 | 0.00 | 0/0 | 13/272 |
| 11 | 352-383 | 412 | 0.024 | 1 | 10 | 0 | 0 | 0.64 | 0/9 | 33/355 |
| 12 | 384-415 | 317 | 0.006 | 0 | 0 | 2 | 0 | 0.75 | 0/2 | 27/267 |
| 13 | 416-447 | 314 | 0.003 | 1 | 0 | 0 | 0 | 0.00 | 0/1 | 31/272 |
| 14 | 448-479 | 349 | 0.100 | 35 | 0 | 0 | 0 | 0.94 | 2/35 | 26/274 |
| 15 | 480-511 | 376 | 0.008 | 0 | 3 | 0 | 0 | 0.00 | 0/2 | 34/340 |
| 16 | 512-543 | 275 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 15/239 |
| 17 | 544-575 | 429 | 0.016 | 0 | 7 | 0 | 0 | 0.86 | 0/6 | 33/386 |
| 18 | 576-607 | 325 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 29/279 |
| 19 | 608-639 | 434 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 25/402 |
| 20 | 640-671 | 442 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 30/410 |
| 21 | 672-703 | 363 | 0.008 | 0 | 3 | 0 | 0 | 0.67 | 1/2 | 25/329 |
| 22 | 704-735 | 413 | 0.005 | 0 | 2 | 0 | 0 | 0.50 | 0/1 | 33/380 |
| 23 | 736-767 | 384 | 0.003 | 0 | 1 | 0 | 0 | 1.00 | 0/0 | 39/352 |
| 24 | 768-799 | 400 | 0.003 | 0 | 1 | 0 | 0 | 0.00 | 0/0 | 45/364 |
| 25 | 800-831 | 385 | 0.008 | 0 | 3 | 0 | 0 | 0.00 | 0/1 | 50/338 |
| 26 | 832-863 | 446 | 0.002 | 0 | 0 | 1 | 0 | 1.00 | 1/1 | 24/413 |
| 27 | 864-895 | 399 | 0.005 | 0 | 1 | 1 | 0 | 0.67 | 1/1 | 46/366 |
| 28 | 896-927 | 498 | 0.006 | 0 | 3 | 0 | 0 | 0.00 | 0/1 | 45/452 |
| 29 | 928-959 | 383 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 48/351 |
| 30 | 960-991 | 252 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 30/220 |
| 31 | 992-1023 | 454 | 0.000 | 0 | 0 | 0 | 0 | n/a | 0/0 | 74/422 |

**R3_B_seed502**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 331 | 0.855 | 100 | 255 | 17 | 30 | 0.36 | 94/136 | 12/24 |
| 1 | 32-63 | 429 | 0.590 | 63 | 223 | 16 | 54 | 0.59 | 133/218 | 75/144 |
| 2 | 64-95 | 381 | 0.331 | 11 | 114 | 11 | 4 | 0.72 | 84/122 | 102/214 |
| 3 | 96-127 | 452 | 0.363 | 30 | 129 | 55 | 0 | 0.88 | 30/157 | 26/263 |
| 4 | 128-159 | 482 | 0.052 | 1 | 6 | 18 | 16 | 0.68 | 10/24 | 67/426 |
| 5 | 160-191 | 426 | 0.282 | 38 | 29 | 77 | 5 | 0.88 | 16/118 | 37/276 |
| 6 | 192-223 | 492 | 0.209 | 13 | 20 | 95 | 1 | 0.84 | 28/101 | 60/359 |
| 7 | 224-255 | 332 | 0.123 | 17 | 9 | 16 | 0 | 0.84 | 4/37 | 13/263 |
| 8 | 256-287 | 360 | 0.050 | 13 | 3 | 4 | 1 | 0.65 | 0/17 | 40/311 |
| 9 | 288-319 | 320 | 0.222 | 28 | 22 | 30 | 0 | 0.80 | 18/67 | 10/221 |
| 10 | 320-351 | 141 | 0.170 | 16 | 8 | 6 | 0 | 0.74 | 1/23 | 6/86 |
| 11 | 352-383 | 271 | 0.137 | 12 | 20 | 11 | 0 | 0.68 | 2/35 | 21/204 |
| 12 | 384-415 | 259 | 0.081 | 3 | 1 | 17 | 0 | 0.70 | 4/19 | 12/208 |
| 13 | 416-447 | 275 | 0.102 | 12 | 15 | 1 | 0 | 0.83 | 1/24 | 15/219 |
| 14 | 448-479 | 231 | 0.113 | 5 | 19 | 3 | 0 | 0.76 | 7/25 | 13/174 |
| 15 | 480-511 | 143 | 0.294 | 36 | 2 | 4 | 0 | 0.85 | 0/38 | 12/73 |
| 16 | 512-543 | 189 | 0.085 | 1 | 5 | 11 | 0 | 0.50 | 0/15 | 11/142 |
| 17 | 544-575 | 211 | 0.114 | 18 | 2 | 4 | 0 | 0.91 | 1/24 | 4/155 |
| 18 | 576-607 | 288 | 0.208 | 32 | 27 | 7 | 9 | 0.84 | 1/57 | 11/199 |
| 19 | 608-639 | 286 | 0.035 | 0 | 6 | 4 | 2 | 0.55 | 1/9 | 17/245 |
| 20 | 640-671 | 253 | 0.043 | 2 | 3 | 6 | 10 | 0.67 | 0/10 | 16/211 |
| 21 | 672-703 | 389 | 0.152 | 21 | 37 | 9 | 14 | 0.66 | 1/57 | 16/300 |
| 22 | 704-735 | 353 | 0.215 | 26 | 32 | 27 | 14 | 0.83 | 3/74 | 15/247 |
| 23 | 736-767 | 374 | 0.115 | 29 | 5 | 9 | 0 | 0.94 | 0/39 | 25/303 |
| 24 | 768-799 | 257 | 0.086 | 21 | 0 | 8 | 0 | 0.83 | 1/22 | 15/203 |
| 25 | 800-831 | 304 | 0.211 | 17 | 37 | 13 | 0 | 0.84 | 4/61 | 17/211 |
| 26 | 832-863 | 350 | 0.129 | 4 | 32 | 10 | 0 | 0.80 | 1/44 | 6/274 |
| 27 | 864-895 | 331 | 0.048 | 1 | 6 | 9 | 0 | 0.50 | 1/14 | 14/285 |
| 28 | 896-927 | 176 | 0.057 | 0 | 7 | 3 | 0 | 0.62 | 1/10 | 5/134 |
| 29 | 928-959 | 141 | 0.035 | 2 | 4 | 0 | 4 | 0.17 | 1/5 | 2/104 |
| 30 | 960-991 | 411 | 0.068 | 3 | 2 | 23 | 13 | 0.64 | 0/26 | 12/353 |
| 31 | 992-1023 | 383 | 0.018 | 5 | 0 | 2 | 6 | 0.43 | 0/7 | 29/344 |

**R4_B_seed604**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 387 | 0.881 | 141 | 324 | 24 | 55 | 0.51 | 89/147 | 3/9 |
| 1 | 32-63 | 381 | 0.806 | 56 | 299 | 21 | 29 | 0.63 | 69/220 | 12/36 |
| 2 | 64-95 | 366 | 0.522 | 56 | 153 | 19 | 29 | 0.68 | 37/184 | 30/149 |
| 3 | 96-127 | 412 | 0.551 | 19 | 186 | 48 | 1 | 0.81 | 34/213 | 11/159 |
| 4 | 128-159 | 487 | 0.417 | 31 | 172 | 27 | 2 | 0.92 | 27/194 | 34/250 |
| 5 | 160-191 | 461 | 0.666 | 47 | 258 | 49 | 0 | 0.91 | 30/270 | 11/134 |
| 6 | 192-223 | 491 | 0.599 | 19 | 276 | 53 | 14 | 0.91 | 29/250 | 24/163 |
| 7 | 224-255 | 497 | 0.314 | 4 | 125 | 35 | 1 | 0.91 | 19/80 | 15/201 |
| 8 | 256-287 | 497 | 0.247 | 35 | 104 | 18 | 14 | 0.94 | 20/92 | 29/229 |
| 9 | 288-319 | 512 | 0.184 | 16 | 53 | 29 | 10 | 0.88 | 17/80 | 27/379 |
| 10 | 320-351 | 512 | 0.416 | 31 | 202 | 2 | 0 | 0.95 | 21/138 | 6/227 |
| 11 | 352-383 | 512 | 0.566 | 22 | 288 | 9 | 0 | 0.94 | 22/240 | 14/178 |
| 12 | 384-415 | 512 | 0.734 | 18 | 375 | 6 | 1 | 0.97 | 11/244 | 20/93 |
| 13 | 416-447 | 512 | 0.547 | 23 | 271 | 4 | 0 | 0.97 | 6/251 | 11/194 |
| 14 | 448-479 | 512 | 0.795 | 13 | 405 | 5 | 0 | 0.95 | 4/294 | 1/86 |
| 15 | 480-511 | 512 | 0.789 | 1 | 404 | 8 | 0 | 0.98 | 0/286 | 6/97 |
| 16 | 512-543 | 512 | 0.898 | 76 | 430 | 0 | 0 | 0.98 | 8/374 | 1/42 |
| 17 | 544-575 | 512 | 0.740 | 7 | 369 | 12 | 0 | 0.98 | 14/273 | 5/93 |
| 18 | 576-607 | 512 | 0.951 | 104 | 487 | 4 | 0 | 0.98 | 17/286 | 3/16 |
| 19 | 608-639 | 512 | 0.955 | 124 | 460 | 16 | 0 | 0.96 | 5/314 | 0/11 |
| 20 | 640-671 | 512 | 0.963 | 64 | 479 | 7 | 0 | 0.97 | 8/238 | 0/12 |
| 21 | 672-703 | 512 | 0.902 | 65 | 461 | 1 | 0 | 0.97 | 24/358 | 5/36 |
| 22 | 704-735 | 512 | 0.686 | 95 | 306 | 0 | 0 | 0.99 | 10/290 | 12/143 |

**R4_B_seed605**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 369 | 0.873 | 115 | 281 | 39 | 32 | 0.42 | 122/155 | 18/18 |
| 1 | 32-63 | 375 | 0.435 | 40 | 153 | 9 | 59 | 0.61 | 58/123 | 82/178 |
| 2 | 64-95 | 489 | 0.319 | 43 | 122 | 15 | 50 | 0.86 | 42/151 | 53/306 |
| 3 | 96-127 | 460 | 0.237 | 20 | 68 | 31 | 16 | 0.90 | 29/106 | 18/322 |
| 4 | 128-159 | 468 | 0.335 | 10 | 136 | 33 | 55 | 0.85 | 23/152 | 15/284 |
| 5 | 160-191 | 512 | 0.303 | 15 | 127 | 16 | 0 | 0.87 | 12/139 | 27/330 |
| 6 | 192-223 | 497 | 0.135 | 2 | 64 | 3 | 2 | 0.82 | 5/63 | 35/402 |
| 7 | 224-255 | 512 | 0.139 | 31 | 22 | 18 | 10 | 0.92 | 6/68 | 61/410 |
| 8 | 256-287 | 512 | 0.098 | 0 | 47 | 3 | 0 | 0.89 | 4/45 | 54/434 |
| 9 | 288-319 | 497 | 0.266 | 0 | 126 | 7 | 0 | 0.97 | 15/124 | 41/341 |
| 10 | 320-351 | 512 | 0.877 | 0 | 448 | 9 | 0 | 0.99 | 53/421 | 17/59 |
| 11 | 352-383 | 512 | 0.990 | 0 | 507 | 7 | 0 | 0.99 | 77/479 | 0/0 |
| 12 | 384-415 | 498 | 0.988 | 0 | 492 | 6 | 0 | 0.99 | 57/459 | 3/6 |
| 13 | 416-447 | 497 | 1.000 | 0 | 497 | 19 | 0 | 0.98 | 64/465 | 0/0 |
| 14 | 448-479 | 467 | 1.000 | 0 | 466 | 4 | 0 | 0.98 | 24/435 | 0/0 |
| 15 | 480-511 | 482 | 0.983 | 0 | 474 | 8 | 0 | 0.98 | 16/441 | 1/7 |
| 16 | 512-543 | 512 | 0.992 | 1 | 508 | 11 | 0 | 0.98 | 48/478 | 0/2 |
| 17 | 544-575 | 512 | 0.990 | 0 | 507 | 1 | 0 | 0.99 | 58/475 | 0/3 |
| 18 | 576-607 | 512 | 0.990 | 0 | 507 | 0 | 0 | 0.99 | 48/465 | 1/2 |
| 19 | 608-639 | 512 | 0.998 | 0 | 511 | 5 | 0 | 0.99 | 36/479 | 0/1 |
| 20 | 640-671 | 73 | 0.973 | 1 | 71 | 1 | 0 | 0.96 | 2/65 | 0/0 |

**R4_B_seed606**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 379 | 0.863 | 100 | 308 | 16 | 29 | 0.46 | 85/121 | 9/16 |
| 1 | 32-63 | 237 | 0.806 | 74 | 175 | 36 | 14 | 0.60 | 13/52 | 2/8 |
| 2 | 64-95 | 442 | 0.706 | 41 | 308 | 6 | 5 | 0.81 | 35/287 | 20/110 |
| 3 | 96-127 | 446 | 0.574 | 40 | 164 | 113 | 4 | 0.91 | 31/247 | 4/166 |
| 4 | 128-159 | 473 | 0.507 | 70 | 168 | 36 | 0 | 0.91 | 19/228 | 12/213 |
| 5 | 160-191 | 512 | 0.721 | 61 | 269 | 155 | 0 | 0.93 | 42/346 | 14/134 |
| 6 | 192-223 | 512 | 0.834 | 14 | 246 | 346 | 0 | 0.90 | 111/404 | 18/76 |
| 7 | 224-255 | 512 | 0.967 | 44 | 423 | 411 | 0 | 0.94 | 72/466 | 7/14 |
| 8 | 256-287 | 512 | 0.951 | 246 | 486 | 430 | 0 | 0.94 | 98/449 | 12/18 |
| 9 | 288-319 | 512 | 0.951 | 16 | 485 | 264 | 0 | 0.93 | 117/432 | 12/24 |
| 10 | 320-351 | 512 | 0.980 | 2 | 502 | 327 | 0 | 0.95 | 77/381 | 5/7 |
| 11 | 352-383 | 512 | 0.906 | 0 | 464 | 144 | 0 | 0.96 | 87/399 | 17/35 |
| 12 | 384-415 | 512 | 0.934 | 1 | 473 | 131 | 0 | 0.97 | 94/347 | 9/16 |
| 13 | 416-447 | 512 | 0.832 | 1 | 357 | 214 | 0 | 0.94 | 72/272 | 14/65 |
| 14 | 448-479 | 512 | 0.518 | 14 | 223 | 107 | 0 | 0.94 | 57/225 | 26/162 |
| 15 | 480-511 | 512 | 0.254 | 0 | 126 | 22 | 0 | 0.95 | 31/106 | 91/328 |
| 16 | 512-543 | 512 | 0.355 | 0 | 181 | 24 | 0 | 0.91 | 45/171 | 74/272 |
| 17 | 544-575 | 512 | 0.268 | 0 | 117 | 24 | 0 | 0.93 | 30/123 | 104/334 |
| 18 | 576-607 | 512 | 0.246 | 3 | 113 | 38 | 0 | 0.95 | 17/101 | 90/332 |
| 19 | 608-639 | 512 | 0.191 | 0 | 93 | 15 | 0 | 0.86 | 49/87 | 160/295 |
| 20 | 640-671 | 512 | 0.145 | 0 | 69 | 7 | 0 | 0.90 | 28/55 | 236/385 |
| 21 | 672-703 | 512 | 0.301 | 0 | 106 | 89 | 0 | 0.86 | 75/146 | 181/315 |
| 22 | 704-735 | 512 | 0.240 | 0 | 112 | 41 | 0 | 0.81 | 77/114 | 202/343 |
| 23 | 736-767 | 512 | 0.350 | 0 | 172 | 72 | 0 | 0.86 | 101/153 | 166/277 |
| 24 | 768-799 | 512 | 0.342 | 1 | 171 | 36 | 0 | 0.95 | 119/150 | 204/272 |
| 25 | 800-831 | 512 | 0.408 | 0 | 123 | 148 | 0 | 0.92 | 129/201 | 148/241 |
| 26 | 832-863 | 512 | 0.410 | 0 | 207 | 48 | 0 | 0.92 | 128/172 | 184/252 |
| 27 | 864-895 | 498 | 0.440 | 11 | 205 | 47 | 0 | 0.94 | 136/189 | 163/229 |

**RP_B_seed402**  (window: thoughts, affect_rate, neg/pos/sur counts, repeat_ctx_frac, P(change|aff) n, P(change|non) n)

| win | episodes | thoughts | affect rate | neg | pos | sur | intent | repeat ctx | P(chg\|aff) | P(chg\|non) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0-31 | 343 | 0.918 | 113 | 305 | 11 | 34 | 0.50 | 88/126 | 5/7 |
| 1 | 32-63 | 213 | 0.296 | 7 | 62 | 1 | 11 | 0.53 | 33/59 | 60/122 |
| 2 | 64-95 | 287 | 0.387 | 9 | 93 | 27 | 4 | 0.81 | 17/98 | 18/143 |
| 3 | 96-127 | 393 | 0.168 | 16 | 38 | 12 | 0 | 0.95 | 7/64 | 26/297 |
| 4 | 128-159 | 427 | 0.119 | 0 | 45 | 6 | 1 | 0.88 | 26/49 | 52/346 |
| 5 | 160-191 | 451 | 0.058 | 1 | 25 | 1 | 0 | 0.90 | 3/23 | 52/396 |
| 6 | 192-223 | 512 | 0.107 | 2 | 21 | 32 | 0 | 0.90 | 2/52 | 79/428 |
| 7 | 224-255 | 497 | 0.087 | 3 | 1 | 40 | 1 | 0.91 | 10/41 | 20/424 |
| 8 | 256-287 | 482 | 0.004 | 0 | 0 | 2 | 0 | 0.50 | 0/1 | 31/449 |
| 9 | 288-319 | 497 | 0.189 | 3 | 1 | 90 | 0 | 0.91 | 1/86 | 37/379 |
| 10 | 320-351 | 511 | 0.125 | 3 | 0 | 61 | 0 | 0.95 | 1/61 | 32/418 |
| 11 | 352-383 | 446 | 0.184 | 12 | 27 | 44 | 0 | 0.92 | 4/77 | 39/337 |
| 12 | 384-415 | 462 | 0.056 | 2 | 0 | 24 | 0 | 0.90 | 6/26 | 34/403 |
| 13 | 416-447 | 452 | 0.038 | 1 | 16 | 0 | 0 | 0.68 | 0/12 | 39/407 |
| 14 | 448-479 | 482 | 0.131 | 5 | 51 | 7 | 0 | 0.89 | 5/58 | 85/389 |
| 15 | 480-511 | 491 | 0.120 | 2 | 56 | 3 | 0 | 0.81 | 17/56 | 82/403 |
| 16 | 512-543 | 454 | 0.183 | 5 | 72 | 15 | 0 | 0.84 | 31/78 | 84/344 |
| 17 | 544-575 | 442 | 0.038 | 4 | 10 | 3 | 0 | 0.39 | 2/16 | 73/394 |
| 18 | 576-607 | 425 | 0.139 | 18 | 28 | 13 | 0 | 0.78 | 20/53 | 69/338 |
| 19 | 608-639 | 503 | 0.018 | 3 | 4 | 3 | 0 | 0.30 | 0/9 | 31/462 |
| 20 | 640-671 | 499 | 0.012 | 0 | 1 | 5 | 0 | 0.83 | 0/6 | 51/461 |
| 21 | 672-703 | 512 | 0.045 | 0 | 20 | 3 | 0 | 0.83 | 19/22 | 82/458 |
| 22 | 704-735 | 512 | 0.037 | 1 | 18 | 1 | 0 | 0.76 | 0/19 | 24/460 |
| 23 | 736-767 | 502 | 0.149 | 10 | 51 | 23 | 0 | 0.79 | 2/73 | 4/391 |
| 24 | 768-799 | 487 | 0.097 | 3 | 46 | 1 | 0 | 0.66 | 1/45 | 18/388 |
| 25 | 800-831 | 512 | 0.254 | 16 | 126 | 4 | 0 | 0.91 | 5/111 | 21/327 |
| 26 | 832-863 | 500 | 0.312 | 26 | 146 | 2 | 0 | 0.89 | 22/110 | 12/182 |
| 27 | 864-895 | 487 | 0.407 | 53 | 159 | 7 | 0 | 0.89 | 3/93 | 10/193 |
| 28 | 896-927 | 512 | 0.730 | 70 | 353 | 12 | 0 | 0.95 | 6/162 | 2/61 |
| 29 | 928-959 | 512 | 0.758 | 1 | 388 | 9 | 0 | 0.98 | 0/185 | 0/80 |
| 30 | 960-991 | 512 | 0.770 | 2 | 394 | 0 | 0 | 0.98 | 4/85 | 0/40 |
| 31 | 992-1023 | 512 | 0.719 | 2 | 367 | 1 | 0 | 0.98 | 1/133 | 9/42 |
| 32 | 1024-1055 | 384 | 0.643 | 15 | 246 | 0 | 0 | 0.98 | 3/87 | 1/42 |
