# Bounded independent review: early findings

Initial source review September 19, 2026, 13:25–13:29 UTC. Implementation is still
changing. This is an engineering/scientific risk review for Main, not a new
human-ratification requirement and not a reason to stop preparation.

## Ready in the inspected design

- The declared diagnostic is seeds **23301/23302**, three preserved sources
  (base, C2 sleep51, C2 sleep117), three development scenes, and **18,432 total
  generated tokens**. It is explicitly sampling variability, not three
  independent training lineages or fresh-scene transfer.
- `sampling_cells.py` delegates the per-cell behavior to the pinned original
  contract. The new `sealed_runner.py` instead reuses the original player and
  judge function code with a seed-aware namespace and tagged request/reply
  receipts. That different executable path needs its own tests; testing only
  `sampling_cells.py` would not establish runner equivalence.
- `execution.py` and `dispatch_sampling.py` use the original V4 source freeze,
  shared `DISPATCH.lock`/GPU-UUID claims, original protected-process and GPU
  admission functions, and transient systemd confinement. This is more than a
  file-lock-only GPU allocation. No execution/custody proof is established by
  those source-level observations alone.
- Fresh deterministic diagnostic/job identities are separate from the consumed
  original jobs. Platform submission failure is terminal; the inspected route
  has no alternate-provider/platform fallback or automatic resubmission.

## Concrete issues to address while implementation continues

1. **Enforce the loaded generation identity, not just weight hashes.** The
   inspected `dispatch_sampling.validate_completion` compares only
   `base_sha256` and `adapter_state_sha256`. Original `LOADED.identity` also
   contains `tokenizer_backend_sha256`, `chat_template_sha256`, `decoder`, and
   `library_versions`. The original backend still loads the mutable receiving
   tokenizer/venv and records those fields; source-code pins alone do not
   enforce their equality. Reject a mismatch before generation where feasible,
   and at minimum do not label it a valid unchanged-protocol completion. Test
   tokenizer, chat-template, decoder, and library-version mutations separately.

2. **Pin/test the actual original-function adapter end to end, without models.**
   Verify all six declared scene/seed cells, actual token totals, unchanged
   THINK/ACT prompts, generation budget, extractor mode, feedback text, panel
   epoch, and request hashes using fake backend/scorer objects around the
   original function code. The current test that function code is reused is
   useful but is not alone a behavioral equivalence proof.

3. **Receiving readiness remains a real, concrete integration task.** Obtain
   fresh staged-source/config/mount pins and successful role proofs showing the
   actual GPU2/GPU7 UUIDs, denied other GPUs, inaccessible private panels and
   host process paths, original host/protected handles, lease, and shared claims.
   Preserve any platform denial as terminal. A local unit-command string or
   same-UID permissions are not substitutes for these observations.

4. **Publish full denominators under the new diagnostic epoch.** Report every
   source × seed (3,072 generated tokens each), with all three scene cells,
   stage/ACT counts, unique scored/accepted/new-pixel strings, and unscored or
   incomplete outcomes. Deduplicate `(contest_id, caption_sha256)` within each
   source/seed, not across sources/seeds, and never count old repeated base
   trajectories as independent lineages. The final completion validator should
   join scene IDs to the pinned game manifest, not just accept any three IDs.

## Exact-source follow-up

Final verdict is pending a stable candidate source freeze, final tests, and the
receiving proof if Main obtains it. This reviewer will not stage, dispatch,
publish, signal, call models, alter original bundles, or change the candidate.
All reviewer writes remain in `replication_review/`.

## Update: independently checked at 13:29:04 UTC

The newer candidate repairs issue 1: `TaggedRuntime.Backend` now compares all
eight recorded inference-identity fields before any generation, and completion
validation also compares tokenizer, chat template, decoder, and library versions.
All four independent protocol-drift mutations were rejected.

**48 CPU tests pass** (43 candidate tests plus five independent tests), with
unchanged input pins during the test run. The independent fake-backend run uses
the pinned original `player` function body for all three arms and demonstrates
identical model-facing requests/feedback and seed sequence under the executable
wrapper, with six cells and 6,144 generated fixture tokens per arm. These are
synthetic CPU fixtures, not model outputs, receiving proofs, or scientific results.

One mutation remains accepted: replacing all six cell scene IDs with three
different IDs passes `validate_completion`. The pinned manifest and unchanged
original loop reduce the immediate execution risk, but the completion audit
should join the exact declared scene IDs rather than only count three scenes.

`CPU_REVIEW_RECEIPT.json` records source pins and mutation outcomes;
`CPU_REVIEW_TESTS.log` records the test names. The supplied execution tests create
temporary directories under their module's `HERE`; this reviewer redirected that
test-only variable to `replication_review/`, so no candidate files were written.

Scientific wording caveat: the epoch says “no score-based source selection.” These
are previously selected C2 ages, not a random/unselected developmental sample.
Interpret this only as **no selection using the new diagnostic outcomes**. Keep
the historical checkpoint-selection caveat visible in the result report; do not
claim the new seeds replicate training or eliminate that selection bias.
