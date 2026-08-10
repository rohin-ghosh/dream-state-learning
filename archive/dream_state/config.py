"""Pydantic v2 configuration system for Dream-State Learning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    device: str = "cuda"
    dtype: str = "bfloat16"
    max_new_tokens: int = 256
    temperature: float = 0.0


class MemoryConfig(BaseModel):
    episodic_capacity: int = 2000
    episodic_embed_dim: int = 768
    episodic_embed_model: str = "sentence-transformers/all-mpnet-base-v2"
    semantic_db_path: str = "semantic_memory.db"
    retrieval_k: int = 3
    recency_decay: float = 0.99


class LoRAConfig(BaseModel):
    rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list[str] = Field(
        default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"]
    )
    learning_rate: float = 1e-4
    num_epochs: int = 3
    batch_size: int = 4
    orthogonal_lambda_start: float = 0.1
    orthogonal_lambda_end: float = 1.0
    max_grad_norm: float = 1.0
    warmup_steps: int = 10
    revert_threshold_bwt: float = -0.03  # revert if BWT drops more than 3pp


class RoutingConfig(BaseModel):
    hidden_dims: list[int] = Field(default_factory=lambda: [128, 64, 32])
    n_classes: int = 4  # EPISODIC, SEMANTIC, PARAMETRIC, NONE
    meta_lr: float = 3e-4
    meta_batch_size: int = 8  # task sequences per meta-batch
    inner_steps: int = 5
    entropy_coeff: float = 0.01
    interference_proj_dim: int = 64  # random projection dim for interference risk


class SleepConfig(BaseModel):
    trigger_every_k_tasks: int = 4
    synthetic_augmentation_ratio: float = 0.3  # fraction synthetic vs. replay
    min_trajectories_for_lora: int = 8
    holdout_per_type: int = 5


class EvalConfig(BaseModel):
    n_per_type: int = 8
    ordering: str = "blocked"
    seed: int = 42
    max_steps_per_task: int = 50


class DreamStateConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    lora: LoRAConfig = Field(default_factory=LoRAConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    sleep: SleepConfig = Field(default_factory=SleepConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)
    output_dir: str = "outputs"
    wandb_project: str = "dream-state"
    wandb_run_name: str = ""


def load_config(path: str) -> DreamStateConfig:
    """Load a DreamStateConfig from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A fully-validated DreamStateConfig instance.
    """
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
    return DreamStateConfig.model_validate(raw)


def save_config(config: DreamStateConfig, path: str) -> None:
    """Serialize a DreamStateConfig to a YAML file.

    Args:
        config: The configuration object to save.
        path: Destination file path.
    """
    data = config.model_dump()
    Path(path).write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
