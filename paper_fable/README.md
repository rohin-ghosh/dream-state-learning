# Experience Models — ICLR 2027 submission (finalized draft, 2026-09-10)

This directory holds the paper draft: `main.tex`, `refs.bib`, and this README.

**What the paper is.** A measurement-first report on an *experience model*: a frozen Qwen2.5-7B-Instruct base plus a per-life rank-8 LoRA that the agent rewrites every 32 episodes from its own recorded thinking (THINK / DREAM / SLEEP), with an optional PARENTING stage in which a stronger, non-learning model prescribes thinking patterns in context. Every empirical statement is a cell count or a measured mean with its noise band, taken from `research_notes/EVIDENCE_TABLES.md` (E) or a dated entry in `research_loop/COORDINATION.md` (C); where the two disagree, the later dated COORDINATION entry wins and the discrepancy is listed below. Design constants (token budgets, thresholds, prompt sizes) are read from the harness code and are labelled as such in the paper. Anything not in those sources is written as "not measured".

**Finalization pass (2026-09-10).** 72 refuted claims from the claim audit were applied. The paper now stands on the latest dated entries (SEQ-001 per-life recount, SEQ-002 life-500 trace, SEQ-003 echo null and compiler references, M5 fixed-recipe reference) wherever they supersede earlier snapshots. Words removed everywhere: "sealed", "never seen", "never gives answers", "rehearse" (now "first-NOTE overlap with the brief", with a control null), "safe" for gated writes (now "0 harmful on the selection panel, post-selection"), "delays ritual", "4/5 rank-16 cells" (now 3/5), "9/10" (now 8/10), "six consecutive probes" for life 500 (now five, no commit between), "44 pairs / 0 harmful" for the parented arm (now 48 pairs / 1 harmful), "0/3 vs 3/9" (now 1/3 vs 4/9).

## Source precedence and known discrepancies

- **R2 ungated lives.** Two counts: the 2026-09-09 ~20:30 mid-life snapshot (82 of 144 pairs; 69 positive / 9 harmful / 4 by subtraction; harm in 3 lives at or after episode 384) and the 2026-09-10 SEQ-001 life-level recount (16 pairs per life; 4/9 lives with ≥1 harmful pair, seeds 2/3/5/6; 3/9 with ≥2; 16 harmful pairs in 144). The paper reports both and stands on the recount. SEQ-001 does not record the episode of each harmful pair, so "last ungated harm at 768" is stated only for the snapshot.
- **R3 gated lives.** Four snapshots: C 2026-09-10 late per-life (8/7/7/10 pairs, means +0.036/+0.016/+0.054/+0.022, rejections 2/0/8/4, ages 448–640); the same day's status line (35 pairs, means +0.039/+0.016/+0.055/+0.022, rejections 2/0/9/4; no per-life pairs or ages); E line 26 "as of 2026-09-11" (500: 9 pairs / 5 rejections, 502: 10 rej, 503: 11 pairs); C tick 1 (17/9, 21/0, 14/11, 23/4, 7/1, 7/1); and SEQ-001 (13/11/13/14/4/5 pairs = 60, 0 harmful, 17/9, 21/1, 15/11, 24/4, 8/1, 8/3). The paper stands on SEQ-001 and lists the earlier ones in Appendix D. The E-line-26 "5 rejections at 9 pairs" for life 500 is not reconcilable with "2 at 8 pairs" one snapshot earlier (three rejections in two sleeps is impossible) and is flagged in the Appendix D caption.
- **Life 500, 0.529 → 0.464.** C tick 1 Observation 2 said the drop followed a commit whose gate probe was ≥ 0.509, with 9 rejections since at 0.27–0.34; SEQ-002 (later) traced gate.json and found NO commit between the two probes, five score rejections (0.341, 0.270, 0.334, 0.276, 0.194 vs floor 0.527–0.529), five (not six) consecutive 0.529 probes, and floor decay to 0.464. The paper follows SEQ-002. SEQ-001's interim statement that the drop "is a real change of the committed adapter" was itself retracted by SEQ-002.
- **Parented life 402.** C 2026-09-10 late: 12 pairs at ~830 episodes, min +0.003, mean +0.014, 0 harmful (giving "RP 0 harmful in 44 pairs" and "0/3"). SEQ-001: 16 pairs at 1,024, mean +0.011, min −0.039, 1 harmful, 4 restarts; "0/3 is withdrawn". The paper uses SEQ-001 (48 pairs, 1 harmful, 1/3 lives).
- **Rehearsal 0.50–1.00.** C 2026-09-10 late reported per-life first-NOTE "rehearsal" rates 0.50–0.84 / 0.97–1.00 / 0.66–1.00; SEQ-003 withdrew them (no stop-word filter, fixed tail counted, no control) and reports 0.454 after brief vs 0.322 pre-brief vs 0.354 unbriefed controls (47 briefs from lives 400/401; 8 control lives; life 402 not in the null). E line 29 still carries the stale 0.50–1.00; E line 53 (addendum) carries the withdrawal. The paper reports the echo null and states the withdrawal.
- **Rank-16 below-base count.** C 2026-09-08 ~00:15 says "r16 4/5 below base"; E line 20 and C 2026-09-10 (harsh-review entry) recount 3/5 (0.504 and 0.502 exceed 0.494). The paper uses 3/5 and 8/10. "Rank 8 kept by the tie rule" was replaced by "unresolved at n = 5" per the registered margin rule (`research_loop/changes/chg_20260908_extractable_sleep_compiler_v1/interpretation_dose.md`) and E line 20's 90% CI [+0.001, +0.083].
- **Base reference for gym numbers.** E line 7 / C 2026-09-07: 0.4936 ± 0.0113 over 9 unseeded single-stream panels at budget 24 (`organism_v6/noise_probes.py`). The lives' seeded 16-chunk OFF probe read 0.463–0.488 (C tick 1) with mean 0.471–0.474 and SD 0.0092/0.0087 from disk (SEQ-001). The paper reports both and uses the from-disk SDs (paired SD ≈ 0.013) as the noise band for life numbers; 0.494 is kept only as the reference the rank cells were counted against.
- **Absorption control at sleep 1.** C 2026-09-07 17:40 (three-sleep preliminary readout) gives 1.72 (both lives); E line 35 gives 1.6 → 1.95 for the 2026-09-08 08:20 eight-sleep run, which drew a different control sample and whose C entry states only "saturates at ~1.95 by sleep 3". Table 3 shows the 17:40 per-sleep values and the eight-sleep endpoints side by side and says so.
- **Row-specific excess.** C 2026-09-08 08:20 and E line 35 give 1.7 → 0.6 (eight-sleep run); the 17:40 sleep-1 cells subtract to about 1.5 and that entry says "≈ 1.3–1.6". The paper quotes both.
- **Committed sleeps at the first certification snapshot.** C 2026-09-08 06:30 says "46 sleeps across 6 lives"; the 06:45 entry says 45/45. The paper uses 45/45.
- **v2.1 trainer epochs.** E line 9 lists 2 epochs for classrooms; `organism_v6/classroom_round.py` passes `--epochs 3` and writes epochs=3 into the round manifest. The paper states 2 for rank cells and bootstrap adapters (C 2026-09-07 night; C tick 1) and 3 for the classroom script, flagged as unreconciled against training receipts.
- **v2.1 row construction.** The earlier draft described "(context render, canonicalized chunk) rows + 30% recall rows" as the v2.1 corpus for all three uses. That is `compile_native` (`sleep_compile.py`, `recall_mix=0.3`), called by the nursery scripts and, per C 2026-09-07 ~22:30 (line 338), used for the rank-calibration corpus format; the classroom builds its own rows (`classroom_round.py`) and the bootstrap uses author renderings. The paper now describes the three corpora separately and omits the 30% figure; whether the recall mix applied to the pooled rank-cell rows is not reconciled.
- **Round-0 harmful writes.** C 2026-09-08 10:00 gives 0/6 parented vs 4/6 self-taught for six lineages; the paper reports counts computed from the full 17-lineage per-write table (2/9 parented, 5/8 self-taught) and gives the six-lineage interim in Appendix E. Parented round-2 harmful count corrected from 4/9 to 5/9 (2+1+5 = 8 matches the arm total of 8 < −0.03).
- **Below-PREV commits.** C 2026-09-08 ~15:00 counts 5, all parented; the seed-8000 exam table (C 2026-09-08 ~03:40, line 389) shows a self-taught round-2 commit at ON 0.317 vs PREV 0.375 that was never tallied. The paper reports five counted (parented) plus one uncounted (self), as a lower bound.
- **Ritual window 224 of life 401.** C 2026-09-09 15:30 (per-sleep detector) records window 224 as ritual (same_recipe + flat_predictions); C 2026-09-10 14:00 (whole-life tally) counts 224–320 clear. The paper reports both and does not resolve it.
- **Old-writer seed 0 full life.** The analysis JSON behind SEQ-001 (`research_notes/analysis/analysis_tables_2026-09-10_a40.json`) lists R_B_seed0 at 16/16 positive pairs; the SEQ-001 text mentions only the collapsed old-writer life (−0.219, 7 harmful). The paper states the 7/8 through episode 512 (C 2026-09-07) and says no later tally is in the evidence sources; the JSON value is noted here only.
- **Bootstrap adapters.** C tick 1 says v3/v2/v1 adapters were trained (v3 final loss 0.675); Codex's STOP (C lines 857–882) classifies v3 as DEV_UNVERIFIED_PROVENANCE; E line 41 still says "training queued". The paper says trained, unmeasured, quarantined.
- **Numbers deliberately excluded** because their only source is outside the permitted set (`research_notes/certification_report_draft.md`, `research_notes/IDEAS.md`): per-sleep absorption values beyond those in COORDINATION (e.g. 3.30, 3.11, 2.88, 2.41, 2.54; excess 1.64, 1.72, …; base NLL 4.34 → 3.17 / 4.36 → 3.32), the decorated-marker counts 24/74, 25/88, 17/87, and the per-life corpus-density values (127 → 30; 314 → 791; …).

## How to compile

No TeX installation (pdflatex, tectonic, latexmk, xelatex, lualatex) was available on the machine where this draft was finalized, so the file was not compiled to PDF. The preamble uses `\IfFileExists{iclr2027_conference.sty}{...}{...}` and `\IfFileExists{iclr2027_conference.bst}{...}{plainnat}` fallbacks so it compiles under `article` defaults when the ICLR kit is absent. A structural check (`python3` script: brace balance, `\begin`/`\end` pairing, `\ref`→`\label` resolution, `\cite`→`refs.bib` resolution, tabular column counts, unescaped `_`) passed with zero errors; the only unresolved citations are the `TODO-*` keys listed below.

1. Obtain the ICLR 2027 author kit and place `iclr2027_conference.sty`, `iclr2027_conference.bst` and `math_commands.tex` next to `main.tex`. Do **not** add `\iclrfinalcopy`; the submission is double-blind.
2. Fill in the `TODO-<topic>` bibliography entries: `TODO-looped-transformers`, `TODO-chain-of-thought`, `TODO-compilergym` (Cummins et al. 2022/2023), `TODO-leafe`, `TODO-early-experience`, `TODO-evaf`, `TODO-memopilot`, `TODO-spark`, `TODO-cl-bench`, `TODO-self-training` (STaR; ReST / ReST-EM; expert iteration), `TODO-model-collapse` (Shumailov et al.; Alemohammad et al.). Or remove the corresponding `\citep{TODO-...}` calls.
3. Compile: `pdflatex main; bibtex main; pdflatex main; pdflatex main`.
4. Figures 1–4 are text placeholders with their captions; replace them with schematics before submission.

**Length.** The main text (Introduction through Related Work, excluding the two statements) grew during finalization because every gated and parented number now carries its post-selection / snapshot qualifiers: a crude token count gives about 12,800 tokens (roughly 10,000–11,000 words once numbers and inline math are discounted) plus four tables and four figure placeholders, i.e. roughly 14–15 pages at ICLR geometry against a 9-page limit. It must be cut before submission; the natural move is to push the earlier-snapshot sentences, the per-life recount details and the gate-log narrative into Appendices B and D, which already hold them. Trim, in this order, once it compiles: the earlier-snapshot sentences in "Gated lives (R3)" (keep the SEQ-001 recount); the earlier-snapshot sentences in "Ungated lives (R2)"; the "Noise at the tolerance; parent size" paragraph; the per-program clause in "recipe lock-in"; the "Sleep consolidation" paragraph of Related Work; figure placeholder captions once real figures exist.

## Number → source table

Abbreviations: **E** = `research_notes/EVIDENCE_TABLES.md` (line numbers as of 2026-09-10); **C** = `research_loop/COORDINATION.md` (dated entry header; approximate line numbers); **code** = `organism_v6/…` (design constants, not measurements); **derived** = arithmetic on cells listed in the same table; **RH** = `research_notes/REVIEW_HARSH_2026-09-10.md` (binding review, used only where it supplies arithmetic on sourced cells).

### Setup constants and Methods (Sections 1–3)

| Number | Where it appears | Source | Dated entry / location | Notes |
|---|---|---|---|---|
| Qwen2.5-7B-Instruct child; rank 8; sleep every 32 episodes; probe every 64; 8 probe programs; 1,024-episode life | Abstract; §1; §2; §3 | E | E:6; rank confirmed by receipts in C [Codex] 2026-09-08 18:49 | Rank 8 is a launch argument, not a trainer default (code defaults to 16) |
| 0.487 = programs shrink 48.7% | §1 | E | E:7 | definition of the gym score |
| 400 tokens per chunk; temperature 0.7 | §1, §2.1 | code | `model_backend.py:24-25`, `batch_loop.py:119` | design constants; not in E or C |
| RECALL returns 6 rows | §2.1, Fig. 1 | code | `ledger.py:35`, `batch_loop.py:83` | design constant |
| 22,000-char context; 4 open surprises; 10 pinned NOTEs; 14 TAIL entries; 1,200-char truncation | §2.2, Fig. 1 | code | `state.py:40-42, 56, 67, 80, 85, 92` | design constants |
| waking brief "max 8 lines"; 2,000-char enforced cap | §2.2, App. A | code | `sleep_compile.py:74-77, 142` | brief lengths not measured |
| 12 largest surprises, 8 used as anchors; 400-char thought quotes; up to 6 PRINCIPLE lines citing ≥2 programs; dedup on first 160 chars | §2.3 (v1) | code | `sleep_compile.py:33, 58-59, 64-69, 96, 98, 111, 140, 150, 164-165` | design constants; hashes match the 2026-09-08 receipts |
| v1 trainer: lr 1e-4, 3 epochs, seq 512, α=2r, dropout 0.05, 7 projections, no seed | §2.3 | E + code | E:9; `train_adapter.py:16-22, 41-44, 54-57`; C [Codex] 2026-09-08 18:49 receipts | E:20 "v1 trainer still unseeded" |
| base emits decorated markers in ~30% of chunks | §2.3, App. B | C | C 2026-09-07 Fable (lines 35–42) | no chunk count or band in E/C (counts exist only in IDEAS.md, excluded) |
| one old-writer seed locked decorated dialect, stopped early | §2.3, App. B, App. G | C | C 2026-09-07 (lines 68–71: "KILLED at 88/128") | n = 1 |
| v2.1 trainer: lr 3e-5, response-only chat-masked loss, rank 8 (16 in rank cells), seed flag added 2026-09-07, max length 2,048 | §2.3 | E + code | E:9, E:20; `train_adapter_v21.py:28-35, 72, 74-91` | 2,048 is code-only |
| v2.1 epochs: 2 (rank cells, bootstrap) vs 3 (classroom script) | §2.3 | C + code | C 2026-09-07 night (line 142); C tick 1 (line 890); `classroom_round.py:310, 317-318` | unreconciled; see discrepancies |
| 12,031 unique pooled rows | §2.3, §3, §4.1, Table 1 | E, C | E:19; C 2026-09-07 ~22:30; C 2026-09-08 ~00:15 | |
| receipt audit: all long lives used v1 | §2.3 | C | C [Codex] 2026-09-08 18:49 (lines 568–590) | |
| parents Qwen2.5-14B-Instruct / 32B-Instruct-AWQ; weights never learn | §2.4 | E, C | E:10; C lines 213, 472, 511 | |
| scout leak scan: 3/32 blocked, 5/32 delivered with rule-descriptor words | §2.4, App. A | E, C | E:10; C 2026-09-07 ~19:10 (line 284), seed 7003 | one round of 32 utterances |
| 8 classrooms × 4 lessons (32 utterances) per round; 2 short episodes per lesson | §2.4, App. A | C | C 2026-09-07 ~20:40 (line 295); lines 214, 222 | |
| parent reads 4 sampled chunks, writes ≤ 8 lines | §2.4 | C | C [Fable] 2026-09-08 ~16:00 (line 475) | |
| rule game: 3 integers, 10 rules, 6-item quiz, quiz triples 0–9, admission post ≥ pre | §2.4, App. B | E + code | E:8 ("3 numbers"); `rulegame.py` RULES, `quiz_triples k=6`; `classroom_round.py:244` | rule count, quiz size, operator are code constants |
| 400-row target; 306/400 scout fill; 400/400 lineage fill | §2.4, App. B, App. F | C | C 2026-09-07 later (lines 100–101); C 2026-09-07 ~16:30 (line 225); C 2026-09-08 ~03:40 (line 393) | shortfall reported, never padded |
| 4 dialect-anchor rows | §2.4, App. B | code | `write_swarm.py:24-40` (ANCHORS); `classroom_round.py:268, 298` | |
| lineage = 3 PREV-chained rounds | §2.4, §4.4 | E, C | E:37; C 2026-09-07 launch (line 359) | |
| training pool: 15 cbench + 12 chstone + 40 mibench = 67 programs, replayed 15–16× | §3 | C + code | C 2026-09-09 ~00:30 (line 489: "~67"); `run_life.py:49-59`; `research_loop/advisory/20260906_..._independent_audit_v1.md` | dataset breakdown from code |
| same-source siblings of 4–6 probes; sibling list | §3 | E, C | E:6; C 2026-09-10 M5 entry (lines 912–913); RH F2 | |
| 51 probe-program rows in the 12k corpus | §3, §4.1, Table 1 | E | E:20 | |
| `_canon` / `benchmark://` prefix leak in a pilot | §3, App. G | code + RH | `run_life.py:43-46` docstring; RH lines 137, 150 | not in E/C; kept as design history |
| probe: 16 chunks, seed 777, per-(program, chunk) seeds, birth-prompt-only context | §3 | E + code | E:6 ("seeded 777"); `run_life_v2.py:24, 76-77, 293-303`; `batch_loop.py:107-118` | 16 is a code default |
| 0.4936 ± 0.0113 over 9 unseeded panels, budget 24 | §3 | E, C | E:7, E:20; C 2026-09-07 (line 337) | `noise_probes.py` default `--budget-ticks 24` |
| life OFF probe 0.463–0.488 | §3, §4.2, §4.3 | C | C tick 1 (line 894) | |
| OFF mean 0.471–0.474; SD 0.0092 / 0.0087 (n = 157 / 153); paired SD ≈ 0.013 | §1, §3 | E, C | E:48; C SEQ-001 "Noise (M3), from disk" | |
| same-adapter replicate SD 0.0064 / 0.0067 (n = 33 / 37); "0.0065 over 70 pairs" | §1, §3, §4.2, App. B | C | C SEQ-001; C SEQ-002 | |
| replicate swings 0.019–0.045 | §3 | E, C | E:25; C tick 1 (line 896) | |
| one replicate pair differing by 0.065 | §3, §4.2 | C | C SEQ-002 | |
| harmful < −0.03; gate tolerance 0.02 | §1, §3, App. B | E, C | E:23, E:25; C 2026-09-09 ~20:30 (lines 528, 537) | |
| 2.7 / 1.8 single-panel SD; 2.3 / 1.5 paired SD; 3 replicate SD | §3, App. B | derived | 0.03/0.0113, 0.02/0.0113, 0.03/0.013, 0.02/0.013, 0.02/0.0065 | arithmetic |
| replicate gaps 0.059 (1,200 rows) and 0.078 (12,031 rows); two panels differing by 0.147 | §3, §5, App. G | C, E | C 2026-09-07 (lines 195, 341); C 2026-09-07 ~19:10 (line 275); C 2026-09-07 ~22:30 (line 343); E:20 | |
| rank-cell probes unseeded until 2026-09-10 | §3, Table 1 | code + RH | `probe_adapter.py:28-30, 47`; RH M10 | |
| gate: same 8 programs and seed as the reported probe; disjoint panel of 12 programs pending | §3, §4.2, App. B | E, C | E:6, E:25, E:52; C 2026-09-10 M5 entry ("Disjoint panel v1") | |
| gate cost ≈ 6 minutes | §3, App. B, App. G | C | C 2026-09-10 ~00:30 (line 544) | one logged timing |
| gate not ratified | §3 | C | C line 544 ("Awaiting your ratification"); no later ratifying entry | |
| ritual flags 0.7 / SD < 0.05 with ≥ 8 / Jaccard ≥ 0.5 / 0.7 with ≥ 8; ≥ 2 flags; 32-instance window | §3, App. C | C + code | C [Fable] 2026-09-08 ~16:00 (line 475); `parent_brief.py:98-107`; `run_life_v2.py:245-246` | |
| cutoffs written 2026-09-08 / 09-09 when parented lives ≤ 48 episodes | §3, Table 4 | C | C lines 475, 485, 489, 505 | |
| templated-notes rule changed 2026-09-10 (parented arm only) at 830–1,024 episodes | §3, App. C, Table 4 | C | C 2026-09-10 late (line 656) | RH M6 |
| first-NOTE overlap ≥ 4 words of ≥ 3 letters; ~24-word "repeat after me" tail | §3, App. C | code | `parent_brief.py:116-119, 137, 201-208, 237` | |
| detector grouping bug (424-episode life looked like 67) fixed before any brief | §3, App. C | C | C 2026-09-09 ~00:30 (line 489) | |
| absorption: 24 rows per sleep (default); control from another same-design life | §3, §4.3, Table 3 | code + C | `absorption_probe.py:51, 102`; C 2026-09-07 ~17:40 (line 242: control = R_B_seed0) | row count used in the logged runs not recorded |
| absorption probe uses chat template; v1 trained bare text; rescoring queued | §3, §4.3 | code + C | `absorption_probe.py:39-41, 71-74`; `train_adapter.py`; C 2026-09-10 harsh-review entry (M10 queued) | |
| exam SD 0.067 (0.398) and 0.072 (0.445) at 8 eps, 8 reps each; 0.030 (0.416) and 0.044 (0.412) at 40, 8 reps each; 0.033 (0.410) at 80, 6 reps | §1, §3, App. E | E, C | E:8; C 2026-09-07 ~16:30 (line 220), ~17:40 (line 233), ~19:10 (line 268); C 2026-09-08 ~15:00 (line 470) | population SDs (`rulegame_noise.py` pstdev) |
| sample SDs 0.072, 0.077, 0.032, 0.047, 0.036 | §3 | derived | recomputed from the logged reps (RH / claim audit C06) | |
| √2 × single-exam SD = 0.042–0.062; tolerance ≈ 0.5–0.7 SD | §3 | derived | RH M11 | arithmetic |
| classroom harm tolerance 0.03; 40-episode exams; 6 smoke + 8 scout decisions at 8 episodes excluded | §3, App. E | C + code | `classroom_round.py:46`; C lines 103, 268, 414, 470; C 2026-09-07 ~15:20 (lines 198–207), ~16:30 (220), 247 | |
| PREV recorded, not compared | §3, §4.4, App. B | C + code | C 2026-09-08 ~15:00 (line 468); `classroom_round.py:354-360` | |

### Results 4.1 (writer)

| Number | Where it appears | Source | Dated entry / location | Notes |
|---|---|---|---|---|
| 130-row screen: plain 0.466 (spread 0.058), +paraphrase 0.496, +replay-mix 0.494, +both 0.489 (spread 0.002); base 0.485–0.494 | §4.1 | E, C | E:12; C 2026-09-07 (lines 76–79) | offline screen, third trainer setting |
| screen: 3 epochs, lr 5e-5, 2 panels, ~3× rows (paraphrase), ~26 anchor rows (mix) | §4.1 | C + code | C [Codex] 2026-09-08 18:56 (lines 594–601); `write_swarm.py` (`--epochs 3 --lr 5e-5`, `--reps 2`, `n = max(4, len//5)`) | |
| Table 1 cells: 300 rows r8 0.485 (0.477/0.492), r16 0.488 (0.491/0.485); 1,200 rows r8 0.492, 0.506, r16 0.456, 0.515; 12,031 rows r8 0.413, 0.440, 0.468, 0.491, 0.343; r16 0.473, 0.504, 0.453, 0.502, 0.434 | Table 1, §4.1 | E, C | E:17–19; C 2026-09-07 night (line 144); C 2026-09-07 ~15:20 (lines 193–194); C 2026-09-08 ~00:15 (line 365) | |
| r8 mean 0.431 SD 0.057; r16 mean 0.473 SD 0.030 | §4.1, §5 | derived | sample SD recomputed from the five cells (E:19 gives the means) | |
| r16 − r8 at 1,200 rows: −0.036, +0.009 | §4.1 | derived | from Table 1 cells (C lines 193–194) | |
| below 0.494: r8 5/5, r16 3/5, total 8/10 | §1, §4.1, Table 1 | E, C | E:20; C 2026-09-10 harsh-review entry ("r16 recount (3/5)") | supersedes C 2026-09-08 "4/5" |
| 7/10 below a 0.485 base | §4.1 | RH | RH F5 | |
| paired r16 − r8: +0.060, +0.064, −0.015, +0.011, +0.091; 4/5; mean +0.042; SD 0.043; 90% CI [+0.001, +0.083] | §4.1, Table 1 | E, C | C 2026-09-08 ~00:15 (line 365); E:20 | |
| margin 0.03 equivalence rule | §4.1 | protocol | `research_loop/changes/chg_20260908_extractable_sleep_compiler_v1/interpretation_dose.md:110-119` | |
| two of five pairs trained before the seed flag | §4.1 | C | C 2026-09-07 (lines 192–196) | |
| dose-splitting cell dropped as degenerate | §4.1 | C, E | C 2026-09-10 late (line 658); E:20 "Frequency is not isolated" | |

### Results 4.2 (safety)

| Number | Where it appears | Source | Dated entry / location | Notes |
|---|---|---|---|---|
| canary rejections per R2 life (16, 10, 2, 2, 1, 0 …) and commits | §4.2, App. D Table | C | C SEQ-001 per-life table | |
| 82 of 144 pairs; 69 positive; 9 harmful; 4 between (by subtraction) | Abstract (earlier draft), §1, §4.2, Table 2, App. D | E, C | E:22–23; C [Fable] 2026-09-09 ~20:30 (lines 527–528) | 4 = 82 − 69 − 9 |
| harmful pairs: seed5 −0.038, −0.186, −0.118, −0.039 at 384–576; seed6 −0.089, −0.045 at 448/576, ~0 by 704–1,024; seed2 −0.039, −0.030, −0.051 at 640–768 | §4.2, App. D | C | C line 528 | first harmful pair AT 384 |
| 0 harmful through episode 320 in 9/9 | §1, §4.2, Table 2 | C, E | C line 529; E:23 | |
| six lives positive at every pair at the snapshot, mid-life +0.03 to +0.065 | §4.2, App. D | C | C line 528 | censored at the snapshot |
| seeds 7 and 8 at 168 / 112 episodes on 2026-09-09 | §4.2, App. D | C | C 2026-09-09 ~00:30 (line 501) | |
| seeds 2, 5, 6 reached 1,024 by 2026-09-10 ~14:00 | §4.2 | C | C line 556 | |
| SEQ-001 recount: 4/9 lives ≥ 1 harmful (seeds 2, 3, 5, 6); 3/9 ≥ 2; 16 harmful pairs; life means +0.037, +0.050, −0.000, +0.045, +0.022, −0.051, −0.005, +0.050, +0.028; mins (−0.242 seed5, −0.057 seed3, −0.051 seed2, −0.089 seed6); 7/9 ≥ +0.02; 2/9 negative | Abstract, §1, §4.2, Table 2, App. D | E, C | E:47; C SEQ-001 per-life table and "Recount at the life level" | 16 = 5 + 1 + 8 + 2 |
| 21/21 positive; mean +0.022; 6/21 ≥ +0.03; 45/45 committed sleeps; canary means ≥ 0.97 | §4.2, §4.3 | C | C [Fable] 2026-09-08 ~06:45 (line 432) | "6/21 > +0.03" in C; one value is exactly +0.030 at display precision |
| seed5 sleep 448: 1.0–1.8 chunks/episode vs 13; parseable-ACT 1.00; canary 1.00 | §4.2, App. B | E, C | E:23; C line 532 | n = 1 adapter inspected |
| seed2 sleep-608 adapter canary 0.67 (threshold 0.5); later candidates 0.08, 0.17, 0.00; 16 commits / 10 rejections at the recount; 16/16 over the full life | §4.2, App. D | C + code | C line 533; `run_life_v2.py:26` (0.5); C SEQ-001 (16 / canary 16) | |
| seed0 canary min 0.58 mean 0.88; seed4 min 0.58 mean 0.84; canary = ≤ 12 chunks (4 programs × 3) | §4.2, App. D | C + code | C line 534; `run_life_v2.py:26-49` | no band |
| gate log life 500: 0.4873 / 0.4847 / 11.1 vs 11.6 (sleep 32); 0.4878 / 0.4847 / 2.1 vs 11.6 REJECTED_BREVITY (64); 0.4903 / 0.5065 / 7.0 vs 11.1 (96); 0.5069 / 0.5065 / 12.2 vs 11.1 (128); 0.4878 / 0.4878 / 16.0 vs 13.0 (160); next pairs +0.042 (ep 64), +0.021 (ep 128) | §4.2, App. B | C | C [Fable] 2026-09-10 ~14:00 (lines 548–556) | post-selection |
| brevity catches: life 505 @288 0.520 vs 0.519, 1.75 vs 9.6; life 501 @704 0.488 = floor, 4.4 vs 11.4 | §4.2, App. B | C | C tick 2 (line 899) | |
| R3 dated snapshot: 8/7/7/10 pairs; +0.036/+0.016/+0.054/+0.022; rej 2/0/8/4; ages 448–640 | §4.2, App. D Table | C | C 2026-09-10 late (line 653) | |
| R3 status line: 35 pairs; +0.039/+0.016/+0.055/+0.022; rej 2/0/9/4 | §4.2, App. D | C | C [Fable → Codex] 2026-09-10 late (line 783) | no per-life pairs or ages |
| R3 intermediate commits/rejections 17/9, 21/0, 14/11, 23/4, 7/1, 7/1 | App. D Table | C | C tick 1 (line 892) | superseded |
| E snapshot: 500 9 pairs / 5 rej incl. 0.270 vs floor 0.527; 502 10 rej; 503 11 pairs | App. D caption | E | E:26 | flagged as unreconciled |
| SEQ-001 R3: pairs 13/11/13/14/4/5 (60); means +0.042/+0.016/+0.056/+0.021/+0.037/+0.028; mins −0.000/+0.001/+0.037/+0.003/+0.025/+0.015; exposures 864/736/840/920/288/368; commits/rejections 17/9 (score 8, brevity 1), 21/1, 15/11 (brevity 10, score 1), 24/4 (brevity 3, score 1), 8/1, 8/3 | Abstract, §1, §4.2, Table 2, App. D | E, C | E:47; C SEQ-001 per-life table | post-selection |
| most-rejected life 502 has the highest mean | §4.2 | C | C line 653; C SEQ-001 | observation, n = 6 |
| 4 of 6 gated lives past 384; 3 past 768 | §4.2 | derived | from SEQ-001 exposures | |
| 0.4903 replaced 0.5065; that adapter read 0.4873 at its gate probe; gap ≈ 1.4 single-panel SD | §4.2, App. B | C + derived | C lines 551–556; 0.016/0.0113 | |
| life 500: 0.529 (0.5291) at five probes 448–704; 0.464 (0.4638) at 768; no commit between; sleeps 672–800 REJECTED_SCORE at 0.341, 0.270, 0.334, 0.276, 0.194 vs floor 0.527–0.529; canary 1.00; 6.6–10 chunks/ep; floor decayed to 0.464; a 0.444 candidate could now commit; totals 17 commits, 8 score + 1 brevity rejections at 864 | §4.2, App. B | C | C SEQ-002; C SEQ-001 (life 500 row) | supersedes C tick 1 Observation 2 |
| confirm-at-next-probe rule and best-confirmed-probe floor proposed, not built | §4.2, §5, App. B | C | C tick 1; C SEQ-002 ("reinstated as the proposal") | |
| recovery path after repeated rejections proposed, not built | §4.2, App. B | C + RH | C line 540; RH line 24 | |

### Results 4.3 (storage; recipe lock-in)

| Number | Where it appears | Source | Dated entry / location | Notes |
|---|---|---|---|---|
| lives A/B = R2 seeds 0/1; 8 sleeps; episodes 32–256 | §4.3, Table 3 | C | C 2026-09-08 ~08:20 (line 438: "Seeds 0/1, 8 sleeps each") | |
| own rows 3.25, 3.55 (A); 3.29, 3.13, 2.99 (B) | §4.3, Table 3 | C | C 2026-09-07 ~17:40 (lines 243–244) | per-sleep, three-sleep readout |
| control 1.72 / 1.72; 1.95 / 1.94; — / 2.08 | §4.3, Table 3 | C | C lines 243–244 | |
| retention 3.26 (A, adapter 2); 3.28, 3.30 (B, adapters 2, 3); 3.16 (B sleep-2 rows, adapter 3) | §4.3, Table 3 | C | C lines 243–244 | no band |
| 3.3 → 2.5 own rows; control ~1.95 plateau by sleep 3; excess 1.7 → 0.6; base NLL 4.3 → 3.2; retention flat | §1, §4.3, Table 3 | C, E | C 2026-09-08 ~08:20 (line 438); E:35 | eight-sleep run, pooled over 2 lives |
| control 1.6 at sleep 1 (eight-sleep run) | §4.3, Table 3 | E | E:35 | not in C text; see discrepancies |
| excess ≈ 1.5 by subtraction at sleep 1 | §4.3, Table 3 | derived | 3.25 − 1.72; 3.29 − 1.72; C line 245 says "≈ 1.3–1.6" | |
| 1 nat ≈ 2.7×; 3 nats ≈ 20× per token | §4.3, §5 | derived | e^1, e^3 | |
| paired pairs A: +0.019, +0.013, +0.011, +0.015; B: +0.003, +0.007, +0.050, +0.048 (ep 64–256); mean +0.021 over 8 | §4.3, App. D | C | C 2026-09-08 ~06:30 (line 429); ON/OFF values C 2026-09-07 ~22:30 (line 353), 2026-09-08 ~05:00 (line 410) | mean is arithmetic on the 8 pairs |
| +0.022 over 21 pairs | §1, §4.3 | C | C line 432 | |
| adapter-ON plateaus 0.4878 (R3 501, 503 six consecutive; R4 600/602/603 most probes) and 0.5291 (R3 500, 502 five to six) | §1, §4.3 | C, E | C tick 1 Observation 1 (line 894); E:54 | |
| birth recipe alone = 0.4878 (per program 0.538, 0.537, 0.389, 0.521, 0.508, 0.471, 0.439, 0.499); 0.5291 = six-pass routine | Abstract, §1, §4.3, App. A | C, E | C 2026-09-10 M5 entry (lines 911–912); E:50, E:54 | |
| -Oz 0.522; -O3 0.341; best adapter edges -Oz by 0.007, common one 0.034 below | §1, §4.3, §5 | C, E | C SEQ-003 "Compiler references"; E:54 | |
| M12 ritual in weights: ON modal share 0.90 / 0.86, fully locked 68% / 52%, note Jaccard 0.62 / 0.59; OFF 0.50, 0%, 0.105 | §4.3, §4.4 | C, E | C SEQ-001 "Ritual lives in the weights (M12)"; E:51 | |
| per-program ON−OFF: patricia +0.113 / +0.158, gsm +0.029 / +0.037, dijkstra ~0 / +0.023; other five −0.03 to 0 | §4.3 | C, E | C SEQ-001 "Per-program ON−OFF"; E:49 | |

### Results 4.4 (parenting) and 4.5 (bootstrap)

| Number | Where it appears | Source | Dated entry / location | Notes |
|---|---|---|---|---|
| ritual table, unparented: seed0 424 / 192 / 7/8; seed1 424 / 224 / 5/7; seed2 552 / 192 / 10/12; seed3 368 / none; seed4 424 / 160 / 7/9; seed5 320 / 160 / 6/6; seed6 320 / 160 / 5/6; old-writer 864 / 160 / 24/24 from 256; old-writer 344 / 224 / 4/4 | §4.4, Table 4 | C, E | C 2026-09-09 ~00:30 (lines 491–504); E:32 | ages at measurement; 24/24 from 256 carried as logged |
| onset 160–224 in 8/9 measured lives; 71–100% persistence (5/7 to 24/24) | §1, §4.4 | C + derived | C lines 491–504; percentages from the per-life cells | E:32 says "~80–100%" |
| same-recipe flag from window 1 in every unparented life scored | §4.4, App. A | C | C line 504 | |
| seed3 +0.065 mid-life; full life +0.045, min −0.057, 1 harmful; seeds 1 and 7 +0.050 | §4.4 | C, E | C lines 528, 565; E:32; C SEQ-001 | |
| seed1 +0.050 (ep 192), +0.048 (ep 256), flagged from 224; 16/16 pairs positive over full life | §4.4, App. D | C | C lines 353, 410, 495; C SEQ-001 (min +0.003) | |
| parented first flagged window 288 (400), 192 (401), 256 (402) | §1, §4.4, Table 4 | C, E | C 2026-09-10 ~14:00 (lines 558–565); E:32 | 401 inside the control range |
| 401 window 224: R by per-sleep detector vs clear in whole-life tally | §4.4, App. A, App. D | C | C 2026-09-09 ~15:30 (lines 520–521) vs C 2026-09-10 ~14:00 (line 562) | unresolved |
| parented persistence 3/3, 7/11 (R from 352), 3/4 (clear 288, R from 320); 3–9 briefs by then | §4.4, Table 4, App. A | C, E | C lines 562–565; E:32 | mid-life snapshot (~ep 384 / 544 / 384, derived from window counts) |
| brief generated only after a flagged sleep; shown only once one exists (v1/v2) | §4.4, §5, App. A | code + C | `parent_brief.py:214`; `run_life_v2.py:132-141, 243-246`; C line 523 (400/402 unflagged through 192) | |
| 16 and 14 v3 briefs in lives 401 / 402 (4 and 6 blocked) | §4.4, Table 4, App. A | C, E | C 2026-09-10 late (line 656); E:10 | |
| 47 briefs from lives 400/401 | §4.4, Table 4, App. D | C, E | C SEQ-003; E:53 | |
| life 401 sleep 192: 1.00 / 0.059 / 0.564 / 0.565; window 224: 1.00 / 0.047 / 0.362 / 0.281 | §4.4, App. A, App. D | C | C 2026-09-09 ~10:30 (line 509); ~15:30 (lines 518–523) | n = 1 window |
| echo null: 0.454 after brief / 0.322 pre-brief / 0.354 controls; best control 0.666; per-brief 0.0–1.0; 8 control lives; +0.10 / +0.13 | Abstract (earlier), §1, §4.4, §5, App. D | C, E | C SEQ-003; E:53 | life 402 not in the null |
| rehearsal 0.50–0.84 / 0.97–1.00 / 0.66–1.00 (withdrawn) | §4.4, App. D caption | C, E | C 2026-09-10 late (line 655); withdrawn in C SEQ-003 and E:53 | reported only as withdrawn |
| RP 400: 16 pairs, +0.038, min +0.006, max +0.063, 0 harmful, 3 restarts; RP 401: 16, +0.016, −0.005, +0.025, 0, 3 restarts; RP 402: 16, +0.011, −0.039, +0.025, 1 harmful, 4 restarts; 48 pairs, 1 harmful | §1, §4.4, Table 2, App. D | C, E | C SEQ-001; C 2026-09-10 late (lines 648–650) for maxima; E:47 | 402 max at 16 pairs is in the analysis JSON only |
| RP 402 earlier snapshot: 12 pairs, ~830 ep, min +0.003, max +0.025, mean +0.014; "0 harmful in 44 pairs" | §4.4, App. D caption | C, E | C line 650; C line 783; E:29 | superseded |
| interim RP pairs: 400 +0.046 / +0.037 (256/320); 401 +0.001 to +0.025 through 448; 402 +0.008 / +0.017 (256/320); no separation from controls at matched ages | §4.4, App. D | C | C 2026-09-10 ~14:00 (line 566) | |
| control range of life means −0.051 to +0.050 | §4.4 | C | C SEQ-001 | |
| 17 lineages; 14B 9 lineages / 27 writes: 8 > +0.03, 8 < −0.03, means ≥ 0 in 4/9; self 8 / 24: 4, 11, 3/8 | Abstract, §1, §4.4, App. E | E, C | E:38; C 2026-09-08 ~15:00 (lines 462–468) | |
| lineage means +0.101 (s8004 B), −0.118 / −0.108 (s8005 B / A) | §4.4, App. E | C | C 2026-09-08 ~12:30 (line 454), ~15:00 (line 460) | |
| App. E per-write table (all 51 values) | App. E | C | C 2026-09-08 ~03:40 (lines 380–398), ~05:00 (403–410), ~06:30 (426), ~08:00 (435), ~10:00 (442–454), ~12:30 (454), ~15:00 (460–468) | |
| single-round cells 14B −0.012, −0.058, +0.058, −0.167; self −0.138, −0.042, −0.050, −0.021; 1/8 positive; post−pre positive 5/8; 2/8 canary, 4/8 harm rejections | §4.4, App. E | C, E | C 2026-09-07 ~22:30 (line 357); E:38 | |
| 5/8 below −0.03, 2/8 in band; pooled round-0 6/25 above, 12/25 below | §4.4 | derived | from the single-round values and the App. E round-0 column | |
| best parented round-0 writes +0.167, +0.121, +0.100, +0.100 | §4.4, App. E | E, C | E:38; C line 468 | |
| top four of 51 writes: +0.167, +0.150 (parented r2), +0.129 (self r0), +0.121 | §4.4 | derived | App. E table; C line 454 | |
| round-0 harmful 2/9 parented, 5/8 self; by round 14B 2/9, 1/9, 5/9; self 5/8, 2/8, 4/8; six-lineage interim 0/6, 0/6, 3/6 and 4/6, 2/6, 3/6 | §4.4, App. E | derived + C | counted from the App. E table; interim C 2026-09-08 ~10:00 (line 450) | 5/9 corrects the earlier 4/9 |
| collapses ON 0.071 (s8000 B r2) and ON 0.100 (s8005 A r2), HARM-rejected | §4.4, App. E | C, E | C lines 386, 460; E:38 | |
| five below-PREV commits: s8000 B r1 0.104 below 0.442; s8001 B r2 0.108 below 0.450; s8000 A r1, r2; s8003 B r1 0.096 below 0.463 | §4.4, App. E | C | C lines 385/392, 403, 426, 442, 468 | |
| uncounted sixth: self s8000 B r2 ON 0.317 vs PREV 0.375 | §4.4, App. E | C | C 2026-09-08 ~03:40 exam table (line 389) | |
| s8002 B r1 −0.029 with PREV 0.367 | §4.4 | C | C line 435 | |
| replicate lineage: −0.025 (ON 0.396 / OFF 0.421) vs −0.075 (0.375 / 0.450); later −0.013, +0.008 vs −0.096, −0.067 | §4.4, App. E | C | C 2026-09-08 ~05:00 (line 406) | only round 0 is a same-config pair |
| +0.167 = ON 0.508 / OFF 0.342; band mean ≈ 0.41 | §4.4 | C, E | C 2026-09-08 ~03:40; E:8 (means 0.412–0.416 at 40 eps) | |
| parent-size cell: 32B −0.087 rej, −0.029, −0.054 rej (21/96 fallback); 14B +0.013, −0.167 rej, +0.075 (PREV 0.375; 6/96); self 0.000, −0.117 rej, −0.100 rej | §4.4, App. E | C, E | C 2026-09-08 ~21:45; E:10 (21/96) | n = 1; exam size not recorded in the entry |
| collapse detail s8000 B r2: OFF 0.383, PREV 0.287; parseable-ACT 0.86 / 0.91; DONE-first 0/40; 5.2 vs 6.3 chunks; 431 vs 728 TRY; 694 vs 870 chars; corpus 400/400 = 256 / 118 / 22 / 4 | App. E | C | C 2026-09-08 ~03:40 (lines 380–398, esp. 393) | "DONE-first" is a ledger count not in code; gloss is the auditor's reading |
| s8000 B playbook overflow: ~50k chars (200 rows); round-1 rewrite skipped | App. A, App. E | C | C 2026-09-08 ~01:30 (line 370) | |
| leak blocks per lineage: s8000 B 12; s8001 B 6; s8000 A 4; s8001 A 10; s8002 B 7 (of 96) | App. E | C | C lines 395, 403, 427, 435 | not recorded for the other four |
| bootstrap v3 470 rows (206 / 94 / 70 / 65 / 35); recipe share 0.26; Jaccard 0.11; v2 370 (152 / 80 / 61 / 52 / 25); v1 552 (200 / 199 / 153); drops 47 (v1), 7–10 (v2/v3) | §4.5, App. F | C, E | C [Fable] 2026-09-11 ~04:00 (lines 851–854); E:41 | 0.26 computed over the 35 full rows only |
| mixture 0.4 / 0.15 / 0.2 / 0.15 / 0.1 | App. F | C + code | C line 792; `bootstrap_corpus.py:143-151` | |
| enforced filter (ACT subset; no ACT in non-full) | §4.5, App. F | code | `bootstrap_corpus.py:128-130` | weaker than the author instruction |
| v3 final training loss 0.675; adapters trained; no life run | §4.5, App. F | C | C tick 1 (line 890) | single run; E:41 says "queued" (stale) |
| DEV_UNVERIFIED_PROVENANCE; not leak-scanned; fail-closed check not implemented | §3, §4.5, App. F | C + code | C lines 840–842, 857–882; `research_loop/coordination/20260910_bootstrap_v3_unverified_provenance_quarantine.md`; `bootstrap_corpus.py:22-23` | |

### Discussion, appendices A–C and G

| Number | Where it appears | Source | Dated entry / location | Notes |
|---|---|---|---|---|
| 17 round-0 writes: 5 in [+0.100, +0.167] (4 parented, 1 self), 7 below −0.03, 5 within ±0.03 | §5 | derived | App. E round-0 column | |
| six 300/1,200-row cells 0.456–0.515 | §5 | E, C | Table 1 cells | |
| clear spells 0, 1, 3–4 windows | §5, App. A | C | C lines 562–565; 520–521 | |
| n = 9, 6, 3 lives; 9 vs 8 lineages; 2 lives for absorption | §5 | E, C | E:22, E:47, E:38, E:35 | |
| rows per sleep ↓ ~4×, chars per row ↑ ~3× (single unreplicated measurement) | §5, App. D | C | C [Fable → Codex] 2026-09-10 (line 671); C [Codex] (lines 758–762) | per-life values only in IDEAS.md (excluded) |
| RP restarts 3 / 3 / 4; R2 seeds 0/1/5 one each; kill on 2026-09-08 | §5, Table 2, App. D | C, E | C SEQ-001; C 2026-09-08 ~02:10 (line 375); E:47 | resume side effects from `run_life_v2.py:214-239`, `DESIGN.md:161` |
| birth prompt, parent prompt (verbatim) | App. A | code | `organism_v6/bootstrap.txt`, `organism_v6/parent_prompt.txt` | |
| waking-brief prompt "max 8 lines"; k = 6 principles | App. A | code | `sleep_compile.py:74-77, 64-69` | |
| correction call: playbook ≤ 6,000 chars, first 3,000 shown; transcript last 8 chunks / 3,500 chars (4,000 cap unbound); "under 100 words"; 220 tokens @ 0.4; self-parent 160 @ 0.5; restatement 100 @ 0.5, 400 chars to ledger, 250 chars to intro; playbook rewrite 1,200 tokens @ 0.4 from ≤ 40 + 20 rows clipped to 160 chars, ≤ 9,000 chars | App. A | code + C | `parent_backend.py:73-90, 121-141, 162-184`; `classroom_round.py:195-261`; playbook bound and overflow in C 2026-09-08 ~01:30 (line 370) | only the bound and the incident are logged |
| leak scan: 12 answer-phrase patterns; 6-pass pattern; half-of-content-words rule; fallback text | App. A | code | `parent_backend.py:121-141`; `parent_brief.py:175-187, 229-236` | |
| scout 7000: 11/32 with descriptor words, exact scanner blocked 1; scout 7003: 3/32 blocked, 5/32 residual; old-scanner scouts 8/32, 6/32 | App. A, §2.4 | C | C 2026-09-07 ~16:30 (lines 229, 250); ~19:10 (line 284) | two different scouts |
| 4/16 and 6/14 v3 briefs blocked before the quote-back exemption | App. A, §4.4 | C, E | C line 656; E:10 | |
| brief v1 at sleep 192, v2 at sleep 224 of life 401 | App. A | C | C 2026-09-09 ~10:30 (line 509); ~15:30 (line 523) | |
| v3: previous brief ≤ 1,200 chars; 320 tokens @ 0.4; four 600-char chunks; 1,900-char cap; shown every wake | App. A, §2.2 | code + C | `parent_brief.py:218-241`; C 2026-09-10 ~17:00 (line 612) | |
| canary: 4 programs × 3 chunks, seeds 4242+i, pass ≥ 0.5 | App. B, §3 | code | `run_life_v2.py:26-49` | |
| paired classroom canary ON ≥ OFF − 0.10 over thought rows; 0.21 vs 0.93 / 0.98; base 0.88–0.95 after fix; one pre-fix 0.19 | App. B | C + code | C 2026-09-07 late (lines 173–181); C ~15:20 smoke table (line 207); `classroom_round.py:47-50, 345-359` | smoke runs are not evidence |
| brevity 0.5×; 6.6–10 chunks/ep for the five score-rejected candidates | App. B | C + code | `run_life_v2.py:158, 179`; C SEQ-002 | |
| classroom strata shares 0.10 / 0.15 / 0.10 / 0.05 / 0.05 / 0.15 / 0.40; back-fill order | App. B | code | `classroom_round.py:52-60, 101-144, 267-306` | caps on a reservation, not minimums |
| App. C: instance restart rule; 424 → 67 grouping bug | App. C | C + code | C line 489; `parent_brief.py:70-84` | |
| vLLM 16k window; 48 GB-class GPUs; 32B TP=2 hung 3× | App. G | E | E:6, E:10, E:44 | no identifiers |
| ~60 GPU-hours for rank cells (logged before the fifth pair finished) | App. G | C | C 2026-09-07 ~22:30 (line 344) | |
| old writer: 7/8 (+0.006 to +0.025) through ep 512; 5/5 then stopped at 344; third life −0.48 at 512, stopped ~704 (killed at 88/128), life mean −0.219, 7 harmful of 10 | App. G | C | C 2026-09-07 Fable (lines 35–42, 68–71); C lines 132–133, 503, 556; C SEQ-001 ("Old-writer R_B_seed2: −0.219, 7 harmful") | "−0.48" logged as "score", read as paired |

## Auditor's brief

Five claims most at risk, and how a second model should attack each:

1. **"0 harmful pairs in 60 gated probes" (§4.2, Table 2).** Post-selection by construction: the gate admits on the same 8 programs and seed that report the pair, with tolerance 0.02 < harm 0.03. Attack: from gate.json and probe records, count how many committed adapters' *next* regular probe fell more than 0.03 below the floor they passed (SEQ-002 shows one 0.065 swing); run the pending disjoint-panel re-probe (`research_notes/disjoint_panel_v1.json`) and check whether any R3 adapter is harmful there; check whether "0 harmful" survives simply because the gate rejected every late-life candidate (life 500: five in a row) so that the scored adapter is frozen, i.e. the same failure mode as ungated seed2 with a better-looking number.
2. **"What the write learned is recipe lock-in; 0.4878 = birth recipe applied with no model" (§4.3).** Rests on a four-decimal coincidence plus M12 modal-share statistics. Attack: pull the probe ledgers of R3 501/503 and R4 600–603 and verify the first ACT line is literally `-mem2reg,-sroa,-gvn,-simplifycfg` in the checkpoints scoring 0.4878 (M12 gives 0.86–0.90 modal share, not identity); identify the six-pass routine behind 0.5291 and confirm it appears in the ledgers; recompute -Oz/-O3 per program; test whether the ungated R2 lives (not covered by Observation 1) also sit on 0.4878/0.5291 or vary.
3. **"Late-life collapse in 4/9 ungated lives, every harmful write passing the format canary" (§1, §4.2).** Attack: the SEQ-001 recount gives no per-pair episodes, so "none before 384" rests on the 82-pair snapshot while seed3's single harmful pair (−0.057, paired SD ≈ 0.013, so ~4 SD but n = 16 pairs × 9 lives = 144 draws) and seed6's two are near threshold; verify from the raw probe JSON that every harmful pair's committing sleep has a canary record ≥ 0.5 (only seed5@448 and seed2@608 were inspected); check whether resumed lives (seeds 0/1/5; seed5 is the worst life) re-recorded partial ledger rows into the corpus; recount harm excluding seed5.
4. **"Storage without extraction: ~3 nats per token stored vs ~+0.02 behaviour" (§4.3).** Attack: the absorption probe scored bare-text-trained v1 adapters under a chat template (rescoring queued, not done), so the absolute nats may move; the control life shares the gym and curriculum, so "row-specific excess 0.6–1.7" may be gym content, not format; n = 2 lives × 24 rows with no per-row values; the behaviour side is 8 pairs with mean +0.021 against paired SD 0.013; and the two runs of the instrument (three-sleep readout vs eight-sleep run) disagree at sleep 1 (1.72 vs 1.6 control). Re-run with per-row losses saved, bare-text format, and a gym-free control corpus.
5. **"Ritual onset is consistent (160–224 in 8/9 measured lives, 71–100% persistence)" and the parented onset/echo story (§4.4).** Attack: the 9 lives were scored once at ages 320–552 (seeds 7/8 never scored), thresholds are hand-set, and the same-recipe flag fires from window 1 by design so ritual reduces to one more flag firing; life 401's window 224 is ritual in one record and clear in another; the templated-notes rule was changed for the parented arm only after its rows were read; briefs were absent from context in every clear window (withdrawal confound); and the echo metric's +0.10 over the control null pools brief versions and excludes life 402. Recompute all windows for all 12 lives at 1,024 episodes under both detector rules, and run the echo metric with a shuffled-brief null.

Secondary risks: the rank × dose table is counted against a base measured with a different probe procedure (0.494 vs life OFF 0.471–0.474; 8/10 becomes 7/10 at 0.485 and is not measured at the cells' own procedure); the classroom exam tolerance is 0.5–0.7 SD of the decision statistic, so every commit/reject in Appendix E is near-coin-flip; the v2.1 classroom epoch count (2 vs 3) is unreconciled; the leak-scan residual (5/32) has never been audited across all delivered utterances.
