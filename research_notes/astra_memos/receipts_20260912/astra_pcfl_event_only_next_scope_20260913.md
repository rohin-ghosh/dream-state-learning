# Separate EVENT-only acquisition from the SEQ171 prefix

2026-09-13. Read-only design and bounded local archive checks only. No new diagnostic implementation, model/native/GPU call, source edit, commit or extraction over existing sources. Main's v5 failure is taken from the request; this memo examines only the selected original format-scaffolded v3 archive, not alternative prefixes.

## Decision

**Prefer a narrowly validated import of SEQ171's first16 call slots, yielding all eight EVENTs, rather than spending16 new formation calls.** A later LINK failure does not undo already executed actions or the exact earlier EVENT generations. This is a new EVENT-only acquisition diagnostic selected after a full-bank failure, not a repaired full bank, successful original formation, or confirmation. Import exactly this named source and prefix; never choose whichever later prompt version or prefix gives better write results.

Proceed only if the original source/capture/release joins can be validated without pretending relocated or current source is the v3 source. If that bounded import cannot be made trustworthy, use a separately declared fresh16-call EVENT-only formation with the same public action/record protocol; do not waive evidence checks. Fresh formation is not needed merely because the old report correctly says FAILED.

## What I verified locally

Archive: `gpu_artifacts_local/pcfl_own_write_format_20260913_attempt1/evidence.tar`, SHA256 `bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869`. Its existing `unpacked/` mirror contains the source tar and the original diagnostic/outer records.

- Original formation config policy is `public_session_history_whole_response_stop_only_format_scaffold_v3`; scaffold is `pcfl.disposable_old.format_only_terminal_lf.v1`, regex `[^\r\n]+\n`, readout unconstrained.
- The report is **FORMATION_FAILED at old/formation/16**, first LINK, for `child LINK differs from pre-output choice`. Counts:17 attempted calls,8 accepted EVENTs,0 accepted LINKs; remaining three LINK slots uncalled; `writer_payload=null`, fits0, updates0. Do not replace any of these fields or fabricate a completion receipt.
- For every slot00..15, I compared the archived actor raw-sidecar bytes/hash to the report's embedded capture, checked actual stop finish, and replayed the action/EVENT pair through the current core whose exact SHA equals the archived core pin. Each actual action matched the sealed action; `WorldSession.explore` reproduced the complete saved world result; `admit_event` reproduced the saved admission exactly. This was a CPU verification of existing evidence, not new experience or a model invocation.
- Materializing the **eight actual admitted rows** with `core.materialize_queries` gives **14 queries:8 READ EVENT,6 READ EVENTS_AT,0 READ LINKS_FROM**. There are12 singleton blocks and2 two-EVENT blocks. Canonical query-map SHA256: `39e2d8d430e54ff3818967790cbe38eb15f41c014010f6647562b4c68ce02f8c`. These14 addresses are not14 independent events; the underlying denominator is8 source EVENTs. No LINK or empty/synthetic target is needed.
- The original explicit EngineCore shutdown receipt reports success; worker exit is1 with no signal; the worker-group release and GPU-vacancy observations are positive. The collection remains **FAILED**, with nonzero-worker/missing-stage-completion errors. The CVD observation is clear with no owners, retaining the approved two service-environment exceptions rather than asserting those environments were read. These are separate failure and release facts, not a valid original scientific completion.

This check did **not** execute the complete archived formation replay or load the native tokenizer. It does not itself certify all native identity/timing/source provenance. The import stage must finish those checks before authorizing a write.

## Exact source/path distinction

The supplied native source path `/tmp/astra_pcfl_own_write_format_source_20260913_attempt1` is absent on this local host. A tar is available both under the archive mirror and at `/tmp/astra_pcfl_own_write_format_source_20260913_attempt1.tar`; both hash to `698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280`. The actual archived v3 formation-module byte SHA is `9c1e4099ac0ad4d4f53c55d7a35b0d26e3b7dc6da0620f5321cca416e71e4669`. Treat Main's `69b760cd` as a supplied version reference, not as an interchangeable file/tar SHA.

All six `formation_config.source_pins` match the corresponding source-tar members. They bind absolute paths under that original native source root. Archived `validate_config` reconstructs `build_config`, including actual imported source paths and v3 policy. Consequently neither current v5 imports nor importing the old bytes at a different path is automatically an equivalent call to old `replay_validate`.

Smallest safe route: Main uses the intact original source tree, or a separately restored exact snapshot at its bound logical path in an isolated CPU process, and calls that v3 `replay_validate(config, config_sha256, report)`. It must reproduce the original failed20-slot report, not a shortened successful report. Keep old module imports isolated from the new writer's modules. This is replay only, never `run_formation` or generation. Archive the replay receipt and original file-byte hashes.

If exact-path replay is unavailable, the only alternative import is a **new explicit archive resolver**, binding original absolute source/data paths to exact archive member bytes and checking each pinned hash, followed by independent public transition and raw-capture replay. It must retain the original strings/seals and report its separate validation method. Do not rewrite source-path fields, reseal old configs, symlink around source equality, monkeypatch source_pins, or silently call the current validator. That alternative is more engineering than the exact-path replay; if it cannot close the joins simply, choose fresh16-call formation instead.

## Minimal legitimate prefix-import receipt

Create a new `EVENT_PREFIX_IMPORT` record in a disjoint root. It references, without modifying, the original archive, source tar, manifest/config/report, original raw capture files and shutdown/failed collection/release receipts. It records `original_status=FORMATION_FAILED`, failed LINK slot16, original17 calls/0 fits/0 updates, and `selected_call_indices=0..15`, `selected_event_indices=[1,3,5,7,9,11,13,15]`. Prefix-import status means only those16 existing calls passed the scoped import checks. It is not `formation.COMPLETE`.

Required checks are local and finite:

1. Original file bytes/seals/source pins and model/tokenizer/environment/C0 route identity; exact default sampling on EXPLORE and JSON regex scaffold on EVENT; no parent, adapter or teacher intervention.
2. All16 ordered native request/render/raw/response joins and token/finish/time bindings. Re-render with the original actual tokenizer and verify output IDs decode to exact raw text, including LF. Whole original responses only: no span extraction from prose or host-appended newline.
3. Exact chronological WorldSession receipts and EVENT admission; source fields, action choice and raw spans all match. Check the public prompt/history for each selected EVENT contains only material available before that generation, not later LINK attempts or private expected bank. All eight events are mandatory; missing, length, unsupported or ambiguous joins fail the import without searching another prefix.
4. Original failure and subsequent release evidence stay attached. Do not invoke the old all-complete lifecycle validator expecting20 successful calls, nor invent rc0. Accept the original rc1 only as the recorded downstream LINK failure after the validated prefix; any unexplained source/backend error blocks import.
5. Copy each admitted row **unchanged**, including its existing `native_generation_verified=False` field. Create the ordinary generation payload from that row's actual raw capture (`raw`, byte SHA, `origin=CHILD_NATIVE`, capture SHA); attach the prefix-import validation separately rather than flipping old provenance booleans. Parent/checker prose and rejected LINK bytes cannot become targets.

This conditional import preserves authentic semantic outputs **under external format scaffolding**. It is a selected component acquisition test, not evidence of spontaneous serialization, successful LINK formation, whole-agent learning, or original full-bank qualification.

## Smallest LOW200 writer adapter

Do **not** call `pcfl_own_write_train.build_fit/validate_fit` with a forged report: it correctly requires COMPLETE native full formation,12 rows,17 first blocks,20 successful calls and the old lifecycle. Do not lower those requirements in place.

Propose one new `organism_v6/pcfl_event_only_train.py` plus its test file. It can own the narrow prefix-import binding, EVENT-only corpus/schedule validation, and calls to the existing numerical helpers. Use exactly14 first query blocks from the real eight-row materializer, then **six prospectively selected exact EVENT-block replays** to retain20 slots. Reuse the existing deterministic `_select_replay` rule over those14 eligible blocks, with a newly declared domain bound to the fixed original report/prefix and EVENT-only scope; preserve the choice list and support counts in the new schedule. This unavoidable change from17+3 to14+6 must be explicit. No invented rows, corpus content repair, example normalization, or search for a schedule based on model results.

Retain the current support-disjoint four-example partition and `writer._schedule` validation. If deterministic placement fails, stop at preparation; do not quietly rotate/select more favorable targets. This memo has not executed or sealed that prospective schedule. It must be CPU-validated and fixed before any new readout or fit output.

Unchanged reusable helpers in `organism_v6/pcfl_vertical_train.py`:

- `_lineage`: already validates any fully referenced authentic row/generation set; eight rows are acceptable without controls.
- `_schedule`:20 slots ×8 W0..W7 views ×5 epochs,40 four-example updates/epoch; underlying EVENT supports cannot collide within a batch.
- `_encode_corpus`: exact materialized raw targets, loss-masked context, target plus supervised EOS,512-token limit, no truncation or packing.
- `_train_encoded`: fresh frozen bf16 C0 base pinned by actual tensor hash, fresh rank8/alpha16/dropout.05 LoRA, fresh AdamW, LOW3e-5,200 updates/800 presentations, existing pooled token objective/clipping/save receipts. Reuse via a separate scoped validation receipt and report filename; no numerical-loop edits or descendant initialization.

Reuse the same actual base/model/tokenizer/environment receipt format, init/dropout seed values and frozen wrappers; Main must pin the numerical/helper sources actually executed. The new import source and new training source are distinct bindings, not one silently replaced snapshot.

## Endpoint to freeze before new outputs

Smallest cold test: **14 W8 queries on fresh AUTH_WRITE and the same14 on fresh NO_WRITE_C0:28 calls total**, one stop-completed generation per query/arm, original unconstrained readout settings/scorer. Query order is deterministic from the14 actual addresses; no expected target strings enter the readout prompt. This tests held-wrapper access to these eight trained events, not held factual content.

Proposed preregistration: primary endpoints are exact-stop W8 correct counts/14 for each arm, their paired gain/loss/tie table, and the two adjacency-block results separately from the eight singleton-address results. Also report the six EVENTS_AT results separately (four singleton/two double), declared semantic-stop scores and raw termination/errors. A stringent optional **new EVENT-only complete-acquisition criterion** would be AUTH14/14 exact-stop and positive paired gain over C0; if C0 is already14/14, mark no measurable acquisition headroom rather than infer a write benefit. Main must explicitly adopt or replace that new criterion before either arm produces outputs. Do not rescale/apply the old17-query threshold or report a full-bank pass.

The28-call design cannot distinguish failure to store from failure to access through W8. If that distinction is required immediately, predeclare W0 for the same14 addresses/arm as a separate secondary endpoint before any outputs (56 total calls); do not add it after seeing a miss and call the resulting choice predeclared. Neither design tests LINK composition, route action or general retention. NO_WRITE is not a compute-matched LR0 control.

`gpu/astra_pcfl_own_write_readout.py` already accepts a sealed variable-length roster with `max_calls=len(roster)` and W0..W8; it need not change. Reuse its `ReadoutActor`, `public_messages`, source/adapter routing and exact decoder custody with the new14-query roster, preserving required legacy source pins and adding the new scope/import binding. Use the existing two legal arm values but label the report externally as EVENT-only. A tiny disjoint `gpu/astra_pcfl_event_only_command.py` plus tests can connect import/fit/readout and new manifests. Old command `_completed` correctly rejects the failed source formation and cannot be used as if it succeeded. Main owns the narrow outer command/report binding and release; no general controller/guard redesign is needed.

## When fresh16-call formation is genuinely required

Use it only if original raw files/pins/stop/token/receipt joins are missing or inconsistent, native identity is unexplained, actual tokenizer revalidation cannot be bound, or no safe original-source replay/archive resolver is available. A full-bank rc1 caused by the later LINK is not by itself such a defect. Fresh acquisition must use a new root/config/source/output binding, exactly eight action/EVENT pairs, fixed prior choices and the same disclosed formatting scaffold, with no LINK calls or retries. It is new experience and a new experiment, not a replacement for SEQ171. Do not automatically fall back from a failed import into new generation; Main should record that decision first.

## CPU acceptance and costs

Tests should reject changed raw bytes/LF, wrong chronology/action/receipt, length finish, missing/extra selected slots, substituted v4/v5 source, relocated-path assumptions, imported LINK/teacher targets, fabricated completion/rc0, repeated selection among attempts and source-hash mismatch. Positive replay uses exactly all eight selected EVENTs and yields exactly8+6 queries with the two double blocks. Verify eight generation joins, lineage,14+6 schedule coverage/disjointness, masks/EOS/no truncation, fresh-base numerical helper dispatch and14-query W8 route/scorer consistency. Existing tiny numerical tests need not be duplicated as a new optimizer implementation.

Incremental planned cost with prefix import:0 new formation/teacher calls,1 fit/200 updates/800 presentations,28 cold readout calls (or56 only if W0 is predeclared). Historical source cost remains17 calls, including the failed LINK,0 fits. Import CPU/tokenizer work and new fit/readout cold-load/shutdown/release time are reported separately. No automatic LR/dose/prompt ladder or checkpoint selection.

## Source/evidence pins

Relative evidence paths below are under `gpu_artifacts_local/pcfl_own_write_format_20260913_attempt1/unpacked/`.

| File | SHA256 |
| --- | --- |
| source tar `astra_pcfl_own_write_format_source_20260913_attempt1.tar` | `698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280` |
| diagnostic `manifest.json` | `e1004bfa9f5cea0538a54f5866054285ea3ab7d7820df6f4ef77da5673d791ec` |
| diagnostic `formation/formation_config.json` | `66704311982c8668744596b92588684b9c638252058d0f220a6effc16a2303b1` |
| diagnostic `formation/records/formation.json` | `595c3e65b8eaa1d73e270094d78f0e3a88c66b3b6a23b44b2677cd807692bd15` |
| outer `collection.json` (FAILED) | `e65f69eeed689b921d489b6297909111aec7562238da1a2b4e541e3fcb6302ac` |
| diagnostic `formation/shutdown.json` | `22ddffc76fb8f4e6afda8a07fcdb08c9f8148f720c375919fd645b49ceeb16e1` |
| diagnostic `formation/actor_close.json` | `205d43c3655a36377cb29e2b12a1a0bdfefbb24445e4b9ceb0a9884ad5ce86b7` |
| outer `worker_exit.json` (rc1) | `8716b33c669649d0f539653ebf72a86e2118455a15e0e6f69c7a8865c025cbd0` |
| outer `worker_release.json` | `01828c50b91218d2e97cff4cc80378f01de38d3fa59a8254a0b3a0636768b634` |
| outer `post_gpu.json` | `8b159ef77663656a78581400872aab816bd756592133d01f3f0ecacd523c635c` |
| outer `post_cvd.json` | `1bc16cb958ad3db8c2715bdf56e42677c47498b5785f2aeeac7ebb6be7a6f13f` |

Reusable source bytes inspected: core `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`; numerical writer `9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078`; old full own-writer `b5af7c634b960288ffe329bc603d09c251125a63f3194409c7b6bb74c9ca7af9`; preparer `c07ba9b684299a8d6cf6c7b45bbdbb95ed6f3e04db9e8de6e926791610b55c61`; readout actor `d8d4ef962ca80933f3c3a60681c8375198197855f8d5f00a2b7835461e8427c4`.

Bottom line: a named failed run can contain a valid authentic EVENT prefix. Reuse requires an honest separate import contract, not a forged complete formation or a source-path substitution. The new outcome concerns EVENT-only acquisition from that fixed development prefix; all full-bank failures and thresholds remain untouched.
