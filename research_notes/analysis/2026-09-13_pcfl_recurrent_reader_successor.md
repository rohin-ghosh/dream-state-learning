# PCFL recurrent reader successor after the terminal interface ladder

**Date:** 2026-09-13 PT  
**Role:** prospective documentation-only design  
**Scope:** exposed-root interface development; no builder source, model,
tokenizer, adapter, benchmark root, GPU, or remote mutation

## 0. Decision

The next experiment should not be another wording or grammar-choice retry.
The terminal results now isolate three different questions:

1. Can the base construct a five-edge route when the complete exact graph is
   visible and it receives genuine recurrent thinking turns?
2. If not spontaneously, can it execute one generic, answer-free traversal
   procedure?
3. Only after one of those reasoner conditions passes, can the same recurrent
   actor assemble incrementally returned memory into a route when the first
   read is scheduled from public state?

Answer them with one prospective ladder:

```text
A3B-LF exact graph, 8-task smoke
  -> A3B-LF exact graph, 64-task DEV if the smoke passes
  -> otherwise A4-LF generic procedure, but only when A3B's physical turns work
  -> scheduled-first-READ recurrent integration, 8 AUTH tasks
  -> full supplied-memory DEV only if integration passes
```

Every neural response ends physically at the first LF. The returned pre-LF
bytes are fullmatched as exactly one `THINK`, `READ`, or `ROUTE`; nothing is
stripped, extracted, repaired, or rescued. This same LF framing becomes the
common actor transport for Dream--LoRA--Think and
`ACTIVE_TEXT_NATIVE-v2.1-AUTO`.

This is the smallest ladder that distinguishes insufficient deliberation from
graph-algorithm failure and incremental-retrieval integration failure. It does
not teach a route, reveal a useful hidden address, fit an interface adapter, or
weaken the exact route scorer.

## 1. Evidence the successor must respect

| terminal component | result | fixed interpretation |
|---|---:|---|
| `A2_DIRECT`, complete exact graph | `0/64` graph success; 54 strict routes, all only 2--3 ports rather than the required 5 | Answer-direct generation did not compose the route. This is beyond syntax. |
| `A3_THINK`, same complete graph | `64/64` raw outputs began `THINK`, but all contained 2--9 physical lines; `0/64` THINK turns accepted | The model attempted thought, but the transport never gave it a recurrent turn. This does not test deliberation. |
| public prose requiring a READ | `0/8` legal reads | Stronger instructions do not induce retrieval. Stop prose retries. |
| `STRUCTURED_ACTION_SMOKE`, constant `READ-or-ROUTE` choice | 8 calls: `0/8` READ, 7 strict ROUTEs, 1 LENGTH, `0/8` legal or graph-successful | Making READ syntactically available does not make the base choose it. Stop grammar-choice retries. |
| `STRUCTURED_FIRST_READ_SMOKE`, READ-only first slot | 48 calls: 40 model-generated READs (30 non-MISS), 8 strict ROUTEs; 4 legal but incomplete and 4 illegal branch-splices; `0/8` graph success | Service transport and follow-on READ syntax can work after a READ-family schedule; connected use without explicit THINK still does not. |
| one PCFL EVENT-only write | held-wrapper AUTH `14/14`, fresh C0 `0/14`, one life/fit | Atomic own-experience carriage works narrowly. It does not rescue the reader or establish LINK/use. |

The structured-action outcomes were independently checked against the node-2
artifacts while this memo was being written. Both use the same eight exposed
tasks, model, prompt/cell/goal/seed values and 13-call/2,048-token actor cap;
both have zero fits/updates. In the first-READ arm, the generic regex forced
only the READ *kind*, not an address: the model itself emitted
`READ EVENTS_AT <public START>` 8/8, all later READ addresses were already
visible, and every terminal port appeared in a prior service return. THINK was
unavailable. Thus `0/8` is specifically useful evidence that retrieving the
right atomic rows and copying their ports is not the same as constructing a
continuous route. The audit's exact custody memo remains the authority for the
terminal scientific record; this design does not rescore those outputs.

The important consequence is negative and positive at once. Do not tune the
atomic writer again now. Also do not run connected LoRA fits until a clean base
has demonstrated a usable action/readout interface. A writer cannot be judged
through an actor that cannot solve the supplied-information ceiling.

## 2. Common physical one-turn contract

### 2.1 Decode boundary

For every typed actor call in this ladder and every later comparison:

```text
stop strings: ["\n"]
include stop string in returned text: false
per-physical-turn maximum: 256 generated tokens
cumulative generated maximum: 2,048 tokens per task
```

The runtime must preserve and bind:

- the exact returned UTF-8 bytes before LF;
- raw output token IDs and prompt token IDs;
- the finish reason and stop reason;
- whether LF, EOS, or the token cap ended generation;
- exact conversation-prefix bytes and hash; and
- the task/slot seed, model identity, mount, and service return.

LF is a transport boundary, not a parser. The dispatcher may not call
`splitlines`, trim whitespace, select a last line, remove a fence, repair an
identifier, or continue a malformed prefix. EOS is acceptable only when the
entire returned byte string already fullmatches one allowed family. A length
stop without a fullmatch fails that task.

The model remains unconstrained inside one physical line. Do not use a dynamic
grammar that enumerates registered node, event, port, link, or route values;
such an enumeration can disclose the memory inventory. A static lexical
grammar is allowed only if it describes the same opaque-ID alphabet without
enumerating valid instances. Exact semantic validity remains the parser and
world's decision.

### 2.2 Typed families

The only generated actor families are:

```text
THINK <one nonempty sequence containing no CR or LF>
READ EVENT <E_[A-Z2-7]{10}>
READ EVENTS_AT <N_[A-Z2-7]{10}>
READ LINKS_FROM <E_[A-Z2-7]{10}>
ROUTE <N_[A-Z2-7]{10}> <N_[A-Z2-7]{10}> : <P_[A-Z2-7]{10}>(,<P_[A-Z2-7]{10}>)*
```

`READ` is disabled in complete-graph conditions. `ROUTE` is terminal. An exact
`THINK` is appended verbatim as assistant history and receives exactly:

```text
CONTINUE: follow the declared turn budgets and commit the final action when ready.
```

An exact legal READ is appended verbatim and receives only the exact registered
service block or `MISS`. It receives no correctness, relevance, progress,
route, or next-address feedback. A malformed or out-of-visibility READ fails
the task; it is never converted to `MISS` after private lookup.

### 2.3 Visible-address closure

At actor turn `t`, a READ address is legal only when its exact identifier is:

- public `START` or public `GOAL`; or
- present in an exact service block delivered before turn `t`.

The controller records the growing visible-address set but never renders the
set as a candidate list. This prevents the model from probing hidden registered
addresses while preserving natural graph expansion: an `EVENTS_AT` result
reveals EVENT IDs and destination nodes, which may then be read.

The service uses exact address equality. A legal visible address with no row
returns exact `MISS`. Private root names, role names, hidden bits, full address
registries, validator codes, and route truth never enter the transcript.

### 2.4 Seed and arm parity

Derive sampling seeds prospectively from `(root/task identity, actor slot)`;
use the same seed tape for the matched A3B/A4 or AUTH/MISS task. The history
will make later random draws nonidentical in effect, so call this common random
numbers, not identical stochastic output. The scorer, parser, model revision,
chat template, per-turn cap, cumulative cap, and LF settings are byte-identical
across matched conditions.

## 3. A3B-LF: recurrent reasoning over the complete exact graph

### 3.1 Sole delta from terminal A3

`A3B_LF_EXACT_GRAPH` reuses terminal A3's exact public system/user bytes,
tasks, exact witnessed graph, seeds, parser, scorer, temperature, and budgets.
The sole scientific delta is that the backend now stops before the first LF.
No new instruction, example, algorithm, answer, candidate, or memory service
is added.

The instantiated public system text remains:

```text
You operate a deterministic directed route system. Identifiers are opaque and case-sensitive. Use only the public task, supplied memory and conversation. Never invent, rename or repair an identifier. Each response must be exactly one complete typed physical line, without a trailing newline, fence or prose. Commit the final action as ROUTE <start> <goal> : <comma-separated ports>. The complete ROUTE is terminal; there is no route feedback, correction or retry. At most 256 generated tokens per response and 2048 cumulatively are available.
EDGE <source> <port> <destination> is a directed transition.
EVENT <event> AT <source> DID <port> GOT <destination> EVIDENCE <receipt>
records the same directed transition: using <port> at <source> moved to
<destination>. LINK records that two EVENTs were consecutive; it does not
change either EVENT transition.
Local reads are disabled; do not emit READ.
You may output THINK <one nonempty physical line of reasoning>. Use at least one THINK before ROUTE and at most six THINK responses. A THINK receives only a fixed CONTINUE message, not world information. Never combine a THINK and an action in one response.
```

The user bytes are exactly:

```text
MEMORY
EDGE <opaque source> <opaque port> <opaque destination>
... all exact witnessed EDGE rows in the predeclared order ...

ROUTE TASK
START <public start>
GOAL <public goal>
Required final grammar:
ROUTE <start> <goal> : <comma-separated ports>
```

The ellipsis above documents the already-materialized row slot; it is not a
literal runtime ellipsis. The immutable roster must bind every exact expanded
user string and hash before the first call.

### 3.2 Smoke and full DEV

Use the already balanced exposed indices
`0,1,16,17,32,33,48,49`: four exposed roots by two goals. These cases are
development data and can be repeated as optimization cases; they are not new
scientific units or confirmation.

Per task:

```text
at most 6 accepted THINK generations + 1 ROUTE generation
at most 7 neural calls
at most 2,048 generated tokens total
zero READ/service calls and zero returned-memory tokens
```

Eight-task smoke maximum: `8 * 7 = 56` neural calls.

The **physical-turn gate** passes only when:

- at least `7/8` first responses are exact accepted THINK turns;
- at least `7/8` tasks complete a typed history containing THINK and one
  strict terminal ROUTE;
- no mixed response is accepted, no response is repaired, and at most one
  task ends malformed/length/cap; and
- every attempted and uncalled slot is retained in the denominator.

Graph success is scored separately with the unchanged executor.

- If physical turns fail: stop. A4 is not eligible because recurrence still
  has not been tested. Do not add prompt prose or raise the token cap.
- If physical turns pass and graph success is at least `7/8`: run A3B once on
  the complete frozen 64-task exposed panel.
- If physical turns pass but graph success is below `7/8`: A4 is eligible.

The A3B 64-task panel passes only with:

- accepted THINK plus strict terminal ROUTE on at least `60/64` tasks;
- exact graph success on at least `60/64` of those same tasks;
- no accepted mixed/repaired turn; and
- all task, root, cell, and failure denominators retained.

If the smoke passes but the full panel misses graph success, A4 remains the one
permitted answer-free algorithm localization. Do not splice the eight smoke
rows into the 64-task score.

## 4. Conditional A4-LF: one generic answer-free algorithm

A4 is not a prompt sweep. It is eligible only when A3B's physical-turn gate
passes but its graph-success gate fails at smoke or full DEV. It uses the
identical LF frame, exact graph rows, tasks, parser, scorer, caps, model, and
seed tape and adds only this fixed block to the public system message:

```text
GENERIC ROUTE PROCEDURE
Treat every EDGE or EVENT as one directed transition: source --port--> destination.
In THINK turns, maintain a candidate path that begins exactly at START and a table of transitions you have actually seen.
Search for a continuous path whose final destination is GOAL. A next transition is usable only when its source equals the current end of that candidate path.
When a branch cannot reach GOAL, backtrack to an earlier branch. Do not include ports from abandoned branches.
Before committing, verify from the visible rows that every adjacent transition joins exactly and that the ordered ports take START to GOAL.
Then emit the exact ROUTE and no explanation.
```

There is no worked example. The block contains no scored identifier, route
length, first port, candidate path, hidden bit, target address, or answer. It
teaches an algorithm, so an A4-only pass must be labeled execution of a
supplied generic procedure rather than spontaneous traversal-policy discovery.

A4 uses the same 8-task/56-call smoke and, only after `>=7/8` graph success,
one 64-task/448-call DEV panel. Its full gate is the same `>=60/64` joint
THINK+strict+graph success. If A4 misses, stop the 7B PCFL reader path. Do not
fit a route procedure into the LoRA and then call the writer successful; use a
separately named stronger resolver or redesign the readout benchmark.

Maximum exact-graph cost if both candidates are required:

```text
A3B smoke + panel = 56 + 448 = 504 calls
A4  smoke + panel = 56 + 448 = 504 calls
maximum             1,008 calls, zero fits/updates
```

Stopped descendants are not spent.

## 5. Scheduled-first-READ recurrent integration smoke

Run this only after A3B or A4 has passed the full exact-graph `60/64` gate.
Use the first passing reasoner policy: A3B without the procedure if A3B passed,
otherwise A4 with the exact generic block. This prevents retrieval failure
from being diagnosed through a reasoner already known not to solve the graph.

The earlier first-READ cell already established `8/8` transport and
model-generated follow-on READ syntax conditional on an externally constrained
first action family, but `0/8` routes. It made 40 READs: 30 non-MISS and 10
MISS, returning 46 exact EVENT row instances and 2,218 tokens. All eight final
ROUTEs were strict; four were legal but incomplete and four spliced branches
illegally. Do not rerun that handshake. The new information in
`R1_SCHEDULED_READ_RECURRENT` is physical recurrent THINK between delivered
rows and the final action.

### 5.1 Public interaction

The system replaces “reads disabled” with these exact generic bytes:

```text
Local reads are enabled. The only legal READ commands are:
READ EVENT <event_id>
READ EVENTS_AT <node_id>
READ LINKS_FROM <event_id>
READ EVENT returns the matching EVENT. READ EVENTS_AT returns all EVENTs whose AT/source is that node. READ LINKS_FROM returns all LINKs whose first event is that event. The return is exact registered rows or MISS.
Your first generated response is scheduled to be one READ-family action. You must choose its command and address. Read the public START first; never guess an undisclosed address. This externally scheduled action family is not evidence that you autonomously chose to retrieve. It counts toward the twelve-READ limit.
After the first delivered memory result, use at least one THINK before ROUTE. Thereafter choose THINK, one legal READ, or final ROUTE as needed. Use only public START/GOAL and identifiers already returned by memory as READ addresses. Never invent an address.
Use at most six THINK responses. Never combine THINK, READ, or ROUTE in one response.
```

For every task, the first neural generation uses only the same generic static
READ regex as the verified first-READ component:

```text
READ (EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})
```

It constrains only action family and opaque-ID spelling. It does not enumerate
or select any address. The returned bytes must be exactly
`READ EVENTS_AT <public START>`; any other first address/operation fails the
task without a service call. This is not post-output repair: the expected
public-start policy and regex are frozen before output and already passed 8/8
in the predecessor. Log the raw model tokens and label the turn
`MODEL_GENERATED_UNDER_EXTERNAL_READ_FAMILY_SCHEDULE`, never autonomous
retrieval.

After this model-generated request receives its exact block, every later slot
uses one static LF-framed union of generic THINK, READ, and ROUTE families,
without enumerating values. A THINK gets only the fixed CONTINUE. A later READ
is model-generated and visible-address-closed and receives only the exact
service result. No controller chooses a READ address, thought content, or route
token. The prompt requires at least one post-return THINK before ROUTE, but
does not force THINK after every later return. This is the smallest combination
of the two components already isolated: scheduled initial access plus freely
recurrent state construction.

### 5.2 One smoke condition

Use the same eight balanced exposed tasks in one `AUTH_SERVICE` smoke:

- `AUTH_SERVICE`: the scheduled and later legal queries return exact registered
  blocks from the task's supplied bank.

Do not add a MISS/wrong-root arm to this component screen. The next full DEV
already contains NONE/OFF, wrong-root, OLD-only, NEW-only and positive
projections under the selected interface. Duplicating one null here spends
calls without changing the screen's decision. An integration-smoke pass is not
yet evidence of memory dependence; that interpretation waits for those full
nulls.

Per task:

```text
12 generated READ operations maximum
6 generated THINK turns maximum
all READ commands, including the first, are model-generated
1 generated terminal ROUTE
19 neural generations maximum (12 READ + 6 THINK + 1 ROUTE)
2,048 generated tokens maximum
4,096 returned-memory tokens maximum
14,336 input tokens maximum at every call
```

Smoke maximum: `8 * 19 = 152` neural calls, zero fits/updates. Failed
transcripts retain all uncalled slots. This diagnostic is deliberately not
compute-matched to the complete-graph condition; it isolates incremental use.

### 5.3 Noncompensatory pass gate

`R1_SCHEDULED_READ_RECURRENT` passes only if all are true:

1. `AUTH_SERVICE` has `8/8` model-generated exact first
   `READ EVENTS_AT <public START>` requests and source-joined returns.
2. At least `7/8` AUTH tasks accept a THINK immediately after the first
   return.
3. At least `7/8` AUTH tasks issue at least one later actor-chosen, legal,
   non-MISS READ whose address came from public state or an earlier return.
4. At least `7/8` AUTH tasks terminate with a strict, legal, graph-successful
   ROUTE after an accepted THINK and a served follow-on READ.
5. Every successful AUTH route transition is supported by a matching exact
   EVENT row delivered before ROUTE; branch-spliced ports fail even if every
   individual port appeared somewhere in memory.
6. No false/private row is returned, no malformed or mixed output is accepted,
   no parser repair occurs, and no arm loses a task from its denominator.

Report separately: scheduled reads, autonomous legal reads, served non-MISS
reads, post-return THINKs, strict terminals, legal executions, graph successes,
invalid addresses, invalid turns, length/cap stops, calls, generated/returned/
input tokens, device seconds, and all source-row joins.

The two roots/goals represented by eight cases are repeated exposed
development cells, not `n=8`. This is a hard interface screen, not a frequency
claim.

### 5.4 Exact interpretations

- **Exact graph fails A4:** the fixed 7B reasoner/interface has no usable graph
  ceiling. Retrieval and LoRA are not reached.
- **Exact graph passes; scheduled service has no typed THINK or later legal
  READ:** the incremental interaction protocol fails. Do not blame graph
  reasoning or the writer.
- **Exact graph passes; THINK and legal reads pass; routes fail:** the model
  cannot reliably integrate incrementally delivered rows into a continuous
  route under this interface. This is a graph/retrieval integration failure,
  not memory transport or atomic storage failure.
- **AUTH passes:** the bounded supplied service, recurrent thought, and route
  action form a usable component interface. Release the full supplied-memory
  DEV and its mandatory nulls; do not yet infer memory dependence or LoRA
  utility.

There is no second READ-prompt retry, address example, candidate route, larger
budget, parser relaxation, or post-output correction on a miss.

## 6. What runs after an integration pass

An integration pass releases the already-defined full zero-fit supplied-memory
DEV under the selected LF-framed reasoner policy. It does not by itself release
paper confirmation or connected LoRA fitting.

The full DEV must retain the existing noncompensatory useful/null gates:

- complete exact graph, full exact child text, EVENT atoms, exact supplied
  service, and native exact rows each `>=60/64` delayed route success;
- OLD-only and NEW-only each `<=36/64`;
- NONE/OFF and wrong-root each `<=20/64`, with zero usable false rows;
- exact graph CPU truth `64/64`; and
- reachout positive projections `>=30/32` with position/ID/null controls.

All supplied-memory roots remain exposed optimization data. Only after those
gates pass are prompt, frame, model, parser, service, retrieval policy, task
generator, scorer, and reducer bytes frozen for untouched interface roots.

Then execute the full objective in this order:

```text
dynamic child LINK formation
-> two-root S1 / memory-dependent reachout / cumulative S2 retention vertical
-> reusable-structure RS8 attachment
-> strong evolving-text certificate
-> combined independent-root confirmation
-> matched RAW chronology compiler ablation
-> novelty-growing lifetime comparison
```

The EVENT-only `14/14` result is the atomic entry point, not a substitute for
any of these stages.

## 7. Reconciliation with ACTIVE_TEXT_NATIVE-v2.1-AUTO

The scheduled service is a **component ceiling**, not the final strong text
opponent. Autonomous READ selection has failed under prose and constant
structured choice, so the paper must not make text memory weak by requiring
the base to learn a tool policy.

`ACTIVE_TEXT_NATIVE-v2.1-AUTO` should therefore use:

- the same LF stop/exclusion and exact typed THINK/ROUTE parser;
- automatic target-blind retrieval before each of up to 16 nonterminal actor
  opportunities, based only on public task/state and accepted prior THINK;
- no actor-generated RECALL command and no extra actor generation;
- q16/B8192 retrieval inside the common 2,048 generated-token envelope;
- equality-only salted opaque-ID normalization;
- the public witnessed-event graph, never hidden route topology;
- only exact actor-visible public documents and rejection information;
- one common `RAW_PUBLIC` lane/lifecycle across compared on-policy systems;
- explicit lexical MODEL support for RS8 without an affine solver feature;
- exact empty/157/571-block prompt-length and device-time profiling; and
- a max-load certificate before any claimed DLT superiority.

The final on-policy comparison gives DLT and ATN the same `16 nonterminal + 1
terminal` actor-generation opportunities, LF framing, 2,048 generated tokens,
task interface, action scorer, and public raw-memory policy if that lane is
enabled. Returned memory, input tokens, retrieval CPU/RAM, persistent bytes,
and DLT training GPU-hours are reported separately; the systems are not called
compute-matched.

This separation is scientifically useful:

- A3B/A4 asks whether a clean reasoner can solve a complete supplied graph.
- Scheduled-first-READ asks whether exact incremental rows can enter a recurrent
  action loop.
- ATN-v2.1-AUTO asks how well a strong evolving lossless text system performs
  when retrieval-policy elicitation is removed.
- DLT asks whether its own experience, compiled into parameters, changes later
  connected decisions and lifetime learning.

No autonomous retrieval-policy claim is necessary for the paper's core. It
can later be taught and measured as a separate disposition.

## 8. Full-objective claim boundary

This ladder is intentionally a prerequisite, not a reduced paper objective.

A confirmed A3B result can say only that recurrent typed thought supports use
of a complete supplied graph. A4-only must say that a generic traversal
procedure was supplied. A scheduled-service pass can say only that the clean
actor can integrate exact supplied rows through a fixed first retrieval and
child-chosen subsequent reads. None establishes:

- own-experience LINK formation or connected parametric knowledge;
- LoRA traversal or action improvement;
- retention across a second SLEEP;
- predictive reuse or semantic compression;
- superiority to active text;
- increasing-lifetime improvement; or
- parenting or meta-learning.

Those remain mandatory downstream claims, with independent roots as the unit.
At current scale the adapter is about 80.8 MB, so “compression” may mean only
bounded predictive reuse or conditional semantic-code shortening after RS8;
physical-byte compression is prohibited.

## 9. Builder handoff checklist

Before any new model call, Astra should bind in one preparation receipt:

1. exact A3B, A4, service, task, CONTINUE, and LF bytes/hashes;
2. the eight smoke task identities and full 64-task roster fixed before output;
3. tokenizer rendering with `stop=[LF]`, stop exclusion, and EOS/LENGTH cases;
4. fullmatch-only parser tests, including mixed-line, CR, fence, whitespace,
   truncated, post-terminal, and fake-identifier failures;
5. scheduled query equals the exact public START function in every task and
   reads no other field;
6. dynamic visible-address closure and exact source-return joins;
7. AUTH/MISS task, prompt, seed, cap, and scorer parity;
8. same-task joint reducers—never separate marginal THINK and route gates;
9. exact call/token/service maxima and uncalled-slot retention;
10. existing route scorer and terminal result immutability;
11. fresh process/custody/replay/release tests; and
12. cause-specific markers that refuse A4 or full-panel launch unless the
    exact predecessor disposition licenses it.

Implementation belongs to Astra under the builder contract. This memo changes
no builder-owned file and authorizes no execution by the watcher.

## 10. Resource arithmetic

Prospective upper bound before the already-budgeted full supplied-memory DEV:

| component | maximum neural calls | fits / updates |
|---|---:|---:|
| A3B smoke + full panel | 504 | 0 / 0 |
| conditional A4 smoke + full panel | 504 | 0 / 0 |
| scheduled integration, 8 AUTH | 152 | 0 / 0 |
| **worst case** | **1,160** | **0 / 0** |

This is a maximum, not a promised spend: failure stops descendants, and
successful routes may use fewer turns. Measure actual prompt lengths and
device seconds rather than converting call count to an unmeasured GPU-hour
claim. The ladder is cheap relative to one connected writer fit and prevents
hundreds of downstream GPU-hours from being interpreted through a broken
reader.
