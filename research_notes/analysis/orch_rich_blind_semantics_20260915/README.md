# Fixed blind semantic review

Read `review.md` for the independent 24-row criticism and `blind_packet.md`
for the permitted evidence. `validation.json` binds the completed report and
packet hashes to deterministic integrity checks and an actual UTC tool clock.

## Blinding boundary

`raw/`, `source_mapping.json`, and `provenance.json` preserve source context and
linkage for Main's later audit; they are not the blinded presentation. Raw
snapshots include all original fields, including excluded labels and stored
answers. A critic remaining blind should read **only the rendered packet**,
not the raw snapshots or linkage. The scripts inspect excluded schema names
or copy original bytes but do not display or use answer/admission/condition
values to judge content. No generated target is rewritten.

## Reproduce within this repository

All scripts use the standard library and the available `apply_patch` command;
there are no model, GPU, external reviewer, or external-data dependencies.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research_notes/analysis/orch_rich_blind_semantics_20260915/prepare_packet.py
PYTHONDONTWRITEBYTECODE=1 python3 research_notes/analysis/orch_rich_blind_semantics_20260915/render_packet.py
PYTHONDONTWRITEBYTECODE=1 python3 research_notes/analysis/orch_rich_blind_semantics_20260915/validate_review.py
```

The source archive must be available at the authorized repository-local path
in `prepare_packet.py`. The first command prints only a value-free schema;
the second prints brief provenance checks. All writes use `apply_patch` and
refuse to overwrite a differing stable snapshot. The validator checks source
hashes, first-four-per-shard coverage, actual call/generation history equality,
neutral evidence, targets, token metadata, every row/axis, literal quotes,
independent arithmetic, and separate exact final-marker formatting. It does
not turn the author's semantic judgments into automated objective truth.

On repeated validation, the original validation artifact timestamp remains
unchanged and the command prints the current observed check time separately.
The worker note also preserves correction of an earlier erroneous future
journal timestamp. This review is not a canonical rescore or launch gate.
