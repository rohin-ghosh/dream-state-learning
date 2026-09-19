# C2-only candidate: exact integration point

Candidate only; no deployment, provider call, process signal or live-file edit.

Use `checkpoint_tail_parent_strong.py --manifest ... --manifest-sha256 ...`.
It invokes the original pinned `r202_parent.py --policy-addendum` hook; the
addendum is loaded once at startup. Preserve the existing addendum verbatim and
append the prospective delta. No prompt-function replacement is needed.

The live publisher is PID 325487/start ticks 753205; its restart service is
PID 361010/start ticks 822432 (original exact observation; fresh ps confirms
the same PID/start-time/argv at September 19, 2026, 14:40:24 UTC).
The native binding verifies PID 1139778/start ticks 30025875, LOAD 11505 on
ovx3. The nested publisher CONFIG has no `questions_only_bank_path`; native
binding/PLAN likewise have no bank configuration. GUARD contains filenames for
question-target source pins, not an enabled questions-only parenting mode.

Do not start a competing publisher. The existing `c2_service.py` discovers
only `c2_session*/MANIFEST.json` under its own directory whose referenced output
has STARTED. The narrower supported route is now prepared: install the
prospective `SUPERVISOR_SEED_MANIFEST.json` through `INSTALL_NEXT_SESSION.patch`
only AFTER Main review. It references the REAL unchanged old config/output
and STARTED, explicitly identifies them as OLD policy, and supplies the next
session's addendum. This is not a fake STARTED or retrospective treatment claim.
When Main safely drains only the old CPU publisher, the SAME live supervisor
recomputes max reserved SOURCE, makes a new config/output, and launches the
unchanged strong wrapper in its inherited environment. Keep the CPU service
and its registry untouched. No native handoff, new supervisor, Main-environment
substitution, or credential transfer is needed. Neither process was signalled.

At the inspection cut, session1 reserved through response 560: 109 attempts,
106 published, three historical recorded HTTP failures. Turn 108's publication
`715c030d61014cc2ac05ce4c730b88d9` has since acquired DELIVERED evidence.
Earlier predecessor ledgers also contain publications without local delivery
receipts. Preserve their identities and unknown status; do not republish them,
erase their accounting, or manufacture consumption. Recheck the current
session for a fully settled handoff; any newly in-flight attempt blocks only
the policy handoff, never the child life.

Measurement is Main's
`operations/C2_REFINEMENT_MEASUREMENT_PLAN.md`, SHA256
`2b7e70e1e6cae4e2b642bdc690fa2dd3b3ad66ca3e90a265c18236aa003af9f1`.
Its first-six-committed-ACT window starts after the new policy's first verified
delivery, not process start. The measurement plan is provenance, NOT new
parent-visible feedback.

The new policy is a one-life exploratory intervention, not a controlled
replication or evidence of adapter retention. The main priority remains
persistent parenting; no taper, absence, learning-rate or training-row change.

`README.md` gives the concrete prepared commands and remaining blockers.
The original supervisor's inherited credential has NOT been validated by a
new API call, and no credential equivalence between it, the incumbent publisher,
and Main's environment is claimed. If inheritance fails authentication, preserve
the failed attempt and require scoped secure renewal or a separately reviewed
same-C2 in-memory handoff; never retry401 or reuse the pair environment.
