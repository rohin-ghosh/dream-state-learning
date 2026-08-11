"""Felt Attention — v1 scorer head + fast-weight memory (numpy reference tier)."""
from .head import (FeltHead, hash_embed, embed_events, train_head_on_dataset,
                   eval_head, all_budgets_regret, normalize_salience)
from .fastweight import FastWeightMemory, value_modulated_weights
