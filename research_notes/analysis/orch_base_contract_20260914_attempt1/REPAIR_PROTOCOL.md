# Non-material read-only flag restoration repair

2026-09-14T23:05Z. Initial native attempt preserved,11calls total. All four
processes stopped at the first completed BASE context when installed PEFT's
enable_adapter_layers restored active adapters AND marked adapter parameters
requires_grad=True. Our read-only assertion correctly stopped before any next
generation. No training/optimizer existed, and all generation was inference_mode.
This is a runtime flag restoration defect in our integration, not task failure.

Repair restores requires_grad(False) in finally after the supported PEFT context,
and adds explicit mounted base/adapter hashes while still inside every future
state. CPU fixture reproduces PEFT's exact local API behavior and invariant
parameter bytes. Regression covers normal/exception exits and fixed completed
state import. Original source/archive/raw/FAILED receipts remain untouched.

Recovery imports completed calls byte-exact into a separate recovery1 directory,
skips every already-called task/state, and runs ONLY previously uncalled frozen
slots. No original response is generated again, no new target/prompt/task/seed,
no failed-task correction or extension. Same8denominator, initial solution and
success-only record policy; total ORIGINAL+recovery unique calls<=32. New CPU,
provenance/sourcehash, fresh resource checks and published dated preGPU entry
precede recovery. Guardian honors the ORIGINAL23:30:23UTC deadline, not a new
30minute allocation. No hypothesis, endpoint or scientific threshold amendment.

Crucial evidence limitation: the initial11calls have mounted before hashes and
exact active-condition receipts but lack post-generation mounted hashes because
their processes exited. Disk inventories after plus CPU flag-only reproduction
cannot retroactively restore this missing observation. Report all raw behavioral
counts, mark historical posthash gap, and DO NOT call this a clean paired null
or claim fully verified before/after preservation for those initial11calls.
Recovery states have full before/after hashes. No scale/fit from any outcome;
all original protocol choices/failures and this integration failure are retained.
