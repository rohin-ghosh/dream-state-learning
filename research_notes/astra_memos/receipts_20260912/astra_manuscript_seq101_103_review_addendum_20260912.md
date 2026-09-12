# Targeted manuscript review addendum — September 12, 2026

## Verdict: PASS

R1 is corrected exactly, and the other five files remain byte-identical to the original reviewed hashes. The prior low-severity editorial finding is closed. The original review's scientific/numerical PASS findings and scope limitations carry forward; no new full review or scientific certification was performed.

## Targeted verification

At `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1332`, the corrected line is:

> checks remain attributed; local review recomputes log-probabilities and NLLs from archived float32

The single replacement is `recomputes logits` → `recomputes log-probabilities and NLLs`. Reversing only that replacement **in memory** reproduces the original reviewed claim-map SHA256 exactly. This verifies that there are no other byte changes anywhere in that file, including the adjoining native-custody and absent-weight qualifications.

- Original claim-map SHA256: `d15eabe46fd2e28f7895d2d98403b26f963dfd623ecf32c0dc94b2bc25e23d72`.
- **Corrected claim-map SHA256: `61b02bf468a4de13e994180fb15e59fd652ddce1d38308bc34fe3f50c7c88fd6`.**

## Other five files: unchanged

| File | Verified SHA256 |
|---|---|
| `paper_prototype/main.tex` | `d384855e5c72cd669553505b9d9cdd7f81fbbbc61f47abc41c5f6842000cf6b7` |
| `paper_prototype/README.md` | `5b2356dc19a6eb997f22d07e35a644188857f8fc5480710d1dfeac4f53663b11` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `bbe93571046b0343c40394567984b15abe7286c697e1c4fe92f91db12d82efef` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `6b8242e620ad65d18acffb6fc0c5ba1fee7d555118b70950ba26c15cb88c092f` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `a3a8f2290d4a8c500d7e729eb9b6fc34374d11711e751342ed521eef18b77004` |

## Binding and limits

Baseline review: `/tmp/astra_manuscript_seq101_103_review_20260912.md`, SHA256 `741a475eff43cbd9492d6e0829dd3d3c38bd2df8eb993d8652148eff0b8c7fe4`. Its original FAIL for clean exact-byte editorial signoff is resolved for the six-file state bound by this addendum.

Main reports commit `661e6c3c`; Git was not accessed, so this addendum verifies current filesystem bytes, not commit contents or commit identity. Only read-only standard-library hashing and the in-memory reverse-replacement check were used. No network, GPU/model calls, Git operations, evidence reruns, repository edits, or full manuscript rereview occurred. Only this requested addendum was written. No launch decision or veto is involved.
