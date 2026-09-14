# Fresh exact-contract audit: ACTIVE_TEXT_NATIVE-v2.1-AUTO

**Date:** 2026-09-14 PT  
**Role:** fresh adversarial proposal/source-readiness reviewer  
**Object:** commit
`21c76fab21ee14ebac62de2848d981ccdd4ff9c8`, file
`research_notes/analysis/2026-09-13_active_text_native_v21_auto_exact_contract_draft.md`,
verified SHA-256
`bc7964a003cf8fe768c6d818f371dd512cfabee0089464ff606a8321df53a331`.

This was a repository/document/arithmetic audit only. I did not author or run
store source, materialize a root, invoke a tokenizer or model, create or mount
an adapter, use a GPU, or inspect a scientific result.

## Verdict

**REWORK. Do not promote these exact bytes to `GO_CPU_SOURCE`.**

The proposal makes substantial progress. Automatic retrieval is genuinely
target-blind at its declared API; `q16/B16384` changes returned-memory access
without adding an actor turn; the witnessed graph no longer pretends that a
child LINK is necessary; the common LF-framed 16+1 generation envelope is
well chosen; the main task/call/token arithmetic reproduces; and the claim
firewall correctly avoids pure-carrier, DREAM, recurrence, general external-
memory, and universal-saturation claims.

It is not yet one executable contract. The remaining failures are exactness
and integration failures, not requests for a larger design:

1. event and interpretation IDs are not root-bound, so wrong-root provenance
   is not guaranteed unique;
2. the public transition parser that creates every graph edge is not defined;
3. rejected interpretation sources and task-local THINK receipt IDs are not
   defined;
4. the root law simultaneously separates and combines RS8 qualification and
   the four-root certificate;
5. the common-raw law says branches have the exact same ledger and their own
   different on-policy ledgers;
6. the declared actor/record languages do not bind to either current Stage2A
   or TSJ wire language;
7. several floating-point/packing operations still admit different byte
   implementations; and
8. P3--P5 omit or leave unbound the acquisition/formation work that creates
   the evolving stores and the exact lifetime/cut registry.

These defects can all be repaired in one narrow v2.2 contract. They do not
require changing automatic retrieval, q16/B8192, the B16384 sensitivity, the
witnessed-event graph, or the scientific role of the baseline.

```text
REWORK_ATN_V21       = TRUE
GO_CPU_SOURCE        = FALSE
GO_CPU_TEST          = FALSE_EXCEPT_NONNORMATIVE_SCRATCH
GO_MATERIALIZE       = FALSE
GO_TOKENIZER_MODEL   = FALSE
GO_GPU_OR_CLAIM      = FALSE
```

## 1. Nine-P0-field audit

| P0 field | disposition | fresh finding |
|---|---|---|
| 1. event/document/lifecycle/duplicate/rejection | **REWORK** | The append-only lifecycle, next-continuation overlay, sibling barrier, and no-supersession choice are definite. But `EV` and `IN` hashes omit the root salt; rejected attempts have no total rule for `source_event_ids`; and the public reason vocabulary is unbounded. |
| 2. automatic query | **REWORK, narrow** | Objective, state, accepted prior THINK, newest-first whole-record retention, 1,024/2,048 caps, and no candidates are exact. The contract nevertheless receipts kept/dropped THINK “record IDs” without ever defining such IDs. |
| 3. equality-only identifiers | **PASS for OID; REWORK for record identity** | `OID=SHA256(root_salt || exact public ID)[:128]`, online creation, collision stop, and no role/type/ordinal bits are sound. That protection is not carried into event/interpretation/citation IDs. |
| 4. public topology/graph | **REWORK** | The six bidirectional incidence arcs and the absence of inferred/child-LINK/MODEL edges are exact. Which raw public byte strings are allowed to instantiate the four transition fields is not. An unspecified “frozen public receipt parser” is the only thing separating public evidence from a structured hidden-world edge. |
| 5. BM25/PPR/fusion/MMR/packing | **REWORK, narrow** | Constants, high-level iteration order, complete-row packing, caps, miss, and most ties are fixed. `avgdl`, normalization, Jaccard-to-float, `tokens(d)`, and some per-destination PPR accumulation bytes are still source choices. |
| 6. common RAW_PUBLIC lane | **REWORK, one sentence plus receipt law** | The same schema/query/BM25/packing/budget is specified, but “receive the exact same event ledger ... on their own branches” is contradictory once actions diverge. |
| 7. common LF-framed transport | **REWORK for integration** | Within the new dialect, LF stop/exclusion, strict fullmatch, 16+1 calls, 2,048 generated tokens, context reserve, and no retry are exact. The dialect is not the current Stage2A or TSJ dialect, and no exact bridge is named. |
| 8. RS8 MODEL lane | **PASS conditionally** | MODEL is lexical, cited, visible only at the common formation barrier, has no graph/affine-solver feature, and adds no condition-specific query generation. It becomes executable only after the interpretation-source and wire-binding repairs. |
| 9. statistical root | **REWORK** | Independent world/writer/schedule/decode/salt seeds conditional on one fixed child, root-level `n`, ITT, and branch fork are clear. Section 2.1 declares RS8-qualification and certificate roots disjoint while Section 9 uses the certificate's reusable stratum as RS8 qualification. |

Five of nine fields therefore remain non-unique. P0's own rule says that one
undefined default or unresolved alternative is `REWORK_P0`.

## 2. Exact blocking repairs

### R1. Root-bind every evidence identity

Current preimages are:

```text
EV = H(tag || JCS(event body))
IN = H(tag || JCS(interpretation body))
DOC = H(tag || kind || NUL || source_record_id)
```

Root and branch live only in an outer custody manifest. Two independent roots
with byte-identical public receipts and coordinates can therefore produce the
same EV, IN, and DOC IDs. Low probability in one random materialization is not
an identity law, and wrong-root citation checks cannot rely on world names
happening to differ.

Use the already sampled common paired-root salt in both record preimages:

```text
event_id = "EV/" + H(b"ATN_EVENT_V1\x00" || root_salt || body_bytes)
interpretation_id = "IN/" +
  H(b"ATN_INTERPRETATION_V1\x00" || root_salt || JCS(body))
```

The existing DOC formula may then remain because its source record ID is
root-bound. Do not include the branch label: byte-identical evidence in paired
branches of one root should retain the same ID. Explicitly declare the
episode/occurrence/decision coordinates global and unique within a branch.

### R2. Totalize rejected interpretations and public feedback

The schema requires `source_event_ids`, but an invalid or partially parsed
attempt need not resolve the 1/2/8 evidence receipts of EVENT/LINK/MODEL. Pick
one mechanical rule. The minimal faithful rule is:

- after a full grammar parse, resolve evidence receipt occurrences in literal
  order against the already-public one-to-one receipt-to-event map;
- record exactly the successfully resolved event IDs in that same order;
- require 1/2/8 distinct, source-consistent events for acceptance;
- use `[]` when no full grammar parse or no receipt resolves; and
- never use a private validator object to fill the array.

Freeze exact status literals (`ACCEPTED`, `REJECTED`) and a finite public
reason vocabulary. In particular, RS8 consistency rejection may return only a
generic already-public failure status, not a corrected A/B bit or a hidden-
solver diagnosis. That preserves the existing one-attempt/no-correctness-
feedback RS8 contract.

### R3. Publish the public-byte transition parser

Section 3.1 permits a non-null transition only when its fields occur in public
action/outcome bytes, which is the right invariant. But it delegates the
selection to an unnamed parser. This is the most important leakage seam:
passing a structured world transition and merely checking that four tokens
occur somewhere is not equivalent to deriving the edge from public bytes.

The successor must give anchored byte grammars and a total algorithm for every
action/outcome family that can yield:

```text
(source, port, destination, receipt)
```

Ambiguous, duplicate, partial, out-of-order, cross-message, or multiply
matching receipts must yield `transition=null` or terminate under one named
rule. The graph builder may receive only the parser output and raw hashes, not
the world transition object. Add allow/deny goldens including swapped fields,
decoy identifiers, repeated fields, unknown receipts, future IDs, mixed roots,
and valid current TSJ `PUBLIC_OUTCOME` bytes.

### R4. Define task-local THINK identity

The query says that kept/dropped THINK record IDs are receipted, but no THINK
record or ID exists. Define a task-local ID from the immutable task identity
and actor call index, or receipt `(task_id, call_index, SHA256(exact bytes))`
directly. It remains ephemeral and never enters lifelong documents. This is a
receipt repair, not a new memory mechanism.

### R5. Close the last arithmetic choices

Add literal rules for:

- `tokens(d) = lex(exact ranking-row bytes)` in both BM25 and MMR;
- `avgdl = binary64(integer_sum_dl / N)` with one stated evaluation order;
- BM25 and L denominators accumulated by ascending document ID after each
  document score is computed;
- restart and graph-document renormalization denominators accumulated by
  ascending vertex/document ID;
- Jaccard as one defined binary64 conversion/division of exact integer set
  cardinalities; and
- each PPR destination sum accumulated over sources in ascending source ID,
  with all multiply/add operations in the written order and no contraction.

Then bind independent byte goldens for empty, one-document, ties, dangling,
non-graph MODEL, graph-only-positive, row-overflow, and MMR-skip cases. The
current mathematical intent is sound; these pins prevent two conforming
implementations from disagreeing on hashes or tie outcomes.

### R6. Correct RAW_PUBLIC parity wording

Replace “receive the exact same event ledger ... on their own branches” with:

> Each on-policy branch uses byte-identical ledger schema, visibility clock,
> query projection, BM25 implementation, packing, and q16/B8192 limits. Ledger
> contents are branch-local consequences of that branch's committed actions
> and may diverge after the fork. Only the explicitly labeled fixed-DLT-
> history descendant receives DLT evidence.

Also receipt that DLT and SLEEP_FROZEN rank only their own raw documents and
that ATN ranks its own raw plus eligible interpretations within the **same one**
512/8,192 envelope. This preserves total-system fairness without falsely
claiming identical post-fork information.

### R7. Choose and bind one actual PCFL-L wire language

The proposal's languages use `N_/E_/P_/R_` ten-character suffixes and final
families such as `ROUTE`, `EXPLORE`, and one-line `EVENT ... AT ... DID ...`.
They are not the current source interfaces:

- Stage2A uses `M2AN_/M2AE_/M2AP_` twelve-character identifiers and actor
  `THINK KEEP|REVISE`, `READ INDEX|RELATION`, `STEP`, `STOP`;
- TSJ uses `TS3N_/TS3E_/TS3P_` twelve-character identifiers, slot-addressed
  `READ`, `STEP`, `STOP`, public `PUBLIC_OUTCOME SOURCE/PORT/DEST/RECEIPT`,
  and child rows `EVENT ... SOURCE ... PORT ... DEST ... PROVENANCE`.

A future receipt cannot choose between these semantics after P0. Publish one
content-addressed PCFL-L adapter contract that maps the actual lifetime actor,
public outcome, and formation bytes into ATN event/interpretation bodies, or
publish a new common lifetime dialect and show exactly how DLT_PERIODIC,
SLEEP_FROZEN, and ATN all use it. Do not claim that P2 mounts “the same physical
transport used by DLT/TSJ” until injected compatibility tests pass both the
new transport and the relevant current source boundary.

This does not require changing Stage2A or TSJ. Those remain prerequisite
mechanism tests; the new binding can be the later lifetime interface.

### R8. Reconcile roots, material registries, and total stage costs

Choose Section 9's efficient rule: the four certificate roots also contain
the reusable/RS8 qualification stratum. Then remove `RS8-qualification` from
Section 2.1's mutually-disjoint list. DEV, profile, writer-scale, and lifetime
roots remain disjoint from that combined certificate.

The proposal also refers to “registered token/type marginals,” a 571-block
store, preassigned necessary bundles/cuts, and a current lifetime retention
cohort without binding their registry bytes. Before CPU source promotion,
define the registry schema and deterministic inputs. Before P4/P5 execution,
bind exact registry/generator/scorer hashes. Hidden exact solvers may create
and check a custody-only necessary/cut registry before actor execution; they
may never enter query, graph, packing, or actor processes.

Finally separate **evaluation maxima** from **total stage work**. The printed
P4 and P5 call counts correctly count their scored actor panels, but they omit
the public acquisition and child-formation calls that create the certificate
and each on-policy evolving store. Add one of:

1. exact maximum acquisition/formation calls and tokens to each stage; or
2. an explicitly shared, separately bounded prerequisite receipt whose costs
   are added to the stage total.

P3 must likewise state whether actor-position 8/16 prefixes are injected
technical transcripts or generated calls. The `54 calls/bandwidth` count is
correct only when each profiled prefix is already fixed and no uncounted model
call is needed to create it. Bind the exact authentic-TSJ prerequisite receipt
and the lifetime schedule/utility/earliest-cohort definitions by hash rather
than by prose labels.

## 3. Required attack results

### Leakage and hidden solver

**Conditional pass after R2/R3/R8.** The retriever API excludes answer,
candidate, route, cut, arm, evaluator, report, and future state; truthful/cut
registries are sealed before execution; FULL and EXACT are public projections;
MODEL never becomes a solver feature. These are strong choices. The undefined
transition parser and unbounded public rejection reason are presently two
paths by which hidden structure could still enter searchable text/edges.

### Identifier attack

**OID passes; evidence identity fails.** Salted OIDs reveal equality and
nothing about type, role, order, or future inventory. Online creation and
collision termination are correct. Root-unbound EV/IN/DOC identities must be
repaired as in R1, and exact current namespace mappings must be tested as in
R7.

### Query attack

**Substantively pass, receipt rework.** Automatic query construction has no
answer-aware model, query writer, retry, candidate text, or final action. Whole
THINK suffixing is deterministic and query text is ephemeral. Keeping
objective/state while deliberately excluding `public_task_bytes` is one
specific frozen projection, not an ambiguity, provided the materializer proves
that omitted task bytes do not contain the only public target identity needed
by retrieval. The missing THINK receipt ID is R4.

### Actor-opportunity and q16/B16384 access-only sensitivity

**Pass within the proposed dialect.** Both configurations retrieve before the
same first 16 actor calls, permit the same unassisted call 17, share the same
2,048 generated-token cap, action/parser/scorer/decode-address law, and give no
condition-specific query generation. B16384 changes only:

```text
per automatic return: 512 -> 1,024 tokens
cumulative return:   8,192 -> 16,384 tokens
```

It does not add q32 or another THINK/action opportunity. Histories may diverge
after different retrieved text, so the result is a **same-turn total access
sensitivity**, not a token-level pure causal effect at a fixed generated
history. The proposal already avoids calling a flat four-root difference
“saturation.” Retain that wording.

### Batch visibility

**Pass in intent; source tests mandatory.** Same-episode evidence is delayed
until the next continuation, siblings wait for the presealed round barrier,
and global commits use a deterministic order independent of device completion.
Tests must force permuted worker completion, terminated siblings, cache
restart, same-task overlay destruction, and a run/skip evaluation descendant.
No blocker beyond R1/R3 was found in the visibility rule itself.

### Same-history overclaim

**Pass.** The disposable store gets exact eligible DLT public events and DLT-
authored interpretations but no DREAM prose, optimizer state, latent
propositions, answers, or evaluator output. Because the actor weights,
interpretation formation, and ATN access algorithm still differ, the proposal
correctly calls this a **same-history conditional system/access contrast** and
not a pure carrier or DREAM comparison. Keep the finite
`TEXT_SAME_SEMANTICS` diagnostic as the only identical-record carrier test.

## 4. BRIDGE_EVENT replacement ruling

**Conceptually correct; registry closure required.** The old child-LINK cut is
invalid for this strong opponent because `AUTO_WITNESSED_GRAPH` joins two raw
events through their shared public symbol without consulting a LINK document.
Replacing it with `BRIDGE_EVENT` therefore tests an object the baseline
actually uses. Removing that raw document, every interpretation citing its
source event, and its six incidence arcs is the right intervention.

Before P4, the presealed registry must prove for each designated case that:

1. the named bridge event is publicly witnessed and eligible at the cut;
2. it lies on every registered public witness path needed for the answer;
3. no duplicate real dispatch preserves the same transition at that frontier;
4. the cut changes the exact public graph/retrieved necessary bundle while
   changing no task bytes or non-descendant evidence; and
5. the CPU public-only oracle loses the registered route without consulting a
   hidden actor-time solver.

Child-LINK deletion remains a separate DLT mechanism test. It should not be
restored to this ATN certificate.

## 5. Arithmetic reproduction and stage/claim audit

I independently reproduced the main maxima:

```text
P3 profiles/bandwidth                         3*3*2*3 = 54
P3 both bandwidths                             108 calls, 27,648 output tokens

P4 with B16384                         10*64 = 640 tasks
                                         640*17 = 10,880 calls
                                      640*2,048 = 1,310,720 generated
                 6*64*8,192 + 64*16,384 = 4,194,304 returned

P4 without B16384                       9*64 = 576 tasks
                                          576*17 = 9,792 calls
                                      576*2,048 = 1,179,648 generated
                                      6*64*8,192 = 3,145,728 returned

P5 one five-cut view                 16*5*40 = 3,200 tasks
                                       3,200*17 = 54,400 calls
                                    3,200*2,048 = 6,553,600 generated
                                    3,200*8,192 = 26,214,400 returned

P6 two added cuts                    16*2*40 = 1,280 tasks
                                      1,280*17 = 21,760 calls
                                    1,280*2,048 = 2,621,440 generated
                                   1,280*8,192 = 10,485,760 returned

P6 terminal B16384                     16*40 = 640 tasks
                                         640*17 = 10,880 calls
                                      640*2,048 = 1,310,720 generated
                                     640*16,384 = 10,485,760 returned
```

The tenths-of-an-A40-hour reservation formula is dimensionally correct:
`ceil(1.5*calls*t_max/360)/10` equals upward rounding of seconds/3,600 to
0.1 hour. The one-sided df=15 critical value `1.7530503556925547` and the
Bonferroni four-family two-sided quantile `2.4898797034798896` are consistent
with the stated confidence rules. The printed counts are panel maxima, not
yet total stage costs because of R8.

The stop order is scientifically conservative: deterministic source first,
then injected transport, excluded profile, certificate, five-cut lifetime,
conditional fixed-history spend, and only then plateau extension. Invalid
roots remain ITT failures and do not trigger redraw or favorable-cut
selection. Clarify `calls_max` in the P3 reservation as `10,880` when B16384
fits and `9,792` otherwise.

The claim firewall passes. P4 licenses only usability of this named system;
P5 licenses only conditional finite-PCFL total-system and conditional
same-history system/access statements; P6 alone licenses a practical local
plateau of this configuration. It does not license physical compression,
general external-memory superiority, DREAM value, recurrence, parenting,
open-world discovery, or general continual learning.

## 6. Minimal successor acceptance checklist

A v2.2 exact proposal can earn `GO_CPU_SOURCE` without another architecture
expansion if a fresh reviewer can answer yes to all of these:

1. EV/IN identities are root-salted and DOC identity inherits that binding.
2. Every accepted/rejected attempt has one total source/status/reason rule.
3. The public-byte transition parser is printed or content-bound with
   exhaustive allow/deny goldens.
4. Task-local THINK receipt IDs exist.
5. All float and token-set evaluation orders are singular.
6. RAW parity says same machinery, branch-local on-policy contents.
7. One actual PCFL-L wire adapter is exact and tested against the relevant
   current interface.
8. Certificate/RS8 root overlap is stated one way only.
9. Load/cut/lifetime registries and authentic-TSJ prerequisite receipts have
   schemas/hashes before their stage opens.
10. Acquisition/formation and evaluation costs are both bounded and reported.
11. BRIDGE_EVENT public-path necessity is proved prospectively.

Until those repairs are bound, the right label is **well-specified algorithmic
direction, not source-ready strong baseline**.

## Evidence inspected

- `AGENTS.md`
- `research_notes/analysis/2026-09-13_active_text_native_v21_auto_exact_contract_draft.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_adversarial_audit.md`
- `research_notes/analysis/2026-09-13_active_linked_text_readiness_fresh_audit.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_executable_design.md`
- `research_notes/analysis/2026-09-13_pcfl_recurrent_reader_successor.md`
- `research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v4.md`
- `research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v5.md`
- `organism_v6/composition_birth_stage2a.py`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_binding_v2.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v3.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v4.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_v4_fresh_source_readiness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_reusable_affine_gate_stratum.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_claim_ladder_area_chair_audit.md`
- `research_notes/analysis/2026-09-13_full_objective_paper_claim_coverage_audit.md`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md`
