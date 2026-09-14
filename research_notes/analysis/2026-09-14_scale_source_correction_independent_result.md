# SEQ259 — bounded actual-correction evidence review

2026-09-14. **Released; retrospective and nonblocking.** The primary `2026-09-14_scale_source_correction_first_result.md` agrees with the recorded calls, literal validity checks, source joins, and costs. Outcome: **three corrected cases and one twice-failed case, in five actual calls**. No discrepancy requiring a primary-result correction was found. Only this memo was written.

Reviewer provenance: this agent previously authored the correction driver/tests. This review independently reduces the actual terminal artifacts; it is **not a fresh-author implementation audit**.

## Evidence binding and replay

`C` = `gpu_artifacts_local/astra_scale_source_correction_terminal_20260914_attempt1/extracted`. Sibling archive `astra_scale_source_correction_terminal_20260914_attempt1.tar.gz` SHA256 matches **`8a22e4435bc492644bd02ee1e7b3113ddd6c51daa57136da9e89486bf30b0257`**. All **2,679 regular files** match extracted inventory and bytes, without duplicate/unsafe paths or nonregular payloads.

Twelve bounded frozen driver/guard/test/helper files match Git commit **`b8508e190a072d6d8f44dc6c4fd09aa76237bd0e`**; launch/root source markers agree. The protocol at that commit hashes to **`e6f4beca65fd3938cf6157c339117e6e8401ecc7623d257d53c6cc7aa47fd934`**. Original-exposure provenance remains the separate SEQ258 source `ff1af2c37003fd4f6d38ecbe7660fd94744c0e31`.

Frozen `astra_scale_source_correction.execute` replay, supplied only the captured responses, reproduces every **5 CALL / 4 CASE** artifact and `correct/DATA.json`. Preparation hash/binding/selection joins, all14 correction output-file hashes, frozen helper/portable source-contract hashes, and accepted candidate capture digests pass. No native `main`, model loader, encoder, or live portable-base verification was invoked.

## Selection, visibility, and actual outcomes

All eight original EXPOSE RESULT hashes and their DATA hashes join to the previously reviewed SEQ258 capsule. Direct enumeration recovers **320 committed transitions,316 valid EVENTs, and exactly four failed records**, all selected. Each selected original record/capture matches its original collection and native-call file hashes, including a successful ROUTE followed by a terminal/nontruncated bad EVENT. This is not a success-selected subset.

| Case | Original shard / world / record | Original EXPOSE call | Correction calls | Outcome |
|---|---|---|---|---|
| 0 | 0 / block0 TRAIN-B / 0 | `CALL_009.json` | `CALL_000.json` | exact valid; stopped |
| 1 | 1 / block0 PROBE-A / 3 | `CALL_071.json` | `CALL_001.json` | exact valid; stopped |
| 2 | 4 / block3 TRAIN-B / 0 | `CALL_057.json` | `CALL_002.json` | exact valid; stopped |
| 3 | 6 / block2 TRAIN-B / 1 | `CALL_043.json` | `CALL_003.json`, `CALL_004.json` | both invalid; no candidate |

For every call, direct JSON comparison verifies the input is exactly the original EVENT-generation messages, then the actual failed assistant text, then:

> Recorded EVENT identifiers do not exactly match the observed receipt. Recheck all identifiers and output one correct EVENT line, no other text.

The original public receipt follows verbatim after a newline. The available EVENT address remains in the original history. The second attempt appends the first correction's actual failed text and **identical feedback/receipt**; no additional hint or altered target is introduced.

No complete correct target EVENT is present in these inputs. No task GOAL, parent procedural plan, policy answer, or score is added. The PROBE-source case is public receipt copying, not a PROBE goal readout or parameter-training example. This conclusion follows from exact prompt equality, not just the result's visibility flags.

Independent literal comparison against the unchanged original receipt/address agrees with all five acceptance flags. Three candidate raw strings equal their actual successful native responses, with correct call locators and JSON-capture digests. Case3 emits exactly the same bad line twice, ending **`R_FB3YG5OKD`** rather than the observed **`R_FB3YG5OKDQ`**. Both failures retain `validation_error="not exact EVENT"`; `candidate=null`. No original evidence is replaced, and no legacy `COLLECTION*` artifact is minted in the correction output.

All five responses are terminal/nontruncated with `error=null`. Recorded prompt-token counts are **385,368,365,372,499** and generated token-ID counts **54,51,50,49,49**, within2048/160 bounds. These are checks of recorded counts, not independent tokenization. Attempt counts `[1,1,1,2]` respect stop-on-first-valid and the two-attempt/eight-call ceilings.

## State, cost, and interpretation

Both recorded adapter states and `correct/STATES.json` join to:

`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`

Prepare is PREPARED_NO_MODEL with zero calls; correction is COMPLETE with five calls, three accepted cases, zero native errors, zero fits/updates, disabled training, and `repair_promotion=false`. RESULT records the frozen base unchanged. These are **recorded state/file joins, not independent live tensor/base authentication**.

Direct timestamp subtraction confirms **90.481151 seconds** for correction (**0.025133653 allocated A40-hours**) and a separate **14.361258 seconds** for CPU preparation. Guardian81305 records **18:38:52–18:40:24 UTC**, September14, a **92-second** outer interval. Neither measured duration is the900-second native or1260-second guard allowance; phase elapsed time includes loading/checking, not solely generation kernels.

The result is **3/4 descriptive externally prompted corrections**, not persistent learning, self-detected error discovery, autonomous correction, or established value/efficiency of feedback. There is no matched no-feedback retry counterfactual. The remaining failure closes this finite diagnostic. Candidates remain separate and unpromoted; they do not repair SEQ258 admission or its separate guided-route failure. No downstream-use, new collection, H1/H2, or broader capability outcome was audited here.

## Checks and limits

Used local `cat`/`find`, inline standard-library `tarfile`/`hashlib`/JSON checks, and bounded local `git show` comparisons. Frozen replay ran under an import guard rejecting model/network libraries; separate JSON assertions checked selection, exact prompts, raw validity, candidate provenance, and times. One initial review-script inventory comparison passed a Python set to a JSON-digest helper; replacing it with direct equality resolved that **review-script error**, after which all replay/reduction checks passed. It was not a capsule/native failure.

No GPU, remote/network call, tokenizer/model/torch loading, new framework, launch, notebook edit, or other-file edit. The released SEQ258 review supplies prior full-stage verification; this pass only rejoined its relevant source evidence. **Ownership released.**
