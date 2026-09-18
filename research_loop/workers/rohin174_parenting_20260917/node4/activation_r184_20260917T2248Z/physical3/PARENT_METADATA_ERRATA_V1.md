# Parent-private schema clarification (non-material repair)

This corrects missing descriptions of existing validator requirements. It does
not change child guidance, evidence, masks, cadence, object budget or validation.
Bind this text in the new parent wrapper/prompt before dispatch; log its hash.
Do not modify already-published source bundles in place.

For the private JSON rationale, `object_id` must match
`[a-z0-9][a-z0-9_-]{0,95}`: lowercase ASCII letters/digits/hyphen/underscore
only. Reuse an existing object's exact ID while working on the same mismatch;
never rename an ID to reset the three-delivered-turn counter.

An optional new credit `id` must match `[a-z0-9_-]{1,96}`, must be new in the
existing ledger, and must identify actual child evidence. Do not re-credit the
same step with a new ID merely to pass uniqueness. Omit credit (`null`) when
not supported. `CREDIT:` in the message and a credit ledger entry must agree.

For disposition `continue`, `next_task` MUST be JSON null and `continuity`
MUST be absent or null. A normal child-facing next-action question is still
allowed; the private `next_task` field is reserved for the set-aside transition.

For disposition `set_aside`, supply the existing continuity evidence schema,
leave the specific mismatch explicitly unresolved, and preserve the project.
The nonempty private `next_task` must be an exact passage in the message.

Use exact `record_index` and `record_sha256` pairs from the same shown committed
child event for perception and credit quotes. Quotes must be literal substrings
of that event. Do not substitute `commit_record_sha256` for the response record
hash. These constraints are not instructions to the child and must not appear
as boilerplate in its message.
