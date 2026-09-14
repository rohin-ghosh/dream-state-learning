# MATH-RICH terminal checked-answer screen

Terminal comparison: initial rich29/32 versus terse5/32; correction0/3;
19/64 non-terse rows admitted (19/47 outcome-and-token candidates).
Node2 root: `/localhome/local-rohing/orch_math_rich_20260914_attempt1`.
Exact node reduction: `<root>/REDUCTION.json`; repository copy: `REDUCTION.json`
in this report's directory. All4shards COMPLETE;96native calls;0fits/updates.

## Strongest result and limits

Rich prompting yields a large finite DEV answer contrast on matched public
math tasks. This is not merely FINAL-format compliance: posthoc acceptance of
unambiguous bare numeric values raises terse from5/32 to7/32, still versus
rich29/32. That sensitivity analysis changes neither original scores nor
eligibility. No terse response was truncated; terse outputs were1–7tokens.
It does not show internal reasoning faithfulness, equal-compute superiority,
learning, held-family transfer, clean pretraining data, or H1/H2.

The three rejected initial rich answers remain0/3 after oracle rejection
feedback. All three tasks have consequential wording ambiguities: flat versus
hourly sailboat fee, terminal versus time-averaged hiking speed, and six
apples total versus six of each size. Thus0/3 is not clean evidence against
feedback learning. No gold answer/reference solution was provided in feedback.
The child repeated its initial answers; no meaningful corrected lesson is
admitted. The public answer oracle is exact but not infallible semantic truth.

## Fixed denominators and admission

| L1 mining family | Initial rich | Initial terse | Admitted rows | Scale gate |
|---|---:|---:|---:|---|
| percentages |8/8|1/8|6|FAIL|
| work_rates |6/8|1/8|3|FAIL|
| fractional_quantities |8/8|2/8|5|FAIL|
| group_accounting |7/8|1/8|5|FAIL|

Every family passes the declared initial outcome-gap requirement. None reaches
the independently declared scale-readiness floor of8admitted rows across4tasks
per family. Outcome-gap success and scale-readiness failure are distinct.

| Row class | Attempted | Outcome pass |150–400token pass| Semantic P/F/U | Admitted |
|---|---:|---:|---:|---:|---:|
| Initial rich |32|29|22|20/8/4|15|
| Oracle correction |3|0|3|0/3/0|0|
| Own record |29|29|28|4/25/0|4|
| Non-terse total |64|58|53|24/36/4|19|

All64non-terse responses were read against their questions and preceding
context. Explicit decisions, target hashes and supporting spans are in
`SEMANTIC_REVIEW.json`; the authored reading table is
`../orch_math_rich_20260914_review.py`. These are author judgments, not
independent verification. No heading or keyword classifier supplies labels.
First-person plural accounts are accepted, so this is not a literal-I gate.

**Important exclusion distinction:** many impersonal recipe-style records
contain correct reusable operations but do not satisfy the declared
first-person account contract. Of64responses,55have grounded operations,
7remain unresolved and2contain a material false premise/check. Do not
misdescribe all36overall rubric failures as wrong mathematical operations.
Five semantic-PASS traces fail the150-token floor; none is padded or rewritten.

The two material content failures despite correct final answers are:
- `gsm8k-train-7054:record`: adds successive inventory states11+7+6=24,
  then invents18sold to claim6remaining. The correct sold total is138;
  sequential inventory states must not be added. Correct FINAL6 is insufficient.
- `gsm8k-train-4062:record`: promotes the prior explicitly assumed four-week
  month into a given quantity. The original question does not specify that
  payroll/calendar convention; its initial rich response remains UNRESOLVED.

The admitted corpus has19unique target hashes across16distinct tasks,
15initial traces and4records, no correction rows. Total target tokens4228;
mean222.5263, min153, median214, max348. Exact sorted token distributions,
class-level totals and rubric axes are in `DISTRIBUTION.json`/`REDUCTION.json`.
Maximum actual inference context541tokens; maximum generated457;0truncations;
maximum3calls/task, within the declared6-turn/512-generation/2048-context caps.
These target-token counts exclude terminal EOS; the native generation ceiling
includes EOS. The historical `unreviewed_candidates` field denotes the47
pre-review candidates, not remaining unreviewed rows: all64non-terse rows
have explicit final judgments in this packet.

`ADMITTED_ROWS.json` contains only actual child targets and the neutral
student prefixes, with no oracle/guidance messages or reference-solution
targets. Prior child responses in record prefixes would be entirely loss-masked
in any later fit. There is no training launch or implicit permission to fit
this19-row corpus; the1000-row requirement was not reached.

## Assumptions and falsification

One fixed portable37ec checkpoint, deterministic generation,32prospectively
selected unique GSM8K train questions and matched rich/terse tasks. Prompt
instruction placement and inference spend differ between treatments; no
equal-token control or multi-seed replication was run. Public benchmark
memorization/contamination remains unknown. Strong per-question mathematical
derivations, rather than verbose correctness alone, support the narrow reading.

Family routing was frozen before sampling, but is coarse: ordinal-day/batch
words routed two non-fraction tasks into fractional_quantities. No family
roster was repaired after viewing outcomes. This prevents treating the label
as a clean conceptual-generalization proof. Held L1 geometry/measurement and
age/time families were declared but not generated/evaluated. New L2/L3 contents
were untouched. Old W0/W8/audit and held uncoached readouts were not run:
those conditional fit gates did not become active.

Attempted falsifications: matched direct-answer control; format-neutral
sensitivity; full-text rejection of invented checks despite correct outcomes;
separate correction outcomes; explicit ambiguity review rather than coerced
agreement with reference gold; readonly base/adapter state checks before/after.
The sailboat ambiguity also received an independent bounded wording check
from the old builder in the notebook; that is not independent certification
of this whole corpus or rubric.

## Preservation, compute and recommendation

Native source620c03d830b9ab31013fd193dfaf5a435f36530b; archive
`0da2fdb970001cc413b3b6d83e19466b6c4f66e767c4d0edfedbc0024716d9c3`.
PreGPUpublication77e8352e preceded actual final-batch launch22:08:52UTC.
Mounted37ec and local base/tokenizer pins pass unchanged before/after.
Two preceding engineering aborts—archive UID comparison and adapter hash-key
namespace—made zero generation calls; both are preserved, not science nulls.
The latter consumed162.1122summed native-process seconds separately from
the final screen's0.2450055assignedGPUhours. No unknown process was killed.

Run archive on local/data:
`gpu_artifacts_local/orch_math_rich_20260914_attempt1/preserved_run.tar.gz`,
SHA256`558ec9728f3f0e4f5de8b619cb794ac1a7694936a1bb60ef3593c5b645c28d1f`,
236entries including all96calls, failures, native receipts and release scans.
Source archives are separately retained; no original evidence was deleted.
`TASKS_VIEW.json` is the repository's newline-normalized view; exact original
TASKS bytes/SHAaeddc122 are in the node root and preserved archive.
All four owned PIDs absent; detached physical+/proc CVD release passes for
GPUs4–7 at22:18:36–37UTC. Current CPU10/10pass; native actor used9/9prelaunch.

**Compute recommendation:** deallocate this bounded scale recipe. The outcome
gap is positive, but the prospective corpus-yield gate fails0/4families and
no corrected-example class is available. No1000-row scaling or matched fit.
This does not disprove rich operations or feedback learning. The cheapest
next prospective test should preserve first-person grounded records without
padding, and select unambiguous mistakes for specific quantity-level oracle
feedback versus a matched extra-call retry. It must not change this screen's
denominator, thresholds, target bytes or failed outcomes.

**Message for peers:** exact final answers do not certify reusable records.
Audit intermediate conservation checks and the oracle's wording assumptions;
separate genuine mathematical content from voice/token contract compliance.
The portable actor hash uses mounted `.lora_A.default`/`.lora_B.default`
parameter names exactly as V3, not PEFT export keys. Both earlier engineering
failures were repaired without relaxing pins.
