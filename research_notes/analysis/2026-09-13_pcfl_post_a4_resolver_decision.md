# PCFL post-A4 resolver decision

**Date:** 2026-09-13 PT

**Role:** independent design/adversarial comparison

**Scope:** documentation only; no source, benchmark, model, tokenizer, adapter,
GPU, process, or claim mutation

## Executive decision

A4 is terminal for the current all-at-once 7B route interface. It produced one
correct route in eight exposed tasks against a predeclared seven-of-eight
gate. Three tasks hit the per-turn token limit and four more completed with an
incorrect path. The result is not only a formatting failure: even the strict
routes commonly omit or splice transitions.

Do not answer this by silently substituting a 32B reasoner, by fitting the
route procedure into the same personal-memory adapter, or by letting a host
DFS construct the answer. Each would make a downstream score easier while
changing what it means.

The best next move for the full Dream--LoRA--Think objective is a separately
named **state-to-state native action readout**:

```text
PCFL-NATIVE-STEP-v1

goal + current public state + ports supported by memory visible in this arm
  -> zero or more typed THINK turns
  -> child chooses exactly one STEP
  -> world executes it and returns the next public state
  -> repeat, with no reset or backtracking, until goal or failure
```

The environment retains state and privately validates a selected action
against world truth. It does not disclose ground-truth legal ports in a
learned-memory condition, search, rank, predict reachability, select a branch,
or construct an answer. The model still makes every branch decision. This
removes the irrelevant burden A3C/A4 exposed--copying and preserving an entire
five-port opaque sequence in one generation--without removing the scientific
burden: choosing the sequence of actions that reaches a future goal from
personal memory.

This is a benchmark/readout redesign, not another A4 wording or grammar retry.
It matches the organism more closely than the old terminal ROUTE string:
THINK is recurrent, an action changes the world, and the resulting state is
the next context. It should be the critical-path successor.

A same-A4 32B run is useful only as an optional cheap capacity localizer. A
generic inherited traversal adapter is scientifically legitimate as the
primary full-objective fallback if the state-to-state readout fails, but only
as a separately controlled schooling factor shared by every main arm. A
mechanical frontier controller is acceptable as a component ceiling only if
it never decides reachability or branch order; the simpler native STEP design
already captures its valid part with less host cognition.

## 1. What A4 actually settles

The observed ladder now separates the seams:

| condition | typed terminal | legal / graph success | disposition |
|---|---:|---:|---|
| A2, whole route directly | 7/8 | 0/8 | no all-at-once supplied-graph ceiling |
| A3B, LF recurrent thought | 4/8 | 0/8 | recurrence physically occurred; motor and semantic failure |
| A3C, static typed grammar | 8/8 | 0/8 | motor syntax fixed; path state still failed |
| A4, supplied generic path procedure | 5/8 | 1/8 | terminal for this 7B all-at-once reader |

The positive EVENT write remains independent: one rank-8 fit cold-reproduced
14/14 address blocks under a held wrapper while C0 reproduced 0/14. That
settles bounded atomic carriage, not connected use. The next endpoint must let
the same model act on carried information without requiring it to serialize a
long artificial command that the real world would ordinarily execute one step
at a time.

No A4 failure licenses:

- a larger per-turn cap on the same exposed condition;
- another route-procedure wording;
- an easier parser or extraction from the three truncated thoughts;
- a route-procedure fit labeled as experiential learning; or
- connected S1/S2 read through the failed all-at-once interface.

## 2. Recommended successor: `PCFL-NATIVE-STEP-v1`

### 2.1 Public interaction

Keep the exact PCFL world, roots, opaque identifiers, transitions, goals,
EVENT/LINK rows, memory conditions, cuts, twins, and source chronology. Change
only how a delayed route is executed.

At every state the public task provides:

```text
ROUTE TASK
START <start>
GOAL <goal>
CURRENT <current>
ARM-VISIBLE MEMORY <exact public rows already available in this condition>
```

The model may emit one exact physical turn from:

```text
THINK <one physical line>
STEP <one port supported by the child's own parametric memory or by an exact
      row already visible in this condition>
```

An accepted THINK receives the same fixed information-free CONTINUE used in
A3C/A4. An accepted STEP is executed by the unchanged world transition table
and returns only the ordinary public next state. The
controller appends the exact selected port to a private score-only action
trace. It never reveals whether the step is on the correct route, how far the
goal is, a better branch, a route prefix, or the hidden world's action set.

In the exact-full-graph ceiling, ports at CURRENT may be derived only from the
EDGE rows already printed in that arm. In an automatic text or parametric
service condition, they may be derived only from authenticated EVENT rows the
service actually returned before that STEP. Structured action syntax may
enumerate those **arm-visible** port IDs because it adds no world fact beyond
the visible row. It may never enumerate a ground-truth port absent from that
arm, a future port, an EVENT/LINK address, a candidate route, or the correct
choice. Counterbalance any printed/enumerated port order. In the direct native
LoRA condition, where no rows are externalized, use only the generic static
port-ID grammar and let the mounted child recall the ID; the host has no basis
for an enumerated choice set. The world privately validates the result. This
keeps action typing from becoming an oracle.

Use the existing LF boundary and exact returned-byte accounting. Preserve the
2,048 generated-token task budget and six-THINK total. Use one fixed public
budget of at most eight STEP actions across every task; do **not** set the cap
to the five-transition answer length. Do not permit reset, undo, backtrack,
branch restart, or a second life. A wrong branch therefore remains
consequential, and the budget discloses no solution depth.

Stop when:

- CURRENT equals GOAL: score the one accumulated action sequence;
- CURRENT has no outgoing public port before GOAL: fail;
- eight STEPs are consumed without reaching GOAL: fail; or
- a malformed/length/cumulative-cap turn occurs: fail.

After termination, the scorer may materialize the equivalent ROUTE bytes from
the accepted STEP trace and pass them to the unchanged `execute_route`/
`score_route`. Those bytes are never shown to the model and never repaired.

### 2.2 Why this remains a prospective test

Intermediate transition results do not give the child a free solution. A
choice is irrevocable within the task. Seeing the destination after a STEP
cannot repair the choice that caused it, and no update occurs during the
evaluation. The child must still select the correct branch at the left start,
at the old/new junction, and at the goal fork. A fixed or random choice policy
therefore remains a real null.

The readout deliberately changes the construct from **write a full plan in one
command** to **execute a multi-step prospective policy without recovery**. It
supports agentic state-to-state traversal if it passes. It does not support
the narrower claim that the model can internally serialize the complete path
before acting.

### 2.3 Smallest zero-fit ceiling

Run one eight-task exposed-root smoke using the exact A3C/A4 roots, cells,
goals, row bytes, and actor seeds. Supply the complete exact witnessed graph
in context, use C0 with no adapter, and change only the STEP interaction.

Maximum per task:

```text
6 THINK + 8 STEP = 14 native calls
2,048 generated tokens
0 fits / 0 updates
```

Maximum smoke: 112 calls. Prospective pass gate:

1. at least 7/8 tasks contain an accepted THINK and reach GOAL through a
   strict legal sequence within the eight-STEP budget;
2. no mixed or repaired turn is accepted;
3. every successful selected port was in the public legal set at that state;
4. both displayed-order views differ by at most one success;
5. at least 3/4 same-root goal pairs both succeed and change the required
   goal-sensitive final choice; and
6. fixed-first, fixed-last, and balanced random policies are printed and none
   exceeds 4/8 on the identical task roster.

The last control is computed from the sealed graph/action rosters before the
model result. It verifies that dynamic legal-action typing did not turn the
endpoint into a position policy.

If the smoke fails, stop this version. Do not tune it on the eight roots. If it
passes, run one 64-task exposed DEV panel requiring at least 60/64 exact goal
success, at least 60/64 accepted THINK histories, legal-action fidelity 1.0,
and the same order/null gates. Only after that should frozen bytes be tested
once on fresh interface-confirmation roots.

Historical A3C timing was about 98 seconds for 25 calls including cold load;
the 112-call smoke should be capped prospectively at **0.25 A40-hours**, and
the 64-task panel at **1.0 A40-hour**. These are hard development caps, not
throughput claims; record actual device time and stop descendants on a miss.

### 2.4 Integration into the mechanism vertical

Use exactly the same STEP/THINK transport for every condition. There are two
different and necessary readouts:

1. **Native organism.** Mount the personal LoRA in the acting 7B child. Give
   it only the ordinary goal and current public state; do not expose
   ground-truth port availability. Under the generic port-ID grammar it
   chooses each STEP from learned memory. This is the claim-bearing
   Dream--LoRA--Think endpoint.
2. **Memory-service isolate.** Query the adapter goal-blindly for exact local
   rows at CURRENT (and the previous EVENT where LINK adjacency is requested),
   place only returned rows in the clean 7B actor's context, permit only ports
   present in those returned rows, and use the same STEP interface. This
   localizes carriage from actor behavior; by itself it is a parametric memory
   service, not the organism.

The strong active-text condition receives the exact same automatic,
target-blind current-node requests, returned-token budget, state messages,
and STEP interface as the memory-service isolate. It receives no hidden legal
action inventory. Full child text and exact graph remain ceilings. OFF,
wrong-life, EVENT twin, LINK permutation, OLD/NEW cuts, and raw chronology
remain causal controls.

LINK value is not built into the controller. If EVENT atoms alone let the
actor choose the route, report event composition. Credit LINK organization
only if AUTH beats ATOMS under the fixed budget and redirects under
permutation/cut. The host may validate and display a LINK row; it may not use
LINK privately to select which STEP is offered or preferred.

## 3. Option A: stronger clean resolver

There are two materially different versions.

### A1. 32B as a component ceiling

Run Qwen2.5-32B-Instruct under the exact frozen A4 prompt, graph, static
grammar, tasks, seeds, and caps. Require at least 7/8 joint
THINK+strict+legal+graph successes. Stop at eight tasks. Cap at **0.5
A100-hours** including load and cleanup.

This is a useful localization: a pass would say the same supplied graph and
procedure are usable at greater model scale; a failure would say the surface
is difficult even there. It is not a final child result and it does not repair
the 7B reader. The prior Semantic World evidence makes a pass plausible only
under careful factoring: 32B improved atomic branches dramatically but its
monolithic recurrent condition still failed.

### A2. 32B as the permanent resolver or child

Using clean 32B to compose rows emitted by a 7B memory adapter is fair if every
arm uses the same resolver, but it supports only a **modular parametric-memory
relay**. The model whose weights contain the life is not the model making the
plan. It therefore cannot headline a claim that the learned child thinks
better.

Switching the entire child and LoRA writer to 32B restores integration but is
a new architecture and calibration program, not a resolver patch. It changes
the frozen base invariant, adapter size, optimizer behavior, fit cost, writer
yield, parenting lineage, and every prior 7B safety result. A rough fourfold
parameter-compute multiplier turns the planned 60-fit M development and
confirmation path into roughly 30--60 aggregate A100-hours before inference,
using the repository's 7.5--15 A40-minute/fit anchor only as a scale estimate.
This is feasible on the leased A100 fleet but high-risk for the submission
calendar and requires a separately ratified system.

**Ruling:** optional A1 diagnostic only; reject A2 from the current critical
path.

## 4. Option B: mechanized route-state/frontier controller

A generic controller may lawfully:

- retain the exact public current node, chosen edge stack, and visited set;
- show public outgoing witnessed edges;
- execute a model-selected legal edge;
- undo an edge when the model explicitly requests BACKTRACK; and
- verify an eventually committed path against public rows.

It may not compute reachability, select a frontier, order candidates by
distance to GOAL, automatically backtrack, exhaustively search until success,
or construct the final path independently of model choices. Any of those
operations moves the graph algorithm into the host. Under a generous enough
budget, a host-maintained exhaustive DFS would make almost any legal-choice
policy pass and would support only “the adapter supplied rows to a task-native
planner.”

The smallest fair B smoke is the same eight exact-graph tasks, with the model
choosing every `FOLLOW <event>` / `BACKTRACK` / `COMMIT`, paired against fixed
order and random-choice policies and capped at **0.25 A40-hours**. A 7/8 pass
would establish bounded tool-mediated search, not internal route planning.

The recommended native STEP endpoint is the strict, simpler form of B: the
world retains only actual state, not hypothetical branches; actions are
irrevocable, and the model owns every consequential choice. It therefore has
less host cognition and a cleaner full-objective interpretation.

## 5. Option C: inherited/post-trained traversal procedure

This is scientifically legitimate only as schooling, never as a rescue of the
EVENT writer or evidence that personal experience taught traversal.

The smallest clean test needs:

```text
                       no personal write    authentic personal write
generic route schooling       I0                      I1
token-matched sham            S0                      S1
```

The schooling corpus must be generated from disjoint generic graph motifs and
identifier namespaces before any scored roots are opened. It may teach typed
THINK/STEP/READ syntax, current-state tracking, branch comparison, and stopping
rules, but may contain no PCFL topology, route length, role ordering, actual
identifier, task answer, memory row, or target distribution statistic. The
sham matches examples, target tokens, updates, heat, rank, and response mask
while teaching equally active non-route text.

For a development localizer, use three fit seeds for route schooling and
three for sham, then test parent-absent on unseen generic motifs and the frozen
PCFL ceiling. At the historical 7.5--15 A40-minutes per 200-update fit, six
fits cost roughly **0.75--1.5 aggregate A40-hours**; impose a 3 A40-hour hard
cap including inference.

If route schooling is adopted, every DLT, frozen, active-text, raw, and batch
arm must start from the same qualified inherited skill. Personal-memory
effects then require adapter OFF/wrong-life/content twins on top of that common
birth. The cleanest implementation is a separately frozen common skill layer
or a prospectively fixed cumulative corpus; selecting whichever composition
works after seeing PCFL scores would invalidate the contrast.

A pass supports “a target-blind inherited traversal skill enables the memory
assay.” It does not support parenting, self-discovery, metacognitive growth, or
learning the procedure from personal experience. Because it introduces
adapter-composition and task-specific-schooling confounds before the carrier
vertical exists, it should not be the immediate successor.

## 6. Adversarial comparison

| option | preserves fixed 7B child | keeps cognition in learned child | smallest cost | strongest valid statement | fatal limitation |
|---|---:|---:|---:|---|---|
| A1: clean 32B resolver ceiling | memory child only | no | <=0.5 A100-h | scale-localized supplied-graph ceiling | not an integrated learned agent |
| A2: switch whole child to 32B | no | yes | 30--60 A100-h for planned 60-fit path, rough | integrated 32B organism if rebuilt and confirmed | resets writer/lineage/calibration and clock |
| B: host frontier + 7B choices | yes | partly | <=0.25 A40-h smoke | bounded tool-mediated search | controller easily becomes the actual planner |
| C: inherited route skill | yes | yes | ~0.75--1.5 A40-h for six DEV fits | target-blind schooling installed a skill | task-specific post-training; adapter composition confound |
| **D: irrevocable native STEP** | **yes** | **yes** | **<=0.25 A40-h smoke** | **state-to-state prospective action from personal memory** | does not prove one-shot full-route serialization |

Option D is the only **zero-fit** path that simultaneously retains the fixed
child, keeps branch decisions neural, avoids training on the answer procedure,
uses the same action interface for parametric and text memory, and directly
resembles the project's THINK -> world action -> new state loop.

### Reconciliation with the independent A4 branch ruling

The independent A4 auditor is right on its central criterion: a host-maintained
DFS is component evidence only, whereas a target-disjoint inherited procedure
can ultimately leave traversal inside the learned child. The disagreement is
only about whether those are the only two valid choices.

`PCFL-NATIVE-STEP-v1` is not the mechanized controller in option B. The host
does not maintain hypothetical branches or search the graph. It retains only
the real world state after an irreversible model-selected action--the same
thing any interactive environment does. Therefore a pass leaves traversal in
the child and makes inherited route schooling unnecessary for this assay. A
failure restores the auditor's ordering exactly: mechanized route-state for
writer/retention components, inherited target-disjoint procedure training for
the integrated child. This conditional order gets the highest-information
zero-fit answer first without weakening the learned-child criterion.

## 7. Exact recommendation and stop rules

1. Preserve A4 as a failed terminal result. Do not alter its cap, prompt,
   grammar, or score.
2. Prospectively bind the eight-task `PCFL-NATIVE-STEP-v1` exact-graph smoke,
   its public-state action protocol, order/null policies, 7/8 gate, and 0.25
   A40-hour cap.
3. If it passes, run the frozen 64-task DEV and then a fresh confirmation
   ceiling. Replace the route endpoint with STEP symmetrically in DLT,
   active-text, full-text, raw, OFF, wrong-life, and batch conditions.
4. If it fails, do not add backtracking or another prompt. Run A1 only if the
   scale localization is worth its small cost. Then adopt the two-track
   fallback: B as a component assay for writer/retention and C as the primary
   route back to the integrated objective. The inherited skill must be learned
   from target-disjoint graph families and shared by every arm; it is not a
   fit of PCFL's exposed answer.
5. Whether C later passes or fails, it may never retroactively qualify A4 or
   the atomic EVENT result. If C also fails on untouched generic families,
   move the paper's claim-bearing endpoint to a different validated agent gym
   rather than continuing to train PCFL-specific solutions.

### What a positive D result would and would not support

With the later AUTH/OFF/wrong-life/twin/cut/text controls, it can support:

> A fixed 7B learning agent used personal parametric experience to choose a
> sequence of irreversible, goal-directed world actions under the same
> state/action interface as a strong text-memory agent.

It still would not by itself show autonomous retrieval, spontaneous formation
of a traversal algorithm, physical compression, cross-topology
generalization, lifetime improvement, or superiority over active text. Those
claims remain gated by dynamic LINK formation, two-write retention,
reusable-structure, and powered lifetime experiments.

This redesign does not weaken the writer claim. It gives the already-positive
atomic carrier a valid agentic action endpoint and keeps the remaining hard
question where it belongs: whether the child's own connected experience
changes consequential choices, not whether it can copy five long opaque
identifiers into one line.
