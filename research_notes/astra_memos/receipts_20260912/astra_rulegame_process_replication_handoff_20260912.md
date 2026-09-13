# Process-write FIT-seed replication — EDITSTOP, September 12, 2026

## Frozen delivery and Main decision

**27 CPU mock tests PASS in74.044s. EDITSTOP: code/tests immutable.** Only the three assigned sidecars changed. No native/model/tokenizer/GPU/SSH/network/Git execution or repository/adjacent edits. Main alone tests natively, stages and launches.

- Driver `/tmp/astra_rulegame_process_replication_20260912.py`: **96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd**.
- Tests `/tmp/test_astra_rulegame_process_replication_20260912.py`: **b6af0ad986880fe3af6987217d75813425819613549ab9577d131fd0c1096fc4**.
- This handoff supersedes the initial design. Main explicitly approved independent seed-aware phases and replaced45min with **MAX60 aggregate A40-min/seed**: write1200 + write collection300 + readout1800 + readout collection300 seconds. **No combined coordinator, clipped-stage policy, run-seed command or automatic phase launch exists.** Separate preparation/launch/release, as inherited; CPU gaps after verified release are elapsed wall, not GPU reservation. Collections are not implemented here.

**Launch prerequisite still outstanding: collector adaptations for these new protocols/APIs. Main requested no launch until available.** Old frozen collectors are not silently compatible. This is an engineering/custody dependency, not a new C11 or scientific-review gate.

## Frozen scope and interpretation

Exactly additional FIT seeds0/1 on the same accepted seed2 process-V2 four wakes, two per arm. Original slot/candidate/Main assessment/context/target/material bytes are inherited from the explicitly pinned completed seed2 write root. New independent fresh-base P then A per seed; no seed2 or cross-arm warm start. Only TrainConfig.seed changes: rank8/alpha16/dropout.05/AdamW LR1e-4/epochs12/updates12/batch2/accum1/no-pack/maxlen4096. Same natural unequal tokens; no target matching, drops/splits/truncation, new formation, later-slot replacement, prediction correction or teacher generation.

Each completed new pair gets separately prepared and launched fresh-process OFF/P_ON/A_ON readout. Generation seed stays20260912 (not FIT seed), temperature.7, existing rules2–5, fixed quiz24/invalid-or-absent zero, <=96 calls/27600 generated-token ceiling. Per-task reset, current-task history only, no parent/restatement/prefix/material in readout worker inputs, no online updates. Source `run_evaluation` and its native replay semantics remain unchanged. Both seeds use fresh OFF, never seed2's OFF. No automatic retry or favorable replacement; a failed phase preserves partial artifacts and has no completed science result.

**Purpose: repeatability of quiz/persistent-output contrast, not learned conditional prediction/internalization.** Main reports seed2 raw audit PASS95calls/268members: quiz P12/OFF7/A6; valid pre-TRY P/A12 versus OFF8; correct P/A9 versus OFF6. P predicts F on all12, correct9 exactly its all-F baseline; all cells' conditional accuracy.75. Global unique triples P4/A3/OFF8 differs from task-local sums12 each. Faithful records P5/A10/OFF9, chiefly P dropping actual F to null. These are Main-supplied audited findings, not independently recounted here; no implementation tuning follows from them.

Main-side full registered criterion (not implemented as a runner gate): **P quizcorrect > both comparators; invalid/absent quiz tasks <= each comparator; valid_preTRY > both AND correct_preTRY > both.** Reference is notebook22:56:58 entry and ASTRA_PROCESS_READOUT_V2 memo, as identified by Main. Seed2 fails it unchanged. No record-harm tolerance: record loss is separately reported, never waived or used to invent a replacement criterion. Runner records automatic_promotion=false and remains descriptive, with no C11 enforcement or scientific-pass Boolean.

## Implementation and stable collector-facing API

Hash-checked imports preserve original writer `a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9` and process readout `46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46`. Further inherited dependencies remain needed on host: record writer-v2 `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c`, record readout `120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde`, and exact original process source tree. New plans include dependency/source pins. Historical files are neither edited nor runtime-monkeypatched. Local phase methods are explicit static adaptations; immutable seed-independent helpers are called normally. CPU tests assert normalized AST identity of the readout worker algorithm.

- `WritePhase(fit_seed)` at driver:85. `prepare(reference_root, reference_plan_sha256, out, device, deadline, lease_end)` at:134 validates the completed original seed2 pair through frozen accepted_writes(native=True), including native capture/token/mask/EOS custody. It copies exact accepted material JSON bytes—including corpus/audit/provenance into separate directories—without rebuilding/exporting targets. Source/root/model/interpreter derive from the accepted reference; device must match that reference (currently2). Final Main candidate and context-distillation review remain bound. Reference adapters are custody evidence only, never initialization.
- `WritePhase.checked_plan(root, sha)` at:187 returns `(root, plan, diagnostic, exporter, trainer)`. New write protocol `rulegame_process_fit_seed_write_v1_20260912`, material protocol unchanged `rulegame_grounded_process_pair_v2`, plan schema2 with `fit_seed`, `replication`, and `reference_write` root/plan/result pins. Config, source, material, reference and seed are rechecked. `validate_fit` at:210 validates actual recipe/train_meta seed, counts/losses/trainability/saved tensor layout/forward receipts. `write_pair` at:295 uses inherited1200/600/140 bounds and returns old paired-success status plus new protocol/fit_seed/automatic_promotion=false. No readout call follows.
- `ReadoutPhase(fit_seed)` at:339. `prepare` at:385 accepts the new write-root/hash plus **this sidecar's path/hash**, fresh readout root and separately supplied deadlines. `checked_plan` at:409 returns `(root, plan, diagnostic)`; `accepted_writes(plan, native=False)` at:454 binds the exact new seed-aware writer and same-seed completed pair. New readout version `rulegame_process_fit_seed_readout_v1_20260912`, schema2 with fit_seed/replication and immutable adapter/lineage pins. Protocol adds replication_fit_seed while preserving generation seed/tasks/settings. `evaluate` at:551 uses inherited1800/600/140 bounds. Worker dispatch is `_readout-worker`; write dispatch `_write-worker`.
- Collector must instantiate the right phase using the **pinned** plan's fit_seed, then use these methods. There is no module-level legacy checked_plan shim. Readout `audit_cell`, `process_metrics`, `accepted_writes`, and usual per-cell data/manifest/native_audit/provenance/supervision files remain available through the phase object. Write fits/forwards/trainability/manifest/receipt paths and material layout remain inherited. Both phases' results retain explicit fit_seed and no automatic promotion. Do not relabel seed-aware plans as historical seed2 protocol.
- `process_metrics` at:369 preserves every original metric/denominator and adds `persistent_output_diagnostics`: valid T/F prediction counts, all-F correct counts on valid-predicted and all-executed probes with separate denominators, globally unique triples and sum of task-local unique triples. Original faithful/actual/allotted12 record counts and fractions remain separate. No new model request, score gate or mechanism inference.

## Exact CLI — separate Main-operated stages

No shell loop or chaining is supplied. Choose SEED0 or1 explicitly; use the same reference pins for both. Each write and readout output is a distinct fresh sibling of the reference/write root, not nested in protected source/model/material roots. Each phase deadline must leave its full inherited controller window; no clipping. Lease-end is Main's real timezone-aware expiry, with six-hour margin. Retain the native venv spelling; do not resolve its symlink.

```bash
export SOURCE="${PROCESS_SOURCE:?exact original process source-root}"
export PYTHONPATH="$SOURCE" ASTRA_SOURCE_ROOT="$SOURCE"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
DRIVER=/tmp/astra_rulegame_process_replication_20260912.py
DRIVER_SHA=96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd

# CPU/native-tokenizer prepare; no GPU model load. SEED must be0 or1.
"$NATIVE_PYTHON" -B "$DRIVER" prepare-write --fit-seed "$SEED" \
  --reference-write-root "$REFERENCE_WRITE_ROOT" \
  --reference-write-plan-sha256 "$REFERENCE_WRITE_PLAN_SHA256" \
  --out "$NEW_WRITE_ROOT" --device 2 --deadline "$WRITE_DEADLINE" --lease-end "$LEASE_END"

# Main launches only after collector adaptation is available and native acceptance.
"$NATIVE_PYTHON" -B "$DRIVER" write --fit-seed "$SEED" \
  --root "$NEW_WRITE_ROOT" --plan-sha256 "$NEW_WRITE_PLAN_SHA256" --allow-gpu

# STOP here for separate terminal collection/full release. No automatic next stage.
# Then independently prepare the readout using returned write hash/new root:
"$NATIVE_PYTHON" -B "$DRIVER" prepare-readout --fit-seed "$SEED" \
  --write-root "$NEW_WRITE_ROOT" --write-plan-sha256 "$NEW_WRITE_PLAN_SHA256" \
  --write-driver-sha256 "$DRIVER_SHA" --out "$NEW_READOUT_ROOT" \
  --deadline "$READOUT_DEADLINE" --lease-end "$LEASE_END"

# Separate Main vacancy/launch supervision; no inherited reservation assumption:
"$NATIVE_PYTHON" -B "$DRIVER" evaluate --fit-seed "$SEED" \
  --root "$NEW_READOUT_ROOT" --plan-sha256 "$NEW_READOUT_PLAN_SHA256" --allow-gpu
# Separate readout terminal collection/full release follows, never automatic.
```

Reference is Main's completed process write-v2 attempt1, plan `67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44`, source `4c3064c1c3eef068951e9c3b2ca46630754564e7`; not record-write-attempt2. No new root/plan/launcher hash is invented. Public run commands require --allow-gpu; worker specifications and private dispatch also require it and verify exact plan/spec bytes.

## Tests and remaining native acceptance

**Actual CLI regression (not argv-equality alone):** both seeds' full pipelines enter the real `main(argv)` argparse parser and real phase handlers for all14 controller/worker commands (write + two write-workers + evaluate + three readout-workers per seed). Forty missing-required-option variants reject with argparse exit2 before dispatch. Both prepare-write and prepare-readout commands also parse and execute their real preparation handlers for each seed. Phase constructors are routed to the test's mocked-native objects; model loads/training/supervision remain CPU mocks, while parser and dispatch are not mocked. No subprocess/native launch is claimed. The actual emitted private commands include every option their respective parser requires; hidden write/readout subcommands are distinct.

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES='' ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state \
python3 -B -m unittest discover -s /tmp \
  -p test_astra_rulegame_process_replication_20260912.py -v
```

27 tests: both complete mocked seed pipelines with fresh P/A and OFF/P/A; unchanged raw material/seed2 recipe/generation seed; config/seed/metadata/reference/parent-context/adapter/promotion tamper including resealed material; finite-loss/count checks; failed second fit/middle readout with partial preservation/no aggregate/no retry; GPU opt-in; fresh roots/symlinks; full separate deadline and six-hour margin; invalid-zero fixed24; parent-free worker file access; original readout worker AST; release failure; no automatic science criterion or phase chaining. Mock legacy training fixture's hard-coded summary seed is corrected in the test double to cfg.seed; no production receipt is rewritten. Tests write only temporary mock artifacts, not native runs.

Outstanding: Main native tests with ASTRA_SOURCE_ROOT set to actual immutable source; native reference material/token/identity checks and saved adapter semantics; **write and readout collector adaptations with finite-weight scan/custody/full PID-PGID-session/GPU-UUID/proc/queue release and300s each**; exact launcher/plan pins; real lease/reservation checks. Existing worker cleanup verification is not a substitute for those full-release collectors. The60min prospective aggregate assumes separately enforced collection bounds; this sidecar alone enforces only1200s and1800s controller bounds. Report observed release/collection and elapsed wall separately; do not claim60min externally witnessed reservation until measured. No native run or new science result has occurred here.

Context-distilled teacher-influenced own wakes are not raw-RECORD objectives, clean lineage or scaffold-free cognition. Origin remains UNRESOLVED_LOCAL_HASHES_ONLY; no operational parenting, G3/P1/G5/H1/H2, adult learning, internalization or scientific promotion follows from this plumbing or CPU tests. No new C11 guard. **EDITSTOP; Main sole operator.**
