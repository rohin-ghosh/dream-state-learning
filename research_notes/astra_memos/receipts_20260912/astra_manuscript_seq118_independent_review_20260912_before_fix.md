# SEQ118 six-file manuscript review — NEEDS FIX / EDIT-STOP

**Scientific/custody consistency: PASS. Overall disposition: one concrete TeX source correction required.** No scientific claim, count, historical-status update or additional experiment is requested. The six manuscripts were not edited.

## Required correction

**`paper_prototype/astra_sprint_draft_20260912.tex:129`: escape the newly introduced text-mode underscore.** The companion abstract currently contains `NEW_ONLY`; replace that token with `NEW\_ONLY`. The document uses ordinary LaTeX text mode here, with no underscore package or catcode override. A bare underscore is a math-subscript token, causing a LaTeX text-mode error rather than reliably rendering the intended arm name. This is a source-syntax defect, not a preference about typography. The rest of the new TeX section already uses `NEW\_ONLY`.

This one-token escape preserves the abstract's displayed text, **225-word count** and normalized Markdown/TeX parity; no Markdown prose change is needed. Banach should refresh the affected final hash and reversible diff in the handoff after the repair. This review binds the current bytes below, not an unseen repaired version. No TeX engine was run; this is a static syntax finding, not a claim about a completed compile/PDF or other compilation errors.

## Verified scope and custody

Read `/tmp/astra_manuscript_seq118_handoff_20260912.md`, which explicitly declares EDITSTOP. Handoff SHA256: `ccf30b4e807a69f27fe64881acca48d24917ffb39490b7138ad7f5ae87d1e7de`.

Compared every baseline/final file against its handoff hash and every embedded unified diff against a freshly generated in-memory diff. All six diffs reconstruct the current file forward and its exact backup in reverse. Backup root: `/tmp/astra_manuscript_seq118_backup_20260912_pkhmkmim`. All six current hashes remained unchanged at the final read. No Git commands were used: the claimed Git baseline `b06a2750` remains Main's statement; this review verifies the exact supplied backups, not the commit independently.

| File | Verified current SHA256 |
|---|---|
| `paper_prototype/main.tex` | `da02ed9ed93f6c404e1f1f4b73765cddb94e71853b902ea89524261517f276a4` |
| `paper_prototype/README.md` | `83f26fd5073d5a907b71fc7a3f86c79f6e1e29d10f8b0d6a5c56c645024c56cb` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `40f270faffd17fdbada083daeb965dcd7951ef0deb3ec654b2cef9ebab7ac1e5` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `09b680aac43929057a7ee668eb509a7532e360e5917c56fc4e978a2185602681` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `af1d573dd04ea530f8a83aa17c3cfa872dce25963ae616ca388b459a4dcfbdb6` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `630482de130ef661fdcd6f73c22f4a8572baaa63d503ee6cb120620ea57f7b87` |

All six evidence-file hashes listed in the handoff match: the canonical Main memo (`396e825a…`), accepted raw review/JSON, custody addendum, archived capsule (`c63437c4…`) and external validation (`10cfd0e1…`). Archived raw-review/JSON/addendum copies equal their accepted `/tmp` counterparts byte-for-byte. The external receipt's availability is correctly incorporated; no native or 640-call scoring rerun was performed for this manuscript review.

## Scientific and accounting consistency

**Counts and baselines pass.** Independently compared all SEQ118 table cells in the companion TeX, README and claim map with the accepted raw-analysis JSON; checked corresponding narrative summaries in the remaining files. Table convention is **dev/exact**, each count /16, unlike the raw review's exact/dev presentation:

| State | M0 dev/exact | B1 dev/exact | B2 dev/exact | Habit /32 | Correct ACT /32 |
|---|---:|---:|---:|---:|---:|
| S0 | 16/16 | 5/5 | 7/6 | 32 | 32 |
| R1 | 16/16 | 16/16 | 5/6 | 32 | 32 |
| NEW_ONLY1 | 10/8 | 16/16 | 5/4 | 32 | 32 |
| R2 | 16/16 | 16/16 | 16/16 | 32 | 32 |
| NEW_ONLY2 | 9/8 | 4/4 | 16/16 | 32 | 32 |

- **Endpoint interpretation:** `paper_prototype/astra_sprint_draft_20260912.tex:2268`, `paper_prototype/astra_sprint_draft_20260912.tex:2289`, `paper_prototype/main.tex:408` and claim map `:2432` correctly distinguish already-trained S0 from OFF and untrained B1/B2 baselines from acquisition. Both cycle1 B1 endpoints are 16/16; NEW_ONLY2's subsequent 12-fact loss is observed retention loss, without making the differing training histories equivalent. M0's unchanged exact total hides four recoveries/four new failures. All 480 color outputs remain valid; arithmetic correctness and PREDICT-before-ACT adherence are both intact, not conflated with formatting alone.
- **Recipe and estimand:** companion `:2320`, canonical `:410` and claim map `:2470` correctly identify **single-question current training**, despite the FOUR400 ancestor. Same S0 forks, fresh seed0 optimizers and own-parent cycle2 continuation yield 400→720→1040 updates. Per-fit 66,160 input/10,000 target/76,960 padded slots match, but R current-new20 versus NEW_ONLY40 does not match new-fact dose. R2 versus NEW_ONLY2 is a trajectory comparison, not a common-parent cycle2 intervention; one-seed/two-cycle scope, M0 primary/B1 separate and repeated-fact dependence are preserved. No general G3, parenting, H1/H2, latent-erasure, clean-lineage or freeze promotion appears in the new claims.
- **Timing and supplement:** companion `:2333`, companion `:2342`, claim map `:2502`, README `:20` and canonical `:410` correctly use **September 12, 2026 UTC**, regardless of September13 filenames: launch23:35:40.672863, terminal23:57:16.712009, release XML23:57:44 and derived observed vacancy23:57:48.133511. The 1,327.460648 seconds / 22.124344 A40-min is launch-to-observed-vacancy, **not complete packaging/validation**; nested worker/controller/generation intervals are not added. The available external receipt supersedes only the earlier availability caveat and supplies no final-packaging timestamp. Excluded weights/native execution/origin remain receipt-backed, as required.

## Preservation and historical cut

- The original `main.tex` abstract is byte-identical to backup. Its prefix before the C61 paragraph and its entire Discussion-through-end are unchanged. All prior tables are preserved: canonical eight table/14 tabular blocks; companion 24 table/30 prior tabular/one longtable blocks (two new tabular blocks added); all prior Markdown tables remain verbatim in README and claim map.
- The companion abstracts at `paper_prototype/astra_sprint_draft_20260912.tex:122` and `paper_prototype/astra_sprint_abstract_20260912.md:187` normalize to identical **225-word** text, below250. The source escape repair above is still necessary despite that textual parity. The opening developmental question remains; earlier process full-criterion failure and historical results are not promoted or rewritten.
- `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:1` and `:3` retain **DRAFT ONLY / UNSENT**. Companion `:2352` and claim map `:2523` explicitly mark a **supplied planning cut, not live birth status**. Main's subsequent report of 133 birth tests/native-audit PASS does not invalidate that historical snapshot and requires no retrospective rewrite. No later GPU outcome is imported here, and this review does not independently verify the subsequent implementation status.

## Reviewer limits and handoff

I authored the underlying SEQ118 raw review and custody supplement, and older related replay/helper/audit code; I did not author these six manuscript edits. This is an independent check of Banach's integration against already accepted evidence, **not new independent native evidence or a blinded/fresh-author raw audit**. Findings are limited to one introduced source-syntax correction; no cosmetic or historical-status rework is requested. Only this assigned review file was written. **EDIT-STOP pending the owner-side escape/hash repair.**
