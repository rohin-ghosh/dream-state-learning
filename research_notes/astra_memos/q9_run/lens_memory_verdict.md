## Verdict

**The completed car test rejects clean, out-of-context owner–colour memory for the tested writes. It does not establish that this child cannot store retrievable facts under any write-and-read interface. Cell F is a fair final mechanism test—but not yet a demonstration that sleep can preserve the child’s own perceptions.**

The operational decision should be:

- **Keep the memory block provisional until F reports.** No F binding result is available in the supplied record; completion rescoring and F fits were still running or queued. **[SEQ-035]**
- **If F passes, call it canonical-cue associative memory.** Require an additional bridge test before claiming usable experiential memory.
- **If F fails a valid high-exposure test using the intended memory-block configuration, stop treating that block as the factual store for this sprint. Use retrieved text as the store and the behaviour adapter as the learned policy.** This is a project decision, not a claim that weight memory is impossible.

**Source boundary:** I audited the pasted notebook, not the underlying code, raw evaluations or report files. No attachment letters were supplied. I cite SEQ sections; the detailed F implementation correction appears in an **unnumbered “Cell family F … implemented” section**, while its execution status appears in **SEQ-035**. I will not invent a SEQ attribution for that specification.

## What the car test actually establishes

### Design: good controls, narrower construct than “memory”

The initial design uses **64 nonce owners**, fact doses of **0, 1, 4 and 16 occurrences**, and exposure distributed across **4 sleeps**. Each dose has **48 paraphrase cues**, comprising **3 cue forms** across **16 owners**. Adapter-OFF comparisons, similar-ID controls, unrelated cues, in-context observations, repainting and scrambled bindings give complementary ways to distinguish factual retrieval from generic colour bias and context copying. **[SEQ-025]**

The writer contrasts are informative:

- **A versus B:** removing versus preserving repeated occurrences in bare short pieces.
- **C versus D:** removing versus preserving occurrences with antecedent context.
- **D versus Dshuf:** learning actual bindings versus learning the representation or reading task regardless of bindings. **[SEQ-025]**

However, “antecedent versus short piece” also changes the rendered training interface. The antecedent examples provide an answer-bearing observation and a target that can copy it. Thus the experiment identifies a **representation/interface package**, not context length alone. **[SEQ-025]**

The final negative is supported across **3 banks**, not just the first bank. But it remains a negative for these writers, cues, doses and training configurations. **[SEQ-034]**

### Metrics: owner specificity is necessary, but the contrast can mislead

For a planted colour \(c\), let \(g(q,c)\) denote its adapter-ON minus adapter-OFF log-odds gain at cue \(q\). Then:

\[
I_d = \mathbb{E}_{\text{owners}}\left[g(q_{\text{owner}},c)-g(q_{\text{similar ID}},c)\right].
\]

The frame metric substitutes canonical completion prefixes:

\[
I_{d,\mathrm{frame}}
= \mathbb{E}_{\text{owners}}\left[g(f_{\text{owner}},c)-g(f_{\text{similar ID}},c)\right].
\]

The original metric uses paired bootstrap uncertainty over owners. **[SEQ-025; unnumbered F implementation section]**

Three qualifications matter.

**First, the subtraction can manufacture an apparent owner advantage.** Pooled C reached \(I_d=0.590\) **log-odds units**, with a **95% confidence interval** of **−0.25 to 1.37 log-odds units**, while owner-cue probability fell by **0.038 probability units**. The notebook attributes the apparent advantage to the similar-ID term falling further. Therefore every report must show the owner and similar-ID terms separately. **[SEQ-026]**

**Second, conditional colour probability is not usable completion probability.** \(P\) is normalized among **4 colour words**; it can improve while the model becomes less likely to emit any colour. Rank-**32** B reached conditional \(P=0.425\), but total colour mass was only **0.044 probability mass**, with spill of **0.28 reported probability-change units**. That is not a clean retrieval success. **[SEQ-025; SEQ-033]**

**Third, text fit does not prove relational storage.** The antecedent adapters’ approximately **4.4 nats** of text-fit improvement demonstrate learning of training strings or conditional continuations. They do **not** independently establish that an owner-indexed fact exists internally but is inaccessible. “Text memorization without demonstrated relational retrieval” is safer than “the fact is stored but cannot be extracted.” **[SEQ-034]**

**Unverified:** the exact log-odds implementation, probability clipping, candidate tokenization, multi-token scoring, spill aggregation and frame-bootstrap implementation. These require code and raw-output inspection.

### Gates: a conjunction, not a points competition

The spill gate is reported as **≤0.03 probability-change units**. Initial spills were **0.20–0.25 reported probability-change units**; the completed summary gives B spill of **0.18–0.28 reported probability-change units**. Those are clear failures of specificity, not near misses. **[SEQ-025; SEQ-034]**

The correct interpretation requires all of the following together:

- positive owner-specific retrieval;
- genuine owner-cue improvement;
- acceptable unrelated-cue spill;
- non-collapsed answer mass and usable completions;
- a dose signal;
- intact action behaviour.

A favourable confidence interval alone is insufficient. At adapter strength **λ=0.5 dimensionless**, B had \(I_d=0.27\) **log-odds units**, with a **95% confidence interval** of **0.06–0.55 log-odds units**, but owner \(\Delta P\) was **0.000 probability units** and spill was **0.11 reported probability-change units**. This is a relative statistical signal, not clean factual retrieval. **[SEQ-033]**

**Unverified:** the full gate definitions and thresholds. The F implementation note explicitly leaves a spill-scale ambiguity and a gate-label collision unresolved. Freeze the actual formulas before interpreting F; do not compare a probability-change spill statistic with a log-odds threshold.

Also distinguish **car-test evidence gates** from the **deployment collapse gate**. The latter demonstrably does not guarantee safety: a gated life ended with a harmful committed adapter. **[SEQ-035]**

### The fallback finalist rule is invalid as scientific selection

Choosing the largest \(I_d\) when every cell fails spill selected B initially, then flipped to C as another bank arrived. C’s apparent advantage came from the control term, not improved owner retrieval. **[SEQ-025; SEQ-026]**

**Replace “fallback finalist” with “diagnostic follow-up.”** No qualifying cell means no winner. Follow up B because it preserves occurrences and has a surface signal; follow up D because it represents the antecedent write. The separate follow-ups were sensible, but they do not turn the fallback winner into a successful memory cell.

### Rank and strength: tested rescues failed; capacity is not globally ruled out

Increasing adapter rank from **8 to 32 dimensions** did not rescue clean extraction in the reported A, B, C or D follow-ups. D’s higher-rank fit retained strong text fit while colour mass collapsed; B’s stronger conditional colour result came with mass collapse and spill. **[SEQ-029; SEQ-033; SEQ-034]**

The strength sweeps likewise found no clean operating point. D’s context-reading ability improved as strength increased, while its owner-specific contrast did not become memory. **[SEQ-030]**

The justified conclusion is:

> **Neither the tested rank increase nor the tested strength settings rescued these representations.**

“Capacity is not the limit” is too strong. Rank does not isolate capacity from optimization, target modules, training exposure or interference. Nor does success or failure of a whole-model LoRA automatically transfer to the proposed memory-only module allocation.

### Exposure order: no rescue, not equivalence

The completed endpoint comparison covers A and C under within-session and across-sleep ordering of the same items. Neither arm produced qualifying binding. **[SEQ-034]**

But B’s trajectory work remained in progress in the latest entry. **[SEQ-035]** Thus:

- **Supported:** neither tested ordering rescued the reported A/C endpoints.
- **Not supported:** exposure order is irrelevant for every writer, or the arms are statistically equivalent.

The exact scheduling and adapter-reset semantics also need manifest verification. Item identity does not establish identical optimization histories.

### Node effect: localize the comparison, do not discard the experiment

The frozen model plus the same routine line scored approximately **0.273 task-score units** on node 1 versus **0.244 task-score units** on node 2 on the unseen panel. Software versions matched; the cause remained open. **[SEQ-032, including its correction; SEQ-033]**

This directly invalidates unpaired cross-node claims about brief or routine superiority. It does **not** demonstrate that the car-test log-probability measurements have the same problem.

Nevertheless, each decisive F comparison should use the same node, model/runtime configuration, tokenizer, candidate strings and OFF reference. Replicate any claimed pass on the other node. **Matching corpora is necessary, not sufficient, for a rank or node comparison.**

## Is F fair for this system?

**Yes—as a deliberately favourable test of canonical-cue weight memory.**

This agent can, in principle, generate its own recall prefix. It is therefore reasonable to write bare declarative frames and retrieve by completing them rather than demanding question answering. Rescoring existing adapters first is especially valuable: it changes retrieval without changing the write. **[SEQ-034; SEQ-035]**

But F changes the claim:

> From “a fact survives a changed question” to “a repeatedly written association can be retrieved through its designated prefix.”

That narrower ability is useful if the agent can invoke it autonomously.

### The corrected trio separates rendering count from variety

The valid comparison is:

- `F_r16k1`
- `F_r16k4`
- `F_r16k16`

Each uses **R=16 renderings per occurrence**, varying **K=1, 4 or 16 templates**. The earlier proposed trio did not match exposure. `F_r64k16` raises rendering count to **R=64 renderings per occurrence**, retaining **K=16 templates**. **[Unnumbered F implementation correction; queued execution confirmed in SEQ-035]**

The accounting must distinguish:

\[
\text{rendered fact presentations}
=
\text{source occurrences}\times R
\]

from training presentations after epochs, packing, truncation and sampling. It must also distinguish all of those from **independent experiences**.

Every template ends in the same canonical sentence. Therefore template variety is principally variety around a shared retrieval target—not necessarily variety in how the owner–colour relation is expressed.

**Fairness conditions:** verify actual trained answer-token counts; equalize or disclose filler and token-budget differences; check no answer leakage into recall prefixes; and test the intended memory-block rank and target modules. F’s exact training configuration is not established by the supplied execution-status entries.

## What would count as binding rather than recitation?

Predeclare this conjunction before reading the F report.

| Requirement | Passing pattern |
|---|---|
| **Owner-specific frame contrast** | At the declared high dose, \(I_{d,\mathrm{frame}}\) has a **95% confidence interval** wholly above zero **log-odds units**, with owner-clustered uncertainty and bank-level results shown. |
| **Positive owner term** | The planted owner’s correct-colour probability and absolute correct-colour likelihood improve. The contrast is not created by depressing similar IDs. |
| **Low spill** | Frame-similar, unexposed-owner, bicycle and generic cues meet the existing **≤0.03 probability-change-unit** spill gate, after its implementation is verified. |
| **Dose response** | Unexposed owners remain a negative control; increasing effective exposure produces a positive prespecified trend in owner-specific retrieval, without parallel spill growth. Saturation is acceptable; exact monotonicity at every sample is unnecessary. |
| **Usable answer** | Natural completions actually produce the correct colour; conditional colour normalization is not hiding mass collapse. |
| **Correct relation and mapping** | Changing owner or relation changes the answer appropriately. A scrambled-binding write retrieves its trained mapping, not the original mapping used by the evaluator. |
| **Beyond the exact string** | The result survives an untrained surrounding context and an agent-generated recall prefix, then supports an appropriate action. |

The confidence convention and spill threshold come from **SEQ-025**; the owner-term and mass requirements address failures in **SEQ-026 and SEQ-033**. The remaining rows are proposed release criteria, not reported results.

**Important boundary:** exact-frame owner-specific retrieval is already evidence of a stored association. It need not generalize to paraphrased questions to be useful. But exact-frame retrieval alone cannot distinguish a lookup-like memorized continuation from broader relational knowledge. Call that **canonical-cue binding**, not general memory.

If F succeeds only on the exact prefix, label it **surface-bound associative recall**. If it also survives contextual embedding and drives conditional action, call it **usable canonical memory**. Reserve “experiential memory” for the own-perception bridge.

## If F binds only at R≥64, what follows for sleep?

**It means this write needs substantial rehearsal—not that one perception naturally supplies that rehearsal.**

First rule out a dose-accounting mistake: **R is renderings per occurrence, not total exposure per fact**. A success at higher R must be interpreted against actual total presentations, optimizer updates and token budget, not the label alone. **[Unnumbered F implementation correction]**

Then distinguish three quantities:

- independent encounters with the situation;
- genuinely different, grounded noticings by the child;
- replayed copies or reformulations of existing text.

Only the first adds independent environmental evidence. The second may improve representation. The third buys optimization exposure without adding evidence.

For production sleep, this implies:

- retain provenance and genuine occurrence counts;
- replay recurrent, verified perceptions deliberately;
- do not manufacture “many experiences” by repeating a claim;
- measure whether the child’s natural corpus reaches the successful regime;
- budget retention and replay across sleeps;
- verify that repeated misconceptions do not become the easiest facts to retrieve.

**A pass obtained only after extensive artificial repetition establishes rehearsal-based storage. It does not validate the claim that the current sleep naturally writes the child’s repeated perceptions.** The bridge must use the child’s own observed situation–outcome statements, with no factual content supplied by a paraphraser.

## If F fails: the fallback architecture

**Yes: after a valid high-exposure failure in the intended configuration, the memory block is dead as this sprint’s factual-store strategy. Text memory becomes the store. Keep the behaviour adapter.**

That decision is consistent with, but not proved by, the existing brief baseline: at end of life, brief ≥ adapter in **12 of 19 lives**, while adapter > brief in **7 of 19 lives**. At the matched mid-life checkpoint, the adapter beat the brief by **0.034 task-score units** on the seen panel and tied it on the unseen panel. Weights can still carry useful behaviour. **[SEQ-034; SEQ-035]**

### Concrete fallback

**Persistent text store**

Store the child’s own observations and lessons with:

- source episode and supporting observation;
- situation/entity/relation keys;
- outcome and applicability conditions;
- independent occurrence count, separate from replay count;
- uncertainty, contradiction and supersession links.

Do not silently delete a disproven belief or train it as a positive fact. Preserve it as rejected or superseded evidence.

**Retrieval into waking context**

Retrieve by current situation and the child’s own recall request. Return short evidence-bearing passages, not just a global brief. Prefer relevant supported memories; expose uncertainty and conflicting observations. If nothing matches, return no memory rather than an invented completion.

**Behaviour adapter**

Train on multi-scale sequences of the child noticing, retrieving, checking applicability, revising and acting. Keep factual persistence in text. The adapter’s job is to make memory use effective, conditional and interface-safe—not to reproduce arbitrary facts without context.

**Atomic deployment and attribution**

Version the adapter and memory snapshot together. Before commit, test action parsing, retrieval compatibility and established behaviour. Evaluate:

- frozen child without retrieval;
- frozen child with retrieval;
- behaviour adapter without retrieval;
- behaviour adapter with retrieval.

Use matched nodes, horizons and retrieval inputs. Existing adapter-plus-brief interactions have both helped and harmed, so composition must be tested rather than assumed. **[SEQ-028; SEQ-031]**

## Proposed 48-hour plan

*This is a planning horizon requested by you, not a notebook result.*

### First day: finish the mechanism decision

- Export corpora, adapters, manifests and raw evaluations before machine loss becomes a recovery problem.
- Audit candidate tokenization, frame prefixes, spill units, gate definitions and trained exposure counts.
- Finish existing-adapter rescoring and the corrected F trio.
- Complete the high-exposure F fit; treat a single-bank result as screening, not final confirmation.
- Publish owner gain, control gain, \(I_{d,\mathrm{frame}}\), colour mass, natural completions, spill and dose response together. No fallback winner.
- Implement the text store and retrieval path in parallel.

### Second day: test the bridge, then freeze the architecture

**If F passes:** replicate the pass, check the intended memory-only block, then use a recurrent difficulty from existing child records. Test the child’s own canonical lesson both through supplied prefixes and autonomous recall, followed by action on new instances and rejection on nonmatching instances.

**If F fails validly:** disable the factual memory block, run the retrieved-text/behaviour-adapter attribution conditions, and commit the fallback if interface and task behaviour remain sound.

**If F is inconclusive:** deploy the same fallback. An unfinished mechanism test is not a reason to make the lineage depend on an unverified store.

**Paper-ready conclusion now:**  
> The tested writes learned training-text continuations and context-dependent skills, but no configuration met the criteria for clean out-of-context owner–colour retrieval. Canonical completion with increased rehearsal remains under test. Until that mechanism also works on the child’s own perceptions, factual persistence belongs in retrieved text, while adapters remain candidates for learning how to use it.