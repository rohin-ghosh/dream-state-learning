# Actual-record readout: independent raw reduction — PASS, bounded claims

**Authorship:** I authored the formation/write collectors and saved-weight audit, not the readout driver/collector. Main’s summary was visible beforehand: this is an independent raw implementation/recount, not a blinded or wholly fresh-author audit. No native replay/tokenizer/model, GPU, SSH/network or Git actions; no run repair or rerun.

**Custody:** capsule SHA256 `f8f2bb688da189ebb8f70c67725f1c008db49d6c5b2800abdc58a0dd4fcb7458`; all **232** members match validation and extracted bytes. Plan SHA256 `cdb71865359498ca0f75db57566e638b667d2e849cc11c9cbd45dd6bfbb97375`. Independently reconstructed requests, current-task histories, world outcomes, record verdicts, balanced quiz panels/labels and every event; only then compared sealed events/results. All comparisons pass. Native exact token audit PASS is corroborating recorded evidence, not a tokenizer audit rerun here.

## Raw outcomes and denominators

| Cell | Executed calls (wake + record) | Quiz correct / fixed 24 | Valid quizzes / 4 | Faithful / allotted 12 | Faithful / executed records |
|---|---:|---:|---:|---:|---:|
| OFF | 32 (20 + 12) | 7/24 = .291667 | 4/4 | 9/12 | 9/12 |
| P_ON | 29 (18 + 11) | 6/24 = .25 | 3/4 | 10/12 | 10/11 |
| A_ON | 29 (18 + 11) | 6/24 = .25 | 3/4 | 10/12 | 10/11 |

**90 calls executed, not 96.** The latter is a ceiling. There are 34 executed TRYs, 10 reveals, 10 scored quiz submissions, 34 record calls, and two protocol-invalid wake responses. Primary quiz contrasts: P−OFF = A−OFF = **−1/24**, P−A = 0. Trained-cell rule5 contributes a prescribed zero, **not six observed wrong answer labels**; dropping that failed task and using 6/18 would change the estimand.

Independent rule2/3/4/5 truth strings: **FTFFTT / FTTFTF / FFFTTT / FTFTFT**. All cells submit **TFTFTF / TFFFFT / TFFFTF** on rules2–4, scoring **2/6, 1/6, 3/6**. OFF submits **TFFFTF** on rule5, scoring **1/6**; P/A submit no scored rule5 quiz.

### Rule5 failure and raw equality

P/A call0028 emits `ACT: TRY 4,8,12`, then a blank line, `PREDICT: F`, another blank line, and `ACT: QUIZ ?`. **Two action markers** invalidate the whole response before world execution. The third TRY is not executed; no corresponding record/reveal/answer occurs. The misplaced prediction is after the first ACT, not a valid pre-TRY prediction. This is not truncation: **zero cap hits**; all 90 responses have `finish_reason="stop"`. The ordinary reveal’s `INVALID: quiz needs 6 answers…` world text is the panel-display mechanism, not this protocol failure.

Equality was checked, not inferred from counts: **all 29 aligned P/A prompt strings, response texts and output-token sequences are identical**. Their adapter hashes and timing receipts differ. Per-task/tick generation seeds are shared by design; matching outputs do not establish identical adapters or latent states.

## Probe choices, predictions and record fidelity

All probes are retained in JSON. Relative to OFF, P/A change rule2’s second/third probes from `(2,4,6)/(0,3,6)` to `(4,5,6)/(0,1,2)`; all still satisfy the average-of-ends rule. Rule3 and rule4 probes are unchanged. Rule5’s second probe changes `(3,5,7)` to `(3,6,9)`, both zero-free; OFF executes `(1,3,5)` third, whereas P/A’s emitted `(4,8,12)` is rejected. Thus each cell tests only true outcomes on rule2 and only false outcomes on rules3–5; these changes supply no observed positive/negative discrimination within a task.

Each cell makes **eight valid explicit pre-TRY predictions, all F; six are correct (6/8)**. OFF: 8/12 executed TRYs explicit, four null. P/A: 8/11 executed TRYs explicit, three null. There are no ambiguous predictions on executed TRYs. Counting all TRY-containing responses restores a denominator of 12 per cell: eight have valid pre-ACT predictions. P/A have nine with a PREDICT line *anywhere*, but the ninth belongs to the invalid response described above and must not inflate compliance or competence.

All cells’ rule2 third record incorrectly labels a null prediction as `matched` rather than `unavailable`. OFF additionally loses the explicit F prediction in rule3’s and rule4’s first records, writing null/unavailable; P/A preserve it. **The faithful-record increase is not increased prediction competence:** valid prediction count, labels and 6/8 correctness are unchanged. Records are generated from prompts already displaying the actual observation and prediction fields.

## Load context, accounting and limits

Reconstructed all 90 prompts exactly: fresh task history, empty parent prefix, no parent/restatement calls, no record feedback into wake, no record training. Three distinct worker PIDs and isolation/spec/identity receipts agree; this is prompt/process separation, not OS filesystem isolation. Base hashes agree across plan/spec/capture. OFF loads no adapter; P/A identities match lineage hashes: P weights `c9f1fa5cd3391b407a0102856faa4926d6a550c799979026d399b55bd979868c`, A weights `5ea89adcf57956867f7bd7014ede004df0874c8ca82c4e72fc485ff121c681ab`. Weight bytes are excluded; this verifies hash **agreement**, not a new native weight rehash or model-origin authentication.

Raw tokens: OFF **11,296 input / 677 output**, P **10,107 / 634**, A **10,107 / 634**; total **31,510 / 1,945**. Executed output ceilings total **25,800**, not the 27,600 maximum. Generation **73.549066s** is inside supervised workers **493.982361s**, inside controller **595.137126s**, inside launch-to-full-release **642.893684s = 10.714895 A40 min**. UUID/XML/release seals agree; release **September 12, 2026, 21:50:03.514265 UTC**. Collection takes **53.982670s**, with **40.602708s** elapsed at release: clocks overlap, and nested role/by-arm usage is not counted twice.

This selected-record, one-shared-OFF exploratory readout shows no quiz improvement here. It does not establish latent erasure, adapter necessity, general adaptation/G5, utility, or a causal explanation for the errors.

Artifacts: analysis `.py` SHA256 `ab9cda5e0d6bbcfa882c5268bc9357c34859cac079353e48761f2038d38134bc`; `.json` SHA256 `8a8312d2f1b6b11b1b9e2b4887ed993657503304a657e54d9d265ac909c69bb0` (both `/tmp/astra_rulegame_record_readout_independent_analysis_20260912.*`). JSON retains every raw response, action/prediction/record code, quiz labels, probes, identity and cost counts.

**EDIT-STOP.**
