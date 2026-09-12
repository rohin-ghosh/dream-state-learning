# Smallest post-H1 connected-knowledge, traversal, and expansion module

Date: 2026-09-12 UTC  
Role: independent design recommendation  
Status: memo only. This does not replace M-core v8, change the benchmark,
authorize source authoring, alter a child, or launch a model/GPU job.

## Verdict

After H1, use one small opaque routing world with four ordered questions:

1. **Rote:** can the child reproduce one transition it personally witnessed?
2. **Compose/traverse:** can it combine separately witnessed transitions into
   two different routes when the goal changes?
3. **Expand:** can old memory tell it which one of several equally uncertain
   experiments closes the current goal's missing edge?
4. **Reuse:** after one SLEEP and a sterile reset, can it solve a different
   delayed goal that requires both old edges and the newly witnessed edge?

Call this module **PCFL-R3** (retrieve, route, reach out). It extracts the
paper-critical core of the much larger M-core specification. M-core v8 remains
the exact governance/falsification map; PCFL-R3 is the minimum scientific
surface worth implementing only after the conditional writer and H1 pass.

Use one H1-qualified, parent-deleted adult checkpoint. Every benchmark visit
is a disposable outward clone. The clean parenting lineage never receives a
PCFL root, score, outcome, selected prompt, or resulting adapter.

Compare three native memory systems from the same adult and public experience:

- **Dream--LoRA--Think (`DLT`)**: the unified child LoRA is the only persistent
  lifetime memory;
- **`ACTIVE_STRUCTURED_TEXT`**: frozen weights, lossless events plus the same
  admitted child-authored DREAM records, with a frozen typed/graph retriever;
- **`WITNESSED_GRAPH`**: frozen weights and an exact graph containing only
  transitions actually observed through public actions.

Also include `NONE/OFF` and raw episodic retrieval as diagnostic floors. DLT
does not have to beat the exact graph for a mechanism result. If structured
text or the graph wins, report it; the benchmark has still done its job.

Drop physical **compression** from this module. A current rank-8 adapter is
about 80.79 MB while one PCFL-R3 root's complete text/graph state is tiny. This
module can establish compilation, connection, traversal, and expansion, not a
positive rate--distortion crossover.

## 1. World and action interface

### Opaque routing world

Every pair-root contains two counterfactual twins. Handles are newly sampled,
token-balanced nonces. The twins are byte-identical until the one informative
experiment returns an outcome.

The hidden world is a deterministic labeled directed graph. A compact root has:

- two public starts, `s` and `s2`;
- two branch pairs, `u0 -> v0` and `u1 -> v1`;
- two frontier destinations, `w0` and `w1`;
- two delayed targets, `g0` and `g1`;
- type-matched distractor nodes and ports; and
- opaque port/action labels whose marginal frequencies are exactly balanced.

The old graph contains two independently witnessed upstream routes:

```text
s  --a0--> u0 --b0--> v0
s  --a1--> u1 --b1--> v1
s2 --a2--> u0
s2 --a3--> u1
w0 --d0--> g0
w1 --d1--> g1
```

The missing relations are frontier edges `v0 -> w0` and `v1 -> w1`. At each
frontier there are two opaque testable ports. In a twin pair, the relevant
port-to-destination binding is swapped while all pre-outcome public bytes,
menus, priors, lengths, and old experiences remain fixed.

The actor has only two world operations:

```text
TEST <node> <port>
ROUTE <start> <goal> : <port_1>,<port_2>,...
```

`TEST` produces one ordinary public transition outcome. `ROUTE` executes the
listed ports from the stated start; the environment, not an LLM judge, returns
success and the realized path. Invalid, missing, or over-budget actions score
zero. Candidate order is presealed and independently randomized.

### Why this geometry separates the abilities

- A one-edge question can be answered by rote event retrieval.
- A route from `s` to `v0` or `v1` requires two old transitions that were
  experienced in separate source episodes; no source row contains the route.
- The two same-start goals require different first ports and paths, so a
  fixed recalled recipe cannot pass traversal.
- Before the reachout action, probes at the two frontiers reduce the same
  amount of global uncertainty. Only the probe on the branch selected by the
  current goal has target-relevant information gain.
- The delayed goal starts at `s2` and ends at `g0` or `g1`. It was hidden at
  the second write. Its unique route requires old upstream/downstream edges
  plus the newly observed frontier edge; the exact reachout task is not the
  final task.

## 2. One root's four phases

### A. Experience and first DREAM/SLEEP

The parent-deleted child receives generic investigation tasks at the old
stations. It chooses legal `TEST`s and observes ordinary outcomes. Goals,
future paths, the frontier challenge, and delayed targets are absent.

At the ordinary DREAM boundary, the child may author:

- cited one-edge atoms; and
- a directionless `USE_LINK(edge_i, edge_j)` when two witnessed edges share a
  public endpoint.

The trusted event layer owns action/outcome/provenance facts. It may validate
that a proposed atom is supported and that a proposed link joins compatible
endpoints. It may not propose, select, repair, rank, or insert the link. No
goal, path, answer, success label, or future identifier may enter a row.

SLEEP uses the already H1-qualified writer and inherited replay policy. It
extends or cumulatively reconstructs the same unified child adapter; it does
not mount a second "memory LoRA."

### B. Rote, composition, and goal traversal; no write

Fork evaluation-only descendants from the exact S1 state. Give:

1. held-wording one-edge questions;
2. route `s -> v0`; and
3. route `s -> v1` from the byte-identical start state.

Phase B is destroyed after scoring and cannot write or affect Phase C.

The S1 causal variants are:

- `OLD_AUTH`: authentic atoms plus child-authored links;
- `OLD_DERANGED`: identical atoms with a fixed-point-free, degree/type/age/
  token-matched link permutation; and
- `OLD_ATOMS`: identical atoms, no links, with gradient-bearing matched
  neutral rows so training dose is equal.

All three must retain comparable rote one-edge accuracy. A difference between
them on two-edge routes then cannot be explained by one arm simply lacking the
atomic facts.

There are two legitimate outcomes:

- `OLD_AUTH > OLD_ATOMS and OLD_DERANGED`: stored child-authored connection
  adds causal value; or
- `OLD_AUTH ~= OLD_ATOMS > OLD_DERANGED`: the child composes atoms at read
  time, so composition/traversal is real but explicit DREAM-link value is not.

Do not call the second outcome a learned connection in memory.

### C. Goal-directed reachout

Restore the exact pre-B S1 state. Reveal a goal `s -> w_b`, where `b` is
balanced across roots. Give exactly one `TEST` opportunity chosen from the
two frontier families. Either port within the relevant frontier is accepted
if it separates its two live outcomes; testing the other frontier is globally
informative but irrelevant to this goal.

Primary evidence is the executed test and its exact target-relevant
information gain. A `PREDICT`/hypothesis declaration is logged as a secondary
thinking diagnostic, not made a brittle prerequisite for the world action.

Compare `OLD_AUTH`, `OLD_DERANGED`, and `OLD_ATOMS` from the same pre-action
state. This reveals whether carried structure helps locate the right gap. Keep
all actions and outcomes in the intention-to-treat denominator.

The environment returns the one public frontier outcome. The twin returns the
opposite port binding. The outcome is sealed before any post-outcome record or
score is available.

### D. Second SLEEP, sterile reset, delayed old-plus-new route

Run a second matched SLEEP, then start a fresh process with empty context,
workspace, retrieval/query state, and raw Phase-C transcript. Reveal the
previously hidden goal `s2 -> g_b` under a new surface and candidate order.

The S2 variants are:

- `FULL_t0` and `FULL_t1`: authentic OLD plus the authentic NEW row for each
  counterfactual twin;
- `OLD_REPLAY`: authentic OLD plus matched S2 neutral work, with NEW absent;
- `NEW_ONLY_t0` and `NEW_ONLY_t1`: authentic NEW plus matched work, with OLD
  absent.

Cross-mounting `FULL_t0` and `FULL_t1` on the opposite twin supplies the
wrong-new-binding intervention without another fit. Thus one pair-root needs
three common S1 fits and five S2 fits: **eight fits**, not a broad sweep.

The delayed route passes only if:

- FULL succeeds;
- OLD_REPLAY fails or loses the registered margin;
- NEW_ONLY fails or loses the registered margin; and
- the opposite-twin FULL redirects the frontier port/path in the donor
  direction rather than leaving behavior unchanged.

This establishes one finite expansion-and-reuse relay. It is not repeated
open-ended self-improvement.

## 3. Information visibility and contamination firewall

### Private to generator/checker

- root seeds and hidden graph;
- twin binding and correct routes;
- future goals/targets;
- intervention maps and answer keys;
- evaluation scores and extension decisions.

### Visible to the child or baseline only when causally legal

- current public state, legal action surfaces, and current goal;
- its own executed public actions and ordinary outcomes;
- rows returned by the assigned memory interface with public citations; and
- the Phase-C outcome only after the one committed test.

### Visible to DREAM/SLEEP

- committed child thought/action continuations;
- authoritative public action/outcome/event IDs up to the frontier; and
- inherited replay/preservation material already allowed by the qualified
  child lineage.

DREAM/SLEEP cannot see future goals, target paths, hidden graph truth, another
arm, evaluator outcomes, or parent text. The mechanical compiler checks facts
and citations; it never supplies the learning judgment or connection.

### Clean-lineage rule

1. Seal and hash the H1 adult before generating PCFL-R3 roots.
2. Copy it outward into disposable benchmark descendants.
3. Use separate DEV and CONF namespace/exposure registries covering every
   generation call, fit-only identifier, prompt, and model-visible artifact.
4. Never merge a benchmark adapter, corpus, lesson, score, parent update, or
   prompt choice back into the adult, classroom, parent, bootstrap, or future
   clean root.
5. A mechanism or writer change forks a new adult lineage; a task/prompt
   change uses DEV descendants only.

## 4. Held-out structure

Use **8 DEV pair-roots** and **16 sealed CONF pair-roots**. Confirmation root
seeds, handles, geometry, goal balance, twin assignments, order, metrics, and
thresholds are hashed before the first DEV model output. DEV roots tune only
prompt/interface and one resource point; they never count in confirmation.

Within every root:

- individual old transitions are witnessed through the child's own actions;
- one-edge tests use unseen wording/order but the same witnessed relation;
- route endpoints and complete action sequences never occur in source rows;
- the two Phase-B goals are absent until after S1;
- the reachout goal is absent until after S1;
- the delayed goal, alternate start/target pair, complete path, and response
  surface are absent until after S2;
- the Phase-C frontier outcome is unknowable from pre-outcome visible bytes
  because counterfactual twins share those bytes; and
- no literal evaluation prompt, correct route, complete path record, or
  answer-bearing summary appears in any corpus or text store.

Run exhaustive CPU shortcut controllers before model calls: identifier-only,
goal-only, state-only, constant route, candidate-order, action-frequency,
one-edge retrieval, nonadaptive fixed probe, exhaustive-but-one-probe, and
wrong-life memory. The first five must be at chance; rote retrieval may pass
one-edge tasks but must fail the two-edge and delayed tasks.

## 5. Native baseline contract

All systems begin from the same parent-deleted adult bytes and the same Phase-A
public event tape for the information-matched mechanism comparison.

### `ACTIVE_STRUCTURED_TEXT`

- starts empty;
- stores every legal public event once;
- receives the exact same admitted child-authored atoms/links as DLT at the
  same SLEEP frontier;
- uses a frozen candidate-blind typed/graph-assisted retriever;
- exposes complete rows with citations, no hidden solution scan; and
- is certified by restart, insertion-order, store-swap, link-derangement,
  bridge-cut, wrong-root, irrelevant-store, and binding-twin tests.

It may preserve raw evidence alongside compiled rows. That makes it a strong
opponent rather than an intentionally lossy text proxy.

### `WITNESSED_GRAPH`

- adds only an edge that was actually observed by a public `TEST`;
- contains no hidden/unwitnessed edge and cannot predict the twin outcome;
- updates transactionally at the same SLEEP frontier;
- supports exact adjacency/path queries or a native shortest-path planner;
- reports every visited node/edge and CPU operation; and
- runs bridge/edge cuts and twin swaps directly.

The native planner is allowed to be strong. A separate common local-edge
reader factorial can isolate storage/interface effects, but the primary
system comparison must not cripple the graph.

### `RAW_EPISODIC`

Store exact public events and retrieve complete cited episodes with the same
maximum read opportunities and returned tokens as structured text. No inferred
link or route is added. This is the cheap diagnostic that should pass rote
retrieval and exposes whether composition really exceeds lookup.

### Resource fairness

- Same adult, source events, causal frontier, task/action surface, goal,
  generation-token allowance, action allowance, decode seeds, and scorer.
- RAG and structured text share a DEV-selected nonbinding read allowance. Test
  1,024/2,048/4,096 returned tokens on DEV and freeze the smallest point where
  doubling changes value by less than the measured noise/practical margin.
- Learned query rewriting or repair consumes ordinary actor turns; there is no
  uncharged second LLM.
- DLT uses its native no-text interface. Do not pad the primary native-system
  comparison. For a same-semantics carrier diagnostic, reserve the same prompt
  slot and use a neutral sham plus native-empty sensitivity.
- Report compiler calls/tokens, optimizer target tokens/steps/GPU time,
  persistent bytes, retrieval/index operations, returned/input/output tokens,
  environment actions, and latency separately. There is no honest scalar
  “equal memory compute.”

The systems are allowed to choose different Phase-C actions in the native
comparison; that is the expansion effect. The common-history carrier table
uses the same witnessed action/outcome for every carrier and is reported
separately.

## 6. Metrics, controls, and claim order

Keep a noncompensatory vector rather than one forgiving average:

| stage | primary root-level outcome | decisive controls |
|---|---|---|
| `R` rote | exact one-edge action/outcome accuracy and legality | OFF, wrong root, row swap; S1 arms must remain within `.05` |
| `C` composition | exact two-edge route success; no direct route row | atoms-only, link derangement, each-edge/bridge cut in text/graph |
| `T` traversal | both same-start goals correct and goal swap redirects first edge/path | goal-only, fixed recipe, bridge substitution, twin path |
| `Q` reachout | relevant-frontier experiment chosen and positive target information gain | irrelevant equal-entropy frontier, nonadaptive probe, reachout disabled |
| `X` delayed reuse | exact `s2 -> g_b` route after reset | OLD-only, NEW-only, SLEEP/OFF, opposite-twin adapter/store, wrong root |

Additional invariants: strict action legality at least `.95`; zero future or
parent leakage; exact event/citation fidelity; unrelated-interface change no
worse than `.05`; no hidden reacquisition path inside the final action budget;
and all failures retained as zeros.

The claim order is fixed:

1. `R` qualifies the memory/read interface; it earns no connection claim.
2. `C` earns composition. Add “child-authored connection added value” only if
   authentic links beat both atoms-only and deranged links.
3. `T` earns goal-conditioned traversal only if both goals and redirection
   pass.
4. `Q` earns active gap-filling only if the chosen action has target-relevant,
   not merely global, information gain.
5. `X` earns one expansion/reuse cycle only if OLD and NEW are separately
   necessary and the twin binding redirects behavior.

For confirmation, the pair-root is the independent unit; twin sides, goals,
calls, technical fit seeds, and decode repetitions are nested. A compact
prospective rule is: each released root-level contrast has mean at least `.10`,
a one-sided 95% root-level lower confidence bound above zero, and the expected
sign in at least `13/16` CONF roots. Use fixed-sequence testing `C -> T -> Q ->
X`; an earlier failure prevents downstream claim promotion. The 13/16 rule is
a useful exact-sign floor, not a substitute for the bound or the practical
effect.

Report DLT, structured text, raw episodic, and witnessed graph side by side.
Use `ACTIVE_STRUCTURED_TEXT` as the primary strong-memory comparator. The exact
graph is a reference allowed to win. No system is called superior from a
single fixed child; population language waits for independent H2 child roots.

## 7. Compression is deliberately out

Do not include a positive rate--distortion gate in PCFL-R3.

The current rank-8 all-layer adapter is `80,792,096` stored bytes. Even the
bf16 tensor floor is about `40.37 MB`. A small root's raw event log, typed
store, and witnessed graph will be orders of magnitude smaller. Rank is
capacity, not evidence of compression.

Log exact bytes for every carrier and report the likely negative ordering.
Use `compiled`, `connected`, or `consolidated`, never `compressed`. A later
separate experiment may test either:

- text-to-text semantic-code rate--distortion (raw expanded events versus a
  denotationally certified schema-plus-residual code); or
- physical LoRA compression only after a model-free crossover receipt shows a
  life large enough to exceed the complete mounted adapter state.

Neither belongs on the post-H1 critical path.

## 8. Scale and GPU estimate

### Staging

1. **CPU generator/oracle audit:** materialize 8 DEV + 16 CONF pair-roots twice
   with independent implementations; exact graph/oracle passes, every shortcut
   ceiling and twin mutation passes. Zero scientific fits.
2. **Zero-fit native kill gate:** on the first four DEV roots,
   `ACTIVE_STRUCTURED_TEXT` and `WITNESSED_GRAPH` must each complete R/C/T/Q/X
   on at least three roots with exact visibility/cut receipts. If not, repair
   the world/reader; do not blame LoRA.
3. **Two-root LoRA sentinel:** `2 roots x 8 fits = 16 fits`. Continue only if
   authentic material moves the intended conditional behavior and the
   interface/locality gates survive.
4. **Complete DEV:** six more roots, 48 fits. Freeze bytes and resource point;
   DEV never enters paper inference.
5. **CONF:** 16 untouched roots, 128 fits, no replacement. Open downstream
   endpoints in fixed sequence.

### Cost

The current qualified-writer planning anchor is about `7.5--15 A40-minutes`
per fit. At that rate:

- two-root sentinel fits: `2--4 A40-hours`;
- complete eight-root DEV fits: `8--16 A40-hours`; and
- sixteen-root CONF fits: `16--32 A40-hours`.

Actor inference, text/graph evaluation, audits, and failed work remain extra.
A reasonable preliminary all-in envelope is **30--70 aggregate A40-hours**,
with a hard planning cap of **80 A40-hours** after one native root is profiled.
These are planning numbers, not an authorization or a promise. If the final
row volume makes a fit slower, rebind the cap before launch rather than using
the old throughput as fact.

Eight-way parallelism can make the confirmation a few wall-clock hours after
roots and actors are ready; it does not change `n=16`.

## 9. Plug into the adult running-versus-frozen-SLEEP 2x2

PCFL-R3 first runs as the post-H1 mechanism module above on disposable clones.
Only if it passes does the same task generator become the adult learning gym.

For each independent H2 child root, fork the sealed P and U adults into:

```text
P_RUNNING    P_FROZEN
U_RUNNING    U_FROZEN
```

Run a fixed sequence of fresh PCFL-R3 blocks. Every block has one old-source
period, one first SLEEP, one gap-filling action, one second SLEEP, and sterile
delayed probes. Running branches promote technically accepted candidates;
frozen branches execute and save the identical compiler/trainer/gate path but
never mount candidates. Evaluation forks are destroyed and their outputs
never enter subsequent SLEEP.

The four branches receive the same exogenous opportunity tape before actions,
but their later public histories may diverge because their policies choose
different tests. That divergence is the proposed mediator, not contamination.
H2 remains:

```text
(gain(P_RUNNING) - gain(P_FROZEN))
  - (gain(U_RUNNING) - gain(U_FROZEN))
```

Use at least four blocks so entry, early, middle, and late acquisition can be
measured; interleave retention probes from prior blocks. Do not carry the
eight-fit mechanism intervention bank into every H2 child. H2 uses only each
branch's native full/shadow writer. Structured-text, graph, and final-batch
branches are separately cloned from the parented adult for the conditional
system comparison; they never re-enter the factorial.

Before scaling, profile one excluded H2 root. Four branches x four blocks x
two shadowed/promoted SLEEP opportunities implies **32 matched writer fits per
root**, or roughly `4--8 A40-hours/root` at the current fit anchor before wake
and probe inference. Therefore a 16-root factorial has a fit-only floor around
`64--128 A40-hours`; its final bound must come from the excluded root, not the
older CompilerGym life estimate.

This plug-in yields a clean division:

- PCFL-R3 mechanism clones establish what connection/traversal/expansion
  means and whether the memory carriers can do it;
- H1 establishes that parenting caused a retained learning behavior; and
- the adult 2x2 establishes whether that developed child gains more from
  continuing SLEEP across new PCFL-R3 blocks.

## Evidence inspected

- `AGENTS.md`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md`
- `research_notes/54_one_child_pcfl_relay_v1_causal_repair.md`
- `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md`
- `research_notes/2026-09-11_final_benchmark_claim_gap_audit.md`
- `research_notes/2026-09-11_paper_path_reconciliation.md`
- `research_notes/analysis/2026-09-12_m_core_exact_two_cycle_design_v8.md`
- `research_notes/analysis/2026-09-12_next_three_information_gain_rank.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/analysis/2026-09-12_minimum_strong_agent_memory_baseline_route.md`
- `research_notes/analysis/2026-09-12_dream_lora_think_paper_decisiveness_gap_audit.md`
- `research_notes/2026-09-11_minimal_causal_parenting_h2_consensus.md`
- current `research_loop/COORDINATION.md` through the level-zero/H1 updates

