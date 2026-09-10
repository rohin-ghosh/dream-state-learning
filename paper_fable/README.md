# Experience Models — ICLR 2027 submission (synthesized draft)

This directory holds the synthesized paper draft: `main.tex`, `refs.bib`, and this README.

**What the paper is.** A measurement-first report on an *experience model*: a frozen Qwen2.5-7B base plus a per-life rank-8 LoRA that the agent rewrites every 32 episodes from its own recorded thinking (THINK / DREAM / SLEEP), with an optional PARENTING stage in which a stronger, non-learning model prescribes thinking patterns in context. Every empirical statement is a cell count or a measured mean with its noise band, taken from `research_notes/EVIDENCE_TABLES.md` or a dated entry in `research_loop/COORDINATION.md`; where the two disagree, the later dated COORDINATION entry wins and the discrepancy is listed below. Anything not in those sources is written as "not measured".

**Source precedence and known discrepancies (to be expanded in the source table).**
- R3 gated lives: three snapshots exist (COORDINATION 2026-09-10 late per-life: 8/7/7/10 pairs, means +0.036/+0.016/+0.054/+0.022, rejections 2/0/8/4; the same day's status line: 35 pairs, means +0.039/+0.016/+0.055/+0.022, rejections 2/0/9/4; EVIDENCE_TABLES "as of 2026-09-11": 500 9 pairs / 5 rejections, 502 10 rejections, 503 11 pairs; and the "[Fable daemon] 2026-09-10 tick 1" status with six gated lives). The paper reports all, uses the 35-pair total as the headline, and states that the per-life pairs sum to 32.
- Absorption control at sleep 1: COORDINATION 2026-09-07 17:40 gives 1.72 (both lives); EVIDENCE_TABLES gives 1.6. The paper uses 1.72 (dated entry wins).
- Committed sleeps at the first certification snapshot: COORDINATION 2026-09-08 06:30 says "46 sleeps across 6 lives", the 06:45 entry says "45/45". The paper uses 45/45 (the certification-draft count).
- v2.1 trainer epochs: EVIDENCE_TABLES lists 2 epochs for classrooms; `classroom_round.py` passes `--epochs 3` (and the write-swarm screen passed 3 epochs at lr 5e-5). The paper states 2 epochs for the v2.1 path as frozen and 3 epochs for the recipe screen; the classroom-round epoch count should be checked against the training receipts before submission.
- Round-0 harmful writes: COORDINATION 2026-09-08 10:00 gives 0/6 parented vs 4/6 self-taught for six lineages; the paper reports the counts computed from the full 17-lineage per-write table (2/9 parented, 5/8 self-taught) and gives the six-lineage interim in Appendix E.
- Row-specific absorption excess: COORDINATION 2026-09-08 08:20 and EVIDENCE_TABLES give "1.7 → 0.6"; the sleep-1 arithmetic from the 2026-09-07 17:40 values (3.25 − 1.72 = 1.53; 3.29 − 1.72 = 1.57) gives about 1.5, and the 17:40 entry itself says "≈ 1.3–1.6". The paper quotes the logged whole-life endpoints (1.7 → 0.6) and does not compute a sleep-1 value.
- Bootstrap adapters: the latest COORDINATION status says the v3/v2/v1 adapters were trained (v3 final loss 0.675); no life has been run from any of them and no effect is measured, so the paper labels the stage "in training".
- Numbers deliberately excluded because their only source is outside the permitted set (`research_notes/certification_report_draft.md`, `research_notes/IDEAS.md`): per-sleep absorption values beyond those in COORDINATION (e.g. 3.30, 3.11, 2.88, 2.41, 2.54; excess 1.64, 1.72, ...; base NLL 4.34 → 3.17), the dialect counts 24/74, 25/88, 17/87, and the per-life corpus-density values (127 → 30; 314 → 791; ...).

**Length.** No TeX installation was available when this draft was written, so the page count is estimated from words: the main text (Introduction through Related Work, excluding the two statements) is about 6,500 words plus four tables and four figure placeholders, which at ICLR geometry (about 700 words per page) is roughly 9 to 10 pages. If it runs over 9 pages after compiling, trim in this order, since every detail is already in the appendices: the "Two weaknesses" sentences in Results 4.2; the "Noise at the tolerance; parent size" paragraph in 4.4; the first-intervention metrics in "Briefs delay ritual"; the "Sleep consolidation" paragraph of Related Work; the figure placeholder captions once real figures exist.

## How to compile

1. Obtain the ICLR 2027 author kit and place `iclr2027_conference.sty`, `iclr2027_conference.bst` and `math_commands.tex` next to `main.tex`. Do **not** add `\iclrfinalcopy`; the submission is double-blind.
2. Fill in the `TODO-<topic>` bibliography entries listed at the end of `refs.bib` (looped transformers, chain-of-thought, CompilerGym, LEAFE, early experience, EVAF, MemoPilot, Spark, CL-Bench), or remove the corresponding `\citep{TODO-...}` calls.
3. Compile:
   ```
   pdflatex main
   bibtex main
   pdflatex main
   pdflatex main
   ```
4. Figures 1–4 are text placeholders with their captions; replace them with schematics before submission.

## Number → source table

*To be filled.* One row per number in the paper: value → section/table → source file (`research_notes/EVIDENCE_TABLES.md` or `research_loop/COORDINATION.md`) → dated entry (e.g. `[Fable] 2026-09-09 ~20:30`) → notes on derivation (e.g. "82 − 69 − 9 = 4 pairs in between", "round-0 harmful counts computed from the per-write table").

## Auditor's brief

*To be filled.* Ten lines listing the five claims most at risk, so a second model can attack them.
