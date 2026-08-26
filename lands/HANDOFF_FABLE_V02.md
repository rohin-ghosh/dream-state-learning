# Semantic World v0.2 — Fable handoff

Branch: `semantic-world-v02`

This branch adds a CPU-only replacement for the invalid v0 D3 mechanic. It
does not modify the frozen v0 implementation or any completed D0-D2 result.

## Accept it

```bash
PYTHONPATH=. python3 lands/test_v02.py
PYTHONPATH=. python3 lands/test_world.py
python3 -m compileall -q lands
git diff --check
```

The first command includes a 1,000-seed joint-identifiability sweep and should
finish in roughly ten seconds on CPU. Inspect one aligned lifetime with:

```bash
PYTHONPATH=. python3 -m lands.v02 render --seed 0 --skin aligned
```

## What changed scientifically

V0 D3 had two shortcuts: its meta signature copied an ordinary land in every
seed, and its three target anchors exposed one answer for every animal role.
The new diagnostic uses ratio-preserving pigment mixtures, known-parent demo
lands, and three target lands that each withhold the queried role. The target
operator and parents are jointly identifiable, while ordinary copying and
same-role lookup are impossible.

Canonical details and the experiment ladder are in
`research_notes/37_semantic_world_v02_spec.md`.

## Stable CPU interface

```python
from lands.model import WorldConfig
from lands.v02 import SemanticWorldV02

world = SemanticWorldV02(WorldConfig(seed=0))
public_lifetime = world.render_lifetime("aligned")
public_goals = world.render_goals("aligned")
offline_report = world.identifiability_report()
```

`offline_report` is evaluator-only. Never place its operator survivors,
parent candidates, hidden roles, or answers in model context.

## First model contact

Before wiring the dreamer, run a clean-model gameability gate over the full
public lifetime. Then add an oracle atomic-memory ceiling. The first learned
condition should reuse C3e's epistemic-state loop but emit two new memory
kinds:

```text
BLEND_OPERATOR | operator=PIGMENT_SUM
BLEND_PARENTS | land=<target> | parents=<land>,<land>,<land>
```

The model self-check may retrieve source observations, public feed relations,
and its own provisional memories. The exact CPU audit is an offline scorer
only. Preserve raw dream text, proposal depth/parents, self-check verdicts,
and the evidence IDs used for every decision.

Do not immediately train LoRAs. First establish that:

1. the clean model can solve the game with all evidence in context;
2. an oracle atomic read plan reaches a high composition ceiling; and
3. graph-free recurrent dreaming proposes the operator and exact parent sets.

Once those pass, compare context+recognition against LoRA+recognition using the
same corpus and query plan. The just-completed v0 result says these should be
equal at 65 lines; v0.2 becomes useful for weights only when the memory horizon
is swept past the available prompt budget.

