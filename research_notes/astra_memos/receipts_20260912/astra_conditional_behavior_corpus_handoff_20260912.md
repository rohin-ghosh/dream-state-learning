# Conditional behavior corpus — CPU handoff, 2026-09-12

**EDIT-STOP. Ready for Main's native tokenizer audit; not native-certified or launch-approved by this artifact.**

## Owned files and exact hashes

- `organism_v6/conditional_behavior_corpus.py` — SHA256 `a0ea3717508f05b751935fa3070792d33fe4a21dd46d8a2a93dadb6c2a8b606a`
- `tests/test_conditional_behavior_corpus.py` — SHA256 `33dff503eeccc9aa1e0c95db7df44bf7356eb8d6d47ee90e6ef27e83112cdd46`
- This handoff is the only other written file. No Git, network, GPU/model calls, runner, manuscript, logs, or empirical outcomes were touched.

## Design and control correctness

Sources: `research_notes/analysis/2026-09-12_behavior_memory_bridge_and_level1_intertwining_protocol.md`; `research_notes/analysis/2026-09-12_l0_to_h1_smallest_decisive_gate_sequence.md` Gate1; accepted operational clarifications in `/tmp/astra_conditional_behavior_design_audit_20260912.md` and Main's shared-group instruction.

- Each arm has 128 isolated rows: deterministic alternating 64 PROSPECT and 64 REVISE. AUTH/DERANGED have exactly the same prompts; DERANGED complements the decision through complete closed target swaps.
- PROSPECT training is 16 semantic instances ×4 renderings (four full squares). REVISE is 16 outcome pairs ×2 renderings (eight full squares). These are repeated binary-world instances, not 16 distinct Boolean rules.
- Dev has eight full crossed squares per operation, 32 cases each: 16 goal and 16 belief twins on the same PROSPECT cases; 16 outcome and 16 prior-action twins on the same REVISE cases. Visible CASE/form/nuisances are shared throughout each square. Both action names are public in REVISE.
- Train/dev instance IDs, contexts and template families are disjoint. Every row retains source-event IDs and explicit oracle/authored diagnostic provenance, not child's experience or clean lineage. There are 112 authored source records; no confirmation cases or composition training rows.
- Each consecutive four-row batch is P/R/P/R with one shared `group` and orders 0/1/2/3. DERANGED targets are AUTH targets in order `[2,3,0,1]`. Actual v3 group-block shuffle preserves these batches; arbitrary row shuffling is not supported.
- Restricted lookup audits enumerate exact best full-joint accuracy (`sum_z max_y count(z,y)/N`) under fixed allowlisted projections. All applicable train/dev, arm/root ceilings are ≤.50. Constant joint=.25; PROSPECT goal-only and first-listed-action-with-binding=.50; REVISE prior-action-name=.50; other applicable registered projections=.25. Absent features are N/A. Goal-only predicted outcome=1 is allowed, not a contradiction. Absolute index/unique-ID oracle policies are expressly excluded; repeated batch-slot policy is included.
- No unresolved mathematical incompatibility under the accepted clarifications. Tampered source, labels, prompts, ordering/group, splits, twins, or audited shortcut correlations fail rather than silently loosening the contract.

## Main's next executable CPU audit

Public entry points are in `organism_v6/conditional_behavior_corpus.py`: recipe at line91, build at270, pure audit at344, v3 items at385, callback audit at398, native audit at495, scoring at554/586, teacher-forcing interface at641.

```python
from organism_v6.conditional_behavior_corpus import (
    build_candidate, audit_candidate, audit_native, training_recipe,
    score_outputs, teacher_forcing_interface,
)

candidate = build_candidate(root=0)
pure_report = audit_candidate(candidate)
recipe = training_recipe(learning_rate=1e-4, seed=0)
# 1e-4 is Main's prospective choice, not a default or optimum selected here.
native_report = audit_native(candidate, local_model_directory, expected_tokenizer_hashes)
auth_training_document = {"corpus": native_report["corpora"]["AUTH"]}
deranged_training_document = {"corpus": native_report["corpora"]["DERANGED"]}
# Caller handles serialization/execution; these APIs do not write files.
```

`expected_tokenizer_hashes` maps local filenames to SHA256. Required: `config.json`, `tokenizer.json`, `tokenizer_config.json`, plus any present `vocab.json`, `merges.txt`, `special_tokens_map.json`, `added_tokens.json`, `chat_template.jinja`, `chat_template.json`. An external `chat_templates` directory is explicitly unsupported. The audit loads only the local tokenizer with `local_files_only=True`, `trust_remote_code=False`, validates Qwen2 config, and rechecks supplied hashes. It does not load model weights or certify their origin.

Use the returned native-rendered corpora unchanged with the returned recipe: fresh single rank8/alpha16 adapter, dropout .05, four epochs, batch4/accum1, 32 updates/epoch, 128 total, no packing or warmstart, target-only loss with EOS. LR remains required in the API; omission fails. Native corpora already contain chat-rendered input spans, so `chat_template=False` is intentional. Although v3's recipe uses its existing `overflow="truncate"` option, the prerequisite audit rejects every overflow and verifies zero dropped tokens; it does not license truncation.

The native audit runs the actual v3 normalizer, encoder, group ordering and collator for all three optimizer seeds ×four epochs. It checks identical paired prefixes, equal context lengths within swaps, complete supervised sequence swaps including EOS, joint context/target/total/EOS-position length multisets and token multisets per actual batch, exact masks/positions, no loss-bearing padding, and no truncation. Return fields include native corpora, per-row IDs/masks and all optimizer schedules. `input_tokens_per_epoch` counts the entire unpadded training sequence (context+target+EOS); `target_tokens_per_epoch` counts supervised target+EOS. Four-epoch processed totals multiply these per-epoch counts by four. No native token counts are asserted here.

`audit_tokenizer(candidate, fixture_or_callback)` is an explicitly untrusted/fixture route and never returns native certification. Tests exercised it with local fixture tokenizers; no actual tokenizer was installed or called in this task. Nonce spelling pairs are configurable; if actual matching fails, report that failure rather than bypass it.

## Scorer and assay boundaries

`score_outputs(candidate, raw_by_case_id, split="dev", assigned_arm="AUTH")` requires the exact complete case-ID set (64 dev or128 train). Use `assigned_arm="DERANGED"` for its own trained map; AUTH semantics remain reported separately. It retains raw output, strict exact syntax, component correctness, full joint semantics, strict-and-joint, per-operation/stratum metrics, and both semantic and strict twin passes. Invalid outputs stay in denominators. Missing/extra IDs raise; they are not replaced with scientific zeros.

Strict strings for the first AUTH pair of each operation are:

```text
PREDICT: dax -> mip
ACT: dax
```

```text
COMPARE: MATCH
POLICY: KEEP
NEXT: dax
```

The conservative semantic parser can distinguish a benign whitespace/field-order deviation from a semantic error, but does not rewrite raw text. Unknown prose, synonyms, duplicate/ambiguous fields cannot rescue joint success. Belief twins flip selected action, not predicted outcome; prior-action twins flip NEXT, not COMPARE/POLICY. Strata are AUTH-grounded plus public input/nuisance features, explicitly labeled even when scoring DERANGED.

Exact threshold arithmetic reports 31/32 for .95, 116/128 for .90, and zero allowed spill at .05×16. It does not disguise30/32 as95% or evaluate an L1 verdict. Future teacher-forcing interface supplies two complete continuations from a shared input-only prefix/empty assistant stub; never gold earlier output fields. Primary contrast families are fixed to PROSPECT belief and REVISE outcome. Composition remains a separate untrained future assay with no chain rows. No claim of cognition, H1, general learning, optimal LR, or L1 pass is supplied.

## Validation

**117 passed in3.01s:** 41 conditional tests plus76 neighboring fundamental corpus tests, no skips. Candidate JSON serialization and pure audit also succeeded. Tests cover independent literal truth tables/public prompts, all root permutations, exact squares/twins, counts/splits/source bindings, marginal and shortcut audits/tampering, v3 schemas, closed swaps/EOS/padding/overflow/group-shuffle parity, symmetric strict/semantic scoring and threshold rounding.

Executed without install/network, bytecode writes or pytest cache:

```bash
PYTHONPATH="/data/home/rohing/dream-state:/home/rohing/.cache/uv/archive-v0/x1HSjiSiIHWXFVFO:/home/rohing/.cache/uv/archive-v0/otX-mnihYO-Z_5I0:/home/rohing/.cache/uv/archive-v0/40CHA3uYuGrxepLQ:/home/rohing/.cache/uv/archive-v0/WhvpL9vEtag5Xx96:/home/rohing/.cache/uv/archive-v0/_og-n3yIa91AcMqC" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
python3 -m pytest -q -p no:cacheprovider \
tests/test_conditional_behavior_corpus.py \
tests/test_fundamental_two_habit_corpus.py \
tests/test_fundamental_teaching_corpus.py
```

**EDIT-STOP: Main may review/integrate and run the native corpus audit next.**
