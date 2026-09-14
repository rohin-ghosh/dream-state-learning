# Prospective finite repair: strengthen actual-trajectory replay during EVENT write

Declared after terminal253, before successor model use. The253 memory dose
already gives exact4/4 new recall and16/16 actual episode-reader responses;
both parametric and text action score2/4. Fresh-text policy previously scored3/4.
Do not conduct a memory-dose sweep to repair this action-selection failure.

Exactly ONE new fit, from SAME37ec parent, not from253's9d36 descendant.
Same254saved rows, same32fresh EVENT views, same actual source-grounded12
old trajectory targets with parental hints removed. No new teacher, collection,
selection of successful test cases, or fabricated correction commands.

100updates, freshAdamW3e-5, seed0, rank8. Preserve all four original253 batch
indexes; append two actual trajectory indexes at every update:
`memory.training_indexes(update) + (210+(2*offset)%12,210+(2*offset+1)%12)`,
where `offset=update-1`. Batch6;100old+100behavior+200new plus200additional
trajectory presentations,212trajectory presentations total. Standard mean causal
CE; record actual supervised tokens. This is a higher-budget engineering repair,
not equal-token or isolated replay-superiority evidence. No rank/LR/dose sweep.

Reuse COMPLETE253BEFORE through the unchanged native reader/bindings; do not
repeat it. Save the new adapter and fresh-process AFTER uses the exact253
panel: fresh PARAMETRIC/OWN_TEXT/UNAVAILABLE, newW0/W8, old16W0/W8, held16audit,
original-taught OWN_TEXT. <=168nativecalls. Starts from the same37ec, so the
existing253before and250/251 contextual reference remain applicable after exact
source/state/prompt joins. Compare full case counts and first divergent actions,
not only aggregate successes. No evaluator change or dropped failed cases.

Repair target: retain4/4newrecall at both wrappers,16/16oldrecall,16/16audit,
at least3/4original-taught text and at least3/4fresh parametric/text goals, with
unavailable failures reported rather than silently imposed as a training gate.
An unchanged or worse result closes this recipe. A positive result is still one
exposed DEV instance, not reliable general composition or a flywheel claim.
Inspect goal-conditioned paired choices even if aggregate counts improve.

One node2GPU, train<=3660s andAFTER<=3660s including teardown; physical+CVD
admission andsix-hourlease margin. CPU/provenance readiness precede launch;
independent review follows execution and does not gate unrelated work. Schrodinger
owns new replay driver/guard/tests, leaves original driver unchanged. Main owns
native preparation/execution. No refit when only AFTER plumbing fails.
