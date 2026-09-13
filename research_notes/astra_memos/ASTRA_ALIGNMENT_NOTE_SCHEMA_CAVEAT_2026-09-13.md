# Alignment NOTE schema caveat — before Main outcome inspection

September 13, 2026. The native assay is already running; two seeds have completed
their controllers and automatic collection, and seed 1 is finishing. Main has
not read any assay correctness results or raw child generations; the independent
reducer has not received the evidence mirror. This is a code-inspection warning,
not a prospective change to the running experiment or a claim about its results.

The frozen core `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010`
uses `normalize_note` and `score_note`. Unknown extra fields fail normalization.
P accepts predicted/observed/relation and an optional matching receipt ID; C
accepts receipt ID/action/outcome, using the declared aliases. The ordinary
instruction requests a relevant-state NOTE object but does not forbid every
other potentially useful piece of public metadata. Thus a schema failure may
coexist with useful public-source processing; it cannot by itself prove that
the model failed to perform the process operation.

Do not change the frozen prompts, parser, native scoring, core hash, thresholds,
or pre-outcome reducer. Keep the original feasibility result. At reduction,
separate closed-schema errors from wrong required bindings and inspect raw
examples as diagnostic evidence, not as hidden replacements for failed cells.
The declared finite-interface result remains reportable, but a semantic claim
about absent reasoning or parenting receptivity requires this limitation.

If raw outputs motivate broader content extraction, specify a separate
exploratory re-score, preserve original scores, apply it symmetrically to all
arms/seeds, and do not use it to rescue the frozen gate. No such alternative
scorer is implemented or authorized for promotion by this note. The next
matched additive writer design is unchanged and does not depend on these
alignment outcomes.
