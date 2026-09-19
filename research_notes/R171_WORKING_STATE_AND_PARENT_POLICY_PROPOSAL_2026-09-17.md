# R171: preserve a decision, then test whether it governs the next action

September 17, 2026, 12:59 PDT. **Proposal for Rohin's ruling, not an activated
fleet policy.** No live R179/R166 source, sleep recipe, control, adapter, or
context is changed by this document.

## Directive and scope

I read message171 in full, including the eight-part design-agent chain. The
source is `research_notes/THESIS_RAW_ROHIN_2026-09-11.md` at fetched commit
`c651533120212d007698721b61289b3d4430ff13`, Git blob
`e32aa032dab71fee3562414f9fcf4b9124c70529`, file SHA-256
`5b9c32fea690a8d6c2a001b1575c843fb4726e351f7d6cc53ff6ee85f46238bf`.
`git pull --ff-only` fetched that commit but refused to merge over current
COORDINATION edits and existing untracked design files. I used `git show` to
read the fetched source; nothing was stashed, reset, deleted, or overwritten.
The source labels171 approximately12:55 PDT; its commit is timestamped12:49:54
PDT. These are source timestamps, not proof of the time of the conversation.

Immediate decisions are separate from proposals: text pairwise-judge work and
throughput profiling proceed under170/171; **image-judge training is on hold
until the text judge works**. Rich image descriptions can come from prompting
the existing local Qwen-VL, without fine-tuning another model. R171 says formal
actions on consolidation will follow. Its design-agent chain is input to this
proposal, not ratification of unannounced code or experimental changes.

My view: this is the right failure to isolate. A reflection is useful only if
it changes a later choice. But we have not established that LoRA is universally
working correctly or that every failure occurs before training. Locate the
first break instead of assuming either conclusion.

## What the current code does

- R179 retains the visible history at a pre-sleep boundary below
  `min(3/4 * context_limit, context_limit - segment_tokens)`: normally12,288
  tokens for a16,384-token context. Its preservation changes the context view,
  not targets or optimizer updates. At the threshold it still replaces the
  old visible prefix with the child's pre-sleep summary. It checks source
  identity/nonempty text, not whether a decision or corrected belief survived.
- The threshold check runs at pre-sleep generation, not every wake step. The
  general `ContinualStream.render` overflow path can still evict old context;
  immediately after compaction it can drop the active summary itself. Merely
  changing the retelling prompt would not protect working state from that path.
- R166 currently asks for rich re-perception, a justified correction and a next
  step. It does not require evidence that the next action enacted that decision.
  Asking the child to describe real feedback is not the same as preserving the
  actual feedback. The plain presenter can also omit scaffold-containing text;
  evidence visibility must be checked at the rendered request, not assumed from
  a journal entry or an inbox publication.
- These are source-level findings. A node3 cycle40 receipt at
  `research_loop/workers/r179_context_survival_20260917/node3/CONTEXT_RETAINED_3_40.json`
  shows an unchanged history hash at3,544 visible tokens. That event alone is
  not proof of the following wake, fleet-wide deployment, or weight retention.

Relevant source: `gpu/orch_r179_context_survival.py:26`,
`gpu/orch_r166_corrected_retelling.py:15`, `gpu/orch_r166_parent_policy.py:28`,
`organism_v6/orch_r125_continual_stream.py:115`,
`organism_v6/orch_r124_train_history.py:199`, and
`organism_v6/orch_r125_plain_context.py:24`.

## Proposed R179 change: working state, not a rewritten history

Keep history across sleep and keep the existing pressure threshold. At actual
compaction, carry a small, revisable piece of working state: the investigation,
current belief and uncertainty, what the latest observation changed, the next
concrete move, and unfinished questions. These are semantic requirements for
our audit, **not five compulsory headings or a ritual the child must repeat**.
“No result obtained” and “I do not yet know what to try” are valid states.

The smallest robust implementation has two parts, not just a new invitation:

1. Elicit an actual child-authored update, preserving an existing useful
   decision verbatim when it has not changed rather than repeatedly paraphrasing
   it. Prefer a short update to the current investigation over a chronological
   account. Do not generate the child's decision on its behalf.
2. Protect that bounded carry and the relevant real evidence when rendering
   after either threshold compaction or emergency overflow. Keep recent action
   context where needed to make the pending decision intelligible. Budget and
   journal every eviction; archive the complete original history as now. The
   carry must not be the first item dropped by the generic overflow path.

Return actual tool stdout/errors or judge values as attributed environment
content, copied from the verified result rather than reconstructed by the
child. Keep hashes, event IDs and wrapper metadata in machine logs, not in the
child's prose. Missing or failed execution remains explicitly missing/failed.
Pin the exact visible evidence and its provenance; never silently transform an
attempt into a successful result. Evidence is not automatically truth: a
provisional judge score remains a provisional judge score.

All parent, console, tool and copied evidence content remains masked from
training. Re-presenting a carry must not automatically create a new trainable
row or multiply its training dose. Preserve original row identities and
eligibility/exclusion records; any changed target selection or replay dose is
a separately declared recipe change. Do not silently give no-distillation or
frozen controls an extra generated sleep segment.

If a summary drops the useful decision, record the failure and retain the
previous child-authored state plus the real evidence within the explicit
budget, rather than inventing a repaired child target. If even that cannot
fit, preserve a checkpoint and report the capacity failure; do not claim
successful state preservation. This recovery behavior and the carry token
budget must be fixed before the diagnostic, not tuned after seeing success.

## Proposed R166 change: three timely questions, then no reminder

Use the three questions at the relevant moments, not together on every turn:

- After a reflection: **“What, specifically, will you do differently on your
  next attempt?”** Invite the child to choose a concrete, revisable practice.
- After a real attempt: **“Did you do it? What happened?”** Ground discussion in
  the actual attempt/result; a promise to test is not execution.
- At compaction: **“What decision and unfinished work must survive for you to
  continue?”** Preserve the pending investigation, not a generic lesson list.

On the first wake after the measured boundary, let the child act without a new
parent hint. A bounded no-reminder window must be explicit in the diagnostic
cadence, with queued parent/console arrivals logged; an intervening reminder
invalidates an autonomous-enactment claim. Do not silently violate or relabel
the existing parent-turn floor. Keep English, attribution, the current90-word
cap, the mismatch budget, credit for real progress, and the same live object.
Neither a fixed introspective opening nor repeated scaffolding is the goal.
Unparented lives remain unparented.

## One diagnostic before a curriculum or fleet-wide change

Use C2 and one failing comparison life; the R127 pilot is a candidate, subject
to confirming a repeatable failure in its open TRAIN trace. Do not select a
case from sealed extraction results. Freeze one useful lesson and its action
criterion before testing it. Trace:

`attempt -> actual evidence -> corrected response/decision -> carry -> exact
eligible rows -> sleep update -> rendered next-wake prompt -> autonomous action`.

At every arrow record what was actually present, masked, excluded or lost.
This distinguishes a tool-delivery failure, a retelling regression, a row
filtering failure, an optimizer problem, and failure to apply a retained rule.
The immediate success criterion is a useful decision that survives actual
compaction and is enacted without reminder, not phrase overlap or low loss.

Proposed small fork: preserve the live parent's checkpoint and take two copies
with identical adapter/optimizer/history and generation RNG, the same completed
carry and eligible rows, just before a sleep update. One performs the registered
updates; one skips updates. Keep decoding, token/tool budgets and wake schedule
matched; isolate training RNG consumption so the first generation RNG is
matched. Preserve the source lives. Neither branch receives a next-wake hint.
Test a pressure-compaction boundary as well as an ordinary retained-history
sleep; a no-pressure sleep does not establish compaction survival.

Use one immediate continuation and one new situation where the practice would
help, scoring the actual action and observed outcome. Include occasions where
continuing directly or leaving a question unresolved is appropriate. A visible
working-state decision supports a context-carry claim, not a weights-only
claim. The updates-ON/OFF fork is also distinct from adapter-ON/OFF extraction.
Keep both existing R164 channels: living-context observations and independent
fresh-process empty-history extraction with the adapter on/off. For the new
update's effect, also compare post-update versus pre-update adapter copies.

Outcome-selected `situation without intervention -> enacted better practice`
examples are a subsequent, explicitly derived training dataset, not silently
rewritten original trajectories. Retain provenance that the practice was first
elicited with help; validate it against real outcomes, mask external content,
and test transfer without the intervention before expanding to a curriculum.
No such derived rows or forks are created by this proposal.

## Acceptance tests and requested ruling

Before any saved-boundary rollout, test: exact low-pressure history retention;
working-state/evidence survival at both pressure and emergency overflow;
unchanged adapter/optimizer/RNG custody on handoff; external-token masking;
no duplicate carry targets; real receipt projection and missing-result handling;
no fabricated fallback thoughts; exact training-row/exclusion linkage; and
no-reminder cadence accounting. Claim semantic/action success only from the
diagnostic, not those software tests.

**Requested ruling:** approve the working-state carry plus the three-question
parenting successor for this bounded two-life diagnostic first, with the live
lineages and controls preserved; review the first broken link and transfer
result before expanding. Existing R179 context-preservation work continues
unchanged meanwhile. The causal claim, target recipe, benchmark controls, and
future rollout scope are not expanded by consensus or by this proposal alone.

Source hashes at12:57 PDT: R179 `b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b`;
R166 parent `2874e7eb436459c207f48c218a267e86e3877d270aba830e3e465c1db382deee`;
R166 invitation `9277b09ca3f312bd7afa8bbcfc94f883940652c4199fe686c2ed47d73a992bcc`.
