# Non-material documentation of existing strict R166 validators

No validator, child message, object ID, quote, counter, cadence or outcome is
autocorrected. These are private schema/validation notes, not child instructions.

`source_records` is a nonempty list of integer record_index values from the
currently shown child events. It is not a list of ordinal offsets, strings,
commit indexes or invented records. Exact quote/hash fields use the same event.

For `set_aside`, the existing legacy validator requires an explicit English
release phrase matching `set.{0,20}aside`, `leave.{0,20}(here|aside|for now)`,
`move on`, or `different object`. Preserve the child-chosen project: release the
specific unresolved correction, not the project. A short `set aside` phrase can
name that correction. The message must also contain `unresolved`.

The same-project preservation check requires the literal chosen_object.quote
inside the exact private next_task passage, which itself must be present in the
message. The message must include keep, continue, stay with, or within. A
paraphrase of the exact chosen quote in next_task does not satisfy this check.
Without actual rendered Tool receipts, progress_basis is UNVERIFIED_NEXT_STEP,
environment_receipts is [], and the message includes `not yet verified`.

For continue, next_task and continuity remain null. No reason to set aside is
inferred from this documentation; disposition still follows the actual object
ledger and the unchanged three-delivered-turn budget.
