# Independent manuscript review — SEQ130–133 / C74–C75

Review date: 2026-09-13 UTC. Timeboxed review of the working-tree diff and relevant surrounding text in the six requested manuscript files only. Main owns integration; Galileo's concurrent work was not modified. This report is the only file written. No repository/Git mutations, network access, launches, GPU tests, native replay, or TeX build were performed.

## Disposition

**Bounded numerical/scientific incorporation is supported; fix the current-abstract provenance ambiguity before integration.** One medium-severity scientific-status ambiguity and two low-severity editorial issues follow. No new unsupported causal promotion, endpoint-denominator error, or broken TeX environment was found in the inspected additions. This is manuscript review, not independent raw-response rescoring, implementation certification, mission completion, or negative-paper finalization. Collaborator remains **UNSENT**.

## Findings and smallest fixes

### 1. MEDIUM — Historical unresolved base pin reads as a current status inside both updated abstracts

- Exact locations: `paper_prototype/astra_sprint_draft_20260912.tex:200–201`; `paper_prototype/astra_sprint_abstract_20260912.md:323` (the long paragraph's final two sentences).
- Wording: “Source is NOT CLEAN and official base revision unresolved.” The new SEQ133 paragraph immediately follows in the same active abstract (`astra_sprint_draft_20260912.tex:203–215`; companion Markdown `:325–337`), without marking that provenance sentence as historical.
- Why it matters: the same files separately document prospective public-revision matching for the checked node3 snapshot: Markdown `:113–116` and sprint TeX `:2716–2729`, revision `a09a35458c702b33eeacc393d103063234e8bc28`. Historical receipt labels remain unchanged, but they are not interchangeable with the later prospective file-binding status. The current abstract can therefore be read as denying the already-described scoped public binding. Conversely, simply changing it to “official base verified” would overclaim all-node or retrospective identity/clean ancestry.
- Smallest fix in both abstracts: replace only that sentence with **“At the historical birth/formation cut, source was NOT CLEAN and official base revision was unresolved. Later prospective file matching is limited to the checked node3 snapshot; historical receipt labels and clean-ancestry limitations remain unchanged.”** Preserve the surrounding negative qualification and formal C11 deferral. An explicit reference to C69 is sufficient; do not rewrite or relabel historical receipts.
- Scope note: the sentence predates these additions, but extending this active abstract through SEQ133 makes its unqualified present tense an integration issue. Historical sections with explicit historical headings do not need blanket replacement.

### 2. LOW — Unqualified “canonical abstract is unchanged” contradicts the actual canonical abstract diff

- Exact location: `paper_prototype/astra_sprint_abstract_20260912.md:318`.
- Wording: “Internal staging only; the canonical abstract is unchanged.” This standalone status immediately precedes `## Abstract`, while `paper_prototype/main.tex:57–66` now adds the Q0/reflection findings inside its abstract.
- Smallest fix: **“Internal staging only; the canonical abstract now includes the bounded SEQ130–133 update while preserving its historical text. H1/H2 remain the proposed developmental thesis, not established outcomes.”** Alternatively, explicitly date this entire sentence as historical. No change to the thesis or historical estimates is needed.
- Do not globally replace analogous statements inside clearly dated historical records; those describe earlier revision states.

### 3. LOW — Missing word/number spaces survive into rendered manuscript prose

- Representative exact locations: `paper_prototype/main.tex:57–63` (“complete128”, “are71/70”, “from7/12”, “adds0,0,-1”); `paper_prototype/astra_sprint_draft_20260912.tex:206–212`; `paper_prototype/astra_sprint_abstract_20260912.md:328–334`; `paper_prototype/README.md:20–22`.
- Scientific values remain correct, but ordinary text will render these as joined words, unlike notebook shorthand.
- Smallest fix: insert ordinary spaces at prose word/number boundaries in the new paragraphs only, e.g. “from 7/12 to 9/12” and “adds 0, 0, -1”. Do not touch hashes, identifiers, raw receipts, or historical tables. This is copyediting, not a numerical correction or TeX compilation blocker.

## Evidence checks that passed

- **Q0 against notebook SEQ132** (`research_loop/COORDINATION.md:9551–9566`): R0 AUTH/DERANGED exact 71/128 and 70/128, held 37/64 and 31/64; R2 exact 65/128 and 72/128, held 31/64 and 32/64. Complementary double-correct counts are R0 39/128 exact and 10/64 held; R2 28/128 and 4/64. Each completed-instance fit has 128 updates; copy is 8/8 per arm. The additions consistently distinguish completed endpoint failures from R1's missing final paired endpoint/runtime abort, and do not substitute zero accuracy or an n=3 scientific failure rate. Root and learner seed are explicitly confounded.
- **Reflection against the requested frozen report and notebook SEQ133** (`research_loop/COORDINATION.md:9568–9586`): each cell has denominator 12 per seed. OFF withdrawn 7,7,7; OFF present 9,9,9; ordinary withdrawn 9,9,9; ordinary present 9,9,9; correction-fit withdrawn 9,9,8; correction-fit present 7,7,7. The six-cell tables and prose agree across the inspected additions. Seed0 is included once, not added to the three-seed total.
- **Meaning/denominators:** all 216 application outputs are syntax-valid; ordinary withdrawn improvement is +2/12 per seed, not perception-style format rescue. Incremental correction versus ordinary withdrawn is 0,0,-1. Separate restatement scores are 0/12 in every cell/seed and `semantic_prose_score` is null; no semantic-prose failure follows. The manuscript distinguishes 216 application and 216 restatement responses, 432 total, from independent learners and from any combined score.
- **Inference limits:** no population null, general LoRA impossibility, identified causal mechanism, parenting benefit, child-authored SLEEP, P1/H2, clean ancestry, or C11 qualification is promoted by these additions. Correction user-message exposure is distinguished from the perception system anchor; matched targets are not called matched input exposure. Preselection is supported by the notebook statement and manifest declaration, not independently timestamp-certified by this review.
- **Boundary/status:** additions exclude L2 and supplemental-readout outcomes, preserve the ongoing-working-draft framing, leave the research question unresolved, and retain collaborator UNSENT. Existing historical supplementary material is not a newly imported supplemental-readout result.
- **Repair provenance:** report SHA256 matches the C75 citation exactly. The v1/v2 explanation preserves the failed attempt and separates original/copy byte pins from decoded identity. Main's reported CPU acceptance is not misrepresented as this independent scientific review or native model verification.
- **Static TeX inspection only:** both TeX files have balanced, correctly nested `begin`/`end` environments; added-line braces balance without negative nesting. New Q0/reflection table structure is conventional and no broken environment was detected. No PDF compile, pagination, overfull-box check, or layout approval is claimed.

## Evidence and snapshot binding

Requested report: `research_notes/astra_memos/receipts_20260912/astra_reflection_three_seed_report_20260913_attempt2.json`.

Verified SHA256: `42aed54229f515540fb878a4610597195fa84e26b4df9dfd8db97de8c284433b`.

The report explicitly limits its own scope to byte custody and unchanged CPU metrics, not native token reencoding, weight deserialization, model ancestry recertification, or independent timestamp certification of preselection. This review does not upgrade those limits. Extra Q0 gate/key detail beyond the notebook's aggregate statement was checked for cross-file consistency, not independently replayed from Q0 raw receipts.

Working-file SHA256 values sampled during review (concurrent later edits require rechecking affected findings):

| File | SHA256 |
| --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `0d220d7a621545d548034a6546ffc8acd9875c6047893e928b30241d591b1d88` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `88e8f0540ed69d1069c3dc0c01c66f11ecfede815d480bf81395de05ea3d563d` |
| `paper_prototype/main.tex` | `3d938c6da8df5d129d5403b9daf8d8957a7ce6b471d14153e02e9a3ab934ce3b` |
| `paper_prototype/README.md` | `7c22d47274f9577f9a35df9440c41bd0f8826dbfd1b8b2994c075039429ba84f` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `a9f7ca12c1189998800ac1e29539ff99c0a4c8d34e8c2aadbdb90ddf16719317` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `68b42f84b531c4ffb7691140e68521ad25e6fc4bd98dd582cefef491628e82cf` |

Main should apply the smallest scoped prose fixes; this review does not authorize external sending, scientific promotion, or finalization.
