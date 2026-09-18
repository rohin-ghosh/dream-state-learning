# R159 executable API — Main-GO required

## Frozen receiving source

`/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1/preparation/runtime_generation2/source`

Runtime generation2 is the non-material timestamp-custody repair. Generation1 and its original strict-COMMIT-age rejection remain preserved. PLAN/FREEZE/task/prompt/scoring bytes and12-slot/672-call semantics are unchanged. Use `runtime_generation2/CPU_GATE.json` and `runtime_generation2/SOURCE_MANIFEST.json`, not the earlier helper's gate.

Immutable PLAN.json and SOURCE_MANIFEST.json are adjacent to `source`. Use existing `/localhome/local-rohing/v2/venv/bin/python`, `PYTHONDONTWRITEBYTECODE=1`, and `PYTHONPATH` equal to receiving source. Bind the actual cohort with a separate execution config; do not rewrite source/plan.

## Commands

All commands are `python -B -m gpu.orch_r159_matched_evaluation ACTION ...`.

- `freeze --output NEW_PRIVATE_DIR`: CPU-only (`CUDA_VISIBLE_DEVICES=`), writes hidden tasks and metadata FREEZE. Already done; preserve it, do not choose/refreeze tasks after checkpoints.
- `gym-selftest --freeze FREEZE.json --output NEW_PRIVATE_DIR`: actual installed-generator/parser/verifier CPU smoke. Metadata only returns; no model calls. Already passed on the receiving helper.
- `plan --freeze FREEZE.json --output NEW_PLAN.json`: immutable12-slot/672-call policy. Already frozen; reuse exact bytes.
- `validate --config EXECUTION.json --go MAIN_GO.json`: CPU metadata/provenance gate. Requires `R159_MAIN_GO_SHA256` binding exact GO bytes; no CUDA/reservation.
- `dispatch --config EXECUTION.json --go MAIN_GO.json`: same GO binding; verifies custody, acquires original physical lock, scans vacancy, charges a new-campaign slot, launches/waits for a fresh timed evaluator. Requires full3600s plus15s runway. Invoke once per available fixed slot; this is not a child watcher/copier. Slots0/1 may operate concurrently; a separate lock serializes budget reservations.
- `evaluate --config EXECUTION.json --go MAIN_GO.json`: dispatcher-internal only; also requires `R159_EXECUTION_SHA256` and exact existing reservation. One checkpoint/fresh process, empty one-item context, no parent/file tools, stripped provider/parent environment, read-only model before/after, no feedback into child/sleep/inbox.
- `status --plan PLAN.json`: new ledger metadata totals, failures/unresolved reservations and missing controls. Never read private corpus/results/logs in Main/parent scope.

## Execution and GO

`API_SCHEMA.json` lists exact fields. References are `{path: absolute_regular_file, sha256: exact_bytes_hash}`. Schema below is `R159_MATCHED_EVALUATION_V1` unless native.

Execution file lives under `CAMPAIGN_ROOT/control`; root is exactly `/localhome/local-rohing/orch_r159_matched_evaluation_20260917_attempt1`. `campaign` references frozen PLAN; `candidate` references copied metadata. `physical`0/1 and `gpu_uuid` must match node2. `source_root`/complete `sources` come from SOURCE_MANIFEST. `model_dir` is existing local frozen Qwen cache. `python`/`python_sha256` pin the existing interpreter (venv symlink permitted). `service_path` is the existing privileged scanner service path. Finite `hard_end_unix`, `lease_end_unix`, `source_read_end_unix` must satisfy node2 six-hour lease margin and current source authority.

`node2_authority`: Main metadata `{schema,node:"node2",campaign_sha256,hard_end_unix,lease_end_unix,physical_slots:[0,1]}`. Node5 authority cannot substitute. `old_terminal` binds actual R158 BOUNDED_PHASE_FINISHED under the original root; `old_terminal_identity` binds its controller `{pid,uid,start_ticks,boot_id}`, required gone. Actual physical locks/vacancy scan still apply.

`cpu_gate` references CPU_GATE with PASS/exact helper/test hashes. `builder` is a new actual-provenance object `{status:"CPU_AND_PROVENANCE_PASS",campaign:PLAN_REF,cpu_gate:CPU_REF,created_unix:...}` after custody checks and a dated Builder receipt. This preparation does not fabricate that actual-cohort gate.

GO is exactly `{schema:"R159_MATCHED_EVALUATION_V1",status:"MAIN_GO",execution:EXECUTION_REF}`; `R159_MAIN_GO_SHA256` must equal its exact hash. CPU PASS or this note is not GO.

## Candidate/source custody

Candidate has schema, `arm` (`parented_learning`, `parented_frozen`, `unparented_learning`), integer `milestone`0/1/2/4, refs `cohort`, `initialized`, `capacity`, `initial_commit`, `manifest`, `source_custody`, and original `source_commit_path`. All candidate/metadata copies are under new campaign `inputs`. Preserve original bytes and nested remote path strings; never rewrite COMMITs.

`manifest`: unchanged R130_CHECKPOINT_MANIFEST_V1 `{schema,adapter_path,commit_path,commit_sha256}`. Local adapter/COMMIT paths remain under inputs. Native COMMIT must be R125_NATIVE_CONTINUITY_V1 as produced by R150. Original paths must match that exact cohort arm's `checkpoints/initial` or `sleep_000001/000002/000004`. Only adapter payloads are opened. Initial clone hashes/experiment binding must match; frozen-arm checkpoints retain step0 adapter and zero optimizer steps.

`capacity` copies actual RESULT.json; its hash/schema matches INITIALIZED.initialization_validation. PASS/restoration VERIFIED, zero generation/updates, no stream writes/scientific evaluation or error fields. INITIALIZED binds actual cohort and initial COMMIT and zero initialization calls/updates. COMMIT alone never qualifies.

`source_owner_authority`: schema, `status:"SOURCE_OWNER_ADMITTED"`, `cohort_sha256`, `source_roots` map all three arms, `source_root` equals cohort.common.source_root, `read_end_unix`, and `initializer_lifecycle` ref whose `service_returncode` is0. Execution source-read deadline matches this ceiling.

Optional recovery: when cohort.common.initialization_source exists, INITIALIZED carries that same original ref. Authority adds local-input refs `initialization_source_copy` and `initialization_commit_copy`. Their copied bytes match the source ref/donor COMMIT hash. INITIALIZED.recovered_initial_state_before_validation equals observed_initial_state; observed checkpoint_file_hashes equal restored initial and donor hashes. Original and copied COMMIT creation timestamps must match. No old-root paths are opened or altered. Untouched initialization may predate the freeze only with this exact recovery proof and the trusted zero-use/exposure custody described below; initialization age alone is not contamination.

`source_custody` exact fields: schema, `cohort_sha256`, `source_root` (arm's original life root), `source_commit_path`, `commit_sha256`, `manifest_sha256`, `checkpoint_boundary` (milestone), `source_owner_authority` (same ref), `timestamp_custody` (same ref as authority.timestamp_custody), `source_read_end_unix`, `adapter_only:true`, `optimizer_rng_read:false`, `history_read:false`, `source_written:false`. Main must obtain this exact hash-bound receipt from the authorized source reader; the evaluator does not invent source custody or copy histories.

## Repaired trusted timestamp contract

Every source-owner authority now includes `timestamp_custody`, referencing copied metadata under campaign `inputs`. It is transitively bound by the exact execution/Main-GO and also by source_custody. Schema details: `runtime_generation2/TIMESTAMP_CUSTODY_SCHEMA.json`. Do not fabricate timestamps or substitute planning placeholders; no actual Main enrollment authorization has been issued here.

The timestamp receipt uses schema `R159_TRUSTED_TIMESTAMP_CUSTODY_V1`, status `TRUSTED_SOURCE_OWNER_ATTESTED`, and exactly these other fields:

- `campaign_sha256`, `freeze` (the original exact reference), `cohort_sha256`, `initial_commit_sha256`, `initialized_sha256`, `initializer_lifecycle_sha256`: must equal the other Main-bound provenance artifacts.
- `initial_created_unix`, `initialized_unix`: exactly the existing native timestamps, never rewritten. `enrollment_unix` is the trusted Main/source-custody enrollment authorization timestamp; `observed_unix` is the source-owner observation covering all supplied histories. All are finite positive numeric UTC Unix seconds, not strings/booleans/unknowns; initial creation <= initialization <= observation <= current time, and original freeze < enrollment <= observation.
- `saved_initial_generation_calls:0`, `saved_initial_optimizer_updates:0` (actual integers), `saved_initial_training_exposure:false`, `saved_initial_evaluation_exposure:false`: certify the original saved initializer was untouched before recovery, not that the subsequently born learning arms never trained. Existing exact saved-source provenance, zero-update/generation INITIALIZED, capacity PASS and clean exit remain independently mandatory.
- `arm_exposures`: exactly all three arms, each mapping exactly `birth`, `train`, `evaluation` to a local-input metadata reference. Every referenced record has schema `R159_FIRST_EXPOSURE_V1`, exact cohort/arm/kind, `coverage_complete:true`, and the same `observed_unix`. `status:"OBSERVED"` requires finite numeric `first_unix` strictly after the original freeze and no later than observation. `status:"NOT_OCCURRED"` requires `first_unix:null` and complete coverage through observation. Missing/unknown/incomplete histories are refused; null is not an inferred absence. The trusted source reader, not Main's language model, must establish first-event completeness from source custody.

For an initial COMMIT at/before the freeze, absence of the exact optional saved-initial recovery proof is still a refusal. A new freeze or changed plan is categorically refused by their original SHA256 pins. No task selection, seed, prompt, scoring, cap, model or saved-state bytes change. Runtime-generation2 remains gated on Main supplying the actual admitted cohort provenance and exact GO. Candidate5's initial3 metadata templates are in `candidate5_initial3_templates/MAIN_HANDOFF.md`; they are not birth/admission/copy authority.

## Failure/visibility contract

### Non-material runtime-generation3 interval extension

Exact `OBSERVED` (`first_unix`) and `NOT_OCCURRED` (`first_unix:null`, positively attested complete history) remain unchanged. An event may instead use `status:"OBSERVED_INTERVAL"`, replacing `first_unix` with `first_earliest_unix`, `first_latest_unix`, and `source_evidence`. No mixed exact/interval fields are allowed. Both bounds must be finite numbers, not booleans/strings, and satisfy `original_freeze < earliest <= latest <= common_observed_unix`. All three arms still require all three kinds: birth, train, evaluation; matching cohort/kind/arm, complete coverage, and common observation bindings remain mandatory.

`source_evidence` is a nonempty list of at most16 distinct `{path,sha256}` references to regular, non-symlink metadata files under the campaign's `inputs/`. Hashes are verified during custody validation and rechecked throughout evaluation, just like the first-exposure receipt itself. Missing, changed, duplicate, unbound or outside-input witnesses fail. Witnesses are source-owner evidence, not held evaluator outputs; no hidden prompt/answer/score/private log content is required or authorized. Main's attestation covers its exclusive-root admission/birth custody and retained contiguous journal/custody history, not an impossible guarantee of machine-wide absence of compromise. Existing UNKNOWN observations and original generations are preserved, never relabeled by this repair.

The extension permits verified BIRTH/native-evaluation brackets without substituting filesystem times or dispatch intent for exact first-item times. Original04:52:56 freeze bytes/selection/seed,12 slots/672 calls, base/LoRA/scoring/claims/visibility remain unchanged. Only a fresh immutable runtime_generation3 may use replacement helper/test pins. No copy/enrollment/evaluation permission follows from the repair or its CPU gate.

Private per-call reservation/raw/scoring records stay sealed. Dispatcher verifies receipt hashes without reading score contents; parent return fields are status/counts/paths/hashes/identities/control completeness only. Every failed/ambiguous reservation charges56 and never replays. Missing scheduled controls are incomplete evidence, not score-selected success. No migration or increase of old campaign caps.
