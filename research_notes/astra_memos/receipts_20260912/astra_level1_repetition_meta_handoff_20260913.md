# Repetition / meta-reflection — authored visible decision screens

2026-09-13. Scope: this handoff and matching material/tests in `/tmp` only.
Main can launch existing skills independently; this task does not change them.

## Project definitions read before implementation

- Rohin raw34/raw35, `research_notes/THESIS_RAW_ROHIN_2026-09-11.md:337`
  and `:343`: granular individual Level1 skills and separate content/format scoring.
- `organism_v6/curriculum/05_replay_what_matters.md`: spend limited review
  time on surprising, important/rewarded, task-relevant evidence; not uniform replay.
- `organism_v6/curriculum/07_scope_your_memories.md`: rereading an episode
  does not create independent evidence or increase its support count.
- `organism_v6/curriculum/11_mind_the_clock_judge_yourself.md`: inspect
  progress per effort, recognize stuck repetition, judge using recorded
  evidence rather than mood, and change the approach when warranted.
- `organism_v6/PARENTING_MENU.md`: concrete self-review, spaced repetition,
  interleaving and application rather than only restating a lesson.
- `research_notes/00_THESIS.md`: bounded experience selection and consolidation;
  this screen does not measure the actual consolidation mechanism.

## Smallest exact public decision contract — recorded BEFORE code

The readings give usable qualitative definitions, not a complete scoring
algorithm for these two tasks. The following is an explicitly authored local
classroom policy, not a discovered law, new thesis claim, or native protocol.
The complete policy will be visible in every relevant prompt. Supplied
"verified" traces are authored public facts inside the vignette, not actual
engine executions or external verification of a learning gain.

Repetition: judge ONE nominated prior evidence record. First skip if its task
is outside the stated current goals. Then skip if its review cost exceeds the
remaining explicit budget. Otherwise rehearse if the current goal names its
task as important, or if its recorded prediction differs from its verified
outcome and no resolution is supplied. Otherwise skip as settled. Importance
takes precedence over unresolved evidence when both apply. A positive replay
count never independently warrants rehearsal, nor makes important unresolved
evidence worthless. Return `decision` (rehearse/skip), `reason` (irrelevant,
budget_exhausted, important, unresolved, settled), and
`independent_support_after`, equal to the public independent support count.
This counter denotes unchanged evidence support, not projected model memory.

Meta-reflection: select a bounded diagnostic label and NEXT learning action
from public strategy/assessment traces. Apply this public priority table:

1. No verified after trace: `insufficient_evidence` / `collect_verified_after_trace`.
2. Different before/after assessment identity or total: `incomparable_checks` /
   `rerun_matched_check`.
3. A practiced target differs from the supplied public correct target:
   `incorrect_practice_targets` / `correct_targets_then_retest`.
4. Same-assessment practiced-example score improves but new-example score
   does not: `practice_only_gain` / `vary_examples_and_test_new`.
5. A matched delayed check declines from its immediate check:
   `retention_loss` / `spaced_rehearsal_and_delayed_check`.
6. Otherwise no matched new-example score improvement despite repeating the
   strategy: `no_progress` / `switch_to_contrastive_practice`.
7. Other patterns: `insufficient_evidence` / `collect_verified_after_trace`.

The six source families exercise rules 1–6; rule 7 is a conservative fallback,
not a seventh balanced outcome family. Return exactly `diagnosis` and
`next_action`. These are declared policy labels, NOT causal proof that an
internal learning algorithm failed, nor truth about hidden thoughts/emotions.

## Implemented budget / independence / reuse

Each skill: 96 distinct training public-fact situations (24 per four fixed
skins), 48 distinct held situations (12 per skin), 12 arithmetic/copy canaries.
One rendering per source; disclose authored sibling group IDs and empty
parent-source lists. Held actions/record/assessment IDs and facts are disjoint;
the same local decision policy and skins intentionally generalize across splits.
Seeds change ordering only. No model-output tuning or native/GPU work.

Reuse the frozen prediction/goal hash, JSON, row packaging, deterministic
ordering and permissive-content/strict-format scoring patterns as local copied
infrastructure, with new source factories/oracles and distinct canary facts.
No runtime dependency on or change to the prediction/goal files. Preserve raw
responses; primary `passed == content_correct`; strict also demands canonical
bytes; both require `finish_reason="stop"` and intact source/target/prompt proofs.

## Scientific limits

These are authored visible decision screens, not actual repeated rehearsal,
improved adult learning, internalization, child SLEEP, hidden-thought truth,
emotions, H1/P1 qualification, or a demonstrated parent/child learning loop.
Handwritten policy compliance does not establish that the prescribed action
would improve a learner. A diagnostic label is a trace-pattern classification.
The repetition screen selects one record, not an optimal multi-record budget
allocation. No learned gain, retention, transfer or causal claim is made.

## API and implementation receipt

`SKILLS = ("repetition", "meta_reflection")`.
`build_dataset(skill, seed=0)` returns `schema`, `qualification`, `provenance`,
`training`, and `evaluation: {held, canary}`. Rows have `row_id`,
`input_messages`, `raw_target`, `target_sha256`, `source`, and `source_proof`.
The module is standalone stdlib-only; no repo imports or runtime dependency
on the prediction/goal module. Example from `/tmp`:

```python
import astra_level1_repetition_meta_material_20260913 as material
dataset = material.build_dataset("meta_reflection", seed=0)
row = dataset["evaluation"]["held"][0]
result = material.score_row(row, row["raw_target"], "stop")
```

CLI: `python3 /tmp/astra_level1_repetition_meta_material_20260913.py repetition --seed 0`
prints a complete JSON dataset without writing files.

Each skill has exactly 96 distinct training situations and 48 distinct held
situations, rendered once per source. Four fixed skins have 24/12 rows each.
The 16 training and 8 held authored sibling groups each cover six public
decision cases. Every primary public action is unique, and train/held source
facts/actions are disjoint. Opaque public record/assessment identifiers are
hash-derived rather than case labels. Proofs and source/group IDs stay outside
the prompt; the public decision contract and relevant facts stay inside it.

Repetition has 48 rehearse / 48 skip training decisions and 24 / 24 held.
Three rehearse cases: important settled evidence, unresolved prediction/outcome
disagreement, and important unresolved evidence. Three skip cases: repeated
irrelevant records, settled evidence (including explicitly resolved disagreement),
and relevant important evidence over budget. Repetition counts do not change
the action on their own; independent support stays unchanged. Within every
skin/outcome/earlier-outcome stratum present, rehearse and skip are balanced.

Meta-reflection has 16 training and 8 held rows for each of the six diagnosis /
action pairs. Every skin/earlier-outcome/correct-target stratum present includes
all six labels equally. Self-reports and the two repeated-strategy descriptions
vary across all cases and do not determine the diagnostic label. Missing and
noncomparable assessment cases are negative controls for unwarranted diagnosis.
This corpus has failed-strategy and uncertainty cases, not a balanced screen
for retaining successful strategies.

Each skill includes the same twelve new evaluation-only canaries: six integer
additions and six copy tasks. Those twelve are intentionally shared between
these two new skills, with the same source/group identifiers; do not count them
as twenty-four independent controls. All canary facts differ from prediction /
goal canaries. No canary enters training.

The JSON/hash, source/row packaging, duplicate-key/nonfinite rejection and
`score_row` functions were copied unchanged from the frozen prediction/goal
module. Regression tests compare their ASTs. New source factories, public
policies, target oracles and proofs are local to this module. Source enumeration
and SHA256 order selection use no model output, fitting, filtering or tuning.

## Scoring contract

Version `typed_content_and_format_v2_raw35`. **`passed == content_correct`** is
the primary. Both content and strict success require `finish_reason="stop"`
and intact source/target/proof/input integrity. `strict` additionally requires
the original exact compact canonical JSON target bytes.

Content tolerates JSON whitespace/key order and exactly one multiline plain or
lowercase `json` fence, with optional outer JSON whitespace. It never repairs
keys/types/values, discards prose, or accepts duplicate keys/nonfinite numbers.
An intact answer terminated by `length` fails both passes. Booleans cannot replace
integer support counts or canary answers. `reason`, `diagnosis` and `next_action`
are declared fixture labels, not scored free-form explanations.

`format` is independent of correctness: `exact`, `json_noncanonical`, `fenced`,
or `unparseable`. A wrong-valued answer may have exact format. `errors` contains
content failures; `strict_errors` additionally describes format failure. `raw`
is returned untouched; `parsed`, `finish_reason`, `score_kind` and
`scoring_version` are also returned. Do not label typed content agreement as
semantic reasoning correctness.

## Tests and EDITSTOP files

One invocation from `/tmp`:

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_astra_level1_repetition_meta_material_20260913`

**7 tests passed, 0.306 seconds.** Counts, distinct facts/actions/splits, skins,
groups, metadata exclusion, public target patterns, budget/support invariants,
negative controls, nuisance-value balance, independence from self-report,
exact/noncanonical/plain+JSON-fenced scoring, truncation, no repair, row
integrity, seed-only ordering, copied infrastructure AST equality, and frozen
prediction/goal preservation are covered. No model-output tuning occurred.

Final files, ready for Main's freeze:

- `/tmp/astra_level1_repetition_meta_material_20260913.py`
  SHA256 `498e841af8c65654b3f090a1c9f951b6d0aa0e040fd3d757d320f69cba007700`
- `/tmp/test_astra_level1_repetition_meta_material_20260913.py`
  SHA256 `d3ae8ec9e4f01e6bcc9f37bf9e538d4e132b33c8cb64253c0ff8251c1cd3e275`
- `/tmp/astra_level1_repetition_meta_handoff_20260913.md`
  SHA256 delivered separately, not self-embedded.

Previously frozen prediction/goal files remain unchanged:

- Material: `3da282322f65525271a48b628b30ecdc8a2fba6ba6ba84d8cf1f3e65ad6d6433`
- Tests: `23a7776078dba1b02500ecb96e16de8b58dd9350a34d2c454711673d51e668b6`
- Handoff: `a11cb3dc0e3c45a5e6ae63d4f98e6efd7df0d125ec723492616c0dd9b639cf6c`

EDITSTOP. Only these three new files were written. No Git, network, repository,
native/GPU, live-root, or existing-run changes. Main's existing four-skill
launch is independent; this handoff imposes no runtime gate. Recipe/native
integration remains Main's responsibility, and no recipe replication is claimed.
