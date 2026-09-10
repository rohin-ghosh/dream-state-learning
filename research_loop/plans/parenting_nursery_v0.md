# Parenting nursery v0 — teachability before childhood scale

Status: nonnormative design note, 2026-09-06. No model, training, behavioral,
GPU, claim, or release authority. This is the next experiment candidate after
the PPC causal transport assay establishes a trustworthy write/read path.

**Scope correction (Rohin, 2026-09-06):** parenting is a one-to-one process:
one parent teaches one child how to think through practice tasks and
thought-to-action correction. The parent then disappears. The resulting child
is deployed with the Think--Dream--Sleep per-life architecture in a fresh gym
against an ordinary agent, and learning is measured over deployment lifetime.
There is no classroom, cohort, teacher ensemble, peer exchange, or population
mechanism in this paper. If independent parent--child lives are repeated for
statistical confidence, they remain isolated replications of the same dyadic
protocol and never share lessons, context, experience, or artifacts.

The first unratified `organism_v6/nursery.py` sketch failed static preflight:
lessons are silently clipped, long prompt-first truncation can remove all
supervised response tokens, the parent prompt has no runtime consumer, and its
assay measures direct lesson recitation rather than disposition transfer. See
`research_loop/advisory/20260906_nursery_phase0_static_audit_v1.md`. Do not use
that implementation as evidence or launch it unchanged.

## Phase-0 scout result and resulting architecture proposal

Fable's already-launched phase-0 artifact was audited after the fact. It was a
null/adverse writer scout, not parenting: every lesson was clipped to its
first 1,176 source characters; 55/56 supposedly native NOTE-admitted thoughts
lacked a native line-start NOTE marker; adapter ON emitted fewer executable
actions and recalls than OFF; neither arm wrote a scoped note. The “mystery
box” probe had no interactive box and retained the compiler bootstrap. Exact
hashes and counts are in
`research_loop/advisory/20260906_nursery_phase0_live_artifact_audit_v2.md`.

The independent long-life audit found the same failure at larger scale. One
adapter checkpoint scored zero because it wrote useful pass sequences as
Markdown (`### ACT:` / `- **ACT:**`) rather than the harness's executable
`ACT:` line. Those saved intended actions score 0.529 when evaluated post hoc,
but the registered harness correctly executed none. Its sleep corpus had
amplified this formatting drift across cycles. See
`research_loop/advisory/20260906_fable_v61_longrun_independent_audit_v1.md`.

**Proposed delta for formal architecture deliberation:** keep THINK as one
free-flowing operation, but make ACT an explicit typed tool-call channel. One
cognitive loop does not imply one untyped serialization channel. The sleep
compiler should type and train at least three distinct continuation classes:

1. `THOUGHT_CONTINUATION`: free reasoning text in the live chat template;
2. `TOOL_CALL_CONTINUATION`: schema-valid call bytes that actually dispatched
   and have a bound public outcome;
3. `DREAM_STATE_CONTINUATION`: validated successor context with goal, current
   model, unresolved surprises, evidence, and plan.

Tool results, old transcript, parent text, and ledger evidence are masked
inputs, never casually copied as assistant targets. A raw transcript target is
an explicit negative control. This proposal requires the repository's full
architecture-deliberation and human-ratification path before implementation.

## Question

Can process-only parental feedback teach one life-LoRA a better way to learn,
such that the improvement remains when the parent and feedback text are absent?

This is deliberately narrower than “does parenting make an intelligent
agent?” The first gate is taught disposition -> parametric absorption ->
held-out behavioral effect.

## Child and inheritance

- One fixed lab-schooled base model and one full-layer rank-8 life-LoRA.
- A target-blind inheritance pack distilled from the repository's general
  laws: predict before acting, use surprise for credit assignment, cheap
  falsifiers first, scope memories, diversify before commitment, monitor
  token/time cost, recall before re-deriving, and distill context reversibly.
- Exclude benchmark source, held-out identifiers, compiler-pass names,
  program-specific scores, winning actions, and any result-derived target
  hint. Freeze a byte manifest and run a lexical plus semantic leakage audit
  before sampling evaluation tasks.

The child may disagree with or outgrow the inheritance pack. It is a starting
prior, not immutable law.

## One parenting cycle

1. **Live:** child receives state, budget, prior notes, and environment result;
   it freely thinks and acts under a generated-token budget.
2. **Observe:** parent sees the child's public thought/action/outcome trace,
   but no hidden target answer or held-out result.
3. **Teach:** parent gives process feedback only: identify one useful behavior,
   one concrete reasoning failure, one question the child should answer, and
   one small exercise or next experiment. No action answer is supplied.
4. **Restate:** child explains the lesson in its own words and applies it to a
   different training situation.
5. **Dream:** child emits a successor conscious state: goal, current model,
   unresolved surprises, active plan, scoped notes, and recalled evidence.
   The prior full stream is checkpointed in the immutable ledger; KV state is
   dropped only after the successor state validates and can be reversed.
6. **Sleep-write:** compile state -> child thought/action -> outcome -> parent
   correction -> child restatement as chat-templated examples in the exact
   dialect used during life. Train from the clean base plus cumulative
   accepted corpus; response-only loss; low heat; write receipt and adapter
   hash.
7. **Probe:** parent absent, clean context, adapter ON and OFF on paired sealed
   tasks and process probes.

Parental advice is a hypothesis, not truth. It enters the positive sleep
corpus only if the child applies it on the separate training exercise and the
public outcome improves against the prebound retry/control rule. A plausible
but unsupported lesson remains in the ledger as rejected advice and may
remain an open surprise; it is not teacher-forced as a correct disposition.
This makes parenting supply credit-assignment proposals while the environment
retains final admission authority.

### Scaffold fading is part of the write

Training only `state + parent correction -> improved continuation` can teach
obedience while leaving the behavior dependent on seeing the parent text.
Each admitted correction therefore produces a prebound scaffold ladder with
the same verified child continuation:

1. full parent correction in the input;
2. a short child-authored lesson/restatement in place of the parent;
3. only the ordinary task state plus a neutral self-review cue;
4. ordinary task state alone, when the target remains unambiguous and legal.

The parent, public outcome, and prior transcript remain masked inputs; only
the child's corrected thought/tool-call/dream-state continuation is a target.
The ladder must be dose-matched against controls so repeated targets do not
manufacture an apparent effect. Parent-absent improvement is the absorption
test; parent-present improvement alone is ordinary in-context instruction
following.

## Deployment comparison after parenting

The headline presentation is deliberately simple:

1. one parent teaches one child how to think through target-blind practice;
2. the parent, lessons, practice ledger, and nursery context are removed;
3. the child retains only the permitted learned parametric state and enters a
   fresh deployment gym with the Think--Dream--Sleep learning architecture;
4. an ordinary agent receives the same deployed tools, task stream, context
   and external-artifact affordances, and generated-token budget; and
5. compare prospective learning curves, forward transfer, and retention.

Two diagnostic controls are necessary even though they are not additional
headline organisms: parented-but-frozen isolates the inherited starting
policy, and unparented-but-continually-learning isolates the online learning
loop. The four cells identify parenting, continual consolidation, and their
interaction. Without them, a two-agent difference cannot show whether the
child won because it started stronger or because it learned faster after
deployment.

If the final contains literally one parenting realization and one child
adapter, treat parenting as a mechanistic case study; repeated deployment
tasks are not independent childhoods. The registered confirmation therefore
uses iid roots of the same frozen parent-policy/child-policy protocol solely
to estimate uncertainty. A root is a fresh isolated realization, not another
participant in a population-learning system: no root observes, teaches, or
shares context, feedback, experience, weights, stores, or artifacts with any
other root.

## Causal arms

All arms use the same base, tasks, generated-token budget, tools, state
renderer, and action opportunities.

1. **Regular:** no parenting, no LoRA update.
2. **Context parent:** authentic feedback remains in context, no LoRA update.
3. **Parented LoRA:** authentic feedback is consolidated; feedback absent at
   probe.
4. **Shuffled parent:** same feedback/token/dose marginals, assigned to the
   wrong episodes before consolidation.
5. **Wrong-child parent:** dose-matched feedback from a different life.
6. **Adapter-off:** exact parented checkpoint with its adapter removed.

The first decisive contrast is parented LoRA vs regular. Context parent tests
whether ordinary prompting is enough. Shuffled/wrong-child test whether the
effect requires this child's actual experience. Adapter-off localizes the
effect to parametric state.

## First teachable dispositions

Register a small set before training:

- prediction coverage and calibration;
- valid, distinct actions per generated token;
- probability of investigating a large surprise before repeating an action;
- scope fidelity (“this program” vs “across programs”);
- recall-before-rederive and note revision after contradiction;
- dream compression fidelity: retained goal/state/surprises/evidence, plus
  successful restoration of one intentionally omitted fact from the ledger.

These are secondary mechanism endpoints. Primary value remains sealed-task
best score/AUC versus lifetime under equal generated-token budgets.

## Writer calibration before long parenting

Race three small corpora at matched accepted tokens:

- raw public trajectory;
- episode-distilled trajectory with parent correction;
- cross-episode, scope-tagged principles plus representative episodes.

Every corpus uses the child's live chat/state/action dialect. Generic
“recall something learned” Q->A training is an explicit negative baseline,
not the default writer. Start rank-8 and cool. Increase rank only after
verified accepted data volume grows and absorption/behavior assays show
under-capacity; do not infer rank from task duration alone.

## Gates before Rohin's parenting time

Invite Rohin only after all are true:

1. authentic lesson content is target-blind and byte-frozen;
2. a known correction is recognized in weights above adapter-off/shuffled;
3. at least one registered disposition changes in the intended direction at
   clean-context probe;
4. the change survives parent removal and does not degrade a generic behavior
   panel beyond its registered tolerance;
5. wall-clock and accepted-token estimates for one useful teaching cycle are
   measured rather than guessed.

Then produce a short parenting guide: which feedback forms stick, required
repetition, response format, correction timing, common failure modes, and the
expected hours/tokens per durable lesson. The later headline experiment is a
Rohin-parented adolescent against the identical regular agent on a fresh gym.

The first two teachability rungs should be separated:

1. **Interface correction (writer floor):** after a child emits a near-miss
   non-dispatching tool call, a parent explains the typed boundary. Test exact
   parent-absent tool-call compliance on different tasks. This only proves a
   correction can enter weights and affect behavior.
2. **Reasoning correction (scientific target):** parent one child-specific
   process failure—such as repeating after a surprise, overgeneralizing one
   episode, or failing to run a cheap discriminator—and test the disposition
   on a new interactive task. This is the first “learn how to learn” claim.
