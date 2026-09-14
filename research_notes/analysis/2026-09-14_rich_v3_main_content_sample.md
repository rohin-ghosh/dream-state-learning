# V3 independent Main sample — September14,2026

Scope: first action-complete episode in packet order from each of the four
shards, selected before receiving the primary reviewer's labels. All24turns
in those four episodes inspected against their pre-action public histories.
This is a deterministic coverage sample, not a random sample or full336-turn
review. Ramanujan owns the full primary review. No teacher plan or PROBE
input is used here. No fit or corpus-wide content yield is declared.

Input `gpu_artifacts_local/astra_rich_action_first_v3_terminal_20260914_attempt1/CONTENT_REVIEW_INPUTS.json`,
SHA256 `b7e19b81e347ee0c0e89f97e669f32fd9bef8513067233ab1355962eb76bc92b`.
Rubric `2026-09-14_rich_content_review_contract.md`, SHA256
`3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b`,
prospectively adopted by the V3 protocol. PASS/FAIL/UNRESOLVED below are
substantive judgments, not literal heading or length checks. UNRESOLVED
does not admit a turn. Call indexes are native indexes within the shard.

## Turn judgments

Episode IDs have prefix `ASTRA-RICH-20260914-V1-SHARD-`; complete suffixes
are in the table. The V1-named source episode IDs are intentionally preserved.

| Episode suffix | Call | Verdict | Public-evidence assessment |
|---|---:|---|---|
| 0-TRAIN-A/task/0 | 0 | UNRESOLVED | The unknown connections/goal path are correctly identified. “will provide information about the connections from the current node” promises more than an opaque unread address establishes; it may instead express a broad inspection purpose. |
| 0-TRAIN-A/task/0 | 1 | UNRESOLVED | “has been reached ... was used to get to a new node” does not clearly distinguish the historical EVENT from the present action state. It could describe past memory, so not a definite current-transition falsehood; its inspection account also remains generic. |
| 0-TRAIN-A/task/0 | 2 | FAIL | “The only unread event is E_OLJO4NDYHO” is false: E_PAYLPNOCNY is also unread. |
| 0-TRAIN-A/task/0 | 3 | UNRESOLVED | The known two-hop route is correctly recognizable, but “only port that could potentially” excludes the still-unread alternative and “understand the next step” does not explain what remains missing. Do not turn this ambiguity into a pass. |
| 0-TRAIN-A/task/0 | 4 | PASS | Names the observed CURRENT→N_TADZALVT42→GOAL chain and its two ports; selecting the first port makes the next hop clear without claiming immediate goal arrival. |
| 0-TRAIN-A/task/0 | 5 | PASS | Uses the actual updated CURRENT and observed final port to forecast direct goal arrival. |
| 1-TRAIN-A/task/0 | 0 | PASS | Admits unexplored connections; “might provide information” about a goal path is appropriate first-read uncertainty and purpose. “goal ... unknown” is interpreted as its unobserved connection, not ignorance of its displayed name. |
| 1-TRAIN-A/task/0 | 1 | FAIL | Attributes P_BYLTMIJRUV→N_LAYOZEDKAI to CURRENT N_ZT5Y7OB6H5, but the only read record originates at N_F7DW6ZZIZJ. This is an explicit false edge origin. |
| 1-TRAIN-A/task/0 | 2 | PASS | Correctly identifies an observed edge to the goal and the still-unknown connection from CURRENT; describes unread E_U7IQZ4W7B6 as potentially informative rather than asserting its contents. |
| 1-TRAIN-A/task/0 | 3 | UNRESOLVED | Summarizes the three read edges correctly, but “only port that can lead us closer” presumes the uninspected alternative's destination. A hypothesis-by-elimination reading is possible; it is stated too categorically for admission. |
| 1-TRAIN-A/task/0 | 4 | PASS | Uses the observed first hop to N_SX7L4MACJ7 and the known goal relation to select the correct branch; relational next-hop explanation is permitted by the rubric. |
| 1-TRAIN-A/task/0 | 5 | PASS | Explicitly links actual CURRENT, final port, prior EVENT and expected goal. |
| 2-TRAIN-A/task/1 | 5 | PASS | Appropriate first-read uncertainty and information-gathering purpose; no specific unread edge is asserted. |
| 2-TRAIN-A/task/1 | 6 | FAIL | Calls observed destination N_7MERJWUZCI “not closer to the goal” before reading any outgoing relation from that node; distinct from the goal does not establish lack of progress. |
| 2-TRAIN-A/task/1 | 7 | FAIL | Assigns unread E_7NVVDFPAQC to N_7MERJWUZCI without any address mapping in the prefix. “path taken so far” also risks conflating memory and movement, but the unsourced event-origin assertion alone is decisive. |
| 2-TRAIN-A/task/1 | 8 | UNRESOLVED | Correctly notes the fourth record is unread. “likely relevant ... next steps or current state of the goal” is too generic to establish the later-READ useful-information floor confidently. |
| 2-TRAIN-A/task/1 | 9 | FAIL | Emits unsourced CURRENT identifier N_B6TVE6AR7DC instead of N_B6TVEAR7DC. The two-hop relation otherwise matches memory, but training the actual invented identifier is not authorized; no silent typo repair. |
| 2-TRAIN-A/task/1 | 10 | PASS | Grounds final port/goal in E_5F4EZBNH6G and actual updated CURRENT. |
| 3-TRAIN-A/task/0 | 0 | UNRESOLVED | Identifies route uncertainty, but “will provide information about the current node” over-specifies what the first opaque event can supply. A broad purpose reading remains possible. |
| 3-TRAIN-A/task/0 | 1 | FAIL | Says GOAL “is not directly connected to the current node” when only an unrelated-origin EVENT has been read; neither CURRENT port destination is known. Unsupported negative edge claim. |
| 3-TRAIN-A/task/0 | 2 | PASS | Correctly identifies N_HNLSZUUOOR→GOAL and the missing CURRENT connection; “might provide” remains an honest information-gathering hypothesis. |
| 3-TRAIN-A/task/0 | 3 | UNRESOLVED | Both connecting edges are already public, yet the explanation seeks a “missing link.” It could be uncertainty about the remaining alternative rather than an incorrect relation, but does not clearly articulate that purpose. |
| 3-TRAIN-A/task/0 | 4 | UNRESOLVED | The relevant port relation has been read, while the explanation calls it “not yet observed.” That may mean not traversed in this rollout; the distinction and intermediate-hop forecast are too unclear to admit. |
| 3-TRAIN-A/task/0 | 5 | PASS | Explicitly calls the EVENT historical and connects actual CURRENT to the goal through its known port. |

Sample counts:10PASS,6FAIL,8UNRESOLVED. Each sampled episode has at least
one decisive FAIL, so all four are excluded independently of the ambiguous
turns. These are four episodes out of56 action-complete candidates, not a
claim that the remaining52 fail or that the full corpus has zero fit rows.
Do not fit isolated passing turns contrary to the all-six-turn shared rule.

The useful distinction survives the parser fix: grounded route explanations
exist, and action completion is real, but successful execution is not a truth
certificate for every explanation. Some uncertainty wording is genuinely
ambiguous; preserve reviewer differences rather than impose an after-the-fact
literal-label rule. The complete primary review and any accepted-episode
challenge determine the usable corpus, not this sample alone.

Read method: local jq over the structured packet, full pre-action context for
the sampled episodes, and sequential raw responses/public feedback. The first
wide display truncated, so the samples were reread in two bounded shard groups;
no conclusion relies on omitted output. No new model/GPU calls or source edits.
