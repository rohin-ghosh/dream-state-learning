# Level 1 → Level 2: why stored experience is not yet usable cognition

**Date:** 2026-09-13 PT  
**Role:** Root synthesis of Rohin message 42 against terminal PCFL evidence  
**Scope:** design/interpretation only; no source, model, adapter, benchmark, or GPU mutation

## Bottom line

Rohin's diagnosis is substantially right: the missing boundary is not another
memory-write trick. It is a learned **composition policy** that turns a goal
and current state into a sequence of memory questions, state revisions, and
actions.

The present EVENT adapter was trained on one mapping:

```text
READ EVENT <known opaque address>  ->  reproduce one exact EVENT row
```

The deployment problem asks for a different mapping:

```text
goal + current state
  -> decide what must be recalled
  -> form/select a useful memory cue
  -> interpret the returned relation
  -> update the candidate path/belief
  -> choose another recall, thought, or world action
  -> verify and stop
```

Nothing in next-token training guarantees that learning the first mapping
creates the second. Parametric storage can make a completion available without
teaching the model when to evoke it or how to chain several completions.

## Evidence localization

The current results separate the boundary unusually cleanly:

1. **Atomic content can be written.** SEQ179's one rank-8, 200-update EVENT
   fit produced `14/14` exact cold reads under held wrappers versus `0/14`
   for C0. This is one-life component evidence, not a population claim.
2. **The untrained actor does not initiate the read policy.** A1 and the
   required-READ smoke produced no usable autonomous READ sequence.
3. **When the first action family is externally scheduled, retrieval moves.**
   The structured diagnostic produced 40 child-chosen READ addresses, 30
   non-MISS returns, and 46 exact EVENT-row instances. It still produced
   `0/8` correct graph routes.
4. **Removing memory access as a bottleneck does not solve composition.** With
   the complete exact graph already visible, A3C reached `8/8` typed recurrent
   THINK+ROUTE histories but `0/8` legal routes.
5. **One verbal algorithm is not yet a stable skill.** A4's prospectively
   fixed generic route procedure produced one correct route in eight and
   failed its `7/8` gate. Three thoughts ran to the token cap and four strict
   routes still omitted or spliced edges.
6. **The later 40-update sequential screen is a separate dose failure.** It
   changed all 16 outputs from `MISS` to EVENT-like text but acquired `0/4`
   exact A records at either wrapper, so it supplies no retention denominator.

Thus the strongest current explanation is a two-factor conjunction:

```text
usable learned agent = extractable experiential content
                     × a policy for cueing/composing/acting on that content
```

The first factor has a narrow positive result at the validated dose. The
second factor has a terminal negative result in the zero-shot 7B condition.

## Rohin's MCTS / self-reflection analogy

The useful part of the MCTS analogy is **conditional expansion**. One thought
or memory completion proposes the next state; a metacognitive operation asks
whether that state is adequate, which uncertainty matters next, and which
branch deserves more computation. In that functional sense, self-reflection
acts like a learned index into the model's own skills and memories.

It is not literally MCTS unless the system preserves multiple branches,
scores them, and revisits them. The minimum flywheel does not need the full
tree machinery. It needs a reliable recurrent policy:

```text
STATE -> QUESTION/CUE -> COMPLETION -> UPDATED STATE -> ACTION OR NEXT CUE
```

Branching, parallel thought, and merge can be added after this linear
state-to-state policy is proven. Calling the minimum mechanism “composition
CoT” is accurate; calling it search-tree learning before branches are actually
represented would overclaim.

## Clean bootstrap design

Treat composition as a **lab-given birth skill**, analogous to tool syntax,
not as a semantic repair performed by SLEEP.

Create target-disjoint first-person traces over fresh generic graph families.
Each trace should contain compact, world-verifiable transitions such as:

```text
THINK current state / goal / missing relation
READ or inspect one relevant local memory
THINK what changed, which alternatives remain, and why another step is needed
STEP or commit one action with an expected consequence
OBSERVE the real next state
THINK verify, revise, continue, or stop
```

The corpus may teach:

- separation of node, port, event, and goal identities;
- asking for a relation from the current state rather than a memorized answer;
- preserving a candidate path across recurrent turns;
- comparing branches whose local appearance is matched;
- using outcome disagreement to revise the state;
- concise self-checks and a stopping rule; and
- the common THINK/READ/STEP physical language.

It must not contain PCFL roots, identifiers, target routes, topology-specific
position rules, A2–A4 outputs, or later deployment-gym data. A token-matched
active sham must teach equally fluent but non-compositional traces.

Freeze one inherited child only after it passes untouched generic graph
families. Give that exact inherited child to every later arm: personal LoRA,
no-write, active text, full context, wrong-life, and batch controls. The
inherited policy then answers **how to use information**; the experimental
memory condition answers **which personal information is available**.

Prefer a separately frozen inherited policy/base checkpoint with the personal
LoRA mounted above it. If implementation forces one cumulative adapter, bind
the complete birth corpus and composition order in advance and preserve a
birth-only ablation. Never fit the scored personal EVENT/LINK rows into the
composition bootstrap and call the result self-learning.

## Minimum qualification

Before combining this skill with personal memory, require on untouched,
shortcut-audited graph families:

1. the child independently invokes the state→cue→update loop rather than
   merely copying a forced format;
2. it beats fixed-position, local-degree, goal-equality, and balanced-random
   policies;
3. it succeeds when correct and incorrect branches have matched local depth,
   out-degree, and identifier/token statistics;
4. its selected action changes with the goal and with one causal edge swap;
5. removing the relevant returned memory changes the selected branch;
6. sham-schooling does not create the same effect; and
7. generic instruction/tool canaries remain within the registered adverse
   bound.

Then combine it with authentic Dream/Sleep in an orthogonal 2×2:

| | no personal write | authentic personal write |
|---|---:|---:|
| sham birth | S0 | S1 |
| composition birth | C0 | C1 |

`C0>S0` establishes the inherited composition skill. `C1>C0` and `C1>S1`,
under content cuts/wrong-life/text controls, establish that the skill used
personal experiential memory. Only repeated sleep cycles and later-action
curves can establish the flywheel.

## Current ruling

Do not repair Level 2 by putting a host graph searcher inside the benchmark or
by training PCFL answers into the personal memory adapter. The valid shortcut
is developmental: amortize a general, target-disjoint composition habit at
birth, then let the child's own experiences supply the facts and relations it
walks through.

This is the precise sense in which Rohin's bootstrap can expedite learning:
it moves the child past the cold-start problem of discovering a metacognitive
control loop while preserving the paper's central question—whether later
experience changes what that loop knows and therefore what the agent does.
