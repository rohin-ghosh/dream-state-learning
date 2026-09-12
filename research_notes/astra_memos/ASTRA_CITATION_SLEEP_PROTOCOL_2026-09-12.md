# Selected exploratory citation-supervision utility diagnostic

Selected 2026-09-12 15:52 UTC, before any new fit or note-free evaluation.
This is a bounded technical diagnostic, not the matched parenting campaign,
P1, H1/H2, or final paper-grade C11. Formal guard completion stays deferred.

## Question and provenance

Does explicitly supervising one already-observed valid own citation produce
different note-free behavior from supervising syntax alone on the same input?
The sole selected event is post-hoc SEQ091 process t02, episode1851301.
Its exact raw child output SHA256 is
`019bcf5685a46a2f05be4e32ac4e9f138b71da7b1fd72f38078ed65e32d842bf`.
The box citation is true; its preceding source note s02 is false. Selection
does not erase that history or certify a correct parent-to-lesson chain.
Unique source experiences=1, regardless of replay count.

Raw source/capsule hashes and all failed records remain preserved. Official
base origin remains UNRESOLVED_LOCAL_HASHES_ONLY; no clean-lineage claim.

## Treatment and controls

Two fresh-base LoRA fits share initialization, token inputs, partitions,
ordering and 32 optimizer steps. Frozen Qwen2.5-7B-Instruct local base,
rank8/alpha16, dropout0.05, all existing projection targets, AdamW LR1e-4,
bf16, batch1/accum1, optimizer seed1729. No hyperparameter sweep or retry.

- Citation condition supervises the exact raw structural/citation prefix,
  masking the case-ID value.
- Syntax condition also masks group, cell-coordinate and digit values.
- Shared OFF is a no-update reference, not a compute-matched training arm.

Training context is the common task and actual t02 board/case only. The raw
child prefix ends before the comma introducing the lesson key; no repaired
closing brace, generated prose, source note, lesson text, parent example or
parent explanation enters the sleep sequence. Original full outputs and
prompts stay in provenance receipts, not the corpus. End-of-sequence loss
must be disabled so the selected prefix is not taught as a complete reply.
Both arms use identical token inputs; conservatively mask mixed-boundary
tokens. Actual tokenizer checks must establish parity, positive target mass,
zero truncation and correct masks before launch. Supervised-token counts
intentionally differ. Syntax still sees values under teacher forcing; this
isolates citation supervision, not all content exposure.

## Fixed readout, cost and stopping

Evaluate all eight captured transfer boards without source note, parent or
example, with the original strict scorer. OFF and each reloaded ON get eight
deterministic generations capped at128tokens:24calls total. Report t02
separately from the other seven already-exposed development cases. These are
not fresh held-out data. Report schema, factual grounding, invalid citations,
per-case transitions, actual input/output/supervised tokens and measured time.

One optimizer seed and one selected event do not estimate robustness. A
positive contrast is at most scoped utility of citation supervision; equal
active-control gains, regression or no nontraining-case content gain do not
demonstrate utility beyond the control. No tuning or replacement selection
on this panel. No automatic continuation, promotion or claim certificate.

Five fresh workers: OFF, citation fit, syntax fit, citation ON, syntax ON.
Maximum900seconds per stage,2700seconds total plus60seconds cleanup reserve;
one device remains reserved across unloaded intervals. Measured fit latency
and resource usage remain unknown before profiling. Main must verify native
CPU tests, provenance, source/model/token identity, full GPU vacancy and the
supplied lease finish cutoff before any launch. Preserve failed artifacts.
