# R125 plain-context repair — design before live changes

2026-09-16, Builder. Implements the 06:40Z audit within the existing frozen-base,
LoRA-only, TRAIN-provenance and parent-free readout contracts. No running lane
has been changed by this design entry.

- Keep immutable events, source hashes, targets, checkpoint lineage and journal
  receipts. Render a versioned plain view: role-separated text, no provenance
  wrappers, short cost sentence and a plain oldest-history omission notice.
- Use Rohin's purpose framing and a factual adapter description. Do not copy the
  draft's unestablished universal learning rates or promise unavailable tools.
- Increase the native context limit to 16,384, subject to the local model config
  and available memory. Keep segments, decoder, anchors and readouts unchanged.
- Do not silently rewrite already generated scaffolding. Exclude whole passages
  containing known journal-format markers from the visible view and future
  target presentations, with source-bound exclusion receipts. Retain ordinary
  prose and ordinary JSON. Re-render legacy replay prefixes without their known
  outer wrappers; never synthesize replacement child targets. This is a narrow
  contamination filter, not a behaviour/outcome acceptance criterion.
- If a sleep has no eligible presentations, record zero updates explicitly;
  do not pretend that a changed adapter or learning occurred. Otherwise retain
  sixteen presentations for eligible new rows, one for eligible rehearsal rows,
  and anchor objective weight 0.25 (not token fraction).
- Apply presentation/budget changes only at a complete saved sleep boundary,
  through a journal-validated transition that cannot change history, rows,
  optimizer, RNG, model hash or frontiers. Use a new immutable source deployment.
- Test raw preservation, no headers in visible inputs/eligible targets, masking,
  ordinary JSON preservation, transition rejection during pending work, exact
  legacy restore, 16k validation, and unchanged fresh-process readout code.

Limitations: this does not unlearn the already fitted scaffolding, recover evicted
context, or establish improved cognition. The filter is intentionally narrow;
natural-language imitation of cost notices is not automatically labelled as
machine metadata. Report the continuation as a new presentation-policy segment,
not a clean from-birth comparison. Experiment shell remains disabled.
