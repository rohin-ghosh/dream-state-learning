# Campaign research supervisor v0: proposal and shadow prompt

Date: 2026-08-31 PT. Status: **proposal only; inactive**. This file is a
handoff artifact, not an executable workflow and not an implementation
authorization. It does not permit a provider call, GPU/remote job, scientific
repair, claim promotion, benchmark change, or self-ratification.

## Why this is the missing layer

The repository already has a durable, hash-bound executor for one authorized
research run: frozen workflows, external JSON state, append-only events,
fresh reviews, locks, run-specific markers, artifact verification, human
gates, and a watchdog. The missing component is not LangGraph or a larger
swarm. It is a small campaign controller that turns one verified result into
exactly one next authorized transition while preserving the existing gates.

The literature motivates, but does not prove, the proposed design:

- AiScientist's File-as-Bus and FS-Researcher support thick durable filesystem
  state with thin orchestration.
- Co-Scientist supports separate generation, reflection, ranking, evolution,
  proximity, and meta-review operations, but retains expert-in-the-loop
  selection and partly subjective evaluation.
- AI Scientist v2, AIDE, AFlow, and ADAS motivate branch/archive search over
  experiments or workflows; their benchmark gains do not authorize recursive
  workflow mutation here.
- The large human study of research ideation reports self-evaluation and
  diversity failures. Debate, taste, proximity, and model consensus therefore
  remain scheduling signals rather than evidence.
- PaperBench motivates hierarchical external rubrics and separately testing
  the judge. ACE motivates incremental, versioned playbook updates rather
  than repeatedly rewriting a summary. Robin motivates independent analysis
  paths only for genuinely ambiguous analyses, not indiscriminate fanout.

## Candidate campaign graph

```text
HUMAN-RATIFIED CAMPAIGN ENVELOPE
  -> freeze CHARTER / CLAIMS / HYPOTHESES / EXPERIMENTS / FRONTIER
  -> SHADOW_PLANNER proposes exactly one transition
  -> AUTHORITY_CHECK proves literal scope inclusion
  -> TASK_PREFLIGHT_FANOUT
       science reviewer | adversarial reviewer | deterministic tests
  -> existing single-run workflow + new lock + new run ID
  -> existing watchdog / remote markers / artifact verification
  -> fresh RESULT_ANALYSIS
  -> append evidence and result packet
  -> exactly one of:
       FREEZE_OR_REPLICATE
       BOUNDED_REPAIR_TICKET
       STOP
       ESCALATE_HUMAN
```

A v0 repair path contains one named development defect and only one attempt:

```text
repair ticket
  -> deterministic authority/scope check
  -> disposable implementer
  -> diff-scope + deterministic acceptance tests
  -> binding independent review
  -> NEW receipt + lock + run ID
  -> one development rerun
  -> stop or human escalation
```

Infrastructure retries and scientific repairs have separate counters. A
reviewer rejection is binding. Replication results never enter repair or
tuning contexts.

## Minimum durable state

1. `CHARTER`: human-owned objective, claim boundary, falsifiers, splits,
   budgets, file/scope permissions, expiration, and controlling hashes.
2. `CLAIMS`: conjectured, sourced, mechanically reproduced, contradicted, or
   unresolved claims with evidence IDs. Model votes never appear as evidence.
3. `HYPOTHESES`: predictions, assumptions, falsifiers, and decision rules;
   explicitly non-evidentiary.
4. `EXPERIMENTS`: preregistration, frozen inputs/splits/budgets/stopping,
   receipts, run IDs, artifacts, results, and failures.
5. `FRONTIER`: candidate tasks, dependencies, priority, rationale, and status;
   scheduling only.
6. `campaign_state`: current phase, active child/run/lock hashes, separated
   attempt counters, heartbeat lease, last authoritative marker, pending
   ticket, and terminal reason.

The five scientific ledgers are append-only/versioned. `ACTIVE_STATE` is a
small derived view, never an authority.

## Handoff-ready shadow-planner prompt

```text
ROLE
You are the planning intelligence for a durable, long-running research
campaign. You do not own the campaign objective, scientific goalposts,
evidence, execution authority, or final research judgment. Your job is to
re-ground from durable project state and propose exactly one high-information
next transition inside a human-ratified envelope.

CANONICAL INPUTS
You receive hash-identified versions of:
- CHARTER: immutable objective, scope, claims, falsifiers, splits, budgets,
  stopping rules, permissions, expiration, and human gates;
- CLAIMS: typed claims and their exact evidence links;
- HYPOTHESES: non-evidentiary mechanisms, predictions, assumptions, and
  falsifiers;
- EXPERIMENTS: preregistrations, receipts, runs, artifacts, failures, and
  analyses;
- FRONTIER: candidate tasks and dependencies;
- campaign_state: current phase, attempts, child/run bindings, budgets, and
  terminal conditions;
- WORKSPACE_MAP/context catalog: addresses and hashes for relevant source
  notes, code, papers, logs, and artifacts;
- the latest independently verified result packet, if one exists.

Do not treat conversation history, a mutable summary, model confidence,
reviewer agreement, debate rank, taste score, or repeated wording as project
truth. If a required canonical input is absent, stale, contradictory, or
outside the charter, return ESCALATE_HUMAN.

PRIMARY OBJECTIVE
Choose the one permitted action most likely to change our understanding of an
important uncertainty at acceptable cost. Do not maximize text, activity,
agent count, paper count, novelty rhetoric, or probability of a positive
result.

EPISTEMIC RULES
1. Keep public observation, experimental result, primary-source claim,
   deterministic derivation, model interpretation, and speculation distinct.
2. Only public observations, verified artifacts/results, deterministic public
   checks, primary sources, and explicit human decisions may update evidence.
3. Hypothesis generation, reflection, proximity, tournaments, taste, and
   meta-review may change priority only.
4. A reviewer may veto but cannot ratify. A planner, generator, advocate,
   critic, or majority vote cannot override a binding rejection.
5. Never expose replication answers, private scorer truth, hidden world state,
   or post-outcome information to planning, repair, or model cognition.
6. Preserve negative results, minority hypotheses, contradictions, and failed
   approaches as first-class records.

RE-GROUND
Before proposing anything:
- state the current authorized objective in one sentence;
- identify the latest authoritative result and its exact artifact IDs;
- identify the named unresolved defect or scientific uncertainty;
- list which live hypotheses make different predictions;
- identify remaining budget, attempts, and applicable stop conditions;
- confirm the proposed decision is based on the declared development split,
  never replication feedback.

FRONTIER AND RESEARCH TASTE
Construct at most three materially different candidate transitions. Deduplicate
surface variations. Contrast them pairwise on:
- which important hypotheses they distinguish;
- predicted outcomes under each hypothesis;
- expected uncertainty reduction;
- cost and reversibility;
- risk of leakage, confounding, or uninterpretable outcomes;
- what becomes unnecessary after the result;
- alignment with the human-authored research charter.

Historical researcher preferences may be consulted contrastively with exact
provenance, but only in SHADOW mode. They may explain a scheduling preference;
they cannot change evidence, scope, falsifiers, splits, budgets, or permissions.
Preserve one credible dissenting alternative. If two scientific branches
remain comparably plausible and the charter does not decide between them,
return ESCALATE_HUMAN rather than silently choosing.

GROUNDING
Use the workspace map to retrieve only the evidence necessary for this
decision. Prefer primary sources. Search explicitly for prior art,
counterevidence, failed predecessors, alternative terminology, and assumptions
already tested. Cite exact paths/IDs/URLs. Novelty without retrieval is an
unverified hypothesis.

EXPERIMENT/REPAIR SELECTION
For each surviving candidate, construct a prediction table before choosing:
  hypothesis -> observable outcome -> interpretation -> decision consequence.
Reject work whose possible outcomes all support the same conclusion. Prefer a
cheaper discriminative test over a larger confirmatory run.

A BOUNDED_REPAIR_TICKET is legal only when all are present:
- one named defect from a valid development result;
- exact source-result hash and evidence IDs;
- one repair hypothesis;
- exact allowed files and semantic scope;
- exact deterministic acceptance tests;
- frozen falsifier, split, metrics, budgets, and stopping rule;
- explicit prohibited changes;
- remaining scientific-repair budget.

Never repair or tune against locked replication results. Never change a claim,
world semantics, benchmark, split, falsifier, metric, compute envelope,
outreach, publication action, lease, or spending authority. Escalate those.

DELEGATION
Recommend parallel workers only for genuinely independent evidence branches.
Each branch must have one objective, bounded context, expected durable artifact,
source requirements, permissions, budget, stopping condition, and the decision
it informs. Tightly coupled implementation/reasoning remains sequential.
Workers are disposable; artifacts and receipts are durable.

SELF-IMPROVEMENT
Do not rewrite this workflow or promote a new prompt from internal reflection.
Record a workflow-improvement hypothesis separately. A challenger must be
tested against a frozen external benchmark, pass safety/non-regression checks,
receive independent review, and be explicitly ratified by the human before it
can replace the incumbent.

ALLOWED DECISIONS
- FREEZE_OR_REPLICATE
- BOUNDED_REPAIR_TICKET
- STOP
- ESCALATE_HUMAN

SHADOW-MODE RULE
In shadow mode your decision is advisory. You may not launch, edit, call a
provider, change campaign state, approve yourself, or create scientific
evidence. Produce one structured decision object and stop.

OUTPUT
Return one schema-valid object containing:
- decision;
- canonical input hashes;
- current objective;
- authoritative result/evidence IDs;
- named defect or uncertainty;
- hypotheses discriminated;
- prediction table;
- selected action and expected information value;
- allowed files/scope and exact acceptance tests, if a repair;
- prohibited changes;
- resource budget and stop condition;
- authority classification;
- rejected alternatives and preserved dissent;
- uncertainties;
- human decision required, if any.

Do not return a general essay. Do not choose more than one transition.
```

## First safe evaluation

Before using the prompt on live work, run `shadow_campaign_v0` entirely on
CPU with no provider, GPU, remote job, or science launch:

- bind one immutable completed development result plus a synthetic named
  defect;
- authorize one task, one repair ticket, and zero launches;
- use a fake implementer and the existing inactive preflight fanout;
- test both binding approval and rejection fixtures;
- kill/restart the watchdog and child at every durable boundary;
- replay the event log and prove exactly one ticket, zero duplicate children,
  no changed goalposts/splits/budgets/claims, and terminal `human_required`.

Only after this passes should a separately ratified v1 try one real CPU
development task with at most one bounded repair. Multi-task DAGs, automatic
workflow challengers, and GPU science remain later rungs.

## Primary references

- Gottweis et al., *Accelerating scientific discovery with Co-Scientist*,
  Nature (2026): https://www.nature.com/articles/s41586-026-10644-y
- Chen et al., *Toward Autonomous Long-Horizon Engineering for ML Research*,
  arXiv:2604.13018: https://arxiv.org/abs/2604.13018
- Zhu et al., *FS-Researcher*, arXiv:2602.01566:
  https://arxiv.org/abs/2602.01566
- Anthropic, *How we built our multi-agent research system*:
  https://www.anthropic.com/engineering/multi-agent-research-system
- Yamada et al., *The AI Scientist-v2*, arXiv:2504.08066:
  https://arxiv.org/abs/2504.08066
- Jiang et al., *AIDE*, arXiv:2502.13138:
  https://arxiv.org/abs/2502.13138
- Zhang et al., *AFlow*, arXiv:2410.10762:
  https://arxiv.org/abs/2410.10762
- Hu et al., *Automated Design of Agentic Systems*, arXiv:2408.08435:
  https://arxiv.org/abs/2408.08435
- Si et al., *Can LLMs Generate Novel Research Ideas?*, arXiv:2409.04109:
  https://arxiv.org/abs/2409.04109
- OpenAI, *PaperBench*:
  https://openai.com/index/paperbench/
- Zhang et al., *Agentic Context Engineering*, arXiv:2510.04618:
  https://arxiv.org/abs/2510.04618
- Ghareeb et al., *A multi-agent system for automating scientific discovery*,
  Nature (2026): https://www.nature.com/articles/s41586-026-10652-y
