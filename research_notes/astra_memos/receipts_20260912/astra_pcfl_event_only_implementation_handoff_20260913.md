# EVENT-only fixed-prefix acquisition adapter — EDITSTOP

2026-09-13. CPU implementation only. No remote/native/model/GPU execution, fit, readout, new formation, extraction over old sources, commit, or changes to old failed artifacts. Main owns new command/outer/readout bindings and execution. Only the four new source/test files below were edited, plus this handoff.

## Final files and SHA256

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_event_prefix_import.py` | `7f12702dffd10d78fae1d115b0bfb6fcf4f993ef8de70c312e47ff6abfa9f88f` |
| `organism_v6/pcfl_event_only_train.py` | `24faf066d22bd15361cd8fe95a40033a3011307cebb6ea94dad05c29aadf04e2` |
| `tests/test_astra_pcfl_event_prefix_import.py` | `f20488c8a38702348fa491ada443be6598240e0c6c7265be0b5f087f724c88bb` |
| `tests/test_pcfl_event_only_train.py` | `73fcce19ae7743cefe4109a22ffe6dcae5e906090360ec9deeb6b018088f5d55` |

## API and evidence boundary

`gpu.astra_pcfl_event_prefix_import`:

- `load_evidence(archive_path)` reads the one fixed SEQ171 archive in memory without extracting or executing source. Exact archive SHA required; no alternate attempt, prefix or fallback.
- `build_import(evidence, replay_receipt, replay_receipt_sha256)` validates original immutable files and all17 actor captures, then independently replays only slots00..15 using the actual public WorldSession/core. Returns a sealed dictionary with eight original admitted EVENT rows, eight exact child generation payloads,14 materialized queries and original evidence/receipt. No LINK is admitted or trained; failed slot16 capture is retained as evidence.
- `validate_import(imported, expected_sha256)` reconstructs the full import; recomputing a seal cannot legitimize substituted data, teacher targets, different selections or changed source paths.
- `verify_tokenizer(imported, tokenizer)` requires the original pinned tokenizer files/measurements/template; re-renders all16 prompts, compares explicit encode and template-tokenize results (including Mapping), and decodes actual output token IDs exactly, LF included. Returns a separately sealed `EVENT_PREFIX_TOKENIZER_VERIFIED` receipt; it does not mutate the import or load a model/tokenizer.
- `seal`, `unseal`, `same` are canonical typed-data helpers, not signatures or attestations of remote identity.

Import schema `pcfl.event_prefix_import.v1`; status `EVENT_PREFIX_IMPORTED_TOKENIZER_PENDING`. Key fields: `evidence`, `replay_receipt`, `replay_receipt_sha256`, `selected_call_indices`, `selected_event_indices`, `rows`, `generations`, `queries`, `original_status`, `original_returncode`, `original_calls`, `format_scaffold`, `new_model_calls`, `fits`, `updates`, `native_custody_verified`, `full_contract_released`, `sha256`. The two custody/release flags remain false. Original `FORMATION_FAILED`, rc1,17 calls, zero fits/updates and null writer payload stay unchanged inside evidence. Prefix import is NOT full-bank completion or old-contract release.

`evidence` contains byte records `{utf8, sha256}` for fixed original files, outer failure/release receipts, original absolute-path source files and all68 request/render/raw/response sidecars; plus archive/source-tar hashes. Generation entries are exactly `{raw, sha256, origin: CHILD_NATIVE, capture_sha256}`. Queries/rows come from the unchanged materializer/admission functions, not an ideal bank. Checks retain e5 Z→Y via u and e7 B via f1; chronology is not ideal-edge numbering. Public histories are reconstructed from real transitions and exact earlier outputs; no later LINK, report or teacher text enters target construction.

## Main's exact-original-v3 receipt

Independent original-path replay schema remains the previously coordinated `pcfl.event_prefix.original_v3_replay.v1`. Exact fields besides `sha256`: `method=EXACT_ORIGINAL_V3_PATH`, `source_root`, `source_tar_sha256`, `formation_source_sha256`, `config_file_sha256`, `report_file_sha256`, actual `replay_result`, `model_calls=0`, `fits=0`, `updates=0`.

Consumed real Main receipt `/tmp/astra_pcfl_event_prefix_original_v3_replay_20260913_attempt1.json` in the final local structural smoke:

- Canonical seal: `56ca52a34fae625747423cd89a4829b91d8c5f15b422977e741ed98325bb1898`.
- Actual receipt FILE SHA256: `5659e39989a4dd26ca336c2787318bda43b1223bc7a52d67dbbf52b950b58dea`.
- Original source root: `/tmp/astra_pcfl_own_write_format_source_20260913_attempt1`.
- Source tar: `698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280`.
- Original v3 formation source: `9c1e4099ac0ad4d4f53c55d7a35b0d26e3b7dc6da0620f5321cca416e71e4669`.
- Config FILE SHA: `66704311982c8668744596b92588684b9c638252058d0f220a6effc16a2303b1`.
- Report FILE SHA: `595c3e65b8eaa1d73e270094d78f0e3a88c66b3b6a23b44b2677cd807692bd15`.

Receipt result preserves original config seal `5db340da5facedb385d2eaa735e4cce02ff8590dc10cfdda621fe42b5c673e2a`, report seal `e6b87cbbec498482e5f536156e10c020f9d1f40fe07bf10ffc1041b653f91bf4`, FORMATION_FAILED, local_replay_valid=true and false native/full custody. The importer does not invoke original replay or pretend current/relocated source is original v3. Main must bind receipt file bytes and canonical seal in the new manifest.

## Writer API and exact schedule

`organism_v6.pcfl_event_only_train`:

- `source_snapshot()` hashes actually loaded new importer/writer plus unchanged core/preparer/numerical writer/shared trainer/native actor. Bind this final snapshot in the new spec; do not reuse the old full-bank source map as the new one.
- `build_schedule(imported, import_sha256)` returns sealed fixed14+6 material/schedule. Sorted14 actual query requests form s00..s13. Frozen existing `_select_replay` chooses six distinct original first slots, with domain `[original report FILE SHA, EVENT_ONLY, S1, EVENT, replay]`; selected sources are s08..s13, copied into s14..s19. All eight underlying EVENT supports have count3. These are replay presentations, not new experiences/sources.
- Five deterministic support-disjoint four-example groups use batch seed0, no resampling. Each W0..W7 view appears once per slot per epoch; identical40-batch order for five epochs. Twenty slots × eight views × five epochs =800 presentations /200 updates. W8 never trains.
- `build_fit(imported, import_sha256, schedule, schedule_sha256, binding)` returns sealed `pcfl.event_only.low200.v1`; `validate_fit(fit)` revalidates import, exact schedule, lineage, recipe, source snapshot and endpoint.
- Binding exact caller keys: `authority_sha256`, `base_state_sha256`, `init_seed`, `dropout_seed`, `environment`, `tokenizer_receipt`, `sources`. New authority comes from Main's adopted scope. Base/seeds/environment/tokenizer remain identical to original manifest binding; init/dropout0, base tensor `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`. No descendant/init_adapter or user-selected LR is accepted. Build adds learning_rate=3e-5 internally.
- `encode_fit(fit, tokenizer)` first revalidates actual tokenizer, then calls unchanged numerical writer `_encode_corpus`: original memory-query public contexts/W0..W7, exact materializer child span targets, target+EOS supervision only, context masked, max512 with NO context/target truncation.
- `train_fit(fit, tokenizer, base_factory, out)` requires fresh output path, validates and encodes before dispatch to unchanged `_train_encoded`. `base_factory()` must return `(fresh_bf16_C0_model, exact_environment_dict)`. Existing loop checks no warm LoRA, actual base tensor identity, freezes base, fresh optimizer, rank8/alpha16/dropout.05, LOW3e-5,200 updates, finite/clipped gradients, save+failure receipts. It writes `event_only_scope_report.json` rather than a full-contract report. No numerical loop was copied or modified.
- `read_roster(imported)` returns28 items in existing readout shape `{id, request, view, seed, output_tokens}`: sorted14 requests at W0 then W8, seed0,2048 output tokens. Reuse exactly this roster for AUTH and NO_WRITE in two fresh processes; caller still binds roster digest/config and per-process custody. No actor/CLI/readout/reducer is implemented here.

`ENDPOINT`: W8 primary, exact service14/14, AUTH≥13/14, C0≤1/14, paired gain≥12/14; stop required. W0 descriptive,28 calls/arm56 total. Old17-query threshold untouched/not applied. This is EVENT-only acquisition from a named developmental prefix, not route/LINK/general-retention success, new formation, or syntax learning. NO_WRITE is not matched training compute. No automatic promotion.

## Example integration calls (not executed here)

```python
import copy
import json
from gpu import astra_pcfl_event_prefix_import as prefix
from organism_v6 import pcfl_event_only_train as event

evidence = prefix.load_evidence(archive_path)
replay = json.loads(replay_receipt_path.read_text())
imported = prefix.build_import(evidence, replay, replay["sha256"])
schedule = event.build_schedule(imported, imported["sha256"])
original = json.loads(evidence["files"]["manifest.json"]["utf8"])["binding"]
binding = {key: copy.deepcopy(original[key]) for key in event.BINDING_FIELDS
           if key not in ("authority_sha256", "sources")}
binding.update(authority_sha256=main_scope_sha256, sources=event.source_snapshot())
fit = event.build_fit(imported, imported["sha256"], schedule, schedule["sha256"], binding)
token_receipt = prefix.verify_tokenizer(imported, actual_local_tokenizer)
encoding = event.encode_fit(fit, actual_local_tokenizer)
roster = event.read_roster(imported)
```

Main persists exact byte hashes/seals in fresh import/prepare artifacts and later invokes `event.train_fit(fit, actual_local_tokenizer, fresh_C0_factory, fresh_fit_out)` only through its finite native stage. There is no executable CLI in these modules and importing them does not launch anything.

## Checks and remaining native work

Final command (repository root):

```bash
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_astra_pcfl_event_prefix_import test_pcfl_event_only_train -v
```

**26 tests PASS,7.945s.** Both new production and test files also pass AST parse and trailing-whitespace checks. Tests cover fixed archive selection; all16/8/14 joins; e5/e7; rejected missing LF/wrong action/length/timing/captures/source/receipt paths; bool-vs-int/forged rc/completion; resealed target/selection/custody mutations;14+6 replay/200-update disjoint schedule; unchanged masks/EOS/truncation; W0/W8 endpoint; parent/seed/source drift; no model factory on invalid or unqualified input; unchanged numerical dispatch/fresh output requirement. Archived token-table and synthetic mask tests explicitly mock file/template qualification; they are NOT installed-tokenizer or model/numerical evidence.

Actual fixed archive + Main's real receipt local structural smoke PASS. Import canonical seal `cc9e97a290933633d67c371625ae5cfffeb46bc8ca7c130279022868e98a545e`; schedule seal `0ffb61115df4dfe82e156bef6fb12ce6e64b70d42603cf0042e0d019784c170a`;14-query material digest `39e2d8d430e54ff3818967790cbe38eb15f41c014010f6647562b4c68ce02f8c`. Smoke fit used clearly synthetic authority hash, was not persisted or qualified/launched. Source archive `gpu_artifacts_local/pcfl_own_write_format_20260913_attempt1/evidence.tar` SHA `bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869`.

Unchanged dependency hashes at final check: core `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`; preparer `c07ba9b684299a8d6cf6c7b45bbdbb95ed6f3e04db9e8de6e926791610b55c61`; numerical writer `9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078`; shared trainer `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`; native helper `915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff`.

Main remaining steps: fresh scope/source/environment manifest; bind actual archive/replay receipt FILE hashes separately from seals; real local tokenizer files/template/output-decode recheck and160-item training encoding with zero truncation; immutable prepare artifacts; fresh C0 native fit and tensor/save receipts using unchanged numerical loop; cold AUTH/NO_WRITE W0/W8 readout with original strict scorer and separately verified14-query exact service. Keep existing readout required source/shutdown pins, plus new import/scope/source provenance; use explicit engine shutdown and owned release via Main's lifecycle, not a fabricated release flag here. Native paths in original evidence remain original, even when archive is read locally. New runtime pins refer to the new separately deployed scope. No old full-bank completion/prepare acceptance is substituted.

No implementation blocker remains. Actual native tokenizer/encoding, fit, cold readout, resource/time enforcement, custody and outcome analysis remain unexecuted responsibilities of Main. Incremental planned cost:0 new formation/model calls for import,1 fit/200 updates/800 training forwards and56 readout calls. Preserve historical17-call FAILED attempt including its LINK error and release receipts; no retries or alternate prefix selection.
