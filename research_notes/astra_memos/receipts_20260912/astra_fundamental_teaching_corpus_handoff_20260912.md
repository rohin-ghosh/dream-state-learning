# Fundamental teaching corpus candidate handoff — 2026-09-12

## Scope and changed paths

Implemented only these repository paths (new files):
- `/data/home/rohing/dream-state/organism_v6/fundamental_teaching_corpus.py` — 204 lines.
- `/data/home/rohing/dream-state/tests/test_fundamental_teaching_corpus.py` — 232 lines.

No Git commands, network, GPU, model, tokenizer, fitting, sleep, or parented-life
execution. No other repository files edited. Main remains sole Git operator.
This is bounded CPU-only candidate construction for the supplied message15
proposal, not a scientific ruling or architecture/claim change.

Source SHA-256:
- Module: `9b63cea57c76f884efc671bb3639cc1013b55d5ba1e38986cc9d3178aad7f293`
- Tests: `3bd19ca84e1223fb0a2276b3ca18eb3ec2bbc9320a2662b729dc4267bf59a683`

## Preserved candidate artifacts

Emitted fresh directory: `/tmp/astra_fundamental_teaching_corpus_candidate_20260912`

Files: `manifest.json`, `train_teach.json`, `train_control.json`, `eval.json`,
`source_records.json`, `audit.json`, `README.md`. Manifest hashes all six other
files. Status is `CANDIDATE_CPU_ONLY`; native token status is
`NATIVE_TOKEN_MATCH_PENDING`.

Counts:
- Each training arm: 80 records = 64 addition cases + 16 device/color QA records.
- Evaluation: 112 records = 64 held-out addition + 32 recall paraphrases of the
  16 taught devices + 16 distinct untaught-device probes expecting `unknown`.
- 145 source events = 128 arithmetic + 16 arbitrary color assignments + 1 closed
  log inventory (the provenance for absence/unknown).
- 272 target derivations = 160 arm-specific training targets + 112 evaluation keys.
- Four colors, each assigned to four taught devices. Every target links to its
  generated sources, also embedded in audit JSON.

Seed 20260912 fixes pair selection, color assignments, and record ordering.
Arithmetic pairs use canonical left <= right, both operands in 0..19; train/eval
pair sets are disjoint even under reversal. Corresponding arm rows have identical
contexts, case IDs, sources, and semantic facts, with globally unique record IDs.
Teaching targets are `PREDICT: {sum}\nACT: {sum}`; controls are
`ACT: {sum}\nRESULT: {sum}`. Both are numerically truthful.

README contains a brief teaching/control protocol and an out-of-range 20+21
illustration, whose arithmetic derivation is separately recorded in the audit.
It is metadata only, never appended to training or evaluation contexts. Memory
facts are teacher-written QA targets; evaluation contains fresh bare questions,
not copies of source statements or teaching prompts. Unknown means absent from
the generated log, not a real-world claim.

## Validation

Passed all 11 focused tests:

`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p test_fundamental_teaching_corpus.py -v`

Coverage: arithmetic truth; fixed disjoint splits and unique IDs; equal arm facts
and target order; taught/untaught memory and fresh paraphrases; full provenance;
no evaluation teacher/prompt residue; raw-byte segment preservation; pending
native audit and truthful label variants; byte/hash determinism and global RNG
isolation; refusal of existing empty/nonempty directories, files and symlinks;
exclusive-write collisions with preservation; CLI determinism/refusal; narrow
standard-library-only implementation imports. Tests exercise only this module;
the CLI test launches a CPU Python subprocess, not a model or tokenizer.

The first attempt used `python`, which is unavailable here; rerunning with
`python3` passed. No broad repository tests were run.

CLI smoke emission succeeded:

`PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.fundamental_teaching_corpus --output /tmp/astra_fundamental_teaching_corpus_candidate_20260912`

That output now exists and MUST NOT be reused. Future invocations require a fresh
directory under an existing parent. Existing outputs are never overwritten;
partial failures remain for inspection, and the manifest is written last.

## Pure helpers and remaining limitations

- `build_candidate()` returns raw records, manifest, sources, and audit.
- `candidate_files()` returns deterministic encoded artifact bytes.
- `addition_context()`, `arithmetic_response()`, and `raw_segments()` provide
  pure low-level construction for Main's later native rendering audit.
- `raw_segments()` returns `(text, target_loss_flag)` pairs, preserving exact raw
  whitespace. There is no native template, EOS handling, token count, truncation,
  padding, fitting, or training recipe in this implementation.
- Predeclared control label order: `RESULT`, `COMPUTED_RESULT`, `RESULT_SUM`.
  The emitted default is RESULT, not a tokenizer-validated selection. Main must
  audit actual native template/loss boundaries/special tokens/counts BEFORE any
  model output. If needed, select the first single global variant matching every
  paired arithmetic example, recording evidence; never choose per case or using
  model outputs. If none matches, report unresolved rather than pad/truncate or
  claim exact matching. No variant has been native-audited here.
- Evaluation arithmetic expected sums are task-only keys, not enforced teaching
  response templates. Behavioral scoring and native training integration remain
  outside scope; this emitter grants no launch authorization.
- Toy low-level behavioral adherence only: no prediction-intelligence, parenting
  efficacy, prior-exposure absence, clean-lineage, completed-substrate, or H1/H2
  claim. Nothing was launched.
