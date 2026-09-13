# EDITSTOP — prediction / goal-completion authored Level1 material

Date: 2026-09-13. Scope: only the two Python files and this handoff in `/tmp`.
No repository/shared files, Git, network, native runners, GPU jobs, or live roots changed.

## Final candidate files — Main owns freeze

- `/tmp/astra_level1_prediction_goal_material_20260913.py`
  SHA256 `3da282322f65525271a48b628b30ecdc8a2fba6ba6ba84d8cf1f3e65ad6d6433`
- `/tmp/test_astra_level1_prediction_goal_material_20260913.py`
  SHA256 `23a7776078dba1b02500ecb96e16de8b58dd9350a34d2c454711673d51e668b6`
- `/tmp/astra_level1_prediction_goal_handoff_20260913.md`
  Its SHA256 is in the delivery response; not self-embedded.

## Intake and interpretation

Read the repository AGENTS contract, latest raw message 34 at
`research_notes/THESIS_RAW_ROHIN_2026-09-11.md:337`, and the
2026-09-13T07:16Z steer at `research_loop/COORDINATION.md:9948`.
Read `organism_v6/birth_skill_corpus.py`, the thesis, birth component notes,
the public belief-card PROSPECT protocol, and curriculum readings 01 and 11.
The dataset provenance lists these references. No architecture or native
grammar changes are proposed by this standalone material.

Scoring revision: read Rohin's full raw message 35 (~07:25 UTC), at
`research_notes/THESIS_RAW_ROHIN_2026-09-11.md:343`, including the supplied
context identifying his approval of all five suggestions. The fourth is
permissive-parse-then-format/content scoring. Applied only to this unfrozen,
future-Level1 candidate per the explicit follow-up instruction; no existing
run or native interface is changed. Main owns the final freeze.

Rohin asks for granular Level1 prediction and goal end/start, individually
tested: useful pieces that may eventually support receptivity to parenting,
not a claim that the teaching flywheel already works. This implementation
narrows prediction to prospective consequences justified by public task facts,
and goal end/start to complete versus continue given a stated goal and public
verification. It does not invent a separate hidden-rule benchmark.

The follow-up directive is applied: **96 DISTINCT sourced situations per
skill, 24 per each of four fixed skins; 48 distinct held situations, 12 per
skin; 12 separate canaries.** There is no four-skin multiplication of a
24-source training set. Each situation appears once. Every primary queried
action is unique between situations, and train/held action ranges are disjoint.

## Stable API and use

```python
import astra_level1_prediction_goal_material_20260913 as material

prediction = material.build_dataset("prediction", seed=0)
goals = material.build_dataset("goal_completion", seed=0)
row = prediction["evaluation"]["held"][0]
result = material.score_row(row, row["raw_target"], "stop")
```

The module is stdlib-only and directly importable from `/tmp`. CLI example:
`python3 /tmp/astra_level1_prediction_goal_material_20260913.py prediction --seed 0`
prints one complete JSON dataset to stdout; it creates no files.

`SKILLS = ("prediction", "goal_completion")`. The top-level dataset has
`schema`, `qualification`, `provenance`, `training`, and
`evaluation: {held, canary}`. Every row has exactly the requested core fields:
`row_id`, `input_messages`, `raw_target`, `target_sha256`, `source`,
`source_proof`. Qualification is
`AUTHOR_LEVEL1_SCREEN_ONLY_NOT_CHILD_SLEEP_NOT_H1_NOT_P1`.

Targets and source/public-fact digests use SHA256. Inputs contain only the
public task evidence, fixed classroom skin, and response contract: no source
IDs, case classes, proofs, split names, or row-specific target metadata.
Source proofs identify the selected belief-card support or goal/observation
paths. Row-integrity checks reconstruct the target, proof, and visible prompt.

Seed affects deterministic SHA256-based ordering only, never cases or labels.
Construction uses fixed factorial enumeration, no model calls or output-based
selection. Repeated calls return independent mutable data.

## Observable behavior and coverage

Prediction:

- Before executing the selected TRY, use a supplied local public belief card
  to predict its consequence, not an earlier prediction or another action's
  observed result.
- Explicitly abstain for absent evidence or unresolved conflicting entries.
- Train targets: 32 true / 32 false / 32 abstentions; held: 16 / 16 / 16.
  Abstentions split equally between missing and conflicting evidence.
- Within every skin, both prior-prediction values and both earlier-outcome
  values are crossed with all three targets. Neither earlier outcome nor
  prior prediction, even jointly with skin, determines the answer.
- Canonical supported example:
  `{"decision":"predict","prediction":true,"reason":"public_evidence"}`.
  Abstention:
  `{"decision":"abstain","prediction":null,"reason":"insufficient_evidence"}`.

Goal completion:

- End only if every stated requirement has current public evidence for the
  exact required action/outcome; otherwise continue. Do not substitute a
  different action's success, a learner's completion claim, partial completion,
  a contrary result, or unresolved conflicting observations.
- Cases include a single requirement, two/three requirements, missing selected
  verification, and both truthful and false self-reports. Profiles also vary
  distractor count/order and consistent/conflicting repeated observations.
- Train: 48 complete / 48 continue; held: 24 / 24. Both desired Boolean values
  are balanced. Every skin × desired-value × earlier-value × case stratum
  contains equal complete/continue counts.
- Canonical outputs:
  `{"decision":"complete","goal_complete":true}` or
  `{"decision":"continue","goal_complete":false}`.

Canaries: six signed-integer additions and six exact-copy tasks per skill,
evaluation-only. The same twelve canaries are intentionally reused between
skills, with matching source/group IDs: they are twelve controls, not twenty-four
independent controls. No canaries are included in skill training.

## Ancestry and independence limits

Every row exposes `source.situation_id`, `source.source_group_id`, and
`source.parent_source_ids` (empty: no row is derived from a previous row).
Prediction has 32 authored sibling groups in train and 16 in held, each with
three distinct true/false/unknown fact situations. Goal completion has 24
groups in train and 12 in held, each with four distinct action/state profiles.
Shared group membership discloses common authored construction, not a hidden
claim of 96 independent causal mechanisms. Held uses disjoint source facts
and action tuples but shares the four skins and authored task families.

## Scorer

Scoring version: `typed_content_and_format_v2_raw35`.

**`passed == content_correct` is the new primary pass.** It requires an exact
typed match to the declared fixture target, intact source/target/prompt proofs,
and `finish_reason == "stop"`. Parsing tolerates JSON whitespace/key order and
one enclosing multiline plain or lowercase `json` code fence, with optional
outer JSON whitespace. No surrounding prose, multiple fences, partial output,
duplicate keys, nonfinite values, or key/type/value repair is accepted. JSON
integers/floats cannot stand in for Booleans, nor Booleans for canary integers.

`strict` requires that same content pass PLUS exact original canonical target
bytes. A complete correct object with `finish_reason="length"` fails BOTH
passes; a valid fence or noncanonical JSON can pass content but never strict.

`format` classifies serialization independently of value agreement and finish:

- `exact`: raw bytes equal the canonical compact/sorted serialization of the
  parsed value. A wrong answer can still have exact format.
- `json_noncanonical`: valid bare JSON with noncanonical whitespace/key order.
- `fenced`: valid JSON inside exactly one supported enclosing fence.
- `unparseable`: malformed/duplicate/nonfinite JSON, unsupported fences,
  surrounding prose, or nontext input.

`errors` contains content-blocking failures; successful tolerant parsing has
`errors=[]`. `strict_errors` adds `not_exact_canonical_format` when appropriate.
Additional outputs are `raw` (untouched input), `parsed`, `finish_reason`,
`score_kind`, and `scoring_version`. The misleading old `semantic_correct`
diagnostic is removed. **Content agreement is not semantic reasoning
correctness; prediction's `reason` field is a declared fixture label.**

No training/held/canary row, source, prompt, target, or ancestry changed for
raw35. Only scoring and top-level provenance changed. Seed-zero rowset digests
were captured before editing and are pinned in regression tests:

- prediction: `aa8544ddc17fe8e4f04af70c31587934c167c2bc4063ac5c861f886d981fea3b`
- goal_completion: `e0198ba31097b97b2ecaf21c6bdc27334ec73ced9e67d4c59469978bbf4e6441`

## Test receipt

Raw35 candidate, one suite invocation after the scorer/test edit:

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_astra_level1_prediction_goal_material_20260913`

Working directory `/tmp`: **9 tests passed, 0.205 seconds**. Coverage: distinct
96/48 fact situations and split disjointness; one skin per situation and 24/12
per-skin budgets; ancestry fields; independent fact-to-target calculations;
balance/shortcut counterexamples; repeatability and seed-only ordering; prompt
metadata exclusion; canary separation; strict/error and integrity handling;
plain/json fences, outer whitespace, reordered keys, independent format
classification, truncation failure for both passes, bool/int separation,
malformed/extra-prose rejection, reason-label mismatch, raw preservation, and
the unchanged pre-edit rowset hashes. No model outputs were used for tuning.
For transparency, earlier pre-raw35 candidates passed six tests each, once
before and once after the user clarified distinct-source counts. This raw35
revision was tested once; Main will perform the final freeze.

## Recipe and scientific boundary

Lovelace/Main own recipe and native integration; neither is implemented here.
The reviewed SEQ113 recipe is warm80 + 320 parents with mixed two-memory /
two-arithmetic batches. A fresh 320-skill fit is **recipe-inspired, not faithful
replication**. Do not train on these evaluation canaries to simulate that replay.

This is PURE authored Level1 material, not child SLEEP or engine-verified life
experience. The local belief card supplies the rule: prediction success is not
hidden-rule induction or probability calibration. Goal judgment is not autonomous
goal creation, planning, action execution, or demonstrated recovery. Explicit
abstention belongs only to this screen and does not change the native no-abstention
play invariant. No native baseline, model learning, general preservation,
withdrawal persistence, transfer, H1/P1 qualification, or Level2 success is claimed.
Main should preserve raw model outputs and compare baseline versus trained
held/canary scores separately; data/scorer success is not evidence of learning.

EDITSTOP: no edits outside these three files; no further execution requested.
