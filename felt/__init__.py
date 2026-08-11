"""Felt Attention — v1 scorer head + fast-weight memory (numpy reference tier)."""
from .head import (FeltHead, hash_embed, embed_events, train_head_on_dataset,
                   eval_head, all_budgets_regret, normalize_salience)
from .fastweight import FastWeightMemory, value_modulated_weights
from .harness import Harness, RunConfig
from .baselines import run_probe_condition, PROBE_POLICIES
from .llm_player import (MockTextPlayer, HFBackend, play_episode, render_manual,
                          render_memory_context, retained_fact_texts, parse_action)
from .gates import gate_calibration
