# RuleGame actual-record material — 2026-09-12 — EDITSTOP

**CPU fixture PASS; implementation complete within assigned scope. Native evidence remains pending.** Non-material integration repair of the intended own-thinking/context contract, not a task, claim, invariant, selection, or curriculum change. No launch veto or additional reviewer framework introduced.

## Owned files and exact SHA256

| File | SHA256 |
|---|---|
| `organism_v6/rulegame_record_material.py` | `918f4dac22e15f5c6189f7fda7211c3a399036c3e7cfe9ab339a2c25ffb0f728` |
| `tests/test_rulegame_record_material.py` | `bd178872e2d889f4905fe95ea0b94a70c5ba2b1be0f136cbb29f1aa286d892bd` |

Only these two new repository files and this handoff were authored. No legacy module/test, RuleGame, renderer, main-selection code, prior note, or other worker file was edited. Test-created temporary capture fixtures were cleaned up. No Git, network, model loading, native tokenizer loading, training, or GPU operation was performed. There is no CLI, migration, corpus write, or automatic historical export.

## API and integration contract

`organism_v6/rulegame_record_material.py:98`:

```python
build_record_pair(capture_root, main_audit, fixed_selection, tokenizer,
                  max_len=4096, *, replay_verified_capture)
```

`capture_root` is the existing `formation/data` directory. Other inputs are already-read Main audit and complete unchanged `select_records` result, a caller-provided tokenizer, and existing CPU replay evidence. The exporter reruns `check_capture` and compares the complete supplied evidence by canonical value hash; an asserted `ok=True` is insufficient. It returns both `corpora.P` and `corpora.A`, source/teacher receipts, capture inventory/identity, formation/audit/selection bindings and encoding options, or raises before returning either arm. All selected rows must pass; later eligible rows are never substitutes.

The existing Main formation review remains required via `validate_main_audit`. In addition, **Main must author**, not the exporter synthesize, `main_audit.record_review` with:

- `decision: "accept"` and substantive `notes` covering actual raw/rendered record contexts and raw targets;
- `scope: "actual_record_context_and_target"`;
- `selection_sha256: diagnostic.value_hash(fixed_selection)`.

The enclosing audit is already bound to the formation manifest. Missing, rejected, or misbound review fails. This small supplemental assessment makes the context/target semantic decision explicit without altering the legacy audit validator. The test fixture's acceptance is mock-only and is not approval of real material.

## What is preserved and checked

- `check_capture`, `validate_main_audit`, `select_records`, `judge_record`, and `audit_native_calls` are reused unchanged. The latter is exercised only with a scripted character tokenizer in these tests. Replay checks requests/seeds/context, model-identity receipts, raw hashes, call chronology, world outcomes, event reconstruction, inventory and budgets.
- Selected record → unique preceding execution → source wake joins include arm/eid/tick/call IDs. Actual record request is verified against emitted wake output plus its **already-public world outcome** and observed fields; the stored request is then used unchanged. A wake request, synthetic Situation, extra future answer, wrong source/tick/outcome, orphan, or resealed inconsistent history fails. Snapshot inventory is rechecked before returning.
- `:24`/`:40`: all source-bound delivered parent/restatement messages supply full-payload, line/sentence and six-word copied-span checks on **raw context, rendered masked context, and target**. Matching prose fails, never gets stripped. Known RECORD/action vocabulary and numeric triples alone are not treated as proof of pedagogical copying. This lexical heuristic does not certify semantic nonleakage, detect every paraphrase, or authenticate a model/actor; Main's review and inherited provenance remain necessary. Hashes establish artifact consistency/origin binding, not resistance to a wholly fabricated self-consistent capture plus forged human approval.
- `:59`: spans are exactly `[actual_rendered_record_request, False, "record_context"]` and `[complete_raw_record_text, True, "own_raw_record"]`. Whitespace, JSON key order and raw target bytes are preserved; the target is never JSON-reserialized. JSON reconstruction is confined to verifying the existing observed-fields portion of the request, not generating a replacement context or target.
- V3 `encode_item_segments`/`collate` must produce context IDs + raw-target IDs + exactly one appended EOS, with context labels `-100`, the correct first-target predictor and all raw-target/EOS labels. Captured native rendering/prompt IDs and output decoding must agree with the supplied tokenizer. Empty targets, embedded target EOS, split/dropped/truncated material, overlength, changed labels or EOS fail. Returned options require **`chat_template=False`, `add_eos=True`, `pack=False`**, using the same tokenizer/max length for consumption.
- Receipts bind original per-arm selection ordinal, full execution ID, both calls' request/response file hashes, event indices/hashes and UTF-8 context/target hashes. Both automatic semantic-certification and model-authentication flags are false. SEQ095 remains declined, was not read as training input, and is not seeded or reclassified here.

## Tests actually run

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
  python3 -B -m unittest discover -s tests -p test_rulegame_record_material.py -v
```

Final result: **24 tests passed in 30.010 seconds**. An initial `python` invocation failed because that executable was absent; using `python3` resolved the command issue. The earlier 21-test version also passed before the final edge-case additions.

Coverage: actual producer→replay→fixed selection→paired V3 fixture roundtrip (both existing protocols); exact whitespace; tampered/resealed source/context/tick/outcome/join/identity/chronology; missing/orphan/duplicate events/calls; forged replay proof and manifest binding; rejected Main/semantic review; altered selection; shortage/SEQ095-like decline without historical seeding; false versus null prediction, ambiguity and wrong relation; copied payload/sentence/restatement in raw or masked-only context and target; shared-protocol exception; later-valid-record nonreplacement; second-arm failure with no partial return; rendering/input/output token mismatch; off-by-one labels/context loss/missing or double EOS; empty target tokens, overlength/splitting; and capture mutation before return. Fixtures use actual legacy producers and pure V3 encoding, not mocked export success.

## Exact remaining native check — NOT EXECUTED

On **separately available, replay-verified, Main-accepted paired material with the unchanged first-two selection**, use the actual pinned local tokenizer and captured record requests/responses to verify native rendered prompt/input IDs and raw output decoding, then the actual V3 causal input/labels/first-target boundary/one-EOS path with no extra template, packing, splitting or truncation. This work supplies the checks but has not established their native result. Do not use declined SEQ095 to satisfy this prerequisite or fill a shortage.

Any subsequent learning claim still needs the paired saved-adapter/write evidence and **fresh parent-free reload** readout with the inherited matched controls and score-visibility/provenance restrictions. No fit, adapter persistence, reload, behavioral improvement, or parenting competency result is claimed by these CPU fixtures. Integration/launch scheduling stays with Main. **EDITSTOP: no further source ownership or edits.**
