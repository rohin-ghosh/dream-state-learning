# Action World v0

CPU-only bridge from Semantic World's parametric world memory to
action-conditioned experiential learning.

The environment is intentionally smaller than `alchemy/`. It isolates the new
scientific question before reconnecting the full system:

> Can memories distilled from experienced state/action/consequence traces
> change an agent's behavior on a related but unseen state, and can those
> memories compose into a longer action chain?

## Environment

Each lifetime has sixteen semantically rendered thresholds. Twelve appear in
the experience stream and four feature combinations are held out for
evaluation. A seed-specific hidden causal law maps four visible threshold
features to the side from which a concealed raider attacks.

The agent can execute:

```text
open
inspect_left
inspect_right
guard_left
guard_right
enter
```

Opening, inspecting, guarding, and entering are real state transitions. An
inspection reveals only the side actually inspected. Entering with the wrong
side guarded ends the episode in failure. This is environment feedback from
an executed action, not a counterfactual verifier.

The lifetime contains temporally shuffled successful cautious crossings and
failed reckless crossings. It is not supplied as an aligned feature table.

## Depth ladder

| Depth | What must transfer | Budget |
|---|---|---:|
| A0 | Remember the danger at a witnessed threshold | 3 |
| A1 | Apply `open -> inspect -> guard -> enter` to an unseen threshold | 4 |
| A2 | Infer the world-specific danger law and skip inspection on an unseen feature combination | 3 |
| A3 | Compose two inferred three-step crossings | 6 |

A1 isolates reusable procedural memory. A2 requires a world model/value guess
to change the action. A3 is the action analogue of Blendyland: several
inferred memories must be composed into one chain.

## CPU controls

- `observed_lookup`: remembers experienced threshold sides, defaults on unseen
  states;
- `generic_cautious`: safe generic procedure, but too expensive for A2/A3;
- `parity_context_oracle`: knows the hidden hypothesis family and infers the
  one consistent law from lived evidence;
- `latent_oracle`: evaluator truth.

The parity solver is a privileged ceiling. It must never gate, steer, or repair
dreamer outputs in the headline condition.

## Commands

```bash
PYTHONPATH=. python3 -m action_world.cli inspect --seed 0
PYTHONPATH=. python3 -m action_world.cli baselines --seed 0
PYTHONPATH=. python3 action_world/test_world.py
PYTHONPATH=. python3 -m action_world.cli generate \
  --seed 0 --output /tmp/action-world-v0-seed0
```

The exporter places ordinary experience and interactive goals under
`model_input/public/`. Hidden laws, danger sides, proof graphs, and CPU
ceilings live only under `evaluator_only/`.

## Integration surface

```python
from action_world import ActionDepth, ActionWorld, WorldConfig

world = ActionWorld(WorldConfig(seed=0))
lifetime = world.sample_lifetime()
goal = world.eval_goals(ActionDepth.A1)[0]
session = world.start(goal)

print(session.intro())
while not session.terminal:
    public_state = session.snapshot()
    action = agent.choose_action(public_state)
    result = session.step(action)
    print(result.observation)
```

The model should receive the public snapshot and consequences only. It must
not receive `world.threat_side`, `_bits_by_threshold`, evaluator artifacts, or
the parity context-oracle.

## Explicit non-claims

This prototype is not yet the final semantic habitat/Alchemy world. Its
feature law is a controlled symbolic diagnostic. It does not yet test:

- a learned dream/think scheduler;
- online LoRA reconsolidation;
- open-ended exploration;
- delayed credit over long horizons;
- natural causal features with graded value;
- recovery after a world-law change.

Those extensions should be added only after the verifier-free depth-growing
memory loop succeeds on Blendyland.
