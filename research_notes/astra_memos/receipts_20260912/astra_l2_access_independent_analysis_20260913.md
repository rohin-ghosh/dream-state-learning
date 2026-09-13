# Independent L2 access analysis — attempt2 / v2

2026-09-13 UTC. **EDITSTOP. Local stored-evidence analysis only.**

## Decision summary

The receipts support **substantial removal of OFF's action0 confidence bias, some modest train-view discrimination after fit2, and weak/non-robust strict keyed choices**, with a remaining wording-sensitive access effect. They do **not** isolate a purely access-only failure, and do not support a blanket “no learning” conclusion. A matched three-learner-seed LR-only comparison is justified as a bounded diagnostic if Main chooses it, **not as a proven repair or a replacement for existing native results**.

The previously suggested `ln(2)/13` explanation is now only a useful illustrative scale. Actual first-position and complete-continuation measurements supersede any assumption that exactly one token accounts for all uncertainty.

## Integrity and independent checks

- Supplied report SHA256 verified: `1d3d33347c246f0e243343d4f18f01b4dfa2c35b669b97cb64d28c3fff259aa1` for `/tmp/astra_l2_access_report_20260913_attempt2.json`.
- Supplied tar SHA256 verified: `e6b80249420b37264981339d84c1744bf12577594c01910e7be959b0bfc2360e` for `/tmp/astra_l2_access_attempt2.tar`. Its `report.json` is byte-identical to the standalone report. Members were read in memory, not extracted. This is not a new full producer/custody audit.
- All three archived worker JSON payloads match `report.worker_files`: OFF `eb14b16805873a7526b22eb7cebb87f219138ccd8d3ac5fdec4a58170502fcc9`; fit1 `e3ad190e31301f3a9da60f3373bec0ef1134f94adb57e633e348cb71b32336a8`; fit2_PROMOTE `c774318e66214a26eaf71a6e3a91bc4ac0f41c13e62bd92046081d1565bd6961`.
- Worker diagnostic-source pins match local `/tmp/astra_l2_access_probe_20260913_v2.py`: `a38a089fae5b09b53415655dd8e5346dfbb0f597f34b35cd49921a98b50e22c1`. Worker source-file pins match the frozen L2 snapshot; collection pins match the existing collection file. Workers agree on case hash `4644578efc36a24f181a1adffd31fabdcac07e936723b435c72b532c87eeea21`, plan hash and base hash. Case-hash agreement is not an independent retokenization.
- Independently recomputed **96 paired rows / 192 candidate continuations** from stored worker log probabilities: first-divergent and full-sum margins, exact ties, choices, correctness, full/first gold NLL, panel counts, and report loss-category aggregation. All checked reductions agree. Truth indices were checked against the original accepted L2 tar's `world.json`, not merely copied from the report. Detailed loss-category partitions beyond first/full were aggregated from report rows rather than independently reconstructed from token positions.
- Both adapters' stored converted/actual tensor inventories agree exactly, **392 records each**. This verifies stored record consistency, not independent loading of those tensors today. Workers record zero updates, 64 forwards each, 192 total.

V2 source `verify_adapter_routes` at line 236 checks actual `BaseTunerLayer` instances, their Boolean `disable_adapters`/`merged` properties and active `default` routes. `native_model` at line 246 checks saved/loaded state records, freezes parameters and enters eval mode. This addresses the v1 mistake of interpreting a model-level method as a Boolean. V1 is not diagnostic evidence of biological/learner failure. Main reports 20 CPU plus native-CPU regression passes; this analysis did not rerun them or independently exercise PEFT. No remaining mount error is demonstrated by these stored v2 records, but HF/vLLM numerical parity is not established by a route assertion.

## What changed, conditioned on class

Here action0 is `move_54b50509ad73` and action1 is `move_7bc22e03caee`. Each view has eight truth0 and eight truth1 items. “First correct” compares the two candidates at their first divergent token; ties are not counted as correct. These are not full-vocabulary greedy generation counts.

| State / view | First strict correct; exact ties | Full-sum correct | First gold NLL, all | First gold NLL, truth0 / truth1 |
| --- | --- | ---: | ---: | --- |
| OFF / train | 8/16; 0 | 8/16 | 2.784746 | 0.002994 / 5.566498 |
| OFF / readout | 8/16; 0 | 8/16 | 2.077657 | 0.012397 / 4.142917 |
| fit1 / train | 8/16; 1 | 9/16 | 0.689233 | 0.611835 / 0.766631 |
| fit1 / readout | 8/16; 0 | 8/16 | 0.670401 | 0.469744 / 0.871057 |
| fit2 / train | 8/16; 5 | 12/16 | 0.638386 | 0.589727 / 0.687045 |
| fit2 / readout | 8/16; 0 | 8/16 | 0.675427 | 0.450832 / 0.900022 |

OFF chooses action0 for **all 16 keys in both views**, with action0-minus-action1 first margins approximately 5.25–7.0 in train and 3.5–7.0 in readout. Its aggregate 8/16 hides a severe class asymmetry, not an unbiased uncertain binary predictor.

Fit1 train chooses action0 on 15 items and ties one; readout remains all action0. The large NLL gain is principally compatible with reducing extreme confidence in the wrong action on truth1 while sacrificing confidence on truth0. That is a real measured distributional change, but is not sufficient evidence of stable key-specific acquisition. In fit1 the train-form NLL is 0.683364 on the eight exposed old keys and 0.695102 on the eight future/unexposed keys: a broad output-bias/calibration change can benefit untrained keys too. “Train view” means **training-form wording**, not that all 16 keys were in fit1's corpus.

Fit2 train first choices are action0 on eight, action1 on three, and ties on five. Class-conditioned strict correctness is 6/8 for truth0 and 2/8 for truth1; there is one truth0 tie and four truth1 ties. Its mean gold first margin is +0.234375 for truth0 and +0.015625 for truth1. This permits modest weak-margin key association, not reliable acquisition. Fit2 readout remains all action0: truth0 first margins are positive 0.25–1.25; truth1 items also favor action0 by 0.125–0.5. A positive aggregate gold margin or NLL below ln(2) can coexist with an unchanged all-action0 thresholded decision.

The fit2 train first counts split **old3/8, new5/8**, versus full-sum **old5/8, new7/8**. Neither the 12/16 full figure nor unchanged aggregate first8/16 should erase those distinctions. Fit2 train NLL improves relative to fit1, but readout NLL slightly worsens (0.670401 → 0.675427): this is a mixed acquisition/access picture, not a single directional improvement in every metric.

## Ties, sequence length and weak-margin accounting

V2 `pair_metrics` at line 347 uses **exact zero**, not an ambiguity tolerance. All five fit2 train first ties resolve toward action1 under complete-sequence sums. Four become correct and one remains incorrect, explaining the increase from **8 strict first hits to 12 full-sum hits** without four additional robust first-position decisions. The full margins on those tied items range from about **−0.000710 to −0.0000396 nats**. Do not round them into strong choices, assign ties half-credit without declaration, or add a post-hoc epsilon to manufacture a different headline.

Action0 has **14 target tokens including EOS**, action1 **12**. Their shared prefix is two tokens; the shared suffix is EOS. First-divergent comparison, total log-likelihood and length-normalized mean log-likelihood are distinct statistics. On those five first-tied items, mean log-likelihood actually favors action0 (roughly +0.00820 to +0.00825), unlike total likelihood. Unequal lengths make that reversal unsurprising: it is not evidence that either normalization recovers the correct semantic estimand.

Identical EOS token identity does not make its conditional probability identical: the two complete action histories differ. The remaining action tokens and EOS can break a first-position tie by tiny amounts. Do not assume every post-divergence token is a shared, neutral suffix. Observed first margins include many exact multiples of 0.125; this is compatible with finite-precision effects, but this pass has not established their numerical cause or tested higher-precision forwards. `hf_forward` converts selected logits to float before log-softmax; that does not restore precision already lost in model computation.

## HF teacher forcing versus original vLLM endpoint

The probe scores supplied candidate continuations and includes EOS; it does not generate its own continuation. Its first comparison restricts attention to two candidate tokens, and full scoring conditions later probabilities on already supplied action histories. A candidate-sum preference is not greedy decoding, a full-vocabulary top1 measurement, or proof of native generation parity.

The report preserves the original vLLM endpoint counts: each panel has 16 legal outputs, old4/8 and new4/8. Do not replace them with HF fit2 train12/16. Conversely, unchanged vLLM accuracy does not negate the measured HF distributional changes. Current evidence supports investigating both small acquisition margins and a prompt/access boundary; it does not warrant a purely access-only fix premised on a strongly acquired exact-prefix mapping. The original `endpoint.native_verified=false` scope and all prior claim limitations remain unchanged.

## Is a matched three-seed LR-only contrast justified?

**Yes, as a predeclared diagnostic—not as a proven repair or an automatic launch.** Exact-training-form choices are still weak/tied, so “only paraphrase access is broken” is not established. The inherited 1e-4 writer supplies a concrete recipe precedent, but its representation and exposure differ and do not prove a causal LR remedy. Three learner seeds help expose optimizer sensitivity, not establish a population success rate.

For Main's experiment choice: pair LR3e-5 versus 1e-4 within learner seeds 0/1/2; hold base bytes, world/truth, admitted child bytes, mask/EOS, rank, optimizer, update count, batching and assessment method fixed. A small isolated fit1 comparison would be **six fits ×20 updates =120 total updates**, with the same eight-row corpus and 20 presentations per row in each cell. This is a proposed aggregate budget, **not permission under the original root's 100-update cap**. If instead Main runs six full three-fit loops, that is 18 fits / up to600 updates and a different scope; later branch-dependent corpora then confound a fixed-data LR interpretation. Do not silently conflate those designs or reuse controls from unmatched conditions.

Report every matched seed pair with class-conditioned old/new first NLL, signed margin distributions, exact-tie counts, and full-sum statistics separately; preserve original vLLM generation as its own endpoint. No best-seed or best-checkpoint selection, new tie threshold, changed target serialization, or response-based training-data selection. A gain confined to tiny tail tie-breaks or weaker action0 bias is not a robust keyed-acquisition repair. Main owns native preparation, evaluation budget, experiment choice and any future implementation; none is duplicated here.

## Limits and scope

Single completed L2 learner seed, small balanced key panel, stored finite-precision scores, no independent model execution. Row/pin/reduction consistency is not a new native validation, full cross-engine parity test, formal uncertainty analysis, or clean causal attribution of all distributional changes. No automatic scientific pass, retention/generalization claim, G1 qualification, H1/H2 claim or promotion follows.

Analysis began **06:45:57 UTC**, bounded to approximately four minutes. Local SHA256, JSON/tar reads, source inspection and arithmetic checks only. No model imports, GPU, network, Git, launcher/code edits, new tests or producer changes. Only this document is written.
