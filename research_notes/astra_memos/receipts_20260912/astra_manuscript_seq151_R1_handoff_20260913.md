# EDITSTOP — SEQ151 R1 terminology-only correction

**EDITSTOP. Only the requested two TeX files and companion abstract changed.**
No later results inspected or incorporated; other three manuscript files remain frozen.
No staging, commit, push, GPU work or external send.

Review source: `/tmp/astra_manuscript_seq151_independent_review_20260913.md`, SHA256 `e37c7a1d30276c7be10e2f0b2d3ca63b49d0f51d5408452e0fa53ef8fd9cb039`.

## New exact hashes

| File | SHA256 |
| --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `591358e95783ef63eac16d4565d4a98eae47e1f8fe07f0f2f056c5e26e480332` |
| `paper_prototype/main.tex` | `24558539cb77caa778e286d6eda4028b4f569f2873dcd5650044e1aa288659b3` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `08b69bb8d64da4b3685968647f6434d75b7048b40aaac23369de6efebf516369` |

## Changes and checks

Three abstract substitutions: `first-token` → `first-divergent-token`.
One definition added immediately after each C87 table:
“First denotes the first divergent candidate token after the shared two-token prefix.”
No count, table value, source, claim boundary or pending-status change.

- paper_prototype/astra_sprint_draft_20260912.tex: inverse of only requested edits matches independently accepted SHA256
- paper_prototype/main.tex: inverse of only requested edits matches independently accepted SHA256
- paper_prototype/astra_sprint_abstract_20260912.md: inverse of only requested edits matches independently accepted SHA256
- paper_prototype/README.md: frozen SHA256 unchanged
- research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md: frozen SHA256 unchanged
- research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md: frozen SHA256 unchanged
- Unrelated dirty rules SHA256 unchanged
- Three SEQ151 abstract paragraphs remain identical
- Both TeX SEQ151 result sections remain identical
- Scoped git diff --check PASS

Exact inverse-edit hash checks prove there are no additional changes relative
to the six independently accepted file hashes. No PDF build performed.
Independent review may now bind the three new hashes; the original acceptance
is not represented as automatically covering edited bytes.

## Exact small diff against accepted bytes

```diff
--- accepted/paper_prototype/astra_sprint_draft_20260912.tex
+++ R1/paper_prototype/astra_sprint_draft_20260912.tex
@@ -284,5 +284,5 @@
 a learned closed loop. Separate high-LR seed0 recovery also has zero observed
 treatment contrasts. A checkpoint-specific HF diagnostic gives TRAIN15/16 and
-READOUT8/16 by both first-token and full likelihood, not native greedy accuracy;
+READOUT8/16 by both first-divergent-token and full likelihood, not native greedy accuracy;
 independent analysis remains pending. Actual-memory writing/readback remains
 protocol/CPU-runner development, not a result. H1/H2 and the mission remain open.
@@ -3478,4 +3478,5 @@
 \end{tabular}
 \end{center}
+First denotes the first divergent candidate token after the shared two-token prefix.
 Fit2 TRAIN old/new is8/8 and7/8 by both metrics; READOUT is4/8 and4/8.
 All full-score ties are zero. This supports checkpoint-specific keyed candidate
--- accepted/paper_prototype/main.tex
+++ R1/paper_prototype/main.tex
@@ -125,5 +125,5 @@
 a learned closed loop. Separate high-LR seed0 recovery also has zero observed
 treatment contrasts. A checkpoint-specific HF diagnostic gives TRAIN15/16 and
-READOUT8/16 by both first-token and full likelihood, not native greedy accuracy;
+READOUT8/16 by both first-divergent-token and full likelihood, not native greedy accuracy;
 independent analysis remains pending. Actual-memory writing/readback remains
 protocol/CPU-runner development, not a result. H1/H2 and the mission remain open.
@@ -1239,4 +1239,5 @@
 \end{tabular}
 \end{center}
+First denotes the first divergent candidate token after the shared two-token prefix.
 Fit2 TRAIN old/new is8/8 and7/8 by both metrics; READOUT is4/8 and4/8.
 All full-score ties are zero. This supports checkpoint-specific keyed candidate
--- accepted/paper_prototype/astra_sprint_abstract_20260912.md
+++ R1/paper_prototype/astra_sprint_abstract_20260912.md
@@ -414,5 +414,5 @@
 a learned closed loop. Separate high-LR seed0 recovery also has zero observed
 treatment contrasts. A checkpoint-specific HF diagnostic gives TRAIN15/16 and
-READOUT8/16 by both first-token and full likelihood, not native greedy accuracy;
+READOUT8/16 by both first-divergent-token and full likelihood, not native greedy accuracy;
 independent analysis remains pending. Actual-memory writing/readback remains
 protocol/CPU-runner development, not a result. H1/H2 and the mission remain open.
```

**EDITSTOP.**
