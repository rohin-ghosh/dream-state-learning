# Independent scientific review — companion sprint drafts

**Disposition: scientifically cautious internal staging draft; no high- or medium-severity finding in the checked claims. One low-severity wording correction.** This is advisory documentation review, not scientific qualification, human ratification, canonical integration approval, or a gate on main's experiment repairs. Nothing here requests delaying a repair or experiment.

## Scope and exact version

Read-only review began **2026-09-12 09:42:16 UTC**. Final whole-file snapshot reads below occurred **09:44:58.537553–09:44:58.537729 UTC**; all four hashes match the initial inspection. Conclusions bind only these bytes, not subsequent Nash edits. The claim-map basename in the request resolves to `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md`; no root-level counterpart exists.

| File | SHA256 at final snapshot read |
|---|---|
| `paper_prototype/astra_sprint_draft_20260912.tex` | `21f3efadc00e5858db6d3dc387a0e9a903be54e93d9c4fbb5aab987f1b660f49` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `2efada69a3abf987c07532db50c77b0c8ea6c9dffca8703b3b94863a36f08a36` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `fa7907ef1df7ecde1e097f5538be88cf76114a1145a8328f169b70557386b052` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `07989a532740e87893da3351b5a2f5b7893665b88d758ecc698be6714cf7c2f4` |

Evidence cut: SEQ-062–068 plus the unnumbered **09:38 UTC** notebook entry, not a newly completed P0 reducer/archive. Only local file reads, hashing, and in-memory text/arithmetic checks were performed. No experiments, model calls, test suite, producer/replay/reducer execution, Git, remote access, resource actions, or external messages. The sole written artifact is this review.

## Finding requiring a minimal wording correction

**LOW — ambiguous comparator denominator.** `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:13` says “previous single-row32/58.” Those are two different counts, not a 32-of-58 accuracy denominator. The surrounding paragraph is otherwise correct, and line 12 already supplies the proper denominators. Evidence: `research_notes/astra_memos/ASTRA_ORACLE_LOOKUP_2026-09-12.md:14` and `research_notes/astra_memos/ASTRA_GROUNDED_COPY_2026-09-12.md:9`. **Minimal correction:** replace that phrase with “previous single-row: 32/64 correct and 58/64 valid.” No numerical change or rerun is needed.

## Numerical and scientific checks

- **PASS — 15 artifacts, not seeds.** TeX lines 124–149 and 250–285 match the SEQ-062 adjacent JSON for the first 12 banks and SEQ-067 archived `analysis.json` for the last three: **all 60 displayed numerical values** round correctly. Fifteen distinct family/optimizer-seed/bank rows span five configurations; every spill exceeds 0.03 and only A1 seed 3 bank 0 lacks a positive binding lower bound. SEQ-064 bank 0 is not double-counted. The 16-owner bootstrap is correctly distinguished from optimizer-seed uncertainty and A1/A2 source confounding. Evidence: `ASTRA_A1A2_BANKS_2026-09-12T080020Z_READONLY.md` and `ASTRA_A2_SEED2_TERMINAL_2026-09-12.md`, under `research_notes/astra_memos/`. Correction: none.

- **PASS — W0 invalid, not qualified negative.** TeX lines 289–299 preserve both distinct failures: unusable oracle and failed seal/replay. Four fits, ten evaluation phases, 1,024 steps, 1,504 requests and rounded 0.471781 A40-hours agree with the custody memo/notebook; 3,160/3,161 sealed files matched and replay exited 2. Four oracle groups of 64 all truncated with zero legal ACT are explicitly supplemental observations. Evidence: `research_notes/astra_memos/2026-09-12_W0_terminal_custody_0818Z_capture_0824Z.md:5`, `:11`, `:23`; `research_loop/COORDINATION.md:2633`. Correction: none; do not promote calibration to W0 rescue.

- **PASS — calibration and actual paired follow-up.** TeX lines 305–343 reproduce all seven diagnostic rows from the interface-calibration, lookup, and grounded-copy memos. Recounting the 64 archived actual-pair records gives correctness transitions 32 correct→correct and 32 incorrect→incorrect; validity transitions 32 valid→valid, 26 valid→invalid, 6 invalid→invalid. Raw grounded outputs are 32 `ACT: a1`, 31 `ACT: a a`, one `ACT: a`. Both archived original-source replay receipts report exit 0. These are inspected development observations without training/adapters, not independent learner replication or a corruption diagnosis. Correction: only the collaborator shorthand above.

- **PASS with source-resolution limit — historical 4/9 versus 3/9.** TeX lines 225–237 and collaborator line 21 distinguish ever-harm (seeds 2/3/5/6) from last-probe harm (2/3/5). Nine local R2 life means recompute to **0.0194444444, SE 0.0111192165**, supporting +0.019/0.011. Ever-harm is reproducible from local life summaries. Seed 2's last value is stored rounded to −0.0300, so the strict-threshold last-probe count cannot be independently recomputed from those rounded series alone; the three-life count and boundary explanation are supported by `research_notes/EVIDENCE_TABLES.md:59` and `paper_prototype/README.md:141`. The drafts disclose that boundary; no correction required. Do not replace the source count with a new threshold applied to rounded data.

- **PASS — other historical contrasts remain bounded.** TeX lines 233–248 match canonical/source-audit values for disjoint final gains −0.017/+0.003/−0.010 and n=9/6/7, the nine-life static factorial .2528/.2382/.2570/.2424, and age-matched brief-minus-A +.00464/−.00405. The near-zero factorial interaction is attributed to unrounded inputs, not inferred from rounded table entries, and is not called H2. Evidence: canonical abstract and `research_notes/2026-09-11_brief_adapter_matched_2x2_audit.md`. Correction: none; this check is source agreement, not new replication.

- **PASS — P0 zero observed records, not population zero.** TeX lines 353–402, abstract lines 7/14–15, collaborator lines 15–19/25–30, and claim map C08 agree with `research_loop/COORDINATION.md:2745`: 64 episodes each; lesson 1,913 records/1,903 measured ACTs; sham 1,632/1,627; zero grounded/unique grounded records. Listed rejection counts plus two lesson action mismatches reconcile exactly to 1,913/1,632, and subtracting unmeasured 10/5 recovers measured ACT totals. These checks validate transcription/arithmetic, not the pending full schedule-level reduction. No population-zero interval or general learning-failure claim is made. Correction: none.

- **PASS — actual paired SKIP, no fits/adapters/probes.** Receipt `research_notes/astra_memos/receipts_20260912/astra_P0_pipeline_prepare_20260912.json:1` reports `PAIRED_SKIP_INSUFFICIENT_MATERIAL`; both arms have available/selected 0, required 64, and `training_executed=false`. The notebook at line 2747 explicitly confirms no fit, adapter, or neutral probe launched. Named adapter/log/probe configuration paths are not misreported as products. Missing loss/probe scores are not filled with zeros. Correction: none.

- **PASS — dose confound and unproven hypotheses.** TeX lines 165–199 expose **203 versus 158 teacher tokens, difference 45 per presentation**, consistent with notebook line 2653, without treating earlier 667/622 prompt heads as realized final exposure. Repeated dose and actual token accounting remain pending. H1/H2 stay proposed, no semantic-parenting effect is isolated, and the static carrier factorial is not substituted for the adult-learning interaction. Correction: none; retain these qualifications when new counts arrive.

## TeX, citations, and completion boundaries

**No obvious undefined TeX command found.** All **40 control words** are supplied by standard LaTeX, the declared packages, or local `\ev`/`\pending` definitions. Escape-aware braces and environment nesting balance; table references resolve; the source contains no non-ASCII characters. The title's `\texorpdfstring` is covered by `hyperref`. `pdflatex`, `latexmk`, `tectonic`, and `bibtex` are absent. **No compile, layout/overflow assessment, or page-count certification is claimed.** Minimal next correction: none at source level; compile later in a separate authorized build location.

The three citation keys/bibliography items at TeX lines 527–543 match the existing `refs.bib` identities for SEAL, TMEM, and MemSkill and the supplied `/tmp/astra_writer_literature_20260912.md` primary-verification register. Titles, author lists, years, arXiv identifiers and stated read versions agree locally; no conference acceptance or invented venue is asserted. This is **local verification against the supplied register**, not new web authentication or an exhaustive literature review.

The two abstract bodies match exactly after whitespace normalization and currently contain **174 whitespace-delimited words**. Claim-map line 182's 194-word validation is explicitly historical under line 186, not a claim about this revision; no discrepancy requiring correction.

**INFO — retain pending status, not a publication or experiment blocker.** TeX lines 15–25/491–525 and collaborator line 38 correctly state that complete paper sections do not complete the canonical manuscript, G5/G6, or outreach. Full P0 frozen paired reduction/accounting/archive and a new SEQ remain pending at this evidence cut. CPU readiness is nowhere promoted to fresh scientific evidence. Later evidence must be bound to its own sources and draft hashes; this review does not pre-approve future edits. No manuscript rewrite or change to main's repair workflow is recommended.

## Custody checks and review limits

All six archive digests listed in claim-map C12 were independently rehashed and matched. Selected archived analysis/actual-pair/replay-receipt JSONs were read in memory; full payload manifests and model inference were not replayed. Models remain unbundled and official model-origin authentication unresolved as the drafts acknowledge.

- Actual P0 preparation JSON SHA256: `d007eb7d54af4d238c4c3201b865b83dd5df23ff36f489a1f37831f6d6eb0927` (matches C08).
- Read 09:38 notebook section, starting line 2743, SHA256: `63263525f03d1038676c5119179af8ce66669afd8ab23b1db205031bca4a2592` (section text through the next heading or EOF).
- Supplied literature-verification record SHA256: `28dff2694b854415c1e1e141ca7327a0296652482b725c2d10bedbf8d66403da`.
- Canonical `main.tex` SHA256: `3eccc364ce4a8639b5e156f443f55eebc70fcdc7567b2bc171f5ff6c12b0f983`; `refs.bib`: `56ffd9d4f4dd306e5a0185f445857e100d813d32860b966a55844517b8b92489`. Both match the claim map's preservation baseline. Neither was edited.

This bounded review checks the requested numerical/scientific boundaries and obvious TeX/citation issues, not every implementation claim, all historical raw data, or manuscript readiness for external submission.
