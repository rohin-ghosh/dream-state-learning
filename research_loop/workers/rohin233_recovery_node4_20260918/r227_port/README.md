# R227 receiving ports: tested copies, not live adoption

September 18, 2026. Authoritative policy: `bb1e9a9033979d50ed97072675515f7290de1237`.

`C2.patch` and `P7.patch` are source-specific, four-file deltas, **not a
general patcher**. `MANIFEST.json` binds original and changed file hashes,
each patch, and the passing receiving logs. The exact original closures had
181 and 175 pinned files, respectively; all other pinned bytes are unchanged.
No resident source, native process, P3 source, or current replay was changed.

## Reuse for Main's P3 copied closure

Use the delta hunks, never wholesale replacement of the trainer or driver.
Run a patch check only inside a new copy. A conflict requires porting the
affected hunk; do not force it or discard P3-specific code.

The reusable pure plan helper is `../r227_plan.py:proposed_plan`. It sets
`learn_row_policy=R227_ALL_AUTHENTIC_CHILD_ROWS_V1` in both plan and THINK,
removes semantic selectors, preserves execution `code_policy`/CPU gate and
all dose/identity/budget fields, rebases the unchanged startup context into
the copied source, and removes the already-consumed wall-extension authority.
Its output is only a prospective plan. It must not replace the current plan
during replay.

Exact code seams:

1. `gpu/orch_r125_continual_native.py`: import policy helpers;
   `validate_plan` checks policy agreement; receipt-only
   `candidate_row_filter_policies`; `NativeChild.sleep` bypasses semantic
   filters and plain-context scaffolding exclusion under R227, but preserves
   technical encoding, provenance, optimizer, and checkpoint behavior.
2. `gpu/orch_r184_think_act_learn.py`: `validate_config` validates effective
   policy config and permits the policy key; `run_loop` checks trainer/driver
   agreement. CPU dispatch, console handling, correction/continuation, and
   deep-work implementations are not replaced.
3. `organism_v6/orch_r125_plain_context.py`: `eligible_rows` receives optional
   `exclude_scaffolding=True`; only R227 callers disable that semantic test.
4. `organism_v6/orch_r227_learning_policy.py`: exact authoritative new module,
   SHA256 `08edb1be7563331df3273abb5a2010dd9273b041708521e084d3dcb75a82e503`.

P3 must retain its existing `r212_prose_replay` and R233 recovered-boundary
guard verbatim, including any custom statements inside a touched function.
These patches do not establish P3 compatibility; Main owns that receiving
check. No shared endpoint or source edits were made here.

## Receiving evidence

- P7: eight receiving tests and five console/continuation seam tests pass.
- C2: eight receiving tests and ten seam tests pass, including five deep-work
  cases with R227 explicitly enabled.
- Forty local operator tests pass, separately from runtime receiving tests.
- Synthetic CPU tests cover substantive Chinese punctuation, fullwidth,
  repetition, meta, quoted labels, historical veto annotations, genuine
  console rows, masking/provenance, and technical special-token rejection.
- Synthetic AdamW checkpoint/audit/restore/next-new-only sleep preserves
  history and optimizer/Python/CPU RNG. No actual live GPU update is claimed.
- Existing CPU bridge calls forward unchanged code/root policy under mocks;
  this is not a new actual live CPU-tool execution receipt.

Reusable runners (sibling files):

```text
r227_receiving_tests.py --source COPY --original ORIGINAL_COPY --plan PLAN \
  --support r227_port/support --life P3
r227_compatibility_tests.py --source COPY
```

Use the receiving venv with CUDA disabled. The source copies' existing test
fixtures are required. The first runner checks all other pinned files and
untouched function ASTs. `--deep-work` adds C2's five deep-work regressions.
The support fixture is bound to the authoritative commit in the manifest.

Earlier V1 failures are preserved privately: startup-context path rebasing
was a real staging defect, now fixed; a console fixture missed its required
stage boundary policy, now fixed. The first extra deep-work invocation also
accidentally included imported legacy content-filter expectations: those two
expected R227 incompatibilities were not rewritten. The focused deep-work
class and the compatibility runner both pass.

## Remaining adoption work

After current restoration and CPU-parent receipts, coordinate a fresh,
coherent COMPLETE. Preserve whole state and same journal. Bind the new
source manifest, startup file, CPU bridge/source-parent metadata and guard
without weakening exact source checks; then use the supported current-state
continuation. No historical replay, stale saved boundary, or extra restart
is authorized merely by this receiving result.

Actual LOAD plus new recipe/eligibility with `active_semantic_filters=[]`
and UPDATE/COMPLETE are still required to call R227 live. Current resident
P7/C2 retain older semantic filters. A zero-exclusion batch is not proof that
filters are disabled.
