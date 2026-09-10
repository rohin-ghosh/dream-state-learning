# ICLR headline adjudication v1: one parent, one child, one deployed life

Date: 2026-09-06

Status: **design-only adjudication**. This document authorizes no architecture
change, implementation, target enumeration, model call, adapter fit, GPU use,
external access, or scientific claim. The selected protocol still requires the
complete `AGENTS.md` change workflow, exact-byte human ratification,
implementation/review, and pre-GPU gates.

## Binding human ruling

There is no classroom, cohort, peer exchange, teacher ensemble, or population
learning mechanism in this paper. Parenting is one-to-one: one parent teaches
one child how to think through assigned tasks and thought-to-action correction.
The parent then disappears. The learned child is deployed with the
Think--Dream--Sleep per-life learning architecture against an otherwise matched
ordinary frozen-parameter agent with the same prospectively validated active
text memory, and learning over the deployed lifetime is measured.

If the intervention is repeated, each parent--child life is sealed from every
other life. Repetition supplies independent statistical units; it is not a
classroom and is not a mechanism by which agents share learning.

## Verdict

**Adopt the one-parent/one-child parenting-by-continual-learning experiment as
the sole headline. Demote Counterfactual Confluence v0.3-R to a terminal
carrier/mechanism assay. Reject the unmodified seven-arm, four-cut C2--C6 plan
as the ICLR critical path.**

This is not merely a calendar compromise. It is the experiment that directly
tests Rohin's project claim: can a model first be taught a better way to think,
then use its own experience to keep improving after the teacher is gone? The
larger v0 plan tests several interesting memory-carrier questions but makes a
generated observation fixture carry an on-policy agency claim it does not yet
support, and its exact cost is not closed.

## The paper in one causal diagram

```text
target-blind practice tasks
        +
one process-only parent
        |
        v
child thinks -> acts -> sees public outcome -> retries
        |
        v
world-supported corrected child continuations -> child LoRA
        |
        | parent, feedback text, nursery transcript, and practice ledger removed
        v
fresh CompilerGym deployment
        |
        +--> frozen child
        |
        +--> Think -> Dream -> Sleep -> updated child -> next task
```

The parent proposes credit assignment; the public task outcome decides whether
the proposed lesson is admitted. Parent prose is never a supervised target.
The supervised target is the child's corrected thought/action continuation,
with parent scaffolding progressively removed from its input. This tests a
durable disposition rather than obedience to a visible teacher.

## Headline presentation and necessary diagnostic design

The paper-facing figure contains two agents:

1. **Parented learning agent:** parented once, parent absent at deployment,
   Think--Dream--Sleep writes enabled during the fresh gym.
2. **Frozen-parameter active-memory reference (`R0`):** raw pinned actor
   weights, no parenting, no childhood or personal parametric writes, and the
   same isolated evolving `ACTIVE_TEXT_FIXED` store during the fresh gym.

The causal experiment must nevertheless be the following $2\times2$:

| childhood | deployment writes off | deployment writes on |
|---|---|---|
| unparented dose-matched practice | `U0`: unparented frozen child | `U1`: unparented continual child |
| parented | `P0`: parented frozen child | `P1`: parented continual child |

Both childhood branches receive the same target-blind practice opportunities,
write cadence, optimizer budget, native anchors, and cumulative LoRA rebuilds;
the U branch writes only its own world-supported continuations and never sees
parent text or P targets. Therefore `U0` is a dose-matched unparented control,
not the pristine ordinary model. `R0` is the fit-free raw-actor, frozen-
parameter active-memory reference for the paper-facing pair. `P0` separates inherited starting competence from later
learning. `U1` separates online consolidation from parenting. Only the P/U
interaction can support the parenting claim; `P1 > P0` is the controlled
total-effect comparison for deployment LoRA writes on top of strong active
text, while `P1 > R0` is the full-system public result.

Every cell retains the same ordinary agent affordances: base model, context
budget, tools, skills, files, one isolated prospectively validated
`ACTIVE_TEXT_FIXED` updater/retriever, clock/token
awareness, task opportunities, public outcomes, and generated-token budget.
The experiment disables only parenting and/or personal parametric writes.
External artifacts are not removed from the learning agent to manufacture a
LoRA-only advantage.

## Parenting phase: what is taught

Parenting teaches process, not CompilerGym answers. The nursery task family
must be target-blind with respect to deployment program identities, LLVM pass
sequences, benchmark outcomes, and probe targets. The parent may correct a
small frozen process vocabulary such as:

- state an expectation before acting;
- notice a large expectation violation;
- isolate one uncertainty with a cheap discriminating action;
- avoid repeating an action after contrary evidence;
- scope a belief to the experiences that support it;
- turn a useful thought into an executable tool action;
- preserve the current goal, state, and unresolved questions when reconciling
  a crowded context; and
- stop or redirect when marginal progress per token collapses.

One cycle is:

1. child attempts a practice task under a fixed generated-token budget;
2. parent sees only the child's public trace and public outcomes;
3. parent names one process failure and proposes one correction;
4. child restates the correction in its own words;
5. child retries on a separate but homologous task;
6. the public outcome admits the lesson only if the registered process and
   task criteria improve without hidden or parent-supplied answer content;
7. sleep trains on the corrected child continuation, using scaffold-faded
   inputs and canonical tool/action syntax; and
8. the next cycle begins from the resulting child checkpoint.

The matched unparented child receives byte-identical tasks, outcome access,
token budgets, dream opportunities, native writer, fit count, labeled-token
and optimizer ceilings, and cumulative childhood LoRA writes from its own
supported behavior, but no parent message. It must not be given dummy text
that changes the task semantics; parent slots use frozen neutral role/token-
matched inputs declared in advance. Without those U writes, parenting would
be confounded with merely receiving nursery post-training.

The number of cycles, feedback dose, accepted-row rule, LoRA rank/placement,
heat, and scaffold-fading mixture remain protocol variables to be fixed by a
target-blind teachability canary. They are not free variables during the
confirmatory run.

## Deployment phase: what is measured

Deploy all four checkpoints on the same sequence distribution of fresh,
unique CompilerGym programs. Within a root, use matched assigned programs,
initial states, RNG opportunities, probe panels, and generated-token budgets.
The realized trajectories may diverge on-policy; byte-identical outcomes must
not be falsely required after actions diverge.

Probe at entry and at predeclared lifetime cuts. The main curve is held-out
program value versus deployed lifetime. Episodes end on generated-token
budget, not action count; actions remain available under the same typed tool
contract. Report action count as behavior, not as a hidden resource advantage.

Primary root-level quantities:

- normalized area under the held-out value--lifetime curve;
- early learning slope after the common entry point;
- forward transfer to unused programs;
- backward retention on earlier probes; and
- value, valid/distinct actions, and information gain per generated token.

Let `AUC(P1)`, `AUC(P0)`, `AUC(U1)`, and `AUC(U0)` be independently rooted,
within-root paired summaries. The primary parenting-of-learning estimand is

```text
I = [AUC(P1) - AUC(P0)] - [AUC(U1) - AUC(U0)].
```

The same interaction is reported at each registered lifetime cut as a
secondary curve. A higher `P0` entry score with parallel later slopes is
parent-absent process transfer, not improved learning. `P1 > R0` without a
positive interaction is an architectural system win but not evidence that
parenting improved the ability to learn.

Fixed-sequence superiority then tests `AUC(P1)-AUC(P0)` as the closed-loop
benefit of personal writes in a parented active-memory agent, followed by
`AUC(P1)-AUC(R0)` as the full developmental-package comparison. The active
text system must pass updater, retrieval/use, end-to-end, and headroom gates;
otherwise it is not called a strong baseline.

## Independent units and power

The independent unit is a separately raised child life: its practice
trajectory, parent interaction, accepted corpus, adapter optimization, and
deployment trajectory. Programs, actions, decoding samples, checkpoints, and
probe targets are repeated measures, not independent children.

A literal one-child Rohin-parented run can be a high-value mechanistic case
study and the clean two-agent visual. It cannot by itself estimate a general
parenting effect. A confirmatory claim requires multiple isolated one-on-one
children raised under one frozen parent policy. This is replication, not a
classroom.

Do not predeclare 12 roots as powered. The independent resource audit found
that a true interaction of `0.03` at `n=12` has about 80% power only if the
root-level interaction SD is at most `0.034`. Use a four-root spending pilot
only to validate direction, plumbing, and estimate treatment-label-blind
variance. Then choose a predeclared maximum of 20 or 32 confirmation roots
using the blinded variance rule. At a true effect of `0.05`, approximately 20
roots are plausible when SD is near `0.075`; approximately 32 are needed when
SD is near `0.10`. Publish the sensitivity curve rather than calling a
feasibility-limited sample universally powered.

## Resource truth

With `J` frozen parenting write cycles and three deployment write cuts, the
four-cell design needs `2J + 6` adapter fits per independent root: `J` parented
practice fits, `J` matched unparented practice fits, and three deployment fits
for each continual cell. Thus:

```text
n=20: 20 * (2J + 6) fits
n=32: 32 * (2J + 6) fits
```

For example, `J=3` implies 240 or 384 fits. Rank reduction does not divide fit
time proportionally because the frozen 7B forward/backward path, sequence
length, model load, save, and serving reload still dominate. Before spending,
bind exact logical samples, generated tokens, fit rows/tokens/steps, engine
lifecycles, terminal fit p95, retries, GPU IDs, and lease end. The current A40
lease ends September 14; September 16 evidence is not credible without an
extension or replacement compute receipt.

## Secondary mechanism assay, not a second paper

Counterfactual Confluence v0.3-R remains useful for asking whether a compact
linked parametric carrier preserves a counterfactual relation better than
controls. It is not currently an agent-own action/outcome lifetime: the source
is a generator-authored observation sequence whose `action` field is the
fixture phase. Do not use it to claim an on-policy self-learning flywheel.

If the headline pilot is positive and the runtime is available, run one
terminal post-context carrier panel with a common frozen resolver:

- compact linked carrier;
- denotationally equivalent expanded linked carrier;
- atoms-only carrier;
- binding-deranged carrier;
- bridge-cut carrier;
- same-corpus active-text read; and
- exact adapter-off diagnostic.

Decision/action targets must be identical or absent across carrier arms so the
panel tests stored connectivity rather than imitation of a supplied action.
The compact and expanded carriers must be byte-audited for semantic
equivalence. At least 48 fresh paired roots is the scientifically preferred
mechanism sample; 20 is explicitly a pilot. This panel is conditional and
must never consume the headline parenting roots or delay the main result.

## Claim ladder

The evidence may support only the highest rung whose tests pass:

1. **Writer floor:** a supported process correction enters a LoRA and changes
   clean-context behavior without breaking the action interface.
2. **Parent-absent transfer:** parenting changes a target-blind disposition
   after all parent text is removed.
3. **Continual-learning efficacy:** `U1` improves over `U0` during deployment.
4. **Parenting improves learning:** the registered interaction `I` is positive
   with the required uncertainty bound and practical margin.
5. **Strong-memory value:** `P1` outperforms parent-matched `P0` on the
   registered lifetime summary after `ACTIVE_TEXT_FIXED` passes its strength
   gates.
6. **System win:** `P1` outperforms fit-free frozen-parameter active-memory
   `R0` under matched deployment resources.
7. **Carrier mechanism:** only if the separate v0.3-R interventions pass.

Do not claim novel strategy discovery from the supplied four-pass bootstrap,
general creativity, population learning, unbounded self-improvement, or
physical-world invention. Do not call a higher starting score a higher
learning rate.

## Staged kill gates for the ICLR attempt

1. **Teachability/writer canary:** one target-blind correction must survive
   parent removal, change a registered disposition on new tasks, preserve
   typed free-action compliance, and pass adapter-off/shuffled checks.
2. **Exact protocol closure:** freeze parent identity/policy, nursery tasks,
   `J`, dose, rank/placement, heat, sleep compiler, dream/context behavior,
   deployment program split, cuts, token budgets, estimands, roots, and a
   maximum call/fit manifest before confirmation identities are revealed.
3. **Four-root end-to-end spending pilot:** all four cells, zero provenance or
   routing failures, and a positive directional interaction in at least three
   roots. The pilot is not confirmation and is never pooled into it.
4. **Confirmation:** run the predeclared root count. Do not rescue a miss by
   changing the parent, writer, parser, benchmark, or estimand.
5. **Mechanism panel:** execute only after the headline result and immutable
   artifacts are secure.

If the writer canary cannot move a disposition without damaging proposal
quality, the ICLR paper becomes a controlled negative about the gap between
absorbing text and acquiring a parent-absent habit. If continual learning
helps but the interaction misses, submit the per-life learning result without
the meta-intelligence claim. If only `P0` improves, report static process
transfer. The conclusion follows the data; the experiment is not weakened
after seeing it.

## Exact decision still owned by Rohin

The architecture is now fixed at one parent and one child. The remaining
identity decision is not cosmetic:

- a frozen model parent permits many reproducible isolated child lives and a
  population-level causal estimate under one parent policy;
- a Rohin-parented child most directly instantiates the motivating idea but,
  unless Rohin repeats the frozen teaching protocol across independent child
  lives, is a mechanistic case study rather than a general effect estimate.

Development may use Codex- or Rohin-authored feedback on explicitly excluded
children to establish teachability. The reproducible confirmatory candidate is
the pinned local Qwen2.5-32B parent under a closed three-code process policy;
a Rohin-parented child is an additional mechanistic case unless Rohin repeats
one frozen blinded protocol across independent roots. Parent identity remains
an exact human-ratification field before source generation.

## Adjudication against the two independent attacks

Adopted from the science attack:

- parenting $\times$ deployment consolidation as the sole headline;
- a prospectively specified, development-gated strong active-text mechanism
  plus matched files/skills/tools in every cell;
- on-policy outcomes after matched task/RNG opportunities;
- v0.3-R as a terminal carrier panel, not an action-learning lifetime;
- separate static starting competence from learning-rate interaction;
- do not treat 12 children as automatically powered; and
- remove action/decision-supervision confounds from carrier ablations.

Adopted from the resource attack:

- reject the unclosed 600-fit number as total cost;
- close logical-call, token, fit, engine, retry, and lease manifests;
- use cut-specific/p95 fit times rather than a global median;
- treat pilot roots as spending evidence, never confirmation;
- choose confirmation roots by a blinded variance rule; and
- stage optional mechanism work after the central positive result.

Rejected from the original headline v0:

- C2--C5 as mandatory before parenting;
- the seven-arm four-cut v0.3-R lifetime as the submission critical path;
- LoRA-only evaluation that removes ordinary external resources;
- generated observations described as agent-own action experience;
- C5 compact-versus-atoms as a clean connectedness test while decision rows
  differ; and
- the claim that 600 fits or 15--35 generation GPU-hours describes the full
  program.

## Immediate next artifact

The proposal-only candidate is
`research_loop/plans/one_parent_child_headline_v1.md`, with `J=3`, twelve
parent opportunities, 48 unique deployment programs, three deployment writes,
eight sealed probes per cut, rank-8 all-layer response-only writing, `R0`, and
a 20/32-root blinded-variance rule. It still requires the full external
architecture deliberation and exact-byte Rohin ratification. Only then may its
scoped implementation and CPU fixtures begin; model or GPU execution requires
a later fresh review and pre-GPU gate.
