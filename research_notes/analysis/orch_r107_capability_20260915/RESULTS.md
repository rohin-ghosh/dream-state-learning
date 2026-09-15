# First R107 paired capability result

September 15, 2026, native completion07:37:32 UTC. MATH764 FULL checkpoint,
actual adapter ON versus adapter disabled OFF; pure no-adapter BASE measurement
is separately pending. Do not relabel the trained new-labels-masked arm as OFF
in this table: these are two activation states of the same FULL checkpoint.

## Output and completion first

All32 responses per condition completed, zero truncations/missing cells.
ON emitted351 tokens total (10.96875/task), OFF381 (11.90625/task), including
one terminal EOS per response. Prompts request compact task-appropriate output;
this is a capability-preservation diagnostic, not a persistence/rumination test.
No semantic thinking or novel-thought advantage is inferred from these lengths.

| Fixed synthetic family | ON passed | OFF passed | ON minus OFF |
|---|---:|---:|---:|
| Strict JSON + bounded code expression | 0/8 | 2/8 | -2 |
| Math | 7/8 | 7/8 | 0 |
| Simulated tool-call schema/selection | 8/8 | 8/8 | 0 |
| Concise instruction following | 7/8 | 7/8 | 0 |
| Total | 22/32 | 24/32 | -2 |

Matched cells:22 both pass,8 both fail,2 OFF-only passes,0 ON-only passes.
This small synthetic panel is not a broad code/tool benchmark. No arbitrary
generated code or external tool call was executed.

## What the two lost passes mean

Author inspected all16 code responses. The two OFF-only passes (CODE02 even
sum, CODE05 reversal) become bare expressions or a non-JSON `expression:` line
with ON. Both ON expressions pass all four existing bounded-interpreter cases
when wrapped in the requested JSON object in an **offline, post-hoc diagnostic**.
Primary strict scores remain unchanged. Evidence therefore points to schema/
instruction-following suppression in these two cases, not loss of the underlying
formulas. Other code failures include interpreter limitations: both conditions
produce valid Python exponentiation on CODE00, but the deliberately restricted
interpreter rejects it. Do not label that as failed Python arithmetic competence.

Base and adapter hashes are verified unchanged at final readout. Disabling the
adapter recovering these two strict passes supports conditional behavioral
suppression on this panel; it is not proof that all fine-tuning harm is harmless,
nor that broad capabilities are preserved. The independently loaded BASE probe
and the continual child's same-suite diagnostic remain required follow-ups.

## Provenance and repairs

`PAIRED_REDUCTION.json` contains64 source paths/hashes, suite/checkpoint bindings,
family counts, task-pair results and native COMPLETE/LOADED/AFTER hashes. Raw
responses remain on node3 at
`/localhome/local-rohing/orch_r107_capability_math764_full_20260915`.
Suite SHA256 `32a1d71ff23e168f42366ec4c96777aceb59247020e7a3ae98b6f64b4b9b602c`.
Checkpoint SHA256 `a970d311de6a3a77881f95fa1b042069d708c6bf814306980f8fe36467c8e792`.

Two pre-inference assertion failures were preserved and repaired; three
already-generated cells were retained, not resampled. V3 generated only61 missing
cells. Total64 generations/66 reservations, original deadlines unchanged.
CODE01's pair crosses two fresh processes; neither condition passes that case.
No optimizer, parent input, training updates or held-output ingestion occurred.
124 suite/runner CPU tests and native PEFT activation/read-only smoke tests pass.
