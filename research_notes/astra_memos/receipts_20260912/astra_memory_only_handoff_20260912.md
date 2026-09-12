# Memory-only positive control — implementation handoff

2026-09-12. **EDIT-STOP.** Only the following three files were written:

- `/tmp/astra_memory_only_20260912.py`
- `/tmp/test_astra_memory_only_20260912.py`
- `/tmp/astra_memory_only_handoff_20260912.md`

No repository/Git/network/GPU operations, native model/tokenizer loading, old-artifact changes, or scientific runs occurred. Main owns native testing, preparation, coordination logging and launch. All other contributors' files remain untouched.

## Fixed implementation

Three children, each from its original teach parent, never a repetition/fading/two-habit descendant:

- Seed0: `~/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/fit_teach/adapter`.
- Seeds1/2: `~/astra_diagnostics/astra_fundamental_replications_20260912_attempt1/seed1/fit_teach/adapter` and `seed2/fit_teach/adapter`.

The sidecar embeds original plan, fit-receipt and teach-readout-plan hashes recovered from the local SEQ098/099 capsules. Seed0 uses `fit_teach/result.json`; seeds1/2 use `fit_teach/verified.json`. Physical VM parent weights/configs/manifests and full original readout captures must remain available; a terminal capsule alone is not sufficient for native prepare.

All three original `teach.json` files must match SHA-256 `2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c`. Preparation filters precisely the16 `view=memory` records without rewriting spans, metadata or relative order. It checks original IDs, source-event IDs, expected colors, native rendered prefixes and training labels using the existing modules. Readout template rendering verifies the existing interfaces; no new training rendering or factual material is introduced.

Recipe: rank8/alpha16/dropout0.05, lr3e-4, epochs20, batch4, grad_accum1, AdamW, no packing, max_len512, no second chat wrapper, EOS enabled, existing seven projection targets/all layers. Continuation optimizer seed equals original parent seed. Full single-adapter weight warm-start, fresh optimizer, no optimizer-state resume/stacking/SVD initialization. Effective native CLI config is checked during prepare and before training.

Per child:16 rows ×20 epochs /batch4 =80 new updates;80 original +80 =160 cumulative. Every row has42 ignored context tokens followed by one color and EOS. Predictor indices41/42 predict target positions42/43. Per epoch704 input/32 target tokens; per child14,080 input-token presentations and640 supervised-token presentations. Fit acceptance checks finite completed80 updates,20 epochs, exact counts, no skipped/no-target/truncated/split material, parent immutability, source/initialized/final full LoRA inventories, one adapter and fresh optimizer receipts. Original fp32 parent state must load exactly without dtype conversion.

After each valid fit, both captures are mandatory regardless of score:

1. Original fixed48 dev via `organism_v6.fundamental_teaching_readout`.
2. Exact16 original training-prefix questions via `organism_v6.fundamental_memory_diagnostic`.

They have separate plan/run/data/calls/reduction directories and unchanged reducers. Native settings remain temperature0, readout seed20260912, max_tokens64. All row-level/raw scores are retained and reductions included in the terminal result, with hashes. No scientific threshold selects seeds, skips exact16, or chooses a checkpoint. Total workload is240 new updates and192 generation calls. No new HF/OFF/confirmation calls.

Original teach baseline counts attach per seed (memory4/7/3 of16; ACT/adherence32/32 each). Three original control captures and the single original OFF dev capture are separately hash-bound in the prepared plan as inherited references, not regenerated or treated as new matched training controls. Original seed1/2 exact-prefix baselines are not invented. Main can reuse existing SEQ100 seed0 exact-prefix evidence from its already-owned capsule; this sidecar does not recapture it.

## Dependencies

Frozen source checkout `3a12807f` is sufficient. Pass its actual absolute path with `--source-root`; no Git lookup is performed. The existing fading sentinel helper is required, default `/tmp/astra_fading_sentinel_20260912.py`, SHA-256:

`7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20`.

It supplies existing sealing/state-inventory helpers; supervision, process ownership and native readout workers remain existing code. No dependency on the separate fading replication sidecar is needed. Source bindings include the helper's dependencies, v3 trainer, exact-memory module and new sidecar. Do not edit existing modules/helper to accommodate the run.

Current implementation SHA-256: `ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb`.

Current test SHA-256: `b0ba7036bdccdd10fc7bfba8f3b84a5e8cc0b08574036acc746c61c52d88f1b7`.

## Main commands

Run tests from the selected frozen source checkout, with Main's actual environment interpreter (`python3` was used locally):

```bash
PYTHONDONTWRITEBYTECODE=1 python -B /tmp/test_astra_memory_only_20260912.py
```

Tests bind the current working directory as source. Native prepare is Main-only, using existing local tokenizer/base/parent files:

```bash
python -B /tmp/astra_memory_only_20260912.py prepare \
  --source-root "$SOURCE" --runroot "$FRESH_RUNROOT" \
  --seed0-root "$HOME/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1" \
  --parentsroot "$HOME/astra_diagnostics/astra_fundamental_replications_20260912_attempt1" \
  --devices "$DEVICE0" "$DEVICE1" "$DEVICE2" \
  --deadline "$ABSOLUTE_DEADLINE_EPOCH" --lease-end "$LEASE_END_EPOCH"
```

All three device assignments are sealed together. Repeated device IDs allow Main to schedule sequentially as capacity becomes available, never concurrently on one device. Choose an absolute deadline allowing each later controller a full900s within the lease margin. The output root must be fresh. Partial preparation evidence is preserved, not overwritten.

After native CPU/provenance acceptance and Builder logging, Main alone performs the existing external full-vacancy/reservation checks and uses its owned-controller launcher/offline environment:

```bash
CUDA_VISIBLE_DEVICES="$DEVICE0" python -B /tmp/astra_memory_only_20260912.py run \
  --source-root "$SOURCE" --runroot "$FRESH_RUNROOT" --seed 0 --allow-gpu
```

Launch seeds1/2 exactly once with their sealed devices. No runtime device override. The foreground example is not a replacement for Main's external launcher/process-group/ledger discipline. Never invoke readout workers directly.

```bash
python -B /tmp/astra_memory_only_20260912.py status \
  --source-root "$SOURCE" --runroot "$FRESH_RUNROOT"
```

Status is read-only. Existing seed directories without a terminal receipt are `NONTERMINAL_OR_ABANDONED`, not retryable successes. Exclusive creation prevents same-root replay/resume; no intermediate checkpoint or best-seed selection is supported.

## Budget and terminal acceptance

Selected prospective envelope: **3 ×900s =2,700 aggregate A40 seconds =45 device-minutes**, replacing the earlier30-minute design estimate. Each controller accounts elapsed time from CLI main entry, including binding/startup, verification, CPU gaps and cleanup. Absolute deadline/lease must permit its entire900s; a shorter window is rejected rather than silently changing the recipe.

Existing worker ceiling600s and cleanup reserve140s remain unchanged. The controller arms its cleanup-boundary signal140s before its effective deadline; active supervised workers use existing owned-process cleanup. All three workers receive the same controller deadline. The whole-controller `reserved_seconds` and summed `worker_reserved_seconds` are separately recorded in `seedN/terminal.json`. Main must additionally record external pre-spawn reservation delays/full release in its ledger. No monetary rate is assumed, and no lease extension/new hardware is requested.

Completion requires fit plus both reducers, exactly three successful worker receipts, accounted process receipts, verified owned-group/GPU release, unchanged source/parent/child evidence and completion within deadline. Failures preserve partial artifacts and produce `FAILED_PARTIAL_NO_RETRY`; missing work is not a scientific zero. A failure during CLI import/binding before branch creation is a launcher failure for Main to log, not a completed seed. No scientific score controls scheduling; Main schedules all three predeclared seeds as capacity permits within the selected allocation.

## Validation performed

**19 CPU fixture tests PASS**, including multiple parameterized rejection cases; both Python files also pass AST parsing. The tests write no fixture files, invoke no subprocess, load no native tokenizer/model and probe no GPU. They cover:

- Subset identity/order/metadata/input immutability; missing/duplicate/source/target/context rejection; native-label mismatch;44/2 per-row token accounting.
- All three effective CLI configs,80/160 history,20 epochs,14,080/640 presentations, nonfinite/skipped/truncation guards.
- Full loaded-state equality, fresh optimizer, matching phase seed, one adapter, parent/cumulative-step ownership checks.
- Explicit complete device mappings, wrong-device rejection, full900s admission, startup cost accounting, helper tampering, fresh-output and supervisor-failure rejection.
- Mandatory separate48/16 captures even when dev scores are zero, raw reduction retention, partial terminal recording, and refusal to complete without three receipts and verified release.

Also exercised `parent_record` against original JSON/hash inventories read directly from local SEQ098/099 terminal archives for all three seeds. This passed with physical VM weight inventory/loader identity/filesystem existence mocked; it is not native weight authentication. An initial mock marking both weight formats present correctly raised the ambiguous-weight error; using the captured loader identity resolved that fixture issue.

## Main acceptance checklist

1. Rerun CPU tests in frozen source; confirm helper/source/sidecar hashes and physical original parent weights/configs/manifests/baseline captures.
2. Native prepare must pass all16 original row/render/token/label checks for every seed, plus CPU `_warm_parent` compatibility, effective recipe and all devices sealed. No tokenizer or baseline exceptions may be silently waived.
3. Log the selected45-minute scope and CPU/provenance acceptance in the existing Builder coordination path; retain reserved invariants and Main's ongoing implementation ownership.
4. Confirm every900s window,140s cleanup reserve and real lease before launch; schedule all predeclared seeds without outcome-based selection.
5. After execution, inspect all three terminal receipts and all six raw reductions. Report weak/invalid results and inherited controls without threshold tuning. Separate acquisition, dev-wording transfer and behavior retention; do not infer causal interference/dose, latent absence, selective locality, new-fact generalization or H1/H2.

**EDIT-STOP.** Main owns all remaining native testing, preparation, logging and GPU execution.
