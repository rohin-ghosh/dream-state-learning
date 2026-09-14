# Action-first-v2 content review — Main, September14,2026

Reviewed all12turns in the two action-complete TRAIN episodes, using only
their pre-action student prefixes and actual child responses. Contract
`2026-09-14_rich_content_review_contract.md`, SHA
`3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b`,
was published before this inspection. No teacher prompt or PROBE score was
used. This is substantive author review, not an automated semantic certificate;
independent review is pending.

Packet: `gpu_artifacts_local/astra_rich_action_first_terminal_20260914_attempt1/CONTENT_REVIEW_INPUTS.json`.
Raw terminal capsule SHA
`508b12e464ee4379fce750675822235d4c23096ac6149ad6c39545dca1f672e7`.
Every locator below uses the zero-based native call index in its shard's
`teach/LESSONS.json`; episode turn indexes are zero-based.

## Episode A: shard0 TRAIN-B/task/2

| Turn / call | Decision | Raw support and public-evidence justification |
|---|---|---|
| 0 /6 | FAIL | “has no direct route to the goal” is asserted before any EVENT has been read. The public task lists opaque ports, not their destinations. Its later “might provide information” is appropriate uncertainty but does not repair the earlier unsupported factual claim. |
| 1 /7 | FAIL | “The current node N_JJDBDX5757 has been reached via port P_FS55PCAO72, which led to node N_E3ACGSRKC2.” Only a READ has occurred; the returned historical record describes an outgoing transition from N_JJDBDX5757. It neither moved the current actor nor says that node was reached via this port. |
| 2 /8 | PASS | “P_FS55PCAO72 led to N_E3ACGSRKC2 and P_XSL3QAYWAT led to N_UFHNUIY4E2. Neither of these nodes is the goal” matches both observed records; the unread E_MD7KH2KO77 “might provide information about a path to the goal.” |
| 3 /9 | PASS | “We have read three events” is true; the remaining listed E_NVHXWA5WMT “may provide information about the path to the goal.” This is a minimally useful remaining-information/goal account, not proof of an optimal search policy. |
| 4 /10 | PASS | “P_FS55PCAO72 leads from N_JJDBDX5757 to N_E3ACGSRKC2, and from there, P_WV4NANY2D5 leads to the goal” matches the two observed edges. The target calls the first route a “first step,” not immediate final arrival. |
| 5 /11 | PASS | “directly reachable from the current node N_E3ACGSRKC2 via the port P_WV4NANY2D5, as evidenced by the event E_NVHXWA5WMT” agrees with the actual preceding transition and previously read final edge; predicts arrival at the goal. |

Episode A is **not admitted**: two failed turns exclude all six rows in every
supervision view, despite actual action success.

## Episode B: shard3 TRAIN-A/task/3

| Turn / call | Decision | Raw support and public-evidence justification |
|---|---|---|
| 0 /3 | PASS | “has not been read yet, and the other events have not been observed” is correct. “We need to determine the path to the goal ... might provide useful information” identifies genuine uncertainty and the purpose of the first opaque read. |
| 1 /4 | UNRESOLVED | The recalled E_WTRHFKCZM2 relation is stated correctly, but the target promises “Reading E_UFANKFCP4J will provide information on the path from N_23TLGYOU42 to the goal or a relevant node.” No observed address-to-edge mapping licenses that specific expectation. It might be broad planning language rather than an asserted edge origin; exclude rather than silently resolve the ambiguity in favor of admission. |
| 2 /5 | FAIL | “the only unread event is E_NTJMK7TUB5” is false: both E_NTJMK7TUB5 and E_FYXV2CBZSA remain unread in the actual prefix. The two already observed outgoing edges are otherwise correctly described. |
| 3 /6 | PASS | “We have read three events” and the named CURRENT/GOAL are correct; the remaining event is identified for resolving the route. “information about the path from N_3YUM2XSVJ6” is read as a planning purpose, not an assertion that the unseen record's edge originates there. Minimal useful floor, not exceptional richness. |
| 4 /7 | PASS | “P_5G3LPTWS3J leads ... to an intermediate node N_23TLGYOU42, which is one hop closer to the goal” agrees with the two observed connected edges; forecast remains one hop from the goal after this first route. |
| 5 /8 | PASS | “P_ZNTSVLEQAB leads from N_23TLGYOU42 to N_7KYAISJAXO, as evidenced by the event E_FYXV2CBZSA” uses actual current state and the observed final edge; predicts the goal-reaching transition. |

Episode B is **not admitted**: one false unread-count claim independently
excludes the episode, regardless of how the ambiguous turn1 is adjudicated.

## Decision and limits

Author turn counts:8PASS,3FAIL,1UNRESOLVED. Qualified episodes0/2; admitted
rows0/12 in TERSE,RICH,RICH_ACTION_ONLY. The full collection denominator remains
64attempted episodes,2action-complete,62format-rejected; no claim that the
unexecuted episodes lack useful content. No fitting or target replacement.
The two supplied episodes also span only two worlds and no complete opposite-
goal pair, so they would be inadequate for a broad rich-transfer comparison
even if their content all passed.

The useful next learning target is concrete: distinguish reading historical
memory from a current transition, track which records remain unread, and avoid
claiming unseen edge facts. These are content errors; accepting the optional
colon after RATIONALE in a separate prospective parser does not fix them.
Keep action syntax, content correctness, learning after a write, and autonomous
learning efficiency as separate observations.
