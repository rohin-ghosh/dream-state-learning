# Exact phase2 retention ports — CPU-ready, not staged

**C0, Astra7, P7, P3 and C2 are ready for Main's separate source-stage/receiving work.** Each isolated variant passes the unchanged **17 phase2 retention tests + five existing contracts + five additional preservation tests**, with no skips: **135 passing checks** across five processes. This sidecar performs no live-source writes, native signals, dispatches, parent deliveries or git commits.

The prior metric audit is final: C2's original distinct counts and narrow within-block arithmetic comparison stand; only the broad scientific claim remains retracted. Its final receipt is `../post_recovery_c2_age_eval_20260918/REPORT_VALIDATION.json`. No metric-audit artifact is changed by this sidecar.

## Handoff

`MANIFEST.json` indexes all five hash-bound readiness receipts. `HASHES.md` gives every exact per-file before/after SHA256. Each named variant directory contains:

- `fork/gpu/orch_r184_think_act_learn.py`
- `fork/organism_v6/orch_r124_train_history.py`
- `fork/organism_v6/orch_r125_continual_stream.py`
- `RETENTION.patch`: minimal unified diff, rooted at `gpu/` and `organism_v6/`; forward application against that variant's preimage and reverse application against its overlay both pass `git apply --check`. These checks do not apply changes.
- `preimage/`: the exact three original modules decoded from the supplied INVENTORY2 receipt, with both embedded file hashes and full-source pins verified.
- `SOURCE_PINS.before.json` and `SOURCE_PINS.after.json`: full captured/proposed closure maps. Exactly the three retention files change; every other source pin and key remains unchanged.
- `READY.json`: exact source/root/guard/inventory provenance, before/after hashes, patch hash, tests, and explicit not-staged status.
- `TEST_RECEIPT.json`, `TESTS.log`, `LEGACY_TESTS.log`, `PRESERVATION_TESTS.log`: module paths/hashes, independent process ID, exact test counts and log hashes.

**C2 first:** `C2/READY.json`, `C2/RETENTION.patch`, `C2/fork/`, `C2/SOURCE_PINS.after.json`, `C2/TEST_RECEIPT.json`. These artifacts were finalized before the other four and are not rewritten by the aggregate handoff.

| Variant | Node | Full source pins | Unchanged pins | Tests |
| --- | --- | ---: | ---: | --- |
| C0 | node2 | 2292 | 2289 | 17 + 5 + 5 PASS |
| Astra7 | node2 | 2295 | 2292 | 17 + 5 + 5 PASS |
| P7 | node4 | 175 | 172 | 17 + 5 + 5 PASS |
| P3 | node4 | 177 | 174 | 17 + 5 + 5 PASS |
| C2 | node5 | 183 | 180 | 17 + 5 + 5 PASS |

## Exact port and preservation

The reference is `../post_recovery_pair_evidence_20260918/phase2/REPAIR.patch`, SHA256 `7053d826efcfbc6ee6a8f44f36a8dbe8c179dd4d9ffb485a7ac548a075e876f1`. Every retention addition/replacement is taken from this patch; only application context is adjusted for the existing variants. The overlay files were edited with `apply_patch`, not by replacing them with another variant's modules.

- C0/Astra7/C2 keep their existing `interrupt=None` stream-step parameter and all preemption/abort behavior, while adding the optional `retained_parent_event_id` argument.
- P7/P3 keep their own driver fields and stage paths. No missing reading/preemption machinery is imported from newer drivers just to make the patch fit.
- P7's language-scope activation and annotation, P3's R227 all-child-row behavior, C0/Astra7/C2's R227 branches, and each custom CPU bridge remain intact where originally present.
- History masking, token thresholds, explicit human pins, input admission, training flags, sleep/checkpoint/restore methods, checkpoint-tail source, frozen/native variants and receiving guards are unchanged except for the exact reference retention delta in the three specified modules.
- An AST inverse removes only the known retention additions and reproduces each complete preimage AST. The byte-level expected-delta check separately requires the exact reference edits with uniquely matching variant context. This checks preservation of untouched branches, not merely a few matching strings.
- Additional synthetic checks cover existing interrupt interfaces, an interrupted generation with retained input, nontraining response behavior, checkpoint roundtrip and unchanged model identity. P7/P3 retain their original absence of the interrupt interface; the tests do not add one.

The transient retention handle still follows the reference patch: newest source-bound parent actually rendered in THINK, carried into current THINK/ACT, cleared for LEARN/new wake, no permanent history pin and no new training row. Hard budgets and masking are unchanged. This is the same scoped implementation repair, not a new retention design or a scientific-success claim.

## Isolated tests and dependencies

The copied `test_retention.py` and `run_checks.py` are byte-identical to phase2. The five selected legacy contracts are frozen under `legacy_tests/`, with hashes in `TEST_INPUTS.json`. Each `validate_variant.py` invocation runs in a fresh process and verifies that all three tested canonical modules resolve to that variant's `fork/`, not a live or sibling module.

Every imported runtime-support module used in the final checks matches that variant's captured full-source pin. P7 required its older `orch_r125_plain_context.py`: the exact pinned bytes were recovered from an existing local immutable snapshot and retained under `P7/test_support/`. `P7/TEST_SUPPORT.json` binds the origin and SHA256. This is **test-only unchanged support**, not a fourth overlay file or a proposed source-pin change.

Reproduce a single variant without any remote action:

```bash
python3 -B research_loop/workers/post_recovery_retention_ports_20260919/validate_variant.py C2
```

Replace `C2` with `C0`, `Astra7`, `P7` or `P3`. Re-running validation rewrites that variant's test logs/receipt; any readiness receipt must subsequently be re-bound deliberately. The final handoff is hash-bound, not a claim that mutable logs can be changed underneath it.

Preserved diagnostic attempts: `C0/PRESERVATION_TESTS.initial.log` / `TEST_RECEIPT.initial.json` record a test-helper AST-stripping error fixed without changing the overlay; `P7/TEST_RECEIPT.unpinned_support.json` records the initial presentation-dependency mismatch. Final receipts include the corrected AST check and pinned support. Neither diagnostic is presented as deployment evidence.

## Main owns receiving and adoption

These are **local CPU-ready ports only**, bound to the supplied node2/node4/node5 INVENTORY2 observations, not a fresh assertion of live-source identity. Main must reverify its actual full source closure and exact preimages, stage into a new immutable source root, preserve all unchanged full-source pins, and supply its separately authorized source-stage/plan/receiving hooks. Nothing here edits a guard or plan, establishes a live adoption hook, restarts a process, or authorizes an arbitrary mid-THINK transition.

No model is sampled and no GPU scientific result is claimed. Actual receiving/LOAD evidence and a new source-bound parent → THINK REQUEST → ACT REQUEST trace remain Main's post-adoption checks; the newly reported frozen-pair loss is not upgraded to a repaired live outcome by these CPU tests.
