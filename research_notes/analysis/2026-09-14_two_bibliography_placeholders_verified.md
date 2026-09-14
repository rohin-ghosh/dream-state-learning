# Two bibliography placeholders resolved against primary papers

Builder, September 14, 2026 UTC. Citation metadata repair only; no experiment,
result, abstract or project-claim change. Work proceeded while the current
Stage2A route/core source definitions remained unanswered.

## Inspected primary sources

1. Auto-Dreamer: arXiv2605.20616v1, submitted May20,2026. Abstract metadata
   and version1 full text, especially sections2.1 and4.3, verify the title,
   ordered authors, preprint identity, external memory bank and the use of
   downstream task reward to train its offline consolidator. This supports
   the existing narrowly descriptive related-work clause, not the project's
   novelty or a general claim that consolidation improves performance.
   Sources: `https://arxiv.org/abs/2605.20616v1` and
   `https://arxiv.org/html/2605.20616v1`.
2. Useful Memories Become Faulty When Continuously Updated by LLMs:
   arXiv2605.12978v2, first submitted May13,2026 and revised August29,2026.
   Abstract metadata and version2 sections2–3 verify the ordered authors,
   title and study of repeated text-memory consolidation. Reported degradation
   below a no-memory baseline supports the existing literature statement.
   It does not establish the cause of this project's parametric degradation;
   the cross-system comparison remains an analogy, not causal identification.
   Sources: `https://arxiv.org/abs/2605.12978v2` and
   `https://arxiv.org/html/2605.12978v2`.

Both are cited as versioned arXiv preprints. No conference acceptance or
peer-review status is inferred. Only these two references were fact-checked
in this pass; earlier bibliography verification claims were not inherited as
newly proven.

## Exact repair and validation

Russell owned only `paper_prototype/refs.bib`: two new entries,
`ye2026autodreamer` and `zhang2026faultymemories`, plus their stale TODO
comments. Main changed only the corresponding two keys in
`paper_prototype/main.tex`. Its remaining bytes, including results, abstract,
tables and author intent, are unchanged. Current README status is updated;
dated historical review records are not rewritten.

Main's structural check at September14 00:57:22UTC establishes:

- 54 unique bibliography entries; all52 previous entries preserved exactly.
- 54 citation commands and54 unique cited keys, with no undefined/TODO cited
  keys in main.tex.
- Exactly the two intended TeX key substitutions and no other TeX edits.
- All18 existing `% VERIFY` annotations remain unchanged and unresolved by
  this pass; the old review's count of16 is not the current annotation count.
- Balanced entry boundaries and no duplicate keys; diff whitespace checks
  pass. Russell also checked full braced-field syntax independently of Main's
  key/preservation assertions.

Receipt: `research_notes/astra_memos/receipts_20260912/astra_bibliography_two_refs_20260914_attempt1.json`,
SHA256 `967086a3e30cc283896bf80054189ecc7a8956ce3221b6a5695d600b2581828e`.
refs.bib SHA256 `8dcc534f036ef568c02cde17bc3f16f48cc23bb3225fcdcb728e2fddc0780fd9`;
main.tex SHA256 `614a71a3173c5feb7191f1817a1c2aa8f769a30a12213b8054ed8a4a73852d03`.

No pdflatex, bibtex or tectonic executable is available here. These checks
are not a rendered PDF, a BibTeX build, layout certification or a complete
reference audit. No dependencies were installed or experiments launched.
Russell is closed. The full campaign remains active and incomplete; remaining
reference checks are legitimate independent work, not a substitute for the
blocked controller and authentic two-SLEEP experiments.
