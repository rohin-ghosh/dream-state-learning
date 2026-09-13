# Bounded C0 failure review — 2026-09-13

Read-only, post-unblinding review for Main. Evidence checked at approximately
13:59 UTC. No repository/code edits, model calls, prompt changes, relaxed
parsing, GPU/remote operations, or commits. Main's independent own-write work
is outside this review. This document is the only written artifact.

## Finding

**Missing terminal LF does not explain these failures. A universal
format-only explanation is contradicted by the fixed sample.**

- All **30/30 sampled outputs lack terminal LF**. The frozen ROUTE, PROBE and
  READ patterns do **not** require LF; they use `re.fullmatch` without a terminal
  newline in the pattern. **19/30 outputs pass the applicable final grammar**,
  including all three sampled successes. EVENT/LINK memory rows have a different,
  LF-terminated grammar; that requirement does not apply to final ROUTE/PROBE.
- Delayed sample: **0/20 correct; 14/20 valid ROUTE syntax but wrong routes**.
  Of those 14, **13 are illegal paths and one is legal but reaches the wrong
  destination**. These failures are not explainable by punctuation or LF.
- The other **6/20 delayed outputs fail final ROUTE syntax**: two unsupported
  multi-line READ responses; two malformed graph-panel ROUTEs; two invented
  placeholder-port ROUTEs in NONE_OFF. The comma-spaced graph response also
  visibly lists a wrong port sequence; it is not merely a spacing issue.
- Reachout sample: **3/10 correct; 2/10 valid PROBEs choose the distractor;
  5/10 substitute a non-probe identifier** (four option numbers, one EVENT ID).
  The two valid distractor choices independently rule out an all-format account.
- In the **2/2 sampled delayed ACTIVE_LINKED_TEXT requests**, the model is told
  to issue a permitted READ but neither message spells out `EVENTS_AT`,
  `LINKS_FROM`, or `READ EVENT`. Both replies issue two bare `READ N_...` lines.
  This documents a service-dialect disclosure limitation alongside observed
  protocol failure, not evidence that a disclosed, working READ service was
  exercised and found unhelpful. No corrected prompt or query was run.

These are **sample descriptions, not estimates of failure-type prevalence
across 800 tasks**. The macro tables below separately confirm the existing
inspection's full-capture aggregates.

## Evidence and exact sampling boundary

Base directory (repository-relative):
`gpu_artifacts_local/pcfl_c0_zero_fit_20260913_attempt2/`.

- Inspection: `inspection_v3/inspection.json`.
- Diagnostic: `unpacked/pcfl_c0_zero_fit_20260913_attempt2/`.
- Original outer failure: `unpacked/pcfl_c0_zero_fit_20260913_attempt2.outer/finalize_failure.json`.
- Selection: traverse the sealed manifest's task list in its existing order;
  take the **first two tasks for each `(panel, projection)`**, regardless of
  outcome. Ten delayed projections and five reachout projections yield **30
  tasks**, not two per root or two per render. Selected indices are **0–19 and
  160–169**. Every selected task is from **excluded/0**. Delayed pairs are the
  two goals for old/relevant/distractor state `0/0/0`; reachout pairs are RA/RB
  for the first fixed cell. No sample expansion based on failures occurred.

For each selected index `i`, checked `task_{i:03}.json`,
`call_{i:04}_request.json`, `call_{i:04}_response.json`, and the actor's matching
`.request.json`, `.render.json`, `.raw.json`, `.response.json`: **210 files**.
Each file's bytes/size match the original capture inventory. The request ID
matches the selected task hash and `/actor/0`; request messages equal the
manifest public messages. Actor raw text, decoded bytes/hex, outer response,
task raw and report row agree. Request/response hashes and task raw hashes agree.

Used the **unchanged frozen `Replay` and existing strict scorers** on each
selected call only, with its recorded call ordinal. A selected-record-only
reader forbade reads beyond that call's bound receipts. All 30 reconstructed
rows equal the stored task/report rows; each consumes exactly one call and
zero service token-count operations. This is strict original-receipt checking,
not relaxed rescoring, a model retry, or a rerun of the full inspector.

For full-capture macros, independently regrouped the existing report's
task/result metadata and checked all **122 inspection strata** for task counts,
denominators, success, invalid READ, usable-false-row flag, served reads,
returned tokens and output tokens. Panel tables agree with both report panels
and the frozen `_panels` aggregation of stored results. All inspection counter
partitions sum consistently across roots, panels and projections; RA/RB sums
match reachout projection totals (float tolerance only for elapsed costs).
Full-capture invalid-syntax/truncation totals are **inspection counters checked
for internal aggregation consistency**, not newly classified raw responses
outside the sample. Source snapshots match the manifest and inspection pins.

## Independently confirmed macro tables — existing full capture

All denominators are fixed. Every panel has `missing=0`.
"Pass" below means only its declared numerical interval, never usability or
scientific release. The eight positive-floor panels all fail. RAW_EPISODIC has
a vacuous `0..64` interval, not a positive performance requirement.

| Delayed projection | Correct / fixed denominator | Invalid final syntax | Invalid READ | Declared interval | Interval pass |
|---|---:|---:|---:|---:|---|
| EXACT_WITNESSED_GRAPH | 0/64 | 52 | 0 | 60..64 | No |
| FULL_CHILD_TEXT | 0/64 | 20 | 0 | 60..64 | No |
| EVENT_ATOMS_TEXT | 0/64 | 22 | 0 | 60..64 | No |
| ACTIVE_LINKED_TEXT | 0/64 | 64 | 64 | 60..64 | No |
| NATIVE_CONTEXT | 0/64 | 20 | 0 | 60..64 | No |
| RAW_EPISODIC | 0/64 | 26 | 0 | 0..64 | Yes, unconstraining |
| OLD_ONLY_TEXT | 0/64 | 8 | 0 | 0..36 | Yes |
| NEW_ONLY_TEXT | 0/64 | 52 | 0 | 0..36 | Yes |
| NONE_OFF | 0/64 | 64 | 0 | 0..20 | Yes |
| WRONG_ROOT | 0/64 | 16 | 0 | 0..20 | Yes |
| **Delayed total** | **0/640** | **344** | **64** | — | — |

| Reachout projection | Correct / fixed denominator | Invalid final syntax | RA correct/16; invalid | RB correct/16; invalid | Declared interval | Interval pass |
|---|---:|---:|---|---|---:|---|
| EXACT_WITNESSED_GRAPH | 6/32 | 7 | 6/16; 4 | 0/16; 3 | 30..32 | No |
| FULL_CHILD_TEXT | 5/32 | 10 | 3/16; 0 | 2/16; 10 | 30..32 | No |
| ACTIVE_LINKED_TEXT | 8/32 | 20 | 8/16; 4 | 0/16; 16 | 30..32 | No |
| NONE_OFF | 16/32 | 14 | 16/16; 0 | 0/16; 14 | 0..18 | Yes |
| WRONG_ROOT | 16/32 | 16 | 16/16; 0 | 0/16; 16 | 0..18 | Yes |
| **Reachout total** | **51/160** | **67** | **49/80; 8** | **2/80; 59** | — | — |

| Root | Correct / fixed denominator | Invalid final syntax | Invalid READ |
|---|---:|---:|---:|
| excluded/0 | 13/200 | 81 | 16 |
| excluded/1 | 13/200 | 98 | 16 |
| excluded/2 | 10/200 | 124 | 16 |
| excluded/3 | 15/200 | 108 | 16 |
| **All** | **51/800** | **411** | **64** |

Full-capture costs/counters: **800 calls**, **426,480 prompt tokens**,
**25,968 output tokens**, **64 READ-request responses**, **0 served reads**,
**0 returned tokens**, **0 truncated calls/tasks**, **0 usable-false-row flags**.
The last flag is the frozen memory-row metric, not evidence that no wrong-root
identifiers occurred in ROUTEs/PROBEs. The sample below demonstrates that distinction.
Recorded generation wall time is **783.9643 s**, call-operation wall time
**804.7470 s**, actor elapsed **842.1160 s**, cold model load **21.6920 s**,
diagnostic through close **855.7135 s**, and outer entry through capture
**994.1862 s**. These are not GPU-active timing measurements.

Interpretation: supplied positive-floor conditions do not meet their declared
ceilings; baseline upper-bound passes do not establish a working positive assay.
The observed reachout baseline counts exceed the positive supplied-panel counts,
but this is not evidence that memory causally hurts. The RA/RB split is pronounced
and the sampled requests visibly reorder and rephrase options. The existing
one-token RA/RB length difference and wording/order differences prohibit an
order-only causal claim. No learning/H1/H2/C11/full-assay claim follows.

## Fixed sample counts — no extrapolation

| Sample | Tasks | Correct | Grammar accepted | Invalid final syntax | Invalid READ | Terminal LF present | Truncated |
|---|---:|---:|---:|---:|---:|---:|---:|
| Delayed | 20 | 0 | 14 | 6 | 2 | 0 | 0 |
| Reachout | 10 | 3 | 5 | 5 | 0 | 0 | 0 |
| **Total** | **30** | **3** | **19** | **11** | **2** | **0** | **0** |

Each sampled raw generation has `finish_reason="stop"`, not `length`.
Invalid READ is an overlapping tag, not an additional task count: the two
delayed READ failures are included among the six delayed invalid final syntaxes.

## Per-task delayed ledger

For every row, both requested START and GOAL are the literal identifiers in
the raw transcript. Correct paths for the sampled cell, supplied here only as
the unchanged scorer/oracle reference, are:

```text
goal 0: ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH,P_RK7VLTKHNM
goal 1: ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH,P_FOPIRGXLPW
```

No invalid answer was cleaned, completed, or passed to an alternate parser.
The ledger's raw column is JSON string notation: `\n` represents an actual
internal LF; quotes are delimiters, not part of the response. None has terminal LF.

| Index and exact fixed task ID | Exact raw response (JSON notation) | Observed classification |
|---|---|---|
| 000 — `delayed/excluded/0/0/0/0/0/EXACT_WITNESSED_GRAPH` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT, P_CFZQL5YFH3, P_RK7VLTKHNM"` | Syntax: spaces after commas. Also lists the start's alternative port after taking the first branch and omits required intervening ports. Lexical/edge comparison only; no relaxed score. |
| 010 — `delayed/excluded/0/0/0/0/1/EXACT_WITNESSED_GRAPH` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : CFZQL5YFH3,IPQ2WLA2DK,BMWO7JVOOV,FOPIRGXLPW"` | Syntax/identifier substitution: drops typed prefixes and mixes node-ID bodies with port-ID bodies. Not a whitespace-only error. |
| 001 — `delayed/excluded/0/0/0/0/0/FULL_CHILD_TEXT` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_CFZQL5YFH3,P_US3ABWJMJ3,P_RK7VLTKHNM"` | Grammar valid; illegal second hop: `P_CFZQL5YFH3` is unavailable at `N_IPQ2WLA2DK`. |
| 011 — `delayed/excluded/0/0/0/0/1/FULL_CHILD_TEXT` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_4RWKAJVRXP,P_FOPIRGXLPW"` | Grammar valid; illegal first hop: `P_4RWKAJVRXP` does not leave START. |
| 002 — `delayed/excluded/0/0/0/0/0/EVENT_ATOMS_TEXT` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_CFZQL5YFH3,P_JFTRJJNMXM,P_RK7VLTKHNM"` | Grammar valid; illegal second hop at `N_IPQ2WLA2DK`. |
| 012 — `delayed/excluded/0/0/0/0/1/EVENT_ATOMS_TEXT` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_7MGNA5ALJT,P_CFZQL5YFH3,P_Z24XENARRH,P_RK7VLTKHNM,P_FOPIRGXLPW"` | Grammar valid; illegal second hop at `N_IPQ2WLA2DK`. |
| 003 — `delayed/excluded/0/0/0/0/0/ACTIVE_LINKED_TEXT` | `"READ N_S6JZXHYXBT\nREAD N_HJZRZAYWOT"` | Unsupported READ dialect plus two lines in one response. No operation name, no valid service call, no final ROUTE. |
| 013 — `delayed/excluded/0/0/0/0/1/ACTIVE_LINKED_TEXT` | `"READ N_S6JZXHYXBT\nREAD N_6TUR2VALJP"` | Same unsupported READ/multi-line failure. No service was served. |
| 004 — `delayed/excluded/0/0/0/0/0/NATIVE_CONTEXT` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_CFZQL5YFH3,P_US3ABWJMJ3,P_RK7VLTKHNM"` | Grammar valid; illegal second hop. Same response as sampled FULL_CHILD_TEXT goal 0. |
| 014 — `delayed/excluded/0/0/0/0/1/NATIVE_CONTEXT` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_4RWKAJVRXP,P_FOPIRGXLPW"` | Grammar valid; illegal first hop. Same response as sampled FULL_CHILD_TEXT goal 1. |
| 005 — `delayed/excluded/0/0/0/0/0/RAW_EPISODIC` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_JFTRJJNMXM,P_RK7VLTKHNM"` | Grammar valid; illegal second hop: `P_JFTRJJNMXM` does not leave `N_IPQ2WLA2DK`. |
| 015 — `delayed/excluded/0/0/0/0/1/RAW_EPISODIC` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_CFZQL5YFH3,P_US3ABWJMJ3"` | Grammar valid and path legal, but ends at `N_MBUDGF5J4B`, not requested `N_6TUR2VALJP`. Direct substantive wrong-destination example. |
| 006 — `delayed/excluded/0/0/0/0/0/OLD_ONLY_TEXT` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_CFZQL5YFH3,P_RK7VLTKHNM"` | Grammar valid; illegal second hop. This is an intentionally incomplete-memory control, not a positive ceiling. |
| 016 — `delayed/excluded/0/0/0/0/1/OLD_ONLY_TEXT` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_CFZQL5YFH3,P_4RWKAJVRXP,P_FOPIRGXLPW"` | Grammar valid; first hop reaches `N_DPH5JSJYDT`, where second port `P_4RWKAJVRXP` is unavailable. |
| 007 — `delayed/excluded/0/0/0/0/0/NEW_ONLY_TEXT` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_US3ABWJMJ3"` | Grammar valid; copies the new edge's port but it does not leave START. Intentionally incomplete-memory control. |
| 017 — `delayed/excluded/0/0/0/0/1/NEW_ONLY_TEXT` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_US3ABWJMJ3"` | Same illegal-first-hop failure. |
| 008 — `delayed/excluded/0/0/0/0/0/NONE_OFF` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : PX_KL,QR_WV"` | Invented placeholder identifiers; not the registered `P_` grammar or task ports. No-memory control. |
| 018 — `delayed/excluded/0/0/0/0/1/NONE_OFF` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : PORT_A,PORT_B"` | Invented placeholder ports; syntax/identifier failure, not LF. |
| 009 — `delayed/excluded/0/0/0/0/0/WRONG_ROOT` | `"ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_CU72HSSTHQ,P_PG3IQT75KG,P_YPCPRH2RM6,P_O66CHZFQQF,P_QKUOHFCFN7,P_CLTAYE7KH3,P_RPRTAHQJHF,P_6MHKGVAZYV"` | Grammar valid, but copies foreign-memory ports; first port has no edge from the task START. Wrong-root control. |
| 019 — `delayed/excluded/0/0/0/0/1/WRONG_ROOT` | `"ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_CU72HSSTHQ,P_PG3IQT75KG,P_YPCPRH2RM6,P_O66CHZFQQF,P_QKUOHFCFN7"` | Grammar valid; same foreign-port/illegal-first-hop issue. |

The actual supplied GRAPH, FULL_CHILD_TEXT, EVENT_ATOMS_TEXT, NATIVE_CONTEXT
and RAW_EPISODIC requests for this cell contain the necessary witnessed route
information in their respective representations. Several sampled responses
nonetheless concatenate ports that are not consecutive outgoing edges. This
is an observed sequence error; it does not establish a model-wide inability
to reason about routes. OLD_ONLY/NEW_ONLY/NONE/WRONG_ROOT lack the same full
task information by design and are not interpreted as equivalent positive tests.

## Per-task reachout ledger

In all ten sampled public tasks, the relevant probe is `Q_VHFOFINGM6`
(tests `N_APBZHN7V4U` to `N_UD6BFQ7GOI`), and the distractor is `Q_GODB62ZVN2`
(tests `N_DPH5JSJYDT` to `N_MBUDGF5J4B`). RA lists the relevant probe first;
RB lists it second and changes the prose template. Each public prompt says
`Commit exactly: PROBE <probe_id>`.

| Index and exact fixed task ID | Exact raw response (JSON notation) | Observed classification |
|---|---|---|
| 160 — `reachout/excluded/0/0/0/RA/EXACT_WITNESSED_GRAPH` | `"PROBE Q_GODB62ZVN2"` | Grammar valid, actual distractor selected. |
| 165 — `reachout/excluded/0/0/0/RB/EXACT_WITNESSED_GRAPH` | `"PROBE 1"` | Option number substituted for an opaque probe ID; invalid grammar. Displayed option 1 is the distractor. No ordinal-to-ID rescoring. |
| 161 — `reachout/excluded/0/0/0/RA/FULL_CHILD_TEXT` | `"PROBE Q_GODB62ZVN2"` | Grammar valid, actual distractor selected. |
| 166 — `reachout/excluded/0/0/0/RB/FULL_CHILD_TEXT` | `"PROBE 2"` | Option number substituted; invalid grammar. Displayed option 2 is relevant, but the response is not repaired or credited. |
| 162 — `reachout/excluded/0/0/0/RA/ACTIVE_LINKED_TEXT` | `"PROBE Q_VHFOFINGM6"` | Correct exact probe; no READ issued. |
| 167 — `reachout/excluded/0/0/0/RB/ACTIVE_LINKED_TEXT` | `"PROBE 2"` | Option number substituted; invalid grammar. No correction or extra credit. |
| 163 — `reachout/excluded/0/0/0/RA/NONE_OFF` | `"PROBE Q_VHFOFINGM6"` | Correct exact probe, from the visible options without supplied memory. |
| 168 — `reachout/excluded/0/0/0/RB/NONE_OFF` | `"PROBE 1"` | Option number substituted; invalid grammar. Displayed option 1 is the distractor. |
| 164 — `reachout/excluded/0/0/0/RA/WRONG_ROOT` | `"PROBE Q_VHFOFINGM6"` | Correct exact probe despite wrong-root supplied memory; not a learning claim. |
| 169 — `reachout/excluded/0/0/0/RB/WRONG_ROOT` | `"PROBE E_K5POAYPVLH"` | EVENT ID copied from wrong-root memory instead of either listed `Q_` probe. Typed-identifier substitution, not punctuation/LF. |

Four ordinal outputs could be discussed as answer-encoding failures, but they
are not all even pointing to the relevant displayed option. Most importantly,
the two fully valid distractor responses and the valid wrong ROUTEs remain
substantive counterexamples to an all-format interpretation. This review does
not compute a hypothetical repaired score or claim that an alternate prompt
would fix any specified number of tasks.

## Exact grammar and runtime basis

- `organism_v6/pcfl_vertical_dev.py:68`: distinct EVENT/LINK/READ/ROUTE/PROBE
  patterns. ROUTE permits comma-separated typed ports with **no spaces after
  commas**; PROBE requires `Q_` plus ten `[A-Z2-7]` characters. Neither requires LF.
- `organism_v6/pcfl_vertical_dev.py:239`: `_parse` uses `re.fullmatch`; no stripping,
  Unicode normalization, prefix insertion, number-to-ID mapping or trailing-LF repair.
- `organism_v6/pcfl_vertical_dev.py:336`: `score_route` separately marks strict
  syntax, legal traversal and graph success against the requested start/goal.
- `organism_v6/pcfl_vertical_dev.py:869`: `read_query` first requires one exact
  `READ EVENT E_...`, `READ EVENTS_AT N_...`, or `READ LINKS_FROM E_...` command.
  A syntactically valid absent query would return MISS; the two sampled bare,
  multi-line READs fail before lookup. Both task query maps actually contain
  `READ EVENTS_AT N_S6JZXHYXBT` (19 registered queries each), but this review
  does not issue that query or count a hypothetical service response.
- `gpu/astra_pcfl_vertical_dev.py:278`: `_task` marks an invalid READ and stops;
  it does not split one output into multiple requests or retry generation.
  Reachout compares the exact parsed probe against the cell's relevant ID.
- `gpu/astra_pcfl_zero_fit_analyze.py:113`: frozen Replay reads archived receipts
  and calls this unchanged task/scoring path. No GPU/model backend was created.

## Original failure and release/claim boundary

The original failure file remains exactly:

```json
{"error":"CVD owner remains; release Main holder before finalization","type":"ActorError"}
```

The inspection's archived failed scan records `PermissionError` reading
`/proc/164452/environ`, `clear=false`, `reservation_check_status="BLOCKED"`,
and incomplete CVD visibility. That evidence explains the recorded finalizer
failure only; **this review makes no current-PID or hardware-release observation**.
Main owns the separate later release observations. No retry or retrospective
release attestation is added here.

`diagnostic_usable=false`, `finalization_failed=true`, and `full_v22_release=false`
remain in force. These are native captured diagnostic observations, not a
successful finalization/collection or full scientific release. The frozen full
analyzer's requirements remain unchanged. Main's two inspector repairs were
inspected as code diffs (ActorError binding and plain-dict counter serialization),
not used to change scores; their asserted pre-score timing is Main's report,
not independently established by this review.

## Pins and reproducibility limits

SHA-256 values verified during this read-only review:

```text
786d96c659379675be03e7eaf40f018556efc25646f721e2d3985601ff2c5afd  inspection_v3/inspection.json FILE
ef2adf4146b525fc9a13e9759137daffefe526373a9f6deda3c37fbd07d6eaa6  diagnostic/manifest.json FILE
9b31501c242a99de53c908fe472bb63f1e309bbfd17b1991e9c2cc9543ff6d3d  outer/capture_complete.json FILE
c8fac984db75fd123cf5264756572da465baaffeee0fcbe186f849dddd319f2d  diagnostic/report.json FILE
ba9c04f7ea7f05d14955fac8b422b32c55d14c2510cdf2983abbf778e726e0cb  report OBJECT seal
cd1cecde5115035107aa78c9f90f7f00ae560320f0b44b0c036dc1c6b0290573  outer/finalize_failure.json FILE
a61b7055a7c0b32927a9e86ce216754fc592dca1fc0cf2552a21b02dc6eb8fa8  inspector source
a84f677e1b41512c0eabfd3865eafb55ec85584e53e99796175334e1bf1db00e  frozen analyzer source
ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e  core scorer source
026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1  runtime source
1324ee1931b84313ccde313e9ce71fea202ba2a71e40ed7f8fd725e10bf931ad  canonical ordered selected-ID list
0499b82885cfdbfc2dfd516190bcc581bfe6eee8ccb74f8814d858526e7d504c  canonical ordered 210-file [{name,sha256},...] list
```

List digests use the existing `audit.digest` canonicalization. Ordering is
ascending manifest index, then task file, outer request, outer response, actor
request/render/raw/response. The literal per-task IDs and raw transcripts are
above; original files remain in their archives. File/object pins are checked
against the supplied inspection/capture lineage, not newly independent proof
of remote collection authenticity.

The sample is deliberately narrow and correlated: one excluded root and one
fixed world state, with paired goals/renders. No confidence interval or model-wide
causal explanation is warranted. The evidence distinguishes observed syntax,
identifier, protocol and path/choice failures; it cannot identify a unique
internal model cause, quantify benefits of hypothetical repairs, or promote
the failed diagnostic to an H1/H2, learning, C11 or full-assay result.
