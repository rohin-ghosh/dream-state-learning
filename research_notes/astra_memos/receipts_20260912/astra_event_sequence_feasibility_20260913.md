# Authenticated EVENT sequential-write feasibility — 2026-09-13

## Decision

**No drop-in sequential continuation exists in the frozen EVENT command/writer. Do not pass the SEQ179 checkpoint into its fresh-base factory or fabricate V3 completion files.** The smallest worthwhile supported alternative is a separately named diagnostic that starts a new V3 adapter on four of the same authenticated EVENTs, then weight-warm-starts that adapter on the remaining four with declared replay. Reuse existing continuation mechanics; do not build an optimizer-resume system or rewrite the PCFL numerical loop for this sidecar.

This is feasible as a scoped material exporter/runner addition, not executable with current EVENT stage arguments alone. If preserving SEQ179's exact unpadded/clipped numerical implementation is mandatory, stop at the small extraction proposal below and let Main decide; do not silently substitute trainers.

## Actual implementation seams and limits

- `organism_v6/pcfl_event_only_train.py:90` reconstructs the fixed14-query/20-slot/200-update fit; `train_fit:131` invokes the shared fresh-only loop. It cannot express a four-row phase or a predecessor checkpoint.
- `organism_v6/pcfl_vertical_train.py:133` requires 20 slots, five epochs, 40 four-item batches/epoch. `_train_encoded:350` rejects warm/adapted bases, creates fresh LoRA/AdamW, and requires exactly200 updates; it saves weights and state hashes, not resumable optimizer tensors. `_encode_corpus:209` and `_batch_objective:307` remain reusable primitives, not authorization to bypass the full-contract entry point.
- `organism_v6/train_adapter_v3.py:657`, `run_training(items,tok,base_model,cfg,out_dir,...,init_adapter=path)`, already supports **one full LoRA weight warm start with a fresh optimizer each write**. `_warm_initialize:614` loads every A/B tensor, checks equality after explicit dtype conversion, freezes the base, and records one adapter, predecessor inventory and initialized tensor identity. No adapter stack or merge is required.
- V3 `_warm_parent:524` requires `DONE`, `train_manifest.json`, adapter config and weights from a completed V3 write. SEQ179's `fit/write/adapter` has PEFT weights/config/README, while its completion uses PCFL receipts outside that directory. It is not a V3 parent. Also, SEQ179 has already trained all eight facts: using it as phase1 would invalidate “new B acquisition” regardless of conversion.
- Existing tests: `tests/test_train_adapter_v3.py:605` zero-step save/reload equality; `:645` finite warm update, fresh optimizer, immutable predecessor and chained continuation; `:672` structural/prewrapped rejection; `:703` partial/nonfinite/bad-weight rejection. These are inspected test definitions, not newly run tests; native-library-dependent checks can return early if dependencies are absent.
- `gpu/astra_pcfl_own_write_readout.py:40` accepts the existing public W0–W8 query wrappers; `ReadoutActor` validates an arbitrary frozen roster with max_calls=len(roster), not only28. It can read eight EVENT addresses at W0/W8 (16 calls/checkpoint), with exact cold adapter/no-adapter routing and existing shutdown seam.
- `gpu/astra_pcfl_event_only_command.py:203` and `gpu/astra_pcfl_event_only_outer.py:41` are hardwired to fit/readout, 200 updates, 28 calls/arm, the original fit predecessor and EVENT14 endpoint. Reuse their lifecycle/readout patterns under a new scope; do not weaken or relabel their completed stages.
- Reuse precedent, not its data: `/tmp/astra_sequential_memory_pair_20260912.py`, `/tmp/test_astra_sequential_memory_pair_20260912.py`, and archived `research_notes/astra_memos/receipts_20260912/astra_sequential_memory_pair_v1_20260912.py` show immediate-predecessor chains/cold panels. Their `select_s0` is specific to an older authored FOUR_VIEW checkpoint. `organism_v6/sequential_memory_corpus.py` generates authored device/color banks and arithmetic: **do not invoke its material builder/exporter for this task**.

## Fixed split and target definition

Use only the immutable imported SEQ171 rows/captures, original import seal `cc9e97a290933633d67c371625ae5cfffeb46bc8ca7c130279022868e98a545e`. Verify import/tokenizer via `gpu/astra_pcfl_event_prefix_import.py`; retain all original failed-formation provenance. Split by original admission chronology, never score or lexical handle order:

- A = EVENTs from call indices1,3,5,7 (first four admissions).
- B = EVENTs from call indices9,11,13,15 (last four admissions).
- Both are original world-phase OLD rows; “A/B” means diagnostic introduction time, not a change of their original phase/taint or a new native experience.
- Primary material/readout: **eight `READ EVENT` singleton mappings only**, four A and four B; exact admitted raw EVENT including terminal LF is the target. This is a new narrower endpoint, not SEQ179's fourteen-address assay.
- Do not slice the fourteen-address query map into seven/seven. EVENTS_AT can span phases: source `N_HO47JGPS4W` has an A EVENT plus a B EVENT, so its full-bank target would leak B in phase1; an A-only target would change after phase2. Exclude EVENTS_AT from the primary split/retention endpoint. If reported separately, label these as changing aggregate-address reconstruction, not forgotten fixed targets.
- Construct contexts only from existing memory system and W0–W7 wrappers. Keep target bytes/capture hashes and support ledger; no new factual rows, ideal answers, LINKs, generated paraphrase targets, parent prose, or unsourced canaries. A phase's encoder must receive only that phase's admitted target subset even though the experiment coordinator retains the sealed full archive.

## Smallest concrete schedule and controls (proposal, not launch authority)

Use V3 for **every fitted arm**, starting fresh frozen Qwen and rank8/alpha16/dropout.05/LR3e-5. Seed0 per write; weight continuation, optimizer reset at each declared boundary. Set pack=False, shuffle_groups=False, batch_size4, grad_accum1, max_len512, add_eos=True, chat_template=False after rendering the context. Require zero context/target truncation and all declared steps, finite loss, nonfinite_batches=0. V3's padded forwards/default AdamW/no PCFL clipping receipt differ from SEQ179; do not claim numerical equivalence.

Sleep ruling: `research_loop/COORDINATION.md:6027` requires many exposures × varied phrasings, not identical copies masquerading as new experience. Use all eight existing wrappers, interleaved across optimizer steps, with explicit repetition counts. Render variations change queries only, never factual targets. Replay sources are the authenticated A records, externally compiled at this level, not autonomous dreaming.

| State / branch | Initialization | Training presentations | Updates |
| --- | --- | --- | ---: |
| S_A | fresh C0 | A4 × W0–7 ×5 repeats =160 | 40 |
| SEQ_REPLAY | exact saved S_A | A4+B4 × W0–7 ×5 =320 | 80 |
| SEQ_NEW_ONLY | same immutable S_A | B4 × W0–7 ×10 =320 | 80 |
| FRESH_MIX | fresh C0, same seed | identical phase2 material/order as SEQ_REPLAY | 80 |
| ALL_AVAILABLE | fresh C0; warm continuation at update40 | interleave same total ledger as S_A+SEQ_REPLAY: A80/B40 presentations per fact | 40+80 |
| NO_WRITE | fresh C0, no fit | same frozen read requests | 0 |

The 40/80 dose is a small prospective screen, **not** an inherited demonstrated split-fit dose. Do not increase it after looking at S_A or B failures under the same diagnostic identity. If S_A learns none of A, report retention unavailable and low-dose acquisition failure; do not infer a retention defect.

ALL_AVAILABLE exposes both banks from the beginning. For each wrapper and each of five repeats, schedule three four-distinct-source batches: A0,A1,B0,B1; A2,A3,B2,B3; A0,A1,A2,A3. This yields120 updates with the same per-source/per-wrapper ledger as the replay trajectory. Save/reload and reset optimizer at update40, as in sequential training, to avoid confounding a single uninterrupted optimizer with a two-write trajectory. Pre-expand the schedule, split into160/320 items, train each segment for one epoch with exact max_steps40/80. Encode batch positions as zero-padded group IDs and within-batch order: V3 `pack_by_group(...,pack=False)` sorts by group/order, so source-handle grouping would silently change the intended schedule.

Apply that pre-expanded, one-epoch schedule convention to all arms; repetitions remain explicit ledger entries. Four distinct supports/batch avoid averaging four identical copies in one update. No hidden partial final batch, automatic shuffle, or within-update duplicate dose claim.

Matching statements: SEQ_REPLAY versus ALL_AVAILABLE matches total updates, target occurrences/tokens and wrapper occurrences plus optimizer-reset boundary, but changes presentation order/batch composition (padding/runtime can differ). SEQ_NEW_ONLY matches phase2 slots/updates, **not new-fact dose**: B receives80 presentations/fact versus40 with replay. FRESH_MIX matches phase2 corpus/update budget, not prior40 updates or total lifetime compute. NO_WRITE is explicitly unmatched compute. This is an allocation/order/initial-state diagnostic, not isolated biological replay causality.

Six physical fits total400 updates/1,600 presented examples when S_A is shared immutably across its two forks. ALL_AVAILABLE uses two of those fits. It is one source bank/seed, not independent learners. The optional zero-step reload check is a CPU mechanics check, not another science branch.

## Pre/post measurement; acquisition is not retention

Freeze 16 cold requests/state: A4+B4 at W0 and W8, using existing strict raw+stop scoring. Measure fresh C0, S_A, SEQ_REPLAY, SEQ_NEW_ONLY, FRESH_MIX and ALL_AVAILABLE final:96 calls total. Optional ALL_AVAILABLE midpoint adds16 calls if predeclared, not selected after results. Each checkpoint gets a fresh readout process; readout does not train or mutate the adapter. No row source store or read history enters model prompts.

- A acquisition: fixed four-element W8 correctness vector at C0 versus S_A; W0 reported separately.
- A retention: each A item's S_A→phase2 transition, lost count1→0, kept count1→1, and postwrite correct/4. Conditional kept/pre-correct denominator is explicit; zero pre-correct means undefined retention, never100% retention or imputed zeros.
- B acquisition: fixed four-element W8 vector before introduction at S_A and after phase2; distinguish preexisting hits, newly acquired0→1, and losses. Report both banks, not a pooled8/8 score that can hide forgetting.
- Present the matched ALL_AVAILABLE and FRESH_MIX/C0 controls beside both bank vectors. Keep raw malformed/length cases and operation costs. No new numerical pass threshold is inherited from13/14; this feasibility proposal recommends descriptive fixed vectors rather than post-hoc gates.
- W8 remains excluded from training but is already a development wrapper seen in SEQ179 outcome inspection. These are not untouched confirmation facts/roots or fresh wrapper generalization.

## Minimal implementation work and stop boundary

1. New narrow exporter/spec: consume validated imported rows, freeze chronological A/B and per-arm source/view/batch ledger, emit V3 normalized context-masked/target-active spans, bind source/tokenizer/authority/parent hashes. Reuse `normalize_items`, `encode_item`, and actual tokenizer checks; reject any truncation before fitting.
2. New scoped runner: call existing `run_training` for fresh S_A/FRESH_MIX/ALL first segment and `init_adapter` for warm segments; validate DONE/manifest/full predecessor files and initialized tensor equality. Require exact steps and zero nonfinite batches even for fresh writes, since generic fresh V3 can record skipped nonfinite batches. No production monkeypatching or fake manifests.
3. New stage names/receipts around existing cold ReadoutActor and owned-process lifecycle; distinguish experiment branch from actor mount label AUTH_WRITE/NO_WRITE_C0. The existing EVENT command/outer/reducer keep their14/28/200 contracts unchanged. A small reducer of fixed4+4 vectors suffices; no new general guard framework.
4. Before execution, owner verifies tiny CPU zero-step load/save equality and a finite two-write chain, unchanged predecessor/base, exact masking/group order and exposure equality, cold roster/route joins, and failure preservation. Existing tests are reusable evidence patterns, not proof that this new exporter/runner already works.

If retaining the PCFL loop is chosen instead: obtain Main's approval for a bounded checkpoint-load initialization seam in `_train_encoded`, reusing V3's full-state validation, plus explicit expected schedule/update count rather than its hardcoded200. Preserve the full-contract and existing EVENT defaults unchanged. A common state-loader extraction from `_warm_initialize` would be needed because its V3 manifest assumptions reject PCFL checkpoints. This is more work than the V3 alternative; **do not implement it here or pretend cold readout loading equals trainable continuation**. Full optimizer resumption adds saved optimizer/RNG tensors and is unnecessary for the stated weight-continuation question.

## Source pins / limits

- EVENT writer: `24faf066d22bd15361cd8fe95a40033a3011307cebb6ea94dad05c29aadf04e2`.
- PCFL numerical writer: `9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078`.
- V3 trainer: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`; tests `9b50c013ea64f9899b1295bcdfe707b4ab59c310f464e975ba377445b86bd534`.
- Current EVENT command: `3ebef8ce6c8cd783104f5d0d74946fd1df5f99e41208508451482f56fdf9d916`; readout module `d8d4ef962ca80933f3c3a60681c8375198197855f8d5f00a2b7835461e8427c4`.

Only this planning file written; no repo edits, tests, models, GPU, network or new material. No general G3, parenting, learned replay policy, independent learners, retention beyond the measured interference interval, or whole-organism claim follows. Formal C11 deferred; no new confirmation infrastructure gate imposed. **EDITSTOP.**
