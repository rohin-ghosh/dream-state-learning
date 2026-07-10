"""
ReAct agent for the Dream-State Learning continual agent system.

Interacts with ALFWorld using a frozen Qwen2.5-7B-Instruct backbone
with active LoRA adapters. Context is composed from working memory,
retrieved episodic memories, and retrieved semantic procedures.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class AgentConfig:
    """Hyperparameters and configuration for the ReAct agent."""

    model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    device: str = "cuda"
    max_new_tokens: int = 256
    temperature: float = 0.0
    adapter_paths: list[str] = field(default_factory=list)
    torch_dtype: torch.dtype = torch.bfloat16
    trust_remote_code: bool = True
    do_sample: bool = False  # greedy when temperature == 0.0


def build_react_prompt(
    goal: str,
    observation: str,
    step: int,
    history: list[dict],
    episodic_context: str = "",
    semantic_context: str = "",
) -> str:
    """
    Build a ReAct-style prompt for the agent.

    Args:
        goal: The task goal description.
        observation: Current environment observation.
        step: Current step index (0-based).
        history: List of dicts with keys 'thought', 'action', 'observation'
                 representing prior steps in the episode.
        episodic_context: Retrieved past experiences (may be empty).
        semantic_context: Retrieved procedural knowledge (may be empty).

    Returns:
        A formatted prompt string ending with "Thought:" ready for the model.
    """
    lines: list[str] = []

    # System preamble
    lines.append("You are an embodied household agent. Think step by step, then act.")
    lines.append("")

    # Task goal
    lines.append(f"Task: {goal}")
    lines.append("")

    # Inject episodic memories if available
    if episodic_context.strip():
        lines.append("Relevant past experiences:")
        lines.append(episodic_context.strip())
        lines.append("")

    # Inject semantic / procedural knowledge if available
    if semantic_context.strip():
        lines.append("Known procedures:")
        lines.append(semantic_context.strip())
        lines.append("")

    # Format episode history as alternating Thought / Action / Observation lines
    for entry in history:
        thought = entry.get("thought", "")
        action = entry.get("action", "")
        obs = entry.get("observation", "")
        if thought:
            lines.append(f"Thought: {thought}")
        if action:
            lines.append(f"Action: {action}")
        if obs:
            lines.append(f"Observation: {obs}")

    # Current observation — model must predict Thought (and then Action)
    lines.append(f"Observation: {observation}")
    lines.append("Thought:")

    return "\n".join(lines)


class ReActAgent:
    """
    ReAct agent backed by a frozen Qwen2.5-7B-Instruct model with optional
    PEFT LoRA adapters.

    The backbone weights are always kept in eval mode and are not modified
    during inference. LoRA adapters can be loaded, swapped, or removed
    without reloading the base model.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        device: str = "cuda",
        max_new_tokens: int = 256,
        temperature: float = 0.0,
        adapter_paths: list[str] | None = None,
    ) -> None:
        """
        Initialise the agent by loading the tokenizer and frozen base model.

        Args:
            model_name: HuggingFace model identifier.
            device: Target device, e.g. "cuda" or "cpu".
            max_new_tokens: Maximum tokens to generate per step.
            temperature: Sampling temperature; 0.0 = greedy decoding.
            adapter_paths: Optional list of PEFT LoRA adapter directories to
                           load on top of the base model at initialisation.
        """
        self.config = AgentConfig(
            model_name=model_name,
            device=device,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            adapter_paths=adapter_paths or [],
        )
        self.device = device

        hf_token: Optional[str] = os.environ.get("HF_TOKEN")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=hf_token,
            trust_remote_code=self.config.trust_remote_code,
        )

        # Load base model in bfloat16, frozen
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=self.config.torch_dtype,
            device_map=device,
            token=hf_token,
            trust_remote_code=self.config.trust_remote_code,
        )
        self.model.eval()

        # Freeze all base parameters
        for param in self.model.parameters():
            param.requires_grad = False

        # Optionally attach LoRA adapters
        for adapter_path in self.config.adapter_paths:
            self.load_adapter(adapter_path)

    # ------------------------------------------------------------------
    # Adapter management
    # ------------------------------------------------------------------

    def load_adapter(self, adapter_path: str) -> None:
        """
        Load a PEFT LoRA adapter and merge it onto the base model.

        If multiple adapters are loaded they are stacked; each call to
        load_adapter attaches one additional adapter set.

        Args:
            adapter_path: Path to a directory containing adapter_config.json
                          and the adapter weights.
        """
        try:
            from peft import PeftModel  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "peft is required to load LoRA adapters. "
                "Install it with: pip install peft"
            ) from exc

        self.model = PeftModel.from_pretrained(
            self.model,
            adapter_path,
            is_trainable=False,
        )
        self.model.eval()

    def remove_adapters(self) -> None:
        """
        Merge all LoRA adapters into the base weights and discard the PEFT
        wrapper, returning the model to a plain AutoModelForCausalLM state.
        """
        try:
            from peft import PeftModel  # type: ignore[import-untyped]
        except ImportError:
            # If peft is not installed there are no adapters to remove.
            return

        if isinstance(self.model, PeftModel):
            self.model = self.model.merge_and_unload()
            self.model.eval()
            for param in self.model.parameters():
                param.requires_grad = False

    # ------------------------------------------------------------------
    # Core inference
    # ------------------------------------------------------------------

    def act(
        self,
        observation: str,
        goal: str,
        step: int,
        episode_history: list[dict],
        episodic_context: str = "",
        semantic_context: str = "",
    ) -> tuple[str, str]:
        """
        Generate the agent's next thought and action given the current state.

        Args:
            observation: Current environment observation string.
            goal: Task goal description.
            step: Current step index within the episode.
            episode_history: List of prior step dicts, each with optional keys
                             'thought', 'action', 'observation'.
            episodic_context: Retrieved episodic memories (may be empty).
            semantic_context: Retrieved semantic / procedural knowledge
                              (may be empty).

        Returns:
            A tuple (thought, action) where both are strings. If the model
            output cannot be parsed, returns ("(no thought)", raw[:100]).
        """
        prompt = build_react_prompt(
            goal=goal,
            observation=observation,
            step=step,
            history=episode_history,
            episodic_context=episodic_context,
            semantic_context=semantic_context,
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_length = inputs["input_ids"].shape[1]

        generate_kwargs: dict = {
            "max_new_tokens": self.config.max_new_tokens,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if self.config.temperature > 0.0:
            generate_kwargs["do_sample"] = True
            generate_kwargs["temperature"] = self.config.temperature
        else:
            generate_kwargs["do_sample"] = False

        with torch.inference_mode():
            output_ids = self.model.generate(**inputs, **generate_kwargs)

        # Decode only the newly generated tokens
        new_ids = output_ids[0, input_length:]
        raw_output: str = self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()

        thought, action = self._parse_output(raw_output)
        return thought, action

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_output(raw: str) -> tuple[str, str]:
        """
        Parse 'Thought: ... Action: ...' from raw model output.

        The model is prompted so that "Thought:" has already been written;
        the model continues from there, so the raw output starts with the
        thought text. We look for an explicit "Action:" delimiter.

        Returns:
            (thought, action) strings stripped of whitespace.
            Falls back to ("(no thought)", raw[:100]) when parsing fails.
        """
        # Pattern: optional leading "Thought:" label, then thought text,
        # then "Action:" followed by the action text.
        pattern = re.compile(
            r"(?:Thought:\s*)?(.*?)\s*Action:\s*(.+?)(?:\s*Observation:|$)",
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(raw)
        if match:
            thought = match.group(1).strip()
            action = match.group(2).strip()
            if action:
                return thought or "(no thought)", action

        # Fallback: try to at least extract an Action line
        action_match = re.search(r"Action:\s*(.+)", raw, re.IGNORECASE)
        if action_match:
            return "(no thought)", action_match.group(1).strip()

        # Complete parse failure
        return "(no thought)", raw[:100]
