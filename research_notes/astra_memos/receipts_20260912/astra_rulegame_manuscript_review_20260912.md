# Independent bounded manuscript review — SEQ094/095

Review date: 2026-09-12, approximately 17:11 UTC. Reviewer: independent Codex review session, not Main or the manuscript author.

## Verdict and scope

**No blocking scientific/count/cost discrepancy found in the SEQ094/095 additions. Two LOW-severity wording fixes recommended.** This is a bounded manuscript-to-receipt consistency review, not teaching-efficacy certification, experimental approval, a GPU gate, or independent model-origin authentication.

Reviewed the new RuleGame claims in all six requested EDIT-STOP files against the two terminal memos, both native captures, both Main audits, and both formation/material-decision capsule pairs. SEQ092/093 results were not re-reviewed. Unrelated preparation, literature, and historical campaign claims are outside this review. No Git commands, network access, GPU queries/jobs, parent jobs, tests, scientific reruns, or repository edits were performed. Archives were read in memory without extraction. The sole written artifact is this requested `/tmp` report.

## Findings, ordered by severity

### F1 — LOW: condensed summaries turn unresolved elicitation ambiguity into a categorical diagnosis

- **Affected evidence lines:** `paper_prototype/astra_sprint_draft_20260912.tex:67` says “Relation-field elicitation is ambiguous”; the same claim appears in `paper_prototype/astra_sprint_abstract_20260912.md:14`, with “An ambiguous relation elicitor” at line 26. `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:14` likewise says the elicitor “is ambiguous.”
- **Reference evidence:** `research_notes/astra_memos/ASTRA_RULEGAME_V2_TERMINAL_2026-09-12.md:49` distinguishes the observable omission of an explicit mapping from the unresolved ambiguity-versus-skill-deficit explanation. `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:837` preserves that distinction. In the v2 formation capsule, `astra_rulegame_interaction_v2_20260912_attempt1/formation/data/calls/0008.request.json:1`, JSON path `request.prompt`, lists the three relation labels followed by “accordingly”; it does not enumerate the mapping. This verifies prompt underspecification, not the model's reason for each error.
- **Why LOW:** These summaries do not explicitly claim that ambiguity caused the failures, and the detailed manuscript sections correctly leave the explanation unresolved. Nevertheless, the standalone abstract/update should retain the same epistemic boundary rather than selecting a diagnosis by compression.
- **Smallest fix:** Replace the categorical sentence with: **“The relation mapping is not explicit; ambiguity versus a skill deficit remains unresolved.”** In the shorter boundary paragraph, use “The underspecified relation elicitor and generic same-7B feedback leave adequate target-skill teaching untested.” No scoring, result, or protocol change is needed.

### F2 — LOW: collaborator update encodes two selected counts as an apparent fraction

- **Affected evidence line:** `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:8`: “first-two selection is1/2.”
- **Reference evidence:** `research_notes/astra_memos/ASTRA_RULEGAME_V2_TERMINAL_2026-09-12.md:23` reports faithful counts P=1/6 and A=3/6, then selected counts P=1 and A=2. The v2 native capture at `research_notes/astra_memos/receipts_20260912/astra_rulegame_v2_formation_capture_20260912.json:1`, JSON path `formation_selection.selected`, contains one P record and two A records. They are counts from different arms, not a 1/2 rate.
- **Why LOW:** The preceding context makes the intended meaning recoverable, but the slash is especially easy to misread beside the genuine 1/6 and 3/6 fractions.
- **Smallest fix:** Replace “first-two selection is1/2” with **“first-two selection is process 1 versus active 2.”**

## Checks that passed

### Counts and denominators

Independently reduced archived task/event records and checked record JSON fields against their linked execution fields; did not merely copy terminal memo totals.

| Quantity | SEQ094 v1 | SEQ095 v2 |
|---|---:|---:|
| Valid first quizzes / tasks | 0/8 | 8/8 |
| Protocol-invalid terminal responses | 8 | 0 |
| Actual TRYs, all pre/apply tasks | 10 | 24 |
| Actual apply TRYs, P / A | 0 / 4 | 6 / 6 |
| Apply record outputs, P / A | 0 / 4 | 6 / 6 |
| Schema-valid apply records | 4/4 | 12/12 |
| Faithful records, P / A | 0 opportunities / 2 of 4 | 1 of 6 / 3 of 6 |
| First-two selected, P / A | 0 / 2 | 1 / 2 |

- V1's zero quiz scores are registered missing/invalid-outcome placeholders, not eight demonstrated incorrect quiz answers. Zero process **apply** opportunities must not be generalized to zero process activity: P executed three pre-task TRYs. The six files preserve the relevant apply/task distinction in their detailed sections.
- V2 quiz counts reproduce P rule0 3/6→4/6, rule1 5/6→3/6; A rule0 3/6→3/6, rule1 5/6→4/6. Each arm therefore totals 8/12 pre and 7/12 apply. These are correlated task/item counts, not learner replications or an efficacy estimate.
- All 24 v2 TRY outcomes are True. Claims explicitly restrict this to the measured envelope and do not assert informative exploration, negative-observation coverage, new-rule generalization, or successful developmental learning.
- Main manuscript anchors: `paper_prototype/main.tex:344`, `paper_prototype/main.tex:346`; companion anchors: `paper_prototype/astra_sprint_draft_20260912.tex:1135`, `paper_prototype/astra_sprint_draft_20260912.tex:1164`, table at line 1178; README table at `paper_prototype/README.md:15`; claim map at `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:753` and line 815.

### Malformed actions versus record semantics

- V1 invalid-call IDs 0007/0008/0011/0022 have unrecognized TRY aliases; 0004/0016/0021/0031 have multiple ACT lines and invented outcome continuations. The archived raw responses confirm the four/four split. These are terminal action-protocol failures, not malformed record-JSON counts.
- All four v1 record outputs parse with the accepted schema; two fail relation semantics. All twelve v2 record outputs likewise have the accepted schema; eight fail relation semantics. No manuscript claim incorrectly calls those eight records malformed JSON.
- Additional diagnostic detail, not a required manuscript addition: v2's eight semantic failures split into four expected `mismatched` and four expected `unavailable` (missing prediction), all emitted as `matched`. Thus even the error category should not be collapsed to Boolean-comparison incapacity. The existing detailed sections appropriately avoid that conclusion.
- Exact archive evidence: v1 `formation/data/events.jsonl` record lines 20, 26, 28, 30; v2 record lines 8, 10, 12, 23, 25, 27, 38, 40, 42, 53, 55, 57, under their respective archive roots. Expected relations were recomputed from the linked execution's `observed`/`predicted` fields; all recomputed eligibility flags match the archived flags.

### Cost accounting

Independently counted every archived response's native prompt/output token-ID arrays and summed paired request-start/response-end durations. Totals match both the usage receipts and manuscript rounding.

| Quantity | SEQ094 v1 | SEQ095 v2 |
|---|---:|---:|
| Responses: wake / parent / restatement / record | 20 / 4 / 4 / 4 = 32 | 40 / 4 / 4 / 12 = 60 |
| Native prompt / output tokens | 11895 / 1446 | 23342 / 1296 |
| Summed recorded generation-call seconds | 42.209187 | 38.957460 |
| Supervised-worker seconds, including cleanup | 169.633754 | 164.493039 |
| Responses, P / A | 12 / 20 | 30 / 30 |
| Prompt tokens, P / A | 5585 / 6310 | 12683 / 10659 |
| Output tokens, P / A | 705 / 741 | 728 / 568 |

- Worker durations come from archived supervision, not subtraction of outer controller/release timestamps. Exclusions of hashing, CPU preparation, Main audit, and transfer are retained; neither these windows nor summed generation-call time is active-GPU compute, campaign cost, or sustained throughput.
- Equal v2 response opportunities plainly do not equal actual token cost. No token/compute-matched treatment claim was found. V1 asymmetry is explicit in the README, companion, and claim map; the canonical component paragraph reports aggregate cost without falsely claiming matching.
- Evidence anchors: `paper_prototype/README.md:39`, `paper_prototype/astra_sprint_draft_20260912.tex:1156`, line 1204, `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:780`, line 851. Raw evidence is each formation capsule's `formation/data/usage.json`, `formation/data/calls/`, and `formation/worker/supervision.json`.

### No downstream writing; parent/control and gate limits

- Both native captures contain `fits: {}`. Both separately hashed material-decision capsules contain `material/result.json` with `status: MAIN_DECLINED_MATERIAL`. Neither formation archive contains fit/readout/corpus/adapter-weight members. These support the bounded reported no-corpus/no-fit/no-new-rule-readout outcome; this is not a claim that no log files were written or a new live filesystem audit of the remote nodes.
- Paired shortage is independently visible before Main's additional content rejection: P=0<2 in v1 and P=1<2 in v2. A's qualifying records do not license an A-only fit. Formation capsules retain the earlier awaiting-audit state; the subsequent decision capsules supply the final material status. The manuscript correctly separates these stages.
- Main's audits accept provenance while rejecting both active-control turns in each version. V1's unsupported quiz premise and false process “no prediction” diagnosis are preserved. V2 control summaries use allowed training outcomes, not sealed scores; process feedback addresses omitted predictions but does not explicitly teach the record relation mapping. Same-frozen-7B parent-role operation is not a strongest-teacher comparison.
- V1 calls 0002(P)/0014(A) independently checked: prompt strings, seeds, and native prompt-token arrays match, while response text differs. The manuscript correctly preserves actual arm baselines and leaves the cause unlocalized.
- No P1/G3/G5/H1/H2, selective-memory, clean-child, mechanism-freeze, generalization, or parenting-efficacy promotion is inferred from these results. Native PASS, Main audit acceptance, and this manuscript review remain distinct. Model-origin status remains `UNRESOLVED_LOCAL_HASHES_ONLY`; hashes are custody evidence, not official-origin authentication.
- Reference anchors: `research_notes/astra_memos/ASTRA_RULEGAME_FORMATION_TERMINAL_2026-09-12.md:20`, line 40, line 49; `research_notes/astra_memos/ASTRA_RULEGAME_V2_TERMINAL_2026-09-12.md:28`, line 37, line 43; `research_notes/astra_memos/receipts_20260912/astra_rulegame_main_audit_20260912.json:5` and its `reviews`; corresponding v2 audit at line 5 and its `reviews`.

## Receipt identity checks

All eight externally listed SHA256 identities below were recomputed locally and match the terminal memos and C38/C39. No archive content was changed.

| Receipt filename under `research_notes/astra_memos/receipts_20260912/` | SHA256 |
|---|---|
| astra_rulegame_formation_terminal_20260912.tgz | b13f6f77fd1b276d2d019e255c09aacbce85a29eaf95b6363c5cf3f276c9e0a4 |
| astra_rulegame_formation_capture_20260912.json | a012dfd8f4a8b246329d407b415685780f1f21be352b3239bb30c953bd3e01ad |
| astra_rulegame_main_audit_20260912.json | cdea111d87b1e06c2a9490e3c8d8528b3f0a8e55f89d0fbca54fe81215b3a0ac |
| astra_rulegame_material_decision_20260912.tgz | 763269cad71d480534d8f5414891ad01cba2bfe75989f84d736d0d91665a194d |
| astra_rulegame_v2_formation_terminal_20260912.tgz | d3433cc22e398343bee59f755f2d2ac9dc5308347eba4ef421abdd76ae969ef8 |
| astra_rulegame_v2_formation_capture_20260912.json | 9660dbbac056c0fdb86a59abbff548d5356861abdbeffceedc8269c6ba9f6569 |
| astra_rulegame_v2_main_audit_20260912.json | 163641c00993e39754b49a79b2ad8daa743013fb3488f7f3cfaf68aab491f17a |
| astra_rulegame_v2_material_decision_20260912.tgz | 31c6483cf197777768a319ac7cbb2f9fd90a912f9128c4fd56af2acb59d1f27c |

## Reviewed target identities

Line references apply to these locally observed file bytes, not an inferred Git diff or any future Main edits.

| File | SHA256 |
|---|---|
| paper_prototype/main.tex | ca2800a2a2ccbf9d5bfa277a5c263e76507082f333cf4277e13663bf7cc0bfe7 |
| paper_prototype/README.md | 25d2b63831ece67b7efc858fd80cad352507fa6c8d5f6491887df6b576961850 |
| paper_prototype/astra_sprint_draft_20260912.tex | d8e6641963e3e5841a1021fd87693b86971b56777565dab9e2527d85fcd95ad5 |
| paper_prototype/astra_sprint_abstract_20260912.md | b0f85e7ca62d51b34ba926e9e1c009d8806bcd9c1882660713722501daf00d00 |
| research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md | b1fec7973235822e7b2cfdbae52c7f12c0a2b9177eb76eb9d7b6d8795d697c59 |
| research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md | 2500a4a76c471267120d0a501e8befff5bcdde0e01a7f7f05af36f5bf9398871 |

**Disposition:** Main can make the two local wording substitutions without changing scientific results. No experiment, protocol redesign, reclassification, gate advancement, or external circulation is recommended or authorized by this review.
