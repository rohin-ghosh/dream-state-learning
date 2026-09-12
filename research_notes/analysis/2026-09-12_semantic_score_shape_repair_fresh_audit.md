# Fresh audit: semantic score-shape repair

Date: 2026-09-12

Audited tree: `02a772f8376f431274699d121f691e80e5e6ea0e` (the relevant files are unchanged through `origin/main` `4c73685b`)

Scope: `semantic_carrier_diagnostic.score`, the saved-request construction/reducer/model loader, `gpu/astra_semantic_rescore.py`, and their focused tests. No model or GPU job was run.

## Verdict: REWORK

The core scorer repair is **causally coherent as a pair-specific, fixed-total-length BF16 scoring convention**. It is not yet evidence that the numbers are canonical likelihoods of the model's actual stepwise generation computation, and the supplementary runner does not prove that its reused generations and adapters are the immutable sealed originals. Those are promotion blockers. The result may remain explicitly diagnostic-only.

## What is correct

- Each candidate is required to equal the exact saved prompt prefix plus a nonempty response, and the labels must mask exactly the prefix. The lookup at logit row `index - 1` therefore scores every response token, including the terminal EOS, under the correct preceding tokens.
- Both tensors have the same `(1, L)` shape, positions `0..L-1`, and all-one attention masks. Extra EOS tokens occur only after the real terminal EOS. In a strictly causal Qwen decoder those future tokens cannot affect any scored row; an attention padding mask is unnecessary for this construction.
- If the first differing token is at index `d`, comparison of `probabilities[:d]` includes the distribution at row `d-1`, i.e. the branch distribution after the entire shared history, while correctly excluding rows conditioned on different branch tokens.
- Common terminal EOS with no earlier EOS makes two distinct continuations disjoint complete events. FP32 `log_softmax`, finite/nonpositive checks, and the summed-mass bound are valid fail-closed consistency checks. The focused shape suite passes 10/10; the four small rescore tests also pass.

Thus, conditional on causal execution and a declared common `L`, the two saved-candidate totals belong to one normalized autoregressive computation. The old unequal-shape contradiction is removed.

## Promotion blockers

1. **Self-consistency is not numerical-reference validity.** Equal shape selects an `L`-conditioned BF16 computation whose values can depend on the other candidate's maximum length. It does not reproduce the stepwise shapes used by generation, and prefix equality plus mass at most one cannot detect a normalized but materially biased distribution. The committed localization artifact demonstrates the gap on the motivating prompt: the first branch token had probability `0.5920015` from a standalone 96-token prefix (the initial shape generation normally uses), `0.7052455` from the equal-BF16 length-101 computation, and `0.7289016` from equal FP32. The repair therefore chooses a coherent convention, not a uniquely validated model likelihood. Before any likelihood-, NLL-, threshold-, or gate-level interpretation, define the estimand explicitly and either (a) score prefix by prefix using the generation-equivalent computation, or (b) validate the complete 832-request BF16 result against a canonical higher-precision reference and show all scientific decisions are invariant. A one-prompt mass check is insufficient.

2. **The rescore does not authenticate the sealed original execution.** `verify_original` checks that `SEAL.json` exists but never checks its manifest binding or inventory. It then reads fit `DONE.json`, adapter trees, and 880 generation records outside the seal. A coherently replaced `DONE.json` plus adapter can pass the self-reported tree hash; changed generation records can enter the hybrid report. `original_report_sha256` merely pins whatever report is present when the supplement starts. The runner needs a source-change-compatible verification of the original `SEAL.json` inventory (or equivalent independently pinned terminal inventory) before any original output is consumed.

3. **The supplementary result has no replayable model/record binding.** `merge_records` checks record-file hashes and request IDs/counts, but not each state's expected adapter, `LOAD.json`, `supplementary_equal_shape`, per-state denominator, hardware/driver identity, or cleanup receipt. The inherited reducer ignores these fields. There is also no supplement seal/replay, and `worker` does not call the original `gpu_identity` check even though driver/hardware stability is especially relevant to this numerical defect. A completed report consequently cannot independently prove which five model states produced its 832 scores. Bind every record to a verified load/model state and seal a replayable inventory.

## Secondary defects / test gap

- The stated 3600-second overall deadline is enforced inside workers but not after the final worker or during reduction/completion.
- `tests/test_astra_semantic_rescore.py` exercises only three shallow failure cases and the state list. It has no successful sealed-original fixture, corrupted-seal/adapter/generation test, wrong-state record test, hardware-binding test, or end-to-end replay test. The toy shape tests establish indexing and logical invariants, not actual Qwen/Hugging Face numerical accuracy.

CPU note: the focused 10 shape and 4 rescore tests passed from an archive of `02a772f8`. Broader carrier/writer tests that do not require Linux passed locally; Linux lifecycle cases could not complete on macOS because `/usr/bin/timeout` is absent. No failure above depends on those environment-limited cases.
