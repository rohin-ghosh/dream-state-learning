# F4 context-capacity repair — 2026-09-16 03:34 UTC

Non-material serialization repair; no architecture, visibility, evaluator,
model, adapter, generation budget or learning-policy change. The saved-state
continuation remains governed by the R139 approved intake and requested scope.

The frozen F4 native actor stopped at C112/N04456 before generation because
the prompt used 16,020 tokens plus a 384-token generation allowance against
16,384 context capacity. The JSON user container escaped Unicode in prior
reflection text. Encoding the same decoded JSON values as literal Unicode
reduces this prompt to 8,338 tokens. No content is removed, no cap changes,
and exact original message bytes can be reconstructed and hash-verified.

`gpu/orch_r140_grid_json.py` applies this only on overflow and only to canonical
user JSON containers; system and assistant messages remain untouched. Inputs
already fitting remain byte-identical. Noncanonical/duplicate-key/nonfinite/
surrogate data are not silently rewritten. If it still cannot fit, it fails
without cropping. New call receipts must record the actual normalized messages
and repair metadata, not claim the escaped version was sent to the model.

Source SHA256: `7a9d95d996fc6854b1a8cf19819850fc7d36d836cc857c9bdf3286245bb251e6`.
14 local plus 14 node-staged CPU tests PASS. Actual frozen-tokenizer proof:
`EXACT_FAILED_CALL_PROOF.json`, also on ovx3 under
`/localhome/local-rohing/orch_r140_grid_repair_20260916/`.
The failed call remains unchanged at SHA256
`d4a7f4885084c8ca56d3770a45d0c67d80c8f4a94ad1168260a5ec6e7ade00dd`.
The proof dispatches zero model, environment or parent calls.

This is not yet a native restoration receipt. F4 remains stopped while exact
C112 frontier recovery and FINAL/wall custody over the successor are validated.
The incomplete N04456 reservation stays charged and preserved. Historical
Fable/MISSING slots, including P0323/P0324, are not replayed. Frozen-gen1-LoRA
F4 remains elicitation-only (zero optimizer steps), not a learning lane.
