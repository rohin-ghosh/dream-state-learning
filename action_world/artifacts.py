"""Evaluator-separated export for Action World v0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .model import LEGAL_ACTIONS, SCHEMA_VERSION
from .solver import evaluate_world
from .world import ActionWorld


def _json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _jsonl(rows) -> str:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_world(world: ActionWorld, output_dir: str | Path) -> Path:
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty {output}")
    public = output / "model_input" / "public"
    evaluator = output / "evaluator_only"
    public.mkdir(parents=True, exist_ok=True)
    evaluator.mkdir(parents=True, exist_ok=True)

    (public / "lifetime.jsonl").write_text(
        _jsonl(episode.public_dict() for episode in world.sample_lifetime().episodes)
    )
    (public / "goals.jsonl").write_text(
        _jsonl(goal.public_dict() for goal in world.eval_goals())
    )
    (public / "thresholds.jsonl").write_text(
        _jsonl(threshold.public_dict() for threshold in world.thresholds.values())
    )
    (public / "action_interface.json").write_text(
        _json(
            {
                "legal_actions": list(LEGAL_ACTIONS),
                "feedback": "consequences of executed actions only",
                "counterfactual_queries": 0,
            }
        )
    )

    (evaluator / "latent_world.json").write_text(_json(world.evaluator_bundle()))
    (evaluator / "cpu_baselines.json").write_text(_json(evaluate_world(world)))

    files = sorted(path for path in output.rglob("*") if path.is_file())
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "world_fingerprint": world.world_fingerprint(),
        "files": {
            str(path.relative_to(output)): _sha256(path) for path in files
        },
    }
    (output / "manifest.json").write_text(_json(manifest))
    return output
