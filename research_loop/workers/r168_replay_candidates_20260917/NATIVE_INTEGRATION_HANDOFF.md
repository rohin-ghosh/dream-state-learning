# R168 isolated native integration — author handoff

2026-09-17. **Implemented, CPU-stub tested, inactive; NOT independently approved or activated.** This implements only the requested one-life OBJECT_REPLAY experimental extra dose. No global native/helper edits, process controls, model calls, GPU work, deployment, or live authority files were made. Original observations and reports remain unchanged.

## Exact source and R145 boundary

Supported native is **only** `cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48`, archived in `NATIVE_cdb542.py`. `ACTUAL_SUFFIX_PATH_CHECK.json` binds the process-located source and entry guard: this native uses its original full-label forward, has no suffix call, and its source directory contains neither R145 helper. The guard invokes native `run` without installing suffix handling. This is a bounded source-path observation, not arbitrary resident interpreter attestation.

Consequently there is **no EXTRA-to-REHEARSAL numerical alias in these bytes**: EXTRA remains explicit in schedule/update/exposure attribution, while the actual unchanged native forward does not branch on it. Installing suffix behavior here would change the pinned numerical path. Tests exercise the actual local R145 helper: NEW/REHEARSAL keep predictor + 199 child tokens, anchors keep full labels, and EXTRA/UNKNOWN/REHEARSAL_OTHER remain rejected. A suffix-substituted native source is refused before model calls, optimizer steps, or consumption. A genuinely suffix-patched native is **unsupported** and requires separately pinned integration and review; never pass EXTRA directly to its R145 helper.

## Driver interface

```python
bridge = NativeReplaySleep(
    native_module, already_safely_loaded_child,
    arm=single_sleep_arm, plan_ref=plan_ref, runtime_ref=runtime_ref,
)
bridge.finish_sleep(stream, journal, anchors, root, actual_cycle)
```

Main's isolated driver calls `bridge.finish_sleep` at the existing sleep-completion call site. It delegates the existing checkpoint and SLEEP_COMPLETE lifecycle to the pinned native function with a per-call proxy for `child.sleep`. The lower-level API is `bridge.sleep(new_rows, old_rows, anchors, record, cycle=actual_cycle)`; its successful return alone is **not** checkpoint completion. Neither API installs a constructor, restore loader, recovery policy, global monkeypatch, queue, or process supervisor.

Default `arm=None` delegates directly to original native behavior without authority reads or marker creation. Armed operation requires existing `SingleSleepArm`, bound plan/runtime refs, exact live plan equality, own root, `reread_select`, NEW16/rehearsal1/anchor_lambda .25, one exact selected OBJECT row and four extras. The actual cycle is mandatory. Runtime JSON has exactly:

```json
{
  "schema": "R168_NATIVE_SLEEP_RUNTIME_V1",
  "native_sha256": "cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48",
  "arm_sha256": "4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3",
  "integration_sha256": "12e512ba08be73a1881bc75c52f60458163aa929c5b0bc682814c9c0bf93e304",
  "dependencies": {
    "gpu.orch_r108_guided_native": "<approved exact source SHA256>",
    "gpu.orch_r144_sleep_targets": "<approved exact source SHA256>",
    "organism_v6.orch_r125_plain_context": "<approved exact source SHA256>"
  }
}
```

The placeholders describe a schema, not usable authorization. Main must bind the actual approved receiving dependency bytes and runtime/plan/selection/GO chain, including the approved intake. `NATIVE_CPU_FINAL.json` records the local dependencies actually tested; different receiving dependencies are not covered by that test receipt. Source reads are descriptor-safe and compare hashes over the same bytes compiled for method-code checks. These checks are not a general admitted-import loader or complete verification of every resident global; trusted isolated construction and receiving source-closure admission remain external requirements.

## Preserved loop and one-shot accounting

The targeted call uses the **same native sleep code object**, with private globals for the encoder cache and schedule hook only. Native presentation filtering and R144 encode/exclusion run before arming. Missing/excluded selected historical row or an empty eligible NEW cohort refuses before updates/consumption; no rehearsal-only fallback bypass. Exact native own encoding, masking, full-label forward, four full-label anchors, five microbatches, fixed optimizer behavior and frozen-base checks remain in the original loop. No global mutation occurs.

Baseline updates precede four explicitly attributed extras. After each native optimizer step, the callback checks actual optimizer counter, source/order, objective weights, five loss labels and token counts; the final receipt reconciles native return values with observed updates and the actual counter delta. A create-only `r168_targeted_replay/sleep_NNNNNN/FINISHED_UPDATES.json` has status `FINISHED_UPDATES_NOT_CHECKPOINT_COMMIT`. Native completed sleep metadata retains this additional accounting only after its own checkpoint and journal completion.

Existing SingleSleepArm owns durable CONSUMED state. A consumed target cannot retry, including from a new arm instance. A missed target expires instead of catching up; later cycles use the original baseline. Failures latch bridge uncertainty and attempt a create-only FAILED_OR_UNCERTAIN receipt; receipt-storage failure may prevent that additional file, but is never converted to success. Checkpoint/journal failure after updates also latches. **External restart admission must still reject uncertain/unfinished prior work; an expired arm is not recovery authority.** This wrapper preserves native numerical checks; it does not claim new adapter/AdamW/RNG checkpoint verification.

## Candidate and cost

- creative_reread segment118 / `child:segment:118`, exact whole own row, 199 recorded target tokens; no cropping or rewriting.
- Source `1d721f3be5a40bac051f0c132451d7bb1e6bec428eec63327b26f64432ae17d7`; row `564f8a4f585ecc2eb4bfb16fb0efb390cf8014050fd761dadc93b4773ecd7e6d`.
- Woman/chrysanthemum narrative with soft paler petal/stem relationship. Qualifies **OBJECT_REPLAY**, not certified correct code/action or demonstrated attention improvement; retain mixed-language and unsupported interpretive content rather than polishing it.
- Parent rendering and committed own response are bound separately in `PARENT_PROVENANCE.json`; exact text match is not unique-publication-ID attribution. Parent text is not a training target.
- One row × four extras at one authorized future sleep: **796 extra own-target token exposures, 16 full-label anchor samples, four extra optimizer updates**. No recurring dose.

## CPU evidence and remaining gates

`NATIVE_CPU_FINAL.json`: **28 focused tests passed; 157 total tests run, 156 passed and one expected actual-Torch-unavailable skip**. Exact archived native sleep/finish code executes with stub tokenizer/Torch/model/optimizer/checkpoint/journal. Synthetic baseline17 → total21 updates; first17 traces unchanged; 105 total microbatches. Coverage includes R144 exclusion, own-prefix mutation, no-arm identity, source/plan/runtime/GO binding, expiry/no retry, full anchors, counter/accounting and optimizer/recorder/receipt/base/checkpoint/final-journal failure latching. This is **not actual Torch, 7B, resident-loader, or real-world activation proof**.

One post-implementation exact-path check at **09:22:17 UTC** found sleep40 COMMIT **absent**, with zero checkpoint payload bytes read (`NATIVE_POST_IMPLEMENTATION_SLEEP40.json`). No polling or journal expansion followed. Do not admit row118 from the older sleep39 checkpoint or assume sleep41 is still the next boundary.

Before activation: (1) authentic completed saved boundary with unchanged eligible row and verified ownership/pending/journal state; (2) exact actual receiving native/dependency/runtime/model/tokenizer/plan bindings and safe restore/single-writer admission; (3) fresh frozen selection plus bounded Main GO for the then-current single future cycle; (4) fresh independent review of these bytes and required receiving CPU/end-to-end evidence. This author supplies no independent approval. Main owns the driver/queue and activation; parent rollout must not wait for this optional arm.

## Bound implementation

- Integration: `12e512ba08be73a1881bc75c52f60458163aa929c5b0bc682814c9c0bf93e304`.
- Tests: `787fa8387a23792f57951289f3571211fbe439b0b69c5eed768ecd2845d552d8`.
- Existing arm: `4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3`.
- Exact dependency/fixture hashes and CPU command modules: `NATIVE_CPU_FINAL.json`.
