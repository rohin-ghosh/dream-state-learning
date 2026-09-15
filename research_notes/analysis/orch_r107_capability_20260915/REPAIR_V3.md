# Read-only adapter-context restoration repair

September 15, 2026. V2 produced three valid responses, then stopped before
the fourth inference: leaving PEFT's adapter-disabled context can restore
trainable flags on adapter parameters. The next read-only assertion correctly
detected this. All generation used inference mode; there was no optimizer or
weight update. Preserve both prior failures and all three responses.

Non-material repair: always restore `requires_grad_(False)` on context exit,
including exceptions, while still checking actual LoRA-layer activation state.
This matches the existing project's read-only condition pattern. The regression
now simulates PEFT re-enabling trainability on context exit. No prompt, task,
score, cap, model or deadline changes. 124 suite/runner tests pass.

V3 must reuse the three hash-bound completed cells rather than regenerate them.
It therefore allows61 new calls, yielding64 total generated cells. Prior
reservations1+4 remain charged; the aggregate reservation ceiling is66, including
two pre-inference failures. Original native/hard deadlines remain unchanged.
The retained cells and subsequent cells span fresh processes; CODE01's pair
crosses the process boundary, which must remain disclosed. All cells use the
same immutable checkpoint, exact prompts and greedy configuration. No best-of
selection, replacement of a generated response or silent retry is permitted.

New source/provenance, native PEFT read-only restoration smoke test, READY,
publication and fresh physical admission precede launch of `/repair_v3`.
