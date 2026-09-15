# Actual launch failed; four input reservations remain charged

The published CPU-only annotation run launched on September 15, 2026 at
14:16:11 UTC (guard PID 1967297). Its worker PID 1967303 loaded the frozen
Qwen-14B model at 14:16:40 UTC: CPU, 16 threads, zero trainable parameters,
CUDA uninitialized.

It failed at **14:16:41 UTC**, before the first decoding step, at
`left_pad`'s `nonempty_exact_token_inputs` assertion. Four CLAIM files were
already written; no RESULT files exist. The guard preserved a FAILED terminal
receipt. Both guard and worker were verified absent at 14:19 UTC.

The original tokenization call did not explicitly request a flat token-list
return. The non-material repair requests `return_dict=False` and validates
nonempty, flat nonnegative integer IDs before writing a claim. It does not
change task content, truncation, prompts, model, greedy decoding, or the
scientific comparison. Two new regression tests check the explicit tokenizer
argument and rejection of mappings, nested/empty lists, boolean, float, negative
and string IDs without coercion. Main's combined batch/legacy/reducer suite
passes 71 tests. Actual installed-tokenizer and tiny-model smoke verification
are assigned before another real annotation run.

**No retry of these four inputs.** Their claims and partial logs remain on the
node and consume four of the ten published new-input slots. Any successor must
be separately rooted, enumerate both predecessor roots, select only the six
remaining never-attempted inputs, preserve the original **15:10 UTC** deadline,
and publish its exact new source and plan binding before launch. No successor
is claimed by this failure report.

`FAILED_NATIVE_RECEIPT.json` binds actual start/load/terminal bytes and process
absence. Raw logs and requests remain node-local. This failed run supplies no
new semantic annotations or evidence of retained learning.
