# Opt-in native generation budget compatibility

2026-09-15 02:24 UTC. Implemented and CPU-tested; not GPU-executed or adopted.

## Interface and purpose

`gpu.orch_guided_native_generation.generate(loaded, messages, *,
max_prompt_tokens, max_new_tokens)` consumes an existing `LoadedStage` from
the native seam. Both budgets are required positive integers; neither has a
default. This addresses the legacy Engine's 2,048-token prompt and 768-token
generation limits without changing that Engine or its existing callers.

The helper accepts only collection or sealed-readout stages, in the bound
process and valid context, with an eval-mode model and frozen parameters.
The declared prompt plus generation budgets must fit the loaded model's
`config.max_position_embeddings`. An overlong prompt fails, never truncates.
Greedy generation arguments and returned fields match the legacy call; exact
prefix preservation, generated-tail bounds and EOS/truncation are checked.

Main owns prospective adoption, experimental dose and resource allocation.
Import this helper explicitly at a new caller; it is not monkey-patched into
any Engine. Existing L1 INTENSITY's separate generator is unchanged.
This removes one legacy-cap incompatibility, not the rest of parented replay
design. It does not select training material, change masks, load another child,
make a parent call, or change lineage/visibility requirements.

## Limits and caller responsibilities

- Positional capacity is not GPU-memory or runtime validation. No native
  long-context throughput, memory footprint or learning result is measured.
- The existing `engine.check('generation')` runs before generation. It is not
  a mid-generation timeout; the caller retains external runtime/lease bounds.
- The native loader supplies the actual mounted-state identity. This helper
  does not hash model tensors on every forward; retain the caller's stage
  boundary `verify_unchanged()` checks and receipt bindings.
- The caller records declared budgets in its prospective configuration and
  binds this source along with the native loader and experiment source.
- The helper does not verify message semantics or scrub private content.
  Parent-free readout and child-only training targets remain caller contracts.

## CPU evidence

Command: `python3 -m unittest tests.test_orch_guided_native_generation
tests.test_orch_guided_native -v`.

Observed 2026-09-15 02:23 UTC: **26 tests passed in 0.503 seconds** (8 generation,
18 existing seam). Fake tensors/tokenizer/model only; no torch, transformers,
PEFT, GPU allocation, fit or new native forward used by this validation.
Coverage includes legacy call/result parity, an explicit 8,192 generated-token
budget passed unchanged to a double, invalid budgets, positional/prompt bounds,
process/context/training violations, prefix/tail drift and pre-call deadline.
The fake long-budget test is not evidence of real 8,192-token generation.

Independent focused reviewer Linnaeus found no concrete correctness regression
and independently ran the 8 CPU-fake generation tests successfully. Review
confirms the caller retains mounted-state verification; no native execution,
resource validation or scientific approval is implied.

Source SHA256:
`7c1f1225addc2636cf51191b9aaaba54c845af1aaf253e59f03134458a3f0273`.
Test SHA256:
`1723c0e5e7efd92a7e73afa9dcaab0c19b1b8d2fc51181c6bf4ac93d7de65297`.

No historical experiment or scientific eligibility is changed. The full
research mission remains incomplete; main retains campaign ownership.
