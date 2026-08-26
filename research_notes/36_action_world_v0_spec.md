# 36 — Action World v0: causal-action bridge after Semantic World

Status: CPU prototype implemented on `action-world-v0`.

## Scientific role

Semantic World answers the substrate prerequisite: structured experience can
be transported into LoRA and used compositionally. Action World adds the
smallest closed-loop consequence needed by the original continual-learning
thesis:

```text
act -> observe transition/outcome -> dream causal structure
-> consolidate -> encounter related state -> act better
```

The prototype intentionally does not attempt the final rich habitat or full
Alchemy environment. It creates a controlled bridge with attributable
failures.

## World state and causal law

Every threshold has four visible binary features:

```text
sun/moon sigil
brass/iron hinges
oak/stone frame
warm/cold draft
```

A seed-specific hidden parity law over two or three features determines the
danger side. Twelve of sixteen feature combinations appear in lived
experience; four combinations are held out. The experience split is selected
so the hidden law is uniquely identifiable by the privileged context-oracle.

This law is deliberately algebraic. It is a diagnostic for whether dreamed
causal memories carry through weights, not a claim that real action knowledge
is parity-shaped.

## Legal actions and transitions

```text
open             reveal the occluded passage, but not the attacker
inspect_left     reveal danger/clear on the left if open
inspect_right    reveal danger/clear on the right if open
guard_left       prepare against a left attack
guard_right      prepare against a right attack
enter            succeed iff the hidden danger side is guarded
```

Exactly one side is dangerous. Therefore a generic four-step adaptive policy
can inspect one side, infer the other if clear, guard, and enter. A learned
world law permits the more efficient three-step plan:

```text
open -> guard(predicted side) -> enter
```

The model receives feedback only for executed actions. Offline evaluation can
inspect the hidden law; the cognitive loop cannot.

## Lifetime

For every experience threshold, a scripted but feedback-responsive cautious
policy performs a successful crossing. A configurable fraction also receives
a reckless `open -> enter` failure. Episodes are shuffled so related feature
patterns and contrast pairs are temporally dispersed.

This supplies factual action consequences while leaving abstraction,
cross-episode causal induction, and consolidation to the dream/think system.

## Evaluation depths

| Depth | Evaluation state | Required memory/computation |
|---|---|---|
| A0 | witnessed threshold, 3 actions | remember experienced danger side |
| A1 | held-out feature combination, 4 actions | transfer inspect/guard procedure |
| A2 | held-out feature combination, 3 actions | infer world law and predict danger |
| A3 | two held-out thresholds, 6 actions | compose two predictions into a chain |

A3 is the minimal action analogue of D3/Blendyland. It should not be attempted
as a one-shot string-generation benchmark only; the model acts through the
public session interface and receives actual transition observations.

## Dream language candidate

The first GPU integration should preserve readable memories:

```text
TRANSITION | state=<features/status> | action=<action> | effect=<observed effect>
CAUSAL_RULE | context=<feature relation> | action=<action> | predicts=<effect>
ACTION_SCHEMA | goal=<goal> | preconditions=<conditions> | steps=<ordered steps>
FAILURE_MODE | context=<conditions> | action=<action> | outcome=<failure>
```

Every dreamed line carries episode/step provenance, depth, predictions, and
epistemic status. Atomic transitions may be consolidated strongly; derived
rules remain provisional until later experience supports them.

## Primary comparison ladder

```text
no memory
raw lifetime context
episodic RAG
direct trajectory -> QA -> LoRA (TMEM-like)
dreamed causal memories -> LoRA, no gate
dreamed causal memories -> self-check -> LoRA
micro-dream depth growth -> self-check -> LoRA
privileged parity/context ceiling
```

The direct trajectory-to-QA arm is essential: dreaming must add value beyond
ordinary parametric distillation.

## Metrics

- success rate and return by A0-A3;
- actions used / regret relative to the three-step oracle;
- raw, accepted, written, read, and behavior-used memory precision;
- time-to-first correct causal rule;
- depth and parent provenance of derived memories;
- recovery after contradictory evidence (future A4);
- seeds/worlds as the replication unit.

## Paper interpretation

If only A0 works, the adapter remembers actions. If A1 works, it carries a
reusable procedure. If A2 works, experiential world construction changes an
unseen action. If A3 works, depth-growing memory composes into a chained
policy. Only A2/A3 support the broader action-conditioned continual-learning
story.

## Deferred richer world

Action Habitat v1 should replace arbitrary parity with coherent animal,
habitat, tool, and intervention features while retaining an exact offline
engine. It should introduce graded value, delayed outcomes, partial
observability, and world-specific semantic exceptions. That is deferred until
the verifier-free Blendyland/micro-dream mechanism demonstrates real depth
growth.
