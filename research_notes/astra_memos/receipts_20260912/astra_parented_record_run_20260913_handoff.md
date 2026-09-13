# Parented-record DEV native lifecycle — 2026-09-13

**EDITSTOP. CPU-tested implementation; no native preparation, model/tokenizer load, GPU execution or launch performed. Main owns allocation, reservations/holder, native preparation and launch decisions.** Lovelace's core and every old helper remain unchanged.

## Frozen delivery

| File | SHA256 |
| --- | --- |
| `/tmp/astra_parented_record_run_20260913.py` | `54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8` |
| `/tmp/test_astra_parented_record_run_20260913.py` | `0542698181b7a820e56c30fd224ca4007b4893293309ff73cfef5ebdb8fb4116` |

Approved scope is the fixed protocol `research_notes/astra_memos/ASTRA_PARENTED_RECORD_DEV_2026-09-13.md`, SHA256 `bae29cfc48d9ae0922531d306bef1434bcc7296f2ae71a4ad6493da2a5dfb964`. Runner scope is `astra_parented_record_dev_20260913_v1`; one invocation handles one predetermined seed, not selection among learners.

Pinned executable dependencies:

- Final Lovelace core `/tmp/astra_parented_record_core_20260913.py`: `68ef29fcc162dbbf5fe1becf4c09b86ed5bc1f8a79e373276dd8ba3cda88e688`.
- Actual-memory lifecycle `/tmp/astra_real_record_memory_run_20260913.py`: `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`.
- Lower-LR recipe adapter `/tmp/astra_memory_lower_lr_run_20260913.py`: `80467204aa7ccb4a1cbf4f8d85c7be4e7347263f98f4f7b8fef5739980fcf413`.
- Transitive source/model/environment/parent and original retention bindings are verified through the frozen original memory plan and its formation/Level1 provenance. The new core additionally requires its two frozen `/tmp` dependencies and the pinned RuleGame source files, as listed in Lovelace's handoff. No dependency pin or imported helper constant was relaxed or mutated.

## Implemented flow

1. Closed specification and fresh-root native CPU preparation. Revalidate the selected original memory provenance; take **its original perception parent**, never its WRITE/LR0 descendant. Import the original parent's pinned old retention scores as noncontemporaneous. Bind the new core manifest, all 36 DEV/CONF namespaces and Main's supplied prior-exposure ID inventory; no CONF episode executes. Native preparation only rechecks the original retention prompt prefixes and template, not new formation outcomes.
2. Independent cold P and N formation workers from that same original adapter. The final core supplies the fixed contact, child restatement, two pre episodes and eight apply episodes, using exactly its request messages. Native callback preserves raw requests/responses, route, actual prompt/output IDs, sampling parameters and costs. Restatement uses 120 tokens/temperature .5/seed0; wake96/record192 use temperature0. No parent model calls. Backend/route/token failures escape the core as infrastructure failures, not scientific refusals.
3. Each arm's own source-gated apply records are projected with **the new core**, not the old projector. All raw admitted targets remain unchanged. Pre/contact/restatement/held material does not enter training cues or targets. Arm material is sealed before fitting; projection and material hashes are rechecked before the fit. The frozen memory encoder enforces the original masked cue, raw target plus EOS, truncation checks and eight-pass deterministic ordering.
4. Nonempty arms use the existing memory `fit_arm(..., "WRITE")` through an arm-specific plan view and the frozen lower-rate `candidate_config`: LR3e-5, eight passes, batch1, original learner seed, original parent, fresh optimizer. Existing fit/manifests/tensor checks are retained. A zero-admission arm writes an explicit `NO_WRITE` receipt, creates **no fit directory or training file**, and routes subsequent assessments to unchanged original tensors. It does not fabricate an LR0 stage.
5. Separate fresh workers assess ORIGINAL, P and N on DEV-held, then P/N on the original 48 held perception plus12canary items. No contact/restatement/history/retrieval state crosses into held inference; old retention settings/prefixes are preserved. There are no memory exact/paraphrase readback calls in this campaign.
6. Once-only collection verifies closed stage inventories, raw/core replay joins, fit provenance, explicit worker exit rc0 plus owned-release receipts, call/update totals and live collection-time group/GPU absence. It reports formation/apply yield, fields/format/raw failures, held P-minus-N and changes from INITIAL, per-arm source-triple novelty, dose/token costs, NO_WRITE states and itemwise old-retention gains/losses. It never sets an efficacy gate, automatic pass or H1/H2 promotion.

Stage order: `P_formation`, `N_formation`, `P_fit` if nonempty, `N_fit` if nonempty, `ORIGINAL_held`, `P_held`, `N_held`, `P_retention`, `N_retention`. Generation stages live under `ROOT/run/STAGE`; fit stages live under `ROOT/arms/P-or-N/run/WRITE_fit` to reuse the unchanged writer. The two training plan views do not redirect any input to the other arm.

## Closed specification contract

Exactly these top-level keys are accepted:

```text
runner_sha256
core: {path, sha256}
protocol: {path, sha256}
memory_runtime: {path, sha256}
lower_runtime: {path, sha256}
memory: {root, plan_sha256}
prior_episode_ids: {path, sha256}
seed
gpu_index
gpu_uuid
expected_boot_id
lease_end
```

Paths are absolute deployed paths. `seed` is an integer 0/1/2; fit seed is fixed to it, not a configurable extra key. The four source records must have the exact pins above. `prior_episode_ids` is a pinned JSON list of strings; Main supplies all known previously exposed task/episode IDs. The runner additionally unions the original formation episode IDs and the core checks its frozen earlier namespace. This verifies disjointness against supplied/bound exposures, **not completeness of a global exposure census**, unseen rule classes or absence of base-model knowledge.

The memory provenance uses the original completed SEQ153 memory root for that seed, only as a source of original-parent/retention/configuration custody. Exact plan pins:

| Seed | `memory.plan_sha256` |
| --- | --- |
| 0 | `66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1` |
| 1 | `9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b` |
| 2 | `48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea` |

Prior memory descendants/results are neither treatment initializers nor outcome gates. The parent scores used for old retention come from the original perception parent's collection, not the lower-LR or high-LR memory readouts.

## Runtime ownership, bounds and Main prerequisites

- Per seed at most300 calls and256 updates; per-arm formation42, held32/state and retention60/descendant. Nonempty fits are at most128 updates each. Main runs all three fixed seeds; this runner does not certify complete cohort execution.
- **Conservative continuous wall-clock cap:** 7200 seconds starts at entry to `prepare`, before its source/native checks, and persists in the plan across controller, workers and collection. Queue/idle time after preparation also consumes that clock. Preparation is bounded separately; collection has at most180 seconds including its entry setup, and must finish before the same whole-work deadline. No phase restart resets it. Prepare only when Main is ready to use the reserved slot.
- Empty `CUDA_VISIBLE_DEVICES` is required for prepare/controller/collect. Main's external holder keeps the assigned UUID reserved across workers and final collection; only worker subprocesses receive that UUID. The runner intentionally creates no competing reservation/launcher framework. Main must perform the established all-process/queue/reservation checks and keep ownership through collection.
- Node boot and a conservative six-hour lease finish margin are checked. Each stage performs a fresh GPU-vacancy check, spawns an isolated process group, binds PID/PGID/start ticks, records return code, invokes the frozen owned-group cleanup, checks group absence/GPU vacancy and seals the stage only on success. Cleanup/query time and collection time are reserved from the shared deadline. Failed release stops/preserves; there are no retries.
- Deploy the complete pinned source snapshot and transitive dependencies used by the original memory plan, not just the two RuleGame files. Use the same native Python/environment authenticated by those original plans, and set `PYTHONPATH` to that source snapshot for initial preparation/controller/collection. Worker subprocesses explicitly receive the pinned source path. Required old roots, collection claims and parent adapters must remain available at their bound paths.
- **Outstanding native prerequisites:** Main's deployed file/spec/input pins, exhaustive prior-ID file, source/Python/model environment checks, actual native tokenizer/mask preparation, allocation/reservation/lease checks and native execution. None is certified by the CPU tests. No core API blocker remains; the final core's explicit protocol-path option is used.

CLI interfaces for Main, not executed here:

```text
python -B /tmp/astra_parented_record_run_20260913.py prepare --root ROOT --spec SPEC --spec-sha256 SHA --allow-native
python -B /tmp/astra_parented_record_run_20260913.py controller --root ROOT --plan-sha256 SHA --allow-gpu
python -B /tmp/astra_parented_record_run_20260913.py collect --root ROOT --plan-sha256 SHA --completion-sha256 SHA --out FRESH_OUT
```

`prepare` returns `plan_sha256`; controller returns `completion_sha256`. The external holder should record controller exit and wait for controller PID termination before invoking collection, while retaining its reservation. Do not invoke internal `worker` manually; it checks the bound launcher identity and fresh process group. Controller and collection claims are exclusive/no-retry. Failed or expired attempts need preservation and Main's next decision, not an automatic new deadline/root.

## CPU validation and limits

`python3 -B /tmp/test_astra_parented_record_run_20260913.py -v`

**27 tests PASS in17.309s.** Tests exercise the lifecycle seams with the final CPU core and frozen native-response validator, synthetic DEV child replies, toy tokenizer, mocked fit/native/process/GPU boundaries. Full synthetic admission yields300calls/256updates; zero admission yields212calls/zero fits/updates while retaining all required held/retention assessments. Tests cover own-arm source/target handoff, excluded contact/restatement context, cold held routing, fixed sampling, source/training/response tampering, closed specs, independent plan/retention binding, consumed deadlines, original fit-view forwarding, once collection, lease/boot mismatch, process timeout, failed release and unchanged helper globals.

An initial test invocation hit a one-second tool timeout; subsequent complete runs passed19, then25, then the final27 tests. This is not a native failure. No model, real tokenizer, native collector, GPU, network, remote operation or Git command was invoked. No original helper/core test suite was rerun; tests here cover the new integration rather than duplicate Lovelace's unit tests. Fake fit manifests bypass tensor arithmetic in the integration fixture; actual native fit/tokenizer/mask/tensor behavior remains a Main-side prerequisite, with the frozen checks retained in production paths.

Only the new runner, its test and this handoff were authored. Test fixtures use isolated disposable `/tmp/astra_parented_runner_test_*` directories. No repository, old sidecar, core or manuscript file was edited. This is implementation delivery only, not launch authority, an experimental result or scientific promotion.
