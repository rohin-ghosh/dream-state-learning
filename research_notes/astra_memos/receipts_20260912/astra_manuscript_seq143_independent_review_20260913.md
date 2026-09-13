# Independent manuscript review — SEQ143 bounded cut

**Disposition: ACCEPT the six-file manuscript integration at the exact hashes below. No validity-critical correction required.** This accepts faithful incorporation of C79–C82 and their qualifications, not scientific promotion, publication readiness, operational authorization, or a fresh approval of all historical claims.

Reviewer: independent Codex review context, not author Copernicus. Date: September 13, 2026 UTC. Final source/author identity check: 08:28:00 UTC. Handoff: `/tmp/astra_manuscript_seq137_143_handoff_20260913.md`. Evidence cutoff remains **SEQ143**, regardless of concurrent HEAD advances. No SEQ144/145 evidence or new sequence entry is required by this review.

## Scope and exact-byte binding

Read repository `AGENTS.md`, the EDITSTOP handoff, and the six-file working-tree diff. Inspected the newly added sections, tables, summaries and amended historical-exclusion language. The four new result subsections match byte-for-byte between the TeX manuscripts; the new abstract paragraph matches both TeX files and the companion abstract. Historical numerical tables were not replaced by this patch.

All six hashes matched the handoff at first inspection and again at the final identity check:

| File, relative to `/data/home/rohing/dream-state` | SHA256 |
| --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `7ebf780637d92cf2eb7863b7013116f8995edbd92e942556012ff1389f12541c` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `b228811f5bb38c871d51defd5b4555037b099ed52fc92b2ebb778b7e6b9ee408` |
| `paper_prototype/main.tex` | `ee97841bc0ee4a5307b28f381aae3c0cab306ab9ea47bde792a92a729bdcda4c` |
| `paper_prototype/README.md` | `3a1ff6ced6d6d8ab4c03c37e9862785f2e26e866077ef801261d4f60c3b0c39b` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `28c7f6a10eba2f2696d659723f718b6f82cba9fa846c6da2d0c475f9aaa5a6f3` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `f2210ab8b73ac9d3a0354817a63266c9b58c8c8055c1369c2ec3f33e5f01665b` |

Observed final HEAD: `773dc4abb936c21f25f16617e75506cde0ecc50d`; this is context, not an expansion of the evidence cut. The scoped diff remains six files, 906 insertions and 32 deletions. SHA256 of `git diff --` with the six paths in the table's order: `2470c34e0a8e59a4f2c897f202d27ba4b9dc6ec7f635a88e690a7e9d67aaa495`. Acceptance binds the file hashes, not mutable HEAD or future edits.

## C79 — completed null contrasts versus missing original cells

Locations: `paper_prototype/astra_sprint_draft_20260912.tex:3157`, `paper_prototype/main.tex:918`, `paper_prototype/README.md:39`, claim map `:3507`.

**Verified:** original seeds 1/2 at both learning rates complete four loops, each 11 stages, 128 calls, three physical fits and 100 updates. All five readouts per completed loop are old 4/8, new 4/8, legal 16/16. Final paired counts are both 8 / PROMOTE-only 0 / SHADOW-only 0 / neither 8. Thus four-original-complete work is 512 calls / 12 fits / 400 updates, and high-minus-low is zero for each of the two paired learners, not an observed three-seed result.

Exact structured binding: source A below, `runs.<seed1_low|seed1_high|seed2_low|seed2_high>.native_collection.{completed,work,reports,endpoint.paired}`, plus `paired_learners` and `descriptive`. All six local collection files identified by `runs.*.collection.path` hash-match their stored pins and JSON-equal the embedded `native_collection`. I inspected/asserted the completed readout counts and original null descriptive means/ranges.

The two seed0 originals remain `NONREPORTABLE_RUNTIME_ABORT`: high closes only baseline/wake1; low closes baseline/wake1/fit1/report1_PROMOTE/report1_SHADOW/wake2_PROMOTE. Sources C/D retain `reason.type=TimeoutExpired` and targeted XML-query timeout after 30 seconds. Neither supplies a final scored endpoint or a zero work estimate. The manuscript correctly keeps these missing and does not impute them from the retry.

Source E separately records low-seed0 attempt2 complete, 128 calls / three fits / 100 updates, the same five flat panels and final pairing, with 8 first / 16 cumulative admitted records. Its existence does not complete the immutable original roster. High recovery is explicitly pending **at the cut**, not asserted to be pending now. Core `native_verified=false` and `scientific_pass=null` are retained; collector replay flags do not promote them. Null greedy treatment contrast is not evidence of no parameter/distribution change.

**Required correction: none.**

## C80 — positive field changes with an actually failed screen

Locations: sprint TeX `:3202`, main TeX `:963`, README `:58`, claim map `:3549`.

**Verified directly from source F's stored item scores:** OFF/PLAIN/CONTRASTIVE held strict = 2/17/19 of 24; D1 = 0/9/12; D2 = 2/8/7; record canary = 0/8/9; general canary = 11/12/12. `material_scores.states.*.items`, `.totals`, `.held_totals` and `.paired_held` agree. Recounting stored strict flags gives 17 wins/0 losses over OFF and 3 wins/1 loss over PLAIN. All 17 OFF wins start syntax-invalid; the four PLAIN-to-CONTRASTIVE status changes are schema/interface-valid on both sides.

Exact field witnesses in `material_scores.states.<plain|contrastive>.items`:

- D1 wins `perception:5cc7ba90aa459dbd2cf6ced99e11be58103099e997f8334ff04a39e38332bb49`, `perception:82af6762ed0a3b32965b46226109796b57bdf7dcc515d467030e1075bbfe3e40`, and `perception:d7358ea228d9f57060009ade48b9526cb9264bd4db7a6fc24e1d74d76bcdf6c6`: raw `predicted:false` becomes `null`, with relation corrected to `unavailable`; observed/TRY were already right. These are not fence removal.
- D2 loss `perception:73674efcc082eb2b69968680ae94c682d308bd8eb62b61317217c9a53e813198`: raw TRY changes from `[13,7,-19]` to `[13,7,19]`. This is a real field regression, not a missing or malformed response.

`exploratory_screen_pass=false` is preserved. The frozen protocol `research_notes/astra_memos/ASTRA_CONTRASTIVE_PERCEPTION_PROTOCOL_2026-09-13.md:56` requires held >=20, each wrapper >=9, and improvement >=4 over each control. Observed 19, D2 7 and +2 over PLAIN fail three conditions. Sources G/H support the additional 21 jointly valid pairs, three versus two duplicate-key failures, both-wrapper 8/12 PLAIN versus 7/12 contrastive, and the earlier-outcome-complement shortcut. The manuscript preserves all these limits rather than upgrading the result to robust source binding.

Work is correctly bounded to 144 calls / two fits / 24 updates, 12 rows and 48 presentations per arm, controller 1323.156 seconds; source F's fit manifests/receipts carry these measured values. Equal updates/targets are not called matched compute. No OFF-correct canary regression is carefully distinguished from universal no-harm: record OFF=0 is vacuous, and comparison with PLAIN has two record wins and one loss.

**Required correction: none.** Do not replace the strict parser with the later Level1 fence-permitting parser, equate +17 to 17 demonstrated semantic gains, erase the +3/-1 valid-field result as mere formatting, or promote this failed screen. The current patch does none of those things.

## C81 — genuine authored content acquisition, limited replication

Locations: sprint TeX `:3253`, main TeX `:1014`, README `:82`, companion abstract `:398`, claim map `:3594`.

**Verified:** sources I/J cover all 12 first-roster cells, four skills x learner seeds 0/1/2, fixed material seed 0. I independently hash-checked all 12 local `scores.json` and all 12 `collection.json` against `cells[].{scores_sha256,collection_sha256}` in I. Their paths are `cells[].local_scores_path` and `.local_collection_path`, under `/tmp/astra_level1_first_scores_20260913/<cell>/`.

Using these existing score objects, I checked row-level stored content/strict flags and format counts against panel totals, recomputed paired wins/losses by row ID, and compared every README cell row. These are checks of stored scoring evidence, not another scorer execution or scientific rerun.

| Skill, same counts in all three learners | Held content OFF -> post /48 | Held strict OFF -> post /48 | Canary content=strict /12 | Content W/L |
| --- | --- | --- | --- | --- |
| Prediction | 22 -> 48 | 22 -> 48 | 11 -> 12 | 26/0 |
| Goal completion | 32 -> 48 | 32 -> 48 | 11 -> 12 | 16/0 |
| Contradiction | 17 -> 48 | 0 -> 48 | 12 -> 12 | 31/0 |
| Update judgement | 8 -> 48 | 0 -> 48 | 12 -> 12 | 40/0 |

Each root records 120 calls / one fit / 320 updates / 1280 presentations. Summing I's per-cell cost entries reproduces 1440 calls / 12 fits / 3840 updates / 15360 presentations, 4826060 training / 251819 supervised / 5053224 padded tokens, fit 4646.8 seconds and controller 7811.911345877044 seconds. Manuscript rounding is consistent. These are accounting sums, not fleet wall time or measured utilization.

The content-versus-format distinction is real and correctly bounded. Source K already permits one enclosing JSON/code fence for content, while strict requires canonical output. J's error breakdown distinguishes prediction's 22 already-canonical typed-decision errors plus four unparseable responses; goal's 16 canonical wrong-value decisions; contradiction's 17 content-correct fenced outputs and 31 field-wrong outputs; and update's 8 correct-fenced / 32 schema-valid field-wrong / 2 reason-domain-invalid / 6 unparseable outputs. One length-capped item is an observed failure inside a completed root, not an unobserved experiment.

Representative stored raw witnesses inspected, each under seed0's `scores.json` at `cells.OFF.held.rows` and the matching `cells.post.held.rows`:

- Prediction `prediction:held:14:True:skin3`: canonical abstain/null/insufficient_evidence -> predict/true/public_evidence.
- Goal `goal_completion:held:42:skin2`: canonical continue/false -> complete/true.
- Contradiction `contradiction:1550df676b1608b3770f0a41236167c4a2e1426186ae2f71a0cc13d76b2a5de2`: fenced disagree/disagreement -> insufficient/ambiguous_prediction. Removing the fence alone cannot produce the corrected fields.
- Update `update_judgement:27d88d2577127d30e0dfe5a9229b00d97b8f1a04b61a2a4829bf1688d8a8fa25`: fenced admit/supported -> abstain/outcome_action_mismatch. Again, not merely a format change.

The patch correctly limits inference to authored-fixture acquisition against no-update OFF: three fitting seeds are not three independent datasets, 576 held renderings are not independent trials, shared canaries are not broad retention, reason labels are not reasoning traces, and supplied goals are not autonomous goal creation. The cold-base standalone recipe is distinguished from SEQ113's warm-parent 80+320 setup. No matched trained parenting effect or general G3 is claimed. Existing `automatic_pass=false` / `scientific_pass=null` remain intact. Proposed prospective source-transfer/actual-record work is future work, not a reported result or launch instruction.

**Required correction: none.**

## C82 — infrastructure missingness, never scientific zeros

Locations: sprint TeX `:3322`, main TeX `:1083`, README `:129`, claim map `:3650`.

Source L's exact reconciliation supports six prepared cells, five launches/OFF failures and five release receipts, zero fits, zero generated request/response captures and zero complete roots. The sixth is prepared-only because the conservative reservation guard stopped launch. Its per-cell table, five stderr SHA256 pins and named launch/start/failure/release chains distinguish these cases.

The manuscript accurately says missing scientific endpoints, **not 0/5 accuracy or five scientific failures**. It retains the diagnosis that JIT cannot discover `ninja`, while distinguishing executable existence and a fresh wrapper PATH observation from the unrecorded historical parent environment. It does not claim successful compilation, historical zombie state, native A100 parity or fresh all-process clearance.

**Required correction: none.** Review of C82 is bounded to the locally archived, hash-matching failure report; I did not fetch its remote stderr files, inspect live processes or independently re-certify its reported receipt chains.

## Exact source artifacts checked

Except K, paths below are beneath `research_notes/astra_memos/receipts_20260912/`. All twelve listed SHA256 values were independently recomputed locally and match the manuscript pins. JSON selectors and report sections above bind the numerical claims, not just document titles.

| ID | Artifact | SHA256 |
| --- | --- | --- |
| A | `astra_l2_lr_original_six_analysis_20260913.json` | `32bdeb890d23e58da1958b0fc94e07e967a6312174ee9e6434a4b09a54a2f9a8` |
| B | `astra_l2_lr_prepared_20260913_attempt1.json` | `2cf367e16116d205eb1e938d05d786d99309d4ae4df4d7afed66863d9d1f865b` |
| C | `astra_l2_lr_seed0_high_attempt1_collected.json` | `a40cd71a0e2fce8a1bd451db19cc7c5e6ec4b91834cf3bf02210bc59d3bc6957` |
| D | `astra_l2_lr_seed0_low_attempt1_collected.json` | `96cd52a01e83f60591b67993d7c6ddcda71b34dda30b5a5952c920da4340d4fe` |
| E | `astra_l2_lr_seed0_low_20260913_attempt2_collected.json` | `def6bc23536a7014b1747f3c42ea2588669f4f386f3429a1532015ce8c38d4b3` |
| F | `astra_contrastive_scores_20260913_attempt1.json` | `7af6484ebb72abc81d2f17d29e7ca15786599afba0b22e88139a80403f3412d0` |
| G | `astra_contrastive_independent_analysis_20260913.md` | `b381effa29b4114ab2c9ce9674cf931bc6a2db0fc98abafb96369c39d7509b68` |
| H | `astra_contrastive_material_advisory_20260913.md` | `6d4e3982521a8cec81f3729461a1947b266cabd8ca7088c2c3a00eb15a5d2944` |
| I | `astra_level1_first_roster_analysis_20260913.json` | `156662015a531a5644e1e1e754f54e0b302fe4221b9b739b5d409876762339d8` |
| J | `astra_level1_first_roster_analysis_20260913.md` | `3ba88822f35b2a295c80d4f870828802f78997a4589cf34eea6f85d646a6b1b9` |
| K | `research_notes/astra_memos/ASTRA_LEVEL1_SKILL_ROSTER_PROTOCOL_2026-09-13.md` | `c5420d9b6464eca62695be450884c2a3226615a065a3e7d6b9021fb2c7303297` |
| L | `astra_a100_level1_failure_20260913.md` | `6d464fb79494274d6bcb05de66643f486dbf1c0b6d2c58e510d57f3ad3623c92` |

## Smallest corrections and review limits

- **Blocking corrections: none.** Main need not wait for SEQ144/145, a new experiment, or a new whole-analysis pass to use this bounded review.
- Optional clarity only: in the opening summaries, “null endpoints” could become “zero observed treatment contrasts” so it cannot be confused with the genuinely missing seed0 endpoints. The detailed tables already make the distinction correctly; this is not an acceptance condition. No author text was changed here.
- Accepted unchanged: R1 supplement does not repair its aborted primary; HF forced-candidate evidence does not replace native greedy readouts; failure of a recipe is not no learning or a verdict on H1/H2. Newer-roster and real-record outcomes remain outside this review's cut.
- This is independent manuscript-to-evidence inspection, with small stored-count/hash checks, not a repeated end-to-end scientific analysis. I did not run the original scorers, reconstruct all material, hash full tar payloads, load tensors/models, verify native inference or reproduce training. Detailed source-field categorizations and archive custody retain G/J's documented review scope; A100 retains L's scope.
- No TeX build, PDF/layout certification, repository test run, installation or global historical re-audit was performed. Author-side “178 checks” is not substituted for this review and is not claimed as independently rerun.
- No author file, coordination ledger, staged state or other agent's work was edited. No staging, commit, push, GPU operation, remote connection, external send, lease action or launch occurred. Only this requested `/tmp` review artifact was written. Collaborator remains UNSENT. Main retains integration and critical-path formation ownership.

**EDITSTOP — bounded independent review complete.**
