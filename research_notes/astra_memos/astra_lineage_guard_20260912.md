# Standalone clean-ancestry guard handoff

Recorded: 2026-09-12T06:26:17Z (2026-09-11 Pacific local evening).
Classification: non-material provenance repair within the explicitly requested
two-new-file scope. No architecture, thesis, experiment protocol, runner,
existing acceptance test, or scientific claim changed.

## Inputs read

- Repository AGENTS.md, including the standing authorization and invariants.
- research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md §15, especially invariant 2.
- research_notes/2026-09-11_minimal_causal_parenting_h2_consensus.md: explicitly
  an unratified candidate. Its experiment protocol was NOT implemented.
  Factual-support validation remains separate from ancestry eligibility.
- No nested AGENTS.md files were found under organism_v6/ or tests/.

## Files authored

- organism_v6/lineage_guard.py (new stdlib module and CLI).
- tests/test_lineage_guard.py (new stdlib unittest fixtures).
- This expressly requested /tmp result note.

No other file was edited/reverted, no commits or branches were created, and no
GPU, network, or remote mutations were performed. Concurrent tracked/untracked
changes observed in the working tree belong to other workers and were left
untouched. Parent/main owns run_life integration. No COORDINATION.md edit was
made because it is outside this task's explicit scope; this is not a GPU gate
receipt or launch authorization.

## Exact integration API

```python
from dataclasses import asdict
from organism_v6.lineage_guard import LineageGuardError, validate_manifest

receipt = validate_manifest(
    "child/manifest.json",
    root=bundle_root,
    expected_sha256=approved_manifest_sha256,
)
receipt_json = asdict(receipt)
```

Signature: `validate_manifest(manifest_path, *, root, expected_sha256=None)`.
The root is required. The expected entry SHA256 pin is optional; omit it only
when no independently selected entry hash is available. File paths may be
strings or path-like objects at the API boundary; JSON paths must be strings.
Failures raise `LineageGuardError` (a `ValueError` subclass). The caller must
abort clean-lineage admission/parenting on failure, never default to eligibility.

Success returns a frozen `EligibilityReceipt`:

- `eligible`: True (there is no partially eligible success).
- `exposure_status`: exactly `UNEXPOSED`, valid across every checked ancestor,
  source, artifact, and corpus declaration.
- `root`: absolute, no-symlink bundle directory.
- `manifest`: frozen `FileBinding(path, sha256)` for the entry manifest.
- `manifests`: sorted tuple of `FileBinding` for the complete manifest closure.
- `files`: sorted tuple of `FileBinding` for all source/artifact/corpus files
  across that closure.
- `scope`: explicit ancestry-only limitation text.

Persist the receipt with run provenance. Match the actual adapter/base,
corpora, source material, and other consumed influences to receipt bindings.
The guard checks a snapshot, not future writes: use immutable verified inputs
or revalidate/pin the exact bytes consumed at use. A receipt never authorizes
additional files merely because they share an output directory or filename.

CLI:

```text
python3 -B -m organism_v6.lineage_guard --root BUNDLE child/manifest.json
python3 -B -m organism_v6.lineage_guard --root BUNDLE --expected-sha256 HASH child/manifest.json
```

Both success and validation rejection print one JSON object to stdout. Exit 0
means ancestry eligible; exit 1 means rejected (`eligible: false`, `error`,
`scope`). Argparse usage errors exit 2. No manifest or receipt file is written
by the CLI. There is no automatic clean-manifest generation or bypass option.

## Exact version 1 manifest/artifact contract

All listed keys are required; unknown keys and duplicate JSON keys reject.

| Object | Exact keys / allowed values |
| --- | --- |
| Manifest | `schema_version: 1` (integer, not boolean), `base_model: "Qwen/Qwen2.5-7B-Instruct"`, `kind: "fresh_base"` or `"descendant"`, `exposure_status: "UNEXPOSED"`, `parents: []`, `sources: []`, `artifacts: []`, `trained_corpus: []` |
| Parent reference | `path`, `sha256` |
| Source | `path`, `sha256`, `exposure_status: "UNEXPOSED"`, `role` |
| Artifact | `path`, `sha256`, `exposure_status: "UNEXPOSED"`, `role`, `source_sha256: []` |
| Trained corpus | `path`, `sha256`, `exposure_status: "UNEXPOSED"`, `source_sha256: []` |

The empty arrays in the table describe list-valued fields, not permission for
every list to be empty. Constraints:

- Every `path`, including nested-parent references, is relative to the ONE
  bundle root, not to its containing manifest. Reject absolute paths, `..`,
  dot components, empty components, backslashes, NULs, and symlinks in any
  component, including the root. Parent manifests should be copied into an
  immutable bundle, not referenced through a symlink or traversal path.
- Every `sha256` is exactly 64 lowercase hexadecimal characters bound to
  actual nonempty regular-file bytes. Missing files, empty files, devices,
  directories, FIFOs, hash mismatches, and changes detected while hashing fail.
  Large base/adapter files are streamed rather than loaded into memory.
- The only accepted source roles are `experienced_event`,
  `environment_outcome`, `parent_turn`, `person`.
- Artifact roles are `base_model`, `lora_adapter`, `memory`, `parent_notes`,
  `ranking`, `selection_decision`. A learned model artifact is a LoRA adapter,
  not an alternate or full-finetuned base. List every constituent checkpoint
  file separately; directories are not file artifacts.
- `source_sha256` cites hashes from THIS manifest's source records. Repeated
  references reject. Non-base artifacts and every trained corpus require at
  least one supported bound source. Base artifacts require no source hashes.
- `fresh_base` requires zero parents, zero sources, zero trained corpus, and
  at least one artifact, all with role `base_model`. This is an explicit birth
  attestation with actual hash-bound files, not a filename-derived verdict.
- `descendant` requires nonempty parents, sources, and artifacts. Its artifacts
  cannot have role `base_model`; the base is recursively bound by its ancestry.
  Multiple parents and shared-ancestor DAGs are supported; duplicate parents,
  active-path cycles and active-file-identity cycles reject.
- `trained_corpus` inventories corpus files used at this step. It may be empty
  for a step with no new trained corpus, but NEVER clears inherited corpora or
  exposure. All parent records remain mandatory and recursively checked.
- Every manifest independently repeats the fixed base and explicit exposure.
  `CLEAN`, unknown, missing, wrong-type, or mixed-case status values do NOT map
  to `UNEXPOSED`. No status is inferred from a path.
- `DEV_UNVERIFIED_PROVENANCE`, `QUARANTINE_TASK_EXPOSED`, bootstrap_v1/v2/v3,
  CompilerGym and R2_B_seed3 markers are vetoed in any manifest string, record
  path, or bundle root. Matching is case-insensitive and includes separator
  variants for bootstrap/CompilerGym. Unknown extra provenance fields reject
  rather than being silently ignored. This guard offers no bootstrap override.
- All declared influences are checked, even if not cited by another local
  artifact; unrelated clean data cannot hide a tainted declared source.
- Bounds: 64 active lineage levels, 512 unique manifest paths, 4,096
  source/artifact/corpus records, 1 MiB per manifest. Exceeding a bound rejects.
  Filesystem traversal requires POSIX no-follow, directory-relative opens;
  unsupported safe-open capability rejects rather than weakening the guard.

## Scientific and trust limits

Clean means ANCESTRY ELIGIBILITY ONLY, not factual entailment, truthful contents,
automatic validity of all data, or authorization to train on parent text.
The guard cannot establish completeness/honesty of declarations, authenticate
the declarant or official base weights, or identify renamed undeclared gym
data from arbitrary file bytes. Callers must inventory every causal influence,
including notes/rankings/selection decisions, and separately retain base-weight
authentication, factual-support, contamination review, training-target,
frozen-base, and consumption-integrity gates. Hash binding establishes byte
identity, not factual support. Parent-turn provenance is not loss-target
approval. No H1/H2 or causal experiment claims are made here.

## Targeted validation result

Only the new targeted suite was run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_lineage_guard.py -v

Ran 30 tests in 0.207s
OK
```

Coverage includes valid explicit base and child (all supported source roles),
tainted grandparent, unknown statuses at every record level, ancestor tainted
non-weight artifacts, empty/missing fields, invalid/mismatched hashes, actual
file tampering, missing files, source traversal and symlinks, manifest/parent/
artifact/corpus/root symlinks, cyclic lineage, shared DAGs, blocked families,
nested-manifest root semantics, resource limits, duplicate keys/references,
unknown fields/roles, unbound sources, nonregular files, read-only behavior,
CLI JSON/exit behavior and the filename-only-clean counterexample.

The initial 23-test run exposed one test-fixture aliasing error (a shared parent
dictionary was mutated while iterating). Copying the fixture parent binding
fixed it; the 23-test rerun passed, then all 30 expanded tests passed. No other
project tests, pytest, GPU workloads, or remote commands were run.

Final authored-file SHA256 at the recorded checkpoint:

```text
2404703eebeb152d944b6eb2ce16f8552a946907833dac7d36aba7b2139c2fc8  organism_v6/lineage_guard.py
1c01108512b65725e1dc6991fd2de70a4356740293f7c8fddc9b6251cc99aba4  tests/test_lineage_guard.py
```
