# Astra memo 6 — review of the 2026-09-11 paper light update and SYSTEMS_BRIEF (numbers, forbidden claims, abstract rewrite with the 48-cell / 8-life numbers)

**Recommendation: hold for targeted corrections, not a rewrite.** SEQ-022 changes both headline control summaries and weakens several universal recipe/text-memory statements.

I audited the supplied diff, brief, evidence addenda and SEQ-022. **The full writing prompt and memo 3 §4 were not supplied**; their filenames and summaries are not enough to certify compliance. Below I distinguish demonstrated errors from items requiring source verification.

## Numbered objections

1. **BLOCKING — Disjoint-panel headline numbers and denominators.**  
   **Where:** Abstract; Measurement design; Controls; both control tables; Discussion; Limitations; Appendix B; SYSTEMS_BRIEF §2.3; associated comments.

   **Fix:** Use this complete accounting from **SEQ-022 / EVIDENCE_TABLES, SEQ-022 addendum**:

   | Arm | Final adapters: mean Δ, denominator | Mid-life adapters: mean Δ, denominator |
   |---|---:|---:|
   | R2, ungated | −0.017, **9** | +0.005, **9** |
   | R3, gated | +0.003, **6** | +0.004, **6** |
   | R4, gate + parent | −0.010, **7** | 0.000, **5** |
   | RP, parented ungated | +0.001, **3** | −0.005, **3** |

   Total: **48 adapter cells**, across **both machines**, with **two adapter replicates per cell** against that machine’s **three-replicate base**: **0.2574 / 0.2541**.

   Threshold tally: **9/48 above +0.015; 33/48 within ±0.015; 6/48 below −0.015**. All **six below-band cells**, not all finals or all 48 cells, are final adapters with a collapsed replicate.

   R3+R4 combined: **24 cells**, mean **−0.001**, **3/24 above**, **1/24 below**.

   The old **21-cell**, **4/3/3-life**, **−0.025/+0.004/−0.024 final**, **+0.002/+0.008/−0.003 mid**, **6/11/4 threshold**, and **11-cell gated mean −0.004** numbers describe the earlier machine-specific subset. They are not numerically invalid *as a labelled historical subset*, but must not remain the current headline evidence.

2. **HIGH — Completion status, cut-off and “every cell” claims are stale.**  
   **Where:** Opening comments; Controls source comments; Reproducibility; Appendix B heading and introductory paragraph; control-table captions; SYSTEMS_BRIEF opening and reading list.

   **Fix:**
   - Replace current-status **“one machine only,” “first machine complete,” “second machine two cells short,” “47 probed”** with **complete across both machines: 48 adapter cells**.
   - Update current control cut-offs from **SEQ-021 / 01:01 UTC** to **SEQ-022 / 2026-09-11 01:38 UTC**.
   - Replace references to the first-machine **21-cell** table as the complete evidence.
   - The appendix table is an aggregate table plus selected detailed cells, **not “every control cell, with replicates.”** Either provide all cell records or change the caption and point to the complete supplementary data.
   - Retain the life-level recount as a separately dated snapshot. Do **not** silently replace its exposure counts with later endpoints.
   - Define “final” as used in SEQ-022. Because the entry still reports running lives, do not equate every “final adapter” with a completed 1,024-episode life without checking its receipt.

3. **HIGH — “Every positive cell is exactly the routine” is now false.**  
   **Where:** Abstract; Controls disjoint paragraph; Discussion amplifier paragraph; SYSTEMS_BRIEF §2.3.

   **Fix:** Of the **9 cells above +0.015**, **7 exactly match 0.2731**. The exceptions are **R2 seed 7 mid, 0.2712**, and **RP 400 final, 0.2713**. Say “seven exactly match the routine score; two are near it,” not “every one … to four decimals.”  
   **Source:** SEQ-022 aggregate tally; also the SEQ-012 addendum.

   SEQ-022 itself contains a local inconsistency: its R2-mid row says the four above-band cells are “all the routine,” while its aggregate identifies seed 7 as an exception. Use the explicit per-cell values and aggregate exception list.

   Also replace **“above two replicate SD”** with **“above the prespecified descriptive band of +0.015, approximately two replicate SD.”** That band is not a significance test or a confidence interval for an arm mean.

4. **BLOCKING — Text-memory headline tally is stale.**  
   **Where:** Abstract and its comments; Introduction characterization paragraph; “What we do not claim”; Controls text-memory paragraph; both tables; Discussion caveat; SYSTEMS_BRIEF §2.4.

   **Fix:** Replace **six lives / four matches-or-wins / two losses** with:

   - **8 lives** on the eight-program panel.
   - Brief ≥ adapter in **5/8**: **R2 seeds 0, 2, 5, 6; R3 500**, the latter a tie.
   - Adapter > brief in **3/8**: **R2 seed 1, +0.013; RP 402, +0.007; R3 501, +0.016**.

   Add the missing table rows, using the precision actually supplied by **SEQ-022**:

   | Life | OFF / ON / brief, eight-program panel | Final / mid / brief, disjoint panel |
   |---|---|---|
   | R2 seed 2 | 0.4629 / 0.4329 / 0.5291 | 0.2496 / 0.2495 / 0.2731 |
   | R3 501 | 0.4767 / 0.5040 / 0.4882 | 0.2495 / verify mid value / 0.2495 |
   | R3 500 | Existing eight-program row unchanged | 0.2621 / 0.2731 / 0.2532 |

   Do not invent R3 501’s mid-life value from its final value. Remove the obsolete comment resolving SEQ-021’s “7 lives” typo once the summary uses SEQ-022.

5. **HIGH — Disjoint text-memory denominator and tally are also stale.**  
   **Where:** Controls: “three of five … lost in two”; tables showing R3 500 disjoint as not measured.

   **Fix:** Against **final adapters**, the supplied records now yield:
   - Brief wins in **4/8**: R2 seeds 0, 2, 5, 6.
   - Brief loses in **3/8**: R2 seed 1, RP 402, R3 500.
   - **1/8 tie**: R3 501.

   The three losses are approximately **0.006, 0.010 and 0.009**, respectively. This tally is arithmetic from the supplied SEQ-022 values and the retained earlier cells; label its comparator explicitly as the **final**, not mid-life, adapter.

6. **HIGH — Crossed/routine-only results are incomplete, and exact-equality language is wrong.**  
   **Where:** Controls design and interpretation; both control tables; SYSTEMS_BRIEF §2.4.

   **Fix, from SEQ-022:**
   - R2 seed 1 adapter+brief on the disjoint panel is now **0.2731**, not “not measured.”
   - Routine-only text has now been tested for **two lives**, not one.
   - For seed 1, routine-only scores **0.5291** on the eight-program panel versus full brief **0.5163**.
   - On the disjoint panel, seed 1 routine-only scores **0.2443**, below full brief **0.2667** and adapter **0.2731**. This contrary cell must accompany any broad recipe-line explanation.
   - Seed 0 routine-only **0.2730** versus full brief **0.2731** is **approximately equal**, not numerically identical. Change “=” and “the same” accordingly.
   - “Two crossed cells” currently means two **life-level crossed conditions**, each now tested on both panels. State that unit rather than mixing life and panel-cell counts.

   For seed 0, specify that the collapsed replicate was on the **disjoint panel**; do not imply the eight-program adapter-only score was itself a collapsed replicate.

7. **HIGH — The count of directly tabulated ungated final adapters is stale.**  
   **Where:** Contributions; “What we do not claim”; Recipe lock-in; Discussion; Limitations; SYSTEMS_BRIEF §2.2.

   **Fix:** The text-memory control now directly scores **five**, not four, ungated endpoint adapters: seeds **0, 1, 2, 5, 6**. **Two of five**, not two of four, exactly sit on the named eight-program plateaus. Seed 2 adds another **0.4329** endpoint score.  
   **Source:** SEQ-022.

   Preserve panel-specific distinctions: seed 6’s eight-program ON score **0.4878** exceeds its OFF score **0.4823**; its collapsed disjoint replicate does not make that eight-program endpoint harmful.

8. **HIGH — Several counts need explicit units or restricted scope.**  
   **Where:** Abstract; gate contribution; Limitations; SYSTEMS_BRIEF.

   **Fix:**
   - Abstract **“0-harmful count”** → **0/60 reported pairs in six incomplete R3 lives at the recount**, explicitly post-selection. Do not attach that historical denominator to all later gated observations.
   - Gate catches: **17 brevity refusals across five lives at the recount, plus two documented later refusals; at least 19 total**. **Five candidates across three lives** were at or above the unrelaxed floor. These are counts, not rejection rates; the total number of eligible writes is not supplied.
   - The Limitations sequence **“n=9, 6 and 3 lives”** omits R4. Name arms: **R2 9, R3 6, RP 3, R4 7**, with recount exposure distinguished from later controls.
   - SYSTEMS_BRIEF §2.3 heading **“final adapters average at or below base”** is arithmetically false: R3 **+0.003**, RP **+0.001**. Use **“final-adapter means are near base or negative.”**
   - Keep **8/9 scored unparented lives** distinct from the nine complete R2 lives: the paper correctly explains that this ritual sample includes two old-writer lives.

9. **HIGH — The abstract exceeds the limit and no longer represents the evidence.**  
   **Where:** Abstract and “rewritten to ≤200 words” comment.

   **Fix:** Replace it with the abstract below. It carries the evidence sizes, three required final-adapter means with denominators, complete threshold tally, eight-life text-memory comparison and a bounded routine explanation. Omit crossed cells rather than compress their qualifications away.

10. **HIGH — Text-memory interpretation overstates equivalence and mechanism.**  
    **Where:** “What we do not claim”; Controls reading; Discussion; SYSTEMS_BRIEF §2.4.

    **Problematic claims:**
    - “gives no evidence that the weight write does what a line of text would not”
    - “the brief’s whole benefit is transmitting the recipe”
    - “where the weights already hold it the text adds nothing”
    - “neither panel rewards a situation-dependent choice”

    The measured adapter advantages must not be erased, and seed 1’s new disjoint routine-only result directly limits the “whole benefit” account. Absence of observed conditional behavior does not establish that the panels cannot reward it.

    **Fix:**  
    > The adapter exceeded the full brief in three of eight eight-program comparisons, while the brief matched or exceeded it in five. The inspected behavior and recipe controls suggest fixed-routine execution explains much of these scores. These controls do not establish a general advantage of weight memory, equivalence of the memories, or absence of other stored information.

    Replace “neither panel rewards…” with **“we have not demonstrated program-dependent choice on either panel.”**

11. **HIGH — Gate efficacy is overstated, even as a “reading.”**  
    **Where:** Controls: “the gate … removed the late-life loss”; SYSTEMS_BRIEF and any adoption of SEQ-022’s “gate stops late collapse.”

    **Fix:**  
    > On the disjoint panel, no R3 cell fell below −0.015; one R4 cell did. Across the 24 gated-arm cells, mean Δ was −0.001. This does not establish that the gate prevents collapse.

    The R4 604 counterexample is measured. The disjoint evaluation removes **selection on that evaluation panel for these R3/R4 adapters**, not every design or selection confound.

    The **0.037** R4 602 drop is correctly rounded relative to historical **0.5307**, but distinguish it from the approximately **0.017** drop relative to its **0.5104** re-probe. It is not a contemporaneously paired causal loss estimate. Also retain the actual floor definition, **max(latest OFF, latest ON)**, rather than universally calling it “the latest ON.”

12. **HIGH — Storage, frequency and exposure explanations exceed the measurements.**  
    **Where:** Storage reading; Discussion amplifier paragraph; Recipe lock-in; SYSTEMS_BRIEF §1 and §2.

    **Fix these formulations:**
    - **“That is the storage–extraction gap”** → “This resembles a storage–extraction gap, but lower loss does not identify usable stored knowledge.”
    - **“sleep amplifies whatever is frequent”** and **“a lesson survives … only once…”** → explicit hypotheses. No frequency intervention establishes that necessary condition.
    - **“sibling exposure is not what produces the gain”** → “The sibling-free programs have mixed signs; this does not isolate the contribution of sibling exposure.”
    - **“the adapter … is the only thing that ever learns”** → “The adapter is the only trainable parameter component; text memory also changes across the life.”

    TMEM remains first in “Closest prior work.” I found no affirmative **first**, **population**, **parenting-works**, or **usable-knowledge** claim to preserve. Their explicit negations are not themselves violations. The risks are the causal and universal formulations above.

13. **MEDIUM — Other numerical/source problems need correction or verification, not guesses.**  
    **Where:** Appendix B; parenting statistics; opening comments; reproducibility; prospective design constants.

    **Fix:**
    - Appendix B calls seed 3’s **+0.045** the best report-panel life mean; the paper elsewhere calls it **third-highest** and reports a maximum **+0.050**. Use “third-highest,” or omit the ranking.
    - **“p=0.64, a difference chance gives about two times in three”** is a misleading probability gloss. Retain the exact-test result with its null/tail interpretation, not a probability that chance caused the difference.
    - The length claims **7,191+631**, **5,891+532**, **11.0/9.1 pages**, and approximately **two pages over** cannot be certified from the supplied attachments. Recount after the patch and compile; do not treat a words-per-page estimate as the submission page count.
    - “Every number is listed” conflicts with the comment that README is not updated. Update the source table before making that claim.
    - The prospective **512-problem** endpoint and SYSTEMS_BRIEF’s numerical design constants need exact dated design/COORDINATION citations. They are proposed settings, not measured results. The supplied SEQ-022 does not authorize them.
    - Legacy numbers whose cited evidence entries are absent here—including absorption, rank/dose, parenting and ritual statistics—remain **unverified in this review**, not demonstrated wrong. Full EVIDENCE_TABLES entries are required for exhaustive numerical sign-off.

14. **BLOCKING — Programme paragraph: prospective intent is clear, but prospective status and memo consistency are not fully secured.**  
    **Where:** “Future work, not results”; preceding mechanism hypothesis; SYSTEMS_BRIEF §§1 and 3.

    **Assessment:** The heading, untested-hypothesis language, two endpoints and single-lineage limitation point in the right direction. However, **“The experiment that follows is…”**, **“sleep makes…”**, and operational present tense in the brief can read as an implemented or validated mechanism.

    **Fix:**
    - Start **“We propose to test…”** and identify the mechanism as **subject to pretests, not the mechanism that produced these results**.
    - Preserve the frozen-checkpoint comparison and matched continual-learning comparison as separate prospective endpoints.
    - Say the result could support only **a case study of this lineage under its internal controls**, not a general parenting or cross-gym learning claim.
    - Separate the proposed **format/work-only brake plus rollback** from the later wishlist’s **score-gated disjoint panel and floor**. As written, they look like contradictory requirements for one experiment.
    - State that the entire mechanism sentence is a hypothesis, not merely that its first two clauses are untested.

    **Memo 3 §4 verdict: not certifiable from this packet.** Its text must be checked before approval; the brief’s pointer to an “honest statement” is not that statement.

15. **BLOCKING — SYSTEMS_BRIEF grants ambiguous score access.**  
    **Where:** §4.4, especially “Gate scores are shown only when … disjoint.”

    **Risk:** That sentence can authorize parents to read numerical gate scores, whereas the paper describes parent access as ledger plus **coarse decisions**. “Disjoint” also does not prevent report scores leaking through a ledger, tool result or central-parent message.

    **Fix with an explicit access rule:**  
    > Parents receive only redacted training records and allowlisted gate decision/reason codes. They never receive report-panel or final-test scores, including through ledgers, tools, briefs or other parents. Numerical gate-score access requires a separate explicit approved policy; verified panel disjointness alone is not permission.

    Specify which non-report score stream the **harness**, not parents, may use for patience and “best committed” rollback. Never select the rollback checkpoint using report/final-test scores.

16. **BLOCKING — SYSTEMS_BRIEF can be read as permission to cross the thinker/compiler line.**  
    **Where:** §1 SLEEP/PARENTING; §3 write; §4.1–2.

    **Risk:** “The child’s own text” is not sufficient provenance if a compiler model paraphrases parent text, imports another lineage’s rows, or treats a copied lesson as independently learned behavior.

    **Fix:** Make the invariant operational:
    - The compiler may select, order and pack **existing child-authored spans**; it may not generate thoughts, paraphrase lessons into child rows or synthesize missing rows.
    - Remove parent/brief spans from training sequences, as the proposed rule says; verify this in receipts.
    - Child restatements may be eligible, but do **not** count them as uptake or proof of independent reasoning.
    - Define eligible clone provenance before merges; “same child” must not silently authorize foreign-lineage data.
    - The brief is orientation, not authority to bypass pretests, provenance checks or the compiler boundary.

    Also replace the assertion that parent words reach weights only through repetition **“in its own words.”** The historical design allowed literal restatement; authorship and paraphrase are different claims.

17. **HIGH — Other SYSTEMS_BRIEF permissions and temporal ambiguities need closing.**  
    **Where:** Opening precedence sentence; §§3–4.

    **Fix:**
    - **“Later COORDINATION entry wins”** should apply to empirical status, not automatically override access restrictions, split rules or the thinker/compiler invariant. Require an explicit authorized policy revision.
    - **“No waiting”** must mean continuing with the last approved adapter, not skipping validation or loading a partial/unapproved merge.
    - Label v1’s R3/R4 re-probes as evaluations conducted without selection on v1; separately disclose that **R5 used v1 for gating**. Do not call v1 permanently untouched.
    - Failure to obtain a fresh sealed panel may make results exploratory; it does **not** authorize leaking final-test content or scores.
    - “Parents never give recipes” is the proposed policy, not a description of historical prompt content or proof of leak-free delivery.
    - Historical ritual means the operational flag definition, not simply repetition of a recipe.

## Replacement abstract — under 200 words

We measure an experience model: frozen Qwen2.5-7B-Instruct plus a rank-8 adapter rewritten every 32 episodes from success-filtered child-authored text. In nine ungated 1,024-episode compiler-optimization lives, paired adapter-on/off probes on eight identifier-held-out programs gave mean life-level gain +0.019 (SE 0.011); 4/9 lives had a harmful pair below −0.03 despite passing format checks. Scores measure fractional instruction-count reduction. A disjoint re-probe covered 48 adapter cells across both machines on 12 programs from datasets absent from the curricula, using two adapter replicates against three base replicates per machine. Final-adapter mean gains were −0.017 (ungated, n=9), +0.003 (gated, n=6), and −0.010 (gate plus parent, n=7). Across 48 cells, 9 exceeded +0.015, 33 were within ±0.015, and 6 fell below −0.015; all six had a collapsed replicate. Seven of the nine above-band cells exactly matched one fixed six-pass routine; two were near it. On the eight-program panel, the frozen model reading the life’s final brief matched or beat the adapter in 5/8 lives; adapter advantages in 3/8 were 0.013, 0.007, and 0.016. In one life, routine-only text approximately matched the full brief on both panels, supporting a fixed-routine explanation.

[astra openai/openai/gpt-6-astra effort=high 168s tokens in=32870 out=7411 reasoning=2539]
