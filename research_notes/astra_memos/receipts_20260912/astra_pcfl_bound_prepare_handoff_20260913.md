# PCFL bound-world preparer — EDITSTOP, September 13, 2026

Narrow integration complete. This binds the prospective world definition; it
does NOT complete the execution contract, qualify production rendering, certify
native custody, or authorize model/native calls. Formal C11 remains deferred.

## Ownership and authority

Only these paths were changed in this assignment:

- `organism_v6/pcfl_vertical_prepare.py`
- `tests/test_pcfl_vertical_prepare.py`
- `/tmp/astra_pcfl_bound_prepare_handoff_20260913.md`

Root AGENTS and local Git status/cached upstream divergence were inspected
before writes; no nested AGENTS were found under organism_v6/tests and no
additional /tmp AGENTS was present. Cached HEAD/origin/main divergence was 0/0
at intake. No network pull, network access, commit, push, native/GPU/model call,
tokenizer loading, or modification of another worker's files occurred.

Explicit new authority, not an inherited fact:

- Commit: `0418cb53`
- Path: `research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md`
- SHA256: `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91`

Both working-tree bytes and `git show 0418cb53:<path>` independently hashed to
that value. Existing six authority pins and the closure pin are unchanged.
Beauvoir's current source, not the stale unresolved section of the older core
handoff, supplied the concrete registry/API; its CPU tests were run read-only.

## Exact integration map

Public APIs and outer contract field names are unchanged:

```python
build_execution_contract(bindings, tokenizer_receipt)
validate_execution_contract(contract, profile_receipts=None)
validate_formation_binding(contract, corpus_id, queries, rows)
```

Caller supplies `bindings['core_registry'] = core.registries()` as before.
No new evidence argument or caller-authored world adapter is required.
The builder now detaches these exact fields without synthesizing a world:

```python
world = bindings['core_registry']['world_registry']
contract['production_bindings'] == {
    'distractor': world['distractor'],
    'probe_result_bytes': world['probe_result'],
}
```

`world['distractor']` is the complete **verbatim core
production_binding_status() object**, not merely its inner distractor subobject.
Its status is `WORLD_DEFINITION_BOUND`, definition_bound is true, source/path
match the memo above, and execution_contract_valid and
production_inventory_complete remain false. All existing pending entries are
preserved. Canonical comparison rejects typed Boolean/integer substitutions,
extra/missing status fields, source drift, and unilateral readiness promotion.

The concrete checks bind X->Z using existing q0/q1 selected by D; terminal D;
no witnessed/fitted latent transition; PROBE r10 cannot support EVENT/LINK;
relevant H->S_R and r9; private G metadata and N public endpoint substitutions;
unchanged namespaces/inventory, visible port order, OLD source order and
chronological handles. Result bytes for either frontier are exactly:

```text
PROBE RESULT {probe} TESTED {source} TO {destination} AVAILABLE PORT {port}\n
```

Here `\n` denotes exactly one LF. No terminal message or public receipt ID is
added. The preparer contains no duplicate world executor or route solver.
Tests execute the actual bound core to verify one-shot/malformed/unlisted
behavior, terminal D with no relevant continuation, ordinary R continuation
with separate r8 EXPLORE, PROBE receipt exclusion, full-private latent edge,
route/cut and pre-outcome/outcome quartet checks.

**No chronological bank remapping changed.** Existing free-choice versus ideal
bank mismatch regression still passes. Formation mismatch remains
VS_FORMATION_BANK_MISMATCH, not permission to insert oracle rows or reseal
slots from outputs. The caller still supplies real presealed banks/schedules.

Old unresolved contracts intentionally fail this new prospective schema.
For a new pre-output preparation, rebuild from the bound registry; changing it
changes the decision/root-skeleton/contract hashes. Do not edit old receipts,
posthoc reseal formation outputs, or reuse old decision-bound evidence.

## Remaining gates (not removed)

Exactly these two obsolete missing-interface markers were removed after the
bound CPU checks:

- `production_D_frontier_outcome_receipt_and_terminal_bytes_binding`
- `production_R_and_D_public_probe_result_bytes_binding`

All actual remaining interface markers persist:

- `core_render_parser_diagnostic_and_cut_oracle_certification`
- `joint_backtracker_first_solution_and_replay_counterpart_proof`
- `complete_tokenizer_inventory_and_response_mask_coverage`
- `expanded_diagnostic_service_load_and_denominator_coverage`
- `native_contract_hash_enforcement_and_actual_source_pin_verification`
- `profile_receipt:<id>` for every missing profile
- `synthetic_evidence_is_not_execution_evidence` when applicable

Both static_contract_complete and execution_contract_valid remain false;
ready_for_model_calls remains false. Pure validation checks pinned declarations,
not filesystem custody or current runtime behavior. Local memo verification and
CPU tests are recorded here, not fabricated as portable native attestations.
The deliberately synthetic contract fixtures still have artificial topology,
implementation hashes, tokenizer arrays and work rows; passing them does not
prove any real production contract exists. No token/profile measurements were
created or promoted. Full actual render coverage and native readiness remain
independent of this bound-world definition.

## Validation and frozen hashes

Final scoped run: **30 preparer tests PASS (16.598s)**.
Final read-only dependency run: **47 core tests PASS (1.730s)**.
Initial dependency run passed 39 tests; Beauvoir added tests concurrently.
The final core source AND core test hashes were identical before/after the
final two-suite run. No dependency edits were made by this worker.

| Path | SHA256 |
|---|---|
| organism_v6/pcfl_vertical_prepare.py | c07ba9b684299a8d6cf6c7b45bbdbb95ed6f3e04db9e8de6e926791610b55c61 |
| tests/test_pcfl_vertical_prepare.py | bcbcb56ab3f8c1d3d9aabbc055f1d9bbbf995052b2dde72e15951f92fcf58ba5 |
| organism_v6/pcfl_vertical_dev.py (read-only dependency) | ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e |
| tests/test_pcfl_vertical_dev.py (read-only dependency) | d4e621dc766967aec7ddf959106fd8fe2a401fbf8e6529526f1d8965b636647a |
| organism_v6/pcfl_tokenizer_qualification.py (unchanged) | da30eb90a8655ec0707dd8c83c22ed08f1032dadb7a663edd7102774e0e84d3a |
| tests/test_pcfl_tokenizer_qualification.py (unchanged) | 30b057078522cc5d0c2396749fb22d529f9935cb6d484eb610e26d1a445004be |

Commands actually run (read-only inspection plus owned apply_patch edits):

```sh
git status --short --branch
git log -4 --oneline
git rev-list --left-right --count HEAD...origin/main
find organism_v6 tests -name AGENTS.md -print
sha256sum research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md
git show 0418cb53:research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md | sha256sum
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_pcfl_vertical_prepare.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_pcfl_vertical_dev.py -q
git diff --check -- organism_v6/pcfl_vertical_prepare.py tests/test_pcfl_vertical_prepare.py
sha256sum organism_v6/pcfl_vertical_prepare.py tests/test_pcfl_vertical_prepare.py organism_v6/pcfl_vertical_dev.py tests/test_pcfl_vertical_dev.py organism_v6/pcfl_tokenizer_qualification.py tests/test_pcfl_tokenizer_qualification.py
```

Also ran in-memory ast.parse/compile for both owned Python files: PASS.
Whitespace check passed. Earlier preparer run: 30 PASS (16.852s).

At handoff inspection Main's concurrent Git state showed
`UU research_loop/COORDINATION.md` and staged research-note changes. These are
outside ownership and were untouched; Main owns any merge resolution. No
source/test work remains from this sidecar. EDITSTOP for Main review.
