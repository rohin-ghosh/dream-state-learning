# PCFL M-TEXT arithmetic and internal-consistency audit — fresh v1

Date: 2026-09-10

Status: **independent source-only audit; not ratified and not executable**.
This file authorizes no implementation, materialization, benchmark/root/data
generation, model or tokenizer execution, training, LoRA/adapter/checkpoint
work, parenting, GPU use, resource acquisition, scientific claim, release, or
submission.

Audited source:
`research_loop/advisory/20260910_pcfl_mtext_supplied_exact_contract_repair_fresh_v1.md`.

## Ruling

**REWORK.** The published multiplication is arithmetically correct under the
listed phase roster, but the roster is not yet an exact executable scientific
contract. In particular:

1. the headline task composites require authentic atom/link citations, which
   makes `ATOMS`, no-memory, target-only, raw-context, and RAG controls fail by
   construction rather than by worse behavior;
2. `trace_dependence` is declared as a cell-local endpoint even though it
   requires unregistered or cross-condition counterfactuals;
3. the 39-call `REACHOUT_OFF` and 13-call `OLD_CUT`/`NEW_CUT` cells do not run
   the acquisition phase that supplies their delayed state, and no exact
   phase-entry fixture is bound;
4. `TRUTHFUL_NULL` either leaks authentic endpoint pairs or is unreachable
   under the common-reader law as currently written;
5. the eight-read constructive path is feasible only under two unstated
   handle/cursor rules; and
6. the one-shot uncertainty tape cannot legally name a later `COMMIT` action
   under the phase-specific action catalogs.

The arithmetic can be retained after those repairs, but it must be described
as a maximum slot/resource envelope. Early terminal outcomes mean the actual
number of emitted model requests is generally smaller.

## 1. Independent arithmetic reconstruction

### 1.1 Phase ceilings

Every recurrent call permits 256 generated tokens. The resulting phase
ceilings are:

| Phase set | Calls | Allowed generated tokens |
|---|---:|---:|
| one path phase | 13 | 3,328 |
| uncertainty/acquisition | 4 | 1,024 |
| full root: A + B + uncertainty/acquisition + delayed | 43 | 11,008 |
| A + B only | 26 | 6,656 |
| A + B + delayed only | 39 | 9,984 |
| uncertainty/acquisition + delayed | 17 | 4,352 |
| delayed only | 13 | 3,328 |
| four one-shot phase calls | 4 | 11,008 |

The last row is not `4 * 256`: the three path tapes each receive 3,328 tokens
and the combined uncertainty/acquisition tape receives 1,024 tokens.

### 1.2 The source's stated nineteen-condition roster

The source total reproduces exactly:

```text
requests/root
  10*43 + 2*26 + 1*17 + 1*39 + 2*13 + 1*17 + 2*4
= 430   + 52   + 17   + 39   + 26   + 17   + 8
= 589 maximum request slots/root

generated-token allowance/root
  10*11,008 + 2*6,656 + 1*4,352 + 1*9,984
  + 2*3,328 + 1*4,352 + 2*11,008
= 170,752 tokens/root
```

The split arithmetic also reproduces:

| Split | Roots | Presentation blocks | Request slots | Generated-token allowance |
|---|---:|---:|---:|---:|
| DEV (`k=0..7`, both `h`) | 16 | 8 | 9,424 | 2,732,032 |
| confirmation (`k=8..23`, both `h`) | 32 | 16 | 18,848 | 5,464,064 |
| DEV + confirmation | 48 | 24 | 28,272 | 8,196,096 |
| dormant reserve (`k=24..31`, both `h`) | 16 | 8 | 9,424 | 2,732,032 |

Four sentinels run three times forward and three times in reverse:

```text
4 * (3 + 3) = 24 requests
24 * 256 = 6,144 allowed generated tokens
```

Therefore the source's grand resource maxima are correct:

```text
28,272 + 24 = 28,296 maximum emitted-request opportunities
8,196,096 + 6,144 = 8,202,240 allowed generated tokens
28,296 * 8,192 = 231,800,832 maximum input tokens
```

These are **ceilings**, not exact realized call/token counts. An abstention,
parse failure, timeout, invalid command, early success, or other terminal ends
a cell before all recurrent slots are emitted. The expected registry should
therefore contain 28,296 request *slots*, with every unissued suffix sealed as
`NOT_REACHED`, while separately reporting calls actually emitted. Calling
589 or 28,296 “exact model requests” contradicts the stopping rules.

### 1.3 Exact alternative if every delayed intervention runs its own acquisition

If the scientific intent is end-to-end condition-local state rather than a
frozen delayed-entry fixture, then `REACHOUT_OFF` must run 43 calls and each
of `OLD_CUT` and `NEW_CUT` must run 17. That exact alternative is:

```text
601 maximum request slots/root
173,824 allowed generated tokens/root

DEV + confirmation: 28,848 slots; 8,343,552 generated tokens
plus sentinels:       28,872 slots; 8,349,696 generated tokens
maximum input:        28,872 * 8,192 = 236,519,424 tokens
reserve alone:         9,616 slots; 2,781,184 generated tokens
```

The source must choose one of two coherent meanings:

- retain 589/170,752 by binding an immutable, model-independent,
  condition-local `DELAYED_ENTRY(k,h)` fixture for the abbreviated cells; or
- use the 601/173,824 end-to-end roster above.

It cannot leave the missing acquisition state implicit or borrow an AUTH
model output across conditions. My recommendation is the first, factorial
interpretation: use a separately materialized supplied delayed-entry fixture,
state explicitly that abbreviated cut/reachout cells have no acquisition or
retention endpoint, and retain the smaller published envelope.

If all-path masking is intended as a fresh model rerun rather than private
trace revalidation, an additional A+B condition costs exactly 26 request
slots and 6,656 generated tokens per root. Under the source's existing roster
that would produce 615 slots and 177,408 tokens/root, or, including 48 roots
and sentinels, 29,544 slots, 8,521,728 generated tokens, and 242,024,448
maximum input tokens. The source currently registers no such condition.

## 2. Root, split, and threshold audit

The root partition is internally complete and disjoint:

```text
DEV          8 k-values * 2 h-values = 16 roots = 8 twin blocks
confirmation 16 k-values * 2 h-values = 32 roots = 16 twin blocks
reserve       8 k-values * 2 h-values = 16 roots = 8 twin blocks
total                                          64 roots
```

Because each `k` contains both `h` values, target-bit balance is exact. The
popcount-parity nuisance is also balanced 4/4 on DEV, 8/8 on confirmation,
and 4/4 on reserve. Goal order alternation is balanced on each split.

The source's reductions are deterministic finite-suite summaries, not
sampling estimators. `min(e(k,0,c),e(k,1,c))` correctly makes a block pass
only when both target-bit twins pass. No confidence interval or p-value is
warranted for the stated one-topology claim.

Thresholds on the actual lattice are:

| Written threshold | Exact meaning |
|---|---:|
| DEV `6/8` | 0.75, at least six twin blocks |
| DEV `4/8` | 0.50, at most four twin blocks |
| confirmation `12/16` | 0.75, at least twelve blocks |
| contrast `4/16` | 0.25, at least four net blocks |
| contrast `8/16` | 0.50, at least eight net blocks |
| shortcut `5/16` | 0.3125, at most five blocks |
| practical margin `1/16` | 0.0625, at least one net block |

The `-0.05` adverse bound does **not** permit one lost confirmation block.
Every block contrast is an integer multiple of `1/16 = 0.0625`, so

```text
D >= -0.05  <=>  D >= 0
```

on this assay. The same applies to “not below either recurrence comparator by
more than 0.05.” This is a valid zero-net-harm rule if intentional, but the
contract should call it that; “five percentage points” suggests tolerance
that the design cannot express. If a literal five-point allowance is wanted,
the reduction or number of blocks must change prospectively.

## 3. Blocking endpoint inconsistency: the controls cannot earn the headline

`two_goal_traversal` requires both `answer_success` and
`constructive_path`. `delayed_integration` requires old/new authentic atom and
link citations plus `constructive_path`. But several comparison arms cannot
produce those citations by construction:

- `ATOMS` has no links;
- no-memory and target-only return no atom/link handles;
- raw context and RAG expose primitive event rows, not returned authentic
  link handles; and
- native graph has no common-reader return unless static-context handles are
  separately declared dependency-capable.

Consequences:

1. AUTH-versus-ATOMS traversal specificity partly tests the scorer's link
   requirement, not better goal behavior.
2. No-memory and target-only shortcut gates can pass even if those policies
   reach every goal, because their constructive composite remains zero.
3. AUTH necessarily beats raw/RAG on delayed integration if only AUTH is
   allowed to satisfy the endpoint. That cannot establish a practical memory
   advantage.

This is especially important because the algebraic node/relation aliases are
structured transforms rather than independent random labels. A state/goal to
action heuristic may exist even when target-bit marginals are perfectly
balanced. Only a substrate-neutral no-memory task-success endpoint can expose
that route; the current citation-required composite masks it.

Repair by separating substrate-neutral task endpoints from organized-memory
mechanism endpoints:

```text
two_goal_task_success
  = answer_success on both A and B, with no carrier-specific citation rule

delayed_task_success
  = reaches and FINISHes at D after reset, with no carrier-specific citation rule

connected_constructive_use
  = the existing authentic atom/link dependency requirement

delayed_connected_integration
  = old/new authentic connected-use requirement, AUTH-family only
```

Use the first two for no-memory, target-only, ATOMS, raw-context, RAG, and
native-graph comparisons. Use the latter two only for within-interface
mechanism diagnosis, together with behavioral cut/derangement/twin
interventions. Otherwise the central superiority and shortcut gates are
structurally guaranteed.

The present `retention` field has the same problem: requiring an old authentic
link makes retention unavailable to honest non-link baselines. Add a
substrate-neutral delayed retention/task field before applying an adverse
bound across substrates.

## 4. `trace_dependence` is not a cell-local endpoint

Section 8 says every endpoint is binary at one `(root, condition)` cell, but
`trace_dependence` requires both all-path masking and `TWIN_REDIRECT`. Those
are counterfactual comparisons across artifacts/conditions. Moreover, the
nineteen-cell roster contains no `ALL_PATH_MASK_RECURRENT` model condition.

There are two coherent repairs:

1. Keep all-path masking as a private deterministic revalidation of the same
   trace, rename that result `trace_support_integrity`, and define behavioral
   `trace_dependence` as an exact root-block derived jointly from AUTH,
   `BRIDGE_CUT`, and `TWIN_REDIRECT`; or
2. add a registered model-executed all-path-mask condition and use the added
   arithmetic given in section 1.3.

The first is cheaper and sufficient if claim language distinguishes
dependency-graph validity from policy-level counterfactual behavior. In
either repair, `R_trace_dependence(AUTH_RECURRENT)` is the wrong notation:
the quantity is a derived paired/block endpoint, not a field of AUTH alone.
The “twin-invariant shortcut rate” also needs an exact numerator,
denominator, goal aggregation, and action-equivalence rule.

## 5. Truthful-null connectivity leakage

The `Link` schema has statuses `AUTH|NULL|EMPTY|REVOKED`; it has no
`TRUTHFUL_NULL` status. More importantly, the condition is not semantically
closed:

- If a NULL record retains the authentic `left` and `right` atom handles, it
  reveals the exact authentic adjacency pair. Saying that it “does not assert
  a connection” does not remove that answer-bearing association from model
  input.
- If `left=right=null`, the common reader cannot retrieve the record through
  an atom anchor, because candidates are indexed only where `left` or `right`
  equals the atom ID. It is then not the promised explicit matched exposure.

Thus endpoint-bearing truthful nulls leak connectivity, while endpoint-free
nulls are unreachable under the current reader. Do not rely on an instruction
that tells the model to ignore the leaked endpoints. Either remove this
redundant scientific condition or specify a new target-independent null
exposure law whose index and bytes reveal no authentic pair. Any retained
variant needs an exhaustive proof that null endpoint/slot/return patterns are
independent of authentic adjacency.

This choice changes the roster. Dropping this one full condition from the
source's otherwise unchanged roster gives 546 maximum slots and 159,744
generated tokens/root; retain the 589 totals only if a nonleaking reachable
definition is frozen.

## 6. Eight-read feasibility and ATOMS non-crawl

Eight reads are just sufficient for an AUTH path, but only under a precise
interpretation that the source must state. For either branch and either goal,
a worst-case constructive sequence is:

1. read start `S`, obtaining one of the two first atoms;
2. read the goal target, obtaining its sole terminal atom;
3. read the first atom's sole incident link;
4. use the endpoint handle exposed by that returned link to read the second
   atom;
5. inspect at most two link cursors at the second atom—one is the known
   predecessor and one is its bridge link;
6. use the bridge-link endpoint handle to read `p4`; and
7. read the terminal atom's sole incident link.

The count is `1+1+1+1+2+1+1 = 8`. At that point the actor has four atoms and
three authentic adjacent links for one complete path.

This proof requires both of the following to be frozen:

- atom endpoint handles appearing inside a returned Link count as legal
  earlier-returned anchors; and
- the mixed candidate cursor law is exactly `cursor 0 = self atom`, followed
  by incident links in semantic-ID order, with one selected record per read.

The source instead says both that cursor selects one record and that a return
contains one atom slot plus one link slot. Those two descriptions do not
define whether a call can return one record or one of each type. A different
interpretation changes the read count.

ATOMS cannot deterministically crawl beyond the start/target atoms only if
the prohibition is equally explicit: a `src` or `dst` node alias merely seen
inside a returned Atom is **not** a legal node anchor. After the first world
action that destination becomes the current state, but the reader is already
closed. Add a required negative test that attempts to READ every node field of
a returned Atom in ATOMS and observes `BLOCKED`/closed rejection without an
index touch. Otherwise the atom fields recreate stepwise graph traversal.

## 7. Recurrence comparator audit

The two controls answer different questions:

- AUTH versus `SCRATCH_OFF` can isolate explicit carried scratch while both
  policies receive repeated public outcomes.
- AUTH versus `ONE_SHOT_TAPE` compares a closed-loop policy with an open-loop
  static action tape. It removes both carried state **and** access to
  within-phase outcomes.

The one-shot uncertainty/acquisition comparison is especially constrained:
one fixed tape cannot choose `COMMIT_h` correctly for both indistinguishable
`h` twins after an unseen E0/E1 outcome. Under twin-min reduction its
acquisition score is therefore expected to be zero even with perfect initial
reasoning. An AUTH advantage there establishes value of outcome-conditioned
execution, not specifically persistent scratch or internal recurrence.

Requiring AUTH to beat *both* controls prevents the one-shot fact alone from
earning the recurrence claim, but the claim should still be split into
“closed-loop observation value” and “carried-scratch value.” Call it
recurrence necessity only if the exact conjunction and its interpretation are
stated.

The comparator also equalizes maximum generated output tokens, not “thought
tokens.” Recurrent responses repeatedly pay JSON/schema overhead; the
one-shot call pays it once. Input tokens, calls, latency, and GPU work are
deliberately unequal. Report those facts as designed rather than calling the
budget cognitively equivalent.

There is a direct catalog contradiction. At initial UNCERTAINTY the catalog
contains experiments plus ABSTAIN; `COMMIT_0/1` are released only in ACQUIRE.
A static tape generated before the experiment therefore cannot legally
include its future commit under the current closed command/catalog rule.
Freeze either a union catalog for the combined outer model phase, with exact
stage-applicability semantics, or a separately typed conditional tape. The
latter would no longer be a simple open-loop linear comparator.

Finally, the 2,048-byte output ceiling is stated only for recurrent responses.
Bind a one-shot decoded-byte maximum compatible with thirteen commands and
3,328 tokens; otherwise output/artifact ceilings and overflow dispositions
are incomplete.

## 8. Additional protocol contradictions and omissions

### 8.1 Dependency identity type

Section 1.4 makes `deps` a list of public capability handles such as `a00` and
`l00`; the inherited command schema says `deps:[hex64]`. These are different
types and lengths. Freeze one actor-visible type. Semantic checker hashes may
remain private, but they cannot also be accepted actor dependencies.

### 8.2 Matched token exposure is not established by byte padding

The source requires rendered-token equality for primary carrier contrasts,
but proves it explicitly only for DERANGED. Equal UTF-8 byte length and equal
slot count do not imply equal tokenizer length; underscore padding can itself
tokenize differently depending on the preceding record content. AUTH,
ATOMS/null, BRIDGE_CUT, and other masked carriers therefore need materialized
per-root/per-return tokenizer-equality certificates or the exact-matched-token
claim must be withdrawn. No favorable remapping after tokenization is allowed.

### 8.3 Free-text scratch cannot satisfy the stated closed-object rule

“Scratch may mention only public objects” is not mechanically decidable for
arbitrary natural language. A parser can reject private identifiers and
unknown handle-shaped tokens, but it cannot prove that unrestricted prose is
about only public objects. Replace this with a checkable lexical rule or
narrow the claim to “contains no recognized private identifier or unissued
capability handle.”

### 8.4 One-shot adverse-command precedence

The tape clause says the first “state-inapplicable command” ends the cell,
while the world law says a catalog relation without an outgoing edge is an
ordinary `NO_EFFECT`, and a post-action READ is an ordinary fixed-size
`BLOCKED`. Define state-inapplicable narrowly so these public behavioral
outcomes are not silently promoted to private terminal errors.

### 8.5 Bypass comparisons need dependency semantics

State explicitly whether IDs visible in raw/RAG/native `static_context` may be
cited in `deps`. If they may not, constructive endpoints cannot compare those
arms. If they may, the provenance checker needs a separate issued-capability
rule; “returned earlier by the common reader” is no longer universal.

### 8.6 Misnamed acceptance test

`MTEXT-PARENT-PATH-ANSWER-LAUNDERING` mentions a parent even though this stage
forbids parenting. Rename it to producer/carrier/query answer laundering so a
later implementation does not accidentally introduce a parent surface.

## 9. DEV, confirmation, reserve, and resource logic

The DEV/confirmation separation is coherent if every change after DEV forks
and rehashes the protocol before any confirmation call. DEV remains tuning
data and cannot be evidence.

The reserve is not an independent replication: it is eight additional
presentation blocks from the same fixed topology, held back inside the same
64-root algebraic census. If opened after seeing confirmation failure, it is
a post-selected follow-up. A new approval can authorize running it, but cannot
turn it into a replacement confirmation or erase the failed result. The
contract mostly says this already; replace “new bound replication” with
“post-confirmation robustness follow-up” unless a genuinely new topology/suite
is registered.

The resource maxima are arithmetically compatible: 192 A40-equivalent
GPU-hours is stricter than the loose product of eight concurrent GPUs and 48
wall hours. But two definitions remain blocking:

1. “A40-equivalent” has no conversion law for another approved hardware
   class. Either bind A40 only or freeze a prospective conversion.
2. The 48-hour clock runs “from first DEV model call through confirmation
   seal,” yet the required sequence includes post-DEV independent review and
   a fresh human confirmation approval. Human/governance waiting cannot be a
   scientific compute limit without pressuring the mandated review. Give DEV
   and confirmation separate execution clocks, or explicitly pause the wall
   clock during review/approval latency.

The first-call timing check may lower but never raise the ceiling. Therefore
the exact throughput feasibility calculation must occur before execution
authority; otherwise an underestimated ceiling forces `INCOMPLETE` for no
scientific reason.

## 10. Exact repair checklist before a GO ruling

1. Add substrate-neutral task and retention endpoints; use them for all
   baseline, shortcut, benefit, and adverse comparisons.
2. Recast connected constructive fields as mechanism diagnostics and define
   cross-condition dependence at the twin-block level.
3. Choose and hash either the 589-slot fixed delayed-entry roster or the
   601-slot condition-local end-to-end roster.
4. Remove or fully define a nonleaking, reachable `TRUTHFUL_NULL` condition.
5. Freeze the two assumptions that make the eight-read AUTH path feasible and
   explicitly deny Atom-field node crawling.
6. Repair the combined uncertainty/acquisition catalog for the one-shot tape,
   add its byte ceiling, and narrow recurrence language.
7. Unify public dependency-handle types and define static-context capability
   rules.
8. Materialize token-equality certificates for every contrast that claims
   them.
9. Clarify `NOT_REACHED` request slots, reserve interpretation, hardware
   equivalence, and paused governance time.

After these changes, the existing root count, split, twin-block reducer, and
published 589/170,752 arithmetic can remain unchanged **if and only if** the
fixed delayed-entry interpretation is selected and truthful-null remains as a
valid nonleaking condition. Until then, the correct disposition is REWORK,
not execution.
