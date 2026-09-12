# Posthoc terminal citation-sleep content audit — 2026-09-12

**Content diagnosis only — not success or requalification. Outputs and primary scores are unchanged.**

## Unchanged primary result and observed pattern

| Arm | Strict format / grounded | Exact trained geometry | Exact 75-byte source prefix | True literal witness | Output tokens |
|---|---|---:|---:|---|---|
| OFF | 0/8 / 0/8 | 0/8 | 0/8 | none | [54, 43, 51, 45, 45, 42, 42, 45] = 367 |
| FULL | 0/8 / 0/8 | 8/8 | 1/8 | t02 | [32, 32, 32, 32, 32, 32, 32, 32] = 256 |
| SYNTAX | 0/8 / 0/8 | 1/8 | 0/8 | none | [32, 32, 32, 32, 32, 32, 32, 32] = 256 |

Whole-record-clean, valid-citation and invalid-citation primary counts are also zero in every arm: schema rejection prevented citation scoring. The posthoc annotation is not a replacement score.

- FULL repeats `box [[3,3],[3,4]]` in 8/8, but only t02 has matching values and digit. Digits in case order: **3,1,4,1,4,1,2,4**; 7/8 match the first cited cell, with t04 instead matching the second. This is not invariant copying of digit 1.
- SYNTAX repeats that geometry in 1/8 (t06). Its other geometries are `[[2,2],[3,3]]` ×5, `[[3,3],[4,3]]` ×1, `[[3,3],[4,1]]` ×1, `[[2,2],[3,1]]` ×1; all declare box. None is a true literal witness.
- OFF has zero well-shaped two-coordinate literal checks: t01/t03 repeat the `cells` key; the other six supply one flat coordinate. No duplicate keys are merged into a pair. t02/t07 also have malformed lesson placement.
- Both ON arms change all 8 raw outputs versus OFF and emit a well-shaped **inner check** in 8/8 but a malformed **whole record** in 8/8: final suffix `][]}`, with `[]}` beginning at zero-based byte 75. Neither ON arm emits a lesson field.

## Literal facts on the actual displayed boards

Only the already-present inner JSON object is decoded. Coordinates, declared group and digit are not repaired or reinterpreted; no outer brace is added. Values below come from the captured request board, matched to the panel and its hash.

| Arm/case | Literal cells (group always box) | Digit | Board values | Same box? | Literal witness true? |
|---|---|---:|---|---|---|
| full/t01 | [[3,3],[3,4]] | 3 | [3,1] | yes | no |
| full/t02 | [[3,3],[3,4]] | 1 | [1,1] | yes | yes (posthoc only) |
| full/t03 | [[3,3],[3,4]] | 4 | [4,3] | yes | no |
| full/t04 | [[3,3],[3,4]] | 1 | [3,1] | yes | no |
| full/t05 | [[3,3],[3,4]] | 4 | [4,2] | yes | no |
| full/t06 | [[3,3],[3,4]] | 1 | [1,4] | yes | no |
| full/t07 | [[3,3],[3,4]] | 2 | [2,3] | yes | no |
| full/t08 | [[3,3],[3,4]] | 4 | [4,1] | yes | no |
| syntax/t01 | [[2,2],[3,3]] | 3 | [3,3] | no | no |
| syntax/t02 | [[2,2],[3,3]] | 1 | [1,1] | no | no |
| syntax/t03 | [[3,3],[4,3]] | 3 | [4,4] | yes | no |
| syntax/t04 | [[2,2],[3,3]] | 1 | [4,3] | no | no |
| syntax/t05 | [[3,3],[4,1]] | 4 | [4,4] | no | no |
| syntax/t06 | [[3,3],[3,4]] | 1 | [1,4] | yes | no |
| syntax/t07 | [[2,2],[3,1]] | 2 | [2,2] | no | no |
| syntax/t08 | [[2,2],[3,3]] | 3 | [3,4] | no | no |

SYNTAX t01/t02/t05/t07 name two values equal to their digit, but across different boxes. t03 cites a genuine same-box pair of 4s while declaring 3; changing the digit would be a repair and is not done. FULL t02 is the sole literal positive; the other seven cases are exposed development, not holdout.

## Exact source-prefix/target boundary

Training target, exactly 75 UTF-8 bytes:

```text
{"case_id":"t02","checks":[{"group":"box","cells":[[3,3],[3,4]],"digit":1}]
```

The source response continued with:

```text
,"lesson":"Check box members for duplicates."}
```

That continuation, the lesson and the closing outer brace are absent from training; EOS is not appended. The 30-token target ends at `}]` (token 25439), closing the check and checks list but not the record. The current prompt still requires case_id/checks/lesson. All ON records reach the malformed continuation at byte 75, not the 128-token generation budget.

The byte-exact cutoff is **not a token-ID-exact source prefix**: the first 29 IDs agree, then the standalone target uses 25439, whereas the captured source continues with IDs `[92,28503,27495,3252]`. This further localizes a boundary difference without decoding unavailable tokenizer files or proving causality.

- **Raw byte comparison:** FULL source-prefix LCP in t01…t08 order is `[14,75,14,14,14,14,14,14]`; SYNTAX is `[14,52,14,14,14,14,14,14]`. OFF differs at byte 11 in all eight. Case-id differences are not silently normalized.
- Comparing source bytes `[15,75)` (the slice after the case-id value; bytes `[0,15)` omitted) gives FULL 3/8 and SYNTAX 1/8 exact matches, including the digit. This is explicitly a substring comparison, not output rewriting or complete-record success.
- The selected original t02 inner citation is literally true, but its prose reminder has **no semantic grounding claim**. Its source request had 332 prompt tokens and temperature 0.7; current requests have 234 and 0.0. Do not treat the selected earlier response as a matched current baseline.

## Captured training and native settings

- Both views have identical **264 input IDs** and the same teacher-forced content; one experience, 32 presentations/steps, 8,448 input tokens each. FULL: 27 supervised labels/presentation (864 total); SYNTAX: 21 (672 total). Both mask case_id; syntax additionally masks group, four coordinate components and digit. Not supervised-dose matched; not content withheld.
- Command and train-manifest settings agree: fresh-base asserted; rank 8, alpha 16, dropout 0.05, lr 1e-4, AdamW, bf16, seed 1729; `--no-eos --no-pack --no-shuffle-groups`, max length 4096, all seven projection modules/all layers. No recorded truncation. Isolation check is recorded as not run (one-item, no packing), not passed.
- Recounted **24 request + 24 raw-return + 24 output events**, one native completion each, matching per-case reductions and COMPLETED. Requests actually specify **temperature 0.0, seed 7101, max_tokens 128**, overriding loader defaults 0.7/400. OFF outputs total 367 tokens; each ON arm 256; **879 total**, 5,616 prompt tokens.
- Every capture finishes `stop`, stop_reason null, rewrite/truncation flags false. Both ON arms are 32 output IDs/case, ending in token ID 151645; no retokenization or fresh generation was performed.
- Request/result identities bind FULL and SYNTAX to their distinct fit adapter hashes; OFF has no adapter. The generic runtime snapshot has `adapter: null` in all arms and must not be mistaken for their actual per-request loader identities.

**NATIVE caption — attributed, not rerun:** the captured terminal audit says `NATIVE_CITATION_SLEEP_REPLAY_AND_RELEASE_PASS`, native reduction equal, source/model/actual adapters verified and released. Here only archived bytes, manifest chains and raw-event reductions were checked. Weights (both adapters and base), tokenizer, upstream log, remote state and GPU release were not independently rerun/authenticated; adapter weights are excluded from this capture.

## Interpretation and next direction

There is **no qualified utility**, not evidence of **no learning**. Reloaded ON outputs visibly change structure; FULL strongly concentrates on trained geometry, while literal transfer remains absent. An incomplete-prefix objective against a complete-record contract is a plausible limitation, **not a proven sole cause** and not an excuse for false citations. Equal inputs with different masks/doses and one selected exposed experience do not establish generalization, internalization, clean ancestry or P1.

Prefer the next selected RuleGame complete concrete record path, with its existing authorization/provenance/control gates, rather than another unchanged-prompt or seed hunt. A prospective output contract should cover the complete intended record and its ending; preserve these failures separately. This audit implements no path, proposes no new GPU diagnostic, and grants no new training approval.

## Reproduction and exact bindings

`python3 -B /tmp/astra_citation_sleep_content_audit_20260912.py`

The standalone standard-library script writes only its named sibling `.json` and `.md`, runs local logic self-checks, and requires the pinned 56-file source tree. It never accesses the repo, network, git, GPU or model weights. JSON includes all 24 verbatim outputs, first-75-byte hashes, literal byte spans, unchanged scores and the complete source-file hash map.

- Source-tree SHA256: `fbc50647ea103ab96d588f8ef7116e018b0a27979cafb9c49f3ddd1d0469b6ba` (sorted compact JSON map of relative path → byte SHA256).
- Prefix SHA256: `a6bc67b28d3c67527a472f6fd4db8a91f9f220fc221c32d3c347ef037272c305`.
- COMPLETED SHA256: `734fd0f8cc0859cf7ac2cb0c188137b625f57a3c42a26145361b05a5f5cd827f`.
- Terminal-audit SHA256: `fd9123e70b917f38e5587611e21e5a8e69c4e6d2d1e98dba7e70e195b5cf43fc`.
- Script SHA256: `1c9147188240b89aed1d6af3fe8ccfd2f859bc9f227d15da3337438552f5e933`.
- JSON SHA256: `10c13cb41dabad486f6a79cf289487b11ea3ab1176a1e2f7656afc4b288f944f`.
