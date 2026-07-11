"""
Generate synthetic dependency-graph tasks for Dream-State Learning.

Each task is a small physical scene with objects that have dependency relationships.
The agent must manipulate objects in the correct order — violating a dependency fails the task.

Task types:
  - blocking: object A sits on object B, must move A before B
  - paired:   object A belongs with object B, must place together
  - sequential: must open container before accessing contents
  - location:   object was seen at location X, moved — agent must remember where

Output: data/dependency_tasks/tasks.json
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Scene vocabulary
# ---------------------------------------------------------------------------

OBJECTS = [
    "red cup", "blue cup", "green mug", "white mug",
    "ceramic bowl", "glass bowl",
    "book", "notebook", "folder",
    "pen", "pencil", "marker",
    "phone", "tablet", "remote",
]

CONTAINERS = [
    "coaster", "tray", "shelf", "drawer", "box", "basket",
]

LOCATIONS = [
    "desk", "table", "counter", "windowsill", "chair", "floor",
]

COLORS = ["red", "blue", "green", "white", "black", "yellow"]

DEPENDENCY_TYPES = ["blocking", "paired", "sequential", "location_memory"]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DependencyEdge:
    dep_type: str          # blocking | paired | sequential | location_memory
    source: str            # object that must be handled first
    target: str            # object that is blocked / paired / contained
    description: str       # natural language description of the dependency


@dataclass
class Task:
    task_id: str
    complexity: int                        # number of dependency edges (1–4)
    goal: str                              # natural language goal
    scene_description: str                 # initial scene state
    dependencies: list[DependencyEdge]     # ground truth dependency graph
    critical_details: list[str]            # details that MATTER (dependencies)
    noise_details: list[str]               # details that DON'T matter (color etc)
    optimal_action_sequence: list[str]     # correct sequence
    distractors: list[str]                 # wrong actions that violate dependencies
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def make_blocking_task(rng: random.Random, complexity: int, task_id: str) -> Task:
    """Object A sits on object B — must move A before grabbing B."""
    obj = rng.choice(OBJECTS)
    container = rng.choice(CONTAINERS)
    location = rng.choice(LOCATIONS)
    color = rng.choice(COLORS)
    target_location = rng.choice([l for l in LOCATIONS if l != location])

    # Add extra objects for higher complexity
    extra_pairs = []
    for i in range(complexity - 1):
        extra_obj = rng.choice([o for o in OBJECTS if o != obj])
        extra_cont = rng.choice([c for c in CONTAINERS if c != container])
        extra_pairs.append((extra_obj, extra_cont))

    # Build scene
    scene_parts = [f"There is a {color} {obj} sitting on a {container} on the {location}."]
    for eo, ec in extra_pairs:
        ec_loc = rng.choice(LOCATIONS)
        scene_parts.append(f"There is a {rng.choice(COLORS)} {eo} on a {ec} on the {ec_loc}.")

    scene = " ".join(scene_parts)
    goal = f"Move the {container} to the {target_location}."

    deps = [DependencyEdge(
        dep_type="blocking",
        source=obj,
        target=container,
        description=f"The {obj} is on the {container} — must move {obj} first"
    )]
    for eo, ec in extra_pairs:
        deps.append(DependencyEdge(
            dep_type="blocking",
            source=eo,
            target=ec,
            description=f"The {eo} is on the {ec} — must move {eo} before {ec}"
        ))

    actions = [f"pick up {obj}", f"place {obj} on {location}", f"pick up {container}", f"place {container} on {target_location}"]
    for eo, ec in extra_pairs:
        actions = [f"pick up {eo}", f"place {eo} aside"] + actions

    return Task(
        task_id=task_id,
        complexity=complexity,
        goal=goal,
        scene_description=scene,
        dependencies=deps,
        critical_details=[f"{obj} is on {container}", f"must move {obj} before {container}"],
        noise_details=[f"{obj} is {color}", f"{container} is on the {location}"],
        optimal_action_sequence=actions,
        distractors=[f"pick up {container}", f"move {container} directly"],
        metadata={"type": "blocking", "obj": obj, "container": container}
    )


def make_paired_task(rng: random.Random, complexity: int, task_id: str) -> Task:
    """Object A and B must be placed together — placing one without the other fails."""
    pairs = [
        ("lid", "pot"), ("cap", "bottle"), ("cover", "tray"),
        ("charger", "phone"), ("case", "tablet"), ("sleeve", "book"),
    ]
    chosen = rng.sample(pairs, min(complexity, len(pairs)))
    location = rng.choice(LOCATIONS)
    target = rng.choice([l for l in LOCATIONS if l != location])

    scene_parts = []
    for a, b in chosen:
        col_a, col_b = rng.choice(COLORS), rng.choice(COLORS)
        scene_parts.append(f"There is a {col_a} {a} near a {col_b} {b} on the {location}.")

    scene = " ".join(scene_parts)
    a0, b0 = chosen[0]
    goal = f"Move the {b0} (with its {a0}) to the {target}."

    deps = [DependencyEdge(
        dep_type="paired",
        source=a,
        target=b,
        description=f"The {a} must accompany the {b}"
    ) for a, b in chosen]

    actions = []
    for a, b in chosen:
        actions += [f"pick up {a}", f"pick up {b}", f"place {b} with {a} on {target}"]

    return Task(
        task_id=task_id,
        complexity=complexity,
        goal=goal,
        scene_description=scene,
        dependencies=deps,
        critical_details=[f"{a} belongs with {b}" for a, b in chosen],
        noise_details=[f"{a} color", f"{b} color", f"exact position on {location}"],
        optimal_action_sequence=actions,
        distractors=[f"move {b0} alone to {target}", f"leave {a0} behind"],
        metadata={"type": "paired", "pairs": chosen}
    )


def make_sequential_task(rng: random.Random, complexity: int, task_id: str) -> Task:
    """Must open container before accessing contents — chain of length complexity."""
    containers_seq = ["cabinet", "drawer", "box", "safe", "locker"]
    chosen = rng.sample(containers_seq, min(complexity + 1, len(containers_seq)))
    obj = rng.choice(OBJECTS)
    color = rng.choice(COLORS)
    target = rng.choice(LOCATIONS)

    # Nested: obj is in chosen[-1], which is in chosen[-2], etc.
    scene_parts = [f"There is a {color} {obj} inside a {chosen[-1]}."]
    for i in range(len(chosen) - 1, 0, -1):
        scene_parts.append(f"The {chosen[i]} is inside the {chosen[i-1]}.")
    scene_parts.append(f"The {chosen[0]} is closed.")
    scene = " ".join(scene_parts)

    goal = f"Retrieve the {obj} and place it on the {target}."

    deps = []
    for i in range(len(chosen) - 1):
        deps.append(DependencyEdge(
            dep_type="sequential",
            source=chosen[i],
            target=chosen[i+1],
            description=f"Must open {chosen[i]} before accessing {chosen[i+1]}"
        ))
    deps.append(DependencyEdge(
        dep_type="sequential",
        source=chosen[-1],
        target=obj,
        description=f"Must open {chosen[-1]} to access {obj}"
    ))

    actions = []
    for c in chosen:
        actions.append(f"open {c}")
    actions += [f"pick up {obj}", f"place {obj} on {target}"]

    return Task(
        task_id=task_id,
        complexity=complexity,
        goal=goal,
        scene_description=scene,
        dependencies=deps,
        critical_details=[f"{chosen[i]} contains {chosen[i+1]}" for i in range(len(chosen)-1)],
        noise_details=[f"{obj} is {color}", "exact container positions"],
        optimal_action_sequence=actions,
        distractors=[f"pick up {obj} directly", f"open {chosen[-1]} first without opening {chosen[0]}"],
        metadata={"type": "sequential", "chain": chosen, "obj": obj}
    )


def make_location_memory_task(rng: random.Random, complexity: int, task_id: str) -> Task:
    """Object was seen at location X, then moved — agent must remember original location."""
    obj = rng.choice(OBJECTS)
    color = rng.choice(COLORS)
    original_loc = rng.choice(LOCATIONS)
    current_loc = rng.choice([l for l in LOCATIONS if l != original_loc])
    target = rng.choice([l for l in LOCATIONS if l not in [original_loc, current_loc]])

    # Extra objects as distractors for higher complexity
    extra = []
    for _ in range(complexity - 1):
        extra.append((rng.choice(OBJECTS), rng.choice(LOCATIONS)))

    scene = (
        f"Earlier you saw a {color} {obj} on the {original_loc}. "
        f"It has since been moved. You can see it is no longer there. "
    )
    for eo, el in extra:
        scene += f"There is a {rng.choice(COLORS)} {eo} on the {el}. "

    goal = f"Find the {obj} and return it to the {original_loc}, then move it to the {target}."

    deps = [DependencyEdge(
        dep_type="location_memory",
        source=original_loc,
        target=obj,
        description=f"{obj} was originally at {original_loc} — agent must remember this"
    )]

    actions = [
        f"search {current_loc} for {obj}",
        f"pick up {obj}",
        f"place {obj} on {original_loc}",
        f"pick up {obj}",
        f"place {obj} on {target}",
    ]

    return Task(
        task_id=task_id,
        complexity=complexity,
        goal=goal,
        scene_description=scene,
        dependencies=deps,
        critical_details=[f"{obj} was originally at {original_loc}"],
        noise_details=[f"{obj} is {color}", f"other objects present"],
        optimal_action_sequence=actions,
        distractors=[f"search {target} first", f"ignore original location"],
        metadata={"type": "location_memory", "obj": obj, "original": original_loc, "current": current_loc}
    )


GENERATORS = {
    "blocking": make_blocking_task,
    "paired": make_paired_task,
    "sequential": make_sequential_task,
    "location_memory": make_location_memory_task,
}


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------

def build_dataset(
    n_per_type: int = 20,
    complexities: list[int] = [1, 2, 3],
    seed: int = 42,
) -> list[Task]:
    rng = random.Random(seed)
    tasks = []
    task_idx = 0

    for dep_type, gen_fn in GENERATORS.items():
        for complexity in complexities:
            count = n_per_type // len(complexities)
            for _ in range(count):
                task_id = f"{dep_type}_c{complexity}_{task_idx:04d}"
                task = gen_fn(rng, complexity, task_id)
                tasks.append(task)
                task_idx += 1

    rng.shuffle(tasks)
    return tasks


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-per-type", type=int, default=30, help="Tasks per dependency type per complexity level")
    parser.add_argument("--complexities", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="data/dependency_tasks/tasks.json")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating dataset: {args.n_per_type} tasks/type/complexity, complexities={args.complexities}")
    tasks = build_dataset(args.n_per_type, args.complexities, args.seed)

    serialized = [asdict(t) for t in tasks]
    with open(out_path, "w") as f:
        json.dump(serialized, f, indent=2)

    print(f"Generated {len(tasks)} tasks → {out_path}")

    # Print summary
    by_type: dict[str, int] = {}
    by_complexity: dict[int, int] = {}
    for t in tasks:
        dep_type = t.metadata.get("type", "unknown")
        by_type[dep_type] = by_type.get(dep_type, 0) + 1
        by_complexity[t.complexity] = by_complexity.get(t.complexity, 0) + 1

    print("\nBy type:")
    for k, v in sorted(by_type.items()):
        print(f"  {k}: {v}")
    print("By complexity:")
    for k, v in sorted(by_complexity.items()):
        print(f"  complexity={k}: {v}")


if __name__ == "__main__":
    main()
