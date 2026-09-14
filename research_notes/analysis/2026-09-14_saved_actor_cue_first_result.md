# Saved-actor cue collection: frozen-source first result

Scope: `/tmp/astra_cue_current_actor_20260914_attempt1/run` on node2, compared only with the previous explicit-cue run. Local evidence: `gpu_artifacts_local/astra_saved_actor_cue_first_result_20260914/`. No model/tokenizer/scorer loads, fitting, launches, remote writes, notebook or project-code edits. Main already inspected all eight one-READ paths; this sidecar verifies their provenance, exact replay and the one changed outcome.

## Result and narrow comparison

Terminal `COLLECTION_COMPLETE_NO_FIT`, source commit **`c6acab47c7708ee2c35d42df97d2ed98d6dafb5b`**. Captured finish literal `1789377770.1009471` is **2026-09-14 09:22:50.1009471 UTC**. Eight retained experiences are reused, zero new exploration/EVENT calls, sixteen actor/model calls, four selected successes and eight draft rows; **fits=0**.

Relative to `/tmp/astra_cue_explicit_20260914_attempt1/run`, **only bank1/task1 loses its arrival and selection**. All seven other outcomes are unchanged. The saved actor reads the first listed address in every task, then ROUTEs the DID from that first record even when GOT does not match GOAL. Consequently it chooses the same port for both goals in each of the four pairs. This is commanded consultation without reliable conditional continuation, not autonomous cue mastery or a parametric-memory-read result.

| Metric | Previous explicit, frozen base | Saved actor, same explicit teacher |
|---|---:|---:|
| Tasks / retained EVENTs | 8 /8 | 8 /8 |
| At least one READ | 8/8 | 8/8 |
| Zero /one /two READ paths | 0 /7 /1 | 0 /8 /0 |
| External READ calls | 9 | 8 |
| Native actor calls | 17 | 16 |
| Actual GOAL arrivals | 5/8 | 4/8 |
| Read-containing selected successes | 5/8 | 4/8 |
| Selected student rows | 11 | 8 |
| Complete selected two-GOAL pairs | 1/4 | 0/4 |
| Wrong-GOAL first reads followed by a second READ | 1/4 | 0/4 |

## The changed raw path

Bank1/task1 requests GOAL `N_X3YCTVLT4S`. Both actors first emit `READ EVENT E_PX3IY2EX4N`. That record has GOT `N_3R5IRXYMLF`, not the requested GOAL.

- Previous explicit: global calls10–12 are `READ EVENT E_PX3IY2EX4N` → `READ EVENT E_U2VS57WTI2` → `ROUTE P_LPWBOOMGJG`; reaches the requested GOAL and is selected.
- Saved actor: global calls10–11 are `READ EVENT E_PX3IY2EX4N` → `ROUTE P_ABJJK3XBG5`; reaches `N_3R5IRXYMLF`, the other goal, and is not selected. The unread second address and a third actor-call slot were still available.

Selected bank/task identities are **0/0,0/3,1/0,1/2**. Their global selected call indices are **0,1,6,7,8,9,12,13**, producing four READ EVENT and four ROUTE targets. The previous explicit run additionally selected1/1. No other outcome comparison was expanded.

All four wrong-GOAL first reads now terminate with premature ROUTE, including the three already documented failures0/1,0/2,1/3. Every first record still has the correct AT/NODE and its DID is the committed port; the discriminating GOT/GOAL check is what fails on those four tasks. A read count alone therefore does not establish use of goal-relevant evidence. These diagnostics do not alter the frozen read-containing selector.

## Exact public/teacher/row replay

**`CPU_FROZEN_SAVED_ACTOR_CUE_REPLAY_PASSED`, exit0,16/16 callbacks consumed.** The replay uses only the captured frozen pure cue collector, controller, microloop and byte-boundary modules. Native wrappers are retained as source evidence and AST-parsed for the explicit guidance literal; they are never imported or executed. An import guard rejects torch, transformers, tokenizers, peft, GPU modules and scorer-named modules. No such modules were loaded.

All eight captured source files match their exact Git blobs at `c6acab47`; the replay does not use the concurrently edited working-tree wrapper. REQUEST has the existing `explicit_cue_strategy=true` and `phase=readout`. The replay selects the old runner's **EXPLICIT_GUIDANCE**, matching REQUEST, RESULT and the previous explicit run byte-for-byte. It neither invokes nor assumes a newer cue option or changed default.

Verification checks:

- Every reconstructed guided prompt equals the actual outer CALL prompt before returning the stored model response. There is no new generation.
- Both complete `BANK_00/CUE_COLLECTION.json` and `BANK_01/CUE_COLLECTION.json`, including failures, traces, rows and hashes, match the frozen replay canonically. Their concatenated reports exactly match `BANK_RESULTS.json`.
- Each of the eight selected assistant targets equals its actual captured CALL output. Each student prefix equals the reconstructed **public** history, not the guided prompt. Both original and explicit teacher strategies are absent from these prefixes, while genuine raw external-reader replies remain intact.
- All selected policies are prefix=`MASK_ALL`, assistant/EOT=`TRAIN`, target EOT=`<|im_end|>`. These are draft-row declarations, not a tokenization/mask or fitting admission audit.
- All16 generations are terminal, untruncated and end in the recorded EOT; outer callback errors are absent. Recorded totals are5170 prompt tokens and180 output tokens including EOT, versus previous explicit5604/192. No retokenization or performance claim is made.

The exact explicit teacher is still present in the actor's collection-time system prompt. Removing it from stored student prefixes does not make the observed actor behavior unguided or learned during this run.

## Same raw experiences, not recollection

All **14 original input-file bindings** agree between current REUSED_EXPERIENCES/RESULT, the previous explicit RESULT, and preserved original cue-collection files: original REQUEST/RESULT, two BANKs, two aggregate EXPERIENCE files and eight individual EXPERIENCE records. Current copied bank/experience files match both previous explicit and original files byte-for-byte.

All eight raw address-keyed EVENT strings and their memory hashes equal the previous explicit reports and current reused-memory map. The two zero-final-LF and six double-final-LF strings remain unchanged; the replay serves those actual bytes, not a normalized replacement. Public tasks, identifiers and displayed address/port lists are identical. `source_cue_rows_used=false` and `source_cue_scores_used=false` remain recorded in the reuse receipt; comparison of previous outcomes happens only retrospectively in this sidecar.

The reader is `EXTERNAL_RETAINED_EVENT_TEXT_NOT_MODEL_GENERATION`. The saved actor does not produce these reader responses parametrically. Eight events reused and four selected episodes are separate denominators; selected rows do not constitute newly generated experiences.

## Saved adapter binding and no-fit boundary

Actor kind is `FROZEN_SAVED_MEMORY_LEARNER`. It uses the pre-existing adapter at `/tmp/astra_microloop_lf_20260914_attempt1/sleep/adapter`, bound to collection `/tmp/astra_microloop_20260914_attempt2/collection`.

- Actual adapter file SHA256, checked remotely before and after capture: **`8597605e7e07b882f613e359decee0193275d4bd16eacac8cd5c45db75f25788`**. All adapter files declared by its original training RESULT also match their live file hashes. Weight bytes were hashed only, not copied or deserialized.
- Original training RESULT SHA256: **`c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f`**, matching current RESULT and the captured binding receipt. It records COMPLETE/train,200 prior updates, frozen base unchanged, and the same collection provenance recorded as current `actor_memory_collection`. Those200 updates belong to the prior adapter, not this cue collection.
- Current recorded in-memory adapter hashes before and after are identical: **`c08852cb6eb2c8bfa106cf2b7976fc5a2ba5f4cb06d79d53a3a3ac7222b865db`**. Current `fits=0` and `frozen_base_unchanged=true`.
- Frozen wrapper source verifies no trainable parameters for the collection actor, checks adapter state equality around collection and revalidates its original training/file bindings afterward. This sidecar verifies those receipts and static guards, not an independent in-memory model reload.

The comparison changes the actor from frozen base to an already trained saved adapter while retaining tasks, external memories and explicit teacher. A single loss of conditional second reading is observed; it does not establish a general adapter effect, forgetting mechanism, autonomous memory policy or qualification.

## Bounded preservation receipt

Local root **L**: `gpu_artifacts_local/astra_saved_actor_cue_first_result_20260914/`.

- **47 payload files,563,865 bytes**, all remote/local/remote-after hashes verified. Includes complete run evidence, three launch/source-binding receipts, eight frozen source files and two adapter-binding metadata files. No weights, base cache, process/resource dumps or unrelated roots; no overwrite of prior captures.
- `L/evidence.tar.gz`:74,718 bytes; remote/local SHA256 **`e1d277154bc73dd92b9b4d973163bacb95cb1b08aab207d0c9238c53cdc91ef5`**. Archive contains47 payload files plus its remote manifest.
- `L/capture/REMOTE_MANIFEST.json`: remote/local SHA256 **`0508f699019d823bc9c613c104859f974099cdd7297a36f7e754e43cd75d1ae2`**.
- `L/MANIFEST.json`: enriched local SHA256 **`d12346881b0294de50eaba2abba4676a014dab0659a52191dca102cc9af6e3a8`**; preserves original remote paths, sizes, source digests, local digests, recheck digests and hash-only adapter bindings.
- `L/ANALYSIS.json`: SHA256 **`85cff707e556941f4c9246038973c8a89a5e861b35c2b22f01476a4be6362c28`**; paired outcomes, raw action/read diagnostics, selected rows, memory identity and replay checks.

Key source hashes:

| Captured file | SHA256 |
|---|---|
| run/RESULT.json | `42695124fe60f2ced43b6af80a841d1d0f450d739f9b0c8561304dab044e2fec` |
| run/REQUEST.json | `b2315680ed5eeec7ad68c01d8a768705fde225b23baa45cdb67eff2fad418a23` |
| run/REUSED_EXPERIENCES.json | `061a17c7f1814a62f38c82e51f9745eefa2bbdcb6ce272ca6071de325138582b` |
| run/BANK_RESULTS.json | `83e7567fd7941d78ea094d2e7ef7e331453b0fef88f6b2edac3dcbe21c203a52` |
| source/gpu/astra_experienced_event_cue_collect.py | `44120337b1bad9ee750e4af8f1d26fffeaa442742ee7db10b569629be518d6e8` |
| source/organism_v6/experienced_event_cue_collection.py | `82369dc5ee234a89cad22e2814fe33bc8fdbb47d4135fca037b12f67f62e3f37` |

`L/REPLAY.py` is a local recorded-callback replay utility, not a native runner; `L/LOCAL_SHA256SUMS` binds that utility, the derived evidence/receipts and this memo. No current-wrapper changes or unrelated comparisons were needed.
