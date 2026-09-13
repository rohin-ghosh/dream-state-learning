# PCFL-GOAL-BRAID-v1 source-contract amendment

**Date:** 2026-09-13 PT
**Status:** documentation-only candidate amendment
**Scope:** resolves the nine source-contract conditions in
`2026-09-13_pcfl_goal_braid_addendum_source_audit.md`. It does not authorize
source authoring, materialization, checker or model execution, training, GPU
use, claims, or release.

If adopted, this amendment governs wherever it conflicts with
`2026-09-13_pcfl_goal_braid_topology_successor.md`, including its addendum.
The role-level graph and the verified `1/4` known-label ceiling do not change.

## 1. Roles, identifiers, addresses, and order are independent

`e0`--`e9` and `l0`--`l7` are generator/checker-private semantic role names.
They are never child-visible addresses and never imply chronology.

For every root/cell, preparation must preseal independent, balanced
permutations for:

1. semantic node, port, probe, EVENT, and LINK roles to opaque identifiers;
2. admitted EVENT roles to public EVENT addresses;
3. admitted LINK roles to public LINK addresses;
4. public row serialization;
5. valid OLD source-opportunity order;
6. selected-first versus scheduled-second bridge order; and
7. S1/S2 training-row and view order.

An EVENT's semantic role is determined only after an authenticated receipt
matches its private `(source, port, destination)` tuple. Its already-presealed
public address is then released. A LINK's role is determined from the two
admitted semantic EVENT roles and their shared node; its presealed address is
then released. No counter such as “eighth EVENT written” may determine either
role or address.

Required EVENT/LINK banks, cuts, and admissions compare semantic tuples as
sets. Child order is retained only as private provenance. No semantic slot
index may be hashed directly into a public identifier.

## 2. Authentic OLD and NEW formation sequence

OLD formation consists of eight public, scaffolded source opportunities, not
one continuous route. The child executes each required edge through the
existing strict action:

```text
EXPLORE <source_node_id> <port_id>
```

Each successful action produces an ordinary authenticated `EXPLORE` receipt.
Only that receipt can support the corresponding child-authored EVENT. LINKs
are authored only after both endpoint EVENTs have been admitted. Both start
ports must be executed; their execution order does not assign branch roles.

NEW formation uses the following exact sequence for both branches:

1. The scored reachout task reveals one presealed goal and two equal-form
   probe cards. The child's one valid `PROBE <probe_id>` ends only the
   **selection task**.
2. The PROBE result publicly reveals the realized bridge port. It is not an
   EVENT receipt.
3. In a separate frontier-formation opportunity at the probed `F` node, the
   child executes `EXPLORE <F_node_id> <revealed_port_id>`.
4. The ordinary authenticated EXPLORE receipt supports one child-authored
   bridge EVENT.
5. After its adjacent OLD EVENTs and bridge EVENT are admitted, the child
   authors the two crossing LINKs.
6. A goal-neutral scheduler then instructs the child to issue the other exact
   `PROBE <probe_id>`. That non-scored PROBE returns the ordinary public result,
   after which the branch repeats steps 3--5 with the same public schemas. A
   malformed scheduled PROBE is a formation failure. It is never scored or
   reported as autonomous reachout.

The selected and scheduled bridge EVENT/LINK rows are byte-identical in schema
and provenance wording. Selected/scheduled status exists only in private
custody metadata.

A wrong but valid first PROBE returns its real bridge, scores reachout as
wrong, and continues the same two-branch formation sequence. A malformed,
unknown, repeated, or otherwise invalid PROBE produces no outcome or receipt,
terminates that lineage as a formation failure, and permits no S2 adapter.
There is no host repair, favorable retry, or selection of only successful
children. Failure remains in the denominator. Missing authentic EVENT/LINK
rows may not be backfilled with ideal rows; ideal rows belong only to supplied
ceilings.

## 3. Exact S2 exclusion boundary

For this bounded assay, S2 may consume only:

- authenticated child-authored OLD and NEW EVENT target spans;
- authenticated child-authored LINK target spans; and
- prospectively fixed, target-blind compiler renderings of those same spans.

The following bytes are forbidden from every S2 model-visible input **and**
target, including loss-masked input:

- the scored reachout goal or any `GOAL <id>` instruction;
- probe-card order, selected/scheduled labels, card-position labels, or the
  PROBE transcript;
- selection score, correctness judgment, teacher/evaluator commentary, or
  repair text;
- formation chronology, child-address release order, or “first/second” tags;
- delayed-use prompts, complete routes, route prefixes, and evaluation
  outcomes; and
- future goal-conditioned DREAM, parent, or external-memory text.

Private custody may retain these fields for audit, but the writer receives no
rendering of them. Necessary node/port IDs appearing inside grounded EVENT and
LINK rows remain lawful; the forbidden signal is their designation as a
reachout target or selection result.

## 4. Cell and fork isolation

Every `(root, O, N0, N1)` cell is one independent authentic lineage with its
own S0, S1, S2 corpus, optimizer state, and adapter. Cells sharing a root may
never pool rows, batches, adapter weights, replay state, or optimizer state;
they contain contradictory bindings for the same opaque namespace.

Only the two final goals fork from one byte-identical S2 snapshot. Those forks
are read-only, start with empty active context and empty external state except
for the arm's declared memory surface, never write, and are destroyed after
scoring. Decode schedules are paired prospectively. Wrong-root, cut, and
cross-mount conditions are read-only descendants of a predeclared source
snapshot and never contaminate it.

The root, not its two goals, eight cells, turns, or decode repeats, remains the
unit of independent confirmation inference.

## 5. Grouped cuts and coherent mounts

The inherited singular `e0`/`e8` cuts are superseded.

- **OLD-start cut:** remove both `S -> U0` and `S -> U1` EVENTs and all LINKs
  incident to either. The rendered memory must collide exactly across
  `O=0/1` while the correct first STEP differs.
- **NEW-bridge cut:** remove both `F0 -> R0` and `F1 -> R1` EVENTs and all four
  crossing LINKs. For each goal, the rendered memory must collide exactly
  across its relevant `N` bit while the bridge STEP differs.
- **G0-tail cut:** remove `K0 -> G0` and every incident LINK. **G1-tail cut**
  does the symmetric operation. These are missing-information tests, not by
  themselves directional-use tests.
- **Opposite-O mount:** mount the complete, internally coherent memory from
  the cell with `O` flipped while holding the true task world fixed. The
  registered first STEP must redirect and fail in that world.
- **Opposite-N mount:** flip only the goal-relevant `N` memory cell while
  holding the true world fixed. The registered bridge STEP must redirect and
  fail.

Removal is semantic before rendering: no dangling LINK, blank slot, row-count
label, address hole, or serialization position may reveal the removed role.
Cut renders receive fresh presealed order permutations. OLD/NEW cuts require
exact byte-collision certificates, not merely reduced oracle scores.

## 6. One active READ interface for every compared arm

The experiment chooses the active-reader design. Every delayed-use and
reachout arm receives the same public response grammar, documentation,
budgets, controller order, and strict whole-response parsing:

```text
THINK <one nonempty physical line>
READ EVENT E_[A-Z2-7]{10}
READ EVENTS_AT N_[A-Z2-7]{10}
READ LINKS_FROM E_[A-Z2-7]{10}
STEP P_[A-Z2-7]{10}
PROBE Q_[A-Z2-7]{10}
```

All responses are exact one-line UTF-8 with no CR/LF, extraction, trimming,
repair, or mixed commands. `STEP` is semantically legal only during delayed
traversal; `PROBE` only during reachout selection. A wrong-family action is
terminal failure.

Every arm receives the same limits: at most 6 THINKs, 12 READs, 6 STEPs, one
PROBE, 25 physical generations, 256 generated tokens per turn, 2,048 actor
tokens cumulatively, and 4,096 returned-memory tokens. The sixth THINK,
twelfth READ, and sixth STEP are legal; exceeding a cap fails without forced
commitment. Reaching a goal ends delayed traversal. Host feedback after STEP
contains only the new `CURRENT` node.

For external-store arms, READ semantics are target-blind and exact:

- `READ EVENT` returns the registered EVENT row or `MISS`;
- `READ EVENTS_AT` returns every registered EVENT whose source is the queried
  node, in a presealed target-blind order, or `MISS`;
- `READ LINKS_FROM` returns every registered LINK whose first EVENT is the
  queried EVENT, in presealed order, or `MISS`.

A valid absent external-store query consumes one READ and returns exactly
`MISS`. The service never proposes a query, ranks by goal, reveals registered
addresses, enumerates legal ports, returns only a useful branch, or alters a
response after seeing the task goal.

The exact external-store condition name is `ACTIVE_LINKED_TEXT`; the alias
`ACTIVE_STRUCTURED_TEXT` is retired. Its query registry holds the declared
EVENT/LINK bank. `ACTIVE_EVENT_ONLY_TEXT` holds the same EVENT rows and no
LINK rows.

Native parametric arms do **not** resolve READ against an empty external
registry. A child-issued READ launches one isolated reader call to the exact
same mounted base-plus-adapter state used by that arm's actor:

- LoRA ON reads with that ON adapter;
- OFF reads with the paired base/OFF state;
- wrong-root and cut arms read with their own wrong-root or cut mount; and
- no adapter is stacked, swapped, or selected after the request.

The reader receives only one prospectively frozen reader-system message and
the child's exact opaque READ request. It receives no actor conversation,
goal, current node, route prefix, candidate list, expected row, registry
contents, scorer field, or prior reader output. Reader wrapper, tokenizer,
decode settings, seed schedule, output cap, and response envelope are fixed
and identical across native arms. Each reader call has a 512-output-token cap;
its actual output tokens count against the common 4,096 returned-memory-token
budget. The actor chooses every address; the host never triggers, rewrites,
ranks, broadens, or retries a read.

The native reader's complete raw UTF-8 output is returned to the actor as inert
memory-response content and preserved in custody. It is never interpreted as
an actor command. An exact checker-only registry compares that raw payload
offline with the expected registered block or literal `MISS`; it does not
alter what the actor sees. A malformed, partial, hallucinated, or otherwise
nonmatching reader payload is returned verbatim, consumes one READ, and is
recorded as a fidelity failure. It is **not** replaced by `MISS`, repaired,
completed, or filtered. The actor may continue within its remaining budget.
The payload is the complete next user-message content, without an added
summary or interpretation; command-looking bytes inside that user message are
inert. If appending it would exceed the common returned-token or context cap,
the task fails without truncation, while the raw receipt remains in custody.

For external-text arms only, the non-generative service returns the exact
registered block or literal `MISS` inside the same response envelope. Thus all
arms share the READ opportunity, grammar, turn cost, returned-token accounting,
and actor-visible envelope, while the treatment differs honestly: exact
external lookup versus self-cued reproduction from the arm's own mounted
parametric state.

## 7. Ceiling and learned-memory claim order

Conditions are qualified in this order, with the same child and interface:

1. **Deterministic graph/checker certificate:** graph oracle `64/64`, known-
   label prompt-only route ceiling `16/64`, first/bridge no-memory ceilings
   `32/64`, and all collisions/interventions below.
2. **`EXACT_WITNESSED_GRAPH`:** the complete exact witnessed graph is supplied
   directly as a constructive actor ceiling. READ remains available under the
   common grammar but its registry is empty. Require at least `60/64` strict
   goal reaches and legality `1.0`.
3. **`ACTIVE_LINKED_TEXT`:** the exact authentic-shaped ideal EVENT/LINK bank
   is available only through self-issued READs. Require at least `60/64`
   strict reaches and legality `1.0` before interpreting native LoRA.
4. **`ACTIVE_EVENT_ONLY_TEXT`:** the matched EVENT-only service localizes
   whether LINK rows add read-time value. Its result is diagnostic, not a
   prerequisite for native execution.
5. **Authentic child-text ceilings:** only after successful authentic
   formation, repeat linked/event-only services over the admitted child rows.
6. **Native memory:** only then compare LoRA ON with paired OFF, wrong-root,
   grouped cuts, and coherent opposite-cell mounts.

Before native action scoring, isolated reader calls must establish that the
mounted ON state can reproduce at least `60/64` sampled `READ EVENT` blocks,
`30/32` sampled `READ EVENTS_AT` blocks, and `30/32` sampled
`READ LINKS_FROM` blocks exactly. Run the same frozen requests on OFF,
wrong-root, cut, and cross-mount states to verify the content predicted by each
mount. These calls are non-writing and their outputs are never shown to the
later actor. A failed reader gate localizes failure to parametric carriage or
extraction; subsequent traversal cannot be promoted as a memory-composition
result.

The supplied graph is a constructive ceiling, not an equal-access external-
memory baseline: it prints information the LoRA must recover internally. If
the exact linked-text ceiling fails, native LoRA behavior cannot diagnose
composition. If EVENT-only matches linked text, LINKs were not necessary. If
linked text wins, that establishes read-time LINK utility only; parametric
LINK-added value still requires matched EVENT fidelity and coherent LINK
intervention.

If a common composition bootstrap is needed, its training families must be
target-disjoint and non-isomorphic to the braid. Freeze one inherited child,
mount it identically in every condition, rerun all ceilings and OFF controls,
and preserve the cold failure. The bootstrap is not SLEEP evidence.

Report accepted THINK separately from strict goal reach. Overt THINK is an
interface endpoint, not proof of hidden reasoning.

## 8. Deep redirection and exact claim boundary

Without an additional deep intervention, the strongest permitted delayed-use
claim is:

> With start and learned memory fixed, changing only the distant goal
> redirected the first irreversible action on a task whose solution depended
> on distributed life-specific relations beyond radius three.

Do not claim that behavior alone reveals graph search, traversal of explicit
LINK objects, or the model's internal algorithm. The reachout claim is also
limited to **goal-conditioned suffix-based probe selection**; the present
two-card task does not require integrating OLD prefix memory.

The optional directional mechanism control is a predeclared coherent
tail-swap sibling. Hold `S`, both first edges, prefixes, bridges, opaque
identifier multiset, addresses, serialization, and task wording fixed; swap
only the two terminal goal destinations in both the true world and its
coherent memory. For a fixed displayed goal, the registered first STEP must
flip. A zero-fit paired text subset can establish supplied-memory redirection.
A native claim requires separately compiled, dose-matched authentic sibling
adapters; no after-the-fact memory edit or tail cut substitutes for them.

Only a successful, predeclared coherent tail swap permits wording that the
agent's early action was directionally controlled by distant remembered
content. It still does not identify a unique internal search algorithm.

## 9. Deterministic surface-projection certificate

Before any model call, two independent deterministic implementations must
agree byte-for-byte on roots, cells, semantic routes, rendered banks, cuts,
mounts, query responses, and scores. The certificate must enumerate every
task—not sample it—and report support, label count, collision groups, and
Bayes-best first-STEP, bridge-STEP, and whole-route accuracy for:

- visible goal/current ID and their lexical/ordinal ranks;
- candidate port, node, EVENT, LINK, and PROBE ID ranks;
- public address rank, row position, block adjacency, and row count;
- OLD formation chronology and selected/scheduled bridge chronology;
- probe-card position and reachout-goal side;
- S1/S2 training-row, batch-slot, and view order;
- every singleton above and every pair involving goal rank, current rank,
  address rank, row position, chronology, or card position; and
- rooted structural signatures at radius 0, 1, 2, and 3.

For projections that exclude semantic memory content, first- and bridge-STEP
accuracy must be at most `32/64`, and exact-route accuracy at most `16/64`.
The two successors of `S` must have identical canonical rooted signatures
through radius three; the target goal may first distinguish them at radius
four. Reachout fixed/local/card-position policies must be at most `16/32`.
Grouped cuts must satisfy their exact collision clauses, and coherent mounts
must produce their registered redirections.

These bounds must follow from prospectively balanced blocks. Do not generate,
discard, or rename roots until observed shortcut scores pass. If the declared
four-root layout cannot balance a required projection, increase and preseal
the root cohort before execution rather than waive the check.

## Source-authoring and execution ruling

This amendment closes the nine documentation ambiguities identified by the
audit. If it is independently accepted as binding, the recommendation becomes
**GO for source authoring under this contract**. It remains **NO-GO for
materialization or execution** until the authored source, independent checker,
surface certificate, exact registries, and custody manifests are separately
reviewed and accepted. No scientific claim follows from this amendment.
