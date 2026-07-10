"""
run_ablations.py — Run ablation study on the 48-task ALFWorld sequential evaluation.

Usage:
    python scripts/run_ablations.py \
        --config configs/base.yaml \
        --ablation full_system \
        --ordering blocked \
        --seed 42 \
        --output-dir outputs/ablations/
"""

from __future__ import annotations

import json
import time
from enum import Enum
from pathlib import Path

import typer
import yaml

app = typer.Typer(pretty_exceptions_enable=False)


class Ablation(str, Enum):
    no_routing_policy = "no_routing_policy"
    no_orthogonal = "no_orthogonal"
    no_checkpoint_safety = "no_checkpoint_safety"
    no_semantic_memory = "no_semantic_memory"
    no_episodic_memory = "no_episodic_memory"
    full_system = "full_system"


class Ordering(str, Enum):
    blocked = "blocked"
    interleaved = "interleaved"
    random = "random"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_agent_config(base: dict, ablation: Ablation) -> dict:
    """
    Start from the full Dream-State system config and remove/replace the
    component under ablation.  Returns a config dict consumed by SequentialEvalHarness.
    """
    # Full Dream-State system defaults
    cfg = {
        # LoRA / weight updates
        "lora_enabled": True,
        "orthogonal_penalty": True,
        # Routing
        "routing_policy": "learned",
        # Checkpoint safety gate
        "checkpoint_safety": True,
        # Memory tiers
        "episodic_memory": True,
        "semantic_memory": True,
        "parametric_memory": True,
        # Sleep-phase consolidation
        "sleep_phase": True,
        # Regulariser
        "regulariser": "olora",
        # Merge base config on top
        **base,
    }

    if ablation == Ablation.no_routing_policy:
        # Replace learned policy with heuristic router
        cfg["routing_policy"] = "heuristic"

    elif ablation == Ablation.no_orthogonal:
        # Standard LoRA without orthogonal penalty
        cfg["orthogonal_penalty"] = False
        cfg["regulariser"] = "none"

    elif ablation == Ablation.no_checkpoint_safety:
        # Always accept LoRA checkpoints without safety gate
        cfg["checkpoint_safety"] = False

    elif ablation == Ablation.no_semantic_memory:
        # Episodic + parametric only; skip semantic memory tier
        cfg["semantic_memory"] = False

    elif ablation == Ablation.no_episodic_memory:
        # Semantic + parametric only; skip episodic memory tier
        cfg["episodic_memory"] = False

    elif ablation == Ablation.full_system:
        # Complete Dream-State system — no changes from defaults above
        pass

    return cfg


# ---------------------------------------------------------------------------
# Thin shim around SequentialEvalHarness
# ---------------------------------------------------------------------------

def run_harness(agent_cfg: dict, ordering: Ordering, seed: int) -> dict:
    """
    Import and invoke SequentialEvalHarness.  Returns an EvalResults-like dict.
    """
    import dataclasses
    try:
        from dream_state.eval.harness import SequentialEvalHarness, EvalConfig, EvalResults
        from dream_state.config import DreamStateConfig
        from dream_state.system import DreamStateAgent
    except ImportError as exc:
        raise SystemExit(
            f"[run_ablations] Cannot import dream_state package: {exc}\n"
            "Make sure the project root is on PYTHONPATH or install via `pip install -e .`"
        ) from exc

    ds_config = DreamStateConfig()
    ds_config.eval.ordering = ordering.value
    ds_config.eval.seed = seed

    agent = DreamStateAgent(ds_config)
    eval_cfg = EvalConfig(ordering=ordering.value, seed=seed)

    harness = SequentialEvalHarness(
        env_config_path=agent_cfg.get("alfworld_config", "configs/alfworld_base.yaml"),
        agent=agent,
        memory_system=agent.episodic_memory,
        sleep_controller=agent.sleep_controller,
        eval_config=eval_cfg,
    )
    results: EvalResults = harness.run()
    return dataclasses.asdict(results)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@app.command()
def main(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to base YAML config (e.g. configs/base.yaml).",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    ablation: Ablation = typer.Option(
        ...,
        "--ablation",
        "-a",
        help="Ablation condition to run.",
        case_sensitive=False,
    ),
    ordering: Ordering = typer.Option(
        Ordering.blocked,
        "--ordering",
        "-o",
        help="Task ordering strategy for the 48-task sequential eval.",
        case_sensitive=False,
    ),
    seed: int = typer.Option(42, "--seed", "-s", help="Global random seed."),
    output_dir: Path = typer.Option(
        Path("outputs/ablations"),
        "--output-dir",
        "-d",
        help="Directory to write EvalResults JSON files.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print resolved config and exit without running eval.",
    ),
) -> None:
    """Run a single ablation condition on the 48-task ALFWorld sequential evaluation."""

    typer.echo(f"[run_ablations] Loading config: {config}")
    base_cfg = load_config(config)

    typer.echo(f"[run_ablations] Building agent config for ablation: {ablation.value}")
    agent_cfg = build_agent_config(base_cfg, ablation)
    agent_cfg["seed"] = seed

    if dry_run:
        typer.echo("\n--- Resolved agent config (dry-run) ---")
        typer.echo(json.dumps(agent_cfg, indent=2, default=str))
        raise typer.Exit(0)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{ablation.value}_{ordering.value}_seed{seed}.json"

    typer.echo(
        f"[run_ablations] Running SequentialEvalHarness | "
        f"ablation={ablation.value} ordering={ordering.value} seed={seed}"
    )
    t0 = time.perf_counter()
    results = run_harness(agent_cfg, ordering, seed)
    elapsed = time.perf_counter() - t0

    results["meta"] = {
        "ablation": ablation.value,
        "ordering": ordering.value,
        "seed": seed,
        "config_path": str(config),
        "elapsed_seconds": round(elapsed, 2),
    }

    with open(out_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    typer.echo(f"[run_ablations] Results written to: {out_file}")
    typer.echo(f"[run_ablations] Elapsed: {elapsed:.1f}s")

    # Print key metrics
    metrics = results.get("metrics", {})
    if metrics:
        typer.echo("\n--- Metrics ---")
        for k, v in metrics.items():
            typer.echo(f"  {k}: {v}")
    else:
        typer.echo("[run_ablations] No 'metrics' key in results dict.")


if __name__ == "__main__":
    app()
