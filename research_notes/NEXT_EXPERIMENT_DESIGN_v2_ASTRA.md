CHANGE LOG — Parent-bearing training inputs are now prohibited by default; input and target provenance are audited separately.
CHANGE LOG — Asynchronous rounds, provisional confirmation, patient strikes, rollback ancestry, and stale-candidate handling are executable rules.
CHANGE LOG — Preparation, conditional memory, rare-exception retention, recurrent reasoning, and self-evaluation now have explicit tests.
CHANGE LOG — Deployment initialization, source splits, report resets, text memory, efficiency, and comparison exposure are specified.
CHANGE LOG — Capacity uses the critics’ planning assumptions; evaluator service, rehearsal, migration, and engineering dependencies are repriced.
CHANGE LOG — Unverified evidence is quarantined; conflicts with rulings or the deadline go to section 10 with compliant defaults.

# NEXT_EXPERIMENT_DESIGN_v2_ASTRA

**Intended file:** `research_notes/NEXT_EXPERIMENT_DESIGN_v2_ASTRA.md`  
**Decision basis:** Rohin’s rulings through **2026-09-11 UTC** [A, latest rulings].  
**Status:** Corrected pretest protocol, **not an accepted launch schedule**.

### Sources and numerical status

- **[A]**: supplied shared context, cited by ruling heading or Constraints.
- **[B]**: supplied draft, cited by section. Its references to Evidence, Write, Child, Parenting, Test, and Plan are **unverified secondary references**: those lens documents were not supplied.
- **[C]**: fidelity critic, cited by objection identifier.
- **[D]**: feasibility critic, cited by objection identifier.
- **[Design]**: a proposed setting or rule in this document, not an observed result. Every table labeled Design inherits that status.
- **[Derived]**: arithmetic from the cited inputs.

Section numbers, test names, file versions, seed names, scaffold levels, and write identifiers are identifiers, not measured quantities. Dates and times are UTC. A “problem” is an environment instance; an “episode” in evaluation is one execution of one problem.

**Could not verify:** repository state, remaining implementation effort, running jobs, raw results, lens documents, cited papers, throughput, lease cutoff hours, relay bandwidth, storage, or rental availability. The reported **76 passing CPU tests out of 76 tests** and byte-identical legacy compiler behavior are supplied regression evidence, not acceptance of the new system [A, Constraints].

A freeze package must contain the exact source documents, code hashes, numerical-settings registry, result registry, and signed acceptance artifacts. Unsupported entries cannot become “verified” through repetition in this document.

---

## 0. One screen

**Question.** Can a developed agent use its experience more effectively because its own thinking has become more conditional, reflective, and revisable—and can consolidation preserve that behavior?

**Child.** Qwen2.5-7B-Instruct, approximately **7 billion frozen base parameters**, with a learning adapter [A, Constraints]. Prefer **2 independent childhoods**, each comprising one adapter lineage and many working clones [A, “Two short childhoods”]. Clones contribute experience to their child; independently trained adapters are not averaged.

**Classroom.** Target-blind reasoning-gym tasks. Persistence through changing attempts comes first, together with recognizing completed goals. CompilerGym remains the unseen final world, never a childhood classroom [A, late compiler-test ruling; Constraints].

**Parenting.** Astra proposer and Astra verifier rooms; Fable and Codex advise asynchronously. Parents repeat a stable conditional lesson, solicit the child’s own restatement, and teach planning, checking, revisiting beliefs, and deciding when to act. Private reflection is readable but not admissible evidence for evaluation or corrective teaching [A, repetition, private-time, and central-parent rulings].

**Write.** Only eligible child-generated text is supervised. **Parent-bearing input sequences are quarantined.** Separately collected parent-free continuations preserve their actual recorded prefixes; no brief is deleted from a prefix to manufacture eligibility [A, repetition ruling; C1–C2].

**Final comparisons.**

- **Frozen transfer:** **12 report programs × 2 repetitions = 24 report episodes per agent**, with fresh context and frozen weights [D4; Design].
- **Continual deployment:** **512 deployment problems per agent**, with report forks at **9 checkpoint ages**, including entry; **216 report episodes per agent** in total [B §6; D4].
- Each comparison pair means **one developed agent and its untaught comparator**. Independent childhoods refer to developmental replication, not to clones.

The comparator has the same mechanism and resource caps, but can have less eligible replay and therefore less realized optimization. Call it a **same-cap, potentially unequal-training-exposure comparator**, not an exposure-matched parenting control [C21–C22].

**Headline discipline.** Preserve Rohin’s steps-/tokens-to-solve direction. Report score transfer and entry-adjusted improvement alongside a preregistered efficiency falsifier. A higher starting score is not faster learning; more reflection language is not metacognition [A, efficiency scoping; C36–C37].

**Deadline.** Protect verified migration by **2026-09-13 at 18:00 UTC** and evidence export by **2026-09-17 at 20:00 UTC** [B §§2, 7; D14]. Access ends **2026-09-18**, with the hour unverified [A, Constraints]. The conditional latest launch, **2026-09-13 at 06:00 UTC**, has **0 hours of unallocated slack** under the proposed critical path [D14].

**Immediate decision:** finish the executable acceptance manifests and measure the critical path. Do not launch because a parent call works, a GPU is idle, or the calendar is uncomfortable.

---

## 1. Evidence and the three core ideas

### What Attachment A supports

Attachment A supports a working diagnosis, not a demonstrated better learning algorithm:

- The write strongly stores generated material, yet behavioral gains are much smaller and can become recipe lock-in [A, “The write is an amplifier of habit”].
- Parenting can help in context, but durable benefit requires the child to produce useful thoughts and actions before consolidation [A, repetition ruling].
- Fixed compiler recipes explain repeated scores; probe variation includes recipe choice, not merely sampling noise [A, quantized gym scores].
- Format validity alone does not establish useful or safe behavior [A, gate and persistence directions].
- Text memory is a necessary comparator for any claim that weight memory adds capability [A, “Always a baseline agent”].

These observations motivate testing conditional behavior, not merely row likelihood or score movement.

### Historical results: quarantined pending a result registry

The draft contains many precise historical claims attributed to unavailable lenses: completed-life means, harmful parented results, disjoint-panel deficits, absorption estimates, overlap scores, and crossed text-memory cells [B §1]. **None is independently verified here.**

They must not be treated as audited corrections until the result registry supplies:

| Required field | Interpretation |
|---|---|
| Artifact identity | Run ID, checkpoint hash, ledger hash, analysis version |
| Panel | Program IDs, source groups, split and exposure status |
| Comparator | Exact adapter, prompt, memory, seeds, and checkpoint |
| Metric | Formula, direction, unit, denominator |
| Aggregation | Within-run and across-run weighting |
| Uncertainty | Repetitions, source units, missing-data treatment |
| Supersession | Which earlier result is replaced, and why |

[Design; C38–C39, C48.]

Do not infer action-distribution change from a noisy mean score difference. Cite the actual action trace analysis. Do not infer row-specific storage from an undefined “absorption” label.

For the new analysis, define row absorption as

\[
a(x)=\frac{\log p_{\mathrm{ON}}(x\mid c)-\log p_{\mathrm{OFF}}(x\mid c)}
{\text{number of target tokens in }x},
\]

in **nats per target token**, under identical context \(c\), tokenizer, and scoring code [Design]. Report own-row, unrelated-row, and format-matched controls separately. This definition does **not** retroactively validate the draft’s historical absorption numbers.

### The three core ideas

**The child is taught to learn.** Teaching should improve noticing, testing, and revising the child’s own rules. Evidence is later behavior without the parent, especially when a familiar response becomes inappropriate.

**Text versus weights.** Weight memory has not shown added capability if a capable frozen agent can match it using the same eligible memory. A shortened final brief is only a proxy for that comparison.

**Conditional memory as a guide.** Useful memory activates in the matching situation, remains restrained elsewhere, and yields to new evidence. Frequent rehearsal is compatible with this goal; unconditional repetition is not.

The mechanism sentence is:

> Parenting changes what the child notices and practices; lived outcomes supply evidence; the child’s own parent-free use becomes training material; consolidation should preserve that use in the situations that made it appropriate.

### Scope and positioning

This is a developed-system case study with internal controls and, if completed, independent replication. It does not isolate parenting from extra experience and optimization, and it does not estimate a population effect over future children [A, one-lineage claim; C45–C46].

The paper acceptance checklist must include:

- Verify the TMEM bibliography and relevant claims against the paper.
- Name TMEM on the first page.
- State the within-episode fast-weight precedent versus this work’s lifetime development, offline consolidation, and failure-study focus.
- Do not repeat “proved” without verifying the precise result.

[A, TMEM framing; C47.]

The psychological, biological, educational, and philosophical survey remains a required curriculum input [A, late gym-selection ruling]. Its mapped hypotheses, source papers, and limitations must be attached. Human-learning effect sizes are not predictions of adapter gains.

---

## 2. PRETESTS FIRST

### Release dependencies

The blocking chain is:

> Source policy and measurements → exact renderer → pilot traces → writer qualification → activated preparation writes → asynchronous integration → paired deployment rehearsal → signed freeze.

Baseline and source-panel work can run alongside renderer development. Fault fixtures can precede the full writer. Later tests cannot claim reuse unless the reused artifact has the same mechanism, configuration, and source policy.

### Planning assumptions—not measurements

Use the following planning rulers until replaced by separately measured rates [D1]:

| Quantity | Planning assumption |
|---|---:|
| Effective training throughput | **1,200 non-padding token-passes per second** |
| Full-problem inference | **22 problems per inference GPU-hour** at **16 turns per problem** |
| Ordinary probe | **12 programs × 2 repetitions = 24 episodes** |
| Ordinary probe cost | **1.091 GPU-hours** |
| Local collection round | **32 problems per clone**, approximately **1.455 hours per clone** |
| Training **1,000,000 token-passes** | **13.89 minutes**, or **0.2315 GPU-hours** |
| Training **5,000,000 token-passes** | **69.44 minutes**, or **1.1574 GPU-hours** |
| Training within **60 minutes** | At most **4,320,000 token-passes** |

[D1–D2; Derived.]

Measure reasoning-gym, CompilerGym, batched likelihood scoring, generated diagnostic answers, training, reload, and relay separately. Do not apply the full-problem ruler to short car queries. Effective training throughput must include padding and checkpointing overhead in elapsed time.

### Resource ledger

The former **128 GPU-hour** total was arithmetic, not a feasible release schedule [B §2; D13]. Replace it with this ledger:

| Test | Reservation or priced component | Remaining qualification |
|---|---:|---|
| P0 provenance and variant registry | **0 local GPU-hours** | Engineer and agent time still charged |
| P2 interface and baseline | **12 GPU-hours** | Measured full-loop pace |
| P4 classroom screen | **8 GPU-hours** | Extra reference/search work separately booked |
| P1 writer comparison | **24 GPU-hours** | Fixed candidate count; no open-ended search |
| PC conditional-memory suite | **12 GPU-hours provisional** | Scoring benchmark and complete token manifest |
| P5 parent room | **0 local GPU-hours** with external calls | API, tool, review, and audit time |
| P3 preparation | **24 GPU-hours provisional** | Activation-indexed excess exposure |
| P8 gate replay | **0 local GPU-hours** for stored fixtures | Prospective gate qualification |
| P6 throughput soak | **18 GPU-hours provisional** | Separate destructive recovery and migration |
| P9 incremental qualification | **12 GPU-hours** | One exact configuration; no unpriced replication |
| P7 deployment rehearsal | At least **9 GPU-hours**, plus collection and overhead | Event-level schedule and served-adapter checks |
| Reruns | **14 GPU-hours reserved** | Not a substitute for unpriced work |

[B §2 reservations, corrected by D6–D13; Design.]

The revised listed reservations total **133 GPU-hours**, before additional P7 collection, source search, calibration, migration, and unresolved scoring costs [Derived; D13]. **There is no accepted all-in pretest total yet.**

### P0 — Preserve evidence and enforce source boundaries

Before preemption:

- Inventory jobs, completion estimates, remaining GPU-hours, and scientific necessity.
- Preserve completed ledgers, configurations, gate decisions, models, and analyses.
- Hash the base, tokenizer, renderer, scorer, writer, trainer, parent tools, and evaluation manifests.
- Map A/B/C build labels to exact context, targets, masking, sampling, optimizer, and attention behavior before outcomes are inspected.

Test access as child, writer, room parent, central parent, and evaluator. Require **0 prohibited reads**, **0 prohibited input spans**, **0 prohibited target spans**, and **0 unresolved candidate definitions** [Design; B P0; C1–C2, C26–C27].

Source labels propagate transitively through summaries, filenames, tool errors, caches, gate records, and parental ledgers. A summary of report data remains report data. Only designated GATE-source dispositions may enter parent tools.

Live central-parent contexts must be fresh and allow-listed. Historical compiler knowledge in a research conversation cannot be removed by a lexical leak scan.

### P2 — Interface

Use the same **64 reasoning problems per condition** and **32 compiler engineering problems per condition**, comparing marker and free-form conditions [B P2]. Total: **192 executions**, approximately **8.727 GPU-hours** under the planning ruler [D7].

Engineering compiler data stays outside childhood and parent inputs.

Release thresholds [Design, retained from B P2]:

- Scoreable submission on at least **90% of problems**.
- Interface acceptance for at least **90% of submitted actions**.
- At least **50% of the marker condition’s actions per problem**.
- At most **2 nudges per problem** on average.

Wrong but valid answers pass interface acceptance, not correctness. Silent problems remain in the scoreable-problem denominator.

### P4 — Headroom, noise, and collapse support

Screen **24 development items under 4 generation seeds**, totaling **96 executions**, approximately **4.364 GPU-hours** [B P4; D7].

Families at or above **90% accuracy**, or at or below **2% accuracy**, fail this budget-specific screen [B P4; Design]. Require reference-search advantage of at least **0.10 verifier-score units** and at least **3 times the observed repeat standard deviation** [B P4; Design].

Additional costs are explicit:

- **8 repetitions × 12 programs = 96 episodes**, or **4.364 GPU-hours per reference checkpoint**, for operational calibration [D7].
- Two reference checkpoints cost **8.727 GPU-hours**, before reserve items or search [D7].
- Reference search uses a fixed budget of **4 candidate-blind search runs per source candidate**, each with the ordinary problem budget [Design].
- Initially register **24 report-source candidates** and **12 reserve-source candidates** [Design]. Their search cost is separately booked; it is not hidden in P4.

Reused observations must have identical panel, budget, scorer, adapter, and generation policy. Otherwise they are additional evaluations.

The positive tolerance formula and insufficient-support behavior are in section 3.

### P1 — Exact-context writer comparison

Freeze **3 representations × 2 training seeds = 6 candidates**, then **2 finalist reruns** under the lineage configuration: **8 candidate writes** total [D8; Design].

Representations:

- Legacy system comparator.
- Stripped-antecedent diagnostic.
- Exact-parent-free-context candidate.

The context-effect comparison uses the same eligible child targets. Legacy is a system comparison, not a pure context ablation.

Split before rendering by immutable generation event. For generalization probes, also hold out situation families. Alternate windows and short views of held-out events cannot enter training [C32].

Inspect **10 rendered sequences**, then run automated checks over the entire corpus [B P1; Design].

**Behavioral gate.** Use **12 held-out paired situations**, each containing a trigger and changed-trigger case, totaling **24 evaluation episodes per candidate** [Design]. Score whether the action is verifier-correct for that situation. Require:

- Exact context exceeds frozen base by at least **0.10 correct-action proportion units**.
- The paired **95% source-pair bootstrap interval** for that gain excludes **0 proportion units**.
- Exact context is not worse than legacy by more than the calibrated tolerance.
- Reversal/no-trigger performance does not decline by more than **0.05 correct-action proportion units**.

[Design; operationalizes C31–C32.]

All required episodes must be present; missing support means inconclusive, not pass. Likelihood improvement is a storage diagnostic, never the behavioral release gate.

The full-time-cap planning subtotal is approximately **18.364 GPU-hours**, leaving approximately **5.636 GPU-hours** within P1 for collection, scoring, loading, and diagnostics [D8]. An ambiguous result does not authorize extra cells automatically.

### PC — Conditional memory

The complete manifest and formulas are in section 4. Before scheduling, benchmark likelihood scoring and generated answers. PC remains **provisionally priced**, not accepted, until its measured scoring cost fits the reservation [D9].

### P3 — Preparation and short-term absorption

Test these authorized variants separately [A, preparation ruling; C3]:

- Ordinary parent brief and ordinary own-words rehearsal.
- The same lesson plus intensive own-words practice.
- Small interface-only instruction tuning, if it fits the pretest budget.

The interface-only corpus may contain neutral `ACT:` syntax examples, valid/invalid payload formatting, and toy interface schemas. It may not contain planning, reflection, predictions, solutions to classroom or deployment tasks, canned thoughts, or autobiographical claims. Maximum corpus: **128 examples**, each at most **128 tokenizer tokens** [Design]. Keep it isolated, versioned, and separately attributed. Content beyond this boundary requires Rohin’s explicit exception.

Intensive rehearsal means one additional child-authored restatement and a trigger/no-trigger application exercise during each initial parent interaction; it does not mean inserting the parent’s words into training [Design].

Use activation-indexed exposure:

1. Collect continuously from birth.
2. Identify the first and second activated preparation writes.
3. Continue for **32 completed problems after the second activation**.
4. Count **all** intervening problems, tokens, generated events, eligible rows, and supervised presentations.

[Design; C6; D10.]

The former **96 problems per variant** is a lower-bound planning case, not a fixed no-wait protocol [B P3; C6]. Cap each variant at **160 collected problems** for this screen; failure to reach the required activation and follow-up is inconclusive [Design].

The narrow two-variant lower-bound estimate is approximately **17.364 GPU-hours** before excess exposure and overhead [D10]. The interface-only variant is optional within the authorized preparation pretests, not a hidden extra arm.

P3 tests preparation and short-term absorption. It does **not** establish the repetition ruling’s comparative persistence falsifier unless **4 subsequent control-comparison windows** are actually completed [A, repetition ruling; D10].

### P5 — Parent room

Each model call has a **300-second timeout**, below the **6-minute gateway limit** [A, Constraints; B P5]. A room invocation permits at most **4 model calls**, including proposer, verifier, and bounded repair, with a **20-minute whole-room deadline** [Design]. Child operation never waits.

Run at least **4 room invocations**, requiring usable non-fallback output in at least **3 invocations** [B P5; Design]. Test delay, outage, disguised answers, private-content use, detector coaching, stale advice, and transitive forbidden sources. Every seeded prohibited candidate must be withheld.

Fallback is the latest verified brief. Local-model fallback is disabled unless its GPU allocation is explicitly booked. Reserve Astra service for final audit; coding, teaching, and review are not assumed to have unlimited concurrent capacity [D17].

### P6 — Separate throughput, faults, and migration

Run tiny destructive fixtures first: duplicate slices, publication interruption, stale ancestry, rollback, failed save, cache reuse, and delayed parent calls.

Then run the real throughput soak at the **actual proposed production configuration**, including sequence length, rank, writer cap, gates, confirmations, and report-service contention. A smaller soak does not qualify larger width [C34].

Require:

- **0 duplicate ingestion events**.
- **0 partial publications**.
- **0 mid-problem adapter changes**.
- Exact intended-versus-served adapter agreement.
- No clone waiting for a writer, parent, or confirmation.
- Compliance with the one-round deadline in section 3.

[B P6; C4–C5; Design.]

The old **18 GPU-hour** reservation is a bounded throughput reservation, not an all-inclusive fault-and-migration budget [D11]. Time destination reload and complete relay separately.

### P8 — Gate qualification

Replay the complete state machine over historical records and prospective fixtures. Historical records alone cannot qualify new score distributions.

Fixtures include stable equal-quality adapters, ordinary recoverable dips, severe harm, missing collapse support, divergent initial and confirmation scores, incompatible gym floors, rollback during training, and stale publication.

Record false strikes, false rollback, confirmation reversals, and incompatible-floor frequency. A confirmed-maximum floor is retained only if the full policy qualifies; otherwise use the conservative anchor policy in section 3 [C12].

### P9 — Incremental qualification

Use the exact finalist checkpoint after its declared cumulative preparation, its earlier-family corpus, a fixed interference corpus, the section 4 sampler, and the incremental learning rate.

Run **2 incremental updates**, with retention probes at **3 checkpoint ages**, plus transactional rollback and replay-cursor restoration [Design; D12]. A single such sequence has an illustrative cost of approximately **7.591 GPU-hours** before collection and overhead [D12].

This reservation covers one exact configuration. Reuse PC evidence only where PC exercises the identical implementation. If qualification fails or remains incomplete, incremental writing stays disabled; cumulative coverage demand must then be priced honestly.

### P7 — Deployment rehearsal

For one comparison pair, entry and post-update reports require **96 report episodes**, costing approximately **4.364 GPU-hours** before collection or training [D6].

Reserve at least **9 GPU-hours plus deployment collection and overhead** [D6]. Exercise:

- Frozen context reset.
- Continued learning and report isolation.
- Actual adapter identities served.
- Replay and phase initialization.
- Final-horizon closure.
- An event-level GPU schedule.

The schedule must show problem completion, slice release, training, examination, confirmation, publication, report execution, reload, and GPU ownership. Startup success is not acceptance.

---

## 3. The child mechanism, frozen

### Identity and interface

Each child is one adapter ancestry over the pinned base. Clones share published weights, not live conversations. Independent children do not share adaptive parent histories.

The compulsory interface is:

```text
ACT: <gym-specific submission>
```

Require the colon and a nonempty payload. Strip only registered leading Markdown wrappers and enclosing backticks. Execute multiple action lines in order until terminal status; record later lines as unexecuted.

`NOTE`, `PREDICT`, `RECALL`, `CONFIDENCE`, and `DONE` are ordinary text. The child cannot end its life by emitting `DONE` [A, no-end-token and less-predefined-child rulings].

### Runtime defaults

All settings below are proposed and must pass pretests [Design; inherited from B §3]:

| Setting | Default |
|---|---:|
| Generation per turn | At most **400 tokenizer tokens** |
| Sampling temperature | **0.7 dimensionless** |
| Assigned problem budget | **16 turns per problem** |
| Silent interval before nudge | **4 consecutive turns** |
| Sequence ceiling | **8,192 tokenizer tokens** |
| Input ceiling before maximum generation | **7,792 tokenizer tokens** |
| Carry-over | Last **3 child turns**, with their necessary visible outcome context |
| Collection round | **32 completed problems per clone** as the reference cadence |
| Private reflection | **4 turns**, at most **400 generated tokens per turn** |
| Waking summary | At most **8 lines** |
| Parent brief | At most **10 lines** |

Use one token-based eviction policy; do not also impose a hidden character cap. Evict complete old units while retaining the current interface and state.

The clock is information. The harness changes situations after terminal status or budget exhaustion. Suppress nudges at terminal or exhausted turns. A fully silent problem can receive at most **3 nudges** under these defaults [B §3; Derived].

### Parent-free consolidation contexts

Parenting interactions are ordinary live experience, but parent-bearing sequences are not eligible training inputs.

At registered parent-free situations:

- Start a new neutral context.
- Do not copy the brief, parent dialogue, or a mixed-origin summary.
- Permit the child to retrieve or restate its lesson from its own memory.
- Record the exact context actually presented.
- Mark any subsequently introduced prohibited source as contaminating that sequence.

Child-authored restatements remain child material, provided they were genuinely generated rather than compiler-authored or copied into targets. The compiler does not rewrite them.

The latest brief is supplied at every **parented wake**. Parent-free tests and consolidation continuations are explicitly labeled exceptions for measuring and collecting unaided use, not silent removal of an expected brief [A, repetition and parent-free-test rulings; Design]. This scheduling interpretation is listed for Rohin in section 10.

### Recurrent reasoning and self-evaluation

The minimum shipped recurrent mechanism is a neutral, checkpointed return to earlier **child-authored** reasoning within the same problem:

- The child can revisit its earlier plan and observed consequence.
- A return state presents only material it actually generated or observed.
- The parent teaches revising a belief after contradictory feedback.
- No mandatory thought marker or hidden branch merger is imposed.

Test with paired situations where an early plausible plan becomes wrong after feedback. Measure explicit return to the earlier belief, revision, and verifier-correct changed action. A generic reflection paragraph does not pass.

Parallel branching is a direction, not an implemented claim unless it passes a separate branch-provenance and child-review test. Default deferral and the resulting narrower mechanism claim are in section 10 [A, recurrent-CoT ruling; C30].

Provide voluntary free-form self-evaluation opportunities at:

| Level | Opportunity | Readout |
|---|---|---|
| Turn | After consequential feedback | Named uncertainty, checking decision, revision, action consistency |
| Episode | After terminal result or budget exhaustion | Goal completion judgment, wrong belief, next experiment |
| Lifetime | At parented round review and ungraded private time | Repeated-pattern recognition, cross-episode connection, proposed rule revision |

[Design; A, multi-level self-evaluation.]

No reply format is compulsory. Detectors record absent as absent. Human audit validates detector precision on a candidate-blind sample. Private-time readouts are research measurements, not parent evaluative inputs.

### Asynchronous rounds and one-round lag

The one-round rule is an acceptance constraint, not an aspiration [A, forever-loop ruling; C4].

At freeze, register a logical-round duration \(T_{\text{round}}\), in **seconds**, from the measured time for the reference **32-problem collection cadence** at the fastest admitted clone configuration [Design]. Wall-clock cutoffs define immutable snapshots; they do not wait for slow clones.

At each cutoff:

- Seal completed eligible events not previously claimed.
- Incomplete events enter the next snapshot.
- Record each clone’s completed problems and generated tokens.
- Train the declared snapshot one round behind.
- Complete its initial examination and make an eligible candidate available before the next cutoff.
- Clones adopt available publications at their next problem boundary.

Thus publication lag is at most **1 logical round** for an ordinary qualified snapshot [A; Design]. Adoption can additionally wait for the current problem to end, which is logged separately.

Held, rejected, or invalid candidates do not count as successful publication. Clones continue on their pinned adapter. Repeated failure to publish is visible nonconsolidation, not a hidden compliant lag.

**Backlog rule:** at most **1 unprocessed snapshot** may wait behind the active writer [Design]. A threatened deadline triggers admission reduction for the next round and available evaluator reassignment. Width reduction can reduce token demand but does not by itself lengthen the round. If measured service still cannot comply, stop admitting new training workload while clones continue parent-free operation, record the mechanism breach, and invoke section 10. Do not quietly redefine the round.

### Publication, ancestry, and recovery

One writer owns each lineage. Every candidate declares:

- Expected active parent hash.
- Publication generation.
- Snapshot and event IDs.
- Source policy.
- Sampler and incorporation state.
- Rank and optimizer state.

Publication is a compare-and-swap transaction on the expected parent and generation. If either changed through rollback or supersession, the candidate is stale: withhold it and retrain or explicitly requalify it from a valid ancestry. Atomic files alone are insufficient [C13–C14].

Maintain two separate ledgers:

1. **Ingestion ledger:** immutable event identity and storage; never rolled back.
2. **Incorporation ledger:** which event presentations belong to the active adapter ancestry; restored transactionally with adapter, sampler RNG, replay clock, counters, and optimizer state.

Rows incorporated only in a discarded branch become pending for the active ancestry without being re-ingested. Log branch-specific training already spent.

No mid-problem or mid-reflection weight swap. A tested local engine restart may cause reload downtime, but unaffected clones continue. Delayed training or parent delivery cannot trigger a global restart barrier [C5].

### Positive tolerance

For each gym, use a fixed panel and define:

\[
\tau_g=\max(q_g,\;2s_g,\;\epsilon_g),
\]

where \(q_g\) is the actual positive score quantum, \(s_g\) is the standard deviation of paired repeat differences, and \(\epsilon_g\) is a predeclared practical resolution [Design; C11].

Defaults:

- Compiler \(\epsilon_g=\) **0.010 reduction-score units** [B §3; Design].
- Reasoning \(\epsilon_g=\) **0.020 verifier-score units** [Design].

For continuous scores without an exact quantum, use the scorer’s registered reporting resolution as \(q_g\). Zero observed variance leaves a positive tolerance. Insufficient paired calibration means no score-gate qualification; collect registered reserves or withhold launch.

### Collapse brake

**Format:** **4 training-split canary problems**, each with **6 turns**; at least **3 problems** must produce an interface-acceptable submission [B §3; Design].

**Token collapse:** on paired observations both candidate and frozen reference leave unsolved, reject a candidate whose median generated-token ratio is below **0.5 dimensionless**, requiring at least **6 paired observations across 3 distinct problems** [B §3; Design].

If support is insufficient, use registered reserve observations. `COLLAPSE_NOT_ESTIMABLE` means **hold inactive**, continue serving the prior adapter, and collect support asynchronously. It is never a pass [C10].

### Patient gate and provisional confirmation

Let the fixed operational floor for gym \(g\) be \(F_g\). Define a strike strictly as:

\[
Q_g < F_g-\tau_g.
\]

Equality is not a strike. Severe deficit is:

\[
Q_g \le F_g-5\tau_g.
\]

[Design; C7–C9.]

Every ordinary passing-brake candidate can activate **provisionally**. It is reexamined as the same immutable checkpoint at the next scheduled probe. Clones continue running.

Use initial and fresh-confirmation statistics separately. **Do not average them for decisions.** Combined means are descriptive only.

| Initial result | Fresh next-probe result | Activation and resolved status |
|---|---|---|
| Integrity or brake failure | Any | Never activate; not a score strike |
| Collapse support missing | Any | Hold pending support |
| Severe deficit | Clears every floor-minus-tolerance | May activate provisionally after fresh pass; initial severe event remains logged |
| Severe deficit | Any gym still below floor-minus-tolerance | Keep inactive; one resolved strike |
| Ordinary provisional | Clears every floor-minus-tolerance | Confirm; no strike |
| Ordinary provisional | Any gym below floor-minus-tolerance | Resolve as one strike; retain provisionally only under patience |
| Any candidate | Confirmation unavailable | Not confirmed, not floor-eligible; report overdue confirmation |

[Design.]

A recovered severe candidate still requires its next scheduled confirmation before becoming floor-eligible. Fresh severe-harm checks do not replace ordinary next-probe confirmation.

After **3 consecutive resolved candidate strikes**, restore the declared rollback checkpoint [B §3; Design]. A resolving non-strike breaks the streak. Infrastructure failures and repeated probes of one candidate do not create extra strikes.

**Floor policy.** Default floor is a fixed, confirmed reference anchor, not the maximum noisy score seen so far [Design]. Raising it requires both initial and next-probe scores to exceed the existing floor by more than one tolerance, and a separate fixed-panel anchor confirmation. The historical-maximum variant is enabled only if P8 qualifies its false-strike and incompatible-floor behavior.

If gyms nominate incompatible floor owners, retain the last jointly qualified checkpoint and report incompatibility. Do not construct an imaginary adapter by combining per-gym maxima. No adaptive floor lowering based on report results is allowed.

---

## 4. The write mechanism in full

### Eligible training objects and source policies

The unit is an immutable child generation event with exact input and generated token IDs, attention and position metadata, template version, source adapter, visible source links, and subsequent environment events.

The compiler does not improve, summarize, canonicalize, or retrospectively explain thoughts.

**Audit inputs and targets separately:**

| Namespace | Eligible inputs | Eligible targets | Always excluded |
|---|---|---|---|
| Childhood | Exact neutral harness, classroom environment, eligible child context | Actual child generations | Parent-origin spans; compiler deployment; GATE/report events; foreign thoughts |
| Deployment | Exact neutral harness, deployment experience, eligible child context | Actual deployment child generations | Parent spans; GATE/report events; future outcomes |
| Authorized interface pretest | Registered syntax-only examples | Registered syntax targets | Thought content and task solutions |

[Design; A, repetition and final-test rulings; C1–C3, C15.]

Parent-bearing sequences remain quarantined unless Rohin explicitly changes the ruling. Masking parent loss is not an acceptable workaround. No direct or derived report information is allowed in either training namespace.

### Context and views

A state-to-state example contains the actual prefix and next child turn. Multi-state continuation is allowed only while the later prefix exactly matches what the child saw. Close before eviction, head replacement, adapter replacement, problem change, or any mismatch.

Use a ceiling of **8,192 tokenizer tokens per sequence**, with **70% multi-state** and **30% state-to-state processed-token budget** [B §4; Design].

No cross-example attention packing ships by default. Length grouping is allowed; attention remains isolated. Earlier memory can appear only if it was genuinely visible. Imagined outcomes remain imagined.

Every target occurrence has one owner within each view. The second view is explicit additional exposure. Identical text generated again is a new event; duplicate ingestion is an error.

### Repeats and sampling

No semantic deduplication, repeat cap, or inverse-frequency penalty [A, no-cap ruling].

Archiving is not consolidation. For each source and registered trigger class, report:

- Lived occurrences.
- Eligible occurrences.
- Unique events supervised in the surviving ancestry.
- Supervised token presentations.
- Context presentations.
- Pending fresh tokens.
- Sampling probability and realized sampling distortion.

This makes visible whether a repeated thought was actually reinforced or merely stored [C19].

### Training budget

A processed token-pass is a non-padding input token traversing training once. Targets are a subset.

The draft fixture remains valid [B §4]:

| Total per sampled pass | Quantity |
|---|---:|
| Input processing | **1,000,000 token-passes** |
| Supervised presentations | **325,000 target tokens** |
| Context processing | **675,000 token-passes** |
| Target share | **32.5% of input token-passes** |
| Context share | **67.5% of input token-passes** |

At **3 epochs**, the totals become **3,000,000 input token-passes**, **975,000 target-token presentations**, and **2,025,000 context token-passes**, requiring approximately **41.67 minutes** at the planning rate [D2; Derived].

Production uses **1 sampled pass** [B §4; Design]:

\[
B_{\text{write}}=\min(B_{\text{configured}},v_{\text{effective}}T_{\text{train}}).
\]

The outer limits are **5,000,000 token-passes** and **60 minutes per write**; at the planning rate the effective maximum is **4,320,000 token-passes per write** [D1–D2].

The actual frozen cap may be lower to satisfy one-round service. It cannot be silently lowered during childhood to conceal overload. Fresh overflow remains pending and is reported.

### Loss and trainer

Apply next-token cross-entropy only to eligible targets. Normalize the accumulated token-loss sum by total target tokens in the accumulation group. Empty-target groups fail.

Proposed settings [B §4; Design]:

| Setting | Value |
|---|---|
| Initial rank | **8 adapter dimensions** |
| LoRA alpha | **2 × rank**, dimensionless |
| Dropout | **0 probability** |
| Cumulative learning rate | **0.00005 dimensionless optimizer hyperparameter** |
| Incremental learning rate | **0.00002 dimensionless optimizer hyperparameter** |
| Optimizer | AdamW |
| Betas | **0.9** and **0.999 dimensionless** |
| Epsilon | **0.00000001 dimensionless** |
| Weight decay | **0 dimensionless** |
| Warm-up | **5% of optimizer updates** |
| Microbatch | **1 sequence** |
| Accumulation | **4 sequences per update** |
| Gradient clipping | Global Euclidean norm over all trainable adapter gradients, threshold **1 dimensionless** |
| Precision | BF16; checkpointing enabled; inference cache disabled during training |

Pin target module names, library versions, scheduler, and all RNG states in the manifest. Freeze the base-parameter allow-list.

### Cumulative preparation, incremental continuation, and replay

Begin with at least **3 published cumulative preparation writes** [B §4; Design]. “Full cumulative” means full declared coverage. If the cap prevents coverage, label it sampled reset-from-base.

Enable incremental continuation only after P9 qualification and either:

- Fresh demand exceeds **50% of the cap for 2 consecutive qualified writes**, or
- Full cumulative coverage cannot fit for **2 consecutive qualified writes**.

[B §4; Design.]

Incremental starts from the active valid ancestry, never an inactive candidate. Allocate **50% of input-token budget to fresh material** and **50% to replay** [B §4; Design]. Unused fresh capacity may transfer to replay; lack of replay leaves unused capacity, which is reported.

Implement use-and-recency replay rather than claiming a uniform/recency sampler is LFU-like [C16]:

\[
p(e)=0.5\,p_{\text{uniform}}(e)+
0.5\,\frac{(1+u_e)\,2^{-a_e/4}}{\sum_j(1+u_j)\,2^{-a_j/4}}.
\]

[Design.]

Here:

- \(u_e\) counts explicit later uses of event \(e\) through logged retrieval or child-linked carry-over in the surviving ancestry. Training presentations do not count as use.
- \(a_e\) is age in **published writes in the surviving active ancestry**.
- Recency half-life is **4 surviving-ancestry writes**.
- The uniform component preserves nonzero opportunity for unused history.

Rollback restores this clock and use state transactionally; abandoned-branch use remains in the audit record but not the active sampler. Rank expansion does not advance replay age. Log probabilities before sampling. This operationalizes, but does not claim literal equivalence to, a weight-level LFU cache [A, stop-replaying direction].

### Rank growth

Default: remain at the qualified **8-dimensional rank** this sprint unless expansion is fully pretested [A, rank-growth ruling; Design].

If enabled, grow only on an **incremental source-adapter path**, never describe larger-rank reset-from-base training as function-preserving.

Keep \(\alpha/r\) constant. Copy existing factors; initialize added \(A\) rows with the registered random initializer and added \(B\) columns to zero. Both-zero padding would preserve function but leave the new factors unable to begin ordinary gradient learning [B §4; C20].

Require update-matrix relative error below **0.000001 dimensionless**, an absolute-error check near zero, logits within the measured reload envelope, and nonzero gradients in added factors [B §4; Design].

The candidate schedule is expansion to **16 dimensions after 4 qualified incremental writes**, then to **32 dimensions after 8 qualified incremental writes** [Design]. If it does not fit or qualify before freeze, disable it; do not make outcome-driven rank choices mid-childhood.

### PC: complete conditional-memory specification

Use **3 randomized banks**, each with **64 owners**, **4 possible colors**, and **16 owners in each observation-dose stratum**: **0, 1, 4, and 16 lived observations per owner** [B §4; D9].

Totals: **192 owners**, **1,008 initial lived observations**, and **576 held-out owner-paraphrase queries per complete evaluation condition** [D9; Derived].

Train exact, stripped, and shuffled diagnostic variants per bank. These are quarantined diagnostic adapters, never childhood bootstrap data.

**Fit budget:** at most **150,000 processed token-passes per diagnostic fit**, with corpus coverage and any overflow reported [Design]. Initial fits total **9 adapters**. Only exact-context adapters undergo **8 interference writes per bank**, giving **33 fits overall** [Design; Derived]. Their nominal training cost is approximately **1.146 GPU-hours** at the planning rate, before scoring and overhead [Derived]. If the capped fit does not cover the declared corpus, the manifest must say so; no “full exposure” claim follows.

Interference writes include:

- Two cumulative continuation writes, reaching the declared cumulative preparation boundary.
- Six incremental writes using the exact production replay implementation.
- A dominant conflicting default.
- A single-observation exception for a registered trigger.
- No new exception observation during the interference gap.
- Current-context reversal queries after the gap.

[Design; C17.]

**Query manifest.** For every owner, register **3 held-out paraphrases** for the matching cue, wrong-owner cue, unrelated cue, and current-context override [B §4 paraphrases; expanded Design]. Separate generated-answer queries from teacher-forced probability queries. Register the conditional-action companion before fitting. Score base and all initial variants; score exact-context retention at entry and after every interference write.

**Definitions and gates** [B §4 thresholds, clarified Design]:

| Endpoint | Definition and acceptance |
|---|---|
| High dose | Owners with **16 lived observations** |
| Assigned-answer probability | Mean normalized probability among the **4 registered answers**; high-dose mean at least **0.80 probability units** |
| ON-minus-OFF gain | Same owner/query, trained minus frozen base; high-dose mean at least **0.30 probability units** |
| Trigger log-odds gain | Assigned-answer log odds ON minus OFF on matching cues; at least **1.5 nats** |
| Cue interaction | Trigger log-odds gain minus wrong-owner-cue gain; paired **95% interval** above **0 nats** |
| Spillover | Mean absolute ON-minus-OFF probability shift on unrelated cues; at most **0.03 probability units** |
| Override accuracy | Correct answer from explicit current context on at least **90% of override queries** |
| Override degradation | Frozen-base override accuracy minus trained override accuracy; at most **0.03 proportion units** |
| Retained gain | Post-interference ON-minus-OFF matching-cue gain divided by initial positive gain; at least **75%** after **2 interference writes** |
| Conditional action | Verifier-correct action rate at least **80%**, improvement over frozen base at least **20 percentage points** |
| Delayed action penalty | Initial post-fit action accuracy minus post-interference accuracy; at most **10 percentage points** |

For the rare-exception stratum, additionally require at least **70% generated-answer accuracy** after the full **8-write gap**, no more than **10 percentage points** below its initial post-fit accuracy, and at least **90% current-context reversal accuracy** [Design]. Report the frequent default and rare exception separately; a pooled success cannot hide exception loss.

Apply gates **per bank**. Use owner-cluster paired bootstrap intervals with **10,000 resamples** and **95% coverage** [Design]. Owners retain all paraphrases and checkpoint observations when resampled. Missing queries, nonpositive initial gain for a retention ratio, or insufficient coverage means inconclusive/fail qualification—not deletion.

Report unnormalized candidate probability mass, generated accuracy, and all cue terms. PC qualifies only when the measured scoring and generation schedule fits its reserved cost.

### Invariants on every write

Require exact target identity, exact visible prefixes, valid input provenance, valid target provenance, attention isolation, no future outcomes, no fabricated branch joins, no silent truncation, unique ingestion, reconciled exposure counts, valid ancestry, frozen-base identity, declared sampler state, successful reload, and transactional publication.

Any failure withholds publication. A hand audit is a build check, not the enforcement mechanism.

---

## 5. Parenting

### Curriculum and values

Parenting is a curriculum of trait-teaching environments with a critic that never gives answers [A, parenting definition].

Start with persistence through informative changing attempts and recognition of goal completion. Add verification, calibration, contrast, re-planning, layered goals, free thought, recurrent review, and deciding whether to think more or act.

Select a small reasoning-gym band only after confirming that feedback permits useful revision. Mere difficulty without informative feedback does not teach persistence.

The required cross-disciplinary survey must map each proposed value to:

- A testable agent behavior.
- A qualified gym affordance.
- A parent intervention.
- A failure mode.
- An instrument.
- An evidence limitation.

[A, late survey ruling; Design.]

### Rooms and central parents

Each room has Astra proposer and verifier roles. Their agreement is not independent correctness evidence because they share a model family.

The proposer uses permitted public evidence, the standing lesson, frontier estimate, and scaffold level. The verifier checks leakage, unsupported claims, detector coaching, private-content use, and consistency.

Fable and Codex may research and advise without asking permission, but cannot change the frozen writer, endpoints, or split policy [A, central-parent research ruling]. Advice never blocks a clone or write.

Independent childhoods use separate adaptive parental ledgers. Shared outcome-derived teaching changes would couple them and must be prevented or disclosed.

### Briefs and dialogue

Each brief has at most **10 lines**, at most **2 questions**, and ends with a request for an own-words restatement at the next parented opening [A, two-channel and repetition rulings; B §5].

Dialogue allows at most **3 exchanges per boundary** [A, two-channel ruling]. Keep the same core lesson; sharpen rather than switch.

At least **half of substantive lines** in a non-birth brief must link to public child events [B §5; Design]. Birth instructions are explicitly evidence-free.

A useful brief names the goal, observed attempt, consequence, conditional lesson, contrasting situation, and a process experiment—not the solving move.

### Fading

Use the scaffold ladder from B §5: model a thinking move, identify a missing link, give a situational cue, ask a non-leading question, then no contingent cue.

A development window contains **16 parent-free problems** [Design]. Advance one scaffold level only after **2 consecutive windows** with:

- At least **75% correct conditional application** on trigger cases.
- At least **75% appropriate restraint** on no-trigger cases.
- No decrease greater than one calibrated tolerance in verifier score.
- At least one changed family or surface form across the windows.

[Design; C44.]

A score dip alone does not increase help. Regression in conditional use can move one level back, with public evidence logged. Lessons remain stable unless the registered criterion or explicit public failure supports revision.

At the no-cue level, remove pending briefs, dialogue, parental summaries, and inherited carry-over. A silent parent with yesterday’s brief still visible is not absent.

### Repetition measurements

Measure visible-brief rehearsal, unaided retrieval, conditional use, and restraint separately. Check after **1, 2, 4, and 8 activated writes**, where reached [B §5; Design].

Rohin’s falsifier remains: child-authored rehearsal within **1–2 sleeps**, then rarer ritual over at least **4 subsequent windows** than controls [A, repetition ruling]. If the required matched control windows are not run, say this falsifier was not tested. Do not substitute main-lineage improvement for its control clause.

### Private reflection and information access

Private reflection is readable but cannot supply evidence for:

- Frontier ratings.
- Scaffold changes.
- Curriculum corrections.
- Evaluation of the child.
- Corrective sentences.

Those decisions require public-event links. Store private content separately from the evaluative parent workspace; provide an explicitly read-only private-view tool whose output cannot be quoted into decision records [Design; C28].

Residual limitation: a model that has read private content may still be influenced by it. Therefore use separate review contexts for private reading and evaluative decisions. Do not claim psychological non-influence from a lexical scan.

Parents may see classroom training scores, teaching-facing development aggregates, and designated GATE dispositions. They may not see report identities, report scores, report-derived summaries, or final-gym feedback during childhood [A, reward-hacking gate and score directions].

All transitive parent inputs are logged. Development tests that later inform teaching are development evidence, not sealed confirmation.

---

## 6. The test protocol and statistics

### Source identity and disjointness

A compiler source group is the upstream project/repository, release or commit lineage, and benchmark-generation lineage—not the program identifier [Design; C26]. Generated variants inherit their parent source group.

Before split assignment:

- Hash normalized source and intermediate representation.
- Group exact duplicates and registered near-duplicates.
- Keep all transformations of one source in the same group.
- Audit overlap against historical, operational, deployment-experience, and report manifests.

Near-duplicate thresholds and normalization code are frozen before candidate evaluation. Source uncertainty excludes a program from the sealed report panel.

Use separate manifests for historical diagnostics, operational engineering/GATE, deployment experience, and sealed report. No source group crosses these boundaries.

The report panel contains **12 programs from 12 source groups**, with **2 repetitions per checkpoint** [D4; Design]. Select candidate-blind. Require reference-search advantage of at least **0.10 reduction-score units** over the best preregistered fixed recipe, with search budget recorded [B §6; Design].

If no fresh source-disjoint panel qualifies, results are exploratory. Confirmatory success language is disabled even if numerical thresholds are exceeded [C40].

### Deployment initialization

Both agents receive the same neutral scaffold, budgets, scorer, writer code, source policy, and resource caps.

| State | Developed agent | Untaught comparator |
|---|---|---|
| Base | Pinned frozen base | Same base |
| Initial weights | Final childhood adapter | Identity adapter |
| Rank | Final qualified rank | Same rank, identity function |
| Deployment phase | Incremental only if P9 qualified; otherwise registered reset policy | Same phase and policy |
| Deployment write counter | Reset to entry | Reset to entry |
| Rank-growth clock | Disabled during finals by default | Disabled |
| Learning rate | Registered deployment phase value | Same value |
| Optimizer | Fresh state | Fresh state |
| Text summary/retrieval | Empty | Empty |
| Pending childhood writes | Excluded | None |
| Replay source | Frozen eligible childhood archive plus later deployment | Own deployment history |
| Replay-age clock | Childhood event ages preserved in immutable archive; new deployment clock starts at entry | New deployment clock starts at entry |
| Gate floor | Separately confirmed entry operational reference | Separately confirmed entry operational reference |
| Rollback anchor | Entry adapter plus complete state | Entry identity adapter plus complete state |
| Sampler RNG | Registered deployment seed | Paired registered seed |
| Input source policy | Deployment namespace | Same policy |

[Design; C21.]

The history-dependent differences are intentional parts of the developmental bundle. Same caps do not imply equal training exposure. Report optimizer updates, target tokens, replay token-passes, total token-passes, writer time, and activated updates per agent [C22].

### Frozen and continual report contexts

The **primary report curve measures weights alone** [Design; C24].

Every report fork, at every checkpoint:

- Loads only the immutable checkpoint and neutral interface.
- Starts each problem fresh.
- Has no childhood or deployment summary, retrieval, carry-over, parent brief, pending message, or optimizer state.
- Permits within-problem interaction only.
- Never returns report events to a live agent, writer, gate, or parent.

Frozen transfer uses the same policy at entry. Entry reports may be reused only when checkpoint, scaffold, seeds, and policy are identical.

Live continual deployment may maintain its own newly generated text memory under the same policy in both agents. That live system is distinct from the weight-only report estimand.

### Horizon and final write closure

Run **512 deployment problems per agent**. Probe at entry and every **64 problems**, giving **9 checkpoint ages** [B §6].

At each checkpoint age, snapshot the adapter actually active at completion of that problem. Do not pause the agent awaiting a write to improve its report checkpoint.

At the final problem:

- Seal the primary endpoint immediately from the active adapter.
- Stop adding deployment experience to the primary trajectory.
- Allow already released work to finish only for a separately labeled post-horizon diagnostic.
- Do not replace the primary endpoint with a drained checkpoint.

[Design; D5.]

Report unactivated, held, and in-flight writes at the horizon. There is no unbounded final drain.

### Score endpoints

For each comparison pair \(i\), frozen transfer is the equal-source mean difference:

\[
F_i=\operatorname{mean}_{s,r}(Y_{D,i,s,r}-Y_{U,i,s,r}).
\]

Proposed practical margin: **+0.020 reduction-score units**, with a conditional interval excluding **0 reduction-score units** [B §6; Design].

Continual improvement is the entry-adjusted, horizon-normalized area:

\[
C_i=\frac{1}{H}\int_0^H
\big([Q_D(t)-Q_D(0)]-[Q_U(t)-Q_U(0)]\big)\,dt,
\]

with \(H=\) **512 deployment problems**, using the trapezoidal rule [B §6].

Its unit is **reduction-score units**. Proposed success requires at least **+0.020 reduction-score units**, a conditional interval excluding zero, and terminal taught score not below its comparator [B §6; Design].

Report absolute curves and normalized absolute area as well. Any unnormalized area must use **reduction-score units × deployment problems** [C41].

### Efficiency headline and falsifier

For each report program, freeze a target before childhood outcomes: best preregistered fixed-recipe score plus **0.05 reduction-score units**, provided the candidate-blind reference search exceeds that target [Design]. Otherwise replace the source before sealing.

Measure:

- All generated child tokens through the first achieved target.
- All attempted action submissions, including invalid ones.
- Accepted actions separately.
- Completion fraction.
- Full budgets and censored failures.

The maximum generation budget is **6,400 tokenizer tokens per report problem**, derived from **16 turns × 400 tokens per turn** [Design; Derived]. A never-solved problem receives this cap in the restricted token-to-target endpoint and remains explicitly censored.

Aggregate within source, then equally across sources. Do not pool easy and hard tasks by their episode count.

**Named efficiency falsifier:** by **512 deployment problems**, the developed checkpoint’s restricted mean tokens-to-target must be at least **10% lower** than its comparator’s, with a paired conditional interval excluding no benefit and completion fraction not lower [Design; A, efficiency scoping]. Otherwise the abstract carries no positive efficiency sentence.

Also report the entry-adjusted change in restricted tokens-to-target. A persistent entry advantage is not evidence of faster improvement.

This restores efficiency as a preregistered headline candidate; score endpoints do not silently supersede Rohin’s instruction [C36–C37].

### Text memory

Ship a candidate-blind policy, not an outcome-selected brief.

For each developed childhood snapshot, cross adapter off/on with text absent/present. The frozen base and adapter cells receive the **same child-owned eligible snapshot** [Design].

The capable text condition:

- Uses only the parent-free eligible childhood archive.
- Uses a frozen lexical retrieval implementation over child text and visible environment context.
- Retrieves at most **4 chunks**, totaling at most **2,048 tokenizer tokens**.
- Uses no outcome-trained summarizer or report-aware selection.
- Fits within the same total context ceiling.

[Design; C25.]

The routine-only diagnostic selects the most frequent executed action sequence in the eligible childhood archive, with lexicographic tie-breaking, before report outcomes. It is diagnostic, not a capable memory policy.

A six-condition comparison costs **144 report episodes**, approximately **6.545 GPU-hours per childhood snapshot** [D18]. Book retrieval build and validation separately. If only a brief proxy is ready, name it a brief-memory proxy and remove weight-superiority claims.

For any later checkpoint comparison, freeze the snapshot cutoff and specify whether childhood and deployment text are included. Do not silently change memory eligibility across cells.

### Statistics and claim limits

The independent developmental unit is the childhood. Clones, programs, writes, and checkpoints do not create additional independent children.

Use paired source-group bootstrap resampling, preserving complete trajectories across agents and ages, with **10,000 resamples** and **95% conditional intervals** [B §6; Design]. Show all **12 source groups** individually [D4; Design].

Intervals describe source sampling conditional on observed histories, not future-child variation.

Report each comparison pair before averages. Under an **independent, sign-symmetric null**, two positive childhood signs have probability **0.25**; exchangeability alone is insufficient for that statement [C42; Derived].

The joint developed-system success statement requires frozen transfer, continual improvement, and any claimed efficiency endpoint to pass their registered rules. A failed threshold is not proof of no effect. An exposed report panel permits descriptive results only.

---

## 7. Two children: allocation by day, migration, what drops

### Available capacity

There are **16 A40 GPUs across 2 isolated nodes** initially and **8 GPUs** after the temporary node ends [A, Constraints]. Rental capacity is **0 GPUs** until booked, accessible, and tested [D14].

At the planning pace, a pooled round arrives approximately every **1.455 hours** [D3]. A serial full-cap writer plus ordinary gate and turn-scaled format canary costs approximately:

- **1.000 GPU-hour** training.
- **1.091 GPU-hours** ordinary gate.
- **0.068 GPU-hours** format canary.
- **2.159 GPU-hours total**, before overhead.

[D3.]

A **1.25-times service margin** requires completion within approximately **1.164 hours** [D3]. Gate and canary alone nearly consume that allowance. **Reducing clone width alone does not solve this cadence problem.**

Separate training and evaluation service. Next-probe confirmation is also real evaluator work. The proposed **2 clone GPUs + 1 writer GPU + 1 evaluator GPU per child** is a candidate allocation, not accepted capacity; confirmation load may require more evaluator service [D3; C7, C34].

A production configuration qualifies only if measured end-to-end service and its event schedule satisfy the one-round rule under ordinary and confirmation load. Otherwise use a smaller pre-frozen write cap, more evaluator capacity, or fewer simultaneous comparison pairs. Sustained lag is not an authorized workaround.

### Finals accounting

With **12 report programs**, each agent has:

| Work | Count or cost |
|---|---:|
| Deployment | **512 problems** |
| Reports | **216 episodes** |
| Total inference | **728 executions** |
| Planning inference cost | **33.091 GPU-hours** |

[D4.]

Across **4 agents**, inference costs approximately **132.364 GPU-hours** [D4].

If entry is reused from frozen transfer, the continual phase has **704 executions per agent**, or **32.000 inference GPU-hours per agent**. Entry reports cost **4.364 GPU-hours across 4 agents** [D4].

An optimistic full-cap budget with **16 candidate writes per agent** is:

| Component across all agents | Cost |
|---|---:|
| Deployment and all report inference | **132.364 GPU-hours** |
| Training | **64.000 GPU-hours** |
| Ordinary gates | **69.818 GPU-hours** |
| Format canaries | **4.364 GPU-hours**, turn-scaled estimate |
| Subtotal | **270.545 GPU-hours** |
| One fresh confirmation per candidate | **69.818 additional GPU-hours** |
| Subtotal with confirmations | **340.364 GPU-hours** |

[D5.]

The proposed **48-hour × 8-GPU** reservation provides **384 GPU-hours** [D5]. The remainder does not automatically cover compilation, reload, reserves, severe rechecks, failures, or serial dependencies.

Training at the effective cap is at most **69,120,000 token-passes per agent**, or **276,480,000 token-passes across 4 agents** [D5]. Actual activated exposure can be lower, especially because the final released write does not alter the primary horizon.

P7 must prove the event schedule. Aggregate GPU-hours are insufficient.

### Calendar

The conditional protected path is [B §2; D14]:

| Block | Reservation |
|---|---:|
| Active childhood | **24 hours per child** |
| Migration | **6 hours** |
| Frozen comparison and initialization | **8 hours** |
| Continual comparison | **48 hours** |
| Recovery | **12 hours** |
| Export and analysis | **12 hours** |
| Total critical path | **110 hours** |

A launch at **2026-09-13 at 06:00 UTC** implies:

- Temporary-node work stops **2026-09-13 at 12:00 UTC**.
- Migration is received, checksum-verified, reload-tested, and resumable by **2026-09-13 at 18:00 UTC**.
- Remaining childhood completes **2026-09-14 at 12:00 UTC**.
- Frozen/init ends **2026-09-14 at 20:00 UTC**.
- Continual block ends **2026-09-16 at 20:00 UTC**.
- Recovery ends **2026-09-17 at 08:00 UTC**.
- Export ends **2026-09-17 at 20:00 UTC**.

[D14.]

This has **0 hours of unallocated slack**. The preferred launch at **2026-09-12 at 12:00 UTC** would provide **18 hours of slack**, but the current engineering estimate does not support committing to it [D14–D15].

No essential work relies on the temporary node during **2026-09-14**.

### Migration and preemption

A complete bundle includes weights, active and rollback pointers, required optimizer state, RNG states, curriculum state, pending events, ingestion and incorporation ledgers, sampler state, parent records, briefs, code/environment hashes, and source ledgers. No credentials.

Take recoverable snapshots every **6 hours** [B §7; Design]. Destination verification, not source tarball completion, defines success.

Current jobs are unverified. Fable must first publish the inventory. Preempt unmatched or unbounded continuations before near-complete unique controls, after preserving evidence. Log censoring.

### What drops

Protect one complete comparison pair first. The second independent childhood and comparison pair remain preferred but conditional on measured capacity and remaining engineering work.

Without rental, cut continued parenting during finals, extra gyms, excess width, and the **1,024-problem deployment extension** [B §7].

Dropping a comparison pair frees resources; it does not halve the surviving pair’s serial learning horizon [D19]. Do not drop only the untaught comparator.

---

## 8. Build list with hours/owners/cut lines

### Staffing reality

The inherited estimate is **52 engineer-hours**: **10 Fable-assigned hours**, **25 Codex-assigned hours**, and **17 Astra-assigned hours** [B §8; D15].

Unless another independent worker is confirmed, treat Fable/Codex work as **35 serial human work-hours**, not parallel human capacity [D15]. Astra effort is not review-free and is not automatically elapsed time.

Repository inspection must replace these estimates with remaining work.

### Dependency and ownership ledger

| Deliverable | Responsible role | Dependency | Remaining estimate status |
|---|---|---|---|
| Source policy, manifests, historical inventory | Human engineer, Fable review | None | Unverified; inspect first |
| Runtime interface and exact renderer | Human-owned interface; Astra implementation | Source schema | Included in inherited **6-hour** runtime estimate, not revalidated |
| Pilot traces and token reconciliation | Human engineer; Astra fixtures | Renderer | Missing from prior estimate; unpriced |
| Compiler and masks | Human engineer/Codex | Pilot schema | Inherited **8 engineer-hours**, unverified |
| Trainer and save/reload | Human engineer/Codex | Compiler | Inherited **5 engineer-hours**, unverified |
| Gate and publication | Human engineer/Codex | Trainer/state schema | Inherited **6 engineer-hours**, unverified |
| Parent daemon and access fixtures | Astra; human review | Source policy | Inherited **4 engineer-hours**, unverified |
| Asynchronous coordinator and recovery | Astra; human integration | Publication interface | Inherited **7 engineer-hours**, unverified |
| Panel construction and search | Human engineer; Astra runner | Source audit/scorer | Unpriced |
| Deployment harness and report isolation | Human engineer/Codex | Gate and loader | Inherited **6 engineer-hours**, unverified |
| Car suite and writer analyses | Fable analysis; Astra runners | Trainer | Inherited **4 engineer-hours**, scoring additions unpriced |
| Relay packaging and destination restore | Human engineer | Complete state schema | Unpriced |
| Export and acceptance audit | Human engineer; Astra independent checks | All artifacts | Inherited **4 engineer-hours**, additions unpriced |

[B §8; D15–D16; Design responsibility.]

For each row, record actual start, finish, owner availability, blocked-on artifact, and remaining estimate. The launch calculation uses that dependency graph, not the sum of optimistic reservations.

### Cut lines

**Runtime cut:** exact recorded contexts and a usable neutral action path. Permits pilot collection only.

**Writer cut:** compile–train–examine–reload correctness, useful conditional action effect, source checks, and measured cost. Permits mechanism comparisons only.

**System cut:** production-load asynchronous soak, parent wall, migration, paired deployment rehearsal, and signed numerical registry. Permits childhood launch.

Cut now unless already nearly complete:

- Rank growth.
- Optional preparation variants beyond the simplest qualified preparation.
- Extra gyms.
- Parallel branching beyond the minimal recurrent-return mechanism.
- Optional marker instruments.
- Attention-packing optimization.

[A’s core requirements remain; D15; Design.]

Do not cut interface correctness, provenance, masks, ancestry, evaluator isolation, or the comparator.

Astra runs end-to-end checks using an allow-list. Fable and Astra debate concrete failures. Codex reviews the executable freeze. The report to Rohin contains unresolved decisions, not another broad survey.

---

## 9. Falsifiers, stop rules, preconditions, abstract numbers

### Nonnegotiable launch conditions

No childhood launches without:

- Qualified baseline and classroom headroom.
- Environment-owned scoring and complete event accounting.
- Exact parent-free input and child-target provenance.
- Beneficial conditional-action writer qualification.
- Costed PC manifest and scoring benchmark.
- Collapse support and executable patient gate.
- Tested ordinary provisional confirmation.
- One-round asynchronous service at admitted load.
- Transactional rollback and stale-candidate rejection.
- Parent/report access wall, including derived data.
- Verified migration and recovery.
- Event-level complete-comparison schedule.
- Frozen endpoints, source manifests, and numerical settings.

Failure is a mechanism or protocol result, not proof that developmental learning is impossible.

### Falsifiers and actions

| Failure | Rule | Action |
|---|---|---|
| Global rather than conditional memory | PC specificity, override, or exception gate fails | No guide-memory claim; no release on this mechanism |
| Likelihood gain without useful action gain | P1 beneficial-action threshold fails | Storage result only |
| Rehearsal is visible-brief echo | Unaided use or restraint fails | Report supported compliance |
| Ordinary decline persists | **3 consecutive resolved strikes**, each strictly below floor minus tolerance | Transactional rollback |
| Severe initial decline | Deficit at least **5 tolerance widths** | Hold and fresh-check |
| Collapse support absent | Registered reserves insufficient | Hold; continue prior adapter |
| Prohibited source enters input or target | **1 prohibited event** | Quarantine affected artifacts and descendants |
| Wrong ancestry at publication | Expected-parent check fails | Withhold stale candidate |
| One-round service breached | Missed deadline or excessive pending snapshot | Apply admission response; record breach; no silent mechanism redefinition |
| Frozen transfer fails | Margin below **+0.020 reduction-score units** or interval includes zero | No positive frozen-transfer claim |
| Continual improvement fails | Margin below **+0.020 reduction-score units**, interval includes zero, or terminal score lower | No positive greater-improvement claim |
| Efficiency fails | Less than **10% token-to-target reduction**, interval includes no benefit, or completion lower | No positive efficiency sentence |
| Horizon incomplete | Either comparator misses **512 deployment problems** | Matched partial curves, labeled incomplete |
| Report exposed | Operational or leaked report source | Exploratory descriptions only |

[Design; thresholds from B §6 and sections 2–6 above.]

Sealed report harm is reported, not used to steer the trajectory. The inherited harm flag is a deficit below **−0.030 reduction-score units** in both repetitions at one checkpoint or at consecutive checkpoints [B §9; Design]. It cannot become an operational gate through a summary channel.

### Abstract-ready export

Export before access ends:

| Field | Unit |
|---|---|
| Developmental replication | Independent childhood count |
| Width | Clone count and active GPU count |
| Childhood exposure | Problems, generated tokens, active hours |
| Consolidation | Candidate, activated, confirmed, held, rejected, rollback, and stale counts |
| Training | Unique events, target-token presentations, replay/fresh/context token-passes, optimizer updates |
| Backlog | Pending events and token-passes |
| Provenance | Programs, source groups, prohibited accesses and spans |
| Frozen transfer | Reduction-score units with conditional intervals |
| Continual improvement | Normalized area in reduction-score units |
| Efficiency | Generated tokens and attempted actions to target; completion fraction; censored count |
| Memory | Nats, probability shifts, generated accuracy, rare-exception retention |
| Resources | Inference/evaluator/writer GPU-hours; API calls and tokens; lag and downtime |
| Completion | Achieved problem horizon and unactivated final work |
| Text baseline | Exact policy, eligible snapshot, token budget, effects |
| Failures | Missing, interrupted, leaked, incompatible-floor, and incomplete cases |

[Design; B §9 expanded by C22, C37.]

### Allowed language

If the sealed endpoints pass:

> “The developed system outperformed its specified same-cap untaught comparator under the registered tests. The treatment included childhood experience, parenting, consolidation, and inherited replay; realized training exposure differed as reported.”

Use measured effects and units, not “parenting caused” language.

If only frozen transfer passes, report transferred behavior without greater continual improvement. If only absolute curves improve, report a retained starting advantage. If markers rise without behavior, say so. If text matches weights, name the exact text policy. If independent childhoods disagree, report inconsistent replication.

For exposed or operational panels, replace “passed” and “confirmed” with descriptive exploratory effects. Numerical thresholds do not restore a sealed-test claim.

The abstract must name the base, developmental bundle, comparator, task family, completed childhood count, horizon, score effects, efficiency falsifier outcome, and source status.

---

## 10. Open decisions for Rohin with defaults, ranked risks, what to cut first

### Decisions where rulings and feasibility meet

| Decision | Compliant default | Escalation or consequence |
|---|---|---|
| Parent text in training input | **Prohibited**; collect separate parent-free exact-context continuations | Only Rohin may authorize parent-bearing input. Masked loss is not an exception |
| Brief at every wake versus parent-free collection | Brief at every parented wake; explicitly scheduled parent-free tests/continuations | Ratify this scheduling interpretation; otherwise no eligible mixed-context shortcut |
| One-round lag versus evaluator cost | Preserve one-round constraint; separate service, reduce pre-frozen cap, or add capacity | Sustained longer lag requires an explicit mechanism change; not a default |
| Provisional next-probe confirmation versus capacity | Keep confirmation and account for it | Cut simultaneous pairs or width before dropping confirmation |
| Number of childhoods | Prefer **2 independent childhoods**; preserve one complete comparison pair if necessary [A; Design] | Report incomplete replication, not population evidence |
| Rental | Assume **0 additional GPUs** until booked and tested [D14] | Rental first protects evaluation/recovery, not scope expansion |
| Initial preparation | Simplest qualified ordinary-parenting preparation | Authorized syntax-only variant may be tested; foreign thought content needs a new exception |
| Rank growth | Qualified **8-dimensional rank**, growth disabled unless pretested [A; Design] | No deadline-driven untested expansion |
| Incremental write | Enable only after exact P9 qualification | Otherwise price cumulative coverage and accept a smaller run |
| LFU-like replay | Tested use-and-recency sampler with uniform support | If it fails, any replacement is named and requalified, not called LFU-like |
| Recurrent reasoning | Ship tested return-and-revise states | Parallel thinking streams are deferred if not built; narrow the claim explicitly |
| Repetition’s comparative falsifier | Run only if matched follow-up windows fit | Otherwise mark not tested; do not claim durable prevention |
| Capable text memory | Frozen retrieval policy if qualified | Brief-only proxy permits no weight-superiority claim |
| Report panel unavailable | Exploratory operational results only | No confirmatory success sentence |
| Efficiency headline | Retain registered token-to-target falsifier | Score-based replacement requires Rohin’s explicit superseding decision |
| Latest launch missed | Recompute one complete comparison pair from measured dependencies | If it cannot fit, ship mechanism/frozen evidence and label continual test incomplete |
| Maximum historical floor | Conservative confirmed anchor by default | Enable maximum-floor variant only after full-policy qualification |

These defaults preserve rulings rather than interpret inconvenience as permission.

### Ranked risks

**Highest — prohibited or wrong conditioning.** Parent text, future outcomes, omitted cues, or derived report information can invalidate an otherwise fluent write. Input and target provenance are separate checks.

**Next — no useful behavioral write.** Storage and action movement can be strong while conditional correctness fails. More clones or rank cannot replace P1 and PC.

**Next — evaluator and writer service cannot meet the round.** The serial writer/exam design is already inconsistent with the planning cadence. Separate service and prove the actual schedule.

**Next — engineering critical path misses the deadline.** The inherited work requires substantial serial human effort. Missing tasks and reviews are not free. Inspect the repository and cut optional scope now.

**Next — migration loses active state.** Adapter files alone are insufficient. Destination-side resumability is the acceptance condition.

**Next — rollback publishes the wrong ancestry or loses incorporation history.** Compare-and-swap publication and transactional state restoration must survive fault injection.

**Next — rare useful rules disappear under replay.** High-dose retention does not establish exception retention. Test dominant defaults, long gaps, and reversals across the phase switch.

**Next — comparison ambiguity.** Same caps can produce unequal training, replay, lag, and optimizer exposure. Report those differences rather than imply exposure matching.

**Next — parents teach the metric or evaluate private thought.** Enforce transitive labels and public-evidence-only evaluative decisions. Separate private-reading contexts.

**Next — narrow compiler panels reward a recipe.** Source disjointness and headroom are necessary but insufficient. Show per-source choices and conditional behavior.

**Next — childhoods become coupled.** Shared adaptive parental lessons reduce developmental independence. Prevent or disclose this.

**Last — API outage.** Reuse verified briefs and continue operation. Unsafe advice or blocked clones are worse than a temporarily absent parent.

### Cut order

Cut extra gyms, packing optimization, rank-growth work, optional preparation variants, parallel branching beyond the qualified recurrent mechanism, optional instruments, excess clone width, continued childhood during finals, and extended horizons.

Then cut the second complete comparison pair if required.

Do not cut parent-input exclusion, exact prefixes, target masks, source splits, actual adapter identity, confirmation, collapse support, rollback correctness, verified migration, the frozen condition, or the untaught comparator to preserve a larger-looking run.

The shipping evidence chain is:

> qualified mechanism → recorded childhood → immutable checkpoint → parent-free frozen comparison → same-cap continual comparison → source-level results, realized exposure, and failure history.

If that chain breaks, identify the broken link. If it completes, make the narrow developed-system claim it supports. The deadline rewards interpretable evidence, not the largest volume of generated thought.