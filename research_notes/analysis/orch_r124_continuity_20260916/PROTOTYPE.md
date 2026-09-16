# TRAIN continuity mechanics — CPU prototype, not a live child

## What is implemented

`organism_v6/orch_r124_train_history.py` provides immutable, sourced TRAIN
events with stable IDs; repeated identical delivery is idempotent, conflicting
reuse is rejected. DEV/FINAL/PROBE and readout origins cannot enter history.
System and birth prompts remain pinned. History renders as fully masked
inference input. Explicit child-authored compaction binds a consumed event
frontier, preserves raw events, and labels the summary as a child assertion,
not an established fact. R125's v0 alternative explicitly evicts oldest visible
events while retaining raw evidence and omission receipts.

`organism_v6/orch_r125_continual_stream.py` connects that component to an
injected generation function. Calling `step` again after EOS or a token cap
continues with the same history, without inventing child-authored cue text or
requesting another external user instruction. The caller supplies already
available human/parent events; an empty inbox does not prevent generation.
No parent network call or waiting queue exists in this component.

Generated text and token IDs are saved to the receipt callback before
validation. Only the current child response becomes a target. Prior child
history, parent text, system context, cost notices and observations remain
masked prefix input. Existing EOS token IDs are retained without appending a
second EOS. Cap hits stay explicit rather than being called productive
persistence. Request receipts carry the pending checkpoint: restoring an
unresolved request blocks automatic redispatch.

Cost notices describe prompt/generated tokens, finite context capacity,
generation-context occupancy, total generated tokens, generation duration and
tokens since the last accepted sleep receipt. They are attributed to the
runtime environment, not to the child. Their own next-turn rendering overhead
is included in the next prompt's tokenizer count.

The scheduler exposes new rows and a sleep-due flag. Accepting a complete,
externally verified sleep receipt advances the new-row frontier, binds the
next generation to adapter/optimizer/RNG hashes, and preserves history. It
does **not** perform optimization or certify the supplied checkpoint files.

## Integration contract and unfinished work

- The generation callback must run the actual frozen-base/LoRA model, return
  exact decoded text and token IDs, enforce the supplied deadline during the
  call, and retain decoder/model provenance. CPU tests use synthetic callbacks.
- The tokenizer callback must count the exact chat template used by that
  generator, including generation headers. No word-count approximation is
  acceptable in a live launch; the tests' counter is deliberately synthetic.
- The receipt callback must durably persist node-local records before returning,
  bind restored snapshots to their externally recorded hashes, and reconcile
  pending requests after a crash. It must never restart from a stale snapshot
  while ignoring newer request records. No durable filesystem journal or
  crash-reconciliation launcher is implemented here.
- A live trainer still needs the real masked encoder, new/rehearsal/anchor
  sampler, adapter-only optimizer, RNG restoration and checkpoint verification.
  The scheduler's sleep receipt is not proof of updates or an exposure count.
- The normal driver must repeatedly call `step`, drain its inbox without
  waiting, and choose actual sleep/compaction boundaries. No continuous native
  model process, Rohin console or background service was launched by this work.
- Four-GPU access and child-selected experiments require an enforced sandbox
  and GPU/process admission. No arbitrary shell command execution, resource
  grant or new lease action is enabled here.
- Existing F1/F2/F4 lives and the September 16 06:00 UTC FINAL reservation are
  unchanged. Evaluation must be independently constructed without this history,
  compaction, parent overlay or memory files. No new benchmark/panel is defined.

This is the first tested mechanism layer, **not completion of R125**. It does
not establish better reasoning, retained learning, consciousness or literal
uninterrupted inference. R121 Level-1 paper scope remains; a clean matched
experiment is needed for scientific claims.
