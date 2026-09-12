# Grounded process material — EDIT-STOP, 2026-09-12

## Result and exclusive scope

Implemented new `rulegame_grounded_process_pair_v1` CPU material under Main's prospective decision 11417838. This sidecar authored the exporter/tests and performed the availability audit; it is not an independent implementation review. No model/tokenizer loading, training, native execution, GPU, network, SSH, Git, or changes to legacy/frozen controllers/material.

Owned files only:
- `organism_v6/rulegame_process_material.py`
- `tests/test_rulegame_process_material.py`
- `/tmp/astra_rulegame_process_material_handoff_20260912.md`

**Actual local result: PAIRED_SHORTAGE. No corpus was exported.** All four positions exist, but A/lesson0 call 0039 uses a native executable TRY alias, not literal canonical `ACT: TRY`. It has `PREDICT: T`; it fails the required explicit ACT interface. Native execution validity and this raw-target eligibility are distinct. Do not relabel this as a native execution failure. The other three slots pass CPU positional/action/prediction/lexical checks, not semantic certification. No later slot was searched for or substituted. No alias canonicalization, target correction, or eligibility relaxation was performed after inventory.

## Stable writer-facing API

```python
from organism_v6 import rulegame_process_material as process

candidate = process.inspect_capture(capture_root)
review = process.review_template(candidate)

# Main, not exporter, supplies the actual four-row acceptance and notes.
# Requires AVAILABLE_PENDING_MAIN_REVIEW; current capsule cannot proceed.
pair = process.build_process_pair(
    capture_root, main_review, tokenizer,
    fixed_candidate=candidate, max_len=4096,
)
manifest = process.export_pair(
    capture_root, fresh_output_root, main_review, tokenizer,
    fixed_candidate=candidate, max_len=4096,
)
```

`capture_root` means the existing **formation/data** directory. `inspect_capture` requires no tokenizer, reruns original capture/world replay and provenance checks, freezes the first eligible-position execution BEFORE checking its raw syntax/copy eligibility, reconstructs original inputs, and returns all four candidates (including failures). It returns no training `corpus`. Candidate includes audit-only teacher/restatement raw bytes; do not print that whole object or enumerate it as a corpus.

`review_template` returns actor `Main`, protocol, `candidate_sha256`, scope `transformed_context_and_complete_raw_wake`, acknowledgment flag, and four ordered slot/call-bound reviews. Each needs `decision="accept"` and nonempty notes; `context_distillation_acknowledged=True`. Pending/rejected/stale/partial reviews cannot export. This records a Main assessment; it does not authenticate the reviewer or prove semantic safety. Shortage blocks export even if all reviews say accept.

`build_process_pair` is read-only and returns:
- `protocol`, `status="PAIRED_CPU_TOKEN_AUDITED_MAIN_REVIEWED"`;
- `corpora["P"/"A"] = {"corpus": [two V3 span items]}`;
- `audit`: bound candidate, copied Main review, separate original-native and transformed-training receipts, max length, tokenizer class, token totals, limitations.

Each item has exactly `[rendered_transformed_context, False, "parent_removed_wake_context"]`, `[whole_unchanged_raw_wake, True, "complete_own_raw_wake"]`; group is actual apply task ID, order is lesson 0/1, metadata binds arm/lesson/execution/source call. No teacher payload is placed in item metadata. Use V3 with **chat_template=False, add_eos=True, pack=False**, max_len as audited. Do not apply a second chat template or enumerate the entire output directory as input.

The injected tokenizer implements `apply_chat_template`, `encode`, `decode`, `eos_token_id`, `pad_token_id`. Original capture rendering/input IDs/output decoding are audited over all source calls. Each transformed item receives separately re-encoded raw-target IDs, exactly one EOS, full IDs/labels/position/segment checks and causal predictor offsets. The first target's predictor index is `len(context_ids)-1`. Native generation token IDs are retained as original evidence, never substituted for training target encoding. Overlength, missing pad/EOS, embedded target EOS, drops, splits, masking shifts and literal teacher copies in new rendered input fail closed. This sidecar did not perform an actual native-tokenizer audit of the real capsule.

`export_pair` requires an existing parent directory and a fresh output root; source/output overlap and symlinks are rejected. It builds and audits both arms before writing a fixed exclusive sibling `.NAME.pending` directory, then uses Linux `renameat2(RENAME_NOREPLACE)` for paired publication:

```text
manifest.json
corpora/P.json
corpora/A.json
audit/candidate.json
audit/main_review.json
audit/token_receipts.json
```

Manifest gives explicit `corpus_files`, hashes of every other output file, candidate and current-source hashes, per-arm input/context/target totals, and unresolved-origin/context-distillation labels. Any post-staging failure preserves pending evidence; no auto-retry, orphan reuse, empty-root replacement, or partial-arm publication. Linux without `renameat2` fails rather than using a weaker overwrite operation. No runner or fit API is implemented here.

## Local availability evidence

Archive: `/tmp/astra_rulegame_v3_formation_terminal_20260912.tgz`.
Validation: adjacent `.tgz.validation.json`. **Archive SHA256 and all 141 listed extracted member SHA256 values independently recomputed and matched.**

```text
archive SHA256 05b9177bb83e800f4f9c10bbc5e34c27c7dd68e2fabe9c18c006c12e6971f90e
capture root /tmp/astra_rulegame_v3_formation_terminal_20260912/astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1/formation/data
capture manifest SHA256 c28283c8fc2ee617ef633b3da82c7ace288ad2206a2abfcff656e9018d6a9267
source plan SHA256 7dae3ca492ed39545987ab8deb5f39631a40332d480ddb99292e5f083741c468
selection SHA256 e321f805eab317978416edd823aa849e34fd97f4940a3279017315e909dbfe0f
candidate SHA256 d0306e200ee9d62c6fb21e361b8313efac0f4ffc731876391cb5158f7fefde61
```

Candidate hash binds local absolute capture/plan paths and current source dependencies. Recompute under the final immutable native source/path and bind Main's review there; do not copy the local candidate hash across relocated roots and claim identical identity. Captured producer source hashes and current exporter dependency hashes remain separate. Initial backend records 14 base-file hashes and empty adapter inventory; source plan seal/model identity match. These are local hash provenance, **UNRESOLVED_LOCAL_HASHES_ONLY**, not authenticated model origin.

| Slot | Call | Execution suffix | Event index | Deleted UTF-8 interval, half-open | CPU eligibility |
|---|---|---|---:|---|---|
| P/lesson0 | 0009 | lesson0/apply#t2 | 8 | [1020,1472), restate 0006 | PASS |
| P/lesson1 | 0024 | lesson1/apply#t2 | 23 | [1020,1274), restate 0021 | PASS |
| A/lesson0 | 0039 | lesson0/apply#t2 | 38 | [1020,1218), restate 0036 | SHORTAGE: missing canonical ACT |
| A/lesson1 | 0054 | lesson1/apply#t2 | 53 | [1020,1210), restate 0051 | PASS |

Full execution ID format: `{arm}:rule{lesson}/astra-minimum-20260912/lesson{lesson}/apply#t2`. Every selected slot has its preceding tick1 public TRY, source call receipts, execution-event hash and exact reconstruction. Each removed interval contains only the known leading newline/Temporary-parent-restatement marker plus its source-bound restatement; surrounding history bytes remain unchanged. Source receipts are `capture_root/calls/{call}.request.json` and `.response.json`.

Whole raw-target UTF-8 SHA256 values, in table order:
```text
0009 26d4d2117747fc0e11953a3c4d1906297f66055a2942ab7eee3ded95157ded1e
0024 e51a156a3742a11000defb8d141d1b9878ab6b03ade123f1530300294b1a02b6
0039 178bdc9289398cda83c21d2607d0d6ad23141bc869536b09cba40149f4991714
0054 0fb179206fb1e4e3319ca253e902a7c090534e6fafcfdce31b6f04290985146a
```

Main can obtain just the four transformed contexts/whole raw targets for manual audit, without teacher-source fields, using `[(r['slot_id'], r.get('context'), r.get('target'), r['failures']) for r in candidate['candidates']]`. Availability report provides shortage IDs instead of reproducing raw teacher prose here. No model-output correctness/quiz score entered selection. Original world replay necessarily reconstructs existing outcomes for integrity; it does not rank candidates or consult held-out readouts.

## Tests and implementation hashes

Run from repository/immutable-source root:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_rulegame_process_material.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_rulegame_record_material.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_rulegame_parenting_diagnostic.py -q
```

Local CPU results: **33/33** new exporter tests PASS (24.920s); **30/30** unchanged record-material tests PASS (37.094s); **46/46** unchanged parenting-diagnostic tests PASS (17.704s). **109 tests PASS, no skips.** Initial new-test run exposed missing-review type handling; fixed within owned module, final run green. Stdlib unittest; pytest is unavailable in this local Python. Fixtures are scripted text/character-token encoders, not model evidence.

Coverage includes fixed-position/nonreplacement and early termination; aliases versus ACT; missing/malformed/multiple/post-action PREDICT; wrong predictions/whole whitespace retained; exact UTF-8 deletion/history; literal-copy rejection versus nonliteral semantic influence; source/request/event/plan seals; native rendering/input/output mismatch; stale/missing Main review and callback snapshots; causal masks/EOS/drop/split limits; source mutation during callback/publication; complete atomic pair, existing empty race, symlinks, overlap, pending evidence and no retry.

```text
organism_v6/rulegame_process_material.py
c26b180df799f2a3e56b3a3dca2f762c1507f66efc13f14c9055c54d0836c21a
tests/test_rulegame_process_material.py
45e70f368f278299cab9bc07f13f9153f04aa1e29dc077b5d34f7d4b1e07642f
```

## Limits / downstream scope

This is **CONTEXT_DISTILLATION_NOT_UNCHANGED_NATIVE_CONTEXT**: own full raw outputs were generated under parental influence, then paired with inputs having only the explicit restatement block removed. Prior public history remains. Literal-copy checks reuse the existing conservative word/span helper; they neither establish truth/grounding of every sentence nor exclude all paraphrase. Semantic influence itself is treatment, not a blanket exclusion. Main four-row review remains required, but cannot override shortage in this protocol.

No target's own outcome, future result, RECORD, hidden label or corrected answer is inserted. Wrong predictions are retained. No training/readout/confirmation requests are generated. Proposed eventual two fresh own-arm rows, r8/seed2/LR1e-4/batch2/12 updates per arm remain outside this exporter; no warm-start from SEQ111 and no fit launched. Naturally unequal raw target/input tokens must be reported, not token-matched by padding. Native feasibility is unmeasured. Current real capsule cannot produce a complete pair under frozen eligibility. No parenting, generality, clean-lineage, latent-erasure or semantic-certification claim follows.

**EDIT-STOP.** Main owns manual inspection, any subsequent decision, immutable-source/native audit, writer orchestration and Git/GPU operations.
