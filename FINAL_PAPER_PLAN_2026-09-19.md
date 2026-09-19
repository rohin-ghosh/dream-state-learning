# Final-paper preparation — September 19, 2026

**Start here for the submission plan.** This is an evidence inventory and a
proposed next-experiment order, not a claim that the proposed experiments ran.
It preserves Rohin's submitted abstract, the H1/H2 thesis, the frozen base,
private-adapter learning, controls, sealed-evaluation blindness, and the current
no-row-exclusion policy. It does not edit the manuscript or submitted abstract.

The submitted title is **Animating Intelligence: Language-Guided Development of
Continually Learning Agents**. The version of
`ABSTRACT_SCOPE_AND_RESEARCH_UPDATE_2026-09-19.md` on remote main at
`181b58d445fc5b6ebaf425e4f5782c88ed597d19` contains the submitted abstract;
the older local copy is not authoritative. Do not overwrite it during publication.

## 1. The short answer

- There is a useful preliminary result: a selected earlier C2 checkpoint yields
  more judge-defined novel accepted ideas than base in both new sampling seeds;
  the selected later checkpoint yields fewer. This is not monotonically improving
  development, and the earlier checkpoint does not win every metric.
- We have examples of coached checking and actual subject switches. We do not
  yet have a reliable correction-to-action-to-unreminded-transfer chain showing
  that LoRA caused the retained habit.
- We have parent-free checkpoint evaluations and one short intentional
  parent-absent cycle. We have not completed a controlled gradual-taper study.
- The final experimental priority is a matched causal comparison, not more
  uncontrolled hours or more examples of the model saying it will reflect.
- Operational failures are not scientific negative results. Conversely, a
  running process is not evidence that teaching, scoring or learning is working.

## 2. Which agent is which?

| Label | Role in this project |
| --- | --- |
| C0 | The math-first developmental life; reading, writing, recall and probing were added later. It is not the main continuous caption player. Its preserved checkpoints can be evaluated on the game. |
| C2 | The long-running developmental lineage used for conversation, reasoning and writing; saved checkpoints such as sleep51 and sleep117 are evaluated separately. Sleep117 is a historical checkpoint, not a synonym for current C2. |
| P3 | The main strongly parented continuous caption-game life. Live activity does not by itself establish current scoring or effective guidance. |
| Frozen base | The no-update caption reference and a source for matched evaluation comparisons. |
| Curriculum learner / frozen sibling | A pair started for curriculum-from-birth comparison, differing in whether sleep updates occur. Provider interruptions compromise their treatment exposure; do not call those interruptions planned tapering. |
| P7 / Astra7 | The reading/parenting-development thread; not a primary causal result for the paper at present. |

## 3. What has actually run recently?

At **20:43 UTC / 13:43 PDT on September 19**, a read-only check verified original
PID/start identities and recent record-file activity for:

| Life | Most recent observed record/file modification, UTC |
| --- | --- |
| C2 | 20:43:04, record16795 |
| P3 | 20:43:00, record13210 |
| P7 | 20:42:21, record17770 |
| Curriculum learner | 20:41:32, record14239 |
| Frozen sibling | 20:42:27, record6333 |
| Frozen-base player | 20:38:32, opportunity286 / attempt1 pointer |

This establishes activity, not substantive success, parent delivery, current
judge scores, or a completed current-hour comparison. No live content was graded
by this metadata check. C0 was not restored by this check. Receipt:
`research_loop/workers/replication_sprint_20260919/operations/PAPER_PREP_ACTIVITY_20260919T2043Z.json`.

The new fixed-budget sampling block completed at **14:24:35 UTC / 07:24:35 PDT**.
All18 cells finished; independent recount agrees on240 metric comparisons and
excludes99 replayed returns from new-discovery counts. C2's revised parenting was
delivered at15:33 UTC. Its first assessed action saw the instruction but did not
produce the requested artifact. A separate observer collected four of six planned
ACTs before its byte limit; collection is not grading, and stopping that observer
did not stop C2.

## 4. The defensible game result

Same three development scenes, same adopted judge, same extraction and novelty
rules, **3,072 generated tokens per source per seed**, no parent or updates in
the evaluation copies. These are new decoding seeds, not new training lineages.

| Source | New pixels, seed23301 | New pixels, seed23302 | Sum of seed-local accepted counts | Sum of seed-local pixel counts |
| --- | ---: | ---: | ---: | ---: |
| Frozen base | 23 | 25 | 81 | 48 |
| C2 sleep51 | 28 | 29 | 79 | 57 |
| C2 sleep117 | 15 | 23 | 81 | 38 |

"New pixels" means the game's operational novelty measure among accepted
captions. It is not a count of human-certified funny jokes. Novelty resets
between seeds; the sum is not a globally deduplicated count across seeds.
Acceptance and novelty are different endpoints: sleep51 has more pixels but
fewer accepted strings than base across these two seeds.

**Supported interpretation:** selected-checkpoint exploration is different and
non-monotonic; the earlier checkpoint's directional novelty advantage recurs on
two new generation seeds. **Not established:** the advantage is caused by
parenting, caused by reflection, transfers to unseen scenes/tasks, results from
tapering, or replicates across independently trained agents.

Primary receipt:
`research_loop/workers/replication_sprint_20260919/replication/RESULTS.md`.
Accounting: `research_loop/workers/replication_sprint_20260919/replication_accounting/README.md`.
Do not use replay-inclusive historical totals or mix judge epochs. The submitted
abstract's cautious description of early gains diminishing later fits these
observations; stronger causal wording does not yet have the needed evidence.

## 5. Reflection, diversity, and independence: what is supported?

| Question | Evidence | Missing evidence |
| --- | --- | --- |
| Was the curriculum diverse? | C0 received math, reading, writing, recall, model-science and research questions; some actual retelling/writing occurred. | Reliable learning or transfer from diversity, not merely delivery. |
| Can feedback change an action? | Two narrow coached subtask successes in an older selected21-trace audit, one in a frozen control. C0 also switched from off-task math to an actual paragraph after guidance. | Reliable complete-task success and an adapter-specific causal effect. These samples are not a population success rate. |
| Does self-reflection reliably carry into ACT? | Both lost-correction cases and visible-correction/non-uptake cases exist. A later bounded window found0/3 correct requested artifacts for C2 and0/3 for P3. | Full recognize-correct-reuse chains, with measured visibility and independent task checks. |
| Has independence been tested? | Parent-free frozen-checkpoint game probes; one completed deliberate parent-absent caption cycle on September18. | Clean-context retained checking, held-out transfer, and a controlled taper schedule. |
| Did the deliberate absence succeed? | Three related caption variants, but no verified correction; earlier teaching stayed in context. | It is not evidence of clean independence or of tapering's benefit. |

Source-bound audit:
`research_loop/workers/replication_sprint_20260919/evidence/EVIDENCE.md`.
Absence receipt:
`research_loop/workers/rohin205_node3_20260918/R232_OBSERVATION_COMPLETED_TRACE.json`.

Do not explain sleep51 using later events. Its weights were saved at
September18 01:36:13 UTC, before the direct-console V=3 derivation at01:58:23
and the later Byte teaching. Those later experiences cannot have trained that
already-saved adapter. Preserve positives without retrofitting the chronology.

## 6. Proposed final experimental order

These are implementation priorities, not new completed experiments. Before
launch, bind the exact task/seed/budget/metric/source manifest and log the
builder's CPU/provenance checks. Keep ongoing lives and failed evidence intact.
Do not spend the remaining window waiting for a general-purpose daemon if an
already-validated, fixed-budget evaluation path can answer a bounded question.

### A. Primary: does guided behavior survive outside the interaction? (H1)

Use a parented/unparented by LoRA-updating/frozen factorial, preserving matched
starting sources and ordinary environmental feedback. Frozen arms get no weight
updates; parented arms get the same guidance policy and opportunity/budget, not
identical corrective words despite different mistakes. Report actual parent
tokens, interventions, child tokens and training compute separately.

The immediate operational priority is a functioning matched parented learner /
frozen-control pair. Complete the other cells for the factorial claim rather
than silently treating the pair alone as the full design. Aim for at least
three independent developmental seeds if resources permit; smaller actual n
must be reported honestly. Extra decoding seeds do not replace those lineages.

Teach across math, reading/recall, writing and caption revision, but predeclare
one primary competency and unseen evaluation environment. Measure the chain:

1. Actual task and observable error/feedback.
2. Concrete correction identified in THINK, with exposure documented.
3. Correct next ACT/artifact, checked against the environment.
4. Another relevant attempt without a new reminder.
5. Repeat after sleep, in fresh context, without a parent, on unseen instances.

Use equal-budget evaluation copies and adapter ON/OFF controls as specified by
the original H1 spine. Do not give the parent sealed test answers. Missing
feedback/visibility is a separately reported invalid or unobservable condition,
not a fabricated behavioral score. All genuine child rows remain eligible.

### B. Secondary: continued learning on a new task (H2)

After the developmental comparison, remove parents and compare fixed-budget
learning curves with sleep enabled versus disabled, with developmental history
explicitly controlled. Report distinct accepted novelty against cumulative
generated tokens, task correctness where available, and update compute.
This tests a slope, not merely cumulative discoveries rising with time.

If the required controls or independent training replications are incomplete,
report this as exploratory. Do not promise H2 success in advance.

### C. Short, announced withdrawal; gradual taper only as a separate test

We have not completed this study. First verify useful guidance and a reliable
return/help route. Then announce one bounded absence: the child keeps its task
and ordinary feedback, knows help is temporarily less frequent, and receives
a longer-horizon objective rather than a promise of imminent micromanagement.

Measure artifact quality, checking, self-correction, branching and requests for
help. A longer taper schedule is a separate intervention to compare with
persistent parenting. Keep learning rate fixed in that comparison; changing
plasticity at the same time would confound the result. Later study plasticity
separately. A failed absence remains a result; return the parent as announced.
Never relabel downtime or a broken judge as deliberate independence.

### D. Fresh-scene game evaluation and judge audit

Use newly held-out scenes, fixed generated-token budgets, the same bound judge
and novelty code, no parents, and no historical working context. Freeze scene
selection and checkpoint ages before observing outcomes. Reuse the completed
sampling pipeline where its existing visibility/identity contract applies.

Alongside scored/accepted/novel counts, report no-caption acts, malformed or
unscored outputs, replay deduplication, environment-feedback delivery and compute.
Prepare a blinded sample of accepted and rejected captions for humor/scene-fit
review; do not call automated acceptance human humor validation. Keep old/new
judge epochs separate and preserve counterexamples, not only attractive captions.

## 7. Final-paper package

The framing is a study of whether guided experience becomes retained behavior,
with the two-timescale explanation as a hypothesis. In compact notation, the
fast loop produces an action from the frozen base plus current adapter, context,
task feedback and available guidance; the slow loop updates only the adapter
from the learner's eligible experience. This notation is explanatory, not a
change to the implemented loss, loop or visibility contract.

| Deliverable | Evidence or work needed | Current state |
| --- | --- | --- |
| Method diagram | Parent guidance, THINK, ACT, feedback, working context, sleep/adapter, evaluation isolation | Ready to draft from implemented stages; verify exact versions. |
| Main factorial table | Actual arm counts, independent seeds, parent policy/exposure, LoRA state, matched budgets | Proposed; controlled final campaign not complete. |
| H1 retention/transfer figure | Immediate, after-sleep and clean-context unseen-task performance; adapter/frozen controls | Decisive missing experiment. |
| H2 developmental learning curves | Parent-free new-task performance versus tokens, sleep on/off, training cost | Not established as a causal result. |
| Checkpoint exploration table | Completed base/sleep51/sleep117 sampling block | Ready as preliminary selected-checkpoint evidence. |
| THINK-to-ACT trace panel | Positive and failed cases with actual request/action IDs and visibility | Audited examples available; no lifetime success-rate claim. |
| Ablations/limitations | Context carryover, parent budget, update state, judge dependence, outages, drift, selected checkpoints | Must remain explicit. |
| Reproducibility appendix | Source/checkpoint hashes, manifests, exact prompts, task splits, accounting scripts, compute and missing-data policy | Much exists; consolidate and check links. |

Recommended section order: problem and H1/H2; method; controlled experimental
design; observed results; failure analysis; limitations and conclusion. Keep
interpretation separate from measurements. The central contribution cannot be
"autonomous self-improvement is demonstrated" without the missing comparisons.
If retention/transfer fails, report where the chain breaks and retain the
negative controls rather than choosing a post-hoc success criterion.

### Submission-readiness checklist

- [ ] Exact final experiment preregistration, controls, seeds and primary outcome bound.
- [ ] Parent guidance actually delivered and visible in both matched parented arms.
- [ ] Independent developmental replications completed, or limited n disclosed.
- [ ] H1 clean-context/held-out evaluation complete; H2 labeled to match its evidence.
- [ ] Taper claims absent unless the planned taper comparison actually ran.
- [ ] Metrics regenerated with duplicate handling and judge epochs verified.
- [ ] Figure/table cells link to exact source receipts; missing cells remain missing.
- [ ] Blind caption-quality review completed, or automated-metric limitation stated.
- [ ] Compute, guidance budgets, operational interruptions and historical row-policy changes reported.
- [ ] Claim-to-evidence pass against the submitted abstract and actual manuscript.
- [ ] Author review and venue-specific submission/checklist verification completed.

No conference requirement or deadline is independently verified by this document.
No external submission or communication is performed by preparing this packet.

## 8. Storage: why checkpoints take space and what to change

C0's last measured saved checkpoint payload is **242,659,584 bytes (~243 MB)**,
not3GB. Each retained version stores adapter/training state; temporary checkpoint
serialization can require another payload-sized footprint. For scale only,
100 payloads of that size would be24.3GB before logs; this is not an inventory
claim about C0's actual checkpoint count.

The conservative restart estimate comprises **~0.49GB** for checkpoint payloads
and temporary copies, **~0.35GB** for initial records/source/startup writes, and
**2GiB (~2.15GB)** of unused shared-disk headroom. That reserve is an engineering
choice, not part of the model and not a scientific threshold. Some individual
observed full-state records are already about21–22MB, making repeated state
serialization expensive independently of the adapter. The cached base model is
not being downloaded again under this startup estimate.

At19:13:49 UTC, node2 had1.415GB available to its owner and all eight GPUs idle.
The estimated writes alone fit; the full conservative reserve does not. A
startup-only fit is not sustained operation. Reconsider the reserve using actual
growth measurements and fix storage growth rather than treating an arbitrary
number as a permanent veto. No reserve reduction or recovery launch is done here.

**Proposed retention layout:** current recoverable state plus required live tail
on the active node; immutable older checkpoints/traces archived once with hashes
and a verified restore route; manifests, code and small result tables in Git.
Keep checkpoint ages required for comparisons, failure boundaries and negative
evidence, not just the best snapshot. Deduplicate identical archived copies and
regenerate disposable reports where safe. Do not delete the only copy, protected
state or a live journal; do not remove training rows. This plan is not a deletion
command or permission to discard evidence.

Storage receipt and budget:
`research_loop/workers/replication_sprint_20260919/operations/AUTH_AND_CAPACITY_RECHECK_20260919T1914Z.json`.

## 9. The evaluator issue, without implementation jargon

The agent writes a record; another program reads records to schedule and count
tests. We reproduced a case where the reader catches a record while its file
publication is still finishing, sees a metadata change despite identical text,
and stops. The exact historical outage is not conclusively attributed to this
case because the original error did not record enough detail.

The repair should wait for a completed publication, then verify the actual
content and source identity. Its tests must show that it still rejects genuinely
changed evidence and never counts the same evaluation twice. It should not simply
ignore every warning. The candidate remains undeployed. This blocks the automatic
every-sleep pipeline, not all inference or all fixed-budget testing. Keep the
original failed evidence and consumed-job accounting when recovering it.

Reader diagnosis: `research_loop/workers/replication_sprint_20260919/operations/PROBE_SOURCE_REPAIR_20260919/CHECKPOINT.md`.

## 10. Immediate engineering order

1. Recover the actual model-parent services using the existing working provider
   configuration; reconcile old failed calls without pretending they succeeded
   or duplicating their accounting. The independent19:14 UTC check returned
   HTTP200; Rohin does not currently need to resend a key. Reboot-persistent
   credential provisioning remains unverified.
2. Verify task → feedback → parent → ACT delivery for the kept comparison arms;
   record an actual checked action, not just a live process or queued message.
3. Resolve active storage growth and C0 recovery with preserved evidence.
4. Use the functioning fixed-budget path for bounded tests while repairing the
   automatic queue; do not hold all science behind that daemon.
5. Freeze the final controlled experiment manifest and run the highest-priority
   comparisons. Populate the paper with actual results, including negatives.

This preparation turn creates documentation and small receipts. It does not
restart parents, launch a new science arm, deploy the reader repair, change
learning, taper a life, delete data or promise unattended execution.
