**Source boundary.** The notebook file itself is not attached here. I can synthesize the shared context and lens excerpts, but cannot independently verify their SEQ mappings, code, manifests, or raw traces. Citations below refer to the reported notebook sections; no lettered attachments were supplied. F’s corrected specification comes from an **unnumbered implementation note**, and its execution status from **SEQ-035**. Proposed compute allocations are explicitly distinguished from measured results.

## Ten-line verdict for the lead

- **The write matters:** its recipe changes which continuations and behaviours survive sleep; it is not a neutral container for experience. [SEQ-031–035]
- **A is the routine-transfer positive control**, not evidence of general factual memory. [SEQ-035]
- **The responsible ingredient remains unresolved:** A versus A_v3 changes both supervised spans and training duration. [SEQ-031]
- **B shows panel-dependent transfer**, not yet better generalisation; inspect actions and finish the missing controls. [SEQ-032–035]
- **C is an interface failure:** a learned answer format can prevent action before memory receives a meaningful test. [SEQ-033]
- **The completed car test found no qualifying out-of-context binding** in the tested configurations; context reading and habitual recitation are different achievements. [SEQ-025–034]
- **F is a fair, deliberately favourable rescue** for canonical-completion memory under repeated exposure—not a rescue of unrestricted factual recall. [SEQ-034–035]
- **Accept F only on a conjunction:** owner improvement, specificity, usable completion, exposure response, and interface survival; no “least-bad winner.” [SEQ-025–026; SEQ-033]
- **If F fails validly or remains inconclusive at the deployment cutoff, use retrieved text as the factual store and retain the behaviour adapter.** [Decision based on SEQ-033–035]
- **Run the real-gym struggle test in parallel:** the remaining claim requires the child’s own repeatedly experienced correction to change appropriate actions after context is cleared. [SEQ-034]

## What the write pretest establishes—and what replication must establish

### The corrected comparison

All entries are **dimensionless task scores**, evaluated at a horizon of **512 episodes** in the reported initial life. Use these matched references rather than earlier probes or cross-node controls. [SEQ-034–035]

| Write or control | Seen-panel score | Unseen-panel score | Defensible reading |
|---|---:|---:|---|
| Frozen | 0.4845 | 0.2487 | Matched baseline |
| A: production whole-text write | 0.5293 | 0.2731 | Reported routine on both panels |
| A_v3: target-only write | 0.4896 | 0.2557 | No demonstrated routine transfer |
| B: episode and local windows | 0.4817 | 0.2731 | Reported routine-like transfer on unseen panel only |
| Bs: episode views only | 0.4878 | Not reported | Seen-panel birth plateau |
| C: QA/chat/EOS write | 0.0000 | 0.0000 | Interface collapse |
| Frozen plus same-sleep brief | 0.4952 | 0.2731 | Below A on seen panel; tied on unseen panel |

**Every numerical table entry: SEQ-035; trainer definitions: SEQ-031 and SEQ-033.** The behavioural readings are reported interpretations; I have not inspected the action ledgers.

**A versus A_v3 establishes a recipe effect, not a loss-mask mechanism.** A uses whole-text loss for **3 epochs**; A_v3 uses target-only loss for **1 epoch**. Both use the same **856 corpus pieces**. Exposure and supervision change together. Neither “headers caused transfer” nor “target content cannot carry the routine” follows. [SEQ-031]

**B is interesting but not yet causal evidence for multi-scale context.** It changes corpus construction and training exposure. Its panel split could reflect conditional activation, more effective training, or brittle generation. Equal aggregate scores do not establish identical action sequences. Bs lacks the unseen-panel result needed even for the first local-view comparison. [SEQ-032–035]

**C is a deployment veto, not a verdict against every QA write.** It produced **0 actions across 16 evaluated episodes**, emitting bare answers without `ACT:`. QA conversion, chat framing, answer supervision, and EOS are bundled; EOS alone has not been isolated. Run an interface canary on memory-only and combined adapters before costly evaluation or commitment. [SEQ-033]

**The brief prevents a blanket weights-over-text claim.** At this horizon, A’s advantage over the brief is **0.034 dimensionless score points** on the seen panel, with an unseen-panel tie. At end of life, brief ≥ adapter in **12 lives**, while adapter > brief in **7 lives**, among **19 evaluated lives**. These are horizon-dependent results, not evidence of a universally superior store. [SEQ-034–035]

### Replication requirements

The pending `seed7` and `seed8` runs are **different-life replications**, not merely optimizer-seed reruns. Their completion is unverified. [SEQ-034–035]

| Claim | Required confirmation |
|---|---|
| A reliably transmits the routine | A executes the routine on both panels relative to each life’s matched frozen control. |
| A_v3 does not transmit it under the tested recipe | A_v3 lacks the corresponding action pattern—not merely a particular aggregate score. |
| B activates it conditionally | The unseen-only behavioural contrast recurs. Otherwise retain only the broader recipe-dependence claim. |
| Local views explain B’s advantage | Bs lacks B’s unseen-panel transfer, and an exposure-matched comparison rules out simply more training. |
| C reliably breaks the interface | Missing `ACT:` output and premature stopping recur. A surviving interface elsewhere would make collapse conditional, not erase the risk. |
| Mid-life weights outperform the brief | A exceeds the same-horizon brief within each replicated life; report the unseen-panel result separately. |

Use **same-node frozen, brief, and routine controls**. The reported node effect makes cross-node score matching unsafe; its cause remains unresolved. [SEQ-032 correction; SEQ-033]

After harvesting existing jobs, the highest-value causal additions are:

- **A, whole-text loss for 1 epoch**, shortening only the original schedule. [Proposed crossed cell using SEQ-031’s existing factors.]
- **A, target-only loss for 3 epochs**, extending only A_v3’s schedule. [Proposed crossed cell using SEQ-031’s existing factors.]
- **C with terminal EOS supervision masked**, leaving the other ingredients unchanged. This tests whether removing EOS is sufficient to restore action, not whether QA memory works. [Proposed ablation of SEQ-033.]

Log supervised-token presentations and optimizer updates: crossing epoch count and loss masking does not equalise training exposure.

## What the car test establishes, and the exact verdict on F

### The completed result

**No tested configuration qualified as clean out-of-context owner–colour binding.** The completed work includes adapter ranks of **8 and 32, dimensionless**, and the reported strength sweeps. Increasing rank or changing strength did not rescue these writes. This bounds the tested regime; it does not establish a universal capacity limit. [SEQ-029–034]

The mechanisms are distinguishable:

- **Antecedent writes learned to read an observation currently in context.** That is a useful context-reading skill, not persistence of the owner’s colour after the observation disappears.
- **Occurrence-preserving bare text B produced the only owner-specific signal**, but with habitual spill and problematic answer mass.
- **Improved training-text fit establishes better prediction of trained continuations**, not an independently verified semantic fact waiting inside the adapter. [SEQ-025–034]

The exposure-order conclusion needs precision: neither reported ordering rescued the completed A/C endpoint comparisons. B’s trajectory work was still unfinished at the latest entry. Do not claim that order is irrelevant across all writers. [SEQ-034–035]

The reason for conjunctive gates is concrete. At adapter strength **λ = 0.5, dimensionless**, B’s owner-specific contrast was **0.27 log-odds units**, with a **95% confidence interval** of **0.06–0.55 log-odds units**. Yet owner probability gain was **0.000 probability units**, and spill was **0.11 probability-change units**, exceeding the reported **0.03 probability-change-unit** ceiling. A positive relative contrast was therefore not clean retrieval. [SEQ-033; spill gate: SEQ-025]

### Is F a fair rescue?

**Yes, with a narrower claim and a fixed stopping rule.** Completing a canonical sentence is a legitimate memory interface if the child can invoke that prefix. Preserving and rehearsing repeated perceptions also better matches this project than demanding retention of an isolated planted fact. [SEQ-034–035]

F nevertheless changes **retrieval cue, write representation, and exposure regime**. Report it separately from the completed negative. Rescoring old adapters with completion cues is especially informative because it changes retrieval without retraining.

**Run-manifest check:** the corrected equal-exposure family is `F_r16k1`, `F_r16k4`, and `F_r16k16`; `F_r64k16` is the higher-exposure extension. These identifiers and their specification are supplied by the **unnumbered F correction**; **SEQ-035 reports execution status, not a verified specification**. Confirm their actual rendering counts, template counts, answer-token presentations, ranks, and target modules before interpreting them. Do not silently cite the specification as a numbered notebook result.

Keep separate:

- independent environmental encounters;
- distinct child-authored noticings;
- rendered copies or reformulations;
- optimizer presentations.

Rehearsal adds training exposure, not independent evidence. A heavily rehearsed F pass would justify **rehearsal-based associative storage**, not show that ordinary sleep naturally reaches the required dose.

### F success: require the whole pattern

Freeze the scoring implementation before opening results. Define the frame contrast as the adapter’s gain for the planted owner minus its gain for a matched similar-owner cue.

| Requirement | Passing pattern |
|---|---|
| Owner-specific association | The frame contrast has a **95% confidence interval** wholly above **zero log-odds units**, with uncertainty clustered by owner and bank-level results visible. [Convention: SEQ-025; proposed application to F.] |
| Genuine owner improvement | Correct-colour probability **and absolute likelihood** improve at the owner cue. The contrast is not manufactured by depressing the control. [Failure motivating this requirement: SEQ-026.] |
| Low spill | Similar-owner, unexposed-owner, unrelated-relation, and generic cues satisfy the verified spill gate, reported as **≤0.03 probability-change units**. Resolve the implementation’s unit ambiguity first. [SEQ-025; unnumbered F correction.] |
| Usable output | Natural completions emit the correct colour; conditional colour normalization does not conceal collapsed total answer mass. [SEQ-033.] |
| Exposure response | Greater effective exposure strengthens owner-specific recall without corresponding spill; unexposed owners remain negative controls. Saturation is acceptable. [Proposed criterion motivated by SEQ-025 and SEQ-034.] |
| Correct mapping | Owner and relation changes affect the answer appropriately. A scrambled-binding adapter follows its trained mapping rather than the evaluator’s original mapping. [Control logic: SEQ-025.] |
| Operational safety | Memory-only and combined adapters preserve the action interface. [SEQ-033.] |

**A qualifying exact-prefix result is canonical-cue binding.** It need not answer paraphrased questions to count as a stored association. To call it **usable canonical memory**, additionally require an agent-generated recall prefix in an untrained surrounding context and an appropriate downstream action. To call it **experiential memory**, require the own-perception struggle test below.

### F failure and fallback

These outcomes are **not passes**:

- a positive contrast caused by control suppression;
- better normalized colour preference with collapsed absolute answer mass;
- colour recitation across unrelated owners or relations;
- success only with the fact still in context;
- an action-interface failure;
- a favourable cell selected after every cell fails the gates.

A failed canary is a write failure; a broken scorer or inadequate exposure audit is an inconclusive experiment. Neither proves that memory capacity is absent.

**Sprint decision:** after a valid high-exposure failure in the intended memory configuration, stop using the factual memory block as the sprint’s store. If F remains inconclusive at deployment cutoff, use the same fallback rather than betting the lineage on it.

**Fallback architecture**

- **Persistent retrieved text:** the child’s observations and lessons, with source episodes, applicability conditions, outcomes, uncertainty, and contradiction/supersession links. Keep independent occurrences separate from replay counts.
- **Behaviour adapter:** multi-scale sequences of noticing, retrieving, checking applicability, revising, and acting. Its job is effective memory use, not arbitrary out-of-context factual persistence.
- **Atomic deployment:** version the text snapshot and adapter together; test frozen, retrieval-only, behaviour-only, and behaviour-plus-retrieval conditions with matched inputs.
- **Memory-block status:** retain the modular architecture for research, but disable the unqualified factual block in production. Do not preserve it merely to preserve the architectural claim.

Composition must be tested: adapter-plus-text interactions have helped and harmed in the reported record. [SEQ-028; SEQ-031]

## Struggle test — one-page execution specification

**Question.** After sleep and a context reset, can the child apply its own repeatedly experienced correction on fresh problems **when appropriate**, while withholding it on matched nontriggering problems? Run this in the operating gym; do not require F to pass first. [SEQ-034]

**Select and freeze the struggle.** Audit existing records for a recurring observable situation in which the child repeatedly makes a specific error, then itself discovers and successfully tests a correction. Require matched cases where that correction is unnecessary or wrong. Choose using acquisition records only, before inspecting post-sleep results. **No qualifying task family or child-authored lesson is verified in the supplied material.**

**Acquire experience.** Increase the sampling frequency of the legitimate task family; interleave contrast cases and ordinary tasks. Reuse same-child records only if their provenance is recoverable. Preserve repeated grounded noticings; do not replace them with parent-authored facts or synthetic paraphrases. Log encounters, child-authored spans, supported canonical statements, and training presentations separately. The intended scale is repeated experience, not an isolated planted fact. [SEQ-034]

**Acquisition gate.** With its relevant record still available, the child must identify the trigger and use its correction on acquisition-only instances. Otherwise label the test **lesson not acquired**, not failed consolidation. Freeze waking weights during diagnostic collection and train candidate writes from the same starting checkpoint.

**Sleep write.** Keep the proposed **rank-8 behaviour block and rank-32 memory block, dimensionless ranks**—a shared design ruling, whose exact module allocation I could not verify in SEQ-033–035. Write contextual thinking into the behaviour block and supported child-authored canonical statements into the memory block. Extraction and packing may change presentation, not author the correction.

**Paired evaluation.** Use identical fresh instances, generation settings, action budgets, and same-node references across:

- experimental blocks OFF;
- behaviour only;
- memory only;
- combined;
- the same behaviour block plus quarantined scrambled memory;
- OFF plus the relevant child-authored text.

The scrambled control permutes outcome spans across incompatible situations while preserving format and training volume; it must never enter the production lineage. Test target cases, matched contrasts, and an unexposed family. Weight-only conditions receive no record, brief, retrieval, or parent assistance.

**Measurements.** Primary: exact gym score, the recurring error rate, and action choice at the trigger. Separately test completion of the child’s canonical sentence against plausible wrong endings and matched nontrigger cues. Never feed diagnostic completions into behavioural evaluation. Estimate paired uncertainty over fresh instances and locally measured OFF variation; do not import a different panel’s noise band as a significance threshold. Audit `ACT:` parsing and termination first. [Interface and node concerns: SEQ-033.]

**Decision rule.**

| Observed pattern | Decision |
|---|---|
| Target correction improves beyond local uncertainty; contrasts remain appropriate; completion is trigger-specific; correct memory adds benefit over behaviour-only and scrambled memory; interface survives | **Pass: usable conditional memory with a demonstrated memory-block contribution in this case study.** |
| Conditional behaviour improves without canonical recall or memory-block contribution | **Behaviour consolidation; do not attribute it to the factual block.** |
| Canonical completion improves but actions do not | **Sentence storage; practical struggle-test failure.** |
| The correction appears everywhere | **Habit substitution; conditionality failure.** |
| Text works but weight-only conditions do not | **Write/persistence failure under the tested recipe.** |
| Acquisition and text controls fail | **Inconclusive about sleep.** |
| The action interface fails | **Write veto.** |

**Compute and stopping rule.** Adopt the supplied planning lens’s **144 GPU-hour ceiling** for collection, writes, controls, and evaluation combined. **This is a proposed allocation, not a notebook runtime; SEQ-034 motivates the experiment but does not verify that budget.** Measure pilot throughput immediately and calculate cost as allocated GPUs × wall-clock hours, summing all phases. Reuse audited records before buying more collection. If the ceiling cannot support acquisition plus adequately precise paired evaluation, report the shortfall; do not weaken the controls to manufacture a pass.

## Execution order for the requested window

Within the requested **48 hours**—a user-specified planning window, not a SEQ result:

**First:** harvest pending replications and F outputs, export artifacts, audit F exposure/scoring, run interface canaries, and select the struggle family. [Pending work: SEQ-034–035]

**In parallel:** launch the struggle diagnostic and implement retrieved-text fallback. Finish crossed A cells only after avoiding duplication of already-running work.

**Close:** inspect blinded action traces, apply the predeclared conjunctions, and freeze the architecture. Publish the strongest earned claim: **routine transfer, conditional behaviour consolidation, canonical-cue binding, or usable experiential memory**. Do not let success at an earlier level stand in for the next.