# BIRTH conditional corpus — EDIT-STOP

Requested handoff filename retained. **CPU candidate/scorer implementation complete; native token audit and all fitting/readout work remain with Main/runner.** No prior corpus, result, or source module was edited. No runner, GPU/model/native-tokenizer call, SSH, network, or Git operation was performed.

## Owned files and exact hashes

- `organism_v6/birth_conditional_corpus.py` — SHA256 `43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b`
- `tests/test_birth_conditional_corpus.py` — SHA256 `7154e51930cdce7fc4857e6a63216271a1b2ae5154dde07c45a522691cb73c29`
- This handoff is the only other written deliverable.

## Frozen runner-facing API

In `organism_v6/birth_conditional_corpus.py`:

```python
build_candidate(root=0, action_labels=("dax", "wug"), outcome_labels=("fep", "nup"))
audit_candidate(candidate)
training_recipe(*, learning_rate, seed, epochs)
train_items(candidate, arm, render_context=None)
readout_cases(candidate, *, split="dev")
audit_tokenizer(candidate, tokenizer, *, recipe=None, epochs=None, seeds=None, max_len=512)
audit_native(candidate, model_path, expected_file_hashes, *, recipe=None, epochs=None, seeds=None)
score_response(case, raw, *, assigned_arm="AUTH")
score_outputs(candidate, outputs, *, split="dev", assigned_arm="AUTH")
```

Canonical runner route is `recipe=training_recipe(...)` for both tokenizer audits. Audit-only callers may instead supply explicit `epochs` and optional `seeds`; conflicting recipe/epoch/seed specifications fail. Recipe requires explicit LR, seed and epochs: there are **no LR/epoch defaults**. Supported recipe optimizer seeds are0/1/2, inherited from the existing v3 recipe helper. Root spellings can be permuted with roots0/1/2; this does not imply replications were run.

Relevant entry lines: builder192, recipe199, readout207, pure audit260, train items292, callback audit302, native audit403, response scorer423, panel scorer458.

## Actual balanced design and counts

**Batch8, grad_accum1, no packing.** Each of32 optimizer groups contains:

`P0, R0, P1, R1, ADD0, ADD1, COPY0, COPY1`

P is a goal-flip pair; R is an **EXPECTED-flip** pair holding OBSERVED and PRIOR fixed. Every row has the same group ID within the block and orders0..7. DERANGED target strings are AUTH targets in order **`[2,3,0,1,4,5,6,7]`**. Thus both anchors of each kind remain identical and truthful. Existing v3 consecutive-group shuffle preserves the whole eight-row batch; arbitrary row shuffle or batch4 is not this contract.

| Operation | Train/arm | Dev | Construction |
|---|---:|---:|---|
| PROSPECT |64|32|Train4 goal×belief squares ×4 renderings; dev8 squares ×1 held rendering each|
| REVISE |64|64|Train4 full8-case cubes ×2 renderings; dev8 full8-case cubes ×1 held rendering each|
| ADDITION |64|16|Truthful ACT-only integer sums; disjoint operand ranges and template families|
| COPY |64|16|Truthful COPY-only literals;64/16 distinct, disjoint literals and template families|
| **Total** |**256**|**128**|Same source/input rows in AUTH and DERANGED|

There are **304 source records**:176 train semantic/anchor sources and128 dev sources. Training renderings share their semantic source IDs. No confirmation selection exists; no chain/composition rows are trained. Readout of both train and dev would be384 inputs/state, but this module does not select states or launch calls.

Training constraints: fresh frozen-base **single rank8** adapter, no warmstart; recipe retains alpha16/dropout.05/AdamW/all projection modules/target-only loss/EOS, uses batch8 and no packing. `max_len=512`, native-pre-rendered contexts with `chat_template=False`, group shuffle enabled. Exactly **32 updates/epoch**, so caller-selected E epochs means32E updates. Main's prospective1e-4 can be supplied explicitly; this code makes no optimum/high-plasticity claim and does not choose E.

## REVISE shortcut repair and visibility

Every REVISE visible instance/rendering contains **all EXPECTED×OBSERVED×PRIOR combinations**. The visible CASE/instance ID, action ordering and template stay fixed within the eight-case cube. Both action names are public. Example fields:

```text
CASE birth-r0-train-revise-00. ACTIONS: dax, wug.
PRIOR: ACT dax.
EXPECTED: fep.
OBSERVED: nup.
Review before the next attempt.
```

The seven other cases cross both expected outcomes, both observed outcomes and both prior actions using this same instance ID. `EXPECTED` is no longer recoverable solely from the instance. Action ordering is balanced50/50 across each operation in train and dev, and constant within each cube/square; pure audit explicitly checks that balance.

The omission auditor enumerates the best lookup on **full joint output** using each remaining public factor **plus instance, template and action ordering**. In BOTH arms and BOTH splits:

- PROSPECT without belief or without goal: exactly .50 joint ceiling.
- REVISE without EXPECTED, without OBSERVED or without PRIOR: exactly .50 joint ceiling.
- Specifically, `(instance, template, action_order, OBSERVED, PRIOR)` without EXPECTED reaches only32/64 in both train and dev.
- Constant/template/action-order-only joint ceilings are .25; repeated batch-slot-only ceilings are ≤.50.

Source IDs, hidden corner IDs and absolute row-index oracles are not model inputs and are not granted to omitted-factor policies. Remaining task factors plus all visible nuisances are included. A separate batch-slot-only policy is audited, not a combined hidden row-position oracle. Component tautologies such as goal-only predicted outcome are not subject to a fabricated .50 ceiling. Structural metadata/canonical reconstruction and independent omission enumeration reject tampering or missing crossings; they do not constitute a model success gate.

Tests independently parse public prompts for both AUTH/DERANGED truth tables and calculate all omitted-factor lookups. Removing EXPECTED=1 rows recreates the old shortcut and is rejected, as is leaking EXPECTED through action ordering.

## Truthful anchors and held locality

- ADDITION train operands: left2..9 ×right12..19,64 ordered pairs. Dev: left31..34 ×right47..50,16 ordered pairs. All sums are derived from source operands. Targets contain only `ACT: <sum>`.
- COPY train values are `amber-<root>-000..063`; dev values `marble-<root>-000..015`. Targets contain only `COPY: <literal>`. These are literal copying examples, not arbitrary hidden fact binding.
- Anchor targets are byte-identical across arms. No false arithmetic or copy supervision is introduced. Train/dev IDs, semantic IDs, visible instance IDs, complete contexts, anchor payloads and per-operation template families are disjoint. No absence of broader historical exposure is asserted.
- Every row has `origin=ORACLE_AUTHORED_BIRTH_DIAGNOSTIC_NOT_OWN_WAKE_NOT_CLEAN_ANCESTRY` and `source_event_ids`. Source-event identifiers are never printed in the prompt. `readout_cases` retains those IDs as routing/provenance metadata only; **send only its `context` string to the model**.

## Candidate and native-audit schemas

Candidate schema string: `birth-conditional-crossed-v1`.

Main fields: `train["AUTH"/"DERANGED"]`, `dev`, `source_records`, `twins["train"/"dev"]`, `training_constraints`, `label_config`, `spellings`, `origin`, `confirmation_cases=[]`, `composition`, `supplies_l1_verdict=False`.

`readout_cases` records contain `id`, `context`, `operation`, `family`, `split`, `instance_id`, `template`, `source_event_ids`, `origin`. **No answer, expected key, target, factors or hidden input dictionary is exported through this input-only route.** Operation/family names are uppercase `PROSPECT`, `REVISE`, `ADDITION`, `COPY` (ADDITION emits ACT).

Native audit returns:

- `corpora[arm]`: native-rendered v3 span records; save for the trainer as `{"corpus": report["corpora"][arm]}`. `train_items` without native rendering is provisional, not certified.
- `rows[arm]`: `case_id`, `operation`, `group`, `order`, `prefix_ids`, full `input_ids`, `labels`, `context_tokens`, total `input_tokens`, supervised `target_tokens`, `supervised_eos_position`. Target count includes one EOS per row; input count includes context+target+EOS. Context labels are all-100.
- `optimizer_update_rows[str(seed)]`: actual v3 row-index order, eight indices/update,32 updates/epoch.
- `group_costs[str(seed)]`: one entry/update with epoch/update/group/row indices; context/input/target/EOS token totals, `padded_input_tokens` and `padding_tokens`. Costs apply **to each arm**, since exact arm equality is verified, not to the two-arm sum. Padding is never loss-bearing.
- `input_tokens_per_epoch[arm]`, `target_tokens_per_epoch[arm]`, `config_counts` (rows256, groups32, explicit epochs/update count, batch8/accum1/no packing, zero skipped/truncated/split rows), the supplied `recipe`, and `source_sha256` for this birth module, old conditional corpus and v3 trainer. `birth_source_sha256` is also explicit.
- `no_truncation=True`, `loss_bearing_padding=False`, `model_origin_authenticated=False`, `supplies_l1_verdict=False`.

All audits use the actual v3 normalizer, encoder, group ordering and collator. They verify whole supervised sequence swaps **including EOS**, native equal-length swap contexts, paired input equality, per-batch joint length/EOS-position/token/target-sequence multisets, zero drops/splits and real loss masks/positions/padding. Although v3 exposes `overflow="truncate"`, any overflow/drop is rejected before this material is certified.

The callback status is always `CALLBACK_AUDIT_PASS_NOT_NATIVE_CERTIFICATION`. The native entry point loads **only a local pinned tokenizer** (`local_files_only=True`, `trust_remote_code=False`); no model weights. It requires config/tokenizer/tokenizer_config hashes plus any existing vocab/merges/special/added-token/standalone-template files, verifies Qwen2 config and rechecks pins. External `chat_templates` directories are explicitly unsupported. On success status is `NATIVE_TOKEN_MATCH_VERIFIED`, with tokenizer path/hashes. No native token totals are asserted in this handoff; earlier conditional label matching does not certify these new contexts.

Example, for Main's later native preparation (not executed here):

```python
from organism_v6 import birth_conditional_corpus as birth

candidate = birth.build_candidate()
pure_audit = birth.audit_candidate(candidate)
recipe = birth.training_recipe(learning_rate=1e-4, seed=0, epochs=EPOCHS)
native = birth.audit_native(candidate, LOCAL_MODEL, TOKENIZER_HASHES, recipe=recipe)
auth_training = {"corpus": native["corpora"]["AUTH"]}
deranged_training = {"corpus": native["corpora"]["DERANGED"]}
held_inputs = birth.readout_cases(candidate)
metrics = birth.score_outputs(candidate, raw_by_id, split="dev", assigned_arm="AUTH")
```

## Descriptive scoring, not syntax-only success

`score_outputs` requires exactly256 train or128 dev IDs. Missing/extra IDs raise rather than becoming scientific zeros. Raw strings are retained. Conditional field/semantic parsing reuses the valid existing primitive, not its fixed old corpus selection/scorer. The new whole-panel scorer reports:

- Per-operation/per-stratum strict surface, AUTH and assigned-map component/joint/strict-joint correctness, exact target strings, instruction compliance, tag spill.
- Both anchor families' literal one-field instruction compliance, not just a numeric/string value found in prose. Extra phase fields spill and fail compliance. Optional final newline is accepted for a one-line anchor, while `exact_*` distinguishes bytes. Leading-zero arithmetic can be semantically right but fails canonical instruction-compliance comparison.
- Train twins:32 each belief/goal/expected/observed/prior-action; dev twins:16 belief,16 goal,32 each expected/observed/prior-action. Both endpoints must be correct and required fields must flip; semantic and strict pair endpoints remain separate.
- Belief swaps action, not goal/outcome. EXPECTED or OBSERVED swaps COMPARE/POLICY/NEXT; PRIOR swaps NEXT while match status is fixed. AUTH and DERANGED maps are evaluated separately, anchors identically.

A constant well-formed REVISE response scores64/64 syntax but only16/64 joint correctness and0 complete REVISE twin passes in tests. No overall PASS, birth/cognition qualification, L1/Q0/H1 verdict or automatic continuation is produced. The future composition/level2 entry is a declaration with zero trained chains; it is not implemented or satisfied here.

## Validation and remaining work

**133 CPU tests passed, no skips (24.71s):40 BIRTH tests +41 existing conditional corpus tests +52 conditional readout tests.** Native loader tests use mocks; all tokenizer audits executed here use character fixtures, not an installed/native tokenizer. Coverage includes independent prompt truth tables/all omitted-factor lookups, full within-ID cubes, action-order balance, truthful anchors/disjoint splits, source/target/group/twin tampering, strict-vs-semantic scoring, actual v3 eight-row shuffle/collation/EOS/padding, context-sensitive token mismatch, overflow, pin rejection and conflicting recipe inputs.

```bash
PYTHONPATH="/data/home/rohing/dream-state:/home/rohing/.cache/uv/archive-v0/x1HSjiSiIHWXFVFO:/home/rohing/.cache/uv/archive-v0/otX-mnihYO-Z_5I0:/home/rohing/.cache/uv/archive-v0/40CHA3uYuGrxepLQ:/home/rohing/.cache/uv/archive-v0/WhvpL9vEtag5Xx96:/home/rohing/.cache/uv/archive-v0/_og-n3yIa91AcMqC" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
python3 -m pytest -q -p no:cacheprovider tests/test_birth_conditional_corpus.py \
tests/test_conditional_behavior_corpus.py tests/test_conditional_behavior_readout.py
```

No known mathematical/control blocker remains in this design. **Pending externally:** native context/token matching and padding-cost profile, Main's explicit dose/resource selection, runner integration, fits and complete held readouts. This artifact neither makes those calls nor claims success from the CPU tests. Source spellings matching in an older corpus are not a substitute for the new native audit.

**EDIT-STOP. Exact owned bytes frozen for Main's integration.**
