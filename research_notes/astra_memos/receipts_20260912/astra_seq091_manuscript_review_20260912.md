# Independent bounded manuscript review — SEQ091 / C35

Review date: September 12, 2026; evidence checks completed at 16:00:23 UTC.

## Verdict and scope

**PASS for the bounded SEQ091/C35 manuscript integration. No critical, high, or medium-severity finding. One optional low-severity wording clarification; no required fixes.** This is a manuscript-evidence review, not a scientific promotion, experiment authorization, or gate on Main's critical path.

Reviewed the six assigned files in commit `40c7223dc52457d797f85299549b42f7fc952b3f` against parent `d1878cb5d56aac2a1009b766fdeaf38e99222f2e`. The initial uncommitted diff became committed during review; the user explicitly confirmed the frozen commit and authorized this comparison. All six working-tree byte sequences matched the reviewed commit when checked. No unrelated untracked writer code was inspected.

Verification is restricted to new SEQ091/C35 assertions and preservation requirements. Scientific sources are the terminal memo and archived independent audit Markdown/JSON listed below. Main's prospective protocol selection and still-running cumulative status are treated as the user-supplied evidence-window status, not independently polled operational facts. The linked prospective protocol was not separately audited; this verdict does not certify its implementation, masks, future fits, or outcomes.

No repository edits, GPU actions, network access, Git mutations, experiment runs, archive extraction, scientific reducer reruns, or external communication were performed. Local read-only Git inspection, source comparisons, JSON parsing, embedded-record consistency checks and SHA256 calculations were used. The sole file written by this review is this `/tmp` report. No TeX compilation or PDF/layout validation is claimed.

## Verified findings

1. **Strict endpoints agree across manuscript and receipts.** Source process 2/8 versus format 0/8; changed-board application 1/8 versus 0/8. Schema validity is process 7/8 versus format 8/8 at both stages. Invalid citations among schema-valid records are respectively 5, 6, 8, 8. A small independent read-only check of the JSON's embedded raw text and candidate boards reproduced all 32 schema/grounding verdicts; it did not invoke the archived audit script or original reducer. Both three-cell process records remain schema failures, without pair salvage.

2. **The essential ancestry limitation is explicit and correct.** Only process t02 is a valid application; its source s02 is invalid. The t02 box citation `(3,3),(3,4), digit 1` matches its embedded candidate, while s02's claimed digit 4 is not present at both cited cells. Valid sources s04 and s07 both have invalid applications. s04 repeats the demonstrated check with different prose; s07 uses another valid pair. Neither the manuscripts nor C35 upgrade this to a verified correct-source-to-application chain, independent discovery, a solved board, or Sudoku ACT.

3. **Context exposure is not misrepresented as internalization.** All 16 JSON transfer-note texts and hashes match their associated raw source outputs, including failures; recorded byte-span lengths also agree. For t02 the s02 note occupies `[966,1087)` and hashes to `8f52557fcc81cae0574c6cf984818063c5aa32ecfde606bd21dcf76d8279cdb8`. Parent/example/source-board exclusion outside the note is attributed to the supplied audit, not newly checked against full native prompts here. The manuscripts retain “parent-free but note-present” and teacher-derived ancestry. Absence of whole-example echoes is not converted into a discovery claim.

4. **Dose and cost are bounded correctly.** Audit explanation lengths are process six times 67 and twice 78 tokens versus eight times 57 for format. Prompt/output totals are 5637/652 versus 5536/648; embedded record output-token sums independently agree at 652 and 648. Same examples, calls, order and caps are not represented as matched token dose or compute. The protocol records one generation sampler seed 7101 and 32 calls; the terminal memo records zero fits. Audit elapsed `340.5489145469983` rounds correctly to **340.548915 controller seconds**. It is not measured GPU compute, independent audit timing, campaign cost, or an observed future fit budget. Preparation/audit are excluded. Native stop/token findings remain attributed receipt observations.

5. **Claims do not exceed evidence.** New material excludes learned persistence/internalization, P1/G5, H1/H2 establishment, generalization, causal parenting, joint retention and campaign closure. All 32 audit records flag lessons unverified and records unapproved for training. Citation correctness does not validate free-prose lesson truth. Source outputs are not repaired or retrospectively rescored into successful training material.

6. **Prospective and running work remain prospective and running.** All six files state Main has separately selected the bounded citation-supervision diagnostic, implementation is in progress, and no fits or outcomes exist in this evidence window. They explicitly say the audit is not a permission block on that selection. C35 distinguishes raw structural/citation-prefix supervision with masks from whole-lesson training. Planned caps are not observed work or utility. Cumulative work contributes no result claim. This review does not introduce any additional approval dependency.

7. **Custody language stays local.** The archived audit Markdown's actual SHA256 matches the digest reproduced in README/C35. JSON reports PASS, an empty failure list, 28 compared archive files and 515 passing checks. All 32 embedded raw-output SHA256 values recompute correctly. These are consistency checks on supplied local evidence, not a fresh capsule/native replay, model-origin authentication, global contamination certification or live cleanup check. This review did not independently establish the author's earlier comparison with the original `/tmp` audit copy; that remains an attributed historical action.

## Preservation and abstract checks

- Canonical `paper_prototype/main.tex` abstract is byte-identical to the parent commit. Its entire suffix beginning at `\appendix` is byte-identical. The canonical change consists solely of the two bounded SEQ091 paragraphs plus spacing; all pre-existing canonical content is retained.
- Canonical table inventory is unchanged: eight `table` environments and fourteen `tabular` blocks, each byte-identical to its parent counterpart. These counts are distinct from the companion's twelve table blocks.
- **All twelve companion table blocks are byte-identical:** eleven `tabular`/`table` blocks plus one `longtable`. No historical table result was reinterpreted in this review.
- Both companion abstract bodies contain **exactly 224 whitespace-delimited words**. After extracting the TeX `abstract` environment and Markdown `## Abstract` section, normalization by collapsing whitespace alone gives exact string equality; no substantive TeX transformations are required. Normalized abstract SHA256: `e324ba47b67d8881a679074f607d9676e00a295982d4feb4abcf817902f3c374`.
- All six files retain final newlines. No literal standalone `\n` escape artifacts are introduced; the prior newline correction is preserved by the source diff. Read-only `git diff --check` for the six-file commit comparison passes.
- The collaborator document remains explicitly UNSENT. No bibliography or new primary-literature claims are introduced by the scoped diff. Earlier results and broader scientific history were not re-audited.

## Small fixes

**Optional, low severity — qualify the blanket training sentence by artifact and authority.** Locations: `paper_prototype/main.tex:336`, `paper_prototype/README.md:346`, `paper_prototype/astra_sprint_draft_20260912.tex:1024`, `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:511`, and `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:20`.

“No output is approved for training” accurately reflects the demonstration audit, but in isolation could be read as contradicting Main's separately selected raw-prefix diagnostic. The subsequent explicit non-blocking language and C35's prefix/whole-lesson distinction already resolve it, so this is **not a blocking defect**. At the next ordinary prose cleanup, consider replacing that sentence only with:

> No complete output or free-prose lesson is training-approved by this audit; Main's separately selected citation-prefix diagnostic is prospective.

Do not alter the already exact 224-word companion abstract, scientific endpoints, historical tables, existing newline fix, or protocol authorization to address this optional clarity point. No edits were applied. No new run, review gate, or pause is requested.

## Exact file identities

SHA256 values below identify the exact reviewed file bytes, not abbreviated Git blob IDs.

| Assigned manuscript file | SHA256 |
|---|---|
| `paper_prototype/main.tex` | `42217a67fe953a8f54360c5117380b517fd687170359c69233b673e0b3b57280` |
| `paper_prototype/README.md` | `e588795e7ceef2f7cdd4e9b213ba4c11273bd45e1ecaac62e911e62fd12363c4` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `ef121bd5fec4bc147b0245e212fe7d28a0e833b945b0724f45208bb61bc09e63` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `9f201eee8823954a6606f96e9788cba087a273a4ccb5c1b4395ccf8be50adc03` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `38ee0a54db1e220277b1b55aeb1f46ce6611aca0422e127dd3b53319bda94ee3` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `36f1086364f15cf72414b39a83dce8060b9c50b83d92053f528497e85102b78d` |

| Evidence source | SHA256 |
|---|---|
| `research_notes/astra_memos/ASTRA_DEMONSTRATION_TERMINAL_2026-09-12.md` | `6a226cb4f823c67c981548f2b967ccea1d4f1e4ae409f2718fa6c08c10e7f839` |
| `research_notes/astra_memos/receipts_20260912/astra_demonstration_content_audit_20260912.md` | `77f758cec7b4e7fef77018f1ccbb28a491ce8bad56a569ebe95c972dd0e6730a` |
| `research_notes/astra_memos/receipts_20260912/astra_demonstration_content_audit_20260912.json` | `9ab41da28dd792461823a50af2901abc655ead72165387a5b387be4a614f60c6` |

Receipt-reported native report and capsule anchors agree between terminal memo, audit and C35: respectively `bd633642bbc6c1c67f1a1478a49f392c41a87c51ffb3fe8eecee506b2b60bfa5` and `b2d03d6b41c7211ac0c87ff177e590badb137cb2a9624abca4bc5749ac1d1417`. These two underlying artifacts were not independently opened or rehashed in this bounded review.
