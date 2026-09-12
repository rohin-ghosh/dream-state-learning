# Process material V2 amendment — EDIT-STOP, 2026-09-12

## Scope and outcome

Implemented Main's **after-inventory exploratory amendment 96a71289** in only:
- `organism_v6/rulegame_process_material.py`
- `tests/test_rulegame_process_material.py`
- this handoff.

V1 remains the default, with its original policy and canonical-ACT requirement. The archived V1 candidate/handoff were not touched. **V1 still reports PAIRED_SHORTAGE** on actual fixed A/lesson0 call 0039. **Explicit V2 reports AVAILABLE_PENDING_MAIN_REVIEW** on all four fixed slots. This is not a retrospective V1 pass or a prospectively unseen protocol test. No later replacement, correctness filter, rewritten target, source alteration, export, or model call occurred.

## Stable API for the distinct writer bridge

```python
from organism_v6 import rulegame_process_material as process

protocol = process.PROTOCOL_V2  # "rulegame_grounded_process_pair_v2"
candidate = process.inspect_capture(capture_root, protocol=protocol)
review = process.review_template(candidate, protocol=protocol)

# Main supplies a new candidate-bound review receipt using its actual review.
# Do not reuse a V1 review or automatically assert semantic certification.
pair = process.build_process_pair(
    capture_root, main_review, tokenizer,
    fixed_candidate=candidate, max_len=4096, protocol=protocol,
)
manifest = process.export_pair(
    capture_root, fresh_output_root, main_review, tokenizer,
    fixed_candidate=candidate, max_len=4096, protocol=protocol,
)
```

All four APIs have keyword-only `protocol=PROTOCOL` (V1) defaults. `validate_wake(text, *, protocol=PROTOCOL)` also supports explicit V2. **Pass V2 throughout, including `review_template`; no implicit protocol inference.** Unknown protocols fail closed. Candidate, review, returned pair, item view/metadata, and export manifest carry the selected namespace. Candidate policy bytes and source hashes bind the review and manifest. Cross-version reviews/candidates fail even when every target happens to use canonical ACT. No new fit/launch CLI is included.

`POLICY_V2` explicitly records amendment 96a71289, `after_inventory_exploratory=True`, V1 as `prior_protocol`, native grammar `interaction_v3`, and `raw_target_canonicalization=False`. V1 `POLICY` remains unchanged. Returned policy objects are copied so mutating a candidate's policy does not mutate module policy constants.

V2 delegates parsing to unchanged `diagnostic.parse_action(text, "interaction_v3")`, requires TRY kind and exactly one explicit, unambiguous `PREDICT: T/F` before the actual sole action marker in the original text. The native grammar accepts `ACT: TRY ...` or `TRY: ...`; malformed spacing/case, unanchored markers, multiple ACT/TRY/QUIZ markers, DONE coexistence, quiz actions and invented OUTCOME fail as before. The parser internally interprets aliases for execution matching; **the exporter never writes the normalized action into the target**. Full original raw wake bytes and their separate training encoding are preserved.

Selection/reconstruction/source joins/teacher-copy checks are unchanged. V2 does not bypass missing predictions, prediction-after-alias, substantive literal teacher echoes, source execution mismatches, or shortages. Wrong predictions remain unchanged targets. Same native tokenizer callback, full mask/EOS/offset audits, no packing/drops/splits/truncation, and fresh atomic paired output behavior as V1.

Output paths remain `corpora/P.json`, `corpora/A.json`, `audit/candidate.json`, `audit/main_review.json`, `audit/token_receipts.json`, and `manifest.json`, under a **new V2 root**. Never reuse the archived V1 root. The existing no-replace publication also rejects an occupied root across protocols. Only `manifest['corpus_files']` are training inputs; audit-only teacher sources are not corpus inputs. V3 writer settings remain `chat_template=False, add_eos=True, pack=False`, bounded audited max length. Native tokenizer/model identity provenance must still be checked by Main; the sidecar loads neither.

## Fixed local capsule comparison

Source capture:
`/tmp/astra_rulegame_v3_formation_terminal_20260912/astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1/formation/data`

Recomputed archive SHA256 **05b9177bb83e800f4f9c10bbc5e34c27c7dd68e2fabe9c18c006c12e6971f90e** and all **141** extracted member SHA256 values against adjacent `.tgz.validation.json`: PASS.

| Fixed slot | Call | Tick | V1 CPU eligibility | V2 CPU eligibility |
|---|---|---:|---|---|
| P/lesson0 | 0009 | 2 | PASS | PASS |
| P/lesson1 | 0024 | 2 | PASS | PASS |
| A/lesson0 | 0039 | 2 | SHORTAGE: missing canonical ACT | PASS, unchanged native TRY alias |
| A/lesson1 | 0054 | 2 | PASS | PASS |

Exact equality checks PASS across versions for fixed slots, selection SHA, all source receipts/execution joins, transformed contexts, whole raw targets, removed byte intervals and preceding public history. No score-based selection occurred.

```text
selection SHA256 (unchanged)
e321f805eab317978416edd823aa849e34fd97f4940a3279017315e909dbfe0f
V2 policy SHA256
f5f671d01d38b2dc3a56af19adbbd2a5cf1bfcf24c592468e0cb6fac8669cfe8
V1 candidate under CURRENT exporter source
65f7b7ffb3623c8f9d0545dc9a55c525765cd5ded2275b5acf2bb0ac77714771
V2 candidate under CURRENT exporter source
fdde7bb3d28f0c3cac3732e434500d832a82fd90aca93a69bcdf121954e4133b
```

Current V1 candidate SHA differs from the archived V1 candidate because exporter source hashes changed; this does not replace the archive. Candidate hashes also bind absolute capture/plan paths. Main must recompute on final immutable native source/path and bind its review there. Main reports inspecting all four contexts/targets; the exporter nevertheless requires the actual V2-bound review receipt and never asserts formal semantic certification.

## CPU receipts and hashes

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_rulegame_process_material.py -q
```

**45 tests PASS, no skips, 33.119s:** all original 33 V1 tests retained plus 12 added tests. New coverage includes alias/canonical native acceptance, actual marker position, multiple/malformed action markers, unchanged raw bytes/token IDs/source/slots, no later replacement, retained literal-copy rejection, explicit review protocol, cross-version review/candidate rejection, stale policy even if self-rehashed, V2 publication namespace/no overwrite, unknown protocols and source execution joins. Scripted CPU fixtures only; no native tokenizer/model validation. Legacy modules were not edited or rerun in this amendment.

```text
organism_v6/rulegame_process_material.py
a060f11165e68baa9baaf50433e157e2b3d348a3577e4fbc8ba540d269c24168
tests/test_rulegame_process_material.py
23741eba5b83194931509910cc5e1bf34c1f9dd28ee1948a2fe95dc6d4ac0923
```

**Limits:** after-inventory exploratory context distillation, not unchanged native conditioning, clean lineage, generality or semantic certification. Local origin remains unresolved; native token audit/fit feasibility are pending. No real corpus export, native/GPU/SSH/network/Git operations, or changes to frozen controllers/other agents' files. Main owns the new bound review, separate writer bridge, native preparation and launches. **EDIT-STOP.**
