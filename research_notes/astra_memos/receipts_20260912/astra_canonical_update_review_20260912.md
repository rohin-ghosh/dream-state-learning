# Independent canonical component-update review — 2026-09-12

## Verdict and frozen scope

**ONE CONCRETE TEXT BLOCKER; otherwise the checked component counts, doses,
historical preservation and claim boundaries agree with the cited evidence.**
Recommend the one-clause correction below, then a fresh Turing freeze through
Main. No result recalculation, table replacement, threshold change, new assay,
or literature expansion is needed for this finding.

Reviewed against HEAD
`7796718c8a4e40369ce4884e0e7c957d28aed834`, which remained unchanged during this
review. The receipt clarified that “README.md” means **paper_prototype/README.md**:

| Canonical file | Frozen SHA256 checked |
|---|---|
| paper_prototype/main.tex | be6edcdd088d7a510afc3f1bf8aed303b19774d1be15be71124c925e86e16920 |
| paper_prototype/README.md | 40299ee3f07e53b3fac44057edb5ed81c7ec28edb32f75e6d5a644dbae198225 |

Both match Main/Turing's handoff and still matched at the final source check.
The repository-root README.md has hash
`c08f472cd9d9d2ad0308ea8a5c8ae96a6ee118f148d13af525cb844ac2192edf` and no diff
against this HEAD; that was a path ambiguity, **not frozen-file drift**.

Turing's 45-PASS receipt was read at
`/tmp/astra_canonical_integration_checks_20260912/results.json`, SHA256
`a5782e7cb64c59002ec2998c9fc6e14dfd282e357749beb58e3d6c51fa3758b6`.
It supports structural checks but does not override the raw-output contradiction
below. I independently checked the specified evidence and preservation items;
I did not rerun Turing's checker or claim a TeX compilation.

Only this review file was written. Git use was read-only diff/object inspection;
no git writes, GPU/process queries, model calls, network or literature audit.

## B1 — correct the OFF/ON newline generalization before accepting this freeze

Location: **paper_prototype/main.tex:809**.

Current clause:

> scored candidates include LF+EOS while original greedy outputs omit LF.

This is false as a statement about the original generations generally. Across
the original sealed semantic writer's **880** generated records:

| Original state | Primary/locality generations | Copy generations | Ends in LF |
|---|---:|---:|---|
| OFF | 192 | 16 | None: 0/208 |
| r0_plus | 160 | 8 | All: 168/168 |
| r0_minus | 160 | 8 | All: 168/168 |
| r1_plus | 160 | 8 | All: 168/168 |
| r1_minus | 160 | 8 | All: 168/168 |

All 880 raw-file hashes matched their original SEAL entries. The ON/OFF
format difference matters to the interpretation of the very large
candidate-format mass shift. The source terminal memo contains similarly broad
wording, but raw outputs are the stronger evidence; matching that memo is not
sufficient validation of the clause.

**Smallest correction, leaving the rest of the paragraph intact:**

> scored candidates include LF+EOS; original OFF outputs omit LF, whereas
> original ON outputs include it.

Keep the adjacent distinction between fixed padded-forward likelihoods and the
dynamic-length greedy generator. That limitation remains valid independently
of the newline correction. No claim of selective storage or of full backend
equivalence should be added.

Exact raw examples under
`/tmp/astra_semantic_writer_terminal_20260912/astra_semantic_writer_Q0_20260912_attempt1/`:

- `stages/off_generate/raw/2e651664782d84b6625595477967329e8db36106769c4646b6921485f3178e47.json`
  has output text `ACT: -mem2reg` without LF; SHA256
  `fb86ef1fc79ea123fd7b5bf55dd9a004b04a098806c5ac3fb9bba501653e9e02`.
- `stages/eval_r0_plus_generate/raw/804adfa6f3938233c302a9a9a346f4fd0c1bada72d62b825fd13a7981acf9729.json`
  has output text `ACT: -gvn\n`; SHA256
  `0480d6aaec2dad6c5fcd3c964041ba69e91138c41f1f11c1fee11ae61ce3fc85`.

Original request inventory SHA256:
`a1795b1ea6a19399954f700624ed2155613b9197f4758ef86f8c772c81963c6c`;
original seal identity previously pinned in this review thread:
`71f164765d1cdfeef96b881da6eac68de05f1921989f1b167f7dff7b6f088d71`.

## Checked numerical claims — no corrections found

### SEQ-073: oracle-material contrast

Locations: main.tex:291, :305, :801; paper README:173–176.

- Useful ON solves **2/3/5 of 16**; corrupt ON **0/1/0 of 16**; every OFF
  condition zero. Useful-minus-corrupt ON-minus-OFF contrasts **2/2/5 of 16**.
- There are **192 condition–episode records**, not 192 independent puzzles:
  3 optimizer seeds × 2 material arms × 2 adapter conditions × 16 panel IDs.
  Every cell reports 16 ACTs; OFF partial-score means are 0.1125, not solve rates.
- Shared development panel, optimizer-seed replication, external oracle source,
  four complete-solution overlaps and solved overlap ID 1900055 are disclosed.
  No episode-level significance, wholly unseen-solution or parenting conclusion
  is substituted for the observed small directional contrast.
- The distinct seed0 devices and useful-first sequential ordering for seeds1/2
  remain disclosed. No correction to these denominators or historical rows is
  justified by this review.

### SEQ-085: one-event whole-text versus ACT-only replay

Locations: main.tex:293, :306, :799, :803; paper README:176–180.

- Whole ON accepted **1/0/1 of 32**, ACT-only **2/2/1 of 32**. Strict-format
  counts **5/6/5** versus **30/30/28**. Every OFF cell has zero accepted and two
  strict actions; the repeated OFF observations are correctly called one
  deterministic baseline, not independent learners.
- Six fits each contain **one unique source event**, **32 explicit replays**,
  **96 steps**. Whole input/target token passes are **92,064 / 8,832 per fit**;
  ACT-only **86,880 / 3,648 per fit**. These match all six actual fit records.
  Equal steps/examples are explicitly not token-, information- or compute-matched.
- The paired recipe includes chat_template=true for SEQ-085. The manuscript
  distinguishes this from SEQ-073's pre-rendered/chat_template=false recipe;
  no false identical-rendering claim remains.
- Seven accepted ON cell-episodes, 192 ON first-action checks, source-board
  incompatibility and the absence of a broad-reasoning inference are consistent
  with the committed terminal account. This review checked the committed
  reduction, not a new independent Sudoku replay of those 192 outcomes.
- The wording correctly limits the negative to this selected source event and
  endpoint. It does not claim reflections generally harm performance or that
  the comparison isolates a teacher, reflective semantics or developmental parenting.

### SEQ-086: supplementary scoring, not new training or new generations

Locations: main.tex:295, :307, :805–813; paper README:181–187.

- Completion receipt: **832 new scores**, **880 reused generations**, **zero new
  fits**, elapsed **347.4679672718048 seconds**. Rounded manuscript value 347.468
  is correct. The inherited report counts still describe the original four fits;
  the text correctly distinguishes those from supplement cost/counts.
- Unchanged generated BA in root0 +/−, root1 +/− order:
  **37/64, 33/64, 32/64, 34/64**, with validity 1.0.
- Mean conditional log-q gains:
  **1.078956617564201, 0.9514255277942695, 0.6465927120448413,
  0.6083201773732566**. The six-decimal presentation is correct and is not
  mislabeled as a raw mean NLL loss.
- Across 16 state/locality-family cells, mean binary conditional TV spans
  **0.2800903957789098–0.6563000606498942**.
- Across 20 state/family cells in the separate post-hoc absolute audit (including
  primary), mean coarse three-category TV spans
  **0.9782725976310174–0.9986583216161667**. The rounded range is correct.
  It is explicitly not full output-distribution TV or semantic action change.
- `OPTIMIZATION_INCONCLUSIVE` remains; optimization/binding/spill false,
  interface/oracle true. The paper neither turns positive mean gains into a
  per-key pass nor transfers the old-score ceiling automatically to new scores.
- Conditional-TV and cancellation blind spots are disclosed. The scoring defect
  is not generalized to historical experiments, generated solves or all scorers.
  Apart from B1, the likelihood/TV qualifications are appropriately bounded.

## Historical preservation and H1/H2 boundaries

Independent byte checks against the pinned HEAD found all **12 historical
tabular environments preserved exactly**, with exactly **one added table**.
The entire old appendix, from its appendix marker to the old end-of-document
boundary, remains byte-identical before the new component appendix.
The main diff adds a separate component subsection/appendix, narrows discussion
and limitations, and replaces the abstract; it does not replace old numerical
rows with component results. Turing's receipt additionally reports preserved
historical README rows and unchanged citation calls/authorship/contribution lists.

Main.tex:289 and :330 and paper README:139–145 keep components distinct from
completed developmental lives, retention, parenting and H1/H2. The future-work
paragraph is explicitly prospective. The abstract's “small” transfer and
single-event Scratchpad statement are qualified by the body rather than promoted
to population generalization or a developmental mechanism. No blocker found on
these claim boundaries. Current exact-training-probe outcomes are outside this
freeze and should not be added opportunistically.

## Nonblocking precision advisories / smallest optional edits

**A1 — label the 37.48 cost as controller elapsed time.**
Main.tex:813 / paper README:187 correctly restrict 37.48 A40-minutes to the two
additional replication controllers. To make actual-versus-reserved/compute scope
unambiguous, prefer “37.48 summed controller-elapsed minutes on A40 devices”
over an unqualified A40-minutes unit. The source describes launch-to-terminal
wall duration, not measured active GPU kernel time, and excludes the seed0
controller. No numerical change is needed.

**A2 — make “per fit” explicit beside token passes.**
Main.tex:803 / paper README:179 can add these two words. The present local
context is consistent, but an isolated table reading could mistake the figures
for six-fit campaign totals. The unchanged per-fit doses are correct; six-fit
totals would instead be 536,832 input and 37,440 target token passes. Do not
replace the per-fit numbers with totals silently.

**Cost claims already appropriately limited:** independently summed SEQ-085
recipient elapsed time is exactly **3,990.821522 seconds**; the paper says this
is not calendar duration or measured GPU compute. Generated-token and
finish/truncation metadata are absent, so reserved token ceilings must not be
reported as usage. The manuscript does not make that mistake. Supplement
verification/release time is additional; no aggregate campaign cost is inferred.

**A3 — compilation remains unverified, not an evidence blocker.**
The handoff reports no pdflatex/latexmk/tectonic and two unchanged unresolved
citation placeholders. A 45-check structural PASS is not proof of page count,
table fit or publication-ready compilation. Do not expand this bounded review
into a literature audit; retain that limitation for the normal build step.

## Evidence identities

The following three main artifacts both exist in pinned HEAD and match its
committed bytes, not merely similarly named working copies:

| Under research_notes/astra_memos/receipts_20260912/ | SHA256 |
|---|---|
| astra_behavior_three_seed_descriptive_20260912.json | 71ca480472207c03eb83e45a5f22b407c87778dc52249e1d0a305aae8cbade91 |
| astra_correction_utility_analysis_20260912_main.json | 29b6cf3ca3de9b4d9f6fe643fc769dbaed3a3cbc710d6e69bb1f6e53ec8dd7b0 |
| astra_semantic_rescore_terminal_20260912.tgz | 7b2f6bc8642055889f5cd824a1bb7762b3b7938e9a644372e18846dec88aedf4 |

Supplementary report inside the capsule:
`f066f98d19cd3801253d63b0cf0622b77865feabffddaf26c25baa96a32e18df`.
Post-hoc absolute audit JSON read beside it:
`82c6c3947a173e4198c01e1334ca0da37cb57934446815ef53dac75e61b9d192`.
The corresponding committed SEQ-073/085/086 terminal memos were read as context;
they were not treated as overriding underlying raw records.

## Handoff to Main / Turing

Ask Turing to apply B1 only (A1/A2 are optional precision improvements), rerun the
existing integration checks, and issue new main.tex/README hashes. This review
does not authorize editing the frozen files on Turing's behalf. No fresh freeze
was needed to inspect the provided bytes; one **will** be needed after correction.
Accept the bounded content update after that targeted check rather than reopening
the old numerical tables, inventing a new scientific gate, or delaying native
probe work for a manuscript-only correction.

## Final disposition — corrected freeze (2026-09-12)

**ACCEPT for this bounded B1/A1/A2 content review; no remaining blockers.**
This disposition supersedes the initial blocker and correction handoff above,
which remain preserved as historical review findings.

- **B1 resolved:** `paper_prototype/main.tex:809` and the matching README clause
  distinguish original OFF outputs omitting LF from original ON outputs including
  LF. This agrees with the audited 208 OFF / 672 ON generation counts. The
  fixed-padded likelihood versus dynamic greedy-generation distinction remains.
- **A1 resolved:** `paper_prototype/main.tex:813` and the README identify 37.48
  as summed controller-elapsed minutes on A40 devices for the two additional
  replication controllers, not measured GPU compute or aggregate campaign cost.
- **A2 resolved:** `paper_prototype/main.tex:293`, `:803`, and the README explicitly
  qualify token doses as per fit: whole/ACT-only input passes 92,064/86,880 and
  supervised passes 8,832/3,648. Equal examples/steps are not token matching.

Independently rechecked corrected frozen SHA256 values; **no drift**:

- `paper_prototype/main.tex`:
  `f4e79aaafed4847bc574f1fee0bbf172276f8484028c850c86181ba116b14f93`
- `paper_prototype/README.md`:
  `5945d1e4f9daa55bf70a52d35aec619112c45159bfa475523d345c8c8518fb43`

Supporting Turing receipt:
`/tmp/astra_canonical_integration_checks_20260912/review_correction_results.json`
reports 25 PASS; its suite was not independently rerun in this final check.
Compilation remains unverified (A3), not a content blocker. This final check
adds no scientific endorsement, retrospective pass, expanded audit, or claim
that H1/H2 are established. Only this review file was changed. Task closed.
