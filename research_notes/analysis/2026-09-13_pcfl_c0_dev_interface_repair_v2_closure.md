# PCFL C0-IFACE-DEV-R1 v2 closure and builder handoff

**Date:** 2026-09-13  
**Status:** documentation-only closure after red-team `e9fa4b6e`  
**Execution authority:** none in this document. No source/runtime/test edit,
model or tokenizer call, fit, update, GPU use, or claim is performed here.

## 1. Closed decision

Implement a clean-base, zero-fit DEV ladder that changes only the public
interface around the existing PCFL task:

1. disclose the exact READ language;
2. add bounded typed THINK turns;
3. keep the entire terminal ROUTE/PROBE response under the existing strict
   parser and scorer; and
4. expose a prebound generic traversal scaffold only when A3 proves that the
   typed interface works but route execution does not.

Keep the world graph, opaque IDs, row contents, tasks, true routes, cuts,
model revision, temperature, route/probe scorers, and immutable SEQ-167
capture unchanged. This successor never rescues or rescores an old output.

SEQ-167 is enough to motivate the repair: 64/320 positive delayed outputs use
an undisclosed/illegal READ language, 86/320 have opaque-ID surface errors,
and 170/320 contain valid root ports in disconnected order; zero contains a
correct route hidden by punctuation. The synthesis promised up to 2,048
thought tokens, but the executed endpoint permitted only one answer line.

## 2. Exact actor-response byte contract

All actor responses are raw strict UTF-8. No actor response may contain CR
(`0x0d`) or LF (`0x0a`), including a terminal LF. No normalization, trimming,
stop-string truncation, fence removal, last-line extraction, or repair is
permitted. Dispatch uses the complete decoded response.

The only response families are:

```text
THINK <payload>
READ EVENT E_[A-Z2-7]{10}
READ EVENTS_AT N_[A-Z2-7]{10}
READ LINKS_FROM E_[A-Z2-7]{10}
ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(,P_[A-Z2-7]{10})*
PROBE Q_[A-Z2-7]{10}
```

These are specifications, not literal regex delimiters in model text. The
existing READ/ROUTE/PROBE fullmatch regexes remain the implementation
authority. THINK is valid iff:

- the raw response begins with the six ASCII bytes `THINK `;
- the remaining strict-UTF-8 payload is nonempty;
- it contains at least one Unicode code point for which `isspace()` is false;
  and
- the whole response contains no CR or LF.

Leading/trailing spaces in READ/ROUTE/PROBE, doubled spaces, spaces after route
commas, multiple commands, and any unregistered top-level family are invalid.
Action-looking text inside a valid THINK payload is inert thought text. It is
never executed or extracted. Only a whole-response READ dispatches the service;
only a whole-response ROUTE or PROBE terminates and is scored.

Service response bytes remain unchanged:

- a row block is the registered one- or two-row concatenation, with one LF
  after every row including the last;
- an absent registered address returns the four bytes `MISS`, without LF;
- a valid request missing from the task's frozen query registry counts as a
  READ attempt and returns `MISS`; and
- only a query present in that registry whose response is a non-`MISS`
  registered block counts as a **served non-MISS READ**.

The public contract must disclose all three READ forms and those meanings, but
must disclose no registered address, useful query, row, adjacency count,
route candidate, route length, first step, hidden bit, score, or correction.

After a valid THINK, append the exact assistant bytes and one frozen
information-free user message. Its exact UTF-8 bytes are the code-block
contents below, without a terminal LF, and must be materialized and hashed
before A1:

```text
CONTINUE: think again, issue one permitted READ if reads are enabled, or commit the final action.
```

A READ gets only the existing exact service result. A terminal action gets no
environment response and no retry.

## 3. Controller state and exhaustion order

Maintain independent integer counters per task:

```text
generation_count = 0
think_count = 0
read_count = 0
actor_tokens = 0
returned_tokens = 0
terminal = false
```

The task declares `think_enabled`, `think_required`, `read_enabled`, and
`terminal_family` (`ROUTE` or `PROBE`). Controller order is fixed:

1. Before a generation, fail if terminal is already true, the task's physical
   generation-slot cap is exhausted, or `2048 - actor_tokens <= 0`.
2. Fully render the next conversation. Fail if input tokens plus requested
   output headroom exceed the frozen model-context limit.
3. Request exactly `min(256, 2048 - actor_tokens)` maximum output tokens.
4. Preserve raw text and output token IDs. Increment `generation_count` and
   `actor_tokens` by the actual receipt before dispatch.
5. Fullmatch one family. An invalid or disabled family fails the task
   immediately.
6. THINK: require `think_count < 6`, increment it, append the exact THINK and
   frozen CONTINUE, then loop.
7. READ: require `read_count < 12`, increment it, resolve the exact frozen
   query. Count returned tokens before appending. If the complete response
   would make `returned_tokens > 4096` or the next rendered context overflow,
   fail without truncation; otherwise append the exact response and loop.
8. ROUTE/PROBE: require the declared terminal family and, when
   `think_required`, `think_count >= 1`; set terminal once and pass the entire
   raw response to the unchanged parser/scorer.

The sixth THINK and twelfth READ are legal; a seventh or thirteenth is not.
An exactly exhausted actor budget is legal only if the response that exhausted
it was already a valid terminal action. No cap failure triggers a forced final
answer. CPU tests must cover every counter at cap-1, cap, and cap+1, plus
actor/returned/context exhaustion ordering.

## 4. Frozen arm-capability matrix

The common record semantics, THINK grammar, terminal grammar, continuation,
caps, task bytes, and selected scaffold bytes are identical wherever the
corresponding capability is enabled. The only lawful capability difference is
the declared READ service.

| arm | mount | memory surface | READ | THINK | scaffold | terminal |
|---|---|---|---|---|---|---|
| A1 READ handshake | C0 | ACTIVE service | enabled/disclosed | forbidden | none | ROUTE |
| A2 answer-direct | C0 | exact graph in prompt | explicitly disabled | forbidden | none | ROUTE |
| A3 typed thinker | C0 | exact graph in prompt | explicitly disabled | required, 1--6 | none | ROUTE |
| A4 scaffolded thinker | C0 | exact graph in prompt | explicitly disabled | required, 1--6 | prebound generic | ROUTE |
| selected direct panels | C0 | exact/full/event/native/old/new/none/wrong | explicitly disabled | required, 1--6 | selected bytes | ROUTE |
| selected active delayed | C0 | ACTIVE service | enabled/disclosed | required, 1--6 | selected bytes | ROUTE |
| selected direct reachout | C0 | exact/full/none/wrong in prompt | explicitly disabled | required, 1--6 | selected bytes | PROBE |
| selected active reachout | C0 | ACTIVE service | enabled/disclosed | required, 1--6 | selected bytes | PROBE |
| future native OFF | C0 | learned/native only | explicitly disabled | same as ON | selected bytes | ROUTE/PROBE |
| future native ON | same base + adapter | learned/native only | explicitly disabled | same as OFF | selected bytes | ROUTE/PROBE |
| future evolving-text baseline | C0 | external store | enabled, same three forms | same common topology | selected bytes | ROUTE/PROBE |

READ-disabled prompts explicitly say no local READ service is available; they
must not merely omit documentation. Future OFF/ON comparison messages, prompt
hashes, turn topology, budgets, task order, and randomness are identical; only
the mount differs. A4, if selected, is byte-identical across every downstream
arm. This closure qualifies no future arm by itself.

## 5. Prebound material before A1

Before the first A1 model call, a CPU-only preparation must freeze and hash:

1. A1, A2, A3, and A4 full system/user templates, record/API descriptions,
   response grammars, CONTINUE bytes, reachout template, caps, dispatcher, and
   reducer;
2. the A4 neutral example's grammar-valid L8 IDs, two-edge topology, tokenizer
   lengths, and proof of non-membership in every existing or reserved root,
   query, memory, candidate, and future final namespace;
3. both complete selectable downstream catalogs—one with A3 bytes and one
   with A4 bytes—so selection chooses a pre-existing hash;
4. one order-only reachout template: RA/RB differ solely by swapping two
   candidate-line byte strings; within a task those lines have equal actual
   tokenizer length, and no numbered choices appear;
5. the four confirmation root seeds, namespace/domain separator, generator
   source revision/hash, deterministic candidate stream, first-valid
   allocation rule, rejection reasons, tokenizer qualification, cube/order
   balance, root wire hashes, and all A3- and A4-rendered task/prompt hashes;
6. disjointness from `excluded/*`, `disposable/*`, `dev/*`, parenting,
   lifetime, and future paper-test namespaces; and
7. the exact unique call-slot registries and partition manifests in section 8.

The confirmation roots and both candidate prompt catalogs are materially
generated before A1, not after a DEV outcome. Store decoded payloads in one
immutable access-logged capsule and expose only its commitment/roster counts
to the agents reading DEV outputs. `blinded` here means the decoded inventory
and prompts enter no model, analyzer, discussion, or prompt-editing context
before the selected DEV disposition; it does not claim cryptographic secrecy
from the machine owner. Release is mechanical from the already committed A3
or A4 catalog after the corresponding DEV pass marker.

No confirmation redraw, favorable-root selection, prompt regeneration, or
same-root retry is allowed. A failed confirmation burns all four roots.

## 6. Ladder, joint gates, and A4 eligibility

All ladder tasks use the already exposed `excluded/0..3` roots and are
explicit optimization data. The immutable SEQ-167 capture is A0 and receives
no new score.

| rung | fixed task set | task max generations | acceptance |
|---|---|---:|---|
| A1 | 64 delayed ACTIVE | 13 | `>=60/64` joint registered non-MISS READ use; zero malformed/multiple READ responses |
| A2 | 64 delayed EXACT graph | 1 | diagnostic `>=60/64` exact graph-successful ROUTE |
| A3 | same 64 EXACT | 7 | `>=60/64` joint THINK + strict graph-successful ROUTE |
| A4 | same 64 EXACT | 7 | same joint gate; conditional only |

Per-task flags are exact:

```text
interface_complete =
  think_count >= 1 AND exact terminal ROUTE present
  AND invalid_turn == false AND cap_failure == false

think_route_success = interface_complete AND graph_success == true

registered_nonmiss_read =
  exact READ request in this task's frozen query registry
  AND exact response is a registered non-MISS row block
```

A1's acceptance count is the number of tasks with
`registered_nonmiss_read >= 1` and no invalid turn/cap failure. Its route
scores remain diagnostics.

The A3 interface qualifies iff `interface_complete >=60/64`. A4 is eligible
**only** when A3 interface qualifies and `think_route_success <60/64`.

- If A3 has `think_route_success >=60/64`, select A3 and prohibit A4.
- If A3 interface does not qualify, prohibit A4; stop for a separately named
  byte/interface successor.
- If A3 graph-succeeds but an auxiliary compliance rule misses, do not add
  cognitive content; stop for interface review.
- If eligible A4 reaches `think_route_success >=60/64`, select A4.
- If eligible A4 misses, stop the 7B assay. Do not fit, relax, add candidates,
  or tune on confirmation material.

A2 versus A3 supports only this statement: the **typed recurrent THINK
protocol** changed traversal under a shared actor-token envelope. It does not
isolate retained state from extra generations, self-produced history, or the
fixed continuation.

## 7. Selected-interface qualification gates

Reuse the selected A3/A4 EXACT task results as the DEV exact-graph panel. They
are never regenerated. Execute remaining panels once.

### Delayed: four roots, 64 task cells per logical projection

- EXACT, FULL, EVENT, ACTIVE, and NATIVE: each `>=60/64` graph success.
- For EXACT/FULL/EVENT/NATIVE, acceptance is jointly `>=1` THINK, exact
  terminal graph-successful ROUTE, no invalid turn, and no cap failure in at
  least `60/64` tasks.
- ACTIVE acceptance is jointly at least one `registered_nonmiss_read` and an
  exact graph-successful ROUTE, with `>=1` THINK and no invalid/cap failure, in
  the same task for `>=60/64` tasks.
- ACTIVE has zero malformed READs and 100% query -> registered block -> source
  row/hash provenance on every served return.
- OLD and NEW are each `<=36/64`; NONE and WRONG are each `<=20/64`.
- WRONG additionally has zero final ROUTE port IDs belonging to the donor
  root and not the task root. This replaces the vacuous scan for EVENT/LINK
  prose inside a typed actor action.

FULL and NATIVE are aliases, not independent evidence, when their complete
rendered messages, task seed, caps, and service state hash equal. Preparation
must prove equality before assigning one physical task/call vector two
compatibility labels. If they differ at all, the 13,952 ceiling has no room
for an unregistered extra set: stop and revise the bound rather than silently
run both.

RAW_EPISODIC is omitted. Adding it later is a new, pre-accounted optional
448-call pool, never an automatic continuation.

### Reachout: four roots, 32 task cells per logical projection

- EXACT, FULL, and ACTIVE: each `>=30/32` exact relevant-Q actions.
- ACTIVE joint acceptance requires `>=1` THINK, `>=1`
  `registered_nonmiss_read`, the exact relevant PROBE, and no invalid/cap
  failure in the same task for `>=30/32`, including `>=14/16` RA and
  `>=14/16` RB.
- Direct positive acceptance likewise requires THINK + exact relevant PROBE
  jointly, with `>=14/16` in each view and `>=30/32` total.
- NONE and WRONG are each `<=18/32`; within either arm the absolute RA/RB
  success difference is `<=4/16`, and first-position choice is 12--20/32.
- Ordinals, node IDs, event IDs, malformed responses, and unregistered Q IDs
  remain invalid. No ordinal-to-Q conversion is allowed.

Report roots=4 and the exact cube/goal/view crossing. The 64/32 task cells are
not independent lives and must never be described as statistical `n=64` or
`n=32`.

All DEV gates must pass before confirmation release. Any failure stops this
version; output inspection may motivate a new named DEV version only.

## 8. Executable call partitions and budgets

The red-team's conservative pre-alias envelope contains exactly 13,952 logical
generation slots:

| component | arithmetic | logical maximum |
|---|---:|---:|
| discovery A1+A2+A3+A4 | `832+64+448+448` | 1,792 |
| remaining DEV | `4 x 1,464` | 5,856 |
| confirmation | `4 x 1,576` | 6,304 |
| **total** | | **13,952** |

Because FULL and NATIVE are byte/seed duplicates, the executable unique
registry aliases rather than reruns 112 slots/root (`16 tasks x 7`) in all
eight DEV/confirmation roots. Therefore:

| session partition | nominal slots | duplicate aliases | unique actor slots | wall/device cap |
|---|---:|---:|---:|---:|
| P00 discovery A1+A2+A3 | 1,344 | 0 | 1,344 | 3,600 s |
| P01 conditional A4 | 448 | 0 | 448 | 1,800 s |
| P02--P05 remaining DEV, one exposed root each | 1,464 each | 112 each | 1,352 each | 3,600 s each |
| P06--P09 confirmation, one blinded root each | 1,576 each | 112 each | 1,464 each | 3,600 s each |
| **maximum with A4** | **13,952** | **896** | **13,056** | **34,200 s** |

If A4 is prohibited because A3 passes, the logical/unique maxima are 13,504
and 12,608. No duplicate call or padding call is issued to consume the larger
authorization envelope.

Per-root arithmetic is fixed:

- remaining DEV: seven logical read-disabled delayed projections
  `7 x 16 x 7 = 784`, ACTIVE delayed `16 x 19 = 304`, four read-disabled
  reachout projections `4 x 8 x 7 = 224`, ACTIVE reachout `8 x 19 = 152`;
  total 1,464, less 112 FULL/NATIVE aliases = 1,352 unique;
- confirmation: eight logical read-disabled delayed projections
  `8 x 16 x 7 = 896`, plus 304 + 224 + 152 = 1,576, less 112 aliases =
  1,464 unique.

The current native actor permits at most 1,952 calls, but the old zero-fit
driver incorrectly requires exactly 1,952. Do not change or reuse that frozen
driver. The new R1 driver must require
`actor.max_calls == len(unique_call_slot_registry) <= 1952` per partition.
Each logical alias maps to one existing physical request/response ID; it is not
a second slot.

Actual calls may be below the slot maximum when a task terminates early. Every
unused slot gets an explicit `NOT_REACHED` reason. A partition timeout/failure
is terminal for its stage; never restart a session or replay completed tasks.

The original undeduplicated token ceilings are 3,407,872 actor-generated and
1,048,576 returned-memory tokens. Duplicate reuse reduces the executable
actor-token ceiling to 3,145,728; returned-memory remains 1,048,576. If A4 is
skipped, subtract 131,072 actor tokens. Each partition includes cold load
through verified engine shutdown inside its stated wall/device cap. The ten
caps sum to 34,200 seconds only in the A4 path and do not authorize another
partition.

## 9. Reducer and terminal dispositions

Every physical task record must include:

- partition/session/task/root/projection/view and all logical alias IDs;
- raw response UTF-8 hash, token IDs, family, call index, full prefix hash,
  stop reason, and exact generation receipt for every turn;
- independent generation/THINK/READ/actor-token/returned-token counters;
- registered query identity, `MISS` status, returned block/source hashes;
- exact terminal syntax, task-root start/goal match, legality, graph success,
  relevant-Q success, donor-ID use, and cap/invalid failure;
- the joint flags defined above; and
- prompt/model/tokenizer/source/partition/confirmation commitment hashes.

Reducers report joint gates first and marginals only as diagnostics. They also
report per-root paired task vectors, RA and RB separately, first-position
choice, malformed family counts, cap failures, and duplicate alias mappings.
No across-root pooling, independence claim, imputation, permissive rescoring,
or downstream rescue is allowed.

Terminal labels are:

- `DEV_A3_SELECTED`;
- `DEV_A4_SELECTED_SCAFFOLDED`;
- `STOP_TYPED_INTERFACE_UNQUALIFIED`;
- `STOP_TRAVERSAL_CEILING_FAILED`;
- `STOP_DEV_PANEL_FAILED`;
- `CONFIRMED_C0_SUPPLIED_MEMORY_INTERFACE_A3`;
- `CONFIRMED_C0_SUPPLIED_MEMORY_INTERFACE_A4_SCAFFOLDED`; or
- `STOP_CONFIRMATION_FAILED_ROOTS_BURNED`.

## 10. Narrow claim boundary

An untouched A3 confirmation permits only:

> For this frozen 7B revision, world topology, root generator, and typed
> recurrent interface, the clean base used sufficient supplied route memory
> through the disclosed service and committed exact candidate-free routes and
> relevant experiments on four interface-confirmation roots.

An A4 confirmation must add:

> The generic traversal algorithm was supplied in the public scaffold.

The A2/A3 comparison may say only that typed recurrent THINK changed success
under the common actor-token cap. It cannot attribute the change specifically
to state retention rather than extra calls, self-produced history, or the
CONTINUE prompt.

No outcome here supports LoRA storage, own-experience acquisition, retention,
compression, continual learning, parenting, lifetime improvement, recurrence
as a learned property, or whole-organism performance. ACTIVE_LINKED_TEXT is a
supplied-memory ceiling, not the strong evolving external-memory baseline.

## 11. Astra's implementation-ready checklist

Before any model call, Astra should have one immutable preparation receipt
showing:

- all exact prompt/response/service bytes and hashes;
- all A3/A4 DEV and blinded confirmation catalogs pre-materialized;
- confirmation/generator/tokenizer/disjointness commitments;
- arm matrix equality and the sole READ-capability delta;
- counter boundary tests and no-stop-string/no-extraction tests;
- unchanged scorer hashes and SEQ-167 immutability;
- exact 13,952 nominal / 13,056 unique call arithmetic and P00--P09 slot
  registries;
- FULL/NATIVE duplicate proof and alias map;
- joint-gate reducer fixtures including the 56/64 overlap counterexample;
- A4 eligibility/skip fixtures;
- order-only reachout equality and 16/0 rejection fixture;
- fresh detached lifecycle/shutdown tests; and
- one command per partition, with later commands refusing to start absent the
  exact predecessor disposition marker.

This is the complete v2 handoff. The scoped own-write run remains separate: it
can diagnose exact row storage, but no writer output becomes a route result
until this supplied-memory acting ceiling is independently qualified.
