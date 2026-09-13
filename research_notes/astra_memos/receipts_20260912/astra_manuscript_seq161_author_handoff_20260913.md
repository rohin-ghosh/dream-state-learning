# Manuscript through SEQ161 — author handoff / EDITSTOP

2026-09-13. Ready for the requested independent manuscript review; this author
does not self-certify independent approval. No commit, push, sending, model call,
scientific rerun, collection or change to source/scorer/protocol/result files.
Collaborator remains **UNSENT**. The existing developmental thesis and research
intent remain hypotheses, not promoted findings or a finished negative paper.

## Exact ownership and edits

Inspected commit `8921724fd2100af2b7a847fc483313b2caa7e8ef`, which changed11files.
The authorized canonical subset is exactly these SIX files; no coordination,
protocol, implementation or archived-receipt file from that commit was edited:

1. `paper_prototype/README.md` — current SEQ161/C97 summary and detailed six-cell
   extension at line140; prior SEQ160 extension relabeled historical.
2. `paper_prototype/astra_sprint_abstract_20260912.md` — current summary and
   bounded SEQ161 abstract paragraph at line578; prior abstract text retained.
3. `paper_prototype/astra_sprint_draft_20260912.tex` — current summary, appended
   abstract paragraph at line448, new section/table at line4073.
4. `paper_prototype/main.tex` — current summary and cutoff comment, appended
   abstract paragraph at line289, new section/table at line1834.
5. `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` — current
   UNSENT section at line121, six-cell table and archived source links; not sent.
6. `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` — current
   summary plus C97 at line4433, with exact archived analysis/review/handoff pins.

Both TeX files use `sec:seq161-additive` and `tab:seq161-additive`, once each.
C97 is the new claim-map entry, not a replacement for C96. Canonical TeX uses its
existing `[C97]` convention; sprint TeX uses `\ev{C97}`. No new bibliography entry,
title change, author identity or external reference was introduced.

## Content boundary

All six cells are included (exact/paraphrase/held/canary):

| Seed | ADDITIVE | Fresh MEMORY_ONLY | Screen ADDITIVE/MEMORY_ONLY |
|---|---|---|---|
| 0 | 14/14,10/14,47/48,12/12 | 10/14,10/14,47/48,12/12 | Meets/Meets |
| 1 | 7/8,7/8,48/48,12/12 | 8/8,8/8,46/48,12/12 | Meets/Fails |
| 2 | 8/8,4/8,39/48,12/12 | 3/8,2/8,47/48,12/12 | Fails/Fails |

Neither arm passes all seeds. Original exact floors8/14,7/8,5/8 plus zero
lost LR0-correct held/canary remain unchanged; original16possible records is
distinct from admitted14/8/8. Direct exact deltas+4/-1/+5, paraphrase0/-1/+2,
held0/+2/-8 are described without compensating gains for losses. Seed2's one
held gain/nine losses are explicit. The constant counts6/14,4/8,4/8 and
seed2ADDITIVE paraphrase tie remain limitations, not a rescued endpoint.

Fresh MEMORY_ONLY differs from historical EXTRA_MEMORY in all three seeds:
source/initialized tensor receipts and exact occurrence/epoch order agree,
but epoch1losses and final tensor receipts differ. No cause is assigned. Native
baseline drift limits attribution despite tiny CPU parity. Historical endpoints
remain noncontemporaneous; no substitute fresh control is claimed.

Original controllers rc0 / collectors and holder-written exits rc1 remain
explicit. Separate collection-only repair returns recorded rc0 without new
generation/fits/updates or a scientific retry. Original failures and seed1's
distinct BrokenPipe persist. Raw/source/route checks pass while retained child
content and format failures still count. Only5/120memory outputs are strict
canonical; eligibility/content are not strict formatting or byte identity.

Dose6fits1632updates480calls, matching original memory schedule, but unequal
replay token/forward compute and RNG/gradient trajectories. Already-trained
authored replay observations are not new TRY experience or parenting. Nested
controller/holder/failed-collector clocks and separate CPU recovery are stated
without claiming GPU-active time, new tensor verification or OS process reaping.
No C11 completion, H1/H2, general G3, clean-lineage, mission or freeze promotion.

## Evidence bindings (read-only)

SEQ161 archive commit: `f15dec6cb0fa678dd00caef608db9e110dc9ed38`.
Paths relative to `research_notes/astra_memos/receipts_20260912/`:

- `astra_additive_replay_recovered_analysis_result_20260913_attempt1/analysis.json`
  SHA256 `848602f01ca0596306dcb629a2e1d6896e08620cc6a67baa996853118c1cdb89`
- `astra_additive_replay_recovered_analysis_execution_20260913_attempt1.md`
  SHA256 `b3397ae8f4a29569f2f49e5d96a21410e73d072b101c439424d401ad5bfcfdfa`
- `astra_additive_replay_recovered_analysis_result_20260913_attempt1/execution_review.json`
  SHA256 `c7e8f7eb64a42589869e6f5f903854044405eb9acfc944102d450164b12c35d1`

The original frozen protocol is linked, not modified. No new results after
SEQ161, native query, archive extraction, scorer execution or parent tensor
authentication was performed for this manuscript task.

## Checks performed

- Applicable project instructions read; no nested AGENTS.md under the affected
  directories. All six owned files were clean before this patch. Other agents'
  GPU/PCFL code and rule edits were present and were not touched or reverted.
- Scoped `git diff --check` PASS. Scoped diff:551insertions/18deletions in exactly
  six authorized manuscript files. Removed lines are cutoff/heading metadata and
  historical-cut wording, not historical result tables or abstract content.
- Read-only table check PASS: all30rows across the five new tables match the
  archived analysis counts, denominators, held-loss masks and screen values.
  The companion abstract contains the same six cells in prose.
- Current headers and explicit limitations checked in all six files; collaborator
  UNSENT retained. C97 exists once in the claim map, and all new local evidence
  links resolve. No broken source binding or rewritten earlier result detected.
- TeX added-block braces/environment nesting and seven-column table rows PASS;
  both labels are unique and all earlier labels remain. Both full historical
  TeX abstract strings remain verbatim inside the updated abstracts.
- No pdflatex, tectonic or chktex is available here. No PDF built, no page/word
  compliance certification, and no claim of a full TeX compile. This is the
  existing long working manuscript, not submission-length certification.
- Initial generated patch syntax was rejected before any edit; the corrected
  context-only apply_patch then updated the six files. No scientific repair.

Suggested independent-review focus: matched memory exposure versus numerical
baseline non-parity; exact/content/strict distinction; collection attempt2 versus
scientific retries0; no inference of retention repair or parenting from two
descriptive screen passes; and historical SEQ160 statements retained as that cut.

## Author-frozen file hashes

| File | Before SHA256 | After SHA256 |
|---|---|---|
| `paper_prototype/README.md` | `9d868e0a67fe8a4e1533b12b1000d37681888d2f45dc925604de571bf6911a64` | `6fbd201ce6c605795c873e66a948d5eab2993ee0e7b855681462d981b2eea66b` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `38ad8c1511b9dd0299b215e5d1d2925667d3dbabf04714770f20eed94cc8eeea` | `340d5e4b496a7f34eb070fcd6f7664c9e2a782ac8006795cb5429b8fd1f9eaca` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `b4462b3f9ca53abca6d8341f313b2e319ba7c7eab4da60096c0aa16c6a2660dc` | `46d510f63878cce0e7cc28d3d7bbbb3b6c936e04fb22d3cd863142ad5cdadfdf` |
| `paper_prototype/main.tex` | `721c43008c4341d2b34367b853226cb234300dcd4aa8a874f701658ae8cef5c9` | `2b5a72870cfd257e2b2f9f10a2fd3ac8815fcfb3a968442d312a0f1e8b1f04bf` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `01fe2454c5e5720a8041405bd56f2d8e91559f1ad8d8f93cd9781e41f5e22012` | `0ba73c2d02f89bfea26ffe8bb1d4e4113e64a00af0ccb93da4d882a53a8e1d8b` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `aa30962bd27c91d8f5950612f38a23d5ac5073bc51411c28895c4b10ab62d5f2` | `4c266a4632745c1344477c531beecf1f71786a1f8eb21d6e4d1707daf3a74e10` |

Only these six repository files plus this explicitly requested /tmp handoff were
written. Independent review is next; no commit was made by this author.
