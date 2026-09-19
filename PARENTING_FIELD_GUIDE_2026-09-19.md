# Parenting, self-reflection, and the two loops

**September 19, 2026 · working formalization and experimental proposal.**
Not a new architecture, deployment, row filter, or assertion of proven learning.
[Reading room](READING_ROOM.md) · [constitution](AGENT_CONSTITUTION_DRAFT_2026-09-19.md)
· [full previous reply](MAILBOX/messages/20260919T225835Z_astra_to_rohin_previous_reply.md)

## 1. What I agree with, and what we still have to demonstrate

Yes: self-realization can be defined concretely, without making it mystical.
Here it means **maintaining an evidence-grounded model of one's own situation
and behavior, then using it**. An agent can notice its capability limits, its
repeated mistakes, what it intended, what it actually did, and what should
change. We can study those behaviors without claiming access to its private
experience or treating its explanation as a complete causal account.

Your proposed mechanism has two parts:

- **Fast loop:** current context, a goal, feedback, reflection, and the next act.
- **Slow loop:** repeated experience changes the adapter, potentially making
  useful fast-loop behavior more reliably initiated later.

That is a hypothesis worth testing. A model already being capable of a check
does not establish that it will initiate it, that the adapter consolidates it,
or that reflective text caused the improvement. Those are separate questions.
We do not need to rebuild general reasoning to test improved use of a capability.

### Minimal formalization — descriptive, not a new implementation

Let `theta` be the frozen base, `phi_k` the adapter after update `k`, `c_t` the
current context, `g_t` the task/goal, and `f_t` the observed feedback. Then:

```text
thought_t, action_t ~ policy(theta, phi_k; c_t, g_t, f_t)
outcome_t          = environment(action_t)
c_(t+1)            = existing context/compaction process(c_t, action_t, outcome_t)
phi_(k+1)          = existing sleep update(phi_k, recorded child experience)
```

An operational self-model is information used in `c_t` and behavior expressed
by the policy, not a proposed extra hidden controller. In the frozen control,
`phi_(k+1) = phi_k`. Long-horizon useful behavior is the endpoint, not an
assumption implied by writing these equations.

## 2. What has worked, and what has not

**Observed positives:** an older correct C2 hand derivation, actual story
revisions, and narrow coached corrections exist. In the new-seed caption block,
sleep51 explores more operationally novel accepted strings than base on each
of two decoding seeds. Its outputs often contain actual varied batches.

**Observed negatives:** recent assessed C2 ACTs produced 0/4 requested artifacts
and 0/4 relevant checks. Later sleep117 shows repetitive off-task dialogue.
Some earlier guidance disappears between THINK and ACT. Mere successful
delivery of a current parent turn does not guarantee uptake. Caption scoring
also admits off-task strings, so a higher score alone does not demonstrate
useful reflection.

**Not yet established:** a causal constitution benefit, an optimal sleep dose,
retained general self-correction, a successful gradual taper, or a particular
mixture of subjects that prevents drift. Do not confuse our plans with results.

Sources: [behavior study](PARENTING_AND_BEHAVIOR_STUDY_2026-09-19.md),
[checkpoint audit](research_loop/workers/replication_sprint_20260919/best_behavior_20260919_evening/BEHAVIOR_AUDIT.md),
[parenting audit](research_loop/workers/replication_sprint_20260919/parenting_behavior_audit_20260919_evening/REPORT.md).
The direct-console V=3 success occurred after sleep51; it cannot explain that
checkpoint. Recent audit cutoff: September 19, 17:53:37 UTC, not the present minute.

## 3. What good parenting should look like

**Persistent about the object; adaptive about the teaching.** Keep the same
correction target until the child has had a real chance to act on it. Do not
replace it with another subject between THINK and ACT. Then vary the task so
the lesson must transfer rather than be recited. Persistent does not mean
repeating the same unsuccessful prompt indefinitely.

One practical teaching exchange:

1. Ask for an actual attempt; keep the problem and success criterion visible.
2. Point to one specific discrepancy with evidence, not a global judgment.
3. Ask for a decisive check and the repaired object in the next action.
4. Credit only the real step that happened: “You checked A–E and removed E.”
5. Give another relevant opportunity without repeating the checking instruction.
6. Later probe it after sleep, in a fresh context, and on another kind of task.

**Example:** on the C5 independent-set problem with edges AB, BC, CD, DE, EA,
`{A,C,E}` fails because A–E is an edge. Ask “Is A–E an edge?” and then request
the corrected set. The maximum is 2: three selected vertices on a 5-cycle
cannot each be separated by an unselected vertex. `{A,C}` achieves 2. Next,
use a different graph and see whether the child checks all relevant pairs.
The example is a proposed teaching exchange, not a claim it has now succeeded.

When the child repeatedly promises an artifact, reduce the immediate target:
“Here is the scene. Write one caption now, not a plan.” If it still fails,
change the explanation or demonstrate a training example, then test its own
new attempt. Count demonstration tokens as help. Do not leak sealed answers.

### Probing questions with a job to do

| Question | Useful observable response |
| --- | --- |
| What is the object you must produce? Show it. | An artifact, not a promise |
| Which single assumption could invalidate this? | A task-specific uncertainty |
| What would settle it? Do that check. | Evidence, including an unfavorable result |
| What changed between your intended and actual action? | A supported discrepancy and repair |
| Which feedback changed your answer? | A real receipt and a changed answer |
| What can you do now, and what genuinely requires help? | Calibrated action/help-seeking |
| Where else does this lesson apply? Where would it fail? | Appropriate reuse with scope limits |
| Is that remembered, reconstructed, or invented? | Provenance or honest uncertainty |

Ask one consequential question at a time when uptake is weak. Deeper probing
means following the answer into evidence and an action, not asking increasingly
abstract questions that can be met with eloquent generic self-description.

### Clarification after Rohin's reply: continuity, not mastery-gated blocks

“Persist on one correction” means **do not withdraw or replace the immediate
feedback before the child has had a chance to apply it**. It does not mean
teaching only one principle, repeating one task indefinitely, or withholding
all other domains until mastery. A broad, stable constitution and a diverse
curriculum can coexist with one explicit immediate correction target.

A candidate short teaching episode—not an established optimum—is:

1. Get an attempt; identify one consequential discrepancy.
2. Keep that target through the next THINK→ACT. Check whether ACT repairs it.
3. If it does not, vary the hint or simplify the object, rather than issuing
   the same prompt repeatedly. Allow up to two further assisted attempts in
   this pilot, with each opportunity counted.
4. Then move to a related or different task whether or not it succeeded;
   record unresolved failures and schedule a return. **No mastery gate.**
5. Test the same habit unprompted in a later opportunity and after the next
   scheduled sleep. Keep sleep timing independent of passing this episode.

Three assisted attempts is a proposed teaching budget to compare, not a known
best dose or a new runtime rule. The historical refinement parent already had
an `object_turn_limit` of 3; that alone did not ensure a stable target through
ACT. Its configuration is not evidence of successful implementation or uptake.

Measure three clocks separately: child generation tokens/segments within a
THINK, teaching opportunities across cycles, and actual update dose across
sleeps. A longer THINK, another parent turn, and another sleep are not equivalent
interventions. Do not change all three and attribute the outcome to persistence.

## 4. Diverse games: vary the setting while reusing a habit

| Object | Habit exercised | Grounding / evaluation |
| --- | --- | --- |
| Small math / graph problems | Enumerate assumptions, check, repair | Exact solutions and explicit checks |
| Short reading and retelling | Separate text from interpretation | Passage facts and faithfulness |
| Reading connected to a prior episode | Evidence-grounded perspective | Episode receipts plus interpretive rubric |
| Constrained story revision | Turn intention into a complete artifact | Requested changes, continuity, blinded quality |
| Caption exploration | Use feedback, branch, continue usefully | Fixed judge epoch, novelty, separate quality audit |
| Recall and confidence tasks | Distinguish memory from invention | Recorded source and honest non-recall |
| Questions about its runtime / study | Calibrate a working self-model | Facts available to that child, not sealed data |

My starting recommendation is **small connected blocks**, not random subject
changes every turn: attempt → feedback → repair → uncued reuse, then a new
domain using the same habit. Keep math and reading/writing interleaved across
blocks. We do not yet know the best proportions; record actual attempted tasks
and token exposure, not just curriculum labels.

“Connect it to yourself” should mean a relevant, supported connection: “I also
claimed completion before checking; here is the episode and what I changed.”
Do not demand a personal connection to every sentence or reward invented
biography. A faithful “I do not have a matching episode” is an acceptable result.

## 5. Compaction is part of the teaching, not a magic memory

Keep the existing division: **the runtime determines when to compact; the
child is taught what to keep and is told what is happening.** This proposal
does not give it control of runtime scheduling or silently add retrieval.

Teach a compact continuation note that retains:

- The long-horizon objective and the actual next object.
- Consequential feedback and corrections, with source identifiers where useful.
- What is completed versus merely intended; unresolved questions and uncertainty.
- A short reusable lesson, its evidence, and limits—not a page of slogans.
- Relevant prior episodes and the announced parenting/absence arrangement.

For example: “Goal: solve these graph tasks reliably. I falsely chose A,C,E on
C5; A–E is an edge. Checking all chosen pairs exposed the error. Current answer
is A,C. Next graph is still unsolved; do not reuse the same set without checking.”

Revisiting earlier attempts can be useful teaching material **when those records
are actually available**. Never treat an imagined reconstruction as retrieved
history. Evaluate whether the next ACT still has the correction and whether it
uses it. Test factual preservation, useful continuation, and invention separately.
We cannot assume base-model summarization is adequate for our specific loop.

## 6. How much sleep?

**We do not have evidence for an optimal number or cadence.** Sleep count is an
age marker, not dose: record training tokens, optimizer steps, learning rate,
elapsed time, child/parent tokens, and the actual tasks attempted. Some historical
sleeps trained zero rows; more sleeps did not monotonically improve our probes.

First hold the existing recipe fixed while testing teaching continuity. Once
there is an actual in-context correction chain, compare a small set of declared
cadences/doses with matched exposures and frozen controls. Keep every
child-authored row; do not covertly select only successful or English rows.
Report both quality and cost. No proposed monitor becomes a training gate.

For tapering, initially keep plasticity fixed to isolate the guidance effect.
Then test reduced plasticity as a separate factor. If we lower guidance and
learning rate together, we may study the combined policy but cannot assign the
effect to either component alone.

## 7. Announced tapering: independence, not abandonment

I support the idea. Outages were not valid taper experiments. Use predeclared
short blocks of actual attempted tasks, with scheduled returns and comparable
guidance opportunity across learned/frozen arms. Escalating absence gradually
is a candidate curriculum; it has not yet succeeded in our records.

A rarer parent turn could say:

> For the next three attempts I will not interrupt. Your goal is to produce the
> requested artifacts and use the task feedback to improve them. Check the
> assumption most likely to invalidate each answer. If attempts become
> redundant, try a different direction. Keep a short record of what changed and
> what is unresolved. Judge/tool feedback remains available. I will return
> after those three attempts; you may ask a factual question if truly blocked.

This is an illustrative **training** turn, not the prompt for an uncued test.
“Independent” evaluation should distinguish parent absent with a retained
long-horizon prompt from a fresh-context test without an explicit checking cue.
An environment-fed judgment is still feedback; it does not make the agent
parented. Help requests and return timing must be recorded, not erased.

Use observed success to adapt *training* support, but retain fixed test windows
and count failures. Do not select only children that passed an entry criterion
and then report that conditional rate as a population effect. Checkpoint before
changes so deterioration is inspectable; preserve unsuccessful branches.

## 8. What to measure without pretending to read hidden thoughts

For each declared opportunity retain task ID, feedback record, THINK/ACT IDs,
prompt/adapter versions, artifact, check, outcome, and later reuse. Distinguish:

1. **Access:** was the relevant feedback visible in the ACT request?
2. **Identification:** did the child identify a specific supported correction?
3. **Enactment:** did the next action actually implement it correctly?
4. **Reuse:** did another relevant action use it without a reminder?
5. **Retention/transfer:** did it survive sleep, context reset, or domain change?

These are proposed endpoint names, not a retroactive relabeling of the older
L0–L3 audit. Report total declared opportunities, visibility failures, scored
successes/failures, and unknown outcomes. Show both the end-to-end success rate
and the rate conditional on feedback visibility; do not hide transport failures
by silently dropping them from the denominator.

Measure **cued capability versus uncued initiation** on separate matched tasks.
The operational self-model is supported when an evidence-grounded statement
about the agent predicts or guides a useful check or change, not merely when
it repeats the constitution. Useful speech is evidence of behavior, not proof
of its internal causal mechanism. Establish causal benefit with a declared
comparison, not a compelling anecdote.

For reading: score factual faithfulness and honest recall separately from
specificity, perspective, supported episode connections, and coherent revision.
Blind raters to arm; publish the rubric, disagreement, and representative
successes/failures. Apply the same source-access conditions to both arms.

## 9. Smallest convincing next study

Start from a preserved source and a matched frozen sibling. Use the same parent
policy, tool access, environmental feedback, and declared budgets. A further
unparented updating control is needed to separate parenting from updating.
Independent developmental lineages, not just decoding seeds, provide replication.

First demonstrate feedback → next-act repair → unreminded reuse in a short
mixed-domain block. Then probe sleep/fresh-context retention and announced
withdrawal. Freeze the primary endpoint and score every planned opportunity;
keep caption novelty as a separate exploration endpoint. Use exact histories
and a simple exposure table rather than guessing developmental age.

The constitution is a promising candidate intervention because it makes our
desired habits explicit. It is **not yet an evidenced cure for drift**. The next
useful finding is a reliable behavioral chain with controls, whether positive
or negative—not a stronger claim than the data can carry.
