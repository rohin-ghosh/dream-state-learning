# EDITSTOP — prospective actual-record readout bridge

2026-09-12; source/test hashes captured at 21:33:47 UTC. This protocol was sent to Main before any live write/readout outcome inspection by this worker. Implementation, tests and this note are the only owned files. No repository/write-driver edits, GPU/native execution, SSH, network, Git, or live outcome reads. Main alone integrates and launches.

## Prospectively fixed protocol

Use the existing frozen `rulegame_parenting_diagnostic.run_evaluation` and `play_task` unchanged, not legacy `evaluate`/material/write paths. Execute **OFF → P_ON → A_ON** once, with a separate fresh supervised process/backend for every cell. OFF loads the pinned base without an adapter; P_ON/A_ON load exactly the independently saved P/A adapters. No merged/warm-start adapter, updates, synthetic sleep, new tasks or curriculum.

- Four existing tasks, in order: `rule2/astra-minimum-20260912/readout` through `rule5/astra-minimum-20260912/readout`. Preserve task IDs, generation seed20260912 with existing task/tick/role derivation, temperature .7, interaction_v3 stop/action/relation semantics and quiz construction. No new random draws, panel selection or confirmation selection. Formation rules0/1 are excluded; no task outside the original four-task evaluation schedule is introduced. Existing confirmation exclusions remain untouched. This is not a claim of globally unseen/never-inspected rule families or fresh confirmation data.
- Five wake opportunities/task: at most three TRYs, one quiz reveal, one scored six-label quiz, with existing early termination/invalid-action handling. First-quiz accuracy is primary; invalid/absent quizzes remain zero. Cell mean always divides by four. Retain all four per-task records and all three cells; report unchanged P−OFF, A−OFF, P−A. One shared OFF, no favorable task/record replacement, no added seeds.
- Keep existing record calls after executed TRYs, including full interaction_v3 relation definition. These are **diagnostic records only**: not selected, trained, slept or fed back into wake prompts. Faithful-record counts/allotted12 opportunities, quiz validity, terminal modes and raw usage remain visible; they do not filter scores.
- Every task starts with the same existing BOOT/task intro, an empty parent prefix and a fresh task-local history. Model prompts receive only current-task child outputs/public world outcomes and existing diagnostic record prompts. No formation transcript, Main assessment, parent lesson/restatement, old records, prior-task history or earlier-cell scores enter the model context. The worker spec is a strict field allowlist containing only runtime/code/base/adapter pins, protocol, deadline and process/output data. Controller-only lineage checks may read sealed training receipts; workers never invoke the write driver or material exporter.

## Scientific scope

This closes **readout plumbing**, not a learning result. Mock success establishes neither native feasibility nor improvement. Native results would be a small exploratory, post-treatment-selected-material, matched new-rule competency/transfer comparison against one shared OFF and the active A control. Adaptation to the new rule occurs only within ordinary task context; there is no readout-time learning loop or pre/post sequential-adaptation estimand. Do not promote this to general parenting, G3/G5, H1/H2, a clean confirmation test, semantic nonleakage certification, or model-origin authentication. Existing selected-record/Main acceptance is inherited, not reclassified. Fresh-process/record-prompt isolation is an executable data-flow contract and exact replay/native-token check, **not OS-level filesystem sandboxing**.

Main's additional scientific boundary is retained: trained targets describe prediction/outcome/relation **conditioned on the already-emitted wake output and public world outcome**. This need not train pre-TRY information selection. The four-rule assay can test transfer of these records/process indicators, not autonomous adult updates or longitudinal G5/H2. No new metric/assay is added here. Any later spontaneous-PREDICT analysis must count explicit pre-TRY predictions separately from faithful-record fractions and quiz scores, state each denominator, and retain invalid/missing cases; faithful records alone must not be labeled spontaneous prediction skill. Raw calls/events retained by this unchanged readout support a separately declared analysis.

## Lineage, costs and failure behavior

`prepare` accepts explicit `--write-root`, `--write-plan-sha256`, `--write-driver`; it checks prepared source/material/base/accepted-audit custody but does **not** read fits or write/readout outcomes. It writes a fresh sibling readout root with an immutable protocol plan and returns its hash. Freeze this now, then run `evaluate` only after Main knows both writes have completed and the device is released.

At evaluation, both fits must pass the selected driver's unchanged `checked_plan`, `verify_inputs`, `validate_fit`, fit seals, completed-pair receipt and cleanup checks. The bridge records the completed-pair result hash, per-arm adapter/config/manifest hashes and supervisory receipts. It rechecks these before cells and at completion; changed base, code, material, audit or adapters fails closed. A fresh worker-spec hash binds each launch; PID/PGID/session-leader checks, parent-death/deadline watcher and existing supervisor require separate owned processes. Capture identities, native rendered prompts/input IDs/decoded output IDs, raw calls/events, replay, usage and owned cleanup are retained. Earlier captures are revalidated before aggregation.

Budget: **1800 seconds controller wall time**, including its lineage checks/cell supervision and cleanup; each worker ≤600 seconds, actual call≤120 seconds, backend readiness≤180 seconds. Reuse existing supervisor with **140 seconds cleanup reserve** and its existing10-second lease guard. These clocks are nested/nonadditive: three full600-second worker windows plus extra cleanup are not promised. Work stops early enough to preserve cleanup. Hard end is min(start+1800, supplied deadline, supplied lease expiry−6hours). `prepare` requires a fresh full1800-second window. Lease expiry is Main-supplied, not independently checked with a provider. Maximum96 responses: ≤60 wake×400 plus ≤36 record×100 = **27,600 generated tokens**, not a total input-token cap; input/output counts/timing are logged and the unchanged16,384 model-length bound applies.

One exclusive run directory; no retry, alternate adapters, replacement cell or auto-promotion. An incomplete pair prevents any readout. A failed cell stops subsequent cells, keeps completed/partial evidence and writes failure with completed cell names; no successful aggregate/partial contrast is emitted. Main must inspect resource-release receipts. A fresh root is not authorization for outcome-driven reruns.

## Tested bytes and results

**PASS: 25 mock-only tests in 27.785 seconds.** Includes exact prompt/request/result parity with direct frozen evaluation; actual v2 driver API using a synthetic fitted pair; retained venv symlink interpreter; worker forbidden-input access checks; no training/legacy path; all-cell/fixed-denominator handling; source-plan/protocol/spec/adapter/identity/capture tamper; failed/partial writes; OFF/P/A failures and cleanup; opt-in/freshness and nested deadlines. No real tokenizer/model was loaded or GPU queried; fits/backend/process/supervision were mocked.

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
python3 -B -m unittest discover -s /tmp -p test_astra_rulegame_record_readout_20260912.py -v
```

Tests reuse read-only synthetic fixtures from `/tmp/test_astra_rulegame_record_write_20260912.py` and existing repository tests. They also expect Main's local v2 driver for the actual-API compatibility case; no fixture/test/source is modified.

SHA256:

| File | Hash |
|---|---|
| `/tmp/astra_rulegame_record_readout_20260912.py` | `120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde` |
| `/tmp/test_astra_rulegame_record_readout_20260912.py` | `e34cb5c9aa7e9c2339eb21a46428cb38e8d8401945a90b5e08f7514d44c8db11` |
| Main's `/tmp/astra_rulegame_record_write_v2_20260912.py` (read-only) | `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c` |
| `organism_v6/rulegame_parenting_diagnostic.py` (read-only) | `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526` |
| `organism_v6/rulegame_record_material.py` (read-only) | `7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1` |
| `organism_v6/train_adapter_v3.py` (read-only) | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |

Code anchors: protocol line96; preparation line118; completed-write custody line159; minimal worker spec line185; owning-process check line227; isolated worker line265; controller line330.

## Main command templates — NOT executed here

Main supplied attempt2 root and plan hash below. These are inputs, not a claim this worker inspected that remote root or its status. Do not use attempt1. Use the **exact absolute native venv interpreter spelling from the write plan**, without `realpath`/`Path.resolve`; the bridge preserves it and rejects a different controller interpreter. Set real timezone-aware deadline/lease strings. Source/model paths must remain available unchanged on node3; use the source-pinned driver bytes.

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
WRITE_ROOT="$HOME/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2"
READOUT_ROOT="$HOME/astra_diagnostics/astra_rulegame_interaction_v3_record_readout_20260912_attempt1"
"${NATIVE_PYTHON:?exact absolute write-plan venv interpreter}" -B \
  /tmp/astra_rulegame_record_readout_20260912.py prepare \
  --write-root "$WRITE_ROOT" \
  --write-plan-sha256 48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4 \
  --write-driver /tmp/astra_rulegame_record_write_v2_20260912.py \
  --out "$READOUT_ROOT" --deadline "${DEADLINE_UTC:?set future deadline}" \
  --lease-end "${LEASE_END_UTC:?set actual lease expiry}"
```

Save the returned `plan_sha256` verbatim. Only after complete paired writes/device release, under Main's explicit launch:

```bash
"${NATIVE_PYTHON:?exact write-plan venv interpreter}" -B \
  /tmp/astra_rulegame_record_readout_20260912.py evaluate \
  --root "$READOUT_ROOT" --plan-sha256 "${READOUT_PLAN_SHA256:?exact prepare return}" --allow-gpu
```

**Remaining decisive native check:** confirm both complete, frozen-base/LoRA-only,12-update writes and their releases; then execute all three fresh generation processes, inspect actual native-context/token audits, raw replay, fixed scoring and cleanup. Failures stay evidence, not opportunities for replacement. `COMPLETE_EXPLORATORY_READOUT` means plumbing completed with captured scores, not that learning/competency improved. No native outcome or scientific-claim approval is supplied by this handoff. EDITSTOP.
