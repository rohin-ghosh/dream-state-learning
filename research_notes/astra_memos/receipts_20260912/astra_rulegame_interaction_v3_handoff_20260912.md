# RuleGame interaction_v3 — 2026-09-12 — EDITSTOP

**Implemented directly within Main's accepted non-material scope. CPU PASS: 46 diagnostic + 30 actual-record exporter tests.** No new formation, model/native tokenizer run, fit, GPU operation, network access or Git operation occurred. Main retains sole Git/launch authority. No H1/H2, task, lineage, parent-visibility, selection or record-faithfulness invariant changed.

## Exclusive scope / exact final SHA256

The actual existing diagnostic test path was verified as `tests/test_rulegame_parenting_diagnostic.py`. Only the following four repository files and this handoff were edited:

| File | Final SHA256 |
|---|---|
| `organism_v6/rulegame_parenting_diagnostic.py` | `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526` |
| `organism_v6/rulegame_record_material.py` | `7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1` |
| `tests/test_rulegame_parenting_diagnostic.py` | `dcd755064dc753d934b5a8e7ad74f8f8ac56bc4330a591a2e731083a5900649f` |
| `tests/test_rulegame_record_material.py` | `4ef73e758324673ea03bf6cc87cd208a3a2d0299c24b8438acd3e8b2f1d71caf` |

The accepted report was **already archived** at `research_notes/astra_memos/receipts_20260912/astra_rulegame_formation_repair_decision_20260912.md`. Its bytes and the original `/tmp/astra_rulegame_formation_repair_decision_20260912.md` both still hash to `0a07b01e5d1a6d20951f61b6372976606ac9fe95232b851c5791fef122334a78`. Neither copy was modified; no duplicate archive or out-of-scope write was needed.

## Implemented contract

- **Explicit `interaction_v3` protocol:** available through the existing prepare-only `--protocol` option; strict_v1 remains the default. V3 inherits v2 action aliases, one-action boundary, stop settings, public harness state and execution logging. Existing task schedule, generation seeds, temperatures, role/call/token caps, training constants and first-two selection are unchanged. P parent guidance and its visible pre-task transcript remain unchanged; no sealed readout data is supplied.
- **Prospective A parent:** `CONTROL_V3` permits neutral participation and optional accurate recap of already-visible events. It prohibits new strategy, hypotheses, recommendations, evaluated corrections, invented facts, hidden rules and future answers. This is not an acknowledgment-only or no-task-information control.
- **Child content unrestricted in both arms:** both receive the same ordinary own-word restatement request, retaining the existing 2–3-sentence phrasing and token budget. V3 removes A's acknowledgment-only/no-reflection content restriction. Spontaneous child reflection is not parent leakage or a purity acceptance decision; actual exported record fidelity and teacher/restatement-exclusion rules still apply.
- **Separate Main assessment scopes:** `main_audit_contract("interaction_v3")` at `rulegame_parenting_diagnostic.py:113` is returned in the v3 formation result and audit template. Each review has a `parent_contract`, a separate `child_criterion`, and free `child_observations`. Existing `decision`/`notes` assess parent-supplied content, not child purity. Contract/scope fields must match the template; child observations are not a second accept/reject gate. Legacy audit templates retain their original shape. Export additionally retains its existing selection-bound Main context/target `record_review`; no automatic semantic or model-authentication certificate is introduced.

## Shared record prompt and export

`record_instruction(protocol)` (`rulegame_parenting_diagnostic.py:101`) and `record_prompt(execution, output, protocol)` (`:106`) are the single prompt construction path for generation, world/call replay, and actual-record export. For v1/v2 the exact old prompt is returned. For v3 the old full-JSON RECORD instruction is followed by one newline and precisely:

> Explicit mapping: no prediction (null) => unavailable; prediction equal to observation => matched; prediction different from observation => mismatched.

This identical public definition is applied to both formation arms and parent-free readout records. Context still contains actual emitted child output, already-public world outcome and the original observed fields; no case-specific label, future action, synthetic Situation, target correction, string surgery or raw-record reserialization is added. Unknown versions, wrong request/header versions, missing/altered/duplicated definition text and old-control substitution fail closed under source replay and export checks.

`rulegame_record_material.build_record_pair` (`:97`) keeps its existing API and atomic pair behavior. It validates the captured protocol and uses the shared helper to verify, not replace, stored context bytes. The public version-specific definition joins known protocol vocabulary in conservative copied-span checks; substantive lesson/restatement echoes still fail in raw context, rendered masked context and target. Shared words alone are not leakage proof, and passing lexical checks is not semantic certification. Raw target whitespace, causal target labels and one appended EOS remain checked through V3 encoding/collation. No later favorable replacements are selected.

**Important consumption boundary:** v3 cannot enter legacy `material`/`verify_material` synthetic-prefix paths (`rulegame_parenting_diagnostic.py:700`, `:737`); these fail explicitly before creating legacy material. V1/v2 paths remain unchanged. V3 material is obtained through `build_record_pair` with an accepted Main audit, unchanged selection and verified capture, then consumed with `chat_template=False`, `add_eos=True`, `pack=False`. This assignment does not add a live V3 write CLI or silently adapt the legacy writer. Formation is implemented; downstream scheduling/integration stays with Main.

## Validation actually performed

All commands used `PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=''`:

```bash
python3 -B -m unittest discover -s tests -p 'test_rulegame_*diagnostic.py' -v
python3 -B -m unittest discover -s tests -p test_rulegame_record_material.py -v
```

- **46 diagnostic tests pass** (final run 16.699s); **30 exporter tests pass** (38.252s). The initial diagnostic run before the final two tests passed 44 tests. Test names mentioning native/VLLM exercise stubs/mocks and a character tokenizer, not a real native model. Existing CPU subprocess-supervision tests also ran; no GPU process was launched.
- New coverage pins pre-edit v1/v2 request, event, result and selection hashes; exercises exact mapping and shared-helper usage across formation/replay/export; checks caps/seeds/temperatures, alias/stop parity, separate parent/child scopes, accurate neutral recap with spontaneous child reflection, Main rejection, version/string/control tamper, parent/restatement spans, unchanged shortage/faithfulness/selection, parent blindness, parent-free readout definition, and exclusion of synthetic fallback. Existing atomicity/raw-byte/causal-label/EOS regressions pass.
- Additional **read-only CPU replay** of archived actual formation captures passed with no material promotion: strict_v1 manifest `d4a157f3a4e39a46dad20282e14192663b6d0320990ec80818d6a7ad1160ef68` still selects P0/A2; interaction_v2 manifest `4fef2770a6be151bc00fc4782575134643f8754b2cd149380b48a4aaf6dfed41` still selects P1/A2. Manifest hashes remain unchanged. SEQ095 stays declined; no historical record or SEQ096 response is reused as new training material.

## Remaining evidence — not executed

No v3 real-model formation or native success is claimed. Main's next actual capture must independently satisfy the unchanged provenance checks and explicit Main assessment, then run the actual pinned-tokenizer rendering/input-ID/output-decoding and V3 causal-mask/one-EOS checks on the fixed paired records. Any learning claim still needs matched write/save and fresh parent-free reload evidence. CPU fixture success is not parenting efficacy, selective learning, model-origin authentication, H1/H2 closure or mechanism freeze.

**EDITSTOP. No further edits or ownership; Main owns integration, Git and launch.**
