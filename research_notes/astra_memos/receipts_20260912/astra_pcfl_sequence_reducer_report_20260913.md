# Frozen paired reduction / EDITSTOP

The unchanged reducer ran on the bound completed local NO_WRITE and S_A
archives. Both states score 0/4 at each A/B W0/W8 panel. S_A's fit receipt
records 40 updates. Pre-correct S_A A is zero at both wrappers; retention
is undefined/null, not zero retention.

`result/analysis.json` field `missing_states` lists FOUR missing READOUT
endpoints: SEQ_REPLAY, SEQ_NEW_ONLY, FRESH_MIX, ALL_AVAILABLE.
This is not a count of unrun fits. Main reports FIVE withheld FIT phases:
SEQ_REPLAY, SEQ_NEW_ONLY, FRESH_MIX, ALL_AVAILABLE_1, ALL_AVAILABLE_2.
ALL_AVAILABLE_1 and ALL_AVAILABLE_2 lead to one ALL_AVAILABLE readout
endpoint. Missing readout evidence alone does not establish fit execution
status; the withheld-fit statement is Main's operational report.

`request.json` contains the exact material and collection FILE pins, local
outer directories, and original-path-to-local-file remap. `fit_completed.json`
is a byte-identical copy of the pinned completion receipt from the nested
archived fit tar. Original archive files were not changed. The reducer itself
remains unchanged; this note clarifies units without altering its sealed output.

Final synthetic suite: 8/8 PASS, 33.849s, no skips. Actual paired CLI reduction
also completed. No GPU/model/network actions, source edits after freeze, or
commits. Descriptive only; no threshold pass, retention success, dose rescue,
parenting, generalization, or compute-matched NO_WRITE claim.
