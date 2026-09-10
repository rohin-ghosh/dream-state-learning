# Fresh recurrent artifact-integrity re-audit

Review only the exact files and lock supplied with this request. Independently
verify every SHA-256 in the lock before reading the implementation as evidence.
Any mismatch requires `escalate`.

The previous independent review found three blockers. Attempt to reproduce
each attack against the repaired snapshot:

1. A recorded proposal or self-check output could disagree with its structured
   operation, event, verdict, status, reason, or citations, and an invalid
   condition/reactivation schedule could still pass.
2. Backend invocations, top-level `trace.model_calls`, cycle/nested call IDs,
   and serialized generations were not bijective; missing, duplicate,
   reordered, rewritten, or leftover calls could pass publication.
3. The returned corpus could differ from the audited trace corpus, and corpus
   text/provenance could be unrelated to the canonical one-edge memory event.

Inspect the implementation and adversarial regression tests, then run the
focused CPU suites. Approve only if all three classes now fail closed and no
materially equivalent bypass remains.

This is an artifact-integrity decision only. The supplied plans deliberately
block GPU execution because Semantic World v0.2 has a target-signature shortcut
and the first scheduler under-allocates WAKE/reactivation opportunities. Do not
treat an integrity approval as approval of the game, scheduler, GPU run, or
scientific claim.
