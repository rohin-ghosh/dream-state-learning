"""Players. ScriptedExplorer = plumbing-tier episode generation (no LLM);
HFPlayer = real LLM play (GPU tier). Same prompt builder for every arm —
compute parity (SPEC_V2 §4)."""

from __future__ import annotations

import re
import numpy as np


def build_prompt(state: dict, memory_ctx: str) -> str:
    mem = memory_ctx if memory_ctx else "(none)"
    return (f"You are an alchemist. Goal: craft {state['goal']}.\n"
            f"MEMORY:\n{mem}\n"
            f"You hold: {', '.join(state['holdings'])}.\n"
            f"Last: {state['obs']}\n"
            "Reply with exactly one line: COMBINE <item> <item>.")


class ScriptedExplorer:
    """Tries untried pairs at random; prefers a goal recipe if one is known
    from this episode's own observations. Generates coverage, not skill."""

    def __init__(self, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        self.tried: set = set()

    def pick_pair(self, state, memory_ctx=""):
        h = state["holdings"]
        pairs = [(a, b) for i, a in enumerate(h) for b in h[i + 1:]]
        fresh = [p for p in pairs if tuple(sorted(p)) not in self.tried]
        pool = fresh if fresh else pairs
        if not pool:
            return None, None
        a, b = pool[int(self.rng.integers(len(pool)))]
        self.tried.add(tuple(sorted((a, b))))
        return a, b


class HFPlayer:
    """Local/GPU LLM player over the shared prompt."""

    def __init__(self, model, tokenizer, max_new_tokens: int = 24):
        self.model, self.tok = model, tokenizer
        self.max_new = max_new_tokens

    def pick_pair(self, state, memory_ctx=""):
        import torch
        prompt = self.tok.apply_chat_template(
            [{"role": "user", "content": build_prompt(state, memory_ctx)}],
            tokenize=False, add_generation_prompt=True)
        ids = self.tok(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(**ids, max_new_tokens=self.max_new,
                                      do_sample=False,
                                      pad_token_id=self.tok.eos_token_id)
        text = self.tok.decode(out[0][ids["input_ids"].shape[1]:],
                               skip_special_tokens=True)
        m = re.search(r"COMBINE\s+([\w-]+)\s+(?:and\s+)?([\w-]+)", text,
                      re.IGNORECASE)
        if not m:
            return None, None
        a, b = m.group(1), m.group(2)
        h = state["holdings"]
        return (a, b) if a in h and b in h else (None, None)
