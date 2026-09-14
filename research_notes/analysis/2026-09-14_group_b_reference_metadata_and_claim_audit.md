# Group B primary-reference metadata and bounded claim audit

Builder, September 14, 2026 UTC. Starting checkout
`736dd6142c435f27aeafc544a438ee49f00d8b59`; pull at 01:07 UTC was up to date.
This closes the 18 metadata flags, not the scientific manuscript review,
mechanism gates, source-contract blocker, or developmental campaign.

## Scope and responsibility

Huygens the 2nd independently inspected the first six entries; Curie the 2nd
inspected the next six. Both were read-only and returned primary sources and
claim limitations. Main inspected the last six and integrated their reports.
There was no mandatory bibliographic field correction: legitimate shortened
authors, first-submission years and conference years are retained. Only
comments in refs.bib change; main.tex is byte-identical. This is not an
independent second verification of every reference or the other 36 entries.

## Metadata disposition and primary sources

Each row checks the existing title, displayed authors/order, year and source
identity. Proceedings/journal claims are checked only where asserted; an
arXiv entry is not silently converted into a later publication. Source URLs
are locators, not immutable copies of the fetched pages.

| Existing key | Result and dating/author convention | Primary source locators |
| --- | --- | --- |
| cummins2023llmcompiler | Existing title, 11 authors and 2023 preprint match. | https://arxiv.org/abs/2309.07062 |
| zelikman2022star | Four authors and NeurIPS 2022 record match. | https://arxiv.org/abs/2203.14465 ; https://proceedings.neurips.cc/paper_files/paper/2022/hash/639a9a172c044fbb64175b5fad42e9a5-Abstract-Conference.html |
| gulcehre2023rest | Title, 14 authors and 2023 preprint match. | https://arxiv.org/abs/2308.08998 |
| singh2023restem | First three authors plus `others` is valid abbreviation; retain 2023 first submission. V4 author list and camera-ready page 1 separately establish TMLR April 2024. | https://arxiv.org/abs/2312.06585v4 ; https://arxiv.org/pdf/2312.06585v4 |
| anthony2017expert | Three authors and 2017 proceedings match; NIPS was the contemporary conference branding. | https://arxiv.org/abs/1705.08439 ; https://proceedings.neurips.cc/paper_files/paper/2017/hash/d8e1344e27a5b08cdfd5d027d9b8d6de-Abstract.html |
| huang2022lmsi | Seven authors and 2022 preprint match; separate EMNLP 2023 publication does not change this preprint year. | https://arxiv.org/abs/2210.11610 ; https://aclanthology.org/2023.emnlp-main.67/ |
| shumailov2024collapse | Nature title, six-author order, volume 631, pages 755–759 and 2024 match. The 2023 preprint has a different title and author order; do not overwrite journal metadata with it. | https://www.nature.com/articles/s41586-024-07566-y ; https://arxiv.org/abs/2305.17493 |
| alemohammad2023mad | Eight authors and ICLR 2024 match; arXiv supplies Richard G. Baraniuk's middle initial. Key's 2023 does not control conference year. | https://arxiv.org/abs/2307.01850 ; https://proceedings.iclr.cc/paper_files/paper/2024/hash/ebc042e767de551803ccfcc45e2454f5-Abstract-Conference.html |
| zweiger2025seal | Six authors, title and 2025 preprint match. | https://arxiv.org/abs/2506.10943 ; https://arxiv.org/html/2506.10943v2 |
| packer2023memgpt | Seven authors, title and 2023 first-submission year match. | https://arxiv.org/abs/2310.08560 ; https://arxiv.org/html/2310.08560v2 |
| sun2024ttt | Twelve authors, title and 2024 first-submission year match. | https://arxiv.org/abs/2407.04620 ; https://arxiv.org/html/2407.04620v4 |
| behrouz2024titans | Three authors and title match. First submission is December 31, 2024 at 22:32:03 UTC; retain 2024 despite identifier prefix 2501. | https://arxiv.org/abs/2501.00663 ; https://arxiv.org/html/2501.00663v1 |
| silver2025experience | Author preprint page 1 confirms title, David Silver/Richard S. Sutton and prospective MIT Press chapter status. Google DeepMind media-hosted PDF metadata has creation/modification `D:20250410153054Z`, corroborating 2025, not establishing the exact public-release date. No assertion that the book has now appeared. | https://storage.googleapis.com/deepmind-media/Era-of-Experience%20/The%20Era%20of%20Experience%20Paper.pdf |
| hu2021lora | Eight-author order and title match arXiv; ICLR 2022 designation retained, distinct from 2021 first preprint. | https://arxiv.org/abs/2106.09685 ; https://iclr.cc/virtual/2022/poster/6319 |
| qwen2025qwen25 | V1 full text explicitly names Qwen Team and lists members separately. Existing corporate author and 2024 preprint year are valid; key's 2025 is not a date field. | https://arxiv.org/abs/2412.15115 ; https://arxiv.org/html/2412.15115v1 |
| kwon2023vllm | Title, nine-author order and 2023 match; author PDF page 1 gives SOSP proceedings and DOI 10.1145/3600006.3613165. | https://arxiv.org/abs/2309.06180 ; https://arxiv.org/pdf/2309.06180 ; https://dl.acm.org/doi/10.1145/3600006.3613165 |
| madaan2023selfrefine | Title, 16-author order and NeurIPS 2023 match official proceedings. | https://arxiv.org/abs/2303.17651 ; https://proceedings.neurips.cc/paper_files/paper/2023/hash/91edff07232fb1b55a505a9e9f6c0ff3-Abstract-Conference.html |
| gou2023critic | Title, seven authors and ICLR 2024 match proceedings; 2023 key names initial preprint. | https://arxiv.org/abs/2305.11738 ; https://proceedings.iclr.cc/paper_files/paper/2024/hash/ed7bfcd111f5c5741bf381a9f4f5b4ae-Abstract-Conference.html |

Main's shell arXiv fetch for Qwen/Self-Refine/CRITIC returned HTTP 429; those
failed fetches are not evidence. Primary browser records/full text and official
proceedings supplied the metadata instead. Silver PDF page 1 and metadata were
read successfully through urllib/pypdf. The ACM landing page returned HTTP
403; vLLM's author PDF supplied its proceedings reference instead. No
curl/wget retry or approval request.

## Advisory claim findings — unresolved, not silently edited

These are prior-work interpretation issues. No local run, mechanism or
scientific claim is promoted or changed by this pass. The existing manuscript
is still an unreviewed working draft; clearing metadata flags does not clear
the following findings.

1. **High priority: TTT/Titans lifetime** (`main.tex:2278`). The phrase
   “last one context window” is not an adequate universal description. TTT
   sections 2.1/2.7 describe per-sequence adapted weights; Titans v1 section
   4.1 carries neural memory across attention segments. Its input-independent
   persistent parameters are also distinct from online neural memory.
   A sequence-processing versus cross-episode evaluation distinction needs
   careful wording. The third paper grouped in that sentence was not audited.
2. **High priority: SEAL prior art** (`main.tex:2278`). V2 sections 3/5 and
   Figure 6 describe generated self-edit data/directives and sequential edits
   with forgetting measurement. “Static tasks” must not imply absence of
   sequential persistent adaptation. Repeated writes alone are not a supported
   novelty distinction. Fixed success filtering versus learned self-editing
   remains a narrower design comparison, not proof of project novelty.
3. **Causal limitation: collapse analogy** (`main.tex:497,2280`). Shumailov
   and MAD study recursive-data degradation; MAD's empirical models generate
   images. Neither identifies the cause of this project's recipe lock-in.
   Fresh frozen-base samples are not fresh real data. Proposed mitigations
   remain unablated. Any common-mechanism interpretation needs explicit limits.
4. **Distinction risk: ReST-EM** (`main.tex:264,2280`). V4 already restarts
   fine-tuning from the original model; base restarting alone cannot distinguish
   this project. Supervised training on reward-filtered data is not
   reward-independent. Correctness filters, learned rewards, majority agreement
   and search-derived expert targets must not be treated as identical.
5. **Attribution limits** (`main.tex:301,2283,2286`). MemGPT supports an
   external context-management comparison, not local row/budget details.
   Cummins supports LLVM pass-ordering/instruction-count work, not an identical
   benchmark. Self-Refine and CRITIC support feedback/refinement neighbours,
   not amortized parenting efficacy. Qwen/LoRA/vLLM sources identify machinery;
   they do not authenticate the deployed revision, adapters or local runs.
   Silver/Sutton supplies conceptual motivation, not evidence for this sprint.

These findings require disposition in the manuscript review/claim map before
submission. The canonical prose and thesis remain untouched in this bounded
pass. Reserved scientific-claim changes still belong to Rohin.

## Validation and campaign boundary

Structural receipt:
`research_notes/astra_memos/receipts_20260912/astra_group_b_metadata_20260914_attempt1.json`.
At 01:09:56 UTC the check passed: all 54 entry bodies are identical after
comment stripping, all 54 cited keys resolve, there are 18 metadata annotations
and no pending VERIFY annotations, and main.tex is byte-identical against
starting HEAD. Receipt SHA256:
`2be2962f201a988f674dac1b3b4c98339ab5d81a994d2581301348628e438df1`.
refs.bib SHA256:
`45776a608c2e88e6af0c8f5e1ccc1339951363283a2dbe4897fba54673b79e3e`.
main.tex SHA256 remains
`614a71a3173c5feb7191f1817a1c2aa8f769a30a12213b8054ed8a4a73852d03`.
No pdflatex, bibtex or tectonic executable was found. This is not
a TeX/BibTeX build, rendered layout test, or full 54-reference claim review.

The actual next experiment remains source-derived Stage2A inventory/bounds,
separate material/native opening, reduced BASE/D1 560-slot screen, then
qualified authentic two-SLEEP work. Missing registered-route membership and
core depth/recovery semantics remain source-owner questions. No fabricated
inventory, new GPU run, Q0 retry, formal C11 enforcement or node-1 write occurs.
No scientific SEQ result is earned by this documentation-only audit.
