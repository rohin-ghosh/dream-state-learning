# Fixed-coaching old-retention scorer replay — EDITSTOP

2026-09-13. Independent local CPU-only closure of the intentionally deferred
material-scorer replay in the parenting reducer. This is not a second cohort
analysis and does not alter any scoring policy, experiment response or label.

## Result

**All360 P/N old-retention items were re-scored; zero discrepancies.**
There are six readouts, each48original perception held rows plus12original
canaries. The complete reconstructed score object equals the stored object
itemwise, with JSON-type-sensitive comparison (Boolean true is not integer1).
This checks all score/error/format/raw fields, not just aggregate Booleans.
`discrepancies=[]`; no discrepant IDs exist. The JSON retains every row_id,
call_id, source-row/target/response hashes, raw response, finish reason,
replayed and stored score objects, equality flag and differing-field list.

| Seed | P held content/strict (/48) | N held content/strict (/48) | P canary content/strict (/12) | N canary content/strict (/12) |
|---|---|---|---|---|
| 0 | 47 / 47 | 47 / 47 | 12 / 12 | 12 / 12 |
| 1 | 47 / 47 | 47 / 47 | 12 / 12 | 12 / 12 |
| 2 | 44 / 44 | 46 / 46 | 12 / 12 | 12 / 12 |

Held error rows: seed0 P/N each1schema error; seed1 P/N each1source error;
seed2 P4source errors; seed2 N1source plus1syntax error. No completion errors.
All canaries are correct. The frozen format classification reports359exact
and1unparseable response. `format=exact` means canonical serialization of the
parsed response, NOT necessarily the correct target; the score's `strict`
additionally requires correct content and target-exact raw text.
These are retention counts, not the different new-cohort held endpoint.
Main/Lovelace retain all cohort interpretation and historical comparisons.

## Discovered scientific scorer and source chain

Pinned parenting runner `/tmp/astra_parented_record_run_20260913.py`, SHA256
`54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8`,
lines512–525 defines `retention_scores`: original supplied source row plus
`response["text"]` and `response["finish_reason"]` go directly to
`bound["material"].score_row`. The runner is hashed/read, never imported or run.

The parenting plans' `parent.material_pin` and the hash-verified original
perception plans' `specification.material` identify exactly:
`/tmp/astra_level1_perception_reflection_material_20260913.py`, SHA256
`4648f8542b1babb10f6ffda4bf023024d71b8c9834a32e2242a7f064a94a8941`.
Its unchanged `score_row` is invoked directly, including explicit authored
abstentions and the original copy/arithmetic canaries. The frozen scorer checks
target/proof consistency, public evidence, typed output and completion; its
content-primary/strict-secondary policy accepts its specified sole JSON fences
and whitespace without repairing prose, types, keys or values.

The scorer's source root is the plan-bound local frozen snapshot
`/tmp/astra_level1_real_record_source_20260913_attempt1`. All five parent source
file hashes are verified; the material's three declared source dependencies
must match them. Only its pure source/scoring loader executes. As in the native
material loader, `ASTRA_LEVEL1_SOURCE_ROOT` is set during module loading and
restored immediately; no frozen source/global constant is patched. The corpus
loader extracts the pinned public parser definitions without importing the
native diagnostic runner. No trainer/runtime/model/tokenizer is invoked.

Original rows are NOT regenerated for the live replay. Exact `material.json`
and `calls.json` are read in-memory from the preserved original perception
archive, their hashes checked against the original plans, whose hashes match
the parenting plans' parent bindings. Fixed material provenance/source pins,
48/12 denominators, unique row/call IDs, original messages/native encoding,
and ordered parenting `retention_calls.json` must agree. Fixture tests alone
generate pure authored source rows for synthetic raw-response checks.

## Custody boundary

Input manifest (read unchanged, shared with Lovelace):
`/tmp/astra_parented_record_analysis_inputs_20260913_attempt1.json`, SHA256
`df245557fc9c11f1ddc6bf08506e53b77ff189a8f0414658ef5e2e5a87c76edd`.
Exactly the fixed three seed entries and P/N panels are required.

Full parenting archive:
`/data/home/rohing/dream-state/gpu_artifacts_local/parented_record_20260913_attempt1/evidence.tar`,
SHA256 `c69caf2c80a682fac26048d351d6f148216161dde7ee5b1ad847dacd0ee8b439`.
Complete local mirror: `/tmp/astra_parented_record_native_20260913_attempt1`.

Original perception archive:
`/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar`,
SHA256 `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a`.

Both whole archives are hash-verified, inspected for unsafe/duplicate/link/special
members, and selected files read without extraction or writes. Parenting
plan/specification/completion/collection/scores bindings are checked. Both
retention stage inventories must match completion inventories and the exact
local file sets/hashes; worker-done plan/stage joins are required. These selected
local captures and collected scores/receipts are also matched to archive bytes.

For every scored item, original source row/messages join to the original call,
then the parenting call and exact saved request (including params and P/N
adapter route). Response native prompt fields and actual prompt IDs must match
the saved native encoding; route/raw/finish/hash join to the stored score item.
The recorded paths are preserved, never opened as remote/native paths.
The JSON includes exact source/plan/collection/score pins and verified local
retention-file inventories for all seeds.

This bounded replay does not repeat formation/new-cohort scoring, historical
original scoring, fit validation or Lovelace's full reducer. It does not freshly
attest hardware, lease, live process identity, tokenizer decoding or numerical
model execution. Adapter routes are checked as recorded identities; adapters
are not loaded. The same frozen scorer is shared scientific machinery, not an
independently redesigned oracle. No policy/promotion decision follows.

## Tests and execution

22CPU tests PASS in1.047s before executing the real replay. Coverage includes
wrong stored Boolean and Boolean/int distinction; non-metric/missing/extra score
fields; exact discrepancy IDs; raw/request/prompt/adapter joins; missing and
duplicate rows; target/source-proof tampering; scorer/source pins; archive
hash/missing/duplicate members; symlinks; strict JSON duplicate/nonfinite input;
fences/whitespace/keyorder; truncated completion; surrounding prose; canary
scoring. CLI help also passed. No native dependencies are loaded.

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120s python3 -B -m unittest discover \
  -s /tmp -p test_astra_parented_retention_rescore_20260913.py -v

PYTHONDONTWRITEBYTECODE=1 timeout 180s python3 -B \
  /tmp/astra_parented_retention_rescore_20260913.py \
  --inputs /tmp/astra_parented_record_analysis_inputs_20260913_attempt1.json \
  --inputs-sha256 df245557fc9c11f1ddc6bf08506e53b77ff189a8f0414658ef5e2e5a87c76edd \
  --original-archive /data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar \
  --out /tmp/astra_parented_retention_rescore_20260913_results.json
```

Replay exit0, tool elapsed7.9s,360items,0discrepancies. The output is exclusively
created; existing paths are rejected, so do not rerun using this output name.
API: `replay(inputs_path, inputs_pin, original_archive) -> report`;
`rescore_panel(...)` performs pure itemwise joins/replay for tests. A custody
failure aborts without output; an authentic stored-score difference is reported
with exact seed/arm/panel/row/call IDs and both score objects, never relabeled.

## Owned deliverables / pins

Only the following new files were written for this task:

| File | SHA256 |
|---|---|
| `/tmp/astra_parented_retention_rescore_20260913.py` | `a9dcc7d4b0355905ba3a187731de7ba1d026f2d5aa5f351434040d047bf9d765` |
| `/tmp/test_astra_parented_retention_rescore_20260913.py` | `ebd6ed6edbee7796fe13544293bca119ab01b696de033b42c4c531427fae398b` |
| `/tmp/astra_parented_retention_rescore_20260913_results.json` | `f217f480f9a42f983fde87f381f497bd63d811ff4baf909b46a57764dbec4d30` |
| `/tmp/astra_parented_retention_rescore_20260913_handoff.md` | Self-hash supplied with EDITSTOP |

No original captures, source files, manifest, other reducer, repository file or
experiment labels changed. No native/GPU/model/tokenizer/network/Git/collection
actions occurred. Main owns integration and cohort conclusions.
