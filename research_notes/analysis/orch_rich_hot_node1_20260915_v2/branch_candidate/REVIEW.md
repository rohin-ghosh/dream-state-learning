# Native V2 counterfactual contrast — author-side review

Raw capture: `CALL_00049.json`, SHA256
`95d7d30ec2faab019921b90da8dea791fed0b37aef48b38f7e9f73019e705967`.
Native origin: node1 physical3, `shard3/CALL_00049.json`, LIGHT_BRANCH,
TRAIN task `gsm8k-train-802`. Full raw, prompt, token IDs, timing, numeric
oracle result, source state, task hash and phase version are preserved.

The model computes an explicit counterfactual: without theft, two cups at
fourteen birds per cup would feed 28 birds. It then rules out that outcome
using the stated weekly theft of half a cup, computes 1.5 available cups,
and returns `FINAL: 21`. Both quantities and the rejecting condition are
present in the task; no invented observation or external answer is needed.

This is a consequential, task-supported counterfactual contrast under the
operational alternative/rejection rubric. It is **not** evidence of exploring
independent solution methods, resolving genuine uncertainty, or correcting
a prior answer. Hubble may reasonably use a stricter search-branch rubric;
under that rubric this example remains ordinary applied arithmetic, not a
confirmed search branch. Do not conflate the two definitions.

Selection: illustrative convenience candidate located by text search and
then assessed by reading the entire task and response. Search matches were
not scored or counted as semantic positives. This selected example is
outside the deterministic 12-output sample and cannot estimate a population
branching rate. It is the first such example verified by this worker, not a
claim that it is chronologically first among all native outputs.

No admission is granted. Raw `UNREVIEWED`, `admitted=false` and
`trainingAllowed=false` remain unchanged; Hubble owns publishing/admission.
