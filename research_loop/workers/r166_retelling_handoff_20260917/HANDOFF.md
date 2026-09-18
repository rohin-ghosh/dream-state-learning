# R166 C1–C5 corrected-retelling handoff preparation

September 17, 2026, 07:49 UTC. Scoped non-material implementation of Main's
Rohin150 directive. Owned files: new `gpu/orch_r166_retelling_handoff.py`,
new `tests/test_orch_r166_retelling_handoff.py`, and this new receipt directory.
No old source, parents, coordination files, live lives, services or GPUs changed.
No remote reads/writes, signals, admission scan, GO, native restart or R162
observation occurred during this task.

## Ready now / explicitly not ready

The **CPU-only `stage`, `verify`, and `prepare` commands are implemented**.
`stage` may inspect the current exact R157 owner without stopping it; it writes
only a new isolated source/control root. `prepare` requires all three recorded
old process PIDs absent and the latest journal record to be a complete saved
sleep with paired intents. It then preserves and validates that exact boundary.

**This is not an activation executor. Do not retire a native for this artifact
alone.** Main must first arrange the separately authorized retirement and
R166-aware strict supervisor. The original R157 `handoff`/`validate_resume`
cannot be invoked unchanged: they require the old deadline-extension delta
and original unpatched source. The emitted strict command is explicitly marked
`executable_as_is=false`; it is an envelope template, not a launch instruction.
The CLI deliberately exposes no `handoff`, `supervise`, `contained-native`,
signal, or GO action. This boundary avoids disguising an admission-validation
bypass as reuse of R157. No rollout or actual saved-state validation is claimed.

## Exact pins and tests

| File | SHA256 |
| --- | --- |
| gpu/orch_r166_retelling_handoff.py | 6940a5c53b8a6e766a7a0ca14d5231e068437cbfa2fa5f7080c3fe45ac7a7c0c |
| tests/test_orch_r166_retelling_handoff.py | c4cbd3f7fa9d53a3657bfe8a2007edee557f24df20108a9d9263b8cda681147f |
| gpu/orch_r166_corrected_retelling.py, unchanged | 1b6e173795b277c39cb4c6b29519716fd36feebe21e99f39cecaa3ec6c145f55 |
| gpu/orch_r157_community_wall_extension.py, unchanged | 7e0fcf8c35b72fc6fa01738446d51d8fe9e996afefae66236dd2d5c47d6a2419 |
| CPU_TESTS.log | 42330f7f9b39d9f486f6caf3bf9d47a35ac4ac3673d7eee95b09d79f2e31a404 |

**218 tests + 256 subtests PASS in 40.10s**, including 18 new handoff tests.
Exact invocation:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/r136-pytest-support:$PWD \
python3 -B -m pytest -p no:cacheprovider -q \
  tests/test_orch_r166_retelling_handoff.py \
  tests/test_orch_r166_corrected_retelling.py \
  tests/test_orch_r157_community_wall_extension.py \
  tests/test_orch_r125_continual_native.py \
  tests/test_orch_r125_stream_journal.py \
  tests/test_orch_r153_community_runtime.py
```

Tests exercise the actual patch function, complete synthetic journal/intent and
checkpoint preservation, exact plan equality, CPU provenance, source tampering,
orphan intents, live-owner refusal, all five physical identities, strict command
construction, control exclusions, and absence of launch/signal actions. Full
prepare tests mock the Torch checkpoint subprocess and node identity/admission
validation; they are not a receiving-host or real-checkpoint test. Actual
`prepare` invokes the staged original guard validator and actual CPU Torch
checkpoint verifier before producing PREPARED.json.

## Minimal staging invocation

On node5 `[REDACTED_HOST]`, as UID2524, from a separately pinned operator source
tree containing the four source/test files in CPU.json (no edits to running
source). Main supplies the current config and actual native PID, not the stale
birth PID in R157's table. Example for C1, repeated independently for C2–C5:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH="$PINNED_OPERATOR_SOURCE" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r166_retelling_handoff stage \
  --agent C1 --config "$EXACT_CURRENT_R157_GUARD" --native-pid "$EXACT_CURRENT_NATIVE_PID" \
  --directive "$PINNED_ROHIN150_DIRECTIVE_MD" --cpu "$PINNED_HANDOFF_CPU_JSON" \
  --output /localhome/local-rohing/orch_r166_retelling_C1_20260917_attempt1
```

`verify --output /localhome/local-rohing/orch_r166_retelling_C1_20260917_attempt1`
rechecks source/request provenance without signals. After Main's separately
authorized exact saved-boundary retirement, the same CPU-only interpreter/env
can run `prepare --output ...`. Never use prepare to force a running life to a
boundary. It cannot do so and refuses any still-present recorded PID, including
a stopped process or PID reuse. A partial failed preparation remains preserved;
its existing control directory refuses overwrite/retry.

## Continuity and effective policy

- Original config, plan, lease, parented COMMUNITY provenance, birth and source
  inventories remain pinned and unmodified. C1–C5 exact roots/UUIDs/minors only;
  original Astra parenting provenance must match the original birth config.
- Only the copied native `prepare_sleep` invitation site changes, through Main's
  exact root-scoped `patch_source`; all other native AST and original source
  bytes remain unchanged. Three new files are added: handoff helper/test/policy.
- Eligible variants: free_distillation and parent_guided_distillation only.
  Unparented, frozen, no-sleep, reread, no_distillation, unrelated roots and
  recovery/matched-cohort plans refuse instead of silently converting controls.
- Effective plan only relocates source/startup paths. If the old plan still
  carries an R157 wall-extension instruction, a matching actual WALL_EXTENDED
  record must exist in the verified journal before removing that already-used
  instruction from the prospective plan. Its original bytes and authority are
  retained in original-plan/policy receipts. No extension is replayed, and no
  wall, lease, seed, invitation-in-original-plan, birth, readout revision,
  NEW16/rehearsal1/lambda0.25, or other recipe field changes.
- Full stream copy/record-intent chain and selected checkpoint directory are
  preserved and frozen. Actual CPU verification restores the original stream
  envelope, checks checkpoint bytes, model/history/experiment identity, AdamW
  state/parameter groups/step count/names, and Python/CPU/single-CUDA RNG payload
  without initializing CUDA. History and carry remain in the exact hashed state;
  no teacher/environment targets or rewritten own outputs are constructed.
- EFFECTIVE_POLICY.json identifies the exact boundary and invitation hash with
  `actual_runtime_applied=false` and `corrected_output_claimed=false`. Only a
  later real invocation/render/own-response can establish exposure or content.
- A future supervisor must bind REQUEST, GUARD, PLAN, BOUNDARY, SAVED_PROOF and
  EFFECTIVE_POLICY, recheck the still-current boundary and old-owner absence,
  retain one-shot ownership, perform the unchanged privileged full scanner,
  original strict systemd device envelope and original verify_containment,
  then the unchanged native LAUNCH_READY handshake with resume=True. No source
  scan bypass or R157 old-wall validator monkeypatch is supplied here.

Main owns all parent policy rollout with Mendel and any future activation GO.
