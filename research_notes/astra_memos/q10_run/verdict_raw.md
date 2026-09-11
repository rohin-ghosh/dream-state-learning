## Recommendation

**Keep the bridge as evidence of feasibility, not yet as a measurement of a pure perception-skill deficit. Proceed with a positive-only teaching experiment; do not make taught negatives part of the primary success criterion.**

The central idea worth testing is **supported factual content per rendering**, not greater surface diversity. The child already produces varied prose. What it often does not produce is another grounded statement of the owner–colour relation, independent of the canonical sentence. The next experiment should test whether a lesson changes that behaviour and whether those changes improve writing through the *same* storage mechanism.

Three qualifications are essential:

1. **The owner-specific metric needs an immediate audit.** Its reported values are incompatible with its supplied definition.
2. **Variant b demonstrates child-generated text under explicit instructions plus harness repair**, not unaided discovery of a storable form.
3. **Variant c teaches particular owners to be “not observed.”** Its evaluation does not yet demonstrate recognizing genuinely unseen owners.

All empirical references below are to your supplied table or explicitly identified earlier facts. I have not fetched or independently verified anything.

---

## 1. Verdict on the bridge

### What is established

**Child-generated corpora can support substantial canonical retrieval under this constrained, repaired protocol.** Variant b reaches 0.822 pooled versus 0.913 for synthetic F; its three bank results are 0.790, 0.684, and 0.992 [pooled CF_r16_b/F_r16k16; bank0–2 CF_r16_b].

That is meaningful feasibility evidence. The gap is not uniformly large: F−b is 0.046, 0.223, and 0.005. Conversely, two near-synthetic results do not establish reliable equivalence: the remaining bank has a substantial deficit.

**Asking the child to produce the canonical ending is a promising prompt intervention.** Relative to a, b improves completion in all three banks, by 0.483, 0.053, and 0.047 [bank0–2 CF_r16_a/b]. But most of the pooled improvement comes from bank0. This warrants replication, not a universal mechanism claim.

**Lexical variety alone is insufficient.** Variant a already has distinctness 0.877 and novelty 0.887 pooled, but completion is 0.628; b has lower measured novelty, 0.855, yet higher completion, 0.822 [pooled CF_r16_a/b]. These diagnostics do not measure the relevant semantic augmentation.

### What is not established

**First, the reported owner-specific numbers cannot literally be probability differences.** You define \(I_{d,\mathrm{frame}}\) as one probability minus another, so it must lie in \([-1,1]\). Yet F is 2.836 pooled and b is 2.279, with bank2 F at 4.899 [pooled F_r16k16/CF_r16_b; bank2 F_r16k16].

This could be a log-odds contrast, a sum, or a reporting mismatch; I cannot determine which. Until the implementation, units, aggregation, and bootstrap are reconciled, I would not publish an unqualified owner-specific conclusion. **If the intended metric is a valid owner-specific contrast, b’s reported positive intervals across all three banks are encouraging conditional evidence**, not an audited result.

Other limitations:

- **No isolated causal effect of “the child writes the sentence itself.”** The training mechanism sees tokens, not authorship. Any difference must arise from changed text, placement, tokenization, sampling, or training. Both a and b contain appended/repaired canonical text.
- **No pure perception-deficit estimate.** F−b also incorporates corpus composition, factual density, formatting, unsupported elaboration, and optimization variability.
- **No clean selectivity result.** Reported spill remains large: 0.308 for b and 0.427 for F pooled [pooled CF_r16_b/F_r16k16].
- **No evidence of enduring behavioural learning.** For a frozen child receiving a lesson in its prompt, the initial claim is instruction-conditioned behaviour. Persistence or transfer requires another test.

### Permitted paper wording

I would replace your sentence with:

> “Across three owner-assignment banks on one material seed, child-generated renderings produced under an explicit canonical-ending instruction, with automatic repair of missed endings, supported mean canonical completion probability of 0.822, versus 0.913 for synthetic renderings. The paired synthetic–child gaps were 0.046, 0.223, and 0.005. This establishes feasibility under a constrained writing protocol; the residual gap is an operational target for teaching, not yet an isolated measure of perception skill.”

After resolving the metric, add the owner-specific finding with its actual units. Do not write **“when”** if it implies a necessary condition: a also succeeds strongly in bank2 [bank2 CF_r16_a].

---

## 2. Bank2: diagnose before narrating

Bank2 is not merely noise around a common effect. F, a, and b all approach ceiling, while c nearly returns to OFF completion [bank2 F_r16k16/CF_r16_a/b/c]. That pattern suggests a bank-dependent interaction with the negative corpus or training trajectory—not an intrinsically ineffective child writer.

Several explanations remain live:

- Owner identifiers tokenize differently or collide with similar-owner controls.
- Assignment structure aligns differently with colour priors or the shared material.
- Negative examples compete with positive retrieval, particularly through overlapping identifier features.
- Packing, ordering, truncation, or training randomness magnifies a corpus difference.
- c’s positive renderings differ from b’s, so “adding negatives” is not the only changed variable.
- An adapter/checkpoint, assignment-map, or evaluation-join error produces an apparent collapse.

### Audit in this order

**1. Identity and corpus integrity**

For every evaluation item, join:

`material seed → bank → owner → colour → dose → control type → raw generation → repaired text → training record → adapter/checkpoint`.

Check:

- No positive owner is also a negative-labelled owner.
- No similar control accidentally names another exposed owner.
- Colour assignments agree across generation, training, and evaluation.
- OFF outputs are identical across cells for identical evaluation inputs.
- Correct adapters and sleep-4 checkpoints were loaded.
- Whether b/c positives are byte-identical. If not, the current b–c comparison is not a clean negatives ablation.

**2. Actual exposure, not nominal row counts**

Count canonical positive and negative occurrences *after* repair, packing, truncation, and repetition. Break them down by owner, colour, and dose. Check duplicate endings, lost endings, sequence boundaries, and actual training exposure at sleep 4.

**3. Item-level probability movement**

For b→c, inspect all four colour probabilities, \(P(\text{“ not”})\), and remaining probability mass at:

- exposed owners;
- explicitly negative-labelled owners;
- genuinely untouched owners;
- similar-owner and bicycle controls.

The 0.164 abstention reported for bank2 c concerns negative-labelled owners; it does **not** explain where probability went at positive owners [bank2 CF_r16_c]. Test that directly.

Plot paired owner-level results by dose, colour, and identifier tokenization. Determine whether bank2 c damages nearly everyone or a small identifiable subset.

**4. One targeted rerun**

If integrity checks pass, rerun bank2 b/c with unchanged corpus bytes and a different training seed. This separates instability of the write from instability of generation or assignment. It is an audit, not a new mechanism-knob campaign.

### Does variance undermine pooling?

It undermines a **uniform or robust-success interpretation**, not the arithmetic mean. Report the mean with all bank results. In particular, pooled c completion of 0.506 hides one strong bank and two failures [bank0–2 CF_r16_c].

The fresh material runs are valuable, but nine banks across three shared material seeds are not automatically nine independent end-to-end replications.

---

## 3. Negatives: neither an inherent trade-off nor demonstrated epistemic abstention

c changes b’s completion by +0.053, −0.267, and −0.733 across banks [bank0–2 CF_r16_b/c]. That is evidence of a potentially severe interaction, **not a universal capacity trade-off**.

The abstention result is real in the narrow sense that probability of “ not” increases at the trained negative owners: 0.166 pooled, versus 0.002 in b [pooled CF_r16_b/c]. But those owners are now exposed to supervision. Rename the group:

> **No positive observation; explicitly trained as “not observed.”**

Reserve **unseen/unexposed** for owners absent from *both* positive and negative training. To claim “knows what it has not seen,” test those untouched owners and false abstention on known positives.

The earlier templated-negative failure is suggestive but not a matched control. Its 64 lines per owner differ in form and dose from c’s 16 lines per owner. It does not isolate child authorship as the cause of abstention.

### Is this dose or form?

You cannot yet distinguish them.

The nominal dose comparison also needs correction. At dose 16, each positive owner receives \(16 \times 16=256\) renderings; 16 such owners yield 4,096 positive renderings. c has 256 negative lines **total**, assuming the stated counts represent actual training records. Thus negatives are not equally numerous to the dose-16 positives, although they could carry disproportionately strong gradients. Actual token exposure remains unverified.

Negative exact-frame miss is 0.559 pooled [pooled CF_r16_c]. This is an important form diagnostic, but all misses are repaired; raw miss rate alone cannot explain the final corpus’s effect.

### Single change to test first

**Reduce negative dose fourfold: four lines per negative-labelled owner, 64 total.**

Use a stratified subset of the existing negative corpus—do not regenerate it. Hold positive corpus bytes and positive training exposure fixed. Compare against matched zero-negative and 256-negative controls, keeping compute and background handling consistent.

Measure:

1. Positive completion and owner specificity.
2. False abstention on exposed positives.
3. Abstention on trained-negative owners.
4. Abstention on genuinely untouched owners.

This is the simplest test of whether the current operating point is unnecessarily aggressive. Do not simultaneously introduce the u lesson: that would change dose and form together.

---

## 4. The teaching lever and concrete lesson edits

### Most likely lever

**More grounded owner–colour restatements in the prose, across varied sentence forms.**

This is a hypothesis supported by the corpus contrast, not a verified attribution to the cited literature. Your context identifies Physics of Language Models and TMEM as the adopted mechanism; I have not inspected those sources here.

The current diagnostics suggest this priority order:

1. **Grounded relational restatement.**
2. Exact-ending compliance and repair dependence.
3. Prose length, only if exposure audits implicate dilution.
4. More looks, last.

Why:

- b is already 99% distinct, with essentially zero exact echoes [pooled CF_r16_b].
- Its sample scratches/garage/sunlight descriptions are unsupported by the supplied owner–colour fact. Unless those details appeared in the observation, they are inventions, not perception.
- Colour drift of 1.5% misses these errors completely [pooled CF_r16_b].
- Because missed endings are repaired, fewer raw misses do not automatically add more canonical facts to training.
- Sixteen looks already provide ample opportunities to produce useful restatements; increasing them before improving content risks buying more decorative text.

### The current lesson partially targets the right thing

“Whose car it is and what colour it is” is well aimed. “Compare it with another car,” “place it in its spot,” and “notice its condition” encourage unsupported assertions unless those facts are available.

Also remove “a single glance is forgotten”: it is an unsupported universal claim, especially while dose-1 results are not shown.

### Suggested positive lesson

> **A suggestion for looking so that you can remember:** a useful note preserves the relation you actually observed—whose car it is and what colour it is. Across your looks, you might express that same supported fact in different words or sentence shapes, sometimes foregrounding the owner and sometimes the colour. Each note should make sense on its own; decorative detail need not help. Do not invent a location, condition, comparison, or history that the observation does not supply. Repeating the fact accurately is better than inventing a new detail. Treat these suggestions as tools to use when helpful.

For the first controlled t experiment, keep the existing b output protocol separate and unchanged. This tests **lesson-conditioned improvement within a constrained assay**. It does not show that the child freely chooses the canonical form. A later transfer probe should remove that explicit requirement and automatic repairs.

Do not silently change the common b prompt while comparing against historical b. Any shared prompt revision needs a new matched control.

### Suggested negative lesson, for later

> When a fact was not provided, distinguish that from learning a negative fact about the world. State the limit of the supplied information without guessing a colour. Do not claim to have inspected places or checked records unless that information is actually available. You may find it useful to say whose car lacks a reported observation.

Keep the canonical “not observed” target explicit as an experimental convention, not a claim about the world.

### Add one diagnostic beyond mention rates

Measure **supported owner–colour relation rate after removing the canonical sentence**. Separate owner and colour mentions can occur without binding the correct owner to the correct car colour.

Also score unsupported-detail rate and owner errors on a blinded sample. Lexical distinctness, echo, and colour drift do not establish factual quality.

---

## 5. Minimal analysis for the paper-spine claim

### First narrow the claim

The present data cannot support:

> “The untaught child does not naturally produce the storable form; a taught child does.”

b is already heavily instructed, and two banks are within five percentage points of F [bank0/bank2 F_r16k16 and CF_r16_b]. A defensible target is:

> “Relative to the same output instructions without a perception lesson, teaching increases grounded factual restatement and improves downstream storage, reducing the gap to synthetic renderings.”

Showing “naturally” requires a less directed baseline; showing learned skill beyond prompt compliance requires transfer.

### Primary comparison

Run **F, b, and t on the same assignments, events, write budget, and evaluation items**. Keep c/u secondary.

Pre-register three outcomes:

1. **Behaviour:** t increases supported relation rate in raw prose.
2. **Storage benefit:** paired completion difference t−b.
3. **Synthetic gap:** paired difference F−t.

Owner specificity, spill, and false abstention are necessary checks: completion must not improve merely by becoming less selective.

### Margin I would defend

**Five absolute percentage points of canonical completion probability**, provided the task treats owners and colours symmetrically.

This is a pragmatic performance tolerance, not a validated universal threshold. I would not defend ten points here: it would already accommodate the current pooled b deficit of 9.1 points [pooled F_r16k16/CF_r16_b].

For the claim “reaches synthetic performance,” use **non-inferiority**, because exceeding F should not count as failure:

\[
\text{upper one-sided 95% confidence bound on }(F-t)<0.05.
\]

Use equivalence within ±0.05 only if the claim genuinely requires both directions.

But non-inferiority alone is insufficient. If b is also non-inferior, teaching was not necessary. Require a positive paired t−b effect and the predicted behavioural change. To claim a meaningful untaught deficit, establish it directly rather than treating b’s failure to pass non-inferiority as proof.

### Respect the replication structure

Show:

- all nine paired bank differences, grouped by material seed;
- each material seed’s mean;
- the overall paired estimate and clearly scoped interval;
- sensitivity to leaving out each material seed;
- the pre-specified dose-16 endpoint, plus the full dose-response curve.

Owner bootstraps measure item variation conditional on the realized runs. They do not capture all material, generation, or training variability. With only three material seeds, broad generalization intervals will be fragile; nine bank rows do not cure that. State which randomness each interval covers.

Since the lesson is being designed from seed0 results, label seed0 exploratory. Lock the lesson and analysis before inspecting fresh-material results. I cannot verify whether the forthcoming runs contain enough independent variation to meet a five-point margin; apparent precision from pooled evaluation items would not settle that.

---

## 6. What you are about to get wrong

**Highest-priority corrections before the next launch:**

1. **Resolve the impossible probability-contrast scale.** This affects the central owner-specific claim.
2. **Do not equate lexical novelty with useful perception.** The sample “new aspects” may be hallucinations.
3. **Do not call trained-negative owners unseen.** Add untouched owners and measure false abstention.
4. **Do not attribute a token-level training effect to authorship itself.** Explain what changes in the corpus.
5. **Do not let repair disappear from the claim.** Retain raw and compiled versions; report dependence on repair. Success after repair is not unaided form production.
6. **Do not launch t/u as one primary package.** Positive teaching should stand alone; negatives currently risk overwhelming its interpretation.
7. **Do not upgrade prompted performance to an acquired general skill.** A small held-out transfer probe—new facts and a changed writing instruction, without the canonical-ending requirement—would be more informative than another adapter-rank sweep.
8. **Do not reopen the mechanism paper.** Under the ruling, F establishes the adopted write path. The research contribution is whether parenting changes the child’s grounded outputs in ways that causally improve that path.

**Go/no-go:** proceed with a locked, positive-only t experiment after the metric and corpus-integrity audit. Treat a reproducible **behaviour change → storage improvement → reduced synthetic gap** chain as the next success criterion. Treat c as a separate unresolved experiment, not yet as evidence that the child has learned epistemic abstention.

[astra openai/openai/gpt-6-astra effort=high 117s tokens in=3383 out=4877 reasoning=1034]
