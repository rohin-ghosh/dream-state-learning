# Node3 R227 — sanitized actual LOAD and completed-sleep receipts

Receipt cut: **2026-09-18 08:44:32 UTC**. Node aliases only. Five caption natives and three math natives are actually live; directories/preparation are not counted as lives. No raw targets, prompts, reference panels, credentials, hostnames, addresses or state binaries are included.

| GPU | Exact life | Native PID | LOADED UTC | Latest complete cycle | Candidates / presented | Updates | Checkpoint optimizer |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: |
| 0 | r213_r226_caption_observation_fork | 1784760 | 08:36:32.658195 | 52 | 3 / 3 | 48 | 4956 |
| 1 | r213_math_a | 1783333 | 08:30:46.737459 | 70 | 3 / 3 | 48 | 5436 |
| 2 | r213_math_b_fork | 1783352 | 08:31:22.960451 | 73 | 3 / 2 | 32 | 5228 |
| 3 | r213_r226_caption_perspective_fork | 1784767 | 08:36:32.635521 | 52 | 3 / 3 | 48 | 4956 |
| 4 | r213_math_c | 1783964 | 08:34:48.993161 | 75 | 3 / 0 | 0 | 5244 |
| 5 | r213_r226_caption_revision_fork | 1784770 | 08:36:32.584850 | 52 | 3 / 3 | 48 | 4956 |
| 6 | r213_r226_caption_selfderive_fork | 1784772 | 08:36:32.637194 | 52 | 4 / 4 | 64 | 4972 |
| 7 | r213_r226_caption_unparented_fork | 1784774 | 08:36:32.580408 | 52 | 4 / 4 | 64 | 4972 |

`RECEIPTS.json` contains bounded projections of actual LOADED, SLEEP_REQUEST, SLEEP_RECIPE and SLEEP_COMPLETE records: exact journal/index/hash references, source-bound candidate hashes, masks, presentation counts, exclusions and checkpoint totals. These are whole completed sleeps, not an extrapolation from partial UPDATEs. Each candidate's original RESPONSE/raw-target equality is verified without publishing its text. Each listed sleep's update count equals its recorded presentation sum. The receipt cut is not a synchronized-cycle comparison or a quality/learning-effect claim.

## Active policy — important limitations

- All five captions started from complete checkpoint51/context5846, adapter `82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92`, optimizer4908. Four received new Astra guidance; GPU7 received **zero new parent messages**. All inherit the same historically parented C2 state, so GPU7 is not a never-parented lineage.
- Caption plan and driver omit `code_target_filter`, `learn_review_filter`, `content_target_filter`, `prose_target_filter`, `question_target_filter`, and `fabricated_speaker_filter`. Their diagnostics do not drop targets. The five first completed sleeps trained **all 17 actual candidates, 16 presentations each, 272 updates total, no exclusions**.
- **The default plain-presentation scaffold rule remains active in all eight resident sources.** A CPU-only synthetic probe of each exact source rejects an own-authored scaffold marker with `journal_scaffolding_target`. This is a distinct remaining rule, not a disabled semantic selector. None of the five completed caption sleeps in this cut excluded a candidate for it; that does not mean the rule is disabled.
- Main's later explicit `learn_row_policy='R227_ALL_AUTHENTIC_CHILD_ROWS_V1'` is **absent from both active plan and active driver on all eight lives**. Source-ready/testing is not adoption. The current caption LOADs/SLEEP_RECIPEs do not demonstrate the later policy's scaffold bypass or inherited-annotation semantics.
- Math retains its prior resident filters. Math B's latest completed cycle excluded one candidate, and Math C's excluded three, for `provisional_english_target_script_quarantine`. C's zero-update COMPLETE is a real filtered cycle, not evidence of an idle/dead process. A's latest cycle had no exclusions. Do not call the trio fully R227-converted.
- Math recovery used saved complete checkpoints, not exact resident continuity. Historical natural exits, failed resumes and interrupted-tail loss remain preserved. No new shared mathematical agreement is claimed.

Main's policy release is parent commit `bb1e9a9033979d50ed97072675515f7290de1237`. This publication does not edit that implementation or activate it in a resident process. No child pause, stop, restart, source overwrite, alias substitution or transport modification was performed for this publication.

## First future ACT after transport repair

The initial transport errors remain historical failures. Leibniz owns the repair; no second scorer/transport implementation was introduced here.

`FIRST_FUTURE_ACT.json` binds GPU7's **new** ACT116 at **08:44:31.733948 UTC** to actual RESPONSE113, hash `dd2cad4770944b6dc70593b5baf05f41fed3e812db6885d72c97bb0e63b59c96`. All three exact caption spans are from that ACT, not THINK salvage, and their source hashes verify. Its scorer receipt is `27df2367c31320b9dde08133d4e27cd1fe7b6eea00e3735bc4b0b6ddac31c2d1`.

There are **3 newly evaluated captions, 0 cached/replayed, 0 accepted**; ranks54/65/65 against the stated65-caption comparison. Each result explicitly reports `replayed=false`. This publication reads existing receipts only; it does not resubmit an old ACT, create an attempt by querying a score, or equate a successful envelope with scoring. No humour improvement or learning improvement is inferred.

## Publication validation

Run `python3 -B -m unittest discover -s research_loop/workers/rohin205_node3_20260918/r227_publication -p 'test_receipts.py' -v` in this clean checkout. Tests verify source-bound candidate accounting, actual completed-sleep totals, the no-selector/later-policy distinction, source-span/replay status, and absence of private-target/host/address/credential fields. The manifest binds the published files; private raw journals remain with their operator.
