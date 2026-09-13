# EDITSTOP — perception and source-diagnosis/procedure material

2026-09-13 UTC. Only new `/tmp` module, tests and this handoff were written.
No repository/Git/network/tokenizer/model/GPU or live-root operations; no real
model outputs were read or generated, including the completed contrastive
screen. Main retains the active roster and all native integration decisions.

## Final pins

- `/tmp/astra_level1_perception_reflection_material_20260913.py`
  SHA256 `4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941`.
- `/tmp/test_astra_level1_perception_reflection_material_20260913.py`
  SHA256 `1964706d6ac672aa2f78e871f5d16d7e32f9d7bb48972a1bd35ffa8ecdd2fad6`.
- `/tmp/astra_level1_perception_reflection_material_handoff_20260913.md`
  Hash supplied separately, not self-embedded.

Seed0 dataset bytes are canonical compact sorted-key UTF-8 JSON plus a final
newline. These hashes were measured in memory, not saved as launch datasets:

| Skill | Bytes | Full dataset SHA256 |
|---|---:|---|
| perception | 370491 | `69d5967ed2fc6f093978b6366c25565c61b1307fd840109d78974c71d21c1c2e` |
| self_reflection | 427371 | `dce0f954ad11964c7c1166a2207f0478675003f0fb78483bdf7cdbf350003442` |

Template/instruction/policy manifest SHA256:
`110f03dc3dae9620a0980706694d5dabc6f87b4affa32b5ecd260f7256bad072`.
Canonical `{training:...,evaluation:...}` row-content SHA256:
perception `274bcd7069feddf45a677d0e1e91dfabb800ce14ecafa0819b55a4030c7be58e`;
self_reflection `8b88d15762cf8e1273bdc4a7f70760661cc6bf11b6ccdca737426268862e8b96`.

Untouched earlier modules were rehashed only for custody, not run or scored:
discrimination remains `cfc2839f11e710b9de513efc465e3d2b895cfd067d7c8146bba97121bf4ad2fb`;
contrastive material remains `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`.

## Directive and source recovery

Read Rohin raw36 at `research_notes/THESIS_RAW_ROHIN_2026-09-11.md:349`:
the near-term criterion is raw experiential data containing what training needs,
not a working recursive/closed loop. Also read the source corpus,
`organism_v6/birth_reflection_probe.py`, the historical birth-reflection handoff,
reflection three-seed analysis handoff (limitations/method sections), birth-skill
corpus review, and Level1 arsenal note. No new-corpus choices were selected from
native outcomes. Historical free-prose fixture matching is not mental truth or
semantic reflection scoring; historical application choices motivate a narrow
source/procedure screen, not a claim of full self-reflection.

Three source files are required and whole-file checked before helper execution:

- `organism_v6/birth_skill_corpus.py`:
  `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`.
- `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.
- **Additional fresh-snapshot dependency:** `organism_v6/birth_reflection_probe.py`:
  `b69dfe4ab39e60fab826e67758d21e708c87d538f3fcd2b8a579bb778b0ace80`.

The corpus is stdlib-only. Its AST-selected public parser/record interface is
reused without importing a native runner. Reflection source is AST-read only
for PROCEDURES and its authored application/distractor triples; it is not
imported. Reference procedures are recorded verbatim in provenance; the new
learning-procedure labels and insufficient-evidence cases are explicitly
authored extensions, not historical targets or hidden-world facts.

Main's read-only-inspected runtime has the correct dataset/scoring API. Its
minimum SOURCE_NAMES does not list birth_reflection_probe.py, so **include the
third file in the new source tree and complete source_files manifest**. Do not
add it to or reopen an existing frozen snapshot. The runtime's subset check
allows extra explicitly pinned files; no runtime edit was made here.

## API and new-directory CLI

```python
dataset = material.build_dataset("perception", seed=0)
dataset = material.build_dataset("self_reflection", seed=0)
score = material.score_row(row, raw, finish_reason)
```

Exactly the final Level1 top-level API: schema, qualification, provenance,
training, evaluation; evaluation contains held and canary. Each row has row_id,
skill, input_messages, raw_target, target_sha256, source and source_proof.
Source proofs bind the source identity, exact selected event, parsed fields,
diagnosis and input-message hash. Targets are recomputed from source when scored;
stale source/target/proof/input data raises an integrity error, not model failure.

```sh
python3 -B /tmp/astra_level1_perception_reflection_material_20260913.py --skill perception --seed 0 --output /FRESH/perception.json
python3 -B /tmp/astra_level1_perception_reflection_material_20260913.py --skill self_reflection --seed 0 --output /FRESH/self_reflection.json
```

Output parent must exist; exclusive-create refuses overwrite and resolved paths
inside the default repository or selected source tree. Before import/run, set
`ASTRA_LEVEL1_SOURCE_ROOT=/FRESH/PINNED_SOURCE` if not using the default
`/data/home/rohing/dream-state`. Three-source relocation is CPU-tested. Paths do
not enter deterministic dataset bytes. Seed is a nonnegative32-bit integer
(bool/string/float/NaN/negative/out-of-range reject), default0; it changes row
ordering only, not data, targets, templates or case selection. Group by row_id.

## Source counts, balance and exposure

Each skill has96 DISTINCT training sources/selected triples,24 per four fixed
skins. Held has48 DISTINCT sources/selected triples,12 per four different fixed
skins. No24-source/four-rendering inflation. Every selected and earlier triple
is unique within that skill's train+held construction; train and held do not
share event triples, source identities or prompts. Old birth-corpus, reflection
application and distractor triples are excluded. Sources are independently
authored public situations, not executions of a hidden gym/rule.

Fixed source seed2026091336, domain-tagged SHA256 coordinates modulo2001-1000,
bounded1000-nonce duplicate rejection. Each skin crosses all six cases:

1. agreement;
2. contradicted prediction;
3. absent prior prediction;
4. ambiguous/conflicting prior predictions;
5. missing selected outcome;
6. outcome belonging to the earlier/different action.

Each case has16 training and8 held examples. For usable selected observations,
True/False and earlier-same/earlier-opposite form equal four-cell counts within
each case in both splits. Earlier is not an always-opposite distractor. Train
crosses all four combinations within each skin; held crosses them across its
four skins. Missing/foreign observations are not counted as known selected
observations. Case labels/proofs are evaluator metadata, not per-example prompt
answers. All output vocabulary/policy definitions are common task instructions.

Canaries are12 fresh evaluation-only tasks: six deterministic integer additions
and six exact copies. Identical across these two skill datasets, so shared
preservation controls, not independent replicas. No dataset/model outputs are
used in construction. No recipe, optimizer, model or compiler is embedded.

## Compiler-facing perception and bounded reflection

For supported evidence, perception emits ONLY the actual record fields
`try` (selected integer triple), `observed` (Boolean), `predicted` (Boolean/null),
and `relation` (matched/mismatched/unavailable). Public parser/strict record-judge
tests verify these targets. No-prior-prediction is a VALID record with null and
unavailable; an outcome must not be converted into an invented prior belief.

There are48 supported records and48 screen abstentions in TRAIN,24+24 in held.
Supported relations are balanced16 each in TRAIN,8 each in held. Unsupported
evidence emits `{"abstain":true,"reason":...}` for ambiguous_prediction,
missing_outcome, or outcome_action_mismatch. **This is an explicit author-screen
alternative, not new production grammar and not a compiler record.** Do not
feed abstention labels to a record compiler as though they were child events.
The three insufficiency types are equally represented, not positive-only data.

`self_reflection` is transparently a **structured source-diagnosis and warranted
procedure-choice proxy**, NOT full reflection, spontaneous introspection, exact
reference prose, or free-text mental truth. Output has diagnosis, next_action,
and evidence (try/observed/predicted). Under the declared authored policy:
agreement selects recording agreement then a new test; contradiction selects
preserving the observation then retesting the prediction; absence selects
leaving prior null then predicting before the next TRY. Ambiguity selects
withholding the record and using one prior prediction; missing/foreign outcome
selects obtaining the selected/action-matched outcome before recording.

These are conservative authored procedure recommendations, not unique truths
about every possible learning policy. Choosing a procedure does not execute it,
measure its consequences, establish persistent learning, or diagnose a hidden
rule. Missing/foreign observations stay null in reflection evidence; ambiguous
prior prediction stays null with an explicit ambiguity diagnosis. No SLEEP
targets are rewritten; none of this material is child-authored experience.

## Content/format scoring and raw36 diagnostic boundary

`passed == content_correct` is primary; `strict` is correct canonical raw bytes;
`strict_pass` aliases strict. All are bool. `format` is exact/json_noncanonical/
fenced/unparseable. Raw text/hash, finish reason, syntax/schema/source/completion
errors and typed field correctness are retained. Reflection fields include
paths such as evidence.try and evidence.predicted. A valid but wrong output
variant (record versus abstention) is a source error, not a formatting error.

Content parsing allows JSON whitespace/key order and one sole enclosing bare or
lowercase-json Markdown fence. No surrounding prose, JSON substring extraction,
duplicate keys, extra fields, nonfinite values, or key/type/value repair.
Integer triples reject bools/floats; nullable Booleans are not coercions. Both
content and strict fail unless finish_reason is stop, even with a parseable
truncated answer. A canonical but source-wrong JSON may have format exact while
both correctness metrics fail. Arithmetic requires actual JSON integer type;
copy stays exact bare text, with no trimming/fence repair.

For Main's **later prospective field/admission wrapper**, compare base versus
each fitted state on actual raw experiential records: action/source joins,
observed correctness, prior availability/fidelity, relation, unsupported
abstention behavior, and actual production-record admission. Keep these apart:
permissive content success, canonical-byte success, and raw production grammar
eligibility. A correct fenced record can pass content but still be ineligible
as an unmodified production record; a noncanonical unfenced JSON can satisfy
the existing production parser. No fence stripping/teacher repairs into SLEEP.

That wrapper and model-output collection are NOT implemented here. No observed
admission rate, compiler success or skill improvement is claimed. Raw36's
criterion is potential usable training evidence versus base, not recursive,
self-recursive, or closed-loop learning. A syntax-only gain stays syntax-only.
Freeze future comparisons before new outputs; no selection using completed
contrastive outcomes. Main owns capacity, native recipe, masks, EOS/token-boundary
and no-truncation checks, actual context costs, fit/readout and interpretation.

## CPU validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p 'test_astra_level1_perception_reflection_material_20260913.py' -v
sha256sum /tmp/astra_level1_perception_reflection_material_20260913.py /tmp/test_astra_level1_perception_reflection_material_20260913.py /tmp/astra_level1_perception_reflection_material_handoff_20260913.md
```

20 tests PASS,8.460s on final module/test bytes. Coverage: exact API/source/skin/
case counts; determinism and order-only seeds; disjoint event triples and
excluded references; independent earlier/observation balance; actual record
grammar; absence versus conflicting prediction; source/procedure scope; no
per-example held label leakage; all authored targets; content/format/fences;
type/prose/duplicate/variant failures; truncation; selected-versus-earlier
counterfactuals; source/target/proof/prompt tampering; arithmetic/copy canaries;
exclusive CLI outputs and three-file relocation/reference-pin rejection.
Temporary CLI fixtures were removed automatically. All other dataset digest
measurements were in memory. EDITSTOP: only the three new paths handed to Main.
