# Interleaved replay material — Main decision memo — 2026-09-12

**EDIT-STOP. CPU material only; not a parenting gate, launch approval, or reopened old protocol.**
Author also implemented the prior varied material/runner/collector: this is implementation and author-side validation, not independent scientific review. Main's grouped-pair findings are supplied context, not recounted here. No GPU/native execution, model/tokenizer loading, network, Git, runner changes, or other agents' edits.

## Decision and exact design

New protocol `AUTHORED_INTERLEAVED_MEMORY_REPLAY_V1`. Accept or defer this balanced-batch intervention before native preparation. It meets the requested source-bearing-step count **without changing V3**, but also changes batch loss composition; those cannot be called a pure dose or longitudinal effect across old/new runs.

- Original selection is unchanged: all16 trained device colors and the same fixed first16 arithmetic sources from original80 teach, in that original selected-source order. Four copies each, 128rows/arm. Original context/target/source-event bytes and FOUR_VIEW's four memory templates remain unchanged. Arithmetic is identical between arms.
- Split that source order into memory list `M[0:16]` and arithmetic list `A[0:16]`. For copy round `r=0..3`, block `b=0..7` contains, in order: `M[2b]`, `A[(2b+2r)%16]`, `M[2b+1]`, `A[(2b+2r+1)%16]`, all at copy/view index `r`.
- Give the four rows the shared V3 group `interleaved-r{r}-b{b:02d}` and orders0..3. Preserve original source IDs in metadata: **group now means batch, not fact**. No packing, splitting, or truncation. Existing `pack_by_group(..., pack=False)` and `epoch_order(..., seed, epoch, True)` shuffle the32 complete groups and preserve the four distinct rows inside each batch.
- Every actual batch has **two distinct memories plus two distinct arithmetic sources**. Every original source appears once per round, in four distinct groups/optimizer steps per epoch. Ten epochs give40 source-bearing steps and40 presentations/source, versus40 presentations in only10 source-bearing steps for grouped replay. Copies may land in consecutive steps: no minimum temporal separation is promised. Fixed companion structure is disclosed, not treated as independent exposure.
- Paired SINGLE/FOUR memberships, copy indices, batch groups, order, target UTF-8 bytes, tokenized targets+EOS, and actual V3 schedules are equal. All30 seed/epoch schedules (seeds0/1/2 ×10epochs) are audited every callback export, including each batch and each source's distinct-step count. This audit is **not** automatic seed eligibility/queueing.

Recipe declaration only: original teaching parent independently per arm, never replay descendants or arm chaining; frozen Qwen2.5-7B-Instruct base, same one rank8/alpha16/dropout.05 LoRA, LR3e-4, fresh optimizer, caller seed0/1/2,10epochs/batch4/accum1,320 new updates (400 cumulative only if the original parent has80). These are intended all-finite updates, not observed training. Native parent/base paths, hashes, optimizer freshness, finite updates and final states remain a later runner's responsibility.

## Important loss/computation distinction

The trainer consumes `model(**batch).loss` without source-wise reweighting. With native token-mean causal loss, an old four-copy memory-only batch devoted all its target mass to memory; half the old source batches were memory batches. New mixed batches include longer arithmetic targets. Memory's per-batch target-token share is `memory_target_tokens / (memory_target_tokens + addition_target_tokens)`, **not necessarily1/2**. Four times as many memory-bearing updates does not imply four times the memory gradient or learning. The audit records `target_tokens_by_kind` for every scheduled batch so Main can inspect the actual native denominators; no compensating weights are added.

Nonpadding token totals should remain exactly the previous varied material's totals **if the native tokenizer/rendering/source are identical**, because only metadata/order changed: supplied prior totals SINGLE66160input/56160context/10000target, FOUR67120/57120/10000target over10epochs. These are inherited expectations, not new native measurements. The callback reports actual counts independently. Mixed batches change maximum-length padding; `scheduled_costs[seed][arm].padded_input_slots` exposes that. Inputs and padded compute are NOT matched across arms, nor claimed matched to old grouped replay.

## New held-out cue families (separate, never training)

Three predeclared families, each instantiated for the same16 source facts:

1. `Look up {device} in the log and give its color.`
2. `Consult the log: {device} has which color?`
3. `In the log entry for {device}, what color is listed?`

No new-cue model outputs were generated or inspected. These are new lexical task prompts, not new facts and not48 independent memory observations. `heldout_cues` keeps source IDs and a separate expected-color key; prompts contain one device and no color/unknown label, example, teaching reminder, or answer appendix. `heldout_prefixes` in the callback receipt contains rendered prefixes/IDs only. These rows never enter either native training corpus.

Uniqueness/disjointness is checked after lowercase word normalization against **all original train/control/eval contexts** (including confirmation, used only as an exclusion set) and current SINGLE/FOUR training contexts, as well as against the48 new cues themselves. No existing confirmation rows/keys are exported. This is bounded known-corpus lexical disjointness, not semantic independence, universal novelty, or absence-of-base-pretraining exposure. No new readout/scorer or acceptance threshold is implemented here.

## Interface and fresh artifacts

Owned files:

- `organism_v6/interleaved_memory_replay_corpus.py`
- `tests/test_interleaved_memory_replay_corpus.py`
- `/tmp/astra_interleaved_memory_replay_design_20260912.md`

From the chosen source checkout, CPU tests/raw material commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_interleaved_memory_replay_corpus -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.interleaved_memory_replay_corpus emit /NEW/PARENT/interleaved_raw_attempt1
PYTHONDONTWRITEBYTECODE=1 python3 -B -m organism_v6.interleaved_memory_replay_corpus verify /NEW/PARENT/interleaved_raw_attempt1
```

The parent directory must already exist. Native-token callback only (after Main's decision, Main supplies an already-loaded actual CPU tokenizer; this module never loads one):

```python
from organism_v6 import interleaved_memory_replay_corpus as material
candidate = material.build_candidate()
material.validate_candidate(candidate)
receipt = material.prepare(fresh_output_path, actual_original80_teach_json_path, tokenizer)
material.verify(fresh_output_path)
```

`prepare(out, teach, tokenizer)` binds the exact original80 native teach file SHA256 `2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c`, verifies all80 original rendered native items/masks/metadata, and preserves target/EOS IDs against that baseline. `export_native(candidate, original_teach_dict, tokenizer)` is the pure lower-level callback interface; only `prepare` additionally requires actual file bytes/hash. No model/weight path is hardcoded. Dependencies (this module, prior varied module, original corpus, trainer) are hashed before/after generation. Failed pre-write audit creates no output; any later partial output remains stale and cannot be overwritten.

Raw export: `candidate.json`, `manifest.json`. Callback export additionally: `SINGLE_VIEW.json`, `FOUR_VIEW.json`, `token_audit.json`. Manifest contains source/artifact hashes, original teach path/hash, declared recipe, `[0,1,2]` schedule-audit seeds, native counts and `native_identity_authenticated=False`. Token audit contains both arms' masks/IDs/counts,960 planned batches, padded costs and48 held-out prefixes. It is not a model/parent attestation. `verify` checks current source/artifact hashes, immutable candidate/schema bindings and original teach bytes for callback exports; it does **not** reload a tokenizer, rerun decoding, rehash model weights, or independently regenerate callback token IDs.

## CPU receipt and cost estimate

**28 new tests PASS; 55 total PASS including all27 unchanged varied-corpus tests; zero skips.** Actual V3 pure helpers, stdlib fixture tokenizer, no native dependency. Covers deterministic global-RNG preservation, original source/targets/views, all seeds/epochs/batches, copy collisions, source-bearing steps, masks/shift/EOS, per-kind target mass, held-out exclusion/leakage, unsupported mutations, truncation, corrupted schedules, fresh paths, stale artifacts/source hashes, pinned-byte callback preparation and source mutation before writes. Native prepare fixture substitutes only the expected source-file hash for synthetic tokenizer bytes; it does not claim native authentication. CLI help also PASS.

Prior runtime supplied by Main: approximately17minutes for the completed grouped pair, including its previous readout workload. Planning estimate for an equivalent interleaved pair is roughly **20–25 A40-min**, explicitly heuristic upward padding allowance, **not** measured throughput or guaranteed completion under1500s. Obtain actual padded-slot counts at native audit and revise the estimate before any allocation. Additional48-cue-per-arm readouts, if later chosen, are extra work outside that inherited readout estimate. A previous1500s pair bound is not extended or newly authorized by this memo. No run/budget/lease/seed-selection machinery is added. Lower-priority diagnostic only; the actual parent-write path need not wait for it.

Implementation SHA256: `068088bf2572afdb0659d9340feb4688614bd3c902fe74867b055e83cd209711`.
Tests SHA256: `489e4490172f555bf2a3bc0566c8aa3c5bc85eb8097e889689721a4582d0350e`.

**EDIT-STOP — Main decides next; no automatic launch or progression.**
