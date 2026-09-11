# Multi-key writer gateway V5 — finite systems repair addendum

Status: proposal only. No implementation or execution authority.

## 1. Bound base and preservation rule

This addendum normatively inherits `research_loop/changes/chg_20260911_multikey_writer_gateway_v4/exact_scope.md` at SHA-256 `f6beb7d23439ecc0d08152d3e63b8360db72b4fe3748e14ed36ad9ed3d81b2b4`.

V5 changes only the four contracts below. Every V4 scientific parameter, root and complement geometry, source rule, DREAM derivative, writer recipe, target and mask rule, parser and overlay, seed relation, workload identity, binary64 reducer, hexadecimal threshold, fixed-panel statistic, ordered root label, resource cap, permitted reading, claim exclusion, and authority boundary remains unchanged. The V4 claim remains limited to development-only supervised endpoint-policy carriage on correctness-selected seen tool×mode keys. V5 adds no claim about autonomous credit assignment, unseen-key generalization, capacity, retention, qualification, parenting, C11, or population inference.

## 2. Total run-status partition

Let `source_started` mean that the run-global first source request has been submitted. Let `terminal_stop` mean that a fail-closed stop receipt has been committed. Exactly one `run_status` applies:

- `PLANNED`: `source_started=false` and no preflight failure has terminalized the run.
- `NOT_RUN`: `source_started=false` and a preflight failure has terminalized the run.
- `TERMINAL_LABELED`: both root scientific labels are non-null.
- `STOPPED_UNLABELED`: `source_started=true`, `terminal_stop=true`, and at least one root scientific label is null.
- `RUNNING`: `source_started=true`, `terminal_stop=false`, and at least one root scientific label is null.

`RUNNING` includes mirror verification, compilation, fitting preparation, the four-commit barrier, trusted selection, and every quiescent interval between committed stages. A root may remain `SOURCE_READY` or `FIT_COMMITTED` during these intervals. The existing V4 stop-reason, nullable-label, `scientific_pair`, and `run_pass` rules are otherwise unchanged.

## 3. Phase-specific execution dispatchers

Add three capability-bearing principals and one immutable information object.

`selected_execution_call` contains only: entry ID; request ID; prompt bytes and hash; optional teacher-forced continuation bytes and hash; condition ID; adapter identity and hash or `OFF`; replicate ID; condition-common seed; frozen decoding limits; and the hashes needed to verify this envelope. It contains no raw map, admission, bank index, unselected entry, training row, lived history, prior result, or score.

- `source_execution_dispatcher` reads only one frozen source request, its derived seed, the continuing public session, and the frozen source-model identity/capability. It writes only the immutable raw transport result to the public-trajectory path. It cannot read the sealed map, admission, evaluation bank, compiled rows, adapters, evaluation results, or scorer outputs, and cannot alter request bytes, seed, order, or retry identity.
- `fit_execution_dispatcher` reads only one adapter-fit identity, committed compiled rows, the frozen writer recipe, matched fit seeds, node/device binding, and frozen-model capability. It writes only that adapter's stage state and hash. It cannot read either map, admission, uncompiled lived history, evaluation bank or subset, other adapter contents, evaluation results, or scorer outputs, and cannot alter rows, masks, order, seeds, recipe, or fit identity.
- `evaluation_execution_dispatcher` reads only one immutable `selected_execution_call`, verifies every bound hash, mounts its already-bound condition and adapter, and writes one immutable raw result. It cannot read either raw map, admission, full bank/index, unselected entries, compiled rows, lived history, prior results, or scorer outputs. It cannot alter or reorder prompt or continuation bytes, condition, adapter, replicate, seed, decoding parameters, request identity, or identical-byte retry identity.

Generators continue to receive only prompt bytes and, for teacher forcing, the bound continuation bytes. They do not receive condition, seed, adapter, capability, or envelope metadata. No dispatcher may expose capabilities, serialize forbidden objects through metadata/logs/exceptions/filenames/caches, form cross-phase aliases, accept feedback from a result or scorer, reseed, reorder, or select a mutable condition.

The V5 visibility matrix is the Cartesian product of the V4 objects and principals plus `selected_execution_call` and the three dispatchers. Every new cell is forbidden except the explicit allowlists above. Tests must prove the product complete and mutation-test the denials.

## 4. Selected-only immutable bank dereference

After admission is final and all four adapter commits exist, `trusted_evaluation_selector` may read the sealed bank index and `source_admission`, compute the canonical selected entry IDs, and then dereference only those immutable entry payloads. Before dereference it verifies the bank-root hash; before emission it verifies every selected entry hash. It emits the stable, order-preserving `selected_evaluation_subset` and immutable `selected_execution_call` objects.

The selector cannot inspect an unselected entry payload or render, mutate, normalize, repair, append, delete, reorder, resample, recount, reseed, recondition, or replace any entry. A missing, extra, duplicate, aliased, or hash-invalid selected entry fails closed. All other V4 selector restrictions remain unchanged.

## 5. Global run boundary versus per-root scientific boundary

The run-global first submitted source request alone sets `source_started` and separates `PLANNED/NOT_RUN` from post-source run semantics.

A root may receive scientific label `SOURCE_INVALID` only after that root's own first source request has been submitted. If one root has started the run but the other root has not, a newly discovered fault in the untouched root leaves that root `NOT_STARTED` with a null scientific label and terminalizes the run as `STOPPED_UNLABELED` under the applicable existing non-scientific stop reason; it cannot fabricate `SOURCE_INVALID` for the untouched root. Once a root has submitted its first request, its root-local source, provenance, admission, or post-source compiled-geometry faults follow the unchanged V4 `SOURCE_INVALID` reducer.

## 6. V5 acceptance-test deltas

- `MWG5_T01`: V4 T01 plus immutable dispatcher-envelope identities, hashes, conditions, seeds, order, and call-graph checks.
- `MWG5_T02`: V4 T02 plus the three dispatcher rows, forbidden ingress/feedback/alias tests, selected-only dereference, and denial of unselected-entry content.
- `MWG5_T03`: V4 T03 plus all combinations of run-global source-started and per-root source-started, including R0-started/R1-untouched with R1 label null.
- `MWG5_T04`: V4 T04 unchanged.
- `MWG5_T05`: V4 T05 unchanged.
- `MWG5_T06`: every V4 numeric/reducer fixture plus exactly-one run-status coverage before source, after source commit, during compilation, during the barrier, during selection, after four commits before evaluation, during evaluation, at a stopped unlabeled terminal, and at a two-label terminal.
- `MWG5_T07`: V4 T07 plus dispatcher isolation, residual `RUNNING`, selected-only dereference, unselected-entry denial, and untouched-root stop-reason fault injection.
- `MWG5_T08`: two fresh independent reviewers must accept identical V5 bytes and T01–T07 receipts before a later, separate execution ratification.

## 7. Authority boundary

Exact ratification of a later PASS consensus may authorize only source authoring for `organism_v6/multikey_writer_gateway.py`, `gpu/multikey_writer_gateway.sh` without execution, deterministic CPU/fault tests in `tests/test_multikey_writer_gateway.py`, and implementation review artifacts inside the V5 change directory.

This proposal does not authorize model or tokenizer execution, benchmark/source generation, training, LoRA/adapter/checkpoint work, GPU use, parenting, resource acquisition, C11 work, scientific execution or claims, release, or submission. A later immutable execution manifest, two fresh implementation reviews, and separate exact human execution ratification remain mandatory before the gateway can run.
