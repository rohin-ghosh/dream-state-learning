# PCFL v2.2 distractor: exact execution-contract candidate

**Date:** 2026-09-13 UTC  
**Role:** contract/tokenization closure candidate  
**Scope:** memo only; no source, test, tokenizer, model, fixture, training, or GPU
work

## Verdict

The strongest minimal completion is:

- relevant frontier: `H -> S_R`, with private port pair `q0/q1` selected by
  `R`;
- distractor frontier: **`X -> Z`**, using the same private port pair
  **`q0/q1`** selected independently by `D`;
- either probe returns the same neutral public result shape, revealing only
  the selected probe, its declared endpoints, and one opaque port;
- a relevant result is followed by the already-registered `EXPLORE`, ordinary
  executed-event receipt, `EVENT`, and two `LINK` opportunities;
- a distractor result is terminal and creates no `EVENT`, `LINK`, receipt, or
  authentic lineage; and
- public `GOAL` and both `ROUTE` endpoints are `N_` node IDs. `G_` IDs are
  private task-instance handles only and never reach the model.

This uses the two otherwise dangling OLD branches deliberately placed in the
registered skeleton:

```text
S_L --a_(1-O)--> X       Z --u--> Y
```

The distractor result is therefore a genuine, action-conditioned, one-bit
observation about an isolated frontier. It is not the archived partial core's
causally empty `D` bit. At the same time it cannot create a route to either
delayed target and cannot enter SLEEP.

This is a **new prospective construction binding**, not a fact recoverable
from the previously passed bytes. Adopting it requires a successor source pin
and contract-schema bump before tokenizer preparation. It does not change the
registered arms, denominators, thresholds, roots, fit count, claims, or GPU
arithmetic. It closes the previously acknowledged topology/render ambiguity.

## Authority and narrow supersession

The candidate preserves these current sources:

| role | SHA-256 |
|---|---|
| `2026-09-13_pcfl_vertical_dev_v2_synthesis.md` | `222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456` |
| `2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md` | `683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca` |
| `2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md` | `5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd` |
| `2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md` | `f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679` |
| `2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md` | `599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b` |
| `2026-09-13_pcfl_v22_minimum_execution_closure_contract.md` | `f9b9891761c47e6d8047e7a9161a827d00fae464df91940c523b40f85af535d0` |

It supersedes only the unresolved distractor/goal/receipt-render seam
identified by
`2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md`
(`bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`).
Every unaffected v2.2 field retains the prior source and value.

## 1. Exact wire types

All JSON objects are closed-schema. Unknown, missing, duplicate, or
wrong-typed fields fail preparation. In particular, Python `bool` is not an
integer bit.

```text
Bit       := JSON integer 0 or 1, never true/false
SHA256    := lowercase ASCII matching ^[0-9a-f]{64}$
NID       := ASCII matching ^N_[A-Z2-7]{10}$
PID       := ASCII matching ^P_[A-Z2-7]{10}$
EID       := ASCII matching ^E_[A-Z2-7]{10}$
LID       := ASCII matching ^L_[A-Z2-7]{10}$
QID       := ASCII matching ^Q_[A-Z2-7]{10}$
RID       := ASCII matching ^R_[A-Z2-7]{10}$
GID       := ASCII matching ^G_[A-Z2-7]{10}$
UTF8      := a JSON string whose encoded bytes are valid UTF-8
```

Every opaque ID is exactly 12 ASCII bytes. Field parsers enforce the field's
type; there is no generic opaque-ID fallback.

Private structural slot enums are:

```text
node  = [S_L,A,H,G_L,S_R,B,G_R0,G_R1,X,Z,Y]
port  = [a0,a1,b,c,d,f0,f1,u,q0,q1]
event = [e0,e1,e2,e3,e4,e5,e6,e7,e8]
link  = [l0,l1,l2,l3,l4,l5]
probe = [relevant,distractor]
receipt = [r0,r1,r2,r3,r4,r5,r6,r7,r8]
goal  = [old_left,old_right,delayed0,delayed1]
```

No opaque slot is added. Actions are keyed by `(source,port)`, so the same
prepared `P_` ID may deterministically denote `H -> S_R` at source `H` and
`X -> Z` at source `X`. No distractor EVENT, LINK, or receipt slot is added.

## 2. Candidate A--E contract fragment

This is a structural JSON fragment. `slot_ref` is resolved during the existing
deterministic opaque-inventory preparation, after which each root also stores
the instantiated exact UTF-8 bytes, hashes, and tokenizer receipts. The
runtime may consume only the prepared instantiation.

### A. Source truth, topology, and goal typing

```json
{
  "A_source_truth": {
    "distractor_binding_schema": "PCFL_V2_2_DISTRACTOR_XZ_V1",
    "new_port_slots": [],
    "frontiers": [
      {
        "frontier_id": "RELEVANT",
        "probe_slot_ref": "probe/relevant",
        "source_node_slot_ref": "node/H",
        "destination_node_slot_ref": "node/S_R",
        "outcome_private_bit": "R",
        "port_by_bit": {"0": "port/q0", "1": "port/q1"},
        "probe_materializes_event": false,
        "post_result_transition": "REVEAL_THEN_EXPLORE",
        "explore_event_slot_ref": "event/e8",
        "explore_receipt_slot_ref": "receipt/r8",
        "may_enter_authentic_lineage": true
      },
      {
        "frontier_id": "DISTRACTOR",
        "probe_slot_ref": "probe/distractor",
        "source_node_slot_ref": "node/X",
        "destination_node_slot_ref": "node/Z",
        "outcome_private_bit": "D",
        "port_by_bit": {"0": "port/q0", "1": "port/q1"},
        "probe_materializes_event": false,
        "post_result_transition": "REVEAL_THEN_TERMINATE",
        "explore_event_slot_ref": null,
        "explore_receipt_slot_ref": null,
        "may_enter_authentic_lineage": false
      }
    ],
    "goal_policy": {
      "private_goal_handles": {
        "old_left": "goal/old_left",
        "old_right": "goal/old_right",
        "delayed0": "goal/delayed0",
        "delayed1": "goal/delayed1"
      },
      "target_node_slots": {
        "old_left": "node/G_L",
        "old_right": "node/G_R0",
        "delayed0": "node/G_R0",
        "delayed1": "node/G_R1"
      },
      "model_visible_goal_field_type": "NID",
      "route_start_field_type": "NID",
      "route_goal_field_type": "NID",
      "gid_visibility": "PRIVATE_ONLY",
      "gid_in_model_bytes": false
    },
    "prohibitions": {
      "add_distractor_only_port_slots": true,
      "distractor_event_or_link_target": true,
      "distractor_in_authentic_lineage": true,
      "distractor_in_sleep_corpus": true,
      "loss_active_pad": true,
      "target_token_equalization": true
    }
  }
}
```

Here a `true` value in `prohibitions` means the named behavior is forbidden.
The literal prompt label `GOAL` remains unchanged; its substitution is the
target `NID`. A `GID` may identify a task inside sealed manifests and work
rows, but a renderer containing it is invalid. This preserves the already
registered prompt and makes a one-shot route executable without leaking an
extra opaque alias.

### B. Exact public bytes, parsers, allowlists, and tokenizer classes

Every string below uses UTF-8, LF (`0x0a`) only between shown lines, no
trailing spaces, and **no terminal LF**. The labels before the triple-quoted
strings are registry metadata and are not rendered.

`RA`:

```text
PROBE TASK
START {START_NODE_ID}
GOAL {GOAL_NODE_ID}
AVAILABLE PROBES
1. {RELEVANT_PROBE_ID} TESTS {RELEVANT_SOURCE_NODE_ID} TO {RELEVANT_DESTINATION_NODE_ID}
2. {DISTRACTOR_PROBE_ID} TESTS {DISTRACTOR_SOURCE_NODE_ID} TO {DISTRACTOR_DESTINATION_NODE_ID}
Commit exactly: PROBE <probe_id>
```

`RB`:

```text
PROBE TASK
START {START_NODE_ID}
GOAL {GOAL_NODE_ID}
PROBE OPTIONS
1. TEST {DISTRACTOR_SOURCE_NODE_ID} TO {DISTRACTOR_DESTINATION_NODE_ID} USING {DISTRACTOR_PROBE_ID}
2. TEST {RELEVANT_SOURCE_NODE_ID} TO {RELEVANT_DESTINATION_NODE_ID} USING {RELEVANT_PROBE_ID}
Commit exactly: PROBE <probe_id>
```

`PROBE_RESULT` (same template for both roles and both bit values):

```text
PROBE RESULT
PROBE {SELECTED_PROBE_ID}
SOURCE {SELECTED_SOURCE_NODE_ID}
PORT {SELECTED_PORT_ID}
DESTINATION {SELECTED_DESTINATION_NODE_ID}
```

`SINGLETON_EXPLORE_TASK` is the already-registered EXPLORE template with one
port:

```text
EXPLORE TASK
SOURCE {SOURCE_NODE_ID}
AVAILABLE PORTS {PORT_ID}
Choose one still-untried port and output exactly:
EXPLORE <source> <port>
```

`PUBLIC_EXECUTED_EVENT_RECEIPT`:

```text
EXECUTION RECEIPT
RECEIPT {RECEIPT_ID}
SOURCE {SOURCE_NODE_ID}
PORT {PORT_ID}
DESTINATION {DESTINATION_NODE_ID}
```

The exact user-message joins are:

```text
RELEVANT_RESULT_TO_EXPLORE = PROBE_RESULT + "\n\n" + SINGLETON_EXPLORE_TASK
DISTRACTOR_TERMINAL_RESULT = PROBE_RESULT
RECEIPT_TO_EVENT_COMMIT    = PUBLIC_EXECUTED_EVENT_RECEIPT + "\n\n" + COMMIT_EVENT
```

All joined messages also have no terminal LF. There is no free string
assembly, alternative heading, punctuation normalization, fence, or
whitespace tolerance.

Strict generated-action parsers are:

```text
PROBE   := ^PROBE (Q_[A-Z2-7]{10})$
EXPLORE := ^EXPLORE (N_[A-Z2-7]{10}) (P_[A-Z2-7]{10})$
ROUTE   := ^ROUTE (N_[A-Z2-7]{10}) (N_[A-Z2-7]{10}) : (P_[A-Z2-7]{10})(,(P_[A-Z2-7]{10}))*$
```

They reject terminal LF, extra prose, multiple commands, a `G_` in either
ROUTE endpoint, a wrong namespace in any field, and a validly shaped but
unregistered ID.

The model-visible projection allowlists are exact:

```text
ReachoutTaskPublic = {
  start_node_id:NID,
  goal_node_id:NID,
  options:[{probe_id:QID,source_node_id:NID,destination_node_id:NID} x2],
  render_id:{RA|RB}, visible_utf8:UTF8, visible_sha256:SHA256
}

ProbeResultPublic = {
  probe_id:QID, source_node_id:NID, destination_node_id:NID, port_id:PID,
  visible_utf8:UTF8, visible_sha256:SHA256
}

ExecutedEventReceiptPublic = {
  receipt_id:RID, source_node_id:NID, port_id:PID,
  destination_node_id:NID, visible_utf8:UTF8, visible_sha256:SHA256
}
```

`root_id`, `root_skeleton_hash`, `O`, `R`, `D`, `GID`, frontier role,
relevance/usefulness, unselected outcome, correct route, cuts, scores, branch,
stage, turn, ancestry hashes, and private structural names are forbidden in
all model-visible projections.

The private contract allowlist is exact:

```text
FrontierPrivate = {
  frontier_id:{RELEVANT|DISTRACTOR}, probe_id:QID,
  source_node_id:NID, destination_node_id:NID,
  bit_source:{R|D}, port0_id:PID, port1_id:PID,
  post_result_transition:{REVEAL_THEN_EXPLORE|REVEAL_THEN_TERMINATE},
  explore_event_id:EID-or-null, explore_receipt_id:RID-or-null,
  may_enter_authentic_lineage:boolean
}

GoalBindingPrivate = {
  goal_handle:GID,
  goal_kind:{OLD_LEFT|OLD_RIGHT|DELAYED0|DELAYED1},
  start_node_id:NID, target_node_id:NID
}

RoutePrivate = {
  start_node_id:NID, target_node_id:NID,
  ordered_port_ids:[PID,PID,PID,PID,PID],
  exact_route_utf8:UTF8, exact_route_sha256:SHA256,
  old_cut_event_id:EID, new_cut_event_id:EID
}

WorldCellPrivate = {
  root_skeleton_hash:SHA256, O:Bit, R:Bit, D:Bit,
  opaque_inventory_ref:SHA256,
  frontiers:[FrontierPrivate,FrontierPrivate],
  outcome_table_ref:SHA256,
  goal:GoalBindingPrivate,
  correct_route:RoutePrivate,
  render_assignment_ref:SHA256,
  address_assignment_ref:SHA256,
  counterpart_assignment_ref:SHA256
}
```

For OLD-route tasks, `RoutePrivate.ordered_port_ids` is a closed two- or
three-item list rather than the five-item delayed list; the `route_kind` in
the enclosing work row fixes which arity is legal. The delayed outcome table
always uses exactly five ports.

The prepared tokenizer registry must enumerate these substitution classes:

1. `REACHOUT_SURFACE/{root}/{O}/{goal}`: complete chat-templated RA versus RB
   input, equal token count;
2. `REACHOUT_OPTION_ROWS/{root}`: the two option rows within each surface,
   equal token count after their role-specific substitutions;
3. `PROBE_RESULT_ALL/{root}`: relevant-R0, relevant-R1, distractor-D0, and
   distractor-D1 result renders, one equal token count;
4. `RELEVANT_RESULT_JOIN/{root}`: R0 versus R1 complete result-plus-EXPLORE
   user messages, equal token count;
5. `RELEVANT_RECEIPT_JOIN/{root}`: R0 versus R1 complete
   receipt-plus-COMMIT-EVENT user messages, equal token count;
6. `E8_EVENT_R_PAIR/{root}`, `L4_LINK_R_PAIR/{root}`, and
   `L5_LINK_R_PAIR/{root}`: the registered R0/R1 grammar rows, equal within
   each class; and
7. every pre-existing EVENT_TWIN, LINK_PERMUTE, READ, ROUTE, collision, and
   zero-fit class from v2.2.

Equality is checked on the exact pinned tokenizer and chat template. It is not
inferred from byte length or bare-ID length. Every accepted ID still has the
same bare-token length in `4..12`. Failure to find one joint inventory that
satisfies all classes is `VS_ASSAY_INVALID`, with no redraw or relaxed class.
No loss-active PAD may repair a mismatch.

### C. Cube, outcome table, branch state, and receipt chain

For every fixed `(root,O,goal)`, the prepared table is exactly:

| R | D | relevant result port | distractor result port | correct delayed route contains |
|---:|---:|---|---|---|
| 0 | 0 | `q0` | `q0` | `q0` |
| 0 | 1 | `q0` | `q1` | `q0` |
| 1 | 0 | `q1` | `q0` | `q1` |
| 1 | 1 | `q1` | `q1` | `q1` |

`q*` denotes private slots; the prepared report records only their
corresponding `P_` IDs. `R` and `D` index the same two-token alphabet but are
independent. Normalizing the two outcomes back to bits must give exactly:

```text
H(Y_R)=1
H(Y_D)=1
I(Y_R;Z_G)=1
I(Y_D;Z_G)=0
```

where `Z_G` is the exact correct ROUTE at the fixed goal. All four
pre-commit model-visible byte sequences are identical; the outcome-table and
bit fields are private.

The reachout state machine is literal:

```text
PRECOMMIT
  valid relevant PROBE   -> RELEVANT_COMMITTED -> reveal relevant result
                            -> require one EXPLORE H q_R
                            -> reveal ordinary r8 receipt
                            -> one EVENT + two LINK opportunities
  valid distractor PROBE -> DISTRACTOR_COMMITTED -> reveal distractor result
                            -> TERMINAL_DISTRACTOR
  malformed/unregistered/multiple PROBE
                          -> TERMINAL_INVALID with no result and no retry
```

There is one PROBE generation and one commitment. A distractor result is the
complete terminal public response: no extra termination text, EXPLORE prompt,
event address, receipt, relevant outcome, correction, or retry is returned.

The probe result itself is **not** an executed-event receipt, receives no
`R_` ID, and cannot support an EVENT or LINK commitment. Only a valid
`EXPLORE` of the revealed relevant port creates `r8` and `e8`.

The private custody record for that result is:

```text
ProbeResultCustody = {
  root_skeleton_hash:SHA256, cell_id:SHA256,
  branch_id:{R0|R1|D0|D1}, selected_probe_id:QID,
  committed_probe_generation_sha256:SHA256,
  public_result_sha256:SHA256, terminal_after_result:boolean,
  custody_sha256:SHA256
}
```

It hashes the canonical object without `custody_sha256`; none of its custody
fields is model-visible. R0/R1 result records cite the same one sealed
pre-outcome state and common committed-PROBE generation before forking.

Executed-event receipt custody is a separate, exact chain:

```text
PublicReceiptInternal = {
  root_skeleton_hash:SHA256, branch_id:{OLD|R0|R1}, stage:{OLD|NEW},
  turn:nonnegative integer, receipt_id:RID,
  source_node_id:NID, port_id:PID, destination_node_id:NID,
  committed_explore_generation_sha256:SHA256,
  previous_receipt_sha256:SHA256-or-null,
  public_visible_sha256:SHA256,
  receipt_sha256:SHA256
}
```

`receipt_sha256` hashes the canonical record without its own field. OLD
receipts are one stage-local chain: `r0` has `turn=0` and null predecessor;
for `i=1..7`, `ri.turn=i` and `ri.previous_receipt_sha256` equals the complete
hash of `r(i-1)`. Each sterile R continuation starts a fresh NEW chain: `r8`
has `turn=0` and null predecessor. R0 and R1 may reuse the same prepared `R_`
address because they are mutually exclusive counterfactual branches, but
their receipt/public hashes differ when `q_R` differs and neither may cite the
other. `committed_explore_generation_sha256` separately proves that each
receipt is downstream of the exact source-qualified action that caused it.
Only the exact four-field public receipt projection above is shown to the
model.

An admitted `EVENT e8` must cite exactly the visible `r8`, occur after that
receipt, and copy its `H`, `q_R`, and `S_R` IDs byte-for-byte. Exact evidence
order is:

```text
e8 cites r8
l4 (e1 THEN e8 VIA H) cites r1,r8
l5 (e8 THEN e3 VIA S_R) cites r8,r3
```

Here names are private structural slots; model bytes contain their prepared
`E_`/`R_`/`L_` IDs. No D-branch trace or result can be a support span, replay
source, counterpart, corpus slot, or authentic ancestor.

The existing opaque inventory, replay, and batch registries are otherwise
unchanged. The new result and join substitution classes must still be checked,
but no new ID, training slot, or item is added.

### D. Calibration

The complete v2.2 LOW/HIGH calibration state machine is inherited byte-for-byte.
The successor contract permits **no D-specific calibration field, branch,
score, fit, target, or trigger**. In particular, a D outcome may not affect
LOW/HIGH selection, writer gates, replay selection, batch order, or rank.

The validator should enforce:

```json
{
  "D_calibration_binding": {
    "inherited_without_change": true,
    "distractor_visible_to_calibration": false,
    "distractor_can_trigger_high": false,
    "distractor_training_rows": 0,
    "distractor_fits": 0
  }
}
```

This object is a guard assertion; it does not replace the already-required
literal calibration subtree.

### E. Route/cut, work, and custody invariants

The private frontier registry may contain `X -> Z` as a potential probed
connection, but the witnessed graph contains only executed EVENTs. Therefore:

- toggling `D` changes exactly one prepared distractor `PROBE_RESULT` port and
  its bytes/hash;
- toggling `D` changes no OLD or NEW EVENT/LINK row, address, receipt, route,
  cut, goal, task prompt, corpus, fit, or authentic state;
- toggling `R` changes the relevant result port, `e8`, `l4/l5`, and the unique
  correct delayed ROUTE, but not the pre-outcome bytes;
- adding the potential `X --q_D--> Z` connection to an independent full-graph
  oracle still gives no path from `S_L` through that branch to `G_R0/G_R1`;
- the only successful delayed route is
  `S_L --a_O,b,q_R,d,f_goal--> G_R_goal`;
- cutting `e0` destroys success in every cell;
- cutting `e8` destroys success in every cell;
- cutting or toggling the distractor frontier never changes delayed success;
  and
- a route that takes `a_(1-O),q_D,u` terminates at `Y` and fails both delayed
  goals.

The work registry adds no model call or fit merely to populate D. It does add
deterministic prepared-result/terminal work rows for every D cell and a
conditional public-result return after an actually committed distractor
PROBE. These are service/render records, not generations. The one primary DEV
reachout generation remains exactly one; on a distractor commitment its root
stops before S2 as already registered.

`root_skeleton_hash` must change if any distractor endpoint, port mapping,
probe-role mapping, exact render, LF policy, join, goal-type policy, or branch
transition changes. It must not contain a child generation, score, loss,
adapter, or runtime result.

## 3. Fail-closed test matrix

These tests are additions to, not replacements for, the 13 closure cases and
the archived 20 route-algebra tests.

1. **Closed types:** reject wrong widths/alphabets/prefixes, lower-case IDs,
   booleans as bits, generic-ID parsing, `G_` in ROUTE, and unknown fields.
2. **Exact frontier:** require relevant `H -> S_R` and distractor `X -> Z`;
   mutate either endpoint and fail.
3. **Shared matched alphabet:** require both frontiers to use exactly the same
   distinct `q0/q1` pair. A third port, a role-specific pair, q0/q1 aliasing,
   missing slot, or cross-root collision fails. Prove `(source,port)` remains
   a deterministic transition in all cells.
4. **Golden renders:** byte-snapshot RA, RB, all four PROBE_RESULTs,
   both relevant joins, both receipts/receipt joins, and the distractor
   terminal response. Flip one byte, space, order, separator, or final LF and
   fail.
5. **RA/RB fact identity:** parse both renders to the same unordered two
   `(probe,source,destination)` tuples and opposite order. Any extra fact or
   role word fails.
6. **Pre-outcome collision:** all `16/16` `(root,O,goal)` R/D quartets have one
   exact pre-outcome hash. Inject `R`, `D`, port, result, role, or route and
   fail.
7. **Real D outcome:** within each quartet, D0/D1 result bytes and selected
   `P_` IDs differ while every non-outcome field stays fixed. A symbolic/no-op
   D fails.
8. **Exact information table:** recover all `00,01,10,11` cells once and exact
   `(1,1,1,0)` information values with two independent implementations.
9. **Public allowlists:** serialize only the three model-visible object types
   above. Inject a root/hash/bit/GID/role/cut/score/branch field and fail.
10. **One-shot transition:** relevant gets result+one EXPLORE; distractor gets
    result+terminal; malformed gets no result+terminal. Any retry, correction,
    second PROBE, D receipt, or relevant reveal after D fails.
11. **Receipt chain:** corrupt branch, sequence, predecessor, exact bytes,
    receipt ID, source, port, destination, or hash and fail. Cross R0/R1 or
    OLD/NEW chaining fails.
12. **Admission chronology:** e8 before r8, wrong receipt, wrong q port,
    reconstructed/repaired EVENT, or any D-supported row fails. Both NEW LINKs
    must cite the exact visible receipt pair and child spans.
13. **Route uniqueness:** both independent oracles agree `64/64`; OLD and NEW
    cuts fail `64/64`; D toggle/cut changes `0/64`; the X-Z-Y route fails both
    targets in every cell.
14. **Projection neutrality:** D toggling changes no OLD_ONLY, NEW_ONLY,
    FULL-child-memory, target row, address, replay, batch, or correct route
    hash. It changes only the named D result/terminal records.
15. **Goal policy:** every public GOAL substitution and ROUTE endpoint is
    `N_`; every private task has exactly one `G_`; no `G_` occurs in any
    model-visible prompt, target, receipt, row, or parser success.
16. **Tokenizer classes:** enumerate every class in Section 2B; require equal
    pinned-tokenizer counts and complete receipts. Missing candidate receipts,
    source/tokenizer/chat-template drift, or pool exhaustion fails without
    redraw or PAD.
17. **No training expansion:** assert D contributes zero corpus slots, views,
    targets, replay sources, fits, and updates; all v2.2 20-slot/160-item/200-
    update denominators remain exact.
18. **Root-hash sensitivity:** each bound D/goal/render/transition mutation
    changes `root_skeleton_hash`; generated-output/score/loss injection is
    rejected rather than hashed.
19. **Shortcut audit:** rerun every singleton/pairwise projection and the
    32-cell RA/RB reachout certificate with the production IDs/renders; all
    registered coverage/support/label/Bayes bounds must hold.
20. **Model-call gate:** `execution_contract_valid` and
    `ready_for_model_calls` remain false until all preceding tests, exact
    tokenizer materialization, source-pin update, sidecar, and validation
    report pass.

## 4. Why this is the minimal scientifically strong choice

`X -> Z` is better than inventing two new nodes: the registered OLD life
already supplies both endpoints and the paths around them, so the useful and
irrelevant probes can be judged using the same learned graph. Reusing
`q0/q1` is stronger than inventing `v0/v1`: both experiments return the same
two-token alphabet, and source-qualified actions remain deterministic. Seeing
`q_D` predicts `q_R` at exactly chance because `D` and `R` are independent.
It is better than adding a distractor EVENT: an extra authored row would
change S2, the writer roster, and the fit arithmetic. It is better than
leaving D symbolic: D0/D1 now cause different ordinary public bytes after a
committed action.

The result remains deliberately narrow. Both delayed goals still make the
same frontier useful, so this tests memory-dependent **task-relevant
expansion**, not goal-switched experiment selection. The distractor never
enters SLEEP, so it does not create another experiential-learning claim.

## Adoption boundary

Do not silently paste these choices into runtime code. If adopted, the
prepared contract must:

1. pin this memo's exact post-commit SHA-256 as a new controlling source;
2. bump its schema to include `PCFL_V2_2_DISTRACTOR_XZ_V1`;
3. replace the unresolved-D sentinel with this exact A--E fragment;
4. rerun deterministic tokenizer qualification over every new substitution
   class using the existing opaque slots; and
5. pass the complete CPU and real-tokenizer gates before the first model call.

Until then, `execution_contract_valid=false` and
`ready_for_model_calls=false` remain correct.
