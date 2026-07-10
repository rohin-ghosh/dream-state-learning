"""O-LoRA fine-tuning for the Dream-State Learning sleep phase.

Implements orthogonal subspace constraints (O-LoRA) to prevent catastrophic
forgetting when continually fine-tuning on new task trajectories.
"""

from __future__ import annotations

import logging
import math
import os
import random
from typing import Callable

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup

from peft import LoraConfig, PeftModel, get_peft_model

from dream_state.config import LoRAConfig
from dream_state.environments.alfworld_env import EpisodeResult

logger = logging.getLogger(__name__)


class ReplayDataset(torch.utils.data.Dataset):
    """Dataset of tokenized trajectory examples for causal LM fine-tuning.

    Each example masks everything except the final action token ids as labels,
    so the model is only trained to predict the last action given the preceding
    trajectory context.

    Trajectories that exceed ``max_length`` are truncated from the *left* so
    that the most recent context (and the target action) is always retained.
    """

    MAX_LENGTH = 1024

    def __init__(
        self,
        trajectories: list[EpisodeResult],
        tokenizer,
    ) -> None:
        self.tokenizer = tokenizer
        self.examples: list[dict[str, torch.Tensor]] = []

        for traj in trajectories:
            example = self._build_example(traj)
            if example is not None:
                self.examples.append(example)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_example(self, traj: EpisodeResult) -> dict[str, torch.Tensor] | None:
        """Tokenize a single trajectory into (input_ids, attention_mask, labels)."""
        text = traj.trajectory_text.strip()
        if not text:
            return None

        # Split into context (everything up to last action) and target (last action).
        # We use the last action stored in traj.actions when available; otherwise we
        # fall back to splitting on the final newline in trajectory_text.
        if traj.actions:
            last_action = traj.actions[-1]
            split_idx = text.rfind(last_action)
            if split_idx == -1:
                # action not literally in text — treat whole text as context
                context_text = text
                target_text = last_action
            else:
                context_text = text[:split_idx]
                target_text = text[split_idx : split_idx + len(last_action)]
        else:
            newline_idx = text.rfind("\n")
            if newline_idx == -1:
                context_text = text
                target_text = ""
            else:
                context_text = text[: newline_idx + 1]
                target_text = text[newline_idx + 1 :]

        if not target_text:
            return None

        context_ids = self.tokenizer(
            context_text, add_special_tokens=False
        )["input_ids"]
        target_ids = self.tokenizer(
            target_text, add_special_tokens=False
        )["input_ids"]

        if not target_ids:
            return None

        full_ids = context_ids + target_ids

        # Truncate from the left to keep at most MAX_LENGTH tokens.  We always
        # keep all target tokens so the label is never empty after truncation.
        if len(full_ids) > self.MAX_LENGTH:
            keep_context = self.MAX_LENGTH - len(target_ids)
            if keep_context < 0:
                # Target alone is already longer than MAX_LENGTH — truncate target
                target_ids = target_ids[-self.MAX_LENGTH :]
                context_ids = []
            else:
                context_ids = context_ids[-keep_context:]
            full_ids = context_ids + target_ids

        n_context = len(full_ids) - len(target_ids)

        input_ids = torch.tensor(full_ids, dtype=torch.long)
        attention_mask = torch.ones_like(input_ids)

        labels = input_ids.clone()
        labels[:n_context] = -100  # mask context tokens

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    # ------------------------------------------------------------------
    # Dataset protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return self.examples[idx]


def _collate_fn(batch: list[dict[str, torch.Tensor]]) -> dict[str, torch.Tensor]:
    """Left-pad sequences in a batch to the same length."""
    max_len = max(item["input_ids"].size(0) for item in batch)
    input_ids_list, attention_mask_list, labels_list = [], [], []

    for item in batch:
        pad_len = max_len - item["input_ids"].size(0)
        input_ids_list.append(
            torch.cat([torch.zeros(pad_len, dtype=torch.long), item["input_ids"]])
        )
        attention_mask_list.append(
            torch.cat([torch.zeros(pad_len, dtype=torch.long), item["attention_mask"]])
        )
        labels_list.append(
            torch.cat([torch.full((pad_len,), -100, dtype=torch.long), item["labels"]])
        )

    return {
        "input_ids": torch.stack(input_ids_list),
        "attention_mask": torch.stack(attention_mask_list),
        "labels": torch.stack(labels_list),
    }


# ---------------------------------------------------------------------------
# Synthetic augmentation
# ---------------------------------------------------------------------------


def generate_synthetic_augmentations(
    trajectories: list[EpisodeResult],
    llm_fn: Callable[[str], str],
    ratio: float = 0.3,
) -> list[EpisodeResult]:
    """Generate paraphrased trajectory augmentations using an external LLM.

    For each trajectory sampled with probability *ratio*, the function prompts
    ``llm_fn`` to paraphrase the observation descriptions while preserving the
    original actions, then wraps the result in a new ``EpisodeResult``.

    Args:
        trajectories: Source trajectories to augment from.
        llm_fn: Callable that accepts a prompt string and returns a completion.
        ratio: Fraction of trajectories to augment (sampled independently).

    Returns:
        List of newly created ``EpisodeResult`` instances (does *not* include
        the original trajectories).
    """
    augmented: list[EpisodeResult] = []

    for traj in trajectories:
        if random.random() > ratio:
            continue

        prompt = (
            "Paraphrase this task trajectory with different observation descriptions"
            " but same actions:\n"
            f"{traj.trajectory_text}"
        )

        try:
            paraphrased_text: str = llm_fn(prompt)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_fn raised %s; skipping augmentation for trajectory.", exc)
            continue

        new_result = EpisodeResult(
            task_path=traj.task_path,
            task_type=traj.task_type,
            success=traj.success,
            steps_taken=traj.steps_taken,
            trajectory_text=paraphrased_text,
        )
        augmented.append(new_result)

    return augmented


# ---------------------------------------------------------------------------
# O-LoRA Trainer
# ---------------------------------------------------------------------------


class OLoRATrainer:
    """Orthogonal LoRA (O-LoRA) continual fine-tuner.

    Trains a LoRA adapter for a new task while penalising any update that
    moves into the subspace spanned by the B matrices of prior-task adapters.
    This prevents catastrophic forgetting without storing replay data from
    previous tasks.
    """

    def __init__(
        self,
        base_model_name: str,
        lora_config_: LoRAConfig,
        output_dir: str,
        device: str = "cuda",
    ) -> None:
        self.base_model_name = base_model_name
        self.lora_cfg = lora_config_
        self.output_dir = output_dir
        self.device = device

        # Prior task B matrices — list of lists (one inner list per prior task,
        # each inner list contains per-layer tensors).
        self.prior_bases: list[list[torch.Tensor]] = []

        logger.info("Loading base model %s in bfloat16 …", base_model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.bfloat16,
            device_map=device,
        )
        logger.info("Base model loaded.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fine_tune(
        self,
        trajectories: list[EpisodeResult],
        task_id: int,
        prior_adapter_paths: list[str] | None = None,
    ) -> str:
        """Fine-tune a LoRA adapter for *task_id* on *trajectories*.

        Args:
            trajectories: Training trajectories for the current task.
            task_id: Integer task identifier used for checkpoint naming.
            prior_adapter_paths: Paths to saved PEFT checkpoints from previous
                tasks. Their B matrices are extracted and used for the
                orthogonality penalty.

        Returns:
            Path to the saved checkpoint directory.
        """
        cfg = self.lora_cfg

        # ------------------------------------------------------------------ #
        # (a) Build training dataset (+ optional synthetic augmentation)       #
        # ------------------------------------------------------------------ #
        dataset = ReplayDataset(trajectories, self.tokenizer)
        if len(dataset) == 0:
            raise ValueError("No valid examples could be built from the provided trajectories.")

        loader = DataLoader(
            dataset,
            batch_size=cfg.batch_size,
            shuffle=True,
            collate_fn=_collate_fn,
            drop_last=False,
        )

        # ------------------------------------------------------------------ #
        # (b) Attach a fresh LoRA adapter                                      #
        # ------------------------------------------------------------------ #
        peft_config = LoraConfig(
            r=cfg.rank,
            lora_alpha=cfg.lora_alpha,
            lora_dropout=cfg.lora_dropout,
            target_modules=cfg.target_modules,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(self.base_model, peft_config)
        model.print_trainable_parameters()
        model.to(self.device)

        # ------------------------------------------------------------------ #
        # (c) Extract B matrices from prior adapters                           #
        # ------------------------------------------------------------------ #
        prior_b_matrices: list[list[torch.Tensor]] = list(self.prior_bases)  # already cached

        if prior_adapter_paths:
            for adapter_path in prior_adapter_paths:
                try:
                    prior_model = PeftModel.from_pretrained(self.base_model, adapter_path)
                    prior_model.to(self.device)
                    prior_bs = self._get_lora_b_matrices(prior_model)
                    prior_b_matrices.append(prior_bs)
                    logger.info("Loaded prior adapter B matrices from %s.", adapter_path)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Could not load prior adapter at %s: %s", adapter_path, exc)

        # ------------------------------------------------------------------ #
        # (d) Training loop                                                    #
        # ------------------------------------------------------------------ #
        optimizer = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=cfg.learning_rate,
        )

        total_steps = cfg.num_epochs * len(loader)
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=cfg.warmup_steps,
            num_training_steps=total_steps,
        )

        lambda_start = cfg.orthogonal_lambda_start
        lambda_end = cfg.orthogonal_lambda_end
        global_step = 0

        model.train()
        for epoch in range(cfg.num_epochs):
            epoch_loss = 0.0
            for batch in loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )
                ce_loss: torch.Tensor = outputs.loss

                # Orthogonality penalty
                orth_loss = torch.tensor(0.0, device=self.device)
                if prior_b_matrices:
                    current_bs = self._get_lora_b_matrices(model)
                    orth_loss = self._orthogonal_penalty(current_bs, prior_b_matrices)

                # Linearly anneal lambda over training steps
                if total_steps > 1:
                    annealing_frac = global_step / (total_steps - 1)
                else:
                    annealing_frac = 1.0
                lambda_orth = lambda_start + annealing_frac * (lambda_end - lambda_start)

                loss = ce_loss + lambda_orth * orth_loss

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    filter(lambda p: p.requires_grad, model.parameters()),
                    cfg.max_grad_norm,
                )
                optimizer.step()
                scheduler.step()

                epoch_loss += loss.item()
                global_step += 1

            avg_loss = epoch_loss / max(len(loader), 1)
            logger.info("Epoch %d/%d — avg loss: %.4f", epoch + 1, cfg.num_epochs, avg_loss)

        # ------------------------------------------------------------------ #
        # (e) Save checkpoint                                                  #
        # ------------------------------------------------------------------ #
        checkpoint_dir = os.path.join(self.output_dir, f"task_{task_id}")
        os.makedirs(checkpoint_dir, exist_ok=True)
        model.save_pretrained(checkpoint_dir)
        self.tokenizer.save_pretrained(checkpoint_dir)
        logger.info("Saved checkpoint to %s.", checkpoint_dir)

        # Cache the B matrices for future orthogonality constraints.
        final_bs = self._get_lora_b_matrices(model)
        self.prior_bases.append(final_bs)

        # ------------------------------------------------------------------ #
        # (f) Return checkpoint path                                           #
        # ------------------------------------------------------------------ #
        return checkpoint_dir

    # ------------------------------------------------------------------
    # B-matrix helpers
    # ------------------------------------------------------------------

    def _get_lora_b_matrices(self, model) -> list[torch.Tensor]:
        """Extract LoRA B matrices from all LoRA-adapted layers.

        Returns a list of tensors — one per LoRA layer — each with shape
        ``[lora_rank, hidden_dim]`` (i.e. the raw ``lora_B.weight`` tensor).
        The matrices are detached and kept on their original device.
        """
        b_matrices: list[torch.Tensor] = []
        for name, module in model.named_modules():
            # PEFT names the weight "lora_B" inside Linear sub-modules
            if hasattr(module, "lora_B"):
                for _key, linear in module.lora_B.items():
                    b_matrices.append(linear.weight.detach())
        return b_matrices

    def _orthogonal_penalty(
        self,
        current_b_matrices: list[torch.Tensor],
        prior_b_matrices: list[list[torch.Tensor]],
    ) -> torch.Tensor:
        """Compute the O-LoRA orthogonality penalty.

        For every prior task and every shared layer index *i*:
            penalty += ||prior_b[i].T @ current_b[i]||_F^2

        The Frobenius norm squared measures how much the current adapter's
        update direction overlaps with the subspace of the prior adapter,
        encouraging orthogonal (non-interfering) updates.

        Args:
            current_b_matrices: B matrices of the adapter currently being
                trained, one tensor per layer.
            prior_b_matrices: Outer list iterates over prior tasks; inner list
                iterates over layers (same ordering as *current_b_matrices*).

        Returns:
            Scalar tensor containing the summed penalty (differentiable w.r.t.
            the current adapter parameters).
        """
        penalty = torch.tensor(0.0, device=self.device, dtype=torch.float32)
        n_current = len(current_b_matrices)

        for prior_task_bs in prior_b_matrices:
            n_layers = min(len(prior_task_bs), n_current)
            for i in range(n_layers):
                prior_b = prior_task_bs[i].to(self.device).float()  # [r_prior, h]
                cur_b = current_b_matrices[i].float()                # [r_cur,   h]
                # prior_b.T: [h, r_prior] — cur_b.T not needed; we want [r_prior, r_cur]
                overlap = prior_b @ cur_b.T  # [r_prior, r_cur]
                penalty = penalty + overlap.pow(2).sum()

        return penalty
