# Child corrective selection: two sourced choices, utility untested

2026-09-14. Bounded read-only audit of node2 `/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY/select_corrective` (**R**). Only this memo is written; earlier code scopes remain released. No model/tokenizer loads, GPU calls, fitting, relaunch, remote changes or new custody files. Captured data were streamed into memory for pure replay, not regenerated.

## Disposition and exact choices

**SOURCE VALIDITY PASS: 2/2 child selections admitted.** The four-task BEFORE panel contains two actual committed wrong-goal outcomes, at zero-based route indexes **1 and 2**. Exactly one fresh selection call was made per such case. Source indexes **0 and 2** were selected from the four original records. Neither choice is replaced, repaired or filtered by whether its outcome equals the requested goal.

| Call | Route index | Public requested GOAL | Actual committed port → observed destination | Child source index / selected EVENT | Selected GOT |
|---|---:|---|---|---|---|
| 0 | 1 | `N_6AUMRWYCVK` | `P_MLFJXQ3WZH → N_WBXQVETNWG` | 0 / `E_43DKZR6D3S` | `N_WBXQVETNWG` |
| 1 | 2 | `N_ZXFXLP2ESD` | `P_FWMNJO5UYN → N_DH2AYPUMUT` | 2 / `E_QQ43NOEYBQ` | `N_ZXFXLP2ESD` |

Call0 selects the exact record of the option that just failed to reach the requested goal. **It remains admitted:** this may supply evidence for avoiding that option. No claim is made that the child explicitly reasoned that way or that replay will help. Call1 selects a sourced record whose outcome matches the requested goal. Outcome/goal equality is **1/2 as an analysis annotation, not a correctness/admission score**. Downstream matched learning outcomes, not a new semantic filter, decide usefulness.

Exact raw strings, with no terminal LF or other suffix in either:

```text
EVENT E_43DKZR6D3S AT N_NQ7SZP2WK3 DID P_MLFJXQ3WZH GOT N_WBXQVETNWG EVIDENCE R_V75J4A4RYG
```

```text
EVENT E_QQ43NOEYBQ AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD EVIDENCE R_6MJCDE77X2
```

Both generations are terminal/untruncated and end their emitted token-ID arrays with **151645 (EOT)**. Calls have **1016/1006 input tokens** and **54/52 emitted token IDs**: totals2022 input/106 emitted. Canonical targets add only the one terminal LF prescribed by `FINAL_LF_ONLY`; all identifiers and original raw outputs remain unchanged. No abstention, unsupported output, retry or best-of selection appears.

## Prompt visibility, order and callback verification

The frozen helper reconstructs all four original route episodes using the existing controller and their captured responses/transitions. Cases are chosen by comparing **observed destination against public GOAL**, not by using `reached_goal` as an input feature. Each case is a fresh system/user pair. Its public payload contains only:

- `public_task`: recorded NODE, GOAL and offered PORT/EVENT lists;
- `public_route_transcript`: the actual seven-message system/user/actor/reader history, including both raw reader responses and the final committed ROUTE;
- `actual_transition_outcome`: source node, committed port and explicitly labelled observed destination from the actual transition trace;
- `own_public_event_records`: **all four** original raw own EVENT records and corresponding public receipt lines, in source order0,1,2,3.

The instruction asks for one exact already-experienced EVENT most useful to correct the outcome, permits NONE, and requires neither W citations nor rationale/novelty. It explicitly distinguishes reader replies from verified outcomes. No hidden bank dictionary, scorer, `reached_goal`, terminal-reason label, expected answer or token metadata is projected into the prompt. Original erroneous reader text is preserved, not replaced with correct records inside the route history. The separate four-record evidence list is explicitly supplied own experience, not evidence of parametric recall during selection.

Each `CALL_000/001.json` exactly joins its SELECTION capture's call index, prompt, response and null error. Each captured response's `messages` equals its corresponding case prompt. Order is route1 then route2, and no extra callback is recorded. All four original BEFORE episode files join the panel and its RESULT; the source receipt's seven BEFORE file hashes match actual bytes. Collection and collection-RESULT hashes also match their source bindings.

## Source rows: mechanical views, no semantic correction

The original32 collection rows are wrapper-major, four source events per wrapper. Selected row indexes are zero-based:

| Selected source | Original row indexes, W0 through W7 |
|---|---|
| 0 | `[0, 4, 8, 12, 16, 20, 24, 28]` |
| 2 | `[2, 6, 10, 14, 18, 22, 26, 30]` |

The emitted `row_source_indexes` concatenate these groups in selection-call order. All **16 material origins** join the original row event, source-raw hash, canonical target hash and row index. They are eight mechanical views per selected record, **not16 independently selected facts**. This actual output has no duplicate source choice; the helper preserves duplicates if made. It does not rewrite first-adult records or manufacture a goal-matching target.

## Actor, source and no-fit receipts

Frozen source: **`d13e017c`**. Native runner bytes from that commit match RESULT's runner hash. The pure corrective helper bytes match `CORRECTION_SOURCE.json`; executing that frozen helper locally over stored data exactly reconstructs CORRECTION_CASES and replays SELECTION, including all16 origins. No model callback is used in this replay.

Native RESULT, correction provenance, collecting receipt and BEFORE receipt agree on the A1 cue actor state:
`07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`.
Initial training RESULT is `3eaad009cc1546fa62209a1871b0b129140db485afc4676f057a93333faf8046`; requested adapter file hash is `7e6fe380553b20e23b63f5934199fb04a44388079ce3fcc68b0ccbb9e9602f26`.
The minimal pure SELECTION bundle has `actor_state_sha256=null` by design; **native provenance supplies the actor binding**, not that field alone. These are receipt joins, not fresh weight measurements.

Status is `SELECTION_CAPTURED_NO_FIT`, with `model_calls=2`, `fits=0`, `parent_present=false`, `own_experience_actor=true`, `task_denominator=4`, `actual_wrong_goal_cases=2`, `admitted_selections=2` and frozen-base-unchanged true. No FAILED file exists. REQUEST/RESULT arguments agree; prefix preflight `[1016,1006]` matches captures. The receipt's `SOURCE_VALID_SELECTION_ONLY_NO_FIT_AUTHORIZATION` describes this stage; this audit neither launches a fit nor withdraws Main's separately declared matched100-step authorization.

## Exact SHA256 receipts

Seven StageA JSON files total **69,552 bytes**, read without copying to a new custody directory.

| R-relative file / source | SHA256 |
|---|---|
| `CORRECTION_SOURCE.json` | `8f71337514d6b9d2e6fbaa1846d47905533f9824b263d90d6d429f2d970fd9a2` |
| `CORRECTION_CASES.json` | `675f8617e2c32749c3f11c972f69c5c3cc20e3241fe4adcadd396f16ed7d1b45` |
| `SELECTION.json` | `f27a29e69ea31acde78cdb2a4dc8a5011d5fe535443fecd23446d369acc0d361` |
| `RESULT.json` | `6fad939ddb10dc22f2ff0ae6d36734f5b4dc1bef510824619bf139445f6212dc` |
| `REQUEST.json` | `2f1b07fd65cac2601e6bb2d7e0970f1637775ffe64b57d5c2d8fb33add7365e3` |
| `CALL_000.json` | `58a2d906eeef5546c811ae54a82bfebeac3af43bb4243973ac58394f232eaa4c` |
| `CALL_001.json` | `9849ab2da05e599ccdf9da1c31c285082e7c7a1e221c99dfd5b8691d27f26b9b` |
| BEFORE RESULT | `f5002ab8c8056034fb71e5d3546698aba23bb6068255b0313a9a252dc32f779a` |
| Frozen native runner | `2e8b2485c9d16e535d2e31af91c01631613bf4c6fabe18170dd87cca9610fa39` |
| Frozen corrective helper | `24716244dbb919f2e909598655b8cd184a8e83368e6d3b8732855c517134f2e3` |

**Boundary:** child choice under an externally posed, public-error selection task is observed. Learned autonomous error detection, beneficial extraction, learning efficiency, retention benefit and H1/H2 are not established by StageA. No goal-correctness filter is added. Memo complete and scope released; paired-sleep work is not gated by this review.
