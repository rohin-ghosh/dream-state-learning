from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import alfworld.agents.environment as alfworld_env_module
import yaml


TASK_TYPES = ["pick", "clean", "heat", "cool", "look", "pick2"]

EASY_TO_HARD_ORDER = ["pick", "look", "clean", "heat", "cool", "pick2"]

_GAMEFILE_TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"pick_two_obj", "pick2"),
    (r"pick_clean_then_place", "clean"),
    (r"pick_heat_then_place", "heat"),
    (r"pick_cool_then_place", "cool"),
    (r"look_at_obj", "look"),
    (r"pick_and_place", "pick"),
]


def infer_task_type(gamefile_path: str) -> str:
    lower = gamefile_path.lower()
    for pattern, task_type in _GAMEFILE_TYPE_PATTERNS:
        if re.search(pattern, lower):
            return task_type
    return "unknown"


@dataclass
class EpisodeResult:
    task_path: str
    task_type: str
    success: bool
    steps_taken: int
    observations: list[str] = field(default_factory=list)
    thoughts: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    rewards: list[float] = field(default_factory=list)
    total_reward: float = 0.0
    trajectory_text: str = ""


class ALFWorldEnv:
    def __init__(
        self,
        config_path: str,
        split: str = "eval_out_of_distribution",
        max_steps: int = 50,
    ) -> None:
        self.config_path = config_path
        self.split = split
        self.max_steps = max_steps
        self._step_count: int = 0
        self._current_info: dict[str, Any] = {}

        with open(config_path) as f:
            config = yaml.safe_load(f)

        config["env"]["type"] = "AlfredTWEnv"
        config["dataset"]["data_path"] = config["dataset"].get("data_path", "data/alfred/json_2.1.1")

        self._env = alfworld_env_module.AlfredTWEnv(config, train_eval=split)
        self._env.seed(42)

    def reset(self) -> tuple[str, dict]:
        obs, info = self._env.reset()
        self._step_count = 0
        self._current_info = info
        if isinstance(obs, list):
            obs = obs[0]
        return obs, info

    def step(self, action: str) -> tuple[str, float, bool, dict]:
        self._step_count += 1
        obs, scores, dones, info = self._env.step([action])
        obs = obs[0] if isinstance(obs, list) else obs
        reward = float(scores[0]) if isinstance(scores, (list, tuple)) else float(scores)
        done = bool(dones[0]) if isinstance(dones, (list, tuple)) else bool(dones)
        self._current_info = info

        if self._step_count >= self.max_steps:
            done = True

        return obs, reward, done, info

    def get_task_type(self) -> str:
        gamefile = self._current_info.get("extra.gamefile", [""])[0]
        if isinstance(gamefile, list):
            gamefile = gamefile[0]
        return infer_task_type(str(gamefile))

    def get_all_tasks(self) -> list[str]:
        game_files = self._env.game_files
        return [str(p) for p in game_files]

    def close(self) -> None:
        try:
            self._env.close()
        except Exception:
            pass


def build_48_task_curriculum(
    all_tasks: list[str],
    ordering: str = "blocked",
    n_per_type: int = 8,
    seed: int = 42,
) -> list[str]:
    rng = random.Random(seed)

    by_type: dict[str, list[str]] = {t: [] for t in TASK_TYPES}
    for path in all_tasks:
        task_type = infer_task_type(path)
        if task_type in by_type:
            by_type[task_type].append(path)

    selected: dict[str, list[str]] = {}
    for task_type in TASK_TYPES:
        candidates = sorted(by_type[task_type])
        rng.shuffle(candidates)
        selected[task_type] = candidates[:n_per_type]

    if ordering == "blocked":
        result: list[str] = []
        for task_type in TASK_TYPES:
            result.extend(selected[task_type])
        return result

    if ordering == "interleaved":
        result = []
        for i in range(n_per_type):
            for task_type in TASK_TYPES:
                if i < len(selected[task_type]):
                    result.append(selected[task_type][i])
        return result

    if ordering == "easy_to_hard":
        result = []
        for task_type in EASY_TO_HARD_ORDER:
            result.extend(selected[task_type])
        return result

    if ordering == "random":
        flat = [path for task_type in TASK_TYPES for path in selected[task_type]]
        rng.shuffle(flat)
        return flat

    raise ValueError(f"Unknown ordering: {ordering!r}. Choose from blocked, interleaved, easy_to_hard, random.")
