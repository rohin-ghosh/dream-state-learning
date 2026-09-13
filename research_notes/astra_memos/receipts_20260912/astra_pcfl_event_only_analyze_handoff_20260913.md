# EVENT-only offline reducer — EDITSTOP

2026-09-13. Prospective reducer frozen before inspecting any new fit/readout outputs. No native/remote/GPU/model/tokenizer call, collection, rerun, commit, original-artifact mutation or importer/writer edit. Only the two new files below and this handoff were written. Lagrange's finished execution handoff was read at `/tmp/astra_pcfl_event_only_execution_handoff_20260913.md`; the reducer follows that actual schema rather than the early suggested layout.

## Frozen files / checks

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_event_only_analyze.py` | `83b88bab9603c3fd519cf08a9e785b3141d5492694abc34e7002397db417cbe4` |
| `tests/test_astra_pcfl_event_only_analyze.py` | `f122d63e82895cc880dcbad34c08322926b9b094d8fe63579b2eb73759e20c13` |

Final **18 tests PASS /31.095s**; AST and trailing-whitespace checks pass. Test command:

```sh
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_astra_pcfl_event_only_analyze -v
```

Fixtures use the fixed original archived prefix and explicitly simulated new encoding/tensor/token/lifecycle/readout receipts. Synthetic `NATIVE` labels exercise the native receipt branch; they are not native origin or numerical/tokenizer evidence. Tests never read new native outcomes. They cover the complete56-call paired archive, fixed endpoint boundaries, raw/semantic vectors, missing arm/call/close/custody, bool/nonzero rc, CVD reservation owners, source mapping/drift, injected teacher messages, route/sampling/raw-byte drift, score-vs-raw disagreement, extra retry captures, exact bytes with length finish, missing LF/fences/prose without repair, fit byte drift, cold PID joins, source-relative mapping, symlinks, fresh output, and release-inclusive floating-point clocks/costs.

## Public API and CLI

```python
analyze(archive_path, manifest_file_sha256, stage_pins) -> dict
endpoints(pairs, service) -> dict
```

`analyze` requires a **relocated immutable local mirror**, not the manifest's original live root. `stage_pins` must be a JSON object with exactly `fit`, `readout_AUTH_WRITE`, `readout_NO_WRITE_C0`. Each value has exactly:

```json
{
  "completed_sha256": "<actual stage completed.json FILE SHA256>",
  "outer_path": "<absolute local mirror of this stage's outer directory>",
  "collection_sha256": "<actual outer collection.json FILE SHA256>"
}
```

These are byte hashes, not canonical body seals. Main supplies actual pins after closure/verified transfer. The archived manifest/source/checkpoint paths inside receipts remain original; `outer_path` is only an explicit local evidence resolver. Missing arms/stages raise an error and produce no numerical endpoint; they are never filled with zero scores. Invalid custody also raises instead of silently excluding calls. The CLI does not collect or repair anything:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m gpu.astra_pcfl_event_only_analyze \
  --archive "$LOCAL_EVENT_MIRROR" \
  --manifest-sha256 "$MANIFEST_FILE_SHA256" \
  --stage-pins "$LOCAL_STAGE_PINS_JSON" \
  --output "$FRESH_ANALYSIS_DIRECTORY"
```

Output must not already exist or overlap the diagnostic mirror, outer mirrors, pin file or source tree. On success the CLI writes `analysis.json` (complete raw/custody/cost report) and `analysis.md` (limits plus endpoint/vectors). No rereadout, repair or automatic second attempt exists. A validation exception is diagnostic failure, not a scientific zero; preserve the evidence and diagnose before a separately versioned change.

## Exact Lagrange seam

Command schema `pcfl.event_only.command.v1`; outer schema `pcfl.event_only.outer.v1`. Tested against:

- Command `3ebef8ce6c8cd783104f5d0d74946fd1df5f99e41208508451482f56fdf9d916`.
- Outer `5bc4f24a744a2ee53edbe7623ce0e10831fd8a566fcfbae58e1f84531a89aac4`.
- Scope `research_notes/astra_memos/ASTRA_PCFL_EVENT_ONLY_SCOPE_2026-09-13.md`, SHA `8e33dc7876db5786ae07dfeec8306b0bfce5b2932ecbdf78284af89905e46428`.
- Unchanged prefix importer `7f12702dffd10d78fae1d115b0bfb6fcf4f993ef8de70c312e47ff6abfa9f88f`; EVENT writer `24faf066d22bd15361cd8fe95a40033a3011307cebb6ea94dad05c29aadf04e2`.

Prepared inputs are the actual top-level eight files: `spec.json`, `import.json`, `fit.json`, `tokenizer.json`, `encoding.json`, `identity.json`, `read_measurements.json`, `service.json`. Their byte hashes join the sealed manifest. The positive tokenizer receipt is separately sealed and joined, not an overwritten import status. `read_measurements.json` contains ordered id/prompt-hash/token-count rows, not full token arrays; the reducer checks exactly that available evidence and does not claim independent tokenizer replay.

Fit layout: `fit/write/fit.json`, `encoding.json`, `event_only_scope_report.json`, `initial.json`, `updates.jsonl`, `completed.json`, adapter files, plus `fit/adapter.json` and stage entry/completed files. Executed fit and encoding must equal prepared versions; numerical completion records200 updates/800 presentations/800 forwards with source/epoch/order/token/mask joins, finite loss/norms, RNG hashes and exact checkpoint inventory. Existing EVENT writer validation supplies original C0/seed/source/recipe/lineage checks; no numerical loop or fit was implemented here.

Each `readout_<arm>` directory contains its exact `readout_config.json`, actor config/identity/load/close, exactly28 sets of request/render/raw/response sidecars, per-ID response copies, `actor_close.json`, `custody.json`, `scores.json`, entry/completed files. The reducer uses the existing `_readout_config` and `public_messages` helpers to derive exact configuration/query messages without model loading. It verifies original base preparation identity versus each cold identity, saved AUTH adapter versus NO_WRITE null route, fresh distinct worker identities, premeasured surfaces, unconstrained sampling, UTF8 hex/hash, raw stop/length and token joins, original scorer output, per-view counts, completion and close/shutdown custody. There is no old153-call/17-address reducer path.

Outer mirrors supply exact original manifest/allocation/stage-completed copies, context/binding, worker start/exit/wait/release and pre/post queue/GPU/CVD observation files plus collection inventory. The reducer requires native stages rc0, no retry, released owned group, vacant GPU and no remaining CVD owner/unresolved process. The archived metadata-only service exceptions/visibility limitation remain visible in `post_cvd`; unreadable approved service environments are not asserted empty. Observation times must occur within the same boot/domain outer interval and post-resource observations after group release. Worker deadline is the archived outer binding value, not assumed equal to stage-start+1740; outer includes prechecks/cold load/close/release under1800 with60 cleanup margin. This is archived attestation validation, not fresh process inventory.

## Output and fixed endpoint

Result schema `pcfl.event_only.analysis.v1`. Major fields: `endpoint`, `pairs`, `strata`, `deterministic_service`, `format_scaffold`, `experimental_units`, `historical_prefix`, `archived_outer_release`, `source_binding`, `stage_pins`, `fit`, `costs_not_gpu_active`, source/inventory hashes, false `full_contract_released` and `automatic_promotion`.

- W8 primary: exact-child service14/14, AUTH strict_stop≥13/14, C0 strict_stop≤1/14, paired difference≥12/14. Thresholds come unchanged from frozen `event.ENDPOINT`.
- Complete ordered W0 and W8 address/ID vectors for both arms: raw strings, strict bytes, strict_stop, semantic, semantic_stop, finish reasons and errors; W8 EVENT8 versus EVENTS_AT6 split and paired difference vector. W0 remains descriptive and cannot rescue failed W8.
- `pairs` retains every raw response verbatim and unchanged `core.score_memory_response`. `errors` distinguishes `non_stop_finish` from `strict_raw_mismatch`. Missing LF/fences/prose are not normalized; semantic acceptance, where the frozen scorer already allows it, never replaces strict_stop. Exact content with length finish still fails both stop-qualified scores.
- Service is recomputed solely from admitted child queries and compared to the archived deterministic service, labeled not a model arm. No synthetic or teacher target enters this path.
- Experimental units are one original source life/root and one fit/initialization, eight EVENTs,14 addresses,20 scheduled blocks,160 encodings,800 presentations,200 updates and56 repeated readout calls—not56 independent lives/experiences.
- Original imported full formation remains `FORMATION_FAILED`, rc1,17 historical calls,zero fits/updates; its rejected LINK and source/capture evidence remain bound by the unchanged importer. Separate prefix acquisition cannot turn that attempt into full-bank success. Original17-query threshold is untouched.
- Costs separate historical17 formation calls from zero new formation and56 readout calls. Report fit-stage time, each cold load/generation/response/actor/stage interval and outer elapsed sum including release; these are elapsed intervals, not GPU-active measurements. Numerical report includes first/last loss, supervised token total, maximum norms, initial/final state hashes and adapter identity. No causal significance or automatic promotion.

## Source relocation and reused mechanics

Reuses only existing `Archive`/typed canonical comparison plus own-write `interval`/`files` helpers, exact public readout configuration/messages/scorer, importer and EVENT-writer validation. Old full-bank `analyze`, `training`, `arm_rows` and17-address endpoint are never called; no monkeypatching old modules.

Original source map is compared with local executed source bytes by **unique command-root anchor plus exact repository-relative file paths**, not loose basename aliases. Both roots and all relative hashes are returned. Original absolute paths in request/custody/checkpoint/import records are preserved. This local comparison does not pretend relocated/current source is original v3 replay: that original path/pin/receipt check remains inside the frozen importer. Input artifact pins additionally remain in actor sources. Actual current dependency bytes are rehashed; old source maps cannot be substituted silently.

Reused utility source pins are separately emitted in results: own-write analyzer `60d7a3d4bdd69eef804173ce937028e3c1c169fb96b59b8d6772a442824bf1a1`; zero-fit archive analyzer `a84f677e1b41512c0eabfd3865eafb55ec85584e53e99796175334e1bf1db00e`. Native command source snapshot excludes the offline reducer; Main should archive/pin these reducer bytes before readout outcomes as a separate prospective analysis protocol, not change the frozen native snapshot merely to add the reducer.

No blocker remains in the tested API. Actual native artifacts have not been opened by this worker; Main must provide all three completed/released stages and independently pinned verified local mirrors before authorizing real reduction. No native or whole-assay success is claimed from synthetic CPU tests.
