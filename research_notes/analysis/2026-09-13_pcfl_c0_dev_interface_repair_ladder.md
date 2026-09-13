# PCFL C0: minimum DEV interface-repair ladder

**Date:** 2026-09-13  
**Role:** independent design-only audit  
**Scope:** prompts, typed turn protocol, prospective DEV gates, and claim
boundaries only. No model/tokenizer/GPU/test/fit/update/parent execution and no
edit to Astra-owned runtime or tests.

## Decision

Do not interpret SEQ-167 as a memory or learning failure. Preserve it exactly
as an engineering-only failed-finalization capture and build one small,
prospective `C0-IFACE-DEV-R1` ladder before any route result is used to judge a
writer.

The minimum design-faithful repair is:

1. disclose the three exact READ commands and what each returns;
2. represent THINK as its own bounded turn, retained in conversation but
   receiving only a fixed, information-free continuation;
3. continue to submit the **entire final ROUTE line** to the unchanged exact
   parser and graph scorer; and
4. add a generic traversal recipe only if disclosed grammar plus explicit
   thinking still does not clear the clean-base ceiling.

This is an interface repair, not easier route truth. It adds no goal-specific
candidate, path, length, first step, hidden bit, score, correction, or retry.

## Why a successor is necessary

The fixed SEQ-167 audit at commit `b0eab6b3` classifies all 320 delayed
supplied-memory positives:

| observable result | count |
|---|---:|
| illegal READ grammar | 64/320 |
| opaque-ID surface error | 86/320 |
| all IDs valid but route disconnected | 170/320 |
| permissively correct answer hidden by punctuation | 0/320 |
| legal route to the wrong endpoint | 0/320 |

All 64 active-memory outputs were exactly two lines, `READ <START>` then
`READ <GOAL>`. None was a legal service request and zero memory rows were
returned. The public prompt never revealed that the only legal calls are
`READ EVENT <E_id>`, `READ EVENTS_AT <N_id>`, and
`READ LINKS_FROM <E_id>`.

The 256 direct positive outputs were terse, not truncated, and not prose.
Among them, 142 were already exact ROUTE syntax but disconnected. On the exact
graph, the model often selected both mutually exclusive first-hop ports and a
salient final port; it selected the required intermediate `b`, `q`, and `d`
roles in 0/64 outputs. This is real five-hop composition failure under the
implemented answer-only interface.

That interface contradicts the frozen synthesis. Section 9 promises that the
actor "may generate up to 2048 thought tokens and then commit exactly one
ROUTE." The implementation instead demands a single ROUTE response and
fullmatches the complete generation. Any visible thought makes the answer
invalid. A decode allowance is not a thought loop.

Reachout is separately confounded. Its two views change wording and order, and
the negative controls are 16/16 on RA and 0/16 on RB. The aggregate 16/32
passes only because the model follows presentation position. The repaired
reachout surface must use one template and swap only two byte-matched candidate
lines.

## Invariants: what must not change

Keep all of the following fixed:

- the directed world topology, opaque namespaces, public memory rows,
  START/GOAL pairs, relevant/distractor meanings, cuts, and route truth;
- Qwen2.5-7B-Instruct C0, temperature 0, and the existing per-task cumulative
  allowance of 2,048 actor tokens plus 4,096 returned-memory tokens;
- the current `parse_route` fullmatch, `execute_route`, and `score_route`;
- exact `PROBE <Q_id>` scoring for reachout;
- at most 12 READs, no route feedback, no repair response, and no retry;
- every malformed, missing, multiple, or post-terminal command as a failure;
- the immutable SEQ-167 prompts, outputs, scorer results, and finalization
  status. Never rescore or relabel them with the new protocol; and
- zero fits, zero updates, zero adapters, and zero parents throughout this
  interface ladder.

The repaired interface is used identically for clean C0, supplied-memory
ceilings, later external-memory baselines, and mounted learners. It may not
make the baseline easier than the learner.

## The repaired public contract

### Record semantics

The public instructions should say, generically:

```text
EDGE <source> <port> <destination> is a directed transition.
EVENT <event> AT <source> DID <port> GOT <destination> EVIDENCE <receipt>
records the same directed transition: using <port> at <source> moved to
<destination>. LINK records that two EVENTs were consecutive; it does not
change either EVENT transition.
```

This defines the existing row language. It does not identify a scored edge.

### Exact memory API

When local reads are enabled, disclose all and only:

```text
READ EVENT <event_id>
READ EVENTS_AT <node_id>
READ LINKS_FROM <event_id>
```

Also disclose the fixed meanings already implemented by the service:

- `READ EVENT` returns the one matching EVENT;
- `READ EVENTS_AT` returns all EVENTs whose source/`AT` is that node;
- `READ LINKS_FROM` returns all LINKs whose first event is that event; and
- the response is exact registered rows or `MISS`.

Say explicitly: one READ per response. Do not list registered addresses,
candidate queries, returned rows, adjacency size, or the task's useful read.

### Typed THINK turns

Every model response is one complete typed turn, not a mixed scratchpad/action
blob. The permitted response families are:

```text
THINK <one nonempty physical line of free reasoning>
READ EVENT <event_id>                         # only when reads are enabled
READ EVENTS_AT <node_id>                      # only when reads are enabled
READ LINKS_FROM <event_id>                    # only when reads are enabled
ROUTE <start> <goal> : <comma-separated ports>
PROBE <probe_id>                              # reachout tasks only
```

Dispatch must fullmatch the **whole raw response** against exactly one family.
There is no last-line extraction, whitespace repair, code-fence removal,
ordinal-to-ID conversion, or semantic rescue.

After a valid THINK, append that exact assistant response to history and add
only this fixed user message:

```text
CONTINUE: think again, issue one permitted READ if reads are enabled, or
commit the final action.
```

This response contains no task/world information. A valid READ gets only the
existing exact service return. A ROUTE or PROBE is terminal and receives no
feedback. Preserve and hash every raw turn and its exact conversation prefix.

Limits are prospective and common across arms:

- at most 6 THINK responses;
- at most 12 READ responses;
- at most 19 physical generations for an active route task
  (`6 THINK + 12 READ + 1 ROUTE`);
- at most 7 for a non-read route/reachout task (`6 THINK + 1 action`);
- at most 256 generated tokens in one turn and 2,048 actor-generated tokens
  cumulatively; and
- the unchanged 4,096 returned-memory-token cap.

If a cap is reached without an exact terminal action, the task fails. Do not
force, extract, or ask for a final answer after exhaustion.

### Optional generic traversal scaffold

Do **not** include this at the first thinker rung. Pre-freeze it as the only
allowed escalation if the thinker rung fails:

```text
Set CURRENT to START and PORTS to empty. Find a recorded transition whose
source is CURRENT. Append that transition's port and set CURRENT to its
destination. Repeat until CURRENT equals GOAL. If several transitions leave
CURRENT, follow a branch that can ultimately reach GOAL. Never append a port
from a transition whose source is not CURRENT. With local reads, query the
current node as needed. Then commit the exact ROUTE.
```

It may include one two-edge worked example made from grammar-valid neutral L8
IDs that occur in no world, task, memory bank, query table, tokenizer choice
pool, or final root. The example must demonstrate only the generic algorithm.
It must not match the scored five-hop topology or expose a scored identifier.

Passing only with this block means the assay measures execution of a supplied
traversal algorithm. It does **not** demonstrate spontaneous traversal-policy
formation.

### Reachout surface

Use one exact template for both views and exchange only the two candidate
lines:

```text
PROBE TASK
START <start_id>
GOAL <goal_id>
CANDIDATE PROBE <probe_id> TESTS <source_id> TO <destination_id>
CANDIDATE PROBE <probe_id> TESTS <source_id> TO <destination_id>
Choose the experiment testing a missing transition that could connect the
START-reachable part of the graph toward GOAL. Copy its Q_ identifier.
Commit exactly: PROBE <probe_id>
Never output a choice number, node ID, or event ID.
```

Candidate line byte/token lengths must be matched within each pair before any
model call. The candidate identities and positions remain balanced. This
defines usefulness without identifying the correct candidate.

## Prospective DEV ladder

All rungs use the four already exposed `excluded/0..3` roots. These roots are
optimization data now; that is acceptable for prompt development and must be
stated. No result on them is confirmation.

| rung | changed from prior rung | tasks | max calls | purpose |
|---|---|---:|---:|---|
| `A0_ARCHIVED` | none; immutable SEQ-167 | 0 new | 0 | debugging reference only, not usable evidence |
| `A1_READ_DISCLOSED` | disclose exact API/row semantics; THINK unavailable | 64 delayed ACTIVE tasks | 832 | isolate whether the model can now speak/use the READ interface |
| `A2_DIRECT` | exact graph in context; same semantic contract; no THINK | 64 delayed EXACT tasks | 64 | answer-direct traversal canary |
| `A3_THINK` | require at least one typed THINK before ROUTE | same 64 delayed EXACT tasks | 448 | isolate the missing iterative thought channel |
| `A4_SCAFFOLD` | add only the generic algorithm + neutral example | same 64 delayed EXACT tasks | 448 | conditional localization of traversal-policy knowledge |

`A4` runs only if `A3` fails. This is a ladder, not a four-way best-of prompt
sweep. `A2` is diagnostic only; the Dream--LoRA--Think endpoint cannot be
qualified by falling back to answer-direct execution.

Predeclared rung gates:

- `A1`: zero malformed/multiple READ outputs; at least 60/64 tasks issue at
  least one served registered READ. Route success is reported but is not the
  API-handshake gate.
- `A2`: report strict syntax, legal path, and graph success separately;
  60/64 graph success is the answer-direct ceiling.
- `A3`: at least one exact THINK in at least 60/64 tasks, zero accepted mixed
  thought/action responses, and at least 60/64 exact graph success.
- `A4` (if reached): the same gates as A3.

Interpretation is fixed:

- A2 and A3 pass: traversal was already available; explicit THINK is
  compatible but not necessary here.
- A2 fails and A3 passes: the answer-only interface suppressed usable
  iterative state tracking.
- A3 fails and A4 passes: the base can execute a disclosed algorithm but did
  not formulate it reliably from the task alone.
- A4 fails: stop. This world/interface has no 7B supplied-memory ceiling; do
  not fit a route learner, relax the scorer, add route candidates, or tune on
  confirmation roots.

Select the first passing THINK-capable rung: A3, otherwise A4. Freeze its
system text, turn grammars, neutral continuation, caps, chat template,
rendering, and hashes before any remaining panel is run.

## Development qualification after rung selection

On the same exposed roots, run the selected interface once over the remaining
registered C0 panels. Preserve the original denominators and thresholds:

### Delayed, 64 tasks per projection

- positive `EXACT_WITNESSED_GRAPH`, `FULL_CHILD_TEXT`,
  `EVENT_ATOMS_TEXT`, `ACTIVE_LINKED_TEXT`, and `NATIVE_CONTEXT`:
  each at least 60/64 exact graph success;
- `OLD_ONLY_TEXT` and `NEW_ONLY_TEXT`: each at most 36/64;
- `NONE_OFF` and `WRONG_ROOT`: each at most 20/64; and
- `WRONG_ROOT`: zero usable false rows.

Do not count `FULL_CHILD_TEXT` and `NATIVE_CONTEXT` as independent evidence:
their SEQ-167 prompts/seeds were identical 64/64. They remain separate
compatibility labels only if the successor preserves that duplication.
`RAW_EPISODIC` may remain a no-threshold diagnostic and is not needed to
select the interface.

For active positive tasks additionally require zero invalid READs, at least
60/64 tasks with a served read, and 100% exact return-to-source receipt joins.

### Reachout, 32 tasks per projection

- positive exact graph, full text, and active text: each at least 30/32 exact
  relevant-Q actions;
- in each positive projection, RA and RB separately at least 14/16;
- `NONE_OFF` and `WRONG_ROOT`: each at most 18/32;
- within either negative arm, absolute RA-versus-RB success difference at
  most 4/16 and first-position choice between 12/32 and 20/32; and
- zero ordinal, node-ID, event-ID, malformed, or usable-false-row outputs.

The per-view and first-position gates prevent another 16/0 position policy
from hiding inside a passing aggregate.

If any mandatory panel fails, stop this interface version. Raw DEV inspection
may motivate a separately named successor, but no failed panel can be rescued
by changing a parser, threshold, prompt, or task after seeing it.

## Outcome-blind confirmation and final-root firewall

SEQ-167 exposed all four current excluded roots. Do not use a repaired score
on those roots as confirmation.

After one interface passes all development gates:

1. freeze every interface and reducer byte;
2. deterministically materialize **four new interface-confirmation roots**
   under a namespace disjoint from `excluded/*`, `disposable/*`, `dev/*`, and
   every future confirmation/lifetime namespace;
3. verify opaque-ID and tokenizer inventories without model calls;
4. run the frozen selected interface and the same required positive/negative
   panels exactly once;
5. expose only aggregate gate results until the pass/fail disposition is
   immutable; and
6. permanently exclude these roots, prompts, rows, adapters (none should
   exist), and descendants from formation, writer, parenting, lifetime, and
   paper-test pools.

Apply the same 64/32 thresholds because there are again four roots. No prompt
selection or retry is allowed on this set. A confirmation failure burns all
four roots and invalidates R1; it does not authorize a local repair.

The current `dev/0` and `dev/1` roots therefore remain untouched for the
already designed two-root mechanism DEV. More importantly, future paper-test
roots are neither generated from observed output nor exposed during interface
selection.

## Exact accounting and information/GPU-hour

The discovery ladder has at most 1,792 physical calls:

- A1: `64 x 13 = 832`;
- A2: `64 x 1 = 64`;
- A3: `64 x 7 = 448`; and
- conditional A4: `64 x 7 = 448`.

The maxima are deliberately loose. Valid READs and ROUTEs are short, and a
successful thinker should normally finish well below the 2,048-token cap.
Stop A4 entirely if A3 passes. Stop all later panels if the selected exact
graph rung fails.

The remaining development and one fresh confirmation use only C0 inference,
no fit. They should be executed as a single cold-load session per stage with
fixed task order, rather than one load per arm. Preserve per-task calls and
turns, but do not spend GPU on RAW_EPISODIC or redundant exploratory panels
until the mandatory gates are known.

This sequence maximizes information per GPU-hour:

1. API handshake first (cheaply falsifies the confirmed READ repair);
2. exact graph next (isolates route construction before row parsing/retrieval);
3. typed THINK versus answer-direct on identical tasks;
4. generic algorithm only if needed;
5. full rows and active retrieval only after traversal works;
6. reachout only after delayed use works; and
7. untouched confirmation only after every DEV gate passes.

## What a pass and a failure mean

A confirmed A3 pass permits only:

> Under a frozen typed THINK/action protocol, the clean 7B base can consume
> sufficient supplied route memory, use the disclosed local READ API, and
> commit exact candidate-free routes and relevant experiments.

A confirmed A4 pass must instead say **under a supplied generic traversal
procedure**.

Neither licenses a statement about LoRA storage, own-experience formation,
retention, compression, retrieval superiority, continual learning, parenting,
or lifetime improvement. `ACTIVE_LINKED_TEXT` remains a supplied-memory
service ceiling, not the strong evolving external-memory baseline.

A failure after A4 is still valuable: it localizes the bottleneck above the
writer and says this PCFL surface is not a valid 7B reader/action assay. The
honest next move would be either a larger resolver or a separately declared
mechanical/structured traversal ceiling—not training a LoRA and hoping it
repairs an invalid readout.

## Required builder handoff

Astra should own implementation and runtime tests. Before any model call, the
builder should freeze:

- exact prompt/template bytes and their hashes for A1--A4 and reachout;
- whole-response fullmatch parsers for THINK/READ/ROUTE/PROBE;
- the fixed neutral CONTINUE response and all turn/cumulative caps;
- a CPU transcript proving THINK adds no world information and only READ can
  return memory;
- unchanged route/probe scorer hashes and old SEQ-167 immutability;
- task/root split and a final-root disjointness receipt;
- exact call-slot maxima and fail-closed lifecycle repair; and
- a reducer that reports syntax, legality, graph success, served reads,
  thought count, per-view reachout, first-position rate, and every stop reason
  without score repair.

This is ordinary DEV interface work under the current builder authorization.
It should remain separate from the scoped own-write acquisition run: the
own-write run asks whether exact child rows can be stored and cold-read; this
ladder asks whether the acting model can traverse supplied rows at all.
