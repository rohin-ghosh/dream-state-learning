# PCFL `NATIVE-STEP-v1` pre-source red-team

**Date:** 2026-09-13 PT

**Role:** independent adversarial review before implementation or execution

**Scope:** documentation only. No source, benchmark/root, model, tokenizer,
adapter, process, GPU, or remote state changed.

## Decision

`STEP` is a sound **interaction primitive**: a model-selected irreversible
action followed by the ordinary next public state does not inherently leak an
answer. It is a better physical match to an acting agent than requiring one
five-port `ROUTE` string.

But the exact eight A3C/A4 PCFL cases do **not** make it a valid test of
multi-step prospective planning. A fixed depth-one public-graph policy solves
all `8/8` cases and all `64/64` cases in the four excluded-root cube. The
planned fixed-first, fixed-last, and random controls miss this shortcut.
Displayed-row or action-option reordering cannot remove it.

Therefore:

1. do not implement or run the authorized condition as a claim-bearing
   `prospective` ceiling;
2. the existing roster may be retained only as a separately named
   **interface/local-memory-use ceiling**;
3. any such successor must use one arm-symmetric generic `STEP` grammar, not
   concrete port enumeration for text/service arms and generic syntax for the
   native LoRA arm; and
4. no currently sealed PCFL root, cube cell, cut, or registered goal repairs
   the prospective construct. A future prospective STEP task needs a
   prospectively authored topology that first defeats the shallow controls
   below. This memo does not authorize or author that benchmark change.

## 1. Exact material inspected

- Proposed decision: commit `51635912`,
  `research_notes/analysis/2026-09-13_pcfl_post_a4_resolver_decision.md`.
- Initial root ruling: commit `8f75f0de`.
- Preserved four A3C/A4 root wires:
  `research_notes/astra_memos/receipts_20260912/`
  `astra_pcfl_c0_inventory_20260913_attempt1/roots.json`, SHA-256
  `bcca78ae2abadb2a5f9680dc70ed55327185614198a4b873a5f3e487b2ed443e`.
- Current world/scorer: `organism_v6/pcfl_vertical_dev.py`.
- Current A3C/A4 roster and grammar:
  `gpu/astra_pcfl_interface_dev.py`.
- Independent A3C and A4 terminal audits, including exact task, route, seed,
  grammar and result reconstruction.

`SMOKE_INDICES=(0,1,16,17,32,33,48,49)` selects cell `old=0`,
`relevant=0`, `distractor=0`, and goals `0/1` for each of four excluded
roots. The identifiers differ by root; the topology does not.

## 2. Constructive shortcut proof

The witnessed graph has these role-level transitions:

```text
S_L --a_old--> A --b--> H --q_relevant--> S_R --d--> B --f_goal--> GOAL
  \--a_other--> X (no witnessed outgoing edge)

H --c--> G_L (no witnessed outgoing edge for delayed goals)
B --f_other--> OTHER_GOAL
```

Use only the exact public `EDGE source port destination` rows and `GOAL`:

```text
LOCAL-1(current, goal):
  if an outgoing edge lands directly at goal, choose it
  otherwise choose the outgoing edge whose destination appears as the source
  of the greatest number of visible witnessed edges
  break ties by the fixed public order
```

This is not a path search. It never retains a candidate path, backtracks,
compares a complete route, uses LINK, or reasons beyond the next
destination's visible outdegree.

On every delayed task:

- at `S_L`, `A` has outdegree one while `X` has zero, so it chooses
  `a_old`;
- at `A`, only `b` is available;
- at `H`, `S_R` has outdegree one while `G_L` has zero, so it chooses
  `q_relevant`;
- at `S_R`, only `d` is available; and
- at `B`, exactly one edge lands directly at the stated goal.

The selected ports are byte-identical to the oracle route in all exact smoke
cases:

| root | goal 0 / goal 1 common prefix | final choice | LOCAL-1 |
|---:|---|---|---:|
| 0 | `P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH` | `P_RK7VLTKHNM` / `P_FOPIRGXLPW` | 2/2 |
| 1 | `P_CU72HSSTHQ,P_PG3IQT75KG,P_Q5KBAFY6SQ,P_O66CHZFQQF` | `P_QKUOHFCFN7` / `P_CLTAYE7KH3` | 2/2 |
| 2 | `P_UKIGM5XADX,P_NXINQGYHG4,P_UF3VWEYYWN,P_BXHVFSUI45` | `P_U6CRRINMLI` / `P_BZOTFNJ5FE` | 2/2 |
| 3 | `P_Y4YTR3GSDB,P_R2GBO7FYMF,P_G2BXGAQCJU,P_E6ERNF6OLY` | `P_FK4GQNFXOT` / `P_ELHF2YQISI` | 2/2 |

Deterministic reconstruction from the preserved root wires gives:

```text
                                 exact smoke      full excluded cube
fixed-first public edge               0/8                 0/64
fixed-last public edge                0/8                 0/64
LOCAL-1                               8/8                64/64
```

The result is invariant to `old` and `relevant`, because those bits relabel
the correct port but do not change destination degrees. `distractor` changes
only the private latent `X -> Z` port; that transition is deliberately absent
from the witnessed graph and authentic memory bank.

The two delayed goals share the first four correct actions. `GOAL` affects
only the final one-edge choice at `B`. Thus the proposed same-root
goal-sensitivity gate proves only direct destination matching, not that a
future goal changed an earlier decision.

The eight-STEP cap does not cure this. The graph is acyclic, the correct path
has five edges, and a wrong witnessed branch reaches a dead state. Extra
budget enables neither recovery nor search.

## 3. Why the original controls are insufficient

Fixed-first and fixed-last test a single global ordering bias. Balanced random
tests chance. Neither tests the strongest cheap policy exposed by the public
state.

At minimum, every future STEP protocol must precompute and print these nulls
on the exact frozen roster, before a model is run:

1. `FIXED_FIRST` and `FIXED_LAST` under every displayed order;
2. presealed uniform `RANDOM_LEGAL`, with its exact realized score and the
   analytical chance rate;
3. `DIRECT_GOAL_ELSE_FIRST`: choose a direct-goal destination when present,
   otherwise choose first;
4. `LOCAL_1_DEGREE`: the policy proved above;
5. `POSITION_SCRIPT`: the best predeclared action-ordinal policy over the
   successive branch positions, with and without direct-goal matching; and
6. for a LINK-visible/service condition, `HAS_LINK_ELSE_FIRST`: choose a
   candidate whose EVENT has any returned outgoing LINK, without examining
   deeper content.

A condition may be called a multi-step prospective test only if every
depth-zero/one policy remains at or below the prospectively set null bound.
The proposed `<=4/8` bound is reasonable, but the current topology fails it
`8/8` before model execution.

Order controls remain necessary for identifier-copying and position bias, but
they are not a remedy: `LOCAL_1_DEGREE` is order invariant. The proposal also
does not specify how two order views fit inside one eight-task run. Before any
interface-only run, bind one order view per root (both goals share the same
view), balanced `4/4`, and report the two four-task cells separately. Do not
claim paired order robustness from that unpaired smoke.

## 4. Arm-symmetric action boundary required before source freeze

The proposal dynamically enumerates concrete allowed ports in exact-graph and
text/service arms but uses a generic port grammar for native LoRA. That is an
arm-dependent decoding intervention: one condition can only emit a valid
visible candidate while the claim-bearing child must retrieve, type and
select an opaque ID. It invalidates a direct native-LoRA versus automatic-text
comparison.

Use the same static union for every actor call in every arm:

```regex
(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*|STEP P_[A-Z2-7]{10})\n?
```

Required semantics:

- no concrete node, port, EVENT, LINK, address, route, answer, or candidate
  list appears in the decoding grammar;
- the model may copy an ID from text or recall it parametrically, but the host
  does not restrict its logits differently by memory substrate;
- the world validates a STEP against one fixed witnessed transition universe
  (`cell.edges`) at `CURRENT`, identical in every arm, rather than against the
  subset of rows a memory service happened to return;
- a syntactically valid but nonexistent/non-current port is terminal failure,
  with no retry or legal-action disclosure;
- a valid STEP returns only the ordinary destination as the new public
  `CURRENT`; it gives no correctness, distance, preferred-branch, route-prefix
  or reward signal;
- malformed, mixed, length-limited, over-budget and post-terminal turns fail
  exactly, with the same LF/raw-byte custody as A3C/A4; and
- six THINKs, eight STEPs and 2,048 generated tokens remain cumulative
  per-task caps, not per-state resets.

If dynamic concrete enumeration is useful diagnostically, name it a separate
`TYPED-CANDIDATE COMPONENT CEILING`. It cannot qualify the native interface
or be used in the headline substrate comparison.

For future automatic text memory, retrieval must likewise remain
target-blind and action-neutral: query all candidate current EVENTs
symmetrically, return all qualifying rows in a presealed neutral order and
never retrieve, rank, suppress or enumerate only the correct candidate. The
same STEP grammar, state response, token/action budget and scorer apply to
native LoRA, LoRA-as-memory-service, automatic text, full text, OFF,
wrong-life and content-twin arms. Memory modality may differ; action help may
not.

## 5. What the existing roster can still establish

Under the corrected symmetric boundary, an `8/8` or `7/8` C0 result would
validly show:

> The fixed 7B actor can use the LF-framed THINK/STEP interface to execute a
> sequence of irreversible typed actions from fully supplied local graph
> information.

Later controlled memory conditions could show that personal or textual
memory supplied enough local information to change those actions. AUTH versus
ATOMS under a fixed retrieval budget might measure whether LINK rows make
local evidence cheaper to surface.

They cannot, on this topology, establish complete-route planning, early
goal-conditioned choice, traversal of a long internal connection, autonomous
retrieval, or broad prospective/action intelligence. EVENT atoms already
contain enough public topology for `LOCAL-1`; LINK is not necessary in the
full-graph condition.

Accordingly, if the cheap physical diagnostic is still valuable, rename it
`PCFL-STEP-INTERFACE-v1`, retain the `7/8` gate only as an **interface** gate,
and prohibit its pass from promoting the 64-task run as a prospective ceiling
or licensing a whole-organism claim. It requires a new explicit ruling because
the prior prospective authorization was withdrawn.

## 6. No existing sealed PCFL material repairs the construct

All registered roots are isomorphic. The eight cube cells change only the
three bits and opaque port identities, not the branch topology. OLD/NEW cuts
remove a required edge and make delayed goals unreachable; they do not create
a balanced decision. `old_left` makes the `H -> G_L` action directly equal to
the goal, and `old_right` starts at `S_R` with only the final fork. They are
easier under the same shallow policies.

The private latent `X -> Z` transition gives `X` a continuation, but it was
never witnessed and has no authentic EVENT/LINK row. Exposing it only in the
ceiling would change the evidence contract and still would not balance the
`H -> G_L` dead branch. It is not a legitimate hidden repair.

Thus no existing sealed root/task roster suffices for a claim-bearing native
STEP prospective test.

The smallest valid future topology must, before any model result:

- give every competing destination at each scored preterminal branch the
  same direct-goal status and the same witnessed outdegree through at least
  depth one;
- require at least one correct choice whose evidence lies two or more linked
  transitions away;
- make at least one paired goal change an early branch, not only the terminal
  edge;
- counterbalance row/action order and path length; and
- pass the full shallow-null battery at `<=4/8` before native inference.

Those are acceptance constraints, not permission to patch the observed
eight-task world. Authoring such a topology now is a benchmark change and
must be prospective. Under the instruction not to broaden this review into a
new benchmark, the correct present disposition is **interface-only or stop**.

## Final ruling

The root pause was correct. Irreversible state-to-state action is not itself a
leak, but this topology turns it into five local transitions whose only three
choices are solved by one-hop viability, one-hop viability, and direct goal
equality. The proposed nulls and arm-asymmetric grammars would have made a
passing model look more prospective than it was.

Freeze no claim-bearing source from `PCFL-NATIVE-STEP-v1`. Either stop it, or
rebind the corrected symmetric version as the explicitly limited
`PCFL-STEP-INTERFACE-v1`. Preserve the existing EVENT writer and sequence
retention work independently; this ruling changes only what the current STEP
roster could prove.
