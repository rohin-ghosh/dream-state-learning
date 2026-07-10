"""
run_baselines.py — Run baseline methods on the 48-task ALFWorld sequential evaluation.

Usage:
    python scripts/run_baselines.py \
        --config configs/base.yaml \
        --baseline naive_ft \
        --ordering blocked \
        --seed 42 \
        --output-dir outputs/baselines/
"""

from __future__ import annotations

import json
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
import yaml

app = typer.Typer(pretty_exceptions_enable=False)


class Baseline(str, Enum):
    naive_ft = "naive_ft"
    frozen_episodic = "frozen_episodic"
    olora_only = "olora_only"
    random_routing = "random_routing"
    no_sleep = "no_sleep"
    ewc = "ewc"
    expel = "expel"


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


def build_agent_config(base: dict, baseline: Baseline) -> dict:
    """
    Overlay baseline-specific overrides onto the base config dict.
    Returns a new config dict with keys consumed by SequentialEvalHarness.
    """
    cfg = {
        # agent
        "lora_enabled": True,
        "orthogonal_penalty": True,
        "routing_policy": "learned",
        "sleep_phase": True,
        # memory tiers
        "episodic_memory": True,
        "semantic_memory": True,
        "parametric_memory": True,
        # regulariser
        "regulariser": "olora",
        # misc
        **base,
    }

    if baseline == Baseline.naive_ft:
        # Sequential LoRA fine-tuning, no orthogonal penalty, no routing
        cfg["orthogonal_penalty"] = False
        cfg["routing_policy"] = "none"
        cfg["sleep_phase"] = False

    elif baseline == Baseline.frozen_episodic:
        # Frozen LLM, episodic memory only, no weight updates
        cfg["lora_enabled"] = False
        cfg["orthogonal_penalty"] = False
        cfg["routing_policy"] = "none"
        cfg["sleep_phase"] = False
        cfg["semantic_memory"] = False
        cfg["parametric_memory"] = False

    elif baseline == Baseline.olora_only:
        # O-LoRA without routing or sleep
        cfg["routing_policy"] = "none"
        cfg["sleep_phase"] = False

    elif baseline == Baseline.random_routing:
        # Dream-State with random routing instead of learned policy
        cfg["routing_policy"] = "random"

    elif baseline == Baseline.no_sleep:
        # Episodic memory only, no sleep-phase consolidation
        cfg["sleep_phase"] = False
        cfg["semantic_memory"] = False

    elif baseline == Baseline.ewc:
        # EWC regularisation (diagonal Fisher) instead of O-LoRA
        cfg["orthogonal_penalty"] = False
        cfg["regulariser"] = "ewc"
        cfg["routing_policy"] = "none"
        cfg["sleep_phase"] = False

    elif baseline == Baseline.expel:
        # ExpeL: experience pool + LLM insight distillation, no weight updates
        cfg["lora_enabled"] = False
        cfg["orthogonal_penalty"] = False
        cfg["routing_policy"] = "none"
        cfg["sleep_phase"] = False
        cfg["regulariser"] = "none"
        cfg["expel_mode"] = True

    return cfg


# ---------------------------------------------------------------------------
# Thin shim around SequentialEvalHarness (imported at runtime so the script
# is importable without a full environment)
# ---------------------------------------------------------------------------

def run_harness(agent_cfg: dict, ordering: Ordering, seed: int) -> dict:
    """
    Import and invoke SequentialEvalHarness.  Returns an EvalResults-like dict.
    Raises ImportError loudly if the project package is not on PYTHONPATH.
    """
    import dataclasses
    try:
        from dream_state.eval.harness import SequentialEvalHarness, EvalConfig, EvalResults
        from dream_state.config import DreamStateConfig, load_config as load_ds_config
        from dream_state.system import DreamStateAgent
    except ImportError as exc:
        raise SystemExit(
            f"[run_baselines] Cannot import dream_state package: {exc}\n"
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
    baseline: Baseline = typer.Option(
        ...,
        "--baseline",
        "-b",
        help="Baseline method to run.",
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
        Path("outputs/baselines"),
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
    """Run a single baseline method on the 48-task ALFWorld sequential evaluation."""

    typer.echo(f"[run_baselines] Loading config: {config}")
    base_cfg = load_config(config)

    typer.echo(f"[run_baselines] Building agent config for baseline: {baseline.value}")
    agent_cfg = build_agent_config(base_cfg, baseline)
    agent_cfg["seed"] = seed

    if dry_run:
        typer.echo("\n--- Resolved agent config (dry-run) ---")
        typer.echo(json.dumps(agent_cfg, indent=2, default=str))
        raise typer.Exit(0)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{baseline.value}_{ordering.value}_seed{seed}.json"

    typer.echo(
        f"[run_baselines] Running SequentialEvalHarness | "
        f"baseline={baseline.value} ordering={ordering.value} seed={seed}"
    )
    t0 = time.perf_counter()
    results = run_harness(agent_cfg, ordering, seed)
    elapsed = time.perf_counter() - t0

    results["meta"] = {
        "baseline": baseline.value,
        "ordering": ordering.value,
        "seed": seed,
        "config_path": str(config),
        "elapsed_seconds": round(elapsed, 2),
    }

    with open(out_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    typer.echo(f"[run_baselines] Results written to: {out_file}")
    typer.echo(f"[run_baselines] Elapsed: {elapsed:.1f}s")

    # Print key metrics
    metrics = results.get("metrics", {})
    if metrics:
        typer.echo("\n--- Metrics ---")
        for k, v in metrics.items():
            typer.echo(f"  {k}: {v}")
    else:
        typer.echo("[run_baselines] No 'metrics' key in results dict.")


if __name__ == "__main__":
    app()
