# Perception anchor attempt3 — bounded raw-evidence analysis

**Date:** 2026-09-13; final identity check 04:05:15 UTC.
**Scope:** the supplied attempt3 raw directory and report only. No code edits, Git, network, model/native/GPU execution, additional experimental runs, or other birth/relay inputs. This report is the only file written. Main retains operations.

## Main conclusion

**The registered raw scores remain absent 0/12, present 10/12 (+10 paired passes).** All 24 archived score decisions and failure messages were reproduced using the archived record scorer on the unchanged response strings.

The raw outputs substantially narrow the interpretation: **all 12 absent responses are complete JSON objects enclosed in Markdown fences; all 12 present responses are bare JSON.** Under an explicitly secondary, descriptive removal of those fences, 11/12 absent objects already contain all four supported fields correctly, versus 10/12 present objects. Eleven paired objects are identical after that secondary extraction; only call 02 changes content, from correct to incorrect prediction/relation.

Thus the ten primary gains are ten cases of bringing already-correct record content into the required raw format. There is no observed correction of an incorrect prediction field by the anchor in these pairs. This does not diminish the legitimate raw-format requirement, but it rules out interpreting 0/12 as twelve failures to extract the public observations or +10 as ten newly acquired perception abilities.

**No invalid response is promoted:** absent stays 0/12 in the primary result. Secondary field counts below are explanatory diagnostics, not a replacement scorer or revised scientific result.

## Evidence integrity, pairing, and input visibility

- Independently hashed all **65 members** listed by `archive.json`: all matched; no unexpected member files were present beyond the archive index itself. The report's archive-index and plan hashes, and the plan's row-file hash, matched the supplied files. Local `closed.json` files each record 12 calls; `release.json` records 24 closed calls, owned groups empty, and GPU processes absent. These are archived receipts, not a new operational probe.
- For all 12 paired indices, row IDs, sources/events, selected event, target/proof metadata, and other non-input fields are identical. The only row differences are the system-containing input messages and their input hash. Both conditions use exactly the same user message and generation parameters at each index, in the same row order.
- Every request matches its planned call and row input messages. Every response's recorded and actual prompt-token arrays match the request's recorded native array; its rendered prompt and system segment also match. After removing the system segment, **both the rendered remainder and the recorded token suffix are identical within all 12 pairs**. No tokenizer/model was loaded to independently re-encode or decode IDs.
- Reconstructed every user message solely from the two public event records, the fixed DEV template, and the shared record instruction/relation mapping: all 24 matched. No serialized `raw_target`, target hash/status, source proof/ID, row ID, case label, or situation-index metadata was supplied as prompt content. Output key names and the public relation definition are intentionally in the task instructions; they are not leaked row-specific answers. TRY values, prediction literals, and outcomes are intentionally visible public evidence.
- All target fields were independently derived from the **selected final event e1** and agreed with the stored target metadata. See archived `source/organism_v6/birth_skill_corpus.py:138` and `source/organism_v6/birth_skill_corpus.py:216` under the raw directory: sources/proofs/targets are separate from `input_messages`.

## What the treatment actually changes

The absent request contains only a user message, but its native chat template inserts:

> You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

The present request explicitly supplies, **in place of that generic system message**:

> Keep observations, prior predictions, and later outcomes distinct. Report only what the public record supports. Do not invent a prediction when none was stated. Compare an explicit prediction with its matching outcome; do not infer a hidden rule. Follow the requested record format.

This is **generic-system versus procedural-system prompting**, not system-message versus no-system-message, and not an additive anchor while retaining the identical generic system prompt. The contrast does not isolate any individual anchor clause or exact wording.

`plan.json:1` and both identity receipts specify no fit, no adapter, LoRA disabled, one output per call, seed 0, temperature 0, and the same public Qwen2.5-7B-Instruct revision. This is immediate elicitation on a fixed public-record task. It establishes neither learned perception nor retention/persistence after removing the prompt, and is not H1/H2, L2, root robustness, or a scientific pass. The 12 rows are a six-case factorial over two authored triples, not 12 independent learning runs or broad paraphrase replication.

## Exact scorer failures and the two content errors

The archived scorer first decodes the **entire raw string** as JSON, rejects duplicate keys/nonfinite constants, checks the exact four-key schema and field types, then checks TRY, observed, predicted, and relation in that order. It does not demand identical whitespace/key order to the target, but it does not strip Markdown. References: `source/organism_v6/rulegame_parenting_diagnostic.py:151` and `source/organism_v6/rulegame_parenting_diagnostic.py:300` under the raw directory.

| Raw condition | Exact failure disposition | Number |
|---|---|---:|
| Absent | Full-string JSON parse failure at the leading fence | 12 |
| Absent, secondary classification only | Fence is the sole discrepancy; internal object matches all supported fields | 11 |
| Absent, secondary classification only | Fence plus wrong predicted/relation fields (call 01) | 1 |
| Present | Exact pass | 10 |
| Present | `prediction mismatch` (calls 01 and 02) | 2 |

The present scorer stops at the first failed prediction check. Its failure arrays therefore contain **only** `prediction mismatch`; the following relation discrepancies are independently described from the raw objects, not extra logged scorer errors.

### Call 01: explicit T prediction is dropped in both conditions

Evidence: `/tmp/astra_perception_anchor_20260913_attempt3_raw/present/01.request.json:1`, `/tmp/astra_perception_anchor_20260913_attempt3_raw/present/01.response.json:1`, and corresponding absent files. Row ID prefix `c8a2d918a6e9`, case `matched_true`, situation 1.

Selected e1 says `PREDICT: T`, `ACT: TRY -6,12,5`, outcome True. Supported record: `try=[-6,12,5]`, `observed=true`, `predicted=true`, `relation="matched"`. Both conditions instead give `predicted=null`, `relation="unavailable"`, while preserving TRY and observed. The absent version additionally has fences.

Earlier e0 has no prediction and a True outcome. The error is compatible with dropping e1's prediction or incorrectly borrowing e0's absence of a prediction, but the output alone cannot identify that mechanism. It is not an observed-outcome reversal.

### Call 02: the anchor reverses an explicit F prediction

Evidence: `/tmp/astra_perception_anchor_20260913_attempt3_raw/present/02.request.json:1`, `/tmp/astra_perception_anchor_20260913_attempt3_raw/present/02.response.json:1`, and corresponding absent files. Row ID prefix `3ef9820c51f6`, case `matched_false`, situation 0.

Selected e1 says `PREDICT: F`, `ACT: TRY 11,-8,3`, outcome False. The absent fenced object has the supported `predicted=false`, `relation="matched"`. Present instead gives `predicted=true`, `relation="mismatched"`, retaining the correct TRY and observed=False. Its relation is internally consistent with its invented prediction, but inconsistent with the public record. Earlier e0 contains no T prediction either, so no supplied event supports the returned `predicted=true`.

## Per-case cells

S0 is `[11,-8,3]`; S1 is `[-6,12,5]`. Calls identify the numbered request/response files in each condition. Every case has two rows, one per situation. **Secondary columns remove only an entire enclosing ` ```json ... ``` ` fence when present, parse the interior unchanged, and compare the four public-source-supported fields. They are not primary scores.**

| Case | Predicted / observed | S0 / S1 calls | Absent exact | Present exact | Absent secondary all-fields | Present secondary all-fields |
|---|---|---|---:|---:|---:|---:|
| matched_true | T / T | 09 / 01 | 0/2 | 1/2 | 1/2 | 1/2 |
| matched_false | F / F | 02 / 08 | 0/2 | 1/2 | 2/2 | 1/2 |
| mismatched_true | F / T | 11 / 03 | 0/2 | 2/2 | 2/2 | 2/2 |
| mismatched_false | T / F | 07 / 05 | 0/2 | 2/2 | 2/2 | 2/2 |
| unavailable_true | null / T | 10 / 04 | 0/2 | 2/2 | 2/2 | 2/2 |
| unavailable_false | null / F | 00 / 06 | 0/2 | 2/2 | 2/2 | 2/2 |
| **Total** | | | **0/12** | **10/12** | **11/12** | **10/12** |

By situation: absent exact 0/6 for both S0/S1; present exact 5/6 for both. Secondary all-fields are absent S0 6/6, S1 5/6; present 5/6 in each. Primary transitions are ten fail-to-pass, two fail-to-fail, and no pass-to-fail because absent has no exact passes. The secondary content comparison has one correct-to-incorrect transition (02), one persistently incorrect pair (01), and ten persistently correct pairs.

## Field support, distractors, and truncation

Under the same **secondary content-only view**:

| Supported field | Absent | Present |
|---|---:|---:|
| TRY matches selected e1 | 12/12 | 12/12 |
| Observed matches selected e1 outcome | 12/12 | 12/12 |
| Predicted matches explicit e1 prediction/absence | 11/12 | 10/12 |
| Relation matches public e1 evidence | 11/12 | 10/12 |

Every e0 uses distractor TRY `[20,21,22]`, distinct from the selected e1 TRY. Neither condition outputs that distractor triple. In six rows (calls 05, 06, 08, 09, 10, 11), e0's outcome conflicts with e1's; both conditions' objects preserve the e1 outcome in **6/6**. In all four mismatched prediction/outcome cases, both preserve the returned observation rather than copying the prediction. Both also leave genuinely absent predictions null in all four unavailable cases.

This supports correct selected-TRY/outcome association on this fixed two-event surface, even though the absent raw format is invalid. It does not establish general event joining: the selected event is always the explicitly designated final event; the distractor never supplies its own prediction; and only two selected triples are used. The two remaining anchored errors are in prediction fidelity, not observed-field fidelity. No stronger causal account of the internal join mechanism is warranted.

**No truncation is indicated:** all 24 finish reasons are `stop`, all recorded output-token arrays end in token 151645, and all objects/fences are complete. Absent outputs use 41–43 tokens, present 37–39, versus a common 192-token cap. `text` and `decoded_output` agree in every response. There is no basis here to change the token cap or treat invalid formatting as a truncation artifact.

## Decisive next experiment: preserve the existing registration

The next discriminating step is **the already-registered two-fit/six-readout experiment**, not another anchor rewrite, fence-stripping primary scorer, retry of these rows, or retuning of held material. Use its existing training-state and prompt-condition comparisons to determine whether fitted changes improve raw exact public-record fidelity beyond immediate anchor-driven formatting, particularly when the anchor is absent. Prediction/relation fidelity must be distinguished from merely removing fences.

Keep its prescribed cells, train/held split, anchor bytes, scorer, generation settings, and controls fixed. Do not turn calls 01/02 into newly selected training corrections or alter held rows in response to this analysis. The supplied no-fit plan does not contain the full two-fit/six-readout cell registration; this report therefore does not invent state names, dose, thresholds, or replacement comparisons. Main should execute only the existing registration through the established operational process. This analysis launches nothing.

## Hashes and method

```text
report.json (supplied report path)
bfcfebee88dbac507affaa822dd6e8a7acb1c79862e1a6aca3b238744f461244
raw/archive.json (member index, NOT the full capsule)
7a1db115d8783940ae6afa0325bb0b715e12a867198915f68c08128fd1f8f59b
raw/plan.json
f57769c71eeb0ecc55283749d7a00e864861c232561fef976f91f19fb61f690c
raw/rows.json
1c12aaf746ad5b0defdaf2d979749f195e7c4b0503ece82897dc54c0c83a8cc6
raw/source/organism_v6/birth_skill_corpus.py
078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6
raw/source/organism_v6/rulegame_parenting_diagnostic.py
e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526
```

Here `raw/` denotes `/tmp/astra_perception_anchor_20260913_attempt3_raw/`. Main's reported full-capsule identity begins `471f1302...`; the full capsule itself was not supplied within the inspected paths and was not independently hashed here. That identity must not be confused with the archive-member index hash.

CPU analysis used only standard-library JSON, hashing, regex, and in-memory AST extraction of the archived `require`, `unique_object`, `decode`, and `judge_record` functions. No archived module was imported wholesale. Primary scoring received the original text; optional secondary fence extraction never entered that scoring path. The report and all raw evidence remain unchanged.
