# Exploratory formation replication seeds — frozen handoff

2026-09-12 09:30 UTC. Completed **seed-only fallback** authorized by main.
No matched-sham implementation, new guard machinery, autoqueue or launch.
No production artifact reads, Git, network, remote or GPU actions were performed.
Current immutable P0 deployed sources/runs were not touched.

## Feasibility decision before implementation

The canonical teacher bytes are constructed in `preschool_reasoning.lesson_block`.
`lesson_receipt` binds those exact bytes and their policy source hash;
`deliver_lesson` persists the canonical receipt and teacher ledger influence.
`_lesson_rows` requires full equality with that canonical receipt, and both
formation `summarize` and analysis call it. Substituting another sham text would
therefore require changing the unowned policy or adding a parallel receipt and
teacher-validation path. That is beyond this bounded seed-only implementation.

No teacher-variant argument is exposed. Config rejects an unknown
`teacher_variant="matched_sham"`; there is no silent fallback to the old teacher.
The original exact lesson/sham teacher bytes, full-byte receipts, actual tokenizer
counting and source judge remain unchanged. The original whole-prompt-package
203-versus-158 teacher-token confound reported by main remains explicit; it was
not remeasured here or converted into a token-matched assertion. No proxy count,
generated padding, outcomes-dependent text, teacher answer access or new teacher
artifact was introduced.

## Six owned files — frozen for main review

| File | SHA256 |
|---|---|
| `organism_v6/parent_material_diagnostic.py` | `325cc3f4554ea4fc32d40f5165a47045efd4f3c0d4553d5464693596ca669fea` |
| `organism_v6/parent_material_write.py` | `e39201fcd2dd165ee9bfd22797c959f35c8ce0ea26657e1274775baf9b2299bd` |
| `organism_v6/parent_material_analysis.py` | `6e3e84aea32a65247d77c08d0e5699e4b1be77ecaccf24fb945ec89f6e5ae096` |
| `tests/test_parent_material_diagnostic.py` | `2f0d0be39a44e9098fba6161efeb011597306cc032d22e48ee4e99b8ba949e42` |
| `tests/test_parent_material_write.py` | `27d75353614dfabe18f83971e2bef8338d7677780931a46f4347dce940119a40` |
| `tests/test_parent_material_analysis.py` | `a8dbf821cc0cd4f63480cba5476dab9659c75e545a80c44ee5b1ed3e03788180` |

No policy, pipeline, backend, other tests or frozen source checkout was edited.
Main owns Git/review/deployment and any subsequent real experiment decision.

## Interface and behavior

`parent_material_diagnostic.Config` adds only:

```python
schedule_seed: int = 6101
generation_seed: int = 7101
```

Both require true Python/JSON integers in `[0, 2147483647]`; booleans, floats,
strings, nulls, negative values and overflow reject before input reads/backend
creation. The pure `protocol(schedule_seed=6101, generation_seed=7101)` returns
the existing fixed SCHEDULE with only these two seeds replaced; SCHEDULE itself
and all other protocol parameters remain unchanged.

- Schedule: actual `gym.training_schedule(64, config.schedule_seed)`; existing
  training-only split checks remain in force.
- Generation: actual `run_episodes_batch(..., gen_seed=config.generation_seed)`
  for every batch. Existing wake and NOTE_AFTER seed derivation is untouched.
- `config.json` records both fields and the corresponding effective protocol.
- Writer validates effective protocol and actual schedule using the recorded
  seeds. Omitted fields mean the old defaults only. `write_prep.json` and
  `formation_inputs.json` now expose `formation_seeds` as factual metadata.
- Writer schedule remains rank8 / epochs3 / LR1e-4 / seed6102 and first64 selected
  records; this task does not parameterize training or probe seeds.
- Analysis requires matched effective paired protocols/schedules. It accepts
  omitted-default versus explicit-default schemas with identical effective
  protocols, but rejects different generation seeds or schedules. Reports expose
  `formation_seeds` and bind both the inference label and bootstrap scope to the
  actual generation seed rather than always claiming 7101. The analysis bootstrap
  seed is independent of the formation seeds and retains its existing default.

## Default compatibility and original-source custody

CPU regression confirms omitted versus explicit `6101/7101` produce byte-equal
`schedule.json`, `lesson_deliveries.jsonl` and `teaching_dose.json`; the recorded
request seeds/prompts and generated texts also match exactly. The default protocol
equals the preexisting SCHEDULE. New config/report fields and changed source hashes
are expected metadata differences. Random occurrence identities/timestamps are
not claimed byte-identical across distinct runs.

Changing only generation_seed preserves the exact episode schedule and changes
the actual request seeds. Changing schedule_seed affects only the declared
training schedule selection and the existing seeds derived from episode IDs.

No producer comparison was relaxed. Missing/changed original sources and different
executing producer bytes still fail, as tested by the existing relocation/drift
regressions. Legacy-schema tests are clearly synthetic: they remove optional
fields from newly generated CPU fixtures, not relabel historical runs.

Use the old frozen producer/helper checkout for current P0. For a new replication,
deploy a matching new source checkout and use it for formation/preparation/analysis.
Identical new producer bytes can still relocate under the existing helper rules;
these new bytes cannot masquerade as the old deployed producer. Pipeline was not
edited: for a future pair, main must supply the same explicit generation seed to
both arm configs. Analysis enforces that pairing; this task adds no new pipeline
pair-checking machinery.

## Prospective CLI example — not executed or queued

The existing JSON config interface is unchanged. Keep actual `out`, `mode`,
`model_path` and locally measured `expected_files`, adding for example:

```json
{"schedule_seed": 6101, "generation_seed": 7201}
```

Use identical seed fields in the future lesson/sham configs. This example varies
generation randomness while retaining the previous schedule; it is not a chosen
experiment or an assertion that first-pair evidence warrants replication.

```bash
V6_MODEL="$LOCAL_MODEL" CUDA_VISIBLE_DEVICES="$RESERVED_GPU" \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_material_diagnostic \
  --config "$NEW_ARM_CONFIG" --execute

CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  "$PY" -B -m organism_v6.parent_material_analysis \
  --lesson-root "$NEW_LESSON_OUT" --sham-root "$NEW_SHAM_OUT" \
  --out "$NEW_ANALYSIS_OUT"
```

Existing writer/pipeline CLI needs no new flags: it reads formation seeds from
the source config. Existing explicit execution, reservations, local pins and
fresh-output requirements still apply. Commands here are documentation only.

## CPU tests and results

Final combined command (pipeline tests read-only):

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 PYTHONPATH=tests:. python3 -B -m unittest \
  test_parent_material_diagnostic test_parent_material_write \
  test_parent_material_analysis test_parent_material_pipeline -v
```

**88 tests passed in 91.829s.**
Log: `/tmp/astra_parent_replication_parameterization_combined.log`.

Two focused execution-seed/default-equivalence regressions also passed in 0.944s;
log `/tmp/astra_parent_replication_seed_focused.log`. An earlier new-test assertion
incorrectly used tick 0 for first wake generation; inspection confirmed existing
`prompt()` advances to tick 1, and only that test expectation was corrected.
No generation behavior changed to satisfy the test.

New coverage includes default equivalence, generation-only schedule stability,
actual configured request seeds, changed training schedule, seed validation,
config CLI parsing, unsupported teacher variant, writer seed propagation without
changing trainer seed, legacy omitted defaults, config/protocol inconsistency,
actual schedule mismatch, paired generation/schedule mismatch, and dynamic
analysis inference versus independent bootstrap seed.

Combined coverage retains real source-join/evaluator CPU fixtures, rejected
teacher targets, strict producer drift rejection, fresh-checkout relocation,
pipeline skips and owned-process timeout cleanup. All model/tokenizer fixtures
are synthetic CPU doubles; no real tokenizer/model/GPU execution is claimed.
The preexisting bootstrap ResourceWarning remains untouched.

## Scope conclusion

Ready for review/freeze. Only independent seed configuration is delivered.
Matched-dose control is not implemented, teacher dose remains confounded, and
there is no writer qualification/H1 promotion or next-run authorization implied.
No additional edits or queued work planned without main's next assignment.
