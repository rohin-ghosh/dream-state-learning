# Rich action-first V2 — independent twelve-turn content review

2026-09-14. **Released.** Independent decision: **6 PASS, 3 FAIL,
3 UNRESOLVED; 0/2 eligible episodes and 0/12 admitted rows in each of
TERSE, RICH and RICH_ACTION_ONLY.** Both episodes contain decisive factual
failures, regardless of the unresolved judgments. Main's episode exclusions
agree; two turn-level PASS judgments remain disputed below. No fit is approved.

SEQ262's `2026-09-14_goal_quality_collection_independent_result.md` is ready
to commit, with ownership already released. It is not changed by this review.

## Scope and evidence

Read all twelve raw responses and their own pre-action public prefixes against
the rubric before consulting Main's interpretation. No teacher plan, coached
prompt, PROBE score, successor code or later unseen feedback was consulted.

- Input: `gpu_artifacts_local/astra_rich_action_first_terminal_20260914_attempt1/CONTENT_REVIEW_INPUTS.json`;
  SHA256 `a43a3cba682f9be7f4135290f642b2dec7c889f285e4b7c9892097459a70ea53`.
- Rubric: `2026-09-14_rich_content_review_contract.md`;
  SHA256 `3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b`,
  matching the packet's contract binding.
- Compared Main's `2026-09-14_rich_v2_content_review.md` at SHA256
  `69ed4ab8c4b0c81d152d61bc581fe20b3e516ef6884382379000b607f88a5001`.

The input remains `UNREVIEWED`, `fit_ready=false`; this memo does not modify
it. Standard-library checks verify all twelve raw hashes, character/byte
projection spans, unique shard/call identities, source-hash consistency within
each episode, and continuity of pre-action prefixes. Each next prefix appends
the preceding exact projected action and actual supplied public feedback.
These are packet-integrity checks, not fresh native/source/outcome authentication.

The two episodes are supplied as action-complete candidates. The packet does
not contain final post-action feedback or a full native replay certificate;
I do not independently recertify that outcome prerequisite here. Their content
exclusions hold even assuming the separately checked action successes.

## Episode A: shard0 TRAIN-B/task/2

Full ID: `ASTRA-RICH-20260914-V1-SHARD-0-TRAIN-B/task/2`.
Source hash: `f1dc184d7ddd3a542854dc9d5942f09e29b9faf75dfb3931453c229cc4514789`.
Initial CURRENT `N_JJDBDX5757`, GOAL `N_C5DE7IUUIT`, displayed ports
`P_FS55PCAO72,P_XSL3QAYWAT`. Calls below are shard-local; turns are zero-based.

| Turn / exact call ID | Decision | Supporting raw span and pre-action reasoning |
|---|---|---|
| 0 / shard0 `CALL_006` | FAIL | “has no direct route to the goal” asserts a hidden edge property before any memory read. The task exposes port names, not destinations. The later “might provide information” is appropriate uncertainty but does not retract the unsupported assertion. |
| 1 / shard0 `CALL_007` | FAIL | “The current node N_JJDBDX5757 has been reached via port P_FS55PCAO72” reverses/confuses the recorded relation. The sole observed EVENT says **AT** N_JJDBDX5757, **DID** P_FS55PCAO72, **GOT** N_E3ACGSRKC2; only READ has occurred, not a current transition. The otherwise sensible next inspection does not repair this claim. |
| 2 / shard0 `CALL_008` | PASS | “P_FS55PCAO72 led to N_E3ACGSRKC2 and P_XSL3QAYWAT led to N_UFHNUIY4E2. Neither of these nodes is the goal” correctly connects both observed edges to the remaining route-choice problem. E_MD7KH2KO77 is unread and “might provide information about a path to the goal”; no unread content is asserted. |
| 3 / shard0 `CALL_009` | UNRESOLVED | “We have read three events” and the listed CURRENT/ports/GOAL are correct. “E_NVHXWA5WMT, which may provide information about the path to the goal” is a legitimate possibility, but the rationale never connects the three observed edges to the information still needed to distinguish the branches. Whether this name-list plus generic expectation meets the substantive later-READ floor is unresolved, not a factual-falsity finding. |
| 4 / shard0 `CALL_010` | PASS | “P_FS55PCAO72 leads from N_JJDBDX5757 to N_E3ACGSRKC2, and from there, P_WV4NANY2D5 leads to the goal” explains the observed connected route. This identifies the goal-reaching branch rather than merely naming a port. “the first step towards the goal” forecasts an intermediate move, not premature final arrival. |
| 5 / shard0 `CALL_011` | PASS | “directly reachable from the current node N_E3ACGSRKC2 via the port P_WV4NANY2D5, as evidenced by the event E_NVHXWA5WMT” agrees with the preceding public CURRENT update and observed remaining edge. “will lead to the goal” is the appropriate final-route forecast. |

Episode A: **3 PASS / 2 FAIL / 1 UNRESOLVED; not eligible**. Its two factual
failures independently exclude all six rows from all three supervision views.

## Episode B: shard3 TRAIN-A/task/3

Full ID: `ASTRA-RICH-20260914-V1-SHARD-3-TRAIN-A/task/3`.
Source hash: `ad309ec63593bf000f63f4fb9953743ee4ae8fac327dc337a7d3b472afdf845c`.
Initial CURRENT `N_3YUM2XSVJ6`, GOAL `N_7KYAISJAXO`, displayed ports
`P_AQF5BVWXWZ,P_5G3LPTWS3J`.

| Turn / exact call ID | Decision | Supporting raw span and pre-action reasoning |
|---|---|---|
| 0 / shard3 `CALL_003` | PASS | “has not been read yet, and the other events have not been observed” correctly states first-read uncertainty. “We need to determine the path to the goal ... might provide useful information” links the listed opaque address to inspection without inventing its hidden edge. This is the rubric's appropriate first-read uncertainty allowance. |
| 1 / shard3 `CALL_004` | UNRESOLVED | The recalled E_WTRHFKCZM2 edge is correct, but “Reading E_UFANKFCP4J will provide information on the path from N_23TLGYOU42 to the goal or a relevant node” promises information more specific than the public address licenses. A broad planning-purpose reading is possible; an asserted mapping to that intermediate-node path is unsupported. Do not resolve that ambiguity toward admission or use the next turn's receipt retroactively. |
| 2 / shard3 `CALL_005` | FAIL | “the only unread event is E_NTJMK7TUB5” is false in this prefix: E_FYXV2CBZSA is also listed and unread. This materially misstates the available evidence/search state. The correct descriptions of the two observed outgoing edges do not cancel the error. |
| 3 / shard3 `CALL_006` | UNRESOLVED | “E_FYXV2CBZSA, which will provide information about the path from N_3YUM2XSVJ6” may describe a broad planning purpose, not an edge-origin assertion. However, “necessary to understand the current state and potential routes to the goal” remains generic and does not explain the unresolved branch after the three observed records. The useful later-READ floor and the intended strength of the forecast remain ambiguous. |
| 4 / shard3 `CALL_007` | PASS | “P_5G3LPTWS3J leads directly from the current node to an intermediate node N_23TLGYOU42, which is one hop closer to the goal” expresses the observed connected two-hop relation, not an arbitrary name list. “reducing the distance to one hop” predicts the intermediate state correctly. The rubric permits relational references; verbatim repetition of the final edge or every rejected alternative is not required. |
| 5 / shard3 `CALL_008` | PASS | “P_ZNTSVLEQAB leads from N_23TLGYOU42 to N_7KYAISJAXO, as evidenced by the event E_FYXV2CBZSA” uses the actual updated CURRENT and observed remaining edge. “will directly move us to the goal node” is grounded as a forecast. |

Episode B: **3 PASS / 1 FAIL / 2 UNRESOLVED; not eligible**. The false unread
count alone excludes all six rows irrespective of either ambiguous READ.

## Comparison with Main and disposition

Main reports 8 PASS / 3 FAIL / 1 UNRESOLVED. We agree on ten of twelve turn
labels, including all three decisive FAILs and shard3 CALL_004's ambiguity.
The two differences are:

| Exact call | Main | Independent | Open issue |
|---|---|---|---|
| shard0 `CALL_009`, turn3 | PASS | UNRESOLVED | Main accepts a “minimally useful remaining-information/goal account.” I cannot establish that the generic possibility, following a list of known IDs, satisfies the rubric's substantive uncertainty/inspection account at this later read. |
| shard3 `CALL_006`, turn3 | PASS | UNRESOLVED | Main reads the forecast as planning purpose and accepts a minimal floor. That reading is possible, but neither its relation to the unresolved alternatives nor its strength is sufficiently clear for my PASS. |

Disputed call hashes respectively:
`030abc2f742303481f42ee25a2b269f367c34a1e003825178923f87cb3c6c9dc`
and `8b7dccea3bdfab9bb0e22963b9c8108663674958ecc9f6c6c85f5e9aa1f2bf8e`.
These are retained disagreements, not adjudicated consensus. They do not allege
that every generic forecast is false, require a PREDICTION heading, or penalize
the unavoidable uncertainty of the first opaque read. They concern the existing
rubric's distinction between substantive later inspection and generic padding.
Do not silently merge either review's marginal turn counts into the other's.

**Episode-level disposition is settled by independent failures:** qualified
episodes 0/2, admitted rows 0/12 in each shared supervision view, selected
world/goal/display coverage zero. The reviewed packet covers two TRAIN worlds,
one goal/display instance each, and no complete opposite-goal pair. Preserve
both rejected episodes, all twelve raw turns and both sets of judgments. No
synthetic repair, subset of individually passing turns, or TERSE-only rescue
is licensed by the all-six-turn shared-admission rule.

## Limits and release

This is substantive content review of the supplied twelve turns, not fresh
whole-capsule approval, factual validation of the other attempted episodes,
verification of the full collection denominator, or an internal-reasoning
certificate. Successful execution cannot retrospectively support pre-action
claims. Zero content-qualified candidates does not establish that rich targets
cannot help after learning; no weights or efficacy comparison are examined.

Checks used local `cat`/`jq`/`sha256sum` and inline standard-library Python for
packet integrity only. No source code, model/tokenizer, GPU, network, extra
native calls or outside files were accessed for content evidence. Only this
memo is written. Whitespace checks cover this memo and the released SEQ262
memo; no commits are made. Ownership released for Main to bind, with the two
non-admission-affecting turn disagreements explicitly preserved.
