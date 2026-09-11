# Astra memo q11 — re-diagnosis with the prose-content table; pre-registration of the taught-variant (t) experiment

Asked by Fable 2026-09-12 00:30 UTC (single call, `tools/astra.py`, effort high, 96 s; prompt in `q11_run/prompt.md`, raw reply in `q11_run/reply_raw.md`). Adopted as the pre-registration for CF_r16_t vs CF_r16_b vs F_r16k16: names-both proxy (≥ 0.50 and ≥ +0.40 over b per confirmatory bank) as the behavioural endpoint; paired t−b completion; F−t non-inferiority (one-sided 95 % upper bound < 0.05); owner-cluster bootstrap; seed 0 exploratory, seeds 1–2 confirmatory; u secondary. Astra's caution: names-both is a binding proxy, not verified relation restatement — audit stripping and semantic correctness before interpreting it.

---

## A. Re-diagnosis

**The table strengthens the owner–colour-restatement hypothesis, but does not establish it as the sole lever.** I withdraw the “impossible scale” objection: your corrected \(I_{d,\mathrm{frame}}\) is a difference of ON−OFF log-odds gains, in nats; 2–5 is not intrinsically problematic.

Three updates matter:

1. **Ending with the canonical frame changes what the child discusses.** Colour mention rises from 0.260–0.283 in **CF_r16_a** to 0.773–0.794 in **CF_r16_b**, despite similar prose lengths. That supports colour-directed elaboration, not merely “more prose.” But a→b also changes who writes the frame, its placement/compliance, and potentially training-token structure. The table does not identify colour attention as the causal mediator.

2. **Owner binding is a plausible remaining bottleneck, not an established explanation of the residual.** In **b**, owner mentions are only 0.027–0.052 and names-both rates 0.022–0.044. However, b already nearly matches F in banks 0 and 2:
   \[
   F-b=0.046,\quad0.223,\quad0.005.
   \]
   Thus, low prose relation rates coexist with excellent storage. The appended/written canonical sentence itself binds owner and colour. Additional binding in the prose might help, but is plainly not necessary for high completion in every bank.

3. **The evidence argues against a simple content-only account.** Bank 2’s **a** completion is 0.945 versus bank 0’s 0.307, with colour rates only 0.283 versus 0.260. Moreover, a→b gains are 0.483 / 0.053 / 0.047: colour-directed prose is not sufficient to explain the bank pattern. The near-identical aggregate prose statistics of **b/c**, alongside sharply different storage, reinforce that limitation—although their nonidentical positives prevent a clean negatives inference.

**Expectation for t:** a substantial rise in explicit binding is plausible because the lesson directly requests it. Full closure is less secure: the deficit is concentrated in bank 1, and the table does not show that bank 1 is uniquely deficient in binding. Also, b’s frame-ending compliance is only about 86% (**b row**); the longer instruction could improve content while worsening format, diversity, or effective exposure.

For **“the lesson landed in the prose,”** I would predeclare a substantial target: **names-both rate ≥0.50 and improvement over b ≥0.40 in each confirmatory bank**, with uncertainty excluding zero improvement. These are practical thresholds, not estimates derived from the table. Raising colour mention from 78% toward 100% is not the intended manipulation.

Crucially, **names-both is a binding proxy, not verified relation restatement**. I cannot verify semantic correctness, stripping accuracy, or the original q10 analyses from these summaries.

## B. Paste-ready pre-registration

### Taught-variant bridge experiment

**Status and scope.** The positive lesson prompt is locked as supplied, before examining t results. Archive the exact prompt, timestamp, code/configuration hashes, material manifests, generation outputs and training manifests. Seed 0, banks 0–2, is exploratory because it informed lesson design. Seeds 1–2, three banks each, are confirmatory. No prompt revision, outcome-dependent rerun, or bank exclusion will enter the confirmatory analysis.

**Treatment.** Compare t against b using the same child, material events, event seeds, \(R=16\), nominal 250k-token training budget and rank 8. F is the synthetic reference. The estimand is the effect of the complete t rendering procedure, not an isolated causal effect of owner mentions.

Record generation node, batch composition, model/software versions, tokenization, training seed, actual tokens, owner-level exposures, truncation and checkpoint selection. Shared event seeds do **not** establish matched text, given the supplied b/c generation divergence. Keep comparison arms on matched infrastructure where possible; disclose confounding otherwise.

### Outcomes and extraction

1. **Primary behavioural endpoint, per bank:** proportion of raw generated lines whose prose names both the planted colour and owner ID, using the supplied case-insensitive whole-word matcher after removing the child-written canonical sentence. Analyse paired t−b differences.

   Freeze the stripping procedure before inspecting t. Failed or malformed outputs are retained and flagged, not silently dropped; use the intended 5,376 line slots per cell per bank as denominator, with missing lines scored zero. Report colour-only, owner-only, suffix compliance, word count and missing/extra-line rates separately.

   Call this endpoint the **names-both proxy**. Conduct a blinded, reproducibly sampled audit of 100 lines per arm per bank for correct owner–colour assertion, invented details and stripping leakage. Audit findings qualify semantic claims; they do not retrospectively replace the primary endpoint.

2. **Primary storage endpoint:** paired difference in dose-16 completion, \(C_t-C_b\), using the unchanged existing completion evaluator and identical evaluation items. First average repeated observations within owner, then owners within bank. Report bank estimates and the confirmatory seed-balanced mean.

3. **Primary reference-gap endpoint:** \(G=C_F-C_t\), paired on the same evaluated owners/items. Non-inferiority margin is **0.05 absolute completion probability**. Non-inferiority on the tested-material average requires the one-sided 95% upper confidence bound for the confirmatory seed-balanced \(G\) to be **strictly below 0.05**. A nonsignificant F−t difference does not establish non-inferiority.

### Aggregation and uncertainty

For arm contrast \(D_{sj}\), average the three bank estimates within material seed:
\[
D_s=\tfrac13\sum_{j=0}^{2}D_{sj}.
\]
The confirmatory estimate is \((D_1+D_2)/2\), giving equal weight to seeds and banks, not to line counts.

Use 10,000 paired owner-cluster bootstrap draws, retaining all repeated events, renderings and evaluation items for each sampled owner and preserving pairing across arms. Preserve any shared-owner dependence across banks. Do not bootstrap lines independently.

Report two-sided 95% intervals descriptively and one-sided 95% bounds for directional decisions. Bankwise descriptive intervals are pointwise, not simultaneous. Claims requiring every component to pass use a conjunction rule.

**These intervals cover owner sampling conditional on the observed materials, generations and fitted models.** They do not cover fresh-material-seed variability, generation/batch randomness, training randomness or node variability. With only two confirmatory material seeds, no reliable population-of-seeds interval will be claimed.

Report:

- all nine paired bank estimates, visibly grouped by material seed;
- separate seed means;
- the primary six-bank confirmatory result;
- the equally seed-weighted nine-bank summary, labelled exploratory;
- leave-one-seed-out summaries over all nine banks, noting that only omission of seed 0 leaves an entirely confirmatory set;
- confirmatory leave-one-seed-out estimates, which are simply the two individual seed means and are sensitivity checks, not replications.

The seed-1 cross-node a/b/c check is diagnostic, not additional material replication, and cannot establish absence of a t-specific node interaction.

### Necessary specificity and failure checks

Retain the existing q10 ON/OFF evaluation definitions and archive their implementation before analysis.

- **Owner specificity:** report \(I_{d,\mathrm{frame}}\) for t and b, and paired t−b differences. This is the planted-colour ON−OFF log-odds gain at the owner’s frame minus that at the matched look-alike frame, in nats—not a probability difference.
- **Spill:** report planted-colour probability ON−OFF changes separately at look-alike, unexposed and bicycle frames.
- **False abstention:** report \(P(\text{“ not”})\) at exposed dose-16 owners for t, b and OFF, including paired t−b changes.
- Report every check by bank and material seed, not only pooled.

For a **qualified bridge-success claim**, require, on the confirmatory seed-balanced estimates: lower one-sided 95% bound for t’s owner-specific contrast \(>0\); upper bounds for each t spill probability increase \(<0.05\); and upper bound for t−b false-abstention increase \(<0.05\). These 0.05 guardrails are prospective practical tolerances, not empirically validated safety thresholds. Also require positive point-estimated owner specificity in both confirmatory seeds. Failure or imprecision on a guardrail prevents an unqualified success claim.

### Decision rules and permitted wording

Define:

- **B, behavioural success:** in every confirmatory bank, t names-both ≥0.50, t−b ≥0.40, and the one-sided 95% lower bound for t−b \(>0\).
- **S, demonstrated storage improvement:** the confirmatory mean t−b completion has lower one-sided 95% bound \(>0\), and both material-seed point estimates are positive.
- **N, average non-inferiority:** the gap criterion above passes.

Assign exactly one primary outcome:

1. **Landed: B and S pass.**  
   Allowed: “The lesson substantially increased explicit owner–colour co-mention and improved storage on the confirmatory materials.”  
   If N and the guardrails also pass: “t was non-inferior to F within five percentage points on the tested-material average, with the prespecified specificity checks satisfied.”  
   Claim “across all tested banks” only if every confirmatory bank’s gap upper bound is below 0.05.

2. **Did not land: B fails, regardless of S.**  
   Allowed: “The lesson did not meet the prespecified behavioural manipulation criterion.” Report any storage benefit separately; do not infer that grounded restatement cannot help.

3. **Changed prose without demonstrated storage improvement: B passes, S fails.**  
   Allowed: “The lesson changed the targeted prose proxy, but storage improvement was not demonstrated.” Distinguish imprecision, near-zero estimates and harm; do not equate failure of significance with no effect.

N is reported independently under every outcome. Non-inferiority alone is not evidence that t helped: b may already lie within the margin.

### Secondary negative variant

Keep u outside all primary decisions. Report its completion, specificity, trained-negative abstention and exposed/control false abstention separately. Unless u reuses t’s **exact stored positive texts**, describe u−t as a composite variant comparison, not a clean negatives ablation. Seed-0 u findings remain exploratory.

## C. One thing we will get wrong next

**We will mistake a higher names-both score for more grounded binding.** A malformed canonical sentence that escapes stripping—or prose mentioning the right two words in the wrong relation—can “pass” the manipulation without implementing the proposed mechanism. Audit stripping and semantic correctness before interpreting a successful proxy as an explanation of storage.

[astra openai/openai/gpt-6-astra effort=high 96s tokens in=1778 out=3827 reasoning=1485]
