# V2 constraint production: independent content audit — 2026-09-12

## Decision summary

**Confirm the original result: all 48 strict grounded scores are zero.** Process schema counts are **1/0/1**, active-format counts **2/2/2**, in generation-seed order 7101/7102/7103. No original score, checker, record, or training approval is changed.

There are **no quoted single-digit numeric strings anywhere in these 48 raw responses**. The earlier coordinate-string-only diagnostic makes zero conversions and leaves every score unchanged. The current problem is chiefly malformed structure, plus genuinely incorrect group/value citations—not an uncorrected integer-string issue. Comparison with v1 does not identify the causal effect of the clarification because the boards also changed.

Do not launch another static-card wording/seed sweep. The bounded next experiment recommended below is **shared concrete worked evidence → child-authored restatement → parent-free changed-board application**, with an active matched control. It is not another attempt to get eight successes by searching for source material.

## Independently reproduced endpoints

| Generation seed | Process strict grounded /8 | Process schema /8 | Control strict grounded /8 | Control schema /8 | Coordinate-only post-hoc grounded, process/control |
|---|---:|---:|---:|---:|---|
| 7101 | 0 | 1 | 0 | 2 | 0 / 0 |
| 7102 | 0 | 0 | 0 | 2 | 0 / 0 |
| 7103 | 0 | 1 | 0 | 2 | 0 / 0 |

These are **three sampling replicates on the same eight boards**, not 24 independent board draws per arm, trained recipients, or optimizer seeds. All strict structured-record-clean counts are zero. Each output requests/attempts one check; no multiple valid citations are being hidden by the denominator.

### Failure partition across all 48 outputs

The following categories are exclusive and sum to 48:

| Category | Count | What actually happened |
|---|---:|---|
| Only one coordinate pair | 25 | E.g. `"cells":[1,2]`; no second cell was specified. |
| Invalid JSON syntax | 8 | Two adjacent arrays without their enclosing array, or a `lesson` key incorrectly placed inside the checks array. |
| Duplicate JSON key | 5 | Two separate `cells` properties; ordinary last-key-wins parsing would silently lose one. Strict rejection is correct. |
| Flat four-coordinate list | 1 | `"cells":[1,1,1,4]`, not two nested coordinate arrays. |
| Coordinate objects rather than arrays | 1 | Two `{row:…,column:…}` objects; meaningful coordinates but wrong schema. |
| Strict schema valid, content incorrect | 8 | All fail the stated common-unit predicate; six also fail the claimed-digit predicate. |

Thus **40/48 fail syntax/schema before content scoring**. Do not interpret their official `invalid_citations=0` as proof that their content is correct. Conversely, do not declare all 40 factually false: many never specify a complete witness.

## The eight strictly parseable citations are genuinely wrong

Actual values below come from the captured candidate matrices. Coordinates are one-based; boxes are the ordinary disjoint 2×2 units, not arbitrary adjacent cells.

| Seed/arm/case | Claimed group; cells; digit | Actual values | Content failure |
|---|---|---|---|
| 7101/process/c03 | box; (2,2),(2,3); 4 | 2,3 | Different boxes; neither value is 4. |
| 7101/format/c01 | box; (2,2),(3,3); 3 | 4,4 | Different boxes; repeated value is not claimed digit 3. |
| 7101/format/c02 | box; (2,2),(2,3); 1 | 1,2 | Different boxes and unequal values. |
| 7102/format/c01 | box; (2,2),(3,3); 3 | 4,4 | Different boxes; wrong claimed digit. |
| 7102/format/c02 | row; (1,4),(4,1); 1 | 1,1 | Equal claimed digits, but different rows. |
| 7103/process/c01 | box; (2,2),(3,3); 3 | 4,4 | Different boxes; wrong claimed digit. |
| 7103/format/c01 | box; (2,2),(3,1); 3 | 4,2 | Different boxes; wrong claimed digit. |
| 7103/format/c02 | box; (3,3),(4,1); 1 | 1,1 | Equal claimed digits, but different boxes. |

This supports teaching an actual **same-unit plus equal-value check**, rather than assuming that better JSON alone would solve the competency bottleneck.

## Explicitly post-hoc literal-witness reading—not record repair

For diagnosis only, the audit also reads coordinates that are completely present but serialized incorrectly. Its conventions are explicit: group a flat four-number list consecutively into two pairs; read named row/column object fields; read both duplicate `cells` occurrences instead of keeping only the last; or read the two adjacent arrays in invalid JSON. **No missing coordinate, group, or digit is supplied, no axis is swapped, and no alternate witness is sought.** This is a separate interpretation of malformed text, not a permissive replacement checker. No repaired response or training target is emitted.

This makes **17 literal witnesses assessable**: the eight strict ones plus nine structurally malformed ones. **Twelve are factually incorrect under those conventions; five describe real duplicates.** The other **31** outputs specify only one coordinate pair and remain content-unassessable as duplicate witnesses.

The five supported literal readings are all process outputs:

| Seed/case | Literal witness; actual values | Original defect |
|---|---|---|
| 7101/c02 | row (1,1),(1,4), digit 1; values 1,1 | Missing enclosing array: `"cells":[1,1],[1,4]`. |
| 7101/c07 | box (3,3),(3,4), digit 3; values 3,3 | Duplicate `cells` keys. |
| 7102/c02 | row (1,1),(1,4), digit 1; values 1,1 | Duplicate `cells` keys. |
| 7102/c07 | box (3,3),(3,4), digit 3; values 3,3 | Duplicate `cells` keys. |
| 7103/c07 | box (3,3),(4,3), digit 3; values 3,3 | Coordinate objects instead of integer arrays. |

These are **five generations on only two source boards and three distinct case/witness combinations**, not five independent transferable lessons. None passes the original checker. There is no corresponding supported complete literal witness in control. The result shows some localized grounding in malformed process text; it does **not** establish a parenting advantage, authorize coercion, or supply approved valid material.

## Own lessons

Every raw output contains a short future-check imperative: examples include `Check row next`, `Check next box`, `Check adjacent boxes`, and `Check rows next`. The JSON contains all 48 verbatim lesson strings, including those found inside invalid enclosing JSON. They are plans, not reports of a completed check or concrete assertions that certify the citation. `Check rows for singles` also changes the suggested focus without supplying supporting evidence. No lesson is independently machine-verified; no prose truth whitelist is used. Neither literal-witness interpretation nor a plausible plan confers training approval.

## Recommended next experiment: worked evidence, own restatement, parent removed

**Select one fixed 32-call production/application pilot, zero fits in this stage.** Use the existing nursery dialogue sequence, but make the source evidence and controls explicit. This recommendation is a design handoff, not execution authorization.

1. **Freeze eight source/transfer pairs from fresh native training questions.** Keep the public-constraint exercise and strict checker, not full solving. Deterministic construction provides at least one real duplicate per candidate. Freeze one machine-verified source witness per source before generation, balancing row/column/box examples as 3/3/2. Each paired transfer board must make that old literal witness invalid while containing another genuine duplicate, verified programmatically before collection. This prevents source-answer copying from passing. IDs, question/candidate hashes and prior-overlap checks remain Main-owned; no model-performance selection or replacement hunt.
2. **Give both arms the same concrete worked example.** The source candidate and one complete valid source JSON record—with the same two nested coordinate pairs and digit—are identical in both arms. This exposes source-answer information openly and equally; it is not a sealed reference or a supposedly self-discovered failed ACT. Process-parent adds a source-specific public explanation: identify the common unit, read the two displayed values, compare them, then state why the citation holds. Active-format control gives equally budgeted serialization commentary about that **same** example, with no checking procedure. Match delivery count, actual tokenizer-measured commentary dose, output cap, order and sampling seed. Do not use answer-bearing padding or a secretly worse/false control example. Freeze packages before output collection.
3. **Ask for the child's own record once per source.** One original child generation per arm/source, capped at 128 tokens, with the existing strict record format. Preserve the entire response and distinguish verbatim teacher echo from additional child wording; copying a shown source check may establish correct emission, not independent inference. Score all eight per arm, including failures. Do not make correctness by host rewriting, last-key-wins parsing, or filling missing cells. There is no all-eight-success prerequisite and no response-triggered retry.
4. **Apply on the changed board with the parent absent.** Reset conversation state. Show only the common task, the paired new candidate and that arm's unmodified child record, explicitly labeled as its note about the earlier source. Remove the parent card, worked example, source board, external scratch state and reference data; do not accidentally reinsert them through a dialogue tail. Run all eight transfer cases per arm even if their source record was invalid. This is another 16 calls: **16 source restatements + 16 parent-free applications = 32 total**, one paired generation seed 7101 as a small feasibility pilot, not three new learner seeds.
5. **Read out grounded source material and strict parent-free transfer separately.** Primary application contrast is strict grounded `/8` per arm; format and source truth/echo counts are secondary. Because both arms had the same correct example, a process difference on changed boards is not simply extra source-answer access. The child's retained note is the only arm-specific conversational material at application. That is **in-context application after parent removal**, not weight persistence, mediation proof, P1 completion, or H1/H2 evidence.
6. **Stop after this fixed pilot.** Zero strict source yield or zero useful parent-free application ends this material route for now; do not launch another prompt/seed/source sweep. Partial valid source yield is reported as-is, not expanded until eight. If meaningful material is produced, Main can separately select a bounded own-output sleep versus no-update comparison. Preserve that option through exact child-byte provenance now; do not train on malformed records, post-hoc interpretations, teacher text, or unverified free-prose lesson claims. No fit, admission certificate or automatic next phase is proposed in the current call budget.

**Why this advances the chain:** v1/v2 supplied abstract static advice but no demonstrated instance of reading two actual cell values and checking unit membership. This intervention tests whether grounded demonstration produces correct child-authored records and useful child-carried material when the parent is removed, before spending on storage. It is a concrete material-formation and changed-task application experiment, not another spelling-only assay. It is deliberately not labeled persistent learning yet.

### Existing paths and minimum wiring

- `organism_v6/nursery_dialogue.py`: `parent_turn` / `play_task` and its live loop already express parent feedback → child restatement → different task → sleep/probe. **Do not run unchanged:** it is a RuleGame path, clips text, its solo arm lacks matched exposure, and its `admitted` flag is not a truth gate.
- `organism_v6/constraint_check_diagnostic.py`: `make_case`, `preflight`, `CaptureBackend`, and `score_record` provide the public candidate, actual-token, native-stop and strict-checker primitives. Missing minimum is an explicit two-stage source-conditioned worked-card wrapper and context reset; no mutable global card/seed overrides, new parser relaxation or general sequential runner.
- `organism_v6/parent_correction_write.py`: `raw_span`, `strip_teacher`, `make_corpus`, `tokenizer_preflight` demonstrate byte-bound own-output spans and teacher exclusion. Their fixed event/hash, single-event replay and exact-package assumptions are **not** valid unchanged for this new exercise. `organism_v6/train_adapter_v3.py` is the later LoRA-only writer if separately selected; no training call here.
- Preserve source ID/board hash, selected public teacher witness, parent-package and prompt hashes, full raw child bytes/token IDs/stop reason, child span pointers, source-to-transfer mapping, and strict outcomes. Label external demonstration exposure, possible copying, unverified lesson prose and `clean_ancestry=false` honestly. Frozen local-hash Qwen2.5-7B and LoRA-only learning limits remain intact; no formal guard/C11 expansion.

**Runtime estimate:** roughly 4–8 minutes for the 32-call pilot with two fresh model processes, hardware/loading dependent; retain at most 900 seconds per arm / 1800 total. Anchor: the three completed 16-call v2 pairs took approximately 224.7, 202.5 and 206.8 seconds. This is an estimate, not a reservation or launch plan; fitting cost is zero for the selected stage.

## Verification and artifact scope

- Capsule `/tmp/astra_constraint_v2_terminal_20260912.tgz`: SHA256 **`476788fb5204ab45dfcc22644382f1519493ce6224ccbce8298616c0d1073692` matched**.
- Verified all nine preparation/arm file inventories; six arm-to-preparation bindings; seeds 7101/7102/7103 in preparation, request, output, runtime and terminal metadata; exact common task plus selected clause; identical parent cards; common model-file/source-pin receipts and identical case records across all three preparations. Captured module hash is `59d66791155c076b40430e5f408e8f044a71f0a9823005e2dee4705aaf87e859` from the `1adccdce…` source snapshot.
- Recomputed all eight actual question and candidate hashes; eight unique questions/candidates, reused across seeds. Reconstructed every public task/card/candidate prompt. Independently checked all 48 request/raw-return/output triplets, raw/summary text equality and hashes, native input/output token counts, normal `stop` completion, 128-token output and 4096-token input-plus-headroom bounds, and strict counts with a standalone predicate implementation. **No verification mismatch found.** The script does not import the production checker.
- Total native usage: **13,560 prompt tokens / 2,066 output tokens**. Per arm/seed, process prompts cost 2,272 versus control 2,248; standalone cards remain 47 versus 44 tokens. Thus existing cards were not token-matched. All 48 outputs stopped normally, including malformed ones; none is a length-stop artifact.
- Six distinct model-worker PIDs are bound to captured process/cleanup receipts, which report owned-group empty, GPU-process absent and reservation release verified. These are **historical captures only**, not live GPU polling. Absolute remote model/source files were not rehashed locally, and local byte pins do not authenticate official model origin.
- `/tmp/astra_constraint_v2_content_audit_20260912.json` contains every raw output, board, hash, strict category, coordinate-only result, literal-witness convention/predicate, lesson and per-arm/seed totals. `/tmp/astra_constraint_v2_content_audit_20260912.py` is the standalone audit; run used `PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_constraint_v2_content_audit_20260912.py`. It requires a fresh JSON destination and never overwrites capture inputs.

Only the assigned `.md`, `.json`, and `.py` audit files were written. No production code, original results, approvals, GPU/SSH/network state or git state was changed; no implementation or launch of the recommendation occurred.
