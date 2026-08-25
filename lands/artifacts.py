"""Deterministic, evaluator-separated artifact export."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from .model import SCHEMA_VERSION
from .claims import CANONICAL_GRAMMAR
from .corpus import build_atomic_corpus
from .skins import all_skin_names
from .solver import evaluate_world
from .world import SemanticWorld


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _jsonl(rows) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def _source_state() -> tuple[str | None, bool | None]:
    root = Path(__file__).resolve().parents[1]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return commit, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_world(world: SemanticWorld, output_dir: str | Path) -> Path:
    """Export one immutable dataset directory.

    Refuses a non-empty destination so a run cannot silently overwrite a
    previous artifact.  Ordinary model-facing files never include latent IDs,
    answers, depth labels, or oracle material.  Privileged model conditions
    are isolated under `model_input/oracle/`; evaluator-owned material is
    isolated under `evaluator_only/`.
    """
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty {output}")
    output.mkdir(parents=True, exist_ok=True)

    lifetime = world.sample_lifetime()
    goals = world.eval_goals()
    for skin_name in all_skin_names():
        public_dir = output / "model_input" / "public" / skin_name
        oracle_dir = output / "model_input" / "oracle" / skin_name
        public_dir.mkdir(parents=True, exist_ok=True)
        oracle_dir.mkdir(parents=True, exist_ok=True)
        rendered = world.render(skin_name)
        by_observation = {record.observation_id: record for record in rendered.observations}
        rows = []
        for episode in lifetime.episodes:
            rows.append(
                {
                    "episode_id": episode.id,
                    "observations": [
                        {
                            "observation_id": observation.id,
                            "text": by_observation[observation.id].text,
                        }
                        for observation in episode.observations
                    ],
                }
            )
        (public_dir / "lifetime.jsonl").write_text(_jsonl(rows))
        rendered_goals = {goal.goal_id: goal for goal in rendered.goals}
        (public_dir / "goals.jsonl").write_text(
            _jsonl(
                {
                    "goal_id": goal.id,
                    "question": rendered_goals[goal.id].question,
                }
                for goal in goals
            )
        )
        (public_dir / "claim_grammar.txt").write_text(
            "\n".join(CANONICAL_GRAMMAR) + "\n"
        )
        (public_dir / "reachout_policy.json").write_text(
            _json(world.start_reachout(skin_name).policy())
        )
        (oracle_dir / "oracle_memories.json").write_text(
            _json({"memories": list(world.oracle_structure(skin_name))})
        )
        (oracle_dir / "atomic_memories.jsonl").write_text(
            _jsonl(
                {
                    "goal_id": goal.id,
                    "depth": goal.depth.value,
                    "unresolved": [
                        memory.to_dict()
                        for memory in world.atomic_memories_for(goal, skin_name)
                    ],
                    "resolved": [
                        memory.to_dict()
                        for memory in world.atomic_memories_for(
                            goal, skin_name, resolved=True
                        )
                    ],
                }
                for goal in goals
            )
        )
        (oracle_dir / "context_oracle.jsonl").write_text(
            _jsonl(
                {
                    "goal_id": goal.id,
                    "depth": goal.depth.value,
                    "unresolved_prompt": world.context_oracle(goal, skin_name),
                    "resolved_prompt": world.context_oracle(
                        goal, skin_name, resolved=True
                    ),
                }
                for goal in goals
            )
        )
        (oracle_dir / "oracle_atomic_corpus.json").write_text(
            _json(build_atomic_corpus(world, skin_name).to_dict())
        )

    evaluator = output / "evaluator_only"
    evaluator.mkdir(parents=True, exist_ok=True)
    (evaluator / "latent_world.json").write_text(
        _json(
            {
                "schema_version": SCHEMA_VERSION,
                "config": world.config.to_dict(),
                "oracle_memory": world.oracle_memory(),
                "observations": [
                    observation.to_dict() for observation in lifetime.observations
                ],
                "goals": [goal.to_dict(include_answer=True) for goal in goals],
                "proofs": [world.proof_for(goal).to_dict() for goal in goals],
            }
        )
    )
    answers = {}
    for skin_name in all_skin_names():
        rendered = world.render(skin_name, include_answers=True)
        answers[skin_name] = {
            goal.goal_id: goal.answer for goal in rendered.goals
        }
    (evaluator / "answers.json").write_text(_json(answers))
    (evaluator / "cpu_baselines.json").write_text(_json(evaluate_world(world)))

    files = sorted(path for path in output.rglob("*") if path.is_file())
    source_commit, source_dirty = _source_state()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        **world.manifest_summary(),
        "source_commit": source_commit,
        "source_dirty": source_dirty,
        "files": {
            str(path.relative_to(output)): {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
            for path in files
        },
    }
    (output / "manifest.json").write_text(_json(manifest))
    return output
