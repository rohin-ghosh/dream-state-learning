# Astra memo q12 — design audit of the H2 2×2 deployment (parented × sleep-running-vs-frozen on the unseen gym)

Asked by Fable 2026-09-11 23:40 UTC (single call, `tools/astra.py`, effort high, 89 s; prompt = THESIS v2 verbatim + facts about the lives + seven questions, in `q12_run/prompt.md`; raw reply in `q12_run/reply_raw.md`). Adopted into THESIS v2 §1 (the 'Astra's design audit' paragraph): staged 2×2 as a test of consolidation-dependent improvement, RP-package vs R2-package (not 'parenting causes'), pre-registered early-vs-late contrast with three within-node blocks, MDE ≈ 0.06, 252-episode balanced schedule, shadow-sleep frozen definition, node canary, budget 223 GPU-h, launch manifest for the STOP decision, instrumentation for an interpretable null, and the narrow-claim warning.

---

## Recommendation

**Approve a staged 2×2 as a test of consolidation-dependent improvement, not yet as a clean causal test of parenting.** Before launch: resolve the STOP, standardise the gate and non-weight memory, block comparisons within node, and preregister one learning-curve contrast. Start with 256 episodes plus a **post-final-sleep probe**; reserve 512 for a pre-authorised extension.

The main qualification is substantive: the finished RP and R2 lives compare **training packages**, not parenting alone. Also, the proposed test could establish useful continued adaptation without establishing that first-person articulation caused it.

*Evidence boundary:* I rely only on the supplied thesis and facts. I cannot verify adapters, receipts, code, gate implementations, or the reported analyses.

## 1. Is the 2×2 right?

**Yes, structurally.** The interaction asks whether continuing consolidation increases the parented advantage, rather than merely preserving an initial advantage (§§0–1). But “sleep” must have a precise intervention definition.

| Issue | Control or measurement |
|---|---|
| **Starting level versus learning** | Probe every seed before deployment. Separate the baseline parenting contrast from the change-in-performance interaction. Do not count an initially higher RP score as H2. Report baseline and ceiling/headroom: identical learning capacity can yield different slopes at different starting scores. |
| **Gate** | Give both running rows the **same** candidate-selection rule, evaluation panel, and threshold. Prefer a fixed panel disjoint from deployment; do not use R5 (§1; supplied facts). Record proposed updates, accepted updates, rejection reasons, and gate/deployment score changes. With a gate, the estimand concerns **gated consolidation**, not unconstrained learning. If native gates differ, the interaction includes that difference. |
| **Episode order/program mix** | Use 21 balanced rounds of the 12 programs: 252 episodes, with four prespecified extras excluded from the primary contrast. Randomise order within rounds; share schedules across the four branches of each block. Match task randomness where possible, not actions or outcomes. Never replay running-cell outcomes as frozen-cell experience. |
| **Sleep schedule** | Sleep every 32 episodes in both running rows, with identical training recipes. Save and probe initial and post-sleep checkpoints. Balance program position relative to sleep across schedules. An eighth sleep after episode 256 cannot affect the preceding score curve. |
| **Node effects** | Keep each parented/unparented × running/frozen block on the same node; randomise execution order and distribute blocks across nodes. Run a short identical-checkpoint canary first. The reported 0.029 node discrepancy is comparable to the existing adapter gains, so pooling unblocked comparisons is unacceptable (supplied facts). |
| **Frozen definition** | Define frozen as **no weight changes**, while matching every other persistent state. “No sleep” is equivalent to “gate always rejects” only if rejected sleep changes no context, notes, retrieval store, RNG trajectory, or later prompts. Otherwise use a shadow-sleep branch that generates the same kinds of artifacts but cannot update weights. Match reporting/artifact prompts in both branches. |

This requires an explicit inventory of non-weight memory. If frozen agents retain useful notes in context while running agents consume and clear them, this is not a clean consolidation intervention.

## 2. Primary estimand, estimator, interval, and detectability

### Preregister this contrast

For each life and deployment condition, calculate:

\[
G=\frac1{12}\sum_{p=1}^{12}
\left(\overline{Y}_{p,\ visits\,15:21}
-\overline{Y}_{p,\ visits\,1:7}\right).
\]

Then estimate:

\[
\theta=(G_{RP,run}-G_{RP,frozen})
       -(G_{R2,run}-G_{R2,frozen}).
\]

This is **additional early-to-late improvement attributable to continued consolidation in RP versus R2**, on these 12 programs. It is more robust and interpretable than assuming linear learning over approximately 21 visits.

Visits 1–7 already include consolidation. Therefore separately report the initial frozen-checkpoint contrast for H1 and baseline-to-post-final-sleep changes as secondary outcomes. A null primary contrast can miss very rapid learning completed in the early window.

Use three prespecified matched RP–R2 blocks, preferably within node. Compute one interaction \(d_b\) per block:

\[
\hat\theta=\operatorname{mean}(d_b),\qquad
95\%\ CI=\hat\theta\pm t_{.975,2}\frac{s_d}{\sqrt3}.
\]

The **life/block, not program or episode, is the independent replication unit**. This interval assumes independent, approximately normally distributed block effects; with three blocks, that assumption is largely uncheckable. Show all three effects. Pairing historical lives improves precision only when meaningful; it does not randomise parenting.

Secondary analysis: per-program curves and a hierarchical model allowing nonlinear visit effects and life-level variation. Program random effects do not manufacture additional life replication. Generalisation beyond this fixed panel needs additional assumptions.

### What can 3 lives detect?

The supplied **0.0065 SD is from three base-panel replicates**, not from life-level learning interactions. Thus **a defensible actual MDE is unknown**.

An illustrative calculation:

- Assume each early/late panel mean has SD 0.0065.
- Assume no early–late or cross-branch covariance.
- Then a block interaction has SD \(\sqrt8(0.0065)=0.0184\).
- With three blocks, \(SE=0.0106\).
- Expected 95% interval half-width: \(4.303(0.0106)\approx0.046\).
- Two-sided 5%, 80%-power MDE using the small-sample \(t\) test is approximately **0.060 score units**.

The large-sample approximation would misleadingly suggest about 0.030. Positive pairing correlations could improve sensitivity substantially; life heterogeneity could worsen it. **Do not pitch this as powered to detect a 0.02 interaction.** Use early data to estimate nuisance variability, not to choose a favourable endpoint.

## 3. Is 256 enough? What is the cheapest defensible version?

**Enough for an initial test; not enough to make a null decisive.** Routine formation within 3–5 childhood sleeps motivates eight opportunities, but does not establish the timescale of transfer learning from already-trained adapters (supplied facts).

At minimum:

1. Initial checkpoint probe.
2. Balanced deployment episodes.
3. Post-sleep probes, including after sleep eight.
4. Saved artifacts and adapters for every attempted update.

For 512 episodes, extend all cells under a prespecified rule based on feasibility or precision—not whether one arm looks promising. Longer runs provide more consolidation opportunities but do not solve three-life replication or historical confounding.

**Cheap frozen control:** repeated fixed-adapter probes can replace full frozen lives **only if** episodes reset all non-weight state, the environment has no consequential carryover, and visit index conveys no usable history. Then there is no frozen learning mechanism to simulate. Match program, prompt, decoding, node, and timing; retain repeated probes to measure drift. Otherwise full frozen trajectories are necessary.

Use the same evaluation protocol on running checkpoints. Adding extensive checkpoint probes can erase much of the saving, so cost that protocol explicitly.

**Budget correction:** 256 episodes cost 17.92 GPU-hours per branch. Twelve branches plus eight ten-minute sleeps in six running branches cost approximately **223 GPU-hours = 9.3 GPU-days**, excluding probes and gate overhead. That is about 28 hours on eight fully available GPUs. Section 4’s “~1.5 GPU-days” conflicts with §1’s approximately 1.5 days on eight GPUs.

## 4. Provenance package for the STOP decision

Do not interpret “full receipts” as authorisation. Submit a launch manifest containing:

- **Identity:** hashes for base model, tokenizer, adapter tensors/config, code commit, prompts, and environment/compiler versions.
- **Ancestry:** life ID, node, initial checkpoint, every accepted sleep checkpoint, parent checkpoint hashes, and links to the experiment ledger.
- **Training lineage:** corpus hashes; episode/source IDs; parent utterance IDs; filtering, optimisation, and gate configurations/results.
- **Verification:** loaded tensors match the recorded final adapter; no undocumented bootstrap ancestor; no R5/deployment-panel selection; no probe feedback entered subsequent training or adapter selection.
- **Reproduction:** load the checkpoint and reproduce a recorded probe within a declared tolerance on the deployment node.
- **Authorisation:** lead’s explicit STOP interpretation or scoped exception, naming exact seed hashes and allowed operations.

The unseen panel has already been probed (§1). Verify that those results did not determine which RP/R2 seeds enter this experiment. Historical evaluation is not automatically training contamination, but selection on it compromises the claim.

**I cannot verify any of this lineage from the supplied narrative.**

## 5. Fair unparented control

R2 is a useful practical baseline, but not a matched parenting control. RP differs in parent interaction, prompt structure, and classroom exposure; parents not seeing scores does not eliminate those differences (supplied facts).

The appropriate prospective control matches:

- initial child and training exposure;
- classroom turns, token/thinking budget, and prompt scaffolding;
- sleep schedule, corpus budget, and gate;
- task-related information available.

It substitutes an active control curriculum without the targeted articulation/self-evaluation instruction. To isolate the proposed mechanism specifically, compare parenting with versus without that instruction while preserving the surrounding interaction.

**No such finished-life control is established here.** R4 can help diagnose gate/panel effects, but is not a classroom-matched parenting control. Label the historical comparison **RP-package versus R2-package**, not “parenting causes faster learning.”

## 6. Measurements that make a null interpretable

Instrument the full chain: **experience → useful artifact → eligible corpus → accepted update → retained knowledge → better action** (§§0, 2–4).

- **Coverage and selection:** outcomes observed, successes/failures, notes produced, items retained, unique facts, and effective training tokens. Success filtering may starve weaker cells or discard informative failures.
- **Register:** first person, prospective versus retrospective, explicit action–outcome linkage. Validate automated markers on a blinded sample; §3 describes crude word-marker measurement.
- **Provenance:** source-ID validity **and factual support**. Lexical overlap alone misses invented relationships and rejects valid paraphrases or derived conclusions. Mark derived claims with their evidence/derivation; report unsupported and unverifiable claims separately.
- **Rituals:** repeated-note rate, template similarity, repeated pass sequences, exploration diversity, and copying without outcome revision.
- **Consolidation:** proposed/accepted sleeps, corpus size, training loss, update norm, and pre/post-sleep performance.
- **Retention and use:** fresh-context probes of selected externally grounded discoveries, plus whether later actions use them appropriately.

First-person language is a diagnostic feature, not proof of trainability. Bare recipes can encode useful policies; outcomes can be written fluently but incorrectly. Likewise, external grounding does not by itself eliminate collapse, selection bias, or accumulated compression errors (§§0, 2–3).

## 7. One thing this design will get wrong

**It will be tempted to call repeated adaptation on the 12 programs “general learning on unseen tasks.”**

Those programs are unseen at deployment start, not after repeated visits. A positive interaction supports consolidation-dependent adaptation on this panel; it does not distinguish reusable learning from program-specific recipe accumulation. Preserve a small genuinely untouched final transfer set if available. If none exists, state that limitation and keep the paper’s claim narrow.

[astra openai/openai/gpt-6-astra effort=high 89s tokens in=3529 out=3504 reasoning=1034]
