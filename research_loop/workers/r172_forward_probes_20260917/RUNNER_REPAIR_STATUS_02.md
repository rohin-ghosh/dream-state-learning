# Runner/design repair handoff — September 17, 2026, 09:10 PDT

## Completed local candidate work, not execution approval

- `RUNNER_CPU_01.txt`: **53 local runner/design CPU tests pass** with CUDA hidden; no provider/model/remote operation. Tests cover the unchanged complete checkpoint verifier and charged adapter rereads, mutation rejection, manifest escape rejection, exact host/device and array-lease handling, full source-closure requirements, immutable ON/OFF capture-pair reservations, no retries, oldest-ready per-life ordering and missing-custody isolation.
- Shared candidate files are `r172_runner.py`, `r172_scheduler.py`, `design.py`, and `test_runner_preparation.py`. Their new acceptance tests are author-side evidence, not independent approval. R172 `PROPOSAL.json` and the deployed capture/source attempts remain unchanged.
- `PREPARATION_CPU_07.txt` preserves the combined run's **89 tests, 1 failure and 3 errors**. Those four transfer-fixture failures use the old receiving API while Ampere's new API requires explicit identity/accounting arguments. No failure is relabeled as a pass; this author does not edit Ampere's transfer/prep_common files after the reassignment.

## Integration still required

- Runner verification expects a `receiving_read_allowance` reference to `GLOBAL_PRECHARGED_RECEIVING_ALLOWANCE`, with exact life/capture/proposal binding, a 64-hex allowance ID, and metadata/adapter ceilings. Each ceiling must match a copied original precharged global reservation. Original and receiver-copy hashes must be identical; the remote copy lives under `control/global_reservations/`. Original paths are preserved as provenance, not rewritten and treated as original receipts.
- Scheduler skips missing registration, private witness freeze or per-checkpoint allowance before consuming a job once-marker. The allowance path is `receiving_allowances/<life>_<sleep:06d>.json`. A held life or absent baseline does not block a ready peer. Final readiness must be joined to Ampere's validated transfer/custody API, not inferred from file presence alone.
- Native model-loading reads also reserve adapter bytes before invoking the unchanged loader. Complete metadata/source-closure reread accounting and the actual receiving/model-loader read contract still need joint validation under the finite ledger. The allocated source envelopes cannot be silently reused for extra verification or loader reads.
- Actual receiving CPU, complete real source/allocation custody, private rubric freeze and a fresh independently bound review remain outstanding. `REVIEW_FORWARD.md` remains REWORK_REQUIRED; this handoff does not alter that verdict. No scheduler/model/provider launch is authorized or attempted.

## R176 priority proposal

The separately fixed C2 sleeps33–38/C5 sleeps29–34 proposal and first CPU candidate are in `../r176_retelling_retention_20260917/FEASIBILITY.md`. Its 72-call/24-process/90-minute ceiling is proposed only. The current R172 runner is deliberately still bound to R172's root and 24-life campaign; R176 needs a separate bound admission/ledger adapter around the unchanged generator, not a monkeypatch of the consumed/future R172 campaign.
