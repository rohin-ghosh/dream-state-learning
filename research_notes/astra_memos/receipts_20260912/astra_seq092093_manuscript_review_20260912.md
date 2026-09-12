# Independent scoped manuscript review — SEQ-092/093

**Verdict: PASS. No required fixes to the reviewed SEQ-092/093 manuscript additions.**

Date: September 12, 2026. Evidence/status cut stated by the manuscript: September 12, 2026, 16:20 UTC. This verdict permits only bounded manuscript reporting of these captured observations. It is not experiment/code review, launch authorization, scientific-gate qualification, official model-origin authentication, or PDF/layout approval.

## Scope and exact reviewed bytes

Reviewed the added SEQ-092/093 evidence and associated status/claim-boundary edits in exactly these six dirty files. The abbreviated filenames in the request resolve to the paths below. Earlier scientific results were not re-reviewed; HEAD was used only to inspect the diff and verify preservation. Preservation reference: `8a52b2623018b96a65271628018183eaa0c0f228`.

| File | Reviewed working-tree SHA256 |
|---|---|
| `paper_prototype/main.tex` | `e0dc3d2864ad430d3b056c798ff06683d3715605b29baacf1fcd485a1b5a0181` |
| `paper_prototype/README.md` | `36cc4241609ff98fe756fc228d39c7ac8f2e06f984f36344aa6e9edc8964b742` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `1f087bad7b68a019910fef266f2b70a5e332f5980f2276c961cd673a09a153a4` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `02f9f7a0e0da492cfb6d72783d2fcd3d954617dae9c0af86375828a2f384c171` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `1421357aeee9217afc9cfd86d84bc97628938cdb52d6fa791b1c7411ad509756` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `dd842d535e770c8b214b765206d3c2e03ae18f49cda1812a9675a3aa485bd268` |

All source references below are repository-relative unless marked `/tmp`; line numbers refer to the reviewed snapshot. Local standard-library checks read the receipts and compressed archives without extracting into or writing to the repository. No repository source, test, launch helper, or stored audit script was executed.

## SEQ-092: numerical and interpretation checks — PASS

The terminal memo, independent result review, summary CSV/JSON, and manuscript agree. I additionally recomputed the five reported gain columns directly from the four captured `stages/*/eval.json` files inside `receipts_20260912/astra_cumulative_terminal_20260912.tgz`, using each target's raw probability divided by the four-colour raw-probability sum, then ON minus OFF. OLD facts have 16 dose-16 owners with three paraphrases each; OLD frames have 16 owners; NEW frame/bicycle cues have 32 matched owners. Recomputed means agree with the summary to absolute tolerance `1e-14`.

| State | OLD fact | OLD frame | NEW frame | NEW bicycle | NEW frame minus bicycle |
|---|---:|---:|---:|---:|---:|
| A1 | 0.292056 | 0.425674 | 0.005779 | 0.008963 | -0.003184 |
| AN | -0.004837 | -0.020875 | 0.673276 | 0.713845 | -0.040570 |
| A2 | 0.341508 | 0.209910 | 0.359223 | 0.620610 | -0.261387 |

- OLD fact and frame ratios are correctly reported together: `1.169323` versus `0.493124` (abstract: `1.169`/`0.493`). NEW bicycle spill exceeds frame gain in both new fits. Rounded colour-mass/abstention values agree with the independent review.
- The manuscript explicitly describes fresh-base reconstruction, not warm-start continuation, resumed optimizer state, or survival of A1 parameters. It distinguishes owner denominators from learner replication, discloses one seed/bank and unmatched history/dose, and does not promote generic NEW retention ratios.
- A1-before/after complete cue arrays are exactly equal in the captured files. The manuscript appropriately limits this to read/reload repeatability, not retention through updates or generated-task performance. Native frame-binding/abstention failures are retained and native gate labels are not presented as sprint qualification.
- Costs reconcile: `1536 + 11229 = 12765` new-fit updates; `199.4 + 1416.8 = 1616.2` native-loop seconds; `1092513` input and `1041453` supervised passes. Four reads report `965.251713` scoring seconds, `1160` forward calls, `84800` candidate sequences including `1792` abstention sequences, and `3511832` padded positions. `2953.833434` seconds remains the controller reservation interval, not active GPU time, the later release observation, or full-campaign throughput. A1 is identified as inherited rather than a new fit.

Sources: `research_notes/astra_memos/ASTRA_CUMULATIVE_TERMINAL_2026-09-12.md:11`, `:18`, `:28`, `:44`, `:65`; `research_notes/astra_memos/receipts_20260912/astra_cumulative_result_review_20260912.md:15`, `:23`, `:31`, `:39`, `:47`, `:49`; `research_notes/astra_memos/receipts_20260912/astra_cumulative_summary_20260912.csv:1`. Manuscript locations: `paper_prototype/astra_sprint_draft_20260912.tex:1043`, `paper_prototype/README.md:17`, and claim-map C36 at `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:576`.

## SEQ-093: strict failures, post-hoc content, and limits — PASS

- Current OFF/FULL/SYNTAX each remain `0/8` schema-valid and strictly grounded. FULL means citation-prefix supervision, not complete-record supervision. Primary zero invalid-citation counts are correctly explained as schema rejection bypassing citation validation, not proof of true citations.
- The archived audit's 24 per-case records recount to trained geometry `0/8`, `8/8`, `1/8` for OFF/FULL/SYNTAX; only FULL `t02` is a true literal witness. Both ON arms change all eight outputs relative to OFF, retain malformed `][]}` endings, and emit 32 tokens/case rather than exhausting the 128-token cap. The manuscript does not repair the outputs or turn the literal annotation into strict success.
- The 75-byte incomplete prefix, omitted lesson/outer closure, unsupervised EOS, and token-30 boundary difference are correctly distinguished from byte identity. The prefix/complete-record mismatch is a plausible limitation, not a proven sole cause. Crucially, zero qualified complete-record utility is explicitly **not proof of no parameter learning**.
- The selected source request's `332` prompt tokens/temperature `0.7` is not treated as a matched baseline for current `234`/`0.0` requests. Current OFF is the baseline. One selected event, one optimizer seed, and eight exposed development boards are not presented as independent learners or holdout generalization.
- Matched `264` input IDs do not become matched supervised dose or withheld content: `27` versus `21` supervised labels over `32` steps/fit yield `64` updates, `16896` input passes, and `1536` supervised passes. The 24 calls reconcile to `5616` prompt and `879` output tokens (`367 + 256 + 256`). `564.719025` controller-execution seconds and `34.9`/`10.7` train-manifest seconds retain their distinct meanings.

Sources: `research_notes/astra_memos/ASTRA_CITATION_SLEEP_TERMINAL_2026-09-12.md:11`, `:17`, `:34`, `:51`, `:63`; `research_notes/astra_memos/receipts_20260912/astra_citation_sleep_content_audit_20260912.md:7`, `:13`, `:24`, `:59`, `:61`, `:69`, `:75`, `:79`; its sibling JSON `records`, `arms`, and `training`; `research_notes/astra_memos/receipts_20260912/astra_citation_sleep_native_terminal_20260912.json:1`. Manuscript locations: `paper_prototype/astra_sprint_draft_20260912.tex:1093`, `paper_prototype/README.md:54`, and claim-map C37 at `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:643`.

## Receipt bindings and review provenance — PASS

- The cumulative capsule is exactly `4802823` bytes, SHA256 `c5a7649d14886ac86fdb966086fb08fe6440a6b766ba904a34ae20ec96266d9c`; its native report and manifest hashes match C36. The original report is preserved; the normalized capture-comparison repair is not misrepresented as an experiment failure or a fresh GPU run.
- The citation capsule is exactly `73933` bytes, SHA256 `c33d6001a12ddd0c737af8bebe7d43384aba84a21c5f101c6d5ecd10b1ba1192`. All 56 regular-file hashes match the audit JSON's complete source-file map; the independently recomputed map hash is `fbc50647ea103ab96d588f8ef7116e018b0a27979cafb9c49f3ddd1d0469b6ba`.
- The archived Halley Markdown/JSON/Python each match their supplied `/tmp` counterpart byte-for-byte. Markdown SHA256 is `41f1c509a2b897fee70aedb8ead5d75f4e228d3671acdbf374d8f90483dd53e8`; JSON SHA256 is `10c13cb41dabad486f6a79cf289487b11ea3ab1176a1e2f7656afc4b288f944f`. The README's five newly linked receipt files exist locally.
- Neither capsule contains `.safetensors` or `.bin` weight files. Native release receipts record GPU0 at `16:07:39.725090 UTC` and GPU1 at `16:11:26.632642 UTC`. These are captured native assertions, not new live GPU/weight checks. The manuscript properly distinguishes SEQ-092's independent bounded-reporting PASS from SEQ-093's native validation PASS plus a separate post-hoc content audit. No official model-origin authentication or standalone weight backup follows.

Sources: cumulative terminal memo `:74` and `:86`; cumulative independent review `:53`; citation terminal memo `:75`; citation content audit `:75` and `:83`; both capsules' `MAIN_TERMINAL_AUDIT.json`; claim map `:621` and `:701`.

## Abstract, preservation, and delivery constraints — PASS

- **Companion abstract: 235 whitespace-delimited words, below 250.** After collapsing whitespace, the Markdown `## Abstract` body and TeX `abstract` environment are exactly identical; a secondary word-regex count is 237, also below 250. Sources: `paper_prototype/astra_sprint_abstract_20260912.md:12` and `paper_prototype/astra_sprint_draft_20260912.tex:47`.
- The canonical `main.tex` abstract is byte-identical to HEAD. All eight canonical table environments and the entire suffix beginning at `\appendix` are unchanged. All 11 pre-existing companion tables remain byte-identical; the companion now has 12 tables because SEQ-092 adds one, rather than replacing historical results. `paper_prototype/refs.bib` has no HEAD diff. The scoped diff does not undo prior newline corrections or alter the historical thesis.
- Lightweight source checks find balanced braces/environments, no duplicate labels, and no unresolved `ref`/`eqref`/`pageref` targets in either TeX file. **No TeX build was performed.** `pdflatex`, `xelatex`, `lualatex`, `latexmk`, and `tectonic` are unavailable locally. No PDF, rendered table width, page count, or submission readiness is certified. This agrees with `paper_prototype/README.md:232` and `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:127`.
- The collaborator note remains explicitly **UNSENT** (`research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:1`, `:3`, `:31`). No collaborator communication occurred. The selected RuleGame `156` responses remain a planned budget, not completed work or an approval inferred from these results; its cited design receipt labels the proposal as design only. Main's implementation/launch work is outside this review, not independently checked or duplicated. Formal C11 and selective-memory/G3/P1/G5/H1/H2/mechanism-freeze/campaign-completion claims remain unqualified.

## Disposition

**PASS for these exact six-file additions; required fixes: none.** This is a local manuscript/evidence review only. No repository edits, network use, GPU activity, code/launch review, or commits were performed. The sole authored artifact is this `/tmp` report, created with `apply_patch`.
