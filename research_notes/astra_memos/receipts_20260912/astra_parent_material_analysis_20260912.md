# Paired CPU formation reducer handoff — 2026-09-12

## Status and scope

Builder-owned, non-material CPU analysis addition. Main must integrate and
freeze this reducer before using completed production outputs. No production
input or outcome was opened during development. The user's progress update
(40/64 by 09:14 UTC) is context, not an inspected result. No production job,
GPU, remote access, git mutation, training, eligibility decision, or new formal
C11 guard was introduced. The live producer and pipeline were not changed.

Only these files were authored:

- `organism_v6/parent_material_analysis.py`
- `tests/test_parent_material_analysis.py`
- `/tmp/astra_parent_material_analysis_20260912.md`

Read the watcher audit's **Immediate update: what the live 64-schedule pair can
decide**, `parent_material_diagnostic.summarize`, and
`parent_material_write._formation_snapshot` / `_select` before implementation.
The existing summarizer remains the authority for faithful/unique judgments.
The reducer does not call writer selection or create training inputs.

## Main's high-level interpretation

The question is whether this whole, longer lesson package yields more observed
strictly grounded child records than the shorter sham package, conditional on
this frozen learner and generation seed. It is not whether the learner learned,
made better task decisions, became eligible, or improved on H1.

The known live teacher doses are 203 versus 158 tokens (difference 45). Content
and dose are confounded. The report also checks and reports actual tokenizer
counts and exports exact teacher bytes; synthetic test doses are deliberately
different, not presented as live doses. No outcome/token division is performed.
A positive result supports only a whole-prompt-package formation difference;
a null is limited to this package, sample and seed. Neither is a training
outcome or evidence of durable learning, retention or parent deletion.

## Endpoints and accounting to freeze

- Every declared schedule is retained: exactly 64 ordered paired rows.
- Primary count: `strict_faithful_note_after`, matching the producer's
  `n_grounded_records` **before text deduplication**. Repeated faithful text is
  still an observed faithful formation, not a new unique record. This avoids
  making per-schedule formation depend on which schedule first emitted text.
- Each arm also has an explicit `any_strict_faithful_note_after` boolean. Each
  paired row includes count and any-grounded differences. The report gives
  lesson-only/sham-only/both/neither discordance, mean count difference and
  any-formation rate difference, with separate paired 95% percentile intervals.
- `unique_grounded_note_after` preserves the existing producer deduplication
  metric separately. Rejection tallies include `duplicate-grounded-record` as
  the producer does; therefore rejected-for-uniqueness and faithful are not
  disjoint. Unique counts do not assert successful writer/training outcomes.
- Bootstrap: local `random.Random`, seed 20260912, 10,000 replicates by default;
  jointly resample 64 schedule indices, not records/actions. Linear percentile
  interpolation at 2.5/97.5%. Explicitly exploratory and conditional on a single
  learner/generation seed, not independent learner replication.
- Missing schedules get zero **observed** counts and a missing-occurrence flag;
  this is not proof of biological failure. Missing notes, missing actual outputs,
  rejected records, ambiguous/unassignable generations, and out-of-schedule
  records remain in explicit accounting. No complete-case pair deletion.
- Arm totals equal all 64 schedule buckets plus `unassigned`. The totals and
  rejection reasons reconcile to the recomputed original summarizer. A teacher
  ledger row is naturally unassigned; that alone is not missing child evidence.

## Diagnostics, without invented subchecks

Requests/outputs join through recorded prompt hash, output hash and seed.
Per-schedule generation ownership uses actual ledger generation receipts, not
guessed episode IDs parsed from free-form prompts. Unjoinable generations remain
in arm totals and the unassigned bucket, with their request indices.

`valid_acts` means measured feedback, a unique execution, and the submitted ACT
in the actual wake output. It does not mean the action solved a task. Measured,
unmeasured and invalid-feedback counts and individual ACT diagnostics are kept.

NOTE_AFTER slot requests, returned outputs and nonempty responses are separate.
First-person form is a lexical observation using the existing policy regex, not
an assertion that the named action is faithful. Exact observed action, displayed
score and verdict come only from a matched authoritative ACT actually found in
wake output. `content_judgment` reuses `judge_record` rather than inferring later
subchecks from its short-circuit reason. Literal verdict presence is explicitly
lexical, not a second semantic judge. A faithful record need not explicitly
repeat the verdict. Unavailable diagnostics are JSON null, not false or pass.
Line bindings, raw-line hashes and actual child-text hashes support inspection.

Child output bytes, characters and retokenized output-text tokens are reported,
including separate slot token diagnostics. These are not runtime generated token
IDs (the producer did not save those). Child-visible tokens sum exact rendered
prompts, including repeated history, rather than claiming unique exposure.

## Existing helpers and old producer paths

The reducer calls the original `parent_material_write._formation_snapshot`.
That verifies completed manifests, result recomputation, canonical schedule,
fixed protocol, local base pins and original producer source hashes. Its existing
`_producer_sources` supports a verified relocated executing checkout with
byte-identical source files; recorded original source paths must remain readable
and unchanged. No new custody framework, copy/edit of source manifests, or
invented resolution of old producer paths was added. If those original paths
are unavailable, use the original unchanged helper checkout/environment rather
than rewriting evidence. Both input roots must retain canonical producer paths.

The same local model/config must be available to the snapshot helper and local
tokenizer loader. Hashing local weight files is streamed CPU I/O, **not** loading
weights for inference. It happens in the existing snapshot validation before
and after reduction. `AutoTokenizer` uses the helper's `local_files_only=True`.

Bounds: 64 paired schedules; 100–20,000 bootstrap replicates; unsigned 32-bit
bootstrap seed; at most 32 formation artifacts, 512 MiB per artifact, 1 GiB per
root, and 100,000 generation events per arm. Inputs and analysis source bytes
are checked again before writing. Fresh output must be disjoint from inputs
and model, have an existing parent and use a nonsymlink canonical path.

## CLI (Main only after integration/freeze and completion)

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.parent_material_analysis \
  --lesson-root /absolute/original/completed-lesson-root \
  --sham-root /absolute/original/completed-sham-root \
  --out /absolute/fresh/paired-report \
  --bootstrap-seed 20260912 --bootstrap-replicates 10000
```

The placeholder paths above were **not executed**. `--help` was checked without
reading inputs. The CLI prints only a compact paired summary, not child text.
Validation failure exits 2. Output contains `report.json`, `per_schedule.jsonl`,
`lesson_teacher.txt`, `sham_teacher.txt`, and `artifact_hashes.json`; teacher text
files preserve exact UTF-8 bytes without adding a newline. No input is modified.

## CPU validation

All fixtures use a synthetic CPU base, deterministic fake generation backend
and tokenizer. No production outcome inspection. The repository environment
has `python3` but neither `python` nor pytest, so use unittest directly:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s tests -p 'test_parent_material*.py' -q
```

The 76-test parent-material suite passed at 09:15 UTC before the final explicit
per-row binary fields were added; a final rerun is recorded below. Coverage
includes actual source judgments, duplicates, rejected/empty/no-first-person
records, missing note/schedule/output evidence, orphan attribution, ungrounded
ACTs, accounting conservation, token counts, seeded pairing, malformed protocol,
completion/dose/hash failures, immutable inputs, source drift during reduction,
fresh paths and CLI. An existing unclosed-bootstrap `ResourceWarning` arises in
`reasoning_gym_gym.py`; it is unrelated and was not changed. One initial test
setup needed to reopen its synthetic read-only directory to inject a fake
failure artifact; that fixture-only issue was fixed.

### Final receipt — 2026-09-12 09:17:38 UTC

Final full suite: **76 tests passed**, 87.612 seconds, including the explicit
per-schedule any-grounded booleans and paired binary differences.

- Reducer SHA-256: `45054c56f654fd79b5bdc333d0f7b2f49eed92fe4077d2d8d66c3f7b4458cda3`
- Tests SHA-256: `8731eb3efcb32e971cbee1a968427fa819ddbfd933e99f60a0b544e8d731a5b6`

Ready for Main to integrate/freeze. No completed production outputs have been
used, and no change to the frozen live pipeline is required by this handoff.
