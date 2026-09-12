# Minimum strong agent-memory baseline route for Dream--LoRA--Think

Date: 2026-09-12 UTC  
Role: independent paper-route audit  
Status: design recommendation only. This memo implements nothing, launches
nothing, and changes no scientific claim or authority.

## Bottom line

The minimum credible paper suite is not twenty memory systems. It is five
competitors plus one headroom reference:

1. **`NONE`** -- the same frozen actor with no persistent lifetime memory;
2. **`NATIVE_CONTEXT`** -- the raw chronological life while it fits in the
   model's measured native window, followed by honest chronological
   truncation;
3. **`RAW_RAG`** -- strong iterative retrieval over the raw action--outcome
   ledger;
4. **`ACTIVE_STRUCTURED_TEXT`** -- a lossless raw store plus the same admitted
   DREAM records as the proposed learner, exposed through a frozen native
   typed/graph-assisted retriever;
5. **`FINAL_BATCH`** -- one end-of-life LoRA consolidation from the same
   accepted material and the same total supervised-token/update budget as the
   periodic writer, with no intermediate promotion; and
6. **`GOLD_HISTORY`** -- a legal-history or exact public-evidence oracle used
   only to establish headroom, never called a deployable baseline.

If the benchmark's target requires explicit multi-hop relations, add an
**exact witnessed-event graph** as a compulsory task-native reference. It is
not optional for a claim about connected knowledge: if a lossless graph with a
native planner wins, the honest result is that explicit memory is better in
that regime. A generator-aware program-induction reference is additionally
required only when the benchmark generator exposes a compact identifiable
program family; it need not be forced into every task.

The comparison should have two layers:

- the **causal developmental test** is still H1 followed by the parented versus
  unparented x running-SLEEP versus frozen-SLEEP H2 factorial; and
- the **memory-system test** compiles a byte-identical public source history
  through the five memory conditions above. This second layer is what can
  support a statement about strong memory baselines. On-policy H2 branches are
  allowed to acquire different experience after treatment; they cannot also
  be used to claim information-matched carrier superiority.

No existing result supplies this suite. The historical final brief is a
static short prefix, `Ledger.recall` is a weak token-overlap helper, and the
historical RAG arms live on a different benchmark. The nine-life matched
brief diagnostic (`F=.2528`, `A=.2382`, `T=.2570`, `AT=.2424`) motivates a
real text baseline but does not instantiate one.

## 1. Which baseline answers which claim

### H1: did developmental teaching persist after the teacher disappeared?

H1's primary experiment should stay small and causal. For every independent
child root, raise a targeted-parent child `P` and a dose-matched active-sham
child `U`, delete the parent and all wake-visible childhood state, then run
common-random parent-free trigger and contraindication probes with each
child's adapter ON and OFF.

The root-level H1 estimand is:

```text
H1 = (P_ON - P_OFF) - (U_ON - U_OFF)
```

Required H1 comparators are therefore only:

- `P_ON`, `P_OFF`, `U_ON`, and `U_OFF`;
- a wrong-binding or active-sham childhood treatment, rather than an inert
  no-message control; and
- exact-form, held-form, contraindication, interface, and spill tests.

One **same-semantics text carrier** is a valuable secondary H1 diagnostic:
mount the exact admitted child-authored record in a fixed memory slot while
the adapter is OFF. The within-child `OFF / ON / TEXT / ON+TEXT` factorial
asks whether the behavior lives in weights, in visible text, or in their
interaction. It is not a strong RAG result and it is not the H1 primary.

`NATIVE_CONTEXT`, `RAW_RAG`, and the full active structured-memory agent do
not belong in the primary H1 test. H1 concerns a learned disposition after
scaffold deletion, not which lifetime retrieval system wins. Loading the
entire childhood into context would answer a different question. Likewise,
`FINAL_BATCH` is not needed to show one H1 skill, though it becomes important
for the temporal claim in H2.

### H2: did parenting increase the value of later autonomous consolidation?

After H1 passes, fork each sealed adult into the already agreed four cells:

```text
P_RUNNING    parented childhood, adult SLEEP candidates promoted
P_FROZEN     parented childhood, full shadow SLEEP, candidates not promoted
U_RUNNING    sham childhood, adult SLEEP candidates promoted
U_FROZEN     sham childhood, full shadow SLEEP, candidates not promoted
```

The H2 estimand is the root-paired interaction in improvement/AUC, not a final
level:

```text
H2 = (P_RUNNING - P_FROZEN) - (U_RUNNING - U_FROZEN)
```

The absolute slope of `P_RUNNING`, childhood/early-adult retention, and
`P_RUNNING - P_FROZEN` must also be favorable. A high starting score cannot
rescue a null interaction.

The five-system baseline suite belongs **after this H2 mechanism gate**, as a
conditional whole-system comparison from the same parented adult checkpoint.
At minimum, compare `P_RUNNING` with:

- `P_NONE` / `P_FROZEN`;
- `P_NATIVE_CONTEXT`;
- `P_RAW_RAG`;
- `P_ACTIVE_STRUCTURED_TEXT`; and
- `P_FINAL_BATCH`.

Those native on-policy branches answer: *which complete deployed system does
better from the same starting adult and the same opportunities?* They need
not retain identical later histories, because changing later evidence is the
proposed feedback loop.

That native comparison alone cannot say LoRA is better *given the same
information*. For carrier/compiler attribution, take one predeclared common
public chronology -- preferably the shadow branch's target-blind deployment
ledger -- and freeze it at every cut. Run every memory system from that exact
source prefix. The raw systems see the same raw events; DREAM-LoRA and
DREAM-text receive the same unique admitted semantics; the final-batch system
receives the same accepted target rows. This is the fair information-matched
comparison.

### Baseline superiority is not H1 or H2

H1 can pass while text is a better carrier. H2 can pass while structured text
is a better whole system. Therefore “beats strong agent memory” is a third,
conditional result, not something to hide inside either hypothesis. The
claim order should be:

1. H1: parenting changed a retained process behavior;
2. H2: that change increased the marginal value of continued consolidation;
3. B: under a separate information/resource contract, the resulting system
   beat named memory configurations over the tested lifetime range; and
4. S, only if qualified: one named baseline configuration met the registered
   plateau rule while the proposed system continued to improve.

Failure of B narrows the paper to development and the flywheel; it does not
invalidate H1/H2. Failure of H1 blocks H2 and B because no developed learner
exists to compare.

## 2. Exact minimum baseline contracts

### `NONE`

- Same base/child checkpoint, system prompt, task state, action API, random
  seeds, thinking allowance, and scoring.
- No lifetime ledger in context, no retrieval, and no promoted adult update.
- For H2, shadow SLEEP still performs compile/train/validation and saves the
  rejected-by-design candidate; only mounting/promotion differs.
- Adapter OFF is also measured within every learned child, but repeated OFF
  calls are technical repeats, not independent learners.

This is the no-persistence counterfactual and the regular-agent floor.

### `NATIVE_CONTEXT`

- Append the public action--outcome chronology verbatim in causal order.
- Compute usable native capacity from the pinned model/tokenizer after
  reserving system, current task/state, memory wrapper, and the complete
  generation allowance. Do not use the advertised window size directly.
- Before capacity, expose all history. After capacity, keep the newest complete
  episodes that fit; no hidden summary, retrieval, or selective deletion.
- Report exactly where first truncation occurs and how much chronology is
  visible at every cut.

This is the honest direct-context reference. Crossing its context boundary is
not itself “saturation.”

### `RAW_RAG`

- Store every eligible public action/outcome event once, losslessly, with
  immutable event IDs and causal visibility.
- Freeze one development-selected hybrid retriever. For opaque PCFL handles,
  exact typed entity/action matching plus BM25 is more defensible than
  pretending an unrelated dense encoder understands the nonce names; for a
  semantic external gym, add one frozen embedding model.
- Let the actor formulate or refine retrieval queries inside its ordinary
  thought/tool turns. Do not add a separate uncharged LLM query-rewriter.
- Return complete source episodes with citations; no summary, inferred edge,
  task answer, future event, or outcome-selected retry.
- Use the same memory-return allowance and maximum retrieval opportunities as
  structured text. Charge misses, repeats, and unused opportunities.

This is the episodic retrieval baseline. The legacy token-set `RECALL` helper
does not meet this contract.

### `ACTIVE_STRUCTURED_TEXT`

- Start from an empty, branch-local store after childhood deletion.
- Preserve the same lossless raw events as RAG and, at the same SLEEP
  boundaries, run the same child-authored DREAM/admission surface used by
  Dream--LoRA--Think.
- Insert each grounded atom, scoped lesson, contrast, and declared connection
  once with evidence citations; keep every superseded version in the audit
  ledger.
- Use a frozen typed/graph-assisted retriever with candidate-blind queries,
  complete-row packing, explicit misses, and no hidden answer scan.
- Permit its native graph traversal: crippling it to one row would compare
  interfaces, not systems.
- Pre-certify source fidelity, causal visibility, restart/insertion-order
  determinism, store swaps, binding-twin redirection, necessary-row/bridge
  cuts, irrelevant-store no-harm, and strict action legality.

This is the strongest relevant external-memory opponent. It deliberately gets
the compiler's useful structure as text, so a LoRA win cannot be attributed to
withholding organization from the baseline.

### `FINAL_BATCH`

The minimum temporal control is not “LoRA at the end with arbitrary epochs.”
It is:

- remain frozen throughout data collection;
- at the terminal cut, train one fresh LoRA from the same starting adult on
  the exact final accepted corpus available to the periodic writer;
- match the periodic arm's cumulative supervised target-token passes,
  optimizer family, target modules, rank, preservation/replay material, and
  technical-seed policy; and
- evaluate only after a clean reload under the same parent-free interface.

This isolates **when** updates influence the life. The final corpus is the same
unique information, while repeated exposure is scheduled at the end rather
than spaced across sleeps.

Call this `FINAL_BATCH`, not LEAFE, unless the implementation also faithfully
constructs LEAFE's successful-trajectory rehearsal and original-failure-
history to improved-action pairs. A later functional `LEAFE_STYLE` baseline is
valuable and close prior art, but a rushed approximation should be labelled
functional, not a reproduction. One fair implementation can be derived from
the same public histories after H2 passes; it is not needed before the writer
and child-authored bridge are qualified.

### Exact graph and `GOLD_HISTORY`

For a typed connected-world benchmark, build an exact witnessed-event graph
from public events only and give it a native planner. It may not add an
unwitnessed edge. Graph storage, traversal work, and actor calls are reported.
If the hidden generator is explicitly learnable from public evidence, also
include a target-blind explicit program-induction reference.

`GOLD_HISTORY` may use the complete legal public evidence or hidden legal
solution only to determine remaining headroom and assay validity. It cannot
enter the system ranking.

## 3. Fairness: what is matched and what is reported

There is no honest scalar called “equal memory compute” across context, text,
graphs, and weights. Exact fairness requires matching the causal information
and actor opportunity, then reporting three different resource ledgers.

### Invariants across the information-matched study

1. **Source information:** one byte-identical ordered public chronology per
   root and cut; no target, future event, hidden state, other arm, parent, or
   evaluation outcome reaches a writer/index.
2. **Availability:** every carrier freezes at the same causal frontier.
3. **Actor:** same frozen model or sealed adult, chat template, task/state
   rendering, tool/action interface, parser, temperature, random seeds,
   generation allowance, and environment-action allowance.
4. **Evaluation:** same target deck, target order, fixed-K scoring, and
   common-random decode seeds. Invalid/missing actions score zero.
5. **Memory bandwidth:** RAG and structured text receive the same maximum
   retrieval opportunities and returned child-tokenizer tokens. Choose the
   allowance on excluded development roots from a predeclared ladder such as
   1,024/2,048/4,096 tokens, then freeze the smallest point at which doubling
   adds less than the measured noise/practical margin. A binding cap cannot be
   mistaken for memory saturation.
6. **Calls:** deterministic retrieval is a tool call, not a free model call.
   Any learned query rewriting, summarization, judging, or repair counts
   against the same total task-time model-call and generated-token ceiling.
   Native retrieval should normally use queries emitted inside the actor's
   existing turns, avoiding an extra hidden LLM.
7. **Prompt occupancy:** same-semantics text/LoRA carrier tests reserve the
   same prompt location. LoRA/OFF receive a target-independent sham block of
   equal tokenizer length plus a native-empty sensitivity cell. If sham versus
   empty shifts legality or value by more than `.05`, the carrier test is
   invalid. Whole-system native comparisons need not pad LoRA with useless
   text; they report the resource difference.
8. **Training:** all LoRA conditions share initialization rule, rank, modules,
   optimizer, precision, seed policy, maximum length, preservation mix, target
   tokens, steps, and clean reload. Technical fit seeds are averaged within a
   root and never counted as independent `n`.
9. **Isolation:** memory roots, indexes, caches, RNG, workspaces, adapters, and
   outputs are branch-local. Run-versus-skip suffix hashes must prove that
   evaluation does not alter later experience.
10. **Failures:** writer, fit, read, parse, retrieval, and action failures stay
    in the intention-to-treat denominator; there are no outcome-selected
    replacement roots.

### Three resource ledgers

Report separately, per root/cut/system:

- **write:** compiler/model calls and tokens, train input/target tokens,
  optimizer steps/FLOPs, GPU time, and write latency;
- **persistent state:** raw bytes, live text/index/graph bytes, number of
  records/edges, adapter bytes and trainable parameters; and
- **read/act:** retrieval/index operations, model calls, input/returned/output
  tokens, latency, thought tokens, and environment actions.

Do not repeat text rows to mimic LoRA epochs; that changes the text prompt.
Bind one set of unique meanings and separately report optimizer exposure.
Do not call a fixed-rank adapter compressed merely because its directory is
small. Compression requires a separate rate--distortion result over the full
persistent acting state.

## 4. Paired comparisons and analysis

The independent unit is a separately generated child/world root. Tasks,
cuts, decode repeats, queries, and optimizer seeds are nested observations.

### H1

For each root compute trigger utility and contraindication utility first, then
the adapter effect within child and the parenting interaction:

```text
P_effect = P_ON - P_OFF
U_effect = U_ON - U_OFF
H1       = P_effect - U_effect
```

Require favorable behavior on both trigger and correct-non-use cases,
parent-free, with interface/no-harm gates. The same-semantics text factorial
is secondary and analyzed within the same root.

### H2

For each deployment task, compute a fixed early-to-late gain or prespecified
area under the score-versus-experience curve. Average tasks within root, then:

```text
P_sleep = gain(P_RUNNING) - gain(P_FROZEN)
U_sleep = gain(U_RUNNING) - gain(U_FROZEN)
H2      = P_sleep - U_sleep
```

H1 is tested first. H2 is promoted only if H1 passes and `P_RUNNING` improves
absolutely while preserving childhood and early-adult competence.

### Strong-system comparison

On parented roots, compare root-paired post-native AUC and terminal utility:

```text
DLT - NATIVE_CONTEXT
DLT - RAW_RAG
DLT - ACTIVE_STRUCTURED_TEXT        # primary strong-memory comparator
DLT - FINAL_BATCH
DLT - WITNESSED_GRAPH               # when the task is relational
```

Declare `ACTIVE_STRUCTURED_TEXT` primary and use simultaneous paired
confidence bounds (for example a max-t/Dunnett procedure) across the remaining
named comparators. Do not turn every task or checkpoint into an independent
sample. Report native-system results and common-history compiler results in
separate tables.

## 5. What “saturation” must mean

The core paper should default to **finite response curves**, not saturation.
The word is earned only by one named, frozen baseline configuration on
novelty-certified information cohorts.

Pre-register at least two earlier increments and three fixed cuts after a
late-window anchor. At every late interval, genuinely new supported causal
information must enter. A baseline configuration is saturated only if all of
the following hold on independent confirmation roots:

1. its root-level late-window slope has a two-sided 90% confidence interval
   wholly inside `[-.02,+.02]` normalized utility per information cohort;
2. each of its final two interval gains separately has a 90% interval wholly
   inside `[-.02,+.02]`;
3. oracle headroom at the terminal cut is at least `.10`;
4. early/old information remains within its frozen retention margin;
5. no run is excluded for writer/read/interface failure; and
6. doubling the baseline's retrieval bandwidth also improves by no more than
   `.02` under the same root-level equivalence rule.

A negative slope is degradation, not saturation. A flat 1,024-token curve
that improves at 2,048 tokens is bandwidth-limited. A long-context curve
flattening exactly when truncation begins is context-limited. Neither earns a
general claim that RAG, text memory, or context “saturates.”

After the baseline's anchor is frozen independently, Dream--LoRA--Think can be
said to improve beyond it only if its own post-anchor slope is positive, its
anchor-to-terminal gain is positive, its paired slope advantage is positive,
retention passes, and the terminal paired advantage clears a registered
practical margin.

The existing design history estimates that a `.02` equivalence band may need
roughly `192--256` independent roots. That is not presently a justified core
paper expense. With `48--96` roots, report curves and uncertainty; if a wider
`.05` band is powered, call it a **practical plateau at the tested resource
setting**, not unqualified saturation. Power is recomputed from an excluded
or blinded variance sample before confirmation; it is never inferred from
targets or decode repetitions.

## 6. Cost and staging

The suite is cheaper than it sounds because only the periodic and batch LoRA
conditions train.

Let:

- `R` = independent roots;
- `K` = evaluation cuts;
- `Q` = sealed target tasks per cut;
- `J` = common-random decode repeats;
- `C` = actor call/turn cap per task; and
- `S` = promoted SLEEP opportunities per running life.

Then the common-history evaluation load is approximately:

```text
actor evaluations = R * K * Q * J * number_of_systems
maximum actor calls = actor evaluations * C
```

`NATIVE_CONTEXT`, `RAW_RAG`, `ACTIVE_STRUCTURED_TEXT`, and the graph use zero
optimizer GPU-hours; they add actor inference and CPU indexing/retrieval.
`FINAL_BATCH` adds one terminal fit per technical seed and root. At the
currently observed writer scale of roughly `7.5--15 A40-minutes/fit`, two
nested fit seeds cost about `.25--.50 A40-hour/root` before actor evaluation.
This is only a scale anchor; a terminal life corpus must be re-profiled and
the cap rebound before launch.

The H2 factorial is much more expensive. The existing 128-episode canary
estimate is `50--80 A40-hours` for one excluded root, and an earlier 16-root
paper-grade estimate is `800--1,200 A40-hours`. Those figures predate a final
benchmark/runner profile and cannot be copied into a new protocol unchanged.
The baseline suite should therefore be staged:

1. **Now:** no agent-memory GPU baselines. Finish the opposite-action writer
   sign canary and the favorable level-1 teaching/plasticity test.
2. **After writer pass:** implement/certify the shared text store and exact
   same-semantics text carrier on CPU; use it as a zero-fit assay ceiling.
3. **After a child-authored H1 bridge:** run the small parent-deleted H1 pilot
   with the secondary text factorial. Do not start adult lifetime baselines
   from a child that has not passed H1.
4. **After directional H2 canary:** launch a small excluded-root common-history
   comparison of all five systems and profile actual read/write cost. Freeze
   one strong structured-text configuration before confirmatory outcomes.
5. **Confirmation:** run the H2 factorial and the predeclared baseline
   comparison on fresh roots. Add a formal plateau extension only if the
   finite curves, headroom, variance, and available compute make it credible.

The CPU substrate and manifests may be built earlier in parallel. What is
premature is spending scientific GPU-hours or writing superiority/saturation
claims before the writer and H1 bridge pass.

## 7. Exact current-state judgment

- **Ready now:** OFF/wrong-binding controls for the level-1 open-loop test;
  text-store and resource-accounting design work; no-memory and exact-text
  zero-fit ceilings.
- **Not yet ready:** any baseline advertised as strong active RAG/text memory,
  any LEAFE-like GPU comparison, the adult H2 factorial, or saturation
  language.
- **Why:** the current writer has not yet passed the required two-input,
  opposite-action sign canary; the proposed level-1 test is not DREAM/SLEEP;
  no prospective child-authored parent-free H1 bridge exists; and no active
  text system has passed a native certificate.
- **Existing evidence:** useful supplied material can alter later action in a
  bounded development assay, but historical whole-text writes are unstable,
  static text is at least competitive, and none of the current artifacts
  establish selective experiential memory, lifetime improvement, strong-
  baseline superiority, or saturation.

The shortest credible route is therefore:

```text
opposite-action writer gate
  -> level-1 favorable teaching/write qualification
  -> child-authored parent-free H1 bridge (+ exact-text factorial)
  -> parented/unparented x running/frozen H2 canary
  -> common-history NONE / CONTEXT / RAG / STRUCTURED-TEXT / FINAL-BATCH
  -> fresh H2 confirmation
  -> optional powered plateau extension
```

## Evidence inspected

- `AGENTS.md`
- `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md`
- `research_notes/analysis/2026-09-12_paper_goal_highest_value_route_synthesis.md`
- `research_notes/analysis/2026-09-12_level1_teaching_corpus_plasticity_redteam_protocol.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/analysis/2026-09-12_dream_lora_think_paper_decisiveness_gap_audit.md`
- `research_notes/analysis/2026-09-12_next_three_information_gain_rank.md`
- `research_notes/2026-09-11_minimal_causal_parenting_h2_consensus.md`
- `research_notes/2026-09-11_paper_path_reconciliation.md`
- `research_notes/2026-09-11_brief_adapter_matched_2x2_audit.md`
- `research_notes/related_work/20260906_experience_learning_neighbors.md`
- `research_loop/plans/rml_paper_claim_audit.md`
- `research_loop/advisory/20260903_rml_paper_experiment_v1.md`
- `research_notes/50_rml_paper_design_adjudication.md`
- `paper_prototype/astra_sprint_abstract_20260912.md`
- current `research_loop/COORDINATION.md` through the level-1 red-team entry

