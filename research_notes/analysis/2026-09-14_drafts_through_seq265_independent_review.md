# Drafts through SEQ265 — independent change-review

Current disposition: the medium finding below is CLOSED by the separately
bound repair verification at snapshot8e5213c85370e2725db333a7b3da64f56a1970f0.
The original reviewed-snapshot finding remains preserved below.

2026-09-14. **Released to Main. Verdict: REVISE one medium-severity
reporting-status inconsistency, repeated at four TeX locations.** The changed
result counts and scientific limits otherwise pass this bounded comparison.
This is not whole-manuscript recertification or a new substantive content audit.
No author files were edited; ownership of this memo is released.

## Bound scope

Reviewed the parent-to-commit diff of
`9ce55e11b0c62323d4d3c1297cc20553be6608bd` in exactly:

- `paper_prototype/main.tex`
- `paper_prototype/astra_sprint_draft_20260912.tex`
- `paper_prototype/astra_sprint_abstract_20260912.md`
- `paper_prototype/README.md`
- `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md`

All draft locations below refer to that committed snapshot, not the live
working tree. Evidence is the published SEQ263/264/265 primary/review records
and the full V3 rollup at `d5989a9e`. The snapshot contains identical rollup
bytes, SHA256 `481c36c22177a8795bfa5674f3f613c77591f87aec4e6ca21e09afdbc5e6568d`.

## Finding and smallest repair

**M1 — current V3 status contradicts the completed rollup.**

| Snapshot location | Incorrect current-status text |
|---|---|
| `paper_prototype/main.tex:51` | `collection with content review pending` |
| `paper_prototype/astra_sprint_draft_20260912.tex:20` | `collection with content review pending` |
| `paper_prototype/main.tex:831` | `content review is pending` (following `full V3`) |
| `paper_prototype/astra_sprint_draft_20260912.tex:1069` | `content review is pending` (following `full V3`) |

These are added/changed reporting-cut statements, not merely untouched old
history. The latter two follow a historical SEQ257/258 boundary but explicitly
describe the later/current rich results. They conflict with the completed
56-episode/336-turn rollup and the same files' correct new result sections
(`paper_prototype/main.tex:968` and
`paper_prototype/astra_sprint_draft_20260912.tex:1206`).

Smallest repair in both TeX files: replace the first phrase with
`collection with full content review complete (one qualified episode; no fit)`;
replace the second with
`content review is complete (one qualified episode; no fit)`.
Keep quality fits LIVE/not analyzed and retain all no-learning/no-fit limits.
Do **not** replace raw collection `UNREVIEWED`/`fit_ready=False` labels or
rewrite the primary's earlier review-pending history. No equivalent stale
current-status assertion occurs in the four Markdown files' changed text.

## Claims that check out within the diff

- **SEQ263:** primary collection 74 calls, 64 attempts, two action-complete
  episodes/12 rows per view, 62 envelope failures. Main's 8P/3F/1U versus
  independent 6P/3F/3U is preserved; both exclude both episodes. Zero
  content-qualified rows and no fit are correctly distinguished from execution.
- **SEQ264 execution:** 372/384 calls, 56/64 action-complete episodes and 336
  rows/view agree with the primary. The looser 58 arrivals include two
  three-read cases excluded by the six-command gate. The primary supports the
  prospective exact-colon compatibility change, unchanged V2 first-turn
  prompts/raw responses and preserved V1/V2 outcomes; no new semantic pass is
  inferred from parsing or diagnostic-label absence.
- **Full content decision:** the disjoint primaries are 100P/48F/32U and
  95P/60F/1U, each with zero eligible episodes. Their original union is
  195P/108F/33U. The separate shard1 TRAIN-B/task1 CALL030 U-to-P adjudication
  leaves CALL031–035 passing and yields 196P/108F/32U: exactly ONE qualified
  episode/56 candidates, 1/64 attempts, six rows/view, no opposite-goal pair.
  Original judgments and raw UNREVIEWED rows remain distinct from that overlay.
  No tiny fit, learned richness, or broad semantic reliability is claimed.
- **SEQ265:** shared initial 4/16 goals, 0/8 pairs; critique 6/16 versus repeat
  4/16 goals, both 1/8 pairs, zero six-turn candidates. Primary and independent
  reduction agree. Actual calls are 25 shared initial + 54 critique + 48 repeat
  = 127, not two copies of the initial phase. Final-arm generated tokens are
  7,518 versus 5,474. The ceiling is correctly **112 calls per arm and 512
  generated tokens per call**, not 512 tokens for an entire arm; equal ceilings
  are explicitly not equal spend. All 16 interventions/final attempts per arm
  remain. The 25 callback stops are not native exceptions; all 127 native
  error fields are null, with one nonterminal/truncated intervention per arm
  preserved separately. NO_FEEDBACK is not blindness to prior public outcomes.
- **Publication boundaries:** quality remains LIVE/not analyzed at this cut;
  1,452 targets and the prospective 2,928-update recipe are not completed-fit
  or AFTER outcomes. No blocked 12,384-update proposal is revived. Changed
  text preserves SEQ245's narrow single-bank write/use result with a matching
  uniform control and SEQ260's lack of incremental PROBE advantage over its
  active control, both target failures. No rich fit, human/clean-lineage,
  full H1/H2, robust-transfer or autonomous-learning promotion appears in the
  reviewed changes. The collaborator message remains UNSENT.

The added result bodies are identical between the two TeX files and identical
across the four Markdown files. Their starts are `paper_prototype/main.tex:950`,
`paper_prototype/astra_sprint_draft_20260912.tex:1188`,
`paper_prototype/astra_sprint_abstract_20260912.md:603`,
`paper_prototype/README.md:567`,
`research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:592`, and
`research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:6059`.

## Evidence, checks and limits

Compared committed `research_notes/analysis/2026-09-14_` records with suffixes:
`rich_action_first_collection_first_result.md`, `rich_v2_content_review.md`,
`rich_v2_content_independent_review.md`,
`rich_action_first_v3_collection_first_result.md`, `rich_v3_content_review.md`,
`rich_v3_content_shards23_review.md`, `rich_v3_content_review_adjudication.md`,
`rich_v3_content_rollup.md`, `self_critique_repeat_collection_first_result.md`,
`self_critique_repeat_independent_result.md`, and `goal_quality_fit_protocol.md`.
Reviewer-role overlap with the earlier V2/shards0–1/adjudication records is
explicit: this is independent of the draft author, not a fresh regrading of
those judgments.

Commands/checks: local `git show`, six-path `git diff --unified=0/2/3/4`,
`rg`, `nl -ba`, bounded `sed`/`head`/`tail`; a standard-library Python check
using only `subprocess`, `hashlib` and `re` verified duplicate result-body
identity, snapshot/rollup byte identity, review-count sums, 56×6 denominator,
127-call sum, arm-token sums and 16+96=112 ceiling arithmetic. These checks
passed. Static whitespace checking of this memo passed. Applicable AGENTS
and CLAUDE ownership/rules were considered; no nested rules were found in the
reviewed directories.

No model/tokenizer/torch, GPU, remote/network, new literature, raw-capsule
replay, teacher-plan inspection, full ancestor inventory, tests of production
code, or TeX engine was used. No live runtime status or tensor authentication
is certified; recorded state/cost claims are checked against released records,
not new execution. Existing older sections are not reapproved wholesale.
The four-site repair is a prose-status correction, not an experiment blocker
or a request to change the rubric, admission gate, or any result.

## Bound repair verification — September 14, 2026

**M1 CLOSED at snapshot `8e5213c85370e2725db333a7b3da64f56a1970f0`.**
The original finding and original-snapshot verdict above remain preserved.
This addendum verifies only the four replacements and the raw-label/review
distinction, not a full rereview or approval of intervening changes.

- `paper_prototype/main.tex:51` and
  `paper_prototype/astra_sprint_draft_20260912.tex:20` now say
  `collection with content review complete (one qualified episode; no fit)`.
- `paper_prototype/main.tex:832` and
  `paper_prototype/astra_sprint_draft_20260912.tex:1070` now say
  `content review is complete (one qualified episode; no fit)`.
- Raw collection labels remain `UNREVIEWED`/`fit_ready=False` at
  `paper_prototype/main.tex:966` and
  `paper_prototype/astra_sprint_draft_20260912.tex:1204`; the separate overlay
  explicitly preserves raw rows and original judgments at
  `paper_prototype/main.tex:981` and
  `paper_prototype/astra_sprint_draft_20260912.tex:1219`.

All locations here refer to the repaired snapshot. Its two bounded V3
execution/content blocks are byte-identical to the original reviewed
`9ce55e11b0c62323d4d3c1297cc20553be6608bd` blocks. The replacement passages
retain quality LIVE/not analyzed and the one-episode/no-fit limitation.

Checks: local `git show`, repair-parent-to-commit two-file `git diff`, and
standard-library assertions for exact replacement occurrences, removed stale
phrases, preserved overlay language and bounded-block byte identity: PASS.
Memo whitespace check: PASS. No draft edits, GPU/model/network calls, TeX,
raw-data rerun or broader manuscript review. Addendum and ownership released.
