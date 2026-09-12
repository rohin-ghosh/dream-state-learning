# Process-v2 parent-free readout: independent raw review

**2026-09-12 — PASS: raw replay, denominators, custody and arithmetic agree. EDIT-STOP.**

Recounted **95 actual calls, not96**: OFF32, P_ON32, A_ON31. All three complete captures were supplied and hash-verified before scoring. Reconstructed prompts/current-task histories, request seeds, actions, world replies, records, deterministic quiz panels and labels from raw captures; compared the resulting events and metrics with sealed results and collector reports only afterward. **No discrepancies found.** Main reads the sealed aggregate separately; no claim of a blinded or fresh-author review.

## Results, including failed-task zeros

| Cell | Wake + record calls | Rule2 / Rule3 / Rule4 / Rule5 correct, each /6 | Quiz fixed /24 | Valid quizzes /4 | Faithful records / actual / allotted |
|---|---|---|---:|---:|---|
| OFF | 20 +12 | 2 /1 /3 /1 | 7/24 =0.291667 | 4 | 9 /12 /12 |
| P_ON | 20 +12 | 5 /1 /4 /2 | 12/24 =0.500000 | 4 | 5 /12 /12 |
| A_ON | 19 +12 | 2 /2 /2 /0 | 6/24 =0.250000 | 3 | 10 /12 /12 |

Prespecified exploratory quiz contrasts: **P−OFF =+5/24 (+0.208333); A−OFF =−1/24 (−0.041667); P−A =+6/24 (+0.25).** P's gains versus OFF by rule are +3,0,+1,+1. A's lower aggregate includes an invalid task, not six executed wrong answers. The fixed denominator remains24: reporting A as6/18 would change the assay.

A_ON rule5, tick4/call0030, after three executed probes, outputs:

> PREDICT: The rule might be that the sum of the three numbers must be less than 10. Let's test this hypothesis with the quiz.

There is **no canonical ACT**, so the exact reason is `missing canonical ACT`; no quiz reveal or final quiz follows. The task contributes0/6. This explains the one unexecuted wake call, not a missing capture or technical failure. All95 responses finish `stop`; none reaches its400-token wake or100-token record cap. No TRY-containing response is protocol-invalid; the sole invalid action is this later prose response.

## Prediction, probes, and records are different endpoints

| Cell | PREDICT-emitting wake / all wake | Valid pre-TRY prediction / executed TRY | Correct / valid predictions | Correct / allotted12 | Null / ambiguous executed predictions |
|---|---:|---:|---:|---:|---|
| OFF | 8/20 | 8/12 | 6/8 =0.75 | 6/12 | 4 /0 |
| P_ON | 12/20 | 12/12 | 9/12 =0.75 | 9/12 | 0 /0 |
| A_ON | 16/19 | 12/12 | 9/12 =0.75 | 9/12 | 0 /0 |

All12 TRY responses per cell are valid executions. OFF's four nulls are absent pre-action predictions; do not exclude them from coverage. A's extra four PREDICT emissions are three quiz-reveal calls plus the invalid prose call, **not four additional valid probe predictions**. Every emitted prediction attached to an executed TRY precedes it. BOOT explicitly requests PREDICT, so this is not unprompted cognition.

Each cell executes12 probes: three distinct triples within each task, zero within-task repeats. The sum “12 distinct” is **task-local**, not12 globally unique triples: unique triples across the four rules are OFF8, P4, A3. OFF uses varying paths; P largely uses (1,2,3),(2,3,4),(3,4,5); A uses (1,2,3),(4,5,6),(7,8,9) in all four tasks. Each cell observes3 True and9 False outcomes. P predicts F on every probe, attaining9/12 exactly as an all-F policy would on those observed paths. OFF's eight valid predictions are also all-F. Thus increased prediction coverage/correct counts do **not** establish improved conditional prediction accuracy: it is0.75 in all cells. Probe diversity does not establish information gain.

Record failures independently reproduce the raw judged reasons:

- OFF:3 failures—rule2 tick3/call0005 has `relation mismatch` (null prediction falsely called matched); rule3 tick1/call0009 and rule4 tick1/call0017 have `prediction mismatch`.
- P:7 failures, all `prediction mismatch`, at calls0009,0011,0013,0017,0021,0027,0029: a real F prediction is replaced by null in the record.
- A:2 failures, both `prediction mismatch`, at calls0013 and0021. Faithful by rule is3,2,2,3.

Faithful totals P5/12 versus OFF9/12 and A10/12 run opposite the quiz ordering; **do not call record faithfulness prediction competence or a uniform process improvement**. Records do not enter later wake history. All raw outputs, reconstructed events, probe paths, quiz triples/true/submitted vectors, record errors and fixed denominators are retained in the JSON. Of31 task/role/tick-aligned P/A calls, zero have identical text and four have identical prompt hashes; P's extra rule5 tick5 wake is retained separately, not zip-truncated.

## Identity, isolation, and training scope

The frozen readout is process-v2 **context distillation of complete own raw wake plus EOS**, not the earlier raw-RECORD objective. It evaluates rules2–5, excluding formation rules0/1. One shared OFF has no adapter; P/A have their corresponding distinct saved adapters. Plan/spec/backend identity hashes agree; workers have fresh task histories, zero parent/restatement calls, empty task prefix, no RECORD-to-wake feedback, and no online updates. Raw prompt reconstruction verifies those boundaries for these captures, not universal semantic nonleakage.

Bound writer metadata records12 updates per arm,24 row presentations,20,185,088 trainable parameters. P versus A target exposures are **384 versus372 tokens**, comprising360/348 raw-wake plus24 EOS each; input exposures9120/9096, padded9120 each (padding0/24). Natural unequal token lengths are retained: this is not a token-matched objective comparison. Training receipts are lineage evidence, not a new fit or source-material semantic audit.

Readout source root ends in `4c3064c1c3eef068951e9c3b2ca46630754564e7`; pinned driver/source text and frozen syntax-helper ASTs agree. Plans retain `UNRESOLVED_LOCAL_HASHES_ONLY` and false model-authentication/clean-lineage/semantic-certification claims. Native token decoding and weight validity are **bound receipt evidence**, not newly executed native checks or rehashed weight bytes.

## Custody and nested costs

Verified Main's capsule hash, all **268 unique regular metadata members**, validation inventory, safe paths/no links or duplicates, and no weight/bytecode payloads. Also cross-checked262 precollection input hashes, source/plan/capture/controller seals, collector metrics/contrasts against the raw recount, and the predecessor write-release hash. Three sequential owned workers have successful supervision/group cleanup and backend closure. Controller PID255725 and GPU2 UUID `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1` bind launch/isolation/release; full-release XML has no GPU processes.

| Cell | Input / output tokens | Backend-ready elapsed s | Raw call intervals s | Supervised worker s |
|---|---|---:|---:|---:|
| OFF | 11296 /677 | 67.195 | 20.329 | 151.037 |
| P_ON | 11368 /709 | 73.931 | 30.076 | 168.295 |
| A_ON | 10882 /734 | 84.709 | 30.087 | 179.959 |

Totals: **33546 input,2120 output tokens;95 calls;27200 call-specific output-token ceiling** (maximum planned96-call ceiling27600). Generation80.492s is inside worker499.292s, inside controller1078.610s, inside launch-to-observed-release **1217.237s =20.287 A40-min**. The579.319s controller-minus-workers interval is accounted outside workers, not attributed to generation or a particular CPU task without further profiling. Backend-ready timings are elapsed initialization-to-ready, not pure model-load measurements.

Launch: **September12,2026 22:58:48.818483 UTC**. Full release observed: **23:19:06.055830 UTC**. Collection228.588s fits its300s cap and overlaps these reservation windows: **do not add it again**. Controller satisfies1800s inclusive/140s-cleanup bounds; worker600s, load180s and call120s checks pass. This cost is the readout stage, not the full formation/write/readout cycle and not an adult-learning-cycle rate.

## Interpretation and independence

P has a positive observed exploratory quiz contrast here, not demonstrated general process-learning efficacy. Its12/24 also equals the constant-T or constant-F score on the balanced quiz panels; this is a descriptive benchmark, not a significance test. One selected-material pair, unequal target exposure, shared OFF and four fixed tasks do not justify generalization or a causal mechanism. No operational-parenting, clean-lineage, G3/P1/G5/H1/H2 or freeze promotion; no retuning, alternate-denominator rescue, or rerun.

I authored related collectors, saved-weight auditing and the earlier record-readout raw analysis; **Planck authored this process driver**. The action parser/record judge are shared frozen code (archived AST equality checked), while world truth, raw prompts/history, scores/denominators and costs are independently reconstructed. This is not fully independent syntax implementation or a blinded/fresh-author review. Sixteen preparation fixtures PASS; actual complete-capsule audit and supplemental custody comparisons PASS. No model/native/tokenizer/GPU/SSH/network/Git operations; only assigned review files changed.

### Principal SHA256 pins

- Capsule: `bbd61be6bb2cb88b36779fc9d1f58eaa5b60570812f8a3221f00e35b6eeab037`
- Readout plan (derived inside that pinned capsule, then seal/custody checked): `8b0f23858427d57b579688bcc06dbae4768b9bbbc2198660d1f1dbe31f092323`
- Write plan: `67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44`
- P/A weight receipt hashes: `c7976a0c035e57ad193790c895a8b6203deb1cba6d2711388c33584c55959dbb` / `7f859e21530bef1ea000ae266a124ad3a0f06ebcdd3784c319d8f1ecff2637e1`
- Readout driver: `46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46`
- Review script: `4501dd019f1fa8eed88880641e666e2ffe5d611fc60576feb68a050244a1b14a`
- Full raw-result JSON: `60f998fdbcb8dfdee0f77e92c93502a47481422f71e45ffd191ef812bce49282`

Artifacts: `/tmp/astra_process_readout_independent_review_20260912.py` and matching `.json`/`.md`. No changes to archived captures or other owners' work.
