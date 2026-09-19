# Additional node2 caption life — read-only recovery assessment

**2026-09-19 03:52:37 UTC observation.** PASS for the selected clean committed
boundary and saved-state/COMMIT document bindings; **HOLD for actual recovery
or bounded fast-resume admission**. This is not a launch authorization.

## Actual life and durable boundary

Base: `/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork`.
Its actual control/source directories are `control_r233_recovery` and
`source_r233_recovery`, not the C0/Astra7 lease-continuation directories.

- COMPLETE **8527**, LEARN/head **8528**, cycle **119**, optimizer **10236**.
- COMPLETE SHA256
  `9bce737fd97a81cb8bee4a0be486db7ee9ae633887e90ab614d04f7d55fce430`;
  LEARN/head SHA256
  `58177fb38f89c7ab66cfa79a4f7d1a8c30d4eb1e8385dc410fb8abcc70a45c39`.
- Saved state has **487 rows, frontier 487, pending null**: no durable pending
  sleep or untrained rows at this observed boundary. The only record after
  COMPLETE is the matching LEARN. This does not assert there is no later or
  unconsumed external mailbox work.
- Saved-state SHA256
  `058e9001c3c2947163b8b3eb52fe5913ea8c83924462dfc5b2fd6329193f979e`;
  history SHA256
  `22625a3fe4cb116060d98bae4644bd4f18c13042319d294160abd1a570fc423b`;
  working-state SHA256
  `45774118e27975cfc41a2e96392a8ebb3414aa1c7357b5d758989679255c7435`.
- Checkpoint under `raw/checkpoints/sleep_000119/COMMIT.json` exactly matches
  the COMPLETE checkpoint document; file SHA256
  `a5d4034d71916d9f5af8eecd9653fb1be62ecd8c37e29259cf06448dd0008c44`.
- Declared adapter artifact digest:
  `edbd4fe25b6706349a14b5df5a2d99b6607f5f3874ac65700088137efd674838`;
  optimizer/RNG file digest:
  `f438987995b73a12d6519bb2771fb889a676d9cb850c8d4e3f316943f8fb2260`.
  **Tensor binaries were not hashed or loaded by this sidecar.**

Selected COMPLETE and LEARN canonical hashes, saved-state digest and COMMIT
document equality were checked. The record-directory listing was stable with
no unexpected entries. These checks do not replace full record/intent replay,
source closure, sidecar audit, or checkpoint binary validation.

## Failure and preservation

`control_r233_recovery/NATIVE.log` shows `fresh_readout_incomplete` in pinned
`gpu/orch_r125_continual_native.py:305`; reporting it then fails with ENOSPC in
`write_once`. The original `gpu/orch_r184_think_act_learn.py:927` completes the
sleep, `:929` publishes LEARN, and only `:935` starts fresh readout. Thus this
failure is **after a durable training boundary**, unlike C0/Astra7. The nested
readout failure’s precise internal cause is not established here; no sealed
score files were opened.

EXIT, OUTER_EXIT and FAILED are empty artifacts, not successful exits or valid
status receipts. No matching same-UID guard/source process was observed.
LAUNCH identifies a timeout parent (PID 787114/start 98128664); do not infer a
native PID by arithmetic or mistake old launch/confinement receipts for current
admission. Preserve failed readout/error artifacts and all original ledgers.

An older `RECOVERY.json` documents a different rollback from COMPLETE3213,
cycle76/optimizer6940, old head3302 with 51 lost-tail updates and explicit
`exact_resident_continuity_claimed=false`. Original-tail archive/cache receipts
also exist. That old authorization does not cover this new incident, and those
records must not be erased or presented as present-day exact replay evidence.

## Original route and remaining gates

Original external executable/route, **template only; not run**:

```text
cd <exact-approved-source-root>
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.r233_node2_recovery dispatch --config <NEW_APPROVED_GUARD>
```

The preserved guard is one-shot/consumed. Fresh source-pinned receiving CPU
tests, allocation and original privileged probe/scan/systemd confinement are
required, not direct invocation of `native`. `gpu/r205_runtime.py:365` enforces
one dispatch; `:367` exact-source CPU evidence; `:370` onward runs admission.
`gpu/r233_node2_recovery.py:97` activates the caption-specific sleep hook and
tool interface for physical GPU2. Preserve their exact source/sidecar bindings
and do not duplicate caption/tool effects or add semantic row exclusions.

- Physical GPU **2**, UUID `GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05`.
- Virtual plan root remains
  `/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life`;
  original confinement binds this life’s distinct raw root there.
- Guard SHA256
  `f17b2c06389e3ef2d1f9e6fac439c096aead14c788421ddc191039418b891ec2`;
  plan SHA256
  `6588bfe99b0a491bb54cc608ca980842a13f66d3a24b61fb677f1286d18476e6`.
- Hard end **1789927200 / 2026-09-20 18:00 UTC**, lease end **1789980180**,
  next reserved **1789958580**. No extension or new effective clock.
- Policy remains `R227_ALL_AUTHENTIC_CHILD_ROWS_V1`.

The preserved source has **no `gpu/checkpoint_tail_runtime.py`**, and its plan
has no checkpoint-tail recovery selection. Its installed journal reader is
full replay, not a demonstrated bounded fast-resume reader. Although the saved
state meets the native’s pending/null and frontier equality conditions
(`gpu/orch_r125_continual_native.py:751`, `:758`), source/reader integration and
original admission still need proof. The next driver cycle derives from the
restored completed-sleep count; do not repeat cycle119 or silently rerun failed
readout side effects. Any newly bounded reader must preserve existing recovery
records, exact history/working state, all inbox/sidecar state and checkpoint
optimizer/Python/CPU/CUDA RNG, with no full-prefix fallback after admission.

## Evidence binding

`CAPTION_READ_ONLY_20260919.json` SHA256
`4193d24d4258f55d54b7ecb806303f0e5244cb7ff4d3397c6be8acc4915ec2a0`
contains source file hashes, exact control paths, selected state verification,
control-file metadata and the failure traceback. Its collector is
`read_caption_state.py`. No GPU/model calls, node mutations, native signals,
lease actions, or recovery attempts were made. Capacity repair is main-owned;
this sidecar does not claim to independently certify its archive or free space.
