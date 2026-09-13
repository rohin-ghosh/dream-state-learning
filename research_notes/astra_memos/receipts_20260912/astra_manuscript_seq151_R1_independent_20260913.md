# Independent addendum — SEQ151 R1 terminology correction

Date: 2026-09-13. Scope: R1-only byte verification, not a new scientific-evidence review.

## Verdict

**PASS — R1 resolved.** The three changed files contain exactly the requested terminology edits; the other three manuscript files are unchanged. The prior bounded acceptance now applies to the exact six hashes below, together with all limitations and pending claims in the original independent review. No additional correction is required for this narrow scope.

For precision, “three changes” means **three changed files**: three abstract substitutions plus two definition insertions, five textual edit sites in total. There are no other byte changes relative to the independently accepted versions.

## Bound inputs

- Original independent review: `/tmp/astra_manuscript_seq151_independent_review_20260913.md`, SHA256 `e37c7a1d30276c7be10e2f0b2d3ca63b49d0f51d5408452e0fa53ef8fd9cb039` (independently rehashed).
- R1 handoff: `/tmp/astra_manuscript_seq151_R1_handoff_20260913.md`, SHA256 `1369b425f865d305a785984fd3da19ddda16761a6fb548dc2d994a8b5f79a482` (independently hashed).

## Exact edit verification

| File | Verified edit sites | In-memory inverse SHA256, matching prior accepted bytes |
| --- | --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | Line 286: the SEQ151 abstract changes `first-token` to `first-divergent-token`; line 3480: the definition below is inserted immediately after the C87 table's closing center environment. | `c4de532df058717ecda12f229afdca2ffcbc574d51a26f17d6f18cd496b673bc` |
| `paper_prototype/main.tex` | Line 127: the same abstract substitution; line 1241: the same definition immediately after the C87 table's closing center environment. | `53a0bd572955b77e6d4524eeaec9388d4a0189dd13df828e474dfe0dfd1383e5` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | Line 416: the same SEQ151 abstract substitution only. | `6bc9e9a21766610e4d1bc4d2fdf7d751fe775b9b4e81a108c4d6c4ebe3f9578c` |

Exact inserted sentence, once in each TeX file:

> First denotes the first divergent candidate token after the shared two-token prefix.

Method: read current file bytes, require exactly one full-line abstract replacement in each changed file, require exactly one definition in each TeX file and none in the abstract companion, verify the table-adjacent placement, then reverse only those edits **in memory**. Each resulting hash equals the corresponding prior independently accepted hash. Independently generated inverse-to-current diffs agree with the handoff. No old file version was written to disk or restored in the repository.

The hash reversals establish that no counts, table values, sources, pending-status language, or claim boundaries changed. Direct hashes establish that README, claim map, and collaborator draft are byte-for-byte unchanged. The three revised SEQ151 abstract paragraphs remain byte-identical, as do the two revised TeX SEQ151 result sections. Scoped `git diff --check` passes for the six files; that check is supplementary, not the baseline for the inverse proof.

## Exact six-file acceptance binding

Main may use this table to check the intended six-file staging scope. This reviewer did not stage anything. Acceptance does not extend to any subsequent differing bytes.

| File | Disposition | SHA256 |
| --- | --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | New R1 bytes accepted | `591358e95783ef63eac16d4565d4a98eae47e1f8fe07f0f2f056c5e26e480332` |
| `paper_prototype/main.tex` | New R1 bytes accepted | `24558539cb77caa778e286d6eda4028b4f569f2873dcd5650044e1aa288659b3` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | New R1 bytes accepted | `08b69bb8d64da4b3685968647f6434d75b7048b40aaac23369de6efebf516369` |
| `paper_prototype/README.md` | Unchanged; prior acceptance retained | `b9cec494b4e1c20162131f787df7de78172481c2486dba11daa301344f168815` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | Unchanged; prior acceptance retained | `a9d54501d1c943ff8bea9ce9502b522ec93f89dc55363550b9c958390251c0ec` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | Unchanged; prior acceptance retained | `4622e7c861c4d9345ecac4c894df02007dd8d59c60fba0b9a18b47e3f54f6060` |

## Severity and preserved boundaries

- **R1, previously low/nonblocking: closed.** The first-divergent-token wording and shared-prefix definition resolve the original ambiguity. Minimal further correction: none.
- **No new finding within the exact-edit scope.** No scientific evidence was re-reviewed or newly certified.
- SEQ146 canary harms, SEQ149 external-scaffold and explicit-prior limitations, SEQ151 HF forced-candidate versus native-greedy distinction, and all original accepted-versus-pending boundaries remain intact by the inverse-byte proof.
- Later outcomes remain excluded. No actual-record native memory-write/readback/retention or native greedy exact-TRAIN result is added. The separately named HF analysis remains pending at this manuscript cut. H1/H2, parenting, general G3, clean lineage, freeze, and mission completion remain unclaimed. Collaborator material remains UNSENT.

## Actions and files changed

Only `/tmp/astra_manuscript_seq151_R1_independent_20260913.md` was created. No repository or native edits, remote operations, GPU work, evidence reruns, web access, PDF build, staging, Git commits, or changes to anyone else's files. Main retains integration and operational ownership.
