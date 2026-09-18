# R168 — one-sleep targeted own-object replay (inactive)

Author handoff, September 17, 2026, 08:18 UTC. **Helper CPU-tested; selection and native integration NOT activation-ready. No Main GO, GPU run, training, restart, parent change or independent approval is asserted.** Unrelated numerical diagnostics remain parked.

## Directive and scope

Latest directive, verbatim:

> Your MAX2rows×dose4=8extra steps looks appropriately cheap; consider C1 existing free-distillation, substantive own narrative-object row selected from TRAIN ONLY, explicitly OBJECT replay (not verified code/behavior) if no genuinely good attention action yet. Main prefers one future sleep single dose (4 presentations of1row=4extra updates) with later automatic arm expiry; no repeated every sleep. Coordinate Banach to potentially add one C1 isolated source hook at same next saved boundary rather than repeated restarts; never invalidate his other4 unchanged retelling stages. Do not hold parent-prompt rollout. Need selection/CPU/end-to-end-ready receipts before any activation.

Implementation scope: new `gpu/orch_r168_targeted_replay.py`, matching tests, this plan and receipts; append the owned R167 carry inventory. No modification to native runtime, Banach's stages, Main's probe/executor, original failure receipts or another author's code.

This is an **explicit experimental exposure change**, not an exposure-neutral repair or a new scientific success claim. Main owns architecture intake, exact approved scope and activation authority. No approved intake artifact was supplied to this author. The helper's `approved_intake_sha256` parameter binds an externally validated intake; it does not validate, ratify or create one. Author CPU evidence cannot replace fresh independent review or Main GO.

## Intended arm / cost

- C1 only, parented/non-control, existing free-distillation. Select **one** pre-existing own TRAIN object row; `OBJECT_REPLAY`, never verified-code/attention-improvement labeling without separately observed support. The general helper retains the earlier hard caps of two rows, dose four, eight extra steps; this proposed arm uses **one row × four** only.
- Target exactly the next sleep after the authorized saved boundary. No new child generation, parent target, rewritten/corrected target, cropped span, tool invocation or fabricated support. Selection is frozen before evaluation and cannot be replaced opportunistically when excluded.
- Baseline for eligible cohorts remains `16*N + O` updates: NEW16, then REHEARSAL1. Append four explicitly labeled `R168_EXPERIMENTAL_EXTRA_OWN` updates. The chosen historical row gets ordinary rehearsal1 plus extra4 at this sleep, not a changed NEW multiplicity.
- Each extra update uses the exact original native encoding/prefix/target tokens/EOS/masks and `.75` own plus four `.0625` full-label anchors. Anchor index continues after the baseline, so all baseline anchor choices remain unchanged.
- Extra cost is four actual AdamW steps, `4*T` own-target token exposures and 16 full-label anchor samples; anchor token cost is the sum at the four actual appended indices across the four sorted families. No token-fraction reweighting. CPU timing here does not estimate real-model wall time or prove 16K capacity.
- `SingleSleepArm` passes through the original baseline on later sleeps, with `EXPIRED_SINGLE_SLEEP_ARM`; no second restart needed to remove the dose. A missed target does not catch up. Expiry/consumption cannot reset via earlier-cycle calls. Admission failure or unfinished/failed iteration prevents same-instance continuation.

## Selection evidence — blocked, not silently weakened

The existing C1 sleep31 boundary is a **historical sampling reference**, not authorization to rewind the continuing life or replay sleep32 now. Record3423 SHA `277edaaff897b8dea93dd8e57b211b23c08792c18cf9250471d8febdf4629d37`; COMMIT SHA `8324d17879d5a4e1fa5ca5e031ed2320589ae890592ad060ac9f5e6c93a0e89c`. Metadata receipts preserve full paths and row/event pins.

| Sample | Observed own TRAIN content | Disposition |
| --- | --- | --- |
| C1 sleep31 compaction / row92 | `{}` | Reject: empty scaffolding, not substantive object carry. |
| C1 row86 (78 tokens), rows84/85/87/88/90/91 | Elara/map/treasure narrative within `write_workspace` JSON; several variants malformed | Concrete narrative object exists, but the exact whole target also trains its wrapper. Not admitted under the instruction not to boost scaffolding. No write-success/code claim. |
| C1 rows74/77 (82/102 tokens) | Forest/fork narrative plus self-described formatting repair and fenced instructions | Not selected: whole-row replay also boosts corrective scaffolding; no observed discriminating attention success. |
| C1 rows65/68/71/80/81/82/83/89 | Empty/sleep operation, code/write wrappers, or unsupported success text | Reject for this object-only proposal. |
| Pilot sleep38 compaction | Python object survives; malformed nested quotes, `data/get`, `resultl`, indentation; summary claims correct | **Not verified good behavior or correct code. Reject as a positive target.** |

Two new bounded C1 reads each consume the same 1,368,933-byte hash-pinned record, selecting nine immediately preceding rows and six fixed earlier pre-sleep-position rows. No broad archaeology, held/eval or tensor read. Neither receipt copies conditioning prefixes/token arrays. The remaining three recent rows were already in the R167 receipt. No semantic acceptance or executable selection manifest has been fabricated. A later naturally generated substantive own row may qualify; do not delay parenting to manufacture one or strip/rewrite an existing target. No genuinely supported attention-strategy target is established.

## Banach handoff — C1-only optional integration

**For Main to relay to Banach; no direct agent message tool was available and no direct delivery is claimed.** If C1's isolated source stage is still pending and all gates become ready, integrate this optional arm at the **same next saved-boundary handoff** as C1's retelling change. Preserve C2–C5's four other stages byte-for-byte. If timing or selection does not align, ship parenting/retelling without R168; no hold or repeated restart for this sidecar.

1. Keep the original immutable PLAN/source provenance. Add a separately hash-bound sidecar referencing original PLAN plus the new isolated source-closure manifest; do not relabel the old plan as the new runtime. Supply that closure-manifest digest as `runtime_sha256`. Bind the actual interpreter, loaded source, configured model/tokenizer/adapter and root in the owning readmission receipt.
2. Construct `SingleSleepArm(selection_ref, main_go_ref, approved_intake_sha256=..., now=...)` only for authorized C1. Do not construct it for other lives or use a process-global schedule monkeypatch. Actual cycle is owned by `finish_sleep`; pass it explicitly to the sleep hook without guessing from row count. Existing `NativeChild.sleep` has no such hook yet; **no native signature change has been made by this author**.
3. After existing presentation/target eligibility and `encode_sleep_targets`, supply `new_rows`, `old_rows`, original `baseline_schedule`, native `encoded_rows`, the unchanged native encoder, exact plan/runtime hashes, actual `target_cycle`, and full-label target-token counts per record in each of the four sorted anchor families to `arm.schedule(...)`.
4. Iterate the returned schedule through the **existing native update loop**, preserving the same row objects, objective, clipping, optimizer and anchor indexing. Record planned/actual extra labels and exposure counts. A missing/changed/excluded row, incorrect cycle, authority expiry or a prior consumed marker must fail, not silently skip/substitute/retry the target dose.
5. Before committing checkpoint success, call `verify_sleep_receipt` on the fully exhausted admitted schedule and actual native receipt; reconcile the journal's four additional UPDATE records and actual optimizer increment. The verifier checks reported accounting, not that an update happened or that a checkpoint is sound. Owning runtime must fail-stop on update, accounting, checkpoint or journal failure; iterator exhaustion is **not** scientific completion. Non-target sleeps receive a zero-extra disposition, not an admitted schedule.
6. Continue later sleeps with the same process/arm, no extra dose. Persistent consumed directory is `<own-root>/r168_targeted_replay/sleep_NNNNNN/`; directory creation itself latches crash/uncertainty even before `CONSUMED.json`. Do not delete/reissue it. On restart, external readmission must verify journal completion/uncertainty before baseline continuation; a newly constructed expired arm is not recovery authority.

## Boundary and authority obligations

The helper validates canonical own-root journal/COMMIT paths before payload reads, bounds regular metadata, hashes and decodes the same bytes, binds completed state/rows/events and COMMIT references, and rejects pending/matched/zero-step controls. It never reads adapter/optimizer pickle or sealed data. `freeze_selection` stores selectors and hashes, not copied history/targets. `admit_schedule` validates exact Main GO and intake/source/root/cycle bindings, rechecks GO/expiry after preparation, and consumes a fixed operation before returning.

**These are metadata checks, not a standalone safe native-resume implementation.** The supervisor must independently bind parented C1 identity, authentic complete journal ancestry/head, latest intended saved boundary, single writer/process ownership, pending absence and own restored history/frontier. Verify exact adapter/optimizer/all RNG payloads, native loader admission and live state against the owning checkpoint before generation/training. Hold the owning lock through admission to prevent concurrent checkpoint creation; no arbitrary old-boundary restart. The helper does not discover/stop a live process, validate parent role from an arbitrary root, inspect payloads, prove history ancestry, or authenticate a GO issuer beyond supplied bound references.

## CPU evidence and bound bytes

| Artifact | SHA256 / result |
| --- | --- |
| `gpu/orch_r168_targeted_replay.py` | `4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3` |
| `tests/test_orch_r168_targeted_replay.py` | `07d105f3bfd8ea366edeb55746e2856ee0d04004b6ffb71fbdb6320685f118e3` |
| `CPU_RECEIVING_ATTEMPT2.json` | `5dff105c06c11b5b22a8e028b9d8ef687a7883c7bf157be967b3f189af3411fa`; **33/33 actual-Torch CPU tests pass** |
| `CPU_LOCAL_FINAL.json` | `26c9afe51ac111a7a33f0b0c69f7adc33e0609ec3433b3c7b0abb4a46eae92a0`; 123 run, **122 pass + one local Torch skip** |

Receiving run used `/localhome/local-rohing/v2/venv/bin/python`, Torch `2.13.0+cu130`, immutable candidate5 source/test_support directories, `CUDA_VISIBLE_DEVICES=` and no bytecode. New exact source/test bytes were executed in memory, with no source staging/install/model load. Receipt pins each loaded project dependency. CUDA remained uninitialized. ATTEMPT1 is preserved as earlier-byte evidence; only ATTEMPT2 binds final bytes.

Tests cover own TRAIN/event provenance, exact saved-state digests and foreign-path rejection, same-buffer JSON, no invented/parent/eval targets, dose/order/mask/token restrictions, four anchor families/accounting, exact authority and final expiry, fixed consumed-operation crash/refusal, changed rows/encoding, and sticky expiry/failure behavior. Actual Torch CPU test executes a two-element float64 parameter through real AdamW: baseline18 vs baseline+4=22, exact unchanged baseline trace, exact explicit-reference final parameters and moments, no CUDA initialization. **This is schedule-level execution, not `NativeChild.sleep`, C1 model, 7B numerical/capacity or full source-stage end-to-end validation.**

## Exact remaining activation blockers

1. Accept and freeze a substantive whole own TRAIN row without boosting prohibited scaffolding; author has not found an acceptable target in this bounded sample. Freeze its selector/support before evaluation against the actual chosen future saved boundary. Do not substitute current evidence with pilot correctness claims.
2. Banach-owned C1-only hook/sidecar/closure and real cycle/anchor/receipt plumbing; a full integrated CPU smoke over that exact closure must show unchanged baseline, four actual updates and UPDATE records, original-prefix/mask preservation, full anchors, checkpoint/optimizer/RNG round-trip and zero extras after automatic expiry. Include wrong-root, duplicate/restart, missed-target, incomplete-loop, expired-GO and checkpoint-failure refusal. Other four stages must remain unchanged.
3. Main-owned approved intake and exact parented C1 saved-boundary readmission/selection/GO; fresh independent review of final helper **and integrated bytes/evidence**. Author cannot self-approve these repairs or infer GO from this receipt.

Until then: **inactive, zero live extra presentations/updates; parent-prompt and retelling rollout proceed independently.**
