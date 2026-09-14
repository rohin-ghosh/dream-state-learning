# V3 rich-content primary review: shards 2–3

Date: 2026-09-14. TRAIN candidate content only. No teacher, PROBE,
model/GPU calls, fits, code changes, or shards0–1 judgments.

## First-pass result — fixed before Main sample consultation

- Reviewed **26/26 scoped candidate episodes, 156/156 turns**.
- **95 PASS, 60 FAIL, 1 UNRESOLVED** turns.
- **0/26 all-six-PASS episodes; 0 admitted rows per supervision form**
  (TERSE, RICH, RICH_ACTION_ONLY). No passing-turn-only salvage from excluded
  episodes. `fit_ready=false`; review authorizes no fit.
- The 26 action-complete/outcome-only candidates are supplied by the packet,
  not newly terminal-replayed here. Six of 32 planned shard2–3 episodes are
  absent from the candidate packet, not counted as content successes.
- Contract SHA256: `3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b`.
- Packet: `gpu_artifacts_local/astra_rich_action_first_v3_terminal_20260914_attempt1/CONTENT_REVIEW_INPUTS.json`.
- Packet SHA256: `b7e19b81e347ee0c0e89f97e669f32fd9bef8513067233ab1355962eb76bc92b`.
- First-pass label digest: `f2e6c5b29beb507568d813472aa6949c1cfcd115de90fc246c8f84b8e91a3c8d`.
- Companion JSON includes every call/source/native-file identifier, decision,
  concise reason, exact full rationale span and pre-action user-message spans.
  Raw/prefix hashes bind reviewed bytes. Native-file/call/source hashes are
  copied from the packet; no full ancestry audit or native-file rehash claimed.

## Coverage by world and goal

| Shard | World | Goal | Reviewed tasks | Episodes | Admitted |
|---|---|---|---|---:|---:|
| 2 | A | `N_UXJVOUWNYH` | 1 | 1 | 0 |
| 2 | A | `N_2WDGW5FRMB` | 2 | 1 | 0 |
| 2 | B | `N_JQQVT3O4AH` | 0 | 1 | 0 |
| 2 | B | `N_RXLBDK6YJW` | 2,3 | 2 | 0 |
| 2 | C | `N_7DDYYRLLKX` | 0,1 | 2 | 0 |
| 2 | C | `N_VNVYNV22J5` | 2,3 | 2 | 0 |
| 2 | D | `N_LP7VQN53OC` | 1 | 1 | 0 |
| 2 | D | `N_UJL5NGAMCM` | 2,3 | 2 | 0 |
| 3 | A | `N_OOTLUSFRTA` | 0,1 | 2 | 0 |
| 3 | A | `N_7KYAISJAXO` | 2,3 | 2 | 0 |
| 3 | B | `N_NPXPJCN54Y` | 0 | 1 | 0 |
| 3 | B | `N_EWK24KWEDJ` | 2,3 | 2 | 0 |
| 3 | C | `N_KBV3LMQBIY` | 0,1 | 2 | 0 |
| 3 | C | `N_U4FOYVYS2O` | 2,3 | 2 | 0 |
| 3 | D | `N_S77ZQSHTJX` | 0 | 1 | 0 |
| 3 | D | `N_NXO4ST3VUU` | 2,3 | 2 | 0 |

## Substantive interpretation

Every label comes from reading actual raw explanation against public evidence
available before that action. Later feedback cannot ground an earlier claim.
Correct executable commands do not rescue false or empty rationales. No IDs,
commands, or explanations were repaired. Full evidence spans remain in JSON.

Recurring failures: invented locations of unread events; historical reads
misdescribed as task motion; wrong opaque IDs; denying already-visible edges;
first-route rationales asserting closer/most direct without explaining the
intermediate-to-goal join; and fourth-read rationales claiming a missing path
already fully shown or giving generic promises rather than useful uncertainty.

Prospective information gathering is not an assertion that an unseen edge was
observed. An initial opaque read may pass when it names the route uncertainty
and listed record without inventing an endpoint. Explicitly historical memory
outcomes are not current task completion. An unambiguous reference to a known
goal-path intermediate or one remaining hop can use an observed continuation
without repeating every ID. Shard2 TRAIN-D task1 call79 remains UNRESOLVED:
already been obtained could mean historical memory or premature attainment.

This is adaptively filtered DEV content, not private-reasoning verification
or an unbiased generalization estimate. Unsupported public statements alone
do not prove hidden-teacher copying. The historically V2-titled contract is
applied unchanged to V3 under this explicit assignment.

## Main sample comparison

Opened Main's sample only after both first-pass artifacts were written and
their exact coverage, hashes and evidence spans validated. First-pass JSON
SHA256: `c5ad329b78493504e0fd96d094311267e7b2b9dcf7f9ad7963b0f09209f18bfa`.
The label/reason digest above remains unchanged after comparison.

Sample: `2026-09-14_rich_v3_main_content_sample.md`, SHA256
`566127914bf03915285370c2f8c7da9d0ebfb5479e0253bcc1de6ebbf576509f`.
Only shard2 TRAIN-A/task1 and shard3 TRAIN-A/task0 are compared here:
**8/12 identical turn labels, four preserved disagreements, 2/2 identical
episode exclusions.** No primary label was changed to match the sample.

| Episode | Call | Primary | Main | Difference retained |
|---|---:|---|---|---|
| shard2 A/task1 | 8 | PASS | UNRESOLVED | Remaining unread record plus missing goal-path information is sufficient inspection purpose to this reader; Main finds the later-READ wording too generic. |
| shard3 A/task0 | 0 | PASS | UNRESOLVED | Primary reads the CURRENT-information forecast as broad prospective purpose; Main finds its promise too specific for an opaque address. |
| shard3 A/task0 | 3 | FAIL | UNRESOLVED | Primary rejects the false missing-link premise after the chain is visible; Main allows an unarticulated alternative-path uncertainty reading. Both exclude. |
| shard3 A/task0 | 4 | FAIL | UNRESOLVED | Primary reads not yet observed as denial of visible memory; Main allows not yet traversed as a possibility. Both exclude. |

Main remains adjudicator of these substantive boundary differences. Each
sample has decisive failures independent of disputed labels, so neither
comparison nor a boundary resolution admits either episode. No extra fit,
turn-level salvage, or literal wording rule follows from this comparison.

## Validation and release

PASS: 26 exact scoped episode IDs, 156 unique shard/call IDs, six turns each,
packet/contract/raw/prefix hashes, action projections, exact raw/public spans,
decision totals and all-six admission. First-pass label digest is unchanged.
Shard2: 12 episodes/72 turns (43 PASS, 28 FAIL, 1 UNRESOLVED).
Shard3: 14 episodes/84 turns (52 PASS, 32 FAIL, 0 UNRESOLVED).

Only this Markdown file and its same-stem JSON are delivered. Ownership is
released to Main for exact-ID union with the separate shards0–1 review.
No commits, source changes, model calls, GPU work, or fit authorization.
