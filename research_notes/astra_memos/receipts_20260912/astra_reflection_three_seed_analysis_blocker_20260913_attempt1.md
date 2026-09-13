# Reflection actual three-seed analysis — blocked before scoring

September 13, 2026. The accepted analyzer was invoked unchanged against one
complete manifest containing all original preselected learner seeds0/1/2.
No partial aggregate was run. No scientific report was produced.

## Preserved invocation and identities

```text
python3 -B /tmp/astra_reflection_multi_seed_analysis_20260913.py --manifest /tmp/astra_reflection_three_seed_manifest_20260913_attempt1.json --output /tmp/astra_reflection_three_seed_report_20260913_attempt1.json
```

- Accepted analyzer SHA256: `6d84b3ed8c983a7702ad9d5a5165cf1cca97c3c92f8353eef7ed1a8bc790a515` (unchanged).
- Exact manifest: `/tmp/astra_reflection_three_seed_manifest_20260913_attempt1.json`, SHA256 `425b67ec52a8434d1931561fe38ad5f9c4db88ef635323238c61f1ef07b3a07c`.
- Failed invocation log: `/tmp/astra_reflection_three_seed_analysis_20260913_attempt1.log`, SHA256 `2f6e46afe5855d91d38c2f229848f50f6f6a23701bacac48c24e1801396ede51`.
- Exit status1: `ValueError: source/binding receipt mismatch`, analyzer line378.
- `/tmp/astra_reflection_three_seed_report_20260913_attempt1.json` does not exist.

The failure occurs on seed0's prepared-input provenance check, before raw
response scoring or any aggregate. Its analogous comparisons also fail on
seed1/2 metadata. No guard was bypassed and no receipt/source bytes were changed.

## Checks that passed before the failure

All five frozen source hashes and both producer-runtime hashes match the
accepted interface. All three selected runtime/config seed identities and
collection-to-completion/score bindings were inspected. Seed1/2 full archive,
completion and score hashes match Main's supplied pins. Seed0 identities were
read from the existing relocated collection and hashed locally; no additional
externally supplied seed0 archive pin was claimed.

Full archive hashes computed locally:
- Seed0 `seed0_attempt1.tar`: `055f3a63cb7c057d8fca1b87bbec72b27c16b226bc031b01f88f7aaf662be40e`.
- Seed1 `seed1_attempt1.tar`: `a711ecc5122570ce7b87de84bd791f4c0ad90d08790ce2aeddffe376d7e35232`.
- Seed2 `seed2_attempt2.tar`: `c95a857053d2d282bb7707df82403a1fb7ee76a208b3eb3d398cf3e10c71a26f`.

The exact per-seed relocated roots, logs, score paths, and plan/completion/
scores/collection file hashes are retained in the manifest. The full raw-stage
custody/scorer checks have NOT completed, so no full analysis PASS is claimed.

## Root cause: two byte identities incorrectly equated

The producer verifies incoming source-pin and binding receipts, decodes them,
then serializes copies into the run root with its own compact JSON writer.
The plan preserves the incoming receipt byte hashes separately from the new
`input_hashes` for these serialized copies. The accepted analyzer incorrectly
requires the two byte hashes to equal, although the decoded content agrees.

The following values are identical across all three relocated roots:

| Receipt | Plan's original receipt SHA256 | Actual copied artifact SHA256 (equals plan input pin) |
| --- | --- | --- |
| `source_pins.json` | `111528d41e8fca6863a853da5d311d414e1a9e83f8c7a6839a9e82a3b80457f1` | `5c2b6ff4befdae2bd069032644c77b864ee02aaaf8d4a74fb90291c99cfcf646` |
| `binding_receipt.json` | `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019` | `9dfba37dd2ce47be6780c83588a8adb07c44ee70395933f35feeb4b70dcc4f70` |

For both receipt objects in every seed, serializing the decoded copy as
`json.dumps(value, indent=2, sort_keys=True) + '\n'` reproduces the plan's
original receipt SHA256. This is a hash-checked reconstruction demonstrating
the formatting distinction, not a claim to have opened the original native
receipt paths. The copied source-pin object equals all five frozen source pins.
The producer implementation establishing these distinct identities was read
from the pinned seed0 runtime's `prepare` function; no native function ran.

## Scope and required next step

This is an analyzer provenance-check bug, **not a scientific null**, failed
learner outcome or evidence of damaged collected captures. No three-seed
interpretation or numerical null bound can be issued from this failed run.

The no-source-changes instruction remains in force. A narrowly scoped sidecar
repair and regression test need authorization before rerunning: preserve the
upstream receipt identities, validate copied artifacts against their own plan
input pins, and distinguish byte serialization from decoded-object identity.
Do not edit collected plans, receipts, captures or the frozen corpus to satisfy
the faulty comparison. Preserve this failed manifest/log and use a fresh report
path for any subsequently authorized repaired analysis.

Only new `/tmp` manifest, log and this diagnostic were written. Accepted
analyzer/tests, producer scripts, all relocated data and manuscripts remain
untouched. No recollection, native/model/GPU/process access, remote/network
activity, Git command or external send occurred.

EDITSTOP
