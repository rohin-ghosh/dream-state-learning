# ICLR 2027 readiness audit — 2026-09-06

Status: planning/report artifact. It authorizes no architecture change,
benchmark exposure, model/training execution, or GPU run.

Official dates:

- genuine abstract: 2026-09-18 23:59 AOE;
- full paper: 2026-09-25 23:59 AOE;
- main text: at most 9 pages, excluding references;
- double blind; required AI-use statement; reproducibility statement strongly
  recommended.

Primary sources:

- https://www.iclr.cc/Conferences/2027/CallForPapers
- https://iclr.cc/Conferences/2027/AuthorGuidelines

## Executive verdict

The project is **not submission-ready today**. It has a strong question,
valuable mechanism failures, extensive diagnostic infrastructure, and an
emerging defensible novelty boundary. It does not yet have the central
prospective positive result or the matched strong-baseline comparison required
for the current Experience Models claim.

Approximate readiness by layer (not a probability of acceptance):

| Layer | Readiness | Evidence / missing item |
|---|---:|---|
| thesis and motivation | 75% | coherent; terminology and claim boundary still need freezing |
| closest-work positioning | 70% | LEAFE, Early Experience, MemoPilot, Evo-Memory now identified; comparison table missing |
| benchmark validity | 35% | old worlds diagnose mechanisms; CompilerGym scout is confounded; final paired protocol unsealed |
| causal writer/agent architecture | 30% | typed provenance and native writer designs exist; no ratified live implementation |
| central positive evidence | 10% | no prospective repeated-write win over frozen/textual/batch controls |
| parenting/meta-learning evidence | 5% | Phase 0 was not parenting; valid practice-and-correction nursery unrun |
| reproducibility package | 25% | many hashes/audits; current headline run lacks source ancestry and seeded paired generation |
| manuscript/figures | 5% | abstracts and review notes exist; no 9-page manuscript or frozen result figures |

Overall project-to-current-claim readiness is roughly **25–30%**. The project
has more intellectual progress than this number suggests; the low number is
because a paper is gated by its weakest central evidence, not averaged across
all ideas and infrastructure.

### Submission strategy ruling (Rohin, 2026-09-06; adjudicated)

Target the ambitious ICLR paper this cycle, but make one causal arc carry it:

1. one parent teaches one child process-level thinking through target-blind
   tasks and thought-to-action correction;
2. the parent and all nursery text disappear;
3. the child enters a fresh deployment gym with Think--Dream--Sleep personal
   writes, against an otherwise matched frozen-parameter agent whose isolated
   evolving text playbook is itself a validated strong memory mechanism; and
4. a parenting-by-deployment-learning interaction distinguishes a better
   starting policy from a better ability to learn during life.

This one-parent/one-child $2\times2$ is now the sole headline. The former broad
C2--C5 Counterfactual Confluence lifetime is demoted to a conditional terminal
carrier/mechanism assay; it is not a prerequisite for the parenting result.
Dreaming, learned context management, population learning, background sleep,
and base-model promotion remain architectural horizon unless required by the
registered headline. Full rationale and resource correction:
`research_loop/advisory/20260906_iclr_headline_adjudication_v1.md`.

**Parenting scope ruling (Rohin, 2026-09-06):** no classroom, cohort,
multi-parent, peer-competition, or population mechanism in this paper. One
parent teaches one child how to think through practice tasks; the parent then
disappears. The deployed comparison is the parented Think--Dream--Sleep
learning agent versus a fit-free frozen-parameter `ACTIVE_TEXT_FIXED`
reference whose raw actor weights stay fixed while its text memory evolves. The causal design
also includes a parented-frozen child plus a dose-matched unparented childhood
forked with deployment writes off/on. The unparented child receives its own
target-blind nursery practice writes; otherwise parenting is confounded with
merely receiving post-training.

## What the current evidence establishes

### Established or strongly localized

1. Low-rank writes can materially change agent behavior.
2. Bare-text self-training can amplify its own representational accidents and
   destroy the executable action channel while retaining useful latent action
   content (B2 terminal strict `0.0511`, saved-byte permissive diagnostic
   `0.5287`, adapter-off `0.4859`).
3. The CompilerGym instrument distinguishes proposal content from routing and
   exposes writer pathology.
4. Prior controlled worlds establish several component facts: parametric
   transport is possible, recognition/read protocol matters, compact structure
   can outperform storing raw pair facts, and hypothesis generation is a
   bottleneck.
5. The early v6.1 `+0.0211` descriptive effect is not purely action-count
   volume, but mainly reinforces a four-pass action already printed in the
   birth prompt. It is transport of a supplied procedure, not discovery or
   learned THINK.

### Not established

1. Periodic personal LoRA consolidation improves later actions under a clean
   prospective comparison.
2. It beats a prospectively validated frozen-parameter active-text agent; a
   bounded LEAFE-style final batch write is descriptive context only.
3. It continues improving after the frozen loop or textual-memory baseline
   saturates.
4. It builds and traverses connected/compressed experiential knowledge in the
   same run that improves actions.
5. Parenting teaches a durable parent-absent reasoning disposition.
6. Learned dreaming/context management improves task performance.
7. The agent's **learning efficiency** itself transfers to a new environment;
   without this endpoint, “model meta-intelligence” is an interpretation, not a
   measured contribution.

## Revised claim ladder

The paper must not skip rungs:

| Rung | Claim | Current state |
|---|---|---|
| C0 | a writer changes behavior and failures are diagnosable | yes |
| C1 | one verified process correction becomes parent-absent behavior without erasing proposal quality | untested |
| C2 | unparented per-life writes improve deployed held-out value over its frozen twin | untested prospectively |
| C3 | the parented continual child beats the frozen-parameter active-memory reference under common ordinary resources | untested |
| C4 | parenting improves deployment-time learning beyond its static starting benefit (positive $2\times2$ interaction) | untested |
| C5 | a separate carrier intervention localizes any gain to authentic connected parametric experience | untested |

The preferred ICLR result reaches C4. C3 without C4 is an architectural system
win but not evidence that parenting taught the ability to learn. C2 without C3
is a narrower per-life consolidation paper. C5 is a conditional mechanism
result and must not delay the headline.

## Minimum headline experiment

Use one frozen base and one exact generated-token budget, with identical
context, tools, skills, files, the prospectively frozen and development-gated
`ACTIVE_TEXT_FIXED` updater/retriever, task opportunities, and public outcomes.
Cross parenting with deployment-time personal writes:

1. raw-actor, frozen-parameter active-memory (`R0`, the paper-facing strong
   reference; no fit but its isolated text memory evolves);
2. dose-matched unparented frozen (`U0`);
3. parented frozen (`P0`, inherited-competence control);
4. dose-matched unparented continual (`U1`, online-write control); and
5. parented continual (`P1`, the full Think--Dream--Sleep child).

The paper-facing comparison is `P1` versus `R0`. The primary causal estimand is
`[AUC(P1)-AUC(P0)] - [AUC(U1)-AUC(U0)]`, supported by change from each cell's
entry checkpoint and an early-slope analysis. Primary outcomes are held-out
value versus lifetime under equal generated tokens, forward transfer,
backward retention, and valid/distinct/informative actions per token. Proposal
quality and typed routing are scored separately. Accepted data, supervised
tokens, model calls, wall time, and GPU time are reported.

The fixed-sequence superiority hierarchy is the parenting interaction, then
`AUC(P1)-AUC(P0)` as the total benefit of parametric writes on top of common
strong active text, then `AUC(P1)-AUC(R0)` as the full-system public contrast.
The active-text mechanism must pass a disjoint once-only semantic-faithfulness
certificate plus prospective updater, retrieval/use, end-to-end, and headroom
gates or lose the word *strong*. Raw response
distillation, a bounded descriptive-only LEAFE-style final system, binding
derangement, and adapter-off remain staged diagnostics rather than coequal
longitudinal arms. No powered “beat LEAFE” claim is permitted.

## Operationalizing “model meta-intelligence”

Continual weight change alone is continual learning. Meta-intelligence becomes
measurable only when experience improves **how efficiently the model learns or
investigates a later problem**.

The clean endpoint is an adolescent transfer test:

1. parent/process-train agents on target-blind nursery environments;
2. remove parent, lessons, ledger, and nursery context at deployment while
   retaining only the permitted adapter;
3. place parented and regular agents in a fresh gym with equal initial task
   information and generated-token budgets;
4. measure early learning slope, surprise-to-experiment latency, information
   gained per action/token, and final performance;
5. repeat on a second ontology/task family to distinguish compiler skill from
   learning-to-learn.

The headline is the two-agent comparison. The minimal causal decomposition is
a $2\times2$: parenting $\{0,1\}$ by deployment-time consolidation $\{0,1\}$.
This distinguishes inherited competence, self-learning without parenting, and
the interaction that would justify the full architecture.

For held-out value $Y_{p,l}(t)$, predeclare the interaction
`[Y_11(t)-Y_10(t)] - [Y_01(t)-Y_00(t)]` plus change from each cell's
pre-deployment checkpoint. A parented child that merely starts higher but has
no positive interaction learned inherited competence, not a better capacity
to learn during deployment.

One parented child is a valid mechanistic demonstration but not an independent
population estimate; target tasks and rollout samples do not replicate the
parenting realization. General parenting language requires multiple isolated
one-on-one child lives raised by the same parent under the frozen protocol.

If the parented agent only starts with better task performance, it learned task
content. If it acquires new task competence faster under matched initial skill,
that is evidence for learned prospective/meta-level agency.

## Critical path to September 25

### Sep 6--9: freeze the paper and the instrument

- Freeze the one-parent/one-child parenting-by-continual-learning claim; do
  not put the broad carrier study back on the critical path.
- Finish and ratify typed action/outcome provenance plus the native-response
  writer floor.
- Freeze target-blind nursery tasks and one fresh CompilerGym deployment
  split, including the four diagnostic cells and entry checkpoint.
- Freeze the closest-work table and exact terminal diagnostic baselines.
- Start the anonymous 9-page manuscript now with result cells marked pending.

**Kill gate:** if the exact parent, nursery, writer, deployment, interaction,
and resource protocol is not frozen by Sep 9, the ambitious Experience Models
submission is no longer realistically supportable this cycle.

### Sep 10--12: writer floor and pilot

- Run the bounded interface-correction writer assay.
- Run a four-root, isolated one-parent/one-child $2\times2$ spending pilot.
- Confirm the data writer, action channel, source ancestry, common RNG,
  adapter serving, and sealed evaluation all work end to end.

**Kill gate:** if no native writer preserves both free routing and typed-forced
proposal quality by Sep 12, stop long GPU lives and write the controlled
negative/mechanism paper only if its evidence is broad and prospective.

### Sep 12--16: decisive headline run

- Execute the blinded-variance-selected number of independently raised child
  lives, not checkpoint or program pseudoreplication.
- Run `U0`, `P0`, `U1`, and `P1` with matched ordinary external resources,
  plus fit-free `R0` as the frozen-parameter active-memory reference.
- Produce entry-adjusted learning curves, the registered interaction,
  uncertainty, resource accounting, and a failure table.

**Kill gate:** a positive central result should exist by Sep 16. A genuine
abstract can still report a mixed/negative result, but cannot promise the
unobserved flywheel.

### Sep 16--18: abstract and main figures

- Freeze title, contribution list, two main figures, and actual abstract.
- Lock authors and verify every OpenReview profile before the abstract
  deadline.
- Submit a genuine abstract; no placeholder claims.

### Sep 18--22: replication and mechanism

- Replicate the decisive contrast.
- Complete adapter-off, shuffled/wrong-child parenting, and only the terminal
  mechanism diagnostics justified by the headline result.
- Add the second environment only if the primary experiment is stable.
- Conduct an adversarial result audit and rerun only preregistered failures.

### Sep 22--25: submission hardening

- Freeze all numbers and artifact hashes.
- Complete 9-page text, appendix, limitations, AI-use statement,
  reproducibility statement, anonymity pass, bibliography, and anonymous code
  bundle.
- Render and inspect the final PDF; reproduce every table/figure from one
  immutable result manifest.

## Go/no-go rule

Proceed toward ICLR 2027 only if, by Sep 16, a prospective experiment supports
at least a clean per-life learning result (`U1>U0`) or parent-absent system win
(`P1>R0`) with no unresolved leakage, source, seed, routing, or external-
resource confound. The preferred submission needs the positive registered
parenting-by-learning interaction (C4).

If that gate fails, do not turn Fable's exploratory runs into a headline by
wording. Preserve the work, write the instrument/failure result cleanly, and
target a later venue with the full parenting and cross-environment study.

Rohin's explicit preference is to make the ICLR attempt despite the compressed
schedule because the field is moving quickly. This preference changes the
parallelism and urgency, not the evidentiary gates or permission to report an
unobserved result.
