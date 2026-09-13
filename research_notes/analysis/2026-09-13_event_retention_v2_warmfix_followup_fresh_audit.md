# Fresh audit: EVENT-retention-v2 warm repair and descendants

Date: 2026-09-13 PT  
Auditor: independent Codex subagent (`warmfix_followup_audit`)  
Scope: commits `21efea43e46a1d51ebdb3d2e4b6c28cf996cd814`,
`fad676bb272e8deffaf87aa651b14ce0c3536ce0`,
`7ee0be92bebe2833c507c1d0ea75785a37416d9d`, and the subsequently required
native-name repair `3dc9edf86e123203c00c0dff5aa2bf4f253e52e6`;
node-2 acquisition/follow-up evidence; uncommitted final reducer. I made no
model or GPU call and did not edit builder-owned source.

## Executive verdict

1. **Acquisition remains PASS and is unaffected.** Each learner seed 0/1/2,
   over the same authenticated exposed DEV bank, has C0 `A=0/4, B=0/4` and
   A200 `A=4/4, B=0/4` at both W0 and W8, with zero truncations. A200 starts
   cold, so none of the warm-path repairs can change this completed evidence.
   It proves repeatable selective four-fact acquisition at this dose only.
2. **The sparse dtype-conversion repair in `21efea43` is semantically right,
   but warmfix2 is operationally NO-GO.** `train_adapter_v3._warm_initialize`
   records conversion entries only when the source and initialized dtypes
   differ. The repaired validator implements that exact sparse rule while
   retaining complete source/initialized tensor coverage, LoRA suffix checks,
   hash checks, shape equality, same-dtype byte equality, and reconstruction
   from pinned parent weights when conversion occurs. Real tiny-Qwen2/PEFT CPU
   tests covered empty, partial, and full conversion maps and corruption.
   However, those tests passed PEFT-wrapper names to the validator and missed
   the real caller namespace.
3. **Warmfix2 relocation/source compatibility is sound.** The original outer
   and relocated regular-file outer are byte-identical at
   `88eb6775f481c02b9888ebdc17e3db49d6fc388a50ff35f94231d76693828360`.
   The repair receipt is pinned at
   `ba1ed31aff1021d6e4ea02c90eb935c0ae433bb0c4ea30922e56f5229b0888e8`.
   The replacement fit is `8dc32cbcca829a226dd98151d64da46ab0c9e110a7a2a45b40f0071329959e1e`,
   versus frozen original
   `4112899215ded5191b697cad9bf912bb72a65b026779f3d6dbbd548b36d0aa19`.
   AST comparison removes exactly the single `validate_warm_tensors` body and
   rejects any other structural delta; the overlay keeps all other sources as
   frozen aliases and reuses the original material/checkpoint bytes.
4. **Attempt2 is a terminal preworker failure and must never be reused.** All
   three roots stopped because the controller did not present an explicitly
   empty `CUDA_VISIBLE_DEVICES`. `worker_identity`, return code, and stage
   inventory were null/null/empty: no worker, model, fit, or GPU work occurred.
   `7ee0be92` correctly sets the offline flags plus `CUDA_VISIBLE_DEVICES=""`
   inside the controller and charges those failed preflights.
5. **Attempt3 is a terminal post-fit failure and none of its adapters is
   admissible.** All three B200 workers executed 200 updates, 800
   presentations, printed `TRAIN_DONE` (loss 0.0003), and wrote approximately
   80.8 MB adapter checkpoints. They then failed the post-fit validator with
   `full parent tensor coverage differs`. Each archive says
   `partial_checkpoint_not_eligible=true`, lacks `fit/completed.json`, has an
   outer `FAILED` collection/return code 1, and has no readout. GPU/process
   release did complete. These artifacts cannot be post-hoc sealed, read out,
   warm-started, or promoted. A fresh root from the unchanged measured A200 is
   required.
6. **The exact attempt3 cause is PEFT namespace mismatch, not dtype or
   learning failure.** The receipt/saved state uses names such as
   `base_model.model.model.layers...lora_A.weight`; `run_phase` recomputed
   trainable names from the mutated, unwrapped cold base after training, whose
   namespace omits PEFT's `base_model.model.` wrapper. Counts were both 392,
   but the raw strings differed. This is why training finished and the
   postcondition alone failed.
7. **`3dc9edf8` plus the evidence committed in `c38bae5f` closes the native
   caller regression: warmfix3 itself is GO.** The fix canonicalizes only
   PEFT's known `base_model.model.` prefix
   and `.default.weight`, rejects canonical-name collisions, and retains all
   earlier coverage/hash/shape/dtype checks. Its fit hash is
   `3702fdc21c052767e41e98666dd09d5ce67c4755561a327c123e74d7ca54a86a`.
   Five real tiny-Qwen2/PEFT CPU tests now use both the mutated unwrapped
   caller names and wrapper names, pass empty/partial/full conversion cases,
   and reject missing, corrupt, and colliding coverage. The exact warmfix3
   repair receipt is
   `916ed0cf44902d426d2a827be3e7d973f093b1a13822cc5b64e7e913600155bd`.
   A no-fit/no-model native preflight at
   `756222b3385e45ab8eb964ec1cd40e642b16447d1c002c9ee0c12f4dbd96d995`
   validated all 12 planned outer inputs and all 392 warm tensor receipts for
   each seed without promoting the failed checkpoints.
8. **Evidence acceptance remains NO-GO because the final reducer is not yet
   committed and does not yet understand the failure chain.** The current
   worktree reducer is strong on raw response rescoring, stage/fit/checkpoint
   inventories, source relocation, repair-receipt/AST joins, exact states, and
   paired reductions. But its `prior_failure_evidence` still accepts only the
   earlier zero-worker failure and requires the previous manifest to have no
   earlier failure. It therefore rejects the real attempt4 ancestry
   (attempt2 preworker -> attempt3 diagnosed post-fit -> fresh attempt4) and
   does not validate `prior_failed_work`. It and its tests remain uncommitted
   at this audit snapshot.

**Exact present decision:** acquisition **GO/PASS**; warmfix2 descendants and
attempt2/attempt3 roots **terminal NO-GO/no reuse**; the warmfix3 validator,
overlay, and native preparation are **code/runtime GO**. Nevertheless, this
independent audit **withholds execution and evidence acceptance GO** because
the reducer must first be committed, terminally green, and independently
audited with complete failure ancestry and failed-work accounting. The builder
subsequently launched attempt4 seed0 under its separate standing authority;
that does not change this acceptance gate. Seeds1/2 should remain held, and no
seed0 output should be interpreted, until the reducer gate passes.

## Sparse conversion semantics

The trainer does the following before any update:

1. Loads exactly one pinned parent adapter tensor file.
2. Constructs a fresh PEFT wrapper and obtains its expected state.
3. Requires identical nonempty key sets and exact shapes.
4. Converts each source tensor to the corresponding expected dtype.
5. Loads the state, reads it back, and requires the complete loaded inventory
   to equal the converted inventory.
6. Records `dtype_conversions` only for tensors whose source and loaded dtypes
   differ.
7. Verifies LoRA-only trainability and a frozen base, then starts a fresh
   optimizer without restoring optimizer state.

The `21efea43` validator matches steps 3-6. For unchanged dtype it requires the
whole inventory record (`shape`, `dtype`, SHA-256) to remain identical. For a
changed dtype it requires an exact source/initialized dtype pair, reloads the
pinned parent safetensors/bin file, recomputes its source inventory, performs
the recorded dtype conversion, and recomputes the initialized inventory. It
also rechecks the parent file inventory before and after. Attempt3's actual
receipts had 392 source tensors, 392 initialized tensors, and zero dtype
conversions; the failure occurred earlier in the caller-name join.

The earlier four real tiny-Qwen2/PEFT CPU tests are still useful evidence for
the conversion semantics, but they were not evidence for the native
`run_phase` namespace. `3dc9edf8` adds the correct regression test, and the
five-test real-dependency run committed in `c38bae5f` executes it using
trainable names obtained from the mutated cold-base caller. All five pass in
3.928 seconds. This closes the native naming/dtype validator gate.

## Runtime overlay and source boundary

- Warmfix1 used a symlinked outer and was correctly refused by the outer's
  absolute, unaliased regular-file pin. No worker launched.
- Warmfix2 copies the outer bytes into a regular file and keeps them identical;
  it does not change outer behavior. Only the fit validator differs.
- The runtime loader permits only the original frozen source root or the exact
  configured repair root. It rejects preloaded modules from another checkout,
  requires all non-repaired files to resolve to frozen originals, verifies the
  repaired fit and relocated outer paths, and maps their source identities back
  to the original frozen campaign identities where compatibility requires it.
- The attempt3 standalone operator was actually
  `ec221bd1983891e92b429a6f72dd9ff8b1d09f909f5bac4fbcb8070d7b04965f`
  (`7ee0be92`). The warmfix2 fit/outer/repair bytes on node 2 matched the values
  above.
- Warmfix3's fit file is
  `3702fdc21c052767e41e98666dd09d5ce67c4755561a327c123e74d7ca54a86a`;
  its exact repair receipt is
  `916ed0cf44902d426d2a827be3e7d973f093b1a13822cc5b64e7e913600155bd`.
  Prepared attempt4 manifests are
  `c4db529691b6ffe4fc32d015cdbfd10f6ae6c96f17b26d4eead9401e77fa795a`,
  `9e3d91f3377c58f24f062cac5742e4d724e2f9c17bbe394b25a383502d74a33c`,
  and `a3fc00c8b982534d1164e857d983af731d8b9272af7ff6e307ead45fe35f4882`
  for seeds 0/1/2. Seed0 was launched after preparation under the builder's
  standing authority; seeds1/2 remained unlaunched at the last inspection.
- The reducer's newer `runtime_cold` logic independently pins the repair
  receipt, verifies root/path identities, re-runs the AST boundary, requires a
  byte-identical relocated outer, and proves that translating repaired runtime
  sources back to originals produces the exact cold input. The final committed
  reducer should additionally bind the approved warmfix3 repair revision/hash
  rather than accept any arbitrary alternate validator body merely because it
  is AST-local.

## Descendant design and arithmetic

All warm descendants must fork the same immutable, measured A200 parent; the
failed attempt3 checkpoint is never an input. The four planned states per seed
are:

| State | Start | New work | A exposure | B exposure | Interpretation |
|---|---|---:|---:|---:|---|
| `B200_NEW_DOSE` | measured A200 | 200 updates / 800 presentations | 200 | 200 | B-dose matched |
| `B400_FIXED_WORK` | measured A200 | 400 / 1,600 | 200 | 400 | update/work matched |
| `REPLAY400` | measured A200 | 400 / 1,600 | 400 | 200 | replay arm |
| `CLEAN_CUM600` | clean C0 | 600 / 2,400 | 400 | 200 | clean cumulative descriptive comparator |

The successful follow-up plan is four new fits, 1,600 updates, 6,400
presentations, and 64 readout calls per seed. Including acquisition gives five
fits, 1,800 updates, 7,200 presentations, and 96 calls per seed. Attempt3 added
one failed physical B200 fit per seed: 200 updates and 800 presentations, zero
calls. Therefore a later successful rerun would make the all-in physical total
per seed **six fits, 2,000 updates, 8,000 presentations, 96 calls**, or over
three seeds **18 fits, 6,000 updates, 24,000 presentations, 288 calls**. These
failed costs must be reported separately from the fixed scientific contrast.

`REPLAY400-B200_NEW_DOSE` is dose-matched for B but not total work.
`REPLAY400-B400_FIXED_WORK` is matched for update/presentation work but not B
dose or target tokens. `REPLAY400-CLEAN_CUM600` crosses a checkpoint/reload and
fresh-optimizer/dropout boundary, so it is descriptive rather than a pure
causal replay comparison. `NO_WRITE` is C0 and not compute-matched.

Input/output separation is otherwise strong: fresh nonoverlapping campaign,
source, and output roots; exact material/model/base/environment/source pins;
phase-specific output directories; immutable measured A200 predecessors;
clean-only C0 parent for cumulative; no B200 outcome gate; no automatic retry
or promotion; per-stage and per-seed deadlines; exact post-stage GPU/process
release checks. The failed roots remain immutable evidence, not resumable work.

## Reducer acceptance checklist

Before any result is accepted, the committed reducer must:

- verify the exact approved warmfix3 receipt, replacement hash, regular outer
  hash, repair revision, and one-function AST boundary;
- validate all tensor key coverage, hashes, shapes, dtypes, sparse conversion
  keys, and same-dtype equality, with the executed validator/source tied to the
  exact parent checkpoint bytes;
- validate the full attempt2 -> attempt3 -> fresh-run ancestry, proving
  attempt2 had no worker and attempt3 was exactly the diagnosed, released,
  unqualified post-fit failure;
- charge attempt2 elapsed time and attempt3 elapsed time plus 1 fit / 200
  updates / 800 presentations / 0 calls per seed, without folding failed work
  into the planned arm counts;
- re-score all raw readout captures and validate exact token/stop/route/load/
  close/custody evidence;
- require all four planned fit/readout branches, exact raw denominators, and
  three learner seeds on the same single bank;
- label all reductions descriptive and preserve the exclusions: no independent
  fact-bank replication, significance, general retention, generalization,
  composition, parenting, or whole-organism claim.

Until those conditions are met, no warm descendant result is admissible even
if another fit appears numerically successful.
