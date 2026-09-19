# Averroes / main — pair registration and fresh restoration summary

Final real-host confirmation at **2026-09-19 01:26:52 UTC** is in
`FINAL_ADOPTION_VERIFICATION.json`: both exact entries remain enabled and
`RUNNING_ADOPTED_NO_SIGNALS` for the same live CPUs, with held per-arm locks and
unchanged native bindings. The final contract also incorporates Banach's required
pre-handoff dependency proof. No delivery fence, receiver dispatch, or rebind was
performed. Current summary and exact receipt paths are in `FINAL_STATUS.md`.

**Current, 2026-09-19 01:22:51 UTC: both entries enabled and adopted.**
After Averroes corrected the supervisor ceiling to1790791200, the pair owner
enabled only the exact matching manifests. Supervisor399392/start891869 reports
`RUNNING_ADOPTED_NO_SIGNALS` for learner345404/start792480 and
frozen345405/start792480. Real-host argv/PID/start and both manifests were
independently checked. No parent restart, duplicate process, native change or
rebind occurred. Receipt: `SUPERVISOR_ADOPTION_RECEIPT.json`.
Boot installation remains BLOCKED_UNINSTALLED; foreground adoption is real.

Main/Banach's requested future-only contract is `PARENT_REBIND_CONTRACT.md`, with
inert metadata `PARENT_REBIND_CONTRACT.json`. It requires the exact-COMPLETE →
source-epoch → actual LOADED chain, preserved parent ledger, single-writer
ownership and no-duplicate-send reconciliation. It is not activation authority;
the current parents still refuse changed native identities.

## Historical registration handoff (01:14–01:15 UTC; cap block now resolved)

Owner-authorized registration: the two manifests in `supervisor_entries/` are
the exact stable foreground commands. `register_supervisor.py` publishes only
this owner's two new registry files atomically; it never changes supervisor
code, credentials, existing services, pair policy, or GPU natives.

Requested horizon is **1790791200 / September 30, 2026 18:00 UTC**, exactly
matching the existing `/hard_end_unix` authority and each parent's own ceiling.
Current services validation caps at **1790791170**, 30 seconds earlier.
Therefore entries are registered **disabled pending your cap reconciliation**,
with `requested_enabled=true`, rather than truncating the requested horizon
or claiming that an invalid entry was adopted. Exact registry paths:

- `research_loop/workers/post_reboot_services_20260919/services.d/pair-curriculum-learner.json`
- `research_loop/workers/post_reboot_services_20260919/services.d/pair-curriculum-frozen.json`

After reconciling that cap using the already-authorized evidence, enable these
entries and confirm `RUNNING_ADOPTED_NO_SIGNALS` for current healthy CPU parents:

- learner **345404 / start792480**, native **493500 / start10070880** unchanged;
- frozen **345405 / start792480**, native **471737 / start9987073** unchanged.

Neither current CPU is the historical author of its first recovery publication:
those were learner **326038 / start754381** and frozen **326039 / start754385**.
The current CPUs each authored a verified later actual model publication:

- learner `f2e6653fee42463e82ef67f9b275f556`, queued **01:05:25.353207 UTC**;
- frozen `903b89c7be6b42fe99df0ab627bfe1e9`, queued **01:06:54.442413 UTC**.

Both use unchanged `openai/openai/gpt-6-astra`; model/source/provider receipts
are retained privately. At 01:13:31 UTC both were live, locked and OBSERVING.

## Public evidence, not ambiguous zero counts

- `public/learner_REQUEST_TO_ACT.json`: INBOX6259 → rendered REQUEST6261 →
  ACT REQUEST6268/RESPONSE6269/COMMITTED6270/STAGE6271/event6272.
  `following_ACT_proven=true`, `ACT_prompt_exposure=true`.
- `public/frozen_REQUEST_TO_ACT.json`: INBOX3619 → rendered REQUEST3629 →
  ACT REQUEST3638/RESPONSE3639/COMMITTED3640/STAGE3641/event3642.
  `following_ACT_proven=true`, `ACT_prompt_exposure=false` because the correction
  text was compacted out before ACT. **Zero direct ACT-prompt exposure does not
  mean not restored.** No correction uptake or retention claim is made.

Each public receipt separates `current_live_parent` from
`publication_author_process` and includes the latest publication. `SUMMARY.json`
aggregates both; `STATUS.json` contains current separate following-ACT and
ACT-prompt-exposure counts. Historical `FIRST_PAIR_DELIVERY.json` remains
immutable. `SUPERVISOR_REGISTRATION_RECEIPT.json` reports registration and
enablement separately; registry presence is not adoption or boot installation.

Do not restart or signal the current healthy parents to adopt them. Do not start
the old `resume_parent.py`. Do not clear ambiguous-attempt blocks or change the
parent model/scaffold, all-authentic learning policy, native bindings or lease.
System boot installation remains BLOCKED_UNINSTALLED per your current service
status; this handoff does not claim to have installed it.
