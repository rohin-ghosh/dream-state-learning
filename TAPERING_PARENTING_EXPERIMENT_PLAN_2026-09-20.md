# Tapering-parenting development cycle — prospective plan

**September 20, 2026. Not yet deployed.** This formalizes the next experiment
Rohin asked for after reviewing the constitution and parenting docs. It is a
launch request and design target, not evidence that tapering has worked.

## Core hypothesis

The development cycle is:

```text
parenting instigates a useful behavior in context
  -> the child enacts it in the next action
  -> sleep/LoRA reinforces the child-authored experience
  -> later the child initiates the behavior with less parent support
```

The missing step is **tapering parenting**: periodic but longer, multi-turn
parenting episodes that ask for long-horizon self-reflection and concrete
repair, followed by declared lower-support windows. The point is not parent
absence by accident. The parent explicitly teaches, then explicitly withdraws
for a bounded window, then returns and audits what happened.

## Behavior to install and measure

Primary behavior: **produce the object, check the consequential claim, repair
the next action, and reuse the check without a reminder.**

Keep endpoints separate:

1. **Access:** relevant feedback or principle was visible.
2. **Context uptake:** child identifies a specific discrepancy while parent is
   present.
3. **Next-ACT repair:** the next action actually changes the artifact/check.
4. **Uncued reuse:** a later related task gets the check without a reminder.
5. **Post-sleep retention:** the behavior recurs after the scheduled update.
6. **Fresh-context transfer:** it recurs without the original working context.
7. **Taper performance:** it recurs during a declared lower-parent window.

Do not score generic reflection as success unless it changes an artifact or
check. Keep failures and unknowns in the denominator.

## Parent schedule

One taper cycle has four phases:

| Phase | Parent behavior | Child window | Measurement |
| --- | --- | --- | --- |
| Teach | multi-turn, concrete, object-stable guidance | immediate task | artifact and consequential check |
| Bridge | parent names the reusable habit and asks for next-action repair | next THINK/ACT | repaired artifact |
| Taper | parent announces a bounded absence or lower cadence | 2-3 attempts | spontaneous checks, help requests, drift |
| Return | parent audits actual attempts and teaches from evidence | one return turn | whether lesson survived and what failed |

For the first pilot, keep sleep/LoRA recipe fixed. Taper parent support before
tapering plasticity. Reduced learning rate or altered sleep dose is a later
factor, not part of the first claim.

## Candidate tasks

Use small connected blocks, not a single monoculture and not random churn:

- graph/math tasks with exact checks;
- short reading/retelling tasks with factual faithfulness;
- constrained writing/revision tasks with a visible requested artifact;
- optional caption exploration only as a separate exploration endpoint.

Each block should create one opportunity for a parent-cued repair and one later
opportunity for uncued reuse of the same habit in a different object.

## Controls

Minimum first study:

- updating best available learner under tapering parent;
- matched frozen sibling under the same parent schedule;
- if available, an unparented updating control with matched task exposure.

The paired learner/frozen services prepared on September 19 are attractive, but
their parenting path was reported blocked by provider authentication. Do not
pretend they are running if auth is still blocked. If those services remain
blocked, Astra should either repair/verify the provider path under existing
authority or choose another preserved best candidate with a working parent
route and matched frozen/control readout.

## Best-candidate constraint

Use preserved strong candidates when possible, especially C2 sleep51 or the
current best live descendants, but do not confuse "best checkpoint on caption
novelty" with a proven autonomous learner. Start from exact identities and
record:

- lineage/checkpoint/adapter hashes;
- completed sleeps and optimizer steps when available;
- current live process or saved-state status;
- parent policy epoch;
- frozen sibling/control identity;
- task block and token/turn budget.

## First operational request to Astra

Before launch, Astra should produce a run-control receipt with:

1. mailbox watcher status and whether a continuous watcher is alive;
2. candidate agent inventory: C2 sleep51/current C2, paired learner/frozen,
   and any other best available live descendants;
3. provider/auth status for parent calls;
4. exact proposed launch command(s) or handoff command(s);
5. the preconditions checked immediately before launch;
6. the first-stop condition and where receipts will be written.

If all preconditions are satisfied and no live-owner guard blocks it, Rohin's
intent is to start the smallest safe tapering-parenting pilot. If a blocker is
present, do not force through it; publish the blocker and the next concrete
unblock step.

## Claim boundary

A successful launch is not a scientific success. The first real result is a
trace where a declared opportunity produces:

```text
parent-cued repair -> next-ACT repair -> later uncued reuse
```

Only after that should post-sleep, fresh-context, and tapered-parent windows be
interpreted. Nulls are useful and should be reported plainly.
