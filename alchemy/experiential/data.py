"""Public-outcome environment and provenance-preserving offline consolidation.

Rules are private to the environment. The learner observes final states, never
rule tables, intermediate oracle states, or answers to held-out tasks.
"""

from __future__ import annotations

import hashlib
import itertools
import random
from collections import defaultdict
from dataclasses import asdict, dataclass

import torch


@dataclass(frozen=True)
class Task:
    initial: int
    operations: tuple[int, ...]

    @property
    def key(self):
        return f"{self.initial}:" + ",".join(map(str, self.operations))

    @property
    def prompt(self):
        names = ("dax", "wug", "zup")
        return f"State: {self.initial}. Apply: {' '.join(names[i] for i in self.operations)}.\nAnswer:"


class HiddenRuleWorld:
    def __init__(self, seed=0, states=5):
        if not 2 <= states <= 9:
            raise ValueError("states must be between 2 and 9")
        self.states = states
        rng = random.Random(seed)
        self._rules = []
        for _ in range(3):
            rule = list(range(states))
            rng.shuffle(rule)
            self._rules.append(rule)

    def observe(self, task: Task, action: str):
        state = task.initial
        for op in task.operations:
            state = self._rules[op][state]
        return {
            "final_state": str(state),
            "reward": float(action.strip() == str(state)),
        }

    def split(self, seed=0):
        # Entire ordered operation pairs are absent from experience. All triples
        # and quadruples are unseen compositions, not random row holdouts.
        held_pairs = {(0, 1), (1, 2), (2, 0)}
        train, transfer = [], []
        for depth in (1, 2, 3, 4):
            for ops in itertools.product(range(3), repeat=depth):
                for initial in range(self.states):
                    task = Task(initial, ops)
                    if depth == 1 or (depth == 2 and ops not in held_pairs):
                        train.append(task)
                    else:
                        transfer.append(task)
        random.Random(seed).shuffle(train)
        random.Random(seed + 1).shuffle(transfer)
        assert not {t.key for t in train} & {t.key for t in transfer}
        return train, transfer


class Codec:
    """ASCII smoke codec or a real HF tokenizer; train only answer tokens."""

    def __init__(self, tokenizer=None):
        self.tokenizer = tokenizer

    def encode(self, text):
        if self.tokenizer is None:
            return [ord(c) for c in text]
        return self.tokenizer.encode(text, add_special_tokens=False)

    def example(self, prompt, target, device):
        prefix, suffix = self.encode(prompt), self.encode(target)
        if not prefix or not suffix:
            raise ValueError("Prompt and target must have tokens")
        ids = torch.tensor([prefix + suffix], dtype=torch.long, device=device)
        labels = ids.clone()
        labels[:, : len(prefix)] = -100
        return ids, labels

    def prompt(self, text, device):
        return torch.tensor([self.encode(text)], dtype=torch.long, device=device)

    def decode(self, ids):
        if self.tokenizer is None:
            return "".join(chr(i) for i in ids if 32 <= i < 127)
        return self.tokenizer.decode(ids, skip_special_tokens=True)


@dataclass
class Episode:
    episode_id: str
    task_key: str
    prompt: str
    action: str
    observation: str
    reward: float
    version: int
    loops: int
    hidden_summaries: list[dict]
    routing: dict[int, list]  # [T, tokens, experts], prompt only

    def record(self):
        return asdict(self)


@dataclass
class Example:
    prompt: str
    target: str
    eligibility: dict[int, list[int]]
    source_ids: list[str]
    weight: float = 1.0


def eligibility_from_routes(routes, threshold=0.1, max_experts=2):
    if not 0 <= threshold < 1 or max_experts < 1:
        raise ValueError("Invalid eligibility configuration")
    masks = {}
    for layer, trace in routes.items():
        # Normalize by actual token/pass exposure; unselected experts have zero
        # eligibility, and longer episodes do not automatically update more.
        q = torch.as_tensor(trace).float().mean(dim=(0, 1))
        ranked = torch.argsort(q, descending=True).tolist()
        masks[int(layer)] = [e for e in ranked if q[e] > threshold][:max_experts]
    return masks


def consolidate(episodes, threshold=0.1, max_experts=2, min_support=2):
    groups = defaultdict(list)
    for episode in episodes:
        groups[episode.task_key].append(episode)
    examples = []
    rejected = {
        "insufficient_support": 0,
        "conflicting_outcome": 0,
        "no_eligible_pathway": 0,
    }
    for rows in groups.values():
        # Count independent interaction IDs, not duplicated buffer entries.
        rows = list({r.episode_id: r for r in rows}.values())
        if len(rows) < min_support:
            rejected["insufficient_support"] += 1
            continue
        if len({r.observation for r in rows}) != 1:
            rejected["conflicting_outcome"] += 1
            continue
        # Same prompt/tokenization and loop depth within an arm's collection.
        routes = {
            l: torch.stack([torch.tensor(r.routing[l]) for r in rows]).mean(0)
            for l in rows[0].routing
        }
        mask = eligibility_from_routes(routes, threshold, max_experts)
        if not any(mask.values()):
            rejected["no_eligible_pathway"] += 1
            continue
        failures = sum(r.reward == 0 for r in rows)
        recovered = any(
            a.reward == 0 and b.reward == 1 for a, b in itertools.pairwise(rows)
        )
        examples.append(
            Example(
                rows[0].prompt,
                rows[0].observation,
                mask,
                [r.episode_id for r in rows],
                1 + failures / len(rows) + 0.5 * recovered,
            )
        )
    return examples, rejected


def retention_examples(states):
    return [Example(f"Copy: {i}.\nAnswer:", str(i), {}, []) for i in range(states)]


def episode_id(arm, version, task, repeat):
    return hashlib.sha256(f"{arm}:{version}:{task.key}:{repeat}".encode()).hexdigest()[
        :20
    ]
