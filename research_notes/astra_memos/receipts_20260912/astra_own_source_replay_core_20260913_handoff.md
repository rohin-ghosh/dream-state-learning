# Own-source TRAIN observation-reading replay core — EDITSTOP

September 13, 2026. CPU-only preparation and scripted fixture tests; no actual
child responses collected, no model/native/network/Git actions, no fitting,
and no old-source/repository edits. Main freezes recipient, replay/control
dose, sampling and native collection separately. No retention-repair decision
or claim is made by this core.

## Exact owned delivery

- `/tmp/astra_own_source_replay_core_20260913.py`
  SHA256 `f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a`
- `/tmp/test_astra_own_source_replay_core_20260913.py`
  SHA256 `6bf5c4d36ddcac8e8eadfb2744a50b7c964a42a878b49505b2063c1d8a51ad4a`
- This handoff's hash is supplied externally.

Schema: `astra_own_source_observation_replay_20260913_v1`.

## Semantic and selection decision, explicit before responses

The original96TRAIN rows are NOT96record-admissible examples. The frozen
material has4skins x6cases x4distinct sources:16each agreement,
contradicted_prediction, absent_prediction, ambiguous_prediction,
missing_outcome, outcome_action_mismatch. The first three cases provide
48source-admissible production records. The other48cannot support the
unchanged four-field public record grammar. Authored abstentions in the
original material are not production records and are not replay targets here.

**Default24 is intentionally supported-source-only**, not a balanced sample
of all96perception/abstention cases or a judgement corpus. Exact selection:

```text
4TRAIN skins x3admissible cases x2selected outcomes =24distinct sources
SUPPORTED case order = agreement, contradicted_prediction, absent_prediction
earlier_same iff (skin_index + case_index + int(selected_outcome)) %2 ==0
```

There are exactly two original sources per skin/case/outcome, one with the
earlier outcome agreeing and one opposing. That rule chooses one. It produces
6sources per skin;8each agreement/contradicted/absent;12true/12false outcomes;
8true/8false/8null priors;12earlier-same/12earlier-opposite. The2x2table of
earlier versus selected outcome has6in each cell. Selection uses public
source facts only, no model output, loss, held result, target answer or
fitted performance. Records and requests are ordered lexically by row_id.

All96source rows remain in the manifest/admission ledger:48unsupported
not requested,24supported not selected,24selected. Unsupported/unselected
are not relabeled as observed response failures or secretly removed from
the population denominator. Report96population,48supported,24requested
denominators separately; do not call a24/24selected result full96competence.

**Main must explicitly accept this supported-only selection before native
capture.** If Main instead wants the unsupported-source/abstention strata,
that is a separately versioned protocol; do not silently change this selection
or turn authored abstentions into positive record supervision.

## Fixed source/request hashes

Same selected source IDs and original prompt text across the three parents;
producer-bound request IDs differ. Cross-parent reuse is shared sourced
situations, NOT independent new sources.

Selection ID-list SHA256 for all three:
`5321a8862e2f9c19dddb57c43950351ea9105d9dce123cf4c4c02ee0ca84cbbb`

Prompt-request manifest SHA256 (includes producer binding):

```text
seed0 511e6a526a0203cba0c10197353cfdfae6616ed51acfb024507c5c1545179ef6
seed1 932fc7b2dd612e8e687e478b3399f629beeb4d4c528e3724e2718df75ffb0f81
seed2 4fce994b80ee5b9d3731b2c13c63dca5de3c75d7286281c047f403a7dac915dd
```

These hashes were computed by CPU `build` before any replay-response results.
They are independent of responses and fit decisions.

## API

```python
bundle = core.build(seed=0)
report = core.admit(bundle, supplied_responses)
```

Exact signatures:

```text
build(seed=0, *, archive_path=ARCHIVE, source_root=SOURCE_ROOT) -> bundle
admit(bundle, responses) -> admission_report
```

Only original perception parent seeds0/1/2 are accepted, not bool. No
recipient/fitting arguments, sampling configuration or native backend exists.
Default archive/source paths are declared below. A relocation may supply a
different path only with unchanged pinned source/archive bytes. There is no
user-selectable count, random seed, outcome-based filtering or dose ladder.

Each `bundle.requests[]` contains:

```text
schema, row_id, source_id, source_split="train",
input_messages, input_sha256, producer_sha256, request_id
```

**Send only `request.input_messages` to the child.** Those are byte-identical
to the original TRAIN row's messages. Do not send the surrounding bundle,
derived public_fields, diagnoses, source ledger, excluded IDs or producer
inventories as additional prompt context. The original generic four-field/
abstention instructions are retained, not augmented with row-specific proof
or labels. No answer field or teacher target is appended.

Each supplied response must have exactly these keys:

```python
{
    "request_id": request["request_id"],
    "input_sha256": request["input_sha256"],
    "producer_sha256": request["producer_sha256"],
    "raw": actual_child_raw_text,
    "finish_reason": actual_child_finish_reason,
}
```

These binding fields are declarations from the caller, not proof of native
generation. Main's future capture wrapper must verify the actual original
parent/model route and actual prompt, preserve its native receipts, and join
them to these request IDs. The core has no model calls or retries. Up to96
response objects can be audited to preserve foreign/duplicate submissions;
this is NOT permission to generate96responses for the24requests. All duplicate
responses to a requested ID are rejected; it never chooses the best retry.
Cross-invocation no-retry/once-capture enforcement belongs to Main's wrapper.

`admit` rebuilds and compares the entire bundle from pinned sources before
using any responses. It preserves every supplied JSON-compatible response
object in `responses` and its exact raw text in the audit, including rejects.
Unknown, held/canary/nonselected IDs, wrong prompt/producer bindings,
duplicates, non-text answers and non-stop completions cannot be admitted.
Malformed non-JSON-compatible transport is an API error, not a repaired row.

Eligible rows in `report.admitted` have:

```text
row_id, request_id, input_messages,
raw_target = the supplied response.raw unchanged,
target_sha256 = SHA256(response.raw UTF-8 bytes),
source = original TRAIN public source,
producer_sha256,
source_proof = original_train_row_id, original_source_id, input_sha256,
               supplied_response_sha256,
               target_origin="SUPPLIED_RAW_CHILD_RESPONSE_ONLY"
```

Raw whitespace, key order and numeric spelling are not normalized; fences
are not stripped. JSON storage escaping round-trips the same string/UTF-8
bytes. The only positive target assignment is from the supplied raw child
response. With no responses, admitted is empty and24requests remain missing.
No host-authored expected record is returned as supervision.

The report includes the complete96row `admission_ledger`, status counts,
admitted/rejected lists, missing request IDs, input bundle hash and preserved
producer/source provenance. Defaults remain `training_export_ready=false`,
`fit_decision=null`, `native_identity_verified=false` regardless of admissions.

## Existing source semantics reused, not rewritten

The canonical96manifest is the original archived `material.json` from the
perception runs, NOT the smaller standalone `birth_skill_corpus.build_slice`.
All three original parents used material_seed0 and the same material hash.
The corpus is reused for its public source assessor and production judge.

- Original Level1 runner:
  `/tmp/astra_level1_skill_run_20260913.py`, SHA256
  `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`.
  Inspected `prepare_inputs`, `validate_dataset`, `source_key`, `load_material`,
  and the prepared plan shape. No native helper or dataset target validator
  is invoked by the new core.
- Original authored material:
  `/tmp/astra_level1_perception_reflection_material_20260913.py`, SHA256
  `4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941`.
  Reuses `evidence`, fixed TRAIN_SKINS, PERCEPTION_TASK and CASES only. Does
  NOT call `expected`, `make_row`, `build_dataset` or `score_row`.
- Frozen corpus:
  `organism_v6/birth_skill_corpus.py`, SHA256
  `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`.
  Reuses `assess_source`, `_identify` and `_interface`.
- Public parser/judge:
  `organism_v6/rulegame_parenting_diagnostic.py`, SHA256
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
  The corpus's existing AST loader extracts `parse_action`, `decode`,
  `judge_record` and their public dependencies without importing the native
  runner. Selected interface hash:
  `82b894ae9f226e739cc23ef9fa0ccd0106cc7ad1e04cd8fb86202d5656a7ccb6`.
  `judge_record` definition hash:
  `39b395a562ed4131886cedb777fd9bc612eff24ca653f890802cd95b60571945`.
- The material's reflection-reference source pin is also preserved:
  `organism_v6/birth_reflection_probe.py`, SHA256
  `b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80`;
  its generator/model code is not invoked.

Here “strict source judge” means the existing production parser's exact keys,
types, triple, supplied outcome, actual explicit/absent prior and relation,
plus an added stop-completion requirement. It is NOT canonical serialization
equality: the existing parser accepts JSON whitespace/key-order variation.
It rejects fences, surrounding prose, repaired keys/types, invented priors,
wrong actions/outcomes and ambiguous source predictions. The material's
more-permissive authored-screen scorer is intentionally not the admission
gate. No author-screen abstention is admitted as a production record.

## Source/parent binding and held exclusion

Default frozen local source root:
`/tmp/astra_level1_real_record_source_20260913_attempt1`.
All relevant files are hash-checked; no environment or old-module globals
are monkeypatched. Original native source root remains recorded separately
in provenance; the read-only local frozen copy has the same semantic bytes.

Default preserved archive:
`/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar`
SHA256 `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a`.
Only original plan/material and adapter artifact members are used; no OFF/
post held/canary response or score artifacts are read for selection/admission.
The archive is read, not extracted. Canonical material SHA256:
`48c52b25ceb3edb719d2e5f958b63c58301fee90dd9df27277f54cabdc2b9cdb`.

Original plan SHA256 by seed:

```text
0 3f4fd56868d2c42fe776c72ad4c5c93b15284ad16cd87c06849ba50419f67900
1 563d6799cd4b4030844f9dc037b931856132771e8e66e005b139e3f9dae96b47
2 bd4c5c4ec37da0a3e6611d430441d786beee2f338200f64ff64d2c40a8875910
```

Original parent adapter weight SHA256 by seed:

```text
0 8bfe8b9d647b58b064733ed24d8aaa97cd79d7012795232305838a23ac415432
1 c9700a2f46b36e64ce9e1845cd4601d3d0da086afbaba9efbc93012af936e0e2
2 5d198acfc7bf2f2c552b6b180688bce5d7fe00b1afd2eea7d056fc44a2e505da
```

The producer binding includes the full archived adapter file inventory,
original adapter path, model path/file-hash inventory, original plan hash and
learner seed. Adapter bytes are hashed read-only, never loaded as a model.
Base weight hashes are preserved from the pinned original plan, not
independently rehashed live on this CPU host. Parent fit must be the original
320step plan/config, not a memory WRITE descendant.

The canonical material file contains authored answers, but `observation_row`
copies ONLY row_id/input_messages/source. Neither expected/answer/raw_target,
target_sha256 nor source_proof drives prompt selection or positive targets.
Held48/canary12 metadata is read only for exclusion; held/canary answers are
not used. All partitions must have unique row IDs, source IDs and prompt
hashes; selected TRAIN/held triples must also be disjoint. Literal source
split and TRAIN skin are enforced. Requests cannot be swapped to held sources
or have teacher text appended without breaking the fixed rebuild check.

## CPU tests and limitations

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_own_source_replay_core_20260913.py' -v
```

**18 tests PASS,6.028s.** Includes three-parent pins/shared source selection,
factorial/counterexample balance, deterministic original prompt bytes,
held/canary/cross-split exclusion, poisoned authored-target/proof fields not
used, no-host-target behavior with missing responses, scripted raw-byte
preservation, unchanged production parsing, fences/prose/bool-int errors,
wrong outcome/prior/action, absent-prior invention, non-stop completion,
wrong producer/prompt binding, duplicate/no-best-of rejection, source/archive
pin failure, tampered bundle/descendant rejection, and no generator/scorer/
native calls. Scripted responses in tests are explicitly CPU fixtures, not
claims that any original learner generated them.

This is a reusable candidate-source core, not a trainer, native identity
attestation, general custody framework or formal C11 guard. Observation
contexts are externally authored and already in original parent training.
Own-output admission may test reading or rote recall of supplied evidence;
it is not new autonomous TRY experience, spontaneous learning, hidden-thought
truth, successful internalization, retention repair or H1/H2 evidence.
Selecting only supported sources limits any abstention/uncertainty claim.
Keep recipient choice, mixing ratios, replay/control dose, native sampling,
retention evaluation and fit/no-fit decisions outside this core.

**EDITSTOP — core and selection fixed; no actual replay responses collected.**
