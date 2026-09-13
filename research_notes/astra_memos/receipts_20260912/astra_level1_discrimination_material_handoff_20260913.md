# EDITSTOP — independent Level1 authored discrimination datasets

2026-09-13 UTC. CPU-only material and scorer; no native launch, tokenizer/model,
network/Git, repository changes, live-run operations, or writes to other owned
artifacts. Read Rohin raw message34 at
`research_notes/THESIS_RAW_ROHIN_2026-09-11.md:337`, the07:16 relay at
`research_loop/COORDINATION.md:9948`, `organism_v6/birth_skill_corpus.py`, the
birth-skill corpus review/handoff in `research_notes/astra_memos/receipts_20260912/`,
and `research_notes/analysis/2026-09-13_level1_arsenal_to_level2_closed_loop_release.md`.

Scoring-only revision follows Rohin raw35 at
`research_notes/THESIS_RAW_ROHIN_2026-09-11.md:343`: permissive parse followed by
separate content/format scoring. Applies only to these new Level1 materials.
Frozen contrastive material and its scorer were not edited.

## Owned files and final pins

Only these three paths were created/edited:

- `/tmp/astra_level1_discrimination_material_20260913.py`
  SHA256 `cfc2839f11e710b9de513efc465e3d2b895cfd067d7c8146bba97121bf4ad2fb`.
- `/tmp/test_astra_level1_discrimination_material_20260913.py`
  SHA256 `155d77869d479c6ffb3234a0f4375caf8e2ff239e11d2ab33cfc60b10dab29f0`.
- `/tmp/astra_level1_discrimination_material_handoff_20260913.md`
  Hash supplied separately rather than self-embedding.

Seed0 deterministic dataset pins (canonical compact sorted-key UTF-8 JSON plus
one newline, measured in memory; no persistent real dataset generated here):

| Skill | Bytes | SHA256 |
|---|---:|---|
| contradiction | 353056 | `0d001645a63efb06c55756e3c113c7fef903a88fd24ee49442ea56e7312abd29` |
| update_judgement | 426003 | `209969b910a33baed5ddccdeabab97c5014b77e03a00ae6027e309ad384f01bc` |

Only the embedded generator hash changes the full dataset bytes in this
scoring revision. All source, prompt, proof and target rows remain byte-identical.
SHA256 of canonical `{training:...,evaluation:...}` (with the same final newline):
contradiction `db9d807fb58cd9ac7dbaf437eb54bf4dd203ba0846dba023bf33cfcfbd7a9eab`;
update_judgement `4c48ce2df6b5bbbb3f04169e00e5dc4ab0fb99b4e4a96871a3543da026967dcf`.
Regression tests bind these pre-revision hashes. Repin future source/dataset
receipts; do not silently reopen or replace a frozen run's scoring source.

Shared complete template/instruction manifest SHA256:
`69bd5aa6b2159e1abc55923651884c27374fe734925eefaabf944207473dd275`.
Dataset provenance embeds generator hash, source pins, templates, parsed-interface
definition pins, seeds, selection, source counts, and claim boundaries. No
outcome-dependent selection or native recipe enters the generator.

## Stable API and CLI

```python
dataset = material.build_dataset("contradiction", seed=0)
dataset = material.build_dataset("update_judgement", seed=0)
result = material.score_row(row, raw, finish_reason)
```

`build_dataset` returns `schema`, `qualification`, `provenance`, `training`,
and `evaluation` with `held` and `canary`. Each row has `row_id`, `skill`,
`input_messages`, `raw_target`, `target_sha256`, `source`, `source_proof`.
The required seed is a nonnegative32-bit integer, default0; bool/string/float/
negative/NaN/out-of-range reject. **Seed changes order only**, never the source,
target, skins, case selection or canaries. Group by exact row_id, not label.

```sh
python3 -B /tmp/astra_level1_discrimination_material_20260913.py --skill contradiction --seed 0 --output /FRESH/contradiction.json
python3 -B /tmp/astra_level1_discrimination_material_20260913.py --skill update_judgement --seed 0 --output /FRESH/update_judgement.json
```

Parent directory must exist. Outputs are exclusive-create, no overwrite, no
resolved output inside the default repository or bound source tree. CLI is a
builder only; scoring is the requested Python API, not an aggregate framework.

Default source root is `/data/home/rohing/dream-state`. For a copied pinned tree,
set `ASTRA_LEVEL1_SOURCE_ROOT` **before importing/running** the module. This keeps
the exact API portable without monkeypatching. Copy both files below under its
`organism_v6/` directory. Every corpus load checks their whole-file bytes before
executing the stdlib-only corpus; its AST interface extracts public parser
functions, not native runner/model imports:

- `organism_v6/birth_skill_corpus.py`:
  `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`.
- `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`.

## Exact material semantics and counts

Each skill has **96 DISTINCT authored source situations**,96 distinct selected
triples and96 training rows:24 per each of four fixed training skins. These
are NOT24 sources replayed four ways. Held has48 distinct authored situations/
selected triples,12 per four different fixed held skins. All selected AND
earlier event triples are unique within the skill's train+held construction;
train and held sources, selected triples, raw selected events and prompts are
disjoint. Existing birth-corpus triples and its20,21,22 distractor are excluded.
Target class strings intentionally repeat across train/held; target-string
disjointness is not claimed or appropriate for classification.

Every row has two chronological public events, selects the final e1, and derives
its target only from exact event fields/availability (plus the judgement
candidate). Situation origin is explicitly authored, not hidden-gym truth.
Fresh independent situations may have unrelated outcomes; no hidden rule is
computed. Source seed2026091334, domain-tagged SHA256 and bounded1000-attempt
duplicate rejection determine triples. No replay ancestry is needed: only
public grammar is inherited. Source IDs hash complete source content; parsed
evidence, selected raw event and input hash bind source_proof.

Contradiction output is a NEW author-screen JSON object with exactly:
`event_id`, `verdict`, `reason`. Verdict is agree/disagree/insufficient.
TRAIN32 each, held16 each; every skin has all classes equally. The task compares
explicit prior prediction to the selected action-matched observed Boolean.
Insufficiency includes absent prior prediction, ambiguous/conflicting prediction,
missing outcome and foreign-action outcome. Their reasons are explicit targets,
not silently dropped rows. No prediction means insufficient to establish a
contradiction, even if a faithful observation record could still be written.

Update judgement is separate: a candidate four-field observation record is
supplied in context and the output is a NEW author-screen JSON object with
exactly `event_id`, `decision`, `reason`. Decisions admit/reject/abstain have
TRAIN32 each, held16 each, equal within every skin. With sufficient evidence,
admit exactly source-supported candidates and reject source mismatches using
the existing strict record judge. Every rejected candidate is internally
consistent: a correct relation relative to its own fields is not sufficient
for admission. Corruptions alter triple, observation, prediction, or both
prediction/observation while preserving internal relation consistency.
Insufficient evidence uses abstain: ambiguous prediction, missing outcome,
foreign-action outcome, or malformed outcome. Absence of prediction ALONE
does not require abstention: a correct predicted-null/relation-unavailable
candidate is admissible, preserving the existing source distinction.

This is candidate observation-record support, NOT general belief revision,
permission to update hidden rules, or a change to production admission grammar.
No author-screen outputs or notes may be inserted into child SLEEP. Child SLEEP
still uses exact child-authored bytes; no teacher rewrite is implemented.

Polarity is balanced. Where the selected observation is usable, earlier and
final outcomes agree half the time and disagree half the time within each
decision/verdict class; earlier is not an always-opposite clue. Both polarities
cross earlier agreement. A test flips only the selected observation and changes
agree->disagree / admit->reject, whereas flipping only earlier leaves the target
unchanged. Insufficient cases with absent/foreign outcomes are not falsely
counted as possessing a selected observation. All four insufficient subtypes
occur in both splits. This addresses the stated shortcut, not every possible
template shortcut or broad semantic generalization.

Canaries:12 simple tasks, six deterministic integer sums and six exact copies.
They are fresh, evaluation-only and identical across the two skill datasets
(shared controls, not independent replicas). Their source/proof fields support
deterministic arithmetic/copy scoring. No thoughts, feelings, free-text mental
states, or exact-match claims about inner experience are included.

## Scoring and Main's integration boundary

Lovelace/Main API contract: `passed == content_correct` is PRIMARY; `strict`
is SECONDARY canonical correct raw bytes, and `strict_pass` aliases `strict`.
All four fields are bool on every returned result. Raw text/hash, finish_reason,
completion/syntax/schema/source errors and per-field correctness remain present.
The current read-only-inspected `/tmp/astra_level1_skill_run_20260913.py` checks
these fields and aggregates content, strict and format counts. No runtime edit
was made here. Scoring signature is unchanged.

For author-screen JSON, parse ignores surrounding whitespace/key order and
optionally removes ONE sole enclosing Markdown fence with an empty or literal
lowercase `json` language marker. Fences require separate opening/closing lines;
surrounding whitespace is allowed, surrounding prose is not. The preserved
`raw` field is never changed. No extraction of a JSON substring from prose,
key/type/value repair, duplicate keys, nonfinite values, trailing commas,
additional fields or multiple fences. Valid typed fields and exact source-derived
values are required for content correctness. Fenced content may pass primary
while failing strict. JSON formatting changes do not alter supervised targets.

`format` is one of `exact`, `json_noncanonical`, `fenced`, `unparseable`.
For parseable JSON it describes serialization independently of correctness:
`exact` means raw equals canonical serialization of the parsed value (even if
that value is source-wrong), `json_noncanonical` means parseable but not those
canonical bytes, and `fenced` means the permitted sole wrapper was removed.
Failed parsing/nontext yields `unparseable`. Typed-schema/source failures still
receive their independent format classification. `strict` additionally requires
correct content, terminal stop, and exact equality to canonical raw_target.
For truncated outputs format may still be diagnosed, but content/strict are false.

Arithmetic canaries use the same permissive JSON surface but require type int
exactly: bool, float, quoted integer, null and list are rejected without
coercion. Exact-copy canaries intentionally remain exact bare-text tasks (not
JSON targets): neither whitespace trimming nor JSON/fence unwrapping repairs a
copied value. Their content and strict coincide; format is exact only for the
exact copy, otherwise unparseable. This preserves the existing copy-task meaning
without redesigning its target. Both canary types require terminal stop.

Only finish_reason `stop` is eligible. Map native length truncation to `length`,
failed calls to `error`, missing output to null/non-stop; all fail even if raw
text resembles a valid target. Main must use genuine terminal receipts, not
relabel truncated completions. Scorer recomputes expected fields from source;
stale source/target/proof/input hashes raise a provenance error, not a model
failure. Main's reducer should report these separately and fail the collection.

Use only `training` rows for fitting and only each row's `input_messages` as the
prompt. Never feed evaluator targets/proofs or the entire dataset manifest to
the model. Instruction vocabularies appear identically across classes; no
per-row derived verdict/reason or source-ID label is inserted into held prompts.
The judgement candidate is intentional task input, not trusted teacher truth.

Main owns native recipe, replay, data collation, comparisons and launch. Native
preparation still must verify exact assistant targets plus EOS, full context
masking, tokenizer boundaries, finite losses, no dropped/truncated examples,
and actual context/target token costs. These were NOT tested with a tokenizer.
No optimizer, LR, rank, update schedule, model or GPU code is in this material.

**Historical recipe distinction:** Main reports SEQ113 used warm80 then320
parent updates with batches containing2 memory +2 arithmetic items. The proposed
fresh320 skill fit (rank8/LR3e-4, replay where appropriate) is recipe-inspired,
NOT a faithful SEQ113 replication. No warm-start or batch-composition equivalence
is asserted. Keep this distinction in Main's actual fit/result receipts.

For an informative readout, compare OFF and fitted CONTENT-CORRECT held totals
primarily, strict canonical/raw totals secondarily, class-balanced totals,
each skin, reason subtype, format counts, schema versus source errors, and
each of12 canary regressions. There is no outcome-dependent pass
threshold here; Main should freeze its comparison before outputs. A syntax-only
gain is interface practice, not established contradiction/update competence.
Even source-field improvement is this authored Level1 screen, not general
G1/H1/H2, a closed-loop gain, a mechanism fix, or automatic release.

## CPU checks and final status

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s /tmp -p 'test_astra_level1_discrimination_material_20260913.py' -v
python3 -B /tmp/astra_level1_discrimination_material_20260913.py --help
sha256sum /tmp/astra_level1_discrimination_material_20260913.py /tmp/test_astra_level1_discrimination_material_20260913.py /tmp/astra_level1_discrimination_material_handoff_20260913.md
```

**22 tests PASS,7.459s** on the final source/test bytes: full target replay,
exact source/skin/class counts, deterministic bytes/seed-only ordering, disjoint
source situations, earlier/polarity balance, all negative subtypes, absent-vs-
ambiguous semantics, internally consistent rejected candidates, no per-example
label leakage, counterfactual selected/earlier dependence, schema/source errors,
truncation refusal, source/target/proof/prompt tampering, source-pin-before-exec,
copy/typed-arithmetic canaries, no recipe and CLI JSON/overwrite checks. Added
sole fenced/plain/reordered/whitespace JSON content-vs-strict tests, bool-vs-int
and float/string refusal, prose/malformed/multiple-fence rejection, both metrics
false on truncation, independent format classification, and frozen row hashes.
CLI fixture output was
only in an automatically removed test temporary directory. No real outputs or
outcome-driven tuning. EDITSTOP: all three files handed back to Main.
